from flask import flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import login_required, login_user, logout_user


from webapp import db
from webapp.main import bp
from webapp.models.User import User


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.session.execute(db.select(User).where(User.username == username)).one_or_none()

        if user and user[0].check_password(password):
            login_user(user[0])
            flash(_("Logged in successfully."), "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("home"))
        else:
            flash(_("Problem while loging in."), "warning")

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))
