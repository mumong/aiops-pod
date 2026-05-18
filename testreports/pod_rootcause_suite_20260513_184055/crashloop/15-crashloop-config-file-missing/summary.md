# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 152.4m
- 人工语义修正: 43 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| crashloop-config-file-missing | 1 | L4 ❌ | ❌ | config, /etc/rootcause-app/config.yaml, config file missing | not found | - | N/A | ✅ | 58s |
| crashloop-config-file-missing | 2 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 75% | ✅ | 511s |
| crashloop-config-file-missing | 3 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 67% | ✅ | 357s |
| crashloop-config-file-missing | 4 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 465s |
| crashloop-config-file-missing | 5 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 369s |
| crashloop-config-file-missing | 6 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 384s |
| crashloop-config-file-missing | 7 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 354s |
| crashloop-config-file-missing | 8 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 386s |
| crashloop-config-file-missing | 9 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 67% | ✅ | 470s |
| crashloop-config-file-missing | 10 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 401s |
| crashloop-config-file-missing | 11 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 412s |
| crashloop-config-file-missing | 12 | L4 ❌ | ❌ | config, /etc/rootcause-app/config.yaml, config file missing | not found | - | N/A | ✅ | 66s |
| crashloop-config-file-missing | 13 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | N/A | ✅ | 75s |
| crashloop-config-file-missing | 14 | L4 ❌ | ❌ | config, /etc/rootcause-app/config.yaml, config file missing | not found | - | N/A | ✅ | 54s |
| crashloop-config-file-missing | 15 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 435s |
| crashloop-config-file-missing | 16 | L4 ❌ | ❌ | config, /etc/rootcause-app/config.yaml, config file missing | not found | - | 60% | ✅ | 484s |
| crashloop-config-file-missing | 17 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 501s |
| crashloop-config-file-missing | 18 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 50% | ✅ | 393s |
| crashloop-config-file-missing | 19 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 409s |
| crashloop-config-file-missing | 20 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 483s |
| crashloop-config-file-missing | 21 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 361s |
| crashloop-config-file-missing | 22 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 384s |
| crashloop-config-file-missing | 23 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 444s |
| crashloop-config-file-missing | 24 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 75% | ✅ | 443s |
| crashloop-config-file-missing | 25 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 406s |
| crashloop-config-file-missing | 26 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 526s |
| crashloop-config-file-missing | 27 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 303s |
| crashloop-config-file-missing | 28 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 381s |
| crashloop-config-file-missing | 29 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 75% | ✅ | 530s |
| crashloop-config-file-missing | 30 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 245s |
| crashloop-config-file-missing | 31 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 465s |
| crashloop-config-file-missing | 32 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 430s |
| crashloop-config-file-missing | 33 | L4 ❌ | ❌ | config, /etc/rootcause-app/config.yaml, config file missing | not found | - | 100% | ✅ | 397s |
| crashloop-config-file-missing | 34 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 416s |
| crashloop-config-file-missing | 35 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 306s |
| crashloop-config-file-missing | 36 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 289s |
| crashloop-config-file-missing | 37 | L4 ❌ | ❌ | config, /etc/rootcause-app/config.yaml, config file missing | not found | - | N/A | ✅ | 40s |
| crashloop-config-file-missing | 38 | L4 ❌ | ❌ | config, /etc/rootcause-app/config.yaml, config file missing | not found | - | N/A | ✅ | 44s |
| crashloop-config-file-missing | 39 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 396s |
| crashloop-config-file-missing | 40 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 67% | ✅ | 470s |
| crashloop-config-file-missing | 41 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 75% | ✅ | 418s |
| crashloop-config-file-missing | 42 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 404s |
| crashloop-config-file-missing | 43 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 67% | ✅ | 311s |
| crashloop-config-file-missing | 44 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 342s |
| crashloop-config-file-missing | 45 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 394s |
| crashloop-config-file-missing | 46 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 403s |
| crashloop-config-file-missing | 47 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 357s |
| crashloop-config-file-missing | 48 | L2 ✅ | ✅ | config, /etc/rootcause-app/config.yaml, config file missing, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 446s |
| crashloop-config-file-missing | 49 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 463s |
| crashloop-config-file-missing | 50 | L4 ❌ | ✅ | config, /etc/rootcause-app/config.yaml, 语义等价修正: 配置文件缺失/不存在 等价 not found | - | - | 100% | ✅ | 335s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| crashloop-config-file-missing | crashloop | 86.0% | 100.0% | 92.7% | 5.6m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 5.6m | ✅ |
| 根因准确率 | >= 60% | 86.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 92.7% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/crashloop/15-crashloop-config-file-missing
