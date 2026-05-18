import json
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Semaphore

from celery import chord, group
from celery.result import AsyncResult

from django.contrib.auth import authenticate, login
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, Order, OrderItem
from .tasks import (
    process_checkout_item,
    process_sales_batch,
    send_verification_email,
)


from .models import (
    Category,
    Product,
    CustomUser,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Payment
)

from .serializers import (
    CategorySerializer,
    ProductSerializer,
    CartSerializer,
    OrderSerializer,
    PaymentSerializer
)


purchase_semaphore = Semaphore(10)

executor = ThreadPoolExecutor(max_workers=5)

processed_requests = 0
def chunk_list(data,chunk_size):
    for i in range(0,len(data),chunk_size):
        yield data[i:i + chunk_size]



def background_task(product_id):

    print("\n===== BACKGROUND TASK STARTED =====")

    print(f"Processing Product {product_id}")

    time.sleep(10)

    print(f"TASK FINISHED FOR PRODUCT {product_id}")

    print("===== BACKGROUND TASK FINISHED =====\n")


@transaction.atomic
def buy_product(request, product_id):

    acquired = purchase_semaphore.acquire(blocking=False)

    if not acquired:

        return JsonResponse({
            'message': 'Server busy'
        })

    try:

        print("\n===== LOCK PURCHASE STARTED =====")

        product = Product.objects.select_for_update().get(
            id=product_id
        )

        print(f"LOCKED PRODUCT -> {product.id}")

        time.sleep(5)

        if product.stock_quantity <= 0:

            print("OUT OF STOCK")

            return JsonResponse({
                'message': 'Out of stock'
            })

        product.stock_quantity -= 1

        product.save()

        print(
            f"PURCHASE SUCCESS | Remaining: {product.stock_quantity}"
        )

        print("===== LOCK PURCHASE FINISHED =====\n")

        return JsonResponse({

            'message': 'Purchase successful',
            'remaining_stock': product.stock_quantity

        })

    finally:

        purchase_semaphore.release()


def buy_atomic(request, product_id):

    acquired = purchase_semaphore.acquire(blocking=False)

    if not acquired:

        return JsonResponse({
            'message': 'Server busy'
        })

    try:

        print("\n===== ATOMIC BUY STARTED =====")

        updated = Product.objects.filter(
            id=product_id,
            stock_quantity__gt=0
        ).update(
            stock_quantity=F('stock_quantity') - 1
        )

        print(f"ROWS UPDATED -> {updated}")

        if updated == 0:

            print("OUT OF STOCK")

            return JsonResponse({
                'message': 'Out of stock'
            })

        product = Product.objects.get(id=product_id)

        print(
            f"ATOMIC SUCCESS | Remaining: {product.stock_quantity}"
        )

        print("===== ATOMIC BUY FINISHED =====\n")

        return JsonResponse({

            'message': 'Atomic purchase successful',
            'remaining_stock': product.stock_quantity

        })

    finally:

        purchase_semaphore.release()


def buy_f(request, product_id):

    acquired = purchase_semaphore.acquire(blocking=False)

    if not acquired:

        return JsonResponse({
            'message': 'Server busy'
        })

    try:

        print("\n===== BUY_F STARTED =====")

        updated = Product.objects.filter(
            id=product_id,
            stock_quantity__gt=0
        ).update(
            stock_quantity=F('stock_quantity') - 1
        )

        print(f"ROWS UPDATED -> {updated}")

        if updated == 0:

            print("OUT OF STOCK")

            return JsonResponse({
                'message': 'Out of stock'
            })

        executor.submit(
            background_task,
            product_id
        )

        print("BACKGROUND TASK SENT")

        product = Product.objects.get(id=product_id)

        print(
            f"BUY_F SUCCESS | Remaining: {product.stock_quantity}"
        )

        print("===== BUY_F FINISHED =====\n")

        return JsonResponse({

            'message': 'buy_f success',
            'remaining_stock': product.stock_quantity

        })

    finally:

        purchase_semaphore.release()


def login_user(request):

    if request.method != 'POST':

        return JsonResponse({
            'message': 'POST request required'
        })

    data = json.loads(request.body)

    username = data.get('username')

    password = data.get('password')

    user = authenticate(
        request,
        username=username,
        password=password
    )

    if user is not None:

        login(request, user)

        print(f"USER LOGGED IN -> {user.username}")

        return JsonResponse({

            'message': 'Login successful',
            'username': user.username

        })

    return JsonResponse({
        'message': 'Invalid username or password'
    })

@api_view(['POST'])
def register(request):

    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    is_seller = request.data.get('is_seller', False)
    is_customer = True

    if is_seller:
        is_customer = False

    if CustomUser.objects.filter(username=username).exists():
        return Response({
            'message': 'Username already exists'
        })

    user = CustomUser.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_seller=is_seller,
        is_customer=is_customer
    )

    send_verification_email.delay(user.email)

    return Response({
        'message': 'User created successfully',
        'user': user.id
    })

# @api_view(['POST'])
# def register(request):

#     username = request.data.get('username')
#     email = request.data.get('email')
#     password = request.data.get('password')

#     is_seller = request.data.get('is_seller', False)
#     is_customer = True

#     if is_seller:
#         is_customer = False

#     if CustomUser.objects.filter(username=username).exists():
#         return Response({
#             'message': 'Username already exists'
#         })

#     user = CustomUser.objects.create_user(
#         username=username,
#         email=email,
#         password=password,
#         is_seller=is_seller,
#         is_customer=is_customer
#     )

#     send_verification_email.delay(user.email)

#     return Response({
#         'message': 'User created successfully',
#         'user': user.id
#     })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):

    return Response({

        'username': request.user.username,
        'email': request.user.email,
        'is_seller': request.user.is_seller,
        'is_customer': request.user.is_customer,

    })


class CategoryListCreateView(generics.ListCreateAPIView):

    queryset = Category.objects.all()

    serializer_class = CategorySerializer


class ProductListCreateView(generics.ListCreateAPIView):

    queryset = Product.objects.all()

    serializer_class = ProductSerializer


class CartView(generics.RetrieveAPIView):

    serializer_class = CartSerializer

    permission_classes = [IsAuthenticated]

    def get_object(self):

        cart, created = Cart.objects.get_or_create(
            user=self.request.user
        )

        return cart


class AddToCartView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        product_id = request.data.get('product_id')

        quantity = int(request.data.get('quantity', 1))

        product = Product.objects.get(id=product_id)

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product
        )

        if not created:

            item.quantity += quantity

        else:

            item.quantity = quantity

        item.save()

        print(
            f"ADDED TO CART -> {product.name} | Qty: {item.quantity}"
        )

        return Response({
            'message': 'Added to cart'
        })


class OrderListView(generics.ListAPIView):

    serializer_class = OrderSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Order.objects.filter(
            user=self.request.user
        )


class PaymentListView(generics.ListAPIView):

    serializer_class = PaymentSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Payment.objects.filter(
            order__user=self.request.user
        )


def product_details(request, id):

    product = get_object_or_404(Product, id=id)

    data = {

        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': str(product.price),
        'stock_quantity': product.stock_quantity

    }

    return JsonResponse(data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_cart_item(request, id):

    item = get_object_or_404(

        CartItem,
        id=id,
        cart__user=request.user

    )

    item.delete()

    print(f"CART ITEM DELETED -> {id}")

    return Response({
        'message': 'Item deleted'
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, id):

    item = get_object_or_404(

        CartItem,
        id=id,
        cart__user=request.user

    )

    quantity = request.data.get('quantity')

    item.quantity = quantity

    item.save()

    print(
        f"CART ITEM UPDATED -> {item.product.name} | Qty: {item.quantity}"
    )

    return Response({

        'message': 'Quantity updated',
        'quantity': item.quantity

    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):

    print("\n===== CHECKOUT STARTED =====")

    cart = Cart.objects.get(
        user=request.user
    )

    items = cart.items.all()

    if not items:

        print("CART EMPTY")

        return Response({
            'message': 'Cart is empty'
        })

    total = 0

    order = Order.objects.create(

        user=request.user,
        total_price=0

    )

    print(f"ORDER CREATED -> {order.id}")

    for item in items:

        print(
            f"PROCESSING -> {item.product.name}"
        )

        updated = Product.objects.filter(

            id=item.product.id,
            stock_quantity__gte=item.quantity

        ).update(

            stock_quantity=F('stock_quantity') - item.quantity

        )

        print(f"ROWS UPDATED -> {updated}")

        if updated == 0:

            print("OUT OF STOCK")

            return Response({
                'message': f'{item.product.name} out of stock'
            })

        executor.submit(
            background_task,
            item.product.id
        )

        print("BACKGROUND TASK SENT")

        OrderItem.objects.create(

            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price

        )

        total += item.product.price * item.quantity

        product = Product.objects.get(
            id=item.product.id
        )

        print(
            f"REMAINING STOCK -> {product.stock_quantity}"
        )

    order.total_price = total

    order.save()

    print(f"TOTAL -> {total}")

    items.delete()

    print("CART CLEARED")

    print("CHECKOUT SUCCESS")

    print("===== CHECKOUT FINISHED =====\n")

    return Response({

        'message': 'Checkout successful',
        'order_id': order.id,
        'total_price': total

    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_api(request):

    order_id = request.data.get('order_id')

    payment_method = request.data.get(
        'payment_method'
    )

    order = get_object_or_404(

        Order,
        id=order_id,
        user=request.user

    )

    payment = Payment.objects.create(

        order=order,
        amount=order.total_price,
        payment_method=payment_method,
        payment_status='completed'

    )

    order.status = 'paid'

    order.save()

    print(f"PAYMENT SUCCESS -> ORDER {order.id}")

    return Response({

        'message': 'Payment successful',
        'payment_id': payment.id

    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_details(request, id):

    order = get_object_or_404(

        Order,
        id=id,
        user=request.user

    )

    data = {

        'id': order.id,
        'status': order.status,
        'total_price': str(order.total_price)

    }

    print(f"ORDER DETAILS VIEWED -> {order.id}")

    return Response(data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def cancel_order(request, id):

    order = get_object_or_404(

        Order,
        id=id,
        user=request.user

    )

    order.status = 'cancelled'

    order.save()

    print(f"ORDER CANCELLED -> {order.id}")

    return Response({
        'message': 'Order cancelled'
    })


def search_products(request):

    q = request.GET.get('q')

    products = Product.objects.filter(
        name__icontains=q
    )

    data = []

    for product in products:

        data.append({

            'id': product.id,
            'name': product.name,
            'price': str(product.price)

        })

    return JsonResponse(
        data,
        safe=False
    )


def products_by_category(request, id):

    products = Product.objects.filter(
        category_id=id
    )

    data = []

    for product in products:

        data.append({

            'id': product.id,
            'name': product.name,
            'price': str(product.price)

        })

    return JsonResponse(
        data,
        safe=False
    )


def server_status(request):

    active_threads = threading.active_count()

    status = "Normal"

    if active_threads > 20:

        status = "High Load"

    return JsonResponse({

        'active_threads': active_threads,
        'server_status': status

    })


def queue_status(request):

    return JsonResponse({

        'waiting_requests': 0,
        'processed_requests': processed_requests

    })


def stats(request):

    return JsonResponse({

        'products': Product.objects.count(),
        'orders': Order.objects.count(),
        'users': CustomUser.objects.count(),
        'active_threads': threading.active_count(),
        'processed_requests': processed_requests

    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkoutLoadDistribution(request):

    print("\n===== DISTRIBUTED CHECKOUT STARTED =====")

    cart = Cart.objects.get(user=request.user)
    items = list(cart.items.all())

    if not items:
        return Response({'message': 'Cart is empty'})

    order = Order.objects.create(
        user=request.user,
        total_price=0
    )

    job = group(
        process_checkout_item.s({
            'product_id': item.product.id,
            'quantity': item.quantity
        }) for item in items
    )

    async_result = job.apply_async()

    cart.items.all().delete()

    print(f"TASK GROUP STARTED -> {async_result.id}")

    return Response({
        "message": "Checkout started",
        "order_id": order.id,
        "task_group_id": async_result.id
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_sales_analytics(request):

    user = request.user

    if not user.is_seller:
        return Response({'message': 'denied'}, status=403)

    period = request.GET.get('period', 'day')
    now = timezone.now()

    if period == 'day':
        start_date = now - timedelta(days=1)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        return Response({'message': 'Invalid period'}, status=400)

    order_items = list(
        OrderItem.objects.filter(
            product__seller=user,
            order__created_at__gte=start_date
        ).values(
            'price',
            'quantity',
            'order_id',
            'product__name'
        )
    )

    chunks = [
        order_items[i:i+5]
        for i in range(0, len(order_items), 5)
    ]

    job = group(
        process_sales_batch.s(chunk)
        for chunk in chunks
    )

    async_result = job.apply_async()

    print(f"ANALYTICS TASK STARTED -> {async_result.id}")

    return Response({
        "message": "Analytics processing started",
        "task_group_id": async_result.id,
        "chunks": len(chunks)
    })

