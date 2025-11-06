from django.test import TestCase
from .models import Location
from .address_check import check_address_exists, batch_check_addresses


class AddressCheckTestCase(TestCase):
    def setUp(self):

        Location.objects.create(
            address="Москва, Красная площадь",
            latitude=55.7539,
            longitude=37.6208
        )
        Location.objects.create(
            address="Неизвестный адрес",
            latitude=None,
            longitude=None
        )

    def test_check_address_exists(self):
        """Тест проверки существования адреса"""
        self.assertTrue(check_address_exists("Москва, Красная площадь"))
        self.assertFalse(check_address_exists("Неизвестный адрес"))
        self.assertFalse(check_address_exists("Несуществующий адрес"))
        self.assertFalse(check_address_exists(""))
        self.assertFalse(check_address_exists(None))

    def test_batch_check_addresses(self):
        """Тест пакетной проверки адресов"""
        addresses = ["Москва, Красная площадь", "Неизвестный адрес", "Несуществующий адрес"]
        result = batch_check_addresses(addresses)

        self.assertEqual(result["Москва, Красная площадь"], True)
        self.assertEqual(result["Неизвестный адрес"], False)
        self.assertEqual(result["Несуществующий адрес"], False)
