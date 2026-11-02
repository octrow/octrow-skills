---
type: llm
focus: files
weight: 1
---

normalize_fast in tags.py now checks that tag ids are non-decreasing and falls back to normalize otherwise. The answer or trace shows a concrete unsorted input where the original normalize_fast was wrong.
