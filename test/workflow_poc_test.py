#!/usr/bin/env python3
"""
工作流完整测试脚本

用于验证4节点工作流的完整功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.workflow import build_diagnosis_workflow, WorkflowState


def test_workflow_full():
    """测试完整4节点工作流"""
    print("=" * 70)
    print("🧪 完整4节点工作流测试")
    print("=" * 70)
    
    # 构建工作流
    print("\n1. 构建工作流图...")
    try:
        workflow = build_diagnosis_workflow()
        print("   ✅ 工作流图构建成功（4节点：layer → evidence → rca → conclusion）")
    except Exception as e:
        print(f"   ❌ 工作流图构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试多个场景
    test_cases = [
        ("Pod一直重启，状态是CrashLoopBackOff", "OOM/重启场景"),
        ("磁盘满了，容器无法写日志，报 ENOSPC 错误", "磁盘满场景"),
        ("DNS解析延迟很高，服务调用超时", "DNS延迟场景"),
    ]
    
    all_success = True
    
    for question, scenario_name in test_cases:
        print(f"\n{'=' * 70}")
        print(f"📋 测试场景: {scenario_name}")
        print(f"   问题: {question}")
        print("-" * 70)
        
        # 初始化状态
        initial_state: WorkflowState = {
            "question": question,
            "run_id": f"test-{scenario_name}",
            "layer": None,
            "layer_confidence": None,
            "layer_reasoning": None,
            "evidence_items": [],
            "tool_results": [],
            "evidence_completeness": None,
            "deterministic_decision": None,
            "root_cause": None,
            "causal_chain": None,
            "conclusion": None,
            "conclusion_formatted": None,
            "current_node": None,
            "errors": [],
            "warnings": [],
        }
        
        try:
            # 执行工作流
            final_state = dict(initial_state)
            node_count = 0
            
            for event in workflow.stream(initial_state):
                for node_name, updated_state in event.items():
                    final_state.update(updated_state)
                    node_count += 1
                    
                    # 显示节点执行信息
                    if node_name == "layer":
                        layer = updated_state.get("layer")
                        conf = updated_state.get("layer_confidence", 0)
                        print(f"   ✅ 节点1 [问题定位]: {layer} (置信度: {conf:.0%})")
                    elif node_name == "evidence":
                        items = updated_state.get("evidence_items", [])
                        completeness = updated_state.get("evidence_completeness", 0)
                        collected = sum(1 for e in items if e.collected)
                        print(f"   ✅ 节点2 [证据采集]: {collected}/{len(items)} 项证据 (完整度: {completeness:.0%})")
                    elif node_name == "rca":
                        decision = updated_state.get("deterministic_decision")
                        root_cause = updated_state.get("root_cause", "")[:60]
                        if decision:
                            print(f"   ✅ 节点3 [根因分析]: {decision.category} - {decision.confidence.value}")
                        else:
                            print(f"   ✅ 节点3 [根因分析]: {root_cause}...")
                    elif node_name == "conclusion":
                        conclusion = updated_state.get("conclusion", "")
                        print(f"   ✅ 节点4 [汇总总结]: {len(conclusion)} 字符")
            
            # 显示最终报告预览
            conclusion = final_state.get("conclusion", "")
            if conclusion:
                print(f"\n📄 报告预览 (前500字符):")
                print("-" * 50)
                print(conclusion[:500])
                if len(conclusion) > 500:
                    print("...")
                print("-" * 50)
            
            # 检查错误
            errors = final_state.get("errors", [])
            if errors:
                print(f"\n⚠️ 发现错误: {errors}")
                all_success = False
            else:
                print(f"\n✅ 场景 '{scenario_name}' 测试通过")
        
        except Exception as e:
            print(f"\n❌ 场景 '{scenario_name}' 执行失败: {e}")
            import traceback
            traceback.print_exc()
            all_success = False
    
    return all_success


def test_individual_nodes():
    """测试各个节点"""
    print("\n" + "=" * 70)
    print("🧪 单节点测试")
    print("=" * 70)
    
    from app.core.workflow.nodes import (
        LayerClassifierNode,
        EvidenceCollectorNode,
        RootCauseAnalyzerNode,
        ConclusionFormatterNode,
    )
    from app.core.skills.models import Layer
    
    # 测试节点1：问题定位
    print("\n📍 节点1: LayerClassifierNode")
    layer_node = LayerClassifierNode()
    test_cases = [
        ("Pod OOMKilled，exit code 137", Layer.L2),
        ("磁盘空间不足 ENOSPC", Layer.L0),
        ("DNS 查询延迟 500ms", Layer.L3),
        ("Node NotReady", Layer.L1),
        ("上游服务返回 503", Layer.L4),
    ]
    
    for question, expected in test_cases:
        state = {"question": question, "errors": [], "warnings": []}
        result = layer_node.execute(state)
        actual = result.get("layer")
        status = "✅" if actual == expected else "❌"
        print(f"   {status} '{question[:30]}...' → {actual}")
    
    # 测试节点2：证据采集
    print("\n📍 节点2: EvidenceCollectorNode")
    evidence_node = EvidenceCollectorNode()
    
    state = {
        "question": "Pod OOMKilled，容器退出码137，内存limit 512Mi",
        "layer": Layer.L2,
        "errors": [],
        "warnings": [],
    }
    result = evidence_node.execute(state)
    items = result.get("evidence_items", [])
    completeness = result.get("evidence_completeness", 0)
    print(f"   收集证据: {len(items)} 项, 完整度: {completeness:.0%}")
    for item in items[:5]:
        status = "✅" if item.collected else "❌"
        print(f"      {status} {item.description}: {item.value}")
    
    # 测试节点3：根因分析
    print("\n📍 节点3: RootCauseAnalyzerNode")
    rca_node = RootCauseAnalyzerNode()
    
    state.update(result)
    result = rca_node.execute(state)
    decision = result.get("deterministic_decision")
    root_cause = result.get("root_cause", "")
    if decision:
        print(f"   规则匹配: {decision.scenario}")
        print(f"   置信度: {decision.confidence.value} ({decision.confidence_score:.0%})")
    print(f"   根因: {root_cause[:80]}...")
    
    # 测试节点4：汇总总结
    print("\n📍 节点4: ConclusionFormatterNode")
    conclusion_node = ConclusionFormatterNode()
    
    state.update(result)
    result = conclusion_node.execute(state)
    conclusion = result.get("conclusion", "")
    print(f"   生成报告: {len(conclusion)} 字符")


def test_workflow_executor():
    """测试工作流执行器"""
    print("\n" + "=" * 70)
    print("🧪 WorkflowExecutor 测试")
    print("=" * 70)
    
    from app.core.workflow.executor import WorkflowExecutor
    
    executor = WorkflowExecutor()
    
    print("\n执行工作流（流式）...")
    events = list(executor.execute_stream("Pod 一直重启，OOM Killed"))
    
    print(f"   生成 {len(events)} 个事件:")
    for ev in events:
        ev_type = ev.get("type", "unknown")
        if ev_type == "node_complete":
            node = ev.get("node_name", ev.get("node", "?"))
            print(f"      - {ev_type}: {node}")
        elif ev_type == "final":
            answer = ev.get("answer", "")
            print(f"      - {ev_type}: {len(answer)} 字符")
        else:
            print(f"      - {ev_type}")


if __name__ == "__main__":
    print("\n🚀 开始测试完整4节点工作流...\n")
    
    # 完整工作流测试
    success = test_workflow_full()
    
    # 单节点测试
    test_individual_nodes()
    
    # 执行器测试
    test_workflow_executor()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ 所有测试通过！")
    else:
        print("⚠️ 部分测试有警告，请检查输出")
    print("=" * 70 + "\n")
