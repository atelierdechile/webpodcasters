from django.contrib.auth.decorators import user_passes_test

def superadmin_required(view_func):
    """
    Permite solo usuarios autenticados que sean superusuarios (is_superuser=True).
    """
    decorated_view = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser
    )(view_func)
    return decorated_view
