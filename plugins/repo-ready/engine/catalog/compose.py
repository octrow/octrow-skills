"""Compose stack pack: the whole stack on one machine."""
import re

from registry import COMPOSE, check, judgement, read, tracked

DEP = {"deploy"}
INFRA_PORTS = {"5432": "PostgreSQL", "3306": "MySQL", "6379": "Redis", "27017": "MongoDB", "9200": "Elasticsearch",
               "5672": "RabbitMQ", "11211": "Memcached"}
OPEN_IPS = ("", "0.0.0.0", "::")


def compose_files() -> dict[str, str]:
    return {f: read(f) for f in tracked() if COMPOSE.search(f)}


def port_specs(text: str) -> list[str]:
    """Short-syntax entries under every `ports:` key, block or flow style, without quotes and comments."""
    out, indent = [], None
    for line in text.splitlines():
        line = re.sub(r"\s+#.*$", "", line)
        key = re.match(r"^(\s*)ports:\s*(\[.*\])?\s*$", line)
        if key:
            indent = None if key.group(2) else len(key.group(1))
            out += [v.strip(" \"'") for v in (key.group(2) or "").strip("[]").split(",") if v.strip()]
            continue
        item = re.match(r"^(\s*)-\s*(\S.*)$", line)
        if indent is not None and item and len(item.group(1)) >= indent:
            out.append(item.group(2).strip("\"'"))
        elif line.strip() and indent is not None and len(line) - len(line.lstrip()) <= indent:
            indent = None
    return out


def exposure(spec: str) -> tuple[str, str] | None:
    """(host ip, container port) of a short-syntax port, defaults of `${VAR:-x}` filled in; None if unreadable."""
    spec = re.sub(r"\$\{[^}:]+:-([^}]*)\}", r"\1", spec).split("/")[0]
    if "$" in spec or "target:" in spec:
        return None  # ponytail: a variable without a default and the long syntax aren't judged
    ip, _, rest = spec[1:].partition("]:") if spec.startswith("[") else ("", "", spec)
    parts = rest.split(":")
    if len(parts) == 3:
        ip, parts = parts[0], parts[1:]
    return ip, parts[-1]


@check("compose_infra_ports", severity="warning", when=("compose",), scenarios=DEP, kind="files",
       why="a bare `5432:5432` publishes the database on every interface, past ufw, to the internet on a VPS",
       procedure="compose.md#infrastructure-ports")
def compose_infra_ports() -> list[str]:
    out = []
    for f, t in compose_files().items():
        for spec in port_specs(t):
            seen = exposure(spec)
            if seen and seen[1] in INFRA_PORTS and seen[0] in OPEN_IPS:
                out.append(f"{f}: {INFRA_PORTS[seen[1]]} on `{spec}`; bind it as `127.0.0.1:<host>:{seen[1]}`")
    return out


judgement("compose_up_wait", severity="warning", when=("compose",), scenarios=DEP,
          question="Does `docker compose up -d --build --wait` from scratch bring every service to healthy, with "
                   "migrations as a one-shot service the app waits for?",
          procedure="compose.md#stack-layout")
