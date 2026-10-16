#!/bin/bash
# Route 3 end to end against a running service: diagnosis (session cookie) -> repair batch
# -> approve every approval request -> wait for the terminal job status -> show the Pods.
#
#   scripts/repair_route_e2e.sh http://10.2.0.48:30800 <namespace> [question]
#
# Writes its working files under $E2E_DIR (default: a temp dir). Only use against a
# namespace you are allowed to change: the approved commands are really executed.
set -u
B=${1:?base url}; NS=${2:?namespace}; Q=${3:-"诊断 $NS 命名空间里异常的 Pod 为什么失败"}
D=${E2E_DIR:-$(mktemp -d)}; J=$D/cookies.txt
log(){ echo "$(date +%H:%M:%S) $*" | tee -a $D/e2e.log; }
field(){ python3 -c "import json,sys;d=json.load(open('$1'));print(eval(sys.argv[1]) if False else $2)" 2>/dev/null; }

log "workdir $D"
RID=""
for attempt in 1 2 3; do
  curl -s -m 1800 -c $J -b $J -G "$B/ask" --data-urlencode "q=$Q" --data-urlencode "stream=false" \
    --data-urlencode "session_id=e2e-$(date +%s)" -o $D/diag.txt -w "attempt $attempt http=%{http_code} time=%{time_total}s\n" >> $D/e2e.log
  RID=$(grep -o "run_id: [a-f0-9]*" $D/diag.txt | head -1 | cut -d' ' -f2)
  grep -q "模型服务请求失败" $D/diag.txt && { log "attempt $attempt: model gateway failure at router, retrying"; RID=""; sleep 20; continue; }
  [ -n "$RID" ] && break
done
log "diagnosis run_id=$RID"; [ -z "$RID" ] && { log "FAIL no run_id"; exit 1; }

curl -s -m 60 -b $J -c $J -X POST "$B/repair/batches" -H 'Content-Type: application/json' \
  -d "{\"diagnosis_run_id\":\"$RID\"}" -o $D/batch.json
JOB=$(python3 -c "import json;d=json.load(open('$D/batch.json'));g=d.get('groups') or [];print(g[0]['job_id'] if g else '')")
log "job_id=$JOB"; [ -z "$JOB" ] && { log "FAIL no job: $(head -c 300 $D/batch.json)"; exit 1; }

APPROVED=0
for i in $(seq 1 240); do
  curl -s -m 30 -b $J "$B/repair/jobs/$JOB" -o $D/job.json || true
  ST=$(python3 -c "import json;print(json.load(open('$D/job.json')).get('status'))" 2>/dev/null)
  if [ "$ST" = "awaiting_approval" ] && [ $APPROVED -lt 5 ]; then
    read -r AID ARUN DS <<< "$(python3 -c "import json;a=json.load(open('$D/job.json')).get('approval') or {};print(a.get('approval_id',''),a.get('run_id',''),a.get('decision_status','pending'))")"
    if [ "$DS" = "pending" ]; then
      log "approving $AID"; python3 -c "import json;a=json.load(open('$D/job.json')).get('approval') or {};print(json.dumps(a.get('payload',{}),ensure_ascii=False)[:1500])" >> $D/e2e.log
      curl -s -m 30 -b $J -X POST "$B/remediation/approve" -F run_id=$ARUN -F approval_id=$AID -F approved=true -F reviewer=repair_route_e2e -F reason=e2e >> $D/e2e.log; echo >> $D/e2e.log
      APPROVED=$((APPROVED+1))
    fi
    sleep 5; continue
  fi
  case "$ST" in planning|planned|executing|awaiting_approval|None|"") [ $((i%6)) -eq 0 ] && log "status=$ST"; sleep 10;; *) log "terminal status=$ST"; break;; esac
done
python3 -c "import json;d=json.load(open('$D/job.json'));print(json.dumps({k:d.get(k) for k in ('status','mode','stage','error','result')},ensure_ascii=False)[:2000])" | tee -a $D/e2e.log
log "pods:"; kubectl -n $NS get pod 2>&1 | tee -a $D/e2e.log
log "DONE"
