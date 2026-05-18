# Pod RootCause E2E

这个目录用于“精确根因”测试，和 `test/pod_abnormal_e2e` 分开维护。

`pod_abnormal_e2e` 验证系统是否识别异常类型，例如 `VolumeMountFailed / L0`。
`pod_rootcause_e2e` 验证同一异常类型下是否识别具体根因，例如 ConfigMap 不存在、Secret 不存在、PVC 不存在、hostPath 错误。

## 当前自动化覆盖范围

当前自动化测试覆盖 10 个 group，共 26 个 case。suite 会按 case 串行执行：清理环境、apply 一个 manifest、执行 case trigger、等待异常稳定、跑诊断、保存结果、清理后进入下一个 case。

| Group | Case 数 | 自动化 | 默认夜跑 | 目标异常族 | 当前覆盖的具体根因 |
|-------|--------:|:------:|:--------:|------------|--------------------|
| `volumemount` | 5 | ✅ | ✅ | `VolumeMountFailed` | ConfigMap 不存在、Secret 不存在、ConfigMap key 不存在、PVC 不存在、hostPath 路径错误 |
| `pending` | 4 | ✅ | ✅ | `PendingUnschedulable` | nodeSelector 不匹配、CPU 不足、Memory 不足、PVC 不存在 |
| `imagepull` | 3 | ✅ | ✅ | `ImagePullFailed` | 无效 registry/DNS、镜像 tag 不存在、imagePullSecret 不存在 |
| `crashloop` | 3 | ✅ | ✅ | `CrashLoopBackOffRuntime` | 非零退出码、启动命令不存在、应用配置文件缺失 |
| `configerror` | 3 | ✅ | ✅ | `ConfigError` | 必需环境变量缺失、ConfigMap key 缺失、Secret key 缺失 |
| `oomkilled` | 1 | ✅ | ✅ | `OOMKilled` | memory limit 过低 |
| `notready` | 2 | ✅ | ✅ | `NotReadyProbeFailed` | readinessProbe 失败、livenessProbe 失败 |
| `terminating` | 3 | ✅ | ⚠️ | `TerminatingStuck` | finalizer 卡住、preStop 阻塞、terminationGracePeriodSeconds 过长 |
| `sandbox` | 1 | ✅ | ⚠️ | `SandboxCreateFailed` | RuntimeClass 不存在 |
| `evicted` | 1 | ✅ | ⚠️ | `Evicted` | ephemeral-storage/emptyDir 超限驱逐 |

## Group 和 Case 明细

### `volumemount`

用于验证 `MountVolume.SetUp failed`、`FailedMount`、卷引用错误等场景是否能区分具体根因。

| Case ID | Manifest | 精确根因匹配重点 |
|---------|----------|------------------|
| `volume-mount-missing-configmap` | `manifests/volumemount/missing-configmap.yaml` | 缺失 ConfigMap，命中 `configmap` 和 `not found` |
| `volume-mount-missing-secret` | `manifests/volumemount/missing-secret.yaml` | 缺失 Secret，命中 `secret` 和 `not found` |
| `volume-mount-configmap-missing-key` | `manifests/volumemount/configmap-missing-key.yaml` | ConfigMap key 缺失，命中 `configmap`、`missing-key` 或 `couldn't find key` |
| `volume-mount-missing-pvc` | `manifests/volumemount/missing-pvc.yaml` | PVC 不存在，命中 `persistentvolumeclaim`、`pvc` 和 `not found` |
| `volume-mount-hostpath-missing` | `manifests/volumemount/hostpath-missing.yaml` | hostPath 路径或类型错误，命中 `hostPath`、`type check failed` 或 `not a directory` |

### `pending`

用于验证 Pending 下不同调度失败原因是否能分开，而不是只输出“Pod Pending”。

| Case ID | Manifest | 精确根因匹配重点 |
|---------|----------|------------------|
| `pending-nodeselector-mismatch` | `manifests/pending/nodeselector-mismatch.yaml` | nodeSelector/节点标签不匹配 |
| `pending-insufficient-cpu` | `manifests/pending/insufficient-cpu.yaml` | `Insufficient cpu` |
| `pending-insufficient-memory` | `manifests/pending/insufficient-memory.yaml` | `Insufficient memory` |
| `pending-missing-pvc` | `manifests/pending/missing-pvc.yaml` | Pending 由 PVC 不存在触发 |

### `imagepull`

用于验证 `ImagePullBackOff / ErrImagePull` 下不同镜像拉取根因。

| Case ID | Manifest | 精确根因匹配重点 |
|---------|----------|------------------|
| `imagepull-invalid-registry` | `manifests/imagepull/invalid-registry.yaml` | registry 地址无效或 DNS/连接失败 |
| `imagepull-image-not-found` | `manifests/imagepull/image-not-found.yaml` | 镜像 tag 不存在、`manifest unknown` 或 `not found` |
| `imagepull-missing-pull-secret` | `manifests/imagepull/missing-pull-secret.yaml` | `imagePullSecret` 不存在 |

### `crashloop`

用于验证 `CrashLoopBackOff` 下应用进程退出原因。

| Case ID | Manifest | 精确根因匹配重点 |
|---------|----------|------------------|
| `crashloop-exit-code-nonzero` | `manifests/crashloop/exit-code-nonzero.yaml` | 非零退出码，例如 `Exit Code: 2` |
| `crashloop-command-not-found` | `manifests/crashloop/command-not-found.yaml` | 启动命令不存在，`command not found` |
| `crashloop-config-file-missing` | `manifests/crashloop/config-file-missing.yaml` | 应用配置文件缺失，例如 `/etc/rootcause-app/config.yaml` |

### `configerror`

用于验证配置注入错误或启动配置校验失败。

| Case ID | Manifest | 精确根因匹配重点 |
|---------|----------|------------------|
| `configerror-env-missing` | `manifests/configerror/env-missing.yaml` | 应用必需环境变量 `APP_BOOT_MODE` 缺失 |
| `configerror-configmap-key-missing-env` | `manifests/configerror/configmap-key-missing-env.yaml` | env 引用 ConfigMap key 缺失 |
| `configerror-secret-key-missing-env` | `manifests/configerror/secret-key-missing-env.yaml` | env 引用 Secret key 缺失 |

### `oomkilled`

用于验证容器被内存限制杀死。

| Case ID | Manifest | 精确根因匹配重点 |
|---------|----------|------------------|
| `oomkilled-memory-limit-too-low` | `manifests/oomkilled/memory-limit-too-low.yaml` | `OOMKilled`、`Exit Code: 137`、memory limit 过低 |

### `notready`

用于验证 Pod Running 但 Ready 不满足时的探针根因。

| Case ID | Manifest | 精确根因匹配重点 |
|---------|----------|------------------|
| `notready-readiness-probe-failed` | `manifests/notready/readiness-probe-failed.yaml` | readinessProbe 失败 |
| `notready-liveness-probe-failed` | `manifests/notready/liveness-probe-failed.yaml` | livenessProbe 失败 |

### `terminating`

用于验证 Pod 已经进入删除流程但长时间不消失时，是否能区分具体阻塞点。

| Case ID | Manifest | 精确根因匹配重点 |
|---------|----------|------------------|
| `terminating-finalizer-stuck` | `manifests/terminating/finalizer-stuck.yaml` | finalizer 未清理，Pod 有 `deletionTimestamp` |
| `terminating-prestop-stuck` | `manifests/terminating/prestop-stuck.yaml` | `preStop` hook 阻塞终止流程 |
| `terminating-long-grace-period` | `manifests/terminating/long-grace-period.yaml` | `terminationGracePeriodSeconds` 过长导致仍在等待优雅退出 |

### `sandbox`

用于验证 Pod sandbox 创建失败类问题。当前只纳入不破坏节点配置的 RuntimeClass 场景。

| Case ID | Manifest | 精确根因匹配重点 |
|---------|----------|------------------|
| `sandbox-runtimeclass-invalid` | `manifests/sandbox/runtimeclass-invalid.yaml` | `runtimeClassName` 指向不存在的 RuntimeClass |

### `evicted`

用于验证 Pod 被 kubelet 驱逐后的精确根因。当前只纳入相对可控的 Pod 级 ephemeral-storage 超限。

| Case ID | Manifest | 精确根因匹配重点 |
|---------|----------|------------------|
| `evicted-ephemeral-storage` | `manifests/evicted/ephemeral-storage.yaml` | Pod status/reason 为 `Evicted`，Message 含 `ephemeral-storage`、`emptyDir` 或 size limit |

## 根因准确率口径

根因准确率只匹配最终报告中的根因部分：

- 优先提取 `## 🎯 根因分析`
- 其次提取 `### 根因结论`
- 兜底使用整份报告，但会在结果中标记 `root_section_source=full_report_fallback`

每个 case 使用 `root_cause_signature` 判断：

- `include_all`: 必须全部命中
- `include_any`: 至少命中一个
- `exclude_any`: 如果命中任意冲突关键词，则判根因错误

报告中会展示：

- `命中关键词`
- `缺失关键词`
- `冲突关键词`

## 单个 case 测试

手动 apply 单个资源后，直接运行精确 case：

```bash
kubectl apply -f test/pod_rootcause_e2e/manifests/00-namespace.yaml
kubectl apply -f test/pod_rootcause_e2e/manifests/volumemount/missing-configmap.yaml

.venv/bin/python test/pod_rootcause_e2e/run_rootcause_cases.py \
  --case volume-mount-missing-configmap \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800
```

## 按 group 测试

这个命令不会自动 apply 资源。它只对当前集群已有异常发请求并统计，适合你已经手动部署了某个具体 case 时使用。

```bash
.venv/bin/python test/pod_rootcause_e2e/run_rootcause_cases.py \
  --group volumemount \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800
```

不推荐在精确根因测试里一次手动 apply 同组多个 case，因为模型可能诊断到任意一个异常 Pod，导致某个 case 的 root signature 统计不稳定。

如果要自动按 group 一个一个部署、测试、清理，请使用下面的 suite 方式。

## 串行自动 apply + 测试

编辑 `test/pod_rootcause_e2e/test.txt`：

```text
group:volumemount
volume-mount-missing-pvc
group:imagepull
```

执行：

```bash
.venv/bin/python test/pod_rootcause_e2e/run_rootcause_suite.py \
  --scenarios-file test/pod_rootcause_e2e/test.txt \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800
```

suite 会串行执行 case：清理已知资源、apply 对应 manifest、等待异常稳定、调用 `run_rootcause_cases.py`、保存 summary。

如果 `test.txt` 同时写了具体 case 和包含它的 group，脚本会自动去重；执行顺序以首次选中的位置为准。

## test.txt 怎么写

`test.txt` 一行一个 selector，支持两种写法：

```text
# 跑整个组
group:volumemount
group:pending

# 跑单个精确 case
volume-mount-missing-configmap
imagepull-image-not-found
```

当前可用 group：

```text
volumemount
pending
imagepull
crashloop
configerror
oomkilled
notready
terminating
sandbox
evicted
```

当前可用 case 来自 `cases.yaml` 的 `id` 字段。

## 保存目录结构

suite 的结果会按 group 分目录保存，方便第二天按异常族查看：

```text
testreports/pod_rootcause_suite_YYYYMMDD_HHMMSS/
  suite_stats.json
  volumemount/
    01-volume-mount-missing-configmap/
      stats.json
      summary.md
      volume-mount-missing-configmap/
        response_1.md
        response_2.md
  imagepull/
    10-imagepull-invalid-registry/
      stats.json
      summary.md
```

每个 case 目录下：

- `summary.md`: 中文汇总，包含根因准确率、命中关键词、缺失关键词、冲突关键词。
- `stats.json`: 结构化统计。
- `response_N.md`: 每次请求的完整诊断输出。

## 夜间测试推荐方式

1. 编辑 `test/pod_rootcause_e2e/test.txt`，写入你要跑的 group/case。

建议先跑成本较低、最能验证根因区分的组合：

```text
group:volumemount
group:imagepull
group:configerror
```

如果要跑完整 v1-core：

```text
group:volumemount
group:pending
group:imagepull
group:crashloop
group:configerror
group:oomkilled
group:notready
```

2. 下班前执行：

```bash
nohup .venv/bin/python test/pod_rootcause_e2e/run_rootcause_suite.py \
  --scenarios-file test/pod_rootcause_e2e/test.txt \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800 \
  > testreports/pod_rootcause_nightly.log 2>&1 &
```

3. 第二天查看：

```bash
tail -n 100 testreports/pod_rootcause_nightly.log
ls -td testreports/pod_rootcause_suite_* | head -1
```

进入最新目录后，优先看每个 group/case 的 `summary.md`。

## 查看当前进度

查看后台进程：

```bash
ps -ef | grep -E 'run_rootcause_suite|run_rootcause_cases' | grep -v grep
```

查看最新落盘文件：

```bash
find testreports/pod_rootcause_suite_* -maxdepth 4 -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' | sort | tail -20
```

查看当前 case 已生成多少个响应：

```bash
find testreports/pod_rootcause_suite_YYYYMMDD_HHMMSS/<group>/<NN-case>/<case-id> -name 'response_*.md' | wc -l
```

## Backlog 自动化状态

| Group | 具体场景 | 自动化状态 | 默认夜跑 | 说明 |
|-------|----------|:----------:|:--------:|------|
| `terminating` | finalizer 卡住 | ✅ | ⚠️ | 已接入 suite，apply 后自动 delete，清理时会移除 finalizer |
| `terminating` | preStop hook 阻塞 | ✅ | ⚠️ | 已接入 suite，测试耗时受 grace period 影响 |
| `terminating` | terminationGracePeriodSeconds 过长 | ✅ | ⚠️ | 已接入 suite，适合单独 group 测试 |
| `sandbox` | RuntimeClass 不存在 | ✅ | ⚠️ | 已接入 suite；不同集群可能表现为调度/创建阶段错误 |
| `evicted` | ephemeral-storage/emptyDir 超限 | ✅ | ⚠️ | 已接入 suite；建议先单独验证该集群 kubelet 是否稳定触发 Evicted |
| `evicted` | NoExecute taint 驱逐 | ⏳ | ❌ | 可以脚本化，但需要给节点打 taint，可能影响同节点其他 Pod，暂不实现默认 case |
| `unknown` | Node NotReady / Unreachable / ContainerStatusUnknown | ❌ | ❌ | 需要停 kubelet 或隔离节点，属于破坏性测试 |
| `sandbox` | CNI 配置缺失、IPAM 耗尽、runtime 磁盘满 | ❌ | ❌ | 需要修改节点 CNI/runtime 或构造 IPAM 故障，环境差异大 |
| `evicted` | DiskPressure / MemoryPressure / PIDPressure | ❌ | ❌ | 需要制造节点级资源压力，风险高 |
| `terminating` | Node NotReady、volume unmount/detach 卡住 | ❌ | ❌ | 依赖节点失联或真实 CSI/NFS 故障，暂不自动化 |

建议执行方式：新增的 `terminating/sandbox/evicted` 先按 group 单独跑，确认集群表现稳定后再决定是否加入夜间全量。

## 未来全量候选覆盖

下面是更完整的生产候选矩阵。v1-core 只选了其中最主流、最容易稳定复现、最能验证诊断能力的部分；其余场景保留为后续增强方向。

| Group | 已覆盖 v1-core | 未来候选子场景 | 需要补充的测试条件 |
|-------|----------------|----------------|--------------------|
| `volumemount` | ConfigMap 不存在、Secret 不存在、ConfigMap key 不存在、PVC 不存在、hostPath 路径错误 | Secret key 缺失、Projected volume 错误、PVC Pending、PV 绑定错误、StorageClass 不存在、provisioner 失败、CSI driver 异常、NFS 服务器不可达、挂载权限错误、subPath 错误、只读文件系统冲突、volume detach/unmount 卡住 | 需要 CSI/NFS/StorageClass/PV 拓扑环境，部分场景依赖外部存储 |
| `pending` | nodeSelector 不匹配、CPU 不足、Memory 不足、PVC 不存在 | taint/toleration 不匹配、nodeAffinity/anti-affinity 冲突、podAffinity 冲突、hostPort 冲突、namespace ResourceQuota 超限、LimitRange 默认值异常、PV NodeAffinity 冲突、节点 cordon/unschedulable、TopologySpreadConstraints 无法满足、Priority/Preemption 不足 | 需要节点标签/污点/配额/PV 拓扑/多副本约束 |
| `imagepull` | 无效 registry/DNS、镜像 tag 不存在、imagePullSecret 不存在 | 私有仓库鉴权失败、pull secret 内容错误、镜像仓库 TLS/x509 错误、registry 超时、DNS 解析失败、代理配置错误、镜像架构不匹配、镜像被限流、节点 runtime 无法访问 registry | 需要私有 registry、错误证书、网络限流或节点 runtime 配置 |
| `crashloop` | 非零退出码、启动命令不存在、应用配置文件缺失 | 权限不足、入口脚本无执行权限、依赖服务不可达、数据库连接失败、端口占用、应用监听地址错误、运行时库缺失、探针杀死后进入 CrashLoop、应用启动超时、工作目录不存在 | 需要更复杂的应用镜像和依赖服务 |
| `configerror` | 必需环境变量缺失、ConfigMap key 缺失、Secret key 缺失 | ConfigMap 整体不存在、Secret 整体不存在、envFrom 引用错误、变量名拼写错误、配置值格式非法、启动参数非法、镜像 entrypoint 参数错误、ServiceAccount token/权限配置缺失 | 大部分可用 manifest 复现，后续可以优先扩展 |
| `oomkilled` | memory limit 过低 | 应用内存泄漏、瞬时内存峰值、JVM/Go/Python runtime 内存配置不合理、节点级 OOM、QoS 低导致被优先驱逐、VPA/limit 配置错误、sidecar 抢占内存 | 需要稳定压测负载和节点资源观测 |
| `notready` | readinessProbe 失败、livenessProbe 失败 | startupProbe 失败、HTTP 状态码错误、探针路径错误、探针端口错误、探针超时、应用启动慢、依赖下游服务不可用、服务监听 `127.0.0.1`/`0.0.0.0` 错误、TLS 探针失败 | 需要自定义健康检查镜像和下游依赖 |
| `unknown` | 暂未自动化 | Pod Unknown、NodeLost、Node NotReady、kubelet 停止、节点网络隔离、节点重启、容器运行时失联 | 需要破坏节点或隔离网络 |
| `sandbox` | 暂未自动化 | CNI 配置缺失、CNI 二进制缺失、IPAM 耗尽、PodCIDR 冲突、NetworkPolicy/CNI 初始化失败、RuntimeClass 不存在、containerd sandbox 创建失败 | 需要 CNI/runtime 故障注入 |
| `evicted` | 暂未自动化 | ephemeral-storage、DiskPressure、MemoryPressure、PIDPressure、inode 压力、emptyDir/log 占满、节点 eviction threshold 触发 | 需要资源压力构造，可能影响节点稳定性 |
| `terminating` | 暂未纳入 rootcause v1-core | finalizer 卡住、preStop hook 卡住、长 `terminationGracePeriodSeconds`、kubelet/Node 不可达、volume detach/unmount 卡住、Pod deletion blocked by API/finalizer | 可以复用 `pod_abnormal_e2e` 的 terminating 场景，后续迁移到精确根因套件 |

更详细的 backlog 条目见 `backlog.yaml`。
