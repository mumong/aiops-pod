# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 112.7m
- 人工语义修正: 11 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| volume-mount-missing-configmap | 1 | L4 ❌ | ✅ | configmap, rc-definitely-missing-configmap, missing-config, 语义等价修正: ConfigMap 不存在 等价 not found | - | - | 100% | ✅ | 226s |
| volume-mount-missing-configmap | 2 | L4 ❌ | ✅ | configmap, rc-definitely-missing-configmap, missing-config, 语义等价修正: ConfigMap 不存在 等价 not found | - | - | 100% | ✅ | 291s |
| volume-mount-missing-configmap | 3 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 238s |
| volume-mount-missing-configmap | 4 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 324s |
| volume-mount-missing-configmap | 5 | L4 ❌ | ✅ | configmap, rc-definitely-missing-configmap, missing-config, 语义等价修正: ConfigMap 不存在 等价 not found | - | - | 100% | ✅ | 364s |
| volume-mount-missing-configmap | 6 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 353s |
| volume-mount-missing-configmap | 7 | L4 ❌ | ✅ | configmap, rc-definitely-missing-configmap, missing-config, 语义等价修正: ConfigMap 不存在 等价 not found | - | - | 100% | ✅ | 296s |
| volume-mount-missing-configmap | 8 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 261s |
| volume-mount-missing-configmap | 9 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 282s |
| volume-mount-missing-configmap | 10 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 242s |
| volume-mount-missing-configmap | 11 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | N/A | ✅ | 25s |
| volume-mount-missing-configmap | 12 | L4 ❌ | ✅ | configmap, rc-definitely-missing-configmap, missing-config, 语义等价修正: ConfigMap 不存在 等价 not found | - | - | 100% | ✅ | 247s |
| volume-mount-missing-configmap | 13 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 246s |
| volume-mount-missing-configmap | 14 | L4 ❌ | ✅ | configmap, rc-definitely-missing-configmap, missing-config, 语义等价修正: ConfigMap 不存在 等价 not found | - | - | 100% | ✅ | 270s |
| volume-mount-missing-configmap | 15 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 232s |
| volume-mount-missing-configmap | 16 | L4 ❌ | ✅ | configmap, rc-definitely-missing-configmap, missing-config, 语义等价修正: ConfigMap 不存在 等价 not found | - | - | 100% | ✅ | 442s |
| volume-mount-missing-configmap | 17 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 292s |
| volume-mount-missing-configmap | 18 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 281s |
| volume-mount-missing-configmap | 19 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 186s |
| volume-mount-missing-configmap | 20 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 267s |
| volume-mount-missing-configmap | 21 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 210s |
| volume-mount-missing-configmap | 22 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 367s |
| volume-mount-missing-configmap | 23 | L0 ✅ | ✅ | configmap, rc-definitely-missing-configmap, missing-config, 语义等价修正: ConfigMap 不存在 等价 not found | - | - | 100% | ✅ | 245s |
| volume-mount-missing-configmap | 24 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 268s |
| volume-mount-missing-configmap | 25 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 355s |
| volume-mount-missing-configmap | 26 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 205s |
| volume-mount-missing-configmap | 27 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 231s |
| volume-mount-missing-configmap | 28 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 383s |
| volume-mount-missing-configmap | 29 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 395s |
| volume-mount-missing-configmap | 30 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 340s |
| volume-mount-missing-configmap | 31 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 259s |
| volume-mount-missing-configmap | 32 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 276s |
| volume-mount-missing-configmap | 33 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 254s |
| volume-mount-missing-configmap | 34 | L4 ❌ | ✅ | configmap, rc-definitely-missing-configmap, missing-config, 语义等价修正: ConfigMap 不存在 等价 not found | - | - | 100% | ✅ | 297s |
| volume-mount-missing-configmap | 35 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | N/A | ✅ | 55s |
| volume-mount-missing-configmap | 36 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 204s |
| volume-mount-missing-configmap | 37 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 234s |
| volume-mount-missing-configmap | 38 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 315s |
| volume-mount-missing-configmap | 39 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 230s |
| volume-mount-missing-configmap | 40 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 362s |
| volume-mount-missing-configmap | 41 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 278s |
| volume-mount-missing-configmap | 42 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 291s |
| volume-mount-missing-configmap | 43 | L3 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 260s |
| volume-mount-missing-configmap | 44 | L0 ✅ | ✅ | configmap, rc-definitely-missing-configmap, missing-config, 语义等价修正: ConfigMap 不存在 等价 not found | - | - | 100% | ✅ | 242s |
| volume-mount-missing-configmap | 45 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 346s |
| volume-mount-missing-configmap | 46 | L4 ❌ | ✅ | configmap, rc-definitely-missing-configmap, missing-config, 语义等价修正: ConfigMap 不存在 等价 not found | - | - | 100% | ✅ | 268s |
| volume-mount-missing-configmap | 47 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 235s |
| volume-mount-missing-configmap | 48 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 243s |
| volume-mount-missing-configmap | 49 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 294s |
| volume-mount-missing-configmap | 50 | L4 ❌ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 172s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| volume-mount-missing-configmap | volumemount | 100.0% | 100.0% | 100.0% | 4.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 4.0m | ✅ |
| 根因准确率 | >= 60% | 100.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 100.0% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/volumemount/01-volume-mount-missing-configmap
