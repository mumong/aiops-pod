#!/bin/bash
# Sprint 2 验收：高危命令黑名单拦截；人工审批；自动执行开关。
#   scripts/acceptance/sprint2_policy_and_switch.sh [namespace]
# 给出 namespace 时额外做真实链路：review 模式下方案等待审批且未执行 → 拒绝；
# 切到 auto 后新任务直接执行（会真实修改该命名空间！）→ 切回 review。
source "$(dirname "$0")/lib.sh"
NS=${1:-}
TOKEN=$(admin_token)
# ---- 1. 黑名单 ----
DANGEROUS=(
 "kubectl taint nodes node1 k=v:NoSchedule" "kubectl cp /etc/passwd demo/x:/tmp/p"
 "kubectl edit deployment/api -n demo" "kubectl port-forward pod/x 8080:80 -n demo" "kubectl auth can-i delete pods"
 "kubectl patch pod/x -n demo --all -p '{}'" "kubectl scale deployment --all --replicas=0 -A" "kubectl delete pods --all-namespaces"
 "kubectl patch deployment api -n demo -l app=api -p '{}'"
 "kubectl patch node/node1 -p '{}'" "kubectl patch clusterrolebinding/admin -p '{}'" "kubectl delete crd widgets.example.com"
 "kubectl exec pod/x -n demo -- dd if=/dev/zero of=/dev/sda"
 "kubectl exec pod/x -n demo -- mkfs.ext4 /dev/sdb" "kubectl exec pod/x -n demo -- reboot"
 "kubectl get pods -n demo ; rm -rf /" "kubectl get pods --kubeconfig=/tmp/c" "kubectl config use-context prod" "bash -c 'kubectl get pods'"
)
# 需人工审批：规则判"允许但需审批"（修复方案可用，执行前强制人工审批；对话执行仍拦截）
APPROVAL=(
 "kubectl drain node1 --ignore-daemonsets" "kubectl delete ns demo"
 "kubectl exec pod/x -n demo -- rm -rf /data" "kubectl exec pod/x -n demo -- sh -c 'rm /tmp/app.lock'"
 "kubectl run shell --image=busybox -n demo -- rm -rf /"
)
SAFE=(
 "kubectl patch pod/x -n demo --type=merge -p '{\"metadata\":{\"finalizers\":null}}'"
 "kubectl patch deployment/api -n demo --type=json -p '[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/readinessProbe/httpGet/port\",\"value\":8080}]'"
 "kubectl set env deployment/api -n demo APP_CONFIG_PATH=/etc/workload/app.json"
 "kubectl rollout restart deployment/api -n demo" "kubectl get pod/x -n demo -o json" "kubectl exec pod/x -n demo -- curl -s http://localhost:8080/ready"
 "kubectl delete pod/x -n demo" "kubectl delete pod/x -n demo --force --grace-period=0" "kubectl apply -f /tmp/fixed.yaml -n demo"
 "kubectl scale deployment/api -n demo --replicas=2" "kubectl cordon node1" "kubectl exec pod/x -n demo -- kill -HUP 1"
)
python3 - "$B" "$D" "${#DANGEROUS[@]}" "${DANGEROUS[@]}" "${SAFE[@]}" "${APPROVAL[@]}" <<'PY'
import json,sys,urllib.request
base,d,n=sys.argv[1],sys.argv[2],int(sys.argv[3]); cmds=sys.argv[4:]
req=urllib.request.Request(base+"/repair/policy/check",data=json.dumps({"commands":cmds}).encode(),headers={"Content-Type":"application/json"})
res=json.load(urllib.request.urlopen(req,timeout=30))["results"]
json.dump(res,open(d+"/check.json","w"),ensure_ascii=False,indent=1)
bad=[r for r in res[:n] if r["allowed"]]; good=[r for r in res[n:] if not r["allowed"]]
print(len(res[:n])-len(bad), len(bad), len(res[n:])-len(good), len(good))
for r in res: print(("拦截 "+r["rule"]) if not r["allowed"] else ("需审批" if r.get("requires_approval") else "允许"), "|", r["command"][:90], file=sys.stderr)
PY
read -r BLOCKED LEAKED ALLOWED WRONG GATED UNGATED <<< "$(python3 -c "
import json;res=json.load(open('$D/check.json'));n=${#DANGEROUS[@]};m=${#SAFE[@]}
d,s,a=res[:n],res[n:n+m],res[n+m:]
print(sum(1 for r in d if not r['allowed']), sum(1 for r in d if r['allowed']),
      sum(1 for r in s if r['allowed'] and not r.get('requires_approval')), sum(1 for r in s if not r['allowed'] or r.get('requires_approval')),
      sum(1 for r in a if r['allowed'] and r.get('requires_approval')), sum(1 for r in a if not (r['allowed'] and r.get('requires_approval'))))")"
check '[ "$LEAKED" = 0 ]' "高危命令黑名单拦截：${#DANGEROUS[@]} 条高危命令全部被拦截且带规则名" "拦截 $BLOCKED，漏放 $LEAKED"
check '[ "$WRONG" = 0 ]' "合规修复命令不被误拦：${#SAFE[@]} 条" "放行 $ALLOWED，误拦 $WRONG"
check '[ "$UNGATED" = 0 ]' "需审批命令判为“允许但需人工审批”：${#APPROVAL[@]} 条" "需审批 $GATED，判定不符 $UNGATED"
check "curl -s $B/repair/policy | python3 -c \"import json,sys;d=json.load(sys.stdin);r=d['rules'];assert 'dd' in r['shell'] and 'rm' in r['approval_required']['shell'] and 'drain' in r['approval_required']['kubernetes']\"" "GET /repair/policy 公布生效规则" "可在前端“查看拦截规则”核对"
# ---- 2. 开关（接口层） ----
check '[ -n "$TOKEN" ]' "运行时开关可用（Secret 已配置 AIOPS_ADMIN_TOKEN）" "" || { summary; exit 1; }
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT $B/repair/policy/mode -H 'Content-Type: application/json' -d '{"mode":"auto"}')
check '[ "$CODE" = 403 ]' "无令牌不能切换开关（HTTP $CODE）" ""
curl -s -X PUT $B/repair/policy/mode -H "X-AIOps-Admin-Token: $TOKEN" -H 'Content-Type: application/json' -d '{"mode":"auto","reason":"Sprint2 验收","ttl_minutes":30,"changed_by":"acceptance"}' -o $D/mode.json
check '[ "$(jget $D/mode.json mode)" = auto ] && [ "$(jget $D/mode.json mode_source)" = runtime ]' "管理员令牌切换为自动执行（带原因与 30 分钟有效期）" "$(jget $D/mode.json override.reason)"
curl -s -X DELETE $B/repair/policy/mode -H "X-AIOps-Admin-Token: $TOKEN" -o $D/mode2.json
check '[ "$(jget $D/mode2.json mode_source)" = config ]' "恢复为配置值（mode=$(jget $D/mode2.json mode)）" ""
curl -s "$B/repair/audit?limit=20&kind=mode_changed" -H "X-AIOps-Admin-Token: $TOKEN" -o $D/audit.json
check '[ "$(jget $D/audit.json events.#)" -ge 2 ]' "开关切换写入审计（GET /repair/audit）" "最近 $(jget $D/audit.json events.#) 条 mode_changed"
# ---- 3. 真实链路（可选） ----
if [ -n "$NS" ]; then
  log "真实链路：$NS（review 模式等待审批→拒绝；auto 模式直接执行）"
  RID=$(diagnose "诊断 $NS 命名空间里异常的 Pod 为什么失败"); check '[ -n "$RID" ]' "诊断 $NS" "run_id=$RID" || { summary; exit 1; }
  JOB=$(start_batch "$RID"); ST=$(wait_status $JOB 900 awaiting_approval planned executing verifying failed skipped blocked)
  check '[ "$ST" = awaiting_approval ]' "人工审批：review 模式下任务停在等待批准（status=$ST）" "$(jget $D/job.json approval.title | cut -c1-60)"
  check '[ "$(jget $D/job.json events.#)" = 0 ]' "人工审批：批准前没有任何命令执行事件" ""
  read -r AID ARUN <<< "$(python3 -c "import json;a=json.load(open('$D/job.json')).get('approval') or {};print(a.get('approval_id',''),a.get('run_id',''))")"
  curl -s -m 30 -b $J -X POST "$B/remediation/approve" -F run_id=$ARUN -F approval_id=$AID -F approved=false -F reviewer=acceptance -F reason=拒绝测试 -o /dev/null
  ST=$(wait_status $JOB 120 rejected); check '[ "$ST" = rejected ]' "人工审批：拒绝后终态 rejected 且未执行" "events=$(jget $D/job.json events.#)"
  curl -s -X PUT $B/repair/policy/mode -H "X-AIOps-Admin-Token: $TOKEN" -H 'Content-Type: application/json' -d '{"mode":"auto","reason":"Sprint2 验收-自动执行","ttl_minutes":20,"changed_by":"acceptance"}' -o /dev/null
  RID2=$(diagnose "诊断 $NS 命名空间里异常的 Pod 为什么失败"); JOB2=$(start_batch "$RID2")
  ST=$(wait_status $JOB2 1200 recovered not_recovered needs_followup failed blocked skipped timeout rejected)
  check '[ "$(jget $D/job.json mode)" = auto ] && [ "$(jget $D/job.json mode_source)" = runtime ]' "自动执行开关：新任务按 auto（来源 runtime）执行" "status=$ST"
  check '[ "$(python3 -c "import json;e=json.load(open(\"$D/job.json\")).get(\"events\") or [];print(sum(1 for x in e if x.get(\"type\")==\"remediation_tool_start\" and x.get(\"approval\")==\"auto\"))")" -ge 1 ]' "自动执行开关：命令事件标记 approval=auto，无审批请求" "$(jget $D/job.json result.reason | cut -c1-80)"
  curl -s -X DELETE $B/repair/policy/mode -H "X-AIOps-Admin-Token: $TOKEN" -o /dev/null; log "已恢复 review"
fi
summary; exit $?
