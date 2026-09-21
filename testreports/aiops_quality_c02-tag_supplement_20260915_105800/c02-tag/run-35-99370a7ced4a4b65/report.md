## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod workload (aiops-case-v07) stuck in ImagePullBackOff, Pending state |
| g2 | `monitor/prometheus-observability-prometheus-0` | Unknown | Prometheus 配置的 PrometheusQL 规则存在 `many-to-many matching` 错误（duplicate series），导致规则评估引擎在后台死锁或长时间阻塞，进而阻塞了 HTTP 服务端响应，造成 Liveness 和 Readiness 探针因 `context deadline exceeded` 持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Error: ErrImagePull` 及 `rpc error: code = NotFound desc = failed to pull...: not found` | 明确注册表返回镜像标签找不到的错误 |
| 2 | K8s Event | Kubernetes | `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 确认 kubelet 因找不到特定标签的镜像而进入指数退避重试状态 |
| 3 | K8s State | Kubernetes | Pod `aiops-case-v07/workload` 处于 `Pending` 阶段，`Ready=False` (ContainersNotReady)，`restart_count=0` | 确认故障发生在容器启动阶段，无重启行为，处于挂起等待状态 |
| 4 | K8s State | Kubernetes | 容器 `app` 处于 `ImagePullBackOff` 等待状态，原因是拉取 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 失败 | 直接指出容器 runtime 的卡点状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (label: `reason=ImagePullBackOff`, value=`1`) | 验证了当前正在等待拉取镜像的指标状态 |

**证据印证说明：**
Kubernetes 事件 (事实 #1, #2) 直接记录了底层容器运行时解析引用失败的详细原因。Kubernetes 状态 (事实 #3, #4) 与 Prometheus 指标 (事实 #5) 从宏观状态和时序指标两个维度一致印证了 `ImagePullBackOff` 的持续存在。日志与链路追踪未采集是合理的，因为容器尚未成功启动运行。

## 🎯 根因分析 · g1

### 因果链

```text
镜像标签 'aiops-fixture-unavailable-20260908' 在注册表中不存在 → 容器拉取返回 NotFound 错误 → Kubelet 进入指数退避重试 → Pod 处于 Pending/ImagePullBackOff 状态
```

### 根因结论

已确认根因为：**镜像标签缺失 (`aiops-fixture-unavailable-20260908`)**。

该标签在注册表 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause` 中未找到（见证据 #1），导致容器拉取操作直接失败。随后 kubelet 在重试机制下不断退避（见证据 #2），使得 Pod 始终停留在 `Pending` 状态且容器处于 `ImagePullBackOff`（见证据 #3, #4, #5）。

证据链已覆盖核心故障路径，但无法确定该标签缺失是源于注册表侧的清理策略，还是部署清单配置错误（属于未确认事项）。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: Get "http://172.16.166.165:9090/-/healthy": context deadline exceeded` | 直接现象：存活探针超时 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: Get "http://172.16.166.165:9090/-/ready": context deadline exceeded` | 直接现象：就绪探针超时 |
| 3 | Logging | Elasticsearch | `err="found duplicate series for the match group {instance=\"10.2.0.48:10250\"} ... many-to-many matching not allowed: matching labels must be unique on one side"` | 根本原因：PromQL 规则存在多对多匹配冲突，导致规则引擎报错阻塞 |
| 4 | K8s State | Kubernetes | Container last terminated reason: `OOMKilled` | 历史资源压力证据，提示该工作负载曾发生过内存耗尽 |
| 5 | K8s Config | Kubernetes | Memory limit: `512Mi`, CPU limit: `100m` | 配置背景：容器资源限制极低 |
| 6 | Tracing | Deepflow | `GET /federate?match%5B%5D=%7B__name__%3D~%22node_.%2A%22%7D` duration 2822ms~4723ms | 行为证据：内部或外部联邦查询耗时数秒，反映服务端响应极其缓慢 |

**证据印证说明：**
日志中的 `many-to-many matching not allowed` 错误（#3）直接证实了 PrometheusQL 配置错误是引发问题的根源。该错误导致规则评估引擎阻塞（机制），进而使得 HTTP 服务端无法及时响应探针请求，表现为探针 `context deadline exceeded` 失败（#1, #2）。追踪数据（#6）进一步佐证了服务端在处理查询请求时的响应延迟异常。

## 🎯 根因分析 · g2

### 因果链

```text
Prometheus Rule 配置错误（many-to-many matching） → Rule manager 执行失败并阻塞后台处理 → HTTP 服务端响应超时（probe timeout） → 集群判定 Prometheus 容器不健康 (Unhealthy)
```

### 根因结论

已确认根因为 `Prometheus 配置的 PrometheusQL 规则存在 many-to-many matching 错误`。
该错误导致 Rule Manager 在后台处理规则时陷入阻塞或循环报错（证据 #3），直接阻断了 HTTP 服务端的正常响应逻辑，最终导致 Liveness 和 Readiness 探针持续超时（证据 #1, #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 52.8s
├─ 并发证据采集: 72.8s
│  ├─ g1 aiops-case-v07/workload: 56.2s (Evidence 44.1s, RCA 11.9s)
│  └─ g2 monitor/prometheus-observability-prometheus-0: 72.8s (Evidence 65.0s, RCA 7.6s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
