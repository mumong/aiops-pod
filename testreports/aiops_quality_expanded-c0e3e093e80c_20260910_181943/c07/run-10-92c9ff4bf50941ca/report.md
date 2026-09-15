## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: CrashLoopBackOff (app) | 确认应用容器当前处于重启退避状态，表现为用户可见现象 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 78 (app) | 提供应用异常退出的具体进程退出码，指向特定的逻辑或环境错误 |
| 3 | K8s Event | Kubernetes | `BackOff restarting failed container app` (x65 over 18m) | 证实了容器处于高频失败重启循环中，符合 CrashLoopBackOff 特征 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`=Error, `restarts_total`=8 | 通过指标交叉验证了 K8s 状态，确认最近一次终止原因为 Error 且重启总数为 8 次 |
| 5 | Logging | Elasticsearch | Pattern: `CONFIG_MISSING`, http_status: 500, path: `/work` (8 occurrences, first: 20:30:51, last: 20:47:12) | 提供应用侧的直接报错信息，明确指示启动/请求阶段因缺少配置导致服务不可用 |
| 6 | Tracing | Tempo / Deepflow | Tempo span: `aiops.observed_mode`="config_missing_exit", http response 500, trace_id: `a358165e4c5df7b2882c057473693f30`<br>Deepflow flows: GET /work → 500 (9 occurrences, trace_ids include `a358165e4c5df7b2882c057473693f30`) | 链路追踪数据通过特定的 observed_mode 将 500 错误与配置缺失关联，且 trace_id 与日志中的请求一致，确证了故障链路 |

**证据关联分析：**
- 证据 1、2、3 建立了 Kubernetes 层面“应用异常退出 (Exit 78) → 重启 → CrashLoopBackOff”的表层因果链。
- 证据 5 (日志) 与证据 6 (追踪) 从应用内部行为层面解释了异常退出的原因：请求 `/work` 接口时返回 500 并记录 `CONFIG_MISSING`，这直接印证了导致应用崩溃的内部逻辑。
- 证据 4 提供了独立于 K8s API 的时序观测（重启计数），与 K8s 状态事实一致，排除了瞬时状态波动的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-code'内容缺失或挂载路径不匹配 (未确认的具体配置项) → 应用进程请求配置返回 CONFIG_MISSING (Error 500) → 进程以 Exit Code 78 异常退出 → K8s 频繁重启容器导致 CrashLoopBackOff
```

### 根因结论

已确认根因为：**应用进程启动后因缺少关键配置文件（或挂载配置不匹配）导致异常退出 (Exit Code 78)**，进而引发 Kubernetes 重启失败循环。

- **已确认部分**：
  - **现象**：Pod `workload-dff5cbc6b-sjvxl` 的容器 `app` 处于 `CrashLoopBackOff` 状态，最近一次终止原因为 `Error`，退出码为 `78` (证据 1, 2, 3, 4)。
  - **内部机制**：应用在处理 HTTP 请求（如 `GET /work`）时明确报出 `CONFIG_MISSING` 错误，且 Trace 数据标记了 `config_missing_exit` 模式，确认了故障是由配置缺失导致的逻辑崩溃 (证据 5, 6)。
  
- **证据不足与待查**：
  - **具体配置项与挂载路径**：当前事实未包含 `ConfigMap 'workload-code'` 的实际 YAML 内容或 Pod 的 `volumeMounts` 配置详情，无法确定是 ConfigMap 本身缺失 Key、文件路径不匹配，还是权限问题 (证据 5 仅指明缺少配置，未指明具体哪个 Key)。
  - **Exit Code 78 的具体代码语义**：虽然确认了退出码，但无法从给定事实中解读该退出码在特定应用代码中的确切业务逻辑含义 (例如是否特定于找不到某文件)。

综上所述，故障根因已锁定在“配置缺失导致的应用崩溃”这一因果链上，但具体的配置差异细节需要进一步检查 ConfigMap 与 Pod 挂载定义。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 28.1s
├─ 并发证据采集: 70.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 70.1s (Evidence 63.0s, RCA 6.9s)
└─ 汇总总结: 15.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
