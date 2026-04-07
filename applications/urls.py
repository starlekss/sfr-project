from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('status/<int:app_id>/', views.application_status, name='application_status'),
    path('search/', views.search_application, name='search_application'),
    path('login/', views.operator_login, name='operator_login'),
    path('logout/', views.operator_logout, name='operator_logout'),
    path('applications/', views.application_list, name='application_list'),
    path('applications/<int:app_id>/', views.application_detail, name='application_detail'),
    path('applications/<int:app_id>/pdf/', views.download_pdf, name='download_pdf'),
    path('create-admin/', views.create_admin, name='create_admin'),
]
