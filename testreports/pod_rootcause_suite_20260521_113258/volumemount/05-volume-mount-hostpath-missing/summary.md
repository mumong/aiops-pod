# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 54.0m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| volume-mount-hostpath-missing | 1 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 59s |
| volume-mount-hostpath-missing | 2 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 80% | ✅ | 66s |
| volume-mount-hostpath-missing | 3 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 67s |
| volume-mount-hostpath-missing | 4 | L0 ✅ | ✅ | hostPath, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 85s |
| volume-mount-hostpath-missing | 5 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈不是目录, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 94s |
| volume-mount-hostpath-missing | 6 | L0 ✅ | ✅ | hostPath, not a directory≈目录不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 83% | ✅ | 102s |
| volume-mount-hostpath-missing | 7 | L0 ✅ | ✅ | hostPath, not a directory≈不是目录, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 91s |
| volume-mount-hostpath-missing | 8 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 87s |
| volume-mount-hostpath-missing | 9 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 101s |
| volume-mount-hostpath-missing | 10 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈目录不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 105s |
| volume-mount-hostpath-missing | 11 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 128s |
| volume-mount-hostpath-missing | 12 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 86% | ✅ | 112s |
| volume-mount-hostpath-missing | 13 | L0 ✅ | ✅ | hostPath, type check failed≈类型检查失败, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 85s |
| volume-mount-hostpath-missing | 14 | L0 ✅ | ✅ | hostPath, type check failed≈类型检查失败, not a directory≈目录不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 99s |
| volume-mount-hostpath-missing | 15 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 72s |
| volume-mount-hostpath-missing | 16 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 80% | ✅ | 87s |
| volume-mount-hostpath-missing | 17 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈目录不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 104s |
| volume-mount-hostpath-missing | 18 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 83% | ✅ | 89s |
| volume-mount-hostpath-missing | 19 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 92s |
| volume-mount-hostpath-missing | 20 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈目录不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 88s |
| volume-mount-hostpath-missing | 21 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈目录不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 95s |
| volume-mount-hostpath-missing | 22 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 80% | ✅ | 94s |
| volume-mount-hostpath-missing | 23 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 83% | ✅ | 107s |
| volume-mount-hostpath-missing | 24 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 93s |
| volume-mount-hostpath-missing | 25 | L0 ✅ | ✅ | hostPath, not a directory≈不是目录, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 111s |
| volume-mount-hostpath-missing | 26 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈不是目录, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 115s |
| volume-mount-hostpath-missing | 27 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈目录不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 93s |
| volume-mount-hostpath-missing | 28 | L0 ✅ | ✅ | hostPath, not a directory≈目录不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 101s |
| volume-mount-hostpath-missing | 29 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 91s |
| volume-mount-hostpath-missing | 30 | L0 ✅ | ✅ | hostPath, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 83s |
| volume-mount-hostpath-missing | 31 | L0 ✅ | ✅ | hostPath, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 87s |
| volume-mount-hostpath-missing | 32 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 83% | ✅ | 85s |
| volume-mount-hostpath-missing | 33 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 90s |
| volume-mount-hostpath-missing | 34 | L0 ✅ | ✅ | hostPath, type check failed≈类型检查失败, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 90s |
| volume-mount-hostpath-missing | 35 | L0 ✅ | ✅ | hostPath, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 104s |
| volume-mount-hostpath-missing | 36 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 96s |
| volume-mount-hostpath-missing | 37 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 110s |
| volume-mount-hostpath-missing | 38 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 80% | ✅ | 86s |
| volume-mount-hostpath-missing | 39 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 103s |
| volume-mount-hostpath-missing | 40 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈目录不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 91s |
| volume-mount-hostpath-missing | 41 | L0 ✅ | ✅ | hostPath, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 83% | ✅ | 108s |
| volume-mount-hostpath-missing | 42 | L0 ✅ | ✅ | hostPath, not a directory≈不是目录, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 111s |
| volume-mount-hostpath-missing | 43 | L0 ✅ | ✅ | hostPath, not a directory≈目录不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 71% | ✅ | 104s |
| volume-mount-hostpath-missing | 44 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 83% | ✅ | 90s |
| volume-mount-hostpath-missing | 45 | L0 ✅ | ✅ | hostPath, type check failed≈类型检查失败, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 89s |
| volume-mount-hostpath-missing | 46 | L0 ✅ | ✅ | hostPath, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 986s |
| volume-mount-hostpath-missing | 47 | UNKNOWN ❌ | ❌ | - | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | N/A | ❌ | 950s |
| volume-mount-hostpath-missing | 48 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 99s |
| volume-mount-hostpath-missing | 49 | L0 ✅ | ✅ | hostPath, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 88s |
| volume-mount-hostpath-missing | 50 | L0 ✅ | ✅ | hostPath, type check failed, not a directory≈路径不存在, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 80% | ✅ | 80s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| volume-mount-hostpath-missing | volumemount | 98.0% | 98.0% | 94.4% | 1.6m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 1.6m | ✅ |
| 根因准确率 | >= 60% | 98.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 98.0% | ✅ |
| 证据采集率 | >= 60% | 94.4% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/volumemount/05-volume-mount-hostpath-missing
