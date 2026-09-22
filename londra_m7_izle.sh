#!/usr/bin/env bash
# Yalniz veri: emir/pilot baslatmaz, butce olusturmaz.
set -euo pipefail
ssh -T -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8 -i "/home/taygun/İndirilenler/polymarket-test-key2.pem" ubuntu@18.135.99.14 bash -s <<'REMOTE'
set -euo pipefail
cd /home/ubuntu/polymarket-bosona-m7-v3
sha256sum -c /home/ubuntu/polymarket-bosona-m7-v3/SHA256SUMS
test ! -e /home/ubuntu/polymarket-bosona-m7-v3/capture/STOP_M7
tmux new-session -d -s bosona-m7-observe 'exec /home/ubuntu/polymarket/venv/bin/python -u /home/ubuntu/polymarket-bosona-m7-v3/stream_iz.py --credentials "/home/taygun/Masaüstü/polymarket/.env.live" --out /home/ubuntu/polymarket-bosona-m7-v3/capture --seconds 2100 >> /home/ubuntu/polymarket-bosona-m7-v3/console.log 2>&1'
printf '%s\n' 'M7: 35 dakikalik salt-okunur kayit istendi. Islem botu baslatilmadi.'
REMOTE
