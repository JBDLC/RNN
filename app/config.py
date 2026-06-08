import os
from datetime import timedelta


class Config:
  """Configuration de base de l'application."""

  SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-a-changer")
  SQLALCHEMY_TRACK_MODIFICATIONS = False

  # SQLite en local, PostgreSQL sur Render via DATABASE_URL
  database_url = os.environ.get("DATABASE_URL", "sqlite:///rnn.db")
  if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
  SQLALCHEMY_DATABASE_URI = database_url

  # E-mail (validation de compte)
  MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
  MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
  MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
  MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
  MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
  MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@rnn-app.local")
  MAIL_TIMEOUT = int(os.environ.get("MAIL_TIMEOUT", 10))
  # Sur Render, RENDER_EXTERNAL_URL est injecté automatiquement (ex. https://rnn-app.onrender.com)
  BASE_URL = os.environ.get(
    "BASE_URL",
    os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5000"),
  )

  # Durée de validité du lien de vérification e-mail
  EMAIL_VERIFY_TOKEN_MAX_AGE = timedelta(hours=48)

  # Test / Render gratuit (SMTP bloqué) : contourne la validation e-mail
  SKIP_EMAIL_VERIFICATION = os.environ.get("SKIP_EMAIL_VERIFICATION", "false").lower() == "true"

  # Session
  REMEMBER_COOKIE_DURATION = timedelta(days=30)
  _on_render = os.environ.get("RENDER") == "true"
  SESSION_COOKIE_SECURE = _on_render or os.environ.get("FLASK_ENV") == "production"
  SESSION_COOKIE_HTTPONLY = True
  SESSION_COOKIE_SAMESITE = "Lax"
