# AIOps 证据统计修正设计

## 目标

让报告统计真实反映异常 Pod 的实时可观测性采集情况，避免同一 Pod 的重复计划项、Layer 定位工具和 Runbook 干扰完整度。

## 设计

1. `collect_aiops_case` 计划按 `tool + namespace + pod` 归一化，同一 Pod 只保留一项。
2. Pod 目标可从 `tool_args`、`command`、`target_scope` 中解析，兼容 Qwen 生成的不同表达。
3. 报告区分三类统计：
   - Pod 可观测性覆盖：成功采集 case 的 Pod 数 / mandatory Pod 数。
   - 补充证据完成度：去重后的 evidence plan 完成数 / 计划数。
   - 工具调用：仅作为调试信息，不参与完整度。
4. Layer 扫描和 Runbook 是定位上下文，不进入 evidence 完整度分母。
5. Runbook 仍由 Qwen 选择。拿到真实 case 后，如果日志、Kubernetes 终态或 Trace 明确表明更具体异常，允许补充一个更具体的 Runbook；不得重复已有 Runbook。
6. 拓扑正文必须区分 `calls` 与 `owned_by`，主表只能引用真实完整 evidence ref。

## 验收

- 两个异常 Pod 各执行一次 `collect_aiops_case` 时，Pod 覆盖显示 `2/2（100%）`。
- 同目标重复 coarse 计划不增加分母，也不产生虚假的缺失项。
- Runbook 不重复调用。
- 报告正文引用真实日志、完整 trace ID、准确拓扑关系和 evidence ref。
- 连续三次模糊诊断均满足以上条件。
