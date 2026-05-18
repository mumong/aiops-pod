# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 120.2m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| pending-insufficient-cpu | 1 | L1 ✅ | ❌ | Insufficient, cpu, 0/, nodes are available | - | nodeSelector | 67% | ✅ | 274s |
| pending-insufficient-cpu | 2 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 280s |
| pending-insufficient-cpu | 3 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 246s |
| pending-insufficient-cpu | 4 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 67% | ✅ | 272s |
| pending-insufficient-cpu | 5 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 303s |
| pending-insufficient-cpu | 6 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 509s |
| pending-insufficient-cpu | 7 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 224s |
| pending-insufficient-cpu | 8 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 75% | ✅ | 284s |
| pending-insufficient-cpu | 9 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 248s |
| pending-insufficient-cpu | 10 | L1 ✅ | ✅ | Insufficient, cpu, 0/ | - | - | 100% | ✅ | 310s |
| pending-insufficient-cpu | 11 | L1 ✅ | ❌ | Insufficient, cpu, 0/, nodes are available | - | pvc | 67% | ✅ | 280s |
| pending-insufficient-cpu | 12 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 281s |
| pending-insufficient-cpu | 13 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 355s |
| pending-insufficient-cpu | 14 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 321s |
| pending-insufficient-cpu | 15 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 268s |
| pending-insufficient-cpu | 16 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 67% | ✅ | 262s |
| pending-insufficient-cpu | 17 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 33% | ✅ | 269s |
| pending-insufficient-cpu | 18 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 267s |
| pending-insufficient-cpu | 19 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 252s |
| pending-insufficient-cpu | 20 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 374s |
| pending-insufficient-cpu | 21 | L1 ✅ | ❌ | Insufficient, cpu, 0/, nodes are available | - | nodeSelector | 100% | ✅ | 373s |
| pending-insufficient-cpu | 22 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 263s |
| pending-insufficient-cpu | 23 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 75% | ✅ | 393s |
| pending-insufficient-cpu | 24 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 272s |
| pending-insufficient-cpu | 25 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 293s |
| pending-insufficient-cpu | 26 | L1 ✅ | ❌ | Insufficient, cpu, 0/, nodes are available | - | nodeSelector, pvc | 100% | ✅ | 257s |
| pending-insufficient-cpu | 27 | L1 ✅ | ❌ | cpu | Insufficient, 100000, 0/, nodes are available | - | 100% | ✅ | 260s |
| pending-insufficient-cpu | 28 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 335s |
| pending-insufficient-cpu | 29 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 325s |
| pending-insufficient-cpu | 30 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 342s |
| pending-insufficient-cpu | 31 | L1 ✅ | ❌ | Insufficient, cpu, 0/, nodes are available | - | pvc | 100% | ✅ | 324s |
| pending-insufficient-cpu | 32 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 167s |
| pending-insufficient-cpu | 33 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 271s |
| pending-insufficient-cpu | 34 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 260s |
| pending-insufficient-cpu | 35 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 67% | ✅ | 265s |
| pending-insufficient-cpu | 36 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 394s |
| pending-insufficient-cpu | 37 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 262s |
| pending-insufficient-cpu | 38 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 293s |
| pending-insufficient-cpu | 39 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 254s |
| pending-insufficient-cpu | 40 | L1 ✅ | ❌ | Insufficient, cpu, 0/, nodes are available | - | pvc | 75% | ✅ | 303s |
| pending-insufficient-cpu | 41 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 253s |
| pending-insufficient-cpu | 42 | L1 ✅ | ✅ | Insufficient, cpu, 0/ | - | - | 100% | ✅ | 284s |
| pending-insufficient-cpu | 43 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 265s |
| pending-insufficient-cpu | 44 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 262s |
| pending-insufficient-cpu | 45 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 276s |
| pending-insufficient-cpu | 46 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 408s |
| pending-insufficient-cpu | 47 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 67% | ✅ | 251s |
| pending-insufficient-cpu | 48 | L1 ✅ | ❌ | Insufficient, cpu, 0/, nodes are available | - | pvc | 100% | ✅ | 152s |
| pending-insufficient-cpu | 49 | L1 ✅ | ✅ | Insufficient, cpu, 0/, nodes are available | - | - | 100% | ✅ | 227s |
| pending-insufficient-cpu | 50 | L1 ✅ | ❌ | Insufficient, cpu | 100000, 0/, nodes are available | - | 100% | ✅ | 231s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| pending-insufficient-cpu | pending | 70.0% | 100.0% | 93.2% | 4.3m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 4.3m | ✅ |
| 根因准确率 | >= 60% | 70.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 93.2% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260513_184055/pending/07-pending-insufficient-cpu
