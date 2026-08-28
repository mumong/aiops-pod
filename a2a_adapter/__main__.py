"""Run the standalone A2A adapter with uvicorn."""

import logging
import os

import uvicorn

from a2a_adapter.config import AdapterSettings


def main() -> None:
    settings = AdapterSettings.from_env()
    log_level = os.getenv("LOG_LEVEL", "INFO").lower()
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    uvicorn.run(
        "a2a_adapter.app:app",
        host=settings.host,
        port=settings.port,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()
