# DeepSeek 临时对照测试（2026-09-18）

## 范围与结论

测试对象：后端 11.0.177、前端 0.1.21，通过实际前端 `/api/query` 代理调用现有 Kubernetes 服务。未修改业务代码、提示词、MCP 或原始 Secret；使用临时 Secret/ConfigMap 切换模型。请求模型名 `deepseek/deepseek-chat`，提供商预检返回实际模型 `deepseek-flash`。上下文窗口保持 54,000，触发比例配置 0.90（扣除输出及安全预留后，本次输入目标约 45,744 token）。

快速查询和会话指代正常；深度诊断实际取得三维证据和 Runbook，但仅部分通过，不能认定完整验收成功。单次试验不能代表稳定准确率或总体性能。

| 测试 | Run ID | 后端耗时 | 审查结果 |
|---|---|---:|---|
| xnet Pod 列表 | `5d51c9434b284e1c` | 5.294s | 正确列出 4 个 Pod；1 次工具调用，未经过独立总结节点。不过用户要求仅名称和状态，回答额外包含其他列 |
| 接着问“其中哪个 Pod CPU 最高” | `312f659d5bed4cf6` | 11.990s | 同一 session_id 与 owner cookie；正确恢复 xnet 的 4 个对象并查询真实 CPU。排名正确，历史稳定性说明有过度推断 |
| OOM Pod 深度诊断 | `c51e696bea0a4b4f` | 198.212s | 三维证据及 Runbook 实际调用；根因主线有依据，但 layer 达到 step_limit，最终 answer.status=partial |
| 54k 合成历史压缩压力 | `deepseek-compaction-live`（本机隔离测试） | 不作为线上延迟样本 | 连续两次超预算均完成历史替换；最新完整工具交互保留；摘要事实保留，但进度措辞存在错误 |

## 多轮记忆

第二轮 request_contract 明确把“其中”解析为上一轮的 4 个 xnet Pod，而不是全量集群检查。实际调用 5 次 `execute_pod_promql`：4 个 Pod 的 CPU 查询，以及最高 Pod 的额外历史查询。

返回值约为 ham-h8sft 0.04065 core、ham-dpkwq 0.03363 core、ham-nnvzq 0.01966 core、chartmuseum 0.00097 core，口径为 5 分钟 rate，而非绝对瞬时峰值。

问题：只取得 ham-h8sft 的历史曲线，却声称历史上稳定高于其他 Pod；其他 Pod 的历史未查，不能证明该比较。这是报告推断边界问题，不是会话记忆丢失。

## 深度诊断证据审查

对象：`aiops-case-08/workload-5c9c7b6489-s7p79`，只读诊断，未执行修复。

- Metrics：实际查询 working_set、RSS、内存 limit、重启计数、终止原因等。OOMKilled、64Mi limit、应用增长配置和日志增长主线相互支持，但不能只凭 exit 137 独立证明 cgroup OOM。
- Logs：实际调用 `query_pod_logs`，取得 `memory allocation advanced`、`allocated_mib` 递增等记录；额外关键字窗口返回空，被报告为缺失而非健康证明。
- Tracing：实际调用 `query_pod_tracing`，返回 30 条 flow、3 条 span；Tempo 5 次 trace 查询成功。flow 存在 SQL limit 截断，最终报告说明了该限制。HTTP 200 只证明已取样请求成功，不能据此排除所有依赖异常。
- Runbook：实际读取 `pod-oomkilled.md` 和 `pod-crashloop-runtime.md`；最终区分前者适用、后者非 OOM 分支不适用。

共 26 次工具调用，未发现工具名和全部参数完全相同的重复调用。这不等于没有语义重复或可省略查询。

### 未通过项

1. layer 的 recursion_limit=15 被触发，随后仍完成 evidence → rca → conclusion；最终报告正确标注 `partial` / `step_limit`，但顶层事件和 metrics.success 仍为 success，不能只看绿色成功状态验收。
2. `execute_pod_promql` 是 Pod 限定工具。查询 node2 的 MemoryPressure 被拒绝 `missing_pod_scope`，随后模型给节点指标硬加 namespace/pod 标签得到空结果。应使用适合节点范围的查询方式，不能据此判断指标未采集或节点健康。
3. 上述 query_rejected 在前端事件中仍为 tool success，统计 failed_tool_calls=0；当前“成功”含调用返回成功，不等于业务取证成功。
4. 最后 YAML 已显示新容器 running，报告开头仍把之前的 CrashLoopBackOff 写成当前状态。应区分采样时间、当前运行状态与持续重启的历史现象。
5. 报告称“比例 0.86 不能转换成 86%”不正确；同一分子/分母和单位口径下可以换算。报告对 cgroup OOM 使用“已验证”，同时又承认节点 OS OOM 未排除，确定性表述存在冲突。

## 压缩与耗时

实际深度 run 的 SSE 记录显示三次整理：layer 31.205s、layer 48.236s、evidence 38.347s，合计约 117.788s，占 198.212s 的约 59%。工具 wall duration 约 17.433s，主要瓶颈不是工具本身。相关大返回包括首轮 logs 约 123KiB、后续 logs 约 76KiB、tracing 约 81KiB。

合成压力测试使用真正 DeepSeek 摘要模型和现有 WorkingContextMiddleware，不降低线上阈值，不把模拟数值当成集群观测。最终可复现样本每轮加入 2,500 行模拟指标目录：

| 轮次 | 压缩前估算输入 | 压缩后估算输入 | 被摘要消息 | 保留近期消息 | 摘要调用 |
|---|---:|---:|---:|---:|---:|
| 1 | 56,289 | 1,252 | 3 | 2 | 3 |
| 2 | 57,470 | 1,485 | 6 | 2 | 3 |

验证：LangGraph reducer 替换历史，而非仅追加；最新工具调用与输出成对保留；用户任务、旧 CPU 值及“内存未查”得到保留；每次替换后再次检查不压缩，新历史增长后能再次触发。第二轮更早的原文转入摘要属于既定策略，不是永远保留第一轮的近期原文。

测试脚本最初误要求第二轮仍原样保留第一轮旧尾部，断言失败；修正为检查“该轮最新完整交互”后重跑通过，未修改生产压缩实现。

语义边界：最后一个分段全部处理后，摘要仍声称还有未读历史，甚至建议继续读取目录。机械替换通过，不代表工作记忆语义完全正确；该措辞可能诱发不必要回读。

## 回归、证据与环境

执行以下测试，49 passed：

`tests/unit/aicall/test_working_context.py`、`tests/unit/workflow/test_request_router.py`、`tests/unit/workflow/test_query_answer.py`。

本轮经前端代理完成真实 SSE 请求，但未新增浏览器视觉验收。未做多 Pod 分组并发压力、重启后记忆持久化或长期稳定性验收。本轮观察未出现感叹号退化，不代表已证明永不复发。

- HTTP 事件记录：`/tmp/aiops-deepseek-test-20260918/{quick,memory,deep}.jsonl`（临时文件）。
- 合成压力归档：`/tmp/aiops-deepseek-test-20260918/archives/deepseek-compaction-live/`。
- 实际运行归档：报告 PVC 的 `context_archives/<run_id>/`；主机根目录 `/data/redis/aiops-aiops-reports-pvc-pvc-52d8916d-bd02-4ad3-9c91-ea2e59356b51/context_archives`。
- 原始业务 Secret 和配置文件未改。测试后已恢复原 Qwen 引用；rollout 成功，前端代理健康检查返回 `openai/Qwen3.8-27B`。临时 Secret 与临时 ConfigMap 已删除，原始配置保留；Pod 重建清空了进程内会话。

未提交 Git，未推送仓库。
