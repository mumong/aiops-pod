## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod `aiops-case-11/workload` 被配置了自定义 finalizer `aiops.lab/hold`，该 finalizer 阻止了 Kubernetes API 在服务/资源解绑前彻底删除 Pod。虽然应用容器已因 OOMKilled (exit code 137) 终止，但由于 finalizer 机制未解除，Pod 处于 Terminating 状态滞留。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-11/workload` phase: Running, status: Terminating (lasts 72m), Ready: False | 确认 Pod 处于无法退出的 Terminating 状态 |
| 2 | K8s Event | Kubernetes | Exit Code: 137 | 指示容器因 OOMKilled 被内核杀掉 |
| 3 | K8s Config | Kubernetes | resource_limit.memory: 96Mi | 定义内存硬限制，支撑 OOM 发生条件 |
| 4 | K8s Config | Kubernetes | resource_request.memory: 24Mi | 定义调度保留量 |

当前日志与链路追踪（Logging/Tracing）数据为空，K8s 状态与事件已充分揭示退出与滞留机制。

## 🎯 根因分析 · g1

### 因果链

```text
资源限制不足/内存溢出 → 容器被 OOMKilled (exit code 137) → Kubernetes 触发终止流程 → 自定义 finalizer `aiops.lab/hold` 阻止彻底删除 → Pod 长期滞留 Terminating
```

### 根因结论

已确认的根因是 Pod 被配置了自定义 finalizer `aiops.lab/hold`（诊断详情描述引用），该机制阻止了 Kubernetes API 在完成服务解绑前彻底删除 Pod。容器因 `Exit Code: 137`（OOMKilled）已终止，但清理流程被 finalizer 阻断，导致 Pod 持续处于 Terminating 状态达 72 分钟（证据 #1, #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 19.8s
├─ 并发证据采集: 79.4s
│  └─ g1 aiops-case-11/workload: 79.4s (Evidence 73.5s, RCA 5.8s)
└─ 汇总总结: 5.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
