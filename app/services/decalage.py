from datetime import time

from app.models import Observation, User


def _minutes_depuis_minuit(heure: time) -> int:
  return heure.hour * 60 + heure.minute


def delta_minutes(heure_prise: time, heure_reference: time) -> int:
  """Écart en minutes (positif = prise plus tardive que la référence)."""
  return _minutes_depuis_minuit(heure_prise) - _minutes_depuis_minuit(heure_reference)


def mediane_heures(heures: list[time]) -> time | None:
  """Calcule la médiane d'une liste d'heures de prise."""
  if not heures:
    return None
  minutes_triees = sorted(_minutes_depuis_minuit(h) for h in heures)
  n = len(minutes_triees)
  mid = n // 2
  if n % 2 == 0:
    mediane = (minutes_triees[mid - 1] + minutes_triees[mid]) // 2
  else:
    mediane = minutes_triees[mid]
  return time(mediane // 60, mediane % 60)


def resoudre_heure_reference(user: User, observations: list[Observation]) -> time | None:
  """
  Heure de référence : fixée par l'utilisateur ou médiane du cycle (auto).
  """
  if user.heure_reference:
    return user.heure_reference

  heures = [o.heure_prise for o in observations if o.heure_prise is not None]
  return mediane_heures(heures)


def appliquer_traitement_temperature(
  observation: Observation,
  user: User,
  observations_cycle: list[Observation],
  *,
  douteux_manuel: bool = False,
  motif_manuel: str | None = None,
) -> None:
  """
  Applique le mode décalage (exclusion ou correction) sur une observation.
  Met à jour douteux, motif_doute et temp_corrigee.
  """
  if douteux_manuel:
    observation.douteux = True
    observation.motif_doute = motif_manuel
  else:
    observation.douteux = False
    observation.motif_doute = None

  observation.temp_corrigee = None

  if observation.temp_brute is None or observation.heure_prise is None:
    return

  # Exclure l'observation courante pour le calcul auto de la médiane
  autres = [o for o in observations_cycle if o.id != observation.id]
  heure_ref = resoudre_heure_reference(user, autres)

  if heure_ref is None:
    return

  ecart_min = delta_minutes(observation.heure_prise, heure_ref)

  if user.mode_decalage == "correction":
    ecart_heures = ecart_min / 60.0
    observation.temp_corrigee = round(observation.temp_brute - 0.1 * ecart_heures, 2)
  elif user.mode_decalage == "exclusion":
    if abs(ecart_min) > user.seuil_decalage_min:
      observation.douteux = True
      observation.motif_doute = observation.motif_doute or "prise_decalee"


def resume_decalage(observation: Observation, user: User, heure_ref: time | None) -> str | None:
  """Message informatif sur le traitement appliqué (affichage formulaire)."""
  if observation.temp_brute is None or observation.heure_prise is None or heure_ref is None:
    return None

  ecart_min = delta_minutes(observation.heure_prise, heure_ref)
  signe = "+" if ecart_min >= 0 else ""

  if user.mode_decalage == "correction" and observation.temp_corrigee is not None:
    return (
      f"Écart : {signe}{ecart_min} min → température corrigée : "
      f"{observation.temp_corrigee:.2f} °C (brute : {observation.temp_brute:.2f} °C)"
    )

  if user.mode_decalage == "exclusion" and observation.douteux:
    return (
      f"Écart : {signe}{ecart_min} min (seuil {user.seuil_decalage_min} min) "
      f"→ point marqué douteux, exclu du calcul thermique."
    )

  return f"Écart : {signe}{ecart_min} min — dans la tolérance."
