# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 160.8m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| oomkilled-memory-limit-too-low | 1 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 196s |
| oomkilled-memory-limit-too-low | 2 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 235s |
| oomkilled-memory-limit-too-low | 3 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 511s |
| oomkilled-memory-limit-too-low | 4 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 664s |
| oomkilled-memory-limit-too-low | 5 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 479s |
| oomkilled-memory-limit-too-low | 6 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 466s |
| oomkilled-memory-limit-too-low | 7 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 413s |
| oomkilled-memory-limit-too-low | 8 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 253s |
| oomkilled-memory-limit-too-low | 9 | L2 ✅ | ✅ | OOMKilled, memory limit≈内存限制 | - | - | 100% | ✅ | 337s |
| oomkilled-memory-limit-too-low | 10 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 332s |
| oomkilled-memory-limit-too-low | 11 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 316s |
| oomkilled-memory-limit-too-low | 12 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 60% | ✅ | 573s |
| oomkilled-memory-limit-too-low | 13 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 75% | ✅ | 261s |
| oomkilled-memory-limit-too-low | 14 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 361s |
| oomkilled-memory-limit-too-low | 15 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 401s |
| oomkilled-memory-limit-too-low | 16 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 389s |
| oomkilled-memory-limit-too-low | 17 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 512s |
| oomkilled-memory-limit-too-low | 18 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 350s |
| oomkilled-memory-limit-too-low | 19 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 366s |
| oomkilled-memory-limit-too-low | 20 | L2 ✅ | ✅ | OOMKilled, memory limit≈内存限制 | - | - | 75% | ✅ | 405s |
| oomkilled-memory-limit-too-low | 21 | L2 ✅ | ✅ | OOMKilled, memory limit≈内存限制 | - | - | 100% | ✅ | 312s |
| oomkilled-memory-limit-too-low | 22 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 67% | ✅ | 690s |
| oomkilled-memory-limit-too-low | 23 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 371s |
| oomkilled-memory-limit-too-low | 24 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 80% | ✅ | 410s |
| oomkilled-memory-limit-too-low | 25 | L2 ✅ | ✅ | OOMKilled, memory limit≈资源限制 | - | - | 100% | ✅ | 350s |
| oomkilled-memory-limit-too-low | 26 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 447s |
| oomkilled-memory-limit-too-low | 27 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 312s |
| oomkilled-memory-limit-too-low | 28 | L2 ✅ | ✅ | OOMKilled, memory limit≈内存限制 | - | - | 100% | ✅ | 378s |
| oomkilled-memory-limit-too-low | 29 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 520s |
| oomkilled-memory-limit-too-low | 30 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 347s |
| oomkilled-memory-limit-too-low | 31 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 354s |
| oomkilled-memory-limit-too-low | 32 | L2 ✅ | ✅ | OOMKilled, Exit Code: 137 | - | - | 100% | ✅ | 601s |
| oomkilled-memory-limit-too-low | 33 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 256s |
| oomkilled-memory-limit-too-low | 34 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 345s |
| oomkilled-memory-limit-too-low | 35 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 374s |
| oomkilled-memory-limit-too-low | 36 | L2 ✅ | ✅ | OOMKilled, memory limit≈内存限制 | - | - | 100% | ✅ | 310s |
| oomkilled-memory-limit-too-low | 37 | L2 ✅ | ✅ | OOMKilled, memory limit≈内存 limit | - | - | 80% | ✅ | 570s |
| oomkilled-memory-limit-too-low | 38 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 324s |
| oomkilled-memory-limit-too-low | 39 | L2 ✅ | ✅ | OOMKilled, Exit Code: 137 | - | - | 100% | ✅ | 314s |
| oomkilled-memory-limit-too-low | 40 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 222s |
| oomkilled-memory-limit-too-low | 41 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 302s |
| oomkilled-memory-limit-too-low | 42 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 75% | ✅ | 352s |
| oomkilled-memory-limit-too-low | 43 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 309s |
| oomkilled-memory-limit-too-low | 44 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 370s |
| oomkilled-memory-limit-too-low | 45 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 402s |
| oomkilled-memory-limit-too-low | 46 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 374s |
| oomkilled-memory-limit-too-low | 47 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 80% | ✅ | 482s |
| oomkilled-memory-limit-too-low | 48 | L2 ✅ | ✅ | OOMKilled, memory limit≈内存限制 | - | - | 100% | ✅ | 318s |
| oomkilled-memory-limit-too-low | 49 | L2 ✅ | ✅ | OOMKilled, memory limit≈内存限制 | - | - | 100% | ✅ | 397s |
| oomkilled-memory-limit-too-low | 50 | L2 ✅ | ✅ | OOMKilled, memory limit | - | - | 100% | ✅ | 345s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| oomkilled-memory-limit-too-low | oomkilled | 100.0% | 100.0% | 95.8% | 6.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 6.0m | ✅ |
| 根因准确率 | >= 60% | 100.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 95.8% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/oomkilled/19-oomkilled-memory-limit-too-low
