## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app in pod workload_aiops-case-v08(00e5e755-886e-4661-9e8a-00d1e71595f6)` | 确认 kubelet 因容器反复失败触发退避重启机制 |
| 2 | K8s State | Kubernetes | 容器 `app` 终止原因为 `Error`，最近一次退出码为 `127` | 提供直接退出码，指向命令未找到或权限类错误 |
| 3 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 定位执行失败的具体命令及文件不存在的确切原因 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (container=app, reason=Error) 采样值 `1` | 佐证容器上次因错误退出而被系统清理 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=CrashLoopBackOff) 采样值 `1` | 佐证当前容器正处于退避等待状态，与事件记录一致 |

**证据关联：**
日志事实 (#3) 提供了 `sh: ... not found` 的确切文本，结合 K8s 事实 (#2) 中 `exit_code: 127`，两者相互印证，指向因命令不存在导致的容器启动失败；K8s 事件 (#1) 和 Metric 事实 (#4, #5) 确认了该失败触发了 Kubernetes 的重启和退避机制，完整复现了当前 `CrashLoopBackOff` 的状态。

## 🎯 根因分析 · g1

### 因果链

```text
YAML配置指定不存在的可执行文件路径 `/opt/app/unavailable-command` → 容器启动执行命令失败（退出码 127） → 容器异常终止（Error） → 用户可见 Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是：`aiops-case-v08/workload` 的 Pod 配置指定了不存在的可执行文件 `/opt/app/unavailable-command`。

该配置错误导致容器在启动阶段执行 `exec` 时失败（日志记录为 `not found`，退出码 `127`）。Kubernetes 根据容器的重启策略自动尝试重启，但因持续失败并达到退避阈值，最终将 Pod 标记为 `CrashLoopBackOff`。

证据来源：日志事实 (fact-1f26c7f41d44)、K8s State (fact-2c3e046cbd19)、K8s Event (fact-3eea1ea6998e)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.8s
├─ 并发证据采集: 43.9s
│  └─ g1 aiops-case-v08/workload: 43.9s (Evidence 34.8s, RCA 8.9s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
