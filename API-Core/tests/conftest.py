import uuid

import pytest
from app import create_app
from app.extensions import db
from app.models.user import AccountStatus, User


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