# Pod RootCause E2E

这个目录用于“精确根因”测试，和 `test/pod_abnormal_e2e` 分开维护。

`pod_abnormal_e2e` 验证系统是否识别异常类型，例如 `VolumeMountFailed / L0`。
`pod_rootcause_e2e` 验证同一异常类型下是否识别具体根因，例如 ConfigMap 不存在、Secret 不存在、PVC 不存在、hostPath 错误。

## 当前总结果

截至 `2026-05-20`，已汇总两批 rootcause E2E 结果：

- `testreports/pod_rootcause_suite_20260513_184055`: v1-core 稳定夜间检查，7 个 group、21 个 case、1050 次诊断。
- `testreports/pod_rootcause_suite_20260519_162052`: backlog-auto 合并结果，3 个 group、5 个 case、250 次诊断；已合并 `pod_rootcause_suite_20260519_103127` 的 `terminating-finalizer-stuck`。

当前总覆盖为 10 个 group、26 个 case、1300 次诊断。整体根因准确率 `82.2%`，Runbook 覆盖率 `99.6%`，平均证据率 `90.7%`，平均 MTTR `5.4m`。

## Group 总指标

| Group | Case | Run | 默认夜跑 | Pod 异常状态/异常族 | 当前覆盖的具体根因 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|-------|-----:|----:|----------|---------------------|--------------------|------------|----------------|------------|-----------|
| `volumemount` | 5 | 250 | 是 | `ContainerCreating` / `VolumeMountFailed` | ConfigMap 不存在、Secret 不存在、ConfigMap key 不存在、PVC 不存在、hostPath 路径错误 | 98.4% | 100.0% | 91.2% | 4.2m |
| `pending` | 4 | 200 | 是 | `Pending` / `PendingUnschedulable` | nodeSelector 不匹配、CPU 不足、Memory 不足、PVC 不存在 | 79.5% | 100.0% | 94.3% | 5.2m |
| `imagepull` | 3 | 150 | 是 | `ImagePullBackOff` / `ErrImagePull` | 无效 registry/DNS、镜像 tag 不存在、imagePullSecret 不存在 | 78.7% | 100.0% | 82.1% | 5.5m |
| `crashloop` | 3 | 150 | 是 | `CrashLoopBackOff` | 非零退出码、启动命令不存在、应用配置文件缺失 | 95.3% | 100.0% | 90.5% | 6.3m |
| `configerror` | 3 | 150 | 是 | `ConfigError` | 必需环境变量缺失、ConfigMap key 缺失、Secret key 缺失 | 80.7% | 100.0% | 90.6% | 4.3m |
| `oomkilled` | 1 | 50 | 是 | `OOMKilled` | memory limit 过低 | 100.0% | 100.0% | 95.8% | 6.0m |
| `notready` | 2 | 100 | 是 | `Running` 但 `Ready=False` | readinessProbe 失败、livenessProbe 失败 | 60.0% | 95.0% | 90.5% | 7.8m |
| `terminating` | 3 | 150 | 按需 | `Terminating` / `TerminatingStuck` | finalizer 卡住、preStop 阻塞、terminationGracePeriodSeconds 过长 | 56.7% | 100.0% | 95.9% | 5.5m |
| `sandbox` | 1 | 50 | 按需 | `ContainerCreating` / `SandboxCreateFailed` | RuntimeClass handler 无效 | 96.0% | 100.0% | 93.3% | 6.6m |
| `evicted` | 1 | 50 | 按需 | `Failed` / `Evicted` | ephemeral-storage/emptyDir 超限驱逐 | 78.0% | 100.0% | 76.9% | 6.0m |

说明：默认夜跑建议只跑前 7 个稳定 group。`terminating/sandbox/evicted` 已经能自动化，但更容易受节点、runtime、存储和模型归因稳定性影响，建议按需单独跑。

## Group 和 Case 明细

### `volumemount`

| Case ID | Manifest | 精确根因匹配重点 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|---------|----------|------------------|------------|----------------|------------|-----------|
| `volume-mount-missing-configmap` | `manifests/volumemount/missing-configmap.yaml` | ConfigMap 不存在，命中 `configmap` 和 `not found` | 100.0% | 100.0% | 100.0% | 4.0m |
| `volume-mount-missing-secret` | `manifests/volumemount/missing-secret.yaml` | Secret 不存在，命中 `secret` 和 `not found` | 98.0% | 100.0% | 97.5% | 4.0m |
| `volume-mount-configmap-missing-key` | `manifests/volumemount/configmap-missing-key.yaml` | ConfigMap key 缺失，命中 `configmap`、`missing-key` 或 `couldn't find key` | 94.0% | 100.0% | 92.2% | 3.6m |
| `volume-mount-missing-pvc` | `manifests/volumemount/missing-pvc.yaml` | PVC 不存在，命中 `persistentvolumeclaim`、`pvc` 和 `not found` | 100.0% | 100.0% | 92.7% | 4.8m |
| `volume-mount-hostpath-missing` | `manifests/volumemount/hostpath-missing.yaml` | hostPath 路径或类型错误，命中 `hostPath`、`type check failed` 或 `not a directory` | 100.0% | 100.0% | 73.8% | 4.7m |
| **Group total** | - | - | **98.4%** | **100.0%** | **91.2%** | **4.2m** |

### `pending`

| Case ID | Manifest | 精确根因匹配重点 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|---------|----------|------------------|------------|----------------|------------|-----------|
| `pending-nodeselector-mismatch` | `manifests/pending/nodeselector-mismatch.yaml` | nodeSelector/节点标签不匹配 | 88.0% | 100.0% | 93.8% | 7.9m |
| `pending-insufficient-cpu` | `manifests/pending/insufficient-cpu.yaml` | `Insufficient cpu` | 70.0% | 100.0% | 93.2% | 4.3m |
| `pending-insufficient-memory` | `manifests/pending/insufficient-memory.yaml` | `Insufficient memory` | 60.0% | 100.0% | 95.9% | 4.3m |
| `pending-missing-pvc` | `manifests/pending/missing-pvc.yaml` | Pending 由 PVC 不存在触发 | 100.0% | 100.0% | 94.3% | 4.3m |
| **Group total** | - | - | **79.5%** | **100.0%** | **94.3%** | **5.2m** |

### `imagepull`

| Case ID | Manifest | 精确根因匹配重点 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|---------|----------|------------------|------------|----------------|------------|-----------|
| `imagepull-invalid-registry` | `manifests/imagepull/invalid-registry.yaml` | registry 地址无效或 DNS/连接失败 | 98.0% | 100.0% | 81.4% | 5.5m |
| `imagepull-image-not-found` | `manifests/imagepull/image-not-found.yaml` | 镜像 tag 不存在、`manifest unknown` 或 `not found` | 70.0% | 100.0% | 80.7% | 5.6m |
| `imagepull-missing-pull-secret` | `manifests/imagepull/missing-pull-secret.yaml` | `imagePullSecret` 不存在 | 68.0% | 100.0% | 84.3% | 5.4m |
| **Group total** | - | - | **78.7%** | **100.0%** | **82.1%** | **5.5m** |

### `crashloop`

| Case ID | Manifest | 精确根因匹配重点 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|---------|----------|------------------|------------|----------------|------------|-----------|
| `crashloop-exit-code-nonzero` | `manifests/crashloop/exit-code-nonzero.yaml` | 非零退出码，例如 `Exit Code: 2` | 100.0% | 100.0% | 97.0% | 6.5m |
| `crashloop-command-not-found` | `manifests/crashloop/command-not-found.yaml` | 启动命令不存在，`command not found` | 100.0% | 100.0% | 81.8% | 6.7m |
| `crashloop-config-file-missing` | `manifests/crashloop/config-file-missing.yaml` | 应用配置文件缺失，例如 `/etc/rootcause-app/config.yaml` | 86.0% | 100.0% | 92.7% | 5.6m |
| **Group total** | - | - | **95.3%** | **100.0%** | **90.5%** | **6.3m** |

### `configerror`

| Case ID | Manifest | 精确根因匹配重点 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|---------|----------|------------------|------------|----------------|------------|-----------|
| `configerror-env-missing` | `manifests/configerror/env-missing.yaml` | 应用必需环境变量 `APP_BOOT_MODE` 缺失 | 98.0% | 100.0% | 89.8% | 5.2m |
| `configerror-configmap-key-missing-env` | `manifests/configerror/configmap-key-missing-env.yaml` | env 引用 ConfigMap key 缺失 | 70.0% | 100.0% | 92.2% | 3.8m |
| `configerror-secret-key-missing-env` | `manifests/configerror/secret-key-missing-env.yaml` | env 引用 Secret key 缺失 | 74.0% | 100.0% | 89.7% | 4.0m |
| **Group total** | - | - | **80.7%** | **100.0%** | **90.6%** | **4.3m** |

### `oomkilled`

| Case ID | Manifest | 精确根因匹配重点 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|---------|----------|------------------|------------|----------------|------------|-----------|
| `oomkilled-memory-limit-too-low` | `manifests/oomkilled/memory-limit-too-low.yaml` | `OOMKilled`、`Exit Code: 137`、memory limit 过低 | 100.0% | 100.0% | 95.8% | 6.0m |
| **Group total** | - | - | **100.0%** | **100.0%** | **95.8%** | **6.0m** |

### `notready`

| Case ID | Manifest | 精确根因匹配重点 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|---------|----------|------------------|------------|----------------|------------|-----------|
| `notready-readiness-probe-failed` | `manifests/notready/readiness-probe-failed.yaml` | readinessProbe 失败 | 94.0% | 96.0% | 87.0% | 10.3m |
| `notready-liveness-probe-failed` | `manifests/notready/liveness-probe-failed.yaml` | livenessProbe 失败 | 26.0% | 94.0% | 93.9% | 5.3m |
| **Group total** | - | - | **60.0%** | **95.0%** | **90.5%** | **7.8m** |

### `terminating`

| Case ID | Manifest | 精确根因匹配重点 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|---------|----------|------------------|------------|----------------|------------|-----------|
| `terminating-finalizer-stuck` | `manifests/terminating/finalizer-stuck.yaml` | finalizer 未清理，Pod 有 `deletionTimestamp` | 74.0% | 100.0% | 97.3% | 5.1m |
| `terminating-prestop-stuck` | `manifests/terminating/prestop-stuck.yaml` | `preStop` hook 阻塞终止流程 | 66.0% | 100.0% | 95.0% | 5.7m |
| `terminating-long-grace-period` | `manifests/terminating/long-grace-period.yaml` | `terminationGracePeriodSeconds` 过长导致仍在等待优雅退出 | 30.0% | 100.0% | 95.5% | 5.7m |
| **Group total** | - | - | **56.7%** | **100.0%** | **95.9%** | **5.5m** |

`preStop` 和 `long-grace` 相关 case 为了支持 `-n 50 -c 2` 的长时间压测，异常窗口设置为 21600 秒（6 小时）。suite 清理阶段会使用 force delete，不需要手动等待 6 小时。

### `sandbox`

| Case ID | Manifest | 精确根因匹配重点 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|---------|----------|------------------|------------|----------------|------------|-----------|
| `sandbox-runtimeclass-invalid` | `manifests/sandbox/runtimeclass-invalid.yaml` | RuntimeClass 对象存在，但 handler 指向不存在的 runtime handler，Pod 会在 kubelet sandbox 阶段失败 | 96.0% | 100.0% | 93.3% | 6.6m |
| **Group total** | - | - | **96.0%** | **100.0%** | **93.3%** | **6.6m** |

### `evicted`

| Case ID | Manifest | 精确根因匹配重点 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|---------|----------|------------------|------------|----------------|------------|-----------|
| `evicted-ephemeral-storage` | `manifests/evicted/ephemeral-storage.yaml` | Pod status/reason 为 `Evicted`，Message 含 `ephemeral-storage`、`emptyDir` 或 size limit | 78.0% | 100.0% | 76.9% | 6.0m |
| **Group total** | - | - | **78.0%** | **100.0%** | **76.9%** | **6.0m** |

## 未覆盖和不建议默认夜跑的场景

| Group | 后续场景 | 不默认夜跑原因 |
|-------|----------|----------------|
| `unknown` | Pod Unknown、NodeLost、Node NotReady、kubelet 停止、节点网络隔离、节点重启、容器运行时失联 | 需要破坏节点或隔离网络 |
| `sandbox` | CNI 配置缺失、CNI 二进制缺失、IPAM 耗尽、PodCIDR 冲突、containerd sandbox 创建失败 | 需要修改 CNI/runtime 或做故障注入 |
| `evicted` | DiskPressure、MemoryPressure、PIDPressure、inode 压力、日志占满、NoExecute taint 驱逐 | 会制造节点级资源压力或影响同节点其他 Pod |
| `terminating` | Node 不可达、kubelet 无响应、volume detach/unmount 卡住、CSI/NFS 卸载异常 | 依赖节点失联或真实存储故障 |

## 测试方式和命令

### 夜间全量 v1-core

编辑 `test/pod_rootcause_e2e/test.txt`：

```text
group:volumemount
group:pending
group:imagepull
group:crashloop
group:configerror
group:oomkilled
group:notready
```

执行：

```bash
nohup .venv/bin/python test/pod_rootcause_e2e/run_rootcause_suite.py \
  --scenarios-file test/pod_rootcause_e2e/test.txt \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800 \
  > testreports/pod_rootcause_nightly.log 2>&1 &
```

### 按 group 单独跑

```bash
printf "group:terminating\ngroup:sandbox\ngroup:evicted\n" > /tmp/rootcause_backlog_auto.txt

.venv/bin/python test/pod_rootcause_e2e/run_rootcause_suite.py \
  --scenarios-file /tmp/rootcause_backlog_auto.txt \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800
```

### 单个 case 跑

```bash
printf "volume-mount-missing-configmap\n" > /tmp/rootcause_one_case.txt

.venv/bin/python test/pod_rootcause_e2e/run_rootcause_suite.py \
  --scenarios-file /tmp/rootcause_one_case.txt \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800
```

### 查看进度和报告

```bash
tail -f testreports/pod_rootcause_nightly.log
ps -ef | grep -E 'run_rootcause_suite|run_rootcause_cases' | grep -v grep
ls -td testreports/pod_rootcause_suite_* | head -1
```

suite 会按 case 串行执行：清理环境、apply manifest、执行 trigger、等待异常稳定、跑诊断、保存 `summary.md/stats.json/response_N.md`、清理后进入下一个 case。
