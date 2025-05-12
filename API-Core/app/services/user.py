# Business logic for user
from ..models.user import User
from ..extensions import db

def create_user_service(username, email, password ):
    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return user

