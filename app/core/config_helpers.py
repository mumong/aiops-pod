#!/usr/bin/env python3
"""
配置相关的辅助函数

提取重复的配置管理逻辑，提高代码复用性
"""

import time
import logging
from typing import Optional, Any
from app.core.constants import DEFAULT_MAX_STEPS, INIT_TIMEOUT_SECONDS


def should_reset_config(api_key: Optional[str], model: Optional[str], max_steps: int) -> bool:
    """
    判断是否需要重置配置

    Args:
        api_key: LLM API Key
        model: 使用的模型
        max_steps: 最大执行步数

    Returns:
        True 表示需要重置配置，False 表示不需要
    """
    return api_key or model or max_steps != DEFAULT_MAX_STEPS


def reset_service_config(service: Any) -> None:
    """
    重置服务配置

    当参数变化时，需要清除缓存的配置和 AI 实例

    Args:
        service: HolmesService 实例
    """
    service.config = None
    service.ai = None


def wait_for_initialization(
    service: Any,
    max_wait: int = INIT_TIMEOUT_SECONDS,
    logger_instance: Optional[logging.Logger] = None
) -> bool:
    """
    等待服务初始化完成

    Args:
        service: HolmesService 实例
        max_wait: 最大等待时间（秒）
        logger_instance: 日志记录器，如果为 None 则使用模块级别 logger

    Returns:
        True 表示初始化成功，False 表示超时或失败
    """
    log = logger_instance or logging.getLogger(__name__)
    waited = 0
    while (service.config is None or service.ai is None) and waited < max_wait:
        if waited == 0:
            log.info("⏳ 等待 HolmesGPT 初始化完成...")
        time.sleep(1)
        waited += 1
    return service.config is not None and service.ai is not None
