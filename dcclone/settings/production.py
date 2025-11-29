from .base import *  # noqa

DEBUG = False

DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME":  os.getenv("POSTGRESQL_DATABASE"),
    "USER": os.getenv("POSTGRESQL_USERNAME"),
    "PASSWORD": os.getenv("POSTGRESQL_PASSWORD"),
    "HOST": "pg-0",
    "PORT": "5432",
}}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/1"),
    }
}

STATIC_URL = '/static_b/'
STATIC_ROOT = Path('/front/static')
MEDIA_URL = '/media/'
MEDIA_PRIV_URL = '/api/file/'
MEDIA_ROOT = Path('/media')
