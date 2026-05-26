from django.http import JsonResponse
from vendorapi.models import VendorApiKey
from django.utils import timezone

class ApiKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo proteger rutas vendorapi
        if request.path.startswith("/vendorapi/"):
            api_key = request.headers.get("x-api-key")

            if not api_key:
                return JsonResponse({"detail": "Missing API Key"}, status=401)

            try:
                key_obj = VendorApiKey.objects.get(key=api_key, is_active=True)
                request.vendor = key_obj.vendor
                key_obj.last_used = timezone.now()
                key_obj.save()
            except VendorApiKey.DoesNotExist:
                return JsonResponse({"detail": "Invalid API Key"}, status=403)

        return self.get_response(request)
