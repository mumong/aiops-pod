# Contract: Query Direct Workflow

## Input

Endpoint: `/query`

Required runtime behavior:
- Workflow override sets `query_mode=direct`.
- Enabled nodes are layer and conclusion only.
- The query chain is read-only.

## Layer Output Contract

For successful query data:

```json
{
  "layer": "QUERY",
  "layers": ["QUERY"],
  "confidence": 0.8,
  "reasoning": "已基于真实查询结果生成 QUERY 结构化结果。",
  "query_result": {
    "query_target": "查询 CPU 和内存",
    "collection_summary": "计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%",
    "columns": [
      {"key": "node", "label": "节点"},
      {"key": "cpu_usage_percent", "label": "CPU 使用率 (%)"},
      {"key": "memory_usage_percent", "label": "内存使用率 (%)"}
    ],
    "rows": [
      {"node": "10.2.0.49:9100", "cpu_usage_percent": 4.35, "memory_usage_percent": 9.95}
    ],
    "notes": [],
    "missing": [],
    "sources": [
      {"tool": "execute_prometheus_instant_query", "query": "real promql"}
    ]
  }
}
```

## Conclusion Output Contract

When `query_result` exists, conclusion returns Markdown rendered locally:

```markdown
## 📊 查询结果

- **查询目标**: 查询 CPU 和内存
- **模式**: QUERY 结构化回复
- **采集情况**: 计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%

## 📈 数据摘要

| 节点 | CPU 使用率 (%) | 内存使用率 (%) |
|------|------|------|
| 10.2.0.49:9100 | 4.35 | 9.95 |
```

## Non-Query Contract

For `/ask` or non-QUERY layers, conclusion remains on the existing diagnosis path and may use the existing diagnosis LLM/structured behavior.
