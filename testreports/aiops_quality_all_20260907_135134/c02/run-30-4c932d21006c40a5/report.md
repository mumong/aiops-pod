## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod `workload-65b7f54794-nqrzv` 处于 `ImagePullBackOff` 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | Pod 状态 `Pending`；容器 `app` 等待原因 `ImagePullBackOff`，消息 `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 核心异常状态 |
| 2 | K8s State | K8s Config | 容器 `app` 配置资源 Request：CPU `5m`, Memory `8Mi`；Limit：CPU `50m`, Memory `32Mi` | 排除资源资源不足引发的调度问题 |
| 3 | K8s Event | K8s State | Pod 条件 `Ready` 与 `ContainersReady` 均为 `False`，原因 `ContainersNotReady`，消息 `containers with unready status: [app]` | 验证容器持续无法就绪 |
| 4 | Metric | Prometheus | 指标 `kube_pod_container_status_waiting_reason` 显示 `1` (容器 `app`, 原因 `ImagePullBackOff`)；重启计数 `0` | 确认异常持续且未发生重启 |
| 5 | Logging/Tracing | 采集状态 | 物理上未产生应用日志或 Trace（原因：容器未启动） | 排除运行时应用级异常 |

**证据说明：**
- 节点层面与资源配额（#2）无异常。
- 集群层面的异常状态（#1, #3, #4）一致指向 `ImagePullBackOff`，并确认未发生过启动尝试（#4 restart_count=0）。
- 日志与追踪缺失（#5）进一步排除了 Pod 内部运行时问题。
- 综合事实 #1 中的错误消息直接锁定了镜像配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置引用了预留域名 registry.invalid → DNS 解析失败（lookup registry.invalid: no such host） → 镜像拉取失败（ImagePullBackOff） → Pod 状态持续 Pending 且未就绪
```

### 根因结论

已确认的根因是：Pod `workload-65b7f54794-nqrzv` 的容器配置了无效的镜像仓库地址 `registry.invalid/aiops/workload:missing`。
- 该错误导致运行时在执行 DNS 解析时因域名不存在而拉取镜像失败（`ImagePullBackOff`）（证据 #1）。
- 镜像拉取失败致使容器始终处于等待状态，Pod 无法就绪（证据 #3, #4）。
- 资源配额正常，且无日志输出（证据 #2, #5），进一步确认问题出在镜像配置阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.4s
├─ 并发证据采集: 39.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 39.6s (Evidence 33.1s, RCA 6.3s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
