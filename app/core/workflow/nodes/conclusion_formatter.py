"""
节点4：汇总总结

职责：
- 整合前3个节点的 LLM 分析结果
- 调用 LLM 生成最终结构化报告
- 输出：conclusion, conclusion_formatted

设计：
- 有自己的专用 prompt
- 基于前3个节点的输出进行总结和扩展
- 使用和 HolmesService 相同的调用方式，支持 runbooks 和 tools
- 输出符合标准模板的完整报告
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.state import WorkflowState
from app.core.skills.models import Layer, DeterministicDecision, EvidenceItem, Confidence
from app.core.prompts import CONCLUSION_FORMATTER_PROMPT
from holmes.core.prompt import build_initial_ask_messages

logger = logging.getLogger(__name__)

# 模型单次输出上限：仅当 API 传入的 conclusion_max_tokens 超过此值时才使用此值，否则完全按传入参数。
# 可通过环境变量 CONCLUSION_MAX_TOKENS_CAP 覆盖（例如换用支持更大输出的模型时设为 32768），默认 8192（DeepSeek）。
def _get_conclusion_max_tokens_cap() -> int:
    try:
        v = os.environ.get("CONCLUSION_MAX_TOKENS_CAP", "")
        if v and v.isdigit():
            return int(v)
    except Exception:
        pass
    return 8192


CONCLUSION_MAX_TOKENS_CAP = _get_conclusion_max_tokens_cap()


class ConclusionFormatterNode(WorkflowNode):
    """
    汇总总结节点

    整合前3个节点的分析结果，生成最终报告
    """

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        """
        初始化节点

        Args:
            holmes_service: HolmesService 实例（用于 LLM 调用）
            metrics: WorkflowMetrics 实例（用于记录统计）
            runbook_catalog: RunbookCatalog 实例（用于 runbook 匹配）
        """
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog
    
    @property
    def node_id(self) -> str:
        return "conclusion"
    
    @property
    def node_name(self) -> str:
        return "汇总总结"
    
    def get_required_fields(self) -> List[str]:
        return ["question", "layer"]
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行汇总总结逻辑
        
        1. 收集前3个节点的分析结果
        2. 调用 LLM 生成最终报告
        3. 格式化输出
        """
        new_state: WorkflowState = {
            "current_node": self.node_id,
        }
        
        try:
            # 收集前3个节点的分析结果
            question = state.get("question", "")
            # 优先使用完整分析文本（含工具原始输出），回退到精简 JSON
            layer_analysis = state.get("layer_full_analysis", "") or state.get("layer_analysis", "{}")
            evidence_analysis = state.get("evidence_analysis") or "{}"
            rca_analysis = state.get("rca_analysis") or "{}"
            
            # 提取其他关键信息
            layer = state.get("layer")
            evidence_items = state.get("evidence_items", [])
            decision = state.get("deterministic_decision")
            root_cause = state.get("root_cause", "")
            causal_chain = state.get("causal_chain", {})
            
            # 使用 LLM 生成最终报告
            if self.holmes_service and self.holmes_service.ai:
                # 从 thinking_events 提取工具真实数据，补充给 conclusion LLM
                tool_data_text = self._build_tool_data_section(
                    state.get("thinking_events", [])
                )
                conclusion = self._generate_with_llm(
                    question=question,
                    layer_analysis=layer_analysis,
                    evidence_analysis=evidence_analysis,
                    rca_analysis=rca_analysis,
                    conclusion_max_tokens=state.get("conclusion_max_tokens"),
                    layer=layer,
                    tool_data_text=tool_data_text,
                )
            else:
                # 回退到模板格式化
                logger.info("⚠️ 无 LLM 服务，使用模板格式化")
                conclusion = self._format_with_template(
                    question=question,
                    layer=layer,
                    evidence_items=evidence_items,
                    decision=decision,
                    root_cause=root_cause,
                    causal_chain=causal_chain,
                    layer_analysis=layer_analysis,
                    evidence_analysis=evidence_analysis,
                    rca_analysis=rca_analysis,
                    errors=state.get("errors", []),
                    warnings=state.get("warnings", []),
                )
            
            new_state.update({
                "conclusion": conclusion,
                "conclusion_formatted": conclusion,
            })

            # 合并 conclusion 节点自己的 thinking_events + 上游的
            conclusion_thinking = getattr(self, '_conclusion_thinking', [])
            self._save_thinking(state, new_state, conclusion_thinking)

            logger.info(f"✅ 汇总总结完成: {len(conclusion)} 字符")

        except Exception as e:
            logger.error(f"汇总总结失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
            new_state.update({
                "conclusion": f"报告生成失败: {str(e)}",
                "conclusion_formatted": f"报告生成失败: {str(e)}",
            })
            self._save_thinking(state, new_state, [])
        
        return new_state
    
    def _generate_with_llm(
        self,
        question: str,
        layer_analysis: str,
        evidence_analysis: str,
        rca_analysis: str,
        conclusion_max_tokens: Optional[int] = None,
        layer: Optional[Layer] = None,
        tool_data_text: str = "",
    ) -> str:
        """
        使用 litellm 直接调用生成最终报告（纯文本生成，不带工具）。

        conclusion 节点不需要调工具，只需要基于前面节点的数据生成报告。
        如果带工具，LLM 会去调 fetch_runbook/TodoWrite 浪费时间且不生成报告。
        """
        import time

        cap = _get_conclusion_max_tokens_cap()
        requested = conclusion_max_tokens if conclusion_max_tokens is not None else cap
        max_tokens = min(requested, cap) if requested > cap else requested

        # 根据 layer 决定指令
        is_query = layer == Layer.QUERY
        is_healthy = layer == Layer.HEALTHY
        if is_healthy:
            instruction = f"""用户问了「{question}」，经过检查集群状态正常，没有发现异常。
请输出一份简洁的健康报告，列出检查过的项目和结果（节点状态、Pod 状态、事件等），
明确告诉用户"集群当前运行正常，未发现异常"。不要套诊断报告模板。"""
        elif is_query:
            instruction = """请基于以上各阶段的分析结果，直接回答用户的查询。
严格按照 system prompt 中的「查询模板」格式输出。
引用实际采集到的数据，不要套诊断报告模板。"""
        else:
            instruction = f"""请基于以上三个阶段的分析结果，生成一份详尽、完整的诊断报告。

⚠️ 最重要的规则：用户的原始问题是「{question}」，你的报告必须在开头直接回答这个问题。
- 如果用户问的是数据/指标（如 CPU 使用率、内存、磁盘），报告开头先用表格展示查到的实际数据，然后再展开诊断分析
- 如果用户问的是"有什么问题"，报告开头先总结当前集群的实际状态和发现的问题
- 不要让诊断模板淹没用户关心的核心信息

然后按照 system prompt 中的「诊断模板」格式输出（## 📊 诊断概览 → ## 🔍 现象描述 → ## 🕵️ 证据链 → ## 🎯 根因分析 → ## 🛠️ 修复建议）。
尽可能多引用原始数据和证据，修复命令可直接复制执行。"""

        tool_section = ""
        if tool_data_text:
            tool_section = f"\n# 工具采集的原始数据（重要！必须引用这些真实数据）\n{tool_data_text}\n"

        user_message = f"""# 用户问题
{question}

# 阶段1：问题定位分析
{layer_analysis}

# 阶段2：证据采集分析
{evidence_analysis}

# 阶段3：根因分析
{rca_analysis}
{tool_section}
{instruction}"""

        start_time = time.time()

        from litellm import completion

        model = self.holmes_service.ai.llm.model
        api_key = getattr(self.holmes_service.ai.llm, 'api_key', None)
        api_base = getattr(self.holmes_service.ai.llm, 'api_base', None)

        completion_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": CONCLUSION_FORMATTER_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
            "max_tokens": max_tokens,
        }
        if api_key:
            completion_kwargs["api_key"] = api_key
        if api_base:
            completion_kwargs["api_base"] = api_base

        resp = completion(**completion_kwargs)
        content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")

        llm_duration_ms = (time.time() - start_time) * 1000

        if self.metrics:
            self.metrics.record_llm_call("conclusion", llm_duration_ms)

        logger.info(f"LLM 报告生成完成 (耗时 {llm_duration_ms:.0f}ms, 长度: {len(content)})")

        # conclusion 不走 _call_llm，没有 thinking_events
        self._conclusion_thinking = []

        if content:
            return content

        return f"报告生成失败：LLM 未返回有效内容。\n\n原始数据：\n{tool_data_text[:1000] if tool_data_text else '无'}"
    
    def _format_fallback(
        self,
        question: str,
        layer_analysis: str,
        evidence_analysis: str,
        rca_analysis: str
    ) -> str:
        """简单格式化回退 - 分层展示各阶段分析"""
        # 解析各阶段的 JSON 分析结果，格式化展示
        layer_formatted = self._format_layer_section(layer_analysis)
        evidence_formatted = self._format_evidence_section(evidence_analysis)
        rca_formatted = self._format_rca_section(rca_analysis)
        
        return f"""
# 🔬 K8s 诊断报告

---

## 📍 阶段一：问题定位与分层

{layer_formatted}

---

## 🔍 阶段二：证据采集与分析

{evidence_formatted}

---

## 🎯 阶段三：根因分析与因果链

{rca_formatted}

---

## 📋 综合诊断结论

**用户问题**：{question}

> 请根据以上三个阶段的分析，参考证据链和因果分析，制定修复方案。

---
"""

    def _format_layer_section(self, layer_analysis: str) -> str:
        """格式化问题定位阶段的输出"""
        try:
            data = json.loads(layer_analysis) if layer_analysis else {}
        except:
            return f"```\n{layer_analysis}\n```" if layer_analysis else "*无分析数据*"
        
        lines = []
        
        # 层级信息
        layer = data.get("layer", "未知")
        layer_name = data.get("layer_name", "")
        confidence = data.get("confidence", 0)
        reasoning = data.get("reasoning", "")
        
        lines.append(f"### 层级判定")
        lines.append("")
        lines.append(f"| 项目 | 结果 |")
        lines.append(f"|------|------|")
        lines.append(f"| **层级** | {layer} - {layer_name} |")
        lines.append(f"| **置信度** | {confidence:.0%} |")
        lines.append("")
        
        # 推理过程
        if reasoning:
            lines.append(f"### 判定理由")
            lines.append("")
            lines.append(f"> {reasoning}")
            lines.append("")
        
        # 关键实体
        entities = data.get("key_entities", [])
        if entities:
            lines.append(f"### 提取的关键实体")
            lines.append("")
            if isinstance(entities[0], dict):
                lines.append("| 类型 | 值 |")
                lines.append("|------|-----|")
                for e in entities:
                    lines.append(f"| {e.get('type', '?')} | `{e.get('value', '?')}` |")
            else:
                for e in entities:
                    lines.append(f"- `{e}`")
            lines.append("")
        
        # 可能场景
        scenarios = data.get("possible_scenarios", [])
        if scenarios:
            lines.append(f"### 可能的故障场景")
            lines.append("")
            if isinstance(scenarios[0], dict):
                lines.append("| 场景 | 可能性 | 原因 |")
                lines.append("|------|--------|------|")
                for s in scenarios:
                    lines.append(f"| {s.get('scenario', '?')} | {s.get('probability', '?')} | {s.get('reason', '')} |")
            else:
                for s in scenarios:
                    lines.append(f"- {s}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_evidence_section(self, evidence_analysis: str) -> str:
        """格式化证据采集阶段的输出"""
        try:
            data = json.loads(evidence_analysis) if evidence_analysis else {}
        except:
            return f"```\n{evidence_analysis}\n```" if evidence_analysis else "*无分析数据*"
        
        lines = []
        
        # 采集策略
        strategy = data.get("collection_strategy", data.get("analysis", ""))
        if strategy:
            lines.append(f"### 采集策略")
            lines.append("")
            lines.append(f"> {strategy}")
            lines.append("")
        
        # 证据计划
        plan = data.get("evidence_plan", [])
        if plan:
            lines.append(f"### 证据采集清单")
            lines.append("")
            lines.append("| # | 级别 | 证据项 | 采集命令 | 用途 |")
            lines.append("|---|------|--------|----------|------|")
            
            for i, item in enumerate(plan, 1):
                level_icon = {"critical": "🔴", "important": "🟡", "optional": "⚪"}.get(item.get("level", ""), "")
                desc = item.get("description", "")[:30]
                cmd = item.get("command", "")[:40]
                purpose = item.get("purpose", item.get("expected_output", ""))[:40]
                lines.append(f"| {i} | {level_icon} {item.get('level', '')} | {desc} | `{cmd}` | {purpose} |")
            
            lines.append("")
        
        # 缺失信息
        missing = data.get("missing_info", "")
        if missing:
            lines.append(f"### ⚠️ 缺失信息")
            lines.append("")
            lines.append(f"> {missing}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_rca_section(self, rca_analysis: str) -> str:
        """格式化根因分析阶段的输出"""
        try:
            data = json.loads(rca_analysis) if rca_analysis else {}
        except:
            return f"```\n{rca_analysis}\n```" if rca_analysis else "*无分析数据*"
        
        lines = []
        
        # 现象描述
        phenomenon = data.get("phenomenon", "")
        if phenomenon:
            lines.append(f"### 现象总结")
            lines.append("")
            lines.append(f"> {phenomenon}")
            lines.append("")
        
        # 证据分析
        evidence_analysis = data.get("evidence_analysis", [])
        if evidence_analysis:
            lines.append(f"### 证据逐条分析")
            lines.append("")
            lines.append("| 证据ID | 原始数据 | 分析结论 |")
            lines.append("|--------|----------|----------|")
            
            for item in evidence_analysis:
                eid = item.get("evidence_id", item.get("id", "?"))
                raw = item.get("raw_data", item.get("evidence", ""))[:50]
                conclusion = item.get("interpretation", item.get("conclusion", ""))[:60]
                lines.append(f"| {eid} | {raw} | {conclusion} |")
            
            lines.append("")
        
        # 因果链
        causal = data.get("causal_chain", {})
        if causal:
            lines.append(f"### 因果链分析")
            lines.append("")
            lines.append("```")
            lines.append("┌─────────────────────────────────────────────────────┐")
            lines.append(f"│ 根本原因: {causal.get('root_cause', causal.get('trigger', '?'))[:45]:<45} │")
            lines.append("└─────────────────────────────────────────────────────┘")
            lines.append("                          ↓")
            lines.append("┌─────────────────────────────────────────────────────┐")
            lines.append(f"│ 传导机制: {causal.get('propagation', causal.get('mechanism', '?'))[:45]:<45} │")
            lines.append("└─────────────────────────────────────────────────────┘")
            lines.append("                          ↓")
            lines.append("┌─────────────────────────────────────────────────────┐")
            lines.append(f"│ 最终表现: {causal.get('manifestation', '?')[:45]:<45} │")
            lines.append("└─────────────────────────────────────────────────────┘")
            lines.append("```")
            lines.append("")
        
        # 根因结论
        root_cause = data.get("root_cause_summary", data.get("root_cause", ""))
        confidence = data.get("confidence", 0)
        if root_cause:
            lines.append(f"### 根因结论")
            lines.append("")
            lines.append(f"**结论**: {root_cause}")
            lines.append("")
            lines.append(f"**置信度**: {confidence:.0%}")
            lines.append("")
        
        # 置信度分解
        breakdown = data.get("confidence_breakdown", {})
        if breakdown:
            lines.append(f"#### 置信度评估")
            lines.append("")
            for key, value in breakdown.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")
        
        # 替代原因
        alternatives = data.get("alternative_causes", [])
        if alternatives:
            lines.append(f"### 其他可能原因")
            lines.append("")
            for alt in alternatives:
                if isinstance(alt, dict):
                    lines.append(f"- **{alt.get('cause', '?')}** (可能性: {alt.get('probability', '?')})")
                    if alt.get("missing_evidence"):
                        lines.append(f"  - 需要证据: {alt.get('missing_evidence')}")
                else:
                    lines.append(f"- {alt}")
            lines.append("")
        
        # 局限性
        limitations = data.get("limitations", "")
        if limitations:
            lines.append(f"### ⚠️ 分析局限性")
            lines.append("")
            lines.append(f"> {limitations}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_with_template(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_items: List[EvidenceItem],
        decision: Optional[DeterministicDecision],
        root_cause: str,
        causal_chain: Dict,
        layer_analysis: str,
        evidence_analysis: str,
        rca_analysis: str,
        errors: List[str],
        warnings: List[str],
    ) -> str:
        """使用模板格式化 - 分层展示各阶段完整分析"""
        
        # 层级名称映射
        layer_name_map = {
            Layer.QUERY: "QUERY - 直接查询",
            Layer.L0: "L0 - 基础设施层",
            Layer.L1: "L1 - 集群与节点层",
            Layer.L2: "L2 - 工作负载层",
            Layer.L3: "L3 - 服务与网络层",
            Layer.L4: "L4 - 应用层",
        }
        
        # 格式化各阶段分析
        layer_formatted = self._format_layer_section(layer_analysis)
        evidence_formatted = self._format_evidence_section(evidence_analysis)
        rca_formatted = self._format_rca_section(rca_analysis)
        
        # 构建完整报告
        report_lines = []
        
        # ========== 报告头部 ==========
        report_lines.append("# 🔬 K8s 诊断报告")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # ========== 诊断概览 ==========
        report_lines.append("## 📊 诊断概览")
        report_lines.append("")
        report_lines.append("| 项目 | 结果 |")
        report_lines.append("|------|------|")
        
        layer_name = layer_name_map.get(layer, str(layer)) if layer else "未确定"
        report_lines.append(f"| **问题层级** | {layer_name} |")
        
        if decision:
            confidence_str = decision.confidence.value if isinstance(decision.confidence, Confidence) else str(decision.confidence)
            report_lines.append(f"| **问题分类** | {decision.category} |")
            report_lines.append(f"| **置信度** | {confidence_str} ({decision.confidence_score:.0%}) |")
        
        evidence_count = len(evidence_items)
        collected_count = sum(1 for e in evidence_items if e.collected)
        report_lines.append(f"| **证据完整度** | {collected_count}/{evidence_count} ({collected_count/max(evidence_count,1):.0%}) |")
        
        report_lines.append("")
        
        # ========== 用户问题 ==========
        report_lines.append("## 🎯 用户问题")
        report_lines.append("")
        report_lines.append(f"> {question}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # ========== 阶段一：问题定位 ==========
        report_lines.append("## 📍 阶段一：问题定位与分层")
        report_lines.append("")
        report_lines.append(layer_formatted)
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # ========== 阶段二：证据采集 ==========
        report_lines.append("## 🔍 阶段二：证据采集与分析")
        report_lines.append("")
        report_lines.append(evidence_formatted)
        report_lines.append("")
        
        # 补充证据项详情
        if evidence_items:
            report_lines.append("### 已识别证据项")
            report_lines.append("")
            report_lines.append("| # | 证据项 | 级别 | 状态 | 采集值 |")
            report_lines.append("|---|--------|------|------|--------|")
            
            for i, item in enumerate(evidence_items, 1):
                level_icon = {"CRITICAL": "🔴", "IMPORTANT": "🟡", "OPTIONAL": "⚪"}.get(item.level.value.upper() if hasattr(item.level, 'value') else str(item.level).upper(), "")
                status = "✅ 已采集" if item.collected else "❌ 未采集"
                value = str(item.value)[:40] if item.value else "-"
                report_lines.append(f"| {i} | {item.description[:35]} | {level_icon} | {status} | `{value}` |")
            
            report_lines.append("")
        
        report_lines.append("---")
        report_lines.append("")
        
        # ========== 阶段三：根因分析 ==========
        report_lines.append("## 🎯 阶段三：根因分析与因果链")
        report_lines.append("")
        report_lines.append(rca_formatted)
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # ========== 综合结论 ==========
        report_lines.append("## 📋 综合诊断结论")
        report_lines.append("")
        
        if root_cause:
            report_lines.append(f"### 根因结论")
            report_lines.append("")
            report_lines.append(f"**{root_cause}**")
            report_lines.append("")
        
        if causal_chain:
            report_lines.append("### 因果链")
            report_lines.append("")
            report_lines.append("```")
            trigger = causal_chain.get("trigger", causal_chain.get("root_cause", "?"))
            mechanism = causal_chain.get("mechanism", causal_chain.get("propagation", "?"))
            manifestation = causal_chain.get("manifestation", "?")
            report_lines.append(f"[根本原因] {trigger}")
            report_lines.append(f"     ↓")
            report_lines.append(f"[传导机制] {mechanism}")
            report_lines.append(f"     ↓")
            report_lines.append(f"[最终表现] {manifestation}")
            report_lines.append("```")
            report_lines.append("")
        
        # ========== 修复建议 ==========
        report_lines.append("## 🛠️ 修复建议")
        report_lines.append("")
        
        if decision and decision.remediation_steps:
            for i, step in enumerate(decision.remediation_steps, 1):
                report_lines.append(f"{i}. {step}")
        else:
            report_lines.append("*请根据以上分析制定修复方案*")
        
        report_lines.append("")
        
        # ========== 警告和错误 ==========
        if warnings or errors:
            report_lines.append("---")
            report_lines.append("")
            report_lines.append("## ⚠️ 注意事项")
            report_lines.append("")
            
            if warnings:
                for w in warnings:
                    report_lines.append(f"- ⚠️ {w}")
            
            if errors:
                for e in errors:
                    report_lines.append(f"- ❌ {e}")
            
            report_lines.append("")
        
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("*报告由 K8s AIOps Copilot 工作流生成*")
        
        return "\n".join(report_lines)

    def _build_tool_data_section(self, thinking_events: list) -> str:
        """
        从 thinking_events 中提取所有节点的工具真实输出数据，
        构建一个文本段落供 conclusion LLM 引用。

        只提取 tool_result 类型且 status=success 的事件。
        """
        parts = []
        seen = set()
        for ev in thinking_events:
            if ev.get("type") != "tool_result":
                continue
            if ev.get("status") != "success":
                continue
            tool_name = ev.get("tool_name", "unknown")
            preview = ev.get("result_preview", "")
            if not preview:
                continue
            # 去重（同一工具同一数据不重复）
            key = f"{tool_name}:{preview[:80]}"
            if key in seen:
                continue
            seen.add(key)
            node = ev.get("node", "")
            parts.append(f"[{node}] {tool_name}: {preview}")

        if not parts:
            return ""
        return "\n".join(parts[:20])  # 最多 20 条，避免超长
