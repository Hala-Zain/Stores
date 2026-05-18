from locust import HttpUser, task, between
import random
import uuid


class EcommerceUser(HttpUser):

    wait_time = between(1, 2)

    def on_start(self):

        self.username = f"user_{uuid.uuid4().hex}"
        self.password = "123456"

        self.user_type = random.choice(["seller", "customer"])

        register_response = self.client.post(
            "register/",
            json={
                "username": self.username,
                "email": f"{self.username}@test.com",
                "password": self.password,
                "user_type": self.user_type
            }
        )

        if register_response.status_code != 201:
            return

        login_response = self.client.post(
            "api/token/",
            json={
                "username": self.username,
                "password": self.password
            }
        )

        if login_response.status_code != 200:
            return

        token = login_response.json()["access"]

        self.client.headers.update({
            "Authorization": f"Bearer {token}"
        })

    @task
    def ecommerce_flow(self):

        product_id = random.randint(1, 3)

        # Add to cart
        self.client.post(
            "cart/add/",
            json={
                "product_id": product_id,
                "quantity": 1
            }
        )

        # Checkout distributed
        self.client.post(
            "checkout_distribution/"
        )

    @task(1)
    def seller_analytics(self):

        if self.user_type != "seller":
            return

        period = random.choice(["day", "month", "year"])

        response = self.client.get(
            "seller_sales",   # ✅ fixed endpoint
            params={
                "period": period
            }
        )

        print("ANALYTICS STATUS:", response.status_code)
        print("ANALYTICS RESPONSE:", response.text)