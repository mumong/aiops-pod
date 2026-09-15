# 历史 E2E 故障注入工具

此目录保留旧版故障清单和 L0–L4 验收工具，供历史回放与专项调试使用，**不是当前质量基线**。当前测试入口见 [AIOps 质量测试](../aiops_quality_e2e/README.md)，可复现 Case 见[异常案例库](../pod-anomaly-cases/README.md)。

## 使用与边界

从仓库根目录执行，先确认 kubectl 指向专用测试集群：

```bash
kubectl config current-context
bash test/e2e/run_all.sh
bash test/e2e/validate.sh
AIOPS_ENDPOINT=http://10.2.0.48:30800 bash test/e2e/test_scenarios.sh
```

上述部署会创建真实故障资源；不要在生产集群运行。NodeLost/Unknown 需要人工节点操作，不能仅靠 manifest 复现。Terminating 使用 finalizer，需要触发删除并在实验后释放；应按脚本及清单核对精确对象，不对业务 namespace 批量清理。

具体资源位于 `manifests/`。例如 `pod-config-error.yaml` 对应 Runbook `pod-config-error.md`。不存在 PVC 可能在调度阶段失败，不能仅因清单名含 volume 就认定为 FailedMount；不存在 RuntimeClass 也可能被准入直接拒绝。

## 历史评分

`test_accuracy.py` 调用 `/ask`，按旧报告格式和正则提取层级、Runbook、证据比例及耗时。它没有当前质量脚本的完整原因门槛、对象归属评分和续跑机制，不宜与新基线直接合并。

```bash
.venv/bin/python test/e2e/test_accuracy.py --scenario pod-imagepull-failed -n 1 -c 1
```

异常类型专项工具见 [Pod Abnormal](../pod_abnormal_e2e/README.md)，历史精确根因工具见 [Pod RootCause](../pod_rootcause_e2e/README.md)。旧代码和单元测试保留，历史成绩应读取对应报告目录，不再复制到本使用文档。
