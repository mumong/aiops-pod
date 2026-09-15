## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用容器启动后持续依赖的后端服务不可用，导致HTTP健康检查端点（/ready）返回503失败，进而触发Kubernetes Readiness Probe持续失败（从connection refused演变为HTTP 503），使Pod状态锁定为NotReady。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-5mlnc` status=NotReady, Ready=False, phase=Running | 确立异常实体状态 |
| 2 | K8s Event | Kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (latest) | 确认就绪探针直接失败原因 |
| 3 | K8s Event | Kubernetes | Readiness probe failed: dial tcp 172.16.104.16:8080: connect: connection refused (earlier) | 排除网络组件故障（早期连接被拒，后期返回503说明网络可达，端口已开） |
| 4 | Logging | Elasticsearch | Pattern: `dependency unavailable`, http_status: 503, path: `/work` (8 occurrences, `allocated_mib`: 0→0) | 确定应用内部逻辑故障，资源消耗正常 |
| 5 | Tracing | Deepflow | Flow: GET /work -> 503, src_ip=172.16.104.62, dst_ip=172.16.104.16 (9 occurrences, duration: 5.1ms~99.3ms) | 确认外部客户端访问应用返回503 |

证据总结：
1. Pod 状态为 `NotReady`（事实 1）。
2. 探针失败机制从“连接被拒”演变为“返回503”（事实 2, 3），表明应用容器已启动且监听端口，但无法处理正常请求。
3. 日志与追踪流量均一致显示内部处理失败并抛出 503 错误（事实 4, 5）。

## 🎯 根因分析 · g1

### 因果链

```text
应用后端依赖不可用（由日志确认） → 应用处理请求返回HTTP 503 → Readiness Probe持续接收503响应 → Pod状态锁定为NotReady
```

### 根因结论

已确认根因：应用容器 `app` 的 HTTP 健康检查端点持续返回 503 错误，导致 Pod 被 Kubernetes 标记为 `NotReady`。

- 证据编号 2 表明 kubelet 直接观察到 Readiness Probe 收到 HTTP 503 状态码。
- 证据编号 4（日志）和证据编号 5（追踪）交叉印证了应用自身返回 503 的具体模式（路径 `/work` 报错“dependency unavailable”）。
- 早期探针记录中的 `connection refused`（证据编号 3）已被后期 503 证据排除为网络/容器未启动问题，确认为启动初期的短暂依赖不可用或初始化失败阶段。

当前现象直接由应用逻辑层抛出 503 导致，Kubernetes 网络层无异常。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 32.0s
├─ 并发证据采集: 89.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 89.3s (Evidence 82.8s, RCA 6.4s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
