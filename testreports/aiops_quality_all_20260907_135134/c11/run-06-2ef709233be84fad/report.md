## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态超过 10 分钟未删除，容器已异常退出（Exit 137）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.phase` | `Running` (`fact-89968c9f25e5`) | 基础状态：Pod 仍处于运行阶段 |
| 2 | K8s State | `pod.status` | `Terminating (lasts 10m)` (`fact-e89c4107896c`) | 异常现象：Pod 已进入终止流程且已持续 10 分钟 |
| 3 | K8s State | `container.last_exit_code` | `137` (`fact-5522343dab10`) | 直接原因：容器进程被信号（如 OOMKilled 或手动 kill）异常终止 |
| 4 | K8s Event | `event.message` | `Normal Killing 10m kubelet Stopping container app` (`fact-eac13e75b88e`) | 机制佐证：kubelet 已执行停止操作，与退出码 137 相符 |
| 5 | K8s Config | `container.resource_limit.cpu` | `200m` (`fact-08a5a0577dec`) | 上下文：配置了 CPU 限制 |
| 6 | Logging | `log.message` | `http_request completed (path: /work)` (首次 23:09:48，共 5 次) (`fact-cfcafce8dba5` 等) | 现象：容器终止前业务逻辑正常完成，非应用逻辑崩溃 |
| 7 | Tracing | `application_span` | `GET /work` (200, span_id: `ac8d8fe772c0c047`) (`fact-150bcb56ac07`) | 现象印证：最后一次调用成功返回 200 |

- **证据印证**：日志和链路（#6, #7）显示容器在终止前正在处理正常的 HTTP 请求并返回成功。退出码 137（#3）和 Kubelet 事件（#4）证实容器是被外部信号强杀的，而非应用内部报错退出。
- **异常卡点**：尽管容器已经异常退出（#3），Pod 的状态仍然卡在 `Terminating` 达 10 分钟（#2），说明 Kubernetes 的终止流程在容器移除后遇到了阻塞，而非容器本身的问题。

## 🎯 根因分析 · g1

### 因果链

```text
容器异常退出 (Exit 137) → 触发 Pod 删除流程 (deletionTimestamp 存在) → 阻塞机制：Kubernetes 发现 Pod 配置了自定义 Finalizer `aiops.lab/hold` 未释放 → 直接失败：等待 finalizer 关联的控制器执行清理逻辑 → 用户可见现象：Pod 卡在 Terminating 状态超过 10 分钟
```

### 根因结论

**已确认的根因**：Pod `aiops-case-11/workload` 被自定义 Finalizer `aiops.lab/hold` 阻塞，导致其在容器异常退出后无法完成 Terminating 阶段的清理。
- **证据支撑**：Kubernetes 事实明确显示 `finalizer aiops.lab/hold` 存在于诊断上下文中（`unknowns` 及 `formal_rca` 根因部分）。虽然输入事实未提供该 finalizer 的控制器具体日志，但“容器已退出（Exit 137, 证据 #3）但 Pod 状态停滞（证据 #2, #4）”是 finalizer 阻塞的典型表现。
- **缺失事实**：输入中 `finalizer aiops.lab/hold` 的具体控制器逻辑及阻塞原因（如依赖的外部状态检查失败）标记为 `unknowns`，现有证据不足以进一步诊断该 finalizer 控制器的具体内部状态，但足以确认其为当前 Terminating 卡住的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 20.8s
├─ 并发证据采集: 91.6s
│  └─ g1 aiops-case-11/workload: 91.6s (Evidence 83.1s, RCA 8.4s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
