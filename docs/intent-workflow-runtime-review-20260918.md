# 自主工作流运行审查（2026-09-18）

审查基准：后端检查点 `5593b534`、前端 `050e884`、MCP `d4a49c3`。本轮展示改动不恢复强制采证或改变模型路由。

## 路由与并发

默认 `/ask`、`/query` 经 RequestRouter 选择 focused、full_diagnosis 或 clarify；任务范围与处理深度独立。路由器没有采集工具。

- focused：query_collect → conclusion。
- full_diagnosis：layer → evidence → rca → conclusion。
- 当前 auto 深度路径没有旧的每 Pod lane 扇出。一次模型响应中的多个工具可以并行，这不等于多个诊断组并行。
- 旧 full 兼容路径保留并发实现，不代表默认入口在使用它。若要恢复，应另行设计按模型确定的对象分组、隔离工作记忆和汇总；不能直接将旧全量扫描兜底接回。

## ef8bb96819d94789 的实际情况

归档位于 reports PVC 的 `context_archives/ef8bb96819d94789`。

- 问题“我的集群有什么问题？”正确路由 full_diagnosis，scope=cluster。
- layer 读取了 Pod、Node、Events、describe、两个 Runbook 和归档；evidence 包含一个 execute_pod_promql、Kubernetes 当前/上次日志、describe 等。
- 没有调用 query_pod_logs、query_pod_tracing、query_pod_topology。不能解释成这些能力未启用，也不能声称三维完整。
- 调用了不存在的 kubectl_logs_previous，随后改为 kubectl_previous_logs；查询 NAD 还遇到 Forbidden。
- conclusion 输入记录 execution_incomplete=[step_limit]；摘要明确全集群 Pod 原文尚未读完。TodoWrite 自称 completed 不等于完成全量检查。
- 503 日志的 dependency unavailable 是应用报告的现象，尚无依赖端取证；不能据此确认具体下游服务根因。OOM 的跨重启指标也不能直接证明单个实例的连续峰值。

## 压缩与展示

该 run 的 `compactions/evidence-001.after.json` 记录 summarized_messages=11、retained_messages=2、summary_calls=2。一次历史替换中分两批产生滚动摘要，最终为用户问题＋一份工作摘要＋近期完整交互，并非两份独立记忆。

WorkingContextMiddleware 为近期完整工具交互预留 min(8000, 窗口15%) token。一个完整交互过大时可能无法保留；不是保证保留固定 N 次调用。原历史归档保留，只有摘要和预算验证成功后才替换工作历史。

另一个边界：节点间 RCA/总结等整包超预算分支直接摘要 material，并没有使用上述近期尾部保留算法。因此“所有路径都保留近期工具原文”目前不成立。本轮不悄悄修改此行为，先明确审查结论；共享摘要函数的进度提示不再一概宣称近期交互已保留。

路由原本返回结构化结果，不提供逐字分析；前端忽略了 state_snapshot 中的路由信息，空面板显示“未提供单独的分析说明”。本轮直接显示真实路由、范围、回答目标和路径。采集节点的流式事件仍存在，之前阶段默认折叠遮住内容；运行阶段现在自动展开。无工具的 RCA/总结调用目前仍是结果式转交，不能把状态动画说成模型逐字输出。

## 工具边界与倾向

运行中的服务确认 36 项允许的只读能力，包含通用 Kubernetes、Prometheus、四项 Pod 可观测性工具、Runbook 和归档回读。query_collect、layer、evidence 使用相同允许集合；RCA、conclusion 无工具。

| 能力 | 通用工具 | Pod 可观测性工具 |
|---|---|---|
| 指标 | execute_prometheus_instant_query / range_query；可查节点、集群、批量 Pod | execute_pod_promql；要求精确 namespace/pod，身份核查、时间窗、安全上限、统计和来源封装 |
| 日志 | kubectl 当前/previous/container logs | query_pod_logs；集中日志 Elasticsearch，受索引和采集覆盖影响 |
| 链路 | Kubernetes 本身不提供请求链路 | query_pod_tracing；DeepFlow＋Tempo，Flow 与 Span 不等价 |
| 关系 | lineage 等 Kubernetes 关系 | query_pod_topology；关系不证明依赖健康 |

两种指标接口都可访问 Prometheus，但不保证返回完全相同：表达式、时间、步长、实例筛选、去重及样本截取均影响结果。CPU rate 单位为核；使用率百分比还要明确相对于节点核数还是 requests/limits。Agent 选择工具；深度提示词推荐 Pod 指标及适用时的链路工具，非代码强制映射。

## 与历史测试及报告比较

`fcf6274e21214d74` 实际是 xnet Pod 列表轻量查询，只调用一次 Kubernetes 列表，不是三维测试。

`testreports/aiops_quality_expanded-c0e3e093e80c_20260910_181943/summary.md` 的 1388 有效样本、77.8% 根因准确率、82.6% 证据完整度属于历史批次＋补测；完整度按旧 Evidence Plan 计算，不能移用来评价当前自主路径。

推荐保留当前意图路由和会话能力，深度报告沿用旧版逐对象现象、证据表、因果链、Runbook 的可审计结构；区分未采集、失败、空结果，不用固定完整率装饰报告。当前提示词已采用这一结构，但模型是否遵循仍需实测，不能凭模板宣称准确性恢复。恢复并发和调整取证策略应分别测试，不和前端视觉更新混为一次效果结论。

## 本轮交付与验证

- 后端 `11.0.173`，前端 `0.1.17` 已滚动部署，原 Service/PVC 保留；MCP 未变更。
- 前端保留 React/TypeScript/Vite，接入 Ant Design X 路径组件；真实路由来自 node_complete.state_snapshot。路由字段随历史消息保存，旧历史无字段时不推测。
- 运行阶段默认展开，可手动折叠；结束默认收起。空阶段不再展示令人困惑的“未提供单独的分析说明”。过程状态不代表诊断结论已核验。
- 后端 1326 项单元测试通过；前端 63 项测试、构建、lint 通过。部署后的桌面1100px、手机390px和模拟SSE浏览器回放通过。
- 真实前端代理请求 `309b3c52ba514617`：focused/namespace=xnet，返回4个Pod；SSE含87个ai_token、工具开始/结果各1、真实路由快照和最终结果。
- 连续请求 `422e0bde1eb24c23` → `db41f163b3ae4863`：第二轮路由输入保留上一轮问答，正确回答“刚才的Pod共4个”，两个总结均通过结构化校验。
- 本轮没有重跑历史1388样本，不宣称当前深度诊断准确率与旧版相同。内存会话仍是进程级，服务重启不保留后端会话；前端历史可见不等于后端仍有记忆。
