# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 76.2m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| crashloop-config-file-missing | 1 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing | - | - | 83% | ❌ | 141s |
| crashloop-config-file-missing | 2 | L3 ❌ | ❌ | not found≈缺失 | config, /etc/rootcause-app/config.yaml, config file missing | - | 86% | ✅ | 153s |
| crashloop-config-file-missing | 3 | L3 ❌ | ✅ | config, not found≈缺少, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 167s |
| crashloop-config-file-missing | 4 | L3 ❌ | ❌ | not found≈不存在 | config, /etc/rootcause-app/config.yaml, config file missing | - | 71% | ❌ | 123s |
| crashloop-config-file-missing | 5 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing≈配置文件缺失 | - | - | 100% | ✅ | 142s |
| crashloop-config-file-missing | 6 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 175s |
| crashloop-config-file-missing | 7 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 177s |
| crashloop-config-file-missing | 8 | L3 ❌ | ❌ | config | not found, /etc/rootcause-app/config.yaml, config file missing | - | 88% | ✅ | 197s |
| crashloop-config-file-missing | 9 | L3 ❌ | ✅ | config, not found≈no such, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 178s |
| crashloop-config-file-missing | 10 | L3 ❌ | ✅ | config, not found≈missing, config file missing≈配置文件缺失 | - | - | 88% | ✅ | 173s |
| crashloop-config-file-missing | 11 | L3 ❌ | ✅ | config, not found≈no such, /etc/rootcause-app/config.yaml, config file missing≈配置文件缺失 | - | - | 100% | ❌ | 142s |
| crashloop-config-file-missing | 12 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 100% | ❌ | 151s |
| crashloop-config-file-missing | 13 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 173s |
| crashloop-config-file-missing | 14 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing≈配置文件缺失 | - | - | 86% | ✅ | 139s |
| crashloop-config-file-missing | 15 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing | - | - | 100% | ✅ | 175s |
| crashloop-config-file-missing | 16 | L3 ❌ | ✅ | config, not found≈missing, config file missing≈配置文件缺失 | - | - | 43% | ✅ | 134s |
| crashloop-config-file-missing | 17 | L3 ❌ | ✅ | config, not found≈缺失, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 413s |
| crashloop-config-file-missing | 18 | L3 ❌ | ❌ | not found≈缺失 | config, /etc/rootcause-app/config.yaml, config file missing | - | 100% | ❌ | 142s |
| crashloop-config-file-missing | 19 | L3 ❌ | ✅ | config, not found≈找不到, /etc/rootcause-app/config.yaml, config file missing≈配置文件缺失 | - | - | 83% | ✅ | 184s |
| crashloop-config-file-missing | 20 | L3 ❌ | ✅ | config, not found≈no such, /etc/rootcause-app/config.yaml | - | - | 88% | ❌ | 260s |
| crashloop-config-file-missing | 21 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 78% | ✅ | 185s |
| crashloop-config-file-missing | 22 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 252s |
| crashloop-config-file-missing | 23 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing | - | - | 78% | ❌ | 131s |
| crashloop-config-file-missing | 24 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing≈配置文件缺失 | - | - | 89% | ✅ | 171s |
| crashloop-config-file-missing | 25 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing | - | - | 100% | ✅ | 173s |
| crashloop-config-file-missing | 26 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 100% | ❌ | 159s |
| crashloop-config-file-missing | 27 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing | - | - | 71% | ✅ | 137s |
| crashloop-config-file-missing | 28 | L3 ❌ | ❌ | not found≈不存在 | config, /etc/rootcause-app/config.yaml, config file missing | - | 100% | ✅ | 191s |
| crashloop-config-file-missing | 29 | L3 ❌ | ❌ | config, not found≈missing | /etc/rootcause-app/config.yaml, config file missing | - | 100% | ✅ | 169s |
| crashloop-config-file-missing | 30 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing | - | - | 100% | ✅ | 165s |
| crashloop-config-file-missing | 31 | L3 ❌ | ✅ | config, not found≈missing, config file missing | - | - | 90% | ❌ | 151s |
| crashloop-config-file-missing | 32 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 202s |
| crashloop-config-file-missing | 33 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing | - | - | 50% | ❌ | 181s |
| crashloop-config-file-missing | 34 | L3 ❌ | ❌ | - | config, not found, /etc/rootcause-app/config.yaml, config file missing | - | 100% | ✅ | 169s |
| crashloop-config-file-missing | 35 | L3 ❌ | ✅ | config, not found≈missing, config file missing | - | - | 100% | ✅ | 183s |
| crashloop-config-file-missing | 36 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing | - | - | 100% | ❌ | 149s |
| crashloop-config-file-missing | 37 | L3 ❌ | ✅ | config, not found≈缺失, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 194s |
| crashloop-config-file-missing | 38 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 88% | ❌ | 171s |
| crashloop-config-file-missing | 39 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 164s |
| crashloop-config-file-missing | 40 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing≈配置文件缺失 | - | - | 89% | ❌ | 136s |
| crashloop-config-file-missing | 41 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing≈配置文件缺失 | - | - | 100% | ✅ | 195s |
| crashloop-config-file-missing | 42 | L3 ❌ | ❌ | config, not found≈missing | /etc/rootcause-app/config.yaml, config file missing | - | 100% | ✅ | 227s |
| crashloop-config-file-missing | 43 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 184s |
| crashloop-config-file-missing | 44 | L3 ❌ | ❌ | config, not found≈缺少 | /etc/rootcause-app/config.yaml, config file missing | - | 88% | ✅ | 188s |
| crashloop-config-file-missing | 45 | L3 ❌ | ✅ | config, not found≈missing, config file missing≈配置文件缺失 | - | - | 100% | ✅ | 237s |
| crashloop-config-file-missing | 46 | L3 ❌ | ❌ | config, not found≈missing | /etc/rootcause-app/config.yaml, config file missing | - | 100% | ✅ | 222s |
| crashloop-config-file-missing | 47 | L3 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml | - | - | 78% | ✅ | 254s |
| crashloop-config-file-missing | 48 | L3 ❌ | ✅ | config, not found≈no such, /etc/rootcause-app/config.yaml | - | - | 100% | ✅ | 184s |
| crashloop-config-file-missing | 49 | L0 ❌ | ✅ | config, not found≈missing, /etc/rootcause-app/config.yaml, config file missing≈配置文件缺失 | - | - | 100% | ✅ | 249s |
| crashloop-config-file-missing | 50 | L3 ❌ | ✅ | config, not found≈no such, /etc/rootcause-app/config.yaml | - | - | 89% | ✅ | 169s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| crashloop-config-file-missing | crashloop | 80.0% | 74.0% | 92.0% | 2.5m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.5m | ✅ |
| 根因准确率 | >= 60% | 80.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 74.0% | ✅ |
| 证据采集率 | >= 60% | 92.0% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/crashloop/15-crashloop-config-file-missing
