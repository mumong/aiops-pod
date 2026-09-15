## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 持续处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 4m27s (x210 over 49m) kubelet Back-off restarting failed container app in pod workload_aiops-case-v08(00e5e755-886e-4661-9e8a-00d1e71595f6)` | 确认 Pod 进入 CrashLoopBackOff 状态及长时间退避重启的周期 |
| 2 | K8s State | kubernetes | 主进程退出码：`127`；最后一次退出原因：`Error`；重启次数：`14` | 退出码 127 明确指向操作系统层面的“命令/文件未找到”错误 |
| 3 | Logging | elasticsearch | 2026-09-11T13:34:23.904Z 日志：`sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接证明容器试图执行的入口命令 `/opt/app/unavailable-command` 在镜像中不存在 |
| 4 | Metric | prometheus | 2026-09-11T13:52:14.920Z 样本：`kube_pod_container_status_last_terminated_reason` (reason=Error) = 1, `kube_pod_container_status_waiting_reason` (reason=CrashLoopBackOff) = 1 | 独立于 K8s API 验证了容器因 Error 终止并处于等待重启状态 |
| 5 | K8s Config | kubernetes | 容器资源限制：Memory `32Mi` / CPU `50m`，请求：Memory `8Mi` / CPU `50m` | 排除因资源超限（OOM）或 CPU 不足导致终止的可能性 |

**证据印证说明：**
日志中的“Command not found”（第 3 条）与 K8s 状态报告的“Exit Code 127”（第 2 条）在机制上完全一致，127 正是 Shell 执行缺失命令时的标准返回码。指标数据（第 4 条）作为第三视角再次确认了终止状态，且资源配置（第 5 条）的极低配额与 CrashLoopBackOff 的症状无矛盾，但不足以支撑 OOMKill 的证据。

## 🎯 根因分析 · g1

### 因果链

```text
容器镜像中缺少主进程可执行文件 /opt/app/unavailable-command → 容器启动时 shell 执行命令失败并返回 Exit Code 127 → Kubernetes 持续探测到容器异常退出并触发指数退避重启 → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：**容器入口点命令 `/opt/app/unavailable-command` 在容器镜像中不存在**。
该事实由 `logging` 维度直接捕获的“not found”报错以及 `kubernetes` 维度反映的“Exit Code 127”共同确证。Kubernetes API 观察到的 `CrashLoopBackOff` 以及 Prometheus 指标中的 `Error` 终止状态均为该根因导致的直接症状。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.4s
├─ 并发证据采集: 38.7s
│  └─ g1 aiops-case-v08/workload: 38.6s (Evidence 30.5s, RCA 8.0s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
