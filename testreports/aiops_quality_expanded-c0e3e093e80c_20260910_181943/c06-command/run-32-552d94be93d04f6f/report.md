## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `container.resource_limit.memory=32Mi` | 确认容器具备极低的资源上限，排除常规 OOM Kill |
| 2 | K8s State | Kubernetes | `container.last_exit_code=127` (container: app) | 核心诊断指标，127 代码对应系统级命令未找到 |
| 3 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接证据，日志明确指出了失败的命令路径和 Shell 报错信息 |
| 4 | K8s State | Kubernetes | `container.last_terminated_reason=Error` | 佐证容器异常终止状态 |

**证据互证说明：**
- K8s 状态显示的 `exit_code=127` 与 Elasticsearch 日志中的 `not found` 错误完全吻合，共同锁定了命令缺失这一根本原因。
- `resource_limit.memory=32Mi` 作为上下文存在，但因日志明确指出了执行命令失败，故资源限制并非此次异常的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了不存在的命令 (/opt/app/unavailable-command) → sh -c exec 执行失败并返回 exit code 127 → kubelet 检测到容器异常退出并触发重启策略 → Pod 进入 CrashLoopBackOff 状态且无法就绪
```

### 根因结论

- **已确认的根因**：容器启动命令（Command）指定了镜像中不存在的可执行文件（`/opt/app/unavailable-command`）。
- **证据引用**：
  - 日志事实 `fact-13cb3242823d` 记录了 `sh: ... unavailable-command: not found`。
  - K8s 状态事实 `fact-acf5760b4cd0` 记录了容器的最后退出码为 `127`。
- **结论**：应用无法启动，Kubernetes 根据重启策略不断尝试重启，导致 Pod 处于 `CrashLoopBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 55.4s
├─ 问题定位: 12.5s
├─ 并发证据采集: 35.4s
│  └─ g1 aiops-case-v08/workload: 35.4s (Evidence 25.3s, RCA 10.0s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
