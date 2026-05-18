# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 274.0m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| notready-readiness-probe-failed | 1 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 75% | ✅ | 574s |
| notready-readiness-probe-failed | 2 | L4 ✅ | ✅ | readiness, Readiness probe failed, dependency unavailable | - | - | 100% | ✅ | 1988s |
| notready-readiness-probe-failed | 3 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 60% | ✅ | 576s |
| notready-readiness-probe-failed | 4 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 75% | ✅ | 396s |
| notready-readiness-probe-failed | 5 | L4 ✅ | ✅ | readiness, Readiness probe failed≈readiness probe 失败, readinessProbe≈readiness probe, dependency unavailable≈健康检查路径 | - | - | 100% | ✅ | 388s |
| notready-readiness-probe-failed | 6 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe | - | - | 100% | ✅ | 504s |
| notready-readiness-probe-failed | 7 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 392s |
| notready-readiness-probe-failed | 8 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 75% | ✅ | 815s |
| notready-readiness-probe-failed | 9 | L4 ✅ | ✅ | readiness, readinessProbe | - | - | 80% | ✅ | 293s |
| notready-readiness-probe-failed | 10 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 425s |
| notready-readiness-probe-failed | 11 | L4 ✅ | ✅ | readiness, readinessProbe | - | - | 67% | ✅ | 225s |
| notready-readiness-probe-failed | 12 | L4 ✅ | ✅ | readiness, readinessProbe, dependency unavailable | - | - | 67% | ✅ | 454s |
| notready-readiness-probe-failed | 13 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 392s |
| notready-readiness-probe-failed | 14 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 359s |
| notready-readiness-probe-failed | 15 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe | - | - | 67% | ✅ | 643s |
| notready-readiness-probe-failed | 16 | L4 ✅ | ✅ | readiness, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 338s |
| notready-readiness-probe-failed | 17 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 419s |
| notready-readiness-probe-failed | 18 | L4 ✅ | ✅ | readiness, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 334s |
| notready-readiness-probe-failed | 19 | UNKNOWN ❌ | ❌ | readiness | Readiness probe failed, readinessProbe, dependency unavailable | - | N/A | ❌ | 1668s |
| notready-readiness-probe-failed | 20 | L4 ✅ | ✅ | readiness, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 248s |
| notready-readiness-probe-failed | 21 | L4 ✅ | ✅ | readiness, Readiness probe failed, dependency unavailable | - | - | 100% | ✅ | 596s |
| notready-readiness-probe-failed | 22 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 67% | ✅ | 511s |
| notready-readiness-probe-failed | 23 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 50% | ✅ | 329s |
| notready-readiness-probe-failed | 24 | L4 ✅ | ✅ | readiness, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 237s |
| notready-readiness-probe-failed | 25 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 1801s |
| notready-readiness-probe-failed | 26 | L4 ✅ | ✅ | readiness, readinessProbe | - | - | 100% | ✅ | 264s |
| notready-readiness-probe-failed | 27 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe | - | - | 100% | ✅ | 251s |
| notready-readiness-probe-failed | 28 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 75% | ✅ | 1905s |
| notready-readiness-probe-failed | 29 | L4 ✅ | ✅ | readiness, readinessProbe | - | - | 100% | ✅ | 296s |
| notready-readiness-probe-failed | 30 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 375s |
| notready-readiness-probe-failed | 31 | L4 ✅ | ✅ | readiness, readinessProbe≈readiness 探针, dependency unavailable≈健康接口不匹配 | - | - | 33% | ✅ | 2327s |
| notready-readiness-probe-failed | 32 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe | - | - | 100% | ✅ | 2041s |
| notready-readiness-probe-failed | 33 | L4 ✅ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | 80% | ✅ | 322s |
| notready-readiness-probe-failed | 34 | L4 ✅ | ✅ | readiness, readinessProbe, dependency unavailable | - | - | 80% | ✅ | 2244s |
| notready-readiness-probe-failed | 35 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 50% | ✅ | 1071s |
| notready-readiness-probe-failed | 36 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 835s |
| notready-readiness-probe-failed | 37 | L4 ✅ | ✅ | readiness, readinessProbe | - | - | 100% | ✅ | 211s |
| notready-readiness-probe-failed | 38 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 285s |
| notready-readiness-probe-failed | 39 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 860s |
| notready-readiness-probe-failed | 40 | L4 ✅ | ✅ | readiness, readinessProbe | - | - | 100% | ✅ | 418s |
| notready-readiness-probe-failed | 41 | UNKNOWN ❌ | ❌ | readiness | Readiness probe failed, readinessProbe, dependency unavailable | - | N/A | ❌ | 133s |
| notready-readiness-probe-failed | 42 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 413s |
| notready-readiness-probe-failed | 43 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe | - | - | 75% | ✅ | 358s |
| notready-readiness-probe-failed | 44 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe | - | - | 50% | ✅ | 271s |
| notready-readiness-probe-failed | 45 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 994s |
| notready-readiness-probe-failed | 46 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | - | 100% | ✅ | 276s |
| notready-readiness-probe-failed | 47 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe | - | - | 75% | ✅ | 376s |
| notready-readiness-probe-failed | 48 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe | - | - | 100% | ✅ | 515s |
| notready-readiness-probe-failed | 49 | L4 ✅ | ✅ | readiness, Readiness probe failed, readinessProbe | - | - | 100% | ✅ | 470s |
| notready-readiness-probe-failed | 50 | L4 ✅ | ✅ | readiness, Readiness probe failed, dependency unavailable | - | - | 75% | ✅ | 261s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| notready-readiness-probe-failed | notready | 94.0% | 96.0% | 87.0% | 10.3m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 10.3m | ✅ |
| 根因准确率 | >= 60% | 94.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 96.0% | ✅ |
| 证据采集率 | >= 60% | 87.0% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/notready/20-notready-readiness-probe-failed
