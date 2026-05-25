# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 69.8m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| imagepull-invalid-registry | 1 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff, ErrImagePull | - | - | 100% | ✅ | 158s |
| imagepull-invalid-registry | 2 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈拉取镜像失败, ImagePullBackOff, ErrImagePull | - | - | 67% | ✅ | 242s |
| imagepull-invalid-registry | 3 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 100% | ✅ | 142s |
| imagepull-invalid-registry | 4 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff, ErrImagePull | - | - | 100% | ✅ | 92s |
| imagepull-invalid-registry | 5 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 75% | ✅ | 96s |
| imagepull-invalid-registry | 6 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff, ErrImagePull | - | - | 75% | ✅ | 164s |
| imagepull-invalid-registry | 7 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 80% | ✅ | 154s |
| imagepull-invalid-registry | 8 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 80% | ✅ | 110s |
| imagepull-invalid-registry | 9 | L3 ✅ | ✅ | registry.invalid, Failed to pull image, ImagePullBackOff | - | - | 75% | ✅ | 100s |
| imagepull-invalid-registry | 10 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 96s |
| imagepull-invalid-registry | 11 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 80% | ✅ | 109s |
| imagepull-invalid-registry | 12 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 100% | ✅ | 92s |
| imagepull-invalid-registry | 13 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈拉取镜像失败, ImagePullBackOff | - | - | 100% | ✅ | 151s |
| imagepull-invalid-registry | 14 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 112s |
| imagepull-invalid-registry | 15 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 80% | ✅ | 82s |
| imagepull-invalid-registry | 16 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 80% | ✅ | 165s |
| imagepull-invalid-registry | 17 | L3 ✅ | ✅ | registry.invalid, Failed to pull image, ImagePullBackOff, ErrImagePull | - | - | 75% | ✅ | 112s |
| imagepull-invalid-registry | 18 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 100% | ✅ | 130s |
| imagepull-invalid-registry | 19 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff, ErrImagePull | - | - | 100% | ✅ | 100s |
| imagepull-invalid-registry | 20 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 204s |
| imagepull-invalid-registry | 21 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 279s |
| imagepull-invalid-registry | 22 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff, ErrImagePull | - | - | 100% | ✅ | 292s |
| imagepull-invalid-registry | 23 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 100% | ✅ | 214s |
| imagepull-invalid-registry | 24 | L3 ✅ | ❌ | Failed to pull image, ImagePullBackOff, ErrImagePull | registry.invalid | - | 86% | ✅ | 213s |
| imagepull-invalid-registry | 25 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff, ErrImagePull | - | - | 67% | ✅ | 201s |
| imagepull-invalid-registry | 26 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff, ErrImagePull | - | - | 83% | ✅ | 142s |
| imagepull-invalid-registry | 27 | L3 ✅ | ❌ | Failed to pull image≈镜像拉取失败, ImagePullBackOff | registry.invalid | - | 100% | ✅ | 180s |
| imagepull-invalid-registry | 28 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈拉取镜像失败, ImagePullBackOff, ErrImagePull | - | - | 88% | ✅ | 214s |
| imagepull-invalid-registry | 29 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff, ErrImagePull | - | - | 70% | ✅ | 243s |
| imagepull-invalid-registry | 30 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈拉取镜像失败, ImagePullBackOff | - | - | 88% | ✅ | 198s |
| imagepull-invalid-registry | 31 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 100% | ✅ | 148s |
| imagepull-invalid-registry | 32 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈拉取镜像失败, ImagePullBackOff | - | - | 100% | ✅ | 155s |
| imagepull-invalid-registry | 33 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 100% | ✅ | 126s |
| imagepull-invalid-registry | 34 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈拉取镜像失败, ImagePullBackOff | - | - | 100% | ✅ | 178s |
| imagepull-invalid-registry | 35 | L3 ✅ | ✅ | registry.invalid, Failed to pull image, ImagePullBackOff, ErrImagePull | - | - | 100% | ✅ | 175s |
| imagepull-invalid-registry | 36 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 245s |
| imagepull-invalid-registry | 37 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 75% | ✅ | 176s |
| imagepull-invalid-registry | 38 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈拉取镜像失败, ImagePullBackOff | - | - | 100% | ✅ | 125s |
| imagepull-invalid-registry | 39 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈拉取镜像失败, ImagePullBackOff | - | - | 100% | ✅ | 285s |
| imagepull-invalid-registry | 40 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff, ErrImagePull | - | - | 100% | ✅ | 110s |
| imagepull-invalid-registry | 41 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 135s |
| imagepull-invalid-registry | 42 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 275s |
| imagepull-invalid-registry | 43 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈拉取镜像失败, ImagePullBackOff | - | - | 100% | ✅ | 268s |
| imagepull-invalid-registry | 44 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 100% | ✅ | 105s |
| imagepull-invalid-registry | 45 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 100% | ✅ | 156s |
| imagepull-invalid-registry | 46 | L3 ✅ | ✅ | registry.invalid, ImagePullBackOff | - | - | 100% | ✅ | 136s |
| imagepull-invalid-registry | 47 | L3 ✅ | ✅ | registry.invalid, Failed to pull image, ImagePullBackOff, ErrImagePull | - | - | 100% | ✅ | 175s |
| imagepull-invalid-registry | 48 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 88% | ✅ | 192s |
| imagepull-invalid-registry | 49 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈镜像拉取失败, ImagePullBackOff | - | - | 89% | ✅ | 133s |
| imagepull-invalid-registry | 50 | L3 ✅ | ✅ | registry.invalid, Failed to pull image≈拉取镜像失败, ImagePullBackOff, ErrImagePull | - | - | 78% | ✅ | 169s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| imagepull-invalid-registry | imagepull | 96.0% | 100.0% | 91.5% | 2.2m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.2m | ✅ |
| 根因准确率 | >= 60% | 96.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 91.5% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/imagepull/10-imagepull-invalid-registry
