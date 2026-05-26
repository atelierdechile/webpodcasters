from django.contrib import admin
from django.utils.html import format_html
from .models import UserActionLog


@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    """Vista administrativa para los logs del sistema (web + bot + errores)."""

    # Campos que se muestran en la lista
    list_display = (
        "colored_timestamp",
        "colored_origin",
        "user_display",
        "action_short",
        "product_id",
    )

    # Campos por los que se puede filtrar
    list_filter = (
        "section",
        "page",
        ("timestamp", admin.DateFieldListFilter),
    )

    # Campos buscables
    search_fields = ("action", "user_name", "page", "section")

    # Orden por defecto (últimos primero)
    ordering = ("-timestamp",)

    # Paginación
    list_per_page = 50

    # Mostrar solo lectura (los logs no se editan)
    readonly_fields = (
        "timestamp",
        "user",
        "user_name",
        "action",
        "page",
        "section",
        "product_id",
        "extra_data",
    )

    # Desactivar la opción de agregar desde el admin
    def has_add_permission(self, request):
        return False

    # Desactivar eliminar en masa (solo lectura)
    def has_delete_permission(self, request, obj=None):
        return False

    # -----------------------------
    # 🧩 Campos personalizados
    # -----------------------------
    def user_display(self, obj):
        """Muestra nombre de usuario o 'Anónimo'."""
        return obj.user.username if obj.user else (obj.user_name or "Anónimo")
    user_display.short_description = "Usuario"

    def action_short(self, obj):
        """Muestra acción truncada si es muy larga."""
        text = obj.action
        return text[:80] + "..." if len(text) > 80 else text
    action_short.short_description = "Acción"

    def colored_origin(self, obj):
        """Colorea según el tipo de origen."""
        if obj.section == "bot" or "manychat" in (obj.page or "").lower():
            color = "#0ea5e9"  # celeste
            label = "🤖 Bot"
        elif "error" in (obj.action or "").lower() or obj.section == "errores":
            color = "#ef4444"  # rojo
            label = "⚠️ Error"
        else:
            color = "#facc15"  # dorado
            label = "🌐 Web"

        return format_html(
            f'<span style="color:{color}; font-weight:600;">{label}</span>'
        )
    colored_origin.short_description = "Origen"

    def colored_timestamp(self, obj):
        """Muestra fecha/hora con color tenue."""
        return format_html(
            f'<span style="color:#6b7280;">{obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")}</span>'
        )
    colored_timestamp.short_description = "Fecha y hora"
