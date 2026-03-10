#!/usr/bin/env python3
"""
联邦查询 - 并发聚合器

职责：
1. 并发调用所有已启用的子集群
2. Token 估算与单报告压缩
3. 调用 LLM 合成多集群统一报告（流式输出）
4. 保存子集群报告到本地
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import litellm

from app.core.federation.client import SubAgentClient, SubAgentResult
from app.core.federation.registry import AgentRegistry

logger = logging.getLogger(__name__)

# 多集群协调者合成提示词（独立常量，不影响单集群 prompts.py）
FEDERATION_SYNTHESIS_PROMPT = """\
# 角色定义
你是多集群 Kubernetes 运维协调专家。以下是各子集群独立执行诊断后的报告，每份报告都由子集群的 AIOps Agent 生成。

# 核心任务
综合分析所有子集群的报告，输出一份**高度结构化**的多集群统一诊断报告。

# 问题类型判断（必须先判断）

根据用户原始问题，判断分析模式：

**1. 对比分析模式**：用户明确要求对比（如"谁的 CPU 高"、"哪个集群问题多"、"对比各集群"）
- 重点：横向对比各集群的相同指标或问题
- 输出：突出差异和排名

**2. 全局诊断模式**：用户询问整体问题（如"我的集群有什么问题"、"集群状态"、"有哪些异常"）
- 重点：列出所有集群的所有问题
- 输出：按严重程度和集群分组

# 输出模板（必须严格遵守 Markdown 格式）

---

## 📊 多集群诊断概览

| 项目 | 内容 |
|------|------|
| **分析模式** | 对比分析 / 全局诊断 |
| **子集群总数** | X 个（Y 个成功，Z 个失败） |
| **问题总数** | X 个（Critical: Y, High: Z, Medium: W） |
| **数据完整度** | XX%（说明哪些集群数据不足） |

---

## 🌐 各集群状态对比表

| 集群名称 | 主要问题 | 严重程度 | 问题数量 | 数据状态 |
|----------|----------|----------|----------|----------|
| cluster-A | [问题摘要] | 🔴 Critical | 3 | ✅ 完整 |
| cluster-B | [问题摘要] | 🟡 Medium | 1 | ⚠️ 监控缺失 |

**说明**：
- 🔴 Critical：需要立即处理，影响整个集群
- 🟠 High：影响节点级，需要优先处理
- 🟡 Medium：影响工作负载，建议尽快处理
- ⚪ Low：应用层问题，影响范围有限

---

## 🕵️ 跨集群证据汇总

### 关键证据追溯

| 集群 | 证据来源 | 原始数据 | 支持的结论 |
|------|----------|----------|------------|
| cluster-A | kubectl describe node | `CPU 限制 101%` | master 节点超配 |
| cluster-B | Prometheus | `CPU 使用率 25%` | 主控集群正常 |

### 数据不足说明（如有）

| 集群 | 缺失数据 | 影响 | 建议 |
|------|----------|------|------|
| cluster-B | 节点监控指标 | 无法获取 CPU 利用率 | 部署 node-exporter |

---

## 🎯 问题分析

### 共性问题（多个集群都存在）

**问题1：[问题名称]**
- **涉及集群**：cluster-A, cluster-B
- **严重程度**：🔴 Critical
- **根因**：[基于证据的根因分析]
- **置信度**：高 (85%)

### 差异化问题（特定集群独有）

**cluster-A 特有问题：**
1. **[问题名称]**
   - **层级**：L? - [层级名称]
   - **根因**：[基于证据的分析]
   - **置信度**：高/中/低

---

## 📋 跨集群优先级排序

按严重程度和影响范围排序，最需要立即处理的问题：

| 优先级 | 问题 | 涉及集群 | 严重程度 | 影响范围 |
|--------|------|----------|----------|----------|
| 1 | [问题描述] | cluster-A | 🔴 Critical | 整个集群 |
| 2 | [问题描述] | cluster-B, cluster-C | 🟠 High | 多个节点 |

---

## 🛠️ 分集群修复建议

### 集群：cluster-A

**修复步骤：**

**1. [优先] [操作名称]**
```bash
# 具体命令
kubectl xxx
```
*依据*：证据 #1 显示...
*预期结果*：...

**2. [可选] [操作名称]**
```bash
# 具体命令
```

### 集群：cluster-B

**修复步骤：**
...

---

## ⚠️ 注意事项

- 如果某集群数据不足，建议先修复数据收集问题（如部署监控组件），再进行深入分析
- 跨集群问题可能有关联性，建议按优先级顺序修复
- 修复后建议重新执行联邦查询，验证问题是否解决

---

# 严格规则

1. **必须使用上述 Markdown 模板格式**
2. **证据汇总表格必须包含原始数据列**，可追溯到具体集群和命令
3. **置信度必须基于证据充分性**，数据不足时明确说明
4. **修复命令必须可直接复制执行**，包含具体的集群、namespace、资源名称
5. **如有数据不足，必须在"数据不足说明"表格中列出**，不要在结论中混淆"数据不足"和"问题诊断"
6. **保留原始报告中的关键数据**：Pod 名称、错误信息、指标值、节点名称等
7. **对比分析模式**：必须明确给出对比结果（如"cluster-A 的 CPU 使用率最高，为 85%"）
8. **全局诊断模式**：必须列出所有集群的所有问题，不要遗漏
"""

COMPRESS_PROMPT = """\
以下是某 Kubernetes 集群的诊断报告，请压缩为简洁摘要，保留：
- 集群名称/标识
- 主要问题列表（按严重程度排序）
- 根因分析（如有）
- 关键证据（Pod 名称、错误信息、关键指标）
- 修复建议摘要

输出长度控制在 800 字以内，使用中文 Markdown 格式。

原始报告：
"""


def _estimate_tokens(text: str) -> int:
    """粗略估算 token 数（英文约 4 char/token，中文约 2 char/token）"""
    return max(len(text) // 3, 1)


class FederationAggregator:
    """联邦查询并发聚合器"""

    def __init__(
        self,
        registry: AgentRegistry,
        max_tokens_per_agent: int = 12000,
        synthesis_timeout: float = 300.0,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self._registry = registry
        self._max_tokens_per_agent = max_tokens_per_agent
        self._synthesis_timeout = synthesis_timeout
        self._client = SubAgentClient()
        self._model = model
        self._api_key = api_key
        self._api_base = api_base

    async def query_all(self, question: str, max_steps: int, conclusion_max_tokens: int = 8192) -> List[SubAgentResult]:
        """并发查询所有已启用的子集群"""
        agents = self._registry.get_enabled_agents()
        if not agents:
            logger.warning("[FEDERATION] 没有已启用的子集群，跳过联邦查询")
            return []

        logger.info(
            f"[FEDERATION] 开始并发查询 {len(agents)} 个子集群，"
            f"问题: {question[:60]}..."
        )

        tasks = [
            self._client.query(
                agent=agent,
                question=question,
                max_steps=max_steps,
                conclusion_max_tokens=conclusion_max_tokens,
                timeout=self._synthesis_timeout,
            )
            for agent in agents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # 保存子集群报告到本地
        self._save_reports(results)

        return list(results)

    def _save_reports(self, results: List[SubAgentResult]) -> None:
        """保存子集群报告到本地目录"""
        try:
            # 创建 reports 目录
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for result in results:
                if not result.success:
                    continue

                # 文件名格式：{cluster_name}_{timestamp}.md
                filename = f"{result.name}_{timestamp}.md"
                filepath = reports_dir / filename

                # 写入报告
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# 子集群诊断报告 - {result.name}\n\n")
                    f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**集群 URL**: {result.url}\n")
                    f.write(f"**耗时**: {result.elapsed_seconds:.1f} 秒\n\n")
                    f.write("---\n\n")
                    f.write(result.text)

                logger.info(f"[FEDERATION] 已保存 {result.name} 报告到: {filepath}")

        except Exception as exc:
            logger.error(f"[FEDERATION] 保存报告失败: {exc}", exc_info=True)

    def _compress_single(self, result: SubAgentResult) -> str:
        """调用 LLM 将单个子集群报告压缩为关键摘要"""
        before_tokens = _estimate_tokens(result.text)
        logger.info(
            f"[FEDERATION] {result.name} 报告超出阈值"
            f"（约 {before_tokens} tokens），开始压缩..."
        )
        prompt = COMPRESS_PROMPT + result.text
        try:
            _completion_kwargs = dict(
                model=self._model,
                api_key=self._api_key,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                max_tokens=1200,
            )
            if self._api_base:
                _completion_kwargs["base_url"] = self._api_base
            resp = litellm.completion(**_completion_kwargs)
            compressed = resp.choices[0].message.content or result.text
            after_tokens = _estimate_tokens(compressed)
            logger.info(
                f"[FEDERATION] {result.name} 压缩完成: "
                f"{before_tokens} → {after_tokens} tokens"
            )
            return compressed
        except Exception as exc:
            logger.error(f"[FEDERATION] {result.name} 压缩失败，使用原始文本: {exc}")
            return result.text

    def synthesize(
        self,
        question: str,
        results: List[SubAgentResult],
    ) -> Generator[str, None, None]:
        """
        合成多集群统一报告，以流式文本 yield。

        Args:
            question: 原始用户问题
            results: 各子集群的查询结果列表
        """
        # 过滤成功结果
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if not successful:
            yield "❌ 所有子集群查询均失败，无法生成联邦报告。\n\n"
            if failed:
                yield "**失败详情：**\n"
                for r in failed:
                    yield f"- `{r.name}` ({r.url}): {r.error}\n"
            return

        # 失败集群提示
        if failed:
            yield f"⚠️ 以下 {len(failed)} 个子集群查询失败，已从合成中排除：\n"
            for r in failed:
                yield f"- `{r.name}` ({r.url}): {r.error}\n"
            yield "\n"

        # Token 估算与压缩
        # max_tokens_per_agent=0 表示不设限，但需检测模型上下文限制
        MODEL_CONTEXT_LIMIT = 60000  # DeepSeek 上下文限制约 64K tokens，预留 4K
        contents: List[str] = []
        total_tokens = 0

        for r in successful:
            text = r.text
            token_count = _estimate_tokens(text)

            # 如果设置了单个子集群限制（非0），则按限制压缩
            if self._max_tokens_per_agent > 0 and token_count > self._max_tokens_per_agent:
                text = self._compress_single(r)
                token_count = _estimate_tokens(text)

            contents.append((r.name, r.url, text, token_count))
            total_tokens += token_count

        # 如果总 token 数超过模型上下文限制，强制压缩
        if total_tokens > MODEL_CONTEXT_LIMIT:
            logger.warning(
                f"[FEDERATION] 总 tokens ({total_tokens}) 超过模型限制 ({MODEL_CONTEXT_LIMIT})，"
                f"开始强制压缩..."
            )
            compressed_contents = []
            total_tokens = 0
            for name, url, text, _ in contents:
                # 重新创建 SubAgentResult 用于压缩
                temp_result = SubAgentResult(
                    name=name, url=url, success=True, text=text, error=None, elapsed_seconds=0
                )
                compressed_text = self._compress_single(temp_result)
                compressed_tokens = _estimate_tokens(compressed_text)
                compressed_contents.append((name, url, compressed_text, compressed_tokens))
                total_tokens += compressed_tokens
            contents = compressed_contents

        logger.info(
            f"[FEDERATION] 开始 LLM 合成，总输入 tokens 约: {total_tokens}，"
            f"集群数: {len(contents)}"
        )

        # 构建 synthesis 消息
        sub_reports = "\n\n".join(
            f"---\n## 集群: {name} ({url})\n\n{text}"
            for name, url, text, _ in contents
        )
        user_message = (
            f"用户原始问题：{question}\n\n"
            f"以下是 {len(contents)} 个子集群的诊断报告：\n\n"
            f"{sub_reports}"
        )

        messages = [
            {"role": "system", "content": FEDERATION_SYNTHESIS_PROMPT},
            {"role": "user", "content": user_message},
        ]

        # 流式 LLM 合成
        try:
            _completion_kwargs = dict(
                model=self._model,
                api_key=self._api_key,
                messages=messages,
                stream=True,
            )
            if self._api_base:
                _completion_kwargs["base_url"] = self._api_base
            stream = litellm.completion(**_completion_kwargs)
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as exc:
            logger.error(f"[FEDERATION] LLM 合成失败: {exc}", exc_info=True)
            yield f"\n\n❌ LLM 合成失败: {exc}\n"
            yield "\n**各子集群原始报告（未合成）：**\n\n"
            for name, url, text, _ in contents:
                yield f"---\n### 集群: {name}\n\n{text}\n\n"
