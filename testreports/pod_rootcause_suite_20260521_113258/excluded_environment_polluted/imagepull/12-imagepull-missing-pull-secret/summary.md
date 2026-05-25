# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 79.4m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| imagepull-missing-pull-secret | 1 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 172s |
| imagepull-missing-pull-secret | 2 | L3 ✅ | ✅ | secret, pull secret≈imagepullsecret | - | - | 100% | ✅ | 306s |
| imagepull-missing-pull-secret | 3 | L3 ✅ | ✅ | secret, pull secret≈imagepullsecret | - | - | 100% | ✅ | 170s |
| imagepull-missing-pull-secret | 4 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 146s |
| imagepull-missing-pull-secret | 5 | L3 ✅ | ✅ | secret, pull secret≈imagepullsecret | - | - | 100% | ✅ | 154s |
| imagepull-missing-pull-secret | 6 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 86% | ✅ | 148s |
| imagepull-missing-pull-secret | 7 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 88% | ✅ | 184s |
| imagepull-missing-pull-secret | 8 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret≈imagepullsecret | - | - | 90% | ✅ | 135s |
| imagepull-missing-pull-secret | 9 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret, pull secret≈imagepullsecret | - | - | 100% | ✅ | 125s |
| imagepull-missing-pull-secret | 10 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret≈imagepullsecret | - | - | 88% | ✅ | 189s |
| imagepull-missing-pull-secret | 11 | L3 ✅ | ❌ | - | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 129s |
| imagepull-missing-pull-secret | 12 | L3 ✅ | ❌ | - | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 263s |
| imagepull-missing-pull-secret | 13 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 252s |
| imagepull-missing-pull-secret | 14 | L3 ✅ | ✅ | secret, imagePullSecrets, pull secret≈imagepullsecret | - | - | 100% | ✅ | 138s |
| imagepull-missing-pull-secret | 15 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 240s |
| imagepull-missing-pull-secret | 16 | L3 ✅ | ❌ | secret, imagePullSecrets, pull secret≈imagepullsecret | - | manifest unknown | 100% | ✅ | 183s |
| imagepull-missing-pull-secret | 17 | L3 ✅ | ❌ | - | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 147s |
| imagepull-missing-pull-secret | 18 | L3 ✅ | ✅ | secret, pull secret≈imagepullsecret | - | - | 100% | ✅ | 203s |
| imagepull-missing-pull-secret | 19 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 127s |
| imagepull-missing-pull-secret | 20 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 200s |
| imagepull-missing-pull-secret | 21 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret | - | - | 100% | ✅ | 182s |
| imagepull-missing-pull-secret | 22 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 80% | ✅ | 137s |
| imagepull-missing-pull-secret | 23 | L3 ✅ | ✅ | secret, imagePullSecrets, pull secret≈imagepullsecret | - | - | 100% | ✅ | 165s |
| imagepull-missing-pull-secret | 24 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 138s |
| imagepull-missing-pull-secret | 25 | L3 ✅ | ❌ | - | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 181s |
| imagepull-missing-pull-secret | 26 | L3 ✅ | ✅ | secret, pull secret≈imagepullsecret | - | - | 88% | ✅ | 187s |
| imagepull-missing-pull-secret | 27 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 150s |
| imagepull-missing-pull-secret | 28 | L3 ✅ | ❌ | - | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 88% | ✅ | 174s |
| imagepull-missing-pull-secret | 29 | L3 ✅ | ✅ | secret, pull secret≈imagepullsecret | - | - | 100% | ✅ | 167s |
| imagepull-missing-pull-secret | 30 | L3 ✅ | ❌ | - | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 83% | ✅ | 142s |
| imagepull-missing-pull-secret | 31 | L3 ✅ | ✅ | secret, imagePullSecrets, pull secret≈imagepullsecret | - | - | 100% | ✅ | 188s |
| imagepull-missing-pull-secret | 32 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 132s |
| imagepull-missing-pull-secret | 33 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret, pull secret≈拉取密钥 | - | - | 100% | ✅ | 247s |
| imagepull-missing-pull-secret | 34 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 262s |
| imagepull-missing-pull-secret | 35 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 422s |
| imagepull-missing-pull-secret | 36 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 408s |
| imagepull-missing-pull-secret | 37 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret≈imagepullsecret | - | - | 88% | ✅ | 143s |
| imagepull-missing-pull-secret | 38 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 335s |
| imagepull-missing-pull-secret | 39 | L3 ✅ | ✅ | secret, pull secret≈imagepullsecret | - | - | 100% | ✅ | 239s |
| imagepull-missing-pull-secret | 40 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 88% | ✅ | 226s |
| imagepull-missing-pull-secret | 41 | L3 ✅ | ✅ | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret≈imagepullsecret | - | - | 100% | ✅ | 155s |
| imagepull-missing-pull-secret | 42 | L3 ✅ | ❌ | - | secret, rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 167s |
| imagepull-missing-pull-secret | 43 | L3 ✅ | ✅ | secret, imagePullSecrets, pull secret≈imagepullsecret | - | - | 100% | ✅ | 116s |
| imagepull-missing-pull-secret | 44 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 137s |
| imagepull-missing-pull-secret | 45 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 78% | ✅ | 138s |
| imagepull-missing-pull-secret | 46 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 238s |
| imagepull-missing-pull-secret | 47 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 162s |
| imagepull-missing-pull-secret | 48 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 100% | ✅ | 178s |
| imagepull-missing-pull-secret | 49 | L3 ✅ | ❌ | secret | rc-definitely-missing-pull-secret, imagePullSecrets, pull secret | - | 86% | ✅ | 224s |
| imagepull-missing-pull-secret | 50 | L3 ✅ | ✅ | secret, imagePullSecrets, pull secret≈imagepullsecret | - | - | 100% | ✅ | 141s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| imagepull-missing-pull-secret | imagepull | 38.0% | 100.0% | 96.6% | 2.7m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.7m | ✅ |
| 根因准确率 | >= 60% | 38.0% | ❌ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 96.6% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/imagepull/12-imagepull-missing-pull-secret
