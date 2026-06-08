"""Fabrique de moteurs selon la méthode choisie."""

from datetime import date

from app.engines.billings import MoteurBillings
from app.engines.cler import MoteurCLER
from app.engines.sensiplan import MoteurSensiplan


def creer_moteur(methode: str, profil=None, cycle_debut: date | None = None, intention: str = "eviter"):
  if methode == "billings":
    return MoteurBillings(profil, cycle_debut, intention)
  if methode == "cler":
    return MoteurCLER(profil, cycle_debut, intention)
  return MoteurSensiplan(profil, cycle_debut, intention)
