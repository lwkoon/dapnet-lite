"""Password hashing and role resolution.

Reads the DAPNET Core hash format (`1000:<salt hex>:<hash hex>`, PBKDF2-HMAC-SHA1) so
existing accounts keep working. New and changed passwords use PBKDF2-HMAC-SHA256
(`pbkdf2_sha256$<iterations>$<salt hex>$<hash hex>`); legacy hashes are upgraded on the
next successful login.
"""

from __future__ import annotations

import base64
import enum
import hashlib
import hmac
import os
import time

ITERATIONS = 310_000
_CACHE_TTL = 300.0
_cache: dict[bytes, float] = {}


class Level(enum.IntEnum):
    EVERYBODY = 0
    USER_ONLY = 1
    OWNER_ONLY = 2
    ADMIN_ONLY = 3


class Status(enum.Enum):
    ANYBODY = "anybody"
    USER = "user"
    OWNER = "owner"
    ADMIN = "admin"

    @property
    def privileged(self) -> bool:
        return self in (Status.ADMIN, Status.OWNER)


_RANK = {Status.ANYBODY: Level.EVERYBODY, Status.USER: Level.USER_ONLY,
         Status.OWNER: Level.OWNER_ONLY, Status.ADMIN: Level.ADMIN_ONLY}


def allowed(status: Status, level: Level) -> bool:
    return _RANK[status] >= level


def create_hash(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${dk.hex()}"


def is_legacy(stored: str) -> bool:
    return not stored.startswith("pbkdf2_sha256$")


def verify(password: str, stored: str) -> bool:
    if not stored:
        return False
    key = hashlib.sha256(f"{stored}\0{password}".encode("utf-8")).digest()
    now = time.monotonic()
    exp = _cache.get(key)
    if exp and exp > now:
        return True
    try:
        if stored.startswith("pbkdf2_sha256$"):
            _, iters, salt, want = stored.split("$")
            got = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iters))
        else:
            iters, salt, want = stored.split(":")
            want_b = bytes.fromhex(want)
            # Java PBEKeySpec uses the UTF-16 chars; for PBKDF2 the JDK encodes them as UTF-8
            got = hashlib.pbkdf2_hmac("sha1", password.encode("utf-8"), bytes.fromhex(salt), int(iters), len(want_b))
        ok = hmac.compare_digest(got, bytes.fromhex(want))
    except (ValueError, TypeError):
        return False
    if ok:
        if len(_cache) > 1000:
            _cache.clear()
        _cache[key] = now + _CACHE_TTL
    return ok


def parse_basic(header: str | None) -> tuple[str, str] | None:
    if not header or not header.startswith("Basic "):
        return None
    try:
        raw = base64.b64decode(header[6:].strip(), validate=False).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
    if ":" not in raw:
        return None
    user, pw = raw.split(":", 1)
    return user, pw
