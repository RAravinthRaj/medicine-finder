from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..services.auth_service import authenticate_user, create_user, get_user_by_email
from ..services.order_service import get_user_orders

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"], endpoint="signup")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if get_user_by_email(email):
            flash("Email already registered.", "error")
            return redirect(url_for("auth.signup"))

        create_user(email, password)
        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = authenticate_user(email, password)

        if user:
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("main.index"))

        flash("Invalid email or password.", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout", endpoint="logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile", endpoint="profile")
@login_required
def profile():
    orders = get_user_orders(current_user.id)
    return render_template("profile.html", orders=orders)
