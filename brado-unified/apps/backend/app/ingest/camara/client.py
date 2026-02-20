from __future__ import annotations

import hashlib
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from threading import Lock
from typing import Any, Iterator, Sequence
from urllib.parse import urlencode

import httpx

from ...core.config import get_settings


class VCRStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.mode = settings.vcr_mode
        self.base = Path(settings.vcr_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _key(self, method: str, url: str, params: dict[str, Any] | None) -> str:
        payload = json.dumps({"method": method, "url": url, "params": params or {}}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def maybe_load(self, method: str, url: str, params: dict[str, Any] | None) -> dict[str, Any] | None:
        if self.mode != "replay":
            return None
        path = self.base / f"{self._key(method, url, params)}.json"
        if not path.exists():
            raise FileNotFoundError(f"VCR replay miss: {path.name}")
        return json.loads(path.read_text())

    def maybe_save(self, method: str, url: str, params: dict[str, Any] | None, data: dict[str, Any]) -> None:
        if self.mode != "record":
            return
        path = self.base / f"{self._key(method, url, params)}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


class CamaraClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.camara_base_url.rstrip("/")
        self.timeout = settings.camara_timeout_seconds
        self.max_rps = settings.camara_max_rps
        self.max_concurrency = max(1, settings.camara_max_concurrency)
        self.max_retries = settings.camara_max_retries
        self._last_req_at = 0.0
        self._throttle_lock = Lock()
        self._vcr = VCRStore()
        self._vcr_lock = Lock()

        self.client = httpx.Client(
            timeout=self.timeout,
            headers={
                "User-Agent": settings.camara_user_agent,
                "Accept": "application/json",
            },
        )

    def _throttle(self) -> None:
        with self._throttle_lock:
            min_interval = 1.0 / max(self.max_rps, 0.1)
            now = time.time()
            wait = min_interval - (now - self._last_req_at)
            if wait > 0:
                time.sleep(wait)
            self._last_req_at = time.time()

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        *,
        raise_for_status: bool = True,
    ) -> tuple[int, dict[str, Any]]:
        endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        url = f"{self.base_url}{endpoint}"

        with self._vcr_lock:
            replay = self._vcr.maybe_load("GET", url, params)
        if replay is not None:
            return replay["status"], replay["body"]

        for attempt in range(self.max_retries + 1):
            try:
                self._throttle()
                response = self.client.get(url, params=params)
                body = response.json() if response.content else {}
                if raise_for_status:
                    response.raise_for_status()
                with self._vcr_lock:
                    self._vcr.maybe_save("GET", url, params, {"status": response.status_code, "body": body})
                return response.status_code, body
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response is not None else 0
                if (not raise_for_status) or (status and status < 500 and status != 429):
                    try:
                        body = exc.response.json() if exc.response is not None and exc.response.content else {}
                    except Exception:
                        body = {}
                    return status, body
                if attempt >= self.max_retries:
                    raise
                backoff = min(8.0, (2**attempt) + random.uniform(0, 0.3))
                time.sleep(backoff)
            except (httpx.HTTPError, ValueError):
                if attempt >= self.max_retries:
                    raise
                backoff = min(8.0, (2**attempt) + random.uniform(0, 0.3))
                time.sleep(backoff)

        raise RuntimeError("unreachable")

    def paginated(self, endpoint: str, params: dict[str, Any] | None = None, max_pages: int | None = None) -> Iterator[tuple[int, dict[str, Any], dict[str, Any]]]:
        current_params = dict(params or {})
        page = int(current_params.get("pagina", 1))
        yielded = 0

        while True:
            current_params["pagina"] = page
            status, body = self.get(endpoint, current_params)
            yield status, body, dict(current_params)
            yielded += 1

            links = body.get("links", []) if isinstance(body, dict) else []
            has_next = any(link.get("rel") == "next" for link in links)
            if max_pages and yielded >= max_pages:
                break
            if not has_next:
                break
            page += 1

    def fetch_many(
        self,
        requests: Sequence[tuple[str, dict[str, Any] | None]],
        *,
        max_workers: int | None = None,
        raise_for_status: bool = True,
    ) -> list[tuple[int, dict[str, Any]]]:
        if not requests:
            return []

        workers = max(1, min(max_workers or self.max_concurrency, self.max_concurrency, len(requests)))
        if workers == 1:
            return [self.get(endpoint, params, raise_for_status=raise_for_status) for endpoint, params in requests]

        per_request_timeout = max(5.0, float(self.timeout) * 2.0)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(self.get, endpoint, params, raise_for_status=raise_for_status)
                for endpoint, params in requests
            ]
            results: list[tuple[int, dict[str, Any]]] = []
            for future in futures:
                try:
                    results.append(future.result(timeout=per_request_timeout))
                except FutureTimeoutError as exc:
                    for pending in futures:
                        pending.cancel()
                    raise TimeoutError(f"fetch_many timeout after {per_request_timeout:.1f}s") from exc
            return results

    def get_text(self, url: str, *, raise_for_status: bool = True) -> tuple[int, str]:
        with self._vcr_lock:
            replay = self._vcr.maybe_load("GET", url, None)
        if replay is not None and "text" in replay:
            return int(replay["status"]), str(replay["text"])

        for attempt in range(self.max_retries + 1):
            try:
                self._throttle()
                response = self.client.get(url)
                text = response.text
                if raise_for_status:
                    response.raise_for_status()
                with self._vcr_lock:
                    self._vcr.maybe_save("GET", url, None, {"status": response.status_code, "text": text})
                return response.status_code, text
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response is not None else 0
                if (not raise_for_status) or (status and status < 500 and status != 429):
                    return status, exc.response.text if exc.response is not None else ""
                if attempt >= self.max_retries:
                    raise
                backoff = min(8.0, (2**attempt) + random.uniform(0, 0.3))
                time.sleep(backoff)
            except httpx.HTTPError:
                if attempt >= self.max_retries:
                    raise
                backoff = min(8.0, (2**attempt) + random.uniform(0, 0.3))
                time.sleep(backoff)

        raise RuntimeError("unreachable")

    def close(self) -> None:
        self.client.close()
