from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.models import User


class RegisterForm(FlaskForm):
  email = StringField("Adresse e-mail", validators=[DataRequired(), Email(), Length(max=255)])
  password = PasswordField(
    "Mot de passe",
    validators=[DataRequired(), Length(min=8, message="Minimum 8 caractères.")],
  )
  password_confirm = PasswordField(
    "Confirmer le mot de passe",
    validators=[DataRequired(), EqualTo("password", message="Les mots de passe ne correspondent pas.")],
  )
  accept_disclaimer = BooleanField(
    "J'ai lu et compris que cette application n'est pas un dispositif médical",
    validators=[DataRequired(message="Vous devez accepter cet avertissement.")],
  )
  submit = SubmitField("Créer mon compte")

  def validate_email(self, field):
    if User.query.filter_by(email=field.data.lower().strip()).first():
      raise ValidationError("Cette adresse e-mail est déjà utilisée.")


class LoginForm(FlaskForm):
  email = StringField("Adresse e-mail", validators=[DataRequired(), Email()])
  password = PasswordField("Mot de passe", validators=[DataRequired()])
  remember = BooleanField("Se souvenir de moi")
  submit = SubmitField("Se connecter")

