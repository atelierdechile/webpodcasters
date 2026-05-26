from django.core.management.base import BaseCommand
from analytics.models import UserActionLog
from analytics.utils import classify_section

class Command(BaseCommand):
    help = "Corrige las secciones vacías o incorrectas en los registros de UserActionLog."

    def handle(self, *args, **options):
        total = UserActionLog.objects.count()
        corregidos = 0

        self.stdout.write(self.style.NOTICE(f"🔍 Analizando {total} registros de logs..."))

        for log in UserActionLog.objects.all().iterator():
            old_section = log.section
            new_section = classify_section(log.page, log.action)

            if not log.section or log.section != new_section:
                log.section = new_section
                log.save(update_fields=["section"])
                corregidos += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Proceso completado. {corregidos} registros actualizados."))
