"""Core operations: state changes with cascading deletes, and routing of calls, news,
rubrics and activations to transmitters. Port of RpcListener + TransmissionManager +
NewsList."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

from . import auth, pager
from .config import Settings
from .store import NEWS_SLOTS, Store, now_iso, parse_iso
from .txserver import TransmitterManager

log = logging.getLogger(__name__)

VERSION = "2.0.0"


class Core:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = Store(settings.state_file)
        self.tx = TransmitterManager(
            lookup=lambda name: self.store.transmitters.get(name),
            on_status=lambda t: self.changed(),
            node_name=settings.node_name,
            sync_loops=settings.number_of_sync_loops,
            send_speed=settings.send_speed,
        )

    # --- lifecycle -------------------------------------------------------------------
    def load(self) -> None:
        self.store.load()
        # nobody is connected yet
        for t in self.store.transmitters.values():
            if t.get("status") != "DISABLED":
                t["status"] = "OFFLINE"
            t["connectedSince"] = None
        self.store.nodes[self.settings.node_name.lower()] = {
            **self.store.nodes.get(self.settings.node_name.lower(), {}),
            "name": self.settings.node_name,
            "status": "ONLINE",
            "version": VERSION,
            "longitude": self.store.nodes.get(self.settings.node_name.lower(), {}).get("longitude", "0"),
            "latitude": self.store.nodes.get(self.settings.node_name.lower(), {}).get("latitude", "0"),
            "ownerNames": self.store.nodes.get(self.settings.node_name.lower(), {}).get("ownerNames") or ["admin"],
        }
        for name, node in self.store.nodes.items():
            if name != self.settings.node_name.lower():
                node["status"] = "SUSPENDED"
        if not self.store.users:
            password = self.settings.admin_password or secrets.token_urlsafe(12)
            self.store.users["admin"] = {"name": "admin", "hash": auth.create_hash(password),
                                         "mail": "admin@example.com", "admin": True}
            if self.settings.admin_password:
                log.warning("Created user 'admin' with the password from DAPNET_ADMIN_PASSWORD")
            else:
                log.warning("Created user 'admin' with password: %s  (change it after first login)", password)
        self.save()

    def changed(self) -> None:
        self.store.dirty = True
        if self.settings.saving_immediately:
            self.save()

    def save(self) -> None:
        try:
            self.store.save()
        except OSError:
            log.exception("Failed to write state file")

    # --- routing helpers -------------------------------------------------------------
    def transmitters_in(self, group_names) -> set[str]:
        names: set[str] = set()
        for g in group_names:
            grp = self.store.transmitterGroups.get(g.lower())
            if grp:
                names.update(n.lower() for n in grp.get("transmitterNames", []))
        return names

    def send_time(self) -> None:
        self.tx.send_all(pager.messages_time(datetime.now(timezone.utc).replace(tzinfo=None)))
        log.info("Time sent to transmitters")

    def send_local_time(self) -> None:
        self.tx.send_all(pager.messages_local_time(datetime.now()))
        log.info("Local time sent to transmitters")

    def send_rubric(self, rubric: dict, only: str | None = None) -> None:
        targets = self.transmitters_in(rubric.get("transmitterGroupNames", []))
        if only is not None:
            targets &= {only.lower()}
        self.tx.send_to(targets, [pager.message_rubric(rubric)])

    def send_all_rubrics(self) -> None:
        for r in list(self.store.rubrics.values()):
            self.send_rubric(r)

    def send_news(self, news: dict) -> None:
        rubric = self.store.rubrics.get(news["rubricName"].lower())
        if rubric:
            self.tx.send_to(self.transmitters_in(rubric["transmitterGroupNames"]), [pager.message_news(news, rubric)])

    def send_news_as_call(self, news: dict) -> None:
        rubric = self.store.rubrics.get(news["rubricName"].lower())
        if rubric:
            self.tx.send_to(self.transmitters_in(rubric["transmitterGroupNames"]),
                            [pager.message_news_as_call(news, rubric)])

    def resend_all_news(self) -> None:
        for slots in self.store.news.values():
            for n in slots:
                if n:
                    self.send_news(n)

    # --- operations ------------------------------------------------------------------
    def post_call(self, call: dict) -> None:
        self.store.calls.append(call)
        self.store.stats["calls"] += 1
        callsigns = [self.store.callSigns[n] for n in call["callSignNames"] if n in self.store.callSigns]
        messages = pager.messages_from_call(call, callsigns)
        targets = self.transmitters_in(call["transmitterGroupNames"])
        self.tx.send_to(targets, messages)
        for name in targets:
            t = self.store.transmitters.get(name)
            if t is not None:
                t["callCount"] = int(t.get("callCount") or 0) + 1
        log.info("Call from %s to %d callsign(s), %d pager message(s), %d transmitter(s)",
                 call["ownerName"], len(callsigns), len(messages), len(targets))
        self.changed()

    def post_activation(self, activation: dict) -> bool:
        msg = pager.message_activation(activation["number"], self.settings.activation_code)
        if msg is None:
            return False
        self.tx.send_to(self.transmitters_in(activation["transmitterGroupNames"]), [msg])
        log.info("Activation for RIC %d sent", activation["number"])
        return True

    def post_news(self, news: dict) -> None:
        rubric_name = news["rubricName"].lower()
        slots = self.store.news.setdefault(rubric_name, [None] * NEWS_SLOTS)
        self.send_news_as_call(news)
        if news["number"] < 1:
            # push to the top, shifting older entries down one slot
            item: dict | None = news
            for i in range(NEWS_SLOTS):
                if item is not None:
                    item["number"] = i + 1
                item, slots[i] = slots[i], item
            for n in slots:
                if n:
                    self.send_news(n)
        else:
            slots[(news["number"] - 1) % NEWS_SLOTS] = news
            self.send_news(news)
        self.store.stats["news"] += 1
        self.changed()

    def put(self, collection: str, obj: dict) -> None:
        key = obj["name"].lower()
        self.store.collection(collection)[key] = obj
        if collection == "rubrics":
            self.store.news.setdefault(key, [None] * NEWS_SLOTS)
            self.send_rubric(obj)
        self.changed()

    # cascading deletes, same rules as the Java core
    def _strip(self, items, field: str, name: str, on_empty) -> None:
        for obj in list(items):
            refs = obj.get(field) or []
            if name in refs:
                if len(refs) == 1:
                    on_empty(obj)
                else:
                    refs.remove(name)

    def _remove_call(self, call: dict) -> None:
        if call in self.store.calls:
            self.store.calls.remove(call)

    def delete_callsign(self, name: str) -> None:
        self._strip(self.store.calls, "callSignNames", name, self._remove_call)
        self.store.callSigns.pop(name, None)

    def delete_rubric(self, name: str) -> None:
        self.store.news.pop(name, None)
        self.store.rubrics.pop(name, None)

    def delete_transmitter_group(self, name: str) -> None:
        self._strip(self.store.rubrics.values(), "transmitterGroupNames", name,
                    lambda r: self.delete_rubric(r["name"].lower()))
        self._strip(self.store.calls, "transmitterGroupNames", name, self._remove_call)
        self.store.transmitterGroups.pop(name, None)

    def delete_transmitter(self, name: str) -> None:
        self._strip(self.store.transmitterGroups.values(), "transmitterNames", name,
                    lambda g: self.delete_transmitter_group(g["name"].lower()))
        self.store.transmitters.pop(name, None)
        self.tx.disconnect(name)

    def delete_user(self, name: str) -> None:
        self._strip(self.store.callSigns.values(), "ownerNames", name,
                    lambda c: self.delete_callsign(c["name"].lower()))
        for call in [c for c in self.store.calls if c.get("ownerName", "").lower() == name]:
            self._remove_call(call)
        self._strip(self.store.rubrics.values(), "ownerNames", name, lambda r: self.delete_rubric(r["name"].lower()))
        self._strip(self.store.transmitterGroups.values(), "ownerNames", name,
                    lambda g: self.delete_transmitter_group(g["name"].lower()))
        self._strip(self.store.transmitters.values(), "ownerNames", name,
                    lambda t: self.delete_transmitter(t["name"].lower()))
        self.store.users.pop(name, None)

    def delete(self, collection: str, name: str) -> None:
        name = name.lower()
        {
            "callSigns": self.delete_callsign,
            "rubrics": self.delete_rubric,
            "transmitterGroups": self.delete_transmitter_group,
            "transmitters": self.delete_transmitter,
            "users": self.delete_user,
            "nodes": lambda n: self.store.nodes.pop(n, None),
        }[collection](name)
        self.changed()

    # --- housekeeping ----------------------------------------------------------------
    def clean_expired(self) -> None:
        now = datetime.now(timezone.utc)
        call_ttl = timedelta(minutes=self.settings.call_expiration_minutes)
        news_ttl = timedelta(minutes=self.settings.news_expiration_minutes)
        before = len(self.store.calls)
        self.store.calls = [c for c in self.store.calls
                            if (ts := parse_iso(c.get("timestamp"))) is None or now <= ts + call_ttl]
        removed_news = 0
        for slots in self.store.news.values():
            for i, n in enumerate(slots):
                ts = parse_iso(n.get("timestamp")) if n else None
                if ts is not None and now > ts + news_ttl:
                    slots[i] = None
                    removed_news += 1
        log.info("Cleanup removed %d call(s) and %d news item(s)", before - len(self.store.calls), removed_news)
        self.save()

    def stats(self) -> dict:
        s = self.store
        return {
            "users": len(s.users),
            "calls": len(s.calls),
            "callsTotal": s.stats["calls"],
            "callSigns": len(s.callSigns),
            "news": sum(1 for slots in s.news.values() for n in slots if n),
            "newsTotal": s.stats["news"],
            "rubrics": len(s.rubrics),
            "nodesTotal": len(s.nodes),
            "nodesOnline": sum(1 for n in s.nodes.values() if n.get("status") == "ONLINE"),
            "transmittersTotal": len(s.transmitters),
            "transmittersOnline": sum(1 for t in s.transmitters.values() if t.get("status") == "ONLINE"),
        }


__all__ = ["Core", "VERSION", "now_iso"]
