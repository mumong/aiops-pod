## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Secret aiops-case-04/workload-input 中缺失被 Pod 模板引用的 key 'unavailable-key' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container 'app': waiting_reason=`CreateContainerConfigError`，waiting_message=`couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 定位到具体的配置缺失故障点 |
| 2 | K8s Config | Kubernetes | Pod 容器 `app` 引用 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key` | 验证引用关系与缺失 key 的一致性 |
| 3 | K8s State | Kubernetes | pod.phase=`Pending`，pod.status=`Pending`；ContainersReady/Ready=False (reason=ContainersNotReady) | 证实容器未能启动且 Pod 处于挂起状态 |
| 4 | K8s Event | Kubernetes | kubelet 记录：`Normal Pulled 4m23s (x399 over 89m) Container image ... already present on machine` | 证明镜像拉取正常，排除镜像网络或存储问题 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=`CreateContainerConfigError`, container=`app`) = 1；`kube_pod_container_status_restarts_total` (container=`app`) = 0 | 监控侧确认状态为等待配置错误且无重启计数 |

证据表明，Kubernetes API 明确报告由于 `Secret aiops-case-04/workload-input` 中缺少 key `unavailable-key`，导致容器 `app` 无法完成配置加载而处于 `CreateContainerConfigError` 状态，进而导致 Pod 挂起。镜像拉取成功且无重启记录（Metric 与 Event 相互印证），排除了运行环境与重启逻辑故障。

## 🎯 根因分析 · g1

```text
Secret aiops-case-04/workload-input 中缺失 key 'unavailable-key' → 容器配置加载失败 → Pod 进入 CreateContainerConfigError 并处于 Pending 状态 → 应用服务不可用
```

### 根因结论

已确认根因为 **Pod 模板引用的 Secret (`aiops-case-04/workload-input`) 中缺失被挂载或引用的 key (`unavailable-key`)** [1, 2]。Kubernetes 调度器与 kubelet 正确识别了该配置错误，导致容器无法启动（`CreateContainerConfigError`），Pod 持续处于 `Pending` 状态 [3]。Metric 数据验证了该等待状态 [5]。现有证据链完整，直接支撑上述根因结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.1s
├─ 并发证据采集: 39.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 39.2s (Evidence 34.9s, RCA 4.2s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
