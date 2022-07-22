import httpx

import logging  # isort:skip

log = logging.getLogger("pyimgbox")


class HTTPClient:
    def __init__(self):
        self._client = httpx.Client(timeout=300)
        self._headers = {}

    @property
    def headers(self):
        return self._headers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        self._client.close()

    def get(self, url, params={}, json=False):
        return self._catch_errors(
            request=self._client.build_request(
                method="GET",
                url=url,
                headers=self._headers,
                params=params,
            ),
            json=json,
        )

    def post(self, url, data={}, files={}, json=False):
        return self._catch_errors(
            request=self._client.build_request(
                method="POST",
                url=url,
                headers=self._headers,
                data=data,
                files=files,
            ),
            json=json,
        )

    def _catch_errors(self, request, json=False):
        log.debug("Sending %r", request)

        # Don't send User-Agent
        if "User-Agent" in request.headers:
            del request.headers["User-Agent"]

        try:
            response = self._client.send(request)

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 413:
                    raise ConnectionError(f"{request.url}: File too large")
                elif response.text.strip():
                    raise ConnectionError(f"{request.url}: {response.text}")
                else:
                    raise ConnectionError(f"{request.url}: Unknown status error: {response.status_code}")

        except httpx.NetworkError:
            raise ConnectionError(f"{request.url}: Connection failed")

        except httpx.HTTPError as e:
            if str(e).strip():
                raise ConnectionError(f"{request.url}: {e}")
            else:
                raise ConnectionError(f"{request.url}: Unknown error")

        else:
            if json:
                try:
                    return response.json()
                except ValueError as e:
                    raise RuntimeError(f"{request.url}: Invalid JSON: {e}: {response.text}")
            else:
                return response.text
