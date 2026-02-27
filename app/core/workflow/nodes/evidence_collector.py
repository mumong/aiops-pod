"""
节点2：证据链采集

职责：
- 调用 LLM 规划需要采集的证据
- 调用工具实际采集证据
- 记录 LLM 调用和工具调用统计
- 详细的输出，详细的给证据具有逻辑性
- 输出：evidence_items, evidence_analysis, evidence_completeness, tool_results

设计：
- 有自己的专用 prompt
- 调用 LLM 进行证据规划（使用和 HolmesService 相同的方式）
- 支持使用 runbooks 和 tools
- 统计 LLM 调用和工具调用次数
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.state import WorkflowState
from app.core.skills.models import Layer, EvidenceItem, EvidenceLevel
from app.core.skills.evidence import EvidenceExtractor, EVIDENCE_SPECS
from app.core.prompts import get_workflow_prompt
from holmes.core.prompt import build_initial_ask_messages

logger = logging.getLogger(__name__)


class EvidenceCollectorNode(WorkflowNode):
    """
    证据链采集节点

    每次执行都会：
    1. 调用 LLM 规划需要采集的证据
    2. 调用工具实际采集证据
    3. 统计 LLM 调用和工具调用次数
    4. 计算证据完整度
    """

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        """
        初始化节点

        Args:
            holmes_service: HolmesService 实例（用于 LLM 和工具调用）
            metrics: WorkflowMetrics 实例（用于记录统计）
            runbook_catalog: RunbookCatalog 实例（用于 runbook 匹配）
        """
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog

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

        流程：
        1. 调用 LLM 规划需要采集的证据
        2. 根据规划调用工具采集证据
        3. 解析工具输出，标记哪些证据已采集
        4. 计算证据完整度
        5. 记录 LLM 调用和工具调用次数到 metrics
        """
        new_state: WorkflowState = {
            "current_node": self.node_id,
        }

        try:
            question = state.get("question", "")
            layer = state.get("layer")
            layer_analysis = state.get("layer_analysis", "{}")
            possible_scenarios = state.get("possible_scenarios", [])
            key_entities = state.get("key_entities", [])

            logger.info(f"📋 证据采集: 层级={layer}, 可能场景={possible_scenarios}")

            # 1. 调用 LLM 规划证据采集计划
            evidence_plan = self._plan_evidence_with_llm(
                question=question,
                layer=layer,
                possible_scenarios=possible_scenarios,
                key_entities=key_entities
            )

            # 2. 根据规划调用工具采集证据
            tool_results, collected_evidence = self._collect_evidence_by_tools(
                question=question,
                layer=layer,
                evidence_plan=evidence_plan,
                key_entities=key_entities
            )

            # 3. 构建证据项列表（基于规划 + 实际采集结果）
            evidence_items = self._build_evidence_items(
                evidence_plan=evidence_plan,
                tool_results=tool_results
            )

            # 4. 计算完整度
            completeness = self._calculate_completeness(evidence_items)

            # 5. 更新 metrics（记录 LLM 调用和工具调用次数）
            self._update_metrics(evidence_plan, tool_results)

            evidence_analysis_text = json.dumps({
                "evidence_plan": evidence_plan,
                "tool_results": [r.get("summary", "") for r in tool_results],
                "collection_summary": f"计划 {len(evidence_plan)} 项，实际采集 {sum(1 for e in evidence_items if e.collected)} 项"
            }, ensure_ascii=False)

            new_state.update({
                "evidence_items": evidence_items,
                "evidence_analysis": evidence_analysis_text,
                "evidence_completeness": completeness,
                "tool_results": tool_results,
                "llm_calls": 1,  # 规划阶段调用了 1 次 LLM
                "tool_call_count": len(tool_results),
            })

            # 同步写入通用节点分析视图
            node_analyses = new_state.get("node_analyses") or {}
            node_analyses[self.node_id] = evidence_analysis_text
            new_state["node_analyses"] = node_analyses

            collected = sum(1 for e in evidence_items if e.collected)
            logger.info(f"✅ 证据采集完成: {collected}/{len(evidence_items)} 项, 完整度 {completeness:.0%}")
            logger.info(f"   LLM 调用: 1 次, 工具调用: {len(tool_results)} 次")

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

    def _plan_evidence_with_llm(
        self,
        question: str,
        layer: Optional[Layer],
        possible_scenarios: List[str],
        key_entities: List[Dict]
    ) -> List[Dict]:
        """
        调用 LLM 规划证据采集（使用和 HolmesService 相同的方式）

        Args:
            question: 用户问题
            layer: 判定的层级
            possible_scenarios: 可能的场景
            key_entities: 关键实体

        Returns:
            证据采集计划列表
        """
        if not self.holmes_service or not self.holmes_service.ai:
            logger.warning("⚠️ 无 LLM 服务，使用规则规划")
            return self._plan_with_rules(question, layer)

        try:
            start_time = time.time()

            layer_str = layer.value if layer else "L2"
            scenarios_str = ", ".join(possible_scenarios) if possible_scenarios else "未知"

            # 构建 entities 信息用于 prompt
            entities_str = ""
            if key_entities:
                entities_str = "\n".join([
                    f"  - {e.get('type', '')}: {e.get('value', '')}"
                    for e in key_entities[:10]
                ])

            # 构建完整的 system prompt
            base_prompt = get_workflow_prompt(self.node_id)
            system_prompt = base_prompt.format(
                layer=layer_str,
                possible_scenarios=scenarios_str
            )

            # 添加 entities 信息到 prompt
            if entities_str:
                system_prompt += f"\n\n# 已提取的关键实体\n{entities_str}\n"

            # 使用 build_initial_ask_messages 构建消息
            # 这样可以支持 runbooks 和 tools
            messages = build_initial_ask_messages(
                console=self.holmes_service.console,
                initial_user_prompt=question,
                file_paths=None,
                tool_executor=self.holmes_service.ai.tool_executor,
                runbooks=self.runbook_catalog,
                system_prompt_additions=system_prompt
            )

            # 调用 LLM（使用和 HolmesService 相同的方式）
            if self.holmes_service.stream_output:
                response = self.holmes_service._call_with_stream(messages)
            else:
                response = self.holmes_service.ai.call(messages)

            llm_duration_ms = (time.time() - start_time) * 1000

            # 记录 LLM 调用
            if self.metrics:
                self.metrics.record_llm_call("evidence", llm_duration_ms)

            if response and response.result:
                logger.debug(f"LLM 规划响应 (耗时 {llm_duration_ms:.0f}ms): {response.result[:500]}...")
                return self._parse_llm_evidence_plan(response.result)

            logger.warning("LLM 未返回有效响应，使用规则规划")
            return self._plan_with_rules(question, layer)

        except Exception as e:
            logger.warning(f"LLM 规划失败，回退到规则: {e}")
            return self._plan_with_rules(question, layer)

    def _parse_llm_evidence_plan(self, response_text: str) -> List[Dict]:
        """
        解析 LLM 返回的证据计划

        Args:
            response_text: LLM 返回的文本

        Returns:
            证据计划列表
        """
        try:
            # 尝试提取 JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
                if "evidence_plan" in parsed:
                    return parsed["evidence_plan"]
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 如果不是 JSON，尝试提取命令列表
            return self._extract_commands_from_text(response_text)

    def _extract_commands_from_text(self, text: str) -> List[Dict]:
        """
        从文本中提取 kubectl 命令

        Args:
            text: LLM 返回的文本

        Returns:
            命令列表
        """
        commands = []
        # 提取 kubectl 命令
        kubectl_pattern = r'kubectl\s+(?:get|describe|logs|top|exec|apply|delete)[^\n]+'
        for match in re.finditer(kubectl_pattern, text, re.MULTILINE):
            cmd = match.group(0).strip()
            commands.append({
                "id": f"cmd_{len(commands)}",
                "description": f"执行命令: {cmd}",
                "level": "critical" if "describe" in cmd or "get events" in cmd else "important",
                "command": cmd,
                "tool": "kubectl",
                "purpose": "获取集群状态或资源信息"
            })
        return commands

    def _plan_with_rules(
        self,
        question: str,
        layer: Optional[Layer]
    ) -> List[Dict]:
        """使用规则规划证据（回退方案）"""
        scenario = self._layer_to_scenario(layer, question)
        specs = EVIDENCE_SPECS.get(scenario, [])

        evidence_plan = []
        for spec in specs:
            evidence_plan.append({
                "id": spec.id,
                "description": spec.description,
                "level": spec.level.value,
                "command": self._get_command_for_evidence(spec, question),
                "tool": "kubectl",
                "purpose": spec.description
            })

        return evidence_plan

    def _get_command_for_evidence(self, spec, question: str) -> str:
        """
        根据证据规格生成对应的 kubectl 命令

        Args:
            spec: EvidenceSpec
            question: 用户问题

        Returns:
            kubectl 命令
        """
        # 基于证据 ID 生成命令
        command_map = {
            # L0-DiskFull
            "disk_usage": "df -h",
            "enospc_error": "kubectl get events -A --field-selector='reason=FreeDiskSpaceFailed' --sort-by='.lastTimestamp'",
            "top_directories": "du -sh /var/log /var/lib 2>/dev/null | head -20",
            # L1-KubeletCert
            "node_status": "kubectl get nodes -o wide",
            "cert_error": "kubectl get events -A --field-selector='reason.*certificate' --sort-by='.lastTimestamp'",
            "kubelet_logs": "journalctl -u kubelet -n 50 --no-pager",
            # L2-OOMKilled
            "oom_reason": "kubectl get pods -A --field-selector='status.phase!=Running' --sort-by='.metadata.creationTimestamp'",
            "exit_code_137": "kubectl get pods -A -o jsonpath='{.items[*].status.containerStatuses[*].state.terminated.exitCode}' | grep -v 'null'",
            "previous_logs": "kubectl logs --previous --tail=100 --all-containers 2>/dev/null || echo 'No previous logs'",
            "memory_limit": "kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].resources.limits}'",
            # L2-VolumeLimitExceeded
            "evicted_reason": "kubectl get events -A --field-selector='reason=Evicted' --sort-by='.lastTimestamp'",
            "volume_limit_exceeded": "kubectl get events -A --field-selector='reason.*volume' --sort-by='.lastTimestamp'",
            "pod_events": "kubectl get events -A --sort-by='.lastTimestamp' | head -50",
            # L3-DNSLatency
            "dns_lookup_time": "kubectl get pods -n kube-system -l k8s-app=kube-dns",
            "coredns_status": "kubectl get pods -n kube-system | grep coredns",
            # L4-Dependency503
            "upstream_503": "kubectl get pods -A --field-selector='status.phase!=Running'",
            "app_5xx_logs": "kubectl logs --all-containers --tail=50 2>/dev/null || echo 'No logs available'",
            "dependency_check": "kubectl get svc -A",
        }

        return command_map.get(spec.id, "kubectl get pods -A")

    def _layer_to_scenario(self, layer: Optional[Layer], question: str) -> str:
        """根据层级和问题确定场景"""
        q_lower = question.lower()

        scenario_keywords = {
            "L0-DiskFull": ["disk", "磁盘", "enospc", "no space", "df"],
            "L1-KubeletCert": ["kubelet", "证书", "certificate", "notready", "node"],
            "L2-OOMKilled": ["oom", "137", "内存", "memory", "重启", "evicted"],
            "L2-VolumeLimitExceeded": ["volume", "存储", "evicted", "limit"],
            "L3-DNSLatency": ["dns", "coredns", "网络", "network", "connect"],
            "L4-Dependency503": ["503", "依赖", "upstream", "service", "pod"],
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

    def _collect_evidence_by_tools(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_plan: List[Dict],
        key_entities: List[Dict]
    ) -> Tuple[List[Dict], Dict[str, str]]:
        """
        根据规划调用工具采集证据

        Args:
            question: 用户问题
            layer: 判定的层级
            evidence_plan: 证据采集计划
            key_entities: 关键实体

        Returns:
            (工具调用结果, 已采集证据的映射)
        """
        tool_results = []
        collected_evidence = {}

        # 提取关键实体（用于动态生成命令）
        pod_names = [e.get("value", "") for e in key_entities if e.get("type") == "Pod"]
        node_names = [e.get("value", "") for e in key_entities if e.get("type") == "Node"]
        namespaces = [e.get("value", "") for e in key_entities if e.get("type") == "Namespace"]

        # 从 evidence_plan 生成默认命令
        default_commands = []
        for item in evidence_plan:
            cmd = item.get("command", "")
            if cmd and cmd not in default_commands:
                default_commands.append(cmd)

        # 如果没有命令，使用默认命令集
        if not default_commands:
            default_commands = self._get_default_commands(layer, question)

        # 执行命令采集证据
        for cmd in default_commands:
            try:
                start_time = time.time()
                result = self._execute_command(cmd, question, pod_names, node_names, namespaces)
                duration_ms = (time.time() - start_time) * 1000

                # 记录工具调用
                if self.metrics:
                    self.metrics.record_tool_call(
                        tool_name="kubectl",
                        duration_ms=duration_ms,
                        success=result is not None
                    )

                if result:
                    tool_results.append({
                        "tool": "kubectl",
                        "command": cmd,
                        "result": result[:500] if len(result) > 500 else result,
                        "success": True,
                        "duration_ms": duration_ms,
                        "summary": f"✅ {cmd[:40]}... (成功, {duration_ms/1000:.1f}s)"
                    })
                    # 标记对应的证据为已采集
                    collected_evidence[cmd] = result
                else:
                    tool_results.append({
                        "tool": "kubectl",
                        "command": cmd,
                        "result": "命令执行失败或超时",
                        "success": False,
                        "duration_ms": duration_ms,
                        "summary": f"❌ {cmd[:40]}... (失败, {duration_ms/1000:.1f}s)"
                    })

            except Exception as e:
                logger.error(f"命令执行失败: {cmd}: {e}")
                tool_results.append({
                    "tool": "kubectl",
                    "command": cmd,
                    "result": str(e)[:200],
                    "success": False,
                    "summary": f"❌ {cmd[:40]}... (错误: {str(e)[:50]})"
                })

        return tool_results, collected_evidence

    def _get_default_commands(
        self,
        layer: Optional[Layer],
        question: str
    ) -> List[str]:
        """获取默认命令列表"""
        # 基于层级的默认命令集
        layer_commands = {
            Layer.L0: [
                "df -h",
                "kubectl get events -A --sort-by='.lastTimestamp' | head -20",
                "kubectl get nodes -o wide",
            ],
            Layer.L1: [
                "kubectl get nodes -o wide",
                "kubectl get events -A --sort-by='.lastTimestamp' | head -30",
                "journalctl -u kubelet -n 30 --no-pager",
            ],
            Layer.L2: [
                "kubectl get pods -A -o wide",
                "kubectl get events -A --sort-by='.lastTimestamp' | head -50",
                "kubectl get pods -A -o jsonpath='{.items[*].status.containerStatuses[*].state}'",
            ],
            Layer.L3: [
                "kubectl get svc -A",
                "kubectl get endpoints -A",
                "kubectl get pods -n kube-system -l k8s-app=kube-dns",
                "kubectl get events -A --sort-by='.lastTimestamp' | head -30",
            ],
            Layer.L4: [
                "kubectl get pods -A -o wide",
                "kubectl get svc -A",
                "kubectl get events -A --sort-by='.lastTimestamp' | head -50",
            ],
        }

        return layer_commands.get(layer, layer_commands[Layer.L2])

    def _execute_command(
        self,
        cmd: str,
        question: str,
        pod_names: List[str],
        node_names: List[str],
        namespaces: List[str]
    ) -> Optional[str]:
        """
        执行 kubectl 命令

        Args:
            cmd: 要执行的命令
            question: 用户问题
            pod_names: Pod 名称列表
            node_names: Node 名称列表
            namespaces: Namespace 列表

        Returns:
            命令输出
        """
        import subprocess

        logger.debug(f"执行命令: {cmd}")

        try:
            # 超时 15 秒（证据采集需要更长超时）
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                return result.stdout
            else:
                stderr = result.stderr or ""
                if stderr:
                    logger.debug(f"命令返回错误: {stderr[:200]}")
                return result.stdout + "\n" + stderr

        except subprocess.TimeoutExpired:
            logger.warning(f"命令超时: {cmd}")
            return "命令超时（15秒）"
        except Exception as e:
            logger.error(f"命令执行失败: {cmd}: {e}")
            return None

    def _build_evidence_items(
        self,
        evidence_plan: List[Dict],
        tool_results: List[Dict]
    ) -> List[EvidenceItem]:
        """
        构建证据项列表

        Args:
            evidence_plan: 证据采集计划
            tool_results: 工具调用结果

        Returns:
            EvidenceItem 列表
        """
        evidence_items = []

        # 从问题中初步提取已有证据
        scenario = self._layer_to_scenario(None, " ".join([p.get("description", "") for p in evidence_plan]))
        initial_items, _ = EvidenceExtractor.extract_all(
            " ".join([p.get("description", "") for p in evidence_plan]),
            scenario
        )

        # 合并规划项和实际采集结果
        for plan_item in evidence_plan:
            item_id = plan_item.get("id", f"ev_{len(evidence_items)}")

            # 检查是否有对应的工具结果
            has_result = False
            result_value = None

            for tool_result in tool_results:
                tool_cmd = tool_result.get("command", "")
                plan_cmd = plan_item.get("command", "")

                # 命令匹配
                if plan_cmd and tool_cmd and plan_cmd in tool_cmd:
                    has_result = True
                    result_value = tool_result.get("result", "")
                    break

            # 确定证据级别
            level_str = plan_item.get("level", "important")
            level = EvidenceLevel.IMPORTANT
            if level_str == "critical":
                level = EvidenceLevel.CRITICAL
            elif level_str == "optional":
                level = EvidenceLevel.OPTIONAL

            evidence_items.append(EvidenceItem(
                id=item_id,
                description=plan_item.get("description", "未知证据"),
                level=level,
                weight=0.2,
                collected=has_result,
                value=result_value,
                source="tool_result" if has_result else "planned"
            ))

        # 添加初始提取的证据
        for init_item in initial_items:
            if not any(e.id == init_item.id for e in evidence_items):
                evidence_items.append(init_item)

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

    def _update_metrics(
        self,
        evidence_plan: List[Dict],
        tool_results: List[Dict]
    ):
        """更新 metrics 统计"""
        if not self.metrics:
            return

        # LLM 调用已经在 _plan_evidence_with_llm 中记录了
        # 这里只补充统计（如果有额外调用）

        # 记录工具调用统计
        for tool_result in tool_results:
            duration_ms = tool_result.get("duration_ms", 0)
            success = tool_result.get("success", True)
            self.metrics.record_tool_call(
                tool_name=tool_result.get("tool", "kubectl"),
                duration_ms=duration_ms,
                success=success
            )
