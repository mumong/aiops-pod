## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | Running | 应用容器内存使用量持续增长并突破 64MiB 硬限制 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff  4m31s (x415 over 112m) kubelet  Back-off restarting failed container app in pod workload-5c9c7b6489-fl85h` | 证实应用容器 `app` 经历了长达 112 分钟的频繁重启，且已进入指数退避等待状态。 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory: 64Mi` | 确认应用容器的内存硬限制，为判断越限提供基准。 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason: OOMKilled` | 明确上次容器终止原因为内存溢出，是触发重启的直接机制。 |
| 4 | K8s State | kubernetes | `container.waiting_message: back-off 5m0s restarting failed container=app` | 说明当前容器因反复失败而处于等待退避状态，无法正常运行。 |
| 5 | K8s State | kubernetes | `container.restart_count: 23` | 量化重启频次，反映该异常在长时间内持续发生且未被解决。 |
| 6 | Metric | prometheus | `container_memory_working_set_bytes` (last restart sample): `first=21733376.0 -> last=55418880.0` | 展示上一轮重启前内存持续上升的趋势，接近 64MiB 阈值。 |
| 7 | Metric | prometheus | `container_memory_working_set_bytes` (current): `max=62021632.0` | 确认当前容器在崩溃前的内存峰值约为 62MB，已逼近并突破 64MiB 限制。 |
| 8 | Logging | elasticsearch | `pattern: http_request memory allocation advanced; allocated_mib: first=12 -> last=40` | 记录应用在处理 HTTP 请求时内存分配持续增加，佐证内存泄漏或增长行为。 |

**证据综合说明**：
- **状态与机制印证**：K8s 状态（#1, #3, #5）清晰展示了“OOMKilled 触发 -> 容器退出 -> kubelet 重启 -> 频繁 BackOff”的循环机制。
- **数据趋势支撑**：Metric 数据（#6, #7）与 Logging 数据（#8）在时序上均显示容器在运行期间内存使用量显著增加，且最终逼近硬限制（64MiB，#2），与 OOMKilled 状态高度吻合。
- **跨维度关联**：Logging 中记录的应用内存分配模式，为 K8s 层面因内存越限导致 OOMKilled 提供了应用行为层面的直接旁证。

## 🎯 根因分析 · g1

### 因果链

```text
应用容器内存持续增长(Metric/Logging) → 突破 64MiB 硬限制(K8s Config) → 触发 OOMKilled(K8s State) → 应用频繁重启并陷入 BackOff 等待(K8s Event)
```

### 根因结论

已确认根因为：**应用容器 `app` 在运行过程中内存使用量持续增长，最终突破 `64MiB` 的硬限制，被 Kubernetes 强制终止（OOMKilled）**。

该结论由以下事实充分支撑：
1. **终止原因**：K8s 明确指出最近一次终止原因为 `OOMKilled`（证据 #3）。
2. **越限证据**：Metric 采样显示容器内存峰值达到 62MB，逼近且结合 OOMKilled 事实确认突破了 64MiB 限制（证据 #2, #6, #7）。
3. **行为模式**：Logging 记录显示应用在处理请求时内存分配持续增加（证据 #8），Metric 也记录了多轮重启前的内存递增趋势（证据 #6），表明这是一个持续的内存消耗过程而非偶发波动。
4. **后果确认**：容器因反复 OOM 终止已导致 23 次重启，并进入长时间的 BackOff 状态，服务当前不可用（证据 #1, #4, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 19.9s
├─ 并发证据采集: 98.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 98.9s (Evidence 92.0s, RCA 6.6s)
└─ 汇总总结: 14.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled, pod-crashloop-runtime
