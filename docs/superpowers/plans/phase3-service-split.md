# Phase 3: service.py 拆分 + holmes/ 清理

## Task 11: 创建 config 模块

**Files:**
- Create: `app/core/config/__init__.py`
- Create: `app/core/config/settings.py`
- Create: `app/core/config/loader.py`

- [ ] **Step 1: 创建 settings.py（配置数据类）**

```python
# app/core/config/settings.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class AppConfig:
    """应用配置（从 YAML + 环境变量加载）"""
    # LLM
    llm_model: str = "deepseek/deepseek-chat"
    llm_api_key: str = ""
    llm_api_base: str = ""
    # 工作流
    workflow: Dict = field(default_factory=dict)
    # MCP
    mcp_servers: Dict = field(default_factory=dict)
    # 内置工具集
    toolsets: Dict = field(default_factory=dict)
    # 指标
    metrics: Dict = field(default_factory=dict)
    # 联邦
    federation: Dict = field(default_factory=dict)
    # Runbook 路径
    runbook_path: str = "knowledge_base/runbooks"
```

- [ ] **Step 2: 创建 loader.py**

从现有 `holmes/config_loader.py` 提取核心逻辑：
- YAML 文件加载
- 环境变量覆盖（LLM_API_KEY, LLM_MODEL, LLM_API_BASE）
- 不再依赖 `holmes.config.Config`

- [ ] **Step 3: 创建 __init__.py**
- [ ] **Step 4: 写测试**
- [ ] **Step 5: Commit**

---

## Task 12: 创建 runbook 模块

**Files:**
- Create: `app/core/runbook/__init__.py`
- Create: `app/core/runbook/catalog.py`
- Move: `app/core/runbook.py` → `app/core/runbook/manager.py`

- [ ] **Step 1: 创建 catalog.py（替代 holmes.plugins.runbooks.RunbookCatalog）**

```python
# app/core/runbook/catalog.py
"""Runbook 目录管理（替代 holmes.plugins.runbooks.RunbookCatalog）"""
import json
import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RunbookEntry:
    id: str
    description: str
    link: str

class RunbookCatalog:
    """Runbook 目录"""
    def __init__(self, catalog: List[RunbookEntry] = None):
        self.catalog = catalog or []

    @classmethod
    def from_json(cls, path: str) -> "RunbookCatalog":
        if not os.path.isfile(path):
            return cls()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        entries = [RunbookEntry(**e) for e in data]
        return cls(catalog=entries)

    def to_prompt_text(self) -> str:
        """生成注入 system prompt 的 catalog 文本"""
        if not self.catalog:
            return ""
        lines = ["# Available Runbooks\n"]
        for e in self.catalog:
            lines.append(f"- **{e.id}** ({e.link}): {e.description}")
        lines.append("\nIf a runbook matches the issue, fetch it with fetch_runbook tool.")
        return "\n".join(lines)
```

- [ ] **Step 2: 迁移 runbook.py → runbook/manager.py**
- [ ] **Step 3: 更新所有 import 引用**
- [ ] **Step 4: Commit**

---

## Task 13: 精简 service.py

**Files:**
- Modify: `app/core/service.py`

- [ ] **Step 1: 替换 holmes 导入**

删除：
```python
from holmes.config import Config
from holmes.core.prompt import build_initial_ask_messages
from holmes.plugins.runbooks import RunbookCatalog
```

替换为：
```python
from app.core.aicall import AICall
from app.core.config import AppConfig, ConfigLoader
from app.core.runbook import RunbookCatalog, RunbookManager
```

- [ ] **Step 2: 删除 _call_with_stream_limited() 方法**（已被 AICall.call() 替代）
- [ ] **Step 3: 删除 holmes/ 相关的初始化代码**
- [ ] **Step 4: 验证 service.py < 250 行**
- [ ] **Step 5: Commit**

---

## Task 14: 删除 holmes/ 目录

**Files:**
- Delete: `app/core/holmes/` (entire directory)
- Modify: `requirements.txt` (remove holmesgpt)

- [ ] **Step 1: 确认无残留引用**

```bash
grep -r "from.*holmes" app/ --include="*.py" | grep -v "__pycache__"
grep -r "import holmes" app/ --include="*.py" | grep -v "__pycache__"
```

- [ ] **Step 2: 删除 holmes/ 目录**
```bash
rm -rf app/core/holmes/
```

- [ ] **Step 3: 从 requirements.txt 移除 holmesgpt**
- [ ] **Step 4: 全量测试**
- [ ] **Step 5: Commit**
