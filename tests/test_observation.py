from datetime import date, datetime

import pytest

from app import create_app
from app.extensions import db
from app.models import Cycle, Observation, ProfilPersonnel, User


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


def _user_complet():
  user = User(email="couple@example.com", email_verified=True)
  user.set_password("password123")
  user.methode = "sensiplan"
  user.intention = "eviter"
  user.mode_decalage = "exclusion"
  user.seuil_decalage_min = 60
  user.avertissement_lu = True
  user.onboarding_complete = True
  db.session.add(user)
  db.session.add(ProfilPersonnel(user=user))
  db.session.flush()
  cycle = Cycle(user_id=user.id, date_debut_regles=date.today())
  db.session.add(cycle)
  db.session.commit()
  return user


def test_saisie_observation_thermique(client):
  user = _user_complet()
  client.post("/auth/login", data={"email": user.email, "password": "password123"})

  response = client.post("/jour", data={
    "date_obs": date.today().isoformat(),
    "temp_brute": "36.52",
    "heure_prise": "07:00",
    "glaire_sensation": "seche",
    "glaire_aspect": "rien",
    "saignement": "rien",
    "union": False,
  }, follow_redirects=True)

  assert response.status_code == 200
  obs = Observation.query.first()
  assert obs is not None
  assert obs.temp_brute == pytest.approx(36.52)
  assert obs.douteux is False


def test_saisie_billings_sans_temperature(client, app):
  user = _user_complet()
  user.methode = "billings"
  db.session.commit()

  client.post("/auth/login", data={"email": user.email, "password": "password123"})

  response = client.post("/jour", data={
    "date_obs": date.today().isoformat(),
    "glaire_sensation": "humide",
    "glaire_aspect": "cremeuse",
    "saignement": "rien",
    "union": False,
  }, follow_redirects=True)

  assert response.status_code == 200
  obs = Observation.query.first()
  assert obs.temp_brute is None
