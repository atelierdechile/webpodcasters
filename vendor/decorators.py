from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def vendor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, "vendor"):
            messages.error(request, "Solo los vendedores pueden acceder a esta sección.")
            return redirect("core:home")
        return view_func(request, *args, **kwargs)
    return wrapper
