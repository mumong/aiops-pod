# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 176.4m
- 人工语义修正: 9 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| crashloop-exit-code-nonzero | 1 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 455s |
| crashloop-exit-code-nonzero | 2 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 360s |
| crashloop-exit-code-nonzero | 3 | L2 ✅ | ✅ | Exit Code, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | - | 75% | ✅ | 415s |
| crashloop-exit-code-nonzero | 4 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 75% | ✅ | 409s |
| crashloop-exit-code-nonzero | 5 | L2 ✅ | ✅ | RUNTIME_STARTUP_ERROR, 语义等价修正: 退出码为2 等价 Exit Code 2 | - | - | 100% | ✅ | 389s |
| crashloop-exit-code-nonzero | 6 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 509s |
| crashloop-exit-code-nonzero | 7 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 321s |
| crashloop-exit-code-nonzero | 8 | L2 ✅ | ✅ | RUNTIME_STARTUP_ERROR, 语义等价修正: 退出码为2 等价 Exit Code 2 | - | - | 100% | ✅ | 395s |
| crashloop-exit-code-nonzero | 9 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 469s |
| crashloop-exit-code-nonzero | 10 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 513s |
| crashloop-exit-code-nonzero | 11 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 302s |
| crashloop-exit-code-nonzero | 12 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 367s |
| crashloop-exit-code-nonzero | 13 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 331s |
| crashloop-exit-code-nonzero | 14 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 375s |
| crashloop-exit-code-nonzero | 15 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 471s |
| crashloop-exit-code-nonzero | 16 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 407s |
| crashloop-exit-code-nonzero | 17 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 458s |
| crashloop-exit-code-nonzero | 18 | L2 ✅ | ✅ | Exit Code, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 322s |
| crashloop-exit-code-nonzero | 19 | L2 ✅ | ✅ | Exit Code, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 262s |
| crashloop-exit-code-nonzero | 20 | L2 ✅ | ✅ | Exit Code, 语义等价修正: 退出码为2 等价 Exit Code 2 | - | - | 100% | ✅ | 412s |
| crashloop-exit-code-nonzero | 21 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 447s |
| crashloop-exit-code-nonzero | 22 | L2 ✅ | ✅ | RUNTIME_STARTUP_ERROR, 语义等价修正: 退出码为2 等价 Exit Code 2 | - | - | 100% | ✅ | 515s |
| crashloop-exit-code-nonzero | 23 | L2 ✅ | ✅ | Exit Code, Exit Code: 2 | - | - | 75% | ✅ | 407s |
| crashloop-exit-code-nonzero | 24 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 413s |
| crashloop-exit-code-nonzero | 25 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 635s |
| crashloop-exit-code-nonzero | 26 | L2 ✅ | ✅ | Exit Code, 语义等价修正: 退出码为2 等价 Exit Code 2 | - | - | 100% | ✅ | 333s |
| crashloop-exit-code-nonzero | 27 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 395s |
| crashloop-exit-code-nonzero | 28 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 504s |
| crashloop-exit-code-nonzero | 29 | L2 ✅ | ✅ | 语义等价修正: 退出码为2 等价 Exit Code 2 | - | - | 75% | ✅ | 393s |
| crashloop-exit-code-nonzero | 30 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 392s |
| crashloop-exit-code-nonzero | 31 | L2 ✅ | ✅ | Exit Code, Exit Code: 2, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 407s |
| crashloop-exit-code-nonzero | 32 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 239s |
| crashloop-exit-code-nonzero | 33 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 452s |
| crashloop-exit-code-nonzero | 34 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 496s |
| crashloop-exit-code-nonzero | 35 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 456s |
| crashloop-exit-code-nonzero | 36 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 436s |
| crashloop-exit-code-nonzero | 37 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 444s |
| crashloop-exit-code-nonzero | 38 | L2 ✅ | ✅ | RUNTIME_STARTUP_ERROR, 语义等价修正: 退出码为2 等价 Exit Code 2 | - | - | 50% | ✅ | 479s |
| crashloop-exit-code-nonzero | 39 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 456s |
| crashloop-exit-code-nonzero | 40 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 413s |
| crashloop-exit-code-nonzero | 41 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 472s |
| crashloop-exit-code-nonzero | 42 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 441s |
| crashloop-exit-code-nonzero | 43 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 446s |
| crashloop-exit-code-nonzero | 44 | L2 ✅ | ✅ | RUNTIME_STARTUP_ERROR, 语义等价修正: 退出码为2 等价 Exit Code 2 | - | - | 100% | ✅ | 623s |
| crashloop-exit-code-nonzero | 45 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 568s |
| crashloop-exit-code-nonzero | 46 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 327s |
| crashloop-exit-code-nonzero | 47 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 425s |
| crashloop-exit-code-nonzero | 48 | L2 ✅ | ✅ | Exit Code, 语义等价修正: 退出码为2 等价 Exit Code 2 | - | - | 100% | ✅ | 364s |
| crashloop-exit-code-nonzero | 49 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 395s |
| crashloop-exit-code-nonzero | 50 | L2 ✅ | ✅ | Exit Code, RUNTIME_STARTUP_ERROR | - | - | 100% | ✅ | 422s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| crashloop-exit-code-nonzero | crashloop | 100.0% | 100.0% | 97.0% | 6.5m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 6.5m | ✅ |
| 根因准确率 | >= 60% | 100.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 97.0% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/crashloop/13-crashloop-exit-code-nonzero
