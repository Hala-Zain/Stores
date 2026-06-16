from django.db.models import F
from .models import Product

def process_product_purchase(product, quantity):
    print(f"PROCESS PURCHASE -> {product.name}")

    updated = Product.objects.filter(
        id=product.id,
        stock_quantity__gte=quantity
    ).update(
        stock_quantity=F('stock_quantity') - quantity
    )

    return updated > 0
from django.core.cache import cache


def try_acquire(key, limit=25, timeout=60):
    current = cache.get(key)

    if current is None:
        cache.set(key, 0, timeout=timeout)

    current = cache.get(key, 0)

    if current >= limit:
        return False

    cache.incr(key)
    return True


def release(key):
    current = cache.get(key, 0)

    if current > 0:
        cache.decr(key)