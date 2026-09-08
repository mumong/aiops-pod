## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | {'message': 'k8s.v1.cni.cncf.io/networks-status:'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-06/workload-7679bcf76-w9s9c` | `status: Running` (Pod层面)；Container `app` 退出码 2，重启次数 21 | 确认 Pod 已调度并处于运行状态，但容器反复崩溃 |
| 2 | K8s Event | Kubelet | `BackOff restarting failed container app` (4m42s, x384 over 89m) | 直接证实容器因异常退出触发指数退避重启机制 |
| 3 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason=Error`；`kube_pod_container_status_waiting_reason=CrashLoopBackOff` | 确认容器最近一次终止原因为 Error，当前处于等待/崩溃循环中 |
| 4 | Logging | Elasticsearch | 4 次重复 `http_request` 错误日志：`"message": "runtime process exiting"`, `"http_status": 500`, `"path": "/work"`，时间窗口 12:58-13:19 | 定位故障触发点为 HTTP `/work` 请求处理期间的内部崩溃 |
| 5 | Logging | Elasticsearch | 4 次重复 `http_request` 成功日志：`"http_status": 200`, `"path": "/work"`，时间窗口 12:58-13:19，`allocated_mib`: 0 | 确认 `/work` 路径同时存在成功与失败情况，资源分配为 0（未体现 OOM 或资源耗尽特征） |
| 6 | Tracing | Tempo/Deepflow | Flow: `GET /work` 返回 500，持续 4.5-9.8ms；Trace ID 与错误日志匹配（如 `75598d...`） | 从网络与调用链角度验证 500 错误确实由应用层在处理该请求时返回 |

**证据综合说明**：Kubernetes 状态与事件确认了容器因非零退出码（2）频繁崩溃。日志与 Trace 事实互相印证，指出崩溃直接发生在处理 `/work` 路径的 HTTP 请求期间，且应用明确输出了 "runtime process exiting" 消息。Metric 数据与资源配置（Request 24Mi / Limit 96Mi）一致，未体现 OOM 特征。日志中的 `allocated_mib: 0` 结合退出码 2 暗示该资源数值可能为应用层自行管理或未正确上报，而非 Kubernetes 层面的资源限制问题。

## 🎯 根因分析 · g1

### 因果链

```text
应用层内部异常 (未确认具体类型) → 处理 GET /work 时返回 500 并触发 "runtime process exiting" → 容器进程强制退出 (Exit Code 2) → Pod 进入 CrashLoopBackOff
```

### 根因结论

**部分确认的根因**：
应用进程在处理 `/work` HTTP 请求时发生了未捕获的严重错误（表现为 HTTP 500 和 "runtime process exiting" 日志），导致容器主进程非正常退出（Exit Code 2），从而引发 Kubernetes 的重启循环 [证据 #4, #5, #6]。

**证据不足/未确认环节**：
- **具体异常类型**：现有日志未提供堆栈跟踪或异常详情，无法区分是代码逻辑 Bug、依赖服务超时还是参数错误。
- **资源监控/管理**：日志中 `allocated_mib` 始终为 0 且退出码非 OOM 常见代码，无法确认是否为资源未被正确监控或应用层自行管理了资源，缺乏决定性事实以排除或证实内存/资源相关的根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.9s
├─ 并发证据采集: 67.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 67.9s (Evidence 58.3s, RCA 9.4s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
