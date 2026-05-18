from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from datetime import timedelta

# from store.models import Category, Product
from django.core.management.base import BaseCommand

from store.models import *

from django.contrib.auth import get_user_model

import random

from decimal import Decimal


import random


class Command(BaseCommand):

    help = 'Seed database with fake data'

    def handle(self, *args, **kwargs):

        # # حذف البيانات القديمة
        # Product.objects.all().delete()
        # Category.objects.all().delete()

        # # إنشاء تصنيفات
        # categories = []

        # for name in ['Electronics', 'Books', 'Clothes']:

        #     category = Category.objects.create(
        #         name=name
        #     )

        #     categories.append(category)

        # # إنشاء منتجات
        # for i in range(20):

        #     Product.objects.create(
        #         category=random.choice(categories),
        #         name=f'Product {i}',
        #         description='Test description',
        #         price=random.randint(10, 500),
        #         stock_quantity=random.randint(1, 100)
        #     )

        # self.stdout.write(
        #     self.style.SUCCESS('Database seeded successfully!')
        # )

        # =====================================
        # DELETE OLD DATA
        # =====================================

        OrderItem.objects.all().delete()

        Order.objects.all().delete()

        Product.objects.all().delete()

        Category.objects.all().delete()

        CustomUser.objects.all().delete()

        # =====================================
        # CREATE SELLER
        # =====================================

        seller = CustomUser.objects.create_user(

            username='seller',

            password='1234',

            is_seller=True

        )

        # =====================================
        # CREATE CUSTOMER
        # =====================================

        customer = CustomUser.objects.create_user(

            username='customer',

            password='1234',

            is_customer=True

        )

        # =====================================
        # CREATE CATEGORIES
        # =====================================

        categories = []

        for name in [

            'Electronics',
            'Books',
            'Clothes'

        ]:

            category = Category.objects.create(
                name=name
            )

            categories.append(category)

        # =====================================
        # CREATE PRODUCTS
        # =====================================

        products = []

        for i in range(200):

            product = Product.objects.create(

                category=random.choice(categories),

                name=f'Product {i}',

                description='Test description',

                price=Decimal(random.randint(10, 500)),

                stock_quantity=1000,
                seller_id=seller.id


            )

            products.append(product)

        self.stdout.write(

            self.style.SUCCESS(
                'Products created'
            )
        )

        # =====================================
        # CREATE ORDERS
        # =====================================

        for i in range(300):

            random_days = random.randint(0, 365)

            random_date = timezone.now() - timedelta(
                days=random_days
            )

            order = Order.objects.create(

                user=customer,

                total_price=0,

                status='paid'

            )

            order.created_at = random_date

            order.save()

            total = 0

            for j in range(random.randint(1, 5)):

                product = random.choice(products)

                quantity = random.randint(1, 10)

                OrderItem.objects.create(

                    order=order,

                    product=product,

                    quantity=quantity,

                    price=product.price

                )

                total += product.price * quantity

            order.total_price = total

            order.save()

        self.stdout.write(

            self.style.SUCCESS(
                'Orders created'
            )
        )

        self.stdout.write(

            self.style.SUCCESS(
                'Database seeded successfully!'
            )
        )
        # =====================================
        # CREATE CARTS WITH MANY ITEMS
        # =====================================

        customers = []

        for i in range(20):

            user = CustomUser.objects.create_user(

                username=f'customer_{i}',

                password='1234',

                is_customer=True

            )

            customers.append(user)

        self.stdout.write(

            self.style.SUCCESS(
                'Customers created'
            )
        )

        # =====================================
        # CREATE CARTS
        # =====================================

        for customer in customers:

            cart = Cart.objects.create(
                user=customer
            )

            selected_products = random.sample(
                products,
                20
            )

            for product in selected_products:

                CartItem.objects.create(

                    cart=cart,

                    product=product,

                    quantity=random.randint(1, 5)

                )

        self.stdout.write(

            self.style.SUCCESS(
                'Carts created'
            )
        )