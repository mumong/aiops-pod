# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 131.8m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| volume-mount-hostpath-missing | 1 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 284s |
| volume-mount-hostpath-missing | 2 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 285s |
| volume-mount-hostpath-missing | 3 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 253s |
| volume-mount-hostpath-missing | 4 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 261s |
| volume-mount-hostpath-missing | 5 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 233s |
| volume-mount-hostpath-missing | 6 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 339s |
| volume-mount-hostpath-missing | 7 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 255s |
| volume-mount-hostpath-missing | 8 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 33% | ✅ | 310s |
| volume-mount-hostpath-missing | 9 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 255s |
| volume-mount-hostpath-missing | 10 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 230s |
| volume-mount-hostpath-missing | 11 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 50% | ✅ | 245s |
| volume-mount-hostpath-missing | 12 | L0 ✅ | ✅ | hostPath, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 204s |
| volume-mount-hostpath-missing | 13 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 336s |
| volume-mount-hostpath-missing | 14 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 347s |
| volume-mount-hostpath-missing | 15 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 319s |
| volume-mount-hostpath-missing | 16 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 306s |
| volume-mount-hostpath-missing | 17 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 353s |
| volume-mount-hostpath-missing | 18 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 283s |
| volume-mount-hostpath-missing | 19 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 405s |
| volume-mount-hostpath-missing | 20 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 75% | ✅ | 388s |
| volume-mount-hostpath-missing | 21 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 279s |
| volume-mount-hostpath-missing | 22 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 397s |
| volume-mount-hostpath-missing | 23 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 33% | ✅ | 370s |
| volume-mount-hostpath-missing | 24 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 253s |
| volume-mount-hostpath-missing | 25 | L3 ❌ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 284s |
| volume-mount-hostpath-missing | 26 | L3 ❌ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 360s |
| volume-mount-hostpath-missing | 27 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 370s |
| volume-mount-hostpath-missing | 28 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 50% | ✅ | 497s |
| volume-mount-hostpath-missing | 29 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 33% | ✅ | 218s |
| volume-mount-hostpath-missing | 30 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 259s |
| volume-mount-hostpath-missing | 31 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 291s |
| volume-mount-hostpath-missing | 32 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 33% | ✅ | 273s |
| volume-mount-hostpath-missing | 33 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 331s |
| volume-mount-hostpath-missing | 34 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 75% | ✅ | 425s |
| volume-mount-hostpath-missing | 35 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 75% | ✅ | 275s |
| volume-mount-hostpath-missing | 36 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 249s |
| volume-mount-hostpath-missing | 37 | L0 ✅ | ✅ | hostPath, type check failed, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 327s |
| volume-mount-hostpath-missing | 38 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 305s |
| volume-mount-hostpath-missing | 39 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 286s |
| volume-mount-hostpath-missing | 40 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 528s |
| volume-mount-hostpath-missing | 41 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 254s |
| volume-mount-hostpath-missing | 42 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 33% | ✅ | 330s |
| volume-mount-hostpath-missing | 43 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 75% | ✅ | 289s |
| volume-mount-hostpath-missing | 44 | L0 ✅ | ✅ | hostPath, not a directory, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 67% | ✅ | 342s |
| volume-mount-hostpath-missing | 45 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 75% | ✅ | 338s |
| volume-mount-hostpath-missing | 46 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 50% | ✅ | 320s |
| volume-mount-hostpath-missing | 47 | L3 ❌ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 33% | ✅ | 412s |
| volume-mount-hostpath-missing | 48 | L0 ✅ | ✅ | hostPath, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 355s |
| volume-mount-hostpath-missing | 49 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 269s |
| volume-mount-hostpath-missing | 50 | L0 ✅ | ✅ | hostPath, type check failed, aiops-rootcause-definitely-missing-hostpath-dir | - | - | 100% | ✅ | 278s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| volume-mount-hostpath-missing | volumemount | 100.0% | 100.0% | 73.8% | 4.7m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 4.7m | ✅ |
| 根因准确率 | >= 60% | 100.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 73.8% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260513_184055/volumemount/05-volume-mount-hostpath-missing
