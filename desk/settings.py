import os
from django.core.management.utils import get_random_secret_key

DEBUG = os.getenv("FRONTDESK_LOCAL") == "1"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or (get_random_secret_key() if DEBUG else os.environ["DJANGO_SECRET_KEY"])
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = [s for s in os.getenv("TRUSTED_ORIGINS", "").split(",") if s]
ROOT_URLCONF = "desk.urls"
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "desk"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
USE_TZ = True
TIME_ZONE = "Asia/Kolkata"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"
TEMPLATES = [{"BACKEND":"django.template.backends.django.DjangoTemplates","APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth"]}}]
DATABASES = {"default":{"ENGINE":"django.db.backends.postgresql","NAME":os.getenv("PGDATABASE","frontdesk"),"USER":os.getenv("PGUSER","frontdesk_app"),"PASSWORD":os.environ["FRONTDESK_DB_PASSWORD"],"HOST":os.getenv("PGHOST","localhost"),"PORT":os.getenv("PGPORT","5432")}}
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = not DEBUG
