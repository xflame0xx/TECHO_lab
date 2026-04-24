import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-key")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "storages",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.Urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.Wsgi.application"
ASGI_APPLICATION = "config.Asgi.application"

USE_SQLITE = os.getenv("DJANGO_USE_SQLITE", "False").lower() == "true"

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "db"),
            "USER": os.getenv("POSTGRES_USER", "admin"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "root"),
            "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.getenv("POSTGRES_PORT", "54322"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "core" / "static"]

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

USE_MINIO = os.getenv("DJANGO_USE_MINIO", "True").lower() == "true"

if USE_MINIO:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "access_key": os.getenv("MINIO_ROOT_USER", "minioadmin"),
                "secret_key": os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123"),
                "bucket_name": os.getenv("MINIO_BUCKET", "jobability"),
                "endpoint_url": os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000"),
                "region_name": "us-east-1",
                "default_acl": None,
                "querystring_auth": False,
                "addressing_style": "path",
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    MEDIA_URL = os.getenv("MINIO_PUBLIC_MEDIA_URL", "http://127.0.0.1:9000/jobability/")

USE_REDIS_SESSIONS = os.getenv("DJANGO_USE_REDIS_SESSIONS", "False").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1")

if USE_REDIS_SESSIONS:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "jobability",
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/login/"

SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.authentication.CookieSessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "JobAbility API",
    "DESCRIPTION": (
        "API для лабораторной 4: регистрация, вход по session-cookie, роли "
        "соискателя/работодателя/модератора, работа с вакансиями и заявками. "
        "Для демонстрации в Swagger сначала выполните POST /api/users/login/, "
        "после чего cookie sessionid будет использована браузером автоматически."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
    },
    "TAGS": [
        {"name": "auth", "description": "Регистрация, вход, выход и текущий пользователь."},
        {"name": "vacancies", "description": "Вакансии и модерация вакансий."},
        {"name": "applications", "description": "Заявки и работа с ними."},
    ],
}
