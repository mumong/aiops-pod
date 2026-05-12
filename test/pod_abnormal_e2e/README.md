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

# 1. 手动 apply 一个 case，例如 ImagePullBackOff
kubectl apply -f ../e2e/manifests/00-namespace.yaml
kubectl apply -f ../e2e/manifests/l3-imagepull-fail-victim.yaml

# 2. 等待 Pod 进入预期异常状态
kubectl -n aiops-e2e get pod imagepull-fail-victim -w

# 3. 使用类似旧 test_accuracy.py 的方式并发测试
.venv/bin/python run_pod_abnormal_cases.py \
  --scenario imagepullbackoff \
  -n 50 -c 5 \
  -q "我的集群有什么问题" \
  --url http://10.2.0.48:30800
```

也可以使用 shell 包装：

```bash
./run.sh --scenario imagepullbackoff -n 50 -c 5 -q "我的集群有什么问题"
```

如果要一次部署所有默认场景，仍可复用旧部署脚本：

```bash
../e2e/run_all.sh
../e2e/validate.sh
./run.sh --scenario all -n 1 -c 1
```

## Pod 异常状态 Case 矩阵

| Scenario/Alias | Pod 异常类型 | 典型状态 | Manifest | Runbook |
|---|---|---|---|---|
| `evicted` | `Evicted` | `Evicted` | `../e2e/manifests/l0-logfill-enospc.yaml` | `l0-volume-limit` |
| `volumemountfailed` | `VolumeMountFailed` | `Pending` / `ContainerCreating` | `../e2e/manifests/pod-volume-mount-failed.yaml` | `pod-volume-mount-failed` |
| `pending` / `unschedulable` | `PendingUnschedulable` | `Pending` | `../e2e/manifests/l1-taint-node.yaml` | `l1-taint-node` |
| `terminating` | `TerminatingStuck` | `Terminating` | `../e2e/manifests/pod-terminating-stuck.yaml` | `pod-terminating-stuck` |
| `oomkilled` | `OOMKilled` | `CrashLoopBackOff` / `Error` | `../e2e/manifests/l2-oomkilled.yaml` | `l2-oomkilled` |
| `crashloopbackoff` | `CrashLoopBackOffRuntime` | `CrashLoopBackOff` | `../e2e/manifests/pod-crashloop-runtime.yaml` | `pod-crashloop-runtime` |
| `imagepullbackoff` | `ImagePullFailed` | `ImagePullBackOff` / `ErrImagePull` | `../e2e/manifests/l3-imagepull-fail-victim.yaml` | `l3-imagepull-failed` |
| `sandboxcreatefailed` | `SandboxCreateFailed` | `Pending` / `ContainerCreating` | `../e2e/manifests/pod-sandbox-create-failed.yaml` | `pod-sandbox-create-failed` |
| `configerror` | `ConfigError` | `CrashLoopBackOff` / `CreateContainerConfigError` | `../e2e/manifests/l4-config-bootstrap-fail.yaml` | `l4-config-bootstrap-fail` |
| `notready` | `NotReadyProbeFailed` | `Running` 且 `READY=0/1` | `../e2e/manifests/pod-notready-probe-failed.yaml` | `pod-notready-probe-failed` |
| `unknown` | `NodeLostOrUnknown` | `Unknown` | `../e2e/manifests/pod-node-lost-unknown.yaml` | `pod-node-lost-unknown` |

`unknown` 默认不参与 `all`，因为需要手动停止 kubelet 或隔离节点网络。

## 单 Case 手动测试示例

```bash
# OOMKilled
kubectl apply -f ../e2e/manifests/00-namespace.yaml
kubectl apply -f ../e2e/manifests/l2-oomkilled.yaml
kubectl -n aiops-e2e get pod -l app=memhog -w
./run.sh --scenario oomkilled -n 50 -c 5 -q "我的集群有什么问题"

# TerminatingStuck
kubectl apply -f ../e2e/manifests/00-namespace.yaml
kubectl apply -f ../e2e/manifests/pod-terminating-stuck.yaml
kubectl -n aiops-e2e delete pod terminating-stuck --wait=false
kubectl -n aiops-e2e get pod terminating-stuck -w
./run.sh --scenario terminating -n 50 -c 5 -q "我的集群有什么问题"
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
