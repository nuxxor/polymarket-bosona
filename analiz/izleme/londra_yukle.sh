#!/bin/bash
# LONDRA'YA YUKLE: yerel ab.py + ONKAYIT -> sunucu; STOP ile temiz kapat; yeniden baslat; dogrula.
set -u
<SSH-ANAHTARI>; H=ubuntu@<LONDRA-SUNUCU-IP>
L=/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5
R=/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5
cd $L && python3 -m py_compile ab.py || { echo "DERLENMEDI, yukleme iptal"; exit 1; }
scp -q -i "$K" $L/ab.py $L/ONKAYIT_*.md $H:$R/ && echo "kopyalandi $(date -u +%H:%M:%SZ)"
ssh -i "$K" $H "cd $R && touch STOP && for i in \$(seq 1 45); do pgrep -x python -a | grep -q 'ab.py --live' || break; sleep 2; done; pgrep -x python -a | grep -q 'ab.py --live' && echo 'DURMADI' || echo 'durdu'; rm -f STOP; grep '\"k\": \"bitti\"' LOG_ab.jsonl | tail -1 | cut -c1-120; (setsid nohup ~/polymarket/venv/bin/python ab.py --live >> canli.out 2>&1 < /dev/null &); sleep 30; pgrep -x python -a | grep 'ab.py --live' | head -1; grep -E '\"k\": \"(SURUM|basladi|BASLAMIYOR)\"' LOG_ab.jsonl | tail -2 | cut -c1-140; tail -2 canli.out | cut -c1-120"
