from flask import Blueprint, render_template
from flask_login import current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/", endpoint="index")
def index():
    return render_template("index.html", user=current_user)
