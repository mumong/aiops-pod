# Pod RootCause Suite 汇总

> 该汇总已排除环境污染后的结果。原始数据未删除，已移动到 `excluded_environment_polluted/`。

## 当前纳入统计范围

- 纳入 Case: 9
- 纳入成功运行: 450
- 排除 Case: 13
- 排除起点: `imagepull/10-imagepull-invalid-registry`。
- 排除原因: 从该阶段开始，诊断过程中出现非 `aiops-e2e` 的临时调试 Pod/网络测试 Pod 污染，例如 `node-debugger-*`、`dns-test*`、`registry-*`、`connectivity-*`，全局扫描不再只反映当前 case。

## 总平均

> 人工校正: `07-pending-insufficient-cpu` 根因准确率由 34.0% 修正为 78.0%（39/50）。原因是自动评分将“已排除 nodeSelector/PVC”等否定上下文误判为冲突，并漏判 `100k/100 核/100,000m` 等语义等价表达。
> 补充人工校正: `06-pending-nodeselector-mismatch` 78.0% -> 100.0%，`08-pending-insufficient-memory` 68.0% -> 80.0%，`09-pending-missing-pvc` 84.0% -> 100.0%。主要修正否定上下文冲突误伤和语义等价表达漏判；`08` 同时扣除了两个自动 false positive。


| Scope          | 完成 Case | 成功运行 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
| -------------- | ------- | ---- | ----- | ----------- | ----- | ------- |
| INCLUDED_CLEAN | 9       | 450  | 94.7% | 99.6%       | 86.4% | 1.2m    |


## Group 平均


| Group       | 完成 Case | 成功运行 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
| ----------- | ------- | ---- | ----- | ----------- | ----- | ------- |
| pending     | 4       | 200  | 89.5% | 99.5%       | 84.0% | 1.3m    |
| volumemount | 5       | 250  | 98.8% | 99.6%       | 88.3% | 1.1m    |


## Case 明细


| Case                                  | Group       | 状态        | 成功运行 | 根因准确率  | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
| ------------------------------------- | ----------- | --------- | ---- | ------ | ----------- | ----- | ------- |
| 01-volume-mount-missing-configmap     | volumemount | completed | 50   | 100.0% | 100.0%      | 90.5% | 1.0m    |
| 02-volume-mount-missing-secret        | volumemount | completed | 50   | 98.0%  | 100.0%      | 90.3% | 1.0m    |
| 03-volume-mount-configmap-missing-key | volumemount | completed | 50   | 98.0%  | 100.0%      | 97.3% | 1.0m    |
| 04-volume-mount-missing-pvc           | volumemount | completed | 50   | 100.0% | 100.0%      | 69.1% | 1.0m    |
| 05-volume-mount-hostpath-missing      | volumemount | completed | 50   | 98.0%  | 98.0%       | 94.4% | 1.6m    |
| 06-pending-nodeselector-mismatch      | pending     | completed | 50   | 100.0% | 100.0%      | 95.0% | 1.1m    |
| 07-pending-insufficient-cpu           | pending     | completed | 50   | 78.0%  | 98.0%       | 87.1% | 2.0m    |
| 08-pending-insufficient-memory        | pending     | completed | 50   | 80.0%  | 100.0%      | 85.6% | 1.2m    |
| 09-pending-missing-pvc                | pending     | completed | 50   | 100.0% | 100.0%      | 68.2% | 1.1m    |


## 已排除 Case


| Case                                     | Group       | 状态                   | 原成功运行 | 原根因准确率 | 排除原因                                             |
| ---------------------------------------- | ----------- | -------------------- | ----- | ------ | ------------------------------------------------ |
| 10-imagepull-invalid-registry            | imagepull   | completed            | 50    | 96.0%  | 环境污染后产生，移出最终统计                                   |
| 11-imagepull-image-not-found             | imagepull   | completed            | 50    | 30.0%  | 环境污染后产生，移出最终统计                                   |
| 12-imagepull-missing-pull-secret         | imagepull   | completed            | 50    | 38.0%  | 环境污染后产生，移出最终统计                                   |
| 13-crashloop-exit-code-nonzero           | crashloop   | completed            | 50    | 58.0%  | 环境污染后产生，移出最终统计                                   |
| 14-crashloop-command-not-found           | crashloop   | completed            | 50    | 78.0%  | 环境污染后产生，移出最终统计                                   |
| 15-crashloop-config-file-missing         | crashloop   | completed            | 50    | 80.0%  | 环境污染后产生，移出最终统计                                   |
| 16-configerror-env-missing               | configerror | completed            | 50    | 46.0%  | 环境污染后产生，移出最终统计                                   |
| 17-configerror-configmap-key-missing-env | configerror | completed            | 50    | 68.0%  | 环境污染后产生，移出最终统计                                   |
| 18-configerror-secret-key-missing-env    | configerror | completed            | 50    | 70.0%  | 环境污染后产生，移出最终统计                                   |
| 19-oomkilled-memory-limit-too-low        | oomkilled   | completed            | 50    | 0.0%   | 环境污染后产生，移出最终统计                                   |
| 20-notready-readiness-probe-failed       | notready    | completed            | 50    | 6.0%   | 环境污染后产生，移出最终统计                                   |
| 21-notready-liveness-probe-failed        | notready    | completed            | 50    | 20.0%  | 环境污染后产生，移出最终统计                                   |
| 22-terminating-finalizer-stuck           | terminating | interrupted_no_stats | 0     | N/A    | 环境污染后产生且测试中途停止，无 stats.json；已发现 response 文件 18 个 |


