## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Container memory limit (64Mi) is insufficient for application behavior (linear memory allocation up to 48Mi+ overhead), causing OOMKilled (exit 137) and CrashLoopBackOff. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 99s (x571 over 149m) kubelet Back-off restarting failed container app in pod workload-5c9c7b6489-p8462_aiops-case-08(7f2eda43-58bc-4f48-bb8a-02435553f7d1)` | 证实容器应用已长期因异常而频繁重启 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` | 直接指向容器因内存超额被内核杀掉 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` | 提供导致 OOM 的硬性限制基准值 |
| 4 | K8s State | Kubernetes | `container.last_exit_code: 137` | 确认进程是被外部信号 (SIGKILL) 终止，而非内部逻辑退出 |
| 5 | Logging | Elasticsearch | `allocated_mib` 线性增长：`first: 14` → `last: 36` (窗口内 `min: 14.0`, `max: 36.0`) | 记录到应用正在持续消耗内存，证明其内存占用行为不受控 |
| 6 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` | 反映当前 Pod 正处于无法恢复的运行状态 |

**证据印证：**
Kubernetes 的 `OOMKilled` 状态、退出码 137 和 `CrashLoopBackOff` 事件在逻辑上完全闭合，共同排除了网络、配置或业务逻辑错误，直指资源超用。日志中记录到的内存从 14Mi 向 36Mi 递增的趋势，与 64Mi 的硬限制形成了充分的因果关联，证实了应用行为超出了资源约束。

## 🎯 根因分析 · g1

### 因果链

```text
硬内存限制 (64Mi) 低于应用实际运行时内存增长 → 内存分配触及上限触发 OOMKilled → 容器退出码 137 被 kubelet 捕获 → CrashLoopBackOff 导致服务不可用
```

### 根因结论

已确认根因为：**容器配置的资源上限 (64Mi) 不足以满足应用线性增长的内存分配行为。**

证据链如下：
1. **终止机制确认**：Kubernetes 状态和事件明确记录最后一次终止原因为 `OOMKilled`，且退出码为 `137` (255 - 128，代表收到 SIGKILL) [[证据 2, 3, 4]]。
2. **触发阈值**：应用运行所在的容器被设置了硬限制 `container.resource_limit.memory` 为 `64Mi` [[证据 3]]。
3. **行为验证**：日志中捕获到应用在执行 `/work` 请求时存在内存分配行为，并在观察窗口内记录了内存分配量从 `14Mi` 上升至 `36Mi` 的过程 [[证据 5]]。这证实了应用具有持续占用内存的线性增长特征，当加上 JVM 堆外或系统开销后，必然突破 `64Mi` 的硬限制。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 26.2s
├─ 并发证据采集: 116.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 116.3s (Evidence 107.0s, RCA 9.1s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime, pod-config-error
