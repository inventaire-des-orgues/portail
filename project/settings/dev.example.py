import os
from .base import BASE_DIR

SECRET_KEY = 'THIS_KEY_WILL_BE_CHANGED'
DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

WSGI_APPLICATION = 'project.wsgi.application'
