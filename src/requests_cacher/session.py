import requests
from typing import Optional

class Session:
    def __init__(self, domain, headers: Optional[dict] = None, params: Optional[dict] = None) -> None:
        self.domain = domain
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)
        if params:
            self.session.params = params

    def get(self, endpoint: str, params: Optional[dict]) -> dict:
        uri = f"{self.domain}/{endpoint}"
        response = self.session.get(uri, params=params)
        response.raise_for_status()

        return response.json()
