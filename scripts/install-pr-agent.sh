#!/usr/bin/env bash
# Install the PR review agent as a user systemd timer.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR="$HOME/.config/dsh-pr-agent"
ENV_FILE="$ENV_DIR/env"
UNIT_DIR="$HOME/.config/systemd/user"
STATE_DIR="$HOME/.local/state/dsh-pr-agent"

mkdir -p "$ENV_DIR" "$UNIT_DIR" "$STATE_DIR"

if [ ! -f "$ENV_FILE" ]; then
  token="$(gh auth token 2>/dev/null || true)"
  key="${DEEPSEEK_API_KEY:-}"
  if [ -z "$key" ] && [ -f "$HOME/.profile" ]; then
    key="$(grep -E '^export DEEPSEEK_API_KEY=' "$HOME/.profile" | tail -1 | cut -d= -f2- | tr -d '"' || true)"
  fi
  [ -n "$token" ] || { echo "install-pr-agent: gh auth token is unavailable" >&2; exit 1; }
  [ -n "$key" ] || { echo "install-pr-agent: DEEPSEEK_API_KEY is unavailable" >&2; exit 1; }
  cat > "$ENV_FILE" <<EOF
GH_TOKEN=$token
DEEPSEEK_API_KEY=$key
DSH_PR_AGENT_ACCOUNT=${DSH_PR_AGENT_ACCOUNT:-butterpurse-dot}
DSH_PR_AGENT_REPOS=${DSH_PR_AGENT_REPOS:-}
DSH_BIN=$(command -v dsh)
EOF
  chmod 600 "$ENV_FILE"
  echo "install-pr-agent: wrote $ENV_FILE"
fi

cat > "$UNIT_DIR/dsh-pr-agent.service" <<EOF
[Unit]
Description=Address review comments on external pull requests
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$REPO_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$REPO_DIR/scripts/run-pr-agent.sh
Nice=10
TimeoutStartSec=1800
EOF

cat > "$UNIT_DIR/dsh-pr-agent.timer" <<'EOF'
[Unit]
Description=Run the PR review agent every five minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=2min
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now dsh-pr-agent.timer
loginctl enable-linger "$USER" 2>/dev/null || sudo loginctl enable-linger "$USER"

echo "install-pr-agent: timer enabled"
systemctl --user list-timers dsh-pr-agent.timer --no-pager
