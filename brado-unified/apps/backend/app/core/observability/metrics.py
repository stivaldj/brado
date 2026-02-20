from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock

_BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)


@dataclass
class MetricsRegistry:
    request_total: dict[tuple[str, str, str], int] = field(default_factory=lambda: defaultdict(int))
    request_errors_total: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))
    request_latency_bucket: dict[tuple[str, str, float], int] = field(default_factory=lambda: defaultdict(int))
    request_latency_count: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))
    request_latency_sum: dict[tuple[str, str], float] = field(default_factory=lambda: defaultdict(float))
    lock: Lock = field(default_factory=Lock)

    def observe_request(self, *, method: str, route: str, status: int, latency_seconds: float) -> None:
        status_class = f"{status // 100}xx"
        key = (method, route)
        with self.lock:
            self.request_total[(method, route, status_class)] += 1
            if status >= 500:
                self.request_errors_total[(method, route)] += 1

            self.request_latency_count[key] += 1
            self.request_latency_sum[key] += latency_seconds

            for bucket in _BUCKETS:
                if latency_seconds <= bucket:
                    self.request_latency_bucket[(method, route, bucket)] += 1
            self.request_latency_bucket[(method, route, float("inf"))] += 1

    def render_prometheus_text(self) -> str:
        with self.lock:
            lines = [
                "# HELP brado_http_requests_total Total HTTP requests",
                "# TYPE brado_http_requests_total counter",
            ]
            for (method, route, status_class), value in sorted(self.request_total.items()):
                lines.append(
                    f'brado_http_requests_total{{method="{method}",route="{route}",status_class="{status_class}"}} {value}'
                )

            lines.extend(
                [
                    "# HELP brado_http_request_errors_total Total HTTP 5xx responses",
                    "# TYPE brado_http_request_errors_total counter",
                ]
            )
            for (method, route), value in sorted(self.request_errors_total.items()):
                lines.append(f'brado_http_request_errors_total{{method="{method}",route="{route}"}} {value}')

            lines.extend(
                [
                    "# HELP brado_http_request_latency_seconds HTTP request latency",
                    "# TYPE brado_http_request_latency_seconds histogram",
                ]
            )
            for method, route in sorted(self.request_latency_count.keys()):
                cumulative = 0
                for bucket in _BUCKETS:
                    cumulative += self.request_latency_bucket[(method, route, bucket)]
                    lines.append(
                        f'brado_http_request_latency_seconds_bucket{{method="{method}",route="{route}",le="{bucket}"}} {cumulative}'
                    )
                lines.append(
                    f'brado_http_request_latency_seconds_bucket{{method="{method}",route="{route}",le="+Inf"}} '
                    f'{self.request_latency_bucket[(method, route, float("inf"))]}'
                )
                lines.append(
                    f'brado_http_request_latency_seconds_sum{{method="{method}",route="{route}"}} '
                    f'{self.request_latency_sum[(method, route)]}'
                )
                lines.append(
                    f'brado_http_request_latency_seconds_count{{method="{method}",route="{route}"}} '
                    f'{self.request_latency_count[(method, route)]}'
                )

        return "\n".join(lines) + "\n"


metrics_registry = MetricsRegistry()
