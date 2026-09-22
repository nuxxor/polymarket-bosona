#!/usr/bin/env bash
# Operator executes the graceful stop, verified source update and same-budget resume.
set -euo pipefail
ssh -T -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8 -i "/home/taygun/İndirilenler/polymarket-test-key2.pem" ubuntu@18.135.99.14 "tmux new-session -d -s bosona-g-fix999 'exec /home/ubuntu/polymarket/venv/bin/python -u /home/ubuntu/g-identity-fix-20260922/operator_resume.py --operator-restart >> /home/ubuntu/g-identity-fix-20260922/operator.console.log 2>&1'"
printf '%s\n' 'G: normal durus -> 999 yamasi -> hesap teyidi -> ayni butceyle devam istendi.' 'Yeni $10 acilmaz. Kayit: /home/ubuntu/g-identity-fix-20260922/operator.console.log' 'LIVE basladi kaydi ayrica teyit edilmeli.'
