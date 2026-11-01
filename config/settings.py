# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

"""
Django settings for the Study Planner project.

Sensitive and environment-specific values are read from environment
variables, which may be supplied by a local .env file (see .env.example).
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load variables from .env if present. Real environment variables take precedence.
load_dotenv(BASE_DIR / '.env')


def env_list(name, default=''):
    """Return a comma-separated environment variable as a list of non-empty strings."""
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


def env_bool(name, default=False):
    """Return an environment variable as a boolean ('true', '1' or 'yes' mean True)."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in ('true', '1', 'yes')


# SECURITY: the secret key must come from the environment and is never hardcoded.
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY environment variable is not set.')

# SECURITY: debug is off unless explicitly enabled.
DEBUG = env_bool('DJANGO_DEBUG', False)

# Local development defaults; deployment sets DJANGO_ALLOWED_HOSTS explicitly
# (e.g. dev-student17.fhsucyber.com).
ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')

# Required when the site is served over HTTPS through a reverse proxy,
# e.g. https://dev-student17.fhsucyber.com. Empty for local development.
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')

# Send session and CSRF cookies only over HTTPS. On by default when DEBUG is off
# (the deployed site is reached through HTTPS); off for local HTTP development.
# Set DJANGO_SECURE_COOKIES explicitly to override.
SECURE_COOKIES = env_bool('DJANGO_SECURE_COOKIES', not DEBUG)
SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SECURE = SECURE_COOKIES

# SECURE_SSL_REDIRECT, SECURE_PROXY_SSL_HEADER and HSTS are intentionally not enabled:
# HTTPS is handled by the course reverse proxy, whose forwarded headers have not been
# verified. Enabling them without that verification could cause redirect loops.


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # Lets WhiteNoise serve static files under runserver, just as it does when DEBUG=False.
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'planner',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Serves files from STATIC_ROOT (after collectstatic) even when DEBUG=False.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Chicago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise compresses collected files (gzip/Brotli when available). The non-manifest
# storage is used so templates still render if collectstatic has not been run (e.g. tests).
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication redirects (URL pattern names)

LOGIN_URL = 'planner:login'
LOGIN_REDIRECT_URL = 'planner:dashboard'
LOGOUT_REDIRECT_URL = 'planner:home'
