#!/usr/bin/env bash
# ==========================================================================
# E2E 一键部署脚本
# 部署 L0-L4 五个故障场景的 manifest 到 aiops-e2e namespace
# ==========================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NS="aiops-e2e"

echo "============================================================"
echo "  E2E 故障场景部署"
echo "============================================================"

echo "[1/3] 创建 namespace"
kubectl apply -f "${ROOT}/manifests/00-namespace.yaml"

echo "[2/3] 部署故障场景 manifests"
kubectl apply -f "${ROOT}/manifests/l0-logfill-enospc.yaml"
kubectl apply -f "${ROOT}/manifests/l1-taint-node.yaml"
kubectl apply -f "${ROOT}/manifests/l2-oomkilled.yaml"
kubectl apply -f "${ROOT}/manifests/l3-imagepull-fail-victim.yaml"
kubectl apply -f "${ROOT}/manifests/l4-app-health-fail.yaml"

echo "[3/3] 等待工作负载就绪"
kubectl -n "${NS}" rollout status deploy/logfill --timeout=60s 2>/dev/null || true
kubectl -n "${NS}" rollout status deploy/memhog --timeout=60s 2>/dev/null || true
kubectl -n "${NS}" rollout status deploy/apphealth --timeout=60s 2>/dev/null || true

echo ""
echo "✅ 部署完成。可用场景："
echo "  L0: logfill (EmptyDir 超限驱逐)"
echo "  L1: l1-test-nginx (Node Taint)"
echo "  L2: memhog (OOMKilled)"
echo "  L3: imagepull-fail-victim (ImagePullBackOff)"
echo "  L4: apphealth (应用健康检查失败)"
echo ""
echo "运行验收测试："
echo "  ./test_scenarios.sh"
