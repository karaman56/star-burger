from django.db import models
from django.utils import timezone


class Location(models.Model):
    address = models.CharField(
        'адрес',
        max_length=200,
        unique=True
    )
    latitude = models.FloatField(
        'Широта',
        null=True,
        blank=True
    )
    longitude = models.FloatField(
        'Долгота',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        'дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'дата обновления',
        auto_now=True
    )
    last_geocode_attempt = models.DateTimeField(
        'последняя попытка геокодирования',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'местоположения'

    def __str__(self):
        return f"{self.address} ({self.latitude}, {self.longitude})"

    def needs_geocoding(self):
        """Проверяет, нуждается ли адрес в геокодировании"""
        if self.latitude is None or self.longitude is None:
            return True


        if self.last_geocode_attempt and \
            (timezone.now() - self.last_geocode_attempt).days >= 1:
            return True

        return False
