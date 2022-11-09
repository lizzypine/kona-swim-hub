import environ
import os

# env = environ.Env(
#     DEBUG=(bool, False)
# )

env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# BASE_DIR = Path(__file__).resolve().parent.parent

# Get environment variables from the .env file
# environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# SECURITY WARNING: keep the secret key used in production secret!
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
    'django.contrib.staticfiles',
    'bootstrap5',
    'bootstrap_datepicker_plus',
    'django.forms',
    'django_filters',
    'crispy_forms',
    # "sendemail.apps.SendemailConfig"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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
        # 'DIRS': [str(BASE_DIR.joinpath('templates'))],
        'DIRS': [os.path.join(BASE_DIR, 'templates'),],
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
    'default': env.db(),

    # read os.environ['SQLITE_URL']
    'extra': env.db_url(
        'SQLITE_URL',
        default='sqlite:////tmp/my-tmp-sqlite.db'
    )
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': env("DATABASE_NAME"),
#         'USER': env("DATABASE_USER"),
#         'PASSWORD': env("DATABASE_PASSWORD"),
#         'HOST': env("DATABASE_HOST"),
#         'PORT': env("DATABASE_PORT"),
#     }
# }


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
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'),]

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

TIME_INPUT_FORMATS = ['%I:%M %p',]

AUTH_USER_MODEL = 'accounts.CustomUser'

AUTH_PROFILE_MODULE = 'accounts.UserProfile'

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

# EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'


# DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
# DEFAULT_FROM_EMAIL = 'lehuaweb@gmail.com'

# EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')
# SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

# Toggle sandbox mode (when running in DEBUG mode)
# SENDGRID_SANDBOX_MODE_IN_DEBUG=False

# echo to stdout or any other file-like object that is passed to the backend via the stream kwarg.
# SENDGRID_ECHO_TO_STDOUT=True

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
CONTACT_EMAIL = env('CONTACT_EMAIL')
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'
SENDGRID_API_KEY = env('SENDGRID_API_KEY')
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True