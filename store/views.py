from concurrent.futures import ThreadPoolExecutor
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
import json
from threading import Semaphore
import time
from rest_framework.decorators import api_view
from .models import Product
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView, csrf_exempt
from .models import (Category, Product , CustomUser,Cart, CartItem ,OrderItem, Order, Payment)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404



from .serializers import (
    CategorySerializer,
    ProductSerializer,
    CartSerializer,
    CartItemSerializer,
    OrderSerializer,
    PaymentSerializer
)

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

    print("INVALID LOGIN")

    return JsonResponse({
        'message': 'Invalid username or password'
    })


@api_view(['POST'])
def register(request):

    username = request.data.get('username')

    email = request.data.get('email')

    password = request.data.get('password')

    if CustomUser.objects.filter(username=username).exists():

        return Response({
            'message': 'Username already exists'
        })

    user = CustomUser.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    print(f"NEW USER CREATED -> {user.username}")

    return Response({
        'message': 'User created successfully'
    })



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

        return Payment.objects.all()
    



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


@csrf_exempt
def delete_cart_item(request, id):

    if request.method != 'DELETE':

        return JsonResponse({
            'message': 'DELETE method required'
        })

    item = get_object_or_404(
        CartItem,
        id=id
    )

    item.delete()

    return JsonResponse({
        'message': 'Item deleted'
    })


@csrf_exempt
def update_cart_item(request, id):

    if request.method != 'PUT':

        return JsonResponse({
            'message': 'PUT method required'
        })

    item = get_object_or_404(
        CartItem,
        id=id
    )

    body = json.loads(request.body)

    quantity = body.get('quantity')

    item.quantity = quantity

    item.save()

    return JsonResponse({

        'message': 'Quantity updated',
        'quantity': item.quantity

    })



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):

    cart = Cart.objects.get(user=request.user)

    items = cart.items.all()

    if not items:
        return Response({'message': 'Cart is empty'})

    total = 0

    for item in items:
        total += item.product.price * item.quantity

    order = Order.objects.create(
        user=request.user,
        total_price=total
    )

    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

    items.delete()

    return Response({
        'message': 'Checkout successful',
        'order_id': order.id
    })



@csrf_exempt
def payment_api(request):

    if request.method != 'POST':

        return JsonResponse({
            'message': 'POST method required'
        })

    body = json.loads(request.body)

    order_id = body.get('order_id')

    payment_method = body.get(
        'payment_method'
    )

    order = Order.objects.get(
        id=order_id
    )

    payment = Payment.objects.create(

        order=order,
        amount=order.total_price,
        payment_method=payment_method,
        payment_status='completed'

    )

    order.status = 'paid'

    order.save()

    return JsonResponse({

        'message': 'Payment successful',
        'payment_id': payment.id

    })



def order_details(request, id):

    order = get_object_or_404(
        Order,
        id=id
    )

    data = {

        'id': order.id,
        'status': order.status,
        'total_price': str(order.total_price)

    }

    return JsonResponse(data)



@csrf_exempt
def cancel_order(request, id):

    if request.method != 'PUT':

        return JsonResponse({
            'message': 'PUT method required'
        })

    order = get_object_or_404(
        Order,
        id=id
    )

    order.status = 'cancelled'

    order.save()

    return JsonResponse({
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

        'waiting_requests': request_queue.qsize(),
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