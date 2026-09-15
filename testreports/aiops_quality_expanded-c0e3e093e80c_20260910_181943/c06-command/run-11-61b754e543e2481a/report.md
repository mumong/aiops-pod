## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod `aiops-case-v08/workload` 处于 CrashLoopBackOff 状态，容器 `app` 反复重启失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `container.waiting_reason`: `CrashLoopBackOff` | 确认 Pod 处于反复重启故障状态 |
| 2 | K8s Event | `kubernetes` | `BackOff` 事件 (x48)：`back-off 5m0s restarting failed container=app` | 证明容器失败已持续约 13 分钟且退避延迟增加 |
| 3 | K8s State | `kubernetes` | `container.last_terminated_reason`: `Error` | 确认上一次容器退出状态为异常终止 |
| 4 | Logging | `elasticsearch` | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 提供决定性根因：启动命令引用的可执行文件不存在 |
| 5 | K8s State | `kubernetes` | `container.last_exit_code`: `127` | 操作系统标准码：命令未找到，与日志完全一致 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_restarts_total`: `7` | 量化重启次数，印证 K8s 状态中多次重启的现象 |

**证据印证分析：**
Kubernetes 事件与状态指标（#1, #2, #6）从宏观层面证实了应用处于 `CrashLoopBackOff` 且持续退避重启。决定性证据来自日志（#4）与退出码（#5）的精确匹配：日志明确指出了文件缺失路径，而 `127` 退出码是 Linux 系统对“命令未找到”的标准响应。这两者互为因果证据，直接指向配置或镜像问题。

## 🎯 根因分析 · g1

### 因果链

```text
镜像中缺失可执行文件 (/opt/app/unavailable-command) → 容器执行启动命令失败 (exit code 127) → 容器被 OOM/Error 终止并触发 Kubelet 重启机制 → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**应用镜像配置错误**（缺少启动所需的二进制文件）。

- **证据编号 4** (Logging) 明确捕获到容器内部执行日志显示 `/opt/app/unavailable-command: not found`。
- **证据编号 5** (K8s State) 确认容器以 `127` 错误码退出，这是典型的“未找到可执行命令”的系统级信号，且与日志内容完全吻合。
- **证据编号 1 & 2** (K8s State & Event) 记录了下层错误导致的上层表现：由于启动即失败，导致 Pod 反复进入 `CrashLoopBackOff` 状态。

现有证据链闭环，可排除资源不足、网络故障或节点问题等其他故障模式。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 27.4s
├─ 并发证据采集: 35.3s
│  └─ g1 aiops-case-v08/workload: 35.3s (Evidence 27.8s, RCA 7.4s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
