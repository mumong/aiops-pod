## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 'aiops-case-11/workload' is in a 'TerminatingStuck' state caused by a custom finalizer 'aiops.lab/hold'. Although the container 'app' was successfully terminated by the kubelet (Exit Code 137, SIGKILL) via 'Killing' event, the Pod object lifecycle is blocked by the Kubernetes API Server because the 'aiops.lab/hold' finalizer remains attached. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status` = `Terminating (lasts 64s)` | 证实 Pod 生命周期处于阻塞状态，无法完成删除。 |
| 2 | K8s State | Kubernetes | `container.last_exit_code` = `137` (SIGKILL) | 证实容器进程已收到信号并被 Kubelet 强制终止，但对象未清理。 |
| 3 | K8s Event | Kubernetes | `Normal Killing` message: `Stopping container app` | 证实 kubelet 执行了正常的容器销毁动作，排除了 Kubelet 自身异常。 |
| 4 | K8s Config | Kubernetes | 容器 `app` 资源限制: CPU `200m`, Memory `96Mi` | 证实资源请求配置明确，非资源耗尽导致的删除阻塞。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = `0` | 证实该 Pod 自启动以来未发生过重启，当前为首次终止。 |
| 6 | Logging | Elasticsearch | HTTP 请求 `GET /work` 响应 200，时间窗口 `23:09:48 - 23:09:56` | 证实应用在处理请求时状态正常，终止行为并非由应用内部报错引发。 |
| 7 | Tracing | Tempo/Deepflow | Span `GET /work` (trace: `25d61c...`) 耗时正常 (min 3626us)，响应 200 | 证实网络层面与日志观测一致，应用服务在终止前功能正常。 |

**证据分析说明：**
1. **现象隔离**：证据 [1] 确认了 Pod 卡在 Terminating 状态，而证据 [2][3] 证实底层的 Kubelet 已成功执行了 kill 动作（Exit Code 137）。这一“容器已死但对象未删”的分离现象排除了节点级故障。
2. **排错逻辑**：日志 [6] 和追踪 [7] 显示应用终止前处理请求正常（HTTP 200），且没有重启记录 [5]，进一步排除了容器因 OOM 崩溃或应用逻辑错误导致无法正常退出的可能性。
3. **指向根因**：既然底层销毁动作已完成，导致 Pod 对象无法从 API Server 删除的唯一阻碍点在于 Kubernetes 对象本身的 Finalizer 机制。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 元数据配置了自定义 Finalizer 'aiops.lab/hold' → 触发删除操作导致 API Server 挂起对象生命周期 → Kubelet 仍执行容器杀进程 (Exit 137) → API Server 等待 Finalizer 移除 → Pod 状态永久卡在 Terminating
```

### 根因结论

**已确认根因：自定义 Finalizer 'aiops.lab/hold' 未处理。**

当前 Pod `aiops-case-11/workload` 的 Terminating 状态是由于其绑定了自定义 Finalizer `aiops.lab/hold`，导致 Kubernetes API Server 阻止了对象的生命周期结束。

*   **事实支撑**：
    *   证据 [2][3] 显示容器已被 Kubelet 正常终止（Exit Code 137），证明 Kubernetes 底层调度与节点执行层无故障。
    *   证据 [1] 显示 Pod 状态停留在 `Terminating` 达 64 秒，表明 API Server 在等待某些条件解除。
    *   输入中的正式 RCA 明确指出了 `aiops.lab/hold` finalizer 是阻塞点。

*   **缺失决定性事实**：
    *   **控制器状态未知**：证据不足以确认负责处理 `aiops.lab/hold` 的自定义控制器（Controller）当前是否存活或正常工作。无法判定该 Finalizer 是手动配置错误，还是控制器故障。
    *   **配置溯源未知**：无法通过现有事实确认 `aiops.lab/hold` 是由 Operator 添加还是手动注入。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.2s
├─ 并发证据采集: 52.3s
│  └─ g1 aiops-case-11/workload: 52.3s (Evidence 43.0s, RCA 9.2s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
