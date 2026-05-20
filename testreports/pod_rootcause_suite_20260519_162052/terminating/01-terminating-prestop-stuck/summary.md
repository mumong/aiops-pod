# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 153.5m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| terminating-prestop-stuck | 1 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | - | 100% | ✅ | 348s |
| terminating-prestop-stuck | 2 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds≈termination grace period, Terminating | - | - | 100% | ✅ | 532s |
| terminating-prestop-stuck | 3 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 322s |
| terminating-prestop-stuck | 4 | L1 ✅ | ❌ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | finalizer | 100% | ✅ | 397s |
| terminating-prestop-stuck | 5 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 388s |
| terminating-prestop-stuck | 6 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 365s |
| terminating-prestop-stuck | 7 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 345s |
| terminating-prestop-stuck | 8 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | - | 100% | ✅ | 332s |
| terminating-prestop-stuck | 9 | L1 ✅ | ❌ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | finalizer | 100% | ✅ | 366s |
| terminating-prestop-stuck | 10 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | - | 100% | ✅ | 368s |
| terminating-prestop-stuck | 11 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 405s |
| terminating-prestop-stuck | 12 | L1 ✅ | ❌ | preStop, hook, sleep, Terminating | - | finalizer | 100% | ✅ | 323s |
| terminating-prestop-stuck | 13 | L1 ✅ | ❌ | preStop, hook, sleep, Terminating | - | finalizer | 100% | ✅ | 384s |
| terminating-prestop-stuck | 14 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 67% | ✅ | 321s |
| terminating-prestop-stuck | 15 | L1 ✅ | ❌ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | finalizer | 100% | ✅ | 366s |
| terminating-prestop-stuck | 16 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 341s |
| terminating-prestop-stuck | 17 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | - | 100% | ✅ | 417s |
| terminating-prestop-stuck | 18 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | - | 100% | ✅ | 378s |
| terminating-prestop-stuck | 19 | L1 ✅ | ❌ | preStop, hook, sleep, terminationGracePeriodSeconds≈termination grace period, Terminating | - | finalizer | 100% | ✅ | 566s |
| terminating-prestop-stuck | 20 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 316s |
| terminating-prestop-stuck | 21 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 430s |
| terminating-prestop-stuck | 22 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 334s |
| terminating-prestop-stuck | 23 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 33% | ✅ | 344s |
| terminating-prestop-stuck | 24 | L1 ✅ | ❌ | preStop, hook, sleep, Terminating | - | finalizer | 100% | ✅ | 376s |
| terminating-prestop-stuck | 25 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 359s |
| terminating-prestop-stuck | 26 | L1 ✅ | ❌ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | finalizer | 100% | ✅ | 364s |
| terminating-prestop-stuck | 27 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 368s |
| terminating-prestop-stuck | 28 | L1 ✅ | ❌ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | finalizer | 33% | ✅ | 335s |
| terminating-prestop-stuck | 29 | L1 ✅ | ❌ | preStop, hook, sleep, terminationGracePeriodSeconds≈termination grace period, Terminating | - | finalizer | 100% | ✅ | 348s |
| terminating-prestop-stuck | 30 | L1 ✅ | ❌ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | finalizer | 100% | ✅ | 331s |
| terminating-prestop-stuck | 31 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds≈termination grace period, Terminating | - | - | 100% | ✅ | 370s |
| terminating-prestop-stuck | 32 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | - | 100% | ✅ | 346s |
| terminating-prestop-stuck | 33 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | - | 100% | ✅ | 357s |
| terminating-prestop-stuck | 34 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | - | 100% | ✅ | 378s |
| terminating-prestop-stuck | 35 | L1 ✅ | ❌ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | finalizer | 100% | ✅ | 332s |
| terminating-prestop-stuck | 36 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 384s |
| terminating-prestop-stuck | 37 | L1 ✅ | ❌ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | finalizer | 100% | ✅ | 372s |
| terminating-prestop-stuck | 38 | L1 ✅ | ❌ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | finalizer | 100% | ✅ | 329s |
| terminating-prestop-stuck | 39 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 389s |
| terminating-prestop-stuck | 40 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds≈termination grace period, Terminating | - | - | 100% | ✅ | 317s |
| terminating-prestop-stuck | 41 | L1 ✅ | ❌ | preStop, hook, sleep, Terminating | - | finalizer | 67% | ✅ | 335s |
| terminating-prestop-stuck | 42 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | - | 100% | ✅ | 325s |
| terminating-prestop-stuck | 43 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 413s |
| terminating-prestop-stuck | 44 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 377s |
| terminating-prestop-stuck | 45 | L1 ✅ | ❌ | preStop, hook, sleep, Terminating | - | finalizer | 100% | ✅ | 370s |
| terminating-prestop-stuck | 46 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds≈termination grace period, Terminating | - | - | 75% | ✅ | 380s |
| terminating-prestop-stuck | 47 | L1 ✅ | ✅ | preStop, hook, sleep, Terminating | - | - | 100% | ✅ | 332s |
| terminating-prestop-stuck | 48 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds, Terminating | - | - | 75% | ✅ | 389s |
| terminating-prestop-stuck | 49 | L1 ✅ | ✅ | preStop, hook, sleep, terminationGracePeriodSeconds≈termination grace period, Terminating | - | - | 100% | ✅ | 371s |
| terminating-prestop-stuck | 50 | L1 ✅ | ❌ | preStop, hook, sleep, Terminating | - | finalizer | 100% | ✅ | 339s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| terminating-prestop-stuck | terminating | 66.0% | 100.0% | 95.0% | 5.7m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 5.7m | ✅ |
| 根因准确率 | >= 60% | 66.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 95.0% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260519_162052/terminating/01-terminating-prestop-stuck
