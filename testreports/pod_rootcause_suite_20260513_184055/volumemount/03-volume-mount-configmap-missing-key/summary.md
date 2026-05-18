# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 105.7m
- 人工语义修正: 12 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| volume-mount-configmap-missing-key | 1 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 270s |
| volume-mount-configmap-missing-key | 2 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 67% | ✅ | 359s |
| volume-mount-configmap-missing-key | 3 | L4 ❌ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 100% | ✅ | 317s |
| volume-mount-configmap-missing-key | 4 | L4 ❌ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 67% | ✅ | 248s |
| volume-mount-configmap-missing-key | 5 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 399s |
| volume-mount-configmap-missing-key | 6 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 234s |
| volume-mount-configmap-missing-key | 7 | L4 ❌ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 100% | ✅ | 232s |
| volume-mount-configmap-missing-key | 8 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 345s |
| volume-mount-configmap-missing-key | 9 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 398s |
| volume-mount-configmap-missing-key | 10 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 166s |
| volume-mount-configmap-missing-key | 11 | L0 ✅ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 100% | ✅ | 239s |
| volume-mount-configmap-missing-key | 12 | L4 ❌ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 100% | ✅ | 299s |
| volume-mount-configmap-missing-key | 13 | L4 ❌ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 100% | ✅ | 284s |
| volume-mount-configmap-missing-key | 14 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 334s |
| volume-mount-configmap-missing-key | 15 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 67% | ✅ | 314s |
| volume-mount-configmap-missing-key | 16 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 238s |
| volume-mount-configmap-missing-key | 17 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 232s |
| volume-mount-configmap-missing-key | 18 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 67% | ✅ | 321s |
| volume-mount-configmap-missing-key | 19 | L4 ❌ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 100% | ✅ | 196s |
| volume-mount-configmap-missing-key | 20 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 251s |
| volume-mount-configmap-missing-key | 21 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 268s |
| volume-mount-configmap-missing-key | 22 | L4 ❌ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 100% | ✅ | 181s |
| volume-mount-configmap-missing-key | 23 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 189s |
| volume-mount-configmap-missing-key | 24 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | N/A | ✅ | 42s |
| volume-mount-configmap-missing-key | 25 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 296s |
| volume-mount-configmap-missing-key | 26 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 283s |
| volume-mount-configmap-missing-key | 27 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 243s |
| volume-mount-configmap-missing-key | 28 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 237s |
| volume-mount-configmap-missing-key | 29 | L4 ❌ | ❌ | configmap | missing-key, couldn't find key, rc-volume-key-config | - | 100% | ✅ | 269s |
| volume-mount-configmap-missing-key | 30 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | N/A | ✅ | 83s |
| volume-mount-configmap-missing-key | 31 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 194s |
| volume-mount-configmap-missing-key | 32 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 0% | ✅ | 211s |
| volume-mount-configmap-missing-key | 33 | L4 ❌ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 100% | ✅ | 346s |
| volume-mount-configmap-missing-key | 34 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 295s |
| volume-mount-configmap-missing-key | 35 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 0% | ✅ | 202s |
| volume-mount-configmap-missing-key | 36 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | N/A | ✅ | 36s |
| volume-mount-configmap-missing-key | 37 | L4 ❌ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 100% | ✅ | 188s |
| volume-mount-configmap-missing-key | 38 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 243s |
| volume-mount-configmap-missing-key | 39 | L4 ❌ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 100% | ✅ | 227s |
| volume-mount-configmap-missing-key | 40 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 201s |
| volume-mount-configmap-missing-key | 41 | L4 ❌ | ❌ | configmap, missing-key | couldn't find key, rc-volume-key-config | - | 100% | ✅ | 359s |
| volume-mount-configmap-missing-key | 42 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 269s |
| volume-mount-configmap-missing-key | 43 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 340s |
| volume-mount-configmap-missing-key | 44 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 337s |
| volume-mount-configmap-missing-key | 45 | L4 ❌ | ✅ | configmap, missing-key, 语义等价修正: ConfigMap key 缺失 | - | - | 100% | ✅ | 280s |
| volume-mount-configmap-missing-key | 46 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 289s |
| volume-mount-configmap-missing-key | 47 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 244s |
| volume-mount-configmap-missing-key | 48 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 236s |
| volume-mount-configmap-missing-key | 49 | L4 ❌ | ❌ | configmap | missing-key, couldn't find key, rc-volume-key-config | - | 75% | ✅ | 227s |
| volume-mount-configmap-missing-key | 50 | L4 ❌ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | N/A | ✅ | 68s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| volume-mount-configmap-missing-key | volumemount | 94.0% | 100.0% | 92.2% | 3.6m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 3.6m | ✅ |
| 根因准确率 | >= 60% | 94.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 92.2% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/volumemount/03-volume-mount-configmap-missing-key
