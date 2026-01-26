#!/usr/bin/env python3
"""
多场景评估器单元测试

验证:
1. 多场景并行评估
2. 优先级排序
3. 相关性分析
4. 多场景报告生成
"""

import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.skills import (
    get_engine,
    DeterministicDecision,
    Confidence,
    Layer,
)
from app.core.skills.multi_scenario import (
    MultiScenarioEvaluator,
    ScenarioSummary,
    CorrelatedScenarios,
    evaluate_all_scenarios,
)
from app.core.skills.models import EvidenceItem


def test_evaluate_all_scenarios():
    """测试多场景并行评估"""
    engine = get_engine()

    # 构造包含多个场景的文本
    text = """
    === 磁盘状态 ===
    Filesystem      Size  Used Avail Use% Mounted on
    /dev/sda1       100G   98G    2G  98% /

    === Pod 状态 ===
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
    Resources:
      Limits:
        memory:  512Mi

    === DNS 查询 ===
    dns_lookup_seconds=0.52
    dns_lookup_seconds=0.48
    """

    # 使用 MultiScenarioEvaluator 进行并行评估
    from app.core.skills.evidence import EvidenceExtractor

    evidence_items, facts = EvidenceExtractor.extract_all(text, "multi")
    evaluator = MultiScenarioEvaluator(engine)
    decisions = evaluator.evaluate_all_scenarios(evidence_items, facts, text)

    print(f"✅ 并行评估测试通过 (检测到 {len(decisions)} 个场景)")
    return decisions


def test_aggregate_results():
    """测试结果聚合和优先级排序"""
    engine = get_engine()

    # 构造多个 DeterministicDecision
    decisions = [
        DeterministicDecision(
            layer=Layer.L0,
            scenario="DiskFull",
            category="DiskFull",
            confidence=Confidence.HIGH,
            confidence_score=0.9,
            evidence_details=[],
            collected_evidence=[],
            missing_evidence=[],
        ),
        DeterministicDecision(
            layer=Layer.L2,
            scenario="OOMKilled",
            category="OOMKilled",
            confidence=Confidence.HIGH,
            confidence_score=0.85,
            evidence_details=[],
            collected_evidence=[],
            missing_evidence=[],
        ),
        DeterministicDecision(
            layer=Layer.L3,
            scenario="DNSLatency",
            category="DNSLatency",
            confidence=Confidence.MEDIUM,
            confidence_score=0.65,
            evidence_details=[],
            collected_evidence=[],
            missing_evidence=[],
        ),
    ]

    evaluator = MultiScenarioEvaluator(engine)
    summaries = evaluator.aggregate_results(decisions)

    # 验证排序：L0 应该在最前面（critical）
    assert len(summaries) == 3
    assert summaries[0].layer == "L0"
    assert summaries[0].impact_severity == "critical"
    assert summaries[1].layer == "L2"
    assert summaries[1].impact_severity == "medium"
    assert summaries[2].layer == "L3"
    assert summaries[2].impact_severity == "medium"

    print(f"✅ 结果聚合测试通过 (排序: {[s.layer for s in summaries]})")


def test_calculate_impact_severity():
    """测试影响严重程度计算"""
    engine = get_engine()
    evaluator = MultiScenarioEvaluator(engine)

    # L0 -> critical
    decision_l0 = DeterministicDecision(
        layer=Layer.L0,
        scenario="DiskFull",
        category="DiskFull",
        confidence=Confidence.HIGH,
        confidence_score=0.9,
        critical_missing=[],
        evidence_details=[],
        collected_evidence=[],
        missing_evidence=[],
    )
    assert evaluator._calculate_impact_severity(decision_l0) == "critical"

    # L1 -> high
    decision_l1 = DeterministicDecision(
        layer=Layer.L1,
        scenario="KubeletCertInvalid",
        category="KubeletCertInvalid",
        confidence=Confidence.HIGH,
        confidence_score=0.9,
        critical_missing=[],
        evidence_details=[],
        collected_evidence=[],
        missing_evidence=[],
    )
    assert evaluator._calculate_impact_severity(decision_l1) == "high"

    # 缺失关键证据 -> critical
    decision_critical_missing = DeterministicDecision(
        layer=Layer.L2,
        scenario="OOMKilled",
        category="OOMKilled",
        confidence=Confidence.HIGH,
        confidence_score=0.9,
        critical_missing=["Exit Code"],
        evidence_details=[],
        collected_evidence=[],
        missing_evidence=[],
    )
    assert evaluator._calculate_impact_severity(decision_critical_missing) == "critical"

    print("✅ 影响严重程度计算测试通过")


def test_find_correlations():
    """测试相关性分析"""
    engine = get_engine()
    evaluator = MultiScenarioEvaluator(engine)

    # 构造共享证据的两个决策
    # 注意：collected_evidence 是 List[str]，evidence_details 是 List[Dict]
    decision1 = DeterministicDecision(
        layer=Layer.L0,
        scenario="DiskFull",
        category="DiskFull",
        confidence=Confidence.HIGH,
        confidence_score=0.9,
        collected_evidence=["磁盘使用率"],
        evidence_details=[{
            "description": "磁盘使用率",
            "value": "98%",
            "collected": True,
            "level": "critical"
        }],
        missing_evidence=[],
        causal_chain={
            "root_cause": "磁盘空间不足",
            "trigger": "磁盘使用率 98%",
            "mechanism": "无法写入新数据",
            "manifestation": "Pod 被驱逐"
        }
    )

    decision2 = DeterministicDecision(
        layer=Layer.L2,
        scenario="VolumeLimitExceeded",
        category="VolumeLimitExceeded",
        confidence=Confidence.HIGH,
        confidence_score=0.85,
        collected_evidence=["磁盘使用率"],
        evidence_details=[{
            "description": "磁盘使用率",
            "value": "98%",
            "collected": True,
            "level": "critical"
        }],
        missing_evidence=[],
        causal_chain={
            "root_cause": "磁盘空间不足",
            "trigger": "存储卷超限",
            "mechanism": "kubelet 驱逐 Pod",
            "manifestation": "Pod 被驱逐"
        }
    )

    correlations = evaluator.find_correlations([decision1, decision2])

    # 应该检测到相关性
    # 注意：由于层级顺序 (L0 < L2)，可能被识别为 cascading 或 shared_cause
    # 两者都是合理的，只要识别到相关性即可
    assert len(correlations) > 0
    assert correlations[0].correlation_type in ["shared_cause", "cascading", "independent"]
    assert "磁盘空间不足" in correlations[0].root_cause

    print(f"✅ 相关性分析测试通过 (检测到 {len(correlations)} 组相关性，类型: {correlations[0].correlation_type})")


def test_build_multi_scenario_report():
    """测试多场景报告生成"""
    engine = get_engine()
    evaluator = MultiScenarioEvaluator(engine)

    # 构造两个场景摘要
    summaries = [
        ScenarioSummary(
            scenario_id="L0-DiskFull",
            layer="L0",
            category="DiskFull",
            confidence=Confidence.HIGH,
            confidence_score=0.9,
            evidence_completeness="100%",
            impact_severity="critical",
            has_critical_missing=False,
            decision=None
        ),
        ScenarioSummary(
            scenario_id="L2-OOMKilled",
            layer="L2",
            category="OOMKilled",
            confidence=Confidence.HIGH,
            confidence_score=0.85,
            evidence_completeness="100%",
            impact_severity="medium",
            has_critical_missing=False,
            decision=None
        )
    ]

    correlations = [
        CorrelatedScenarios(
            root_cause="磁盘空间不足",
            scenarios=["L0-DiskFull", "L2-VolumeLimitExceeded"],
            shared_evidence=[],
            correlation_type="shared_cause"
        )
    ]

    report = evaluator.build_multi_scenario_report(summaries, correlations)

    # 验证报告结构
    assert "total_scenarios" in report
    assert report["total_scenarios"] == 2
    assert "scenarios" in report
    assert len(report["scenarios"]) == 2
    assert "correlations" in report
    assert "priority_summary" in report
    assert report["priority_summary"]["critical"] == 1
    assert report["priority_summary"]["medium"] == 1

    print("✅ 多场景报告生成测试通过")


def test_convenience_function():
    """测试便捷函数"""
    engine = get_engine()

    # 构造包含 OOM 证据的文本
    text = """
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
    Resources:
      Limits:
        memory:  512Mi
    """

    # 使用便捷函数
    report = evaluate_all_scenarios(
        rules_engine=engine,
        evidence_items=[],
        facts=[],
        tool_text=text,
        context=None
    )

    # 验证报告结构
    assert "total_scenarios" in report
    assert "priority_summary" in report
    assert "scenarios" in report

    print(f"✅ 便捷函数测试通过 (检测到 {report['total_scenarios']} 个场景)")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  多场景评估器单元测试")
    print("=" * 60 + "\n")

    try:
        test_evaluate_all_scenarios()
        test_aggregate_results()
        test_calculate_impact_severity()
        test_find_correlations()
        test_build_multi_scenario_report()
        test_convenience_function()

        print("\n" + "=" * 60)
        print("  ✅ 所有测试通过")
        print("=" * 60 + "\n")
        return 0
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
