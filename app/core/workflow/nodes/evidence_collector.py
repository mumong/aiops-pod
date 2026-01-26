"""
节点2：证据链采集

职责：
- 调用 LLM 规划需要采集的证据
- 调用工具采集证据
- 输出：evidence_items, evidence_analysis, evidence_completeness

设计：
- 有自己的专用 prompt
- 调用 LLM 进行证据规划
- 使用 HolmesGPT 工具采集证据
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.state import WorkflowState
from app.core.skills.models import Layer, EvidenceItem, EvidenceLevel
from app.core.skills.evidence import EvidenceExtractor, EVIDENCE_SPECS
from app.core.prompts import EVIDENCE_COLLECTOR_PROMPT

logger = logging.getLogger(__name__)


class EvidenceCollectorNode(WorkflowNode):
    """
    证据链采集节点
    
    每次执行都会调用 LLM 规划证据，然后采集证据
    """
    
    def __init__(self, holmes_service: Any = None):
        """
        初始化节点
        
        Args:
            holmes_service: HolmesService 实例（用于 LLM 和工具调用）
        """
        self.holmes_service = holmes_service
    
    @property
    def node_id(self) -> str:
        return "evidence"
    
    @property
    def node_name(self) -> str:
        return "证据链采集"
    
    def get_required_fields(self) -> List[str]:
        return ["question", "layer"]
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行证据采集逻辑
        
        1. 调用 LLM 规划需要采集的证据
        2. 调用工具采集证据
        3. 整理证据清单
        """
        new_state: WorkflowState = {
            "current_node": self.node_id,
        }
        
        try:
            question = state.get("question", "")
            layer = state.get("layer")
            layer_analysis = state.get("layer_analysis", "{}")
            possible_scenarios = state.get("possible_scenarios", [])
            
            logger.info(f"📋 证据采集: 层级={layer}")
            
            # 如果有 LLM 服务，使用 LLM 规划证据
            if self.holmes_service and self.holmes_service.ai:
                evidence_result = self._plan_with_llm(
                    question, layer, possible_scenarios
                )
            else:
                # 回退到规则
                logger.info("⚠️ 无 LLM 服务，使用规则规划")
                evidence_result = self._plan_with_rules(question, layer)
            
            # 从问题描述中提取证据（当前简化实现）
            evidence_items = self._extract_evidence(
                question, layer, evidence_result
            )
            
            # 计算完整度
            completeness = self._calculate_completeness(evidence_items)
            
            new_state.update({
                "evidence_items": evidence_items,
                "evidence_analysis": json.dumps(evidence_result, ensure_ascii=False),
                "evidence_completeness": completeness,
                "tool_results": evidence_result.get("evidence_plan", []),
            })
            
            collected = sum(1 for e in evidence_items if e.collected)
            logger.info(f"✅ 证据采集完成: {collected}/{len(evidence_items)} 项, 完整度 {completeness:.0%}")
        
        except Exception as e:
            logger.error(f"证据采集失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
            new_state.update({
                "evidence_items": [],
                "evidence_analysis": "{}",
                "evidence_completeness": 0.0,
                "tool_results": [],
            })
        
        return new_state
    
    def _plan_with_llm(
        self,
        question: str,
        layer: Optional[Layer],
        possible_scenarios: List[str]
    ) -> Dict:
        """使用 LLM 规划证据采集"""
        try:
            layer_str = layer.value if layer else "L2"
            scenarios_str = ", ".join(possible_scenarios) if possible_scenarios else "未知"
            
            # 构建 system prompt
            system_prompt = EVIDENCE_COLLECTOR_PROMPT.format(
                layer=layer_str,
                possible_scenarios=scenarios_str
            )
            
            # 构建消息列表
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
            
            # 调用 LLM
            response = self.holmes_service.ai.call(messages)
            
            if response and response.result:
                return self._parse_llm_response(response.result)
            
            return self._plan_with_rules(question, layer)
        
        except Exception as e:
            logger.warning(f"LLM 规划失败，回退到规则: {e}")
            return self._plan_with_rules(question, layer)
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """解析 LLM 的 JSON 响应"""
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "evidence_plan": [],
                "analysis": response_text[:500],
                "missing_info": ""
            }
    
    def _plan_with_rules(
        self,
        question: str,
        layer: Optional[Layer]
    ) -> Dict:
        """使用规则规划证据（回退方案）"""
        scenario = self._layer_to_scenario(layer, question)
        specs = EVIDENCE_SPECS.get(scenario, [])
        
        evidence_plan = []
        for spec in specs:
            evidence_plan.append({
                "id": spec.id,
                "description": spec.description,
                "level": spec.level.value,
                "command": f"根据 {spec.keywords[:2] if spec.keywords else '规则'} 提取",
                "purpose": spec.description
            })
        
        return {
            "evidence_plan": evidence_plan,
            "analysis": f"基于规则为 {scenario} 场景规划证据",
            "missing_info": ""
        }
    
    def _layer_to_scenario(self, layer: Optional[Layer], question: str) -> str:
        """根据层级和问题确定场景"""
        q_lower = question.lower()
        
        scenario_keywords = {
            "L0-DiskFull": ["disk", "磁盘", "enospc", "no space"],
            "L1-KubeletCert": ["kubelet", "证书", "certificate", "notready"],
            "L2-OOMKilled": ["oom", "137", "内存", "memory", "重启"],
            "L3-DNSLatency": ["dns", "coredns", "延迟"],
            "L4-Dependency503": ["503", "依赖", "upstream"],
        }
        
        for scenario, keywords in scenario_keywords.items():
            if any(kw in q_lower for kw in keywords):
                return scenario
        
        layer_default = {
            Layer.L0: "L0-DiskFull",
            Layer.L1: "L1-KubeletCert",
            Layer.L2: "L2-OOMKilled",
            Layer.L3: "L3-DNSLatency",
            Layer.L4: "L4-Dependency503",
        }
        return layer_default.get(layer, "L2-OOMKilled")
    
    def _extract_evidence(
        self,
        question: str,
        layer: Optional[Layer],
        plan_result: Dict
    ) -> List[EvidenceItem]:
        """从问题描述中提取证据"""
        scenario = self._layer_to_scenario(layer, question)
        evidence_items, _ = EvidenceExtractor.extract_all(question, scenario)
        
        # 补充 LLM 规划的证据项
        plan = plan_result.get("evidence_plan", [])
        existing_ids = {e.id for e in evidence_items}
        
        for item in plan:
            if item.get("id") not in existing_ids:
                level = EvidenceLevel.IMPORTANT
                if item.get("level") == "critical":
                    level = EvidenceLevel.CRITICAL
                elif item.get("level") == "optional":
                    level = EvidenceLevel.OPTIONAL
                
                evidence_items.append(EvidenceItem(
                    id=item.get("id", f"llm_{len(evidence_items)}"),
                    description=item.get("description", "LLM 规划的证据"),
                    level=level,
                    weight=0.2,
                    collected=False,
                    value=None,
                    source="llm_plan"
                ))
        
        return evidence_items
    
    def _calculate_completeness(self, evidence_items: List[EvidenceItem]) -> float:
        """计算证据完整度"""
        if not evidence_items:
            return 0.0
        
        total_weight = sum(e.weight for e in evidence_items)
        collected_weight = sum(e.weight for e in evidence_items if e.collected)
        
        if total_weight == 0:
            return 0.0
        
        return collected_weight / total_weight
