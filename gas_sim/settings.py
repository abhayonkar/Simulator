# gas_sim/settings.py
import os
import dj_database_url

SECRET_KEY = 'dev-key'
DEBUG = True
ALLOWED_HOSTS = ['*']  # Allow all hosts for Replit environment

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'simulator',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gas_sim.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database configuration - PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/gas_sim')

DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}

# InfluxDB configuration for time-series data
INFLUXDB_CONFIG = {
    'url': os.environ.get('INFLUXDB_URL', 'http://localhost:8086'),
    'token': os.environ.get('INFLUXDB_TOKEN', ''),
    'org': os.environ.get('INFLUXDB_ORG', 'gas_sim'),
    'bucket': os.environ.get('INFLUXDB_BUCKET', 'gas_pipeline_data')
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
