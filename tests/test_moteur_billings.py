from datetime import date, timedelta

from app.engines.base import Feu, Phase
from app.engines.billings import MoteurBillings
from app.engines.glaire import detecter_pic_billings
from tests.factories import ObsMock


class TestBillings:
  def test_jours_secs_apres_regles(self):
    debut = date(2026, 1, 1)
    obs = [
      ObsMock(debut, saignement="regles"),
      ObsMock(debut + timedelta(days=1), saignement="regles"),
      ObsMock(debut + timedelta(days=2), glaire_sensation="seche", glaire_aspect="rien"),
      ObsMock(debut + timedelta(days=3), glaire_sensation="seche", glaire_aspect="rien"),
    ]
    moteur = MoteurBillings(cycle_debut=debut, intention="eviter")
    statuts = {s.date: s for s in moteur.calculer_statuts(obs)}
    assert statuts[debut + timedelta(days=3)].feu == Feu.VERT

  def test_glaire_fertile_rouge(self):
    debut = date(2026, 1, 1)
    obs = [
      ObsMock(debut, saignement="regles"),
      ObsMock(debut + timedelta(days=5), glaire_sensation="humide"),
    ]
    moteur = MoteurBillings(cycle_debut=debut, intention="eviter")
    statut = moteur.calculer_statuts(obs)[-1]
    assert statut.phase == Phase.FERTILE
    assert statut.feu == Feu.ROUGE

  def test_union_veille_glaire_non_fiable(self):
    debut = date(2026, 1, 1)
    obs = [
      ObsMock(debut, union=True, glaire_sensation="seche"),
      ObsMock(debut + timedelta(days=1), glaire_sensation="humide"),
    ]
    moteur = MoteurBillings(cycle_debut=debut, intention="eviter")
    statut = moteur.calculer_statuts(obs)[-1]
    assert statut.feu == Feu.ORANGE
    assert any("Union la veille" in m for m in statut.messages)

  def test_pic_billings_3e_jour(self):
    debut = date(2026, 1, 1)
    obs = [ObsMock(debut + timedelta(days=i), glaire_sensation="humide") for i in range(9)]
    obs[5] = ObsMock(debut + timedelta(days=5), glaire_sensation="mouillee_glissante")
    obs[6] = ObsMock(debut + timedelta(days=6), glaire_sensation="seche", glaire_aspect="rien")
    pic = detecter_pic_billings(obs)
    assert pic == debut + timedelta(days=5)
    moteur = MoteurBillings(cycle_debut=debut, intention="eviter")
    statuts = {s.date: s for s in moteur.calculer_statuts(obs)}
    # Pic J5 + 3 jours → infertilité confirmée le soir du J8
    assert statuts[debut + timedelta(days=8)].phase == Phase.POSTOVULATOIRE
