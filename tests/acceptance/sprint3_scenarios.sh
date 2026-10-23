#!/bin/bash
# Sprint 3 验收：三个典型场景自动修复 + 恢复观察 + 超时反馈。
#   tests/acceptance/sprint3_scenarios.sh <c06|c09|c11|all> [--no-reset]
# c11 Terminating（finalizer 阻塞）、c09 Ready 0/1（Readiness 端口错）、c06 CrashLoopBackOff（启动脚本/变量错）。
# 会真实修改 aiops-case-06/09/11；审批由脚本自动批准（review 模式），不替模型选命令。
# 需求表中 CrashLoopBackOff 的字面场景"启动脚本路径错误"见 fixtures/c06-script-path.yaml（命名空间 aiops-case-66），
# apply 后用相同链路（诊断→建批次→批准→恢复观察）验证；c06 本身是启动脚本读取配置路径的变量名错误。
source "$(dirname "$0")/lib.sh"
# The cases' Pods are owned by Deployment "workload"; select them by the owner's selector, not a guessed label.
workload_pods() { kubectl -n "$1" get pods -o json | python3 -c "import json,sys;[print(i['metadata']['name'],i['status']['phase'],'ready=' + str(any(c.get('ready') for c in i['status'].get('containerStatuses',[])))) for i in json.load(sys.stdin)['items'] if i['metadata']['name'].startswith('workload-') and not i['metadata'].get('deletionTimestamp')]"; }
workload_restarts() { kubectl -n "$1" get pods -o json | python3 -c "import json,sys;print(sum(c.get('restartCount',0) for i in json.load(sys.stdin)['items'] if i['metadata']['name'].startswith('workload-') and not i['metadata'].get('deletionTimestamp') for c in i['status'].get('containerStatuses',[])))"; }
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
SEL=${1:?c06|c09|c11|all}; RESET=1; [ "${2:-}" = --no-reset ] && RESET=0
case $SEL in all) CASES="c11 c09 c06";; *) CASES=$SEL;; esac
if [ $RESET = 1 ]; then log "重置用例环境（repair_cases.py reset）"; python3 $ROOT/tests/cases/scripts/repair_cases.py reset >> $D/log.txt 2>&1 || { fail "重置用例环境" "见 $D/log.txt"; summary; exit 1; }; pass "重置用例环境" "c04/c06/c09/c11 异常已就位"; fi
for C in $CASES; do
  NS=aiops-case-${C#c}
  log "===== $C / $NS"
  RID=$(diagnose "诊断 $NS 命名空间里异常的 Pod 为什么失败"); check '[ -n "$RID" ]' "$C 诊断" "run_id=$RID" || continue
  JOB=$(start_batch "$RID"); check '[ -n "$JOB" ]' "$C 创建修复任务" "job=$JOB" || continue
  N=$(approve_all $JOB 1500); log "$C approved $N action(s)"
  ST=$(wait_status $JOB 600 recovered not_recovered needs_followup failed blocked skipped timeout rejected cancelled interrupted)
  REASON=$(jget $D/job.json result.reason | cut -c1-160)
  check '[ "$ST" = recovered ]' "$C 修复后恢复观察（status=$ST）" "$REASON"
  python3 - "$D/job.json" <<'PY' >> $D/log.txt
import json;j=json.load(open(__import__('sys').argv[1]));r=(j.get('result') or {}).get('recovery') or {}
for t in r.get('targets',[]): print('  before:',t.get('before'),'\n  after :',t.get('after'),'\n  elapsed:',t.get('elapsed_seconds'),'timed_out:',t.get('timed_out'))
PY
  case $C in
    c11) check '! kubectl -n $NS get pod workload >/dev/null 2>&1' "$C 复核：Terminating Pod 已消失" "$(kubectl -n $NS get pod 2>&1 | head -3 | tr '\n' ' ')";;
    c09) check '[ "$(kubectl -n $NS get deploy workload -o jsonpath="{.status.readyReplicas}")" = "1" ]' "$C 复核：Deployment workload readyReplicas=1" "$(workload_pods $NS | tr '\n' ' ')";;
    c06) R0=$(workload_restarts $NS); sleep 60; R1=$(workload_restarts $NS)
         check '[ "$(kubectl -n $NS get deploy workload -o jsonpath="{.status.readyReplicas}")" = "1" ] && [ "$R0" = "$R1" ]' "$C 复核：Deployment 就绪且 60 秒无新增重启" "restarts $R0→$R1 · $(workload_pods $NS | tr '\n' ' ')";;
  esac
done
summary; exit $?
