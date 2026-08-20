"""
config.py
Central configuration for the Flask app. Reads sensitive values from
environment variables so nothing secret is hard-coded for production use.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core Flask / security -------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-this-in-production")
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Flip to True automatically when served over HTTPS in production (Render/Railway set this)
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 2  # 2 hours

    # --- Database ----------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'fake_news.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- ML model paths ------------------------------------------------------------
    MODEL_DIR = os.path.join(BASE_DIR, "model")
    MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
    VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")
    METADATA_PATH = os.path.join(MODEL_DIR, "metadata.pkl")

    # --- Dataset paths -------------------------------------------------------------
    DATASET_DIR = os.path.join(BASE_DIR, "dataset")
    TRUE_CSV = os.path.join(DATASET_DIR, "True.csv")
    FAKE_CSV = os.path.join(DATASET_DIR, "Fake.csv")

    # --- Default admin account (created on first run if it doesn't exist) --------
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@12345")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@fakenewsdetector.local")

    # --- Misc ------------------------------------------------------------------------
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB max request body (basic DoS guard)
    HISTORY_PAGE_SIZE = 10
