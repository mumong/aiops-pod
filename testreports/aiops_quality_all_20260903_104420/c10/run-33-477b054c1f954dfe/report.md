## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | {'type': 'Warning', 'reason': 'BackOff', 'message': 'Warning  BackOff  4m43s (x346 over 95m)  kubelet  Back-off restarting failed container app in pod workload-79d9f8fd88-sbqvc_aiops-case-10(b1c01c93-0091-4506-bcbd-69cfd75e0f12)'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-9c13e45ddbb5` | 容器 `app` 退出码 `137` | 确定容器终止信号为 `SIGKILL` |
| 2 | K8s Config | `fact-60464f2b1983` | 容器内存限制 `96Mi` | 确认资源硬限制，为判断 OOM 提供边界 |
| 3 | K8s Event | `fact-2e377444d736` | `Back-off restarting failed container app` (持续 95 分钟) | 确认 Pod 处于 `CrashLoopBackOff` 循环 |
| 4 | Metric | `fact-0a0c34b29bf8` | `kube_pod_container_status_waiting_reason` 为 `1` (CrashLoopBackOff) | 确认外部监控系统同步观察到等待/重启状态 |
| 5 | Logging | `fact-09717ab98082` | 8 条 `request completed` (HTTP 200) 记录，时间窗口 `21:43:38 - 21:44:09` | 确认崩溃前应用处于正常响应请求状态 |
| 6 | Tracing | `fact-3e4c521a5e84` | 9 次 `GET /work` 请求成功 (200)，时间窗口 `05:23 - 05:42` | 确认应用流量正常，且与日志记录存在时间重叠 |

**证据关联说明**：
Kubernetes 状态明确显示容器以 `SIGKILL (137)` 异常退出并陷入重启循环 (证据 1, 3)。应用层面的日志 (证据 5) 和追踪记录 (证据 6) 显示在崩溃前应用正常接收并处理了 HTTP 请求，未记录到内存错误。Metric 数据 (证据 4) 仅作为状态确认，缺乏内存使用趋势细节，无法直接证实是内存溢出还是探针超时导致的强制终止。

## 🎯 根因分析 · g1

### 因果链

```text
容器 app 运行期间异常终止 → kubelet 尝试重启失败 → 触发 Liveness Probe 探测机制（或资源限制触发 OOM-Killer） → 标记为 CrashLoopBackOff
```

### 根因结论

**证据不足**。

现有证据证实容器 `app` 因退出码 `137` (`SIGKILL`) 被终止，但无法区分具体触发方：
1. **缺少关键日志**：无法确定是由内核 `OOM-Killer` 因超过 `96Mi` 限制（证据 2）杀除，还是由 `Liveness Probe` 探测超时后由 `kubelet` 发起的 `SIGKILL`。
2. **监控盲区**：缺乏崩溃瞬间的内存使用指标峰值记录，无法证明存在瞬时内存超限。
3. **应用层未报错**：崩溃前的日志和追踪记录均显示请求处理成功，未记录到应用层面的异常捕获。

需获取崩溃前的系统级日志（如 dmesg 或 container runtime 日志）或配置探针超时/重试参数对比，方可明确根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 17.3s
├─ 并发证据采集: 75.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 75.1s (Evidence 63.3s, RCA 11.7s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
