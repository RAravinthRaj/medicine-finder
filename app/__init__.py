import os

from flask import Flask
from dotenv import load_dotenv

from .controllers import register_blueprints
from .extensions import db, login_manager
from .seed import seed_data


def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder="../templates")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///medicines.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    register_blueprints(app)

    with app.app_context():
        db.create_all()
        seed_data()

    return app
