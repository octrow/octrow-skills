#!/usr/bin/env python3
"""Audit a README: local images, SVG basics, length budget and plain-language rules."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NamedTuple

MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\(((?:[^()\s]|\([^()\s]*\))+)(?:\s+[^)]*)?\)")  # one level of () in the URL
HTML_IMAGE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)
HTML_ALT = re.compile(r"\balt=[\"']([^\"']*)[\"']", re.IGNORECASE)
UNSAFE_SVG_TAGS = {"script", "foreignObject"}

# Budgets from references/plain-language.md and SKILL.md "Length budget".
MAX_README_LINES = 150
MAX_FIRST_SCREEN_LINES = 25
MAX_SECTION_LINES = 20
MAX_PARAGRAPH_LINES = 5
MAX_PARAGRAPH_WORDS = 60
MAX_SENTENCE_WORDS = 25
MAX_LIST_ITEMS = 7
MAX_BADGES = 5
MAX_BOLD_LABELS = 2

# Word tiers after conorbronsdon/avoid-ai-writing (references/patterns.md), plus README hype and Russian.
# FILLER: flag every hit. CLUSTER: normal alone, flag when 2+ different ones share a paragraph.
FILLER = re.compile(
    r"\b(?:powerful|blazing(?:ly)?[- ]fast|next[- ]generation|state[- ]of[- ]the[- ]art|best[- ]in[- ]class"
    r"|world[- ]class|revolutionary|effortless(?:ly)?|hassle[- ]free"
    r"|delve|landscape|tapestry|realm|paradigm|embark|testament to|robust|comprehensive|cutting[- ]edge"
    r"|leverag\w*|pivotal|underscores|meticulous(?:ly)?|seamless(?:ly)?|game[- ]chang\w*|showcasing"
    r"|deep dive|dive into|intricac\w*|ever[- ]evolving|holistic(?:ally)?|actionable|impactful|at its core"
    r"|synerg\w*|interplay|genuinely|load-bearing"
    r"|utiliz\w*|in order to|due to the fact that|serves as|boasts|commence|ascertain|endeavou?r"
    r"|whether you'?re|look no further|in today'?s|it'?s worth noting|happy coding|the future looks bright"
    r"|мощн\w*|инновационн\w*|осуществ\w*|реализаци\w*|в рамках|на предмет|многое другое|является)\b",
    re.IGNORECASE,
)
CLUSTER = re.compile(
    r"\b(?:harness\w*|navigat\w*|foster\w*|elevat\w*|unleash\w*|unlock\w*|streamlin\w*|empower\w*|bolster\w*"
    r"|spearhead\w*|resonat\w*|revolutioniz\w*|facilitat\w*|underpin\w*|nuanced|crucial|multifaceted|ecosystem"
    r"|myriad|plethora|encompass\w*|reimagin\w*|transformative|cornerstone|paramount|poised|overarching"
    r"|supercharg\w*|very|truly|extremely|highly|fully|various|several"
    r"|очень|максимальн\w*|полностью|окончательно|различн\w*|некотор\w*|эффективн\w*|удобн\w*)\b",
    re.IGNORECASE,
)
CONTRAST = re.compile(r"\b(?:not (?:just|only|merely)|isn'?t (?:just|only)|не (?:просто|только))\b", re.IGNORECASE)
DASH = re.compile(r"[\u2013\u2014]")
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50\u2B55]")
CAPS = re.compile(r"\b(?:IMPORTANT|WARNING|ВАЖНО|ВНИМАНИЕ)\b|\b[A-ZА-ЯЁ]{4,}(?:\s+[A-ZА-ЯЁ]{4,})+\b")
LIST_ITEM = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+")
BOLD_LABEL = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*[^*]+(?::\*\*|\*\*:)")
BADGE = re.compile(r"shields\.io|badge", re.IGNORECASE)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
LINE_CHECKS = (
    (CONTRAST, "'not just X' framing"),
    (DASH, "long dash, use '-'"),
    (EMOJI, "emoji in text"),
    (CAPS, "caps for emphasis"),
)


def local_target(src: str, base: Path) -> Path | None:
    if src.startswith(("http://", "https://", "data:", "#")):
        return None
    clean = src.split("#", 1)[0].split("?", 1)[0]
    return (base / clean).resolve()


def audit_svg(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"invalid SVG XML: {exc}"]

    if "viewBox" not in root.attrib:
        issues.append("missing viewBox")

    title_found = False
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag == "title":
            title_found = True
        if tag in UNSAFE_SVG_TAGS:
            issues.append(f"contains unsupported <{tag}>")
    if not title_found:
        issues.append("missing <title>")
    return issues


def audit_images(text: str, base: Path) -> tuple[int, list[str]]:
    sources = MARKDOWN_IMAGE.findall(text) + HTML_IMAGE.findall(text)
    warnings: list[str] = []
    for tag in re.findall(r"<img\b[^>]*>", text, flags=re.IGNORECASE):
        match = HTML_ALT.search(tag)
        if not match or not match.group(1).strip():
            warnings.append(f"HTML image missing useful alt text: {tag[:100]}")

    checked = 0
    for src in dict.fromkeys(sources):
        target = local_target(src, base)
        if target is None:
            continue
        checked += 1
        if not target.is_file():
            warnings.append(f"missing image: {src}")
        elif target.suffix.lower() == ".svg":
            warnings.extend(f"{src}: {issue}" for issue in audit_svg(target))
    badges = sum(1 for src in sources if BADGE.search(src))
    if badges > MAX_BADGES:
        warnings.append(f"{badges} badges, keep at most {MAX_BADGES}")
    return checked, warnings


class Row(NamedTuple):
    """One README line outside code fences and HTML comments."""

    no: int
    kind: str  # blank, fence (opening ``` of a code block), heading, list, table, quote, html, image, prose
    line: str
    folded: bool  # inside <details>


def classify(text: str) -> list[Row]:
    rows = []
    in_code = in_comment = folded = False
    for no, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith(("```", "~~~")):
            in_code = not in_code
            if in_code:
                rows.append(Row(no, "fence", line, folded))
            continue
        if in_code:
            continue
        if in_comment or s.startswith("<!--"):
            in_comment = "-->" not in s
            continue
        if s.lower().startswith("<details"):
            folded = True
        if s.lower().startswith("</details"):
            folded = False
        rows.append(Row(no, line_kind(line), line, folded))
    return rows


def line_kind(line: str) -> str:
    s = line.strip()
    if not s:
        return "blank"
    if s.startswith("#"):
        return "heading"
    if LIST_ITEM.match(line):
        return "list"
    if s.startswith("|"):
        return "table"
    if s.startswith(">"):
        return "quote"
    if MARKDOWN_IMAGE.fullmatch(s) or s.startswith(("[![", "<img")):
        return "image"
    if s.startswith("<"):
        return "html"
    return "prose"


def plain(line: str) -> str:
    """Drop inline code, link targets and image markup so word checks see only prose."""
    line = re.sub(r"`[^`]*`", "x", line)
    line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)
    line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
    return re.sub(r"\[!\w+\]", "", line)


def audit_words(rows: list[Row]) -> list[str]:
    warnings = []
    for block in text_blocks(rows):
        for row in block:
            issues = line_issues(plain(row.line))
            if row.kind != "prose":
                issues += list_issues(plain(row.line))
            warnings.extend(f"L{row.no}: {msg}" for msg in issues)
        prose = " ".join(plain(row.line) for row in block if row.kind == "prose")
        if any(len(s.split()) > MAX_SENTENCE_WORDS for s in SENTENCE_END.split(prose)):
            warnings.append(f"L{block[0].no}: sentence over {MAX_SENTENCE_WORDS} words")
        cluster = sorted({m.group(0).lower() for row in block for m in CLUSTER.finditer(plain(row.line))})
        if len(cluster) >= 2:
            warnings.append(f"L{block[0].no}: filler cluster: {', '.join(cluster)}")
    return warnings


def text_blocks(rows: list[Row]) -> list[list[Row]]:
    """Runs of consecutive text rows: a paragraph, a list, a table, a heading."""
    blocks: list[list[Row]] = [[]]
    for row in rows:
        if row.kind in ("blank", "fence", "image", "html"):
            blocks.append([])
        else:
            blocks[-1].append(row)
    return [b for b in blocks if b]


def line_issues(text: str) -> list[str]:
    issues = []
    hits = sorted({m.group(0).lower() for m in FILLER.finditer(text)})
    if hits:
        issues.append(f"filler: {', '.join(hits)}")
    issues.extend(msg for rx, msg in LINE_CHECKS if rx.search(text))
    return issues


def list_issues(text: str) -> list[str]:
    """A list item is its own sentence run; prose sentences are checked per paragraph."""
    sentences = SENTENCE_END.split(LIST_ITEM.sub("", text))
    if any(len(s.split()) > MAX_SENTENCE_WORDS for s in sentences):
        return [f"sentence over {MAX_SENTENCE_WORDS} words"]
    return []


def audit_bold_labels(rows: list[Row]) -> list[str]:
    labels = sum(1 for row in rows if row.kind == "list" and BOLD_LABEL.match(row.line))
    if labels > MAX_BOLD_LABELS:
        return [f"{labels} list items start with a bold label, drop the labels"]
    return []


def audit_blocks(rows: list[Row]) -> list[str]:
    """Paragraph and list size: runs of consecutive prose lines or list items."""
    warnings = []
    run: list[Row] = []
    for row in [*rows, Row(0, "blank", "", False)]:
        if run and row.kind != run[0].kind:
            check = audit_list if run[0].kind == "list" else audit_paragraph
            warnings.extend(check(run))
            run = []
        if row.kind in ("prose", "list"):
            run.append(row)
    return warnings


def audit_list(items: list[Row]) -> list[str]:
    nested = [row for row in items if LIST_ITEM.match(row.line).group(1)]
    warnings = [f"L{nested[0].no}: nested list"] if nested else []
    top = len(items) - len(nested)
    if top > MAX_LIST_ITEMS:
        warnings.append(f"L{items[0].no}: list of {top} items, keep at most {MAX_LIST_ITEMS}")
    return warnings


def audit_paragraph(lines: list[Row]) -> list[str]:
    words = sum(len(plain(row.line).split()) for row in lines)
    if len(lines) <= MAX_PARAGRAPH_LINES and words <= MAX_PARAGRAPH_WORDS:
        return []
    size = f"paragraph of {len(lines)} lines / {words} words"
    return [f"L{lines[0].no}: {size}, keep {MAX_PARAGRAPH_LINES} lines / {MAX_PARAGRAPH_WORDS} words"]


def audit_budget(rows: list[Row]) -> list[str]:
    """Whole-README and first-screen budgets; <details> content does not count."""
    counted = [row for row in rows if row.kind not in ("blank", "fence") and not row.folded]
    warnings = []
    if len(counted) > MAX_README_LINES:
        warnings.append(f"README has {len(counted)} lines outside code, budget {MAX_README_LINES}")
    first_fence = next((row.no for row in rows if row.kind == "fence"), None)
    if first_fence:
        before = sum(1 for row in counted if row.no < first_fence)
        if before > MAX_FIRST_SCREEN_LINES:
            warnings.append(f"{before} lines before the first command, budget {MAX_FIRST_SCREEN_LINES}")
    return warnings


def audit_sections(rows: list[Row]) -> list[str]:
    warnings = []
    heading, size = None, 0
    for row in [*rows, Row(0, "heading", "## end", False)]:
        if row.folded:
            continue
        if row.kind == "heading" and row.line.startswith("## "):
            if heading and size > MAX_SECTION_LINES:
                name = heading.line[3:].strip()
                warnings.append(f"L{heading.no}: section '{name}' has {size} lines, budget {MAX_SECTION_LINES}")
            heading, size = row, 0
        elif row.kind in ("prose", "list", "quote", "table"):
            size += 1
    return warnings


def length_issues(text: str) -> list[str]:
    """Length budget: whole README, first screen, sections, paragraphs and lists."""
    rows = classify(text)
    return audit_budget(rows) + audit_sections(rows) + audit_blocks(rows)


def wording_issues(text: str) -> list[str]:
    """Plain-language rules: filler, contrast framing, dashes, emoji, caps, long sentences, bold labels."""
    rows = classify(text)
    return audit_words(rows) + audit_bold_labels(rows)


def audit_text(text: str) -> list[str]:
    return length_issues(text) + wording_issues(text)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: readme_audit.py /path/to/README.md", file=sys.stderr)
        return 2

    readme = Path(sys.argv[1]).expanduser().resolve()
    if not readme.is_file():
        print(f"ERROR: README not found: {readme}")
        return 2

    text = readme.read_text(encoding="utf-8")
    checked, image_warnings = audit_images(text, readme.parent)
    text_warnings = audit_text(text)

    print(f"README: {readme}")
    print(f"Local images checked: {checked}")
    for title, warnings in (("Image issues", image_warnings), ("Text issues", text_warnings)):
        if warnings:
            print(f"{title}:")
            print("\n".join(f"- {w}" for w in warnings))
    if image_warnings or text_warnings:
        return 1
    print("OK: images, length budget and text rules passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
