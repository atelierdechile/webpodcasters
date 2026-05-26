import os
import sys
import django
from django.core.management import call_command

# Indica dónde están tus settings de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simple_multivendor_site.settings')

# Inicializa Django
django.setup()

# Fuerza UTF-8 en salida
sys.stdout.reconfigure(encoding='utf-8')

# Ejecuta dumpdata sin pasar por PowerShell
with open('data.json', 'w', encoding='utf-8') as f:
    call_command(
        'dumpdata',
        exclude=['contenttypes', 'auth.permission'],
        stdout=f
    )
