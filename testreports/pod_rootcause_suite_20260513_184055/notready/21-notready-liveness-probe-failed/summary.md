# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 143.1m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| notready-liveness-probe-failed | 1 | L4 ✅ | ✅ | liveness, Liveness probe failed, livenessProbe | - | - | 100% | ✅ | 404s |
| notready-liveness-probe-failed | 2 | L4 ✅ | ✅ | liveness, Liveness probe failed, livenessProbe | - | - | 100% | ✅ | 362s |
| notready-liveness-probe-failed | 3 | L4 ✅ | ❌ | liveness, Liveness probe failed, endpoint failed | - | readiness, OOMKilled | N/A | ✅ | 42s |
| notready-liveness-probe-failed | 4 | L4 ✅ | ❌ | liveness, Liveness probe failed | - | OOMKilled | 100% | ✅ | 308s |
| notready-liveness-probe-failed | 5 | L4 ✅ | ✅ | liveness, Liveness probe failed≈liveness probe 失败, livenessProbe≈liveness probe, endpoint failed≈健康检查接口异常 | - | - | 100% | ✅ | 311s |
| notready-liveness-probe-failed | 6 | L4 ✅ | ✅ | liveness, Liveness probe failed, livenessProbe, endpoint failed | - | - | 100% | ✅ | 330s |
| notready-liveness-probe-failed | 7 | L2 ❌ | ✅ | liveness, Liveness probe failed | - | - | 75% | ✅ | 316s |
| notready-liveness-probe-failed | 8 | L4 ✅ | ❌ | liveness, Liveness probe failed | - | OOMKilled | 100% | ✅ | 352s |
| notready-liveness-probe-failed | 9 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 75% | ✅ | 282s |
| notready-liveness-probe-failed | 10 | L4 ✅ | ✅ | liveness, Liveness probe failed, livenessProbe | - | - | 100% | ✅ | 445s |
| notready-liveness-probe-failed | 11 | L2 ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 100% | ✅ | 276s |
| notready-liveness-probe-failed | 12 | L2 ❌ | ❌ | liveness, Liveness probe failed | - | OOMKilled | 100% | ✅ | 427s |
| notready-liveness-probe-failed | 13 | L4 ✅ | ✅ | liveness, endpoint failed | - | - | 100% | ✅ | 336s |
| notready-liveness-probe-failed | 14 | L4 ✅ | ✅ | liveness, Liveness probe failed | - | - | 100% | ✅ | 306s |
| notready-liveness-probe-failed | 15 | L4 ✅ | ✅ | liveness, Liveness probe failed | - | - | 75% | ✅ | 323s |
| notready-liveness-probe-failed | 16 | L4 ✅ | ✅ | liveness, Liveness probe failed, livenessProbe, endpoint failed | - | - | 100% | ✅ | 441s |
| notready-liveness-probe-failed | 17 | UNKNOWN ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | - | N/A | ❌ | 186s |
| notready-liveness-probe-failed | 18 | L4 ✅ | ❌ | liveness, Liveness probe failed, livenessProbe | - | readiness, OOMKilled | 100% | ✅ | 284s |
| notready-liveness-probe-failed | 19 | L4 ✅ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | readiness | 100% | ✅ | 727s |
| notready-liveness-probe-failed | 20 | L4 ✅ | ✅ | liveness, Liveness probe failed | - | - | 100% | ✅ | 280s |
| notready-liveness-probe-failed | 21 | L4 ✅ | ❌ | liveness, Liveness probe failed, livenessProbe | - | readiness | 80% | ✅ | 492s |
| notready-liveness-probe-failed | 22 | L4 ✅ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | readiness, OOMKilled | 100% | ✅ | 647s |
| notready-liveness-probe-failed | 23 | L2 ❌ | ❌ | liveness, Liveness probe failed | - | OOMKilled | 100% | ✅ | 322s |
| notready-liveness-probe-failed | 24 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 100% | ✅ | 369s |
| notready-liveness-probe-failed | 25 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 100% | ✅ | 369s |
| notready-liveness-probe-failed | 26 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | - | 67% | ✅ | 228s |
| notready-liveness-probe-failed | 27 | L4 ✅ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | readiness | 100% | ✅ | 320s |
| notready-liveness-probe-failed | 28 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 100% | ✅ | 307s |
| notready-liveness-probe-failed | 29 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 100% | ✅ | 256s |
| notready-liveness-probe-failed | 30 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 100% | ✅ | 471s |
| notready-liveness-probe-failed | 31 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 100% | ✅ | 296s |
| notready-liveness-probe-failed | 32 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 75% | ✅ | 232s |
| notready-liveness-probe-failed | 33 | L4 ✅ | ❌ | liveness, livenessProbe | - | readiness | 75% | ✅ | 653s |
| notready-liveness-probe-failed | 34 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | - | 75% | ✅ | 289s |
| notready-liveness-probe-failed | 35 | UNKNOWN ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | - | N/A | ❌ | 38s |
| notready-liveness-probe-failed | 36 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 100% | ✅ | 395s |
| notready-liveness-probe-failed | 37 | L4 ✅ | ❌ | liveness, livenessProbe | - | readiness | 100% | ✅ | 324s |
| notready-liveness-probe-failed | 38 | L4 ✅ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 100% | ✅ | 291s |
| notready-liveness-probe-failed | 39 | L4 ✅ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | readiness | 100% | ✅ | 248s |
| notready-liveness-probe-failed | 40 | UNKNOWN ❌ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | - | N/A | ❌ | 98s |
| notready-liveness-probe-failed | 41 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 75% | ✅ | 354s |
| notready-liveness-probe-failed | 42 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 100% | ✅ | 332s |
| notready-liveness-probe-failed | 43 | L4 ✅ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | readiness, OOMKilled | 100% | ✅ | 848s |
| notready-liveness-probe-failed | 44 | L4 ✅ | ❌ | liveness, livenessProbe | - | readiness | 100% | ✅ | 287s |
| notready-liveness-probe-failed | 45 | L4 ✅ | ❌ | liveness | Liveness probe failed, livenessProbe, endpoint failed | readiness | 50% | ✅ | 186s |
| notready-liveness-probe-failed | 46 | L2 ❌ | ❌ | - | liveness, Liveness probe failed, livenessProbe, endpoint failed | OOMKilled | 100% | ✅ | 349s |
| notready-liveness-probe-failed | 47 | L4 ✅ | ❌ | liveness, Liveness probe failed | - | OOMKilled | 100% | ✅ | 364s |
| notready-liveness-probe-failed | 48 | L2 ❌ | ❌ | liveness, Liveness probe failed | - | OOMKilled | 100% | ✅ | 346s |
| notready-liveness-probe-failed | 49 | L4 ✅ | ✅ | liveness, Liveness probe failed | - | - | 100% | ✅ | 361s |
| notready-liveness-probe-failed | 50 | L4 ✅ | ✅ | liveness, Liveness probe failed, endpoint failed | - | - | 100% | ✅ | 311s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| notready-liveness-probe-failed | notready | 26.0% | 94.0% | 93.9% | 5.3m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 5.3m | ✅ |
| 根因准确率 | >= 60% | 26.0% | ❌ |
| Runbook 覆盖率 | >= 60% | 94.0% | ✅ |
| 证据采集率 | >= 60% | 93.9% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/notready/21-notready-liveness-probe-failed
