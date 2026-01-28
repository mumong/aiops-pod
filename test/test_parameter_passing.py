#!/usr/bin/env python3
"""
测试文件：验证工作流节点参数传递

用于调试参数传递问题
"""
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置日志级别为 DEBUG 以查看详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_node_parameter_types():
    """测试节点的参数类型"""

    logger.info("=" * 60)
    logger.info("测试工作流节点参数传递")
    logger.info("=" * 60)

    # 模拟参数
    from holmes.plugins.runbooks import RunbookCatalog

    # 创建模拟对象
    class MockHolmesService:
        def __init__(self):
            self.console = None
            self.ai = None
            self.merged_catalog = None  # 不需要实际的 catalog

    class MockMetrics:
        def __init__(self):
            self.calls = []

        def record_llm_call(self, node_id, duration_ms):
            self.calls.append(("llm", node_id, duration_ms))

        def record_tool_call(self, tool_name, duration_ms, success):
            self.calls.append(("tool", tool_name, duration_ms, success))

    # 导入节点类
    from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
    from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
    from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
    from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode

    # 创建模拟对象
    holmes_service = MockHolmesService()
    metrics = MockMetrics()
    runbook_catalog = None  # 不需要实际的 catalog

    logger.info(f"\n创建的测试对象：")
    logger.info(f"  - holmes_service: type={type(holmes_service).__name__}")
    logger.info(f"  - metrics: type={type(metrics).__name__}")
    logger.info(f"  - runbook_catalog: type={type(runbook_catalog).__name__}")

    # 测试正确的参数顺序
    logger.info(f"\n测试 1: 正确的参数顺序 (holmes_service, metrics, runbook_catalog)")

    try:
        layer_node = LayerClassifierNode(holmes_service, metrics, runbook_catalog)
        logger.info(f"  LayerClassifierNode 创建成功")
        logger.info(f"    - self.holmes_service type: {type(layer_node.holmes_service).__name__}")
        logger.info(f"    - self.metrics type: {type(layer_node.metrics).__name__}")
        logger.info(f"    - self.runbook_catalog type: {type(layer_node.runbook_catalog).__name__}")

        # 验证 metrics 有正确的方法
        if hasattr(layer_node.metrics, 'record_tool_call'):
            logger.info(f"    - self.metrics 有 record_tool_call 方法 ✅")
        else:
            logger.warning(f"    - self.metrics 没有 record_tool_call 方法 ❌")

    except Exception as e:
        logger.error(f"  LayerClassifierNode 创建失败: {e}", exc_info=True)

    try:
        evidence_node = EvidenceCollectorNode(holmes_service, metrics, runbook_catalog)
        logger.info(f"  EvidenceCollectorNode 创建成功")
        logger.info(f"    - self.holmes_service type: {type(evidence_node.holmes_service).__name__}")
        logger.info(f"    - self.metrics type: {type(evidence_node.metrics).__name__}")
        logger.info(f"    - self.runbook_catalog type: {type(evidence_node.runbook_catalog).__name__}")

        # 验证 metrics 有正确的方法
        if hasattr(evidence_node.metrics, 'record_tool_call'):
            logger.info(f"    - self.metrics 有 record_tool_call 方法 ✅")
        else:
            logger.warning(f"    - self.metrics 没有 record_tool_call 方法 ❌")

    except Exception as e:
        logger.error(f"  EvidenceCollectorNode 创建失败: {e}", exc_info=True)

    try:
        rca_node = RootCauseAnalyzerNode(holmes_service, metrics, runbook_catalog)
        logger.info(f"  RootCauseAnalyzerNode 创建成功")
        logger.info(f"    - self.holmes_service type: {type(rca_node.holmes_service).__name__}")
        logger.info(f"    - self.metrics type: {type(rca_node.metrics).__name__}")
        logger.info(f"    - self.runbook_catalog type: {type(rca_node.runbook_catalog).__name__}")

        # 验证 metrics 有正确的方法
        if hasattr(rca_node.metrics, 'record_tool_call'):
            logger.info(f"    - self.metrics 有 record_tool_call 方法 ✅")
        else:
            logger.warning(f"    - self.metrics 没有 record_tool_call 方法 ❌")

    except Exception as e:
        logger.error(f"  RootCauseAnalyzerNode 创建失败: {e}", exc_info=True)

    try:
        conclusion_node = ConclusionFormatterNode(holmes_service, metrics, runbook_catalog)
        logger.info(f"  ConclusionFormatterNode 创建成功")
        logger.info(f"    - self.holmes_service type: {type(conclusion_node.holmes_service).__name__}")
        logger.info(f"    - self.metrics type: {type(conclusion_node.metrics).__name__}")
        logger.info(f"    - self.runbook_catalog type: {type(conclusion_node.runbook_catalog).__name__}")

        # 验证 metrics 有正确的方法
        if hasattr(conclusion_node.metrics, 'record_tool_call'):
            logger.info(f"    - self.metrics 有 record_tool_call 方法 ✅")
        else:
            logger.warning(f"    - self.metrics 没有 record_tool_call 方法 ❌")

    except Exception as e:
        logger.error(f"  ConclusionFormatterNode 创建失败: {e}", exc_info=True)

    # 测试错误的参数顺序
    logger.info(f"\n测试 2: 错误的参数顺序 (holmes_service, runbook_catalog, metrics)")

    try:
        wrong_node = EvidenceCollectorNode(holmes_service, runbook_catalog, metrics)
        logger.info(f"  EvidenceCollectorNode 创建成功（错误参数顺序）")
        logger.info(f"    - self.holmes_service type: {type(wrong_node.holmes_service).__name__}")
        logger.info(f"    - self.metrics type: {type(wrong_node.metrics).__name__}")
        logger.info(f"    - self.runbook_catalog type: {type(wrong_node.runbook_catalog).__name__}")

        # 验证 metrics 有正确的方法
        if hasattr(wrong_node.metrics, 'record_tool_call'):
            logger.info(f"    - self.metrics 有 record_tool_call 方法 ✅")
        else:
            logger.warning(f"    - self.metrics 没有 record_tool_call 方法 ❌")

    except Exception as e:
        logger.error(f"  EvidenceCollectorNode 创建失败: {e}", exc_info=True)

    # 测试 build_diagnosis_workflow
    logger.info(f"\n测试 3: build_diagnosis_workflow 参数传递")

    try:
        from app.core.workflow.graph import build_diagnosis_workflow

        logger.info(f"  调用 build_diagnosis_workflow(holmes_service, metrics, runbook_catalog)")
        workflow = build_diagnosis_workflow(holmes_service, metrics, runbook_catalog)
        logger.info(f"  工作流构建成功")

    except Exception as e:
        logger.error(f"  工作流构建失败: {e}", exc_info=True)

    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    test_node_parameter_types()
