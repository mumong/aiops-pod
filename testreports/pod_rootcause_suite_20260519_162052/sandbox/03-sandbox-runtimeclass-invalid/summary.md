# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 176.9m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| sandbox-runtimeclass-invalid | 1 | L3 ✅ | ✅ | runtimeClass, FailedCreatePodSandBox | - | - | 100% | ✅ | 359s |
| sandbox-runtimeclass-invalid | 2 | L3 ✅ | ✅ | runtimeClass, runtime handler, FailedCreatePodSandBox | - | - | 80% | ✅ | 602s |
| sandbox-runtimeclass-invalid | 3 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 498s |
| sandbox-runtimeclass-invalid | 4 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 431s |
| sandbox-runtimeclass-invalid | 5 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 40% | ✅ | 496s |
| sandbox-runtimeclass-invalid | 6 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 669s |
| sandbox-runtimeclass-invalid | 7 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 75% | ✅ | 288s |
| sandbox-runtimeclass-invalid | 8 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, runtime handler | - | - | 100% | ✅ | 559s |
| sandbox-runtimeclass-invalid | 9 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler | - | - | 75% | ✅ | 386s |
| sandbox-runtimeclass-invalid | 10 | L1 ❌ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 284s |
| sandbox-runtimeclass-invalid | 11 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 541s |
| sandbox-runtimeclass-invalid | 12 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, runtime handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 379s |
| sandbox-runtimeclass-invalid | 13 | L1 ❌ | ✅ | runtimeClass, runtime handler, FailedCreatePodSandBox | - | - | 75% | ✅ | 453s |
| sandbox-runtimeclass-invalid | 14 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, runtime handler | - | - | 100% | ✅ | 327s |
| sandbox-runtimeclass-invalid | 15 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 348s |
| sandbox-runtimeclass-invalid | 16 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 80% | ✅ | 398s |
| sandbox-runtimeclass-invalid | 17 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 247s |
| sandbox-runtimeclass-invalid | 18 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 361s |
| sandbox-runtimeclass-invalid | 19 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler | - | - | 100% | ✅ | 587s |
| sandbox-runtimeclass-invalid | 20 | L1 ❌ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 299s |
| sandbox-runtimeclass-invalid | 21 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler, runtime handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 477s |
| sandbox-runtimeclass-invalid | 22 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 399s |
| sandbox-runtimeclass-invalid | 23 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 437s |
| sandbox-runtimeclass-invalid | 24 | L3 ✅ | ✅ | runtimeClass, FailedCreatePodSandBox | - | - | 80% | ✅ | 618s |
| sandbox-runtimeclass-invalid | 25 | L3 ✅ | ❌ | runtimeClass, FailedCreatePodSandBox | - | CNI | 100% | ✅ | 482s |
| sandbox-runtimeclass-invalid | 26 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, runtime handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 355s |
| sandbox-runtimeclass-invalid | 27 | L3 ✅ | ✅ | runtimeClass, FailedCreatePodSandBox | - | - | 100% | ✅ | 551s |
| sandbox-runtimeclass-invalid | 28 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, runtime handler | - | - | 100% | ✅ | 353s |
| sandbox-runtimeclass-invalid | 29 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler | - | - | 67% | ✅ | 306s |
| sandbox-runtimeclass-invalid | 30 | L3 ✅ | ✅ | runtimeClass, FailedCreatePodSandBox | - | - | 100% | ✅ | 328s |
| sandbox-runtimeclass-invalid | 31 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler, runtime handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 437s |
| sandbox-runtimeclass-invalid | 32 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, runtime handler, FailedCreatePodSandBox | - | - | 80% | ✅ | 510s |
| sandbox-runtimeclass-invalid | 33 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 422s |
| sandbox-runtimeclass-invalid | 34 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler | - | - | 100% | ✅ | 522s |
| sandbox-runtimeclass-invalid | 35 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler | - | - | 100% | ✅ | 400s |
| sandbox-runtimeclass-invalid | 36 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, runtime handler | - | - | 100% | ✅ | 456s |
| sandbox-runtimeclass-invalid | 37 | L3 ✅ | ❌ | runtimeClass, rc-definitely-missing-runtime-handler, runtime handler, FailedCreatePodSandBox | - | CNI | 100% | ✅ | 500s |
| sandbox-runtimeclass-invalid | 38 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 385s |
| sandbox-runtimeclass-invalid | 39 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 337s |
| sandbox-runtimeclass-invalid | 40 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 412s |
| sandbox-runtimeclass-invalid | 41 | L3 ✅ | ✅ | runtimeClass, runtime handler | - | - | 67% | ✅ | 269s |
| sandbox-runtimeclass-invalid | 42 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 80% | ✅ | 344s |
| sandbox-runtimeclass-invalid | 43 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, runtime handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 373s |
| sandbox-runtimeclass-invalid | 44 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, runtime handler | - | - | 67% | ✅ | 334s |
| sandbox-runtimeclass-invalid | 45 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 352s |
| sandbox-runtimeclass-invalid | 46 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler, runtime handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 517s |
| sandbox-runtimeclass-invalid | 47 | L3 ✅ | ✅ | runtimeClass, FailedCreatePodSandBox | - | - | 100% | ✅ | 399s |
| sandbox-runtimeclass-invalid | 48 | L3 ✅ | ✅ | runtimeClass, rc-definitely-missing-runtime-handler, runtime handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 465s |
| sandbox-runtimeclass-invalid | 49 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler, runtime handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 627s |
| sandbox-runtimeclass-invalid | 50 | L3 ✅ | ✅ | runtimeClass, rc-invalid-runtime-handler, rc-definitely-missing-runtime-handler, FailedCreatePodSandBox | - | - | 100% | ✅ | 287s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| sandbox-runtimeclass-invalid | sandbox | 96.0% | 100.0% | 93.3% | 6.6m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 6.6m | ✅ |
| 根因准确率 | >= 60% | 96.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 93.3% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260519_162052/sandbox/03-sandbox-runtimeclass-invalid
