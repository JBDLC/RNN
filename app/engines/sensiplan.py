"""Moteur Sensiplan — sympto-thermique."""

from datetime import date, timedelta

from app.engines.base import Feu, MoteurMethode, Phase, StatutJour
from app.engines.feu import calculer_feu
from app.engines.glaire import (
  date_fin_post_ovulatoire_glaire,
  detecter_pic_glaire,
  detecter_premier_signe_glaire,
  est_jour_sec,
)
from app.engines.thermique import detecter_hausse_thermique
from app.engines.utils import (
  confiance_depuis_profil,
  cycle_min_effectif,
  jour_du_cycle,
  obs_a_la_date,
  observations_triees,
)


class MoteurSensiplan(MoteurMethode):
  """Moteur de calcul Sensiplan."""

  def __init__(self, profil_personnel=None, cycle_debut: date | None = None, intention: str = "eviter"):
    super().__init__(profil_personnel)
    self.cycle_debut = cycle_debut
    self.intention = intention

  def _analyse_cycle(self, observations: list) -> dict:
    thermique = detecter_hausse_thermique(observations)
    pic = detecter_pic_glaire(observations)
    fin_glaire = date_fin_post_ovulatoire_glaire(pic)

    fin_fertile = None
    if thermique.date_confirmation and fin_glaire:
      fin_fertile = max(thermique.date_confirmation, fin_glaire)

    premier_glaire = detecter_premier_signe_glaire(observations)
    cycle_min = cycle_min_effectif(self.profil_personnel)
    debut_theorique = None
    if self.cycle_debut:
      debut_theorique = self.cycle_debut + timedelta(days=cycle_min - 8)

    debut_fertile = None
    candidats = [d for d in (premier_glaire, debut_theorique) if d]
    if candidats:
      debut_fertile = min(candidats)

    regle_5 = self._regle_des_5_jours_applicable()
    fin_regles = self._fin_regles(observations)

    return {
      "thermique": thermique,
      "pic": pic,
      "fin_fertile": fin_fertile,
      "debut_fertile": debut_fertile,
      "regle_5": regle_5,
      "fin_regles": fin_regles,
    }

  def _regle_des_5_jours_applicable(self) -> bool:
    if not self.profil_personnel:
      return False
    return self.profil_personnel.nb_cycles_enregistres >= 1

  def _fin_regles(self, observations: list) -> date | None:
    fin = None
    for obs in observations_triees(observations):
      if obs.saignement == "regles":
        fin = obs.date
    return fin or self.cycle_debut

  def _statut_jour(self, obs, analyse: dict) -> StatutJour:
    messages = []
    jdc = jour_du_cycle(obs.date, self.cycle_debut) if self.cycle_debut else 0
    en_doute = obs.douteux

    fin_fertile = analyse["fin_fertile"]
    debut_fertile = analyse["debut_fertile"]
    infertilite_confirmee = fin_fertile is not None and obs.date >= fin_fertile

    preov_infertile = False
    if analyse["regle_5"] and jdc <= 5 and analyse["fin_regles"]:
      if obs.date <= analyse["fin_regles"] + timedelta(days=5):
        if est_jour_sec(obs):
          preov_infertile = True
          messages.append("Règle des 5 jours : jour sec en début de cycle (cycle précédent ovulatoire).")

    if debut_fertile and obs.date < debut_fertile and not preov_infertile:
      phase = Phase.PREOVULATOIRE
      messages.append("Avant le début de fertilité estimé.")
    elif infertilite_confirmee:
      phase = Phase.POSTOVULATOIRE
      messages.append("Double verrou confirmé : hausse thermique et 3e jour après le pic de glaire.")
    elif debut_fertile and obs.date >= debut_fertile:
      phase = Phase.FERTILE
      if analyse["pic"] and obs.date <= analyse["pic"]:
        messages.append("Fenêtre fertile — avant ou au pic de glaire.")
      else:
        messages.append("Fenêtre fertile — en attente de confirmation post-ovulatoire.")
    else:
      phase = Phase.INDETERMINEE
      messages.append("Statut en cours de détermination — prudence.")

    if en_doute:
      messages.append(f"Point douteux ({obs.motif_doute or 'non précisé'}) — exclu du calcul thermique.")

    if obs.union:
      messages.append("Union enregistrée ce jour.")

    fenetre_conception = (
      phase == Phase.FERTILE
      and analyse.get("pic")
      and obs.date >= analyse["pic"] - timedelta(days=2)
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

    if debut_fertile and self.profil_personnel and self.profil_personnel.cycle_min:
      messages.append(
        f"Borne prédictive (profil) : cycle le plus court {self.profil_personnel.cycle_min} j — "
        "utilisée uniquement pour anticiper, jamais pour raccourcir les verrous."
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
    return [self._statut_jour(obs, analyse) for obs in observations_triees(observations)]

  def fenetre_fertile(self, observations: list) -> tuple:
    analyse = self._analyse_cycle(observations)
    return analyse["debut_fertile"], analyse["fin_fertile"]

  def donnees_courbe(self, observations: list) -> dict:
    """Métadonnées pour Chart.js."""
    analyse = self._analyse_cycle(observations)
    thermique = analyse["thermique"]
    return {
      "ligne_reference": thermique.ligne_reference,
      "indices_points_hauts": thermique.indices_points_hauts,
      "serie": thermique.serie,
      "pic_glaire": analyse["pic"],
    }
