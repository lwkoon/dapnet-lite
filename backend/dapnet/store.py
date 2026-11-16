"""In-memory state with JSON persistence, layout-compatible with DAPNET Core State.json."""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

NEWS_SLOTS = 10
MAP_KEYS = ("callSigns", "nodes", "users", "transmitters", "transmitterGroups", "rubrics")


def now_iso() -> str:
    """Java Instant.toString() style: 2026-11-16T07:00:00.123Z"""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class Store:
    def __init__(self, path: str):
        self.path = Path(path)
        self.callSigns: dict[str, dict] = {}
        self.nodes: dict[str, dict] = {}
        self.users: dict[str, dict] = {}
        self.transmitters: dict[str, dict] = {}
        self.transmitterGroups: dict[str, dict] = {}
        self.rubrics: dict[str, dict] = {}
        self.calls: list[dict] = []
        self.news: dict[str, list[dict | None]] = {}
        self.stats = {"calls": 0, "news": 0}
        self.dirty = False

    # --- lookup helpers --------------------------------------------------------------
    def collection(self, name: str) -> dict[str, dict]:
        return getattr(self, name)

    def exists(self, collection: str, name: str) -> bool:
        return name.lower() in self.collection(collection)

    # --- persistence -----------------------------------------------------------------
    def load(self) -> bool:
        if not self.path.is_file():
            log.warning("State file %s not found, starting with empty state", self.path)
            return False
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        for key in MAP_KEYS:
            # keys are lower-case in the Java core too; normalise defensively
            self.collection(key).update({k.lower(): v for k, v in (raw.get(key) or {}).items() if v})
        self.calls = [c for c in (raw.get("calls") or []) if c]
        for rubric, slots in (raw.get("news") or {}).items():
            lst: list[dict | None] = [None] * NEWS_SLOTS
            for n in slots or []:
                if n and 1 <= int(n.get("number", 0)) <= NEWS_SLOTS:
                    lst[int(n["number"]) - 1] = n
            self.news[rubric.lower()] = lst
        stats = raw.get("stats") or raw.get("coreStats") or {}
        self.stats = {"calls": int(stats.get("calls", 0)), "news": int(stats.get("news", 0))}
        # every rubric needs a news list
        for name in self.rubrics:
            self.news.setdefault(name, [None] * NEWS_SLOTS)
        log.info("Loaded state: %d users, %d transmitters, %d callsigns, %d rubrics",
                 len(self.users), len(self.transmitters), len(self.callSigns), len(self.rubrics))
        return True

    def to_json(self) -> dict:
        data = {key: self.collection(key) for key in MAP_KEYS}
        data["calls"] = self.calls
        data["news"] = self.news
        data["stats"] = self.stats
        return data

    def save(self) -> None:
        """Atomic write: keep the previous file as .bak, write a temp file, rename."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_json(), indent=2, ensure_ascii=False)
        if self.path.exists():
            shutil.copy2(self.path, self.path.with_suffix(self.path.suffix + ".bak"))
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".state-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        self.dirty = False
        log.debug("State written to %s", self.path)
