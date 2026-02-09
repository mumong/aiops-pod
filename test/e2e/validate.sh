#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="${1:-aiops-e2e}"
NS="aiops-e2e"

echo "### E2E Validation Checklist"
echo "- Cluster: ${CLUSTER_NAME}"
echo "- Namespace: ${NS}"
echo ""

echo "### 场景取证（用于你手工对照 runbook/规则判定）"
echo ""

echo "## L2 OOMKilled"
kubectl -n "${NS}" get pod -l app=memhog -o wide || true
POD_OOM="$(kubectl -n "${NS}" get pod -l app=memhog -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo '')"
if [[ -n "${POD_OOM}" ]]; then
  kubectl -n "${NS}" describe pod "${POD_OOM}" | sed -n '1,120p' || true
  kubectl -n "${NS}" logs "${POD_OOM}" --previous --tail=80 || true
fi
echo ""

echo "## L4 Dependency 503"
kubectl -n "${NS}" get pod -l app=appcaller -o wide || true
kubectl -n "${NS}" logs deploy/appcaller --tail=80 || true
kubectl -n "${NS}" run tmp-curl --rm -i --restart=Never --image=curlimages/curl -- \\
  curl -s -o /dev/null -w "dep_http_code=%{http_code}\\n" http://dep503:8080/ || true
echo ""

echo "## L0 ENOSPC (safe simulation)"
kubectl -n "${NS}" get pod -l app=logfill -o wide || true
kubectl -n "${NS}" logs deploy/logfill --tail=80 || true
echo ""

echo "## L3 DNS latency (tc 500ms injected in client)"
kubectl -n "${NS}" logs pod/dns-latency-client --tail=30 || true
echo ""

echo "## 8. 扩展知识"
echo ""
echo "### 8.1 K8s Node Taint 机制"
echo "K8s Taints 是节点级别的标记，用于控制 Pod 调度："
echo "| Effect | 含义 | 影响 |"
echo "|--------|------|------|"
echo "| NoSchedule | Pod 不会被调度到此节点 | 最严格 |"
echo "| PreferNoSchedule | 优先避免调度到此节点 | 中等影响 |"
echo "| NoExecute | 已调度 Pod 不会被执行 | 最严重 |"
echo "| PreferNoExecute | 优先避免执行，已调度 Pod 会被驱逐 | 严重影响 |"
echo ""

echo "### 8.2 节点状态类型"
echo "| 类型 | 含义 | 正常值 |"
echo "|------|--------|--------|"
echo "| Ready | 节点健康且可用 | Ready = True |"
echo "| NotReady | 节点存在问题 | Ready = False |"
echo "| Unknown | 控制器无法通信 | 任何值 |"
echo "| MemoryPressure | 内存压力存在 | N/A |"
echo "| DiskPressure | 磁盘压力存在 | N/A |"
echo "| PIDPressure | 进程压力存在 | N/A |"
echo "| NetworkUnavailable | 网络不可用 | N/A |"
echo ""

echo "### 8.3 快速命令参考"
echo ""
echo "\\`bash"
echo "# 诊断"
echo "alias diag-node='kubectl get nodes && kubectl describe node && kubectl get events -A --field-selector involvedObject.kind=Node'"
echo ""
echo "# 快速检查 Ready 节点"
echo "kubectl get nodes --no-headers | grep Ready | grep -v NotReady"
echo ""
echo "# 检查特定节点的所有条件"
echo "kubectl get node <node-name> -o jsonpath='{.status.conditions[*]}'"
echo "# 清理 taint"
echo "kubectl taint nodes <node-name> <taint-key>-"
echo ""
echo "# 查看 kubelet 日志"
echo "kubectl logs -n kube-system -l k8s-app=kubelet <node-name> --tail=50"
EOF
