# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 62.9m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| notready-readiness-probe-failed | 1 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ✅ | 362s |
| notready-readiness-probe-failed | 2 | L3 ❌ | ✅ | readiness, Readiness probe failed≈就绪探针失败, readinessProbe≈就绪探针, dependency unavailable≈探针失败, readiness 探针失败语义命中 | - | - | 100% | ✅ | 130s |
| notready-readiness-probe-failed | 3 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ❌ | 167s |
| notready-readiness-probe-failed | 4 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ❌ | 145s |
| notready-readiness-probe-failed | 5 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 78% | ✅ | 154s |
| notready-readiness-probe-failed | 6 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | - | 100% | ❌ | 139s |
| notready-readiness-probe-failed | 7 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 78% | ❌ | 167s |
| notready-readiness-probe-failed | 8 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ❌ | 128s |
| notready-readiness-probe-failed | 9 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 88% | ❌ | 113s |
| notready-readiness-probe-failed | 10 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 78% | ❌ | 121s |
| notready-readiness-probe-failed | 11 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ❌ | 175s |
| notready-readiness-probe-failed | 12 | L3 ❌ | ❌ | readiness | Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ✅ | 160s |
| notready-readiness-probe-failed | 13 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 75% | ✅ | 147s |
| notready-readiness-probe-failed | 14 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ✅ | 120s |
| notready-readiness-probe-failed | 15 | L3 ❌ | ❌ | readiness, readinessProbe≈readiness probe | - | ImagePullBackOff | 71% | ✅ | 155s |
| notready-readiness-probe-failed | 16 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ✅ | 133s |
| notready-readiness-probe-failed | 17 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ❌ | 110s |
| notready-readiness-probe-failed | 18 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ✅ | 134s |
| notready-readiness-probe-failed | 19 | L3 ❌ | ❌ | readiness, readinessProbe≈就绪探针 | - | ImagePullBackOff | 100% | ✅ | 168s |
| notready-readiness-probe-failed | 20 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ✅ | 144s |
| notready-readiness-probe-failed | 21 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 86% | ❌ | 113s |
| notready-readiness-probe-failed | 22 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ❌ | 152s |
| notready-readiness-probe-failed | 23 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 88% | ✅ | 130s |
| notready-readiness-probe-failed | 24 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ✅ | 113s |
| notready-readiness-probe-failed | 25 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 89% | ❌ | 130s |
| notready-readiness-probe-failed | 26 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ❌ | 124s |
| notready-readiness-probe-failed | 27 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 78% | ❌ | 108s |
| notready-readiness-probe-failed | 28 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 67% | ✅ | 131s |
| notready-readiness-probe-failed | 29 | L3 ❌ | ❌ | readiness | Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ✅ | 132s |
| notready-readiness-probe-failed | 30 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 88% | ✅ | 150s |
| notready-readiness-probe-failed | 31 | L3 ❌ | ❌ | dependency unavailable≈探针失败 | readiness | ImagePullBackOff | 83% | ❌ | 126s |
| notready-readiness-probe-failed | 32 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ❌ | 298s |
| notready-readiness-probe-failed | 33 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ❌ | 232s |
| notready-readiness-probe-failed | 34 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 89% | ❌ | 115s |
| notready-readiness-probe-failed | 35 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 89% | ❌ | 142s |
| notready-readiness-probe-failed | 36 | L0 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 80% | ❌ | 130s |
| notready-readiness-probe-failed | 37 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ✅ | 206s |
| notready-readiness-probe-failed | 38 | L3 ❌ | ✅ | readiness, Readiness probe failed≈就绪探针失败, readinessProbe≈就绪探针, dependency unavailable, readiness 探针失败语义命中 | - | - | 83% | ✅ | 130s |
| notready-readiness-probe-failed | 39 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ❌ | 117s |
| notready-readiness-probe-failed | 40 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 90% | ✅ | 168s |
| notready-readiness-probe-failed | 41 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 88% | ❌ | 106s |
| notready-readiness-probe-failed | 42 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 78% | ❌ | 130s |
| notready-readiness-probe-failed | 43 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ❌ | 135s |
| notready-readiness-probe-failed | 44 | L0 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 67% | ✅ | 160s |
| notready-readiness-probe-failed | 45 | L3 ❌ | ✅ | readiness, readiness 探针失败语义命中 | - | - | 67% | ❌ | 156s |
| notready-readiness-probe-failed | 46 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ✅ | 129s |
| notready-readiness-probe-failed | 47 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 89% | ❌ | 144s |
| notready-readiness-probe-failed | 48 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 100% | ✅ | 221s |
| notready-readiness-probe-failed | 49 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | 86% | ❌ | 195s |
| notready-readiness-probe-failed | 50 | L3 ❌ | ❌ | - | readiness, Readiness probe failed, readinessProbe, dependency unavailable | ImagePullBackOff | N/A | ❌ | 90s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| notready-readiness-probe-failed | notready | 6.0% | 44.0% | 90.8% | 2.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.0m | ✅ |
| 根因准确率 | >= 60% | 6.0% | ❌ |
| Runbook 覆盖率 | >= 60% | 44.0% | ❌ |
| 证据采集率 | >= 60% | 90.8% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/notready/20-notready-readiness-probe-failed
