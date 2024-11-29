from django.urls import path
from .views import AdminDeliveryCompany, AdminOrderHistory, AdminOrderStatistics, BarcodeView, CartView, CategoryView, GenerateBarcode, GetCategory, GetReview, GetProducts, ProductView, Metrics, OrderView, OrderHistory, OrderStatus, PaymentInit, PaymentVerify, ReviewView, UpdateProductQuantity, UserDeliveryCompany, WishlistView



urlpatterns = [
    path('delivery/', AdminDeliveryCompany.as_view(), name='admin_delivery'),
    path('delivery/<int:pk>/', AdminDeliveryCompany.as_view(), name='admin_delivery'),
    path('barcode/', BarcodeView.as_view(), name='barcode'),
    path('generate/', GenerateBarcode.as_view(), name='generate'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/<int:pk>/', CartView.as_view(), name='update-cart'),
    path('category/', CategoryView.as_view(), name='category'),
    path('getcategory/', GetCategory.as_view(), name='get_category'),
    path('metrics/', Metrics.as_view(), name='metrics'),
    path('get-products/', GetProducts.as_view(), name='get_products'),
    path('products/', ProductView.as_view(), name='products'),
    path('products/<int:pk>/', ProductView.as_view(), name='update-products'),
    path('init-payment/', PaymentInit.as_view(), name='initialize_payment'),
    path('verify-payment/', PaymentVerify.as_view(), name='verify_payment'),
    path('orders/', OrderView.as_view(), name='orders'),
    path('order-history/', OrderHistory.as_view(), name='order-history'),
    path('admin-orders/', AdminOrderHistory.as_view(), name='admin-order-history'),
    path('admin-orders/statistics/', AdminOrderStatistics.as_view(), name='admin-order-statistics'),
    path('orderstatus/<int:pk>/', OrderStatus.as_view(), name='order_status'),
    path('see-reviews/<int:product_id>/', GetReview.as_view(), name='product-reviews'),
    path('add-reviews/<int:product_id>/', ReviewView.as_view(), name='add-review'),
    path('userdelivery/', UserDeliveryCompany.as_view(), name='user_delivery'),
    path('userdelivery/<int:pk>/', UserDeliveryCompany.as_view(), name='user_delivery'),
    path('update-quantity/<int:product_id>/', UpdateProductQuantity.as_view(), name='update-product-quantity'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:pk>/', WishlistView.as_view(), name='remove-wishlist'),
]

