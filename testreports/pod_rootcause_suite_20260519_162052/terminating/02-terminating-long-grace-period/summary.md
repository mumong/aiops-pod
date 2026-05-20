# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 154.9m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| terminating-long-grace-period | 1 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, Terminating | - | - | 100% | ✅ | 372s |
| terminating-long-grace-period | 2 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, Terminating | - | - | 100% | ✅ | 373s |
| terminating-long-grace-period | 3 | L1 ✅ | ❌ | 21600, Terminating | terminationGracePeriodSeconds | finalizer | 100% | ✅ | 431s |
| terminating-long-grace-period | 4 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer | 75% | ✅ | 377s |
| terminating-long-grace-period | 5 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, Terminating | - | - | 100% | ✅ | 363s |
| terminating-long-grace-period | 6 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, Terminating | - | - | 100% | ✅ | 403s |
| terminating-long-grace-period | 7 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | preStop | 100% | ✅ | 354s |
| terminating-long-grace-period | 8 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer, preStop | 100% | ✅ | 409s |
| terminating-long-grace-period | 9 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer | 100% | ✅ | 389s |
| terminating-long-grace-period | 10 | L1 ✅ | ❌ | Terminating | terminationGracePeriodSeconds | finalizer, preStop | 100% | ✅ | 390s |
| terminating-long-grace-period | 11 | L1 ✅ | ❌ | Terminating | terminationGracePeriodSeconds | finalizer | 100% | ✅ | 341s |
| terminating-long-grace-period | 12 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, Terminating | - | - | 100% | ✅ | 365s |
| terminating-long-grace-period | 13 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, Terminating | - | - | 100% | ✅ | 357s |
| terminating-long-grace-period | 14 | L1 ✅ | ❌ | Terminating | terminationGracePeriodSeconds | finalizer, preStop | 67% | ✅ | 361s |
| terminating-long-grace-period | 15 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer | 67% | ✅ | 354s |
| terminating-long-grace-period | 16 | L1 ✅ | ❌ | Terminating | terminationGracePeriodSeconds | finalizer | 100% | ✅ | 339s |
| terminating-long-grace-period | 17 | L1 ✅ | ✅ | terminationGracePeriodSeconds≈termination grace period, 21600, grace period, Terminating | - | - | 100% | ✅ | 380s |
| terminating-long-grace-period | 18 | L1 ✅ | ✅ | terminationGracePeriodSeconds≈grace period, 21600, grace period, Terminating | - | - | 100% | ✅ | 331s |
| terminating-long-grace-period | 19 | L1 ✅ | ❌ | Terminating | terminationGracePeriodSeconds | finalizer | 100% | ✅ | 336s |
| terminating-long-grace-period | 20 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, Terminating | - | - | 100% | ✅ | 307s |
| terminating-long-grace-period | 21 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer | 100% | ✅ | 431s |
| terminating-long-grace-period | 22 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, grace period, Terminating | - | - | 100% | ✅ | 359s |
| terminating-long-grace-period | 23 | L1 ✅ | ❌ | Terminating | terminationGracePeriodSeconds | finalizer | 67% | ✅ | 380s |
| terminating-long-grace-period | 24 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer, preStop | 100% | ✅ | 441s |
| terminating-long-grace-period | 25 | L1 ✅ | ❌ | 21600, Terminating | terminationGracePeriodSeconds | finalizer | 100% | ✅ | 375s |
| terminating-long-grace-period | 26 | L1 ✅ | ❌ | 21600, Terminating | terminationGracePeriodSeconds | finalizer, preStop | 100% | ✅ | 342s |
| terminating-long-grace-period | 27 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer | 100% | ✅ | 343s |
| terminating-long-grace-period | 28 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer | 100% | ✅ | 343s |
| terminating-long-grace-period | 29 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, Terminating | - | - | 100% | ✅ | 370s |
| terminating-long-grace-period | 30 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer | 100% | ✅ | 339s |
| terminating-long-grace-period | 31 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, Terminating | - | - | 100% | ✅ | 349s |
| terminating-long-grace-period | 32 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer, preStop | 100% | ✅ | 384s |
| terminating-long-grace-period | 33 | L1 ✅ | ❌ | 21600, Terminating | terminationGracePeriodSeconds | finalizer, preStop | 100% | ✅ | 386s |
| terminating-long-grace-period | 34 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, Terminating | - | - | 67% | ✅ | 362s |
| terminating-long-grace-period | 35 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, grace period, Terminating | - | finalizer, preStop | 100% | ✅ | 390s |
| terminating-long-grace-period | 36 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer | 100% | ✅ | 372s |
| terminating-long-grace-period | 37 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, grace period, Terminating | - | finalizer | 100% | ✅ | 382s |
| terminating-long-grace-period | 38 | L1 ✅ | ❌ | Terminating | terminationGracePeriodSeconds | finalizer | 100% | ✅ | 347s |
| terminating-long-grace-period | 39 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, Terminating | - | - | 100% | ✅ | 365s |
| terminating-long-grace-period | 40 | L1 ✅ | ❌ | Terminating | terminationGracePeriodSeconds | - | 67% | ✅ | 436s |
| terminating-long-grace-period | 41 | L1 ✅ | ❌ | 21600, Terminating | terminationGracePeriodSeconds | - | 100% | ✅ | 327s |
| terminating-long-grace-period | 42 | L1 ✅ | ❌ | 21600, Terminating | terminationGracePeriodSeconds | - | 100% | ✅ | 364s |
| terminating-long-grace-period | 43 | L1 ✅ | ❌ | terminationGracePeriodSeconds≈termination grace period, 21600, grace period, Terminating | - | finalizer | 100% | ✅ | 358s |
| terminating-long-grace-period | 44 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer | 100% | ✅ | 282s |
| terminating-long-grace-period | 45 | L1 ✅ | ❌ | terminationGracePeriodSeconds≈termination grace period, 21600, grace period, Terminating | - | finalizer | 100% | ✅ | 381s |
| terminating-long-grace-period | 46 | L1 ✅ | ✅ | terminationGracePeriodSeconds, 21600, grace period, Terminating | - | - | 100% | ✅ | 489s |
| terminating-long-grace-period | 47 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer | 100% | ✅ | 370s |
| terminating-long-grace-period | 48 | L1 ✅ | ❌ | terminationGracePeriodSeconds≈优雅终止, 21600, Terminating | - | finalizer | 100% | ✅ | 365s |
| terminating-long-grace-period | 49 | L1 ✅ | ❌ | Terminating | terminationGracePeriodSeconds | finalizer | 67% | ✅ | 300s |
| terminating-long-grace-period | 50 | L1 ✅ | ❌ | terminationGracePeriodSeconds, 21600, Terminating | - | finalizer | 100% | ✅ | 329s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| terminating-long-grace-period | terminating | 30.0% | 100.0% | 95.5% | 5.7m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 5.7m | ✅ |
| 根因准确率 | >= 60% | 30.0% | ❌ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 95.5% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260519_162052/terminating/02-terminating-long-grace-period
