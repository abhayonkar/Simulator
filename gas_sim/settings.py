# gas_sim/settings.py
SECRET_KEY = 'dev-key'
INSTALLED_APPS = ['simulator']
DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3','NAME':'db.sqlite3'}}
ROOT_URLCONF = 'gas_sim.urls'
DEBUG = True
ALLOWED_HOSTS = []

# add this:
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
