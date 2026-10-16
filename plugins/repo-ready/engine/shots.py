"""README screenshots from a JSON spec, at fixed viewport and device scale.

usage: uv run --no-project --with playwright python shots.py spec.json out-dir [base-url]
       (base-url overrides "base": point it at YOUR server, not one the user may already run on that port)
       (no browser installed? add  "chrome": "/usr/bin/google-chrome"  to the spec, or run `playwright install chromium`)

spec.json:
{
  "base": "http://127.0.0.1:8080",
  "chrome": "/usr/bin/google-chrome",
  "shots": [
    {"name": "home", "path": "/", "width": 1560, "height": 1134, "scale": 1.25},
    {"name": "dialog", "path": "/runs/x", "width": 1200, "height": 1275, "scale": 1.1,
     "steps": [["click_text", "some row"], ["wait", 1500]], "element": ".q-dialog .q-card", "last": true},
    {"name": "nested", "path": "/runs/x", "width": 1200, "height": 1275, "scale": 1.1, "clip": "box",
     "steps": [["click_text", "some row"], ["remember_box", ".q-dialog .q-card"], ["click_button", "Inspect"]]},
    {"name": "filled", "path": "/", "width": 1555, "height": 1302, "scale": 1.1, "full_page": true,
     "steps": [["click_label", "Draft"], ["click_option", "Eval · buy-smarter"], ["click_text", "Advanced"]]}
  ]
}
Steps: click_text <text>, click_label <label>, click_option <name>, click_button <name>, fill <label> <value>,
wait <ms>, remember_box <selector> (box of its last match; "clip": "box" crops the shot to it,
e.g. a nested dialog cropped to its parent card). The mouse moves to the corner before each shot (no hover tint).
Pick width × scale so the PNG matches the old screenshot's pixel size; then the README needs no edits.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SETTLE_MS = 1200
STEP_MS = 600


def do(page, step, memo):
    kind, *args = step
    if kind == "wait":
        page.wait_for_timeout(int(args[0]))
        return
    if kind == "remember_box":
        memo["box"] = page.locator(args[0]).last.bounding_box()
        return
    actions = {
        "click_text": lambda t: page.get_by_text(t, exact=True).first.click(),
        "click_label": lambda t: page.get_by_label(t).first.click(),
        "click_option": lambda t: page.get_by_role("option", name=t, exact=True).click(),
        "click_button": lambda t: page.get_by_role("button", name=t).first.click(),
        "fill": lambda t, v: page.get_by_label(t).first.fill(v),
    }
    actions[kind](*args)
    page.wait_for_timeout(STEP_MS)


def main(spec_path: str, out: str, base: str = "") -> None:
    spec = json.loads(Path(spec_path).read_text())
    base = base or spec["base"]
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(**({"executable_path": spec["chrome"]} if spec.get("chrome") else {}))
        for shot in spec["shots"]:
            ctx = browser.new_context(viewport={"width": shot["width"], "height": shot["height"]},
                                      device_scale_factor=shot.get("scale", 1),
                                      color_scheme=shot.get("theme", "light"))
            page = ctx.new_page()
            page.goto(base + shot.get("path", "/"))
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(SETTLE_MS)
            memo = {}
            for step in shot.get("steps", []):
                do(page, step, memo)
            page.mouse.move(2, 2)
            page.wait_for_timeout(STEP_MS)
            target = out_dir / f"{shot['name']}.png"
            if shot.get("element"):
                loc = page.locator(shot["element"])
                (loc.last if shot.get("last") else loc.first).screenshot(path=target)
            elif shot.get("clip") == "box":
                page.screenshot(path=target, clip=memo["box"])
            else:
                page.screenshot(path=target, full_page=shot.get("full_page", False))
            print(target)
            ctx.close()
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(*sys.argv[1:4])
