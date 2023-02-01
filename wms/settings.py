from pathlib import Path
import os
from dotenv import load_dotenv
from logging import FileHandler

load_dotenv()

SECRET_KEY = os.getenv('secret_key')

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.getenv('debug')

ALLOWED_HOSTS = ['nail.network', 'www.nail.network', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'simple_history',
    'wms_app',
    'wms'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'wms.log'
        }
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG'
        }
    }
}

DATABASES = {
    'default': {
        'ENGINE': os.getenv('db_engine'),
        'NAME': os.getenv('db_name'),
        'USER': os.getenv('db_user'),
        'PASSWORD': os.getenv('db_password'),
        'HOST': 'localhost',
        'PORT': '',
    }
}

ROOT_URLCONF = 'wms.urls'

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

OAUTH_URL_WHITELISTS = []

OAUTH_CLIENT = {
    'client_name': 'lightspeed',
    'client_id': '1230262cdb25bd7485a1780b0c63b701a3d3eccd4598571524e469b7929ebc98',
    'client_secret': 'd936758a5852fbf5788641a29df650065ce2ea38ba19bce670e6672a8e7db776',
    'access_token_url': 'https://cloud.lightspeedapp.com/oauth/access_token.php',
    'authorize_url': 'https://cloud.lightspeedapp.com/oauth/authorize.php',
    'api_base_url': 'https://api.lightspeedapp.com/API/V3/Account',
    'redirect_uri': 'https://nail.network/token',
    'client_kwargs': {
        'scope': 'employee:inventory_read',
        'token_placement': 'header'
    }
    #'userinfo_endpoint': 'https://api.lightspeedapp.com/API/V3/Account.json',
}

OAUTH_CLIENT_NAME = 'lightspeed'

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

WSGI_APPLICATION = 'wms.wsgi.application'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True
