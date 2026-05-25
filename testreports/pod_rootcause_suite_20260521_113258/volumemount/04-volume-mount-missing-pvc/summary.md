# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 26.4m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| volume-mount-missing-pvc | 1 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 50% | ✅ | 64s |
| volume-mount-missing-pvc | 2 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 80% | ✅ | 85s |
| volume-mount-missing-pvc | 3 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 60s |
| volume-mount-missing-pvc | 4 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 60s |
| volume-mount-missing-pvc | 5 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 64s |
| volume-mount-missing-pvc | 6 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 61s |
| volume-mount-missing-pvc | 7 | L0 ✅ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 60% | ✅ | 88s |
| volume-mount-missing-pvc | 8 | L0 ✅ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 63s |
| volume-mount-missing-pvc | 9 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 68s |
| volume-mount-missing-pvc | 10 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 60% | ✅ | 56s |
| volume-mount-missing-pvc | 11 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 67% | ✅ | 65s |
| volume-mount-missing-pvc | 12 | L0 ✅ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 66s |
| volume-mount-missing-pvc | 13 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 64s |
| volume-mount-missing-pvc | 14 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 61s |
| volume-mount-missing-pvc | 15 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 58s |
| volume-mount-missing-pvc | 16 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 59s |
| volume-mount-missing-pvc | 17 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 60% | ✅ | 67s |
| volume-mount-missing-pvc | 18 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 50% | ✅ | 61s |
| volume-mount-missing-pvc | 19 | L0 ✅ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 40% | ✅ | 63s |
| volume-mount-missing-pvc | 20 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 80% | ✅ | 77s |
| volume-mount-missing-pvc | 21 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 67s |
| volume-mount-missing-pvc | 22 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 80% | ✅ | 66s |
| volume-mount-missing-pvc | 23 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 50% | ✅ | 59s |
| volume-mount-missing-pvc | 24 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 80% | ✅ | 68s |
| volume-mount-missing-pvc | 25 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 67% | ✅ | 54s |
| volume-mount-missing-pvc | 26 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 67% | ✅ | 59s |
| volume-mount-missing-pvc | 27 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 50% | ✅ | 66s |
| volume-mount-missing-pvc | 28 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 60% | ✅ | 67s |
| volume-mount-missing-pvc | 29 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 55s |
| volume-mount-missing-pvc | 30 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 80% | ✅ | 68s |
| volume-mount-missing-pvc | 31 | L0 ✅ | ✅ | not found≈missing, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 59s |
| volume-mount-missing-pvc | 32 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 81s |
| volume-mount-missing-pvc | 33 | L0 ✅ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 50% | ✅ | 62s |
| volume-mount-missing-pvc | 34 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 80% | ✅ | 63s |
| volume-mount-missing-pvc | 35 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 63s |
| volume-mount-missing-pvc | 36 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 60% | ✅ | 64s |
| volume-mount-missing-pvc | 37 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 64s |
| volume-mount-missing-pvc | 38 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 67% | ✅ | 67s |
| volume-mount-missing-pvc | 39 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 67% | ✅ | 66s |
| volume-mount-missing-pvc | 40 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 80% | ✅ | 66s |
| volume-mount-missing-pvc | 41 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 50% | ✅ | 69s |
| volume-mount-missing-pvc | 42 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 50% | ✅ | 58s |
| volume-mount-missing-pvc | 43 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 61s |
| volume-mount-missing-pvc | 44 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 52s |
| volume-mount-missing-pvc | 45 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 49s |
| volume-mount-missing-pvc | 46 | L0 ✅ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 48s |
| volume-mount-missing-pvc | 47 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 80% | ✅ | 51s |
| volume-mount-missing-pvc | 48 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 60% | ✅ | 49s |
| volume-mount-missing-pvc | 49 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 80% | ✅ | 53s |
| volume-mount-missing-pvc | 50 | L0 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-definitely-missing-pvc | - | - | 75% | ✅ | 50s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| volume-mount-missing-pvc | volumemount | 100.0% | 100.0% | 69.1% | 1.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 1.0m | ✅ |
| 根因准确率 | >= 60% | 100.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 69.1% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/volumemount/04-volume-mount-missing-pvc
