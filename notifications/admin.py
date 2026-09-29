from django.contrib import admin
from .models import NotificationSetting

@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ('business', 'email_daily', 'popup', 'reminder_input_night')
