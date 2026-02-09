## E2E（kind）故障注入与验收

目标：为 5 个典型原子场景（L0-L4）提供**可复现**的故障环境与验收脚本，便于回归测试你的 AIOps Agent。

### 前置依赖
- `docker`
- `kind`
- `kubectl`
- `curl`

### 一键跑通（建议在本机/CI 上执行）

```bash
cd test/e2e
./run_all.sh
```

### 设计说明
- **L2 OOMKilled**：纯 K8s 方式稳定复现（Deployment + 小内存 limit）。
- **L4 依赖 503**：mock 依赖固定 503，应用侧透传 503 并打印证据日志。
- **L3 DNS 延迟**：在客户端 Pod 注入 `tc netem delay 500ms` 并打印 `dns_lookup_seconds=...` 样本。
- **L0 磁盘满**：
  - 安全版本：使用 `emptyDir.sizeLimit` 写满触发 `No space left on device`（不会把宿主机磁盘打爆）。
  - 如果你一定要"node_disk_utilization > 95%"那种节点级注入，请在独立测试机上做，并把清理流程做成强门禁。
- **L1 Node Taint (NotReady 模拟)**：
  - 使用 Node Taint 注入标记节点为不可调度，AI Agent 通过 kubectl get nodes 直接看到异常
  - 命令简单：`kubectl taint nodes ...`，不需要进入容器
  - 易于验证：直接查看 STATUS 列和 Taints
  - 易于清理：`kubectl taint nodes <key>-` 清除标记

