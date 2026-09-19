#!/bin/bash
# TR -> LONDRA GECIS: yerel botu STOP ile kapat, state+log'u tasi, sunucuda baslat.
set -u
K=~/İndirilenler/polymarket-test-key2.pem; H=ubuntu@18.135.99.14
L=/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5
R=/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5
P=$(ps -eo pid,args | grep "python3 ab.py --live" | grep -v grep | awk '{print $1}')
echo "yerel PID: $P  $(date -u +%H:%M:%SZ)"
touch $L/STOP
for i in $(seq 1 60); do ps -p $P >/dev/null 2>&1 || break; sleep 2; done
ps -p $P >/dev/null 2>&1 && { echo "YEREL BOT DURMADI, GECIS IPTAL"; exit 1; }
rm -f $L/STOP
echo "yerel durdu $(date -u +%H:%M:%SZ)"; grep '"k": "bitti"' $L/LOG_ab.jsonl | tail -1 | cut -c1-160
# kuru kosu artiklarini temizle, state+log tasi
ssh -i "$K" $H "pkill -f 'etiket kuruL' 2>/dev/null; rm -f $R/STOP; true"
scp -q -i "$K" $L/STATE_ab.json $L/LOG_ab.jsonl $H:$R/ && echo "state+log tasindi ($(wc -l < $L/LOG_ab.jsonl) satir)"
ssh -i "$K" $H "cd $R && (setsid nohup ~/polymarket/venv/bin/python ab.py --live >> canli.out 2>&1 < /dev/null &) && sleep 25 && pgrep -f 'ab.py --live' | head -1 && grep -E '\"k\": \"(SURUM|basladi|BASLAMIYOR|acilis_tekrar)\"' LOG_ab.jsonl | tail -3 | cut -c1-140"
