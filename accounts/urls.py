from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.decorators.http import require_POST
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', require_POST(auth_views.LogoutView.as_view(template_name='accounts/logout.html')), name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('business_list/', views.dashboard, name='business_list'),
]