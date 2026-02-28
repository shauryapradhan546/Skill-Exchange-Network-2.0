"""
settings.py — Django Project Configuration

This is the central configuration file for the entire Django project.
All settings (database, auth, email, static files, etc.) are defined here.

Important sections:
    - INSTALLED_APPS: Which Django apps are active
    - MIDDLEWARE: Request/response processing pipeline
    - TEMPLATES: How Django finds and renders HTML templates
    - DATABASES: Which database to use (SQLite for development)
    - AUTH: Custom user model and authentication backends
    - REST_FRAMEWORK: Django REST Framework config (for API endpoints)
    - EMAIL/TWILIO: Notification services configuration
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths relative to the project root directory
# BASE_DIR = d:\Updated Field Project\updated_skill_exchange_network
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: Keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-to-your-secret-key')

# SECURITY WARNING: Set to False in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

# List of allowed hostnames — add your domain here for production
ALLOWED_HOSTS = []


# ============================================
# INSTALLED APPS
# ============================================
# Order matters: Django apps first, then third-party, then our apps

INSTALLED_APPS = [
    'django.contrib.admin',         # Admin panel
    'django.contrib.auth',          # Authentication system
    'django.contrib.contenttypes',  # Content type framework (used by auth)
    'django.contrib.sessions',      # Session management
    'django.contrib.messages',      # Flash messages (success/error alerts)
    'django.contrib.staticfiles',   # Serves CSS/JS/images
    'rest_framework',               # Django REST Framework for API endpoints
    'core',                         # Our main application
]


# ============================================
# MIDDLEWARE
# ============================================
# Middleware processes every request/response in order.
# Think of it as a pipeline: Request → Middleware1 → Middleware2 → View → Response

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',            # HTTPS redirects, security headers
    'django.contrib.sessions.middleware.SessionMiddleware',     # Enables sessions (login state)
    'django.middleware.common.CommonMiddleware',                # URL normalization, content-length
    'django.middleware.csrf.CsrfViewMiddleware',               # CSRF protection for forms
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Attaches user to request
    'django.contrib.messages.middleware.MessageMiddleware',     # Flash messages support
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Prevents clickjacking attacks
]

ROOT_URLCONF = 'updated_skill_exchange_network.urls'


# ============================================
# TEMPLATES
# ============================================
# Tells Django where to find HTML templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # Additional directories to search for templates
        # Note: 'templetes' is a typo but kept for compatibility with existing setup
        'DIRS': [BASE_DIR / 'core' / 'templetes'],

        # APP_DIRS=True means Django also looks in each app's "templates/" folder
        # This is how core/templates/core/*.html files are found
        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',      # Adds 'debug' variable to templates
                'django.template.context_processors.request',    # Adds 'request' object to templates
                'django.contrib.auth.context_processors.auth',   # Adds 'user' and 'perms' to templates
                'django.contrib.messages.context_processors.messages',  # Adds 'messages' for flash alerts
                'core.context_processors.firebase_config',       # Adds Firebase config to all templates
            ],
        },
    },
]

WSGI_APPLICATION = 'updated_skill_exchange_network.wsgi.application'


# ============================================
# DATABASE
# ============================================
# Using SQLite for development — switch to PostgreSQL for production

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # Creates db.sqlite3 in the project root
    }
}

# No password validators in development — add them for production!
AUTH_PASSWORD_VALIDATORS = []


# ============================================
# INTERNATIONALIZATION
# ============================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'   # Indian Standard Time (UTC+5:30)
USE_I18N = True
USE_TZ = True


# ============================================
# STATIC FILES (CSS, JavaScript, Images)
# ============================================
# STATIC_URL: The URL prefix for static files (e.g., /static/css/style.css)
# STATICFILES_DIRS: Where Django looks for static files during development
# STATIC_ROOT: Where collectstatic gathers all static files for production

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'core' / 'static',  # Our app's static directory
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  # For production: python manage.py collectstatic


# ============================================
# AUTHENTICATION
# ============================================
# Use our custom User model instead of Django's default User

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.User'  # Points to our User model in core/models.py

# Django REST Framework — supports both session auth (browser) and Firebase auth (mobile/API)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',    # For browser sessions
        'core.authentication.FirebaseAuthentication',             # For Firebase token auth
    )
}


# ============================================
# FIREBASE
# ============================================
# Set to {} to disable Firebase auth (runs in local-only mode)
# To enable: replace with your Firebase service account JSON credentials

FIREBASE_SERVICE_ACCOUNT = {}

# Firebase client-side config — read from .env file
# These are passed to JavaScript via the 'firebase_config' context processor
FIREBASE_CONFIG = {
    'apiKey': os.getenv('FIREBASE_API_KEY', ''),
    'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN', ''),
    'projectId': os.getenv('FIREBASE_PROJECT_ID', ''),
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', ''),
    'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID', ''),
    'appId': os.getenv('FIREBASE_APP_ID', ''),
    'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID', ''),
}


# ============================================
# EMAIL CONFIGURATION
# ============================================
# ConsoleEmailBackend prints emails to the terminal instead of sending them
# For production, switch to: 'django.core.mail.backends.smtp.EmailBackend'
# and configure EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@updated-skill-exchange.test"


# ============================================
# TWILIO (WhatsApp Notifications)
# ============================================
# Set these environment variables to enable WhatsApp notifications:
#   TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
# Leave empty to disable WhatsApp (the app works without it)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
