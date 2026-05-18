from celery import shared_task
from django.core.mail import send_mail
from .models import Product
from django.db.models import F

import time

@shared_task

def send_verification_email(email, token):

    verify_link = f"http://127.0.0.1:8000/verify-email/{token}/"

    send_mail(
        subject="Verify Your Account",
        message=f"Click this link to verify your account: {verify_link}",
        from_email="zhala369@gmail.com",
        recipient_list=[email],
        fail_silently=False,
    )

    return "sent"
@shared_task
def process_sales_batch(batch):
    batch_total = 0

    batch_orders = set()

    batch_products = {}
    for item in batch:

        batch_total += float(item['price']) * item['quantity']

        batch_orders.add(item['order_id'])
        product_name = item['product__name']

        if product_name not in batch_products:

            batch_products[product_name] = 0

        batch_products[product_name] += item['quantity']  
    return {

        'total_sales': batch_total,
        'total_orders': len(batch_orders),
        'products': batch_products

    }
@shared_task
def process_checkout_item(item_data):

    product_id = item_data['product_id']

    quantity = item_data['quantity']

    product = Product.objects.get(id=product_id)

    updated = Product.objects.filter(

        id=product.id,
        stock_quantity__gte=quantity

    ).update(

        stock_quantity=F('stock_quantity') - quantity

    )

    if updated == 0:

        return {

            'success': False,
            'product': product.name

        }

    total = float(product.price) * quantity

    return {

        'success': True,
        'product': product.name,
        'quantity': quantity,
        'price': float(product.price),
        'total': total

    }
