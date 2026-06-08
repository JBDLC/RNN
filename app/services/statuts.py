"""Calcul et mise en cache des statuts moteur."""

import json

from app.choices import methode_thermique
from app.engines.factory import creer_moteur
from app.extensions import db
from app.models import Statut
from app.services.cycle import get_observations_cycle


def calculer_statuts_cycle(cycle, user) -> list:
  observations = get_observations_cycle(cycle)
  moteur = creer_moteur(
    user.methode,
    user.profil,
    cycle.date_debut_regles,
    user.intention or "eviter",
  )
  return moteur.calculer_statuts(observations)


def mettre_en_cache_statuts(cycle, user) -> list:
  """Calcule les statuts et les persiste en base."""
  statuts = calculer_statuts_cycle(cycle, user)
  obs_par_date = {o.date: o for o in get_observations_cycle(cycle)}

  for statut in statuts:
    obs = obs_par_date.get(statut.date)
    if obs is None:
      continue

    cache = obs.statut
    if cache is None:
      cache = Statut(observation_id=obs.id)
      db.session.add(cache)

    cache.phase = statut.phase.value
    cache.feu = statut.feu.value
    cache.confiance = statut.confiance
    cache.messages_json = json.dumps(statut.messages, ensure_ascii=False)

  db.session.commit()
  return statuts


def statut_du_jour(cycle, user, jour):
  statuts = calculer_statuts_cycle(cycle, user)
  for s in statuts:
    if s.date == jour:
      return s
  return None


def donnees_graphique(cycle, user) -> dict | None:
  """Prépare les données Chart.js pour Sensiplan / CLER."""
  if not methode_thermique(user.methode):
    return None

  observations = get_observations_cycle(cycle)
  if not observations:
    return None

  moteur = creer_moteur(
    user.methode,
    user.profil,
    cycle.date_debut_regles,
    user.intention or "eviter",
  )
  courbe = moteur.donnees_courbe(observations)
  serie_index = {d: i for i, (d, _) in enumerate(courbe["serie"])}
  high_indices = set(courbe.get("indices_points_hauts", []))

  labels = []
  data_corrigee = []
  data_brute = []
  point_styles = []
  point_radius = []
  border_dash = []

  for obs in observations:
    labels.append(obs.date.strftime("%d/%m"))
    data_brute.append(obs.temp_brute)
    data_corrigee.append(obs.temp_corrigee if obs.temp_corrigee is not None else obs.temp_brute)

    if obs.douteux:
      point_styles.append("#9ca3af")
      point_radius.append(6)
      border_dash.append([4, 4])
    else:
      idx = serie_index.get(obs.date)
      if idx is not None and idx in high_indices:
        point_styles.append("#c0392b")
        point_radius.append(9)
      else:
        point_styles.append("#5a9b91")
        point_radius.append(5)
      border_dash.append([])

  ligne_ref = courbe.get("ligne_reference")
  pic = courbe.get("pic_glaire")
  pic_index = next((i for i, o in enumerate(observations) if o.date == pic), None)

  return {
    "labels": labels,
    "data_brute": data_brute,
    "data_corrigee": data_corrigee,
    "point_styles": point_styles,
    "point_radius": point_radius,
    "border_dash": border_dash,
    "ligne_reference": [ligne_ref] * len(labels) if ligne_ref else [],
    "ligne_ref_value": ligne_ref,
    "pic_index": pic_index,
  }
