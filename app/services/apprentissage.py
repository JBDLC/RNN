"""
Apprentissage personnalisé — statistiques sur les cycles clôturés.
Le profil sert UNIQUEMENT à anticiper et personnaliser les messages,
jamais à raccourcir les verrous de confirmation.
"""

import statistics
from datetime import time

from app.engines.factory import creer_moteur
from app.engines.glaire import detecter_premier_signe_glaire
from app.engines.thermique import detecter_hausse_thermique
from app.engines.utils import jour_du_cycle, observations_triees, temp_thermique
from app.extensions import db
from app.models import Cycle, ProfilPersonnel
from app.services.cycle import get_observations_cycle


def _duree_cycle(cycle: Cycle) -> int | None:
  if cycle.date_fin is None:
    return None
  return (cycle.date_fin - cycle.date_debut_regles).days + 1


def _cycles_clotures(user, limite: int = 12) -> list[Cycle]:
  return (
    Cycle.query.filter_by(user_id=user.id)
    .filter(Cycle.date_fin.isnot(None))
    .order_by(Cycle.date_debut_regles.desc())
    .limit(limite)
    .all()
  )


def _jour_ovulation(cycle: Cycle, user) -> int | None:
  observations = get_observations_cycle(cycle)
  if user.methode == "billings":
    from app.engines.glaire import detecter_pic_billings
    pic = detecter_pic_billings(observations)
    if pic:
      return jour_du_cycle(pic, cycle.date_debut_regles)
    return None

  thermique = detecter_hausse_thermique(observations)
  if thermique.date_confirmation:
    return jour_du_cycle(thermique.date_confirmation, cycle.date_debut_regles)
  return None


def _stats_temperatures(observations: list) -> tuple[float | None, float | None, float | None]:
  temps = [temp_thermique(o) for o in observations_triees(observations)]
  temps = [t for t in temps if t is not None]
  if len(temps) < 6:
    return None, None, None

  six_basses = sorted(temps)[:6]
  plateau_bas = statistics.mean(six_basses)
  plateau_haut = statistics.mean(sorted(temps)[-3:]) if len(temps) >= 3 else None
  amplitude = (plateau_haut - plateau_bas) if plateau_haut else None
  return plateau_bas, plateau_haut, amplitude


def _heure_habituelle(observations: list) -> time | None:
  from app.services.decalage import mediane_heures

  heures = [o.heure_prise for o in observations if o.heure_prise]
  return mediane_heures(heures)


def _jour_apparition_glaire(cycle: Cycle, observations: list) -> int | None:
  premier = detecter_premier_signe_glaire(observations)
  if premier:
    return jour_du_cycle(premier, cycle.date_debut_regles)
  return None


def mettre_a_jour_profil(user) -> ProfilPersonnel:
  """Recalcule le profil personnel après clôture d'un cycle."""
  if user.profil is None:
    profil = ProfilPersonnel(user_id=user.id)
    db.session.add(profil)
    user.profil = profil
  else:
    profil = user.profil

  cycles = _cycles_clotures(user)
  durees = [d for c in cycles if (d := _duree_cycle(c))]

  if durees:
    profil.cycle_moyen = statistics.mean(durees)
    profil.cycle_min = min(durees)
    profil.cycle_max = max(durees)
    profil.ecart_type_cycle = statistics.stdev(durees) if len(durees) > 1 else 0.0

  jours_ovul = []
  jours_glaire = []
  plateau_bas_list = []
  plateau_haut_list = []
  amplitudes = []
  total_obs = 0
  total_douteux = 0

  for cycle in cycles:
    observations = get_observations_cycle(cycle)
    total_obs += len(observations)
    total_douteux += sum(1 for o in observations if o.douteux)

    jo = _jour_ovulation(cycle, user)
    if jo:
      jours_ovul.append(jo)

    jg = _jour_apparition_glaire(cycle, observations)
    if jg:
      jours_glaire.append(jg)

    pb, ph, amp = _stats_temperatures(observations)
    if pb is not None:
      plateau_bas_list.append(pb)
    if ph is not None:
      plateau_haut_list.append(ph)
    if amp is not None:
      amplitudes.append(amp)

  if jours_ovul:
    profil.jour_ovulation_moyen = statistics.mean(jours_ovul)
  if jours_glaire:
    profil.jour_apparition_glaire_moyen = statistics.mean(jours_glaire)
  if plateau_bas_list:
    profil.temp_plateau_bas = statistics.mean(plateau_bas_list)
  if plateau_haut_list:
    profil.temp_plateau_haut = statistics.mean(plateau_haut_list)
  if amplitudes:
    profil.amplitude_saut = statistics.mean(amplitudes)

  # Heure habituelle sur le cycle le plus récent clôturé
  if cycles:
    obs_recentes = get_observations_cycle(cycles[0])
    profil.heure_prise_habituelle = _heure_habituelle(obs_recentes)

  profil.pct_points_douteux = (total_douteux / total_obs * 100) if total_obs else 0.0
  profil.nb_cycles_enregistres = len(cycles)

  db.session.commit()
  return profil


def cycle_etait_ovulatoire(cycle: Cycle, user) -> bool:
  """Indique si un cycle clôturé présentait une ovulation détectée."""
  return _jour_ovulation(cycle, user) is not None
