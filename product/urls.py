from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('orders/', views.order_history, name='order_history'),
    path('checkout/', views.checkout, name='checkout'),
    path('cart/remove/<int:item_id>/',views.remove_from_cart,name='remove_from_cart'),
    path('cart/update/<int:item_id>/',views.update_cart,name='update_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('product/<int:product_id>/add-to-cart/',views.add_to_cart,name='add_to_cart'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('order/success/<int:order_id>/',views.order_success,name='order_success'),
    path('product/<int:product_id>/order/',views.create_order,name='create_order'),
    path('product/<int:product_id>/',views.product_detail , name = 'product_detail'),
    path('', views.product_list, name='product_list'),
    
]