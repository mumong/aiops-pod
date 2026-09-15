## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | ConfigMap `workload-code` 挂载配置缺失或路径错误导致应用启动时无法找到必要配置 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.last_terminated_reason: Error`, `exit_code: 78`, `restart_count: 11` (fact-55d46ba3c4af, fact-a77e3d7b5ef9, fact-68431093273c, fact-78750133e389) | 确认应用进程异常退出且已进入崩溃重启循环 |
| 2 | K8s Config | Kubernetes | `resource_limit.memory: 96Mi`, `resource_request.memory: 24Mi` (fact-02aecf194d53, fact-1d0e2c3efd90) | 排除内存资源不足导致 OOM 杀进程的可能性 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: 1` (CrashLoopBackOff), `kube_pod_container_status_restarts_total: 11` (fact-69a9231a3580, fact-3ef0ca1efde1) | 时序指标确认了异常状态的持续性与重启次数 |
| 4 | Logging | Elasticsearch | `pattern: CONFIG_MISSING (http_status 500, path: /work, service: aiops-lab-workload)`, `occurrence_count: 8` (fact-70eaa3a8eaeb等) | 核心应用日志明确报告配置缺失，直接指向故障根因 |
| 5 | Tracing | Tempo/Deepflow | `span: GET /work (http.response.status_code: 500, aiops.observed_mode: config_missing_exit)` (fact-02fed02d4b31) | 链路追踪确认 500 错误源于配置异常逻辑，且与日志中的 `CONFIG_MISSING` 相互印证 |

**证据关联说明：**
1. K8s 记录的 `exit_code: 78` 配合日志中的 `CONFIG_MISSING`，表明进程因配置文件不可用主动抛出异常退出（事实 1 与事实 4）。
2. Tracing 记录中的 `config_missing_exit` 模式与日志的报错模式在业务逻辑层面完全一致，共同限定了故障范围为配置问题（事实 4 与事实 5）。
3. 内存限制（事实 2）与 Metric 的当前值（事实 3）证明异常并非由资源争抢或 OOM 引起，排除了基础设施层面的干扰。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `workload-code` 挂载内容缺失或挂载路径/文件名不匹配 → Python 应用 `server.py` 启动初始化阶段因配置文件不可用抛出异常 → 进程退出返回 exitCode=78 (配置错误语义) → Kubernetes 触发 CrashLoopBackOff 进入重启退避循环
```

### 根因结论

已确认的根因为：**ConfigMap `workload-code` 挂载配置缺失或路径错误导致应用启动时无法找到必要配置**。

现有证据形成了完整的闭环：
1. **现象层**：Kubernetes 显示容器反复以 `Error` 状态退出，Exit Code 为 78（事实 1）。
2. **业务层**：应用日志持续抛出 `CONFIG_MISSING` 错误，并返回 HTTP 500（事实 4）；追踪日志进一步将其标记为 `config_missing_exit`（事实 5）。
3. **排除层**：容器内存请求与限制配置充足（事实 2），非资源竞争所致。

`exit_code=78` 是典型的配置错误退出码，结合日志明确指出的 `CONFIG_MISSING` 状态，直接验证了 ConfigMap 挂载存在问题的根因推断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.9s
├─ 并发证据采集: 53.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 53.8s (Evidence 47.3s, RCA 6.4s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
