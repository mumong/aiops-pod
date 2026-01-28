#!/usr/bin/env python3
"""
测试文件：模拟真实场景的参数传递

模拟 WorkflowExecutor.__init__ 和 build_diagnosis_workflow 的调用
"""
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置日志级别为 DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_workflow_executor_scenario():
    """测试 WorkflowExecutor 的实际场景"""

    logger.info("=" * 60)
    logger.info("测试 WorkflowExecutor 实际场景")
    logger.info("=" * 60)

    # 模拟真实的 HolmesService
    class MockHolmesService:
        def __init__(self):
            self.console = None
            self.ai = None
            self.merged_catalog = None  # 真实场景中这是 RunbookCatalog

    # 模拟真实的 WorkflowMetrics
    class MockWorkflowMetrics:
        def record_llm_call(self, node_id, duration_ms):
            pass

        def record_tool_call(self, tool_name, duration_ms, success):
            pass

    # 模拟真实的 RunbookCatalog
    class MockRunbookCatalog:
        def __init__(self):
            self.catalog = []

    # 创建模拟对象（模拟真实场景）
    logger.info("\n创建模拟对象（模拟真实场景）：")
    holmes_service = MockHolmesService()
    holmes_service.merged_catalog = MockRunbookCatalog()  # 设置 catalog
    metrics = None  # WorkflowExecutor 在实际调用中不传 metrics

    logger.info(f"  - holmes_service: type={type(holmes_service).__name__}")
    logger.info(f"  - holmes_service.merged_catalog: type={type(holmes_service.merged_catalog).__name__}")
    logger.info(f"  - metrics: {metrics}")

    # 模拟 WorkflowExecutor.__init__ 的逻辑
    logger.info("\n模拟 WorkflowExecutor.__init__ 的逻辑：")

    runbook_catalog = (
        holmes_service.merged_catalog
        if holmes_service and holmes_service.merged_catalog
        else None
    )

    logger.info(f"  - runbook_catalog: type={type(runbook_catalog).__name__ if runbook_catalog else 'NoneType'}")

    # 调用 build_diagnosis_workflow
    logger.info("\n调用 build_diagnosis_workflow(holmes_service, metrics, runbook_catalog)")

    from app.core.workflow.graph import build_diagnosis_workflow

    workflow = build_diagnosis_workflow(holmes_service, metrics, runbook_catalog)
    logger.info("  ✅ 工作流构建成功")

    # 测试错误场景：参数顺序错误
    logger.info("\n" + "=" * 60)
    logger.info("测试错误场景：参数顺序错误")
    logger.info("=" * 60)

    logger.info("\n模拟错误的参数传递：(holmes_service, runbook_catalog, metrics)")

    # 这会导致：self.metrics = runbook_catalog (MockRunbookCatalog)
    logger.info("  这会导致 self.metrics 被设置为 RunbookCatalog 对象！")

    try:
        from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
        wrong_node = EvidenceCollectorNode(holmes_service, runbook_catalog, None)

        logger.info(f"\n创建节点后的属性：")
        logger.info(f"  - self.holmes_service type: {type(wrong_node.holmes_service).__name__}")
        logger.info(f"  - self.metrics type: {type(wrong_node.metrics).__name__ if wrong_node.metrics else 'NoneType'}")
        logger.info(f"  - self.runbook_catalog type: {type(wrong_node.runbook_catalog).__name__ if wrong_node.runbook_catalog else 'NoneType'}")

        if wrong_node.metrics:
            if hasattr(wrong_node.metrics, 'record_tool_call'):
                logger.info(f"  - self.metrics 有 record_tool_call 方法 ✅")
            else:
                logger.warning(f"  - self.metrics 没有 record_tool_call 方法 ❌")
                logger.warning(f"  - 这就是错误 '{type(wrong_node.metrics).__name__}' object has no attribute 'record_tool_call' 的根源！")

    except Exception as e:
        logger.error(f"节点创建失败: {e}", exc_info=True)

    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    test_workflow_executor_scenario()
