"""
database.py
Holds the shared SQLAlchemy instance so models.py and app.py can both
import it without circular imports.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Attach the db instance to the Flask app and create tables."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _seed_admin(app)


def _seed_admin(app):
    """Create a default admin user on first run if none exists."""
    from models import User  # local import avoids circular dependency

    if not User.query.filter_by(is_admin=True).first():
        admin = User(
            username=app.config["ADMIN_USERNAME"],
            email=app.config["ADMIN_EMAIL"],
            is_admin=True,
        )
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
