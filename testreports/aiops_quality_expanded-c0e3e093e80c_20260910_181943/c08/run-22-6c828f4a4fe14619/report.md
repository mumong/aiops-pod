## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | Running | Pod aiops-case-08/workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态，重启16次，exit code 137 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` (fact-03bc44eac66c) | 直接证明容器因内存超限被系统杀死 |
| 2 | K8s State | Kubernetes | `container.last_exit_code: 137` (fact-30d4468bb37f) | 137 是 Linux 收到 SIGKILL 的 Exit Code，佐证 OOM 事件 |
| 3 | K8s Event | Kubernetes | `BackOff ... Back-off restarting failed container app` (fact-6f6fce4ed6b3) | 确认 Pod 处于 CrashLoopBackOff 循环重启状态 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` (fact-4665b8b51136) | 容器硬内存上限为 64Mi，限制极低 |
| 5 | Logging | Elasticsearch | `allocated_mib` 从 14 增至 48 (fact-2a54da1448c6 聚合, 窗口: 34秒) | 应用内存在短时间窗口内快速累积，逼近 64Mi 上限 |
| 6 | Tracing | Deepflow | L7 Flow: `GET /work` `response_code: 200`, 9次记录 (fact-46026be2fb04 聚合) | 证明 `/work` 接口被频繁调用，是内存分配的源头 |
| 7 | Tracing | Tempo | Span: `GET /work`, `attributes: aiops.observed_mode: oom_growth` (fact-0308cadd2cc5) | 追踪数据确认该接口调用伴随内存增长模式 |

**证据关联说明：**
Kubernetes 的 OOMKilled 信号（事实 1、2）与 Logging 观测到的内存快速分配（事实 5）高度一致。Tracing 数据（事实 6、7）锁定了 `/work` 接口为内存增长的触发源。结合 Kubernetes 配置（事实 4），形成了“接口高频调用导致内存分配”->“突破 64Mi 限制”->“OOMKilled”的闭环证据。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /work 接口存在内存累积 (每轮增加约 2MiB) → 容器总内存突破硬限制 64Mi → 触发 Linux OOM Killer (Exit Code 137) → 容器终止并陷入 CrashLoopBackOff 重启
```

### 根因结论

- **根因确认**：容器内存限制配置过低（`64Mi`），而应用在 `/work` 接口存在内存分配累积行为，最终导致 OOMKilled。
- **证据支撑**：
  - 配置证据：事实 4 显示内存限制仅为 64Mi。
  - 现象证据：事实 1、2 确认了 OOMKilled 和退出码 137。
  - 机制证据：事实 5 显示内存从 14MiB 快速升至 48MiB，事实 6 显示 `/work` 接口被高频访问。
- **结论**：应用内存增长速率与容器资源限制（64Mi）不匹配，导致 OOM。

**未确认事项**：
- 确切导致首次触发 OOM 的总内存峰值（堆+非堆）未知（事实 1 仅显示终止原因，无峰值数值）。
- 是否存在更深层的底层内存泄漏模式（如 Goroutine 或 C 泄漏）未知。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 50.2s
├─ 并发证据采集: 101.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 101.2s (Evidence 87.9s, RCA 13.2s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-oomkilled, pod-crashloop-runtime
