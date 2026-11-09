from datetime import datetime, timezone
import time
import uuid

from core.logger import Logger


class RequestLifecycleMiddleware:
    def __init__(self, app):
        self.app = app

    @staticmethod
    def _safe_message(error):
        message = str(error).replace("\r", " ").replace("\n", " ")
        return message[:500]

    @staticmethod
    def _log(level, message):
        try:
            getattr(Logger, level)(message)
        except Exception:
            pass

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex
        started_at = time.monotonic()
        response_status = None
        response_started = False
        response_completed = False
        body_complete = False
        request_failed = False

        headers = {
            key.lower(): value
            for key, value in scope.get("headers", [])
        }
        content_length = headers.get(b"content-length")
        content_length = (
            content_length.decode("latin-1")
            if content_length is not None
            else None
        )
        path = scope.get("path", "")

        self._log(
            "info",
            "http.request.arrived "
            f"request_id={request_id!r} "
            f"method={scope.get('method', '')!r} "
            f"path={path!r} "
            f"content_length={content_length!r} "
            f"timestamp={datetime.now(timezone.utc).isoformat()}",
        )

        def log_failure(error):
            nonlocal request_failed
            if request_failed:
                return
            request_failed = True
            self._log(
                "error",
                "http.request.failed "
                f"request_id={request_id!r} "
                f"exception_type={type(error).__name__!r} "
                f"message={self._safe_message(error)!r}",
            )

        async def receive_wrapper():
            nonlocal body_complete
            try:
                message = await receive()
            except Exception as error:
                log_failure(error)
                raise

            if (
                message.get("type") == "http.request"
                and not message.get("more_body", False)
                and not body_complete
            ):
                body_complete = True
                self._log(
                    "info",
                    "http.request.body_complete "
                    f"request_id={request_id!r} "
                    f"elapsed_seconds={time.monotonic() - started_at:.3f}",
                )
            return message

        async def send_wrapper(message):
            nonlocal response_status, response_started, response_completed
            if message.get("type") == "http.response.start":
                response_status = message.get("status")
                if not response_started:
                    response_started = True
                    self._log(
                        "info",
                        "http.response.started "
                        f"request_id={request_id!r} "
                        f"status_code={response_status} "
                        f"elapsed_seconds={time.monotonic() - started_at:.3f}",
                    )

            try:
                await send(message)
            except Exception as error:
                log_failure(error)
                raise

            if (
                message.get("type") == "http.response.body"
                and not message.get("more_body", False)
                and not response_completed
            ):
                response_completed = True
                self._log(
                    "info",
                    "http.response.completed "
                    f"request_id={request_id!r} "
                    f"status_code={response_status} "
                    f"duration_seconds={time.monotonic() - started_at:.3f}",
                )

        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        except Exception as error:
            log_failure(error)
            raise
