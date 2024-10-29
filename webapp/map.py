import json
from dash import Dash, dcc, html, Input, Output
from flask import Flask
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go

def create_dash_app(flask_server: Flask):
    # Load GeoJSON files for lakes, municipalities, and country borders with utf-8 encoding
    with open("./data/lakes.json", encoding="utf-8") as f:
        lakes_data = json.load(f)
    with open("./data/municipalities.json", encoding="utf-8") as f:
        municipalities_data = json.load(f)
    with open("./data/country.json", encoding="utf-8") as f:
        country_data = json.load(f)

    # Load response data files for current and past commune responses
    df_commune_responses = pd.read_csv("data/commune_responses.csv")
    # Map language codes to integers for easier processing
    df_commune_responses['GSB23_UserLanguage'] = df_commune_responses['GSB23_UserLanguage'].map({'DE': 1, 'FR': 2, 'RO': 3, 'IT': 4})
    df_commune_response_old_year = pd.read_csv("data/GSB_1988_2017_V1.csv", low_memory=False)

    # Load combined responses from both current and old years
    df_commune_responses_combined = pd.read_csv("data/commune_responses_combined.csv")

    # Define a row for the user language question, with labels and options in multiple languages
    sprache_row = {
        'label': 'spr', 
        'code_first_question': 'GSB23_UserLanguage', 
        'code_other_question': 'spr88; spr94; spr98; spr05; spr09; spr17',
        'text_de': 'Benutzersprache', 
        'text_fr': 'Langue de l\'utilisateur', 
        'text_it': 'Lingua dell\'utente', 
        'text_ro': 'lingua da l\'utilisader', 
        'text_en': 'User language', 
        'category_label': 'discrete', 
        'category_text_de': 'character-200', 
        'category_text_fr': 'character-200', 
        'category_text_it': 'character-200', 
        'category_text_ro': 'character-200', 
        'category_text_en': 'character-200', 
        'options_value': None, 
        'options_label': None
    }

    # Load additional data files for the app
    df_combined = pd.read_csv("data/combined_df.csv")
    question_globale_NLP = pd.read_csv("data/QuestionGlobales_NLP.csv")
    top_10_question_globales = pd.read_csv("data/top_10_QuestionGlobales_NLP.csv")

    # Create a Dash app instance with Bootstrap styling
    dash_app = Dash(
        __name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=flask_server, url_base_pathname="/map/"
    )
    dash_app.config.suppress_callback_exceptions = True  # Suppress callback exceptions for better error handling

    # Translation dictionaries for different languages used in the interface
    translation = {
        "fr": {
            "title": "Carte avec échelle de couleur dynamique",
            "survey_selection": "Sélection de l'enquête",
            "variable_selection": "Sélection de la variable",
            "slider_label": "Ajuster le curseur",
            "global_question": "Question globale",
            "survey": "Enquête",
            "voluntary_no_response": "Réponse volontaire non fournie",
            "exited_survey": "Enquête abandonnée",
            "no_opinion": "Pas d'opinion",
            "values": "Valeurs",
        },
        "en": {
            "title": "Map with dynamic color scale",
            "survey_selection": "Survey selection",
            "variable_selection": "Variable selection",
            "slider_label": "Adjust the slider",
            "global_question": "Global question",
            "survey": "Survey",
            "voluntary_no_response": "Voluntary no response",
            "exited_survey": "Exited survey",
            "no_opinion": "No opinion",
            "values": "Values",
        },
        "de": {
            "title": "Karte mit dynamischer Farbskala",
            "survey_selection": "Umfrageauswahl",
            "variable_selection": "Variablenauswahl",
            "slider_label": "Schieberegler anpassen",
            "global_question": "Globale Frage",
            "survey": "Umfrage",
            "voluntary_no_response": "Freiwillige keine Antwort",
            "exited_survey": "Umfrage verlassen",
            "no_opinion": "Keine Meinung",
            "values": "Werte",
        },
        "it": {
            "title": "Mappa con scala cromatica dinamica",
            "survey_selection": "Selezione del sondaggio",
            "variable_selection": "Selezione della variabile",
            "slider_label": "Regola il cursore",
            "global_question": "Domanda globale",
            "survey": "Sondaggio",
            "voluntary_no_response": "Nessuna risposta volontaria",
            "exited_survey": "Sondaggio abbandonato",
            "no_opinion": "Nessuna opinione",
            "values": "Valori",
        },
        "ro": {  # Romansh
            "title": "Carta cun scala da colur dinamica",
            "survey_selection": "Tscherna da l'enquista",
            "variable_selection": "Tscherna da la variabla",
            "slider_label": "Midar il slider",
            "global_question": "Dumonda globala",
            "survey": "Enquista",
            "voluntary_no_response": "Risposta betg dada voluntarmain",
            "exited_survey": "Enquista terminada",
            "no_opinion": "Nagina opiniun",
            "values": "Valurs",
        },
    }
    
    # Translations for survey responses based on language, with unique mappings for special responses
    response_translations = {
        "fr": {-99: "Réponse volontaire non fournie", 99: "Pas d'opinion", "default": "Enquête abandonnée"},
        "de": {-99: "Freiwillige keine Antwort", 99: "Keine Meinung", "default": "Umfrage verlassen"},
        "it": {-99: "Nessuna risposta volontaria", 99: "Nessuna opinione", "default": "Sondaggio abbandonato"},
        "ro": {-99: "Risposta betg dada voluntarmain", 99: "Nagina opiniun", "default": "Enquista terminada"},
    }

    # Define the layout of the app, including dropdowns, map, and slider
    dash_app.layout = html.Div(
        [
            # Application title displayed at the top
            html.H1(id="page-title", style={"text-align": "left", "margin-bottom": "40px"}),
            
            # Dropdown menu for language selection
            html.Div(
                [
                    html.Label("Language"),
                    dcc.Dropdown(
                        id="language-dropdown",
                        options=[
                            {"label": "Français", "value": "fr"},
                            {"label": "Deutsch", "value": "de"},
                            {"label": "Italiano", "value": "it"},
                            {"label": "Rumantsch", "value": "ro"},
                            {"label": "English", "value": "en"},
                        ],
                        value="fr",  # Default language set to French
                        clearable=False,
                    ),
                ],
                style={
                    "position": "fixed",
                    "bottom": "10px",
                    "left": "10px",
                    "width": "200px",
                    "background-color": "white",
                    "padding": "10px",
                    "box-shadow": "0px 0px 5px rgba(0, 0, 0, 0.1)",
                    "z-index": "1000",
                    "max-height": "150px",
                    "overflow-y": "auto",
                },
            ),
            
            # Dropdowns for selecting the survey and variable (question)
            html.Div(
                [
                    html.Div(
                        [
                            html.Label(id="survey-selection-label"),
                            dcc.Dropdown(
                                id="survey-dropdown",
                                options=[],
                                value="survey",
                                clearable=False,
                            ),
                        ],
                        style={"width": "48%", "display": "inline-block"},
                    ),
                    html.Div(
                        [
                            html.Label(id="variable-selection-label"),
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
                    html.Label(id="slider-label"),
                    html.Div(  
                        dcc.Slider(
                            id="slider",
                            min=1988,
                            max=2023,
                            value

=None,  # Initial value depends on selected global question
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

    # Callback for updating the language of the app based on the selected language
    @dash_app.callback(
        Output("page-title", "children"),
        Output("survey-selection-label", "children"),
        Output("variable-selection-label", "children"),
        Output("survey-dropdown", "options"),
        Output("slider-label", "children"),
        Input("language-dropdown", "value"),
    )
    def update_language(selected_language):
        # Define options based on translation dictionary
        options = [
            {"label": translation[selected_language]["global_question"], "value": "global_question"},
            {"label": translation[selected_language]["survey"], "value": "survey"},
        ]

        # Return translated text for page title, labels, dropdown options, and slider label
        return (
            translation[selected_language]["title"],
            translation[selected_language]["survey_selection"],
            translation[selected_language]["variable_selection"],
            options,
            translation[selected_language]["slider_label"],
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
        Input("language-dropdown", "value"),
        Input("slider", "value"),
    )
    def update_dropdown_and_map(selected_survey, selected_variable, selected_language, selected_year):
        # Reindex to ensure 'year' and 'quest_glob' are accessible as rows
        if 'year' not in df_commune_responses_combined.index:
            df_commune_responses_combined.set_index(df_commune_responses_combined.columns[0], inplace=True)

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
                if 'quest_glob' in df_commune_responses_combined.index:
                    survey_columns = df_commune_responses_combined.columns[
                        df_commune_responses_combined.loc['quest_glob'] == selected_variable
                    ]
                    year_row = df_commune_responses_combined.loc['year', survey_columns]
                    associated_years = [int(year) for year in year_row.unique() if pd.notna(year) and str(year).isdigit()]
                    year_to_survey = dict(zip(associated_years, survey_columns))

                    slider_marks = {year: str(year) for year in sorted(associated_years)}
                    
                    # Use the last selected slider value if valid; otherwise, reset to the first available year
                    slider_value = selected_year if selected_year in associated_years else associated_years[0] if associated_years else None
                else:
                    print("Error: 'quest_glob' row not found in df_commune_responses_combined.")
                    slider_marks, slider_value = {}, None
            else:
                slider_marks, slider_value = {}, None

            slider_style = {"display": "block"}

        # Handle individual survey question selection
        else:  # selected_survey == "survey"
            options = [
                {"label": row[f"text_{selected_language}"], "value": row["code"]}
                for _, row in df_combined.iterrows()
            ]
            
            # Hide the slider and reset map for "survey" selection
            slider_style, slider_marks, slider_value = {"display": "none"}, {}, None
            
            # Display the map based on selected survey question
            if selected_variable and selected_variable in df_commune_responses_combined.columns:
                # Filter data for the selected survey question
                filtered_responses = df_commune_responses_combined[["GSB23_Q100", selected_variable]].dropna()
                communes = filtered_responses["GSB23_Q100"].astype(int).tolist()
                responses = filtered_responses[selected_variable].tolist()
                response_dict = dict(zip(communes, responses))
                aggregated_responses = [
                    response_dict.get(feature["properties"]["id"], -99) for feature in municipalities_data["features"]
                ]
                
                # Return the options and updated map figure
                return (
                    options,
                    slider_style,
                    create_figure(
                        aggregated_responses, [feature["properties"]["id"] for feature in municipalities_data["features"]]
                    ),
                    slider_marks,
                    slider_value
                )
            else:
                # If no survey question selected, return an empty map
                return options, slider_style, create_empty_map_figure(), slider_marks, slider_value

        # Prepare the map figure for global question selection with slider control
        if selected_variable and selected_survey == "global_question":
            selected_survey_column = year_to_survey.get(slider_value)
            if selected_survey_column:
                filtered_responses = df_commune_responses_combined[["GSB23_Q100", selected_survey_column]].dropna()
                communes = filtered_responses["GSB23_Q100"].astype(int).tolist()
                responses = filtered_responses[selected_survey_column].tolist()
                response_dict = dict(zip(communes, responses))
            else:
                # No data for the selected year; return an empty map
                return options, slider_style, create_empty_map_figure(), slider_marks, slider_value

            aggregated_responses = [
                response_dict.get(feature["properties"]["id"], -99) for feature in municipalities_data["features"]
            ]

            return (
                options,
                slider_style,
                create_figure(
                    aggregated_responses, [feature["properties"]["id"] for feature in municipalities_data["features"]]
                ),
                slider_marks,
                slider_value
            )

        # Default fallback: return empty map and no options if conditions aren't met
        return options, slider_style, create_empty_map_figure(), slider_marks, slider_value


    # Function to create an empty map figure when no data is available
    def create_empty_map_figure():
        fig = go.Figure()

        # Add base layer for the country, in white
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=country_data,
                locations=[feature["properties"]["id"] for feature in country_data["features"]],
                z=[1] * len(country_data["features"]),
                colorscale=[[0, "white"], [1, "white"]],
                featureidkey="properties.id",
                name="Country",
            )
        )

        # Add municipalities layer in white
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

        # Add lakes layer in blue
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=lakes_data,
                locations=[feature["properties"]["id"] for feature in lakes_data["features"]],
                z=[1] * len(lakes_data["features"]),
                colorscale="Blues",
                featureidkey="properties.id",
                name="Lakes",
                hoverinfo="text",
                text=[feature["properties"]["name"] for feature in lakes_data["features"]],
                showscale=False,
            )
        )

        # Map layout configuration for an empty view
        fig.update_layout(
            mapbox_zoom=7,
            mapbox_center={"lat": 46.4, "lon": 8.8},
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=800,
            width=1200,
            dragmode=False,
            uirevision=True,
            mapbox=dict(
                layers=[], accesstoken="your-access-token", zoom=7, center={"lat": 46.4, "lon": 8.1}, style="white-bg"
            ),
            showlegend=False,
        )
        return fig

    # Function to create the map figure based on survey responses
    def create_figure(variable_values, communes):
        # Count unique non-NaN values
        unique_values = [v for v in variable_values if isinstance(v, (int, float)) and not pd.isna(v)]
        num_unique_values = len(set(unique_values))

        # Determine color scale based on the number of unique values
        if num_unique_values == 99: # to correct once we know how to 
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
                [10, "rgb(0,30,45)"]
            ]
        else: 
            # Use Viridis continuous color scale for more than 10 unique values
            color_scale = "Viridis"

        # Prepare display values, assigning -1 to NaN values to appear as gray if using discrete scale
        display_values = [
            -1 if pd.isna(value) else value for value in variable_values
        ]

        fig = go.Figure()

        # Add the country layer as a white background
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=country_data,
                locations=[feature["properties"]["id"] for feature in country_data["features"]],
                z=[1] * len(country_data["features"]),
                colorscale=[[0, "white"], [1, "white"]],
                featureidkey="properties.id",
                name="Country",
            )
        )

        # Add the municipalities layer with dynamic or discrete color scale based on unique value count
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=municipalities_data,
                locations=communes,
                z=display_values,
                colorscale=color_scale,
                featureidkey="properties.id",
                name="Municipalities",
                hoverinfo="text",
                text=[
                    f"{feature['properties']['name']}: "
                    f"{'No Data' if value == -1 else ('Voluntary no response' if value == -99 else ('No opinion' if value == 99 else value))}"
                    for value, feature in zip(display_values, municipalities_data["features"])
                ],
                colorbar=dict(
                    title="Values",
                    thickness=25,
                    x=1.05,
                    y=0.5,
                    tickvals=[-99, -1] + list(range(0, 11)),
                    ticktext=["Voluntary No Response", "No Data"] + [str(i) for i in range(0, 11)],
                ),
                showscale=True,
                zmin=-1 if num_unique_values <= 10 else None,
                zmax=10 if num_unique_values <= 10 else None,
            )
        )

        # Add the lakes layer
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=lakes_data,
                locations=[feature["properties"]["id"] for feature in lakes_data["features"]],
                z=[1] * len(lakes_data["features"]),
                colorscale="Blues",
                featureidkey="properties.id",
                name="Lakes",
                hoverinfo="text",
                text=[feature["properties"]["name"] for feature in lakes_data["features"]],
                showscale=False,
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
            uirevision=True,
            mapbox=dict(
                layers=[], accesstoken="your-access-token", zoom=7, center={"lat": 46.4, "lon": 8.1}, style="white-bg"
            ),
            showlegend=False,
        )

        return fig


    return dash_app.server
