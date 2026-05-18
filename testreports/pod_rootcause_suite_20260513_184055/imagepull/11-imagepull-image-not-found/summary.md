# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 153.3m
- 人工语义修正: 31 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| imagepull-image-not-found | 1 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 260s |
| imagepull-image-not-found | 2 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 237s |
| imagepull-image-not-found | 3 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 75% | ✅ | 630s |
| imagepull-image-not-found | 4 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 50% | ✅ | 333s |
| imagepull-image-not-found | 5 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 67% | ✅ | 301s |
| imagepull-image-not-found | 6 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 552s |
| imagepull-image-not-found | 7 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 75% | ✅ | 390s |
| imagepull-image-not-found | 8 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 67% | ✅ | 417s |
| imagepull-image-not-found | 9 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 0% | ✅ | 364s |
| imagepull-image-not-found | 10 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 388s |
| imagepull-image-not-found | 11 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 75% | ✅ | 448s |
| imagepull-image-not-found | 12 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 67% | ✅ | 378s |
| imagepull-image-not-found | 13 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 314s |
| imagepull-image-not-found | 14 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 377s |
| imagepull-image-not-found | 15 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 592s |
| imagepull-image-not-found | 16 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 75% | ✅ | 489s |
| imagepull-image-not-found | 17 | L3 ✅ | ❌ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause | not found | - | 33% | ✅ | 232s |
| imagepull-image-not-found | 18 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 440s |
| imagepull-image-not-found | 19 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 75% | ✅ | 468s |
| imagepull-image-not-found | 20 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 50% | ✅ | 310s |
| imagepull-image-not-found | 21 | L3 ✅ | ✅ | not found, definitely-not-existing-rootcause-tag, registry.k8s.io/pause | - | - | 100% | ✅ | 429s |
| imagepull-image-not-found | 22 | L3 ✅ | ❌ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause | not found | - | 100% | ✅ | 397s |
| imagepull-image-not-found | 23 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 67% | ✅ | 261s |
| imagepull-image-not-found | 24 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 75% | ✅ | 380s |
| imagepull-image-not-found | 25 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 309s |
| imagepull-image-not-found | 26 | L3 ✅ | ❌ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause | not found | - | 100% | ✅ | 320s |
| imagepull-image-not-found | 27 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 75% | ✅ | 348s |
| imagepull-image-not-found | 28 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 404s |
| imagepull-image-not-found | 29 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 80% | ✅ | 342s |
| imagepull-image-not-found | 30 | L3 ✅ | ✅ | not found, definitely-not-existing-rootcause-tag, registry.k8s.io/pause | - | - | 75% | ✅ | 335s |
| imagepull-image-not-found | 31 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 33% | ✅ | 293s |
| imagepull-image-not-found | 32 | L3 ✅ | ❌ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause | not found | - | 100% | ✅ | 260s |
| imagepull-image-not-found | 33 | L3 ✅ | ❌ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause | not found | - | 100% | ✅ | 262s |
| imagepull-image-not-found | 34 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 375s |
| imagepull-image-not-found | 35 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 312s |
| imagepull-image-not-found | 36 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 375s |
| imagepull-image-not-found | 37 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 33% | ✅ | 313s |
| imagepull-image-not-found | 38 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 80% | ✅ | 387s |
| imagepull-image-not-found | 39 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 100% | ✅ | 321s |
| imagepull-image-not-found | 40 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 75% | ✅ | 325s |
| imagepull-image-not-found | 41 | L3 ✅ | ❌ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause | not found | - | 100% | ✅ | 320s |
| imagepull-image-not-found | 42 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 50% | ✅ | 329s |
| imagepull-image-not-found | 43 | L3 ✅ | ✅ | not found, definitely-not-existing-rootcause-tag, registry.k8s.io/pause | - | - | 100% | ✅ | 340s |
| imagepull-image-not-found | 44 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 67% | ✅ | 298s |
| imagepull-image-not-found | 45 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 60% | ✅ | 394s |
| imagepull-image-not-found | 46 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 80% | ✅ | 557s |
| imagepull-image-not-found | 47 | L3 ✅ | ✅ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause, 语义等价修正: 镜像 tag 不存在 等价 image not found | - | - | 75% | ✅ | 341s |
| imagepull-image-not-found | 48 | L3 ✅ | ❌ | definitely-not-existing-rootcause-tag, registry.k8s.io/pause | not found | - | 100% | ✅ | 434s |
| imagepull-image-not-found | 49 | L3 ✅ | ❌ | registry.k8s.io/pause | not found | - | 100% | ✅ | 232s |
| imagepull-image-not-found | 50 | L3 ✅ | ✅ | not found, definitely-not-existing-rootcause-tag, registry.k8s.io/pause | - | - | 100% | ✅ | 300s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| imagepull-image-not-found | imagepull | 70.0% | 100.0% | 80.7% | 5.6m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 5.6m | ✅ |
| 根因准确率 | >= 60% | 70.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 80.7% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/imagepull/11-imagepull-image-not-found
