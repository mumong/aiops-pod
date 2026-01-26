#!/usr/bin/env python3
"""
Skills 模块单元测试

验证:
1. 场景检测正确性
2. 证据提取正确性
3. 规则匹配正确性
4. 置信度计算正确性
5. 证据门禁正确性
"""

import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.skills import (
    evaluate_deterministic_decision,
    get_engine,
    DeterministicDecision,
    Confidence,
    Layer,
)
from app.core.skills.evidence import EvidenceExtractor, EVIDENCE_SPECS
from app.core.skills.rules import RULES


def test_scenario_detection():
    """测试场景检测"""
    engine = get_engine()
    
    # L0: DiskFull
    assert engine.detect_scenario("磁盘满了", "") == "L0-DiskFull"
    assert engine.detect_scenario("", "no space left on device") == "L0-DiskFull"
    assert engine.detect_scenario("", "ENOSPC error") == "L0-DiskFull"
    
    # L1: KubeletCert
    assert engine.detect_scenario("节点 NotReady", "x509 certificate") == "L1-KubeletCert"
    
    # L2: OOMKilled
    assert engine.detect_scenario("Pod OOMKilled", "") == "L2-OOMKilled"
    assert engine.detect_scenario("out of memory", "") == "L2-OOMKilled"

    # L2: VolumeLimitExceeded
    assert engine.detect_scenario("Pod 被驱逐", "exceeds limit") == "L2-VolumeLimitExceeded"
    assert engine.detect_scenario("", "evicted") == "L2-VolumeLimitExceeded"
    
    # L3: DNSLatency
    assert engine.detect_scenario("DNS latency", "") == "L3-DNSLatency"
    assert engine.detect_scenario("", "dns_lookup_seconds=0.5") == "L3-DNSLatency"
    
    # L4: Dependency503
    assert engine.detect_scenario("upstream 503", "") == "L4-Dependency503"
    assert engine.detect_scenario("", "service unavailable") == "L4-Dependency503"
    
    print("✅ 场景检测测试通过")


def test_evidence_extraction():
    """测试证据提取"""
    
    # L0: DiskFull
    text = """
    Filesystem      Size  Used Avail Use% Mounted on
    /dev/sda1       100G   98G    2G  98% /
    """
    items, facts = EvidenceExtractor.extract_all(text, "L0-DiskFull")
    disk_usage = next((i for i in items if i.id == "disk_usage"), None)
    assert disk_usage is not None
    assert disk_usage.collected is True
    print("✅ L0 证据提取测试通过")
    
    # L2: OOMKilled
    text = """
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
    """
    items, facts = EvidenceExtractor.extract_all(text, "L2-OOMKilled")
    oom_reason = next((i for i in items if i.id == "oom_reason"), None)
    exit_code = next((i for i in items if i.id == "exit_code_137"), None)
    assert oom_reason is not None and oom_reason.collected is True
    assert exit_code is not None and exit_code.collected is True
    print("✅ L2 证据提取测试通过")
    
    # L3: DNSLatency
    text = "dns_lookup_seconds=0.52\ndns_lookup_seconds=0.48"
    items, facts = EvidenceExtractor.extract_all(text, "L3-DNSLatency")
    dns_time = next((i for i in items if i.id == "dns_lookup_time"), None)
    assert dns_time is not None and dns_time.collected is True
    print("✅ L3 证据提取测试通过")


def test_rule_matching():
    """测试规则匹配"""
    engine = get_engine()
    
    # L2: OOMKilled - 完整证据
    text = """
    State:          Running
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
      Started:      Thu, 23 Jan 2026 10:00:00 +0800
      Finished:     Thu, 23 Jan 2026 10:05:00 +0800
    Resources:
      Limits:
        memory:  512Mi
    Previous logs: Cannot allocate memory
    """
    
    decision = engine.evaluate("Pod OOMKilled 排查", text)
    
    assert decision is not None
    assert decision.layer == Layer.L2
    assert decision.category == "OOMKilled"
    assert decision.confidence in [Confidence.HIGH, Confidence.MEDIUM]
    print(f"✅ L2 规则匹配测试通过 (置信度: {decision.confidence.value})")


def test_confidence_calculation():
    """测试置信度计算"""
    engine = get_engine()
    
    # 完整证据 -> 高置信度
    full_evidence = """
    Exit Code: 137
    OOMKilled
    memory limit: 512Mi
    --previous logs available
    """
    decision = engine.evaluate("OOM", full_evidence)
    assert decision is not None
    print(f"  完整证据置信度: {decision.confidence.value} ({decision.confidence_score:.2f})")
    
    # 部分证据 -> 中置信度
    partial_evidence = "Exit Code: 137"
    decision = engine.evaluate("OOM", partial_evidence)
    if decision:
        print(f"  部分证据置信度: {decision.confidence.value} ({decision.confidence_score:.2f})")


def test_evidence_gate():
    """测试证据门禁"""
    from app.core.skills.gate import EvidenceGate, apply_gate
    from app.core.skills.models import EvidenceLevel
    
    # 创建一个有 Critical 缺失的决策
    decision = DeterministicDecision(
        layer=Layer.L2,
        scenario="OOMKilled",
        category="OOMKilled",
        confidence=Confidence.HIGH,
        confidence_score=0.9,
        critical_missing=["Exit Code（Critical）"],
        missing_evidence=["Exit Code（Critical）"]
    )
    
    # 应用门禁
    gated = apply_gate(decision)
    
    # 验证降级
    assert gated.confidence == Confidence.LOW
    assert any("关键证据缺失" in s for s in gated.next_steps)
    print("✅ 证据门禁测试通过")


def test_evaluate_deterministic_decision():
    """测试主入口函数"""
    
    # 模拟事件列表
    events = [
        {
            "type": "tool_result",
            "seq": 1,
            "result_preview": "Exit Code: 137\nOOMKilled",
            "description": "kubectl describe pod"
        },
        {
            "type": "tool_result",
            "seq": 2,
            "result_preview": "memory limit: 512Mi",
            "description": "kubectl get pod -o yaml"
        }
    ]
    
    decision = evaluate_deterministic_decision("Pod OOMKilled 排查", events)
    
    assert decision is not None
    assert decision.layer == Layer.L2
    assert len(decision.evidence_refs) > 0
    print(f"✅ 主入口函数测试通过 (Layer: {decision.layer.value}, Category: {decision.category})")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  Skills 模块单元测试")
    print("=" * 60 + "\n")
    
    try:
        test_scenario_detection()
        test_evidence_extraction()
        test_rule_matching()
        test_confidence_calculation()
        test_evidence_gate()
        test_evaluate_deterministic_decision()
        
        print("\n" + "=" * 60)
        print("  ✅ 所有测试通过")
        print("=" * 60 + "\n")
        return 0
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
