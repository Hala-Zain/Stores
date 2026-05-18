from django.core.management.base import BaseCommand

from store.models import Product, Category, CustomUser


class Command(BaseCommand):

    help = "Seed products"

    def handle(self, *args, **kwargs):

        seller, created = CustomUser.objects.get_or_create(

            username="seller",

            defaults={

                "email": "seller@test.com",
                "is_seller": True,
                "is_customer": False

            }

        )

        if created:

            seller.set_password("123456")

            seller.save()

        category, _ = Category.objects.get_or_create(

            name="Electronics"
        )

        products = [

            {
                "id": 1,
                "name": "Laptop",
                "description": "Gaming laptop",
                "price": 1200,
                "stock_quantity": 10000
            },

            {
                "id": 2,
                "name": "Phone",
                "description": "Smart phone",
                "price": 800,
                "stock_quantity": 10000
            },

            {
                "id": 3,
                "name": "Headphones",
                "description": "Wireless headphones",
                "price": 200,
                "stock_quantity": 10000

            }

        ]

        for data in products:

            product, created = Product.objects.update_or_create(

                id=data["id"],

                defaults={

                    "name": data["name"],
                    "description": data["description"],
                    "price": data["price"],
                    "stock_quantity": data["stock_quantity"],
                    "category": category,
                    "seller": seller

                }

            )

            self.stdout.write(

                self.style.SUCCESS(

                    f"Product seeded -> {product.name}"

                )

            )

        self.stdout.write(

            self.style.SUCCESS("SEED COMPLETED")

        )