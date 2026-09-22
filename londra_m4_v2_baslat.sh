#!/usr/bin/env bash
# Operator: 30 dakika, 5 pay, $10 yeni olcum butcesi; bir kez kullanilabilir.
set -euo pipefail
ssh -T -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8 -i "/home/taygun/İndirilenler/polymarket-test-key2.pem" ubuntu@18.135.99.14 "tmux new-session -d -s bosona-m4-v2 'exec /home/ubuntu/polymarket/venv/bin/python -u /home/ubuntu/polymarket-bosona-m4-v2/bot/m4.py --live >> /home/ubuntu/polymarket-bosona-m4-v2/bot/console.log 2>&1'"
printf '%s\n' 'M4v2 baslatma istendi: 30 dakika / 5 pay / $10. Hesap onkontrolunden sonra LIVE baslar.' 'Kayit: /home/ubuntu/polymarket-bosona-m4-v2/bot/console.log; LIVE basladi ayrica teyit edilmeli.'
