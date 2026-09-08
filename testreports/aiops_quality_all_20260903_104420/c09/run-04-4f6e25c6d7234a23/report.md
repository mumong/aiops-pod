## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | {'message': 'cni.projectcalico.org/podIP: 172.16.104.26/32'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `workload-5f4fb9ff45-cfzz6` phase=Running, container `app` restart_count=0, status=NotReady | 确认容器已运行且非重启问题，但应用层状态异常 |
| 2 | K8s Event | kubernetes | Readiness probe failed: `http://172.16.104.26:8080/ready` dial tcp: connection refused (5m53s) | 排除网络层中断（CNI/连接可达），定位故障在应用层端口未响应 |
| 3 | K8s Event | kubernetes | Readiness probe failed: HTTP 503 (53s, x104) | 确认应用主动返回业务错误状态码，而非崩溃 |
| 4 | Logging | elasticsearch | Pattern: `dependency unavailable` (503, /work), 8 occurrences (17:58:38 - 17:59:10) | 定位应用内部逻辑检测到依赖不可用，触发 503 响应 |
| 5 | Tracing | deepflow+tempo | Span: `GET /work` (HTTP 503, trace_id: `d882babe0b383bda1a35dd7116d979a4`) | 验证日志与追踪的一致性，确认异常发生在业务请求处理阶段 |

上述证据链显示网络层（TCP连接）是通畅的，因为 `dial tcp` 未报 timeout 或 no route，而是应用层直接拒绝了连接或返回了 503。Pod 本身处于 Running 状态且未发生重启，排除了资源不足导致的崩溃。日志和追踪明确指向应用依赖问题导致业务逻辑返回 503，从而触发 Kubelet 的 Readiness 探针失败。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖不可用/无响应 → 应用返回 HTTP 503 → Kubelet Readiness Probe 收到 503 失败 → Pod 被标记为 NotReady
```

### 根因结论

**证据不足**。

现有证据确认了故障现象的直接原因：应用代码中的外部依赖不可用（日志显示 `dependency unavailable`），导致应用返回 HTTP 503 错误，进而触发 Kubelet 的 Readiness 探针检查失败，使 Pod 进入 `NotReady` 状态。

但是，无法确定导致“应用依赖不可用”的底层根本原因（Root Cause）：
1.  **缺失具体依赖目标**：日志仅泛化提示 `dependency unavailable`，未指明具体的后端服务 IP、主机名或数据库连接。
2.  **缺失拓扑/网络上下文**：工具 `observability-gate-1-topology` 查询失败，导致无法确认该 Pod 访问的具体后端服务是否存在网络中断、DNS 解析失败或目标服务宕机等情况。

因此，当前只能确定是“应用层业务逻辑”引发了 `NotReady`，但无法断定是“目标服务故障”还是“配置错误”或“网络策略阻断”这一层级的真正故障点。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 18.9s
├─ 并发证据采集: 70.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 70.3s (Evidence 61.0s, RCA 9.0s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
