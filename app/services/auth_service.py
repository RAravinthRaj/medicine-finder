import bcrypt

from ..extensions import db
from ..models import User


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def create_user(email, password, is_admin=False):
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    user = User(email=email, password=hashed_password, is_admin=is_admin)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if user and bcrypt.checkpw(password.encode("utf-8"), user.password):
        return user
    return None
