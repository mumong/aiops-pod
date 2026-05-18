# Pod RootCause E2E 精确根因报告

- 模型: openai/Qwen3-32B-AWQ
- 总运行: 50
- 成功: 50
- 失败: 0
- 总耗时: 142.3m
- 人工语义修正: 29 条（仅修正中文/英文等价表达导致的误判）

## 运行明细

| Case | # | 层级 | 根因 | 命中关键词 | 缺失关键词 | 冲突关键词 | 证据 | Runbook | 耗时 |
|------|---|------|------|------------|------------|------------|------|---------|------|
| configerror-env-missing | 1 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required | - | - | 100% | ✅ | 376s |
| configerror-env-missing | 2 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 329s |
| configerror-env-missing | 3 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required | - | - | 100% | ✅ | 343s |
| configerror-env-missing | 4 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 412s |
| configerror-env-missing | 5 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 67% | ✅ | 399s |
| configerror-env-missing | 6 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 322s |
| configerror-env-missing | 7 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 362s |
| configerror-env-missing | 8 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 75% | ✅ | 376s |
| configerror-env-missing | 9 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 340s |
| configerror-env-missing | 10 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 371s |
| configerror-env-missing | 11 | L4 ✅ | ✅ | APP_BOOT_MODE, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 339s |
| configerror-env-missing | 12 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 375s |
| configerror-env-missing | 13 | L4 ✅ | ❌ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | configmap | 100% | ✅ | 374s |
| configerror-env-missing | 14 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 306s |
| configerror-env-missing | 15 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 374s |
| configerror-env-missing | 16 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 499s |
| configerror-env-missing | 17 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 60% | ✅ | 339s |
| configerror-env-missing | 18 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 67% | ✅ | 369s |
| configerror-env-missing | 19 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 67% | ✅ | 244s |
| configerror-env-missing | 20 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 304s |
| configerror-env-missing | 21 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 259s |
| configerror-env-missing | 22 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 294s |
| configerror-env-missing | 23 | L4 ✅ | ✅ | APP_BOOT_MODE, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 329s |
| configerror-env-missing | 24 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 75% | ✅ | 382s |
| configerror-env-missing | 25 | L4 ✅ | ✅ | APP_BOOT_MODE, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 319s |
| configerror-env-missing | 26 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 323s |
| configerror-env-missing | 27 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 328s |
| configerror-env-missing | 28 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 238s |
| configerror-env-missing | 29 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required | - | - | 67% | ✅ | 304s |
| configerror-env-missing | 30 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 352s |
| configerror-env-missing | 31 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 276s |
| configerror-env-missing | 32 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 344s |
| configerror-env-missing | 33 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 40% | ✅ | 524s |
| configerror-env-missing | 34 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 378s |
| configerror-env-missing | 35 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 368s |
| configerror-env-missing | 36 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 75% | ✅ | 377s |
| configerror-env-missing | 37 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 75% | ✅ | 396s |
| configerror-env-missing | 38 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 67% | ✅ | 325s |
| configerror-env-missing | 39 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 207s |
| configerror-env-missing | 40 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 75% | ✅ | 420s |
| configerror-env-missing | 41 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 349s |
| configerror-env-missing | 42 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required | - | - | 100% | ✅ | 290s |
| configerror-env-missing | 43 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required | - | - | 100% | ✅ | 380s |
| configerror-env-missing | 44 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 231s |
| configerror-env-missing | 45 | L4 ✅ | ✅ | APP_BOOT_MODE, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 268s |
| configerror-env-missing | 46 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 0% | ✅ | 189s |
| configerror-env-missing | 47 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 390s |
| configerror-env-missing | 48 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 80% | ✅ | 458s |
| configerror-env-missing | 49 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL, 语义等价修正: APP_BOOT_MODE 缺失 | - | - | 100% | ✅ | 233s |
| configerror-env-missing | 50 | L4 ✅ | ✅ | APP_BOOT_MODE, missing required, L4_CONFIG_BOOTSTRAP_FAIL | - | - | 100% | ✅ | 260s |

## 场景汇总

| Case | Group | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 成功运行 |
|------|-------|------------|----------------|------------|-----------|----------|
| configerror-env-missing | configerror | 98.0% | 100.0% | 89.8% | 5.2m | 50/50 |

## 质量指标汇总

| 指标 | 阈值 | 实际 | 状态 |
|------|------|------|------|
| MTTR | < 15m | 5.2m | ✅ |
| 根因准确率 | >= 60% | 98.0% | ✅ |
| Runbook 覆盖率 | >= 60% | 100.0% | ✅ |
| 证据采集率 | >= 60% | 89.8% | ✅ |

报告目录: testreports/pod_rootcause_suite_20260513_184055/configerror/16-configerror-env-missing
