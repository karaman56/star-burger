from django.db import migrations


def fill_orderitem_prices(apps, schema_editor):
    """Заполняем цены в существующих OrderItem на основе текущих цен продуктов"""
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')

    order_items = OrderItem.objects.all().select_related('product').iterator(chunk_size=1000)

    updated_items = []
    for item in order_items:
        if not item.price or item.price == 0:
            item.price = item.product.price
            updated_items.append(item)

        if len(updated_items) >= 100:
            OrderItem.objects.bulk_update(updated_items, ['price'])
            updated_items = []

    if updated_items:
        OrderItem.objects.bulk_update(updated_items, ['price'])


def reverse_fill_orderitem_prices(apps, schema_editor):
    """Откат миграции - устанавливаем цены в 0"""
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')
    OrderItem.objects.all().update(price=0)


class Migration(migrations.Migration):
    dependencies = [

        ('foodcartapp', '0040_alter_orderitem_price'),
    ]

    operations = [
        migrations.RunPython(fill_orderitem_prices, reverse_fill_orderitem_prices),
    ]


