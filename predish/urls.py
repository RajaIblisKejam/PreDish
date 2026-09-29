from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def index_view(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    try:
        business = request.user.businesses.first()
        if not business or not business.onboarding_done:
            return redirect('business:onboarding_step1')
    except:
        return redirect('business:onboarding_step1')
    return redirect('forecast:dashboard')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_view, name='index'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('onboarding/', include('business.urls', namespace='business')),
    path('sales/', include('sales.urls', namespace='sales')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('forecast/', include('forecast.urls', namespace='forecast')),
]
