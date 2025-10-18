from django.contrib import admin
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Product, Order, OrderItem
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'firstname', 'lastname', 'phonenumber',
        'address', 'status', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['firstname', 'lastname', 'phonenumber', 'address']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Информация о клиенте', {
            'fields': [
                'firstname', 'lastname', 'phonenumber', 'address'
            ]
        }),
        ('Статус и даты', {
            'fields': [
                'status', 'created_at', 'called_at', 'delivered_at'
            ]
        }),
        ('Комментарии', {
            'fields': [
                'comment',
                'manager_comment',
            ],
            'classes': ['wide']
        }),
    )

    readonly_fields = ['created_at']

    def response_change(self, request, obj):
        """Переопределяем поведение после сохранения заказа"""
        if '_continue' not in request.POST:
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return HttpResponseRedirect(next_url)
        return super().response_change(request, obj)

    def save_formset(self, request, form, formset, change):
        """Валидация OrderItem при сохранении в админке"""
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.price or instance.price == 0:
                instance.price = instance.product.price
            if instance.price < 0:
                from django.core.exceptions import ValidationError
                raise ValidationError('Цена не может быть отрицательной')
            instance.save()
        formset.save_m2m()
