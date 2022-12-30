from pathlib import Path
# from environs import Env
import environ
import os

# env = Env()
# env.read_env()
# env = environ.Env()
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)
# environ.Env.read_env()

# Set the project base directory
BASE_DIR = Path(__file__).resolve().parent.parent
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = env.bool('DEBUG', default=False)
DEBUG = env('DEBUG')

# SECRET_KEY = env.str('SECRET_KEY')
SECRET_KEY = env('SECRET_KEY')

ALLOWED_HOSTS = ['.herokuapp.com', 'localhost', '127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'lessons.apps.LessonsConfig',
    'accounts.apps.AccountsConfig',
    'pages.apps.PagesConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'bootstrap5',
    'bootstrap_datepicker_plus',
    'django.forms',
    'crispy_forms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

ROOT_URLCONF = 'django_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'),],
        #'DIRS': [str(BASE_DIR.joinpath('templates'))],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages'
            ],
        },
    },
]

WSGI_APPLICATION = 'django_project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    # 'default': env.dj_db_url('DATABASE_URL')
    # 'default': ('DATABASE_URL')
    'default': env.db(),

    'extra': env.db_url(
        'SQLITE_URL',
        default='sqlite:///db.sqlite3'
    )
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# STATICFILES_DIRS = [str(BASE_DIR.joinpath('static'))]
# STATIC_ROOT = str(BASE_DIR.joinpath('staticfiles'))

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

TIME_INPUT_FORMATS = ['%I:%M %p',]

AUTH_USER_MODEL = 'accounts.CustomUser'

AUTH_PROFILE_MODULE = 'accounts.UserProfile'

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL")
# DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
DEFAULT_FROM_EMAIL = 'lizzy@lehuaweb.com'
# CONTACT_EMAIL = env.str("CONTACT_EMAIL")
# CONTACT_EMAIL = env('CONTACT_EMAIL')
CONTACT_EMAIL = 'lizzy@lehuaweb.com'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'
# SENDGRID_API_KEY = env.str('SENDGRID_API_KEY')
SENDGRID_API_KEY = env('SENDGRID_API_KEY')
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
# EMAIL_HOST_PASSWORD = env('SENDGRID_API_KEY')
EMAIL_PORT = 587
EMAIL_USE_TLS = True