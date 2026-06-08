"""Moteur CLER — méthode des trois points hauts."""

from datetime import date, timedelta

from app.engines.base import StatutJour
from app.engines.glaire import (
  date_fin_post_ovulatoire_glaire,
  detecter_pic_glaire,
  detecter_premier_signe_glaire,
)
from app.engines.sensiplan import MoteurSensiplan
from app.engines.thermique import detecter_hausse_thermique
from app.engines.utils import cycle_min_effectif


class MoteurCLER(MoteurSensiplan):
  """
  CLER : proche de Sensiplan.
  Début de fertilité = min(plus_court_cycle − 20, apparition glaire).
  Fin = max(3e point haut, 3e jour après sommet de glaire).
  """

  def _analyse_cycle(self, observations: list) -> dict:
    thermique = detecter_hausse_thermique(observations)
    pic = detecter_pic_glaire(observations)
    fin_glaire = date_fin_post_ovulatoire_glaire(pic)

    fin_fertile = None
    if thermique.date_confirmation and fin_glaire:
      fin_fertile = max(thermique.date_confirmation, fin_glaire)

    premier_glaire = detecter_premier_signe_glaire(observations)
    cycle_min = cycle_min_effectif(self.profil_personnel)
    debut_theorique = None
    if self.cycle_debut:
      debut_theorique = self.cycle_debut + timedelta(days=cycle_min - 20)

    debut_fertile = None
    candidats = [d for d in (premier_glaire, debut_theorique) if d]
    if candidats:
      debut_fertile = min(candidats)

    return {
      "thermique": thermique,
      "pic": pic,
      "fin_fertile": fin_fertile,
      "debut_fertile": debut_fertile,
      "regle_5": False,
      "fin_regles": self._fin_regles(observations),
    }

  def _statut_jour(self, obs, analyse: dict) -> StatutJour:
    statut = super()._statut_jour(obs, analyse)
    messages = [m for m in statut.messages if "Règle des 5 jours" not in m]
    if analyse["debut_fertile"] and self.cycle_debut:
      cycle_min = cycle_min_effectif(self.profil_personnel)
      messages.append(
        f"CLER : début de fertilité au plus tôt J{max(1, cycle_min - 19)} "
        f"(cycle le plus court − 20) ou à la première glaire."
      )
    return StatutJour(
      date=statut.date,
      phase=statut.phase,
      feu=statut.feu,
      confiance=statut.confiance,
      messages=messages,
    )
