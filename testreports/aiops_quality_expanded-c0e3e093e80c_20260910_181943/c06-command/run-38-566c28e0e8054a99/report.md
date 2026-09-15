## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff，容器不断重启失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` | 确认容器处于重启退避状态 |
| 2 | K8s Event | Kubernetes | `event.message`: `Warning BackOff ... Back-off restarting failed container app` | 确认 Pod 已频繁重启 (x187 over 44m) |
| 3 | K8s State | Kubernetes | `container.last_exit_code`: `127` | 证明容器进程启动失败，且错误码为“命令未找到” |
| 4 | Logging | Elasticsearch | `log.message`: `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接记录启动命令执行失败的详情，锁定缺失文件路径 |
| 5 | K8s Config | Kubernetes | `container.resource_limit.memory`: `32Mi` | 提供资源限制上下文，非 OOM 指标 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `13` | 量化重启次数，与 K8s 状态一致 |

上述证据形成了完整的闭环：K8s 状态日志（#1, #2）证实了服务不可用的表象，日志记录（#4）精准定位了“命令未找到”的原因，结合退出码 `127`（#3）彻底排除了资源超限或网络故障的可能，并锁定了镜像构建中缺失 `/opt/app/unavailable-command` 文件这一具体事实。

## 🎯 根因分析 · g1

### 因果链

```text
镜像中缺失可执行文件 /opt/app/unavailable-command → 容器启动执行 shell 命令时报错 not found → 容器以 Exit Code 127 终止 → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因**：容器启动脚本 (`sh -c exec /opt/app/unavailable-command`) 中引用的二进制文件在容器镜像中不存在，导致进程启动失败（退出码 127）。

证据支持：
- 日志记录明确显示：`/opt/app/unavailable-command: not found` (#4)。
- 容器退出码确认为 127，对应经典的“命令未找到”错误 (#3)。
- K8s 状态与事件日志均一致表明容器反复启动失败并进入退避 (#1, #2, #6)。

**未知项**：为何镜像构建或部署配置中未包含该可执行文件（属于构建上游问题）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 11.1s
├─ 并发证据采集: 41.1s
│  └─ g1 aiops-case-v08/workload: 41.1s (Evidence 32.2s, RCA 8.8s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
