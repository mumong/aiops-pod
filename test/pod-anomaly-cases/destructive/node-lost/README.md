# Node Lost manual runbook

## Preflight

选择一台专用、可丢弃的 worker，记录其主机名和带外登录方式。运行
`kubectl get pods -A --field-selector spec.nodeName=<NODE> -o wide`，确认没有生产、存储、
控制面或其他不可中断负载；确认候选 Pod 的 requests/limits 不影响节点。

## Blast radius

停止 kubelet或隔离到 apiserver 的网络会让目标节点上所有 Pod 状态失真，并可能触发
控制器迁移、卷 fencing 和告警。影响范围是整台 `<NODE>`，不是本目录的单个 namespace。

## Manual confirmation

由集群所有者明确确认 `<NODE>`、维护窗口、带外恢复通道和回滚负责人。未获得确认时只可
阅读本文件，不得应用 candidate，也不得操作节点。

## Trigger

先把 `candidate.yaml` 中 `REPLACE_WITH_DISPOSABLE_NODE` 改为确认过的主机名，再手工
`kubectl apply -f candidate.yaml`。确认 Pod Running 后，通过既有运维通道手工停止该节点
kubelet，或只隔离该节点到控制面的网络。不要用 DaemonSet、特权 Pod 或 hostPath 注入。

预期真实证据包括 Node Ready `Unknown`、node heartbeat 超时、Pod `Unknown/NodeLost`、
kube-state 指标和控制面 Event；节点网络断开后，应用日志和 trace 可能只保留故障前窗口。

## Recovery

恢复节点网络并启动 kubelet，等待 `kubectl get node <NODE>` 回到 `Ready`。检查该节点
所有业务、CNI、CSI 和日志/指标采集 daemon 的健康状态；若未恢复，按平台节点恢复流程处理。

## Cleanup

确认节点 Ready 且遥测采集恢复后，执行
`kubectl delete namespace aiops-manual-01 --ignore-not-found=true`，再核对没有残留卷或 Pod。
