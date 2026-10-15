#!/usr/bin/env python3
"""
Runbook Manager
负责加载、合并和管理 Runbooks
"""
import json
import logging
import os
from pathlib import Path
from typing import Optional

from holmes.plugins.runbooks import RunbookCatalog

logger = logging.getLogger(__name__)

from app.core.paths import get_project_root


class RunbookManager:
    """Runbook 管理器"""
    
    def __init__(self, runbook_dir: Optional[Path] = None):
        """
        初始化 Runbook 管理器
        
        Args:
            runbook_dir: 自定义 runbook 目录路径，如果为 None 则使用默认路径
        """
        if runbook_dir is None:
            # 默认路径：项目根目录下的 knowledge_base/runbooks
            # K8s 部署时会被 ConfigMap 覆盖
            project_root = get_project_root()
            self.runbook_dir = project_root / "knowledge_base" / "runbooks"
        else:
            self.runbook_dir = Path(runbook_dir)
        
        # 额外的 runbook 目录（用于扩展）
        self.additional_dirs: list[Path] = []
    
    def load_custom_catalog(self) -> Optional[RunbookCatalog]:
        """
        加载自定义 runbook catalog
        
        Returns:
            RunbookCatalog 对象或 None
        """
        catalog_file = self.runbook_dir / "catalog.json"
        
        if not catalog_file.exists():
            logger.debug("自定义 runbook catalog 不存在: %s", catalog_file)
            return None
        
        try:
            with open(catalog_file, 'r', encoding='utf-8') as f:
                catalog_dict = json.load(f)
            
            # 验证 runbook 文件是否存在
            validated_entries = []
            for entry in catalog_dict.get("catalog", []):
                if "link" in entry:
                    # 检查文件是否存在（支持相对路径和绝对路径）
                    found = False
                    if os.path.isabs(entry["link"]):
                        runbook_path = Path(entry["link"])
                        found = runbook_path.exists()
                    else:
                        # 在主目录和所有额外目录中查找
                        for search_dir in [self.runbook_dir] + self.additional_dirs:
                            runbook_path = search_dir / entry["link"]
                            if runbook_path.exists():
                                found = True
                                break
                    
                    if not found:
                        logger.warning("Runbook 文件不存在，跳过: %s", entry['link'])
                        continue
                
                validated_entries.append(entry)
            
            if not validated_entries:
                logger.warning("没有有效的 runbook 条目在 %s", catalog_file)
                return None
            
            # 创建 catalog（只包含有效的条目）
            catalog_dict["catalog"] = validated_entries
            catalog = RunbookCatalog(**catalog_dict)
            logger.info("加载自定义 runbook catalog: %s 个 runbooks", len(catalog.catalog))
            return catalog
        except Exception as e:
            logger.error("加载自定义 runbook catalog 失败: %s", e, exc_info=True)
            return None
    
    def merge_catalogs(
        self,
        base_catalog: Optional[RunbookCatalog],
        custom_catalog: Optional[RunbookCatalog]
    ) -> Optional[RunbookCatalog]:
        """
        合并内置和自定义 runbook catalogs
        
        Args:
            base_catalog: 内置 runbook catalog
            custom_catalog: 自定义 runbook catalog
        
        Returns:
            合并后的 RunbookCatalog
        """
        if not custom_catalog:
            return base_catalog
        if not base_catalog:
            return custom_catalog
        
        # 合并两个 catalog
        merged_catalog = RunbookCatalog(
            catalog=base_catalog.catalog + custom_catalog.catalog
        )
        logger.info(
            "合并 runbook catalogs: 内置 %s + 自定义 %s = 总计 %s", len(base_catalog.catalog), len(custom_catalog.catalog), len(merged_catalog.catalog)
        )
        return merged_catalog
