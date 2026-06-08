"""Utilitaires partagés entre les moteurs."""

from datetime import date, timedelta


def observations_triees(observations: list) -> list:
  return sorted(observations, key=lambda o: o.date)


def temp_thermique(obs) -> float | None:
  """Température utilisable pour le calcul (exclut les points douteux)."""
  if obs.douteux:
    return None
  if obs.temp_corrigee is not None:
    return obs.temp_corrigee
  return obs.temp_brute


def jour_du_cycle(obs_date: date, cycle_debut: date) -> int:
  return (obs_date - cycle_debut).days + 1


def obs_par_date(observations: list) -> dict[date, object]:
  return {o.date: o for o in observations}


def obs_a_la_date(observations: list, jour: date):
  return obs_par_date(observations).get(jour)


def cycle_min_effectif(profil, defaut: int = 21) -> int:
  if profil and profil.cycle_min:
    return profil.cycle_min
  return defaut


def confiance_depuis_profil(profil) -> str:
  """Module la confiance selon la régularité de saisie (jamais les verrous)."""
  if not profil or profil.pct_points_douteux is None:
    return "haute"
  if profil.pct_points_douteux > 20:
    return "basse"
  return "haute"
