# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 45.6m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| pending-insufficient-memory | 1 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 100% | ✅ | 122s |
| pending-insufficient-memory | 2 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 60% | ✅ | 111s |
| pending-insufficient-memory | 3 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 83% | ✅ | 111s |
| pending-insufficient-memory | 4 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/ | - | - | 80% | ✅ | 113s |
| pending-insufficient-memory | 5 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | nodeSelector, pvc | 100% | ✅ | 116s |
| pending-insufficient-memory | 6 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 100% | ✅ | 107s |
| pending-insufficient-memory | 7 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 75% | ✅ | 119s |
| pending-insufficient-memory | 8 | L1 ✅ | ❌ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | nodeSelector, pvc | 100% | ✅ | 132s |
| pending-insufficient-memory | 9 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 67% | ✅ | 109s |
| pending-insufficient-memory | 10 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 86% | ✅ | 112s |
| pending-insufficient-memory | 11 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 75% | ✅ | 106s |
| pending-insufficient-memory | 12 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 75% | ✅ | 105s |
| pending-insufficient-memory | 13 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 80% | ✅ | 110s |
| pending-insufficient-memory | 14 | L1 ✅ | ❌ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | nodeSelector, pvc | 75% | ✅ | 120s |
| pending-insufficient-memory | 15 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 100% | ✅ | 106s |
| pending-insufficient-memory | 16 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 126s |
| pending-insufficient-memory | 17 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 80% | ✅ | 105s |
| pending-insufficient-memory | 18 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 100% | ✅ | 104s |
| pending-insufficient-memory | 19 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 100% | ✅ | 96s |
| pending-insufficient-memory | 20 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 60% | ✅ | 111s |
| pending-insufficient-memory | 21 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 100% | ✅ | 110s |
| pending-insufficient-memory | 22 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 80% | ✅ | 115s |
| pending-insufficient-memory | 23 | L1 ✅ | ❌ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | nodeSelector, pvc | 67% | ✅ | 94s |
| pending-insufficient-memory | 24 | L1 ✅ | ❌ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | nodeSelector, pvc | 67% | ✅ | 104s |
| pending-insufficient-memory | 25 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 80% | ✅ | 118s |
| pending-insufficient-memory | 26 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 100% | ✅ | 144s |
| pending-insufficient-memory | 27 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 100% | ✅ | 151s |
| pending-insufficient-memory | 28 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 100% | ✅ | 129s |
| pending-insufficient-memory | 29 | L1 ✅ | ❌ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | nodeSelector, pvc | 80% | ✅ | 127s |
| pending-insufficient-memory | 30 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 75% | ✅ | 109s |
| pending-insufficient-memory | 31 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 60% | ✅ | 105s |
| pending-insufficient-memory | 32 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 100% | ✅ | 99s |
| pending-insufficient-memory | 33 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 100% | ✅ | 98s |
| pending-insufficient-memory | 34 | L1 ✅ | ❌ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | nodeSelector, pvc | 100% | ✅ | 94s |
| pending-insufficient-memory | 35 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 100% | ✅ | 102s |
| pending-insufficient-memory | 36 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 80% | ✅ | 107s |
| pending-insufficient-memory | 37 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 60% | ✅ | 92s |
| pending-insufficient-memory | 38 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 100% | ✅ | 88s |
| pending-insufficient-memory | 39 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 100% | ✅ | 87s |
| pending-insufficient-memory | 40 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 100% | ✅ | 91s |
| pending-insufficient-memory | 41 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 67% | ✅ | 115s |
| pending-insufficient-memory | 42 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 75% | ✅ | 112s |
| pending-insufficient-memory | 43 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 83% | ✅ | 169s |
| pending-insufficient-memory | 44 | L1 ✅ | ❌ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | nodeSelector, pvc | 83% | ✅ | 99s |
| pending-insufficient-memory | 45 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | nodeSelector, pvc | 100% | ✅ | 98s |
| pending-insufficient-memory | 46 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | nodeSelector, pvc | 50% | ✅ | 77s |
| pending-insufficient-memory | 47 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 100% | ✅ | 100s |
| pending-insufficient-memory | 48 | L1 ✅ | ❌ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | nodeSelector, pvc | 100% | ✅ | 103s |
| pending-insufficient-memory | 49 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi | - | - | 80% | ✅ | 90s |
| pending-insufficient-memory | 50 | L1 ✅ | ✅ | Insufficient, memory, 100000Gi, 0/, nodes are available | - | - | 100% | ✅ | 93s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| pending-insufficient-memory | pending | 68.0% | 100.0% | 85.6% | 1.2m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 1.2m | ✅ |
| 根因准确率 | >= 60% | 68.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 85.6% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/pending/08-pending-insufficient-memory
