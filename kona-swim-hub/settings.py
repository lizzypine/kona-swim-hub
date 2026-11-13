from pathlib import Path
from environs import Env
from decouple import config
import os
import subprocess
import ast

env = Env()
env.read_env()


def get_environ_vars():
    completed_process = subprocess.run(
        ["/opt/elasticbeanstalk/bin/get-config", "environment"],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )

    return ast.literal_eval(completed_process.stdout)


# Set the project base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
DEBUG = env.bool("DEBUG", default=False)

TURNSTILE_SITEKEY = os.getenv("TURNSTILE_SITEKEY") or (
    "1x00000000000000000000AA" if DEBUG else ""
)
TURNSTILE_SECRET = os.getenv("TURNSTILE_SECRET") or (
    "1x0000000000000000000000000000000AA" if DEBUG else ""
)

# AWS EB
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
)

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".konaswimhub.com",
    "konaswimhub.com",
    "kona-swim-hub-prod2.us-west-1.elasticbeanstalk.com",
]

# Application definition
INSTALLED_APPS = [
    "lessons.apps.LessonsConfig",
    "accounts.apps.AccountsConfig",
    "pages.apps.PagesConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django_bootstrap5",
    "turnstile",
    "bootstrap_datepicker_plus",
    "django.forms",
    "crispy_forms",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "kona-swim-hub.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "kona-swim-hub.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

if env.str("DATABASE_URL", default=""):
    DATABASES = {"default": env.dj_db_url("DATABASE_URL")}
elif "RDS_HOSTNAME" in os.environ:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.environ["RDS_DB_NAME"],
            "USER": os.environ["RDS_USERNAME"],
            "PASSWORD": os.environ["RDS_PASSWORD"],
            "HOST": os.environ["RDS_HOSTNAME"],
            "PORT": os.environ["RDS_PORT"],
        }
    }

else:
    DATABASES = {"default": env.dj_db_url("DATABASE_URL")}

default_database = DATABASES["default"]
if "postgresql" in default_database["ENGINE"]:
    default_database["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
    default_database["CONN_HEALTH_CHECKS"] = True
    default_database.setdefault("DISABLE_SERVER_SIDE_CURSORS", True)

    if default_database.get("HOST", "").endswith(".neon.tech"):
        default_database.setdefault("OPTIONS", {}).setdefault("sslmode", "require")

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "..", "www", "static")

if "AWS_STORAGE_BUCKET_NAME" in os.environ:
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

    AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
    AWS_S3_REGION_NAME = os.environ["AWS_S3_REGION_NAME"]

    AWS_S3_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
    AWS_S3_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

TIME_INPUT_FORMATS = [
    "%I:%M %p",
]

AUTH_USER_MODEL = "accounts.CustomUser"

AUTH_PROFILE_MODULE = "accounts.UserProfile"

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend"
    if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=10)
CONTACT_EMAIL = "Kona Swim Hub <team@konaswimhub.com>"
DEFAULT_FROM_EMAIL = "Kona Swim Hub <team@konaswimhub.com>"
