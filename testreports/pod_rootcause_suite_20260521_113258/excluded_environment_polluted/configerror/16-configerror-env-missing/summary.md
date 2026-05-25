# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 77.6m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| configerror-env-missing | 1 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 75% | ❌ | 177s |
| configerror-env-missing | 2 | L3 ❌ | ❌ | - | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ❌ | 173s |
| configerror-env-missing | 3 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 88% | ✅ | 188s |
| configerror-env-missing | 4 | L3 ❌ | ✅ | APP_BOOT_MODE, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ❌ | 186s |
| configerror-env-missing | 5 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 213s |
| configerror-env-missing | 6 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required | - | - | 100% | ✅ | 202s |
| configerror-env-missing | 7 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 237s |
| configerror-env-missing | 8 | L3 ❌ | ❌ | - | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 88% | ❌ | 158s |
| configerror-env-missing | 9 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 123s |
| configerror-env-missing | 10 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 164s |
| configerror-env-missing | 11 | L3 ❌ | ✅ | APP_BOOT_MODE, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 194s |
| configerror-env-missing | 12 | L3 ❌ | ❌ | - | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 50% | ❌ | 155s |
| configerror-env-missing | 13 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required | - | - | 88% | ✅ | 154s |
| configerror-env-missing | 14 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 166s |
| configerror-env-missing | 15 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required | - | - | 100% | ✅ | 167s |
| configerror-env-missing | 16 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 156s |
| configerror-env-missing | 17 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 194s |
| configerror-env-missing | 18 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 208s |
| configerror-env-missing | 19 | L3 ❌ | ❌ | - | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 90% | ✅ | 206s |
| configerror-env-missing | 20 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 175s |
| configerror-env-missing | 21 | L3 ❌ | ❌ | - | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ❌ | 143s |
| configerror-env-missing | 22 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 150s |
| configerror-env-missing | 23 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 86% | ❌ | 131s |
| configerror-env-missing | 24 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 186s |
| configerror-env-missing | 25 | L3 ❌ | ❌ | - | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ❌ | 154s |
| configerror-env-missing | 26 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 217s |
| configerror-env-missing | 27 | L3 ❌ | ❌ | - | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 211s |
| configerror-env-missing | 28 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required | - | - | 75% | ❌ | 215s |
| configerror-env-missing | 29 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 89% | ✅ | 173s |
| configerror-env-missing | 30 | L3 ❌ | ❌ | - | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ❌ | 187s |
| configerror-env-missing | 31 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required | - | - | 67% | ❌ | 444s |
| configerror-env-missing | 32 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 156s |
| configerror-env-missing | 33 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ❌ | 169s |
| configerror-env-missing | 34 | L3 ❌ | ❌ | - | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 83% | ❌ | 137s |
| configerror-env-missing | 35 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required | - | - | 100% | ✅ | 183s |
| configerror-env-missing | 36 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 142s |
| configerror-env-missing | 37 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required | - | - | 100% | ✅ | 149s |
| configerror-env-missing | 38 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required | - | - | 100% | ❌ | 129s |
| configerror-env-missing | 39 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required | - | - | 70% | ❌ | 159s |
| configerror-env-missing | 40 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 226s |
| configerror-env-missing | 41 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required | - | - | 86% | ❌ | 162s |
| configerror-env-missing | 42 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 219s |
| configerror-env-missing | 43 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ❌ | 113s |
| configerror-env-missing | 44 | L0 ❌ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 88% | ❌ | 196s |
| configerror-env-missing | 45 | L3 ❌ | ❌ | - | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ✅ | 138s |
| configerror-env-missing | 46 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required | - | - | 100% | ✅ | 157s |
| configerror-env-missing | 47 | L3 ❌ | ✅ | APP_BOOT_MODE, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ❌ | 171s |
| configerror-env-missing | 48 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ❌ | 165s |
| configerror-env-missing | 49 | L3 ❌ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 164s |
| configerror-env-missing | 50 | L3 ❌ | ❌ | APP_BOOT_MODE | missing required, L4_CONFIG_BOOTSTRAP_FAIL, exit 42 | - | 100% | ❌ | 305s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| configerror-env-missing | configerror | 46.0% | 58.0% | 94.4% | 2.5m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.5m | ✅ |
| 根因准确率 | >= 60% | 46.0% | ❌ |
| Runbook 覆盖率 | >= 60% | 58.0% | ❌ |
| 证据采集率 | >= 60% | 94.4% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/configerror/16-configerror-env-missing
