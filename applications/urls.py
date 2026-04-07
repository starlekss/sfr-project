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
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('register/', views.UserRegistrationView.as_view(), name='user_register'),
    path('login/', views.UserLoginView.as_view(), name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('citizen-login/', views.citizen_login, name='citizen_login'),
    path('citizen-register/', views.citizen_register, name='citizen_register'),
]
