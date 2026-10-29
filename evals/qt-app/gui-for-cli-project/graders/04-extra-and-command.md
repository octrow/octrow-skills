---
type: llm
focus: trace
weight: 1
---

pyproject.toml gains an optional gui extra with PySide6-Essentials (not the full PySide6) and qtawesome, and the greenkeep CLI gains a gui command that imports Qt lazily with a hint when the extra is missing.
