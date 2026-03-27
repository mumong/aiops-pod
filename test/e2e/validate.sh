#!/usr/bin/env bash
# ==========================================================================
# E2E 场景取证脚本 — 手动验证各场景是否正确注入
# ==========================================================================
set -euo pipefail

NS="aiops-e2e"

echo "============================================================"
echo "  E2E 场景取证 (namespace: ${NS})"
echo "============================================================"
echo ""

echo "## L0: EmptyDir 超限 (logfill)"
kubectl -n "${NS}" get pod -l app=logfill -o wide 2>/dev/null || echo "  logfill 未部署"
kubectl -n "${NS}" logs deploy/logfill --tail=10 2>/dev/null || true
echo ""

echo "## L1: Node Taint"
kubectl get nodes -o custom-columns='NAME:.metadata.name,STATUS:.status.conditions[?(@.type=="Ready")].status,TAINTS:.spec.taints[*].key' 2>/dev/null || true
echo ""

echo "## L2: OOMKilled (memhog)"
POD_OOM="$(kubectl -n "${NS}" get pod -l app=memhog -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo '')"
if [[ -n "${POD_OOM}" ]]; then
    kubectl -n "${NS}" get pod "${POD_OOM}" -o wide
    kubectl -n "${NS}" describe pod "${POD_OOM}" | grep -A5 "Last State" || true
else
    echo "  memhog 未部署"
fi
echo ""

echo "## L3: ImagePullBackOff"
kubectl -n "${NS}" get pod imagepull-fail-victim -o wide 2>/dev/null || echo "  imagepull-fail-victim 未部署"
kubectl -n "${NS}" describe pod imagepull-fail-victim 2>/dev/null | grep -A5 "Events" || true
echo ""

echo "## L4: App Health Fail (apphealth)"
kubectl -n "${NS}" get pod -l app=apphealth -o wide 2>/dev/null || echo "  apphealth 未部署"
kubectl -n "${NS}" logs deploy/apphealth --tail=5 2>/dev/null || true
echo ""

echo "✅ 取证完成"
