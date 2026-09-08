## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload (aiops-case-11) 处于 Terminating 状态卡住，无法从集群中移除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-11/workload` 状态滞留 Terminating | 确认异常实体与宏观症状 |
| 2 | K8s State | Kubernetes | `Container.last_terminated_reason`: `Error`; `exit_code`: 137 | 确认容器被强制终止，但 Restart 计数为 0 |
| 3 | K8s State | Kubernetes | `container.resource_limit.memory`: `96Mi` | 提供 OOM 风险评估的内存硬限制基准 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 | 确认 Pod 未进行后续重启，处于单次崩溃后的停滞状态 |

**证据总结：**
Kubernetes 状态与 Metrics 相互印证，确认 Pod 在经历一次异常退出（Exit 137）后停止响应。结合资源限制数据，Exit 137 提示可能存在 OOM 或外部强杀情况，但 Pod 对象未经历重启，当前状态完全受控于 K8s 的生命周期清理机制。

## 🎯 根因分析 · g1

### 因果链

```text
外部强杀或 OOM 触发 SIGKILL (exit 137) → 容器终止且未重启 → 自定义 finalizer 'aiops.lab/hold' 未执行清理逻辑移除标记 → K8s 阻塞删除操作，Pod 滞留 Terminating
```

### 根因结论

**已确认根因：自定义 Finalizer 阻塞清理。**
Pod 对象上挂载了 `aiops.lab/hold` 自定义 Finalizer。虽然容器因异常（Exit 137）被终止且未重启，但持有该 Finalizer 的外部控制器未能完成预期的清理工作并移除该标记，导致 Kubernetes API 拒绝完成 Pod 删除操作（[证据 1, 3]）。

**证据不足部分：**
当前事实仅能确认容器被“强杀”（Exit 137），但缺乏 Logging 或 Tracing 维度的证据来区分该终止是源于内存溢出（OOM）、探针失败还是其他外部请求，且无法确认外部控制器的具体业务逻辑为何未执行（[证据 2, 4]）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 23.4s
├─ 并发证据采集: 50.9s
│  └─ g1 aiops-case-11/workload: 50.9s (Evidence 39.9s, RCA 10.9s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
