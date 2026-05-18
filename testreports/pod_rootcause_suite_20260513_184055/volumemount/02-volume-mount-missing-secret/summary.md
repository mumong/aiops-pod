# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 111.4m
- 人工语义修正: 11 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| volume-mount-missing-secret | 1 | L3 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 282s |
| volume-mount-missing-secret | 2 | L4 ❌ | ✅ | secret, rc-definitely-missing-secret, missing-secret, 语义等价修正: Secret 不存在 等价 not found | - | - | 100% | ✅ | 318s |
| volume-mount-missing-secret | 3 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 268s |
| volume-mount-missing-secret | 4 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 261s |
| volume-mount-missing-secret | 5 | L4 ❌ | ✅ | secret, rc-definitely-missing-secret, missing-secret, 语义等价修正: Secret 不存在 等价 not found | - | - | 100% | ✅ | 215s |
| volume-mount-missing-secret | 6 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 211s |
| volume-mount-missing-secret | 7 | L3 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 67% | ✅ | 251s |
| volume-mount-missing-secret | 8 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 248s |
| volume-mount-missing-secret | 9 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 266s |
| volume-mount-missing-secret | 10 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 314s |
| volume-mount-missing-secret | 11 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | N/A | ✅ | 33s |
| volume-mount-missing-secret | 12 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 223s |
| volume-mount-missing-secret | 13 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 218s |
| volume-mount-missing-secret | 14 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 267s |
| volume-mount-missing-secret | 15 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret, 语义等价修正: Secret 不存在 等价 not found | - | - | 50% | ✅ | 313s |
| volume-mount-missing-secret | 16 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 259s |
| volume-mount-missing-secret | 17 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 300s |
| volume-mount-missing-secret | 18 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 277s |
| volume-mount-missing-secret | 19 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 308s |
| volume-mount-missing-secret | 20 | L3 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 67% | ✅ | 316s |
| volume-mount-missing-secret | 21 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | N/A | ✅ | 51s |
| volume-mount-missing-secret | 22 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 242s |
| volume-mount-missing-secret | 23 | L3 ❌ | ✅ | secret, rc-definitely-missing-secret, missing-secret, 语义等价修正: Secret 不存在 等价 not found | - | - | 100% | ✅ | 240s |
| volume-mount-missing-secret | 24 | L4 ❌ | ✅ | secret, rc-definitely-missing-secret, missing-secret, 语义等价修正: Secret 不存在 等价 not found | - | - | 100% | ✅ | 333s |
| volume-mount-missing-secret | 25 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 261s |
| volume-mount-missing-secret | 26 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 333s |
| volume-mount-missing-secret | 27 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 325s |
| volume-mount-missing-secret | 28 | L4 ❌ | ✅ | secret, rc-definitely-missing-secret, missing-secret, 语义等价修正: Secret 不存在 等价 not found | - | - | 100% | ✅ | 448s |
| volume-mount-missing-secret | 29 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 304s |
| volume-mount-missing-secret | 30 | L4 ❌ | ✅ | secret, rc-definitely-missing-secret, missing-secret, 语义等价修正: Secret 不存在 等价 not found | - | - | 100% | ✅ | 254s |
| volume-mount-missing-secret | 31 | L3 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 261s |
| volume-mount-missing-secret | 32 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 264s |
| volume-mount-missing-secret | 33 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 253s |
| volume-mount-missing-secret | 34 | L4 ❌ | ✅ | secret, rc-definitely-missing-secret, missing-secret, 语义等价修正: Secret 不存在 等价 not found | - | - | 100% | ✅ | 315s |
| volume-mount-missing-secret | 35 | L3 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 190s |
| volume-mount-missing-secret | 36 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 344s |
| volume-mount-missing-secret | 37 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 272s |
| volume-mount-missing-secret | 38 | L4 ❌ | ✅ | secret, rc-definitely-missing-secret, missing-secret, 语义等价修正: Secret 不存在 等价 not found | - | - | 100% | ✅ | 283s |
| volume-mount-missing-secret | 39 | L4 ❌ | ✅ | secret, rc-definitely-missing-secret, missing-secret, 语义等价修正: Secret 不存在 等价 not found | - | - | 100% | ✅ | 270s |
| volume-mount-missing-secret | 40 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 265s |
| volume-mount-missing-secret | 41 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 291s |
| volume-mount-missing-secret | 42 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 191s |
| volume-mount-missing-secret | 43 | L4 ❌ | ❌ | secret, rc-definitely-missing-secret, missing-secret | not found | - | N/A | ✅ | 50s |
| volume-mount-missing-secret | 44 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 249s |
| volume-mount-missing-secret | 45 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 326s |
| volume-mount-missing-secret | 46 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 286s |
| volume-mount-missing-secret | 47 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 246s |
| volume-mount-missing-secret | 48 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 369s |
| volume-mount-missing-secret | 49 | L4 ❌ | ✅ | secret, rc-definitely-missing-secret, missing-secret, 语义等价修正: Secret 不存在 等价 not found | - | - | 100% | ✅ | 259s |
| volume-mount-missing-secret | 50 | L4 ❌ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 220s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| volume-mount-missing-secret | volumemount | 98.0% | 100.0% | 97.5% | 4.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 4.0m | ✅ |
| 根因准确率 | >= 60% | 98.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 97.5% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/volumemount/02-volume-mount-missing-secret
