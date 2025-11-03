from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Prefetch, Count
from foodcartapp.models import Order, OrderItem, Product, Restaurant
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from locations.utils import get_or_create_location, batch_update_locations


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


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    # Оптимизированный запрос с prefetch_related
    orders = Order.objects.exclude(
        status__in=['completed', 'canceled']
    ).prefetch_related(
        Prefetch(
            'items',
            queryset=OrderItem.objects.select_related('product')
        )
    ).order_by('-created_at')

    order_addresses = set(orders.values_list('address', flat=True))
    restaurant_addresses = set(Restaurant.objects.values_list('address', flat=True))
    all_addresses = order_addresses.union(restaurant_addresses)

    try:
        batch_update_locations(all_addresses)
    except Exception as e:

        print(f"Ошибка пакетного геокодирования: {e}")

    orders_data = []
    for order in orders:
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
            'total_amount': 0,
            'cooking_restaurant': order.cooking_restaurant,
            'available_restaurants': order.get_available_restaurants() if not order.cooking_restaurant else []
        }

        for item in order.items.all():
            product_info = f"{item.product.name} x{item.quantity}"
            order_info['products'].append(product_info)
            order_info['total_amount'] += item.price * item.quantity

        orders_data.append(order_info)

    return render(request, template_name='order_items.html', context={
        'orders': orders_data
    })
