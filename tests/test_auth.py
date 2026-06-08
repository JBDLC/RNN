import pytest

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture
def app():
  app = create_app()
  app.config.update({
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "WTF_CSRF_ENABLED": False,
    "MAIL_SUPPRESS_SEND": True,
  })
  with app.app_context():
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()


@pytest.fixture
def client(app):
  return app.test_client()


def test_register_creates_user(client):
  response = client.post("/auth/register", data={
    "email": "test@example.com",
    "password": "motdepasse123",
    "password_confirm": "motdepasse123",
    "accept_disclaimer": True,
  }, follow_redirects=True)

  assert response.status_code == 200
  user = User.query.filter_by(email="test@example.com").first()
  assert user is not None
  assert user.email_verified is False
  assert user.verification_token is not None


def test_login_blocked_until_verified(client):
  client.post("/auth/register", data={
    "email": "test@example.com",
    "password": "motdepasse123",
    "password_confirm": "motdepasse123",
    "accept_disclaimer": True,
  })

  response = client.post("/auth/login", data={
    "email": "test@example.com",
    "password": "motdepasse123",
  }, follow_redirects=True)

  text = response.data.decode("utf-8").lower()
  assert "pas encore" in text or "vérifiée" in text


def test_skip_email_verification(client, app):
  app.config["SKIP_EMAIL_VERIFICATION"] = True
  client.post("/auth/register", data={
    "email": "skip@example.com",
    "password": "motdepasse123",
    "password_confirm": "motdepasse123",
    "accept_disclaimer": True,
  })
  user = User.query.filter_by(email="skip@example.com").first()
  assert user.email_verified is True

  response = client.post("/auth/login", data={
    "email": "skip@example.com",
    "password": "motdepasse123",
  }, follow_redirects=True)
  assert response.status_code == 200
  text = response.data.decode("utf-8").lower()
  assert "déconnexion" in text


def test_verify_email_allows_login(client):
  client.post("/auth/register", data={
    "email": "test@example.com",
    "password": "motdepasse123",
    "password_confirm": "motdepasse123",
    "accept_disclaimer": True,
  })
  user = User.query.filter_by(email="test@example.com").first()
  token = user.verification_token

  client.get(f"/auth/verify/{token}", follow_redirects=True)

  response = client.post("/auth/login", data={
    "email": "test@example.com",
    "password": "motdepasse123",
  }, follow_redirects=True)

  assert response.status_code == 200
  text = response.data.decode("utf-8").lower()
  assert "déconnexion" in text
