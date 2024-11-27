import os


from dash import ALL, ctx, Dash, dcc, html, Input, Output
from flask import Flask, render_template_string
from flask_babel import _
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go


from webapp.config import BASEDIR
from webapp.map_helpers import (
    COLOR_SCALE_10,
    COLOR_SCALE_SPECIAL,
    fig_switzerland_empty,
    MUNICIPALITIES,
    MUNICIPALITIES_DATA,
    SPECIAL_ANSWERS,
)


def create_dash_app(flask_server: Flask, url_path="/map/"):
    # Load combined responses from both current and old years
    df_commune_responses_combined = pd.read_csv("data/commune_responses_combined.csv").set_index("gemid")
    df_commune_responses_combined.replace({-99: None, -99.0: None}, inplace=True)
    df_commune_responses_combined = df_commune_responses_combined.applymap(
        lambda x: -99 if pd.notna(x) and isinstance(x, (int, float)) and x < 0 else x
    )
    df_commune_responses_combined = df_commune_responses_combined.apply(pd.to_numeric, errors="coerce")


    
    # Load additional data files for the app
    df_combined = pd.read_csv("data/combined_df.csv")
    top_10_question_globales = pd.read_csv("data/top_10_QuestionGlobales_NLP.csv")
    # Load labels
    df_labels = pd.read_csv("data/answ_details_2023.csv", delimiter=";").set_index("qid")
    labels = {
        qid: {val: lab for val, lab in zip(cols["values"].split(";"), cols["labels"].split(";"))}
        for qid, cols in df_labels.to_dict(orient="index").items()
    }

    # Create a Dash app instance with Bootstrap styling
    dash_app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        server=flask_server,
        url_base_pathname=url_path,
    )
    dash_app.config.suppress_callback_exceptions = True  # Suppress callback exceptions for better error handling

    # Define the layout of the app, including dropdowns, map, and slider
    layout_card = dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                id="map-graph",
                style={
                    "height": "75vh",
                },
            )
        ),
        className="mb-4",
    )
    layout_infos = dbc.Card(
        dbc.CardBody(
            [
                html.H4("Instructions", id="info-title", className="card-title"),
                html.P(
                    "Select a question in the list bellow, then select a municipality on the map.",
                    id="info-text",
                    className="card-text",
                ),
                html.Em(
                    "Please note that some of the data is incomplete/still being worked on. Bugs and inconsistency are to be expected!"
                ),
            ]
        ),
        className="mb-4",
    )
    layout_options = dbc.Card(
        dbc.CardBody(
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
                ),
                html.Div(
                    id="slider-container",
                    style={"display": "none"},
                    children=[
                        html.Label(
                            _("Select a question to see the years"),
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
                                disabled=True,
                            ),
                        ),
                    ],
                ),
            ]
        ),
        className="mb-4",
    )
    layout_questions = dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.Label(
                            _("Question"),
                            id="variable-selection-label",
                        ),
                        dbc.ListGroup(
                            [],
                            id="questions-list",
                            style={"overflow-y": "auto", "max-height": "300px"},
                        ),
                    ],
                ),
            ]
        ),
        className="mb-4",
    )

    layout_full = html.Div(
        dbc.Row(
            [
                dbc.Col(layout_card, width=8),
                dbc.Col([layout_infos, layout_options, layout_questions], width=4),
            ]
        )
    )

    dash_app.layout = layout_full

    # Callback to update options, map figure, and slider properties based on survey selection and year
    @dash_app.callback(
        Output("questions-list", "children"),
        Output("slider-container", "style"),
        Output("map-graph", "figure"),
        Output("slider", "marks"),
        Output("slider", "value"),
        Input("survey-dropdown", "value"),
        Input({"type": "list-group-item", "index": ALL}, "n_clicks"),
        Input("slider", "value"),
    )
    def update_dropdown_and_map(selected_survey, list_group_items, selected_year):
        if any(list_group_items):
            selected_variable = ctx.triggered_id.index
        else:
            selected_variable = None

        selected_language = "en"  # get_locale()

        # Reindex to ensure 'year' and 'quest_glob' are accessible as rows
        if "year" not in df_commune_responses_combined.index:
            df_commune_responses_combined.set_index(df_commune_responses_combined.columns[0], inplace=True)

        # Handle global questions selection
        if selected_survey == "global_question":
            codes = top_10_question_globales[
                top_10_question_globales["code_first_question"].isin(df_commune_responses_combined.columns)
            ]
            options = [
                dbc.ListGroupItem(
                    row[f"text_{selected_language}"],
                    id={"type": "list-group-item", "index": row["code_first_question"]},
                    n_clicks=0,
                    action=True,
                )
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
                dbc.ListGroupItem(
                    row[f"text_{selected_language}"],
                    id={"type": "list-group-item", "index": row["code"]},
                    n_clicks=0,
                    action=True,
                )
                for _, row in [(i, r) for i, r in df_combined.iterrows()][3:]
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

                # assign a default value (-99) to communes without data
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
                        labels[selected_variable] if selected_variable in labels else None,
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
                    aggregated_responses,
                    [feature["properties"]["id"] for feature in MUNICIPALITIES_DATA["features"]],
                    labels[selected_variable] if selected_variable in labels else None,
                ),
                slider_marks,
                slider_value,
            )

        # Default fallback: return empty map and no options if conditions aren't met
        return options, slider_style, fig_switzerland_empty(), slider_marks, slider_value

    # Function to create the map figure based on survey responses
    def create_figure(variable_values, communes, labels=None):
        # Count unique non-NaN values
        unique_values = set([v for v in variable_values if isinstance(v, (int, float)) and not pd.isna(v)])
        num_unique_values = len(unique_values)

        # We remove the special values
        keep_special_values = set()
        for value in SPECIAL_ANSWERS.keys():
            try:
                unique_values.remove(value)
                keep_special_values.add(value)
            except KeyError:
                pass

        fig = fig_switzerland_empty()

        if num_unique_values > len(COLOR_SCALE_10):
            fig.add_trace(
                go.Choroplethmapbox(
                    geojson=MUNICIPALITIES_DATA,
                    locations=communes,
                    z=variable_values,
                    colorscale="Blues",
                    featureidkey="properties.id",
                    hoverinfo="text",
                    text=[
                        f"{feature['properties']['name']}: "
                        f"{('No data' if value == -99 else ('No opinion' if value == 99 else value))}"
                        for value, feature in zip(variable_values, MUNICIPALITIES_DATA["features"])
                    ],
                    showscale=True,
                )
            )
        else:
            for i, value in enumerate(unique_values):
                temp_answers = [x for x in zip(communes, variable_values) if x[1] == value]
                fig.add_trace(
                    go.Choroplethmapbox(
                        geojson=MUNICIPALITIES_DATA,
                        locations=[x[0] for x in temp_answers],
                        z=[i] * len(temp_answers),
                        featureidkey="properties.id",
                        showlegend=True,
                        name=labels[str(int(value))] if labels else value,
                        colorscale=COLOR_SCALE_10[i],
                        hoverinfo="text",
                        text=[f"{MUNICIPALITIES[temp_name]}: {temp_value}" for (temp_name, temp_value) in temp_answers],
                        showscale=False,  # Hidding the scale
                    )
                )

        # Add special values back
        for i, value in enumerate(keep_special_values):
            temp_answers = [x for x in zip(communes, variable_values) if x[1] == value]
            text_answer = SPECIAL_ANSWERS[value]
            fig.add_trace(
                go.Choroplethmapbox(
                    geojson=MUNICIPALITIES_DATA,
                    locations=[x[0] for x in temp_answers],
                    z=[i] * len(temp_answers),
                    featureidkey="properties.id",
                    showlegend=True,
                    name=text_answer,
                    colorscale=COLOR_SCALE_SPECIAL[i],
                    hoverinfo="text",
                    text=[f"{MUNICIPALITIES[temp_name]}: {text_answer}" for (temp_name, temp_value) in temp_answers],
                    showscale=False,  # Hidding the scale
                )
            )

        return fig

    # Integrate dash app into flask app
    with flask_server.app_context(), flask_server.test_request_context():
        with open(os.path.join(BASEDIR, "templates", "public", "map.html"), "r") as f:
            html_body = render_template_string(f.read())

        for comment in ["app_entry", "config", "scripts", "renderer"]:
            html_body = html_body.replace(f"<!-- {comment} -->", "{%" + comment + "%}")

        dash_app.index_string = html_body

    return dash_app.server
