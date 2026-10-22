import logging
import time

log = logging.getLogger("worker")


def fetch(job: dict) -> str:
    log.info("fetching %s", job["url"])
    if "bad" in job["url"]:
        raise ConnectionError("timeout")
    return "<html>" + "x" * 5000


def summarize(text: str) -> str:
    log.info("summarizing %d chars", len(text))
    return text[:100]


def handle(job: dict) -> None:
    log.info("job %s start", job["id"])
    page = fetch(job)
    log.debug("page body: %s", page)
    summary = summarize(page)
    log.info("job %s summary: %s", job["id"], summary)
    log.info("job %s done", job["id"])


def run(queue: list[dict]) -> None:
    logging.basicConfig(level=logging.DEBUG)
    for job in queue:
        t0 = time.time()
        try:
            handle(job)
        except Exception as exc:
            log.error("job failed: %s", exc)
        log.info("took %.2f", time.time() - t0)


if __name__ == "__main__":
    run([{"id": 1, "url": "https://ok.example"}, {"id": 2, "url": "https://bad.example"},
         {"id": 3, "user": "u7", "url": "https://ok.example/2"}])
