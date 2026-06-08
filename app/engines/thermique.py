"""Détection de la hausse thermique — règle 3 au-dessus de 6 (Sensiplan / CLER)."""

from dataclasses import dataclass, field
from datetime import date

from app.engines.utils import observations_triees, temp_thermique

SEUIL_HAUT_C = 0.2


@dataclass
class ResultatThermique:
  date_confirmation: date | None = None
  ligne_reference: float | None = None
  indices_points_hauts: list[int] = field(default_factory=list)
  indices_six_basses: list[int] = field(default_factory=list)
  serie: list[tuple[date, float]] = field(default_factory=list)


def serie_temperatures(observations: list) -> list[tuple[date, float]]:
  serie = []
  for obs in observations_triees(observations):
    temp = temp_thermique(obs)
    if temp is not None:
      serie.append((obs.date, temp))
  return serie


def detecter_hausse_thermique(observations: list) -> ResultatThermique:
  """
  6 températures basses consécutives → ligne de référence = plus haute des 6.
  3 consécutives au-dessus ; la 3e ≥ +0,2 °C ou 4e simplement au-dessus.
  """
  serie = serie_temperatures(observations)
  n = len(serie)
  resultat = ResultatThermique(serie=serie)

  if n < 9:
    return resultat

  for i in range(n - 5):
    ligne_ref = max(serie[k][1] for k in range(i, i + 6))

    for j in range(i + 6, n - 2):
      if not all(serie[j + k][1] > ligne_ref for k in range(3)):
        continue

      if serie[j + 2][1] >= ligne_ref + SEUIL_HAUT_C:
        resultat.date_confirmation = serie[j + 2][0]
        resultat.ligne_reference = ligne_ref
        resultat.indices_six_basses = list(range(i, i + 6))
        resultat.indices_points_hauts = [j, j + 1, j + 2]
        return resultat

      if j + 3 < n and serie[j + 3][1] > ligne_ref:
        resultat.date_confirmation = serie[j + 3][0]
        resultat.ligne_reference = ligne_ref
        resultat.indices_six_basses = list(range(i, i + 6))
        resultat.indices_points_hauts = [j, j + 1, j + 2, j + 3]
        return resultat

      break

  return resultat
