# 运行逻辑修复与压缩优化验证

日期：2026-09-18。代码、提示词及 Kubernetes 服务均在既有部署上更新；不修改 MCP 权限、凭据或测试业务 Pod，不提交 Git。

## 修复内容

- 将工具传输成功与业务成功分开：query_rejected/语义失败显示为失败，进入失败统计；合法空查询保持成功但明确无数据。
- 最终结果支持 partial，性能统计不再把执行不完整标成 success；前端显示“本次仅部分完成”。这不是程序判断根因是否正确。
- 每个并发诊断组显示自己的采集、压缩、RCA 进度；父定位阶段失败不再污染每个子组的独立完成状态，整体仍保留父阶段的限制。
- 同名同 ID 工具计数加入 lane 身份；完成后的未返回调用显示“未返回/阶段已结束”，不继续显示执行中与旋转等待图标。
- 压缩后保留轻量 evidence_receipts：实际调用过的可观测性工具/Runbook、对象、覆盖状态及原文引用。不保存重复全文，不据此强制采集或推断根因。
- 提示词区分 Pod 与节点指标工具，禁止给节点指标硬加 Pod 标签；区分最新状态与历史异常、单对象历史与多对象排名、比例与百分比，以及 OOMKilled 与尚未验证的 cgroup/节点 OOM 机制。
- 定位 recursion_limit 从 15 调为 24；取证从 20 调为 32。递归步数包含模型、工具及中间件，不等于工具调用次数；不无限提高上限。

## 网上调研与采用方案

以下为本轮实际访问的官方公开资料，不把文档示例的效果直接当成本项目数据：

| 来源 | 成熟做法 | 本项目取舍 |
|---|---|---|
| [LangChain short-term memory](https://docs.langchain.com/oss/python/langchain/short-term-memory) | SummarizationMiddleware；旧历史摘要与近期消息共存；摘要模型可独立选择 | 保持现有状态替换/近期完整工具交互，不更换整个框架。独立快模型有价值，但没有未经评测直接替换摘要模型 |
| [LangChain middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) | 可配置 trigger/keep、摘要与上下文编辑 | 保持 54k/90% 配置。不采用仅为加速而裁掉早期历史的方法 |
| [LangGraph Graph API / Send](https://docs.langchain.com/oss/python/langgraph/graph-api#send) | 独立子任务并行处理，再汇合的 map-reduce 模式 | 用于三段及以上历史摘要：最多三路提取证据卡，再按原顺序合并。不把完成顺序当源顺序 |
| [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) | 大结果外置、上下文管理和独立子 Agent | 继续保留原文归档与按需读取；不直接引入新 Agent 框架或强制工具流程 |
| [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 历史 compaction、结构化笔记、引用式按需读取；警告过度压缩丢失关键细节 | 用轻量采集记录保护“已查/未查”事实；不能承诺摘要无损 |

实现：一至两段串行；至少三段默认最多三路 map，再有序 reduce。每段必须成功，空内容、输出截断、超预算或异常时保留原历史，取消未完成兄弟任务。新摘要通过原预算核验后才替换 LangGraph 状态。`AIOPS_COMPACTION_WORKERS=1` 可回退串行。并发上限是每次压缩三路，多诊断组同时压缩可能产生更多模型请求，不是服务级全局限流。

没有采用：直接丢弃旧工具响应；后台无同步点替换历史；自动切换未评测的小模型。后台预摘要可降低触发时等待，但会增加无效调用、版本对齐与取消复杂度，暂留为后续选项。

## 同输入压缩对照

数据：上一轮真实 OOM run `c51e696bea0a4b4f` 的 layer 历史，真实 DeepSeek，54k 窗口；相同问题、数据及当轮摘要提示词，先串行再并行，没有更改触发阈值。

| 对照 | 串行 4 次调用 | 并行分段 + 合并 5 次调用 | 耗时减少 |
|---|---:|---:|---:|
| 第一轮 | 27.149s | 15.799s | 41.8% |
| 收紧证据整理措辞后复测 | 24.431s | 15.049s | 38.4% |

人工检查保留了对象 UID、OOMKilled、64Mi limit、日志 allocated_mib、指标/日志范围与不足。第二轮避免了部分不必要单位换算，但摘要仍是有损模型输出；这些是两个小样本，不是严格随机交叉基准，也不代表 Qwen 上必然同幅度加速。多一次模型调用，成本与并发压力可能上升。

## 实际并发与前端验证

三 Pod 实际运行：`8ef88ca2c97b4b8a`，case-05/08/09，约 183.7s。三个分支启动时间差约 15ms，分支耗时约 30.27/33.34/96.35s，取证阶段约 96s，而非三者相加约 160s，确认真正并发。

该次不是全部通过：layer 和一个分支仍触发 step_limit，工具权限等失败如实保留。此轮暴露并修复了父状态污染子组、采集事实被摘要遗漏、终态未返回调用仍显示执行中的问题。实际工具包含 Metrics/Logs/Tracing；各组根据问题选择，未要求无网络/从未启动容器也必须有完整链路。

第一次 run `1195ac09f8514fdf` 因测试启动与前端滚动更新重叠，SSE 连接终止，明确排除通过记录。没有把连接中断当成模型错误。

最终版本的双 Pod 重测、真实 SSE 浏览器回放及部署检查结果在本报告末尾补充。

双 Pod 复测 `0b33e7eb37b943d9`（后端 11.0.180，经同一后端 NodePort 调用以避开前端更新）：146.724s；两组启动相差约 2ms。g1 独立 completed、g2 因自身 step_limit 为 partial，整体正确 partial，不再污染所有子组。模型已改用通用 Prometheus 工具查询 node2 指标；实际读取的两本 Runbook 均保留在最终列表。该次没有要求全维度取证，Trace 未查询，报告明确说明；未把空数据/权限拒绝改写为健康。

前端真实 SSE 回放分别使用上述三组、两组完整事件：目标归组正确、无未归属结果、完成后未返回调用不再显示执行中、历史刷新可恢复分组，均通过。受控乱序/部分失败/独立进度浏览器测试也通过。最终 11.0.181 仅追加通用 Prometheus 归 Metrics、kubectl logs 归 Logging 的展示分类及对应测试，没有再更改模型诊断流程。

## 证据位置

- 三组实际 SSE：`/tmp/aiops-parallel-live-20260918.jsonl`。
- 最终版本双组 SSE：`/tmp/aiops-parallel-180.jsonl`。
- 压缩对照输出：`/tmp/aiops-compaction-compare-20260918/1.json`、`3.json`（第二轮结果）。
- 真实运行及各分支原始记录：报告 PVC 的 `context_archives/<run_id>/` 和 `<run_id>-g*/`。
- 浏览器脚本：前端 `tests/autonomous-parallel.browser.py`（受控乱序/部分失败）、`tests/live-parallel-replay.browser.py`（真实 SSE 回放与历史保存）。

## 最终上线检查

- 后端 **11.0.181**：镜像 digest `sha256:da5edcfbbfaf41f26613f867cf57ba5e3d05a25ab0d879c56e4716fbfb41f02e`；Pod `aiops-copilot-545798c856-7hwbl`，2/2 Running。
- 前端 **0.1.23**：镜像 digest `sha256:2bd9d5bb2f3486073426c7b6c1b311d9d308f406e0866d8191f3624e6de34f0e`；Pod `aiops-copilot-frontend-57d9646f45-qkk88`，1/1 Running。
- 后端最终回归 **1346 passed**；前端 **70 passed**，构建和 lint 通过。浏览器：受控并发、真实三组/两组回放、直接结构化查询展示/历史恢复均通过。
- 前端 `/api/health` 返回 healthy，已恢复 `openai/Qwen3.8-27B`；临时 DeepSeek Secret/ConfigMap 已删除，原始凭据保持不变。过程内存会话因 Pod 更新清空。
- MCP 无修改，A2A sidecar 保持 11.0.168；不发布无关服务，不清理测试业务资源，不提交 Git。
- 剩余边界：没有证明模型永不冗余取证、压缩无损、永不触发 step_limit；MCP 查询 NAD 的 RBAC 拒绝未扩大权限修复。上线后的 Qwen 未做同量深度性能对照，不能以 DeepSeek 结果替代其性能验收。
