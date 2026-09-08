## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` `last_terminated_reason`: OOMKilled; `last_exit_code`: 137 | 判定异常的直接性质 |
| 2 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app ... (x315 over 84m)` | 确认为 CrashLoopBackOff 循环重启 |
| 3 | K8s Config | Kubernetes | Container `app` `resource_limit.memory`: 64Mi | 内存硬限制配置 |
| 4 | Logging | Elasticsearch | Pattern `memory allocation advanced`: 在 22s 内 `allocated_mib` 从 24 增长至 46 (min 24.0, max 46.0) | 证实 `/work` 请求持续增加内存占用 |
| 5 | Tracing | Tempo/Deepflow | `GET /work` 返回 200，标记 `oom_growth`，Flow 持续成功 (01:26 - 01:50) | 验证业务请求在触发 OOM 前是成功的 |
| 6 | K8s State | Kubernetes | Container `app` `restart_count`: 18 | 反映频繁重启的历史状态 |

**证据分析：**
Kubernetes 状态明确显示 `app` 容器因 `OOMKilled` (Exit Code 137) 终止并进入 `BackOff` 重启循环（证据 1, 2）。日志与追踪数据互相印证了根因触发路径：`GET /work` 请求在处理过程中持续进行内存分配（证据 4, 5），当内存增长超过硬限制 `64Mi`（证据 3）时，导致容器被系统 OOM Kill。

## 🎯 根因分析 · g1

### 因果链

```text
`GET /work` 请求持续分配内存 (max 46 MiB) → 超出 64Mi 内存硬限制 → 触发 OOMKilled (Exit 137) → 容器 CrashLoopBackOff
```

### 根因结论

**根因确认**：Pod `workload-5c9c7b6489-wmjhr` 的容器 `app` 内存硬限制被配置为 `64Mi`（证据 3），其处理 `/work` 请求时内存使用量增长过快，最高已达 46MiB 仍持续上升（证据 4, 5），最终突破 64MiB 上限。这导致内核 OOM Killer 终结进程（Exit Code 137），进而引发 kubelet 的 CrashLoopBackOff 重启（证据 1, 2）。

**缺失环节**：当前事实仅显示单次时间窗口下的内存增长快照。未能获取应用内存工作集（working set）的完整时间序列趋势数据，也未直接确认 Deployment YAML 中的精确限制声明（仅通过事实值推导），但现有证据已足以确立 OOM 为直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 7.4m
├─ 问题定位: 23.5s
├─ 并发证据采集: 409.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 409.3s (Evidence 397.9s, RCA 11.2s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
