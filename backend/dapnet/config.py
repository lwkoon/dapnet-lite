"""Settings loader. Reads the same Settings.json layout as DAPNET Core; unknown keys
(e.g. clusterSettings.clusterConfigurationFile) are ignored. Environment variables
override the file."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class Settings:
    # transmissionSettings
    number_of_sync_loops: int = 5
    send_speed: int = 1  # 0: 512, 1: 1200, 2: 2400 baud
    activation_code: str = "0 7 50,0 7 34,0 7 53,0 7 51,0 7 51,0 7 52,0 7 52,0 7 56"
    tx_host: str = "0.0.0.0"
    tx_port: int = 43434
    # modelSettings
    state_file: str = "data/State.json"
    saving_immediately: bool = True
    call_expiration_minutes: int = 24 * 60
    news_expiration_minutes: int = 24 * 60
    # restSettings
    rest_host: str = "0.0.0.0"
    rest_port: int = 8080
    # node identity (clusterSettings.nodeName in the Java core)
    node_name: str = "dapnet-lite"
    # schedulerSettings (Quartz syntax: sec min hour dom month dow)
    cron: dict = field(default_factory=lambda: {
        "time": "0 0/20 * * * ?",
        "localTime": "0 10/20 * * * ?",
        "rubricNames": "15 0/20 * * * ?",
        "news": "45 0 * * * ?",
        "stateSaving": "30 0/10 * * * ?",
        "stateCleaning": "0 0 0 * * ?",
        "identification": "0 0/10 * * * ?",
    })
    web_dir: str = ""
    admin_password: str = ""


_CRON_KEYS = {
    "timeTransmissionCron": "time",
    "localTimeTransmissionCron": "localTime",
    "rubricNameTransmissionCron": "rubricNames",
    "newsTransmissionCron": "news",
    "stateSavingCron": "stateSaving",
    "stateCleaningCron": "stateCleaning",
    "transmitterIdentificationCron": "identification",
}


def load(path: str | None = None) -> Settings:
    s = Settings()
    path = path or os.environ.get("DAPNET_SETTINGS", "data/Settings.json")
    p = Path(path)
    if p.is_file():
        raw = json.loads(p.read_text(encoding="utf-8"))
        tx = raw.get("transmissionSettings", {})
        pp = tx.get("pagingProtocolSettings", {})
        s.number_of_sync_loops = int(pp.get("numberOfSyncLoops", s.number_of_sync_loops))
        s.send_speed = int(pp.get("sendSpeed", s.send_speed))
        s.activation_code = pp.get("activationCode", s.activation_code)
        s.tx_port = int(tx.get("serverSettings", {}).get("port", s.tx_port))
        ms = raw.get("modelSettings", {})
        s.state_file = ms.get("stateFile", s.state_file)
        s.saving_immediately = bool(ms.get("savingImmediately", s.saving_immediately))
        s.call_expiration_minutes = int(ms.get("callExpirationTimeInMinutes", s.call_expiration_minutes))
        s.news_expiration_minutes = int(ms.get("newsExpirationTimeInMinutes", s.news_expiration_minutes))
        rs = raw.get("restSettings", {})
        s.rest_host = rs.get("hostname", s.rest_host)
        s.rest_port = int(rs.get("port", s.rest_port))
        s.node_name = raw.get("clusterSettings", {}).get("nodeName") or s.node_name
        for k, v in raw.get("schedulerSettings", {}).items():
            if k in _CRON_KEYS:
                s.cron[_CRON_KEYS[k]] = v
        log.info("Loaded settings from %s", p)
    else:
        log.info("No settings file at %s, using defaults", p)

    env = os.environ
    s.state_file = env.get("DAPNET_STATE_FILE", s.state_file)
    s.rest_host = env.get("DAPNET_HTTP_HOST", s.rest_host)
    s.rest_port = int(env.get("DAPNET_HTTP_PORT", s.rest_port))
    s.tx_port = int(env.get("DAPNET_TX_PORT", s.tx_port))
    s.node_name = env.get("DAPNET_NODE_NAME", s.node_name)
    s.web_dir = env.get("DAPNET_WEB_DIR", s.web_dir)
    s.admin_password = env.get("DAPNET_ADMIN_PASSWORD", "")
    return s
