# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 26.9m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| volume-mount-missing-secret | 1 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 58s |
| volume-mount-missing-secret | 2 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 68s |
| volume-mount-missing-secret | 3 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 58s |
| volume-mount-missing-secret | 4 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 75% | ✅ | 59s |
| volume-mount-missing-secret | 5 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 70s |
| volume-mount-missing-secret | 6 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 80% | ✅ | 62s |
| volume-mount-missing-secret | 7 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 60s |
| volume-mount-missing-secret | 8 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 58s |
| volume-mount-missing-secret | 9 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 63s |
| volume-mount-missing-secret | 10 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 75% | ✅ | 59s |
| volume-mount-missing-secret | 11 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 62s |
| volume-mount-missing-secret | 12 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 60s |
| volume-mount-missing-secret | 13 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 58s |
| volume-mount-missing-secret | 14 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 65s |
| volume-mount-missing-secret | 15 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 60s |
| volume-mount-missing-secret | 16 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 57s |
| volume-mount-missing-secret | 17 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 65s |
| volume-mount-missing-secret | 18 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 71s |
| volume-mount-missing-secret | 19 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 70s |
| volume-mount-missing-secret | 20 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 58s |
| volume-mount-missing-secret | 21 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 80% | ✅ | 64s |
| volume-mount-missing-secret | 22 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 59s |
| volume-mount-missing-secret | 23 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 63s |
| volume-mount-missing-secret | 24 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 63s |
| volume-mount-missing-secret | 25 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 67% | ✅ | 66s |
| volume-mount-missing-secret | 26 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 56s |
| volume-mount-missing-secret | 27 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 67% | ✅ | 68s |
| volume-mount-missing-secret | 28 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 75% | ✅ | 60s |
| volume-mount-missing-secret | 29 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 62s |
| volume-mount-missing-secret | 30 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 75% | ✅ | 60s |
| volume-mount-missing-secret | 31 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 65s |
| volume-mount-missing-secret | 32 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 80% | ✅ | 65s |
| volume-mount-missing-secret | 33 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 80% | ✅ | 64s |
| volume-mount-missing-secret | 34 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 62s |
| volume-mount-missing-secret | 35 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 75% | ✅ | 67s |
| volume-mount-missing-secret | 36 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 69s |
| volume-mount-missing-secret | 37 | L0 ✅ | ❌ | secret, not found, rc-definitely-missing-secret, missing-secret | - | persistentvolumeclaim, hostPath | 75% | ✅ | 66s |
| volume-mount-missing-secret | 38 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 84s |
| volume-mount-missing-secret | 39 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 64s |
| volume-mount-missing-secret | 40 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 67% | ✅ | 61s |
| volume-mount-missing-secret | 41 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 66s |
| volume-mount-missing-secret | 42 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 68s |
| volume-mount-missing-secret | 43 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 67% | ✅ | 67s |
| volume-mount-missing-secret | 44 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 70s |
| volume-mount-missing-secret | 45 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 75% | ✅ | 68s |
| volume-mount-missing-secret | 46 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 100% | ✅ | 76s |
| volume-mount-missing-secret | 47 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 67% | ✅ | 61s |
| volume-mount-missing-secret | 48 | L0 ✅ | ✅ | secret, not found, rc-definitely-missing-secret, missing-secret | - | - | 75% | ✅ | 64s |
| volume-mount-missing-secret | 49 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 80% | ✅ | 63s |
| volume-mount-missing-secret | 50 | L0 ✅ | ✅ | secret, not found≈missing, rc-definitely-missing-secret, missing-secret | - | - | 80% | ✅ | 61s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| volume-mount-missing-secret | volumemount | 98.0% | 100.0% | 90.3% | 1.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 1.0m | ✅ |
| 根因准确率 | >= 60% | 98.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 90.3% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/volumemount/02-volume-mount-missing-secret
