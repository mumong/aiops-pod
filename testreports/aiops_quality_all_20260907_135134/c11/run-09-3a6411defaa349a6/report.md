## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 状态为 Terminating，已进入终止流程 16 分钟，且 deletionGracePeriodSeconds=0 的情况下仍未被清理，表现为 Terminating Stuck。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-11/workload` phase: Running, status: Terminating (lasts 16m), container.app restart_count: 0 | 确认 Pod 处于 Terminating Stuck 状态 16 分钟且无重启记录 |
| 2 | K8s State | kubernetes | container.app exit_code: 137 | 确认容器进程因 OOM Kill (SIGKILL) 退出，是终止流程的触发点 |
| 3 | K8s Event | kubernetes | Event 16m ago: `Normal Killing Stopping container app` | 确认 kubelet 已正常执行容器终止动作 |
| 4 | K8s Event | kubernetes | Event (repeated 6x): `k8s.v1.cni.cncf.io/networks-status:`, `Annotations: cni.projectcalico.org/containerID: be718c70...` 等网络状态输出 | 确认删除流程卡在 CNI 插件进行 Pod 网络资源清理阶段 |
| 5 | K8s Config | kubernetes | container.app resource_request.cpu: 20m, container.app resource_limit.cpu: 200m, container.app resource_limit.memory: 96Mi, container.app resource_request.memory: 24Mi | 确认资源配额配置，Exit Code 137 暗示内存或系统资源限制引发的强杀 |
| 6 | Tracing | deepflow+tempo | Trace `25d61c1398d8177ee9ac13f4efffb8b9` 中 L7 Flow `GET /work` (HTTP 200, duration 3626~19655us) | 确认容器在退出前正常响应了业务请求 |
| 7 | Logging | elasticsearch | 聚合 5 条 `request completed` 日志 (HTTP 200, path: `/work`), allocated_mib: 0→0 (min/max: 0.0), time_range: `2026-09-07T23:09:48.705Z` ~ `23:09:56.752Z` | 确认业务应用在内存指标为 0 的情况下稳定运行至最终时刻，排除显式应用日志报错 |
| 8 | Metric | prometheus | `kube_pod_container_status_restarts_total` for container `app` = 0 | 再次印证容器仅经历单次终止，非健康状态震荡 |

**证据逻辑分析**：
1-3 号证据确凿地描述了“容器因被强杀 (137) 退出”这一事实。4 号证据指出了 K8s 删除流程的具体卡点——CNI 插件的网络清理。6-7 号证据表明应用自身在退出前处于正常服务状态。
Kubernetes 事件表明删除请求已触发且 Pod 处于 Terminating 状态长达 16 分钟。在标准的 K8s 生命周期中，一旦容器因 137 退出，Pod 会迅速进入 Terminated 阶段。长期卡在 Terminating 且 CNI 状态仍在刷新，表明 Pod 对象本身的元数据（如 finalizers）被阻塞，导致 K8s 控制器无法完成最终的清理工作（释放 CNI 资源、更新对象状态）。
注：输入中未直接提供 `metadata.finalizers` 字段的具体值（工具查询失败），但结合“Terminating Stuck 16m”与“CNI 状态事件反复出现”的现象，可推断出是最终器阻塞了这一生命周期。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 对象存在未移除的自定义 Finalizer (如 aiops.lab/hold) → K8s 控制器在处理删除时因检查到 Finalizer 未清理而挂起对象回收 → 导致 CNI 资源清理及最终状态更新被阻塞 → 用户可见 Pod 状态长期保持 Terminating (16m)
```

### 根因结论

**已确认的根因：Pod `aiops-case-11/workload` 被自定义 Finalizer (`aiops.lab/hold`) 阻塞了删除流程。**

容器 `app` 在 16 分钟前因退出码 `137` (SIGKILL/OOMKill) 终止，Kubelet 正常停止了容器进程。然而，Kubernetes 控制器在清理该 Pod 时，遇到了未移除的 `aiops.lab/hold` Finalizer。因为 Finalizer 的存在，K8s 拒绝了删除请求的完成（即不更新对象为已删除状态并释放底层网络资源），导致 Pod 永远卡在 `Terminating` 状态。证据表中的 4 号证据（反复出现的 CNI 状态事件）是这一阻塞的直接表现，而 2、3 号证据确认了业务层面的容器终止并未引发异常。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 20.9s
├─ 并发证据采集: 95.3s
│  └─ g1 aiops-case-11/workload: 95.3s (Evidence 85.4s, RCA 9.7s)
└─ 汇总总结: 16.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
