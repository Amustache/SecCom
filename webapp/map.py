import json
import os


from dash import Dash, dcc, html, Input, Output
from flask import Flask, render_template_string
from flask_babel import _
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go


from webapp.config import BASEDIR
from webapp.map_helpers import fig_switzerland_empty, MUNICIPALITIES_DATA


def create_dash_app(flask_server: Flask, url_path="/map/"):
    # Load response data files for current and past commune responses
    df_commune_responses = pd.read_csv("data/commune_responses.csv")
    # Map language codes to integers for easier processing
    df_commune_responses["GSB23_UserLanguage"] = df_commune_responses["GSB23_UserLanguage"].map(
        {"DE": 1, "FR": 2, "RO": 3, "IT": 4}
    )

    # Load combined responses from both current and old years
    df_commune_responses_combined = pd.read_csv("data/commune_responses_combined.csv")

    # Load additional data files for the app
    df_combined = pd.read_csv("data/combined_df.csv")
    top_10_question_globales = pd.read_csv("data/top_10_QuestionGlobales_NLP.csv")

    # Create a Dash app instance with Bootstrap styling
    dash_app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        server=flask_server,
        url_base_pathname=url_path,
    )
    dash_app.config.suppress_callback_exceptions = True  # Suppress callback exceptions for better error handling

    # Define the layout of the app, including dropdowns, map, and slider
    dash_app.layout = html.Div(
        [
            # Dropdowns for selecting the survey and variable (question)
            html.Div(
                [
                    html.Div(
                        [
                            html.Label(
                                _("Survey selection"),
                                id="survey-selection-label",
                            ),
                            dcc.Dropdown(
                                id="survey-dropdown",
                                options=[
                                    {"value": "survey", "label": "2023"},
                                    {"value": "global_question", "label": _("All surveys")},
                                ],
                                value="survey",
                                clearable=False,
                            ),
                        ],
                        style={"width": "48%", "display": "inline-block"},
                    ),
                    html.Div(
                        [
                            html.Label(
                                _("Question"),
                                id="variable-selection-label",
                            ),
                            dcc.Dropdown(id="variable-dropdown", options=[], value=None, clearable=False),
                        ],
                        style={"width": "48%", "display": "inline-block"},
                    ),
                ],
                style={"display": "flex", "justify-content": "space-between"},
            ),
            # Map display component
            dcc.Graph(id="map-graph", style={"position": "relative", "z-index": "0"}),
            # Slider for selecting a year, dynamically updated based on selected global question
            html.Div(
                id="slider-container",
                style={"display": "none"},
                children=[
                    html.Label(
                        _("Select a year"),
                        id="slider-label",
                    ),
                    html.Div(
                        dcc.Slider(
                            id="slider",
                            min=1988,
                            max=2023,
                            value=None,  # Initial value depends on selected global question
                            marks={},  # Marks updated based on available years for the question
                            step=None,  # No intermediate values
                        ),
                        style={"width": "600px", "margin": "auto"},
                    ),
                ],
            ),
        ],
        style={
            "min-height": "100vh",
            "min-width": "100vw",
            "padding": "20px",
            "margin": "0",
            "font-family": "Arial, sans-serif",
            "position": "relative",
        },
    )

    # Callback to update options, map figure, and slider properties based on survey selection and year
    @dash_app.callback(
        Output("variable-dropdown", "options"),
        Output("slider-container", "style"),
        Output("map-graph", "figure"),
        Output("slider", "marks"),
        Output("slider", "value"),
        Input("survey-dropdown", "value"),
        Input("variable-dropdown", "value"),
        Input("slider", "value"),
    )
    def update_dropdown_and_map(selected_survey, selected_variable, selected_year):
        selected_language = "fr"  # get_locale()
        # Reindex to ensure 'year' and 'quest_glob' are accessible as rows
        if "year" not in df_commune_responses_combined.index:
            df_commune_responses_combined.set_index(df_commune_responses_combined.columns[0], inplace=True)

        empty_map = create_empty_map_figure()

        # Handle global questions selection
        if selected_survey == "global_question":
            codes = top_10_question_globales[
                top_10_question_globales["code_first_question"].isin(df_commune_responses_combined.columns)
            ]
            options = [
                {"label": row[f"text_{selected_language}"], "value": row["code_first_question"]}
                for _, row in codes.iterrows()
            ]

            if selected_variable:
                # Find associated survey questions and years for the selected global question
                if "quest_glob" in df_commune_responses_combined.index:
                    survey_columns = df_commune_responses_combined.columns[
                        df_commune_responses_combined.loc["quest_glob"] == selected_variable
                    ]
                    year_row = df_commune_responses_combined.loc["year", survey_columns]
                    associated_years = [
                        int(year) for year in year_row.unique() if pd.notna(year) and str(year).isdigit()
                    ]
                    year_to_survey = dict(zip(associated_years, survey_columns))

                    slider_marks = {year: str(year) for year in sorted(associated_years)}

                    # Use the last selected slider value if valid; otherwise, reset to the first available year
                    slider_value = (
                        selected_year
                        if selected_year in associated_years
                        else associated_years[0] if associated_years else None
                    )
                else:
                    print("Error: 'quest_glob' row not found in df_commune_responses_combined.")
                    slider_marks, slider_value = {}, None
            else:
                slider_marks, slider_value = {}, None

            slider_style = {"display": "block"}

        # Handle individual survey question selection
        else:  # selected_survey == "survey"
            options = [
                {"label": row[f"text_{selected_language}"], "value": row["code"]} for _, row in df_combined.iterrows()
            ]

            # Hide the slider and reset map for "survey" selection
            slider_style, slider_marks, slider_value = {"display": "none"}, {}, None

            # Display the map based on selected survey question
            if selected_variable and selected_variable in df_commune_responses_combined.columns:
                # Filter data for the selected survey question
                filtered_responses = df_commune_responses_combined[["GSB23_Q100", selected_variable]].fillna(99)
                communes = filtered_responses["GSB23_Q100"].astype(int).tolist()
                responses = filtered_responses[selected_variable].tolist()
                response_dict = dict(zip(communes, responses))

                # assign a default value (99) to communes without data
                aggregated_responses = [
                    response_dict.get(feature["properties"]["id"], -99) for feature in MUNICIPALITIES_DATA["features"]
                ]

                # Return the options and updated map figure
                return (
                    options,
                    slider_style,
                    create_figure(
                        aggregated_responses,
                        [feature["properties"]["id"] for feature in MUNICIPALITIES_DATA["features"]],
                    ),
                    slider_marks,
                    slider_value,
                )
            else:
                # If no survey question selected, return an empty map
                return options, slider_style, fig_switzerland_empty(), slider_marks, slider_value

        # Prepare the map figure for global question selection with slider control
        if selected_variable and selected_survey == "global_question":
            selected_survey_column = year_to_survey.get(slider_value)
            if selected_survey_column:
                filtered_responses = df_commune_responses_combined[["GSB23_Q100", selected_survey_column]].fillna(99)
                communes = filtered_responses["GSB23_Q100"].astype(int).tolist()
                responses = filtered_responses[selected_survey_column].tolist()
                response_dict = dict(zip(communes, responses))
            else:
                # No data for the selected year; return an empty map
                return options, slider_style, fig_switzerland_empty(), slider_marks, slider_value

            # assign a default value (99) to communes without data
            aggregated_responses = [
                response_dict.get(feature["properties"]["id"], -99) for feature in MUNICIPALITIES_DATA["features"]
            ]

            return (
                options,
                slider_style,
                create_figure(
                    aggregated_responses, [feature["properties"]["id"] for feature in MUNICIPALITIES_DATA["features"]]
                ),
                slider_marks,
                slider_value,
            )

        # Default fallback: return empty map and no options if conditions aren't met
        return options, slider_style, fig_switzerland_empty(), slider_marks, slider_value

    # Function to create the map figure based on survey responses
    def create_figure(variable_values, communes):
        # Count unique non-NaN values
        unique_values = [v for v in variable_values if isinstance(v, (int, float)) and not pd.isna(v)]
        num_unique_values = len(set(unique_values))
        print(num_unique_values)

        # Determine color scale based on the number of unique values
        if num_unique_values < 11:  # to correct once we know how to
            # Use discrete color scale for 10 or fewer unique values
            color_scale = [
                [-1, "gray"],  # Voluntary no response (-99)
                [0, "rgb(255,247,251)"],  # Example colors, you can customize these as needed
                [1, "rgb(236,231,242)"],
                [2, "rgb(208,209,230)"],
                [3, "rgb(166,189,219)"],
                [4, "rgb(116,169,207)"],
                [5, "rgb(54,144,192)"],
                [6, "rgb(5,112,176)"],
                [7, "rgb(4,90,141)"],
                [8, "rgb(2,56,88)"],
                [9, "rgb(1,42,62)"],
                [10, "rgb(0,30,45)"],
            ]
        else:
            # Use Viridis continuous color scale for more than 10 unique values
            color_scale = "Viridis"

        fig = fig_switzerland_empty()

        # temporary white layer to avoid the holes in the map
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=municipalities_data,
                locations=[feature["properties"]["id"] for feature in municipalities_data["features"]],
                z=[1] * len(municipalities_data["features"]),
                colorscale=[[0, "white"], [1, "white"]],
                featureidkey="properties.id",
                name="Municipalities",
                hoverinfo="text",
                text=[feature["properties"]["name"] for feature in municipalities_data["features"]],
                showscale=False,
            )
        )

        # Add the municipalities layer with dynamic or discrete color scale based on unique value count
        fig.add_trace(
            go.Choroplethmapbox(
                name="municipalities",
                geojson=MUNICIPALITIES_DATA,
                locations=communes,
                z=variable_values,
                colorscale=color_scale,
                featureidkey="properties.id",
                hoverinfo="text",
                text=[
                    f"{feature['properties']['name']}: "
                    f"{'No Data' if value == -1 else ('Voluntary no response' if value == -99 else ('No opinion' if value == 99 else value))}"
                    for value, feature in zip(variable_values, MUNICIPALITIES_DATA["features"])
                ],
                colorbar=dict(
                    title="Values",
                    thickness=25,
                    x=1.05,
                    y=0.5,
                    tickvals=[-99] + list(range(0, 11)),
                    ticktext=["No Data", "Voluntary No Response"] + [str(i) for i in range(0, 11)],
                ),
                showscale=True,
                zmin=0 if num_unique_values <= 10 else None,
                zmax=10 if num_unique_values <= 10 else None,
            )
        )

        # Update layout for the map
        fig.update_layout(
            mapbox_zoom=7,
            mapbox_center={"lat": 46.4, "lon": 8.8},
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=800,
            width=1200,
            dragmode=False,
            uirevision=str(np.random.rand()),
            mapbox=dict(
                layers=[], accesstoken="your-access-token", zoom=7, center={"lat": 46.4, "lon": 8.1}, style="white-bg"
            ),
            showlegend=False,
        )

        return fig

    # Black magic tkt
    with flask_server.app_context(), flask_server.test_request_context():
        with open(os.path.join(BASEDIR, "templates", "public", "map.html"), "r") as f:
            html_body = render_template_string(f.read())

        for comment in ["app_entry", "config", "scripts", "renderer"]:
            html_body = html_body.replace(f"<!-- {comment} -->", "{%" + comment + "%}")

        dash_app.index_string = html_body

    return dash_app.server
