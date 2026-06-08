from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth.emails import send_verification_email
from app.auth.forms import LoginForm, RegisterForm
from app.extensions import db
from app.models import ProfilPersonnel, User

from . import auth_bp


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
  if current_user.is_authenticated:
    return redirect(url_for("main.accueil"))

  form = RegisterForm()
  if form.validate_on_submit():
    user = User(email=form.email.data.lower().strip())
    user.set_password(form.password.data)
    user.generate_verification_token()

    db.session.add(user)
    db.session.add(ProfilPersonnel(user=user))
    db.session.commit()

    email_sent = send_verification_email(user)
    if email_sent:
      flash(
        "Compte créé ! Consultez votre boîte e-mail pour confirmer votre adresse avant de vous connecter.",
        "success",
      )
    else:
      flash(
        "Compte créé, mais l'e-mail de vérification n'a pas pu être envoyé. "
        "Utilisez « Renvoyer la vérification » depuis la page de connexion.",
        "warning",
      )
    return redirect(url_for("auth.login"))

  return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
  if current_user.is_authenticated:
    return redirect(url_for("main.accueil"))

  form = LoginForm()
  unverified_email = None

  if form.validate_on_submit():
    user = User.query.filter_by(email=form.email.data.lower().strip()).first()

    if user is None or not user.check_password(form.password.data):
      flash("E-mail ou mot de passe incorrect.", "danger")
      return render_template("auth/login.html", form=form)

    if not user.email_verified:
      unverified_email = user.email
      flash(
        "Votre adresse e-mail n'est pas encore vérifiée. Consultez votre boîte de réception.",
        "warning",
      )
      return render_template(
        "auth/login.html",
        form=form,
        unverified_email=unverified_email,
      )

    login_user(user, remember=form.remember.data)

    if not user.avertissement_lu:
      return redirect(url_for("main.a_lire"))
    if not user.onboarding_complete:
      return redirect(url_for("main.onboarding"))

    flash("Connexion réussie.", "success")
    return redirect(url_for("main.accueil"))

  return render_template("auth/login.html", form=form)


@auth_bp.route("/verify/<token>")
def verify_email(token):
  user = User.query.filter_by(verification_token=token).first()

  if user is None:
    flash("Lien de vérification invalide ou déjà utilisé.", "danger")
    return redirect(url_for("auth.login"))

  user.email_verified = True
  user.verification_token = None
  db.session.commit()

  flash("Votre adresse e-mail est confirmée. Vous pouvez vous connecter.", "success")
  return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
  email = request.form.get("email", "").lower().strip()

  if not email:
    flash("Adresse e-mail manquante.", "danger")
    return redirect(url_for("auth.login"))

  user = User.query.filter_by(email=email).first()
  if user is None:
    flash("Aucun compte trouvé pour cette adresse.", "danger")
    return redirect(url_for("auth.login"))

  if user.email_verified:
    flash("Cette adresse e-mail est déjà vérifiée.", "info")
    return redirect(url_for("auth.login"))

  user.generate_verification_token()
  db.session.commit()

  if send_verification_email(user):
    flash("Un nouvel e-mail de vérification a été envoyé.", "success")
  else:
    flash("Impossible d'envoyer l'e-mail. Réessayez plus tard.", "danger")

  return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
@login_required
def logout():
  logout_user()
  flash("Vous êtes déconnecté(e).", "info")
  return redirect(url_for("main.accueil"))
