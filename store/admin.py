from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    CustomUser,
    Category,
    Product,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Payment
)


admin.site.register(CustomUser, UserAdmin)

admin.site.register(Category)

admin.site.register(Product)

admin.site.register(Cart)

admin.site.register(CartItem)

admin.site.register(Order)

admin.site.register(OrderItem)

admin.site.register(Payment)