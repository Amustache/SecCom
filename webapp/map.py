import json


from dash import Dash, dcc, html, Input, Output
from flask import Flask
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def create_dash_app(flask_server: Flask):
    # Load the GeoJSON files with utf-8 encoding
    with open("./data/lakes.json", encoding="utf-8") as f:
        lakes_data = json.load(f)

    with open("./data/municipalities.json", encoding="utf-8") as f:
        municipalities_data = json.load(f)

    with open("./data/country.json", encoding="utf-8") as f:
        country_data = json.load(f)

    # Load response data files
    df_commune_responses = pd.read_csv("data/commune_responses.csv")
    df_commune_responses['GSB23_UserLanguage'] = df_commune_responses['GSB23_UserLanguage'].map({'DE': 1,'FR': 2,'RO': 3,'IT': 4})
    df_commune_response_old_year = pd.read_csv("data/GSB_1988_2017_V1.csv", low_memory=False)
    #print('response old years',df_commune_response_old_year.head())
    # Combine the current and old year responses
    #df_commune_responses_combined = pd.concat([df_commune_responses, df_commune_response_old_year], axis=1, ignore_index = False)
    #df_commune_responses_combined.to_csv("data/commune_responses_combined.csv", index=False)
    df_commune_responses_combined = pd.read_csv("data/commune_responses_combined.csv")
    spr_df = pd.read_csv("data/spr_df.csv")
    #print('response full years',df_commune_responses_combined.head())

    # add the line with the language question
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

    df_combined = pd.read_csv("data/combined_df.csv")
    question_globale_NLP = pd.read_csv("data/QuestionGlobales_NLP.csv")
    #question_globale_NLP = pd.concat([question_globale_NLP, pd.DataFrame([sprache_row])], ignore_index=True)
    top_10_question_globales = pd.read_csv("data/top_10_QuestionGlobales_NLP.csv")
    #top_10_question_globales = pd.concat([top_10_question_globales, pd.DataFrame([sprache_row])], ignore_index=True)
    #top_10_question_globales.to_csv("data/top_10_QuestionGlobales_NLP.csv", index=False)

    # Create a Dash app
    dash_app = Dash(
        __name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=flask_server, url_base_pathname="/map/"
    )
    dash_app.config.suppress_callback_exceptions = True  # Suppress callback exceptions for better error handling

    # Translation dictionaries for different languages
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
        "ro": {  # Romanche
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
    response_translations = {
        "fr": {-99: "Réponse volontaire non fournie", 99: "Pas d'opinion", "default": "Enquête abandonnée"},
        "de": {-99: "Freiwillige keine Antwort", 99: "Keine Meinung", "default": "Umfrage verlassen"},
        "it": {-99: "Nessuna risposta volontaria", 99: "Nessuna opinione", "default": "Sondaggio abbandonato"},
        "ro": {-99: "Risposta betg dada voluntarmain", 99: "Nagina opiniun", "default": "Enquista terminada"},
    }

    # Define the layout of the app
    dash_app.layout = html.Div(
        [
            # Title of the application
            html.H1(id="page-title", style={"text-align": "left", "margin-bottom": "40px"}),
            # dropdown for language selection
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
                        value="fr",  # defaut language
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
            # Dropdown for survey selection and variable selection
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
            dcc.Graph(id="map-graph", style={"position": "relative", "z-index": "0"}),
            # slider for year selection
            html.Div(
                id="slider-container",
                style={"display": "none"},
                children=[
                    html.Label(id="slider-label"),
                    html.Div(  # Wrap the Slider in a Div for styling
                        dcc.Slider(
                            id="slider",
                            min=1988,
                            max=2023,
                            value=2023,  # default value
                            marks={
                                1988: "1988",
                                1994: "1994",
                                1998: "1998",
                                2005: "2005",
                                2009: "2009",
                                2017: "2017",
                                2023: "2023",
                            },
                            step=None,  # to disable intermediate values
                        ),
                        style={"width": "600px", "margin": "auto"},  # style for the container
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

    # Callbacks
    @dash_app.callback(
        Output("page-title", "children"),
        Output("survey-selection-label", "children"),
        Output("variable-selection-label", "children"),
        Output("survey-dropdown", "options"),
        Output("slider-label", "children"),
        Input("language-dropdown", "value"),
    )
    # Update the language of the app
    def update_language(selected_language):
        options = [
            {"label": translation[selected_language]["global_question"], "value": "global_question"},
            {"label": translation[selected_language]["survey"], "value": "survey"},
        ]

        return (
            translation[selected_language]["title"],
            translation[selected_language]["survey_selection"],
            translation[selected_language]["variable_selection"],
            options,
            translation[selected_language]["slider_label"],
        )

    @dash_app.callback(
        Output("variable-dropdown", "options"),
        Output("slider-container", "style"),
        Output("map-graph", "figure"),
        Input("survey-dropdown", "value"),
        Input("variable-dropdown", "value"),
        Input("language-dropdown", "value"),
        Input("slider", "value"),
    )
    def get_results(selected_year, df):
        year_to_column_index = {
            2023: 2,  
            1988: 3,  
            1994: 4,  
            1998: 5,  
            2005: 6,   
            2009: 7,   
            2017: 8   
        }
        column_index = year_to_column_index.get(selected_year)
        if column_index is not None:
            results = df.iloc[:, column_index]
        else:
            results = None  # Ou une valeur par défaut si l'année n'est pas reconnue
        return results
    
    def update_dropdown_and_map(selected_survey, selected_variable, selected_language, selected_year):
        # Update variable options based on selected survey

        if selected_survey == "global_question":
            codes = top_10_question_globales[
                top_10_question_globales["code_first_question"].isin(df_commune_responses_combined.columns)
            ]
            options = [
                {"label": row[f"text_{selected_language}"], "value": row["code_first_question"]}
                for _, row in codes.iterrows()
            ]
        else:
            options = [
                {"label": row[f"text_{selected_language}"], "value": row["code"]} for _, row in df_combined.iterrows()
            ]

        if selected_survey == "global_question" and selected_variable == 'GSB23_UserLanguage':
            # Utiliser spr_df pour obtenir les résultats pour GSB23_UserLanguage
            results = get_results(selected_year, spr_df)
            # Vous pouvez maintenant utiliser `results` pour mettre à jour les données à afficher sur la carte
            # Par exemple, si vous devez filtrer les réponses, cela pourrait ressembler à ceci :
            filtered_responses = pd.DataFrame({
                'GSB23_Q100': df_commune_responses_combined['GSB23_Q100'],  # Assurez-vous que cette colonne est correcte
                'responses': results  # Utiliser les résultats récupérés
            }).dropna()

            communes = filtered_responses["GSB23_Q100"].astype(int).tolist()
            responses = filtered_responses['responses'].tolist()
            response_dict = dict(zip(communes, responses))
            aggregated_responses = [
                response_dict.get(feature["properties"]["id"], -99) for feature in municipalities_data["features"]
            ]

            return (
                options,
                slider_style,
                create_figure(
                    aggregated_responses, [feature["properties"]["id"] for feature in municipalities_data["features"]]
                ),
            )

        # Determine if the slider should be shown
        slider_style = {"display": "block"} if selected_survey == "global_question" else {"display": "none"}

        # Prepare the map figure
        if selected_variable is None:
            return options, slider_style, create_empty_map_figure()  # Provide a function to create an empty figure

        if selected_variable not in df_commune_responses_combined.columns:
            raise ValueError(f"The variable '{selected_variable}' does not exist in the commune responses.")

        filtered_responses = df_commune_responses_combined[["GSB23_Q100", selected_variable]].dropna()
        communes = filtered_responses["GSB23_Q100"].astype(int).tolist()
        responses = filtered_responses[selected_variable].tolist()
        response_dict = dict(zip(communes, responses))
        aggregated_responses = [
            response_dict.get(feature["properties"]["id"], -99) for feature in municipalities_data["features"]
        ]

        return (
            options,
            slider_style,
            create_figure(
                aggregated_responses, [feature["properties"]["id"] for feature in municipalities_data["features"]]
            ),
        )

    # Define the function to create an empty map figure when logging in
    def create_empty_map_figure():
        fig = go.Figure()

        # Add the country layer (Switzerland)
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

        # Layout settings for the empty map
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

    # Function to create the map figure
    def create_figure(variable_values, communes):
        unique_values = [v for v in variable_values if isinstance(v, (int, float)) and v != -99 and not np.isnan(v)]
        num_unique_values = len(set(unique_values))

        if num_unique_values == 99:  # to modify when fixed the issue with the discrete color scale
            custom_colorscale = {
                -99: "darkgray",  # Voluntary no response
                np.nan: "lightgray",  # Exited survey
                0: "rgb(255,247,251)",
                1: "rgb(236,231,242)",
                2: "rgb(208,209,230)",
                3: "rgb(166,189,219)",
                4: "rgb(116,169,207)",
                5: "rgb(54,144,192)",
                6: "rgb(5,112,176)",
                7: "rgb(4,90,141)",
                8: "rgb(2,56,88)",
            }
        else:
            custom_colorscale = "Viridis"

        fig = go.Figure()

        # Add the country layer (Switzerland)
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

        # Add the municipalities layer with dynamic values and color scale
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=municipalities_data,
                locations=communes,
                z=variable_values,
                colorscale=custom_colorscale,
                featureidkey="properties.id",
                name="Municipalities",
                hoverinfo="text",
                text=[
                    f"{feature['properties']['name']}: "
                    f"{'Exited Survey' if np.isnan(value) else ('Voluntary no response' if value == -99 else ('No opinion' if value == 99 else value))}"
                    for value, feature in zip(variable_values, municipalities_data["features"])
                ],
                colorbar=dict(
                    title="Values",
                    thickness=25,
                    x=1.05,
                    y=0.5,
                    tickvals=[-99, float("nan")] + list(range(0, 8)),
                    ticktext=["Voluntary No Response", "Exited Survey"] + [str(i) for i in range(0, 8)],
                ),
                showscale=True,
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

        # Layout settings for the map
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
