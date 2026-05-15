from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from store.models import Category, Product

import random


class Command(BaseCommand):

    help = 'Seed database with fake data'

    def handle(self, *args, **kwargs):

        # حذف البيانات القديمة
        Product.objects.all().delete()
        Category.objects.all().delete()

        # إنشاء تصنيفات
        categories = []

        for name in ['Electronics', 'Books', 'Clothes']:

            category = Category.objects.create(
                name=name
            )

            categories.append(category)

        # إنشاء منتجات
        for i in range(20):

            Product.objects.create(
                category=random.choice(categories),
                name=f'Product {i}',
                description='Test description',
                price=random.randint(10, 500),
                stock_quantity=random.randint(1, 100)
            )

        self.stdout.write(
            self.style.SUCCESS('Database seeded successfully!')
        )