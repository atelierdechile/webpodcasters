import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

#  BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')  
DEBUG = True  # Cambiar a False en producción real

#Hosts mi local , ngrok, pythonanywhere
ALLOWED_HOSTS = [
    'nicolasbriceno.pythonanywhere.com',
    'sommstore.pythonanywhere.com',
    '127.0.0.1',
    'localhost',
    'webpodcasters.onrender.com',
    'nonfimbriate-usha-aerobically.ngrok-free.dev',
]
CSRF_TRUSTED_ORIGINS = [
    "https://nonfimbriate-usha-aerobically.ngrok-free.dev",
    "https://nicolasbriceno.pythonanywhere.com",
    "https://webpodcasters.onrender.com",
]

#Apps instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'product',
    'cart',
    'order',
    'widget_tweaks',
    'location',
    'botapi',  
    'analytics',
    'vendor.apps.VendorConfig',
    'marketing',
    'offers',
    'assistant',
    'vendorapi',
    "vendorpos",
    'rest_framework',
    "superadmin_panel",
    'chat',
]
NOMINATIM_EMAIL = os.getenv('NOMINATIM_EMAIL', '')

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'analytics.middleware.ErrorLoggingMiddleware',
    # 'vendorapi.middleware.ApiKeyMiddleware',
]

# URL y Templates
ROOT_URLCONF = 'simple_multivendor_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Directorio global para templates
        'APP_DIRS': True,  # Asegura que Django busque también en las carpetas de cada app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'product.context_processors.menu_categories',
                'cart.context_processors.cart',
                'core.context_processors.comuna_context',
                'core.context_processors.price_helpers'
            ],
        },
    },
]

WSGI_APPLICATION = 'simple_multivendor_site.wsgi.application'


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


import os
import dj_database_url

if os.getenv('DATABASE_URL'):
    # Producción (Render)
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
            'NAME': os.getenv('DB_NAME', ''),
            'USER': os.getenv('DB_USER', ''),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }




# Password validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_L10N = True
USE_TZ = True


#  Archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'core/static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configucación de almacenamiento
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

#  Archivos media
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Login & sesiones
LOGIN_URL = 'core:login'
# LOGIN_REDIRECT_URL = 'vendor:vendor-admin'
LOGOUT_REDIRECT_URL = 'core:home'
SESSION_COOKIE_AGE = 86400  # 1 día en segundos
CART_SESSION_ID = 'cart'

# MERCADOPAGO
MERCADOPAGO_SANDBOX = True  # Cambia a False cuando vayas a producción



# Email (ajústalo si usarás notificaciones)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

#  Mercado Pago
MERCADOPAGO_PUBLIC_KEY = os.getenv('MERCADOPAGO_PUBLIC_KEY', '')
MERCADOPAGO_ACCESS_TOKEN = os.getenv('MERCADOPAGO_ACCESS_TOKEN', '')
MERCADOPAGO_WEBHOOK_SECRET = os.getenv('MERCADOPAGO_WEBHOOK_SECRET', '')

# MANYCHAT SECRET (reemplaza esto con tu propio secreto de ManyChat)
MANYCHAT_SECRET = os.getenv('MANYCHAT_SECRET', '')

# URL BASE DEL SITIO (OBLIGATORIA PARA MERCADO PAGO)
SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000')

# GOOGLE MAPS API KEY
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", None)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")