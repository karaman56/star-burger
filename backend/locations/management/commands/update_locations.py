from django.core.management.base import BaseCommand
from locations.utils import batch_update_locations
from foodcartapp.models import Order, Restaurant


class Command(BaseCommand):
    help = 'Обновляет координаты для всех заказов и ресторанов'

    def handle(self, *args, **options):

        order_addresses = set(Order.objects.values_list('address', flat=True))
        restaurant_addresses = set(Restaurant.objects.values_list('address', flat=True))
        all_addresses = order_addresses.union(restaurant_addresses)

        self.stdout.write(f"Найдено {len(all_addresses)} уникальных адресов для геокодирования")


        updated_locations = batch_update_locations(all_addresses)

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно обновлено {len(updated_locations)} местоположений'
            )
        )
