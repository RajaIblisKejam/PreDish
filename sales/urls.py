from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('input/', views.input_data, name='input_data'),
    path('download-template/', views.download_template, name='download_template'),
    path('history/', views.history, name='history'),
    path('history/export/', views.history_export, name='history_export'),
    path('history/edit/<int:sale_id>/', views.edit_sale, name='edit_sale'),
    path('history/delete/<int:sale_id>/', views.delete_sale, name='delete_sale'),
]
