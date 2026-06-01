# Quickstart: Query Direct Render Validation

## Focused Unit Tests

```bash
pytest tests/unit/workflow/test_query_direct_mode.py tests/unit/workflow/test_fast_paths.py -q
```

Expected:
- Query conclusion with `query_result` does not call conclusion LLM.
- Query direct can build result from JSON text or Prometheus tool events without Pydantic layer_extract.
- Non-query diagnosis conclusion behavior remains covered by existing tests.

## Real Deployment Validation

1. Update `VERSION` to the next requested version.
2. Run the normal build/push/deploy flow used for this project.
3. Wait for `aiops-copilot` rollout to complete.
4. Run:

```bash
curl -N "http://<service>/query?q=查询下我cpu和memory的使用率&format=sse&stream=true"
```

Expected:
- Final answer contains `## 📊 查询结果`.
- Final answer contains a node table with CPU and memory columns.
- Final answer does not contain `报告生成失败：LLM 未返回有效内容`.
- Performance statistics are present at the end of the response.
- Logs show no conclusion LLM call for the query result render path.
