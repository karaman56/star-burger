from .models import Location
from restaurateur.geocoder import fetch_coordinates
from django.conf import settings
from django.utils import timezone


def get_or_create_location(address):
    """Получает или создает Location для адреса"""
    if not address:
        return None

    normalized_address = address.strip()

    location, created = Location.objects.get_or_create(
        address=normalized_address,
        defaults={}
    )

    if created or location.needs_geocoding():
        try:
            coords = fetch_coordinates(settings.YANDEX_GEOCODER_APIKEY, normalized_address)
            if coords:
                location.longitude, location.latitude = coords
            location.last_geocode_attempt = timezone.now()
            location.save()
        except Exception as e:
            print(f"Ошибка геокодирования для адреса {normalized_address}: {e}")

    return location


def batch_update_locations(addresses):
    """Пакетное обновление координат для списка адресов"""
    locations = []
    for address in addresses:
        if address:
            location = get_or_create_location(address)
            if location:
                locations.append(location)
    return locations
