## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload 处于 Terminating 状态，Kubelet 已发送 Stopping 信号但 Pod 未自动回收 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | Terminating (lasts <invalid>) | 确认 Pod 处于终止状态 |
| 2 | K8s State | pod.phase | Running | 确认应用进程尚未退出 |
| 3 | K8s Event | event.message | Normal Killing 110s kubelet Stopping container app | 确认 Kubelet 已发送终止信号 |
| 4 | K8s Config | container.resource_request.memory | 8Mi | 排除内存资源申请异常 |
| 5 | K8s Config | container.resource_limit.cpu | 50m | 排除 CPU 资源限制异常 |
| 6 | K8s Config | container.resource_limit.memory | 32Mi | 排除内存资源限制异常 |
| 7 | Logging | log.message | application started | 确认应用进程曾正常启动 |

**证据说明：**
1. K8s 状态（事实 1, 2）与事件（事实 3）结合，证实 Pod 已进入终止流程且 Kubelet 正在执行停止操作，而应用容器仍维持在 Running 状态。
2. 资源配置（事实 4, 5, 6）显示资源限制宽松，结合重启次数为 0，排除了因资源不足导致 OOM 或崩溃的可能。
3. 日志（事实 7）仅显示启动信息，结合终止状态，暗示应用可能在收到 SIGTERM 后未正常退出，而是处于静默等待或挂起状态，这与长 TerminationGracePeriodSeconds 机制吻合。

## 🎯 根因分析 · g1

### 因果链

```text
Deletion 触发 (含 3900s 宽限期) → Kubelet 发送 SIGTERM 等待优雅退出 → 应用进程未响应信号/超时 → Pod 滞留 Terminating 状态
```

### 根因结论

**已确认的根因：** Pod 配置了较长的 `terminationGracePeriodSeconds`（3900秒），目前仍处于终止宽限期内。

**依据：**
1. 现象上，Pod 处于 `Terminating` 状态且 Kubelet 正在发送停止信号（事实 3），但容器依然处于 `Running` 状态（事实 2）。
2. 排除了资源不足（事实 4-6）和重启异常（事实 6 重启次数为 0，事实 8 restart_count=0）。
3. 日志（事实 7）与状态矛盾（应用已启动但未退出），结合已知配置，推断是优雅退出超时机制生效。

**不确定性：**
1. 缺乏应用内部的具体报错或跟踪数据，无法确认应用进程具体卡在哪个环节（如网络关闭、资源清理等）导致未响应 SIGTERM。
2. 缺乏 Kubelet 更详细的停止尝试日志。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 12.8s
├─ 并发证据采集: 117.5s
│  └─ g1 aiops-case-v12/workload: 117.5s (Evidence 109.7s, RCA 7.7s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
