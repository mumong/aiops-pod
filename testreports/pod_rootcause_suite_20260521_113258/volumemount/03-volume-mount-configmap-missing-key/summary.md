# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 27.4m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| volume-mount-configmap-missing-key | 1 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 缺失, rc-volume-key-config | - | - | 100% | ✅ | 69s |
| volume-mount-configmap-missing-key | 2 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 缺失, rc-volume-key-config | - | - | 100% | ✅ | 69s |
| volume-mount-configmap-missing-key | 3 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 67s |
| volume-mount-configmap-missing-key | 4 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 65s |
| volume-mount-configmap-missing-key | 5 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 66s |
| volume-mount-configmap-missing-key | 6 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 缺失, rc-volume-key-config | - | - | 100% | ✅ | 60s |
| volume-mount-configmap-missing-key | 7 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 不存在, rc-volume-key-config | - | - | 100% | ✅ | 61s |
| volume-mount-configmap-missing-key | 8 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 60% | ✅ | 60s |
| volume-mount-configmap-missing-key | 9 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 缺失, rc-volume-key-config | - | - | 75% | ✅ | 66s |
| volume-mount-configmap-missing-key | 10 | L4 ❌ | ✅ | configmap, missing-key, couldn't find key≈缺少 key, rc-volume-key-config | - | - | 100% | ✅ | 70s |
| volume-mount-configmap-missing-key | 11 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 63s |
| volume-mount-configmap-missing-key | 12 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 69s |
| volume-mount-configmap-missing-key | 13 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 63s |
| volume-mount-configmap-missing-key | 14 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 68s |
| volume-mount-configmap-missing-key | 15 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 67s |
| volume-mount-configmap-missing-key | 16 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈缺少 key, rc-volume-key-config | - | - | 100% | ✅ | 61s |
| volume-mount-configmap-missing-key | 17 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈缺少 key, rc-volume-key-config | - | - | 100% | ✅ | 66s |
| volume-mount-configmap-missing-key | 18 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 64s |
| volume-mount-configmap-missing-key | 19 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 70s |
| volume-mount-configmap-missing-key | 20 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 75% | ✅ | 70s |
| volume-mount-configmap-missing-key | 21 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 64s |
| volume-mount-configmap-missing-key | 22 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 68s |
| volume-mount-configmap-missing-key | 23 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 65s |
| volume-mount-configmap-missing-key | 24 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 71s |
| volume-mount-configmap-missing-key | 25 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 63s |
| volume-mount-configmap-missing-key | 26 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 61s |
| volume-mount-configmap-missing-key | 27 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈缺少 key, rc-volume-key-config | - | - | 100% | ✅ | 60s |
| volume-mount-configmap-missing-key | 28 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 不存在, rc-volume-key-config | - | - | 100% | ✅ | 70s |
| volume-mount-configmap-missing-key | 29 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 缺失, rc-volume-key-config | - | - | 100% | ✅ | 59s |
| volume-mount-configmap-missing-key | 30 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈键错误, rc-volume-key-config | - | - | 100% | ✅ | 63s |
| volume-mount-configmap-missing-key | 31 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈缺少 key, rc-volume-key-config | - | - | 100% | ✅ | 66s |
| volume-mount-configmap-missing-key | 32 | L0 ✅ | ❌ | configmap, missing-key, couldn't find key≈key 不存在, rc-volume-key-config | - | persistentvolumeclaim, hostPath | 100% | ✅ | 71s |
| volume-mount-configmap-missing-key | 33 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 缺失, rc-volume-key-config | - | - | 100% | ✅ | 64s |
| volume-mount-configmap-missing-key | 34 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 缺失, rc-volume-key-config | - | - | 100% | ✅ | 65s |
| volume-mount-configmap-missing-key | 35 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 65s |
| volume-mount-configmap-missing-key | 36 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 62s |
| volume-mount-configmap-missing-key | 37 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 80% | ✅ | 70s |
| volume-mount-configmap-missing-key | 38 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 不存在, rc-volume-key-config | - | - | 75% | ✅ | 65s |
| volume-mount-configmap-missing-key | 39 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈键名不匹配, rc-volume-key-config | - | - | 100% | ✅ | 68s |
| volume-mount-configmap-missing-key | 40 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 62s |
| volume-mount-configmap-missing-key | 41 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 缺失, rc-volume-key-config | - | - | 100% | ✅ | 64s |
| volume-mount-configmap-missing-key | 42 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 67s |
| volume-mount-configmap-missing-key | 43 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 64s |
| volume-mount-configmap-missing-key | 44 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈缺少 key, rc-volume-key-config | - | - | 100% | ✅ | 61s |
| volume-mount-configmap-missing-key | 45 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 70s |
| volume-mount-configmap-missing-key | 46 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 66s |
| volume-mount-configmap-missing-key | 47 | L0 ✅ | ✅ | configmap, missing-key, rc-volume-key-config | - | - | 100% | ✅ | 62s |
| volume-mount-configmap-missing-key | 48 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈缺少 key, rc-volume-key-config | - | - | 100% | ✅ | 66s |
| volume-mount-configmap-missing-key | 49 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈key 不存在, rc-volume-key-config | - | - | 100% | ✅ | 67s |
| volume-mount-configmap-missing-key | 50 | L0 ✅ | ✅ | configmap, missing-key, couldn't find key≈缺少 key, rc-volume-key-config | - | - | 100% | ✅ | 65s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| volume-mount-configmap-missing-key | volumemount | 98.0% | 100.0% | 97.3% | 1.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 1.0m | ✅ |
| 根因准确率 | >= 60% | 98.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 97.3% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/volumemount/03-volume-mount-configmap-missing-key
