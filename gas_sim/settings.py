SECRET_KEY = 'dev-key'
INSTALLED_APPS = ['simulator']
DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3','NAME':'db.sqlite3'}}
ROOT_URLCONF = 'gas_sim.urls'
DEBUG = True
ALLOWED_HOSTS = []
