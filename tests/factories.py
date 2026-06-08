"""Objets factices pour les tests des moteurs."""

from datetime import date, timedelta


class ObsMock:
  def __init__(self, jour: date, **kwargs):
    self.date = jour
    self.temp_brute = kwargs.get("temp")
    self.temp_corrigee = kwargs.get("temp_corrigee")
    self.douteux = kwargs.get("douteux", False)
    self.motif_doute = kwargs.get("motif_doute")
    self.glaire_sensation = kwargs.get("glaire_sensation", "")
    self.glaire_aspect = kwargs.get("glaire_aspect", "")
    self.saignement = kwargs.get("saignement", "rien")
    self.union = kwargs.get("union", False)
    self.heure_prise = kwargs.get("heure_prise")
    self.cycle_id = 1
    self.id = kwargs.get("id", 0)


def serie_obs(debut: date, *entries) -> list:
  """Crée une série d'observations à partir de tuples (temp,) ou dicts."""
  obs = []
  for i, entry in enumerate(entries):
    jour = debut + timedelta(days=i)
    if isinstance(entry, dict):
      obs.append(ObsMock(jour, **entry))
    else:
      obs.append(ObsMock(jour, temp=entry))
  return obs
