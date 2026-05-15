from locust import HttpUser, task, between


class EcommerceUser(HttpUser):

    wait_time = between(1, 2)

    @task
    def buy_product(self):

        self.client.get("/buy-f/22/")