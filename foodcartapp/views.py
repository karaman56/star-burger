from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view

from .models import Product, Order, OrderItem


def banners_list_api(request):
    print("🟢 [API] Запрос баннеров")
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    print("🟢 [API] Запрос списка продуктов")
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })

@api_view(['POST'])
def register_order(request):
    print("🟢 [API] Запрос регистрации заказа")

    if request.method == 'POST':
        import json
        data = json.loads(request.body)

        print("📦 НОВЫЙ ЗАКАЗ:")
        print(f"• Имя: {data.get('firstname')}")
        print(f"• Фамилия: {data.get('lastname')}")
        print(f"• Телефон: {data.get('phonenumber')}")
        print(f"• Адрес: {data.get('address')}")

        # СОХРАНЯЕМ В БД
        order = Order.objects.create(
            firstname=data['firstname'],
            lastname=data['lastname'],
            phonenumber=data['phonenumber'],
            address=data['address'],
        )

        print("• Продукты:")
        for product_data in data.get('products', []):
            # ИСПРАВЛЕНО: используем ключ 'product'
            product_id = product_data.get('product')
            quantity = product_data.get('quantity', 1)

            if not product_id:
                print(f"  ❌ Ошибка: нет ID продукта в данных: {product_data}")
                continue

            try:
                product = Product.objects.get(id=product_id)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )
                print(f"  ✅ Продукт ID: {product_id}, Количество: {quantity}")
            except Product.DoesNotExist:
                print(f"  ❌ Продукт с ID {product_id} не найден в БД")
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")

        print(f"✅ Заказ #{order.id} сохранен в БД")
        return JsonResponse({'order_id': order.id})


    return JsonResponse({'error': 'Use POST method'}, status=400)
