import requests
from django.conf import settings
from geopy.distance import distance
import logging

logger = logging.getLogger(__name__)


apikey = "0b77519b-66c0-4aa9-923e-827e4512b95e"


def fetch_coordinates(apikey, address):
    """Получает координаты адреса через Yandex Geocoder API"""
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon


def calculate_distance(coord1, coord2):
    """Рассчитывает расстояние между двумя координатами в км"""
    if not coord1 or not coord2:
        return None
    return distance(coord1, coord2).km


def get_restaurant_distances(order_address, restaurants, apikey):
    """Рассчитывает расстояния от адреса заказа до всех ресторанов"""
    try:
        order_coords = fetch_coordinates(apikey, order_address)
    except Exception as e:
        logger.error(f"Ошибка геокодирования адреса {order_address}: {e}")
        return {}

    if not order_coords:
        return {}

    distances = {}
    for restaurant in restaurants:
        try:
            restaurant_coords = fetch_coordinates(apikey, restaurant.address)
            if restaurant_coords:
                dist = calculate_distance(order_coords, restaurant_coords)
                distances[restaurant.id] = round(dist, 2)  # округляем до 2 знаков
            else:
                distances[restaurant.id] = None
        except Exception as e:
            logger.error(f"Ошибка геокодирования ресторана {restaurant.name}: {e}")
            distances[restaurant.id] = None

    return distances
