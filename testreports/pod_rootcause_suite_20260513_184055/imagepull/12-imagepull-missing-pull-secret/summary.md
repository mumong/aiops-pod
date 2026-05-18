# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 146.9m
- 人工语义修正: 16 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| imagepull-missing-pull-secret | 1 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 75% | ✅ | 393s |
| imagepull-missing-pull-secret | 2 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 100% | ✅ | 310s |
| imagepull-missing-pull-secret | 3 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 75% | ✅ | 359s |
| imagepull-missing-pull-secret | 4 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 75% | ✅ | 328s |
| imagepull-missing-pull-secret | 5 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 25% | ✅ | 416s |
| imagepull-missing-pull-secret | 6 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 273s |
| imagepull-missing-pull-secret | 7 | L3 ✅ | ✅ | secret, imagePullSecrets | - | - | 67% | ✅ | 336s |
| imagepull-missing-pull-secret | 8 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 75% | ✅ | 301s |
| imagepull-missing-pull-secret | 9 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 67% | ✅ | 405s |
| imagepull-missing-pull-secret | 10 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 100% | ✅ | 361s |
| imagepull-missing-pull-secret | 11 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 100% | ✅ | 274s |
| imagepull-missing-pull-secret | 12 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 245s |
| imagepull-missing-pull-secret | 13 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 67% | ✅ | 339s |
| imagepull-missing-pull-secret | 14 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 303s |
| imagepull-missing-pull-secret | 15 | L3 ✅ | ❌ | - | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 370s |
| imagepull-missing-pull-secret | 16 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 67% | ✅ | 331s |
| imagepull-missing-pull-secret | 17 | L3 ✅ | ✅ | secret, imagePullSecrets | - | - | 80% | ✅ | 408s |
| imagepull-missing-pull-secret | 18 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 80% | ✅ | 427s |
| imagepull-missing-pull-secret | 19 | L3 ✅ | ❌ | - | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 464s |
| imagepull-missing-pull-secret | 20 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 67% | ✅ | 412s |
| imagepull-missing-pull-secret | 21 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret, imagePullSecrets | - | - | 100% | ✅ | 323s |
| imagepull-missing-pull-secret | 22 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 75% | ✅ | 378s |
| imagepull-missing-pull-secret | 23 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 100% | ✅ | 267s |
| imagepull-missing-pull-secret | 24 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 75% | ✅ | 368s |
| imagepull-missing-pull-secret | 25 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 80% | ✅ | 326s |
| imagepull-missing-pull-secret | 26 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 100% | ✅ | 320s |
| imagepull-missing-pull-secret | 27 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 389s |
| imagepull-missing-pull-secret | 28 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 60% | ✅ | 388s |
| imagepull-missing-pull-secret | 29 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 100% | ✅ | 418s |
| imagepull-missing-pull-secret | 30 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 75% | ✅ | 370s |
| imagepull-missing-pull-secret | 31 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 100% | ✅ | 334s |
| imagepull-missing-pull-secret | 32 | L3 ✅ | ✅ | secret, imagePullSecrets | - | - | 100% | ✅ | 406s |
| imagepull-missing-pull-secret | 33 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 75% | ✅ | 393s |
| imagepull-missing-pull-secret | 34 | L3 ✅ | ❌ | - | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 80% | ✅ | 379s |
| imagepull-missing-pull-secret | 35 | L3 ✅ | ✅ | secret, imagePullSecrets | - | - | 50% | ✅ | 226s |
| imagepull-missing-pull-secret | 36 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 50% | ✅ | 332s |
| imagepull-missing-pull-secret | 37 | L3 ✅ | ✅ | secret, imagePullSecrets | - | - | 100% | ✅ | 428s |
| imagepull-missing-pull-secret | 38 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 100% | ✅ | 303s |
| imagepull-missing-pull-secret | 39 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 100% | ✅ | 312s |
| imagepull-missing-pull-secret | 40 | L3 ✅ | ❌ | - | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 379s |
| imagepull-missing-pull-secret | 41 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 50% | ✅ | 407s |
| imagepull-missing-pull-secret | 42 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 100% | ✅ | 291s |
| imagepull-missing-pull-secret | 43 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 363s |
| imagepull-missing-pull-secret | 44 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 75% | ✅ | 431s |
| imagepull-missing-pull-secret | 45 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 100% | ✅ | 334s |
| imagepull-missing-pull-secret | 46 | L3 ✅ | ✅ | secret, 语义等价修正: imagePullSecret 缺失/不存在 | - | - | 100% | ✅ | 312s |
| imagepull-missing-pull-secret | 47 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 100% | ✅ | 345s |
| imagepull-missing-pull-secret | 48 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 75% | ✅ | 377s |
| imagepull-missing-pull-secret | 49 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 100% | ✅ | 272s |
| imagepull-missing-pull-secret | 50 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 75% | ✅ | 247s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| imagepull-missing-pull-secret | imagepull | 68.0% | 100.0% | 84.3% | 5.4m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 5.4m | ✅ |
| 根因准确率 | >= 60% | 68.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 84.3% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/imagepull/12-imagepull-missing-pull-secret
