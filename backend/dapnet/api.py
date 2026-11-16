"""REST API, compatible with the DAPNET Core v1 API (paths, JSON fields, Basic auth,
role rules and error format). Mounted under /api."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from . import auth, models
from .auth import Level, Status
from .core import VERSION, Core
from .store import now_iso

log = logging.getLogger(__name__)

AUTHKEY_RE = re.compile(r"[A-Za-z0-9]+")

# collection -> (model kind, level for GET)
RESOURCES = {
    "callsigns": ("callSigns", "callsign", Level.USER_ONLY),
    "transmitters": ("transmitters", "transmitter", Level.EVERYBODY),
    "transmitterGroups": ("transmitterGroups", "transmitterGroup", Level.USER_ONLY),
    "rubrics": ("rubrics", "rubric", Level.USER_ONLY),
    "users": ("users", "user", Level.USER_ONLY),
    "nodes": ("nodes", "node", Level.USER_ONLY),
}


class ApiError(Exception):
    def __init__(self, code: int, name: str, message: str, violations: list | None = None):
        self.code, self.name, self.message, self.violations = code, name, message, violations


def _err(code: int) -> ApiError:
    return {
        4000: ApiError(4000, "Bad Request", "Malformed request syntax or invalid message framing"),
        4002: ApiError(4002, "Empty Body", "Request body does not contain any data"),
        4010: ApiError(4010, "Not Authorized", "Invalid or missing username or password"),
        4030: ApiError(4030, "Forbidden", "No permission for this request"),
        4040: ApiError(4040, "Not Found", "The requested resource could not be found"),
        4060: ApiError(4060, "Not Acceptable", "Requested response is not available in the requested form"),
        5000: ApiError(5000, "Internal Server Error", "A server-side error occurred while executing the request"),
    }[code]


def pretty(data: Any, status: int = 200, headers: dict | None = None) -> Response:
    body = json.dumps(data, indent=2, ensure_ascii=False)
    return Response(body, status_code=status, media_type="application/json", headers=headers)


def error_response(e: ApiError) -> Response:
    data: dict[str, Any] = {"code": e.code, "name": e.name, "message": e.message}
    if e.violations is not None:
        data["violations"] = e.violations
    return pretty(data, e.code // 10)


class Api:
    def __init__(self, core: Core):
        self.core = core
        self.store = core.store

    # --- auth ------------------------------------------------------------------------
    def identify(self, request: Request) -> tuple[Status, dict | None]:
        creds = auth.parse_basic(request.headers.get("authorization"))
        if creds is None:
            return Status.ANYBODY, None
        user = self.store.users.get(creds[0].lower())
        if user is None or not auth.verify(creds[1], user.get("hash", "")):
            raise _err(4010)
        if auth.is_legacy(user["hash"]):
            user["hash"] = auth.create_hash(creds[1])
            self.core.changed()
            log.info("Upgraded password hash for %s", user["name"])
        return (Status.ADMIN if user.get("admin") else Status.USER), user

    def authorize(self, request: Request, level: Level, owners: list[str] | None = None) -> tuple[Status, dict | None]:
        status, user = self.identify(request)
        if status is Status.USER and owners and user["name"].lower() in [o.lower() for o in owners]:
            status = Status.OWNER
        if not auth.allowed(status, level):
            raise _err(4030)
        return status, user

    @staticmethod
    def owners_of(kind: str, obj: dict | None) -> list[str] | None:
        if obj is None:
            return None
        if kind == "user":
            return [obj["name"]]
        return obj.get("ownerNames") or []

    async def body(self, request: Request) -> dict:
        raw = await request.body()
        if not raw.strip():
            raise _err(4002)
        try:
            data = json.loads(raw)
        except ValueError as e:
            raise ApiError(4003, "Invalid Json", str(e)) from e
        if not isinstance(data, dict):
            raise ApiError(4003, "Invalid Json", "expected a JSON object")
        # the original web UI trims strings before sending; do it server side as well
        return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}

    def validate(self, kind: str, data: dict) -> dict:
        try:
            return models.validate(kind, data, self.store.exists)
        except models.ValidationError as e:
            raise ApiError(4001, "Constraint Violation", "Missing fields or invalid values", e.violations) from e

    # --- core / stats ----------------------------------------------------------------
    async def version(self, request: Request) -> Response:
        self.authorize(request, Level.EVERYBODY)
        which = request.path_params.get("which")
        if which in ("core_version", "api_version"):
            return pretty({"version": VERSION})
        return pretty({"core": VERSION, "api": VERSION})

    async def stats(self, request: Request) -> Response:
        self.authorize(request, Level.EVERYBODY)
        return pretty(self.core.stats())

    # --- calls -----------------------------------------------------------------------
    async def get_calls(self, request: Request) -> Response:
        self.authorize(request, Level.USER_ONLY)
        owner = (request.query_params.get("ownerName") or "").lower()
        calls = [c for c in self.store.calls if not owner or c.get("ownerName", "").lower() == owner]
        return pretty([models.view("call", c, True) for c in calls])

    async def post_call(self, request: Request) -> Response:
        _, user = self.authorize(request, Level.USER_ONLY)
        data = await self.body(request)
        data["ownerName"] = user["name"]
        call = self.validate("call", data)
        call["timestamp"] = now_iso()
        self.core.post_call(call)
        return pretty(models.view("call", call, True), 201, {"Location": str(request.url)})

    async def post_activation(self, request: Request) -> Response:
        self.authorize(request, Level.USER_ONLY)
        act = self.validate("activation", await self.body(request))
        act["timestamp"] = now_iso()
        if not self.core.post_activation(act):
            raise _err(5000)
        return pretty(models.view("activation", act, True))

    # --- news ------------------------------------------------------------------------
    def _news_list(self, slots: list) -> list:
        return [models.view("news", n, True) if n else None for n in slots]

    async def get_news(self, request: Request) -> Response:
        rubric_name = (request.query_params.get("rubricName") or "").lower()
        if not rubric_name:
            self.authorize(request, Level.USER_ONLY)
            return pretty({k: self._news_list(v) for k, v in self.store.news.items()})
        rubric = self.store.rubrics.get(rubric_name)
        self.authorize(request, Level.USER_ONLY, self.owners_of("rubric", rubric))
        slots = self.store.news.get(rubric_name)
        if slots is None:
            raise _err(4040)
        return pretty(self._news_list(slots))

    async def post_news(self, request: Request) -> Response:
        _, user = self.authorize(request, Level.USER_ONLY)
        data = await self.body(request)
        data["ownerName"] = user["name"]
        rubric = self.store.rubrics.get(str(data.get("rubricName") or "").lower())
        self.authorize(request, Level.OWNER_ONLY, self.owners_of("rubric", rubric))
        news = self.validate("news", data)
        news["timestamp"] = now_iso()
        self.core.post_news(news)
        return pretty(models.view("news", news, True), 201, {"Location": str(request.url)})

    # --- generic resources -----------------------------------------------------------
    def _resource(self, request: Request) -> tuple[str, str, Level]:
        res = RESOURCES.get(request.path_params["resource"])
        if res is None:
            raise _err(4040)
        return res

    async def list_objects(self, request: Request) -> Response:
        coll, kind, level = self._resource(request)
        status, _ = self.authorize(request, level)
        objs = sorted(self.store.collection(coll).values(), key=lambda o: o["name"].lower())
        return pretty([models.view(kind, o, status.privileged) for o in objs])

    async def get_object(self, request: Request) -> Response:
        coll, kind, level = self._resource(request)
        obj = self.store.collection(coll).get(request.path_params["name"].lower())
        status, _ = self.authorize(request, level, self.owners_of(kind, obj))
        if obj is None:
            raise _err(4040)
        return pretty(models.view(kind, obj, status.privileged))

    async def put_object(self, request: Request) -> Response:
        coll, kind, _ = self._resource(request)
        name = request.path_params["name"].lower()
        old = self.store.collection(coll).get(name)

        if kind == "user":
            self.authorize(request, Level.USER_ONLY)
            data = await self.body(request)
            data["name"] = name
            password = data.get("hash")
            if not password:
                if old is None:
                    raise ApiError(4001, "Constraint Violation", "Missing fields or invalid values",
                                   [{"code": 6001, "constraint": "NotNull", "field": "hash", "value": None,
                                     "message": "may not be null"}])
                data["hash"] = old["hash"]
            if data.get("admin") or old is None:
                self.authorize(request, Level.ADMIN_ONLY)
            else:
                self.authorize(request, Level.OWNER_ONLY, self.owners_of(kind, old))
            obj = self.validate(kind, data)
            if password:
                obj["hash"] = auth.create_hash(str(password))
        else:
            if kind == "node" or old is None:
                self.authorize(request, Level.ADMIN_ONLY)
            else:
                self.authorize(request, Level.OWNER_ONLY, self.owners_of(kind, old))
            data = await self.body(request)
            data["name"] = name
            obj = self.validate(kind, data)

        if kind == "transmitter":
            if not AUTHKEY_RE.fullmatch(obj["authKey"]):
                raise ApiError(4060, "Not Acceptable", "Auth key contains invalid characters.")
            if obj["status"] != "DISABLED":
                obj["status"] = "OFFLINE"
            obj["lastUpdate"] = now_iso()
            for keep in ("callCount", "lastConnected", "deviceType", "deviceVersion", "address", "nodeName"):
                obj[keep] = (old or {}).get(keep)
            obj["connectedSince"] = None
            self.core.tx.disconnect(name)  # reconnect with the new key / time slots
        elif kind == "node":
            for keep in ("address", "version"):
                obj[keep] = (old or {}).get(keep)

        self.core.put(coll, obj)
        view = models.view(kind, obj, True)
        if old is None:
            return pretty(view, 201, {"Location": str(request.url)})
        return pretty(view)

    async def delete_object(self, request: Request) -> Response:
        coll, kind, _ = self._resource(request)
        name = request.path_params["name"].lower()
        old = self.store.collection(coll).get(name)
        if old is None or kind == "node":
            self.authorize(request, Level.ADMIN_ONLY)
        else:
            self.authorize(request, Level.OWNER_ONLY, self.owners_of(kind, old))
        if old is None:
            raise _err(4040)
        if kind == "node" and name == self.core.settings.node_name.lower():
            raise ApiError(4000, "Bad Request", "The local node cannot be deleted")
        self.core.delete(coll, name)
        return pretty(models.view(kind, old, True))

    async def send_rubric_names(self, request: Request) -> Response:
        name = request.path_params["name"].lower()
        t = self.store.transmitters.get(name)
        if t is None:
            raise _err(4002)
        self.authorize(request, Level.OWNER_ONLY, t.get("ownerNames"))
        for r in list(self.store.rubrics.values()):
            self.core.send_rubric(r, only=name)
        return Response(status_code=200)

    def routes(self) -> list[Route]:
        return [
            Route("/core/{which}", self.version, methods=["GET"]),
            Route("/stats", self.stats, methods=["GET"]),
            Route("/calls", self.get_calls, methods=["GET"]),
            Route("/calls", self.post_call, methods=["POST"]),
            Route("/activation", self.post_activation, methods=["POST"]),
            Route("/activation/", self.post_activation, methods=["POST"]),
            Route("/news", self.get_news, methods=["GET"]),
            Route("/news", self.post_news, methods=["POST"]),
            Route("/news/", self.post_news, methods=["POST"]),
            Route("/transmitterControl/sendRubricNames/{name}", self.send_rubric_names, methods=["GET"]),
            Route("/{resource}", self.list_objects, methods=["GET"]),
            Route("/{resource}/{name}", self.get_object, methods=["GET"]),
            Route("/{resource}/{name}", self.put_object, methods=["PUT"]),
            Route("/{resource}/{name}", self.delete_object, methods=["DELETE"]),
        ]
