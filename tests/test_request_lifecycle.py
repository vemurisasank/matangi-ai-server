import asyncio

from fastapi import FastAPI, File, UploadFile
from httpx import ASGITransport, AsyncClient

from middleware.request_lifecycle import RequestLifecycleMiddleware


def _run(coro):
    return asyncio.run(coro)


def _messages(logs, event):
    return [
        message if isinstance(message, str) else message[1]
        for message in logs
        if (message if isinstance(message, str) else message[1]).startswith(event)
    ]


def test_request_lifecycle_logs_arrival_body_and_response(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "middleware.request_lifecycle.Logger.info",
        lambda message: logs.append(("info", message)),
    )
    monkeypatch.setattr(
        "middleware.request_lifecycle.Logger.error",
        lambda message: logs.append(("error", message)),
    )

    async def app(scope, receive, send):
        await receive()
        await send({
            "type": "http.response.start",
            "status": 201,
            "headers": [],
        })
        await send({
            "type": "http.response.body",
            "body": b"ok",
            "more_body": False,
        })

    async def run():
        sent = []

        async def receive():
            return {
                "type": "http.request",
                "body": b"payload",
                "more_body": False,
            }

        async def send(message):
            sent.append(message)

        await RequestLifecycleMiddleware(app)(
            {
                "type": "http",
                "method": "POST",
                "path": "/upload",
                "headers": [(b"content-length", b"7")],
            },
            receive,
            send,
        )
        return sent

    sent = _run(run())

    arrival = _messages(logs, "http.request.arrived")
    body_complete = _messages(logs, "http.request.body_complete")
    started = _messages(logs, "http.response.started")
    completed = _messages(logs, "http.response.completed")

    assert sent[-1]["body"] == b"ok"
    assert len(arrival) == len(body_complete) == len(started) == len(completed) == 1
    request_id = arrival[0].split("request_id=")[1].split(" ", 1)[0]
    assert f"request_id={request_id}" in body_complete[0]
    assert f"request_id={request_id}" in started[0]
    assert f"request_id={request_id}" in completed[0]
    assert "status_code=201" in started[0]
    assert "status_code=201" in completed[0]


def test_body_completion_is_logged_only_after_final_body_event(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "middleware.request_lifecycle.Logger.info",
        lambda message: logs.append(message),
    )

    received = []

    async def app(scope, receive, send):
        received.append(await receive())
        assert not any(
            message.startswith("http.request.body_complete")
            for message in logs
        )
        received.append(await receive())
        assert any(
            message.startswith("http.request.body_complete")
            for message in logs
        )
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def run():
        messages = iter([
            {
                "type": "http.request",
                "body": b"first",
                "more_body": True,
            },
            {
                "type": "http.request",
                "body": b"second",
                "more_body": False,
            },
        ])

        async def receive():
            return next(messages)

        async def send(message):
            pass

        await RequestLifecycleMiddleware(app)(
            {"type": "http", "method": "POST", "path": "/", "headers": []},
            receive,
            send,
        )

    _run(run())

    assert len([
        message for message in logs
        if message.startswith("http.request.body_complete")
    ]) == 1
    assert received[0]["body"] + received[1]["body"] == b"firstsecond"


def test_request_body_passes_through_and_multipart_parsing_works(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "middleware.request_lifecycle.Logger.info",
        lambda message: logs.append(message),
    )

    app = FastAPI()

    @app.post("/upload")
    async def upload(file: UploadFile = File(...)):
        return {"filename": file.filename, "content": (await file.read()).decode()}

    wrapped_app = RequestLifecycleMiddleware(app)

    async def run():
        async with AsyncClient(
            transport=ASGITransport(app=wrapped_app),
            base_url="http://test",
        ) as client:
            return await client.post(
                "/upload",
                files={"file": ("reference.png", b"image-data", "image/png")},
            )

    response = _run(run())

    assert response.status_code == 200
    assert response.json() == {
        "filename": "reference.png",
        "content": "image-data",
    }
    assert _messages(logs, "http.request.body_complete")
    assert _messages(logs, "http.response.completed")


def test_middleware_logs_exception_and_reraises(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "middleware.request_lifecycle.Logger.error",
        lambda message: logs.append(message),
    )

    async def app(scope, receive, send):
        raise RuntimeError("controlled failure")

    async def run():
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            pass

        await RequestLifecycleMiddleware(app)(
            {"type": "http", "method": "GET", "path": "/", "headers": []},
            receive,
            send,
        )

    try:
        _run(run())
    except RuntimeError as error:
        assert str(error) == "controlled failure"
    else:
        raise AssertionError("middleware swallowed the application exception")

    failures = _messages(logs, "http.request.failed")
    assert len(failures) == 1
    assert "exception_type='RuntimeError'" in failures[0]
    assert "controlled failure" in failures[0]


def test_logging_failure_does_not_break_request(monkeypatch):
    monkeypatch.setattr(
        "middleware.request_lifecycle.Logger.info",
        lambda message: (_ for _ in ()).throw(RuntimeError("logging failed")),
    )

    async def app(scope, receive, send):
        await receive()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    async def run():
        sent = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            sent.append(message)

        await RequestLifecycleMiddleware(app)(
            {"type": "http", "method": "GET", "path": "/", "headers": []},
            receive,
            send,
        )
        return sent

    assert _run(run())[-1]["body"] == b"ok"
