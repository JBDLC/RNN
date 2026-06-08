from app import create_app
from app.auth.emails import is_mail_configured, send_verification_email
from app.extensions import db
from app.models import User


def test_mail_non_configure_ne_bloque_pas():
  app = create_app()
  app.config.update({
    "TESTING": True,
    "MAIL_SERVER": "localhost",
    "MAIL_USERNAME": None,
    "MAIL_PASSWORD": None,
  })
  with app.app_context():
    assert is_mail_configured() is False
    user = User(email="test@example.com")
    user.verification_token = "abc"
    assert send_verification_email(user) is False


def test_mail_configure_detecte():
  app = create_app()
  app.config.update({
    "TESTING": True,
    "MAIL_SERVER": "smtp.gmail.com",
    "MAIL_USERNAME": "a@b.com",
    "MAIL_PASSWORD": "secret",
    "MAIL_SUPPRESS_SEND": True,
  })
  with app.app_context():
    assert is_mail_configured() is True
