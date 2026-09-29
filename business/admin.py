from django.contrib import admin
from .models import Business, MenuItem

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'type', 'plan', 'onboarding_done', 'created_at')
    list_filter = ('type', 'plan', 'onboarding_done')
    search_fields = ('name', 'owner__username')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'is_active', 'created_at')
    list_filter = ('is_active', 'business')
    search_fields = ('name', 'business__name')
