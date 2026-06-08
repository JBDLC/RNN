import secrets
from datetime import datetime, time

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
  """Compte utilisateur — un couple = un compte."""

  __tablename__ = "users"

  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String(255), unique=True, nullable=False, index=True)
  password_hash = db.Column(db.String(256), nullable=False)
  email_verified = db.Column(db.Boolean, default=False, nullable=False)
  verification_token = db.Column(db.String(64), unique=True, nullable=True)
  created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

  # Préférences RNN (complétées à l'onboarding)
  methode = db.Column(db.String(20), nullable=True)  # sensiplan | billings | cler
  intention = db.Column(db.String(20), nullable=True)  # eviter | concevoir
  heure_reference = db.Column(db.Time, nullable=True)
  mode_decalage = db.Column(db.String(20), default="exclusion")  # exclusion | correction
  seuil_decalage_min = db.Column(db.Integer, default=60)

  # Avertissement lu à la première ouverture
  avertissement_lu = db.Column(db.Boolean, default=False, nullable=False)
  onboarding_complete = db.Column(db.Boolean, default=False, nullable=False)

  cycles = db.relationship("Cycle", back_populates="user", cascade="all, delete-orphan")
  profil = db.relationship("ProfilPersonnel", back_populates="user", uselist=False, cascade="all, delete-orphan")

  def set_password(self, password: str) -> None:
    self.password_hash = generate_password_hash(password)

  def check_password(self, password: str) -> bool:
    return check_password_hash(self.password_hash, password)

  def generate_verification_token(self) -> str:
    self.verification_token = secrets.token_urlsafe(32)
    return self.verification_token

  def __repr__(self) -> str:
    return f"<User {self.email}>"


class Cycle(db.Model):
  """Un cycle menstruel."""

  __tablename__ = "cycles"

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  date_debut_regles = db.Column(db.Date, nullable=False)
  date_fin = db.Column(db.Date, nullable=True)

  user = db.relationship("User", back_populates="cycles")
  observations = db.relationship("Observation", back_populates="cycle", cascade="all, delete-orphan")

  def __repr__(self) -> str:
    return f"<Cycle {self.id} user={self.user_id}>"


class Observation(db.Model):
  """Observation quotidienne."""

  __tablename__ = "observations"

  id = db.Column(db.Integer, primary_key=True)
  cycle_id = db.Column(db.Integer, db.ForeignKey("cycles.id"), nullable=False, index=True)
  date = db.Column(db.Date, nullable=False)

  # Température
  temp_brute = db.Column(db.Float, nullable=True)
  temp_corrigee = db.Column(db.Float, nullable=True)
  heure_prise = db.Column(db.Time, nullable=True)
  douteux = db.Column(db.Boolean, default=False, nullable=False)
  motif_doute = db.Column(db.String(50), nullable=True)

  # Glaire cervicale
  glaire_sensation = db.Column(db.String(30), nullable=True)  # seche | humide | mouillee_glissante
  glaire_aspect = db.Column(db.String(30), nullable=True)  # rien | collante_epaisse | cremeuse | filante_transparente

  # Col (optionnel)
  col_hauteur = db.Column(db.String(20), nullable=True)
  col_ouverture = db.Column(db.String(20), nullable=True)
  col_consistance = db.Column(db.String(20), nullable=True)

  # Autres
  saignement = db.Column(db.String(20), default="rien")  # rien | leger | regles
  union = db.Column(db.Boolean, default=False, nullable=False)
  test_lh = db.Column(db.String(20), nullable=True)  # negatif | positif

  cycle = db.relationship("Cycle", back_populates="observations")
  statut = db.relationship("Statut", back_populates="observation", uselist=False, cascade="all, delete-orphan")

  __table_args__ = (db.UniqueConstraint("cycle_id", "date", name="uq_observation_cycle_date"),)

  def __repr__(self) -> str:
    return f"<Observation {self.date} cycle={self.cycle_id}>"


class ProfilPersonnel(db.Model):
  """Statistiques personnelles apprises au fil des cycles (pas de ML)."""

  __tablename__ = "profils_personnels"

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

  cycle_moyen = db.Column(db.Float, nullable=True)
  cycle_min = db.Column(db.Integer, nullable=True)
  cycle_max = db.Column(db.Integer, nullable=True)
  ecart_type_cycle = db.Column(db.Float, nullable=True)
  jour_ovulation_moyen = db.Column(db.Float, nullable=True)
  temp_plateau_bas = db.Column(db.Float, nullable=True)
  temp_plateau_haut = db.Column(db.Float, nullable=True)
  amplitude_saut = db.Column(db.Float, nullable=True)
  heure_prise_habituelle = db.Column(db.Time, nullable=True)
  jour_apparition_glaire_moyen = db.Column(db.Float, nullable=True)
  pct_points_douteux = db.Column(db.Float, nullable=True)
  nb_cycles_enregistres = db.Column(db.Integer, default=0)

  user = db.relationship("User", back_populates="profil")

  def __repr__(self) -> str:
    return f"<ProfilPersonnel user={self.user_id}>"


class Statut(db.Model):
  """Cache du calcul moteur pour une observation."""

  __tablename__ = "statuts"

  id = db.Column(db.Integer, primary_key=True)
  observation_id = db.Column(db.Integer, db.ForeignKey("observations.id"), unique=True, nullable=False)
  phase = db.Column(db.String(30), nullable=False)
  feu = db.Column(db.String(10), nullable=False)
  confiance = db.Column(db.String(10), nullable=False)
  messages_json = db.Column(db.Text, nullable=True)

  observation = db.relationship("Observation", back_populates="statut")

  def __repr__(self) -> str:
    return f"<Statut obs={self.observation_id} feu={self.feu}>"
