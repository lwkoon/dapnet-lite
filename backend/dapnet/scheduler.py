"""Minimal Quartz-style cron (`sec min hour day-of-month month day-of-week`) and an
asyncio job runner. Supports `*`, `?`, lists, ranges and `/` steps; day-of-week is
1-7 = SUN-SAT as in Quartz, names (MON, TUE, ...) are accepted too."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable

log = logging.getLogger(__name__)

_DOW_NAMES = {"SUN": 1, "MON": 2, "TUE": 3, "WED": 4, "THU": 5, "FRI": 6, "SAT": 7}
_MON_NAMES = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def _parse_field(expr: str, lo: int, hi: int, names: dict[str, int] | None = None) -> set[int] | None:
    """Returns the allowed values, or None for 'any'."""
    if expr in ("*", "?"):
        return None
    values: set[int] = set()
    for part in expr.split(","):
        step = 1
        has_step = "/" in part
        if has_step:
            part, step_s = part.split("/", 1)
            step = int(step_s)
        if part in ("*", "?", ""):
            start, end = lo, hi
        elif "-" in part:
            a, b = part.split("-", 1)
            start, end = _num(a, names), _num(b, names)
        else:
            start = _num(part, names)
            end = hi if has_step else start
        if not (lo <= start <= hi and lo <= end <= hi):
            raise ValueError(f"cron value out of range in {expr!r}")
        values.update(range(start, end + 1, step))
    return values


def _num(s: str, names: dict[str, int] | None) -> int:
    s = s.strip().upper()
    if names and s in names:
        return names[s]
    return int(s)


class Cron:
    def __init__(self, expr: str):
        parts = expr.split()
        if len(parts) == 7:
            parts = parts[:6]  # ignore optional year
        if len(parts) != 6:
            raise ValueError(f"expected 6 cron fields, got {expr!r}")
        self.expr = expr
        self.sec = _parse_field(parts[0], 0, 59)
        self.min = _parse_field(parts[1], 0, 59)
        self.hour = _parse_field(parts[2], 0, 23)
        self.dom = _parse_field(parts[3], 1, 31)
        self.mon = _parse_field(parts[4], 1, 12, _MON_NAMES)
        self.dow = _parse_field(parts[5], 1, 7, _DOW_NAMES)

    @staticmethod
    def _ok(allowed: set[int] | None, v: int) -> bool:
        return allowed is None or v in allowed

    def matches(self, t: datetime) -> bool:
        quartz_dow = (t.isoweekday() % 7) + 1  # Mon=1..Sun=7 -> Sun=1..Sat=7
        return (self._ok(self.sec, t.second) and self._ok(self.min, t.minute) and self._ok(self.hour, t.hour)
                and self._ok(self.dom, t.day) and self._ok(self.mon, t.month) and self._ok(self.dow, quartz_dow))

    def next_after(self, t: datetime) -> datetime:
        t = t.replace(microsecond=0) + timedelta(seconds=1)
        # coarse search: skip minutes/hours that cannot match
        for _ in range(366 * 24 * 60):
            if not (self._ok(self.mon, t.month) and self._ok(self.dom, t.day)
                    and self._ok(self.dow, (t.isoweekday() % 7) + 1)):
                t = (t + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                continue
            if not self._ok(self.hour, t.hour):
                t = (t + timedelta(hours=1)).replace(minute=0, second=0)
                continue
            if not self._ok(self.min, t.minute):
                t = (t + timedelta(minutes=1)).replace(second=0)
                continue
            for s in range(t.second, 60):
                if self._ok(self.sec, s):
                    return t.replace(second=s)
            t = (t + timedelta(minutes=1)).replace(second=0)
        raise ValueError(f"cron {self.expr!r} never fires")


class Scheduler:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, Cron, Callable[[], None]]] = []
        self.tasks: list[asyncio.Task] = []

    def add(self, name: str, expr: str, fn: Callable[[], None]) -> None:
        self.jobs.append((name, Cron(expr), fn))

    def start(self) -> None:
        for job in self.jobs:
            self.tasks.append(asyncio.create_task(self._run(*job), name=f"job:{job[0]}"))
        log.info("Scheduler started with %d jobs", len(self.jobs))

    async def stop(self) -> None:
        for t in self.tasks:
            t.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

    @staticmethod
    async def _run(name: str, cron: Cron, fn: Callable[[], None]) -> None:
        while True:
            now = datetime.now()  # server local time, like Quartz
            nxt = cron.next_after(now)
            await asyncio.sleep(max(0.0, (nxt - datetime.now()).total_seconds()))
            try:
                fn()
            except Exception:
                log.exception("Job %s failed", name)
