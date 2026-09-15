## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod/workload in namespace aiops-case-v07 is stuck in ImagePullBackOff state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod/workload in namespace aiops-case-v07 status: ImagePullBackOff | 确认异常状态 |
| 2 | Metric | prometheus | kube_pod_container_status_waiting_reason(app, reason=ImagePullBackOff): value=1 | 确认 Pod 处于拉取镜像等待状态 |
| 3 | Metric | prometheus | kube_pod_container_status_restarts_total(app): value=0 | 排除因重启导致的间歇性故障，确认为启动前阻滞 |
| 4 | K8s Config | Kubernetes (fact 关联) | spec.containers[0].image: registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908 | 定位导致拉取失败的镜像标识 |

**证据关联说明**：
Kubernetes 报告的 `ImagePullBackOff` 状态与 Metric `waiting_reason` 强一致，证明容器因镜像拉取问题被阻塞。Metric 中重启次数为 0 确认了 Pod 无法完成启动流程，从而限制了 Logging 和 Tracing 的可用性。根因直接指向 K8s Spec 中指定的镜像 `aiops-fixture-unavailable-20260908`。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了不存在的镜像 'aiops-fixture-unavailable-20260908' → Kubelet 拉取镜像返回 NotFound 错误 → 容器启动失败且状态转为 ImagePullBackOff → Pod 长期处于未运行状态，无法响应业务请求
```

### 根因结论

已确认根因为：**Pod 规格中指定的容器镜像不存在于注册表中**。
证据 `g1#4` 显示 Pod 配置了镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908`。结合 `g1#1` 和 `g1#2` 中观察到的 `ImagePullBackOff` 状态，证实了 kubelet 无法从该 registry 获取该镜像。因镜像不存在导致的拉取失败阻止了容器的启动，从而引发当前现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.2s
├─ 并发证据采集: 37.8s
│  └─ g1 aiops-case-v07/workload: 37.8s (Evidence 30.4s, RCA 7.3s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
