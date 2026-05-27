# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 39.0m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| pending-missing-pvc | 1 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 60% | ✅ | 92s |
| pending-missing-pvc | 2 | L0 ❌ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 84s |
| pending-missing-pvc | 3 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 60% | ✅ | 81s |
| pending-missing-pvc | 4 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 207s |
| pending-missing-pvc | 5 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 50% | ✅ | 79s |
| pending-missing-pvc | 6 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 60% | ✅ | 113s |
| pending-missing-pvc | 7 | L0 ❌ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 79s |
| pending-missing-pvc | 8 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 85s |
| pending-missing-pvc | 9 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 50% | ✅ | 99s |
| pending-missing-pvc | 10 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 50% | ✅ | 65s |
| pending-missing-pvc | 11 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 81s |
| pending-missing-pvc | 12 | L1 ✅ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 80% | ✅ | 83s |
| pending-missing-pvc | 13 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 50% | ✅ | 82s |
| pending-missing-pvc | 14 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 95s |
| pending-missing-pvc | 15 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 83s |
| pending-missing-pvc | 16 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 80% | ✅ | 92s |
| pending-missing-pvc | 17 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 84s |
| pending-missing-pvc | 18 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 80s |
| pending-missing-pvc | 19 | L0 ❌ | ✅ | not found≈missing, pvc, rc-pending-definitely-missing-pvc | - | - | 60% | ✅ | 93s |
| pending-missing-pvc | 20 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 80% | ✅ | 102s |
| pending-missing-pvc | 21 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 92s |
| pending-missing-pvc | 22 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 97s |
| pending-missing-pvc | 23 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 82s |
| pending-missing-pvc | 24 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 94s |
| pending-missing-pvc | 25 | L0 ❌ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 90s |
| pending-missing-pvc | 26 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 90s |
| pending-missing-pvc | 27 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 84s |
| pending-missing-pvc | 28 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 94s |
| pending-missing-pvc | 29 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 97s |
| pending-missing-pvc | 30 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 89s |
| pending-missing-pvc | 31 | L0 ❌ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 50% | ✅ | 79s |
| pending-missing-pvc | 32 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 91s |
| pending-missing-pvc | 33 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 93s |
| pending-missing-pvc | 34 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 87s |
| pending-missing-pvc | 35 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 50% | ✅ | 122s |
| pending-missing-pvc | 36 | L0 ❌ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 91s |
| pending-missing-pvc | 37 | L0 ❌ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 50% | ✅ | 82s |
| pending-missing-pvc | 38 | L0 ❌ | ✅ | not found≈missing, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 88s |
| pending-missing-pvc | 39 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 80% | ✅ | 97s |
| pending-missing-pvc | 40 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 87s |
| pending-missing-pvc | 41 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 77s |
| pending-missing-pvc | 42 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 80% | ✅ | 111s |
| pending-missing-pvc | 43 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 95s |
| pending-missing-pvc | 44 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 89s |
| pending-missing-pvc | 45 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 60% | ✅ | 92s |
| pending-missing-pvc | 46 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 88s |
| pending-missing-pvc | 47 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 84s |
| pending-missing-pvc | 48 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 67% | ✅ | 91s |
| pending-missing-pvc | 49 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 60% | ✅ | 98s |
| pending-missing-pvc | 50 | L0 ❌ | ✅ | not found, persistentvolumeclaim, pvc, rc-pending-definitely-missing-pvc | - | - | 75% | ✅ | 93s |

## 人工校正说明

- 校正时间: 2026-05-26
- 校正标准: 最终报告明确指出 Pod 引用的 PVC `rc-pending-definitely-missing-pvc` 在 `aiops-e2e` 命名空间不存在，并导致 `persistentvolumeclaim ... not found` 调度失败，判为根因正确。
- 误伤类型: `nodeSelector`、`configmap`、`secret` 出现在“已排除/无此依赖”的上下文中，不应计为冲突；`PersistentVolumeClaim`、`PVC not found`、PVC 名称等表达按语义命中处理。
- 人工校正后: 50/50 正确，根因准确率 100.0%。

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| pending-missing-pvc | pending | 100.0% | 100.0% | 68.2% | 1.1m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 1.1m | ✅ |
| 根因准确率 | >= 60% | 100.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 68.2% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/pending/09-pending-missing-pvc
