from flask import Flask

from app.config import Config
from app.extensions import csrf, db, login_manager, mail, migrate
from app.models import User


def create_app(config_class=Config):
  """Fabrique d'application Flask."""
  app = Flask(__name__)
  app.config.from_object(config_class)

  db.init_app(app)
  migrate.init_app(app, db)
  login_manager.init_app(app)
  mail.init_app(app)
  csrf.init_app(app)

  @login_manager.user_loader
  def load_user(user_id):
    return db.session.get(User, int(user_id))

  from app.auth import auth_bp
  from app.main import main_bp

  app.register_blueprint(auth_bp)
  app.register_blueprint(main_bp)

  return app
