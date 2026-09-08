## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 处于 ContainerCreating/Pending 状态，长时间未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | fact-6711f8dd96c1 | MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 核心证据：明确指出了 Volume 挂载失败的具体原因是依赖的 ConfigMap 不存在 |
| 2 | K8s State | fact-0ce5a9d92bdf | 资源请求 (CPU: 5m, Memory: 8Mi) | 上下文：资源请求极小，排除因资源不足导致调度失败的可能性 |
| 3 | K8s State | fact-41b1963aa14c | 资源限制 (CPU: 50m, Memory: 32Mi) | 上下文：资源硬限制明确，属于典型的配置错误而非资源耗尽 |
| 4 | K8s Event | fact-4e0ddbc78f19 | Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition | 核心证据：证实了挂载失败导致了超时和阻塞 |
| 5 | K8s State | fact-2ee219ca4e49 | Pod 处于 Pending 状态 | 现象佐证：Pod 尚未进入运行状态，说明挂载阻塞发生在容器启动前 |
| 6 | Metric | fact-68af0d53db34 | kube_pod_container_status_waiting_reason = 1 (reason: ContainerCreating) | 现象佐证：Prometheus 指标确认容器处于等待创建阶段 |
| 7 | Metric | fact-d303efb86cb8 | kube_pod_container_status_restarts_total = 0 | 排除重启：容器尚未启动成功，排除了 OOMKill 等运行期崩溃因素 |

**证据关联说明：**
K8s Event 中的 `configmap not found` (证据 #1) 直接解释了挂载超时 (证据 #4) 的根本原因。K8s State 显示资源请求极低 (证据 #2-3)，且 Metric 显示重启次数为 0 (证据 #7)，排除了资源调度竞争或运行期崩溃的可能，将故障锁定在启动阶段的配置引用错误。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用了不存在的 ConfigMap 'unavailable-config' → kubelet 挂载 Volume 失败 (NotFound) → 挂载超时导致 Pod 阻塞 → 容器 app 持续处于 ContainerCreating 状态
```

### 根因结论

已确认的根因是 Pod 配置错误。Pod `aiops-case-03/workload-5b5fc86c8c-zz82w` 定义了一个名为 `input` 的 Volume，该 Volume 引用了 ConfigMap `unavailable-config`。由于该 ConfigMap 在集群中不存在，且该 Volume 配置为非可选（`optional=false`），导致 `kubelet` 在启动阶段无法完成挂载操作，进而使得 Pod 永远卡在 `Pending/ContainerCreating` 状态。相关事实引用证据 #1 和证据 #4。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 30.6s
├─ 并发证据采集: 538.5s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 538.5s (Evidence 530.3s, RCA 8.1s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
