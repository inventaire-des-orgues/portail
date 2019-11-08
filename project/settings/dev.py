import os
from .base import BASE_DIR

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'vh4*k+T!-P6RSG&7wv4ZP3ZYFm7qc!bnDj2caKPa+Gw#J5hK=+rrX=reTv5S'  # TODO CHANGE THE WHOLE KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

WSGI_APPLICATION = 'project.wsgi.application'

FABACCESSLOG_FILE = 'fabaccess.log'
LOG_DATEFMT = '%Y-%m-%d %H:%M'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'csvformatted': {
            'format': '{asctime};{levelname};{message}',
            'datefmt': LOG_DATEFMT,
            'style': '{'
        },
        'simple': {
            'format': '[{asctime}] [{levelname}] {message}',
            'datefmt': LOG_DATEFMT,
            'style': '{'
        }
    },
    'handlers': {
        'fabaccesslogfile': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': FABACCESSLOG_FILE,
            'maxBytes': 3 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'csvformatted'
        },
    },
    'loggers': {
        'fabaccess': {
            'handlers': ['fabaccesslogfile'],
            'level': 'DEBUG',
        },
    },
}
