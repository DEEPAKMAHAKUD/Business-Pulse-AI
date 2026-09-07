"""
URL configuration for data_ingestion app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_data, name='upload_data'),
    path('upload/<int:dataset_id>/', views.upload_file, name='upload_file'),
    path('result/<int:import_id>/', views.import_result, name='import_result'),
    path('datasets/', views.dataset_list, name='dataset_list'),
    path('datasets/<int:dataset_id>/', views.dataset_detail, name='dataset_detail'),
    path('datasets/<int:dataset_id>/delete/', views.dataset_delete, name='dataset_delete'),
]
