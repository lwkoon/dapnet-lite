import logging
import os

import uvicorn

from . import config
from .app import create_app


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("DAPNET_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    settings = config.load()
    uvicorn.run(
        create_app(settings),
        host=settings.rest_host,
        port=settings.rest_port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        access_log=os.environ.get("DAPNET_ACCESS_LOG", "0") == "1",
        log_config=None,
        server_header=False,
    )


if __name__ == "__main__":
    main()
