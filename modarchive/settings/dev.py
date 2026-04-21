import tempfile
from modarchive.settings.base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

IS_RECAPTCHA_ENABLED = False

BASE_URL = 'http://localhost:8000'

TEMP_UPLOAD_DIR = os.getenv('TEMP_UPLOAD_DIR', tempfile.mkdtemp(prefix='temp_uploads_'))
NEW_FILE_DIR = os.getenv('NEW_FILE_DIR', tempfile.mkdtemp(prefix='new_files_'))
MAIN_ARCHIVE_DIR = os.getenv('MAIN_ARCHIVE_DIR', tempfile.mkdtemp(prefix='main_archive_'))
REJECTED_FILE_DIR = os.getenv('REJECTED_FILE_DIR', tempfile.mkdtemp(prefix='rejected_files_'))
REMOVED_FILE_DIR = os.getenv('REMOVED_FILE_DIR', tempfile.mkdtemp(prefix='removed_files_'))

DATABASES['legacy'] = {
    'ENGINE': 'django.db.backends.mysql',
    'HOST': os.getenv('MYSQL_HOST', ''),
    'NAME': os.getenv('MYSQL_DATABASE_NAME', ''),
    'USER': os.getenv('MYSQL_USERNAME', ''),
    'PASSWORD': os.getenv('MYSQL_PASSWORD', ''),
    'PORT': '3306'
}

# This is only used in dev environment to populate your local archive
SONG_SOURCE = 'https://api.modarchive.org/downloads.php'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

BS_ICONS_BASE_PATH = 'homepage/static/bootstrap-icons/'
BS_ICONS_CACHE = os.path.join(STATIC_ROOT, 'icon_cache')
BS_ICONS_NOT_FOUND = '<?xml version="1.0" ?>\
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="red" class="bi bi-x-circle" viewBox="0 0 16 16">\
	<path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>\
	<path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>\
</svg>'

# LOGGING = {
#     'version': 1,
#     'filters': {
#         'require_debug_true': {
#             '()': 'django.utils.log.RequireDebugTrue',
#         }
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'filters': ['require_debug_true'],
#             'class': 'logging.StreamHandler',
#         }
#     },
#     'loggers': {
#         'django.db.backends': {
#             'level': 'DEBUG',
#             'handlers': ['console'],
#         }
#     }
# }
