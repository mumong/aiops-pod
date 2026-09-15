# AIOps 异常 Case 质量报告

任务状态：completed_with_errors；评分版本：2026-09-10.1。

场景数：28；已记录运行：1340 / 计划 1400；成功：1340；失败：0。

以下保留脚本原始评分，不据此宣称已完成人工审查。

## 场景汇总

| Case | 异常类型 | 根因准确率 | Runbook 覆盖率 | 平均 MTTR | 证据完整度 | 成功运行 |
|---|---|---:|---:|---:|---:|---:|
| [c01](c01/readme.md) | PendingUnschedulable | 90.0% | 100.0% | 1.6m | 87.3% | 50/50 |
| [c02](c02/readme.md) | ImagePullFailed | 100.0% | 98.0% | 1.9m | 82.4% | 50/50 |
| [c03](c03/readme.md) | VolumeMountFailed | 96.0% | 76.0% | 2.3m | 81.9% | 50/50 |
| [c04](c04/readme.md) | ConfigError | 94.0% | 94.0% | 1.9m | 71.1% | 50/50 |
| [c05](c05/readme.md) | SandboxCreateFailed | 96.0% | 34.0% | 2.5m | 80.8% | 50/50 |
| [c06](c06/readme.md) | CrashLoopBackOffRuntime | 84.0% | 98.0% | 2.3m | 82.1% | 50/50 |
| [c07](c07/readme.md) | ConfigError | 94.0% | 53.0% | 1.7m | 82.9% | 50/50 |
| [c08](c08/readme.md) | OOMKilled | 98.0% | 24.0% | 3.0m | 76.4% | 50/50 |
| [c09](c09/readme.md) | NotReadyProbeFailed | 78.0% | 100.0% | 2.4m | 84.7% | 50/50 |
| [c10](c10/readme.md) | NotReadyProbeFailed | 26.0% | 48.0% | 3.3m | 74.8% | 50/50 |
| [c11](c11/readme.md) | TerminatingStuck | 82.0% | 100.0% | 2.0m | 87.9% | 50/50 |
| [c01-cpu](c01-cpu/readme.md) | PendingUnschedulable | 44.0% | 96.0% | 1.5m | 84.9% | 50/50 |
| [c01-memory](c01-memory/readme.md) | PendingUnschedulable | 90.0% | 96.0% | 1.5m | 84.1% | 50/50 |
| [c01-pvc](c01-pvc/readme.md) | PendingUnschedulable | 100.0% | 98.0% | 1.2m | 86.6% | 50/50 |
| [c03-secret](c03-secret/readme.md) | VolumeMountFailed | 98.0% | 82.0% | 1.4m | 80.4% | 50/50 |
| [c03-key](c03-key/readme.md) | VolumeMountFailed | 100.0% | 82.0% | 1.6m | 82.4% | 50/50 |
| [c03-hostpath](c03-hostpath/readme.md) | VolumeMountFailed | 88.0% | 74.0% | 1.6m | 80.7% | 50/50 |
| [c02-tag](c02-tag/readme.md) | ImagePullFailed | N/A | N/A | N/A | N/A | 0/0 |
| [c06-command](c06-command/readme.md) | CrashLoopBackOffRuntime | 94.0% | 100.0% | 1.3m | 80.9% | 50/50 |
| [c06-file](c06-file/readme.md) | CrashLoopBackOffRuntime | 78.0% | 98.0% | 1.3m | 82.5% | 50/50 |
| [c07-env](c07-env/readme.md) | ConfigError | 64.0% | 53.0% | 1.7m | 83.5% | 50/50 |
| [c04-configmap-key](c04-configmap-key/readme.md) | ConfigError | 93.9% | 100.0% | 1.8m | 78.8% | 50/50 |
| [c11-prestop](c11-prestop/readme.md) | TerminatingStuck | 56.0% | 98.0% | 1.8m | 89.0% | 50/50 |
| [c11-grace](c11-grace/readme.md) | TerminatingStuck | 14.0% | 92.0% | 1.5m | 87.0% | 50/50 |
| [c05-plugin](c05-plugin/readme.md) | SandboxCreateFailed | 76.9% | 33.3% | 1.5m | 81.7% | 40/40 |
| [c08-startup](c08-startup/readme.md) | OOMKilled | 60.0% | 24.0% | 2.8m | 84.2% | 50/50 |
| [c09-port](c09-port/readme.md) | NotReadyProbeFailed | 70.0% | 98.0% | 1.5m | 85.8% | 50/50 |
| [c10-timeout](c10-timeout/readme.md) | NotReadyProbeFailed | 54.0% | 50.0% | 2.2m | 81.7% | 50/50 |

## 总体质量指标

| 指标 | 实际 | 阈值 | 状态 |
|---|---:|---:|---|
| 根因准确率 | 78.5% | >= 70% | 待复核 |
| Runbook 覆盖率 | 77.8% | >= 70% | 待复核 |
| 平均 MTTR | 1.9m | < 15m | 待复核 |
| 证据完整度 | 82.5% | >= 70% | 待复核 |

先在每个 Case 内按运行求算术平均，再对有有效值的 Case 等权平均；不把各 Case 的数量合并作分母。
单项通过不代表每个 Case 都通过，请同时查看上表和各 Case 明细。

> ⚠ 未完成全量有效验收：以下仅为已获得有效样本的统计，不代表整套测试通过。

> ⚠ c02-tag 场景阻塞：registry_tls_untrusted；详见 /root/huhu/agent/combine-aiops-mcp/robusta/testreports/aiops_quality_expanded-c0e3e093e80c_20260910_181943/c02-tag/fixture-failure-setup-1789359055841421234.json。

> ⚠ c02-tag 无成功样本，未进入质量均值。

> ⚠ c04-configmap-key 有 1 次注入失效，原评分仅供审计，已排除质量均值。

> ⚠ c04-configmap-key 证据完整度有效样本 49/50；缺失值未计入均值，不代表采集完成。

> ⚠ c05-plugin 场景阻塞：fixture_gate_unmet；详见 /root/huhu/agent/combine-aiops-mcp/robusta/testreports/aiops_quality_expanded-c0e3e093e80c_20260910_181943/c05-plugin/fixture-failure-run-41-precheck-1789377956114755014.json。

> ⚠ c05-plugin 有 1 次注入失效，原评分仅供审计，已排除质量均值。

> ⚠ c05-plugin 证据完整度有效样本 39/40；缺失值未计入均值，不代表采集完成。
