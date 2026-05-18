from celery import shared_task
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F

from .models import (
    Product,
    Order,
    OrderItem,
    CartItem
)

import time


# =====================================================
# 1. EMAIL TASK
# =====================================================

@shared_task(
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True
)
def send_verification_email(email):

    print(f"\n===== EMAIL TASK STARTED =====")

    print(f"SENDING EMAIL TO -> {email}")

    time.sleep(2)  # احذفها بالإنتاج

    send_mail(

        subject='Verify Your Account',

        message=(
            'Welcome! Your account was created successfully.'
        ),

        from_email='huda1812zain@gmail.com',

        recipient_list=[email],

        fail_silently=False,

    )

    print(f"EMAIL SENT -> {email}")

    print("===== EMAIL TASK FINISHED =====\n")

    return {

        "success": True,
        "email": email

    }


# =====================================================
# 2. SALES BATCH TASK
# =====================================================

@shared_task
def process_sales_batch(batch):

    print("\n===== SALES BATCH STARTED =====")

    batch_total = 0

    batch_orders = set()

    batch_products = {}

    for item in batch:

        subtotal = (
            float(item['price']) * item['quantity']
        )

        batch_total += subtotal

        batch_orders.add(
            item['order_id']
        )

        product_name = item['product__name']

        if product_name not in batch_products:

            batch_products[product_name] = 0

        batch_products[product_name] += item['quantity']

    print(
        f"BATCH TOTAL -> {batch_total}"
    )

    print(
        f"BATCH ORDERS -> {len(batch_orders)}"
    )

    print("===== SALES BATCH FINISHED =====\n")

    return {

        "total_sales": batch_total,

        "total_orders": len(batch_orders),

        "products": batch_products

    }


# =====================================================
# 3. PROCESS CHECKOUT ITEM TASK
# =====================================================

@shared_task(

    autoretry_for=(Exception,),

    retry_kwargs={
        'max_retries': 3
    },

    retry_backoff=True

)
def process_checkout_item(item_data):

    print("\n===== CHECKOUT ITEM TASK STARTED =====")

    product_id = item_data['product_id']

    quantity = item_data['quantity']

    order_id = item_data['order_id']

    print(
        f"PROCESSING PRODUCT -> {product_id}"
    )

    try:

        with transaction.atomic():

            updated = Product.objects.filter(

                id=product_id,

                stock_quantity__gte=quantity

            ).update(

                stock_quantity=F(
                    'stock_quantity'
                ) - quantity

            )

            print(
                f"ROWS UPDATED -> {updated}"
            )

            if updated == 0:

                product = Product.objects.filter(
                    id=product_id
                ).first()

                print("OUT OF STOCK")

                return {

                    "success": False,

                    "product": (
                        product.name
                        if product
                        else "unknown"
                    ),

                    "reason": "OUT_OF_STOCK"

                }

            product = Product.objects.get(
                id=product_id
            )

            OrderItem.objects.create(

                order_id=order_id,

                product=product,

                quantity=quantity,

                price=product.price

            )

            subtotal = (
                float(product.price) * quantity
            )

            print(
                f"SUCCESS -> {product.name}"
            )

            print(
                f"REMAINING STOCK -> "
                f"{product.stock_quantity}"
            )

            print(
                f"SUBTOTAL -> {subtotal}"
            )

            print(
                "===== CHECKOUT ITEM TASK FINISHED =====\n"
            )

            return {

                "success": True,

                "product_id": product.id,

                "product": product.name,

                "quantity": quantity,

                "price": float(product.price),

                "subtotal": subtotal

            }

    except Product.DoesNotExist:

        print("PRODUCT NOT FOUND")

        return {

            "success": False,

            "product": "unknown",

            "reason": "NOT_FOUND"

        }

    except Exception as e:

        print(f"TASK ERROR -> {str(e)}")

        raise e


# =====================================================
# 4. FINALIZE ORDER TASK
# =====================================================

@shared_task
def finalize_order(results, order_id, user_id):

    print("\n===== FINALIZE ORDER STARTED =====")

    order = Order.objects.get(
        id=order_id
    )

    failed_items = []

    total = 0

    for result in results:

        if result['success']:

            total += result['subtotal']

        else:

            failed_items.append(result)

    if failed_items:

        print("CHECKOUT FAILED")

        order.status = 'failed'

        order.save()

        print(
            f"FAILED ITEMS -> {failed_items}"
        )

        print(
            "===== FINALIZE ORDER FAILED =====\n"
        )

        return {

            "success": False,

            "order_id": order.id,

            "failed_items": failed_items

        }

    order.total_price = total

    order.status = 'completed'

    order.save()

    CartItem.objects.filter(
        cart__user_id=user_id
    ).delete()

    print(
        f"ORDER COMPLETED -> {order.id}"
    )

    print(
        f"TOTAL PRICE -> {total}"
    )

    print("CART CLEARED")

    print(
        "===== FINALIZE ORDER FINISHED =====\n"
    )

    return {

        "success": True,

        "order_id": order.id,

        "total_price": total

    }