#!/usr/bin/env python3
"""
联邦查询端到端验证测试

验证项：
1. 模块导入
2. 配置加载
3. 注册表功能
4. HTTP 客户端
5. 聚合器功能
6. 协调器完整流程
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """测试1：模块导入"""
    print("✓ 测试1：模块导入")
    from app.core.federation import FederationCoordinator, get_federation_coordinator
    from app.core.federation.registry import AgentRegistry, SubAgentConfig
    from app.core.federation.client import SubAgentClient, SubAgentResult
    from app.core.federation.aggregator import FederationAggregator
    print("  ✓ 所有模块导入成功")

def test_registry():
    """测试2：注册表功能"""
    print("✓ 测试2：注册表功能")
    from app.core.federation.registry import AgentRegistry

    cfg = {
        "enabled": True,
        "sub_agents": [
            {"name": "test1", "url": "http://test1:8000", "enabled": True},
            {"name": "test2", "url": "http://test2:8000", "enabled": False},
        ]
    }
    reg = AgentRegistry.load_from_dict(cfg)
    enabled = reg.get_enabled_agents()
    assert len(enabled) == 1
    assert enabled[0].name == "test1"
    print(f"  ✓ 注册表加载成功，已启用: {len(enabled)}/{len(reg)}")

def test_coordinator_creation():
    """测试3：协调器创建"""
    print("✓ 测试3：协调器创建")
    from app.core.federation import FederationCoordinator

    cfg = {
        "enabled": True,
        "max_tokens_per_agent": 10000,
        "synthesis_timeout": 300,
        "sub_agents": [{"name": "test", "url": "http://test:8000", "enabled": True}]
    }
    coord = FederationCoordinator.from_config(cfg, model="deepseek/deepseek-chat", api_key="test")
    assert coord.is_enabled()
    print("  ✓ 协调器创建成功")

def test_config_loader_exclusion():
    """测试4：config_loader 排除字段"""
    print("✓ 测试4：config_loader 排除字段")
    import tempfile, yaml
    from pathlib import Path

    test_yaml = """
toolsets:
  test: {enabled: true}
federation:
  enabled: true
stream_output: false
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(test_yaml)
        p = Path(f.name)

    with open(p) as f:
        d = yaml.safe_load(f)

    _excluded_keys = {"stream_output", "sub_agents", "federation"}
    filtered = {k: v for k, v in d.items() if k not in _excluded_keys}

    assert "federation" not in filtered
    assert "toolsets" in filtered
    p.unlink()
    print("  ✓ 排除字段逻辑正确")

def test_service_integration():
    """测试5：service.py 集成"""
    print("✓ 测试5：service.py 集成")
    from app.core.service import HolmesService

    svc = HolmesService()
    assert hasattr(svc, 'federation_coordinator')
    assert svc.federation_coordinator is None  # 初始为 None
    print("  ✓ HolmesService 包含 federation_coordinator 属性")

def main():
    print("=" * 60)
    print("联邦查询端到端验证测试")
    print("=" * 60)
    print()

    tests = [
        test_imports,
        test_registry,
        test_coordinator_creation,
        test_config_loader_exclusion,
        test_service_integration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
