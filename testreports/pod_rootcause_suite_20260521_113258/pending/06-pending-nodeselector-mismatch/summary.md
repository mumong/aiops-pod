# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 39.8m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| pending-nodeselector-mismatch | 1 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 69s |
| pending-nodeselector-mismatch | 2 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 73s |
| pending-nodeselector-mismatch | 3 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 60% | ✅ | 73s |
| pending-nodeselector-mismatch | 4 | L1 ✅ | ❌ | didn't match, nonexistent-node-label | nodeSelector | - | 100% | ✅ | 82s |
| pending-nodeselector-mismatch | 5 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 81s |
| pending-nodeselector-mismatch | 6 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 75% | ✅ | 90s |
| pending-nodeselector-mismatch | 7 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label, node selector≈nodeselector | - | - | 75% | ✅ | 98s |
| pending-nodeselector-mismatch | 8 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 94s |
| pending-nodeselector-mismatch | 9 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 75% | ✅ | 83s |
| pending-nodeselector-mismatch | 10 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 75% | ✅ | 102s |
| pending-nodeselector-mismatch | 11 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 75% | ✅ | 95s |
| pending-nodeselector-mismatch | 12 | L1 ✅ | ❌ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | pvc | 100% | ✅ | 90s |
| pending-nodeselector-mismatch | 13 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 75% | ✅ | 83s |
| pending-nodeselector-mismatch | 14 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 93s |
| pending-nodeselector-mismatch | 15 | L1 ✅ | ❌ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | Insufficient cpu, pvc | 100% | ✅ | 82s |
| pending-nodeselector-mismatch | 16 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 97s |
| pending-nodeselector-mismatch | 17 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 81s |
| pending-nodeselector-mismatch | 18 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 81s |
| pending-nodeselector-mismatch | 19 | L1 ✅ | ❌ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | pvc | 100% | ✅ | 91s |
| pending-nodeselector-mismatch | 20 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 92s |
| pending-nodeselector-mismatch | 21 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 94s |
| pending-nodeselector-mismatch | 22 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 97s |
| pending-nodeselector-mismatch | 23 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 91s |
| pending-nodeselector-mismatch | 24 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 101s |
| pending-nodeselector-mismatch | 25 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 95s |
| pending-nodeselector-mismatch | 26 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 98s |
| pending-nodeselector-mismatch | 27 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 101s |
| pending-nodeselector-mismatch | 28 | L1 ✅ | ❌ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | pvc | 100% | ✅ | 110s |
| pending-nodeselector-mismatch | 29 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 98s |
| pending-nodeselector-mismatch | 30 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 86s |
| pending-nodeselector-mismatch | 31 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 90s |
| pending-nodeselector-mismatch | 32 | L1 ✅ | ❌ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | pvc | 100% | ✅ | 101s |
| pending-nodeselector-mismatch | 33 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 93s |
| pending-nodeselector-mismatch | 34 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 121s |
| pending-nodeselector-mismatch | 35 | L1 ✅ | ❌ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | pvc | 100% | ✅ | 215s |
| pending-nodeselector-mismatch | 36 | L1 ✅ | ❌ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | pvc | 75% | ✅ | 98s |
| pending-nodeselector-mismatch | 37 | L1 ✅ | ❌ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | pvc | 100% | ✅ | 98s |
| pending-nodeselector-mismatch | 38 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 67% | ✅ | 91s |
| pending-nodeselector-mismatch | 39 | L1 ✅ | ❌ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | pvc | 100% | ✅ | 96s |
| pending-nodeselector-mismatch | 40 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 103s |
| pending-nodeselector-mismatch | 41 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 99s |
| pending-nodeselector-mismatch | 42 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 100s |
| pending-nodeselector-mismatch | 43 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 102s |
| pending-nodeselector-mismatch | 44 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 95s |
| pending-nodeselector-mismatch | 45 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 96s |
| pending-nodeselector-mismatch | 46 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 100s |
| pending-nodeselector-mismatch | 47 | L1 ✅ | ❌ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | pvc | 100% | ✅ | 98s |
| pending-nodeselector-mismatch | 48 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 90s |
| pending-nodeselector-mismatch | 49 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 96s |
| pending-nodeselector-mismatch | 50 | L1 ✅ | ✅ | nodeSelector, didn't match≈不匹配, nonexistent-node-label, node selector≈nodeselector | - | - | 100% | ✅ | 93s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| pending-nodeselector-mismatch | pending | 78.0% | 100.0% | 95.0% | 1.1m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 1.1m | ✅ |
| 根因准确率 | >= 60% | 78.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 95.0% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/pending/06-pending-nodeselector-mismatch
