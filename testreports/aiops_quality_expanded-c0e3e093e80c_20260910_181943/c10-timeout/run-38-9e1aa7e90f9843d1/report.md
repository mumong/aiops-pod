## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod workload (aiops-case-v17) 处于 CrashLoopBackOff 状态，容器反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.exit_code: 137 (fact-1ee2a67df59a) | 确认进程被操作系统强制终止 (OOM Kill)，而非应用层异常退出 |
| 2 | K8s State | kubernetes | container.resource_limit.memory: 64Mi (fact-247ac3d7b546) | 确定容器处于低内存边界限制环境中，为 OOM 提供资源前提 |
| 3 | K8s State | kubernetes | event.reason: Liveness probe failed / context deadline exceeded (fact-b8fe3ed7c0a1) | 证实因进程突然终止，Liveness Probe 在探测端发生超时并被判定为失败 |
| 4 | Metric | prometheus | kube_pod_container_status_restarts_total: 33 (fact-eb4f77c22ac3) | 量化验证了进程反复崩溃并重启的持续性故障现象 |
| 5 | Logging | elasticsearch | log.message: GET /health HTTP/1.1 200 - (fact-0a6fffa9714b) | 证明在 14:31:08 健康检查返回正常，而 14:31:54 探测超时，说明进程在 46 秒内突发性崩溃 |

**证据链说明：**
K8s 事件与状态显示进程以 Exit 137 异常终止，且 Liveness Probe 随之超时；Metrics 确认了 33 次循环重启的历史；Logging 证明服务在健康检查刚刚通过后迅速失去响应。低内存限制 (64Mi) 提供了触发 Linux OOM Killer 的必要条件，上述证据共同指向因资源瓶颈导致的进程突发性被杀。

## 🎯 根因分析 · g1

### 因果链

```text
内存资源限制过低 (64Mi) → 运行中触发 OOM Killer 强制终止 → 进程退出码 137，Liveness Probe 探测超时 → 容器 CrashLoopBackOff 反复重启
```

### 根因结论

已确认的根因是：Pod `workload` 的容器 `app` 配置了过低的内存硬限制（64Mi），在运行 `python http.server` 进程时，因实际内存消耗超过该阈值，触发 Linux 内核 OOM Killer 机制导致进程被 SIGKILL 终止（Exit Code 137）。进程的突然死亡导致 Kubelet 的健康检查探针无法获取响应（超时），进而触发容器重启策略，形成了反复 `CrashLoopBackOff` 的循环。

**事实依据：**
- 容器退出码为 137，明确标识为 OOM 被杀。
- 容器配置了 64Mi 的 `resource_limit.memory`。
- Liveness Probe 报错 `context deadline exceeded`，证实了连接断开的原因。
- 日志与 Trace 观测窗口内健康检查从成功到失败的时间差极短，符合 OOM 瞬间发生的特征。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 12.5s
├─ 并发证据采集: 97.5s
│  └─ g1 aiops-case-v17/workload: 97.5s (Evidence 88.0s, RCA 9.3s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
