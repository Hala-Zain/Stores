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


@shared_task(
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True
)
def send_verification_email(email):

    print(f"\n===== EMAIL TASK STARTED =====")

    print(f"SENDING EMAIL TO -> {email}")

    time.sleep(2) 

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

from celery import shared_task
from django.db import transaction
from django.core.cache import cache
from .models import Product

@shared_task
def process_checkout_item(item_data):
    product_id = item_data['product_id']
    quantity = item_data['quantity']
    
    print(f"\n===== ADAPTIVE THRESHOLD CHECKOUT STARTED FOR PRODUCT {product_id} =====")
    
    redis_key = f"product_tokens:{product_id}"
    
    new_stock = cache.get(redis_key)
    
    if new_stock is None:
        try:
            with transaction.atomic():
                product = Product.objects.get(id=product_id)
                new_stock = product.stock_quantity
                cache.set(redis_key, new_stock, timeout=None)
        except Product.DoesNotExist:
            return {"success": False, "reason": "PRODUCT_NOT_FOUND"}

    try:
        if new_stock <= 5:
            print(f"⚠️ [CRITICAL STOCK DETECTED: {new_stock}]. SWITCHING TO STRICT MYSQL LOCK...")
            
            with transaction.atomic():
                product = Product.objects.select_for_update().get(id=product_id)
                
                if product.stock_quantity >= quantity:
                    product.stock_quantity -= quantity
                    product.save()
                    
                    cache.set(redis_key, product.stock_quantity, timeout=None)
                    print(f"✅ [PESSIMISTIC SUCCESS] Critical item sold safely. DB Stock: {product.stock_quantity}")
                    return {"success": True, "product_id": product_id}
                else:
                    print(f"❌ [PESSIMISTIC FAIL] Product {product_id} is OUT OF STOCK.")
                    return {"success": False, "product": product.name, "reason": "OUT_OF_STOCK"}

        else:
            if new_stock < quantity:
                print(f"🛑 [REDIS SHIELD] Blocked by Redis pre-check. Out of stock.")
                return {"success": False, "product_id": product_id, "reason": "OUT_OF_STOCK"}

            new_stock -= quantity
            cache.set(redis_key, new_stock, timeout=None)

            Product.objects.filter(id=product_id).update(stock_quantity=new_stock)
            print(f"⚡ [REDIS FAST SUCCESS] Subtracted {quantity} from RAM. New Stock: {new_stock}")
            return {"success": True, "product_id": product_id}

    except Exception as e:
        if new_stock is not None and new_stock > 5:
            cache.incr(redis_key, quantity)
        print(f"💥 ERROR IN THRESHOLD TASK: {str(e)}")
        return {"success": False, "reason": str(e)}

# =====================================================
# 4. FINALIZE ORDER TASK
# =====================================================

@shared_task
def finalize_order(results, order_id, user_id):
    print("\n===== FINALIZE ORDER STARTED =====")

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        print(f"❌ Order {order_id} not found in database.")
        return {"success": False, "reason": "ORDER_NOT_FOUND"}

    failed_items = []
    total = 0

    # 🔄 فحص النتائج بحذر شديد لمنع الـ KeyError نهائياً
    for result in results:
        # تأمين 1: التأكد من أن النتيجة ليست فارغة وأنها عبارة عن قاموس (Dictionary)
        if not result or not isinstance(result, dict):
            failed_items.append({"success": False, "reason": "INVALID_OR_EMPTY_RESULT"})
            continue

        # تأمين 2: جلب قيمة success بأمان، إذا لم تكن موجودة نعتبرها False تلقائياً
        is_success = result.get('success', False)

        if is_success:
            # نأخذ الحساب بأمان، وإذا لم يجد 'subtotal' يضع 0 بدلاً من الانهيار
            total += result.get('subtotal', 0)
        else:
            # إذا فشل المنتج (مثل الـ Headphones اللي خلص ستوكها بالـ Logs) نضيفه هنا
            failed_items.append(result)

    # 🛑 إذا كان هناك أي منتج فاشل في الطلب
    if failed_items:
        print("CHECKOUT FAILED")
        order.status = 'failed'
        order.save()

        print(f"FAILED ITEMS -> {failed_items}")
        print("===== FINALIZE ORDER FAILED =====\n")

        return {
            "success": False,
            "order_id": order.id,
            "failed_items": failed_items
        }

    #  إذا نجحت كل المنتجات وتم حجز مخزونها بالكامل
    order.total_price = total
    order.status = 'completed'
    order.save()

    # تفريغ سلة المستخدم الفعلي
    CartItem.objects.filter(cart__user_id=user_id).delete()

    print(f"ORDER COMPLETED -> {order.id}")
    print(f"TOTAL PRICE -> {total}")
    print("CART CLEARED")
    print("===== FINALIZE ORDER FINISHED =====\n")

    return {
        "success": True,
        "order_id": order.id,
        "total_price": total
    }
    