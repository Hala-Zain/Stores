from concurrent.futures import ThreadPoolExecutor

from django.http import JsonResponse
from django.db import transaction
from django.db.models import F

from threading import Semaphore
import time

from .models import Product


purchase_semaphore = Semaphore(10)

executor = ThreadPoolExecutor(max_workers=5)



def background_task(product_id):

    print("\nBACKGROUND TASK STARTED")

    print(f"Processing Product {product_id}")

    time.sleep(10)

    print(f" TASK FINISHED FOR PRODUCT {product_id}")




@transaction.atomic
def buy_product(request, product_id):

    acquired = purchase_semaphore.acquire(blocking=False)

    if not acquired:

        print("SERVER BUSY")

        return JsonResponse({
            'message': 'Server busy, try again later'
        })

    try:

        print("\n===== LOCK REQUEST STARTED =====")

        product = Product.objects.select_for_update().get(
            id=product_id
        )

        print(f" Product Locked -> ID: {product.id}")

        time.sleep(5)

        if product.stock_quantity <= 0:

            print(" OUT OF STOCK")

            return JsonResponse({
                'message': 'Out of stock'
            })

        product.stock_quantity -= 1

        product.save()

        print(
            f" LOCK PURCHASE SUCCESS | Remaining: {product.stock_quantity}"
        )

        print("===== LOCK REQUEST FINISHED =====\n")

        return JsonResponse({
            'message': 'Purchase successful',
            'remaining_stock': product.stock_quantity
        })

    finally:

        purchase_semaphore.release()

        print(" Semaphore Released")



def buy_atomic(request, product_id):

    acquired = purchase_semaphore.acquire(blocking=False)

    if not acquired:

        print("SERVER BUSY")

        return JsonResponse({
            'message': 'Server busy'
        })

    try:

        print("\n===== ATOMIC REQUEST STARTED =====")

        print(f" Trying Atomic Buy -> Product {product_id}")

        updated = Product.objects.filter(
            id=product_id,
            stock_quantity__gt=0
        ).update(
            stock_quantity=F('stock_quantity') - 1
        )

        print(f"📌 Rows Updated: {updated}")

        if updated == 0:

            print(" OUT OF STOCK")

            return JsonResponse({
                'message': 'Out of stock'
            })

        product = Product.objects.get(id=product_id)

        print(
            f"ATOMIC PURCHASE SUCCESS | Remaining: {product.stock_quantity}"
        )

        print("===== ATOMIC REQUEST FINISHED =====\n")

        return JsonResponse({
            'message': 'Atomic purchase successful',
            'remaining_stock': product.stock_quantity
        })

    finally:

        purchase_semaphore.release()

        print(" Semaphore Released")





def buy_f(request, product_id):

    acquired = purchase_semaphore.acquire(blocking=False)

    if not acquired:

        print(" SERVER OVERLOADED")

        return JsonResponse({
            'message': 'Server busy'
        })

    try:

        print("\n===== NEW BUY_F REQUEST =====")

        print(f" Fast Processing Product {product_id}")


        updated = Product.objects.filter(
            id=product_id,
            stock_quantity__gt=0
        ).update(
            stock_quantity=F('stock_quantity') - 1
        )

        print(f"📌 Rows Updated: {updated}")



        if updated == 0:

            print(" OUT OF STOCK")

            return JsonResponse({
                'message': 'Out of stock'
            })

     

        print(" Sending Task To ThreadPool")

        executor.submit(
            background_task,
            product_id
        )

        print(" Task Submitted To ThreadPool")

     

        product = Product.objects.get(id=product_id)

        print(
            f" BUY_F SUCCESS | Remaining Stock: {product.stock_quantity}"
        )

        print(" FAST RESPONSE SENT")

        print("===== BUY_F FINISHED =====\n")

        return JsonResponse({
            'message': 'buy_f success',
            'remaining_stock': product.stock_quantity
        })

    except Exception as e:

        print(f" ERROR: {e}")

        return JsonResponse({
            'message': 'Server error'
        })

    finally:

        purchase_semaphore.release()

        print(" Semaphore Released")