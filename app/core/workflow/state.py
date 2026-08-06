"""
工作流状态模型

设计原则：
- 与现有数据结构对接（Layer, DeterministicDecision, EvidenceItem）
- 支持增量更新（每个节点只更新自己负责的字段）
- 类型安全（TypedDict 提供类型提示）
- 每个节点的 LLM 分析结果都被保存，供下游节点使用
"""

from typing import TypedDict, Optional, List, Dict, Any

from app.core.skills.models import Layer, DeterministicDecision, EvidenceItem


class WorkflowState(TypedDict, total=False):
    """
    工作流状态（LangGraph StateGraph 要求）
    
    注意：使用 total=False 表示所有字段都是可选的，支持增量更新
    
    每个节点都有两类输出：
    1. 结构化数据（如 layer, evidence_items）- 用于程序处理
    2. LLM 分析文本（如 layer_analysis）- 保留完整的 LLM 分析供下游使用
    """
    # ========== 输入 ==========
    question: str
    run_id: str
    
    # ========== 节点1 输出：问题定位 ==========
    layer: Optional[Layer]               # 主层级（根因最深的层级，用于路由和下游处理）
    layers: List[Layer]                  # 所有检测到的层级（多问题并存时有多个）
    layer_confidence: Optional[float]    # 定层置信度 [0, 1]
    layer_reasoning: Optional[str]       # 定层理由
    layer_analysis: Optional[str]        # LLM 完整分析（JSON 字符串）
    layer_full_analysis: Optional[str]   # Deprecated: 大文本不再跨节点传递，完整内容写入 context archive
    layer_handoff: Optional[Dict[str, Any]]  # 阶段1给下游的结构化交接信息
    layer_archive_ref: Optional[Dict[str, Any]]  # layer 全量分析与 handoff 归档引用
    issue_groups: List[Dict[str, Any]]     # Deprecated alias: 当前异常问题组（按异常状态族聚合）
    abnormal_groups: List[Dict[str, Any]]  # 当前异常组（按异常状态族聚合）
    abnormal_pods: List[Dict[str, Any]]    # 当前异常 Pod 列表（紧凑摘要）
    pod_status_keyword: Optional[str]      # 当前 Pod 异常状态关键字，如 CrashLoopBackOff/ImagePullBackOff
    pod_abnormal_type: Optional[str]       # 当前 Pod 异常类型，如 OOMKilled/ConfigBootstrapFail
    derived_layer: Optional[str]           # Pod 异常状态派生出的兼容 L0-L4/HEALTHY 层级
    status_category: Optional[str]         # Pod 异常类型的归一化类别，如 container_resource/image_registry
    context_archive_ref: Optional[str]   # 当前 run 的 context archive 根目录
    context_budget: Optional[Dict[str, Any]]  # 最近一次/汇总上下文预算估算
    tool_artifact_refs: List[Dict[str, Any]]  # 工具 raw/structured/summary 归档引用
    key_entities: List[str]              # 提取的关键实体
    possible_scenarios: List[str]        # 可能的场景
    
    # ========== 节点2 输出：证据链 ==========
    # 多异常并发模式（异常组 > 阈值时由 parallel_evidence 节点填充）：
    # 每组独立 evidence context 采集+单组分析的结果列表，conclusion 据此
    # 确定性拼接真实数据 + LLM 读摘要写结论。非并发模式为 None。
    group_results: Optional[List[Dict[str, Any]]]
    evidence_items: List[EvidenceItem]   # 已采集证据
    tool_results: List[Dict]             # 工具调用结果
    evidence_completeness: Optional[float]  # 证据完整度 [0, 1]
    evidence_analysis: Optional[str]     # LLM 完整分析（JSON 字符串）
    query_result: Optional[Dict[str, Any]]  # QUERY 模式下的结构化查询结果
    evidence_facts: List[Dict[str, Any]]     # 已验证事实摘要
    evidence_conflicts: List[Dict[str, Any]] # 负向/冲突观察
    missing_evidence: List[Dict[str, Any]]   # 缺失证据

    # ========== 节点3 输出：根因分析 ==========
    deterministic_decision: Optional[DeterministicDecision]  # 决策对象
    root_cause: Optional[str]            # 根因结论
    causal_chain: Optional[Dict[str, str]]  # 因果链
    rca_analysis: Optional[str]          # LLM 完整分析（JSON 字符串）
    primary_runbook_id: Optional[str]    # AI 判定的核心 Runbook（与诊断结论最匹配的）
    
    # ========== 节点4 输出：汇总总结 ==========
    conclusion: Optional[str]            # 最终报告
    conclusion_formatted: Optional[str]  # 格式化后的 Markdown
    remediation_plan: Optional[Dict[str, Any]]  # conclusion 中提取的结构化修复计划
    remediation_result: Optional[Dict[str, Any]]  # 修复执行结果摘要
    
    # ========== 元数据 ==========
    current_node: Optional[str]          # 当前执行节点
    errors: List[str]                    # 错误列表
    warnings: List[str]                  # 警告列表
    thinking_events: List[Dict]          # 各节点的中间推理事件

    # ========== 多场景模式新增字段 ==========
    # 全局场景检测结果
    multi_scenario_decisions: Optional[Dict[str, Any]]  # 多场景输出对象
    detected_scenarios: List[Dict]            # 检测到的场景列表
    detection_duration: Optional[float]       # 检测耗时（秒）
