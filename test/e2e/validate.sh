#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="${1:-aiops-e2e}"
NS="aiops-e2e"

echo "### E2E Validation Checklist"
echo "- Cluster: ${CLUSTER_NAME}"
echo "- Namespace: ${NS}"
echo ""

echo "### 现场取证（用于你手工对照 runbook/规则判定）"
echo ""
echo "## L2 OOMKilled"
kubectl -n "${NS}" get pod -l app=memhog -o wide || true
POD_OOM="$(kubectl -n "${NS}" get pod -l app=memhog -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
if [[ -n "${POD_OOM}" ]]; then
  kubectl -n "${NS}" describe pod "${POD_OOM}" | sed -n '1,120p' || true
  kubectl -n "${NS}" logs "${POD_OOM}" --previous --tail=80 || true
fi
echo ""

echo "## L4 Dependency 503"
kubectl -n "${NS}" get pod -l app=appcaller -o wide || true
kubectl -n "${NS}" logs deploy/appcaller --tail=80 || true
kubectl -n "${NS}" run tmp-curl --rm -i --restart=Never --image=curlimages/curl -- \
  curl -s -o /dev/null -w "dep_http_code=%{http_code}\n" http://dep503:8080/ || true
echo ""

echo "## L0 ENOSPC (safe simulation)"
kubectl -n "${NS}" get pod -l app=logfill -o wide || true
kubectl -n "${NS}" logs deploy/logfill --tail=80 || true
echo ""

echo "## L3 DNS latency (tc 500ms injected in client)"
kubectl -n "${NS}" logs pod/dns-latency-client --tail=30 || true
echo ""

cat <<'EOF'
### 下一步：用 AIOps API 跑验收（你部署好 aiops-copilot 后）

按你的规则引擎（软拦截）与新 runbook，建议用 format=sse 观察 deterministic_decision 事件：

1) L2 OOMKilled
   q="ns=aiops-e2e pod=<memhog-pod> OOMKilled 排查"

2) L4 依赖 503
   q="ns=aiops-e2e 依赖服务返回503 导致应用5xx 激增，app=appcaller svc=dep503"

3) L0 磁盘满（ENOSPC）
   q="ns=aiops-e2e 日志写入 No space left on device 排查"

4) L3 DNS 延迟
   q="ns=aiops-e2e DNS 查询很慢（500ms），coredns 延迟排查"

示例：
curl -N -G "http://<NODE_IP>:30800/ask" \
  --data-urlencode "q=${q}" \
  --data-urlencode "format=sse"

验收点：
- final 中必须出现证据链表格（>=3条）
- final 末尾会附带 “机器判定（Deterministic，软拦截）”
- SSE 中会出现 event: deterministic_decision
EOF

