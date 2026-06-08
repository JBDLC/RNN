from datetime import date, timedelta

from app.engines.cler import MoteurCLER
from app.models import ProfilPersonnel
from tests.factories import ObsMock


class TestCLER:
  def test_debut_fertilite_plus_court_moins_20(self):
    debut = date(2026, 1, 1)
    profil = ProfilPersonnel(user_id=1, cycle_min=26)
    obs = [ObsMock(debut + timedelta(days=i), temp=36.4) for i in range(5)]
    moteur = MoteurCLER(profil_personnel=profil, cycle_debut=debut, intention="eviter")
    debut_f, fin_f = moteur.fenetre_fertile(obs)
    assert debut_f == debut + timedelta(days=6)  # 26 - 20 = jour 6

  def test_donnees_courbe(self):
    debut = date(2026, 1, 1)
    temps = [36.40, 36.35, 36.38, 36.36, 36.37, 36.39, 36.55, 36.58, 36.65]
    obs = [ObsMock(debut + timedelta(days=i), temp=t) for i, t in enumerate(temps)]
    moteur = MoteurCLER(cycle_debut=debut)
    donnees = moteur.donnees_courbe(obs)
    assert donnees["ligne_reference"] == 36.40
    assert len(donnees["indices_points_hauts"]) == 3
