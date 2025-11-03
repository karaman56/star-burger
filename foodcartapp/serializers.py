from django.db import transaction
from rest_framework import serializers
from .models import Order, OrderItem, Product


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.IntegerField(source='product.id')

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

    def validate_product(self, value):
        """Проверяем что продукт существует"""
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Продукт с ID {value} не найден")
        return value

    def validate_quantity(self, value):
        """Проверяем количество"""
        if value < 1:
            raise serializers.ValidationError("Количество должно быть положительным")
        if value > 100:
            raise serializers.ValidationError("Количество не может превышать 100")
        return value


class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(many=True, source='items')

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']  # ДОБАВИЛИ 'products'

    def validate_firstname(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Имя должно быть минимум из 2 символов")
        return value.strip()

    def validate_lastname(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Фамилия должна быть минимум из 2 символов")
        return value.strip()

    def validate_phonenumber(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Номер телефона должен быть корректным")
        return value.strip()

    def validate_address(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Адрес должен содержать минимум 10 символов")
        return value.strip()

    def validate_products(self, value):
        """Проверяем список продуктов"""
        if not value:
            raise serializers.ValidationError("Список продуктов не может быть пустым")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Создаем заказ и товары в заказе в одной транзакции"""
        products_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        for product_data in products_data:
            product_id = product_data['product']['id']
            quantity = product_data['quantity']
            product = Product.objects.get(id=product_id)

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

        return order
