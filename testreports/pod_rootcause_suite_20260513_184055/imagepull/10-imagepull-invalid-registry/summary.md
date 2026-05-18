# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 149.6m
- 人工语义修正: 1 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| imagepull-invalid-registry | 1 | L3 ✅ | ✅ | registry.invalid, Failed to pull image, ImagePullBackOff | - | - | 67% | ✅ | 290s |
| imagepull-invalid-registry | 2 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 494s |
| imagepull-invalid-registry | 3 | L3 ✅ | ✅ | registry.invalid, Failed to pull image, ImagePullBackOff | - | - | 100% | ✅ | 254s |
| imagepull-invalid-registry | 4 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 67% | ✅ | 312s |
| imagepull-invalid-registry | 5 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 67% | ✅ | 305s |
| imagepull-invalid-registry | 6 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 434s |
| imagepull-invalid-registry | 7 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 50% | ✅ | 423s |
| imagepull-invalid-registry | 8 | L3 ✅ | ✅ | registry.invalid, Failed to pull image, ImagePullBackOff | - | - | 67% | ✅ | 293s |
| imagepull-invalid-registry | 9 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff, ErrImagePull | - | - | 100% | ✅ | 380s |
| imagepull-invalid-registry | 10 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 218s |
| imagepull-invalid-registry | 11 | L3 ✅ | ✅ | registry.invalid, 语义等价修正: registry.invalid DNS/解析失败 | - | - | 100% | ✅ | 254s |
| imagepull-invalid-registry | 12 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 67% | ✅ | 277s |
| imagepull-invalid-registry | 13 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 67% | ✅ | 348s |
| imagepull-invalid-registry | 14 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 67% | ✅ | 325s |
| imagepull-invalid-registry | 15 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 281s |
| imagepull-invalid-registry | 16 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 75% | ✅ | 362s |
| imagepull-invalid-registry | 17 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 423s |
| imagepull-invalid-registry | 18 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 1941s |
| imagepull-invalid-registry | 19 | L3 ✅ | ✅ | registry.invalid, Failed to pull image, ImagePullBackOff | - | - | 100% | ✅ | 286s |
| imagepull-invalid-registry | 20 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 427s |
| imagepull-invalid-registry | 21 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 67% | ✅ | 312s |
| imagepull-invalid-registry | 22 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 33% | ✅ | 285s |
| imagepull-invalid-registry | 23 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 277s |
| imagepull-invalid-registry | 24 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 67% | ✅ | 353s |
| imagepull-invalid-registry | 25 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 264s |
| imagepull-invalid-registry | 26 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 80% | ✅ | 352s |
| imagepull-invalid-registry | 27 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 370s |
| imagepull-invalid-registry | 28 | L3 ✅ | ✅ | registry.invalid, ErrImagePull | - | - | 25% | ✅ | 335s |
| imagepull-invalid-registry | 29 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 345s |
| imagepull-invalid-registry | 30 | L3 ✅ | ❌ | registry.invalid, ImagePullBackOff, ErrImagePull | - | not found | N/A | ✅ | 38s |
| imagepull-invalid-registry | 31 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 75% | ✅ | 315s |
| imagepull-invalid-registry | 32 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 0% | ✅ | 324s |
| imagepull-invalid-registry | 33 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 271s |
| imagepull-invalid-registry | 34 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 60% | ✅ | 376s |
| imagepull-invalid-registry | 35 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 332s |
| imagepull-invalid-registry | 36 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 287s |
| imagepull-invalid-registry | 37 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 75% | ✅ | 350s |
| imagepull-invalid-registry | 38 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 311s |
| imagepull-invalid-registry | 39 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 338s |
| imagepull-invalid-registry | 40 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 326s |
| imagepull-invalid-registry | 41 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 50% | ✅ | 307s |
| imagepull-invalid-registry | 42 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 306s |
| imagepull-invalid-registry | 43 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 335s |
| imagepull-invalid-registry | 44 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 75% | ✅ | 408s |
| imagepull-invalid-registry | 45 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 75% | ✅ | 354s |
| imagepull-invalid-registry | 46 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 287s |
| imagepull-invalid-registry | 47 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 405s |
| imagepull-invalid-registry | 48 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 272s |
| imagepull-invalid-registry | 49 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 67% | ✅ | 322s |
| imagepull-invalid-registry | 50 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 50% | ✅ | 347s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| imagepull-invalid-registry | imagepull | 98.0% | 100.0% | 81.4% | 5.5m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 5.5m | ✅ |
| 根因准确率 | >= 60% | 98.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 81.4% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/imagepull/10-imagepull-invalid-registry
