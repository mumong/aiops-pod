# c02-tag · ImagePullFailed

[返回总体报告](../readme.md)

具体故障：已有镜像仓库中的镜像 tag 不存在

场景状态：blocked。

> 故障验收记录：registry_tls_untrusted；归档 `/root/huhu/agent/combine-aiops-mcp/robusta/testreports/aiops_quality_expanded-c0e3e093e80c_20260910_181943/c02-tag/fixture-failure-setup-1789131760046472617.json`。

> 故障验收记录：registry_tls_untrusted；归档 `/root/huhu/agent/combine-aiops-mcp/robusta/testreports/aiops_quality_expanded-c0e3e093e80c_20260910_181943/c02-tag/fixture-failure-setup-1789359055841421234.json`。

期望 Runbook：pod-imagepull-failed

成功运行：0/0；证据完整度有效样本：0/0。

## 四项质量指标

| 指标 | 实际 | 阈值 | 状态 |
|---|---:|---:|---|
| 根因准确率 | N/A | >= 70% | 待复核 |
| Runbook 覆盖率 | N/A | >= 70% | 待复核 |
| 平均 MTTR | N/A | < 15m | 待复核 |
| 证据完整度 | N/A | >= 70% | 待复核 |

## 每次运行

以下是原脚本评分，不等于人工裁决；根因 0% 不自动代表 Agent 实际误诊。

| # | 请求 | 根因准确率 | Runbook 覆盖率 | 证据完整度 | MTTR | 原始报告 / Run ID |
|---|---|---:|---:|---:|---:|---|

## 统计说明

Case 内对成功运行的单次指标求算术平均。证据单次先按各 lane 的完成项/计划项计算，再对每次完整度求平均；N/A 不进入均值。请求失败单列，不作为质量分数。
Runbook 覆盖不等于选用精确率；证据完整度是 Agent Plan 完成率，不是独立的事实充分性核验。
