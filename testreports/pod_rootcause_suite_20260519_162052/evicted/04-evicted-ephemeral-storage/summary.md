# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 163.9m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| evicted-ephemeral-storage | 1 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 67% | ✅ | 295s |
| evicted-ephemeral-storage | 2 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 100% | ✅ | 798s |
| evicted-ephemeral-storage | 3 | L0 ✅ | ✅ | Evicted, ephemeral-storage≈临时存储, emptyDir | - | - | 75% | ✅ | 385s |
| evicted-ephemeral-storage | 4 | L0 ✅ | ✅ | Evicted, ephemeral-storage≈临时存储, emptyDir, sizeLimit | - | - | 50% | ✅ | 387s |
| evicted-ephemeral-storage | 5 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 67% | ✅ | 291s |
| evicted-ephemeral-storage | 6 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir | - | - | 100% | ✅ | 428s |
| evicted-ephemeral-storage | 7 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 100% | ✅ | 357s |
| evicted-ephemeral-storage | 8 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 75% | ✅ | 440s |
| evicted-ephemeral-storage | 9 | L0 ✅ | ❌ | Evicted, ephemeral-storage, emptyDir | - | OOMKilled | 40% | ✅ | 396s |
| evicted-ephemeral-storage | 10 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 100% | ✅ | 362s |
| evicted-ephemeral-storage | 11 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 100% | ✅ | 281s |
| evicted-ephemeral-storage | 12 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 100% | ✅ | 329s |
| evicted-ephemeral-storage | 13 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir | - | - | 100% | ✅ | 307s |
| evicted-ephemeral-storage | 14 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 100% | ✅ | 453s |
| evicted-ephemeral-storage | 15 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 100% | ✅ | 506s |
| evicted-ephemeral-storage | 16 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir, sizeLimit | - | - | 100% | ✅ | 457s |
| evicted-ephemeral-storage | 17 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir, sizeLimit | - | - | 80% | ✅ | 494s |
| evicted-ephemeral-storage | 18 | L0 ✅ | ✅ | Evicted, ephemeral-storage≈ephemeral storage | - | - | 67% | ✅ | 366s |
| evicted-ephemeral-storage | 19 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 40% | ✅ | 406s |
| evicted-ephemeral-storage | 20 | L0 ✅ | ❌ | Evicted, ephemeral-storage, emptyDir, sizeLimit | - | OOMKilled | 40% | ✅ | 467s |
| evicted-ephemeral-storage | 21 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 33% | ✅ | 304s |
| evicted-ephemeral-storage | 22 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 50% | ✅ | 309s |
| evicted-ephemeral-storage | 23 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 33% | ✅ | 324s |
| evicted-ephemeral-storage | 24 | L0 ✅ | ❌ | Evicted, ephemeral-storage | - | OOMKilled | 40% | ✅ | 377s |
| evicted-ephemeral-storage | 25 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 75% | ✅ | 594s |
| evicted-ephemeral-storage | 26 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir | - | - | 100% | ✅ | 323s |
| evicted-ephemeral-storage | 27 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir | - | - | 100% | ✅ | 308s |
| evicted-ephemeral-storage | 28 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir | - | - | 100% | ✅ | 269s |
| evicted-ephemeral-storage | 29 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 100% | ✅ | 362s |
| evicted-ephemeral-storage | 30 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 75% | ✅ | 404s |
| evicted-ephemeral-storage | 31 | L0 ✅ | ✅ | Evicted, ephemeral-storage, sizeLimit | - | - | 75% | ✅ | 369s |
| evicted-ephemeral-storage | 32 | L0 ✅ | ✅ | Evicted, ephemeral-storage≈临时存储, emptyDir | - | - | 100% | ✅ | 347s |
| evicted-ephemeral-storage | 33 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir, sizeLimit | - | - | 100% | ✅ | 467s |
| evicted-ephemeral-storage | 34 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 20% | ✅ | 481s |
| evicted-ephemeral-storage | 35 | L0 ✅ | ❌ | Evicted, ephemeral-storage | - | OOMKilled | 100% | ✅ | 296s |
| evicted-ephemeral-storage | 36 | L0 ✅ | ❌ | Evicted, ephemeral-storage, emptyDir | - | finalizer | 75% | ✅ | 433s |
| evicted-ephemeral-storage | 37 | L0 ✅ | ❌ | Evicted, ephemeral-storage, emptyDir, sizeLimit | - | OOMKilled | 100% | ✅ | 407s |
| evicted-ephemeral-storage | 38 | L0 ✅ | ❌ | Evicted, ephemeral-storage | - | OOMKilled | 67% | ✅ | 325s |
| evicted-ephemeral-storage | 39 | L0 ✅ | ✅ | Evicted, ephemeral-storage≈临时存储, emptyDir | - | - | 100% | ✅ | 327s |
| evicted-ephemeral-storage | 40 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 50% | ✅ | 420s |
| evicted-ephemeral-storage | 41 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir | - | - | 100% | ✅ | 339s |
| evicted-ephemeral-storage | 42 | L0 ✅ | ❌ | Evicted, ephemeral-storage≈临时存储, emptyDir, sizeLimit | - | OOMKilled | 100% | ✅ | 399s |
| evicted-ephemeral-storage | 43 | L0 ✅ | ✅ | Evicted, ephemeral-storage≈临时存储, emptyDir | - | - | 40% | ✅ | 432s |
| evicted-ephemeral-storage | 44 | L0 ✅ | ❌ | Evicted, ephemeral-storage | - | OOMKilled | 75% | ✅ | 373s |
| evicted-ephemeral-storage | 45 | L0 ✅ | ❌ | Evicted, ephemeral-storage | - | OOMKilled | 67% | ✅ | 372s |
| evicted-ephemeral-storage | 46 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir, sizeLimit | - | - | 67% | ✅ | 451s |
| evicted-ephemeral-storage | 47 | L0 ✅ | ✅ | Evicted, ephemeral-storage | - | - | 75% | ✅ | 359s |
| evicted-ephemeral-storage | 48 | L0 ✅ | ❌ | Evicted, ephemeral-storage≈临时存储 | - | OOMKilled | 80% | ✅ | 386s |
| evicted-ephemeral-storage | 49 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir | - | - | 50% | ✅ | 327s |
| evicted-ephemeral-storage | 50 | L0 ✅ | ✅ | Evicted, ephemeral-storage, emptyDir | - | - | 100% | ✅ | 295s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| evicted-ephemeral-storage | evicted | 78.0% | 100.0% | 76.9% | 6.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 6.0m | ✅ |
| 根因准确率 | >= 60% | 78.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 76.9% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260519_162052/evicted/04-evicted-ephemeral-storage
