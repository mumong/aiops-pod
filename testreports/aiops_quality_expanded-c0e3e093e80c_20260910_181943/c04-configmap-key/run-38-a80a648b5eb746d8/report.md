## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod Spec 引用了 ConfigMap 'aiops-case-v11/workload-input' 中不存在的 key 'unavailable-key'，导致 kubelet 在创建容器时校验失败，Pod 进入 'CreateContainerConfigError' 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed (x12 over 59m) kubelet: Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 确认为配置项缺失导致 kubelet 在创建容器时校验失败。 |
| 2 | K8s State | kubernetes | `container.app waiting_reason: CreateContainerConfigError; message: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接描述容器等待状态及具体错误原因，与 Event 互为印证。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1 (reason=CreateContainerConfigError, container=app)` | 监控数据证实容器处于配置错误导致的等待状态。 |
| 4 | K8s State | kubernetes | `pod.phase: Pending; pod.condition[type=Ready status=False reason=ContainersNotReady]` | 确认 Pod 因容器未就绪而卡在 Pending 阶段。 |

**证据说明**：
Kubernetes Event、Container Waiting State 与 Prometheus Metric 三者在错误类型（`CreateContainerConfigError`）和错误原因（`unavailable-key` 缺失）上完全一致，形成闭环证据。Pod 日志采集失败是预期的结果，因为容器未能成功启动。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 引用了不存在的 ConfigMap Key → kubelet 校验失败 → 容器创建中止 → 进入 CreateContainerConfigError 状态
```

### 根因结论
已确认根因为 **Pod 配置错误**。Pod 的 `aiops-case-v11/workload` 在配置容器挂载点时引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的 key `unavailable-key`（见证据 #1, #2）。该配置缺陷导致 kubelet 在拉取容器镜像前检查配置阶段即告失败，引发 `CreateContainerConfigError` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 12.5s
├─ 并发证据采集: 48.9s
│  └─ g1 aiops-case-v11/workload: 48.9s (Evidence 41.8s, RCA 7.0s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
