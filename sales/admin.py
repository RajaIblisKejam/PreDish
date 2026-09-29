from django.contrib import admin
from .models import DailySale

@admin.register(DailySale)
class DailySaleAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'date', 'qty_sold', 'qty_produced', 'qty_leftover')
    list_filter = ('date', 'menu_item__business')
    search_fields = ('menu_item__name',)
