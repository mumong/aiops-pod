# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 121.2m
- 人工语义修正: 22 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| pending-missing-pvc | 1 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 227s |
| pending-missing-pvc | 2 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 413s |
| pending-missing-pvc | 3 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 196s |
| pending-missing-pvc | 4 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 279s |
| pending-missing-pvc | 5 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 389s |
| pending-missing-pvc | 6 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 266s |
| pending-missing-pvc | 7 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 280s |
| pending-missing-pvc | 8 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 189s |
| pending-missing-pvc | 9 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 307s |
| pending-missing-pvc | 10 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 358s |
| pending-missing-pvc | 11 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 253s |
| pending-missing-pvc | 12 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 266s |
| pending-missing-pvc | 13 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 291s |
| pending-missing-pvc | 14 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 185s |
| pending-missing-pvc | 15 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 298s |
| pending-missing-pvc | 16 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 284s |
| pending-missing-pvc | 17 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 205s |
| pending-missing-pvc | 18 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 216s |
| pending-missing-pvc | 19 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 280s |
| pending-missing-pvc | 20 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 334s |
| pending-missing-pvc | 21 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 50% | ✅ | 227s |
| pending-missing-pvc | 22 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 297s |
| pending-missing-pvc | 23 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 223s |
| pending-missing-pvc | 24 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 330s |
| pending-missing-pvc | 25 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 249s |
| pending-missing-pvc | 26 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 307s |
| pending-missing-pvc | 27 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 309s |
| pending-missing-pvc | 28 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 246s |
| pending-missing-pvc | 29 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 242s |
| pending-missing-pvc | 30 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 67% | ✅ | 420s |
| pending-missing-pvc | 31 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 274s |
| pending-missing-pvc | 32 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 293s |
| pending-missing-pvc | 33 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 285s |
| pending-missing-pvc | 34 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 300s |
| pending-missing-pvc | 35 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 253s |
| pending-missing-pvc | 36 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 290s |
| pending-missing-pvc | 37 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 484s |
| pending-missing-pvc | 38 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 165s |
| pending-missing-pvc | 39 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 327s |
| pending-missing-pvc | 40 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 50% | ✅ | 369s |
| pending-missing-pvc | 41 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 267s |
| pending-missing-pvc | 42 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 67% | ✅ | 327s |
| pending-missing-pvc | 43 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 75% | ✅ | 363s |
| pending-missing-pvc | 44 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 286s |
| pending-missing-pvc | 45 | L1 ✅ | ✅ | pvc, rc-pending-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 183s |
| pending-missing-pvc | 46 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 448s |
| pending-missing-pvc | 47 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 330s |
| pending-missing-pvc | 48 | L1 ✅ | ✅ | not found, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 268s |
| pending-missing-pvc | 49 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 217s |
| pending-missing-pvc | 50 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 100% | ✅ | 234s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| pending-missing-pvc | pending | 100.0% | 100.0% | 94.3% | 4.3m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 4.3m | ✅ |
| 根因准确率 | >= 60% | 100.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 94.3% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/pending/09-pending-missing-pvc
