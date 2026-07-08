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

前提：仅在**测试覆盖充分**处动手；纯删/纯合并，不改可观测行为。
- [ ] B1 死代码 / 未被引用的函数、分支扫描并清理（先出证据清单）
- [ ] B2 重复逻辑合并（同一处理散落多份）
- [ ] B3 巨型文件职责拆分（evidence_collector 2885 / conclusion_formatter 1822 / layer_classifier 1766 / client 1677 / observation 1433），仅纯搬运、导入等价

## Track C — 完成 001（data 指引：测试 → 审查 → 开发）

- [ ] C1 补 mcpstander 分组测试：T016（collectors）/ T021 T022（coarse 契约 + no-data 断言）
- [ ] C2 T048 审查两仓 diff 范围仅限迁移文件
- [ ] C3 完成任何未竟开发（若审查发现缺口）
- [ ] C4 更新 data/specs/001 tasks 勾选与 quickstart 记录

## 执行顺序

A（在飞，先收尾）→ C（补测试+审查，风险低、可闭环）→ B（去冗余，需最谨慎、最后做）
