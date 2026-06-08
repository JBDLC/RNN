"""Moteur Billings — glaire cervicale seule."""

from datetime import date, timedelta

from app.engines.base import Feu, MoteurMethode, Phase, StatutJour
from app.engines.feu import calculer_feu
from app.engines.glaire import (
  date_fin_post_ovulatoire_glaire,
  detecter_pic_billings,
  detecter_premier_signe_glaire,
  dernier_jour_regles,
  est_en_regles,
  est_glaire_fertile,
  est_jour_sec,
)
from app.engines.utils import (
  confiance_depuis_profil,
  jour_du_cycle,
  obs_a_la_date,
  observations_triees,
)


class MoteurBillings(MoteurMethode):
  """Moteur de calcul Billings."""

  def __init__(self, profil_personnel=None, cycle_debut: date | None = None, intention: str = "eviter"):
    super().__init__(profil_personnel)
    self.cycle_debut = cycle_debut
    self.intention = intention

  def _analyse_cycle(self, observations: list) -> dict:
    pic = detecter_pic_billings(observations)
    fin_fertile = date_fin_post_ovulatoire_glaire(pic)
    premier_glaire = detecter_premier_signe_glaire(observations)
    fin_regles = dernier_jour_regles(observations, self.cycle_debut)
    return {
      "pic": pic,
      "fin_fertile": fin_fertile,
      "premier_glaire": premier_glaire,
      "fin_regles": fin_regles,
    }

  def _jour_sec_infertile(self, obs, observations: list, analyse: dict) -> bool:
    """Règle des jours secs après les règles."""
    if not est_jour_sec(obs):
      return False
    fin_regles = analyse["fin_regles"]
    if fin_regles is None or obs.date <= fin_regles:
      return False
    if analyse["premier_glaire"] and obs.date >= analyse["premier_glaire"]:
      return False
    return True

  def _glaire_non_fiable(self, obs, observations: list) -> bool:
    """Après une union, la glaire du lendemain peut être non fiable."""
    veille = obs.date - timedelta(days=1)
    obs_veille = obs_a_la_date(observations, veille)
    return obs_veille is not None and obs_veille.union

  def _statut_jour(self, obs, observations: list, analyse: dict) -> StatutJour:
    messages = []
    en_doute = False
    fin_fertile = analyse["fin_fertile"]
    infertilite_confirmee = fin_fertile is not None and obs.date >= fin_fertile

    if est_en_regles(obs):
      phase = Phase.PREOVULATOIRE
      messages.append("Jour de règles.")
    elif infertilite_confirmee:
      phase = Phase.POSTOVULATOIRE
      messages.append("Infertilité post-ovulatoire confirmée — soir du 3e jour après le pic Billings.")
    elif est_glaire_fertile(obs):
      phase = Phase.FERTILE
      messages.append("Glaire ou sensation fertile détectée — fenêtre fertile.")
    elif self._jour_sec_infertile(obs, observations, analyse):
      phase = Phase.PREOVULATOIRE
      messages.append("Jour sec après les règles — soir infertile (règle des jours secs).")
    elif analyse["premier_glaire"] is None:
      phase = Phase.PREOVULATOIRE
      messages.append("Pas encore de glaire fertile observée.")
    else:
      phase = Phase.INDETERMINEE
      messages.append("Statut en cours de détermination.")

    if self._glaire_non_fiable(obs, observations):
      en_doute = True
      messages.append(
        "Union la veille — observation de glaire potentiellement non fiable (sperme résiduel). Prudence."
      )

    preov_infertile = self._jour_sec_infertile(obs, observations, analyse) and not en_doute

    fenetre_conception = (
      phase == Phase.FERTILE
      and analyse.get("pic")
      and obs.date >= analyse["pic"] - timedelta(days=1)
      and obs.date <= analyse["pic"] + timedelta(days=1)
    )

    feu = calculer_feu(
      phase,
      self.intention,
      infertilite_confirmee=infertilite_confirmee,
      preovulatoire_infertile=preov_infertile,
      en_doute=en_doute,
      fenetre_conception=fenetre_conception,
    )

    return StatutJour(
      date=obs.date,
      phase=phase,
      feu=feu,
      confiance=confiance_depuis_profil(self.profil_personnel),
      messages=messages,
    )

  def calculer_statuts(self, observations: list) -> list[StatutJour]:
    if not observations:
      return []
    analyse = self._analyse_cycle(observations)
    return [
      self._statut_jour(obs, observations, analyse)
      for obs in observations_triees(observations)
    ]

  def fenetre_fertile(self, observations: list) -> tuple:
    analyse = self._analyse_cycle(observations)
    debut = analyse["premier_glaire"]
    if debut is None and analyse["fin_regles"]:
      debut = analyse["fin_regles"] + timedelta(days=1)
    return debut, analyse["fin_fertile"]
