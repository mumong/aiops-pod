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

echo "## Evicted: EmptyDir 超限 (logfill)"
kubectl -n "${NS}" get pod -l app=logfill -o wide 2>/dev/null || echo "  logfill 未部署"
kubectl -n "${NS}" logs deploy/logfill --tail=10 2>/dev/null || true
kubectl -n "${NS}" describe pod -l app=logfill 2>/dev/null | grep -Ei "Reason:|Message:|Evicted|ephemeral-storage|sizeLimit" || true
echo ""

echo "## VolumeMountFailed: missing ConfigMap volume"
kubectl -n "${NS}" get pod volume-mount-failed -o wide 2>/dev/null || echo "  volume-mount-failed 未部署"
kubectl -n "${NS}" describe pod volume-mount-failed 2>/dev/null | grep -Ei "FailedMount|MountVolume|not found|configmap" || true
echo ""

echo "## VolumeMountFailed variants: Secret / ConfigMap key / hostPath / PVC"
for pod in \
    volume-mount-missing-secret \
    volume-mount-missing-configmap-key \
    volume-mount-hostpath-missing \
    volume-mount-missing-pvc
do
    kubectl -n "${NS}" get pod "${pod}" -o wide 2>/dev/null || echo "  ${pod} 未部署"
    kubectl -n "${NS}" describe pod "${pod}" 2>/dev/null | grep -Ei "FailedMount|MountVolume|not found|couldn't find key|hostPath|persistentvolumeclaim|secret|configmap" || true
done
echo ""

echo "## PendingUnschedulable: impossible nodeSelector"
kubectl -n "${NS}" get pod -l app=pending-unschedulable -o wide 2>/dev/null || echo "  pending-unschedulable 未部署"
kubectl -n "${NS}" describe pod -l app=pending-unschedulable 2>/dev/null | grep -Ei "FailedScheduling|node selector|didn't match|Insufficient|taint" || true
echo ""

echo "## NodeLostOrUnknown: candidate Pod"
kubectl -n "${NS}" get pod node-lost-unknown-candidate -o wide 2>/dev/null || echo "  node-lost-unknown-candidate 未部署"
kubectl -n "${NS}" get pod node-lost-unknown-candidate -o jsonpath='{.metadata.annotations.aiops\\.e2e/manual-trigger}{"\n"}' 2>/dev/null || true
echo ""

echo "## TerminatingStuck: finalizer holds deletion"
kubectl -n "${NS}" get pod terminating-stuck -o wide 2>/dev/null || echo "  terminating-stuck 未部署或已清理"
kubectl -n "${NS}" get pod terminating-stuck -o jsonpath='{.metadata.deletionTimestamp}{" finalizers="}{.metadata.finalizers}{"\n"}' 2>/dev/null || true
echo ""

echo "## OOMKilled: memhog"
POD_OOM="$(kubectl -n "${NS}" get pod -l app=memhog -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo '')"
if [[ -n "${POD_OOM}" ]]; then
    kubectl -n "${NS}" get pod "${POD_OOM}" -o wide
    kubectl -n "${NS}" describe pod "${POD_OOM}" | grep -A5 "Last State" || true
else
    echo "  memhog 未部署"
fi
echo ""

echo "## CrashLoopBackOffRuntime: process exits with code 2"
POD_CRASH="$(kubectl -n "${NS}" get pod -l app=crashloop-runtime -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo '')"
if [[ -n "${POD_CRASH}" ]]; then
    kubectl -n "${NS}" get pod "${POD_CRASH}" -o wide
    kubectl -n "${NS}" describe pod "${POD_CRASH}" | grep -A6 "Last State" || true
    kubectl -n "${NS}" logs "${POD_CRASH}" --previous --tail=10 2>/dev/null || true
else
    echo "  crashloop-runtime 未部署"
fi
echo ""

echo "## ImagePullFailed: invalid registry"
kubectl -n "${NS}" get pod imagepull-fail-victim -o wide 2>/dev/null || echo "  imagepull-fail-victim 未部署"
kubectl -n "${NS}" describe pod imagepull-fail-victim 2>/dev/null | grep -Ei "ImagePullBackOff|ErrImagePull|Failed to pull|registry.invalid" || true
echo ""

echo "## SandboxCreateFailed: missing RuntimeClass handler"
kubectl -n "${NS}" get pod sandbox-create-failed -o wide 2>/dev/null || echo "  sandbox-create-failed 未部署"
kubectl -n "${NS}" describe pod sandbox-create-failed 2>/dev/null | grep -Ei "FailedCreatePodSandBox|RuntimeClass|runtime|sandbox|handler" || true
echo ""

echo "## ConfigError: Config Bootstrap Fail (appconfigfail)"
POD_L4="$(kubectl -n "${NS}" get pod -l app=appconfigfail -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo '')"
if [[ -n "${POD_L4}" ]]; then
    kubectl -n "${NS}" get pod "${POD_L4}" -o wide
    kubectl -n "${NS}" describe pod "${POD_L4}" | grep -A6 "Last State" || true
    kubectl -n "${NS}" logs "${POD_L4}" --previous --tail=10 2>/dev/null || kubectl -n "${NS}" logs "${POD_L4}" --tail=10 2>/dev/null || true
else
    echo "  appconfigfail 未部署"
fi
echo ""

echo "## NotReadyProbeFailed: readiness probe always fails"
kubectl -n "${NS}" get pod notready-probe-failed -o wide 2>/dev/null || echo "  notready-probe-failed 未部署"
kubectl -n "${NS}" describe pod notready-probe-failed 2>/dev/null | grep -Ei "Readiness probe failed|Unhealthy|Ready" || true
echo ""

echo "✅ 取证完成"
