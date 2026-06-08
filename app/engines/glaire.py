"""Détection des signes de glaire cervicale."""

from datetime import date, timedelta

from app.engines.utils import observations_triees

_SCORES_ASPECT = {
  "rien": 0,
  "collante_epaisse": 1,
  "cremeuse": 2,
  "filante_transparente": 4,
}

_SCORES_SENSATION = {
  "seche": 0,
  "humide": 2,
  "mouillee_glissante": 4,
}


def score_glaire(obs) -> int:
  score_a = _SCORES_ASPECT.get(obs.glaire_aspect or "", 0)
  score_s = _SCORES_SENSATION.get(obs.glaire_sensation or "", 0)
  return max(score_a, score_s)


def est_glaire_fertile(obs) -> bool:
  if obs.glaire_sensation in ("humide", "mouillee_glissante"):
    return True
  return obs.glaire_aspect in ("collante_epaisse", "cremeuse", "filante_transparente")


def est_jour_sec(obs) -> bool:
  if obs is None:
    return False
  sensation = obs.glaire_sensation or "seche"
  aspect = obs.glaire_aspect or "rien"
  return sensation in ("", "seche") and aspect in ("", "rien")


def est_qualite_pic(obs) -> bool:
  return (
    obs.glaire_aspect == "filante_transparente"
    or obs.glaire_sensation == "mouillee_glissante"
  )


def est_sensation_glissante_billings(obs) -> bool:
  return (
    obs.glaire_sensation == "mouillee_glissante"
    or obs.glaire_aspect == "filante_transparente"
  )


def detecter_premier_signe_glaire(observations: list) -> date | None:
  for obs in observations_triees(observations):
    if est_glaire_fertile(obs):
      return obs.date
  return None


def detecter_pic_glaire(observations: list) -> date | None:
  """
  Pic = dernier jour de meilleure qualité, confirmé rétrospectivement
  (lendemain de qualité inférieure ou fin de série).
  """
  obs_list = observations_triees(observations)
  pic_confirme = None

  for i, obs in enumerate(obs_list):
    if not est_qualite_pic(obs):
      continue
    suivante = obs_list[i + 1] if i + 1 < len(obs_list) else None
    if suivante is None or score_glaire(suivante) < score_glaire(obs):
      pic_confirme = obs.date

  return pic_confirme


def detecter_pic_billings(observations: list) -> date | None:
  """Pic Billings = dernier jour de sensation glissante/lubrifiée, confirmé rétrospectivement."""
  obs_list = observations_triees(observations)
  pic_confirme = None

  for i, obs in enumerate(obs_list):
    if not est_sensation_glissante_billings(obs):
      continue
    suivante = obs_list[i + 1] if i + 1 < len(obs_list) else None
    if suivante is None or not est_sensation_glissante_billings(suivante):
      pic_confirme = obs.date

  return pic_confirme


def date_fin_post_ovulatoire_glaire(pic: date | None) -> date | None:
  """Soir du 3e jour après le pic."""
  if pic is None:
    return None
  return pic + timedelta(days=3)


def est_en_regles(obs) -> bool:
  return obs is not None and obs.saignement == "regles"


def dernier_jour_regles(observations: list, cycle_debut: date) -> date | None:
  dernier = None
  for obs in observations_triees(observations):
    if est_en_regles(obs):
      dernier = obs.date
    elif dernier and obs.date > dernier:
      break
  if dernier is None and cycle_debut:
    return cycle_debut
  return dernier
