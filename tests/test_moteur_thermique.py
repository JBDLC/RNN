from datetime import date

from app.engines.base import Feu, Phase
from app.engines.thermique import detecter_hausse_thermique
from app.engines.sensiplan import MoteurSensiplan
from tests.factories import ObsMock, serie_obs


class TestHausseThermique:
  def test_cas_nominal_3_au_dessus_de_6(self):
    debut = date(2026, 1, 1)
    temps = [36.40, 36.35, 36.38, 36.36, 36.37, 36.39, 36.55, 36.58, 36.65]
    obs = serie_obs(debut, *temps)
    resultat = detecter_hausse_thermique(obs)
    assert resultat.date_confirmation == date(2026, 1, 9)
    assert resultat.ligne_reference == 36.40

  def test_point_douteux_exclu(self):
    debut = date(2026, 1, 1)
    obs = serie_obs(
      debut,
      36.40, 36.35, 36.38, 36.36, 36.37, 36.39,
      {"temp": 39.0, "douteux": True, "motif_doute": "fievre"},
      36.55, 36.58, 36.65,
    )
    resultat = detecter_hausse_thermique(obs)
    assert resultat.date_confirmation == date(2026, 1, 10)

  def test_regle_exception_4e_point(self):
    debut = date(2026, 1, 1)
    temps = [36.40, 36.35, 36.38, 36.36, 36.37, 36.39, 36.55, 36.58, 36.50, 36.56]
    obs = serie_obs(debut, *temps)
    resultat = detecter_hausse_thermique(obs)
    assert resultat.date_confirmation == date(2026, 1, 10)
    assert len(resultat.indices_points_hauts) == 4


class TestSensiplan:
  def test_double_verrou_post_ovulatoire(self):
    debut = date(2026, 1, 1)
    obs = []
    for i, t in enumerate([36.40, 36.35, 36.38, 36.36, 36.37, 36.39, 36.55, 36.58, 36.65]):
      obs.append(ObsMock(debut + __import__("datetime").timedelta(days=i), temp=t))
    # Glaire fertile + pic au jour 12, régression jour 13
    from datetime import timedelta
    for j in range(10, 13):
      obs.append(ObsMock(debut + timedelta(days=j), glaire_aspect="cremeuse"))
    obs.append(ObsMock(debut + timedelta(days=12), glaire_aspect="filante_transparente"))
    obs.append(ObsMock(debut + timedelta(days=13), glaire_sensation="seche", glaire_aspect="rien"))
    for k in range(14, 20):
      obs.append(ObsMock(debut + timedelta(days=k), temp=36.65 + (k - 14) * 0.01))

    moteur = MoteurSensiplan(cycle_debut=debut, intention="eviter")
    statuts = moteur.calculer_statuts(obs)
    par_date = {s.date: s for s in statuts}

    # Après double verrou (max thermique J9, pic J12 + 3 = J15)
    assert par_date[date(2026, 1, 16)].phase == Phase.POSTOVULATOIRE
    assert par_date[date(2026, 1, 16)].feu == Feu.VERT

  def test_fenetre_fertile_avec_glaire(self):
    debut = date(2026, 1, 1)
    from datetime import timedelta
    obs = [ObsMock(debut + timedelta(days=i), temp=36.4) for i in range(5)]
    obs.append(ObsMock(debut + timedelta(days=5), glaire_sensation="humide"))
    moteur = MoteurSensiplan(cycle_debut=debut, intention="eviter")
    statut = moteur.calculer_statuts(obs)[-1]
    assert statut.phase == Phase.FERTILE
    assert statut.feu == Feu.ROUGE
