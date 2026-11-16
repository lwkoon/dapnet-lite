import hashlib
from datetime import datetime

from dapnet import auth
from dapnet.scheduler import Cron


def test_cron_defaults():
    t = datetime(2026, 11, 16, 7, 8, 9)
    assert Cron("0 0/20 * * * ?").next_after(t) == datetime(2026, 11, 16, 7, 20, 0)
    assert Cron("0 10/20 * * * ?").next_after(t) == datetime(2026, 11, 16, 7, 10, 0)
    assert Cron("15 0/20 * * * ?").next_after(t) == datetime(2026, 11, 16, 7, 20, 15)
    assert Cron("45 0 * * * ?").next_after(t) == datetime(2026, 11, 16, 8, 0, 45)
    assert Cron("0 0 0 * * ?").next_after(t) == datetime(2026, 11, 17, 0, 0, 0)
    assert Cron("0 0/10 * * * ?").next_after(datetime(2026, 11, 16, 7, 50, 0)) == datetime(2026, 11, 16, 8, 0, 0)


def test_cron_dow_and_lists():
    # 2026-11-16 is a Monday; Quartz MON = 2
    t = datetime(2026, 11, 16, 12, 0, 0)
    assert Cron("0 0 9 ? * MON").next_after(t) == datetime(2026, 11, 23, 9, 0, 0)
    assert Cron("0 0 9 ? * 1").next_after(t) == datetime(2026, 11, 22, 9, 0, 0)  # Sunday
    assert Cron("0 5,35 * * * ?").next_after(t) == datetime(2026, 11, 16, 12, 5, 0)


def test_legacy_hash_from_java_core():
    # same construction as HashUtil.createHash: PBKDF2WithHmacSHA1, 1000 iterations, 24-byte salt/hash
    salt = bytes(range(24))
    dk = hashlib.pbkdf2_hmac("sha1", b"secret123", salt, 1000, 24)
    stored = f"1000:{salt.hex()}:{dk.hex()}"
    assert len(stored) == 102  # matches the @Size(102) constraint on User.hash
    assert auth.verify("secret123", stored)
    assert not auth.verify("wrong", stored)
    assert auth.is_legacy(stored)


def test_new_hash():
    h = auth.create_hash("p@ss wörd")
    assert not auth.is_legacy(h)
    assert auth.verify("p@ss wörd", h)
    assert not auth.verify("p@ss word", h)


def test_basic_header():
    assert auth.parse_basic("Basic YWRtaW46YTpi") == ("admin", "a:b")
    assert auth.parse_basic("Bearer x") is None
    assert auth.parse_basic(None) is None
