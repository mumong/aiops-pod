# Pod Abnormal E2E

这个目录用于新的异常 Pod 场景验收，不复用旧的 L0-L4 主矩阵评分方式。旧目录 `test/e2e` 仍负责故障注入 manifest；本目录负责按 `pod_abnormal_type` 评估 `/ask` 输出质量。

## 覆盖指标

| 指标 | 说明 |
|------|------|
| MTTR | 从请求发出到完整报告返回的耗时，优先取报告里的 `总耗时`，回退到 HTTP wall clock |
| 根因准确率 | 报告必须命中期望 `pod_abnormal_type`/关键根因词，并且不能只停留在宽泛 L0-L4 |
| 证据完整率 | 优先读取系统输出的 `计划 N 项，实际采集 M 项` 或 `证据: M/N 项` |
| Runbook 覆盖率 | 报告、诊断追踪、工具日志中命中期望 runbook ID 即算通过 |

## 使用方式

```bash
cd test/pod_abnormal_e2e

# 1. 部署旧 e2e manifests
../e2e/run_all.sh

# 2. 确认故障注入状态
../e2e/validate.sh

# 3. 运行单个异常 Pod 场景
./run.sh --case oomkilled-memory-limit

# 4. 运行全部 enabled case
./run.sh --case all -n 1 -c 1

# 5. 多轮稳定性测试
./run.sh --case all -n 3 -c 2 --url http://10.2.0.48:30800
```

## Case 文件

`cases.yaml` 是唯一的 case 数据源。每个 case 包含：

- `expected_pod_abnormal_type`: 期望的异常 Pod 类型，例如 `OOMKilled`、`ImagePullFailed`
- `expected_layer`: 兼容层级，只作为辅助校验
- `expected_runbooks`: 期望命中的 runbook ID
- `root_cause_keywords`: 根因准确率关键词
- `evidence_keywords`: 证据链必须覆盖的关键证据词

`node-lost-unknown-manual` 默认禁用，因为它需要人工制造节点 NotReady/Unknown。

## 输出

默认输出到 `testreports/pod_abnormal_<timestamp>/`：

- `<case_id>/response_N.md`: 每次请求完整报告
- `stats.json`: 结构化统计
- `summary.md`: 人类可读汇总
