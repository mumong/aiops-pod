# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 73.3m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| crashloop-exit-code-nonzero | 1 | L3 ❌ | ❌ | - | Exit Code, exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ✅ | 256s |
| crashloop-exit-code-nonzero | 2 | L3 ❌ | ❌ | - | Exit Code, exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ✅ | 128s |
| crashloop-exit-code-nonzero | 3 | L3 ❌ | ❌ | exit 2, Exit Code: 2≈exit 2 | Exit Code | - | 100% | ✅ | 182s |
| crashloop-exit-code-nonzero | 4 | L3 ❌ | ✅ | Exit Code, exit 2, Exit Code: 2≈exit 2, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 169s |
| crashloop-exit-code-nonzero | 5 | L3 ❌ | ✅ | Exit Code≈退出码, Exit Code: 2≈退出码 2, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 144s |
| crashloop-exit-code-nonzero | 6 | L3 ❌ | ❌ | - | Exit Code, exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ✅ | 133s |
| crashloop-exit-code-nonzero | 7 | L3 ❌ | ❌ | - | Exit Code, exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 57% | ✅ | 127s |
| crashloop-exit-code-nonzero | 8 | L3 ❌ | ✅ | Exit Code, Exit Code: 2≈退出码为 2, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 155s |
| crashloop-exit-code-nonzero | 9 | L3 ❌ | ✅ | Exit Code≈退出码, Exit Code: 2≈退出码 2 | - | - | 100% | ❌ | 118s |
| crashloop-exit-code-nonzero | 10 | L3 ❌ | ✅ | Exit Code≈退出码, Exit Code: 2≈退出码 2 | - | - | 88% | ❌ | 225s |
| crashloop-exit-code-nonzero | 11 | L3 ❌ | ✅ | Exit Code≈退出码, Exit Code: 2≈退出码为 2 | - | - | 100% | ✅ | 221s |
| crashloop-exit-code-nonzero | 12 | L3 ❌ | ✅ | Exit Code≈退出码, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 156s |
| crashloop-exit-code-nonzero | 13 | L3 ❌ | ❌ | Exit Code | exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ❌ | 123s |
| crashloop-exit-code-nonzero | 14 | L3 ❌ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 347s |
| crashloop-exit-code-nonzero | 15 | L3 ❌ | ❌ | RUNTIME_STARTUP_ERROR | Exit Code | - | 100% | ✅ | 296s |
| crashloop-exit-code-nonzero | 16 | L3 ❌ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 88% | ✅ | 454s |
| crashloop-exit-code-nonzero | 17 | L3 ❌ | ❌ | Exit Code | exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 88% | ✅ | 169s |
| crashloop-exit-code-nonzero | 18 | L3 ❌ | ✅ | Exit Code≈退出码, Exit Code: 2≈退出码 2 | - | - | 86% | ✅ | 155s |
| crashloop-exit-code-nonzero | 19 | L3 ❌ | ❌ | Exit Code | exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ✅ | 116s |
| crashloop-exit-code-nonzero | 20 | L3 ❌ | ✅ | Exit Code≈退出码, Exit Code: 2≈退出码 2, RUNTIME_STARTUP_ERROR | - | - | 90% | ✅ | 186s |
| crashloop-exit-code-nonzero | 21 | L3 ❌ | ❌ | Exit Code | exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 29% | ✅ | 124s |
| crashloop-exit-code-nonzero | 22 | L3 ❌ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 89% | ✅ | 163s |
| crashloop-exit-code-nonzero | 23 | L3 ❌ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 150s |
| crashloop-exit-code-nonzero | 24 | L3 ❌ | ✅ | Exit Code, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | - | 100% | ❌ | 123s |
| crashloop-exit-code-nonzero | 25 | L3 ❌ | ❌ | Exit Code | exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ❌ | 111s |
| crashloop-exit-code-nonzero | 26 | L3 ❌ | ✅ | Exit Code, exit 2, Exit Code: 2 | - | - | 100% | ✅ | 126s |
| crashloop-exit-code-nonzero | 27 | L3 ❌ | ✅ | Exit Code, exit 2, Exit Code: 2≈exit 2 | - | - | 100% | ✅ | 176s |
| crashloop-exit-code-nonzero | 28 | L3 ❌ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 134s |
| crashloop-exit-code-nonzero | 29 | L3 ❌ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 201s |
| crashloop-exit-code-nonzero | 30 | L3 ❌ | ❌ | - | Exit Code, exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 86% | ✅ | 149s |
| crashloop-exit-code-nonzero | 31 | L3 ❌ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 142s |
| crashloop-exit-code-nonzero | 32 | L3 ❌ | ❌ | Exit Code | exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ✅ | 211s |
| crashloop-exit-code-nonzero | 33 | L3 ❌ | ✅ | Exit Code, exit 2, Exit Code: 2≈exit 2 | - | - | 100% | ✅ | 194s |
| crashloop-exit-code-nonzero | 34 | L3 ❌ | ❌ | - | Exit Code, exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ❌ | 135s |
| crashloop-exit-code-nonzero | 35 | L3 ❌ | ✅ | Exit Code≈退出码, Exit Code: 2≈退出码 2 | - | - | 100% | ❌ | 131s |
| crashloop-exit-code-nonzero | 36 | L3 ❌ | ✅ | Exit Code≈退出码, Exit Code: 2≈退出码为 2 | - | - | 100% | ❌ | 141s |
| crashloop-exit-code-nonzero | 37 | L3 ❌ | ❌ | - | Exit Code, exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ✅ | 135s |
| crashloop-exit-code-nonzero | 38 | L3 ❌ | ❌ | Exit Code≈退出码 | exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ✅ | 190s |
| crashloop-exit-code-nonzero | 39 | L0 ❌ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 90% | ✅ | 209s |
| crashloop-exit-code-nonzero | 40 | L3 ❌ | ❌ | Exit Code≈退出码 | exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ❌ | 180s |
| crashloop-exit-code-nonzero | 41 | L3 ❌ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 135s |
| crashloop-exit-code-nonzero | 42 | L3 ❌ | ✅ | Exit Code, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 165s |
| crashloop-exit-code-nonzero | 43 | L3 ❌ | ❌ | - | Exit Code, exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ✅ | 204s |
| crashloop-exit-code-nonzero | 44 | L3 ❌ | ✅ | Exit Code≈退出码, Exit Code: 2≈退出码 2 | - | - | 100% | ❌ | 155s |
| crashloop-exit-code-nonzero | 45 | L3 ❌ | ❌ | RUNTIME_STARTUP_ERROR | Exit Code | - | 100% | ✅ | 137s |
| crashloop-exit-code-nonzero | 46 | L3 ❌ | ❌ | Exit Code | exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 86% | ✅ | 180s |
| crashloop-exit-code-nonzero | 47 | L3 ❌ | ✅ | Exit Code≈退出码, Exit Code: 2≈退出码为 2 | - | - | 86% | ❌ | 156s |
| crashloop-exit-code-nonzero | 48 | L3 ❌ | ✅ | Exit Code≈退出码, Exit Code: 2≈退出码为 2, RUNTIME_STARTUP_ERROR | - | - | 86% | ✅ | 154s |
| crashloop-exit-code-nonzero | 49 | L3 ❌ | ✅ | Exit Code, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 167s |
| crashloop-exit-code-nonzero | 50 | L3 ❌ | ❌ | - | Exit Code, exit 2, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | 100% | ✅ | 221s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| crashloop-exit-code-nonzero | crashloop | 58.0% | 78.0% | 94.9% | 2.4m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.4m | ✅ |
| 根因准确率 | >= 60% | 58.0% | ❌ |
| Runbook 覆盖率 | >= 60% | 78.0% | ✅ |
| 证据采集率 | >= 60% | 94.9% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/crashloop/13-crashloop-exit-code-nonzero
