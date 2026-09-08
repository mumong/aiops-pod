## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | 应用启动时缺失关键配置项导致崩溃 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` 状态：`CrashLoopBackOff` (fact-8b0a5b7a35c9)，Exit Code: `78` (fact-deae42ef244b) | 确认应用反复崩溃且进程已异常退出 |
| 2 | K8s Event | Kubernetes | `BackOff  78s (x354 over 81m)` 警告 (fact-01ec40af8a34) | 记录容器长期重启行为，佐证非偶发故障 |
| 3 | K8s Config | Kubernetes | 资源配置：Request Memory `24Mi` (fact-1419083ca8d9)；Limit Memory `96Mi` (fact-605ae2726903) | 排除资源硬限制导致的 OOM KILL |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = `Error` (fact-10d75d09cc03) | 量化确认最近一次容器终止原因为错误 |
| 5 | Logging | Elasticsearch | 日志模式：`CONFIG_MISSING`，HTTP Status `500`，Path `/work` (fact-13e2ada463ab 等 8 条) | 明确应用内部错误原因为配置项缺失 |
| 6 | Tracing | Tempo | Span 属性 `aiops.observed_mode`: `config_missing_exit` (fact-056e308a9210) | 从应用可观测性确认配置缺失导致的服务退出 |
| 7 | Tracing | Deepflow | L7 Flow: `GET /work` → `500` (fact-6c1f1b9f5c2c 等 9 条) | 网络流确认客户端请求持续收到 500 错误 |

上述证据中，K8s 层面的反复重启与高退出码（#1, #2）是应用异常的外部表现。日志模式明确指出了应用内部错误原因 `CONFIG_MISSING`（#5），而 Tracing 数据（#6, #7）在应用侧和流量侧共同验证了这一特定错误类型，形成了完整的逻辑闭环。由于 OOM 原因已被资源限制数据排除（#3），配置缺失是唯一的直接失败路径。

## 🎯 根因分析 · g1

```text
ConfigMap 挂载或配置项缺失 → 应用启动检查失败返回 Error 78 → CrashLoopBackOff 持续重启 → 请求持续返回 500 错误
```

### 根因结论

**已确认的根因**：应用启动时缺失关键配置项。

该结论由以下事实直接支撑：
1. 日志中反复出现 `CONFIG_MISSING` 错误信息，且伴随 HTTP `500` 响应（证据 #5）；
2. Tracing 明确记录了 `config_missing_exit` 模式（证据 #6）；
3. 容器退出码 `78` 与配置缺失导致的非正常终止一致（证据 #1）。

**缺失的决定性事实**：
1. 具体缺失的配置键名；
2. ConfigMap `workload-code` 的挂载路径与代码预期路径的映射关系。
目前虽有证据指明是配置问题，但尚需确认具体是哪项配置或挂载配置有误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.0s
├─ 并发证据采集: 69.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 69.9s (Evidence 61.3s, RCA 8.5s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
