from django.urls import path
from . import views

app_name = 'forecast'

urlpatterns = [
    path('variables/', views.variables, name='variables'),
    path('calculate/', views.calculate_view, name='calculate'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('apply/', views.apply_action, name='apply'),
]
