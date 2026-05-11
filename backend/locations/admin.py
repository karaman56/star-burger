from django.contrib import admin
from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['address', 'latitude', 'longitude', 'updated_at', 'last_geocode_attempt']
    list_filter = ['updated_at', 'last_geocode_attempt']
    search_fields = ['address']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'last_geocode_attempt'),
            'classes': ('collapse',)
        }),
    )
