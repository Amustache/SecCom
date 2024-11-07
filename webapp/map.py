import os


from dash import ALL, ctx, Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from flask import Flask, render_template_string
from flask_babel import _
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import dash_bootstrap_components as dbc


from webapp.config import BASEDIR, DB_URI, DEMO
from webapp.database import Answer, QuestionGlobal, QuestionPerSurvey, Survey
from webapp.map_helpers import DF_2023, DF_QUESTIONS, fig_map_with_data, fig_switzerland_empty


LOCALE = "en"


def create_dash_app(flask_server: Flask, url_path="/map"):
    # Create a Dash app instance with Bootstrap styling
    dash_app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        server=flask_server,
        url_base_pathname=url_path,
    )
    # dash_app.config.suppress_callback_exceptions = True  # Suppress callback exceptions for better error handling

    ENGINE = create_engine(DB_URI, echo=True)
    with Session(ENGINE) as session:
        if DEMO:
            db_years = [1988, 1994, 1998, 2005, 2009, 2017, 2023]
        else:
            db_years = list(session.execute(session.query(Survey.year)).scalars())
        db_years = sorted(db_years)
        DB_QUESTIONS_GLOBAL = list(session.execute(session.query(QuestionGlobal)).scalars())
        # TODO réponses

    # Define the layout of the app, including dropdowns, map, and slider
    # Map display component
    layout_card = dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                id="map-graph",
                figure=fig_switzerland_empty(),
                style={
                    "height": "75vh",
                },
            )
        )
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
            ]
        ),
        className="mb-4",
    )
    layout_questions = dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Checklist(
                                id="global-question-switch",
                                options=[{"label": "Global questions", "value": 1}],
                                value=[1],
                                switch=True,
                                className="text-start",
                            )
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id="years-dropdown",
                                options=[{"label": str(year), "value": str(year)} for year in db_years],
                                value=None,
                                clearable=True,
                                className="invisible",
                            )
                        ),
                    ],
                    className="card-text mb-3",
                ),
                dbc.Row(
                    dbc.Col(
                        html.Em(_("Please note that some of the data is incomplete/still being worked on.")),
                        className="card-text mb-3",
                    )
                ),
                dbc.Row(
                    dbc.Col(
                        dcc.Slider(
                            db_years[0],
                            db_years[-1],
                            id="years-slider",
                            step=None,
                            marks=None,
                            value=db_years[-1],
                        ),
                        className="card-text mb-3",
                    ),
                    id="years-slider-container",
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.ListGroup([], id="questions", style={"overflow-y": "auto", "max-height": "300px"}),
                        className="card-text",
                    )
                ),
            ]
        )
    )

    dash_app.layout = html.Div(
        dbc.Row(
            [
                dbc.Col(layout_card, width=8),
                dbc.Col([layout_infos, layout_questions], width=4),
            ]
        )
    )

    @dash_app.callback(
        Output("questions", "children"),
        Input("global-question-switch", "value"),
        Input("years-dropdown", "value"),
    )
    def update_question_list(switch_value, year):
        if switch_value:
            questions_list = list(
                dbc.ListGroupItem(
                    getattr(
                        question,
                        f"text_{LOCALE}",
                    ),
                    id={"type": "list-group-item", "index": question.uid},
                    n_clicks=0,
                    action=True,
                )
                for question in DB_QUESTIONS_GLOBAL
            )
        else:
            if year:
                dft = DF_QUESTIONS[DF_QUESTIONS["year"] == int(year)]
                questions_list = list(
                    dbc.ListGroupItem(
                        getattr(
                            question,
                            f"text_{LOCALE}",
                        ),
                        id={"type": "list-group-item", "index": question.code},
                        n_clicks=0,
                        action=True,
                    )
                    for index, question in dft.iterrows()
                )
            else:
                questions_list = list()
            #     else:
            #         with Session(ENGINE) as session:
            #             db_survey = session.execute(session.query(Survey).where(Survey.year == int(year))).one_or_none()
            #             if db_survey:
            #                 db_questions = [question for question in db_survey[0].questions]
            #             else:
            #                 print("Warning: no survey in database")
            #                 db_questions = []
            #             questions_list = [
            #                 dbc.ListGroupItem(
            #                     getattr(
            #                         question,
            #                         f"text_{LOCALE}",
            #                     ),
            #                     id={"type": "list-group-item", "index": question.uid},
            #                     n_clicks=0,
            #                     action=True,
            #                 )
            #                 for question in db_questions
            #             ]
            # else:
            #     print("Warning: no year")
            #     questions_list = list()
            # print(questions_list)
        return questions_list

    @dash_app.callback(
        Output("years-dropdown", "className"),
        Output("years-dropdown", "value"),
        Output("years-slider-container", "className"),
        Output("years-slider", "marks"),
        Output("years-slider", "value"),
        Input("global-question-switch", "value"),
        Input("years-dropdown", "value"),
    )
    def update_years(switch_value, year):
        """
        Update the list of questions and the dropbox when the question global switch is used and/or a year selected.
        """
        if switch_value:  # Global questions
            return "invisible", None, "visible", {year: str(year) for year in db_years}, db_years[-1]
        else:  # Per survey questions
            return "visible", year, "invisible", None, None

    @dash_app.callback(
        Output("map-graph", "figure"),
        # Output({"type": "list-group-item", "index": ALL}, "active"),
        # Output({"type": "list-group-item", "index": ALL}, "n_clicks"),
        Input("global-question-switch", "value"),
        Input({"type": "list-group-item", "index": ALL}, "n_clicks"),
    )
    def question_update(switch_value, list_group_items):
        """
        Update the map when a question is selected.
        """
        if not ctx.triggered:
            raise PreventUpdate
        if any(list_group_items):
            # print(f"Clicked on Item {ctx.triggered_id.index}")
            if switch_value:  # Global questions
                return fig_switzerland_empty()
            else:  # Per survey questions
                print(f"Clicked on Item {ctx.triggered_id.index}")

                if DEMO:
                    if ctx.triggered_id.index in DF_QUESTIONS["code"].values:
                        chosen_question = ctx.triggered_id.index
                    else:
                        chosen_question = None
                else:
                    chosen_question = session.execute(
                        session.query(QuestionPerSurvey).where(QuestionPerSurvey.uid == int(ctx.triggered_id.index))
                    ).one_or_none()
                    if chosen_question:
                        chosen_question = chosen_question[0].code

                if chosen_question:
                    print(f"Question: {chosen_question}")

                    return fig_map_with_data(
                        DF_2023, chosen_question
                    )  # , list_group_items, [0] * len(list_group_items)
                else:
                    print(f"NO SUCH QUESTION: {ctx.triggered_id.index}")

                # db_answers = session.execute(session.query(Answer).where(Answer.question_uid == 2325)).scalars()
                # print([answer.value for answer in db_answers])
                # print("done")
        else:
            return fig_switzerland_empty()  # , list_group_items, [0] * len(list_group_items)

    with flask_server.app_context(), flask_server.test_request_context():
        with open(os.path.join(BASEDIR, "templates", "public", "map.html"), "r") as f:
            html_body = render_template_string(f.read())

            for comment in ["app_entry", "config", "scripts", "renderer"]:
                html_body = html_body.replace(f"<!-- {comment} -->", "{%" + comment + "%}")

            dash_app.index_string = html_body

    return dash_app.server
