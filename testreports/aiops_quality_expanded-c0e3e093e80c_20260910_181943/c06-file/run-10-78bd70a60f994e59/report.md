## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v09/workload` | CrashLoopBackOff | 容器启动命令硬编码读取 '/input/app.conf'，但该路径在 Pod 配置中仅挂载了空的 EmptyDir 卷（未挂载真实配置文件），导致进程启动时因 FileNotFoundError 异常退出，进而触发 kubelet 的 CrashLoopBackOff 机制。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Container `app` exit code: 1; Reason: Error | 终止状态与异常退出直接关联 |
| 2 | K8s State | kubernetes | Container `app` Reason: CrashLoopBackOff | 处于重试循环状态 |
| 3 | K8s Config | kubernetes | Pod 配置仅挂载空 `EmptyDir` 卷至 `/input/` 路径 | 证实应用启动命令引用的配置文件路径不存在 |
| 4 | K8s Event | kubernetes | Warning BackOff restarting failed container app (x43 over 13m) | 记录异常退出的时间跨度与频率 |
| 5 | K8s Config | kubernetes | CPU Limit: 50m, Request: 5m; Memory Limit: 32Mi, Request: 8Mi | 排除资源配额引发的 OOM/Killed 终止 |
| 6 | Logging | elasticsearch | `FileNotFoundError` at `/usr/local/lib/python3.14/pathlib/__init__.py:787` | 确认应用启动时因找不到文件而抛出标准异常 |
| 7 | Logging | elasticsearch | `Traceback (most recent call last):\n    from pathlib import Path; print(Path('/input/app.conf').read_text())` | 直接证明应用硬编码读取 `/input/app.conf` 是触发上述异常的代码行 |
| 8 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}` = 1 | 确认 Pod 当前处于等待重试状态 |

**证据关联说明**：K8s State 提供的 CrashLoopBackOff 状态和 Event 记录的长时间重试，与 Metric 监控指标一致。关键证据在于 Logging 中的 Python 错误堆栈直接指出了 `FileNotFoundError` 发生在 `Path('/input/app.conf').read_text()`，结合 K8s Config 中确认该路径仅为空 EmptyDir 挂载，确立了配置缺失导致进程启动失败的完整逻辑链条。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 挂载的空 EmptyDir 卷（/input/） → 应用启动命令读取 `/input/app.conf` 失败 → 抛出 FileNotFoundError (exit code 1) → 容器崩溃并触发 CrashLoopBackOff 重试循环
```

### 根因结论

**已确认的根因**：容器启动配置与集群挂载配置不匹配。应用启动命令硬编码读取 `/input/app.conf` 文件，但该路径在 Pod 中仅仅被配置为空的 `EmptyDir` 卷，导致进程启动时因找不到文件（FileNotFoundError）而异常退出（exit code 1），进而触发 Kubernetes 的 CrashLoopBackOff 机制。
- **支持证据**：
  - 终止状态与退出码：`fact-232d530e3cd5` (Reason: Error), `fact-1028ea202e98` (exit code 1)。
  - 应用错误堆栈：`fact-bd3424bfb9ca` (读取 /input/app.conf 的 Traceback), `fact-0d0fa82a82e1` (FileNotFoundError)。
  - 资源状态：`fact-b911581b9a5d` (CrashLoopBackOff), `fact-217c782d62bf` (BackOff Event)。
- **排除因素**：CPU (50m) 和 Memory (32Mi) 资源限制充足 (`fact-2ce6981b4d48`, `fact-d38624094aea`)，无 OOM 终止记录。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.5s
├─ 并发证据采集: 40.4s
│  └─ g1 aiops-case-v09/workload: 40.4s (Evidence 34.4s, RCA 5.9s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-v09/workload**: pod-crashloop-runtime
