# vendor/geocoding.py
import time
import requests
from django.conf import settings

def geocode_address(address: str, comuna: str = "", region: str = "", country: str = "Chile"):
    # 1) intento completo
    lat, lng = _nominatim_search([address, comuna, region, country])
    if lat and lng:
        return lat, lng

    # 2) fallback: sin address (centro de comuna)
    lat, lng = _nominatim_search([comuna, region, country])
    if lat and lng:
        return lat, lng

    return None, None


def _nominatim_search(parts):
    import time, requests
    from django.conf import settings

    q = ", ".join([p for p in parts if p]).strip()
    if not q:
        return None, None

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": q, "format": "json", "limit": 1, "addressdetails": 0}

    email = getattr(settings, "NOMINATIM_EMAIL", None)
    if email:
        params["email"] = email

    headers = {"User-Agent": f"pizza-marketplace/1.0 ({email or 'no-email-set'})"}

    time.sleep(1.1)
    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()

    if not data:
        return None, None

    return float(data[0]["lat"]), float(data[0]["lon"])

