import traceback
from django.utils.deprecation import MiddlewareMixin
from .models import UserActionLog


class ErrorLoggingMiddleware(MiddlewareMixin):
    """Captura y registra automáticamente errores globales."""

    def process_exception(self, request, exception):
        try:
            if request.path.startswith("/analytics/"):
                return None

            user = (
                request.user
                if hasattr(request, "user") and request.user.is_authenticated
                else None
            )
            error_message = f"❌ ERROR GLOBAL: {type(exception).__name__} - {str(exception)}"

            UserActionLog.objects.create(
                user=user,
                user_name=getattr(user, "username", "Anónimo") if user else "Sistema",
                action=error_message,
                page="web",
                section="errores",
                extra_data={"path": request.path},
            )
            print("⚠️ Error capturado:\n", traceback.format_exc())

        except Exception as e:
            print(f"⚠️ No se pudo registrar error global: {e}")
            print(traceback.format_exc())
