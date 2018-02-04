"""
Django settings for Amazon project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'zcd5t7)u4yaz$+%ygs&l$4^p*7wec_2ikw_5c4!dopizx*1pxe'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'amazon_services',
    'rest_framework',
    'rest_framework_extensions',
    'django_filters',
    'chardet',
    'dateutil',
    'xlrd',
    'xlwt',
    'dcors',
    'PIL',
    'products',
    'client',
    'my_auth',
    'rolepermissions',
    'purchasing',
    'shipment',
)


TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'client/templates'),
    os.path.join(BASE_DIR, 'my_auth/templates'),
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    # 'website.middleware.DisableCSRFCheck',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'dcors.dcorsmiddleware.CorsMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'website.urls'

WSGI_APPLICATION = 'website.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'amazon',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        # 'USER': 'zhfdb',
        # 'PASSWORD': 'Zhouhuafeng.1',
        # 'HOST': '116.62.192.177',
        # 'PORT': '3506',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

LOGIN_URL = '/login/'

CORS_ALLOW_ORIGIN = '*'
CORS_ALLOW_HEADERS = ['Origin', 'x-requested-with','content-type', 'Accept']
CORS_ALLOW_METHODS = ['GET', 'POST', 'DELETE', 'PATCH', 'PUT']
# CORS_ORIGIN_ALLOW_ALL = True
# CORS_ALLOW_CREDENTIALS = True

ROLEPERMISSIONS_MODULE = 'website.roles'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s][%(asctime)s][%(module)s:%(funcName)s-%(lineno)s ]%(message)s'
        },
        'simple': {
            'format': '[%(levelname)s]%(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'default': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/', 'all.log'),
            'maxBytes': 1024 * 1024 * 20,  # 20 MB
            'backupCount': 10,
            'formatter': 'verbose',
            # 'filters': ['require_debug_false']
        },
        'backup': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR,'logs/', 'log.log'),
            "when":"d",
            "interval":7,
            'formatter': 'verbose',
        },
        'amazon': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR,'logs/', 'request.log'),
            "when":"d",
            "interval":7,
            'formatter': 'verbose',
        },
        'product': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR,'logs/', 'product.log'),
            "when":"d",
            "interval":7,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'default', 'backup'],
            'propagate': False,
            'level': 'INFO',
        },
        'amazon': {
            'handlers': ['console', 'amazon'],
            'propagate': False,
            'level': 'INFO',
        },
        'product': {
            'handlers': ['console', 'product'],
            'propagate': False,
            'level': 'INFO',
        },
    }
}