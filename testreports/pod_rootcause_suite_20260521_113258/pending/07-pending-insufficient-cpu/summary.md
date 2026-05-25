# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 61.1m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| pending-insufficient-cpu | 1 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 67% | ✅ | 135s |
| pending-insufficient-cpu | 2 | L1 ✅ | ✅ | Insufficient, cpu, 0/ | - | - | 75% | ✅ | 111s |
| pending-insufficient-cpu | 3 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 75% | ✅ | 126s |
| pending-insufficient-cpu | 4 | L1 ✅ | ❌ | Insufficient, cpu, 100000, 0/, nodes are available | - | nodeSelector, pvc | 100% | ✅ | 124s |
| pending-insufficient-cpu | 5 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 131s |
| pending-insufficient-cpu | 6 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 142s |
| pending-insufficient-cpu | 7 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 75% | ✅ | 109s |
| pending-insufficient-cpu | 8 | L1 ✅ | ❌ | Insufficient, cpu, 0/, nodes are available | - | nodeSelector, pvc | 67% | ✅ | 126s |
| pending-insufficient-cpu | 9 | L1 ✅ | ✅ | Insufficient, cpu, 100000 | - | - | 100% | ✅ | 121s |
| pending-insufficient-cpu | 10 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 113s |
| pending-insufficient-cpu | 11 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 75% | ✅ | 121s |
| pending-insufficient-cpu | 12 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 126s |
| pending-insufficient-cpu | 13 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 113s |
| pending-insufficient-cpu | 14 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 251s |
| pending-insufficient-cpu | 15 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 75% | ✅ | 133s |
| pending-insufficient-cpu | 16 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 136s |
| pending-insufficient-cpu | 17 | L1 ✅ | ❌ | Insufficient, cpu, 100000, 0/, nodes are available | - | nodeSelector | 100% | ✅ | 114s |
| pending-insufficient-cpu | 18 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 109s |
| pending-insufficient-cpu | 19 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 126s |
| pending-insufficient-cpu | 20 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 122s |
| pending-insufficient-cpu | 21 | L1 ✅ | ❌ | Insufficient, cpu, 100000, 0/, nodes are available | - | nodeSelector, pvc | 100% | ✅ | 190s |
| pending-insufficient-cpu | 22 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 204s |
| pending-insufficient-cpu | 23 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 80% | ✅ | 126s |
| pending-insufficient-cpu | 24 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 101s |
| pending-insufficient-cpu | 25 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 124s |
| pending-insufficient-cpu | 26 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 117s |
| pending-insufficient-cpu | 27 | L1 ✅ | ❌ | Insufficient, cpu, 100000, 0/, nodes are available | - | nodeSelector | 100% | ✅ | 145s |
| pending-insufficient-cpu | 28 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 80% | ✅ | 119s |
| pending-insufficient-cpu | 29 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 75% | ✅ | 117s |
| pending-insufficient-cpu | 30 | L1 ✅ | ❌ | Insufficient, cpu, 0/, nodes are available | - | nodeSelector, pvc | 100% | ✅ | 122s |
| pending-insufficient-cpu | 31 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 75% | ✅ | 93s |
| pending-insufficient-cpu | 32 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 83% | ✅ | 145s |
| pending-insufficient-cpu | 33 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | nodeSelector | 80% | ✅ | 118s |
| pending-insufficient-cpu | 34 | L1 ✅ | ❌ | - | Insufficient, cpu, 100000, 0/, nodes are available | - | 60% | ✅ | 517s |
| pending-insufficient-cpu | 35 | L1 ✅ | ❌ | Insufficient, cpu, 0/, nodes are available | - | nodeSelector, pvc | 25% | ✅ | 664s |
| pending-insufficient-cpu | 36 | UNKNOWN ❌ | ❌ | - | Insufficient, cpu, 100000, 0/, nodes are available | - | N/A | ❌ | 75s |
| pending-insufficient-cpu | 37 | L1 ✅ | ❌ | Insufficient≈不足, cpu | 100000, 0/, nodes are available | - | 50% | ✅ | 156s |
| pending-insufficient-cpu | 38 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 75% | ✅ | 116s |
| pending-insufficient-cpu | 39 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 80% | ✅ | 112s |
| pending-insufficient-cpu | 40 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 125s |
| pending-insufficient-cpu | 41 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 133s |
| pending-insufficient-cpu | 42 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 125s |
| pending-insufficient-cpu | 43 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 75% | ✅ | 115s |
| pending-insufficient-cpu | 44 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 128s |
| pending-insufficient-cpu | 45 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 60% | ✅ | 126s |
| pending-insufficient-cpu | 46 | L1 ✅ | ❌ | Insufficient, cpu, 100000, 0/, nodes are available | - | nodeSelector, pvc | 80% | ✅ | 107s |
| pending-insufficient-cpu | 47 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 106s |
| pending-insufficient-cpu | 48 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 108s |
| pending-insufficient-cpu | 49 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 129s |
| pending-insufficient-cpu | 50 | L1 ✅ | ✅ | Insufficient, cpu, 100000, 0/, nodes are available | - | - | 80% | ✅ | 125s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| pending-insufficient-cpu | pending | 34.0% | 98.0% | 87.1% | 2.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.0m | ✅ |
| 根因准确率 | >= 60% | 34.0% | ❌ |
| Runbook 覆盖率 | >= 60% | 98.0% | ✅ |
| 证据采集率 | >= 60% | 87.1% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/pending/07-pending-insufficient-cpu
