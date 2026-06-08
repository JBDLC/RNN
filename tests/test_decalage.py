from datetime import time

import pytest

from app.models import Observation, User
from app.services.decalage import (
  appliquer_traitement_temperature,
  delta_minutes,
  mediane_heures,
  resoudre_heure_reference,
)


def _user(mode="exclusion", seuil=60, heure_ref=None):
  user = User(email="x@y.z", password_hash="x")
  user.mode_decalage = mode
  user.seuil_decalage_min = seuil
  user.heure_reference = heure_ref
  return user


def _obs(temp=36.5, heure=None, obs_id=1):
  obs = Observation(cycle_id=1, date=None)
  obs.id = obs_id
  obs.temp_brute = temp
  obs.heure_prise = heure
  return obs


class TestDeltaMinutes:
  def test_meme_heure(self):
    assert delta_minutes(time(7, 0), time(7, 0)) == 0

  def test_retard(self):
    assert delta_minutes(time(8, 30), time(7, 0)) == 90

  def test_avance(self):
    assert delta_minutes(time(6, 0), time(7, 0)) == -60


class TestMedianeHeures:
  def test_mediane_impaire(self):
    heures = [time(7, 0), time(7, 30), time(6, 30)]
    assert mediane_heures(heures) == time(7, 0)

  def test_liste_vide(self):
    assert mediane_heures([]) is None


class TestResoudreHeureReference:
  def test_heure_utilisateur_prioritaire(self):
    user = _user(heure_ref=time(7, 15))
    obs = [_obs(heure=time(8, 0))]
    assert resoudre_heure_reference(user, obs) == time(7, 15)

  def test_mediane_auto(self):
    user = _user(heure_ref=None)
    obs = [_obs(heure=time(7, 0)), _obs(heure=time(7, 30), obs_id=2)]
    assert resoudre_heure_reference(user, obs) == time(7, 15)


class TestAppliquerTraitement:
  def test_exclusion_point_decale(self):
    user = _user(mode="exclusion", seuil=60, heure_ref=time(7, 0))
    obs = _obs(temp=36.5, heure=time(8, 30))
    appliquer_traitement_temperature(obs, user, [])
    assert obs.douteux is True
    assert obs.motif_doute == "prise_decalee"
    assert obs.temp_corrigee is None

  def test_exclusion_dans_tolerance(self):
    user = _user(mode="exclusion", seuil=60, heure_ref=time(7, 0))
    obs = _obs(temp=36.5, heure=time(7, 30))
    appliquer_traitement_temperature(obs, user, [])
    assert obs.douteux is False

  def test_correction_retard(self):
    user = _user(mode="correction", heure_ref=time(7, 0))
    obs = _obs(temp=36.50, heure=time(9, 0))
    appliquer_traitement_temperature(obs, user, [])
    assert obs.temp_corrigee == pytest.approx(36.30)
    assert obs.douteux is False

  def test_correction_avance(self):
    user = _user(mode="correction", heure_ref=time(7, 0))
    obs = _obs(temp=36.50, heure=time(6, 0))
    appliquer_traitement_temperature(obs, user, [])
    assert obs.temp_corrigee == pytest.approx(36.60)

  def test_douteux_manuel(self):
    user = _user(mode="exclusion", heure_ref=time(7, 0))
    obs = _obs(temp=36.5, heure=time(7, 0))
    appliquer_traitement_temperature(
      obs, user, [], douteux_manuel=True, motif_manuel="fievre"
    )
    assert obs.douteux is True
    assert obs.motif_doute == "fievre"
