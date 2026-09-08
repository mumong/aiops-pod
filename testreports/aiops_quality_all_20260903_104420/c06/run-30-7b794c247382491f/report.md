## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod workload-7679bcf76-w9s9c in CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason: "Error" (fact-54b38ea5cd38) | 确证应用进程发生过非零退出 |
| 2 | K8s State | Kubernetes | container.last_exit_code: 2 (fact-b04e9fec5d4d) | 明确进程终止退出码为 2 |
| 3 | Logging | Elasticsearch | Pattern: `/work` HTTP 500, "runtime process exiting", trace_ids: `41ea4f274c5f...`, `75598d8e...` 等 (fact-626f40fba010聚合) | 直接展示导致崩溃的请求路径及应用日志报错 |
| 4 | Logging | Elasticsearch | Pattern: `/work` HTTP 200, "request completed", trace_ids: `bee5e41c...`, `dc73979d...` 等 (fact-3984ae5f5637聚合) | 证明 `/work` 接口本身功能可用，非配置错误或全量宕机 |
| 5 | Tracing | DeepFlow | Flow GET `/work` response_code: 500, trace_ids: `41ea4f274c5f...`, `75598d8e...` 等 (fact-0b294f621470聚合) | 与日志 Error 模式 100% 关联，确认 HTTP 请求在到达应用层后触发退出 |
| 6 | Tracing | Tempo | Span GET `/work` aiops.observed_mode: "runtime_exit", http.response.status_code: 200 (fact-55a8e42444ef) | 记录了一次成功请求后进程退出的边界行为 |
| 7 | K8s State | Kubernetes | container.waiting_reason: "CrashLoopBackOff" (fact-876da999ce9e) | 描述 Pod 当前异常状态，系进程反复崩溃导致 |
| 8 | K8s Config | Kubernetes | resource_request.memory: 24Mi, resource_limit.memory: 96Mi (fact-00f9676b9cab, fact-3a87966f4148) | 资源配额极低，排除显式 OOMKilled (exit code 137) |

证据交叉验证：Kubernetes 的 `exit_code=2` 和 `CrashLoopBackOff` (证据1,7) 与 Elasticsearch 中 `/work` 路径返回 HTTP 500 后进程退出的日志模式 (证据3) 完全吻合。同时，相同的 trace_ids (如 `41ea4f...`) 跨 Logging 和 Tracing (DeepFlow 500 Flow) 维度均被记录，证明是业务逻辑在 `/work` 接口处理中触发进程退出。资源限制极低 (证据8) 但并非 OOM，因为日志明确记录了 `runtime process exiting`。

## 🎯 根因分析 · g1

### 因果链

```text
应用在处理 /work 接口时触发运行时报错 → 进程处理完毕后直接退出(exit code=2) → K8s 检测到容器退出并重启 → CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用在处理 HTTP `/work` 接口时发生运行期逻辑错误（Runtime logic error），导致进程直接终止（退出码 2）并抛出 HTTP 500。

该根因由以下事实支撑：
1. **Kubernetes 状态**：容器 `app` 频繁重启，处于 `CrashLoopBackOff` 状态，且上一次终止原因为 `Error`，退出码确认为 `2` (证据1, 7, 8)。
2. **应用日志与链路**：应用日志和 Tracing 均显示，当访问 `/work` 接口时，服务返回 HTTP 500 并触发 "runtime process exiting"，随后进程结束 (证据3, 4, 5)。
3. **排除资源限制**：虽然容器内存限制仅为 96Mi，但日志中 `numeric_fields` 显示 `allocated_mib` 始终为 0.0，且进程退出码为 2 而非 OOM 常见的 137，表明崩溃由逻辑错误引起而非内存超限。

**未知部分**：具体的代码缺陷或缺失的依赖库导致 `/work` 报错的具体代码路径，因缺乏 Traceback 堆栈信息而未能确定 (见诊断中的 `unknowns`)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 31.1s
├─ 并发证据采集: 66.6s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 66.6s (Evidence 57.7s, RCA 8.8s)
└─ 汇总总结: 15.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
