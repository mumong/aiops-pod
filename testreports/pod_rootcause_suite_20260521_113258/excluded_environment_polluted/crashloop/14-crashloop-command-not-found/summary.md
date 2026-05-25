# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 71.9m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| crashloop-command-not-found | 1 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 78% | ✅ | 183s |
| crashloop-command-not-found | 2 | L3 ❌ | ✅ | command not found, not found | - | - | 100% | ❌ | 151s |
| crashloop-command-not-found | 3 | L3 ❌ | ✅ | command not found, not found | - | - | 100% | ✅ | 159s |
| crashloop-command-not-found | 4 | L3 ❌ | ✅ | command not found≈命令不存在, definitely-missing-command-for-rootcause, not found | - | - | 90% | ✅ | 174s |
| crashloop-command-not-found | 5 | L3 ❌ | ❌ | definitely-missing-command-for-rootcause, not found≈missing | command not found | - | 83% | ❌ | 176s |
| crashloop-command-not-found | 6 | L3 ❌ | ❌ | - | command not found, definitely-missing-command-for-rootcause, not found | - | 100% | ✅ | 128s |
| crashloop-command-not-found | 7 | L3 ❌ | ✅ | command not found≈命令不存在, not found≈不存在 | - | - | 100% | ✅ | 202s |
| crashloop-command-not-found | 8 | L3 ❌ | ✅ | command not found, not found | - | - | 71% | ✅ | 131s |
| crashloop-command-not-found | 9 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 192s |
| crashloop-command-not-found | 10 | L3 ❌ | ✅ | command not found≈命令不存在, not found≈不存在 | - | - | 100% | ✅ | 188s |
| crashloop-command-not-found | 11 | L3 ❌ | ✅ | command not found≈命令未找到, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 157s |
| crashloop-command-not-found | 12 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 88% | ✅ | 260s |
| crashloop-command-not-found | 13 | L3 ❌ | ✅ | command not found≈命令不存在, definitely-missing-command-for-rootcause, not found≈missing | - | - | 89% | ✅ | 182s |
| crashloop-command-not-found | 14 | L3 ❌ | ❌ | definitely-missing-command-for-rootcause, not found≈missing | command not found | - | 75% | ✅ | 180s |
| crashloop-command-not-found | 15 | L3 ❌ | ❌ | not found≈缺失 | command not found | - | 100% | ✅ | 177s |
| crashloop-command-not-found | 16 | L3 ❌ | ❌ | - | command not found, definitely-missing-command-for-rootcause, not found | - | 86% | ✅ | 148s |
| crashloop-command-not-found | 17 | L3 ❌ | ✅ | command not found, not found | - | - | 100% | ❌ | 138s |
| crashloop-command-not-found | 18 | L3 ❌ | ✅ | command not found, not found | - | - | 100% | ✅ | 251s |
| crashloop-command-not-found | 19 | L0 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 88% | ✅ | 145s |
| crashloop-command-not-found | 20 | L3 ❌ | ✅ | command not found, not found | - | - | 100% | ✅ | 136s |
| crashloop-command-not-found | 21 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 141s |
| crashloop-command-not-found | 22 | L3 ❌ | ✅ | command not found≈命令未找到, definitely-missing-command-for-rootcause, not found | - | - | 88% | ✅ | 145s |
| crashloop-command-not-found | 23 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 86% | ✅ | 246s |
| crashloop-command-not-found | 24 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 89% | ✅ | 233s |
| crashloop-command-not-found | 25 | L3 ❌ | ❌ | definitely-missing-command-for-rootcause, not found≈missing | command not found | - | 86% | ✅ | 159s |
| crashloop-command-not-found | 26 | L3 ❌ | ✅ | command not found, not found | - | - | 100% | ❌ | 130s |
| crashloop-command-not-found | 27 | L3 ❌ | ✅ | command not found, not found | - | - | 86% | ✅ | 133s |
| crashloop-command-not-found | 28 | L3 ❌ | ✅ | command not found≈命令未找到, definitely-missing-command-for-rootcause, not found≈missing | - | - | 100% | ✅ | 190s |
| crashloop-command-not-found | 29 | L3 ❌ | ✅ | command not found, not found | - | - | 62% | ✅ | 142s |
| crashloop-command-not-found | 30 | L3 ❌ | ✅ | command not found≈命令未找到, not found | - | - | 100% | ✅ | 155s |
| crashloop-command-not-found | 31 | L3 ❌ | ❌ | - | command not found, definitely-missing-command-for-rootcause, not found | - | 88% | ❌ | 159s |
| crashloop-command-not-found | 32 | L3 ❌ | ❌ | - | command not found, definitely-missing-command-for-rootcause, not found | - | 86% | ✅ | 166s |
| crashloop-command-not-found | 33 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ❌ | 204s |
| crashloop-command-not-found | 34 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 88% | ✅ | 149s |
| crashloop-command-not-found | 35 | L3 ❌ | ❌ | not found≈缺少 | command not found | - | 100% | ✅ | 137s |
| crashloop-command-not-found | 36 | L3 ❌ | ❌ | definitely-missing-command-for-rootcause, not found | command not found | - | 100% | ✅ | 137s |
| crashloop-command-not-found | 37 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 86% | ✅ | 141s |
| crashloop-command-not-found | 38 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 86% | ✅ | 130s |
| crashloop-command-not-found | 39 | L3 ❌ | ✅ | command not found≈命令未找到, not found≈未找到 | - | - | 100% | ❌ | 120s |
| crashloop-command-not-found | 40 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 88% | ✅ | 255s |
| crashloop-command-not-found | 41 | L3 ❌ | ✅ | command not found≈命令不存在, not found≈不存在 | - | - | 88% | ✅ | 271s |
| crashloop-command-not-found | 42 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 88% | ✅ | 168s |
| crashloop-command-not-found | 43 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 86% | ✅ | 130s |
| crashloop-command-not-found | 44 | L3 ❌ | ✅ | command not found≈找不到命令, definitely-missing-command-for-rootcause, not found | - | - | 100% | ❌ | 245s |
| crashloop-command-not-found | 45 | L3 ❌ | ✅ | command not found, not found | - | - | 100% | ❌ | 182s |
| crashloop-command-not-found | 46 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 86% | ✅ | 151s |
| crashloop-command-not-found | 47 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 86% | ✅ | 151s |
| crashloop-command-not-found | 48 | L3 ❌ | ❌ | definitely-missing-command-for-rootcause, not found | command not found | - | 78% | ✅ | 136s |
| crashloop-command-not-found | 49 | L3 ❌ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 83% | ❌ | 142s |
| crashloop-command-not-found | 50 | L3 ❌ | ✅ | command not found≈命令未找到, definitely-missing-command-for-rootcause, not found | - | - | 86% | ✅ | 176s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| crashloop-command-not-found | crashloop | 78.0% | 80.0% | 90.8% | 2.4m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.4m | ✅ |
| 根因准确率 | >= 60% | 78.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 80.0% | ✅ |
| 证据采集率 | >= 60% | 90.8% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/crashloop/14-crashloop-command-not-found
