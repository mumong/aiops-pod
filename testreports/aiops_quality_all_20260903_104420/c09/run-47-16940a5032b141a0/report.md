## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6处于NotReady状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `workload-5f4fb9ff45-cfzz6` 状态 `NotReady`；`Ready` 与 `ContainersReady` 均为 `False`，原因 `ContainersNotReady`，消息 `containers with unready status: [app]` (fact-5f63845c0332) | 确认可观察的集群层面故障现象，定位到应用容器 `app` 健康检查未通过 |
| 2 | K8s State | kubernetes | 容器 `app` 无重启记录 (`restart_count: 0`)；内存限制 `96Mi`，请求 `24Mi` (fact-4fe66d64c4ed, fact-1b4efab21447) | 排除因 OOM 重启或内存配置错误导致的进程异常，缩小排查范围 |
| 3 | Logging | elasticsearch | 8 次模式重复的 `http_request` 错误日志：`dependency unavailable`，状态码 `503`，路径 `/work` (fact-16f3777160e6...) | 直接揭示应用内部错误机制，确认服务因依赖缺失无法响应健康检查 |
| 4 | Tracing | deepflow+tempo | 9 次等效 L7 流与 1 次应用 Span 记录，均为 `GET /work` 返回 `503`，trace_id `5a23e0c80f2d1e117abdc6c429c94edd` 关联日志与追踪 (fact-2758e156e554, fact-0354564c0cbf) | 确认外部探针调用与内部错误响应的因果关联，消除网络隔离或配置错误的假设 |

**证据关联分析**
Kubernetes 的 `NotReady` 状态直接由日志中的 `503 dependency unavailable` 引起。Tracing 数据作为跨维度纽带，将外部探针的 `GET /work` 请求与容器内的具体报错关联，证明了探针失败并非偶发网络抖动，而是应用层明确的依赖不可用。内存等静态资源配置未发生异常，佐证了逻辑依赖问题。

## 🎯 根因分析 · g1

### 因果链

```text
应用服务依赖不可用 → Readiness Probe 请求 /work 返回 HTTP 503 → Kubernetes 判定容器 NotReady → Pod 状态变为 NotReady
```

### 根因结论

**已确认根因**：应用服务内部依赖不可用导致就绪探针持续失败。
日志记录了明确的错误模式 `dependency unavailable` 且伴随 HTTP 503 响应（证据 #3），Tracing 数据证明该错误稳定复现于健康检查接口 `/work`（证据 #4），导致 Kubernetes 容器状态检查失败并标记 Pod 为 `NotReady`（证据 #1）。当前证据链完整，因果关系闭环。

**未确认项**：具体的底层依赖服务名称（如数据库或缓存实例）未被应用暴露。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 16.2s
├─ 并发证据采集: 84.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 84.8s (Evidence 76.6s, RCA 8.0s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
