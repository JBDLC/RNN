from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
  BooleanField,
  DateField,
  FloatField,
  IntegerField,
  RadioField,
  SelectField,
  StringField,
  SubmitField,
  TimeField,
)
from wtforms.validators import DataRequired, NumberRange, Optional, ValidationError

from app.choices import (
  COL_CONSISTANCES,
  COL_HAUTEURS,
  COL_OUVERTURES,
  GLAIRE_ASPECTS,
  GLAIRE_SENSATIONS,
  INTENTIONS,
  METHODES,
  MODES_DECALAGE,
  MOTIFS_DOUTE,
  SAIGNEMENTS,
  TESTS_LH,
  methode_thermique,
)


class OnboardingForm(FlaskForm):
  methode = RadioField("Méthode", choices=METHODES, validators=[DataRequired()])
  intention = RadioField("Intention", choices=INTENTIONS, validators=[DataRequired()])
  date_debut_regles = DateField(
    "Date du premier jour des dernières règles",
    validators=[DataRequired()],
    default=date.today,
  )
  mode_decalage = RadioField("Gestion du décalage horaire", choices=MODES_DECALAGE, default="exclusion")
  heure_reference = TimeField(
    "Heure de prise habituelle (optionnel — laisser vide pour calcul auto)",
    validators=[Optional()],
    format="%H:%M",
  )
  seuil_decalage_min = IntegerField(
    "Seuil de décalage (minutes)",
    default=60,
    validators=[DataRequired(), NumberRange(min=15, max=180)],
  )
  submit = SubmitField("Commencer le suivi")


class ReglagesForm(FlaskForm):
  methode = RadioField("Méthode", choices=METHODES, validators=[DataRequired()])
  intention = RadioField("Intention", choices=INTENTIONS, validators=[DataRequired()])
  mode_decalage = RadioField("Gestion du décalage horaire", choices=MODES_DECALAGE)
  heure_reference = TimeField(
    "Heure de référence (vide = médiane auto du cycle)",
    validators=[Optional()],
    format="%H:%M",
  )
  seuil_decalage_min = IntegerField(
    "Seuil de décalage (minutes)",
    validators=[DataRequired(), NumberRange(min=15, max=180)],
  )
  submit = SubmitField("Enregistrer")


class CloturerCycleForm(FlaskForm):
  date_fin = DateField("Date de fin du cycle", validators=[DataRequired()], default=date.today)
  submit = SubmitField("Clôturer ce cycle")


class NouveauCycleForm(FlaskForm):
  date_debut_regles = DateField(
    "Premier jour des nouvelles règles",
    validators=[DataRequired()],
    default=date.today,
  )
  submit = SubmitField("Démarrer un nouveau cycle")


class ObservationForm(FlaskForm):
  date_obs = DateField("Date", validators=[DataRequired()], format="%Y-%m-%d")
  temp_brute = FloatField("Température (°C)", validators=[Optional(), NumberRange(min=35.0, max=40.0)])
  heure_prise = TimeField("Heure de prise", validators=[Optional()], format="%H:%M")
  glaire_sensation = SelectField("Sensation", choices=GLAIRE_SENSATIONS, validators=[Optional()])
  glaire_aspect = SelectField("Aspect de la glaire", choices=GLAIRE_ASPECTS, validators=[Optional()])
  saignement = SelectField("Saignement", choices=SAIGNEMENTS, default="rien")
  union = BooleanField("Union ce jour-là")
  test_lh = SelectField("Test LH", choices=TESTS_LH, validators=[Optional()])
  col_hauteur = SelectField("Col — hauteur", choices=COL_HAUTEURS, validators=[Optional()])
  col_ouverture = SelectField("Col — ouverture", choices=COL_OUVERTURES, validators=[Optional()])
  col_consistance = SelectField("Col — consistance", choices=COL_CONSISTANCES, validators=[Optional()])
  douteux_manuel = BooleanField("Marquer comme point douteux")
  motif_doute = SelectField("Motif du doute", choices=MOTIFS_DOUTE, validators=[Optional()])
  submit = SubmitField("Enregistrer")

  def __init__(self, *args, methode_utilisateur=None, **kwargs):
    super().__init__(*args, **kwargs)
    self.methode_utilisateur = methode_utilisateur

  def validate_temp_brute(self, field):
    if self.methode_utilisateur and methode_thermique(self.methode_utilisateur):
      if field.data is None:
        raise ValidationError("La température est requise pour cette méthode.")

  def validate_heure_prise(self, field):
    if self.methode_utilisateur and methode_thermique(self.methode_utilisateur):
      if field.data is None:
        raise ValidationError("L'heure de prise est requise pour cette méthode.")

  def validate_motif_doute(self, field):
    if self.douteux_manuel.data and not field.data:
      raise ValidationError("Indiquez un motif si le point est douteux.")

  def validate_date_obs(self, field):
    if field.data and field.data > date.today():
      raise ValidationError("Impossible de saisir une date future.")
