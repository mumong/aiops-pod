# Quickstart: Ask Layer Structured Fallback

## Unit Validation

```bash
pytest -q tests/unit/workflow/test_fast_paths.py tests/unit/workflow/test_query_direct_mode.py
```

## Real Validation

1. Deploy the new image.
2. Confirm the deployed environment:

```bash
kubectl exec -n aiops deploy/aiops-copilot -- printenv | rg 'LLM_API_BASE|LLM_MODEL'
```

3. Confirm LLM endpoint connectivity:

```bash
kubectl exec -n aiops deploy/aiops-copilot -- sh -lc 'nc -vz -w 3 10.2.0.54 4000'
```

4. Run `/ask`:

```bash
curl --no-buffer -H "Accept: text/event-stream" -G "http://10.2.0.48:30800/ask" --data-urlencode "q=我的集群有什么问题？"
```

5. Check backend logs:

```bash
kubectl logs -n aiops deploy/aiops-copilot --since=10m | rg 'LLM 服务不可用|layer_extract|LayerOutput|remediation_approval'
```

Expected result when port 4000 remains closed: `/ask` reports LLM service unavailable clearly, and logs do not show duplicate layer extraction attempts as the root cause.

Expected result when LLM service is healthy: `/ask` reaches a validated layer result, then continues into evidence/RCA/conclusion and remediation review if the final plan is safe and available.
