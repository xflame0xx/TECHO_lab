import time

from django.http import HttpResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS_TOTAL = Counter(  # количество HTTP-запросов
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status"],
)

HTTP_ERRORS_TOTAL = Counter(  # количество ошибок 4xx и 5xx
    "http_errors_total",
    "Total number of HTTP 4xx and 5xx errors",
    ["method", "path", "status"],
)

HTTP_RESPONSE_TIME_SECONDS = Histogram(  # время ответа backend
    "http_response_time_seconds",
    "HTTP response time in seconds",
    ["method", "path"],
)

AUTH_ATTEMPTS_TOTAL = Counter(  # количество успешных и неуспешных авторизаций
    "auth_attempts_total",
    "Total authentication attempts",
    ["result"],
)


class PrometheusMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()

        response = self.get_response(request)

        duration = time.perf_counter() - start_time

        if request.resolver_match:
            path = request.resolver_match.route
        else:
            path = request.path

        method = request.method
        status_code = str(response.status_code)

        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            path=path,
            status=status_code,
        ).inc()

        HTTP_RESPONSE_TIME_SECONDS.labels(
            method=method,
            path=path,
        ).observe(duration)

        if response.status_code >= 400:
            HTTP_ERRORS_TOTAL.labels(
                method=method,
                path=path,
                status=status_code,
            ).inc()

        return response


def metrics_view(request):
    return HttpResponse(
        generate_latest(),
        content_type=CONTENT_TYPE_LATEST,
    )
