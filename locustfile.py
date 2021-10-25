"""Load test a single trait page"""
from locust import HttpUser, task, between


class LoadTest(HttpUser):
    wait_time = between(1, 2.5)

    @task
    def fetch_trait(self):
        """Fetch a single trait"""
        # /api/v_pre1/gen_dropdown
        self.client.get("/show_trait?trait_id="
                        "1457545_at&dataset=HC_M2_0606_P")
