from django.db import models
from business.models import Business

class NotificationSetting(models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='notification_setting')
    email_daily = models.BooleanField(default=True)
    popup = models.BooleanField(default=True)
    reminder_input_night = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.business.name}"

class Notification(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50) # 'missing_data', 'accuracy_drop', 'overproduction'
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.type}] {self.business.name}"
