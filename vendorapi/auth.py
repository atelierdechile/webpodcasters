# from rest_framework.authentication import BaseAuthentication
# from rest_framework.exceptions import AuthenticationFailed
# from vendorapi.models import VendorApiKey


# class APIKeyAuth(BaseAuthentication):
#     def authenticate(self, request):
#         api_key = request.headers.get("x-api-key")

#         if not api_key:
#             raise AuthenticationFailed("Missing API key")

#         try:
#             api_key_obj = VendorApiKey.objects.get(key=api_key)
#         except VendorApiKey.DoesNotExist:
#             raise AuthenticationFailed("Invalid API key")

#         vendor = api_key_obj.vendor
#         return (vendor.created_by, vendor)  # user, vendor


# vendorapi/auth.py
# vendorapi/auth.py

# vendorapi/auth.py

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from vendorapi.models import VendorApiKey


class APIKeyAuth(BaseAuthentication):
    def authenticate(self, request):
        print(">>> APIKeyAuth.authenticate EJECUTADO")
        print("   GET:", request.GET)

        # Aceptamos x-api-key por header o api_key por query
        api_key = request.headers.get("x-api-key") or request.GET.get("api_key")

        # Si no viene API key, no autenticamos, pero TAMPOCO lanzamos error
        if not api_key:
            return None

        try:
            api_key_obj = VendorApiKey.objects.get(key=api_key)
        except VendorApiKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key")

        vendor = api_key_obj.vendor
        # user, auth
        return (vendor.created_by, vendor)
