import logging
import time

logger = logging.getLogger("core.requests")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()

        try:
            response = self.get_response(request)
        except Exception:
            logger.exception(
                "Unhandled exception method=%s path=%s result=ERROR",
                request.method,
                request.path,
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code

        if status_code >= 500:
            log_method = logger.error
            result = "ERROR"
        elif status_code >= 400:
            log_method = logger.warning
            result = "FAIL"
        else:
            log_method = logger.info
            result = "OK"

        log_method(
            "HTTP method=%s path=%s status=%s result=%s duration_ms=%.2f",
            request.method,
            request.path,
            status_code,
            result,
            duration_ms,
        )

        return response
