# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'imagekit',  # https://github.com/matthewwithanm/django-imagekit
    'rest_framework',  # https://www.django-rest-framework.org/
    'rest_framework.authtoken',
    'dbbackup',  # https://django-dbbackup.readthedocs.io/en/stable/installation.html
    'debug_toolbar', #https://django-debug-toolbar.readthedocs.io/en/latest/installation.html

    'accounts',
    'fabutils',
    'orgues'

]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],

    # or allow read-only access for unauthenticated users.
    # https://www.django-rest-framework.org/api-guide/permissions/
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50
}

DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': '/home/fabdev/data/db_saved'}
DBBACKUP_CLEANUP_KEEP = 10

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost'
]
