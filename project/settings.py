import sys
import os
from pathlib import Path
import deploymentutils as du
import time


# export DJANGO_DEVMODE=True; py3 manage.py custom_command
env_devmode = os.getenv("DJANGO_DEVMODE")
if env_devmode is None:
    DEVMODE = "runserver" in sys.argv or "shell" in sys.argv
else:
    DEVMODE = env_devmode.lower() == "true"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.as_posix()

cwd = None# os.getcwd()
try:
    cfg = du.get_nearest_config("config.toml", devmode=DEVMODE)
except FileNotFoundError:
    if 1:
        try:
            cfg = du.get_nearest_config("config-example.toml", devmode=DEVMODE)
        except FileNotFoundError:
            msg = "could not find neither `config.toml` nor config-example.toml`"
            raise FileNotFoundError(msg)
        msg = "Could not find `config.toml. Using `config-example.toml instead."
    print(du.yellow("Warning:"), msg)

SECRET_KEY = cfg("SECRET_KEY")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = cfg("DEBUG")
BASE_URL = cfg("BASE_URL")

# displays a nice error page instead of a traceback
# can be deactivated for debugging
CATCH_EXCEPTIONS = True

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/


ALLOWED_HOSTS = cfg("ALLOWED_HOSTS")


# Collect static files here (will be copied to correct location by deployment script)
STATIC_ROOT = cfg("STATIC_ROOT").replace("__BASEDIR__", BASE_DIR)

# Collect media files here (unclear whether we need this, copied from codequiz)
MEDIA_ROOT = cfg("MEDIA_ROOT").replace("__BASEDIR__", BASE_DIR)

# not yet used
BACKUP_PATH = os.path.abspath(cfg("BACKUP_PATH").replace("__BASEDIR__", BASE_DIR))


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django_bleach',
    "base",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # TODO: make this more professional
    # this line should be commented out for debugging
    "base.error_handler.ErrorHandlerMiddleware"
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(BASE_DIR) / cfg("DB_FILE_NAME"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


BLEACH_ALLOWED_TAGS = [
    'p', 'b', 'i', 'u', 'em', 'strong', 'a', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'ul', 'ol', 'li', 'pre', 'code'
] + ["br", "hr", "blockquote"]
BLEACH_STRIP_COMMENTS = False


BLEACH_ALLOWED_ATTRIBUTES = {
    "*": ["id", "style"],
    "img": ["src"],
    "a": ["href"],
}

BLEACH_ALLOWED_STYLES = [
    'font-family', 'font-weight', 'text-decoration', 'font-variant'
]
