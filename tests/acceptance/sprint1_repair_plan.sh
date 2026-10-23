#!/bin/bash
# Sprint 1 验收：从诊断报告进入修复 → 方案展示对象/异常原因/命令 → 对话修改方案生成新版本。
#   tests/acceptance/sprint1_repair_plan.sh <namespace> [question]
# 不批准任何动作；只验证方案生成与修改链路。
source "$(dirname "$0")/lib.sh"
NS=${1:?namespace of a deployed anomaly case, e.g. aiops-case-09}; Q=${2:-"诊断 $NS 命名空间里异常的 Pod 为什么失败"}
log "基础地址 $B，命名空间 $NS"
RID=$(diagnose "$Q"); check '[ -n "$RID" ]' "诊断完成并返回 run_id" "run_id=$RID" || { summary; exit 1; }
JOB=$(start_batch "$RID"); check '[ -n "$JOB" ]' "从诊断记录创建修复批次（POST /repair/batches）" "job_id=$JOB" || { summary; exit 1; }
ST=$(wait_status $JOB 900 planned awaiting_approval executing verifying failed skipped blocked)
check '[ "$ST" = planned ] || [ "$ST" = awaiting_approval ]' "修复方案生成（status=$ST）" "$(jget $D/job.json error)"
ACTIONS=$(jget $D/job.json plan.actions.#); TARGETS=$(jget $D/job.json plan.targets.#)
check '[ "${ACTIONS:-0}" -ge 1 ]' "方案包含可执行动作" "actions=$ACTIONS targets=$TARGETS"
check '[ -n "$(jget $D/job.json plan.targets.0.pod)" ]' "方案展示修复对象（namespace/pod）" "$(jget $D/job.json plan.targets.0.namespace)/$(jget $D/job.json plan.targets.0.pod)"
check '[ -n "$(jget $D/job.json diagnosis_summary)" ] && [ "$(jget $D/job.json diagnosis_summary)" != None ]' "方案展示异常原因（来自诊断）" "$(jget $D/job.json diagnosis_summary | cut -c1-80)"
CMD=$(jget $D/job.json plan.actions.0.execute_command); check '[[ "$CMD" == kubectl* ]]' "方案展示执行命令" "$CMD"
check '[ -n "$(jget $D/job.json plan.actions.0.description)" ]' "动作带说明与风险" "risk=$(jget $D/job.json plan.actions.0.risk | cut -c1-60)"
V=$(jget $D/job.json version)
curl -s -m 30 -b $J -X POST "$B/repair/jobs/$JOB/feedback" -H 'Content-Type: application/json' \
  -d "{\"version\":$V,\"feedback\":\"请把修复动作的说明写得更具体，并补充验证命令；其余保持不变。\"}" -o $D/feedback.json
JOB2=$(jget $D/feedback.json job_id); check '[ -n "$JOB2" ] && [ "$JOB2" != None ]' "通过对话提交修改意见（POST /repair/jobs/{id}/feedback）" "new job=$JOB2 v$(jget $D/feedback.json version)"
ST2=$(wait_status $JOB2 900 planned awaiting_approval executing verifying failed skipped blocked)
check '[ "$ST2" = planned ] || [ "$ST2" = awaiting_approval ]' "新版本方案生成（v$(jget $D/job.json version) status=$ST2)" "$(jget $D/job.json error)"
check '[ "$(jget $D/job.json history.#)" -ge 1 ]' "旧版本进入历史记录，新版本携带用户意见" "feedback=$(jget $D/job.json feedback.text | cut -c1-40)"
curl -s -m 30 -b $J -X POST "$B/repair/jobs/$JOB2/cancel" -o /dev/null
summary; exit $?
