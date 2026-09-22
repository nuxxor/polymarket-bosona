#!/usr/bin/env bash
# The operator executes graceful G2 shutdown, verified G3 update and same-budget resume.
set -euo pipefail
ssh -T -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8 -i "/home/taygun/İndirilenler/polymarket-test-key2.pem" ubuntu@18.135.99.14 "tmux new-session -d -s bosona-g3 'exec /home/ubuntu/polymarket/venv/bin/python -u /home/ubuntu/polymarket-bosona-g-continuous/staging/g3/g3_operator.py --operator-restart >> /home/ubuntu/polymarket-bosona-g-continuous/staging/g3/G3_operator.console.log 2>&1'"
printf '%s\n' 'G3 istendi: normal G2 kapanisi -> hesap teyidi -> ayni butceyle G2/G3 karsilastirmasi.' '5 pay / sinirsiz sure; yeni $10 acilmaz. Butce tukenmisse baslamaz.' 'Kayit: /home/ubuntu/polymarket-bosona-g-continuous/staging/g3/G3_operator.console.log' 'LIVE basladi kaydi ayrica teyit edilmeli.'
