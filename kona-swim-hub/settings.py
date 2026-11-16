from pathlib import Path
from environs import Env
import os

env = Env()
env.read_env()


def split_csv(value):
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def parse_proxy_header(value):
    if not value:
        return ("HTTP_X_FORWARDED_PROTO", "https")
    if isinstance(value, tuple) and len(value) == 2:
        return value
    if isinstance(value, str):
        header, sep, scheme = value.partition(":")
        if sep:
            return (header, scheme)
    return ("HTTP_X_FORWARDED_PROTO", "https")


# Set the project base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

TURNSTILE_SITEKEY = os.getenv("TURNSTILE_SITEKEY") or (
    "1x00000000000000000000AA" if DEBUG else ""
)
TURNSTILE_SECRET = os.getenv("TURNSTILE_SECRET") or (
    "1x0000000000000000000000000000000AA" if DEBUG else ""
)

SECRET_KEY = os.environ.get("SECRET_KEY")

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "kona-swim-hub.service.local",
    ".konaswimhub.com",
    "konaswimhub.com",
]
ALLOWED_HOSTS.extend(split_csv(os.getenv("ALLOWED_HOSTS", "")))
ALLOWED_HOSTS.extend(split_csv(os.getenv("ALLOWED_HOSTS_EXTRA", "")))
ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS))

CSRF_TRUSTED_ORIGINS = [
    "https://konaswimhub.com",
    "https://www.konaswimhub.com",
    *split_csv(os.getenv("CSRF_TRUSTED_ORIGINS", "")),
    *split_csv(os.getenv("CSRF_TRUSTED_ORIGINS_EXTRA", "")),
]
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS))

SECURE_PROXY_SSL_HEADER = parse_proxy_header(os.getenv("SECURE_PROXY_SSL_HEADER"))

# Application definition
INSTALLED_APPS = [
    "inbound.apps.InboundConfig",
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
    "pages.middleware.HealthCheckMiddleware",
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
STATIC_ROOT = os.getenv("STATIC_ROOT", os.path.join(BASE_DIR, "..", "www", "static"))

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
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "team@konaswimhub.com")
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", "Kona Swim Hub <team@notifications.konaswimhub.com>"
)

# Inbound forwarding uses the HTTP API independently of existing outgoing SMTP.
RESEND_API_KEY = os.getenv("RESEND_API_KEY") or (
    EMAIL_HOST_PASSWORD if EMAIL_HOST.lower() == "smtp.resend.com" else ""
)
RESEND_WEBHOOK_SECRET = os.getenv("RESEND_WEBHOOK_SECRET", "")
EMAIL_FORWARD_TO = os.getenv("EMAIL_FORWARD_TO", "")
RESEND_INBOUND_ADDRESS = os.getenv("RESEND_INBOUND_ADDRESS", "team@ilkaxle.resend.app")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"inbound_console": {"class": "logging.StreamHandler"}},
    "loggers": {"inbound": {"handlers": ["inbound_console"], "level": "INFO", "propagate": False}},
}
