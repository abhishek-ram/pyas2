"""
Django settings for djproject project.

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
SECRET_KEY = '7slz5$2)6k0%)(mip*mw9aa836al=+6!5dz23lan)p0@=*597a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

TEMPLATE_DIRS = (os.path.join(BASE_DIR, 'pyas2/templates'),)

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pyas2',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'djproject.urls'

WSGI_APPLICATION = 'djproject.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

MANAGERS = (    #pyas2 will send error reports to the MANAGERS
        ('abhishek ram', 'abhishek8816@gmail.com'),
    )
EMAIL_HOST = 'localhost'             #Default: 'localhost'
EMAIL_PORT = '25'             #Default: 25
EMAIL_USE_TLS = False       #Default: False
EMAIL_HOST_USER = ''        #Default: ''. Username to use for the SMTP server defined in EMAIL_HOST. If empty, Django won't attempt authentication.
EMAIL_HOST_PASSWORD = ''    #Default: ''. PASSWORD to use for the SMTP server defined in EMAIL_HOST. If empty, Django won't attempt authentication.

## PYAS2 app settings
PYAS2 = {
    ## Full path to the base directory for storing files, logs ...
    'ROOTDIR' : os.path.dirname(os.path.dirname(__file__)),
    ## Path to the python executable, neccessary with virtual environments
    'PYTHONPATH' : '/Users/abhishekram/Documents/work/Research/pythondev/bin/python',
    ## environment_text: text displayed on right of the logo. Useful to indicate different environments.
    'ENVIRONMENTTEXT' : 'BETA',   
    ## environment_text_color: Use HTML valid "color name" or #RGB values. Default: Black (#000000)
    'ENVIRONMENTTEXTCOLOR' : 'Yellow',
    ## level for logging to log file. Values: DEBUG,INFO,STARTINFO,WARNING,ERROR or CRITICAL. Default: INFO
    'LOGLEVEL' : 'DEBUG',
    ## console logging on (True) or off (False); default is True.
    'LOGCONSOLE' : True,
    ## level for logging to console/screen. Values: DEBUG,INFO,STARTINFO,WARNING,ERROR or CRITICAL. Default: STARTINFO  
    'LOGCONSOLELEVEL' : 'DEBUG',
    ## Maximum number of retries for failed outgoing messages, defaule is 10
    'MAXRETRIES': 5,	
    ## Return url for receiving async MDNs from partners
    'MDNURL' : 'http://104.155.212.52:8001/pyas2/as2receive',
    ## Maximum wait time in minutes for asyn MDNs from partner, post which message will be marked as failed
    'ASYNCMDNWAIT' : 30,
    ## number of days files and messages are kept in storage; default is 30
    'MAXARCHDAYS' : 30,
}

