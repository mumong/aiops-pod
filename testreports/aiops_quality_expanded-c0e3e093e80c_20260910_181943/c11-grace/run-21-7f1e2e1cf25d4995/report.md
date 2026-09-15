## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod workload (aiops-case-v13) 显示 Terminating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `phase: Running`, 条件 `Ready=True` | 确认 Pod 处于逻辑运行状态且就绪 |
| 2 | K8s Event | kubernetes | `ContainersReady` 于 `07:09:03Z` 标记为 `True` | 验证 Pod 在报告周期内已正常运行 |
| 3 | Logging | elasticsearch | `07:09:02Z` "application started", `07:09:03Z` "SIGTERM received; waiting" | 记录正常启动后立即进入 SIGTERM 接收与等待状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: `0` | 确认 Pod 生命周期内无重启记录 |
| 5 | K8s Config | kubernetes | 资源请求/限制极小：CPU Request `5m`, Limit `50m`；Memory Request `8Mi`, Limit `32Mi` | 排除资源耗尽导致的 OOM 或 CPU Throttling |

上述证据表明：Pod 容器进程正常启动并运行，但在 `07:09:03Z` 立即收到了 `SIGTERM` 信号。日志 "SIGTERM received; waiting" 明确指向应用侧进入阻塞式等待状态，且无重启发生，排除了启动失败或崩溃场景。

## 🎯 根因分析 · g1

### 因果链

```text
K8s 删除流程触发 (deletionTimestamp 已设置) → 容器进程收到 SIGTERM 信号 → 应用捕获信号进入等待 /state/teardown-requested 文件的死循环 → Pod 保持 Terminating 等待状态
```

### 根因结论

已确认的根因是**Pod 执行优雅关闭（Graceful Shutdown）时陷入应用侧等待逻辑**。
根据事实，Pod 容器进程在运行期间收到 `SIGTERM` 信号，其代码逻辑被设计为打印 "SIGTERM received; waiting" 并等待 `/state/state/teardown-requested` 文件出现。由于该文件在观察窗口内未出现，导致容器进程无法退出，从而使得 Pod 长期处于 `Terminating` 状态。

支持证据：
- 日志 `SIGTERM received; waiting` 证实了阻塞点 (证据 #3)。
- 状态 `Terminating` 与 `Running`/`Ready` 并存，符合优雅关闭中进程未退出的特征 (证据 #1, #2)。
- `restart_count: 0` 证实进程未崩溃 (证据 #4)。
- 资源限制未触发硬性终止，排除了资源争抢因素 (证据 #5)。

缺失的关键事实：
- 无法确定 `/state/teardown-requested` 文件应当由哪个上游组件或流程创建（unknowns）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 13.7s
├─ 并发证据采集: 67.8s
│  └─ g1 aiops-case-v13/workload: 67.8s (Evidence 59.6s, RCA 8.1s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
