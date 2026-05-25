# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 62.7m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| oomkilled-memory-limit-too-low | 1 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制, 40Mi | - | ImagePullBackOff | 100% | ✅ | 181s |
| oomkilled-memory-limit-too-low | 2 | L3 ❌ | ❌ | OOMKilled, Exit Code: 137≈退出码 137, exitCode: 137≈退出码 137, memory limit≈内存 limit | - | ImagePullBackOff | 86% | ✅ | 130s |
| oomkilled-memory-limit-too-low | 3 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 153s |
| oomkilled-memory-limit-too-low | 4 | L3 ❌ | ❌ | - | OOMKilled, Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 100% | ✅ | 117s |
| oomkilled-memory-limit-too-low | 5 | L3 ❌ | ❌ | OOMKilled, memory limit | - | ImagePullBackOff | 83% | ✅ | 109s |
| oomkilled-memory-limit-too-low | 6 | L3 ❌ | ❌ | OOMKilled, memory limit | - | ImagePullBackOff | 100% | ✅ | 153s |
| oomkilled-memory-limit-too-low | 7 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 130s |
| oomkilled-memory-limit-too-low | 8 | L3 ❌ | ❌ | OOMKilled, memory limit | - | ImagePullBackOff | 90% | ✅ | 137s |
| oomkilled-memory-limit-too-low | 9 | L0 ❌ | ❌ | OOMKilled | Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 100% | ✅ | 114s |
| oomkilled-memory-limit-too-low | 10 | L3 ❌ | ❌ | OOMKilled | Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 67% | ✅ | 123s |
| oomkilled-memory-limit-too-low | 11 | L3 ❌ | ❌ | OOMKilled | Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 88% | ✅ | 129s |
| oomkilled-memory-limit-too-low | 12 | L3 ❌ | ❌ | OOMKilled, Exit Code: 137, exitCode: 137≈exit code: 137, memory limit≈内存限制 | - | ImagePullBackOff | 88% | ✅ | 182s |
| oomkilled-memory-limit-too-low | 13 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制, 40Mi | - | ImagePullBackOff | 100% | ✅ | 142s |
| oomkilled-memory-limit-too-low | 14 | L3 ❌ | ❌ | OOMKilled | Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 80% | ✅ | 172s |
| oomkilled-memory-limit-too-low | 15 | L3 ❌ | ❌ | - | OOMKilled, Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 100% | ✅ | 157s |
| oomkilled-memory-limit-too-low | 16 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制, 40Mi | - | ImagePullBackOff | 90% | ✅ | 134s |
| oomkilled-memory-limit-too-low | 17 | L3 ❌ | ❌ | OOMKilled | Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 100% | ✅ | 136s |
| oomkilled-memory-limit-too-low | 18 | L3 ❌ | ❌ | OOMKilled, Exit Code: 137≈退出码为 137, exitCode: 137≈退出码为 137, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 145s |
| oomkilled-memory-limit-too-low | 19 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制, 40Mi | - | ImagePullBackOff | 100% | ✅ | 180s |
| oomkilled-memory-limit-too-low | 20 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 120s |
| oomkilled-memory-limit-too-low | 21 | L3 ❌ | ❌ | OOMKilled | Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 70% | ✅ | 140s |
| oomkilled-memory-limit-too-low | 22 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制, 40Mi | - | ImagePullBackOff | 100% | ✅ | 158s |
| oomkilled-memory-limit-too-low | 23 | L3 ❌ | ❌ | OOMKilled, Exit Code: 137≈exit 137, exitCode: 137≈exit 137, memory limit≈内存限制, 40Mi | - | ImagePullBackOff | 100% | ✅ | 157s |
| oomkilled-memory-limit-too-low | 24 | L3 ❌ | ❌ | OOMKilled, Exit Code: 137, exitCode: 137≈exit code: 137, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 120s |
| oomkilled-memory-limit-too-low | 25 | L3 ❌ | ❌ | OOMKilled | Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 62% | ✅ | 130s |
| oomkilled-memory-limit-too-low | 26 | L3 ❌ | ❌ | OOMKilled, Exit Code: 137, exitCode: 137≈exit code: 137, memory limit≈内存限制 | - | ImagePullBackOff | 90% | ✅ | 147s |
| oomkilled-memory-limit-too-low | 27 | L3 ❌ | ❌ | OOMKilled, memory limit, 40Mi | - | ImagePullBackOff | 100% | ✅ | 126s |
| oomkilled-memory-limit-too-low | 28 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 89% | ✅ | 151s |
| oomkilled-memory-limit-too-low | 29 | L3 ❌ | ❌ | OOMKilled, Exit Code: 137, exitCode: 137≈exit code: 137, memory limit | - | ImagePullBackOff | 100% | ✅ | 212s |
| oomkilled-memory-limit-too-low | 30 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 187s |
| oomkilled-memory-limit-too-low | 31 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 184s |
| oomkilled-memory-limit-too-low | 32 | L3 ❌ | ❌ | OOMKilled, memory limit, 40Mi | - | ImagePullBackOff | 78% | ✅ | 133s |
| oomkilled-memory-limit-too-low | 33 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 162s |
| oomkilled-memory-limit-too-low | 34 | L3 ❌ | ❌ | - | OOMKilled, Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 78% | ✅ | 124s |
| oomkilled-memory-limit-too-low | 35 | L3 ❌ | ❌ | - | OOMKilled, Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 86% | ✅ | 156s |
| oomkilled-memory-limit-too-low | 36 | L3 ❌ | ❌ | OOMKilled, Exit Code: 137, exitCode: 137≈exit code: 137 | - | ImagePullBackOff | 90% | ✅ | 115s |
| oomkilled-memory-limit-too-low | 37 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 138s |
| oomkilled-memory-limit-too-low | 38 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 130s |
| oomkilled-memory-limit-too-low | 39 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 89% | ✅ | 141s |
| oomkilled-memory-limit-too-low | 40 | L3 ❌ | ❌ | OOMKilled | Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 89% | ✅ | 175s |
| oomkilled-memory-limit-too-low | 41 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 90% | ✅ | 148s |
| oomkilled-memory-limit-too-low | 42 | L3 ❌ | ❌ | OOMKilled, memory limit | - | ImagePullBackOff | 100% | ✅ | 137s |
| oomkilled-memory-limit-too-low | 43 | L3 ❌ | ❌ | OOMKilled | Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 100% | ✅ | 117s |
| oomkilled-memory-limit-too-low | 44 | L3 ❌ | ❌ | OOMKilled, memory limit≈内存限制, 40Mi | - | ImagePullBackOff | 100% | ✅ | 162s |
| oomkilled-memory-limit-too-low | 45 | L3 ❌ | ❌ | OOMKilled, memory limit | - | ImagePullBackOff | 100% | ✅ | 134s |
| oomkilled-memory-limit-too-low | 46 | L3 ❌ | ❌ | OOMKilled, Exit Code: 137, exitCode: 137≈exit code: 137, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 290s |
| oomkilled-memory-limit-too-low | 47 | L3 ❌ | ❌ | OOMKilled | Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 100% | ✅ | 244s |
| oomkilled-memory-limit-too-low | 48 | L3 ❌ | ❌ | OOMKilled | Exit Code: 137, exitCode: 137, memory limit, 40Mi | ImagePullBackOff | 100% | ✅ | 141s |
| oomkilled-memory-limit-too-low | 49 | L3 ❌ | ❌ | OOMKilled, Exit Code: 137≈退出码 137, exitCode: 137≈退出码 137, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 172s |
| oomkilled-memory-limit-too-low | 50 | L2 ✅ | ❌ | OOMKilled, memory limit≈内存限制 | - | ImagePullBackOff | 100% | ✅ | 93s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| oomkilled-memory-limit-too-low | oomkilled | 0.0% | 100.0% | 93.6% | 2.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.0m | ✅ |
| 根因准确率 | >= 60% | 0.0% | ❌ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 93.6% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/oomkilled/19-oomkilled-memory-limit-too-low
