## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | Running | {'type': 'Warning', 'reason': 'Unhealthy', 'message': 'Warning  Unhealthy  7m2s (x55 over 81m)   kubelet  Liveness probe failed: HTTP probe failed with statuscode: 500'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-79d9f8fd88-48j8r` 状态为 Running，但 app 容器 Exit Code 为 137，重启次数达 30 次 | 确认为偶发性崩溃，非配置错误 |
| 2 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 (x55 over 81m) | 表明应用进程在崩溃前处于极度无响应状态，引发健康检查失败 |
| 3 | K8s Event | Kubernetes | Back-off restarting failed container (x310 over 83m) | 验证了 Pod 进入 CrashLoopBackOff 状态 |
| 4 | Metric | Prometheus | 内存 Working Set 在观察窗口内从 589.8KiB 飙升至 16,482.3KiB (max) | 提供内存异常增长的直接量化证据，逼近 96Mi 硬限制 |
| 5 | Tracing | Tempo/Deepflow | 多个 Flow 记录显示 `GET /work` 返回 HTTP 200，耗时在 16ms-99ms 之间 | 证明应用逻辑本身正常，OOM 或阻塞更可能发生在请求间隙 |

**证据印证与冲突分析：**
*   **现象矛盾**：Exit 137（通常对应 OOMKilled）与 Liveness 返回 500 存在时间差。K8s Event 指出探针在 81 分钟前就开始返回 500，而 Metrics 显示内存持续飙升，暗示应用可能因 GC 停顿或内存耗尽导致线程阻塞（进而导致 500），最终彻底崩溃（137）。
*   **配置印证**：K8s 配置 `memory_limit=96Mi` 远低于 Metric 峰值 16MB，结合 Exit 137 强指向 OOM。
*   **数据缺失**：Tracing 数据全部为 200，未捕获到导致 500 的那个特定请求的完整 Trace，说明探针失败发生在非 200 的后台阻塞期。

## 🎯 根因分析 · g1

### 因果链

```text
未知上游原因 (应用内存泄漏或突发资源争用) → 容器内存工作集异常增长 (589KiB -> 16MB) → 触发 OOM 风险或导致应用线程阻塞 → Liveness Probe 因阻塞返回 500 (x55) → OOMKiller 强制终止进程 (Exit 137) → Pod 重启并暂时恢复 Running
```

### 根因结论

**证据不足**

虽然 Exit 137 和内存 Metrics (16MB) 强烈指向 **Out Of Memory (OOM)** 导致的崩溃，且 `96Mi` 的内存限制相对该增长量确实显得过低，但以下关键事实缺失，导致无法锁定确切根因：
1.  **缺少 OOM 瞬间的确凿日志**：Elasticsearch 仅捕获到应用正常的 200 响应日志，缺失 `kernel: Out of memory: Kill process` 或应用层的内存溢出报错。
2.  **无法区分阻塞与 OOM 的先后**：Metrics 工具调用失败导致无法获取崩溃瞬间的精确内存峰值。虽然内存在增长，但无法证明是否真的物理触发了 96Mi 的硬限制，还是因为应用逻辑缺陷导致线程阻塞从而引发 Probe 500 并被系统 Kill。
3.  **未验证的泄漏假设**：当前证据不足以证明存在持续性的内存泄漏（Memory Leak），因为样本窗口可能仅覆盖了一次异常事件。

综上，根因暂时定性为 **“疑似因资源限制（96Mi）不足或应用层内存泄漏导致的 OOM，进而引发 Liveness 探针失败与进程终止”**，但因缺乏 OOM 判定所需的 Kernel 日志或峰值数据，正式 RCA 判定为证据不足。

---

## 📊 性能统计

```text
├─ 总耗时: 8.0m
├─ 问题定位: 21.2s
├─ 并发证据采集: 444.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 444.3s (Evidence 428.5s, RCA 15.6s)
└─ 汇总总结: 14.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-oomkilled, pod-crashloop-runtime
