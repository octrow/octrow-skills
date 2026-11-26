#!/usr/bin/env bash
# One blocking wait for a GitHub Actions run instead of polling it from the chat.
# Run it in the background (run_in_background): the model is woken once, by the final line.
#
#   ci-wait.sh <repo> <run-id>                 wait for a known run
#   ci-wait.sh <repo> --sha <sha> [workflow]   find the run of a commit (waits up to 5 min for it to appear)
#
# Output: one status line, then only the failed jobs. Exit code = 0 for success.
# Examples:
#   ci-wait.sh owner/repo --sha "$(git rev-parse HEAD)" CI
#   ci-wait.sh owner/repo 1234567890
set -euo pipefail
[ $# -ge 2 ] || { echo "usage: ci-wait.sh <repo> <run-id | --sha SHA [workflow]>"; exit 2; }
REPO=$1; shift
if [ "$1" = "--sha" ]; then
  SHA=${2:?--sha needs a commit sha}; WF=${3:-}
  for _ in $(seq 30); do   # ponytail: 30 x 10 s; raise if runners queue longer
    ID=$(gh run list -R "$REPO" --commit "$SHA" ${WF:+--workflow "$WF"} -L 1 --json databaseId --jq '.[0].databaseId // empty')
    [ -n "$ID" ] && break
    sleep 10
  done
  [ -n "${ID:-}" ] || { echo "no run for $SHA in $REPO after 5 min"; exit 3; }
else
  ID=$1
fi
gh run watch "$ID" -R "$REPO" --interval 30 --exit-status >/dev/null 2>&1 && RC=0 || RC=$?
gh run view "$ID" -R "$REPO" --json name,conclusion,headBranch,headSha,url,jobs --jq \
  '"\(.name): \(.conclusion) | \(.headBranch) \(.headSha[0:9]) | \(.url)",
   (.jobs[] | select(.conclusion != "success" and .conclusion != "skipped") | "  FAILED \(.name) (job \(.databaseId))")'
exit "$RC"
