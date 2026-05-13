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
kubectl apply -f ../e2e/manifests/pod-imagepull-failed.yaml

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

## 串行自动化测试

如果要下班前批量跑多个异常场景，编辑 `test/pod_abnormal_e2e/test.txt`，每行写一个 scenario/alias：

```text
evicted
volumemountfailed
pending
terminating
oomkilled
crashloopbackoff
imagepullbackoff
sandboxcreatefailed
configerror
notready
# unknown
```

然后在仓库根目录执行：

```bash
.venv/bin/python test/pod_abnormal_e2e/run_pod_abnormal_suite.py \
  --scenarios-file test/pod_abnormal_e2e/test.txt \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800
```

脚本行为：

- 每个 scenario 串行执行，前一个场景的 runner 完全结束并写出 `summary.md` 后才进入下一个。
- 每个 scenario 内部仍使用 `run_pod_abnormal_cases.py -c 2` 并发请求。
- 每个 scenario 前会清理已知 E2E 资源，apply `00-namespace.yaml` 和对应 manifest，等待默认 20 秒后开始测试。
- `terminating` 会自动执行 `cases.yaml` 中的 delete trigger，使 Pod 进入 Terminating。
- 每个 scenario 后会清理当前 E2E 资源，避免下一个场景被上一个异常 Pod 干扰。
- 总报告目录默认是 `testreports/pod_abnormal_suite_<timestamp>/`，每个场景一个子目录。

`unknown` 是 manual 场景，默认会跳过。它需要 Pod 调度后手动停止 kubelet 或隔离该节点网络，脚本不会自动执行这类破坏性动作。如需只 apply 资源并把它纳入测试，使用 `--include-manual`，但仍需要你手动制造 NodeLost/Unknown。

## Pod 异常状态 Case 矩阵

| Scenario/Alias | Pod 异常类型 | 典型状态 | Manifest | Runbook |
|---|---|---|---|---|
| `evicted` | `Evicted` | `Evicted` | `../e2e/manifests/pod-evicted.yaml` | `pod-evicted` |
| `volumemountfailed` | `VolumeMountFailed` | `Pending` / `ContainerCreating` | `../e2e/manifests/pod-volume-mount-failed.yaml` | `pod-volume-mount-failed` |
| `pending` / `unschedulable` | `PendingUnschedulable` | `Pending` | `../e2e/manifests/pod-pending-unschedulable.yaml` | `pod-pending-unschedulable` |
| `terminating` | `TerminatingStuck` | `Terminating` | `../e2e/manifests/pod-terminating-stuck.yaml` | `pod-terminating-stuck` |
| `oomkilled` | `OOMKilled` | `CrashLoopBackOff` / `Error` | `../e2e/manifests/pod-oomkilled.yaml` | `pod-oomkilled` |
| `crashloopbackoff` | `CrashLoopBackOffRuntime` | `CrashLoopBackOff` | `../e2e/manifests/pod-crashloop-runtime.yaml` | `pod-crashloop-runtime` |
| `imagepullbackoff` | `ImagePullFailed` | `ImagePullBackOff` / `ErrImagePull` | `../e2e/manifests/pod-imagepull-failed.yaml` | `pod-imagepull-failed` |
| `sandboxcreatefailed` | `SandboxCreateFailed` | `Pending` / `ContainerCreating` | `../e2e/manifests/pod-sandbox-create-failed.yaml` | `pod-sandbox-create-failed` |
| `configerror` | `ConfigError` | `CrashLoopBackOff` / `CreateContainerConfigError` | `../e2e/manifests/pod-config-error.yaml` | `pod-config-error` |
| `notready` | `NotReadyProbeFailed` | `Running` 且 `READY=0/1` | `../e2e/manifests/pod-notready-probe-failed.yaml` | `pod-notready-probe-failed` |
| `unknown` | `NodeLostOrUnknown` | `Unknown` | `../e2e/manifests/pod-node-lost-unknown.yaml` | `pod-node-lost-unknown` |

`unknown` 默认不参与 `all`，因为需要手动停止 kubelet 或隔离节点网络。

## 自动化资源分类

| Scenario/Alias | 自动化方式 | 说明 |
|---|---|---|
| `evicted` | 直接 apply | emptyDir sizeLimit 触发本地临时存储异常，状态可能需要一点时间稳定 |
| `volumemountfailed` | 直接 apply | 缺失 ConfigMap volume 触发 FailedMount |
| `pending` | 直接 apply | 不存在的 nodeSelector 触发 FailedScheduling |
| `terminating` | apply + trigger | apply 后 Running，脚本执行 `kubectl delete pod terminating-stuck --wait=false` 触发 finalizer 卡住 |
| `oomkilled` | 直接 apply | 低 memory limit 触发 OOMKilled/CrashLoopBackOff |
| `crashloopbackoff` | 直接 apply | 容器退出码 2，触发 CrashLoopBackOff |
| `imagepullbackoff` | 直接 apply | 无效 registry 触发 ErrImagePull/ImagePullBackOff |
| `sandboxcreatefailed` | 直接 apply | 不存在 RuntimeClass handler 触发 sandbox 创建失败 |
| `configerror` | 直接 apply | 缺少业务必填环境变量，触发应用启动配置失败 |
| `notready` | 直接 apply | readinessProbe 固定失败，Pod Running 但 READY=0/1 |
| `unknown` | 需要人工动作 | apply 只创建候选 Pod；必须停止 kubelet 或隔离节点网络才会进入 Unknown |

## 单 Case 手动测试示例

```bash
# OOMKilled
kubectl apply -f ../e2e/manifests/00-namespace.yaml
kubectl apply -f ../e2e/manifests/pod-oomkilled.yaml
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
