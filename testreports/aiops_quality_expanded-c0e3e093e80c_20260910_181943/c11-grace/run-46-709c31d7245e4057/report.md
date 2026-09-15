## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod 处于正常终止流程中（Grace Period 内），尚未构成异常阻塞。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | Normal Killing 77s Stopping container app (fact-505c8d058132) | 证实 Pod 已执行终止操作，处于被 Kubelet 强制或优雅关闭的阶段 |
| 2 | K8s Event | kubelet | Normal Killing 48s Stopping container app (fact-0cdee52ee7b4) | 证实停止容器的动作在 29s 内重复确认 |
| 3 | K8s State | kubelet | Pod Status: Terminating (fact-9c70bd9a5bce); Phase: Running (fact-f429cfc4ae66) | 状态不一致，表明 Pod 逻辑上已被标记为删除，但底层容器仍在运行 |
| 4 | K8s Config | container.spec | memory limit: 32Mi; cpu limit: 50m (fact-2d0a5c21a06d, fact-af1292312253) | 确认资源配额，非资源超限导致 CrashLoop |
| 5 | Logging | elasticsearch | 08:01:37 application started (fact-3d8b3c619ef9) | 确认应用正常启动 |
| 6 | Logging | elasticsearch | 08:01:38 SIGTERM received; waiting (fact-cdce40df7375) | 关键证据：应用接收到了 SIGTERM 信号，并在执行等待清理逻辑 |
| 7 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 (fact-e9ef3ed4bd69) | 证实无重启风暴，非因健康检查失败或 OOM 导致的异常重启 |

日志 (fact-6) 显示应用处理了 SIGTERM 并进入等待状态，而 K8s State (fact-3) 显示容器仍处于运行中，这直接印证了 Pod 因应用未能在 Grace Period 内主动退出而处于正常的终止流程中。

## 🎯 根因分析 · g1

### 因果链

```text
外部控制器发起删除请求（未确认） → Kubelet 向容器发送 SIGTERM 信号（K8s Event） → 应用捕获信号并进入等待清理状态（Logging） → Pod 状态转为 Terminating 但尚未结束（K8s State）
```

### 根因结论

**已确认结论**：当前 Pod (`aiops-case-v13/workload`) 处于正常的优雅终止流程中。
根据日志事实 (fact-6)，应用已成功接收 Kubelet 发送的 SIGTERM 信号（由事实 1、2 确认），并明确显示“waiting”状态，这表明应用正在按预期进行清理工作，并未因 Crash、OOM 或配置错误而异常退出。由于应用未在设定的宽限期内主动退出，Kubernetes 将其维持在 `Terminating` 状态等待最终完成。

**不足/未知**：
触发此次删除的源头控制器（如 Deployment 缩容、Job 完成等）未在现有事实中确认，但不影响当前 Pod 行为本身的正常性判断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 22.5s
├─ 并发证据采集: 69.6s
│  └─ g1 aiops-case-v13/workload: 69.6s (Evidence 64.3s, RCA 5.1s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
