from django.urls import path

from .views import (
    buy_product,
    buy_atomic,
    buy_f,
    login_user,
    register,
    product_details,
    delete_cart_item,
    seller_sales_analytics,
    update_cart_item,
    checkout,
    payment_api,
    order_details,
    cancel_order,
    search_products,
    products_by_category,
    server_status,
    queue_status,
    stats,
    profile,
    checkoutLoadDistribution,trending_products,#test,
)

from .views import (
    CategoryListCreateView,
    ProductListCreateView,
    CartView,
    AddToCartView,
    OrderListView,
    PaymentListView,
)

urlpatterns = [
    path('buy/<int:product_id>/', buy_product),
    path('buy/a/<int:product_id>/', buy_atomic),
    path('buy-f/<int:product_id>/', buy_f),
    path('login/', login_user),
    path('register/', register),
    path('profile/', profile),
    path('categories/', CategoryListCreateView.as_view()),
    path('products/', ProductListCreateView.as_view()),
    path('cart/', CartView.as_view()),
    path('cart/add/', AddToCartView.as_view()),
    path('orders/', OrderListView.as_view()),
    path('payments/', PaymentListView.as_view()),
    path('products/<int:id>/', product_details),
    path('cart/item/<int:id>/', delete_cart_item),
    path('cart/item/update/<int:id>/', update_cart_item),
    path('checkout/', checkout),
    path('payment/', payment_api),
    path('orders/<int:id>/', order_details),    
    path('orders/<int:id>/cancel/', cancel_order),
    path('products/search/', search_products),
    path('products/category/<int:id>/', products_by_category),
    path('server-status/', server_status),
    path('queue-status/', queue_status),
    path('stats/', stats),
    path('seller_sales', seller_sales_analytics),
    path('checkout_distribution/', checkoutLoadDistribution),
    path('trending_products/',trending_products)

]