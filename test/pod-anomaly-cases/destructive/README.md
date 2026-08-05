# Manual-only node scenarios

这里的案例可能影响整台节点，永远不会被 `../safe` 引用，也不提供自动故障注入脚本。
只有在专用、可丢弃节点上完成变更审批后，才可按各目录 runbook 手工执行。

- `node-lost/`：停止 kubelet 或隔离节点控制面网络。
- `evicted-node-pressure/`：通过外部、受控的压力工具触发真实节点压力驱逐。

`candidate.yaml` 只是低资源观测目标，不会制造节点故障。
