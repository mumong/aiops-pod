# Node pressure Evicted manual runbook

## Preflight

选择一台专用、可重建的 worker，检查 `kubectl describe node <NODE>`、磁盘余量、内存、PID、
污点及该节点所有 Pod。确认没有生产、存储、控制面或不可中断负载，并准备带外清理压力源。

## Blast radius

真实 memory、ephemeral-storage 或 PID pressure 会影响节点上的全部 Pod，可能造成驱逐、
镜像垃圾回收、服务中断或节点失联。影响范围是整台 `<NODE>`，压力源失控可能持续扩大。

## Manual confirmation

集群所有者必须明确确认节点、压力维度、硬上限、停止阈值、维护窗口和恢复负责人。没有书面
确认时不得制造压力；本目录不会替你执行任何压力命令。

## Trigger

把 `candidate.yaml` 的占位节点名替换为已批准节点并手工 apply。然后使用平台已有、集群外
管理的受控压力工具，在该节点逐步增加一种压力；每一步观察 Node condition 和候选 Pod。
禁止通过本仓库部署 privileged/hostPath DaemonSet。达到第一个 `DiskPressure`、
`MemoryPressure`、`PIDPressure` 或 Evicted 证据后立即停止增长。

预期证据包括 Node condition、kubelet eviction Event、Pod `status.reason=Evicted`、
Prometheus node/kube-state 指标，以及驱逐前 Elasticsearch、DeepFlow 数据窗口。

## Recovery

先停止并删除外部压力源，释放磁盘、内存或 PID；等待 Node condition 恢复为 False、节点
Ready，并检查 kubelet、CNI、CSI、Filebeat、DeepFlow agent 和 Prometheus target。

## Cleanup

节点完全恢复后运行 `kubectl delete namespace aiops-manual-02 --ignore-not-found=true`。
再次检查节点压力、残留进程、临时文件和被驱逐的非实验 Pod，必要时按平台流程重建节点。
