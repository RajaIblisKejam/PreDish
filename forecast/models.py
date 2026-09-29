from django.db import models
from business.models import Business, MenuItem

class ExternalFactor(models.Model):
    DAY_TYPE_CHOICES = (
        ('weekday', 'Weekday'),
        ('weekend', 'Weekend'),
        ('holiday', 'Libur Nasional'),
    )
    PERIOD_CHOICES = (
        ('old_date', 'Tanggal Tua'),
        ('payday', 'Tanggal Gajian'),
        ('young_date', 'Tanggal Muda'),
    )
    WEATHER_CHOICES = (
        ('clear', 'Cerah'),
        ('cloudy', 'Berawan'),
        ('rainy', 'Hujan'),
    )

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='external_factors')
    date = models.DateField()
    day_type = models.CharField(max_length=50, choices=DAY_TYPE_CHOICES)
    period = models.CharField(max_length=50, choices=PERIOD_CHOICES)
    weather = models.CharField(max_length=50, choices=WEATHER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=["business", "date"],
                name="unique_external_factor_per_day"
            )
        ]

    def __str__(self):
        return f"{self.business.name} - {self.date} ({self.get_day_type_display()})"


class Forecast(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='forecasts')
    target_date = models.DateField()
    recommended_qty = models.PositiveIntegerField()
    confidence = models.PositiveIntegerField()
    data_days_used = models.PositiveIntegerField()
    factors_snapshot = models.JSONField(help_text="Snapshot dari faktor dan adjustment saat diprediksi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-target_date']
        constraints = [
            models.UniqueConstraint(
                fields=["menu_item", "target_date"],
                name="unique_forecast_per_day"
            )
        ]

    def __str__(self):
        return f"Forecast {self.menu_item.name} for {self.target_date}: {self.recommended_qty} qty"
