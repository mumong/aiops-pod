# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 78.1m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| configerror-configmap-key-missing-env | 1 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, ConfigMap key 缺失语义命中 | - | - | 100% | ✅ | 175s |
| configerror-configmap-key-missing-env | 2 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, CreateContainerConfigError | - | - | 100% | ❌ | 123s |
| configerror-configmap-key-missing-env | 3 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, couldn't find key≈key 不存在, rc-app-config, CreateContainerConfigError | - | - | 100% | ❌ | 159s |
| configerror-configmap-key-missing-env | 4 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 186s |
| configerror-configmap-key-missing-env | 5 | L0 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 158s |
| configerror-configmap-key-missing-env | 6 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 191s |
| configerror-configmap-key-missing-env | 7 | L3 ❌ | ❌ | CreateContainerConfigError | configmap, APP_BOOT_MODE | - | 100% | ❌ | 324s |
| configerror-configmap-key-missing-env | 8 | L3 ❌ | ❌ | - | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | 100% | ✅ | 201s |
| configerror-configmap-key-missing-env | 9 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 90% | ✅ | 184s |
| configerror-configmap-key-missing-env | 10 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 135s |
| configerror-configmap-key-missing-env | 11 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 160s |
| configerror-configmap-key-missing-env | 12 | L3 ❌ | ✅ | configmap, rc-app-config, CreateContainerConfigError, ConfigMap key 缺失语义命中 | - | - | 100% | ✅ | 150s |
| configerror-configmap-key-missing-env | 13 | L3 ❌ | ❌ | - | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | 88% | ✅ | 242s |
| configerror-configmap-key-missing-env | 14 | L3 ❌ | ❌ | - | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | 100% | ✅ | 161s |
| configerror-configmap-key-missing-env | 15 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config | - | - | 100% | ✅ | 219s |
| configerror-configmap-key-missing-env | 16 | L3 ❌ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | - | 100% | ✅ | 132s |
| configerror-configmap-key-missing-env | 17 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config | - | - | 100% | ❌ | 174s |
| configerror-configmap-key-missing-env | 18 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, CreateContainerConfigError | - | - | 100% | ✅ | 183s |
| configerror-configmap-key-missing-env | 19 | L3 ❌ | ✅ | configmap, rc-app-config, ConfigMap key 缺失语义命中 | - | - | 100% | ✅ | 220s |
| configerror-configmap-key-missing-env | 20 | L0 ❌ | ❌ | configmap, couldn't find key≈key 不存在, CreateContainerConfigError | APP_BOOT_MODE | - | 83% | ✅ | 183s |
| configerror-configmap-key-missing-env | 21 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config | - | - | 100% | ✅ | 164s |
| configerror-configmap-key-missing-env | 22 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, CreateContainerConfigError | - | - | 100% | ❌ | 139s |
| configerror-configmap-key-missing-env | 23 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 159s |
| configerror-configmap-key-missing-env | 24 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 245s |
| configerror-configmap-key-missing-env | 25 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, couldn't find key≈缺少 key, rc-app-config, CreateContainerConfigError | - | - | 90% | ✅ | 195s |
| configerror-configmap-key-missing-env | 26 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config | - | - | 89% | ✅ | 204s |
| configerror-configmap-key-missing-env | 27 | L3 ❌ | ❌ | - | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | 100% | ❌ | 156s |
| configerror-configmap-key-missing-env | 28 | L3 ❌ | ❌ | CreateContainerConfigError | configmap, APP_BOOT_MODE | - | 86% | ❌ | 149s |
| configerror-configmap-key-missing-env | 29 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, CreateContainerConfigError | - | - | 100% | ❌ | 185s |
| configerror-configmap-key-missing-env | 30 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, couldn't find key≈缺少 key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 149s |
| configerror-configmap-key-missing-env | 31 | L3 ❌ | ❌ | - | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | secret | 100% | ✅ | 218s |
| configerror-configmap-key-missing-env | 32 | L3 ❌ | ❌ | - | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | 100% | ❌ | 173s |
| configerror-configmap-key-missing-env | 33 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config | - | - | 100% | ✅ | 173s |
| configerror-configmap-key-missing-env | 34 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 196s |
| configerror-configmap-key-missing-env | 35 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 183s |
| configerror-configmap-key-missing-env | 36 | L3 ❌ | ❌ | configmap, APP_BOOT_MODE, rc-app-config | - | secret | 86% | ❌ | 154s |
| configerror-configmap-key-missing-env | 37 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, couldn't find key≈缺少 key, rc-app-config, CreateContainerConfigError | - | - | 86% | ✅ | 159s |
| configerror-configmap-key-missing-env | 38 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ❌ | 149s |
| configerror-configmap-key-missing-env | 39 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ❌ | 192s |
| configerror-configmap-key-missing-env | 40 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, couldn't find key≈键不存在, rc-app-config, CreateContainerConfigError | - | - | 71% | ✅ | 125s |
| configerror-configmap-key-missing-env | 41 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 89% | ✅ | 186s |
| configerror-configmap-key-missing-env | 42 | L3 ❌ | ❌ | configmap | APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | 89% | ✅ | 187s |
| configerror-configmap-key-missing-env | 43 | L3 ❌ | ❌ | configmap | APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | 100% | ✅ | 156s |
| configerror-configmap-key-missing-env | 44 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, CreateContainerConfigError | - | - | 100% | ✅ | 193s |
| configerror-configmap-key-missing-env | 45 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, rc-app-config | - | - | 100% | ✅ | 202s |
| configerror-configmap-key-missing-env | 46 | L3 ❌ | ✅ | configmap, rc-app-config, CreateContainerConfigError, ConfigMap key 缺失语义命中 | - | - | 100% | ✅ | 140s |
| configerror-configmap-key-missing-env | 47 | L3 ❌ | ✅ | configmap, APP_BOOT_MODE, couldn't find key≈key 缺失, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 184s |
| configerror-configmap-key-missing-env | 48 | L3 ❌ | ❌ | - | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | 88% | ✅ | 363s |
| configerror-configmap-key-missing-env | 49 | L3 ❌ | ❌ | - | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | 80% | ✅ | 227s |
| configerror-configmap-key-missing-env | 50 | L3 ❌ | ❌ | - | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | 67% | ✅ | 213s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| configerror-configmap-key-missing-env | configerror | 68.0% | 76.0% | 95.6% | 2.7m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.7m | ✅ |
| 根因准确率 | >= 60% | 68.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 76.0% | ✅ |
| 证据采集率 | >= 60% | 95.6% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/configerror/17-configerror-configmap-key-missing-env
