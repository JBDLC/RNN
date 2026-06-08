from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from enum import Enum


class Phase(Enum):
  PREOVULATOIRE = "preovulatoire"
  FERTILE = "fertile"
  POSTOVULATOIRE = "postovulatoire"
  INDETERMINEE = "indeterminee"


class Feu(Enum):
  VERT = "vert"
  ORANGE = "orange"
  ROUGE = "rouge"


@dataclass
class StatutJour:
  """Résultat de calcul pour un jour donné."""

  date: date
  phase: Phase
  feu: Feu
  confiance: str  # "haute" | "basse"
  messages: list[str]


class MoteurMethode(ABC):
  """Interface commune. Chaque méthode implémente sa propre logique."""

  def __init__(self, profil_personnel=None):
    self.profil_personnel = profil_personnel

  @abstractmethod
  def calculer_statuts(self, observations: list) -> list[StatutJour]:
    """Calcule le statut pour chaque observation du cycle."""

  @abstractmethod
  def fenetre_fertile(self, observations: list) -> tuple:
    """Retourne (date_debut, date_fin) de la fenêtre fertile estimée."""
