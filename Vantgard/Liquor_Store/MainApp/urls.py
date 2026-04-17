from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('productos/', views.product_list, name='product_list'),
    path('productos/<slug:slug>/', views.product_detail, name='product_detail'),
    path('carrito/', views.cart_detail, name='cart_detail'),
    path('carrito/agregar/<int:product_id>/', views.cart_add, name='cart_add'),
    path('carrito/actualizar/<int:product_id>/', views.cart_update, name='cart_update'),
    path('carrito/quitar/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/exito/<uuid:codigo>/', views.checkout_success, name='checkout_success'),
    path('tracking/<str:token>/', views.order_tracking, name='order_tracking'),
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
