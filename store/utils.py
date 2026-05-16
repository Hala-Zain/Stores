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