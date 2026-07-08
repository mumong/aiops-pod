# 轻量计划：robusta 延迟优化 + 架构去冗余（行为无损）+ 完成 001

关联 ADR：[docs/adr/0001-behavior-preserving-perf-optimization.md](adr/0001-behavior-preserving-perf-optimization.md)

## 铁律护栏（每次改动后必须复验）

- robusta：`.venv/bin/python -m pytest tests/unit -q` = **404 passed**（基线）
- mcpstander：`.venv/bin/python -m unittest discover -s tests` = **12 OK**（基线）
- **绝不影响功能/诊断结果**；触碰诊断行为（LLM 轮次、采证逻辑、early_stop）的改动一律不做。
- 每完成一项 → 跑对应单测保持全绿 → 再进下一项。

## Track A — 延迟优化（行为无损）

读码后的诚实结论：在"绝不影响功能"铁律下，纯延迟项大多踩线，唯 A1 是安全大头。
- [x] A1 关 `AIOPS_CONTEXT_USAGE_PROBE`：deploy env `secretKeyRef` → 显式 `value:"false"`，与密钥解耦（**已做**，最大非诊断延迟来源）
- [~] A2 conclusion 流式 — **丢弃**：最终报告要过整段后处理（`_enforce_evidence_stats`/`_strip_think_blocks`/`_normalize_ask_remediation_plan`），逐 token 流会绕过后处理→改输出→踩功能红线
- [ ] A3 MCP 工具持久会话 — **暂缓**：仅在带"断连即回退无状态per-call"兜底时才安全；收益中、复杂度中
- [ ] A4 `estimate()`/落盘 I/O 安全去重 — **低优先**：A1 关探针后收益已微
- [~] A5 复用 ChatOpenAI+event loop — **丢弃**：需改"每调用一 loop"执行模型，功能风险高、明文 HTTP 内网收益仅几 ms

## Track B — 架构精简 / 去冗余（行为无损）

前提：仅在**测试覆盖充分**处动手；纯删/纯合并，不改可观测行为。全程 404→408 单测护栏。
- [x] B1 死代码清理：grep 复验后删除 10 个 0 调用/0 测试/0 反射的私有死方法 + 1 个失引用 import（`ea4c5aa`，~246 行）
- [x] B2 重复逻辑上移基类：`_get_prompt_language`(4→1)、`_has_successful_tool_results`(2→1) 收敛到 `WorkflowNode`（`42e0142`）
- [ ] B3（**deferred，NEEDS-REVIEW，留作后续**，均需跨文件/涉行为需谨慎复核）：
  - `_archive_node_input`(3 份，日志前缀不同 → 需参数化上移)、`_is_llm_unavailable_text`/单行摘要压缩/QUERY LayerOutput dict/`safe_json_loads`(十余处 try-except) 等重复逻辑合并
  - `layer_classifier` 1497 附近确证不可达块 + `_has_early_stop_event` 传递性死代码（控制流复核后可清）
  - 巨型文件职责拆分（纯搬运、导入等价）——风险最高，建议独立小步进行

## 最终整体测试（2026-07-08）

- robusta：`pytest tests/` = **408 passed**；`pytest tests/unit` = 404 passed
- mcpstander：`unittest discover -s tests` = **28 OK**
- app 装配冒烟：4 个节点均继承 base 的 `_get_prompt_language`/`_has_successful_tool_results`，无 local override 残留，工作流成图正常

## Track C — 完成 001（data 指引：测试 → 审查 → 开发）

- [ ] C1 补 mcpstander 分组测试：T016（collectors）/ T021 T022（coarse 契约 + no-data 断言）
- [ ] C2 T048 审查两仓 diff 范围仅限迁移文件
- [ ] C3 完成任何未竟开发（若审查发现缺口）
- [ ] C4 更新 data/specs/001 tasks 勾选与 quickstart 记录

## 执行顺序

A（在飞，先收尾）→ C（补测试+审查，风险低、可闭环）→ B（去冗余，需最谨慎、最后做）
