import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'star_burger.settings')
django.setup()

from locations.utils import get_or_create_location, batch_update_locations
from foodcartapp.models import Order, Restaurant
from locations.models import Location

print("=== ПРОВЕРКА СИСТЕМЫ ГЕОКОДИРОВАНИЯ ===\n")

# 1. Проверим существующие локации
print("1. Существующие локации:")
print(f"Всего локаций: {Location.objects.count()}")
for loc in Location.objects.all()[:5]:
    print(f"  - {loc.address}: ({loc.latitude}, {loc.longitude})")

# 2. Получим адреса для обновления
order_addresses = set(Order.objects.values_list('address', flat=True))
restaurant_addresses = set(Restaurant.objects.values_list('address', flat=True))
all_addresses = order_addresses.union(restaurant_addresses)

print(f"\n2. Адреса для обработки: {len(all_addresses)}")

# 3. Обновим локации
print("\n3. Обновление локаций...")
batch_update_locations(all_addresses)

# 4. Проверим результат
print("\n4. Результат после обновления:")
print(f"Всего локаций: {Location.objects.count()}")
for loc in Location.objects.all()[:5]:
    print(f"  - {loc.address}: ({loc.latitude}, {loc.longitude})")

# 5. Проверим заказы
print("\n5. Проверка заказов:")
for order in Order.objects.all()[:3]:
    print(f"Заказ {order.id}: {order.address}")
    print(f"  Координаты: {order.get_coordinates()}")
    print(f"  Адрес найден: {order.is_address_found()}")
    print("  ---")

print("\n=== ПРОВЕРКА ЗАВЕРШЕНА ===")
