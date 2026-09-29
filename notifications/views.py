from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Notification
from .services import check_and_create_alerts

@login_required
def list_notifications(request):
    business = request.user.businesses.first()
    if not business:
        return render(request, 'notifications/list.html', {'notifications': []})
        
    check_and_create_alerts(business)
    
    notifications = Notification.objects.filter(business=business).order_by('-created_at')[:20]
    Notification.objects.filter(business=business, is_read=False).update(is_read=True)
    
    return render(request, 'notifications/list.html', {'notifications': notifications})
