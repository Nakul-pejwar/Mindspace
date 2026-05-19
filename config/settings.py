"""
Django settings for MindSpace project.
Project structure:
BASE_DIR/
├── config/
├── mindspace/
├── templates/
├── static/
├── media/
└── manage.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    ""
)

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost"
).split(",")


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "django.contrib.sites",
    "django.contrib.postgres",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    "mindspace",
]

SITE_ID = 2

# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ============================================================
# URL / WSGI
# ============================================================

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        # Your templates folder is directly inside BASE_DIR
        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ============================================================
# DATABASE
# ============================================================
# Development: SQLite
# Later you can switch to PostgreSQL safely.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "mds"),
        "USER": os.environ.get("DB_USER", "mds_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "google_login_redirect"
LOGOUT_REDIRECT_URL = "login"

ACCOUNT_LOGIN_REDIRECT_URL = "google_login_redirect"
ACCOUNT_SIGNUP_REDIRECT_URL = "google_login_redirect"

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"

SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "OAUTH_PKCE_ENABLED": True,
    }
}

# ============================================================
# LANGUAGE / TIMEZONE
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# ============================================================
# MEDIA FILES
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# EMAIL SETTINGS
# ============================================================
# For development, emails print in terminal.

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = "MindSpace <noreply@mindspace.local>"


# ============================================================
# SESSION / CSRF SETTINGS
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"


# ============================================================
# MESSAGES
# ============================================================

from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: "debug",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "error",
}


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# LOCAL API CONFIG FOR MINDSPACE PIPELINE
# ============================================================
# You can use these later in assessments/views.py

FACE_EXTRACT_URL = os.environ.get(
    "FACE_EXTRACT_URL",
    "http://88.222.12.15:5100/extract/video"
)

FACE_SCORE_URL = os.environ.get(
    "FACE_SCORE_URL",
    "http://127.0.0.1:8011"
)

VOICE_FEATURE_URL = os.environ.get(
    "VOICE_FEATURE_URL",
    "http://127.0.0.1:8013"
)

VOICE_SCORE_URL = os.environ.get(
    "VOICE_SCORE_URL",
    "http://127.0.0.1:9100"
)

TEXT_PARAMETER_URL = os.environ.get(
    "TEXT_PARAMETER_URL",
    "http://127.0.0.1:8025"
)

TEXT_SCORE_URL = os.environ.get(
    "TEXT_SCORE_URL",
    "http://127.0.0.1:9000"
)

FUSION_API_URL = os.environ.get(
    "FUSION_API_URL",
    "http://127.0.0.1:8000"
)