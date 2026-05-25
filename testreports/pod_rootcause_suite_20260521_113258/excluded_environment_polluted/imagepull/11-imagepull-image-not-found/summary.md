# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 84.0m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| imagepull-image-not-found | 1 | L3 ✅ | ✅ | not found≈不存在, definitely-not-existing-rootcause-tag, manifest unknown≈镜像 tag 不存在, registry.k8s.io/pause | - | - | 100% | ✅ | 80s |
| imagepull-image-not-found | 2 | L3 ✅ | ✅ | not found≈不存在, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | - | 100% | ✅ | 89s |
| imagepull-image-not-found | 3 | L3 ✅ | ❌ | not found≈不存在 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 80% | ✅ | 226s |
| imagepull-image-not-found | 4 | L3 ✅ | ✅ | not found≈不存在, definitely-not-existing-rootcause-tag, manifest unknown≈镜像 tag 不存在, registry.k8s.io/pause | - | - | 100% | ✅ | 218s |
| imagepull-image-not-found | 5 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 80% | ✅ | 251s |
| imagepull-image-not-found | 6 | L3 ✅ | ✅ | not found≈不存在, definitely-not-existing-rootcause-tag | - | - | 100% | ✅ | 248s |
| imagepull-image-not-found | 7 | L3 ✅ | ❌ | not found≈缺少 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 209s |
| imagepull-image-not-found | 8 | L3 ✅ | ❌ | not found≈不存在 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 207s |
| imagepull-image-not-found | 9 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 181s |
| imagepull-image-not-found | 10 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | N/A | ✅ | 114s |
| imagepull-image-not-found | 11 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 183s |
| imagepull-image-not-found | 12 | L3 ✅ | ✅ | not found≈不存在, registry.k8s.io/pause | - | - | 100% | ✅ | 383s |
| imagepull-image-not-found | 13 | L3 ✅ | ✅ | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | - | 83% | ✅ | 284s |
| imagepull-image-not-found | 14 | L3 ✅ | ✅ | not found≈不存在, definitely-not-existing-rootcause-tag | - | - | 100% | ✅ | 165s |
| imagepull-image-not-found | 15 | L3 ✅ | ✅ | not found≈不存在, definitely-not-existing-rootcause-tag | - | - | 100% | ✅ | 201s |
| imagepull-image-not-found | 16 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 146s |
| imagepull-image-not-found | 17 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 202s |
| imagepull-image-not-found | 18 | L3 ✅ | ❌ | not found≈不存在 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 197s |
| imagepull-image-not-found | 19 | L3 ✅ | ❌ | not found≈不存在 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 158s |
| imagepull-image-not-found | 20 | L3 ✅ | ❌ | not found≈缺少 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 201s |
| imagepull-image-not-found | 21 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 90% | ✅ | 182s |
| imagepull-image-not-found | 22 | L3 ✅ | ❌ | not found≈不存在 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 150s |
| imagepull-image-not-found | 23 | L3 ✅ | ❌ | not found≈缺少 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 194s |
| imagepull-image-not-found | 24 | L3 ✅ | ✅ | not found≈缺少, registry.k8s.io/pause | - | - | 100% | ✅ | 164s |
| imagepull-image-not-found | 25 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 70% | ✅ | 188s |
| imagepull-image-not-found | 26 | L3 ✅ | ✅ | not found≈不存在, definitely-not-existing-rootcause-tag | - | - | 100% | ✅ | 202s |
| imagepull-image-not-found | 27 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 184s |
| imagepull-image-not-found | 28 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 179s |
| imagepull-image-not-found | 29 | L3 ✅ | ✅ | not found≈不存在, definitely-not-existing-rootcause-tag | - | - | 100% | ✅ | 177s |
| imagepull-image-not-found | 30 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 228s |
| imagepull-image-not-found | 31 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 174s |
| imagepull-image-not-found | 32 | L3 ✅ | ❌ | not found≈不存在 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | unauthorized | N/A | ✅ | 112s |
| imagepull-image-not-found | 33 | L3 ✅ | ❌ | not found≈不存在 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 225s |
| imagepull-image-not-found | 34 | L3 ✅ | ✅ | not found≈不存在, definitely-not-existing-rootcause-tag, manifest unknown | - | - | 80% | ✅ | 415s |
| imagepull-image-not-found | 35 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 374s |
| imagepull-image-not-found | 36 | L3 ✅ | ✅ | not found≈缺失, registry.k8s.io/pause | - | - | 100% | ✅ | 294s |
| imagepull-image-not-found | 37 | L3 ✅ | ❌ | not found≈缺失 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 134s |
| imagepull-image-not-found | 38 | L3 ✅ | ❌ | not found≈缺失 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 212s |
| imagepull-image-not-found | 39 | L3 ✅ | ❌ | not found≈缺失 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 143s |
| imagepull-image-not-found | 40 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 175s |
| imagepull-image-not-found | 41 | L3 ✅ | ❌ | not found≈缺少 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 213s |
| imagepull-image-not-found | 42 | L3 ✅ | ❌ | not found≈缺失 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 78% | ✅ | 154s |
| imagepull-image-not-found | 43 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 181s |
| imagepull-image-not-found | 44 | L3 ✅ | ❌ | not found≈不存在 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 220s |
| imagepull-image-not-found | 45 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 139s |
| imagepull-image-not-found | 46 | L3 ✅ | ✅ | not found≈不存在, definitely-not-existing-rootcause-tag | - | - | 100% | ✅ | 220s |
| imagepull-image-not-found | 47 | L3 ✅ | ✅ | not found≈missing, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | - | 86% | ✅ | 210s |
| imagepull-image-not-found | 48 | L3 ✅ | ❌ | not found≈缺失 | definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 276s |
| imagepull-image-not-found | 49 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 171s |
| imagepull-image-not-found | 50 | L3 ✅ | ❌ | - | not found, definitely-not-existing-rootcause-tag, manifest unknown, registry.k8s.io/pause | - | 100% | ✅ | 173s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| imagepull-image-not-found | imagepull | 30.0% | 100.0% | 96.8% | 2.8m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.8m | ✅ |
| 根因准确率 | >= 60% | 30.0% | ❌ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 96.8% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/imagepull/11-imagepull-image-not-found
