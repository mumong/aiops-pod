# Pod RootCause E2E 精确根因报告

- 模型: deepseek
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 69.1m

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| configerror-secret-key-missing-env | 1 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret | - | - | 86% | ❌ | 139s |
| configerror-secret-key-missing-env | 2 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 143s |
| configerror-secret-key-missing-env | 3 | L3 ❌ | ❌ | secret | APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 100% | ✅ | 151s |
| configerror-secret-key-missing-env | 4 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret | - | - | 100% | ✅ | 166s |
| configerror-secret-key-missing-env | 5 | L4 ✅ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 67% | ✅ | 161s |
| configerror-secret-key-missing-env | 6 | L3 ❌ | ❌ | secret | APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 100% | ✅ | 161s |
| configerror-secret-key-missing-env | 7 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 139s |
| configerror-secret-key-missing-env | 8 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 88% | ❌ | 147s |
| configerror-secret-key-missing-env | 9 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret | - | - | 83% | ✅ | 164s |
| configerror-secret-key-missing-env | 10 | L3 ❌ | ❌ | - | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 100% | ✅ | 126s |
| configerror-secret-key-missing-env | 11 | L3 ❌ | ❌ | - | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 100% | ✅ | 120s |
| configerror-secret-key-missing-env | 12 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 145s |
| configerror-secret-key-missing-env | 13 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret | - | - | 100% | ❌ | 195s |
| configerror-secret-key-missing-env | 14 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 140s |
| configerror-secret-key-missing-env | 15 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 137s |
| configerror-secret-key-missing-env | 16 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 141s |
| configerror-secret-key-missing-env | 17 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 139s |
| configerror-secret-key-missing-env | 18 | L3 ❌ | ✅ | secret, rc-app-secret, Secret key 缺失语义命中 | - | - | 100% | ✅ | 132s |
| configerror-secret-key-missing-env | 19 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ❌ | 133s |
| configerror-secret-key-missing-env | 20 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret | - | - | 100% | ✅ | 162s |
| configerror-secret-key-missing-env | 21 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 122s |
| configerror-secret-key-missing-env | 22 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 216s |
| configerror-secret-key-missing-env | 23 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 144s |
| configerror-secret-key-missing-env | 24 | L3 ❌ | ❌ | - | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 100% | ✅ | 491s |
| configerror-secret-key-missing-env | 25 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 89% | ✅ | 217s |
| configerror-secret-key-missing-env | 26 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 133s |
| configerror-secret-key-missing-env | 27 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 90% | ✅ | 228s |
| configerror-secret-key-missing-env | 28 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key≈key 缺失, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 147s |
| configerror-secret-key-missing-env | 29 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key≈key 缺失, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 139s |
| configerror-secret-key-missing-env | 30 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key≈键名不匹配, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 206s |
| configerror-secret-key-missing-env | 31 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret | - | - | 100% | ✅ | 173s |
| configerror-secret-key-missing-env | 32 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret | - | - | 100% | ✅ | 171s |
| configerror-secret-key-missing-env | 33 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 157s |
| configerror-secret-key-missing-env | 34 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret | - | - | 88% | ✅ | 161s |
| configerror-secret-key-missing-env | 35 | L3 ❌ | ❌ | - | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 89% | ❌ | 149s |
| configerror-secret-key-missing-env | 36 | L3 ❌ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | - | 100% | ✅ | 203s |
| configerror-secret-key-missing-env | 37 | L3 ❌ | ❌ | - | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 100% | ✅ | 206s |
| configerror-secret-key-missing-env | 38 | L3 ❌ | ❌ | secret | APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 100% | ✅ | 162s |
| configerror-secret-key-missing-env | 39 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 88% | ✅ | 201s |
| configerror-secret-key-missing-env | 40 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret | - | - | 100% | ✅ | 142s |
| configerror-secret-key-missing-env | 41 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, rc-app-secret, CreateContainerConfigError | - | - | 88% | ✅ | 129s |
| configerror-secret-key-missing-env | 42 | L3 ❌ | ❌ | secret | APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 100% | ✅ | 175s |
| configerror-secret-key-missing-env | 43 | L3 ❌ | ❌ | secret | APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 100% | ✅ | 112s |
| configerror-secret-key-missing-env | 44 | L3 ❌ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | - | 75% | ❌ | 142s |
| configerror-secret-key-missing-env | 45 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key≈键不存在, rc-app-secret, CreateContainerConfigError | - | - | 88% | ❌ | 134s |
| configerror-secret-key-missing-env | 46 | L3 ❌ | ✅ | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | - | 100% | ✅ | 185s |
| configerror-secret-key-missing-env | 47 | L3 ❌ | ❌ | - | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 86% | ✅ | 173s |
| configerror-secret-key-missing-env | 48 | L3 ❌ | ❌ | - | secret, APP_SECRET_TOKEN, couldn't find key, rc-app-secret, CreateContainerConfigError | - | 70% | ❌ | 124s |
| configerror-secret-key-missing-env | 49 | L3 ❌ | ✅ | secret, rc-app-secret, CreateContainerConfigError, Secret key 缺失语义命中 | - | - | 90% | ✅ | 142s |
| configerror-secret-key-missing-env | 50 | L3 ❌ | ❌ | secret, CreateContainerConfigError | APP_SECRET_TOKEN | - | 80% | ✅ | 146s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| configerror-secret-key-missing-env | configerror | 70.0% | 84.0% | 94.8% | 2.3m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 2.3m | ✅ |
| 根因准确率 | >= 60% | 70.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 84.0% | ✅ |
| 证据采集率 | >= 60% | 94.8% | ✅ |

报告目录: /root/huhu/agent/combine-aiops-mcp/robusta/testreports/pod_rootcause_suite_20260521_113258/configerror/18-configerror-secret-key-missing-env
