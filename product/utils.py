from django.db.models import Count, Case, When, IntegerField, Q

def aplicar_preferencias(user, queryset, solo_pref=False):
    """
    🍕 Aplica preferencias del usuario a un queryset de productos.

    - Si el usuario no está autenticado → devuelve queryset sin cambios.
    - Si no tiene preferencias → devuelve queryset sin cambios.
    - Si solo_pref=True → devuelve solo productos que coinciden con sus preferencias.
    - Si solo_pref=False → devuelve todos los productos, pero ordenando primero
      los que coinciden con sus preferencias.

    Compatible con todas las vistas (home, categoría, búsqueda).
    """

    # 🧱 1. Validaciones iniciales
    if not user.is_authenticated:
        return queryset

    profile = getattr(user, "profile", None)
    if not profile or not profile.preferences.exists():
        return queryset

    prefs = profile.preferences.all()

    # 🌱 2. Modo filtrado estricto
    if solo_pref:
        return (
            queryset.filter(preferences__in=prefs)
            .distinct()
            .annotate(
                match_pref=Count(
                    Case(
                        When(preferences__in=prefs, then=1),
                        output_field=IntegerField(),
                    )
                )
            )
            .order_by("-match_pref", "-id")
        )

    # 🌾 3. Modo orden inteligente (todas las pizzas, preferidas arriba)
    return (
        queryset
        .annotate(
            match_pref=Count(
                Case(
                    When(preferences__in=prefs, then=1),
                    output_field=IntegerField(),
                )
            )
        )
        .order_by("-match_pref", "-id")
        .distinct()
    )
