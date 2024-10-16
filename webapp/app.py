from logging import FileHandler, Formatter
import logging


from flask import abort, Flask, render_template, Blueprint
from flask_sqlalchemy import SQLAlchemy

from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from dash import callback_context, Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from map import map_bp

if __name__ == "__main__":
    from database import Base, Canton, Commune, District, QuestionGlobal, QuestionPerSurvey, Survey
else:
    from webapp.database import Base


def create_app():
    app = Flask(__name__)
    app.config.from_object("config")
    db = SQLAlchemy(app, model_class=Base)

    with app.app_context():
        db.reflect()

    # Error handlers
    @app.errorhandler(403)
    def error_forbidden(error):
        return render_template("errors/40x.html"), 403

    @app.errorhandler(404)
    def error_not_found(error):
        return render_template("errors/40x.html"), 404

    @app.errorhandler(500)
    def error_internal(error):
        return render_template("errors/50x.html"), 500

    # Homepage, with default visualisation
    @app.route("/")
    def home():
        return render_template("home.html")

    # Links to other parts of the website
    @app.route("/about")
    def about():
        return render_template("placeholder.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("placeholder.html")

    # Survey
    @app.route("/survey/new", methods=("GET", "POST"))
    def survey_new():
        pass

    @app.route("/survey/list")
    def survey_list():
        surveys = db.session.execute(db.select(Survey).order_by(Survey.year)).scalars()
        return render_template("surveys/survey_list.html", liste=surveys)

    @app.route("/survey/<uid>")
    def survey_show(uid):
        survey = db.session.execute(db.select(Survey).where(Survey.uid == uid)).one_or_none()
        questions = db.session.execute(
            db.select(QuestionPerSurvey).where(QuestionPerSurvey.survey_uid == uid)
        ).scalars()
        if survey:
            return render_template("surveys/survey_show.html", item=survey[0], liste=questions)
        else:
            abort(404)

    # Questions
    @app.route("/questions/qps/list")
    def qps_list():
        qps = db.session.execute(db.select(QuestionPerSurvey)).scalars()
        return render_template("questions/qps_list.html", liste=qps)

    @app.route("/questions/qg/list")
    def qg_list():
        qg = db.session.execute(db.select(QuestionGlobal)).scalars()
        return render_template("questions/qg_list.html", liste=qg)

    # Answers

    # Places
    @app.route("/places/canton/list")
    def canton_list():
        cantons = db.session.execute(db.select(Canton).order_by(Canton.code)).scalars()
        return render_template("places/canton_list.html", liste=cantons)

    @app.route("/places/district/list")
    def district_list():
        districts = db.session.execute(db.select(District).order_by(District.code)).scalars()
        return render_template("places/district_list.html", liste=districts)

    @app.route("/places/commune/list")
    def commune_list():
        communes = db.session.execute(db.select(Commune).order_by(Commune.code)).scalars()
        return render_template("places/commune_list.html", liste=communes)

    @app.route("/config")
    def config():  # TODO
        return render_template("placeholder.html")
    
    # register the blueprints for dash
    # je comprends pas trop, ça ne s'affiche pas sur http://localhost:8888/map
    app.register_blueprint(map_bp, url_prefix="/map")

    if not app.debug:
        file_handler = FileHandler("error.log")
        file_handler.setFormatter(Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
        app.logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.info("errors")

    return app

# Default port:
if __name__ == "__main__":
    from config import SERVER_HOST, SERVER_PORT

    app = create_app()
    app.run(host=SERVER_HOST, port=SERVER_PORT)
