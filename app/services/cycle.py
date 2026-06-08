from datetime import date

from app.extensions import db
from app.models import Cycle, Observation


def get_cycle_courant(user) -> Cycle | None:
  """Retourne le cycle ouvert (sans date de fin) de l'utilisateur."""
  return (
    Cycle.query.filter_by(user_id=user.id, date_fin=None)
    .order_by(Cycle.date_debut_regles.desc())
    .first()
  )


def get_cycles_utilisateur(user) -> list[Cycle]:
  return (
    Cycle.query.filter_by(user_id=user.id)
    .order_by(Cycle.date_debut_regles.desc())
    .all()
  )


def get_or_create_cycle_courant(user) -> Cycle:
  """Retourne le cycle courant ou en crée un commençant aujourd'hui."""
  cycle = get_cycle_courant(user)
  if cycle:
    return cycle

  cycle = Cycle(user_id=user.id, date_debut_regles=date.today())
  db.session.add(cycle)
  db.session.flush()
  return cycle


def get_observation(cycle: Cycle, jour: date) -> Observation | None:
  return Observation.query.filter_by(cycle_id=cycle.id, date=jour).first()


def get_observations_cycle(cycle: Cycle) -> list[Observation]:
  return (
    Observation.query.filter_by(cycle_id=cycle.id)
    .order_by(Observation.date)
    .all()
  )


def heure_prise_par_defaut(user, cycle: Cycle | None) -> str:
  """Heure pré-remplie : profil → réglage utilisateur → dernière obs → 07:00."""
  if user.profil and user.profil.heure_prise_habituelle:
    return user.profil.heure_prise_habituelle.strftime("%H:%M")

  if user.heure_reference:
    return user.heure_reference.strftime("%H:%M")

  if cycle:
    obs = (
      Observation.query.filter_by(cycle_id=cycle.id)
      .filter(Observation.heure_prise.isnot(None))
      .order_by(Observation.date.desc())
      .first()
    )
    if obs and obs.heure_prise:
      return obs.heure_prise.strftime("%H:%M")

  return "07:00"


def cloturer_cycle(cycle: Cycle, user, date_fin: date | None = None) -> Cycle:
  """Clôture le cycle en cours et met à jour le profil personnel."""
  from app.services.apprentissage import mettre_a_jour_profil

  cycle.date_fin = date_fin or date.today()
  db.session.commit()
  mettre_a_jour_profil(user)
  return cycle


def demarrer_nouveau_cycle(user, date_debut_regles: date) -> Cycle:
  """Démarre un nouveau cycle après clôture du précédent."""
  cycle = Cycle(user_id=user.id, date_debut_regles=date_debut_regles)
  db.session.add(cycle)
  db.session.commit()
  return cycle
