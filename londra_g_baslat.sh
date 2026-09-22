#!/usr/bin/env bash
# Operator: one 30-minute G1 pilot, 5 shares, new $10 budget only on this command.
set -euo pipefail
ssh -T -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8 -i "/home/taygun/İndirilenler/polymarket-test-key2.pem" ubuntu@18.135.99.14 "tmux new-session -d -s bosona-g 'exec /home/ubuntu/polymarket/venv/bin/python -u /home/ubuntu/polymarket-bosona-g-v2/bot/pilot.py --live >> /home/ubuntu/polymarket-bosona-g-v2/bot/console.log 2>&1'"
printf '%s\n' 'G1 baslatma istendi: 30 dakika / 5 pay / $10. Hesap ve iki kayitci kontrolunden sonra LIVE baslar.' 'Kayit: /home/ubuntu/polymarket-bosona-g-v2/bot/console.log; LIVE basladi ayrica teyit edilmeli.'
