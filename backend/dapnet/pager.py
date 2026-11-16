"""Pager message model and Skyper/POCSAG payload encoding.

Byte-compatible port of the DAPNET Core Java classes PagerMessage, SkyperProtocol,
DE_ASCII7 and MessageEncoder.
"""

from __future__ import annotations

import enum
import itertools
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone


class Priority(enum.IntEnum):
    """Lower value is sent first."""

    EMERGENCY = 0
    TIME = 1
    CALL = 2
    NEWS = 3
    ACTIVATION = 4
    RUBRIC = 5


class FunctionalBits(enum.IntEnum):
    NUMERIC = 0
    TONE = 1
    ACTIVATION = 2
    ALPHANUM = 3


# Wire message types
MT_SYNCREQUEST = 2
MT_SYNCORDER = 3
MT_SLOTS = 4
MT_NUMERIC = 5
MT_ALPHANUM = 6

ADDR_TIME_SKYPER = 2504
ADDR_TIME_SWISSPHONE = 200
ADDR_LOCALTIME_SWISSPHONE = 208
ADDR_TIME_ALPHAPOC = 216
ADDR_LOCALTIME_ALPHAPOC = 224
ADDR_RUBRIC_NAMES = 4512
ADDR_NEWS = 4520

_order = itertools.count()


@dataclass(order=True)
class PagerMessage:
    sort_key: tuple = field(init=False, repr=False)
    text: str = field(compare=False)
    address: int = field(compare=False)
    priority: Priority = field(compare=False)
    bits: FunctionalBits = field(compare=False)
    timestamp: float = field(compare=False, default_factory=lambda: datetime.now(timezone.utc).timestamp())

    def __post_init__(self) -> None:
        # priority first, then age; the counter keeps FIFO order for equal timestamps
        self.sort_key = (int(self.priority), self.timestamp, next(_order))


# --- German 7-bit charset (DIN 66003) -------------------------------------------------

_DE_MAP = {"Ä": 91, "Ö": 92, "Ü": 93, "ä": 123, "ö": 124, "ü": 125, "ß": 126}


def encode_de_ascii7(text: str) -> str:
    """Map text to 7-bit DE-ASCII. Unmapped characters are masked to 7 bits, as in Java
    (which works on UTF-16 code units, so astral characters become two masked units)."""
    out = []
    for ch in text:
        code = _DE_MAP.get(ch)
        if code is not None:
            out.append(chr(code))
            continue
        cp = ord(ch)
        if cp > 0xFFFF:
            cp -= 0x10000
            for unit in (0xD800 + (cp >> 10), 0xDC00 + (cp & 0x3FF)):
                out.append(chr(unit & 0x7F))
        else:
            out.append(chr(cp & 0x7F))
    return "".join(out)


def _single_line(text: str) -> str:
    # The transmitter protocol is line framed; a newline inside a payload would corrupt it.
    return text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")


# --- Skyper protocol ----------------------------------------------------------------

_NUMERIC_RE = re.compile(r"[-Uu\d() ]+")


def messages_from_call(call: dict, callsigns: list[dict]) -> list[PagerMessage]:
    priority = Priority.EMERGENCY if call.get("emergency") else Priority.CALL
    text = _single_line(call["text"])
    numeric_text = _NUMERIC_RE.fullmatch(text) is not None
    now = datetime.now(timezone.utc).timestamp()
    messages: list[PagerMessage] = []
    for cs in callsigns:
        if not cs.get("numeric"):
            bits, payload = FunctionalBits.ALPHANUM, encode_de_ascii7(text)
        elif numeric_text:
            bits, payload = FunctionalBits.NUMERIC, text.upper()
        else:
            continue  # numeric-only pager cannot show this text
        for pager in cs.get("pagers") or []:
            messages.append(PagerMessage(payload, int(pager["number"]), priority, bits, now))
    return messages


def message_time(utc: datetime) -> PagerMessage:
    return PagerMessage(utc.strftime("%H%M%S   %d%m%y"), ADDR_TIME_SKYPER, Priority.TIME, FunctionalBits.NUMERIC)


def _swissphone(t: datetime) -> str:
    s = t.strftime("XTIME=%H%M%d%m%y")
    return s + s


def _alphapoc(t: datetime) -> str:
    return "YYYYMMDDHHMMSS" + t.strftime("%y%m%d%H%M") + "00"


def messages_time(utc: datetime) -> list[PagerMessage]:
    return [
        message_time(utc),
        PagerMessage(_swissphone(utc), ADDR_TIME_SWISSPHONE, Priority.TIME, FunctionalBits.ALPHANUM),
        PagerMessage(_alphapoc(utc), ADDR_TIME_ALPHAPOC, Priority.TIME, FunctionalBits.ALPHANUM),
    ]


def messages_local_time(local: datetime) -> list[PagerMessage]:
    return [
        PagerMessage(_swissphone(local), ADDR_LOCALTIME_SWISSPHONE, Priority.TIME, FunctionalBits.ALPHANUM),
        PagerMessage(_alphapoc(local), ADDR_LOCALTIME_ALPHAPOC, Priority.TIME, FunctionalBits.ALPHANUM),
    ]


def _shift(text: str) -> str:
    return "".join(chr(ord(c) + 1) for c in text)


def message_rubric(rubric: dict) -> PagerMessage:
    label = encode_de_ascii7(rubric["label"])
    text = "1" + chr(int(rubric["number"]) + 0x1F) + chr(10 + 0x20) + _shift(label)
    return PagerMessage(text, ADDR_RUBRIC_NAMES, Priority.RUBRIC, FunctionalBits.ALPHANUM)


def message_news(news: dict, rubric: dict) -> PagerMessage:
    text = encode_de_ascii7(news["text"])
    payload = chr(int(rubric["number"]) + 0x1F) + chr(int(news["number"]) + 0x20) + _shift(text)
    return PagerMessage(payload, ADDR_NEWS, Priority.NEWS, FunctionalBits.ALPHANUM)


def message_news_as_call(news: dict, rubric: dict) -> PagerMessage:
    text = encode_de_ascii7(_single_line(news["text"]))
    return PagerMessage(text, 1000 + int(rubric["number"]), Priority.CALL, FunctionalBits.ALPHANUM)


def message_activation(number: int, activation_code: str) -> PagerMessage | None:
    chars = []
    for part in activation_code.split(","):
        sub = part.split(" ")
        if len(sub) != 3:
            return None
        shift, mask, offset = (int(x) for x in sub)
        chars.append(chr(((number >> shift) & mask) + offset))
    return PagerMessage("".join(chars), number, Priority.ACTIVATION, FunctionalBits.ACTIVATION)


def message_identification(name: str, address: int) -> PagerMessage:
    return PagerMessage(name, address, Priority.CALL, FunctionalBits.ALPHANUM)


def encode_wire(seq: int, msg: PagerMessage, send_speed: int) -> bytes:
    """`#SS T:S:ADDR:F:text\\n` — sequence and address in upper-case hex."""
    mtype = MT_NUMERIC if msg.bits == FunctionalBits.NUMERIC else MT_ALPHANUM
    line = f"#{seq:02X} {mtype}:{send_speed:X}:{msg.address:X}:{int(msg.bits)}:{msg.text}\n"
    return line.encode("ascii", errors="replace")
