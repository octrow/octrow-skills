#!/usr/bin/env python3
"""Read-only facts for lean-spec: toolchain, sandbox, agent tooling, project language.

Prints one `name: value` line per fact, then `install:` lines for what is missing.
Exit 1 on macOS (not supported) or when a hard requirement (lake, bwrap) is missing, else 0.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PINNED_LEAN = "4.35.0"  # the example and its proofs are checked on this version
HOME = Path.home()
# Another target is frozen there: copying the template over it would reset Frozen.lean.
EXISTING_LEAN = "lean/ (exists: add a target next to it, never copy the template over it)"
INSTALL = {
    "lake": "curl -sSfL https://elan.lean-lang.org/elan-init.sh | sh -s -- -y "
    f"--default-toolchain leanprover/lean4:v{PINNED_LEAN}  # then add ~/.elan/bin to PATH",
    "bwrap": "sudo apt install bubblewrap  # lake comparator runs the build in a bwrap sandbox",
    "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
    "lean-lsp-mcp": "claude mcp add lean-lsp -s project uvx lean-lsp-mcp",
    "lean4-skills": "/plugin marketplace add cameronfreer/lean4-skills, then /plugin install lean4",
}
LANG_MARKERS = {
    "python": ("pyproject.toml", "requirements.txt", "setup.py"),
    "go": ("go.mod",),
    "rust": ("Cargo.toml",),
    "typescript": ("package.json",),
}


def which(tool: str) -> str | None:
    found = shutil.which(tool)
    if found:
        return found
    elan_bin = HOME / ".elan" / "bin" / tool
    return str(elan_bin) if elan_bin.exists() else None


def lean_version(lake: str) -> str:
    lean = Path(lake).with_name("lean")
    try:
        out = subprocess.run([lean, "--version"], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"unknown ({exc})"
    return out.split("version ")[1].split(",")[0] if "version " in out else out.strip()


def config_dir() -> Path:
    """Claude Code's config root: CLAUDE_CONFIG_DIR when set (profiles), else ~/.claude."""
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or HOME / ".claude")


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def lean4_skills_installed() -> bool:
    data = read_json(config_dir() / "plugins" / "installed_plugins.json")
    return any(key.startswith("lean4@") for key in data.get("plugins", data))


def lean_lsp_configured(root: Path) -> bool:
    """Project scope (.mcp.json), then user and local scope for this repo; another project's setup does not count."""
    if "lean-lsp" in read_json(root / ".mcp.json").get("mcpServers", {}):
        return True
    state_file = config_dir() / ".claude.json" if os.environ.get("CLAUDE_CONFIG_DIR") else HOME / ".claude.json"
    state = read_json(state_file)
    this_project = state.get("projects", {}).get(str(root.resolve()), {})
    return any("lean-lsp" in scope.get("mcpServers", {}) for scope in (state, this_project))


def facts(root: Path) -> tuple[dict[str, str], list[str]]:
    """All facts plus the names of missing pieces (keys of INSTALL)."""
    found = {**toolchain_facts(), **agent_facts(root), **project_facts(root)}
    missing = [name for name in INSTALL if found.get(name, "").startswith("missing")]
    return found, missing


def toolchain_facts() -> dict[str, str]:
    found = {tool: which(tool) or "missing" for tool in ("lake", "bwrap", "uv")}
    if found["lake"] != "missing" and not shutil.which("lake"):
        found["lake_on_path"] = 'no: start shell commands with export PATH="$HOME/.elan/bin:$PATH"'
    if found["lake"] != "missing":
        version = lean_version(found["lake"])
        drift = "" if version == PINNED_LEAN else f" (example is checked on {PINNED_LEAN}; API drift is likely)"
        found["lean_version"] = version + drift
    return found


def agent_facts(root: Path) -> dict[str, str]:
    return {
        "lean-lsp-mcp": "configured" if lean_lsp_configured(root) else "missing",
        "lean4-skills": "installed" if lean4_skills_installed() else "missing (optional)",
    }


def project_facts(root: Path) -> dict[str, str]:
    langs = [lang for lang, files in LANG_MARKERS.items() if any((root / f).exists() for f in files)]
    return {
        "project_language": ", ".join(langs) or "unknown",
        "lean_project": EXISTING_LEAN if (root / "lean" / "lakefile.toml").exists() else "none yet",
    }


def main() -> int:
    if sys.platform == "darwin":
        print("platform: macOS is not supported: lake comparator builds inside bubblewrap, which is Linux only")
        return 1
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    found, missing = facts(root)
    for name, value in found.items():
        print(f"{name}: {value}")
    for name in missing:
        print(f"install {name}: {INSTALL[name]}")
    return 1 if {"lake", "bwrap"} & set(missing) else 0


if __name__ == "__main__":
    sys.exit(main())
