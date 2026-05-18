# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 111.8m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| configerror-secret-key-missing-env | 1 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 273s |
| configerror-secret-key-missing-env | 2 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 263s |
| configerror-secret-key-missing-env | 3 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 249s |
| configerror-secret-key-missing-env | 4 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 268s |
| configerror-secret-key-missing-env | 5 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 291s |
| configerror-secret-key-missing-env | 6 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | N/A | ✅ | 106s |
| configerror-secret-key-missing-env | 7 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 346s |
| configerror-secret-key-missing-env | 8 | L4 ✅ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | - | 100% | ✅ | 159s |
| configerror-secret-key-missing-env | 9 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 205s |
| configerror-secret-key-missing-env | 10 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 233s |
| configerror-secret-key-missing-env | 11 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 25% | ✅ | 321s |
| configerror-secret-key-missing-env | 12 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 293s |
| configerror-secret-key-missing-env | 13 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 289s |
| configerror-secret-key-missing-env | 14 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 67% | ✅ | 236s |
| configerror-secret-key-missing-env | 15 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 67% | ✅ | 242s |
| configerror-secret-key-missing-env | 16 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 305s |
| configerror-secret-key-missing-env | 17 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 314s |
| configerror-secret-key-missing-env | 18 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 266s |
| configerror-secret-key-missing-env | 19 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 276s |
| configerror-secret-key-missing-env | 20 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 453s |
| configerror-secret-key-missing-env | 21 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 212s |
| configerror-secret-key-missing-env | 22 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 67% | ✅ | 252s |
| configerror-secret-key-missing-env | 23 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 284s |
| configerror-secret-key-missing-env | 24 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 67% | ✅ | 290s |
| configerror-secret-key-missing-env | 25 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 313s |
| configerror-secret-key-missing-env | 26 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 279s |
| configerror-secret-key-missing-env | 27 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 67% | ✅ | 350s |
| configerror-secret-key-missing-env | 28 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 198s |
| configerror-secret-key-missing-env | 29 | L4 ✅ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | configmap | 50% | ✅ | 272s |
| configerror-secret-key-missing-env | 30 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 75% | ✅ | 262s |
| configerror-secret-key-missing-env | 31 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | N/A | ✅ | 39s |
| configerror-secret-key-missing-env | 32 | L4 ✅ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | configmap | 100% | ✅ | 260s |
| configerror-secret-key-missing-env | 33 | L4 ✅ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | configmap | N/A | ✅ | 39s |
| configerror-secret-key-missing-env | 34 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 249s |
| configerror-secret-key-missing-env | 35 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 298s |
| configerror-secret-key-missing-env | 36 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 314s |
| configerror-secret-key-missing-env | 37 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 339s |
| configerror-secret-key-missing-env | 38 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 251s |
| configerror-secret-key-missing-env | 39 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 228s |
| configerror-secret-key-missing-env | 40 | L4 ✅ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | configmap | 67% | ✅ | 263s |
| configerror-secret-key-missing-env | 41 | L4 ✅ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | configmap | 67% | ✅ | 299s |
| configerror-secret-key-missing-env | 42 | L4 ✅ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | configmap | 75% | ✅ | 268s |
| configerror-secret-key-missing-env | 43 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 309s |
| configerror-secret-key-missing-env | 44 | L4 ✅ | ❌ | CreateContainerConfigError | secret, APP_SECRET_TOKEN | configmap | 75% | ✅ | 319s |
| configerror-secret-key-missing-env | 45 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 286s |
| configerror-secret-key-missing-env | 46 | L4 ✅ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | configmap | 100% | ✅ | 427s |
| configerror-secret-key-missing-env | 47 | L4 ✅ | ❌ | CreateContainerConfigError | secret, APP_SECRET_TOKEN | configmap | 75% | ✅ | 235s |
| configerror-secret-key-missing-env | 48 | L4 ✅ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | configmap | 100% | ✅ | 267s |
| configerror-secret-key-missing-env | 49 | L4 ✅ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | configmap | 75% | ✅ | 406s |
| configerror-secret-key-missing-env | 50 | L4 ✅ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | configmap | 100% | ✅ | 209s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| configerror-secret-key-missing-env | configerror | 74.0% | 100.0% | 89.7% | 4.0m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 4.0m | ✅ |
| 根因准确率 | >= 60% | 74.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 89.7% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260513_184055/configerror/18-configerror-secret-key-missing-env
