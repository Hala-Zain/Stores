from locust import HttpUser, task, between
import random
import uuid


class EcommerceUser(HttpUser):

    wait_time = between(1, 2)

    def on_start(self):

        self.username = f"user_{uuid.uuid4().hex}"
        self.password = "123456"

        register_response = self.client.post(
            "register/",
            json={
                "username": self.username,
                "email": f"{self.username}@test.com",
                "password": self.password,
                "is_seller": False
            }
        )

        print("REGISTER STATUS:", register_response.status_code)

        if register_response.status_code != 200:
            return

        login_response = self.client.post(
            "api/token/",
            json={
                "username": self.username,
                "password": self.password
            }
        )

        print("LOGIN STATUS:", login_response.status_code)

        if login_response.status_code != 200:
            return

        data = login_response.json()
        token = data["access"]

        self.client.headers.update({
            "Authorization": f"Bearer {token}"
        })

    @task
    def ecommerce_flow(self):

        product_id = random.randint(1, 3)

        # Add to cart
        add_response = self.client.post(
            "cart/add/",
            json={
                "product_id": product_id,
                "quantity": 1
            }
        )

        print("ADD TO CART:", add_response.status_code)

        # # Traditional checkout (اختياري)
        # with self.client.post(
        #     "checkout/",
        #     catch_response=True
        # ) as checkout_response:

        #     print("CHECKOUT:", checkout_response.status_code)

        #     if checkout_response.status_code != 200:
        #         checkout_response.failure("Checkout failed")
        #     else:
        #         checkout_response.success()

        # 🚀 Distributed checkout (الجديد)
        with self.client.post(
            "checkout_distribution/",
            catch_response=True
        ) as dist_response:

            print("DISTRIBUTED CHECKOUT:", dist_response.status_code)
            print("RESPONSE:", dist_response.text)

            if dist_response.status_code != 200:
                dist_response.failure("Distributed checkout failed")
            else:
                dist_response.success()