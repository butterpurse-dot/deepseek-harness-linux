#!/usr/bin/env bash
# Update the review queue issue, then address any new external review comments.
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 scripts/track_external_prs.py || echo "run-pr-agent: queue update failed; continuing" >&2
exec python3 scripts/pr_agent.py
