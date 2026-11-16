"""Transmitter TCP server (port 43434).

Port of ServerHandler, SyncTimeHandler, TransmitterClient and TransmitterManager.
Line-based ASCII protocol:

  tx -> [Type vVersion name authkey]
  core -> 2:XXXX          time sync request (0.1 s ticks, 16 bit), repeated N times;
  tx -> 2:XXXX:YYYY       echo + transmitter time
  tx -> +
  core -> 3:+XXXX         time adjustment
  tx -> +
  core -> 4:slots         time slots
  tx -> +                 -> online
  core -> #SS T:S:ADDR:F:text
  tx -> #SS+ | #SS% | #SS-   ok (SS = next seq) / retry / error
"""

from __future__ import annotations

import asyncio
import heapq
import logging
import re
import socket
import time
from typing import Callable, Iterable

from . import pager
from .pager import PagerMessage
from .store import now_iso

log = logging.getLogger(__name__)

ACK_RE = re.compile(r"#([0-9A-Fa-f]{2}) ([-%+])")
AUTH_RE = re.compile(r"\[([/\-A-Za-z0-9]+) v(\d[\d.]+[!-~]*) ([A-Za-z0-9_]+) ([A-Za-z0-9]+)\]")
SYNC_RE = re.compile(r"(\d):(\w+):(\w+)")
HANDSHAKE_TIMEOUT = 30
MAX_RETRY = 5
MAX_LINE = 2048


class ProtocolError(Exception):
    pass


def _ticks() -> int:
    """Current time in 1/10 s, truncated to 16 bits."""
    ms = int(time.time() * 1000)
    return ((ms // 1000) * 10 + (ms % 1000) // 100) & 0xFFFF


class Client:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, send_speed: int):
        self.reader = reader
        self.writer = writer
        self.send_speed = send_speed
        self.transmitter: dict | None = None
        self.queue: list[PagerMessage] = []
        self.seq = 0
        self.current: tuple[int, PagerMessage] | None = None
        self.retries = 0
        peer = writer.get_extra_info("peername") or ("?", 0)
        self.peer = (peer[0], peer[1])

    @property
    def name(self) -> str:
        return self.transmitter["name"] if self.transmitter else f"{self.peer[0]}:{self.peer[1]}"

    def write_line(self, line: str) -> None:
        self.writer.write(line.encode("ascii", errors="replace"))

    async def read_line(self) -> str:
        try:
            raw = await self.reader.readuntil(b"\n")
        except asyncio.LimitOverrunError as e:
            raise ProtocolError("line too long") from e
        except asyncio.IncompleteReadError as e:
            raise ConnectionResetError("connection closed") from e
        return raw.decode("ascii", errors="replace").rstrip("\r\n")

    # --- message queue ---------------------------------------------------------------
    def send(self, messages: Iterable[PagerMessage]) -> None:
        for m in messages:
            heapq.heappush(self.queue, m)
        self._send_next(False)

    def pending(self) -> int:
        return len(self.queue) + (1 if self.current else 0)

    def _send_next(self, retransmit: bool) -> None:
        if self.writer.is_closing():
            return
        if self.current is None:
            if not self.queue:
                return
            msg = heapq.heappop(self.queue)
            self.current = (self.seq, msg)
            self.retries = 0
            self.seq = (self.seq + 1) % 256
        elif not retransmit:
            return
        seq, msg = self.current
        self.writer.write(pager.encode_wire(seq, msg, self.send_speed))

    def ack(self, seq: int, kind: str) -> bool:
        if self.current is None:
            return False
        cur_seq = self.current[0]
        retransmit = False
        if kind == "+":
            valid = (cur_seq + 1) % 256 == seq
            self.current = None
        elif kind == "%":
            valid = cur_seq == seq
            self.retries += 1
            if self.retries < MAX_RETRY:
                retransmit = True
            else:
                self.current = None
        else:
            valid = cur_seq == seq
            self.current = None
        self._send_next(retransmit)
        return valid

    def close(self) -> None:
        if not self.writer.is_closing():
            self.writer.close()


class TransmitterManager:
    """Tracks connected transmitters and routes messages to them."""

    def __init__(self, lookup: Callable[[str], dict | None], on_status: Callable[[dict], None],
                 node_name: str, sync_loops: int, send_speed: int):
        self.lookup = lookup
        self.on_status = on_status
        self.node_name = node_name
        self.sync_loops = sync_loops
        self.send_speed = send_speed
        self.clients: dict[str, Client] = {}
        self._server: asyncio.base_events.Server | None = None

    # --- routing ---------------------------------------------------------------------
    def send_all(self, messages: list[PagerMessage]) -> None:
        for c in list(self.clients.values()):
            c.send(messages)

    def send_to(self, names: Iterable[str], messages: list[PagerMessage]) -> int:
        count = 0
        for n in set(x.lower() for x in names):
            c = self.clients.get(n)
            if c:
                c.send(messages)
                count += 1
        return count

    def send_identification(self) -> None:
        for c in list(self.clients.values()):
            t = c.transmitter
            if t:
                c.send([pager.message_identification(t["name"], int(t.get("identificationAddress", 1)))])

    def disconnect(self, name: str) -> None:
        c = self.clients.pop(name.lower(), None)
        if c:
            c.close()

    def disconnect_all(self) -> None:
        for name in list(self.clients):
            self.disconnect(name)

    # --- server ----------------------------------------------------------------------
    async def start(self, host: str, port: int) -> None:
        self._server = await asyncio.start_server(self._handle, host, port, limit=MAX_LINE)
        log.info("Transmitter server listening on %s:%d", host, port)

    async def stop(self) -> None:
        self.disconnect_all()
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        sock = writer.get_extra_info("socket")
        if sock is not None:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        client = Client(reader, writer, self.send_speed)
        log.info("Accepted connection from %s:%d", *client.peer)
        try:
            await asyncio.wait_for(self._handshake(client), HANDSHAKE_TIMEOUT)
            self._on_connect(client)
            while True:
                line = await client.read_line()
                m = ACK_RE.fullmatch(line)
                if not m:
                    raise ProtocolError(f"Invalid response received: {line}")
                if not client.ack(int(m.group(1), 16), m.group(2)):
                    log.warning("Invalid ack received from %s: %s", client.name, line)
                await writer.drain()
        except asyncio.TimeoutError:
            log.warning("Handshake timed out for %s", client.name)
        except ProtocolError as e:
            log.error("Closing connection for %s: %s", client.name, e)
            if client.transmitter is not None:
                client.transmitter["status"] = "ERROR"
        except (ConnectionError, OSError) as e:
            log.info("Connection to %s lost: %s", client.name, e)
        except Exception:
            log.exception("Unexpected error in transmitter handler for %s", client.name)
            if client.transmitter is not None:
                client.transmitter["status"] = "ERROR"
        finally:
            if client.pending():
                log.warning("Client %s has %d pending messages", client.name, client.pending())
            client.close()
            self._on_disconnect(client)
            log.info("Connection to %s closed", client.name)

    async def _reject(self, client: Client, reason: str) -> None:
        # The Java core sends the reason without a trailing newline and closes.
        client.writer.write(f"7 {reason}".encode("ascii"))
        try:
            await client.writer.drain()
        finally:
            client.close()
        raise ConnectionResetError(reason)

    async def _handshake(self, client: Client) -> None:
        line = await client.read_line()
        m = AUTH_RE.fullmatch(line)
        if not m:
            log.error("Invalid welcome message from %s: %s", client.peer[0], line)
            await self._reject(client, "Invalid welcome message format")
        dev_type, version, name, key = m.groups()
        t = self.lookup(name.lower())
        if t is None:
            log.error("Transmitter %s not registered (from %s)", name, client.peer[0])
            await self._reject(client, "Transmitter not registered")
        if t.get("status") == "DISABLED":
            log.error("Transmitter %s is disabled (from %s)", name, client.peer[0])
            await self._reject(client, "Transmitter disabled")
        if t.get("authKey") != key:
            log.error("Wrong auth key for transmitter %s (from %s)", name, client.peer[0])
            await self._reject(client, "Invalid credentials")

        self.disconnect(t["name"])
        t["deviceType"] = dev_type
        t["deviceVersion"] = version
        t["address"] = {"ip_addr": client.peer[0], "port": client.peer[1]}
        client.transmitter = t

        # time synchronisation: keep the adjustment from the round trip with lowest RTT
        min_rtt = None
        adjust = 0
        for _ in range(self.sync_loops):
            tx = _ticks()
            tx_msg = f"{tx:04X}"
            client.write_line(f"{pager.MT_SYNCREQUEST}:{tx_msg}\n")
            await client.writer.drain()
            resp = await client.read_line()
            rx = _ticks()
            if await client.read_line() != "+":
                raise ProtocolError("Wrong ack received.")
            sm = SYNC_RE.fullmatch(resp)
            if not sm or int(sm.group(1)) != pager.MT_SYNCREQUEST or sm.group(2).upper() != tx_msg:
                raise ProtocolError("Wrong sync response received.")
            rtt = rx - tx
            if min_rtt is None or rtt < min_rtt:
                min_rtt = rtt
                adjust = (tx + int(rtt / 2)) - int(sm.group(3), 16)
        if abs(adjust) > 65536:
            raise ProtocolError("Time difference too large.")
        sign = "-" if adjust < 0 else "+"
        client.write_line(f"{pager.MT_SYNCORDER}:{sign}{abs(adjust):04X}\n")
        await client.writer.drain()
        if await client.read_line() != "+":
            raise ProtocolError("Wrong ack received.")

        client.write_line(f"{pager.MT_SLOTS}:{t.get('timeSlot', '')}\n")
        await client.writer.drain()
        if await client.read_line() != "+":
            raise ProtocolError("Wrong ack received.")

    def _on_connect(self, client: Client) -> None:
        t = client.transmitter
        ts = now_iso()
        t["status"] = "ONLINE"
        t["lastConnected"] = ts
        t["connectedSince"] = ts
        t["nodeName"] = self.node_name
        self.clients[t["name"].lower()] = client
        log.info("Transmitter %s online (%s %s from %s)", t["name"], t.get("deviceType"),
                 t.get("deviceVersion"), client.peer[0])
        self.on_status(t)

    def _on_disconnect(self, client: Client) -> None:
        t = client.transmitter
        if t is None:
            return
        key = t["name"].lower()
        if self.clients.get(key) is client:
            del self.clients[key]
        elif key in self.clients:
            return  # a newer connection owns this transmitter now
        if t.get("status") != "ERROR":
            t["status"] = "OFFLINE"
        t["connectedSince"] = None
        self.on_status(t)
