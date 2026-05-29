# Quickstart: Real Validation

## Focused automated validation

```bash
python3 -m unittest test.workflow.test_runbook_remediation_guidance
```

Expected result after implementation: all tests pass.

## Real deployment validation

```bash
printf '11.0.0\n' > VERSION
make delete
make build
make push
make deploy
kubectl get pod -n aiops -l app=aiops-copilot -o wide
curl -sS http://10.2.0.48:30800/health
curl --no-buffer --max-time 900 -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=请诊断 aiops-e2e 命名空间 terminating-stuck Pod 为什么一直 Terminating，并给出安全修复建议" \
  --data-urlencode "stream=false" | tee /tmp/aiops-runbook-remediation-11.0.0.md
```

Expected result:

- Deployment rolls out image `xnet.registry.io:8443/xnet-cloud/aiops-copilot:11.0.0`.
- `/ask` answer uses updated TerminatingStuck guidance.
- Finalizer patch is recommended only when finalizers are confirmed.
- `delete --force` is not presented as the first/default repair.
