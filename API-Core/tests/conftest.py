import uuid

import pytest
from app import create_app
from app.extensions import db
import jwt
from app.models.user import AccountStatus, User
from flask_jwt_extended import create_access_token
from datetime import timedelta



@pytest.fixture(scope='module')
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['DEBUG'] = True  # Add this
    app.config['PROPAGATE_EXCEPTIONS'] = True  # Add this
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        pass
         #db.drop_all()

@pytest.fixture(scope='module')
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture(scope='module')
def db_fixture(app):
    """Provide database context, renaming to avoid conflict with db function"""
    with app.app_context():
        yield db




@pytest.fixture
def test_user(db_fixture):
    user = User(
        email=f"test{uuid.uuid4()}@example.com",
        password="testpassword123",
        first_name="Test",
        last_name="User",
        account_status=AccountStatus.ACTIVE
    )
    db_fixture.session.add(user)
    db_fixture.session.commit()
    return user

@pytest.fixture
def inactive_user(db_fixture):
    db_fixture.session.query(User).filter_by(email="inactive@example.com").delete()
    db_fixture.session.commit()

    user = User(
        email="inactive@example.com",
        password="testpassword123",
        first_name="Inactive",
        last_name="User",
        account_status=AccountStatus.INACTIVE
    )
    db_fixture.session.add(user)
    db_fixture.session.commit()
    return user


@pytest.fixture
def auth_headers(test_user, app):
    with app.app_context():
        token = create_access_token(identity=str(test_user.user_id))
        decoded = jwt.decode(
            token,
            app.config['JWT_SECRET_KEY'],
            algorithms=["HS256"]
        )
        csrf_token = decoded.get('csrf', '')
        return {
            'Authorization': f'Bearer {token}',
            'X-CSRF-Token': csrf_token
        }

@pytest.fixture
def expired_token(test_user):
    """Generate expired token"""
    return create_access_token(
        identity=str(test_user.user_id),
        expires_delta=timedelta(seconds=-1)
    )