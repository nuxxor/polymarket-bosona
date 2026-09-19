#!/bin/bash
# polymarket-bosona deposunu guncelle: kopyala -> maskele -> commit -> push.  Kullanim: depo_senkron.sh "mesaj"
set -u
SRC=/home/taygun/Masaüstü/polymarket; DST=/home/taygun/Masaüstü/polymarket-bosona
B=$SRC/data/analysis/pm_merdiven_ab_20260918_v5; MEM=/home/taygun/.claude/projects/-home-taygun-Masa-st--polymarket/memory
SP=/tmp/claude-1000/-home-taygun-Masa-st--polymarket/0e095c2e-d109-4b41-8066-a0b2005c3a13/scratchpad
MSG=${1:-"senkron $(date -u +%Y-%m-%d_%H:%MZ)"}
cp $B/ab.py $DST/bot/ab.py; cp $B/ONKAYIT_*.md $DST/bot/
cp $B/STATE_ab.json $B/LOG_ab.jsonl $B/canli.out $DST/bot/ 2>/dev/null; cp $B/LOG_ab_kuru*.jsonl $B/kuru*.out $DST/bot/ 2>/dev/null
cp $B/ab.py.bak_* $DST/bot/arsiv/ 2>/dev/null
cp $SRC/scripts/izleme/*.py $SRC/scripts/izleme/*.sh $DST/analiz/izleme/ 2>/dev/null
cp $SRC/scripts/record_polymarket_orderbook.py $SRC/scripts/record_fills_tape.py $SRC/scripts/record_btc_tape.py $SRC/scripts/collect_chainlink_rtds.py $DST/kaydediciler/
cp $SRC/data/analysis/pm_chainlink_history_20260913_v1/cl_direct_rec.py $DST/kaydediciler/chainlink/
cp $SP/*.py $SP/*.sh $DST/analiz/bu_oturum/ 2>/dev/null
cp $SRC/data/bosona_canli/activity.jsonl $SRC/data/bosona_canli/kayit.log $DST/data/bosona/
cp $SP/bosona_*.json $SP/bosona_*.csv $DST/data/bosona/ 2>/dev/null
for f in $SRC/data/tape_fills/*.jsonl; do gzip -c "$f" > $DST/data/tape_fills/$(basename $f).gz; done
cp $SRC/data/tape_cl_direct/*.gz $SRC/data/tape_cl_direct/*.parquet $DST/data/tape_cl_direct/ 2>/dev/null
cp $SRC/data/tape_btc/*.gz $DST/data/tape_btc/ 2>/dev/null
sqlite3 $SRC/data/db/chainlink_history.db ".backup '$DST/data/db/chainlink_history.db'" 2>/dev/null
cp $SRC/HANDOVER.md $SRC/RESEARCH_DISCIPLINE_PLAYBOOK.md $DST/docs/
awk '/2026-09-19/{p=1} p' $SRC/tasks/lessons.md > $DST/docs/lessons_20260919.md
awk '/2026-09-19 16:43Z DEVIR/{p=1} p' $SRC/tasks/todo.md > $DST/docs/todo_20260919.md
cp $MEM/project_*2026091[3-9]*.md $MEM/feedback_londra_yukleme_yetkisi_20260919.md $DST/docs/hafiza/ 2>/dev/null; cp $MEM/MEMORY.md $DST/docs/hafiza/INDEX_MEMORY.md
# maskele (sunucu IP, ssh anahtari)
grep -rl "18\.135\.99\.14\|polymarket-test-key2" $DST --exclude-dir=.git | xargs -r sed -i 's/18\.135\.99\.14/<LONDRA-SUNUCU-IP>/g; s#[^ ]*polymarket-test-key2\.pem#<SSH-ANAHTARI>#g'
cd $DST
# guvenlik: gizli dosya/deger taramasi
if git ls-files --others --exclude-standard | grep -qiE "\.env|\.pem|creds|secret"; then echo "GIZLI DOSYA TESPIT — push iptal"; exit 1; fi
if grep -rIqE "PRIVATE_KEY=0x|API_SECRET=[A-Za-z0-9]{8,}|BEGIN (RSA|OPENSSH|EC) PRIVATE" . --exclude-dir=.git --exclude=depo_senkron.sh; then echo "GIZLI DEGER TESPIT — push iptal"; exit 1; fi
git add -A && git -c user.name=nuxxor commit -q -m "$MSG

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" && git push -q origin main && echo "push ok: $(git rev-parse --short HEAD) | $(git ls-files | wc -l) dosya | $(du -sh . | cut -f1)"
