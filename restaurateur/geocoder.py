import requests
from requests.exceptions import HTTPError, RequestException
from django.conf import settings


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"

    try:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        }, timeout=10)

        if response.status_code == 403:
            print("Ошибка 403: Проверьте API-ключ и его настройки")
            return None
        elif response.status_code == 404:
            print("Ошибка 404: API endpoint не найден")
            return None
        elif response.status_code != 200:
            print(f"Ошибка {response.status_code}: {response.text}")
            return None

        response.raise_for_status()

        found_places = response.json()['response']['GeoObjectCollection']['featureMember']

        if not found_places:
            return None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        return float(lon), float(lat)

    except HTTPError as e:
        print(f"HTTP ошибка: {e}")
        return None
    except RequestException as e:
        print(f"Ошибка соединения: {e}")
        return None
    except Exception as e:
        print(f"Общая ошибка при геокодировании адреса {address}: {e}")
        return None
