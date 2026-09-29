from django.db import models
from django.contrib.auth.models import User

class Business(models.Model):
    TYPE_CHOICES = (
        ('cafe', 'Kafe'),
        ('restaurant', 'Restoran'),
        ('catering', 'Katering'),
    )
    
    PLAN_CHOICES = (
        ('freemium', 'Freemium'),
        ('starter', 'Starter'),
        ('growth', 'Growth'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='businesses')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    plan = models.CharField(max_length=50, choices=PLAN_CHOICES, default='freemium')
    onboarding_done = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Businesses"

    def __str__(self):
        return f"{self.name} ({self.owner.username})"

class MenuItem(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['business', 'name']

    def __str__(self):
        return f"{self.name} - {self.business.name}"
