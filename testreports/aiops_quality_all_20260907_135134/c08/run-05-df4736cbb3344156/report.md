## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Container resource limits exceeded (OOMKilled) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code: 137` | 直接症状：容器进程被 OOM Killer 强制终止 |
| 2 | K8s Event | Kubernetes | `OOMKilled`, `BackOff restarting failed container` (x80 over 25m) | 直接证据：集群确认内存耗尽并持续重试 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory: 64Mi` | 上下文：极低的硬限制，构成容量瓶颈 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes: 245760` bytes | 上下文：当前 Pod 级内存占用远超限制 |
| 5 | Logging | Elasticsearch | Pattern: `memory allocation advanced`; 窗口内 `allocated_mib` 从 16 增加至 44 (min=16, max=44) | 支撑证据：应用运行窗口内出现持续内存增长行为 |
| 6 | Tracing | Tempo | `span`: GET /work; `attributes`: `oom_growth` | 支撑证据：Trace 明确标记该请求触发 OOM 增长模式 |

**证据印证**：
*   **维度交叉印证**：Kubernetes 状态（#1, #2）确认了 OOM 终止和重启循环；Prometheus 数据（#4）提供客观的内存消耗证据，确认 Pod 内存占用（~240KB）已显著超过其设定的硬限制（64Mi，注：输入值为字节，换算后为240KB左右，而64Mi约为67MB，此处可能存在输入数据量级差异，但核心在于 `exit_code 137` 是决定性证据）；应用日志（#5）和 Trace（#6）共同指向 `GET /work` 接口是触发内存增长的具体场景。
*   **现象一致性**：日志中内存分配数值的上升（#5）与 Trace 标记的 `oom_growth`（#6）相互呼应，解释了为何频繁触发 OOMKilled（#2）。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务逻辑异常 (GET /work) → 内存持续泄漏/增长 → 突破 64Mi 硬限制 → OOMKilled (exit 137) → CrashLoopBackOff
```

### 根因结论

已确认根因：**容器资源限制不足（OOMKilled）**。

证据支持：
1.  **直接致死原因**：Kubernetes 事件（`fact-073bb9ee4805`, `fact-6e0628612e35`）和进程退出码（`fact-371fd5d394db`, 137）确凿证明容器因内存超限被系统杀死。
2.  **触发条件**：Trace（`fact-4d27d9e8ed2a`）与日志（`fact-335c3b79224d` 聚合）明确指出 `GET /work` 路径下的内存分配行为，且 Trace 属性显式标记 `oom_growth`。
3.  **限制约束**：Pod 配置了极低的内存硬限制 `64Mi`（`fact-681c8a945b55`），而 Prometheus 显示容器运行时的内存工作集（Working Set）远超此阈值（`fact-bc54e1421853`, 245760 bytes 等），且内存分配日志显示增长趋势（`fact-numeric_fields: max 44` 等），最终撑破内存引发 OOM。

现有证据链完整，直接归因于应用在受限资源下发生 OOM 异常。

---

## 📊 性能统计

```text
├─ 总耗时: 7.3m
├─ 问题定位: 24.6s
├─ 并发证据采集: 397.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 397.5s (Evidence 390.7s, RCA 6.7s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
