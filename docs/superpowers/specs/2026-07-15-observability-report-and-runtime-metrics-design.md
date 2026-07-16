# 可观测性报告与运行统计修正设计

## 目标

在不修改 Runbook 选择逻辑、不改变现有工作流节点结构的前提下：

1. 让最终报告中的 LLM 调用、工具调用和工具耗时来自真实运行事件。
2. 避免 `collect_aiops_case` 成功后把诊断完整度无条件写成 100%。
3. 允许 Qwen 在粗粒度 case 返回后，根据缺失、冲突或关键疑点按需调用细粒度证据工具。
4. 保留当前结构化报告，移除重复的“采集统计”，扩展可观测性原始数据，并为拓扑增加人可读总结。

## 设计边界

- 不修改 Runbook 获取、选择和展示逻辑。
- 不为 OOM、ConfigError、ImagePullBackOff 等异常增加固定分支。
- `collect_aiops_case` 仍是每个已确认异常 Pod 的首个实时可观测性入口。
- 细粒度补采由模型依据 case 返回的 coverage、dimension details、conflicts、limitations 和 recommended refs 决定。
- 不读取 `data` 项目或历史 case label 作为在线诊断答案。

## 真实统计

最终统计以工作流最终状态中的 `thinking_events` 和真实 LLM 请求边界共同重建：

- Agent 循环 LLM 调用数：去重后的 `ai_usage` 事件数量。
- 直接 LLM 调用数：在 `layer_extract`、`evidence_plan`、RCA、上下文压缩和最终报告等结构化或简单请求的真实调用边界记录。
- LLM 总调用数：Agent 循环请求与直接请求之和，不按工作流节点或 Agent loop 粗略估算。
- 工具发起数：去重后的 `tool_start` 事件数量。
- 工具成功数：去重后的成功 `tool_result` 事件数量。
- 工具失败数：已发起但没有成功结果，或明确失败的调用数量。
- 工具累计耗时：每个 `tool_call_id` 的 `tool_start.timestamp` 到 `tool_result.timestamp` 的时长之和；缺少时间戳时使用事件携带的 duration。
- 工具并行关键路径：合并所有工具调用的重叠时间区间，表达工具阶段真实占用的墙钟时间，避免把并行调用相加后误认为端到端耗时。

`WorkflowMetrics` 不再把一次 Agent loop 等同于一次模型请求，也不再为 `result.tool_call_count` 写入 0ms 的伪工具耗时。

## 证据完整度

报告中的完整度表达“证据是否足以支撑当前结论”，而不是“粗粒度工具是否返回成功”。

保留三种内部口径：

- `observability_target_coverage`：异常 Pod 是否各自完成实时 case。
- `dimension_coverage`：K8s、Metrics、Logging、DeepFlow/Trace、Topology 是否真实存在。
- `diagnostic_evidence_completeness`：计划中的决定性证据是否已经验证。

诊断概览优先展示 `diagnostic_evidence_completeness`。目标 case 全部成功但仍存在缺失维度、冲突或关键问题未验证时，不得显示 100%。

## 粗粒度与细粒度工具流程

```text
异常 Pod
  -> collect_aiops_case
  -> 检查 coverage / dimension_details / conflicts / limitations
  -> 判断当前数据是否足以支撑根因
     -> 足够：停止采集
     -> 不足：按 recommended_refs_by_dimension 调 get_aiops_case_evidence
     -> MCP coverage 缺失：调用对应 kubectl/Prometheus 等降级工具
  -> RCA
```

mandatory case 全部返回后，Evidence Agent 必须获得一次继续推理机会。只有模型明确判断关键问题已回答且没有必要补采，才允许停止。上下文达到 80% 时仍立即停止新增工具。

## 最终报告

保留：

- 诊断概览
- 现象描述
- 可观测性数据
- 已采集核心证据
- 证据关联分析
- 根因分析
- 修复建议、验证步骤、注意事项
- 结构化修复计划
- 机器可核验附录

移除：

- 诊断概览后的“采集统计”章节

可观测性表格每个异常 Pod 分别展示：

- Metrics：指标名、时间窗口、start/max/last/limit/ratio 和关键样本。
- Logging：日志原文、事件名、错误码、Pod、时间和 trace ID。
- Tracing：DeepFlow 请求、响应码、时延、源/目标和 trace ID；Tempo span 与关键 attributes。
- K8s：当前状态、Last State、reason、exit code 和 restart count。

拓扑部分保留原始边，并增加一段确定性或受约束的自然语言总结，说明：

- 调用从哪里进入目标 Pod。
- Service 如何选择目标 Pod。
- Pod 由哪个 ReplicaSet/Deployment 管理。
- 责任实体和影响边界在哪里。
- 拓扑只能证明关系，不能单独证明根因。

## 验证标准

1. 构造包含多个 `ai_usage` 和 tool start/result 的状态，最终统计与事件数量和耗时一致。
2. 只有 case 成功但存在关键缺失时，Evidence 不立即停止，允许调用细粒度工具。
3. case 信息充分时，模型可不调用细粒度工具并正常停止。
4. 最终报告不包含“采集统计”章节。
5. 可观测性表格包含真实 Metrics、Logging、DeepFlow、Tempo 和 K8s 关键字段。
6. 拓扑部分包含原始边和人可读责任/调用/影响总结。
7. 使用真实集群模糊问题运行，核对归档事件、最终统计和报告内容。
