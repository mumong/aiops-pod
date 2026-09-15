# 历史 Pod 异常类型测试

本目录按 `pod_abnormal_type` 验证异常类型，保留用于旧结果回放和专项调试。当前正式入口为 [AIOps 质量测试](../aiops_quality_e2e/README.md)，后者支持具体根因、变体和多对象测试。

## 单次使用

所有命令从仓库根目录执行，仅限专用测试集群：

```bash
kubectl config current-context
kubectl apply -f test/e2e/manifests/00-namespace.yaml
kubectl apply -f test/e2e/manifests/pod-imagepull-failed.yaml
kubectl -n aiops-e2e get pod imagepull-fail-victim
.venv/bin/python test/pod_abnormal_e2e/run_pod_abnormal_cases.py --scenario imagepullbackoff -n 1 -c 1 --url http://10.2.0.48:30800
```

手动模式不会替你确认具体故障已成立；应核对当前 Pod 状态和 Events 后再请求诊断。

串行部署及测试入口：

```bash
.venv/bin/python test/pod_abnormal_e2e/run_pod_abnormal_suite.py --scenarios-file test/pod_abnormal_e2e/test.txt -n 1 -c 1 --question "我的集群有什么问题" --url http://10.2.0.48:30800
```

`cases.yaml` 定义场景、别名、预期类型、Runbook 和关键词；`test.txt` 选择要运行的场景。suite 会清理已知 E2E 资源、部署相应清单、执行触发动作、运行诊断并清理。不要在测试 namespace 存放业务数据。

## 安全与评分边界

- `unknown` 默认排除：部署候选 Pod 不会自动制造节点失联；停止 kubelet 或隔离网络需要独立人工授权。
- Terminating 需 delete 触发，实验后需释放测试 finalizer；节点压力类场景可能影响同节点负载。
- 旧评分依赖异常类型、关键词、报告计数和 Runbook 文本，不能替代具体根因核验；不能与当前四项指标直接混算。
- 输出为 `testreports/pod_abnormal_*/` 或 `pod_abnormal_suite_*/`，含 `response_N.md`、`stats.json`、`summary.md`。审计优先查看原报告，不把字符串命中视为语义正确。
