import os
from .base import BASE_DIR

SECRET_KEY = 'THIS_KEY_WILL_BE_CHANGED'
DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

WSGI_APPLICATION = 'project.wsgi.application'

FABACCESSLOG_FILE = 'fabaccess.log'
SEARCHLOG_FILE = 'search.log'
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
        'searchlogfile': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': SEARCHLOG_FILE,
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
        'search': {
            'handlers': ['searchlogfile'],
            'level': 'INFO',
        },
    },
}

CAPTCHA_SECRET  = "KJOKJLJLKJ"
