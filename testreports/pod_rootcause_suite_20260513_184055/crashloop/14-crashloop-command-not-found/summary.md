# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 179.1m
- 人工语义修正: 7 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| crashloop-command-not-found | 1 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 385s |
| crashloop-command-not-found | 2 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 426s |
| crashloop-command-not-found | 3 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 398s |
| crashloop-command-not-found | 4 | L2 ✅ | ✅ | command not found, not found | - | - | 100% | ✅ | 370s |
| crashloop-command-not-found | 5 | L2 ✅ | ✅ | definitely-missing-command-for-rootcause, not found, 语义等价修正: 启动命令不存在 等价 command not found | - | - | 75% | ✅ | 376s |
| crashloop-command-not-found | 6 | L2 ✅ | ✅ | definitely-missing-command-for-rootcause, not found, 语义等价修正: 启动命令不存在 等价 command not found | - | - | 75% | ✅ | 361s |
| crashloop-command-not-found | 7 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 50% | ✅ | 386s |
| crashloop-command-not-found | 8 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 75% | ✅ | 374s |
| crashloop-command-not-found | 9 | L2 ✅ | ✅ | command not found, not found | - | - | 75% | ✅ | 419s |
| crashloop-command-not-found | 10 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 379s |
| crashloop-command-not-found | 11 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 75% | ✅ | 528s |
| crashloop-command-not-found | 12 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 443s |
| crashloop-command-not-found | 13 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 67% | ✅ | 369s |
| crashloop-command-not-found | 14 | L2 ✅ | ✅ | command not found, not found | - | - | 50% | ✅ | 409s |
| crashloop-command-not-found | 15 | L2 ✅ | ✅ | command not found, not found | - | - | 75% | ✅ | 403s |
| crashloop-command-not-found | 16 | L2 ✅ | ✅ | definitely-missing-command-for-rootcause, not found, 语义等价修正: 启动命令不存在 等价 command not found | - | - | 100% | ✅ | 554s |
| crashloop-command-not-found | 17 | L2 ✅ | ✅ | command not found, not found | - | - | 67% | ✅ | 300s |
| crashloop-command-not-found | 18 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 443s |
| crashloop-command-not-found | 19 | L2 ✅ | ✅ | command not found, not found | - | - | 50% | ✅ | 446s |
| crashloop-command-not-found | 20 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 75% | ✅ | 372s |
| crashloop-command-not-found | 21 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 75% | ✅ | 579s |
| crashloop-command-not-found | 22 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 50% | ✅ | 330s |
| crashloop-command-not-found | 23 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 2020s |
| crashloop-command-not-found | 24 | L2 ✅ | ✅ | definitely-missing-command-for-rootcause, 语义等价修正: 启动命令不存在 等价 command not found | - | - | 100% | ✅ | 336s |
| crashloop-command-not-found | 25 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 50% | ✅ | 268s |
| crashloop-command-not-found | 26 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 286s |
| crashloop-command-not-found | 27 | L2 ✅ | ✅ | command not found, not found | - | - | 75% | ✅ | 343s |
| crashloop-command-not-found | 28 | L2 ✅ | ✅ | command not found, not found | - | - | 75% | ✅ | 304s |
| crashloop-command-not-found | 29 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 75% | ✅ | 450s |
| crashloop-command-not-found | 30 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 504s |
| crashloop-command-not-found | 31 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 67% | ✅ | 378s |
| crashloop-command-not-found | 32 | L2 ✅ | ✅ | definitely-missing-command-for-rootcause, not found, 语义等价修正: 启动命令不存在 等价 command not found | - | - | 75% | ✅ | 408s |
| crashloop-command-not-found | 33 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 363s |
| crashloop-command-not-found | 34 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 394s |
| crashloop-command-not-found | 35 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 379s |
| crashloop-command-not-found | 36 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 75% | ✅ | 372s |
| crashloop-command-not-found | 37 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 75% | ✅ | 413s |
| crashloop-command-not-found | 38 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 75% | ✅ | 360s |
| crashloop-command-not-found | 39 | L2 ✅ | ✅ | definitely-missing-command-for-rootcause, not found, 语义等价修正: 启动命令不存在 等价 command not found | - | - | 100% | ✅ | 436s |
| crashloop-command-not-found | 40 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 50% | ✅ | 437s |
| crashloop-command-not-found | 41 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 478s |
| crashloop-command-not-found | 42 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 67% | ✅ | 245s |
| crashloop-command-not-found | 43 | L2 ✅ | ✅ | command not found, not found | - | - | 100% | ✅ | 377s |
| crashloop-command-not-found | 44 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 100% | ✅ | 376s |
| crashloop-command-not-found | 45 | L2 ✅ | ✅ | command not found, not found | - | - | 75% | ✅ | 386s |
| crashloop-command-not-found | 46 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 75% | ✅ | 512s |
| crashloop-command-not-found | 47 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 75% | ✅ | 495s |
| crashloop-command-not-found | 48 | L2 ✅ | ✅ | definitely-missing-command-for-rootcause, not found, 语义等价修正: 启动命令不存在 等价 command not found | - | - | 100% | ✅ | 399s |
| crashloop-command-not-found | 49 | L2 ✅ | ✅ | command not found, not found | - | - | 100% | ✅ | 323s |
| crashloop-command-not-found | 50 | L2 ✅ | ✅ | command not found, definitely-missing-command-for-rootcause, not found | - | - | 75% | ✅ | 324s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| crashloop-command-not-found | crashloop | 100.0% | 100.0% | 81.8% | 6.7m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 6.7m | ✅ |
| 根因准确率 | >= 60% | 100.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 81.8% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/crashloop/14-crashloop-command-not-found
