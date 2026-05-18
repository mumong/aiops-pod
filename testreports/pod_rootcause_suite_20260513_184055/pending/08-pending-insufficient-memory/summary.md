# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 121.0m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| pending-insufficient-memory | 1 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 275s |
| pending-insufficient-memory | 2 | L1 ✅ | ❌ | - | Insufficient, memory, 100000Gi, 0/, nodes are available | - | 100% | ✅ | 271s |
| pending-insufficient-memory | 3 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 253s |
| pending-insufficient-memory | 4 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | nodeSelector | 100% | ✅ | 250s |
| pending-insufficient-memory | 5 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | nodeSelector | 100% | ✅ | 412s |
| pending-insufficient-memory | 6 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 274s |
| pending-insufficient-memory | 7 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 67% | ✅ | 350s |
| pending-insufficient-memory | 8 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 216s |
| pending-insufficient-memory | 9 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 100% | ✅ | 341s |
| pending-insufficient-memory | 10 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 100% | ✅ | 251s |
| pending-insufficient-memory | 11 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | pvc | 100% | ✅ | 261s |
| pending-insufficient-memory | 12 | L1 ✅ | ❌ | - | Insufficient, memory, 100000Gi, 0/, nodes are available | - | 100% | ✅ | 198s |
| pending-insufficient-memory | 13 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 233s |
| pending-insufficient-memory | 14 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 261s |
| pending-insufficient-memory | 15 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 75% | ✅ | 259s |
| pending-insufficient-memory | 16 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 235s |
| pending-insufficient-memory | 17 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 100% | ✅ | 401s |
| pending-insufficient-memory | 18 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 256s |
| pending-insufficient-memory | 19 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 340s |
| pending-insufficient-memory | 20 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 170s |
| pending-insufficient-memory | 21 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 339s |
| pending-insufficient-memory | 22 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 262s |
| pending-insufficient-memory | 23 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 304s |
| pending-insufficient-memory | 24 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | nodeSelector, pvc | 100% | ✅ | 271s |
| pending-insufficient-memory | 25 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 379s |
| pending-insufficient-memory | 26 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 248s |
| pending-insufficient-memory | 27 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 232s |
| pending-insufficient-memory | 28 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 100% | ✅ | 345s |
| pending-insufficient-memory | 29 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 224s |
| pending-insufficient-memory | 30 | L1 ✅ | ✅ | Insufficient, memory, 0/ | - | - | 100% | ✅ | 244s |
| pending-insufficient-memory | 31 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 245s |
| pending-insufficient-memory | 32 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 286s |
| pending-insufficient-memory | 33 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 100% | ✅ | 413s |
| pending-insufficient-memory | 34 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 299s |
| pending-insufficient-memory | 35 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 75% | ✅ | 286s |
| pending-insufficient-memory | 36 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | pvc | 100% | ✅ | 554s |
| pending-insufficient-memory | 37 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 212s |
| pending-insufficient-memory | 38 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | pvc | 100% | ✅ | 189s |
| pending-insufficient-memory | 39 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | pvc | 71% | ✅ | 280s |
| pending-insufficient-memory | 40 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 67% | ✅ | 414s |
| pending-insufficient-memory | 41 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 100% | ✅ | 230s |
| pending-insufficient-memory | 42 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 100% | ✅ | 226s |
| pending-insufficient-memory | 43 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | pvc | 100% | ✅ | 298s |
| pending-insufficient-memory | 44 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 380s |
| pending-insufficient-memory | 45 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 75% | ✅ | 389s |
| pending-insufficient-memory | 46 | L1 ✅ | ❌ | Insufficient, memory, 0/, nodes are available | - | pvc | 100% | ✅ | 265s |
| pending-insufficient-memory | 47 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 293s |
| pending-insufficient-memory | 48 | L1 ✅ | ❌ | Insufficient, memory | 100000Gi, 0/, nodes are available | - | 67% | ✅ | 452s |
| pending-insufficient-memory | 49 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 191s |
| pending-insufficient-memory | 50 | L1 ✅ | ✅ | Insufficient, memory, 0/, nodes are available | - | - | 100% | ✅ | 174s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| pending-insufficient-memory | pending | 60.0% | 100.0% | 95.9% | 4.3m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 4.3m | ✅ |
| 根因准确率 | >= 60% | 60.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 95.9% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260513_184055/pending/08-pending-insufficient-memory
