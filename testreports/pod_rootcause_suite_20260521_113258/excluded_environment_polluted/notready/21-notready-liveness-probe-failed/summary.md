# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 73.2m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| notready-liveness-probe-failed | 1 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 86% | ❌ | 162s |
| notready-liveness-probe-failed | 2 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 88% | ❌ | 154s |
| notready-liveness-probe-failed | 3 | L3 ❌ | ❌ | liveness, livenessProbe≈liveness probe | - | ImagePullBackOff | 100% | ✅ | 132s |
| notready-liveness-probe-failed | 4 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ❌ | 123s |
| notready-liveness-probe-failed | 5 | L3 ❌ | ✅ | liveness, Liveness probe failed≈liveness probe 失败, livenessProbe≈liveness probe, liveness 探针失败语义命中 | - | - | 100% | ✅ | 138s |
| notready-liveness-probe-failed | 6 | L3 ❌ | ✅ | liveness, Liveness probe failed, livenessProbe≈liveness probe, endpoint failed, liveness 探针失败语义命中 | - | - | 100% | ✅ | 159s |
| notready-liveness-probe-failed | 7 | L3 ❌ | ✅ | liveness, Liveness probe failed, livenessProbe≈liveness probe, endpoint failed≈探针失败, liveness 探针失败语义命中 | - | - | 88% | ✅ | 168s |
| notready-liveness-probe-failed | 8 | L3 ❌ | ❌ | liveness, Liveness probe failed≈liveness probe 失败, livenessProbe≈liveness probe | - | ImagePullBackOff | 75% | ✅ | 139s |
| notready-liveness-probe-failed | 9 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 255s |
| notready-liveness-probe-failed | 10 | L3 ❌ | ❌ | liveness, livenessProbe≈liveness 探针 | - | ImagePullBackOff | 90% | ✅ | 211s |
| notready-liveness-probe-failed | 11 | L3 ❌ | ❌ | liveness, livenessProbe≈liveness probe | - | ImagePullBackOff | 88% | ✅ | 183s |
| notready-liveness-probe-failed | 12 | L3 ❌ | ✅ | liveness, livenessProbe≈liveness probe, liveness 探针失败语义命中 | - | - | 75% | ✅ | 209s |
| notready-liveness-probe-failed | 13 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 89% | ✅ | 167s |
| notready-liveness-probe-failed | 14 | L3 ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 62% | ✅ | 209s |
| notready-liveness-probe-failed | 15 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 89% | ✅ | 162s |
| notready-liveness-probe-failed | 16 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 167s |
| notready-liveness-probe-failed | 17 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ❌ | 153s |
| notready-liveness-probe-failed | 18 | L3 ❌ | ✅ | liveness, Liveness probe failed≈liveness 探针失败, livenessProbe≈liveness 探针, endpoint failed≈探针失败, liveness 探针失败语义命中 | - | - | 100% | ✅ | 176s |
| notready-liveness-probe-failed | 19 | L3 ❌ | ❌ | liveness, livenessProbe≈liveness probe | - | ImagePullBackOff | 100% | ✅ | 181s |
| notready-liveness-probe-failed | 20 | L3 ❌ | ✅ | liveness, endpoint failed≈探针失败, liveness 探针失败语义命中 | - | - | 89% | ✅ | 164s |
| notready-liveness-probe-failed | 21 | L3 ❌ | ❌ | liveness, livenessProbe | - | ImagePullBackOff | 100% | ✅ | 148s |
| notready-liveness-probe-failed | 22 | L3 ❌ | ❌ | liveness, livenessProbe≈liveness probe | - | ImagePullBackOff | 100% | ✅ | 126s |
| notready-liveness-probe-failed | 23 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 175s |
| notready-liveness-probe-failed | 24 | L3 ❌ | ✅ | liveness, Liveness probe failed≈存活探针失败, livenessProbe≈存活探针, endpoint failed≈探针失败, liveness 探针失败语义命中 | - | - | 100% | ✅ | 125s |
| notready-liveness-probe-failed | 25 | L3 ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 285s |
| notready-liveness-probe-failed | 26 | L3 ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 90% | ✅ | 171s |
| notready-liveness-probe-failed | 27 | L3 ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 184s |
| notready-liveness-probe-failed | 28 | L3 ❌ | ✅ | liveness, liveness 探针失败语义命中 | - | - | 100% | ✅ | 343s |
| notready-liveness-probe-failed | 29 | L3 ❌ | ✅ | liveness, Liveness probe failed≈存活探针失败, livenessProbe≈存活探针, endpoint failed≈探针失败, liveness 探针失败语义命中 | - | - | 90% | ✅ | 135s |
| notready-liveness-probe-failed | 30 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ❌ | 152s |
| notready-liveness-probe-failed | 31 | L3 ❌ | ❌ | liveness, livenessProbe, endpoint failed | - | ImagePullBackOff | 100% | ✅ | 163s |
| notready-liveness-probe-failed | 32 | L3 ❌ | ✅ | liveness, Liveness probe failed, livenessProbe≈liveness probe, endpoint failed≈探针失败, liveness 探针失败语义命中 | - | - | 100% | ✅ | 150s |
| notready-liveness-probe-failed | 33 | L3 ❌ | ❌ | liveness, livenessProbe≈存活探针 | - | ImagePullBackOff | 100% | ✅ | 141s |
| notready-liveness-probe-failed | 34 | L3 ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 86% | ✅ | 139s |
| notready-liveness-probe-failed | 35 | L3 ❌ | ❌ | liveness, livenessProbe≈liveness probe | - | ImagePullBackOff | 100% | ✅ | 160s |
| notready-liveness-probe-failed | 36 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 186s |
| notready-liveness-probe-failed | 37 | L3 ❌ | ❌ | liveness, livenessProbe≈liveness 探针 | - | ImagePullBackOff | 100% | ✅ | 153s |
| notready-liveness-probe-failed | 38 | L3 ❌ | ❌ | liveness, livenessProbe≈liveness 探针 | - | ImagePullBackOff | 89% | ✅ | 164s |
| notready-liveness-probe-failed | 39 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 89% | ❌ | 200s |
| notready-liveness-probe-failed | 40 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 88% | ❌ | 200s |
| notready-liveness-probe-failed | 41 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 183s |
| notready-liveness-probe-failed | 42 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 187s |
| notready-liveness-probe-failed | 43 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ❌ | 142s |
| notready-liveness-probe-failed | 44 | L3 ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 174s |
| notready-liveness-probe-failed | 45 | L3 ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 162s |
| notready-liveness-probe-failed | 46 | L1 ❌ | ❌ | liveness, livenessProbe≈liveness probe | - | ImagePullBackOff | 80% | ✅ | 168s |
| notready-liveness-probe-failed | 47 | L3 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 154s |
| notready-liveness-probe-failed | 48 | L3 ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | OOMKilled, ImagePullBackOff | 89% | ✅ | 171s |
| notready-liveness-probe-failed | 49 | L3 ❌ | ❌ | liveness, livenessProbe≈liveness 探针 | - | ImagePullBackOff | 100% | ✅ | 147s |
| notready-liveness-probe-failed | 50 | L3 ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | ImagePullBackOff | 100% | ✅ | 192s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| notready-liveness-probe-failed | notready | 20.0% | 84.0% | 94.3% | 2.4m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.4m | ✅ |
| 根因准确率 | >= 60% | 20.0% | ❌ |
| Runbook 覆盖率 | >= 60% | 84.0% | ✅ |
| 证据采集率 | >= 60% | 94.3% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/notready/21-notready-liveness-probe-failed
