# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 213.2m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| pending-nodeselector-mismatch | 1 | L1 ✅ | ❌ | didn't match | nodeSelector | - | 100% | ✅ | 405s |
| pending-nodeselector-mismatch | 2 | L1 ✅ | ❌ | nodeSelector | didn't match, nonexistent-node-label, node selector | - | 67% | ✅ | 262s |
| pending-nodeselector-mismatch | 3 | L1 ✅ | ✅ | nodeSelector, didn't match | - | - | 100% | ✅ | 181s |
| pending-nodeselector-mismatch | 4 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label | - | - | 100% | ✅ | 279s |
| pending-nodeselector-mismatch | 5 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label | - | - | 100% | ✅ | 442s |
| pending-nodeselector-mismatch | 6 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label | - | - | 100% | ✅ | 422s |
| pending-nodeselector-mismatch | 7 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 353s |
| pending-nodeselector-mismatch | 8 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label | - | - | 100% | ✅ | 322s |
| pending-nodeselector-mismatch | 9 | L1 ✅ | ✅ | nodeSelector, didn't match | - | - | 100% | ✅ | 285s |
| pending-nodeselector-mismatch | 10 | L1 ✅ | ❌ | nodeSelector | didn't match, nonexistent-node-label, node selector | - | 100% | ✅ | 236s |
| pending-nodeselector-mismatch | 11 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label | - | - | 100% | ✅ | 318s |
| pending-nodeselector-mismatch | 12 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label | - | - | 100% | ✅ | 419s |
| pending-nodeselector-mismatch | 13 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 67% | ✅ | 328s |
| pending-nodeselector-mismatch | 14 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 348s |
| pending-nodeselector-mismatch | 15 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 238s |
| pending-nodeselector-mismatch | 16 | L1 ✅ | ✅ | nodeSelector, didn't match | - | - | 100% | ✅ | 233s |
| pending-nodeselector-mismatch | 17 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 222s |
| pending-nodeselector-mismatch | 18 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 272s |
| pending-nodeselector-mismatch | 19 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 459s |
| pending-nodeselector-mismatch | 20 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 75% | ✅ | 261s |
| pending-nodeselector-mismatch | 21 | L1 ✅ | ✅ | nodeSelector, didn't match | - | - | 67% | ✅ | 271s |
| pending-nodeselector-mismatch | 22 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 266s |
| pending-nodeselector-mismatch | 23 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label | - | - | 100% | ✅ | 314s |
| pending-nodeselector-mismatch | 24 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 426s |
| pending-nodeselector-mismatch | 25 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 352s |
| pending-nodeselector-mismatch | 26 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label | - | - | 100% | ✅ | 251s |
| pending-nodeselector-mismatch | 27 | L1 ✅ | ✅ | nodeSelector, didn't match | - | - | 100% | ✅ | 257s |
| pending-nodeselector-mismatch | 28 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 284s |
| pending-nodeselector-mismatch | 29 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label | - | - | 0% | ✅ | 234s |
| pending-nodeselector-mismatch | 30 | L1 ✅ | ✅ | nodeSelector, didn't match | - | - | 100% | ✅ | 278s |
| pending-nodeselector-mismatch | 31 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 287s |
| pending-nodeselector-mismatch | 32 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label | - | - | 67% | ✅ | 335s |
| pending-nodeselector-mismatch | 33 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 210s |
| pending-nodeselector-mismatch | 34 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 382s |
| pending-nodeselector-mismatch | 35 | L1 ✅ | ❌ | nodeSelector | didn't match, nonexistent-node-label, node selector | - | 100% | ✅ | 223s |
| pending-nodeselector-mismatch | 36 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 297s |
| pending-nodeselector-mismatch | 37 | L1 ✅ | ✅ | nodeSelector, didn't match | - | - | 100% | ✅ | 189s |
| pending-nodeselector-mismatch | 38 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 302s |
| pending-nodeselector-mismatch | 39 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 80% | ✅ | 528s |
| pending-nodeselector-mismatch | 40 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 232s |
| pending-nodeselector-mismatch | 41 | L1 ✅ | ❌ | nodeSelector, didn't match | - | pvc | 67% | ✅ | 825s |
| pending-nodeselector-mismatch | 42 | L1 ✅ | ✅ | nodeSelector, didn't match | - | - | 100% | ✅ | 6295s |
| pending-nodeselector-mismatch | 43 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 1731s |
| pending-nodeselector-mismatch | 44 | L1 ✅ | ✅ | nodeSelector, didn't match | - | - | 100% | ✅ | 1060s |
| pending-nodeselector-mismatch | 45 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 1153s |
| pending-nodeselector-mismatch | 46 | L1 ✅ | ✅ | nodeSelector, didn't match | - | - | 100% | ✅ | 1096s |
| pending-nodeselector-mismatch | 47 | L1 ✅ | ✅ | nodeSelector, didn't match | - | - | 100% | ✅ | 445s |
| pending-nodeselector-mismatch | 48 | L1 ✅ | ✅ | nodeSelector, didn't match, nonexistent-node-label | - | - | 100% | ✅ | 316s |
| pending-nodeselector-mismatch | 49 | L1 ✅ | ❌ | nodeSelector | didn't match, nonexistent-node-label, node selector | - | 100% | ✅ | 221s |
| pending-nodeselector-mismatch | 50 | L1 ✅ | ✅ | nodeSelector, nonexistent-node-label | - | - | 100% | ✅ | 166s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| pending-nodeselector-mismatch | pending | 88.0% | 100.0% | 93.8% | 7.9m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 7.9m | ✅ |
| 根因准确率 | >= 60% | 88.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 93.8% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260513_184055/pending/06-pending-nodeselector-mismatch
