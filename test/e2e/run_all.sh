#!/usr/bin/env bash
# ==========================================================================
# E2E 一键部署脚本
# 部署 Pod 异常状态专属故障场景 manifest 到 aiops-e2e namespace
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

# 允许重复执行：TerminatingStuck 会保留 finalizer，重新部署前先清理旧对象。
kubectl -n "${NS}" patch pod terminating-stuck --type=merge -p '{"metadata":{"finalizers":[]}}' >/dev/null 2>&1 || true
kubectl -n "${NS}" delete pod terminating-stuck --ignore-not-found --wait=true >/dev/null 2>&1 || true

MANIFESTS=(
  "pod-evicted.yaml"              # Evicted
  "pod-volume-mount-failed.yaml"        # VolumeMountFailed
  "pod-pending-unschedulable.yaml"                  # PendingUnschedulable
  "pod-node-lost-unknown.yaml"          # NodeLostOrUnknown candidate; requires manual node fault to become Unknown
  "pod-terminating-stuck.yaml"          # TerminatingStuck; delete is triggered below
  "pod-oomkilled.yaml"                   # OOMKilled
  "pod-crashloop-runtime.yaml"          # CrashLoopBackOffRuntime
  "pod-imagepull-failed.yaml"       # ImagePullFailed
  "pod-sandbox-create-failed.yaml"      # SandboxCreateFailed
  "pod-config-error.yaml"       # ConfigError
  "pod-notready-probe-failed.yaml"      # NotReadyProbeFailed
)

for manifest in "${MANIFESTS[@]}"; do
  kubectl apply -f "${ROOT}/manifests/${manifest}"
done

# 触发 TerminatingStuck：对象带 finalizer，delete 后会保持 Terminating。
kubectl -n "${NS}" delete pod terminating-stuck --wait=false >/dev/null 2>&1 || true

echo "[3/3] 等待工作负载就绪"
kubectl -n "${NS}" rollout status deploy/logfill --timeout=60s 2>/dev/null || true
kubectl -n "${NS}" rollout status deploy/memhog --timeout=60s 2>/dev/null || true
kubectl -n "${NS}" rollout status deploy/crashloop-runtime --timeout=30s 2>/dev/null || true
# L4 场景预期进入 CrashLoopBackOff，不等待 rollout 成功
kubectl -n "${NS}" get pod -l app=appconfigfail >/dev/null 2>&1 || true

echo ""
echo "✅ 部署完成。可用场景："
echo "  Evicted: logfill"
echo "  VolumeMountFailed: volume-mount-failed"
echo "  PendingUnschedulable: l1-test-nginx"
echo "  NodeLostOrUnknown: node-lost-unknown-candidate（需手动让所在节点 NotReady/Unknown）"
echo "  TerminatingStuck: terminating-stuck"
echo "  OOMKilled: memhog"
echo "  CrashLoopBackOffRuntime: crashloop-runtime"
echo "  ImagePullFailed: imagepull-fail-victim"
echo "  SandboxCreateFailed: sandbox-create-failed"
echo "  ConfigError: appconfigfail"
echo "  NotReadyProbeFailed: notready-probe-failed"
echo ""
echo "运行验收测试："
echo "  ./test_scenarios.sh"
