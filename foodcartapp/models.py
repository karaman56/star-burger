from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from geopy.distance import distance


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )


    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name

    def get_coordinates(self):
        """Возвращает координаты ресторана через Location"""
        from locations.models import Location
        try:
            location = Location.objects.get(address=self.address)
            if location.latitude and location.longitude:
                return (location.latitude, location.longitude)
        except Location.DoesNotExist:
            pass
        return None


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        'Order',
        related_name='items',
        verbose_name='заказ',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        verbose_name='товар',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        'количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказа'

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def clean(self):
        """Валидация на уровне модели"""
        if self.price < 0:
            raise ValidationError({'price': 'Цена не может быть отрицательной'})


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Завершен'),
        ('canceled', 'Отменен'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Наличными'),
        ('electronic', 'Электронно'),
    ]

    firstname = models.CharField(
        'имя',
        max_length=50
    )
    lastname = models.CharField(
        'фамилия',
        max_length=50
    )
    phonenumber = PhoneNumberField(
        'телефон',
        db_index=True
    )
    address = models.CharField(
        'адрес',
        max_length=200
    )
    status = models.CharField(
        'статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )
    payment_method = models.CharField(
        'способ оплаты',
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        db_index=True
    )

    cooking_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Ресторан для приготовления',
        related_name='orders',
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(
        'создан',
        auto_now_add=True,
        db_index=True
    )
    called_at = models.DateTimeField(
        'позвонили',
        blank=True,
        null=True
    )
    delivered_at = models.DateTimeField(
        'доставлен',
        blank=True,
        null=True
    )
    comment = models.TextField(
        'комментарий',
        blank=True
    )
    manager_comment = models.TextField(
        'комментарий менеджера',
        blank=True
    )

    # Убираем координаты - будем использовать Location

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} - {self.firstname} {self.lastname}"

    def get_coordinates(self):
        """Возвращает координаты заказа через Location"""
        from locations.models import Location
        try:
            location = Location.objects.get(address=self.address)
            if location.latitude and location.longitude:
                return (location.latitude, location.longitude)
        except Location.DoesNotExist:
            pass
        return None

    def calculate_distance_to_restaurant(self, restaurant):
        """Рассчитывает расстояние от заказа до ресторана в км"""
        order_coords = self.get_coordinates()
        restaurant_coords = restaurant.get_coordinates()

        if not order_coords or not restaurant_coords:
            return None

        try:
            return distance(order_coords, restaurant_coords).km
        except Exception:
            return None

    def get_available_restaurants(self):
        """Определяет какие рестораны могут приготовить весь заказ с расстояниями"""
        from django.db.models import Count

        order_products = self.items.values_list('product', flat=True)

        if not order_products:
            return []

        available_restaurants = Restaurant.objects.filter(
            menu_items__product__in=order_products,
            menu_items__availability=True
        ).annotate(
            matching_products=Count('menu_items__product', distinct=True)
        ).filter(
            matching_products=len(order_products)
        ).distinct()

        restaurants_with_distance = []
        for restaurant in available_restaurants:
            dist = self.calculate_distance_to_restaurant(restaurant)
            restaurants_with_distance.append({
                'restaurant': restaurant,
                'distance': dist
            })


        restaurants_with_distance.sort(key=lambda x: (x['distance'] is None, x['distance']))

        return restaurants_with_distance
