import random
import uuid
from locust import HttpUser, between, task


class EcommerceUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
     
        self.username = f"user_{uuid.uuid4().hex[:10]}"
        self.password = "123456"
        self.user_type = random.choice(["seller", "customer"])
        
        self.is_authenticated = False

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

        if login_response.status_code == 200:
            token = login_response.json().get("access")
            self.client.headers.update({
                "Authorization": f"Bearer {token}"
            })
            self.is_authenticated = True

    @task(3)
    def ecommerce_flow(self):
      
        if not self.is_authenticated:
            return

        product_id = random.randint(1, 3)

        self.client.post(
            "cart/add/",
            json={
                "product_id": product_id,
                "quantity": 1
            }
        )

        self.client.post("checkout_distribution/")

    @task(1)
    def seller_analytics(self):
        if not self.is_authenticated or self.user_type != "seller":
            return

        period = random.choice(["day", "month", "year"])

        self.client.get(
            "seller_sales",
            params={
                "period": period
            }
        )