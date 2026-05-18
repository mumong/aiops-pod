# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 109.3m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| configerror-configmap-key-missing-env | 1 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 208s |
| configerror-configmap-key-missing-env | 2 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 205s |
| configerror-configmap-key-missing-env | 3 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 221s |
| configerror-configmap-key-missing-env | 4 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 256s |
| configerror-configmap-key-missing-env | 5 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 289s |
| configerror-configmap-key-missing-env | 6 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 240s |
| configerror-configmap-key-missing-env | 7 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 259s |
| configerror-configmap-key-missing-env | 8 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 410s |
| configerror-configmap-key-missing-env | 9 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 292s |
| configerror-configmap-key-missing-env | 10 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 67% | ✅ | 258s |
| configerror-configmap-key-missing-env | 11 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 316s |
| configerror-configmap-key-missing-env | 12 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 215s |
| configerror-configmap-key-missing-env | 13 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 292s |
| configerror-configmap-key-missing-env | 14 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | N/A | ✅ | 63s |
| configerror-configmap-key-missing-env | 15 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 239s |
| configerror-configmap-key-missing-env | 16 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 67% | ✅ | 251s |
| configerror-configmap-key-missing-env | 17 | L4 ✅ | ❌ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | OOMKilled | N/A | ✅ | 89s |
| configerror-configmap-key-missing-env | 18 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 263s |
| configerror-configmap-key-missing-env | 19 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 67% | ✅ | 278s |
| configerror-configmap-key-missing-env | 20 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 75% | ✅ | 424s |
| configerror-configmap-key-missing-env | 21 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 175s |
| configerror-configmap-key-missing-env | 22 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 282s |
| configerror-configmap-key-missing-env | 23 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | N/A | ✅ | 51s |
| configerror-configmap-key-missing-env | 24 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 234s |
| configerror-configmap-key-missing-env | 25 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 224s |
| configerror-configmap-key-missing-env | 26 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 277s |
| configerror-configmap-key-missing-env | 27 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 255s |
| configerror-configmap-key-missing-env | 28 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 261s |
| configerror-configmap-key-missing-env | 29 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 194s |
| configerror-configmap-key-missing-env | 30 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 236s |
| configerror-configmap-key-missing-env | 31 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 244s |
| configerror-configmap-key-missing-env | 32 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | - | 100% | ✅ | 243s |
| configerror-configmap-key-missing-env | 33 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | - | 67% | ✅ | 232s |
| configerror-configmap-key-missing-env | 34 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | secret | 67% | ✅ | 296s |
| configerror-configmap-key-missing-env | 35 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | - | 100% | ✅ | 290s |
| configerror-configmap-key-missing-env | 36 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | - | 100% | ✅ | 345s |
| configerror-configmap-key-missing-env | 37 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | secret | 100% | ✅ | 293s |
| configerror-configmap-key-missing-env | 38 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 290s |
| configerror-configmap-key-missing-env | 39 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | - | 100% | ✅ | 253s |
| configerror-configmap-key-missing-env | 40 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, CreateContainerConfigError | - | - | 100% | ✅ | 321s |
| configerror-configmap-key-missing-env | 41 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | - | 100% | ✅ | 489s |
| configerror-configmap-key-missing-env | 42 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, couldn't find key, rc-app-config, CreateContainerConfigError | - | - | 33% | ✅ | 217s |
| configerror-configmap-key-missing-env | 43 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 75% | ✅ | 349s |
| configerror-configmap-key-missing-env | 44 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | - | 67% | ✅ | 271s |
| configerror-configmap-key-missing-env | 45 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | - | 100% | ✅ | 240s |
| configerror-configmap-key-missing-env | 46 | L4 ✅ | ✅ | configmap, APP_BOOT_MODE, rc-app-config, CreateContainerConfigError | - | - | 100% | ✅ | 318s |
| configerror-configmap-key-missing-env | 47 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | - | 100% | ✅ | 201s |
| configerror-configmap-key-missing-env | 48 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | - | 100% | ✅ | 276s |
| configerror-configmap-key-missing-env | 49 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | secret | 75% | ✅ | 238s |
| configerror-configmap-key-missing-env | 50 | L4 ✅ | ❌ | configmap, CreateContainerConfigError | APP_BOOT_MODE | secret | 75% | ✅ | 254s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| configerror-configmap-key-missing-env | configerror | 70.0% | 100.0% | 92.2% | 3.8m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 3.8m | ✅ |
| 根因准确率 | >= 60% | 70.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 92.2% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/configerror/17-configerror-configmap-key-missing-env
