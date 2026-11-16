"""ASGI application: REST API under /api, web UI at /, transmitter server and scheduler
running on the same event loop."""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import FileResponse, Response
from starlette.routing import Mount, Route, Router
from starlette.staticfiles import StaticFiles

from . import config
from .api import Api, ApiError, _err, error_response
from .core import VERSION, Core
from .scheduler import Scheduler

log = logging.getLogger("dapnet")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "origin, content-type, accept, authorization",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD",
}


class ApiMiddleware:
    """CORS headers, OPTIONS pre-flight and DAPNET-style error bodies for /api."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        if scope["method"] == "OPTIONS":
            return await Response(status_code=200, headers=CORS_HEADERS)(scope, receive, send)

        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers += [(k.lower().encode(), v.encode()) for k, v in CORS_HEADERS.items()]
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_cors)
        except ApiError as e:
            await error_response(e)(scope, receive, send_with_cors)
        except HTTPException as e:
            code = {404: 4040, 405: 4050}.get(e.status_code)
            err = ApiError(4050, "Method not allowed", "The resource does not support the request method") \
                if code == 4050 else _err(4040)
            await error_response(err)(scope, receive, send_with_cors)
        except Exception:
            log.exception("Unhandled API error on %s %s", scope["method"], scope["path"])
            await error_response(ApiError(5001, "Internal Server Error",
                                          "A unknown server-side error occurred while executing the request"))(
                scope, receive, send_with_cors)


def _spa(web_dir: Path):
    index = web_dir / "index.html"

    async def handler(request: Request) -> Response:
        path = request.path_params.get("path", "")
        candidate = (web_dir / path).resolve()
        if path and candidate.is_file() and web_dir.resolve() in candidate.parents:
            return FileResponse(candidate)
        if index.is_file():
            return FileResponse(index, headers={"Cache-Control": "no-cache"})
        return Response("Web UI not built", status_code=404, media_type="text/plain")

    return handler


def create_app(settings: config.Settings | None = None) -> Starlette:
    settings = settings or config.load()
    core = Core(settings)
    api = Api(core)
    scheduler = Scheduler()

    @contextlib.asynccontextmanager
    async def lifespan(app):
        core.load()
        await core.tx.start(settings.tx_host, settings.tx_port)
        cron = settings.cron
        scheduler.add("time", cron["time"], core.send_time)
        scheduler.add("localTime", cron["localTime"], core.send_local_time)
        scheduler.add("rubricNames", cron["rubricNames"], core.send_all_rubrics)
        scheduler.add("news", cron["news"], core.resend_all_news)
        scheduler.add("identification", cron["identification"], core.tx.send_identification)
        scheduler.add("stateSaving", cron["stateSaving"], core.save)
        scheduler.add("stateCleaning", cron["stateCleaning"], core.clean_expired)
        scheduler.start()
        log.info("DAPNET lite %s started as node %s (HTTP %d, transmitters %d)",
                 VERSION, settings.node_name, settings.rest_port, settings.tx_port)
        try:
            yield
        finally:
            await scheduler.stop()
            await core.tx.stop()
            core.save()
            log.info("Stopped, state saved")

    api_router = Router(routes=api.routes())
    routes = [Mount("/api", app=ApiMiddleware(api_router))]
    web_dir = Path(settings.web_dir) if settings.web_dir else None
    if web_dir and web_dir.is_dir():
        if (web_dir / "assets").is_dir():
            routes.append(Mount("/assets", app=StaticFiles(directory=web_dir / "assets")))
        routes.append(Route("/{path:path}", _spa(web_dir), methods=["GET", "HEAD"]))
    app = Starlette(routes=routes, lifespan=lifespan)
    app.state.core = core
    return app
