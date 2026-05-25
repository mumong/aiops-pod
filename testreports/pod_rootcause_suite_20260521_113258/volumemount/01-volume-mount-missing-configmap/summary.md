# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 27.9m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| volume-mount-missing-configmap | 1 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 75% | ✅ | 79s |
| volume-mount-missing-configmap | 2 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 84s |
| volume-mount-missing-configmap | 3 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 67% | ✅ | 70s |
| volume-mount-missing-configmap | 4 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 62s |
| volume-mount-missing-configmap | 5 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 74s |
| volume-mount-missing-configmap | 6 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 75s |
| volume-mount-missing-configmap | 7 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 64s |
| volume-mount-missing-configmap | 8 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 65s |
| volume-mount-missing-configmap | 9 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 75s |
| volume-mount-missing-configmap | 10 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 60% | ✅ | 71s |
| volume-mount-missing-configmap | 11 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 72s |
| volume-mount-missing-configmap | 12 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 75s |
| volume-mount-missing-configmap | 13 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 67% | ✅ | 75s |
| volume-mount-missing-configmap | 14 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 61s |
| volume-mount-missing-configmap | 15 | L4 ❌ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 67% | ✅ | 68s |
| volume-mount-missing-configmap | 16 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 67s |
| volume-mount-missing-configmap | 17 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 69s |
| volume-mount-missing-configmap | 18 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 67% | ✅ | 70s |
| volume-mount-missing-configmap | 19 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 66s |
| volume-mount-missing-configmap | 20 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 65s |
| volume-mount-missing-configmap | 21 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 64s |
| volume-mount-missing-configmap | 22 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 59s |
| volume-mount-missing-configmap | 23 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 67s |
| volume-mount-missing-configmap | 24 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 75% | ✅ | 65s |
| volume-mount-missing-configmap | 25 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 80% | ✅ | 75s |
| volume-mount-missing-configmap | 26 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 62s |
| volume-mount-missing-configmap | 27 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 63s |
| volume-mount-missing-configmap | 28 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 60s |
| volume-mount-missing-configmap | 29 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 60% | ✅ | 70s |
| volume-mount-missing-configmap | 30 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 64s |
| volume-mount-missing-configmap | 31 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 80% | ✅ | 68s |
| volume-mount-missing-configmap | 32 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 61s |
| volume-mount-missing-configmap | 33 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 69s |
| volume-mount-missing-configmap | 34 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 75% | ✅ | 64s |
| volume-mount-missing-configmap | 35 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 75% | ✅ | 61s |
| volume-mount-missing-configmap | 36 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 61s |
| volume-mount-missing-configmap | 37 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 80% | ✅ | 64s |
| volume-mount-missing-configmap | 38 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 64s |
| volume-mount-missing-configmap | 39 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 72s |
| volume-mount-missing-configmap | 40 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 75s |
| volume-mount-missing-configmap | 41 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 57s |
| volume-mount-missing-configmap | 42 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 60s |
| volume-mount-missing-configmap | 43 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 75% | ✅ | 65s |
| volume-mount-missing-configmap | 44 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 75% | ✅ | 64s |
| volume-mount-missing-configmap | 45 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 58s |
| volume-mount-missing-configmap | 46 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 58s |
| volume-mount-missing-configmap | 47 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 56s |
| volume-mount-missing-configmap | 48 | L0 ✅ | ✅ | configmap, not found≈missing, rc-definitely-missing-configmap, missing-config | - | - | 75% | ✅ | 66s |
| volume-mount-missing-configmap | 49 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 100% | ✅ | 68s |
| volume-mount-missing-configmap | 50 | L0 ✅ | ✅ | configmap, not found, rc-definitely-missing-configmap, missing-config | - | - | 75% | ✅ | 68s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| volume-mount-missing-configmap | volumemount | 100.0% | 100.0% | 90.5% | 1.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 1.0m | ✅ |
| 根因准确率 | >= 60% | 100.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 90.5% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/volumemount/01-volume-mount-missing-configmap
