import time
import random
import requests

# Some districts need this.
#
# # Usage:
# requester = requestsss.EBRequest()
# response = requester.get("https://example.com/api/data")
# print(response.json())

class EBRequest:
    def __init__(self, max_retries=5, base_delay=0.125, max_delay=16.0, backoff_factor=2):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def get(self, url, **kwargs):
        return self._request_with_backoff("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._request_with_backoff("POST", url, **kwargs)

    def _request_with_backoff(self, method, url, **kwargs):
        retries = 0
        while retries <= self.max_retries:
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()  # Raises an exception for 4xx and 5xx responses.
                return response
            except requests.RequestException as e:
                # If the error is a 4xx client error, raise it without retrying
                if isinstance(e, requests.HTTPError) and 400 <= e.response.status_code < 500:
                    raise e

                wait = min(self.max_delay, (self.backoff_factor ** retries) * self.base_delay)
                print(e)
                print(f'Retrying {retries}...')
                jitter = wait * random.uniform(0.5, 1.5)  # Add randomness
                time.sleep(jitter)
                retries += 1

        raise requests.RequestException(f"Failed after {self.max_retries} retries")