# Pod RootCause Suite 汇总

- 完成 Case: 5/5
- 失败/未完成 Case: 0
- 总耗时: 862.8m
- Repeat: 50
- Concurrency: 2
- URL: http://10.2.0.48:30800
- Question: 我的集群有什么问题
- 合并来源: pod_rootcause_suite_20260519_103127 + pod_rootcause_suite_20260519_162052

## Case 明细

| Case | Group | 状态 | 成功运行 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 错误 |
|------|-------|------|----------|------------|----------------|------------|-----------|------|
| terminating-finalizer-stuck | terminating | completed | 50 | 74.0% | 100.0% | 97.3% | 5.1m | - |
| terminating-prestop-stuck | terminating | completed | 50 | 66.0% | 100.0% | 95.0% | 5.7m | - |
| terminating-long-grace-period | terminating | completed | 50 | 30.0% | 100.0% | 95.5% | 5.7m | - |
| sandbox-runtimeclass-invalid | sandbox | completed | 50 | 96.0% | 100.0% | 93.3% | 6.6m | - |
| evicted-ephemeral-storage | evicted | completed | 50 | 78.0% | 100.0% | 76.9% | 6.0m | - |

## Group 平均

| Group | 完成 Case | 成功运行 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|-------|-----------|----------|------------|----------------|------------|-----------|
| evicted | 1 | 50 | 78.0% | 100.0% | 76.9% | 6.0m |
| sandbox | 1 | 50 | 96.0% | 100.0% | 93.3% | 6.6m |
| terminating | 3 | 150 | 56.7% | 100.0% | 95.9% | 5.5m |

## 总平均

| Scope | 完成 Case | 成功运行 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|-------|-----------|----------|------------|----------------|------------|-----------|
| TOTAL | 5 | 250 | 68.8% | 100.0% | 91.6% | 5.8m |
