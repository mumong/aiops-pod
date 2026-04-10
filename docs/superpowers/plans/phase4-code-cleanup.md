# Phase 4: 代码精简

## Task 15: executor.py 拆分 reporter.py

**Files:**
- Create: `app/core/workflow/reporter.py`
- Modify: `app/core/workflow/executor.py`

- [ ] **Step 1: 创建 reporter.py**

从 executor.py 提取以下方法：
- `update_metrics_from_state(metrics, state)` — 指标提取
- `extract_runbook_info(state, metrics, runbook_catalog)` — Runbook 识别
- `save_report(conclusion, question, layer)` — 报告保存
- `extract_layer_from_report(text)` — 层级提取

- [ ] **Step 2: executor.py 中调用 reporter 函数**

```python
from app.core.workflow.reporter import (
    update_metrics_from_state,
    extract_runbook_info,
    save_report,
)
```

- [ ] **Step 3: 验证 executor.py < 450 行**
- [ ] **Step 4: Commit**

---

## Task 16: 节点公共逻辑提取

**Files:**
- Modify: `app/core/workflow/nodes/base.py`

- [ ] **Step 1: 提取公共方法到 base.py**

各节点中重复的模式：
- `_try_parse_json(text)` — JSON 解析（layer_classifier 和 rca 都有）
- `_save_thinking(state, new_state, events)` — thinking 事件保存
- `_get_model_config()` — 获取 LLM 模型配置

将这些提取到 WorkflowNode 基类。

- [ ] **Step 2: 各节点删除重复代码**
- [ ] **Step 3: 运行全量测试**
- [ ] **Step 4: Commit**

---

## Task 17: 清理冗余代码

**Files:**
- Multiple files

- [ ] **Step 1: 删除未使用的 import**

```bash
# 用 autoflake 检查
.venv/bin/python -m autoflake --check -r app/
```

- [ ] **Step 2: 删除注释掉的旧代码**
- [ ] **Step 3: 统一日志格式**
- [ ] **Step 4: 最终验证**

```bash
# 语法检查
.venv/bin/python -c "import app.core.service"
# 部署测试
make build push deploy-master
# 功能测试
.venv/bin/python test/e2e/test_accuracy.py -n 3 -c 2 --expect-layer L3
```

- [ ] **Step 5: Commit**

---

## 验收检查清单

- [ ] `aicall` 模块独立可用，单元测试通过
- [ ] 所有 4 个工作流节点使用 `aicall` 调用 LLM
- [ ] `holmesgpt` 从 `requirements.txt` 移除
- [ ] `holmes/` 目录完全删除
- [ ] `service.py` < 250 行
- [ ] `executor.py` < 450 行
- [ ] 诊断报告质量不低于当前水平
- [ ] TodoWrite + fetch_runbook 通过 MCP 工具可用
- [ ] 流式输出格式保持兼容
- [ ] 无 holmes 相关 import 残留
