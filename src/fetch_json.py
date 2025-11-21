import json
import os
import ssl
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TRANSIENT_ERRORS = (URLError, TimeoutError, ConnectionError, ssl.SSLError)

DEFAULT_TIMEOUT = float(os.getenv("HYPERACT_HTTP_TIMEOUT", "20"))
DEFAULT_RETRIES = int(os.getenv("HYPERACT_HTTP_RETRIES", "3"))
DEFAULT_BACKOFF = float(os.getenv("HYPERACT_HTTP_BACKOFF", "0.5"))


def fetch_json(url: str) -> dict[str, Any]:
    last_exc: Exception | None = None
    request = Request(
        url,
        headers = {
            "Accept": "application/json",
            "User-Agent": "hyperact-mcp/1.0",
            "Connection": "close"
        }
    )

    for attempt in range(DEFAULT_RETRIES):
        try: 
            with urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
                return json.loads(response.read().decode("utf8"))
            
        except HTTPError as exc:
            raise RuntimeError(f"Request failed with status {exc.code} for {url}") from exc
        
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON returned from {url}") from exc

        except TRANSIENT_ERRORS as exc:
            last_exc = exc
            time.sleep(DEFAULT_BACKOFF * (2 ** attempt))

    raise RuntimeError(
        f"Unable to reach {url} after {DEFAULT_RETRIES} attempts: {last_exc!r}"
    ) from last_exc
