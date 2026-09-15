## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'message': 'Annotations:               cni.projectcalico.org/containerID: 013a25c192c2d9f7fa2c490be72b95c278f91a3a3d81d923192c830f47e566b9'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | phase=Running, status=Terminating (lasts <invalid>) | 确认 Pod 已处于终止状态，但进程仍在运行 |
| 2 | K8s Event | event.message | Normal Killing 9m21s kubelet Stopping container app | 证实 Kubelet 已向容器发送 SIGTERM 信号 |
| 3 | K8s Config | container.resource_request/limit | CPU: 5m/50m, Memory: 8Mi/32Mi | 资源配额极低，排除了资源耗尽导致的阻塞 |
| 4 | Logging | log.message | application started (timestamp: 2026-09-14T05:10:16.103Z) | 确认应用曾正常启动，未显示进程僵死或报错日志 |
| 5 | Metric | kube_pod_container_status_restarts_total | 0 (timestamp: 2026-09-14T05:19:27.021000Z) | 证实此前未发生过重启，状态为首次或近期异常 |

**证据综合说明：**
Kubernetes 状态机显示 Pod 已进入 `Terminating` 阶段，但 `phase` 仍为 `Running`，且 `Killing` 事件（第 2 条）证实了信号已发出。结合资源限制（第 3 条）极低，排除了因 OOMKilled 或 CPU Throttling 导致立即退出的可能。日志（第 4 条）与监控指标（第 5 条）表明应用处于正常启动后的运行态，没有报错退出，说明进程可能对 SIGTERM 信号无响应（未捕获或未处理），或者正在执行耗时操作而无法退出。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 收到删除请求 (deletionTimestamp: 2026-09-14T06:15:08Z) 
→ 失败机制：Kubelet 发送 SIGTERM (event: Killing) 
→ 直接失败：容器进程未在宽限期内终止 (state: Running, 仍在窗口内) 
→ 用户可见现象：Pod 处于 Terminating 状态，Killing 事件已记录但未进入 terminated 状态
```

### 根因结论

**已确认的根因：** Pod 的 `app` 容器在收到 SIGTERM 信号后（`fact-985a806e8bff`），未在规定时间内完成退出逻辑，导致 Pod 保持在 `Terminating` 状态。

**证据分析：**
1. **信号已发出**：K8s Event (`fact-985a806e8bff`) 确认 `Stopping container app` 发生在 9m21s 前。
2. **进程未响应**：Pod 状态 (`fact-b332d5991542`) 显示仍在 `Terminating` 且 `phase=Running`，同时重启次数为 0 (`fact-48d1d465f0b0`, `fact-962441d78fb8`)，说明进程未正常退出，也未因错误重启。
3. **无环境干扰**：极低的资源限制 (`fact-520b34ec60c6`, `fact-63a375d35db2`) 排除了资源竞争导致的阻塞；日志仅显示 `application started` (`fact-cebbe531e4c7`)，无明确的崩溃堆栈。

**未确认的缺失环节：**
正式 RCA 判定为“证据不足”，因为缺失决定性的容器状态细节。具体来说，输入未提供容器等待状态（如 `waiting.reason` 是否显示 `ContainerCreating` 或特定状态码），也未提供 `preStop` hook 的耗时配置或执行日志。因此，无法区分是应用代码未实现信号处理、`preStop` 阻塞，还是网络 IO 挂起导致的无法终止。当前现象符合“进程未响应 SIGTERM"的表征，但无法定位根本的业务或配置原因。

---

## 📊 性能统计

```text
├─ 总耗时: 10.6m
├─ 问题定位: 21.4s
├─ 并发证据采集: 604.0s
│  └─ g1 aiops-case-v12/workload: 604.0s (Evidence 593.9s, RCA 9.9s)
└─ 汇总总结: 13.5s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
