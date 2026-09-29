from django.urls import path
from . import views

app_name = 'business'

urlpatterns = [
    path('onboarding/1/', views.onboarding_step1, name='onboarding_step1'),
    path('onboarding/2/', views.onboarding_step2, name='onboarding_step2'),
    path('onboarding/3/', views.onboarding_step3, name='onboarding_step3'),
    path('menus/', views.manage_menus, name='manage_menus'),
    path('menus/delete/<int:menu_id>/', views.delete_menu, name='delete_menu'),
]
