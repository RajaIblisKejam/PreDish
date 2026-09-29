from django.contrib import admin
from .models import ExternalFactor, Forecast

@admin.register(ExternalFactor)
class ExternalFactorAdmin(admin.ModelAdmin):
    list_display = ('business', 'date', 'day_type', 'period', 'weather')
    list_filter = ('day_type', 'period', 'weather', 'business')

@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'target_date', 'recommended_qty', 'confidence')
    list_filter = ('target_date', 'menu_item__business')
