#!/usr/bin/env bash
# Facts for the handoff skill. Usage: handoff.sh [facts]   (run from the project root or any subfolder)
#   (no arg) - the "State" block: branch, last 5 commits, uncommitted and new files
#   facts    - the same with 8 commits, plus .notes/ files with dates and "Next step" of .notes/handoff.md
# Works without git. First run adds .notes/ to .git/info/exclude (not .gitignore).
set -uo pipefail
MODE=${1:-}; N=5; [ "$MODE" = facts ] && N=8
if ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
  EX=$(git rev-parse --path-format=absolute --git-path info/exclude)
  mkdir -p "$(dirname "$EX")"
  grep -qxF '.notes/' "$EX" 2>/dev/null || echo '.notes/' >> "$EX"
else ROOT=$PWD; fi
mkdir -p "$ROOT/.notes"

if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  BR=$(git -C "$ROOT" branch --show-current); [ -n "$BR" ] || BR="(detached HEAD)"
  echo "- Folder: \`$ROOT\`; branch: \`$BR\`"
  echo "- Last commits:"
  git -C "$ROOT" log --oneline -"$N" 2>/dev/null | sed 's/^/  - /' || true
  [ -n "$(git -C "$ROOT" log -1 --format=%h 2>/dev/null)" ] || echo "  - (no commits yet)"
  echo "- Uncommitted: $(git -C "$ROOT" status --porcelain | wc -l) file(s)"
  git -C "$ROOT" status --porcelain | head -10 | sed 's/^/  - /'
else
  echo "- Folder: \`$ROOT\`; not a git repository"
fi

[ "$MODE" = facts ] || exit 0
echo "- Files in .notes/:"
ls -1t --time-style=+%Y-%m-%d -l "$ROOT/.notes" 2>/dev/null | awk 'NR>1{d=$6; sub(/^([^ ]+ +){6}/,""); print "  - " d " " $0}'
H="$ROOT/.notes/handoff.md"
if [ -f "$H" ]; then
  echo "- Next step (from .notes/handoff.md):"
  NEXT=$(awk '/^#+ .*Next step/{f=1;next} /^#+ /{f=0} f&&NF' "$H")
  echo "${NEXT:-(no \"Next step\" heading in the file)}" | sed 's/^/  /'
else echo "- .notes/handoff.md: none"; fi
