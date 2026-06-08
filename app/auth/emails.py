from flask import current_app, render_template, url_for
from flask_mail import Message

from app.extensions import mail


def send_verification_email(user) -> bool:
  """Envoie l'e-mail de validation de compte. Retourne True si envoyé."""
  token = user.verification_token
  if not token:
    token = user.generate_verification_token()

  verify_url = f"{current_app.config['BASE_URL']}/auth/verify/{token}"

  msg = Message(
    subject="Confirmez votre compte — RNN App",
    recipients=[user.email],
    html=render_template("auth/email_verify.html", user=user, verify_url=verify_url),
    body=(
      f"Bonjour,\n\n"
      f"Merci de vous être inscrit(e) sur l'application RNN.\n"
      f"Confirmez votre adresse e-mail en cliquant sur ce lien :\n{verify_url}\n\n"
      f"Ce lien expire dans 48 heures.\n\n"
      f"— L'équipe RNN App"
    ),
  )

  try:
    mail.send(msg)
    return True
  except Exception:
    current_app.logger.exception("Échec d'envoi de l'e-mail de vérification")
    return False
