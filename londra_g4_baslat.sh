#!/usr/bin/env bash
set -euo pipefail
ssh -T -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8 -i "/home/taygun/İndirilenler/polymarket-test-key2.pem" ubuntu@18.135.99.14 "tmux new-session -d -s bosona-g4 'exec /home/ubuntu/polymarket/venv/bin/python -u /home/ubuntu/polymarket-bosona-g-continuous/staging/g4/g4_operator.py --operator-start >> /home/ubuntu/polymarket-bosona-g-continuous/staging/g4/G4_operator.console.log 2>&1'"
printf '%s\n' 'G4 istendi: normal G3 kapanisi -> tam hesap teyidi -> G4 icin yeni $100 zarar butcesi.' '5 pay/emir, net en fazla 10 pay, sinirsiz sure. Ayni G4 tekrarinda butce sifirlanmaz.' 'Kayit: /home/ubuntu/polymarket-bosona-g-continuous/staging/g4/G4_operator.console.log' 'LIVE basladi kaydi ayrica teyit edilmeli.'
