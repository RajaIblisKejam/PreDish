from django.db import models
from business.models import MenuItem

class DailySale(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='daily_sales')
    date = models.DateField()
    qty_sold = models.PositiveIntegerField()
    qty_produced = models.PositiveIntegerField(null=True, blank=True)
    qty_leftover = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'menu_item__name']
        constraints = [
            models.UniqueConstraint(
                fields=["menu_item", "date"],
                name="unique_menu_sale_per_day"
            )
        ]

    def __str__(self):
        return f"{self.menu_item.name} - {self.date}: {self.qty_sold} sold"
