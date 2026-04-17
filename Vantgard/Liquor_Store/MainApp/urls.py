from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('productos/', views.product_list, name='product_list'),
    path('productos/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cuenta/', views.account, name='account'),
    path('registro/', views.register, name='register'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='MainApp/auth/login.html',
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout',
    ),
]
