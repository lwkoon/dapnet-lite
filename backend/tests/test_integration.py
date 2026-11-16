"""End to end: REST API + a fake transmitter speaking the DAPNET TX protocol."""

import asyncio
import base64
import json

import httpx
import pytest

from dapnet import config
from dapnet.app import create_app

ADMIN = "Basic " + base64.b64encode(b"admin:adminpass").decode()


def basic(user, pw):
    return "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()


@pytest.fixture
async def env(tmp_path, unused_tcp_port):
    s = config.Settings()
    s.state_file = str(tmp_path / "State.json")
    s.admin_password = "adminpass"
    s.tx_host = "127.0.0.1"
    s.tx_port = unused_tcp_port
    s.number_of_sync_loops = 2
    app = create_app(s)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test/api") as client:
            yield client, app.state.core, s


async def put(client, path, body, auth=ADMIN):
    return await client.put(path, content=json.dumps(body), headers={"Authorization": auth})


async def setup_network(client):
    r = await put(client, "/transmitters/tx1", {
        "authKey": "secret1", "longitude": "101.69", "latitude": "3.14", "power": "10",
        "timeSlot": "0123", "ownerNames": ["admin"], "antennaType": "OMNI", "usage": "WIDERANGE",
        "antennaAboveGroundLevel": 10, "antennaGainDbi": 2.5, "identificationAddress": 8,
    })
    assert r.status_code == 201, r.text
    r = await put(client, "/transmitterGroups/my-group", {"description": "test", "transmitterNames": ["TX1"],
                                                          "ownerNames": ["admin"]})
    assert r.status_code == 201, r.text
    r = await put(client, "/callsigns/9w2abc", {"description": "me", "numeric": False,
                                                "pagers": [{"number": 1234, "name": "skyper"}],
                                                "ownerNames": ["admin"]})
    assert r.status_code == 201, r.text


async def connect_transmitter(port, name="tx1", key="secret1"):
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(f"[UniPager v1.0.4 {name} {key}]\n".encode())
    while True:
        line = (await asyncio.wait_for(reader.readline(), 5)).decode().strip()
        if line.startswith("2:"):
            writer.write(f"{line}:0000\n+\n".encode())
        elif line.startswith("3:"):
            writer.write(b"+\n")
        elif line.startswith("4:"):
            assert line == "4:0123"
            writer.write(b"+\n")
            await writer.drain()
            return reader, writer
        else:
            raise AssertionError(f"unexpected line {line!r}")


async def test_auth_and_errors(env):
    client, core, _ = env
    r = await client.get("/stats")
    assert r.status_code == 200 and r.json()["users"] == 1
    r = await client.get("/users")
    assert r.status_code == 403 and r.json()["code"] == 4030
    r = await client.get("/users", headers={"Authorization": basic("admin", "nope")})
    assert r.status_code == 401 and r.json()["code"] == 4010
    r = await client.get("/users", headers={"Authorization": ADMIN})
    assert r.status_code == 200 and "hash" not in r.json()[0] and r.json()[0]["mail"]
    r = await client.get("/nothing/here/x", headers={"Authorization": ADMIN})
    assert r.status_code == 404
    r = await put(client, "/rubrics/x", {"number": 1})
    assert r.status_code == 400 and r.json()["code"] == 4001
    codes = {v["field"]: v["code"] for v in r.json()["violations"]}
    assert codes["name"] == 6002 and codes["transmitterGroupNames"] == 6001
    r = await client.options("/calls")
    assert r.status_code == 200 and r.headers["access-control-allow-origin"] == "*"


async def test_user_roles(env):
    client, core, _ = env
    r = await put(client, "/users/bob", {"hash": "bobpw", "mail": "bob@example.com", "admin": False})
    assert r.status_code == 201, r.text
    bob = basic("bob", "bobpw")
    # bob may edit himself but not make himself admin or create users
    assert (await put(client, "/users/bob", {"mail": "b2@example.com", "admin": False}, bob)).status_code == 200
    assert (await put(client, "/users/bob", {"mail": "b2@example.com", "admin": True}, bob)).status_code == 403
    assert (await put(client, "/users/eve", {"hash": "x", "mail": "e@example.com"}, bob)).status_code == 403
    # password unchanged when hash omitted
    assert (await client.get("/users/bob", headers={"Authorization": bob})).status_code == 200
    # plain users do not see transmitter auth keys
    await setup_network(client)
    r = await client.get("/transmitters/tx1", headers={"Authorization": bob})
    assert "authKey" not in r.json()
    r = await client.get("/transmitters/tx1", headers={"Authorization": ADMIN})
    assert r.json()["authKey"] == "secret1"


async def test_transmitter_flow(env):
    client, core, s = env
    await setup_network(client)
    reader, writer = await connect_transmitter(s.tx_port)
    await asyncio.sleep(0.05)
    r = await client.get("/transmitters/tx1")
    t = r.json()
    assert t["status"] == "ONLINE" and t["deviceType"] == "UniPager" and t["address"]["ip_addr"] == "127.0.0.1"

    r = await client.post("/calls", content=json.dumps({"text": "Hallo Welt", "callSignNames": ["9W2ABC"],
                                                         "transmitterGroupNames": ["my-group"]}),
                          headers={"Authorization": ADMIN})
    assert r.status_code == 201, r.text
    line = (await asyncio.wait_for(reader.readline(), 5)).decode()
    assert line == "#00 6:1:4D2:3:Hallo Welt\n"
    writer.write(b"#01 +\n")
    await writer.drain()

    # retry once, then ok
    core.tx.send_identification()
    line = (await asyncio.wait_for(reader.readline(), 5)).decode()
    assert line == "#01 6:1:8:3:tx1\n"
    writer.write(b"#01 %\n")
    await writer.drain()
    assert (await asyncio.wait_for(reader.readline(), 5)).decode() == line
    writer.write(b"#02 +\n")
    await writer.drain()
    await asyncio.sleep(0.05)
    assert (await client.get("/transmitters/tx1")).json()["callCount"] == 1

    # rubric + news
    r = await put(client, "/rubrics/wxr", {"number": 3, "label": "Weather", "transmitterGroupNames": ["my-group"],
                                          "ownerNames": ["admin"]})
    assert r.status_code == 201, r.text
    rubric_line = (await asyncio.wait_for(reader.readline(), 5)).decode()
    assert rubric_line.startswith("#02 6:1:11A0:3:1")
    writer.write(b"#03 +\n")
    await writer.drain()
    r = await client.post("/news", content=json.dumps({"rubricName": "wxr", "text": "Sunny"}),
                          headers={"Authorization": ADMIN})
    assert r.status_code == 201, r.text
    assert r.json()["number"] == 1
    as_call = (await asyncio.wait_for(reader.readline(), 5)).decode()
    assert as_call == "#03 6:1:3EB:3:Sunny\n"  # rubric address 1000 + 3

    # editing the transmitter disconnects it so it reconnects with new settings
    writer.write(b"#04 +\n")
    await writer.drain()
    await asyncio.sleep(0.05)
    r = await put(client, "/transmitters/tx1", {**{k: t[k] for k in (
        "longitude", "latitude", "power", "ownerNames", "antennaType", "usage")},
        "authKey": "secret1", "timeSlot": "0123"})
    assert r.status_code == 200, r.text
    assert (await asyncio.wait_for(reader.read(), 5)) in (b"", b'#04 6:1:11A8:3:"!Tvooz\n')
    writer.close()


async def test_bad_key_rejected(env):
    client, core, s = env
    await setup_network(client)
    reader, writer = await asyncio.open_connection("127.0.0.1", s.tx_port)
    writer.write(b"[UniPager v1.0.4 tx1 wrong]\n")
    assert await asyncio.wait_for(reader.read(), 5) == b"7 Invalid credentials"
    writer.close()


async def test_cascade_delete_and_persistence(env, tmp_path):
    client, core, s = env
    await setup_network(client)
    await client.post("/calls", content=json.dumps({"text": "x", "callSignNames": ["9w2abc"],
                                                    "transmitterGroupNames": ["my-group"]}),
                      headers={"Authorization": ADMIN})
    r = await client.delete("/transmitters/tx1", headers={"Authorization": ADMIN})
    assert r.status_code == 200
    # group had only tx1 -> deleted, and the call that only targeted it is gone
    assert (await client.get("/transmitterGroups", headers={"Authorization": ADMIN})).json() == []
    assert (await client.get("/calls", headers={"Authorization": ADMIN})).json() == []
    saved = json.loads((tmp_path / "State.json").read_text())
    assert "tx1" not in saved["transmitters"] and saved["stats"]["calls"] == 1
    assert (tmp_path / "State.json.bak").exists()
