from django.contrib import admin
from django.utils.html import format_html
from .models import UserActionLog


@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    """Vista administrativa para los logs del sistema (web + bot + errores)."""

    list_display = (
        "colored_timestamp",
        "colored_origin",
        "user_display",
        "action_short",
        "product_id",
    )

    list_filter = (
        "section",
        "page",
        ("timestamp", admin.DateFieldListFilter),
    )

    search_fields = ("action", "user_name", "page", "section")
    ordering = ("-timestamp",)
    list_per_page = 50

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

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # -----------------------------
    # 🧩 Campos personalizados corregidos
    # -----------------------------
    @admin.display(description="Usuario")
    def user_display(self, obj):
        """Muestra nombre de usuario o 'Anónimo'."""
        return obj.user.username if obj.user else (obj.user_name or "Anónimo")

    @admin.display(description="Acción")
    def action_short(self, obj):
        """Muestra acción truncada si es muy larga."""
        text = obj.action or ""
        return text[:80] + "..." if len(text) > 80 else text

    @admin.display(description="Origen")
    def colored_origin(self, obj):
        """Colorea según el tipo de origen de forma segura."""
        action_text = (obj.action or "").lower()
        page_text = (obj.page or "").lower()
        section_text = (obj.section or "").lower()

        if section_text == "bot" or "manychat" in page_text:
            color = "#0ea5e9"  # celeste
            label = "🤖 Bot"
        elif "error" in action_text or section_text == "errores":
            color = "#ef4444"  # rojo
            label = "⚠️ Error"
        else:
            color = "#facc15"  # dorado
            label = "🌐 Web"

        # Alternative correcta: Pasamos los valores como argumentos externos
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color,
            label
        )

    @admin.display(description="Fecha y hora")
    def colored_timestamp(self, obj):
        """Muestra fecha/hora con formato seguro para format_html."""
        if not obj.timestamp:
            return "—"
        
        formatted_date = obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # 🔥 FIX AQUÍ: Se usa '{}' y se pasa la variable por fuera
        return format_html(
            '<span style="color: #6b7280;">{}</span>',
            formatted_date
        )