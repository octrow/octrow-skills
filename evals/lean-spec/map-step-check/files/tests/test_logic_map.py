import re
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_module_lines_point_to_real_modules():
    text = (ROOT / "docs/logic-map.md").read_text(encoding="utf-8")
    for module in re.findall(r"^Module: `([^`]+)`", text, flags=re.M):
        assert (ROOT / f"{module}.py").exists(), module
