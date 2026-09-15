## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v09/workload` | CrashLoopBackOff | Pod aiops-case-v09/workload 处于 CrashLoopBackOff 状态，启动失败并反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 113s (x290 over 66m) kubelet Back-off restarting failed container app in pod workload_aiops-case-v09(5746c496-b67c-4906-aabb-e71359674305)` | 确认 Pod 进入 CrashLoopBackOff 并触发指数级退避 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`；`container.last_exit_code: 1` | 证实容器异常退出且终止原因为 Error |
| 3 | K8s State | Kubernetes | `pod.condition Ready: False (ContainersNotReady)`；`restart_count: 17` | 反映容器无法就绪并频繁重启的状态 |
| 4 | Logging | Elasticsearch | `Traceback (most recent call last):` ... `FileNotFoundError: [Errno 2] No such file or directory: '/input/app.conf'` | 提供根因核心日志，指向文件缺失 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason(Error): 1`；`kube_pod_container_status_restarts_total: 17` | 与 K8s 状态和日志现象交叉印证 |

证据互相印证：Kubernetes 事件 (fact-3bbd9a00f2b3) 记录了 290 次重试和指数退避，直接对应 Prometheus 指标 (fact-74ba61d5d5e3) 中 17 次重启计数和终止状态 Error；Elasticsearch 日志 (fact-3fb4dc88620e) 提供了最底层的技术原因：Python 进程启动时尝试读取 `/input/app.conf` 失败抛出 FileNotFoundError，这解释了为何容器会异常退出 (Exit Code 1) 并触发 K8s 的重启与退避机制。

## 🎯 根因分析 · g1

### 因果链

```text
EmptyDir卷 'input' 中缺失配置文件 '/input/app.conf' → 容器启动命令尝试读取该路径 → Python 进程抛出 FileNotFoundError 并 exit(1) → 触发 Kubernetes CrashLoopBackOff 重启策略
```

### 根因结论

已确认的根因是**配置文件缺失**。
容器启动命令引用了路径 `/input/app.conf`，但该文件在挂载的 EmptyDir 卷中不存在（证据编号：#4, fact-3fb4dc88620e）。这导致 Python 进程启动即报错退出（Exit Code 1, 证据编号：#2, fact-2b0c72d52f23），进而触发 Kubernetes 的重启机制，最终表现为 Pod 处于 CrashLoopBackOff 状态（证据编号：#1, fact-3bbd9a00f2b3；#3, fact-9d313d7b023d；#5, fact-29c882c013b8）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 13.6s
├─ 并发证据采集: 45.2s
│  └─ g1 aiops-case-v09/workload: 45.2s (Evidence 34.4s, RCA 10.7s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v09/workload**: pod-crashloop-runtime
