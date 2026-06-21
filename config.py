"""
DFEMS – Configuration
Reads from environment variables (or a .env file via python-dotenv).
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask ─────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-please")
    DEBUG = False
    TESTING = False

    # ── Database ──────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://dfems_user:dfems_pass@localhost/dfems_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_recycle": 280, "pool_pre_ping": True}

    # ── JWT ───────────────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "false").lower() == "true"
    JWT_COOKIE_CSRF_PROTECT = False  # Handled separately in production

    # ── File uploads ──────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    REPORTS_FOLDER = os.path.join(os.path.dirname(__file__), "reports")
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB
    ALLOWED_EXTENSIONS = {
        "png", "jpg", "jpeg", "gif", "bmp", "tiff",
        "pdf", "doc", "docx", "xls", "xlsx", "txt",
        "zip", "tar", "gz", "7z",
        "log",
        "pcap", "pcapng",
        "bin", "raw", "img", "dd", "mem",
        "csv", "json", "xml",
    }

    # ── Pagination ────────────────────────────────────────────────────────
    ITEMS_PER_PAGE = 15


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = True
