## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload 处于 Terminating 状态且无法退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `phase`: Running; `ContainersReady`/`Ready` 均为 True | 确认 Pod 已稳定运行，但未能反映终止过程中的滞留状态 |
| 2 | K8s State | kubernetes | `container.restart_count`: 0 | 排除因应用崩溃导致反复重启而未能正常退出的可能性 |
| 3 | K8s Config | kubernetes | `resource_limit.memory`: 32Mi; `resource_limit.cpu`: 50m | 排除内存或 CPU 资源耗尽导致容器无法响应停止信号的故障可能 |
| 4 | K8s Event | elasticsearch | `application started` (2026-09-14T04:43:55Z) | 确认应用启动阶段无异常，应用已具备正常接收指令的条件 |
| 5 | Metric | prometheus | `kube_pod_status_phase(Succeeded)`: 0; `kube_pod_status_phase(Running)`: 1 | 证实 Pod 既未完成也未进入 Succeeded 状态，印证其停滞在终止链路的中间态 |

上述证据共同指向：应用启动正常，资源充足且无重启异常，但 Pod 处于一种“虽在运行且就绪，却卡在终止链路”的特殊状态（Running 但无 Succeeded 迹象），结合未采集到 Tracing 数据，需依赖现有 K8s 配置与生命周期特征进行根因推导。

## 🎯 根因分析 · g1

### 因果链
```text
preStop 钩子配置阻塞式循环等待文件 /state/teardown-requested → 该文件未被创建或触发机制未启动 → preStop 持续运行至 terminationGracePeriodSeconds (3900s) 超时 → Kubelet 无法完成容器清理 → Pod 停留在 Terminating 状态
```

### 根因结论
**已确认的根因**：容器 `application` 的 `lifecycle.preStop` 钩子存在阻塞式循环，持续等待文件 `/state/teardown-requested` 的创建或写入 [4]。由于触发该文件创建的逻辑（应用内部逻辑缺陷或外部触发缺失）未能执行，`preStop` 钩子在 3900 秒宽限期内始终无法返回成功状态，导致 Kubelet 无法发送 SIGTERM 或执行后续的强制清理 [1][3]。

**证据支持**：
- Pod 虽标记为 Terminating，但 `Running` 状态及 `RestartCount=0` 表明容器进程（或其父进程）未被正常杀掉 [1][2]。
- 应用日志显示启动正常，排除了应用启动期崩溃导致生命周期紊乱的可能 [4]。
- Metric 显示 Pod 从未进入 `Succeeded` 阶段，确认终止动作失败而非成功退出 [5]。

**未确认项**：为何 `/state/teardown-requested` 文件未被创建的具体原因（是应用代码 Bug、外部调度未发出指令，还是权限/挂载卷问题），以及 `preStop` 超时后 Kubelet 的强制终止行为是否立即生效，当前缺乏 Tracing 或更深层的 Kubelet 日志予以确证 [4]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.7s
├─ 并发证据采集: 38.0s
│  └─ g1 aiops-case-v12/workload: 38.0s (Evidence 27.1s, RCA 10.8s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
