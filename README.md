# DAPNET Lite

A lightweight, standalone rewrite of [DAPNET Core](https://github.com/DecentralizedAmateurPagingNetwork/Core)
(Java) and [DAPNET Web](https://github.com/DecentralizedAmateurPagingNetwork/Web) (Vue 2).

- **backend/** — Python 3.12, Starlette + asyncio. One process runs the REST API, the transmitter
  server and the scheduler. ~45 MB RAM, two runtime dependencies (`starlette`, `uvicorn`).
- **web/** — Vue 3 + Vite single-page app, served by the backend. Same pages, same translations
  (9 languages) as DAPNET Web.

## Compatibility

| Area | Status |
|---|---|
| Transmitter protocol (TCP 43434) | Byte-compatible: handshake, time sync, time slots, `#SS` sequence/ack/retry. UniPager, RasPager and MMDVM DAPNET gateways connect unchanged. |
| Pager encoding | Same Skyper/Swissphone/AlphaPoc formats, DE-ASCII7 charset, rubric/news/activation encoding, message priorities. |
| REST API | Same paths, JSON fields, Basic auth, admin/owner/user rules, hidden fields and error codes — served under `/api` (like hampager.de). |
| State | Reads an existing DAPNET Core `State.json`. Old password hashes still work and are upgraded to PBKDF2-SHA256 on next login. |
| Settings | Reads the DAPNET Core `Settings.json` layout (cluster settings ignored). |
| Clustering | **Removed.** Runs as a single standalone node. |

Behaviour changes vs. the Java core:

- State is written atomically (temp file + rename, previous version kept as `State.json.bak`) on every change.
- Transmitter statuses are reset to `OFFLINE` on startup instead of keeping stale `ONLINE`.
- Editing a transmitter keeps its call counter and connection history.
- Newlines in call text are flattened (they would break the line-based transmitter protocol).
- The news counter in `/stats` counts news (Java incremented the call counter by mistake).
- Passwords may contain any characters.

## Run with Docker

```sh
cp .env.example .env && chmod 600 .env    # set DAPNET_ADMIN_PASSWORD, DAPNET_NODE_NAME, TZ
docker compose up -d --build
docker compose logs -f                    # first start prints the admin password if none was set
```

- Web UI / API: `http://127.0.0.1:8097` (bound to localhost; put a reverse proxy in front).
- Transmitters: TCP `43434` on all interfaces — open it in the firewall.
- Data: `./data/State.json` (+ optional `./data/Settings.json`, see `deploy/Settings.example.json`).

To migrate from a Java core, copy its `State.json` to `./data/` before the first start.

### Apache reverse proxy

See `deploy/apache-dapnet.conf`.

### Connecting a transmitter

1. In the web UI, create the transmitter (callsign + auth key, `A-Z a-z 0-9`) and add it to a transmitter group.
2. On the transmitter (e.g. UniPager), set master host to this server, port `43434`, and the same callsign/auth key.

## Development

```sh
cd backend && uv sync && uv run pytest          # tests: encoding, cron, auth, full TX handshake + API
cd backend && DAPNET_WEB_DIR=../web/dist uv run python -m dapnet
cd web && npm install && npm run dev            # Vite dev server, proxies /api to :8080
```

Environment variables: `DAPNET_SETTINGS`, `DAPNET_STATE_FILE`, `DAPNET_HTTP_HOST`, `DAPNET_HTTP_PORT`,
`DAPNET_TX_PORT`, `DAPNET_NODE_NAME`, `DAPNET_WEB_DIR`, `DAPNET_ADMIN_PASSWORD`, `DAPNET_LOG_LEVEL`,
`DAPNET_ACCESS_LOG`.

## Licence

Derived from DAPNET Core (© 2016 Institut für Hochfrequenztechnik, RWTH Aachen University — Daniel
Sialkowski, Ralf Wilke) and DAPNET Web (MIT, © 2015-2018 DAPNET). The DAPNET Core licence allows
**non-commercial, amateur-radio use only** and requires its notice to be kept. See
`LICENSE-NOTICES.txt`.
