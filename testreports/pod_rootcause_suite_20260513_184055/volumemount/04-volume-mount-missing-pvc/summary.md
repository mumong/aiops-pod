# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 131.9m
- 人工语义修正: 19 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| volume-mount-missing-pvc | 1 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 424s |
| volume-mount-missing-pvc | 2 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 253s |
| volume-mount-missing-pvc | 3 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 252s |
| volume-mount-missing-pvc | 4 | L3 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 67% | ✅ | 372s |
| volume-mount-missing-pvc | 5 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 378s |
| volume-mount-missing-pvc | 6 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 242s |
| volume-mount-missing-pvc | 7 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 273s |
| volume-mount-missing-pvc | 8 | L3 ❌ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 218s |
| volume-mount-missing-pvc | 9 | L0 ✅ | ✅ | not found, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 188s |
| volume-mount-missing-pvc | 10 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 67% | ✅ | 343s |
| volume-mount-missing-pvc | 11 | L0 ✅ | ✅ | not found, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 283s |
| volume-mount-missing-pvc | 12 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 282s |
| volume-mount-missing-pvc | 13 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 298s |
| volume-mount-missing-pvc | 14 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 329s |
| volume-mount-missing-pvc | 15 | L3 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 420s |
| volume-mount-missing-pvc | 16 | L3 ❌ | ✅ | not found, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 268s |
| volume-mount-missing-pvc | 17 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 306s |
| volume-mount-missing-pvc | 18 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 67% | ✅ | 231s |
| volume-mount-missing-pvc | 19 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 245s |
| volume-mount-missing-pvc | 20 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 264s |
| volume-mount-missing-pvc | 21 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 288s |
| volume-mount-missing-pvc | 22 | L3 ❌ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 241s |
| volume-mount-missing-pvc | 23 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 1939s |
| volume-mount-missing-pvc | 24 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 217s |
| volume-mount-missing-pvc | 25 | L0 ✅ | ✅ | not found, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 180s |
| volume-mount-missing-pvc | 26 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 75% | ✅ | 333s |
| volume-mount-missing-pvc | 27 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 315s |
| volume-mount-missing-pvc | 28 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 252s |
| volume-mount-missing-pvc | 29 | L3 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 280s |
| volume-mount-missing-pvc | 30 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 67% | ✅ | 294s |
| volume-mount-missing-pvc | 31 | L3 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 33% | ✅ | 283s |
| volume-mount-missing-pvc | 32 | L3 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 294s |
| volume-mount-missing-pvc | 33 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 67% | ✅ | 252s |
| volume-mount-missing-pvc | 34 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 237s |
| volume-mount-missing-pvc | 35 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 227s |
| volume-mount-missing-pvc | 36 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 225s |
| volume-mount-missing-pvc | 37 | L3 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 263s |
| volume-mount-missing-pvc | 38 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 227s |
| volume-mount-missing-pvc | 39 | L3 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 269s |
| volume-mount-missing-pvc | 40 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 283s |
| volume-mount-missing-pvc | 41 | L3 ❌ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 301s |
| volume-mount-missing-pvc | 42 | L3 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 318s |
| volume-mount-missing-pvc | 43 | L3 ❌ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 281s |
| volume-mount-missing-pvc | 44 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 230s |
| volume-mount-missing-pvc | 45 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 463s |
| volume-mount-missing-pvc | 46 | L3 ❌ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 254s |
| volume-mount-missing-pvc | 47 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 67% | ✅ | 212s |
| volume-mount-missing-pvc | 48 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 305s |
| volume-mount-missing-pvc | 49 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 100% | ✅ | 306s |
| volume-mount-missing-pvc | 50 | L0 ✅ | ✅ | pvc, rc-definitely-missing-pvc, 语义等价修正: PVC 不存在/未创建 等价 not found | - | - | 100% | ✅ | 204s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| volume-mount-missing-pvc | volumemount | 100.0% | 100.0% | 92.7% | 4.8m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 4.8m | ✅ |
| 根因准确率 | >= 60% | 100.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 92.7% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/volumemount/04-volume-mount-missing-pvc
