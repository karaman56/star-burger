from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Prefetch
from foodcartapp.models import Order, OrderItem, Product, Restaurant, \
    RestaurantMenuItem
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from locations.utils import get_or_create_location, batch_update_locations
from collections import defaultdict
from geopy.distance import distance


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff



@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def get_addresses_coordinates(addresses):
    """Получает координаты для всех адресов сразу"""
    from locations.models import Location
    from locations.utils import get_or_create_location

    coordinates_dict = {}

    # Получаем существующие локации
    existing_locations = Location.objects.filter(address__in=addresses)
    for location in existing_locations:
        if location.latitude and location.longitude:
            coordinates_dict[location.address] = (location.latitude, location.longitude)

    # Обрабатываем отсутствующие адреса
    for address in addresses:
        if address not in coordinates_dict:
            location = get_or_create_location(address)
            if location and location.latitude and location.longitude:
                coordinates_dict[address] = (location.latitude, location.longitude)
            else:
                coordinates_dict[address] = None

    return coordinates_dict


def calculate_distance(coord1, coord2):
    """Рассчитывает расстояние между двумя координатами"""
    if not coord1 or not coord2:
        return None

    try:
        return distance(coord1, coord2).km
    except Exception:
        return None


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.exclude(
        status__in=['completed', 'canceled']
    ).select_related('cooking_restaurant').prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('product'))
    ).with_total_cost().order_by('-created_at')

    order_addresses = set(orders.values_list('address', flat=True))
    restaurant_addresses = set(Restaurant.objects.values_list('address', flat=True))
    all_addresses = order_addresses.union(restaurant_addresses)

    coordinates_dict = get_addresses_coordinates(all_addresses)

    all_restaurants = Restaurant.objects.prefetch_related(
        Prefetch('menu_items',
                 queryset=RestaurantMenuItem.objects.filter(availability=True)
                 .select_related('product'))
    )

    restaurant_products = defaultdict(set)
    for restaurant in all_restaurants:
        for menu_item in restaurant.menu_items.all():
            restaurant_products[restaurant.id].add(menu_item.product.id)

    restaurants_dict = {r.id: r for r in all_restaurants}


    orders_data = []
    for order in orders:
        order_product_ids = {item.product.id for item in order.items.all()}

        available_restaurants = []
        if not order.cooking_restaurant and order_product_ids:
            for restaurant_id, available_products in restaurant_products.items():
                if order_product_ids.issubset(available_products):
                    restaurant = restaurants_dict[restaurant_id]
                    available_restaurants.append(restaurant)

        available_restaurants_with_distances = []
        for restaurant in available_restaurants:
            distance = calculate_distance(
                coordinates_dict.get(order.address),
                coordinates_dict.get(restaurant.address)
            )
            available_restaurants_with_distances.append({
                'restaurant': restaurant,
                'distance': distance
            })

        available_restaurants_with_distances.sort(key=lambda x: (x['distance'] is None, x['distance']))

        order_info = {
            'id': order.id,
            'firstname': order.firstname,
            'lastname': order.lastname,
            'phonenumber': order.phonenumber,
            'address': order.address,
            'status': order.get_status_display(),
            'payment_method': order.get_payment_method_display(),
            'comment': order.comment or '-',
            'manager_comment': order.manager_comment or '-',
            'created_at': order.created_at,
            'called_at': order.called_at,
            'delivered_at': order.delivered_at,
            'products': [],
            'total_amount': order.total_cost or 0,
            'cooking_restaurant': order.cooking_restaurant,
            'available_restaurants': available_restaurants_with_distances,
            'is_address_found': coordinates_dict.get(order.address) is not None
        }

        for item in order.items.all():
            product_info = f"{item.product.name} x{item.quantity}"
            order_info['products'].append(product_info)

        orders_data.append(order_info)

    return render(request, template_name='order_items.html', context={
        'orders': orders_data
    })
