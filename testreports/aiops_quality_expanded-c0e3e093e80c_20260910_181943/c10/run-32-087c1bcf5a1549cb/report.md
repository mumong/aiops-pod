## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Container memory limit (96Mi) exceeded, causing OOMKilled (exit code 137) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | 容器退出码 137 | 直接确认容器被 OOMKilled |
| 2 | K8s Config | K8s | 内存硬限制 96Mi | 提供内存耗尽的直接原因 |
| 3 | K8s Event | K8s | Liveness probe failed: HTTP probe failed with statuscode: 500 | 解释 Pod 状态为何不健康 |
| 4 | K8s Config | K8s | 内存资源保留量 24Mi | 确认容器可用的内存上限为 72Mi |
| 5 | Metric | Prometheus | 容器重启总数: 13 | 佐证故障已重复发生 |

### 证据关联性分析
- 退出码 137（事实 1）与内存硬限制 96Mi（事实 2）相互印证，确认为内存超限导致的 OOMKilled 事件。
- 资源保留量 24Mi（事实 4）使得可用内存进一步缩减至 72Mi，加剧了内存溢出的风险，解释了为何 96Mi 的限制仍会导致崩溃。
- Liveness 探针 500 错误（事实 3）是 OOMKilled 导致进程不可用后的直接表象，解释了 Kubernetes 进入 CrashLoopBackOff 的机制。
- 重启数 13 次（事实 5）反映了该 OOM 事件不是偶发现象，而是常态行为。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制仅 96Mi 且保留量 24Mi（事实 2, 4） → 应用运行过程中内存占用超过 72Mi 可用空间 → 触发内核 OOMKilled 机制，强制终止进程并返回退出码 137（事实 1） → 容器崩溃退出，Liveness 探针检查失败报 500 错误（事实 3），Kubernetes 触发 CrashLoopBackOff 并不断重启（事实 5）
```

### 根因结论
已确认根因为：**容器内存限制过低导致频繁 OOMKilled**。
具体而言，Pod 的内存硬限制被设置为 96Mi（事实 2），同时保留了 24Mi 的系统级资源（事实 4），这极大地压缩了应用的实际可用内存。应用无法在如此严苛的内存空间内稳定运行，导致内存耗尽被系统强制杀死（退出码 137，事实 1），进而引发健康检查失败（事实 3）和不断重启的恶性循环（事实 5）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 26.1s
├─ 并发证据采集: 139.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 139.7s (Evidence 133.2s, RCA 6.3s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
