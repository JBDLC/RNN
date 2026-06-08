from datetime import date, datetime, timedelta

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.choices import FEU_LABELS, METHODE_LABELS, PHASE_LABELS, methode_thermique
from app.extensions import db
from app.main.forms import (
  CloturerCycleForm,
  NouveauCycleForm,
  ObservationForm,
  OnboardingForm,
  ReglagesForm,
)
from app.models import Cycle, Observation
from app.services.cycle import (
  cloturer_cycle,
  demarrer_nouveau_cycle,
  get_cycle_courant,
  get_cycles_utilisateur,
  get_observation,
  get_observations_cycle,
  heure_prise_par_defaut,
)
from app.services.decalage import appliquer_traitement_temperature, resoudre_heure_reference, resume_decalage
from app.services.statuts import donnees_graphique, mettre_en_cache_statuts, statut_du_jour

from . import main_bp


def _require_onboarding():
  if not current_user.onboarding_complete:
    return redirect(url_for("main.onboarding"))
  return None


def _parse_date_param(value: str | None) -> date | None:
  if not value:
    return None
  try:
    return datetime.strptime(value, "%Y-%m-%d").date()
  except ValueError:
    return None


def _remplir_formulaire_observation(form: ObservationForm, observation: Observation | None, cycle: Cycle):
  form.date_obs.data = observation.date if observation else form.date_obs.data
  if observation:
    form.temp_brute.data = observation.temp_brute
    form.heure_prise.data = observation.heure_prise
    form.glaire_sensation.data = observation.glaire_sensation or ""
    form.glaire_aspect.data = observation.glaire_aspect or ""
    form.saignement.data = observation.saignement or "rien"
    form.union.data = observation.union
    form.test_lh.data = observation.test_lh or ""
    form.col_hauteur.data = observation.col_hauteur or ""
    form.col_ouverture.data = observation.col_ouverture or ""
    form.col_consistance.data = observation.col_consistance or ""
    form.douteux_manuel.data = observation.douteux and observation.motif_doute != "prise_decalee"
    form.motif_doute.data = observation.motif_doute if observation.douteux else None
  else:
    heure_str = heure_prise_par_defaut(current_user, cycle)
    form.heure_prise.data = datetime.strptime(heure_str, "%H:%M").time()


def _enregistrer_observation(form: ObservationForm, cycle: Cycle, jour_cible: date) -> Observation:
  observation = get_observation(cycle, jour_cible)
  if observation is None:
    observation = Observation(cycle_id=cycle.id, date=jour_cible)
    db.session.add(observation)

  if methode_thermique(current_user.methode):
    observation.temp_brute = form.temp_brute.data
    observation.heure_prise = form.heure_prise.data
  else:
    observation.temp_brute = None
    observation.heure_prise = None
    observation.temp_corrigee = None

  observation.glaire_sensation = form.glaire_sensation.data or None
  observation.glaire_aspect = form.glaire_aspect.data or None
  observation.saignement = form.saignement.data
  observation.union = form.union.data
  observation.test_lh = form.test_lh.data or None
  observation.col_hauteur = form.col_hauteur.data or None
  observation.col_ouverture = form.col_ouverture.data or None
  observation.col_consistance = form.col_consistance.data or None

  observations_cycle = get_observations_cycle(cycle)
  motif = form.motif_doute.data if form.douteux_manuel.data else None
  appliquer_traitement_temperature(
    observation,
    current_user,
    observations_cycle,
    douteux_manuel=form.douteux_manuel.data,
    motif_manuel=motif,
  )

  db.session.commit()
  mettre_en_cache_statuts(cycle, current_user)
  return observation


@main_bp.route("/health")
def health():
  """Sonde de santé pour Render (ne nécessite pas d'authentification)."""
  return {"status": "ok"}, 200


@main_bp.route("/")
def accueil():
  cycle = None
  statut_aujourdhui = None
  if current_user.is_authenticated and current_user.onboarding_complete:
    cycle = get_cycle_courant(current_user)
    if cycle:
      statut_aujourdhui = statut_du_jour(cycle, current_user, date.today())
  return render_template(
    "main/accueil.html",
    cycle=cycle,
    statut_aujourdhui=statut_aujourdhui,
    phase_labels=PHASE_LABELS,
    feu_labels=FEU_LABELS,
  )


@main_bp.route("/a-lire", methods=["GET", "POST"])
@login_required
def a_lire():
  if request.method == "POST":
    current_user.avertissement_lu = True
    db.session.commit()
    flash("Merci d'avoir pris connaissance des avertissements.", "success")
    if not current_user.onboarding_complete:
      return redirect(url_for("main.onboarding"))
    return redirect(url_for("main.accueil"))

  return render_template("main/a_lire.html")


@main_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
  if not current_user.avertissement_lu:
    return redirect(url_for("main.a_lire"))

  if current_user.onboarding_complete:
    return redirect(url_for("main.jour"))

  form = OnboardingForm()
  if form.validate_on_submit():
    current_user.methode = form.methode.data
    current_user.intention = form.intention.data
    current_user.mode_decalage = form.mode_decalage.data
    current_user.heure_reference = form.heure_reference.data
    current_user.seuil_decalage_min = form.seuil_decalage_min.data
    current_user.onboarding_complete = True

    cycle = Cycle(user_id=current_user.id, date_debut_regles=form.date_debut_regles.data)
    db.session.add(cycle)
    db.session.commit()

    flash("Configuration enregistrée. Vous pouvez saisir votre première observation.", "success")
    return redirect(url_for("main.jour"))

  return render_template("main/onboarding.html", form=form)


@main_bp.route("/jour", methods=["GET", "POST"])
@login_required
def jour():
  redirect_onboarding = _require_onboarding()
  if redirect_onboarding:
    return redirect_onboarding

  cycle = get_cycle_courant(current_user)
  if cycle is None:
    flash("Aucun cycle en cours.", "warning")
    return redirect(url_for("main.historique"))

  jour_cible = _parse_date_param(request.args.get("date")) or date.today()

  if jour_cible > date.today():
    flash("Impossible de saisir une date future.", "warning")
    return redirect(url_for("main.jour"))

  if jour_cible < cycle.date_debut_regles:
    flash("Cette date est antérieure au début du cycle en cours.", "warning")
    return redirect(url_for("main.jour"))

  obs_existante = get_observation(cycle, jour_cible)
  form = ObservationForm(methode_utilisateur=current_user.methode)

  if request.method == "GET":
    form.date_obs.data = jour_cible
    _remplir_formulaire_observation(form, obs_existante, cycle)

  if form.validate_on_submit():
    jour_saisi = form.date_obs.data
    if jour_saisi < cycle.date_debut_regles:
      flash("Cette date est antérieure au début du cycle en cours.", "danger")
    elif jour_saisi > date.today():
      flash("Impossible de saisir une date future.", "danger")
    else:
      _enregistrer_observation(form, cycle, jour_saisi)
      flash(f"Observation du {jour_saisi.strftime('%d/%m/%Y')} enregistrée.", "success")
      return redirect(url_for("main.jour", date=jour_saisi.isoformat()))

  observations_cycle = get_observations_cycle(cycle)
  heure_ref = resoudre_heure_reference(current_user, observations_cycle)
  info_decalage = None
  if obs_existante:
    info_decalage = resume_decalage(obs_existante, current_user, heure_ref)

  jour_precedent = jour_cible - timedelta(days=1) if jour_cible > cycle.date_debut_regles else None
  jour_suivant = jour_cible + timedelta(days=1) if jour_cible < date.today() else None
  jour_affiche = form.date_obs.data if form.date_obs.data else jour_cible
  obs_pour_jour = get_observation(cycle, jour_affiche)
  statut = statut_du_jour(cycle, current_user, jour_affiche) if obs_pour_jour else None

  return render_template(
    "main/jour.html",
    form=form,
    cycle=cycle,
    jour_cible=jour_affiche,
    today=date.today(),
    jour_precedent=jour_precedent,
    jour_suivant=jour_suivant,
    obs_existante=obs_existante,
    statut=statut,
    methode_label=METHODE_LABELS.get(current_user.methode, ""),
    afficher_temperature=methode_thermique(current_user.methode),
    heure_reference=heure_ref,
    info_decalage=info_decalage,
    phase_labels=PHASE_LABELS,
    feu_labels=FEU_LABELS,
  )


@main_bp.route("/cycle")
@login_required
def cycle():
  redirect_onboarding = _require_onboarding()
  if redirect_onboarding:
    return redirect_onboarding

  cycle_courant = get_cycle_courant(current_user)
  if cycle_courant is None:
    flash("Aucun cycle en cours.", "info")
    return redirect(url_for("main.historique"))

  observations = get_observations_cycle(cycle_courant)
  statuts = mettre_en_cache_statuts(cycle_courant, current_user)
  statut_aujourdhui = statut_du_jour(cycle_courant, current_user, date.today())
  graphique = donnees_graphique(cycle_courant, current_user)

  jours_avec_statut = list(zip(observations, statuts))

  return render_template(
    "main/cycle.html",
    cycle=cycle_courant,
    statut_aujourdhui=statut_aujourdhui,
    jours_avec_statut=jours_avec_statut,
    graphique=graphique,
    methode_label=METHODE_LABELS.get(current_user.methode, ""),
    afficher_graphique=methode_thermique(current_user.methode),
    phase_labels=PHASE_LABELS,
    feu_labels=FEU_LABELS,
    intention_label=current_user.intention,
  )


@main_bp.route("/historique", methods=["GET", "POST"])
@login_required
def historique():
  redirect_onboarding = _require_onboarding()
  if redirect_onboarding:
    return redirect_onboarding

  cycle_courant = get_cycle_courant(current_user)
  cycles = get_cycles_utilisateur(current_user)
  form_cloture = CloturerCycleForm()
  form_nouveau = NouveauCycleForm()

  if request.method == "POST":
    action = request.form.get("action")
    if action == "cloturer" and form_cloture.validate_on_submit():
      if cycle_courant is None:
        flash("Aucun cycle à clôturer.", "warning")
      else:
        cloturer_cycle(cycle_courant, current_user, form_cloture.date_fin.data)
        flash("Cycle clôturé. Le profil personnel a été mis à jour.", "success")
      return redirect(url_for("main.historique"))

    if action == "nouveau" and form_nouveau.validate_on_submit():
      if cycle_courant is not None:
        flash("Clôturez d'abord le cycle en cours.", "warning")
      else:
        demarrer_nouveau_cycle(current_user, form_nouveau.date_debut_regles.data)
        flash("Nouveau cycle démarré.", "success")
      return redirect(url_for("main.jour"))

  profil = current_user.profil

  return render_template(
    "main/historique.html",
    cycles=cycles,
    cycle_courant=cycle_courant,
    profil=profil,
    form_cloture=form_cloture,
    form_nouveau=form_nouveau,
    methode_label=METHODE_LABELS.get(current_user.methode, ""),
  )


@main_bp.route("/reglages", methods=["GET", "POST"])
@login_required
def reglages():
  form = ReglagesForm(obj=current_user)

  if form.validate_on_submit():
    current_user.methode = form.methode.data
    current_user.intention = form.intention.data
    current_user.mode_decalage = form.mode_decalage.data
    current_user.heure_reference = form.heure_reference.data
    current_user.seuil_decalage_min = form.seuil_decalage_min.data
    db.session.commit()

    cycle = get_cycle_courant(current_user)
    if cycle:
      mettre_en_cache_statuts(cycle, current_user)

    flash("Réglages enregistrés.", "success")
    return redirect(url_for("main.reglages"))

  cycle = get_cycle_courant(current_user)
  observations = get_observations_cycle(cycle) if cycle else []
  heure_ref_effective = resoudre_heure_reference(current_user, observations)

  return render_template(
    "main/reglages.html",
    form=form,
    cycle=cycle,
    heure_ref_effective=heure_ref_effective,
  )
