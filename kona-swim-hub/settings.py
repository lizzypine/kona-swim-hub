from pathlib import Path
from environs import Env
from decouple import config
import os

env = Env()
env.read_env()

# Set the project base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

# AWS EB
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1").lower() in ["true", "t", "1"]

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".konaswimhub.com",
    "ksh-dev.us-west-1.elasticbeanstalk.com",
]

# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# SECURE_SSL_REDIRECT = True

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
    "bootstrap5",
    "bootstrap_datepicker_plus",
    "django.forms",
    "crispy_forms",
    "storages",
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


if "RDS_DB_NAME" in os.environ:
    # if "RDS_HOSTNAME" in os.environ:
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
    # DATABASES = {"default": env.dj_db_url("DATABASE_URL")}

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }

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

# Remove?
# USE_S3 = os.getenv("USE_S3") == "TRUE"

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

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = os.getenv("SENDGRID_API_KEY")
CONTACT_EMAIL = "Kona Swim Hub <team@konaswimhub.com>"
DEFAULT_FROM_EMAIL = "Kona Swim Hub <team@konaswimhub.com>"
