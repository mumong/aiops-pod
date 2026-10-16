#!/bin/bash
# Shared helpers for the Sprint acceptance scripts. Pure bash + curl + python3 + kubectl.
# Every script prints a PASS/FAIL table and exits non-zero on any FAIL.
set -u
B=${AIOPS_BASE:-http://10.2.0.48:30800}
D=${ACCEPT_DIR:-$(mktemp -d /tmp/aiops-accept-XXXXXX)}
mkdir -p "$D"
J=$D/cookies.txt
RESULTS=()
ts() { date +%H:%M:%S; }
log() { echo "$(ts) $*" | tee -a $D/log.txt >&2; }
record() { RESULTS+=("$1|$2|$3"); log "[$1] $2 — $3"; }
pass() { record PASS "$1" "$2"; }
fail() { record FAIL "$1" "$2"; }
check() { if eval "$1"; then pass "$2" "$3"; return 0; else fail "$2" "$3"; return 1; fi; }
jget() { python3 - "$1" "$2" <<'PY' 2>/dev/null
import json,sys
v=json.load(open(sys.argv[1]))
for part in sys.argv[2].split('.'):
    if part=='#': v=len(v or []); break
    v=(v or {})[int(part)] if part.isdigit() else (v or {}).get(part)
print('' if v is None else v)
PY
}
admin_token() { kubectl -n aiops get secret aiops-secret -o jsonpath='{.data.AIOPS_ADMIN_TOKEN}' 2>/dev/null | base64 -d; }
summary() {
  echo; echo "== 结果汇总 ($D)"; printf '%-5s | %-44s | %s\n' 结果 测试项 说明
  local bad=0; for r in "${RESULTS[@]}"; do IFS='|' read -r s n m <<< "$r"; printf '%-5s | %-44s | %s\n' "$s" "$n" "$m"; [ "$s" = FAIL ] && bad=1; done
  echo "== 工作目录 $D"; return $bad
}
# diagnose <question> -> prints run_id (session cookie kept in $J)
diagnose() {
  local q=$1 rid=""
  for attempt in 1 2 3; do
    curl -s -m 1800 -c $J -b $J -G "$B/ask" --data-urlencode "q=$q" --data-urlencode "stream=false" \
      --data-urlencode "session_id=accept-$(date +%s)" -o $D/diag.txt
    rid=$(grep -o "run_id: [a-f0-9]*" $D/diag.txt | head -1 | cut -d' ' -f2)
    grep -q "模型服务请求失败" $D/diag.txt && { log "diagnosis attempt $attempt hit a gateway failure, retrying"; rid=""; sleep 15; continue; }
    [ -n "$rid" ] && break
  done
  echo "$rid"
}
start_batch() { curl -s -m 60 -b $J -c $J -X POST "$B/repair/batches" -H 'Content-Type: application/json' -d "{\"diagnosis_run_id\":\"$1\"}" -o $D/batch.json; jget $D/batch.json groups.0.job_id; }
job() { curl -s -m 30 -b $J "$B/repair/jobs/$1" -o $D/job.json; jget $D/job.json status; }
# wait_status <job> <seconds> <status...>: poll until status in the list; prints final status
wait_status() {
  local jid=$1 limit=$2; shift 2; local deadline=$(( $(date +%s) + limit )) st=""
  while [ $(date +%s) -lt $deadline ]; do st=$(job $jid); for want in "$@"; do [ "$st" = "$want" ] && { echo "$st"; return 0; }; done; sleep 5; done
  echo "$st"; return 1
}
approve_all() { # approve every pending action of a job until it leaves awaiting_approval; prints count
  local jid=$1 limit=${2:-900} n=0 st aid arun ds
  local deadline=$(( $(date +%s) + limit ))  # separate statement: expansion precedes `local` assignment
  while [ $(date +%s) -lt $deadline ]; do
    st=$(job $jid)
    case "$st" in
      awaiting_approval)
        read -r aid arun ds <<< "$(python3 -c "import json;a=json.load(open('$D/job.json')).get('approval') or {};print(a.get('approval_id',''),a.get('run_id',''),a.get('decision_status','pending'))")"
        if [ "$ds" = pending ] && [ -n "$aid" ]; then
          curl -s -m 30 -b $J -X POST "$B/remediation/approve" -F run_id=$arun -F approval_id=$aid -F approved=true -F reviewer=acceptance -F reason=sprint >> $D/log.txt; echo >> $D/log.txt; n=$((n+1)); log "approved $aid"
        fi; sleep 3;;
      queued|planning|planned|executing|verifying) sleep 5;;
      *) break;;
    esac
  done
  echo $n
}
