import logging
import time
from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler("logs/app.log", when="midnight", backupCount=30)
logging.basicConfig(level=logging.DEBUG, handlers=[handler])
log = logging.getLogger(__name__)


def poll() -> None:
    while True:
        try:
            data = {"items": list(range(1000))}
            log.debug("fetched %s", data)
            print("polled", len(data["items"]))
        except Exception as exc:
            log.error("poll failed: %s", exc)
        time.sleep(1)


if __name__ == "__main__":
    poll()
