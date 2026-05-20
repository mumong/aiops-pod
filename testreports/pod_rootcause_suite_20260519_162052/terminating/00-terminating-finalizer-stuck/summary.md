# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 141.2m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| terminating-finalizer-stuck | 1 | L1 ✅ | ✅ | finalizer, Terminating | - | - | 100% | ✅ | 478s |
| terminating-finalizer-stuck | 2 | L1 ✅ | ❌ | finalizer, Terminating | - | OOMKilled | 100% | ✅ | 288s |
| terminating-finalizer-stuck | 3 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 67% | ✅ | 212s |
| terminating-finalizer-stuck | 4 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 538s |
| terminating-finalizer-stuck | 5 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 75% | ✅ | 332s |
| terminating-finalizer-stuck | 6 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 316s |
| terminating-finalizer-stuck | 7 | L1 ✅ | ❌ | finalizer, Terminating | - | OOMKilled | 100% | ✅ | 343s |
| terminating-finalizer-stuck | 8 | L1 ✅ | ❌ | finalizer, deletionTimestamp, Terminating | - | OOMKilled | 100% | ✅ | 391s |
| terminating-finalizer-stuck | 9 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 293s |
| terminating-finalizer-stuck | 10 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 447s |
| terminating-finalizer-stuck | 11 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 229s |
| terminating-finalizer-stuck | 12 | L1 ✅ | ❌ | finalizer, deletionTimestamp, Terminating | - | OOMKilled | 100% | ✅ | 302s |
| terminating-finalizer-stuck | 13 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 275s |
| terminating-finalizer-stuck | 14 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 303s |
| terminating-finalizer-stuck | 15 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 278s |
| terminating-finalizer-stuck | 16 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 347s |
| terminating-finalizer-stuck | 17 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 398s |
| terminating-finalizer-stuck | 18 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 421s |
| terminating-finalizer-stuck | 19 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 275s |
| terminating-finalizer-stuck | 20 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 370s |
| terminating-finalizer-stuck | 21 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 295s |
| terminating-finalizer-stuck | 22 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 287s |
| terminating-finalizer-stuck | 23 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 285s |
| terminating-finalizer-stuck | 24 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 328s |
| terminating-finalizer-stuck | 25 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 523s |
| terminating-finalizer-stuck | 26 | L1 ✅ | ❌ | finalizer, aiops.e2e/rootcause-finalizer, Terminating | - | OOMKilled | 100% | ✅ | 397s |
| terminating-finalizer-stuck | 27 | L1 ✅ | ❌ | finalizer, deletionTimestamp, Terminating | - | terminationGracePeriodSeconds | 100% | ✅ | 310s |
| terminating-finalizer-stuck | 28 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 279s |
| terminating-finalizer-stuck | 29 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 295s |
| terminating-finalizer-stuck | 30 | L1 ✅ | ❌ | finalizer, Terminating | - | OOMKilled | 100% | ✅ | 293s |
| terminating-finalizer-stuck | 31 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 324s |
| terminating-finalizer-stuck | 32 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | N/A | ✅ | 52s |
| terminating-finalizer-stuck | 33 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 429s |
| terminating-finalizer-stuck | 34 | L1 ✅ | ❌ | finalizer, deletionTimestamp, Terminating | - | OOMKilled | 60% | ✅ | 308s |
| terminating-finalizer-stuck | 35 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 305s |
| terminating-finalizer-stuck | 36 | L1 ✅ | ❌ | finalizer, deletionTimestamp, Terminating | - | OOMKilled | 100% | ✅ | 326s |
| terminating-finalizer-stuck | 37 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 275s |
| terminating-finalizer-stuck | 38 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 375s |
| terminating-finalizer-stuck | 39 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 282s |
| terminating-finalizer-stuck | 40 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 323s |
| terminating-finalizer-stuck | 41 | L1 ✅ | ❌ | finalizer, deletionTimestamp, Terminating | - | OOMKilled | 100% | ✅ | 321s |
| terminating-finalizer-stuck | 42 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 344s |
| terminating-finalizer-stuck | 43 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 501s |
| terminating-finalizer-stuck | 44 | L1 ✅ | ❌ | finalizer, aiops.e2e/rootcause-finalizer, Terminating | - | OOMKilled | 100% | ✅ | 430s |
| terminating-finalizer-stuck | 45 | L1 ✅ | ❌ | finalizer, deletionTimestamp, Terminating | - | OOMKilled | 100% | ✅ | 271s |
| terminating-finalizer-stuck | 46 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 485s |
| terminating-finalizer-stuck | 47 | L1 ✅ | ✅ | finalizer, deletionTimestamp, Terminating | - | - | 100% | ✅ | 303s |
| terminating-finalizer-stuck | 48 | L1 ✅ | ✅ | finalizer, aiops.e2e/rootcause-finalizer, deletionTimestamp, Terminating | - | - | 67% | ✅ | 339s |
| terminating-finalizer-stuck | 49 | L1 ✅ | ✅ | finalizer, Terminating | - | - | 100% | ✅ | 467s |
| terminating-finalizer-stuck | 50 | L1 ✅ | ❌ | finalizer, deletionTimestamp, Terminating | - | OOMKilled | 100% | ✅ | 259s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| terminating-finalizer-stuck | terminating | 74.0% | 100.0% | 97.3% | 5.1m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 5.1m | ✅ |
| 根因准确率 | >= 60% | 74.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 97.3% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260519_103127/terminating/01-terminating-finalizer-stuck
