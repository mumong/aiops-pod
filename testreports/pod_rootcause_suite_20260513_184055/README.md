# Pod RootCause E2E 全量结果归档

- 报告目录: `testreports/pod_rootcause_suite_20260513_184055`
- 生成时间: 2026-05-18 09:47:33
- 模型: `openai/Qwen3-32B-AWQ`
- 测试规模: 7 个 group，21 个 case，1050 次成功诊断请求
- Suite 总耗时: 51.4h
- 判定阈值: 根因准确率 / Runbook 覆盖率 / 证据采集率均为 `>= 60%`，MTTR 为 `< 15m`

## 总体结论

| 指标 | 结果 | 状态 |
|------|------|------|
| 根因准确率 | 85.4% | ✅ |
| Runbook 覆盖率 | 99.5% | ✅ |
| 证据采集率 | 90.4% | ✅ |
| 平均 MTTR | 5.3m | ✅ |


关键判断：Runbook 和证据链整体稳定，精确根因总体通过；主要短板集中在 `notready-liveness-probe-failed`，模型经常把 livenessProbe 导致的重启误判成 OOMKilled 或 readiness 问题。`volumemount` 的根因准确率很高

## Case 明细

| # | Group | Case | 根因准确率 | Layer | Runbook | 证据 | MTTR | 语义修正 | 状态 |
|---:|-------|------|------------|-------|---------|------|------|----------|------|
| 1 | `volumemount` | `volume-mount-missing-configmap` | 100.0% | 8.0% | 100.0% | 100.0% | 4.0m | 11 | ✅ |
| 2 | `volumemount` | `volume-mount-missing-secret` | 98.0% | 6.0% | 100.0% | 97.5% | 4.0m | 11 | ✅ |
| 3 | `volumemount` | `volume-mount-configmap-missing-key` | 94.0% | 6.0% | 100.0% | 92.2% | 3.6m | 12 | ✅ |
| 4 | `volumemount` | `volume-mount-missing-pvc` | 100.0% | 72.0% | 100.0% | 92.7% | 4.8m | 19 | ✅ |
| 5 | `volumemount` | `volume-mount-hostpath-missing` | 100.0% | 94.0% | 100.0% | 73.8% | 4.7m | 0 | ✅ |
| 6 | `pending` | `pending-nodeselector-mismatch` | 88.0% | 100.0% | 100.0% | 93.8% | 7.9m | 0 | ✅ |
| 7 | `pending` | `pending-insufficient-cpu` | 70.0% | 100.0% | 100.0% | 93.2% | 4.3m | 0 | ✅ |
| 8 | `pending` | `pending-insufficient-memory` | 60.0% | 100.0% | 100.0% | 95.9% | 4.3m | 0 | ✅ |
| 9 | `pending` | `pending-missing-pvc` | 100.0% | 100.0% | 100.0% | 94.3% | 4.3m | 22 | ✅ |
| 10 | `imagepull` | `imagepull-invalid-registry` | 98.0% | 100.0% | 100.0% | 81.4% | 5.5m | 1 | ✅ |
| 11 | `imagepull` | `imagepull-image-not-found` | 70.0% | 100.0% | 100.0% | 80.7% | 5.6m | 31 | ✅ |
| 12 | `imagepull` | `imagepull-missing-pull-secret` | 68.0% | 100.0% | 100.0% | 84.3% | 5.4m | 16 | ✅ |
| 13 | `crashloop` | `crashloop-exit-code-nonzero` | 100.0% | 100.0% | 100.0% | 97.0% | 6.5m | 9 | ✅ |
| 14 | `crashloop` | `crashloop-command-not-found` | 100.0% | 100.0% | 100.0% | 81.8% | 6.7m | 7 | ✅ |
| 15 | `crashloop` | `crashloop-config-file-missing` | 86.0% | 30.0% | 100.0% | 92.7% | 5.6m | 43 | ✅ |
| 16 | `configerror` | `configerror-env-missing` | 98.0% | 100.0% | 100.0% | 89.8% | 5.2m | 29 | ✅ |
| 17 | `configerror` | `configerror-configmap-key-missing-env` | 70.0% | 100.0% | 100.0% | 92.2% | 3.8m | 1 | ✅ |
| 18 | `configerror` | `configerror-secret-key-missing-env` | 74.0% | 100.0% | 100.0% | 89.7% | 4.0m | 0 | ✅ |
| 19 | `oomkilled` | `oomkilled-memory-limit-too-low` | 100.0% | 100.0% | 100.0% | 95.8% | 6.0m | 9 | ✅ |
| 20 | `notready` | `notready-readiness-probe-failed` | 94.0% | 96.0% | 96.0% | 87.0% | 10.3m | 3 | ✅ |
| 21 | `notready` | `notready-liveness-probe-failed` | 26.0% | 56.0% | 94.0% | 93.9% | 5.3m | 1 | ❌ |

## Group 平均

| Group | Case 数 | Runs | 根因准确率 | Layer | Runbook | 证据 | MTTR | 语义修正 | 状态 |
|-------|--------:|-----:|------------|-------|---------|------|------|----------|------|
| `volumemount` | 5 | 250 | 98.4% | 37.2% | 100.0% | 91.2% | 4.2m | 53 | ✅ |
| `pending` | 4 | 200 | 79.5% | 100.0% | 100.0% | 94.3% | 5.2m | 22 | ✅ |
| `imagepull` | 3 | 150 | 78.7% | 100.0% | 100.0% | 82.1% | 5.5m | 48 | ✅ |
| `crashloop` | 3 | 150 | 95.3% | 76.7% | 100.0% | 90.5% | 6.3m | 59 | ✅ |
| `configerror` | 3 | 150 | 80.7% | 100.0% | 100.0% | 90.6% | 4.3m | 30 | ✅ |
| `oomkilled` | 1 | 50 | 100.0% | 100.0% | 100.0% | 95.8% | 6.0m | 9 | ✅ |
| `notready` | 2 | 100 | 60.0% | 76.0% | 95.0% | 90.5% | 7.8m | 4 | ✅ |

## 后 5 个 Case 的语义修正结论

| Case | 修正次数 | 结论 |
|------|---------:|------|
| `configerror-configmap-key-missing-env` | 1 | 1 次最终根因段已经明确 `APP_BOOT_MODE + rc-app-config`，原先因冲突词漏判；其余失败多为把 key 缺失说成 ConfigMap 不存在，保留失败。 |
| `configerror-secret-key-missing-env` | 0 | 没有可确认的 matcher 漏判；失败样本多为泛化成 ConfigMap/Secret 或直接说 ConfigMap 缺失，保留失败。 |
| `oomkilled-memory-limit-too-low` | 9 | 9 次报告明确 OOMKilled 和内存限制，只是没有命中英文 `memory limit` 或 `Exit Code: 137`，已按中文语义修正。 |
| `notready-readiness-probe-failed` | 3 | 3 次最终根因段明确 readiness 探针失败/健康接口不匹配，已修正；fallback-only 输出不修正。 |
| `notready-liveness-probe-failed` | 1 | 只有 1 次是 matcher 漏判；大部分失败是真实误判为 OOMKilled/readiness 或输出 healthy/unknown，保留失败。 |

修正审计文件：`manual_rootcause_corrections.json` 记录前 16 个 case 的历史修正，`semantic_rootcause_corrections_after16.json` 记录本次后 5 个 case 的新增修正。

## 已覆盖自动化范围

| Group | 当前自动化子场景 |
|-------|------------------|
| `volumemount` | ConfigMap 不存在、Secret 不存在、ConfigMap key 不存在、PVC 不存在、hostPath 路径错误 |
| `pending` | nodeSelector 不匹配、CPU 不足、Memory 不足、PVC 不存在 |
| `imagepull` | 无效 registry/DNS、镜像 tag 不存在、imagePullSecret 不存在 |
| `crashloop` | 非零退出码、启动命令不存在、应用配置文件缺失 |
| `configerror` | 必需环境变量缺失、ConfigMap key 缺失、Secret key 缺失 |
| `oomkilled` | memory limit 过低 |
| `notready` | readinessProbe 失败、livenessProbe 失败 |

## 未测试 Group 和后续扩展

本次归档结果覆盖的是旧的 v1-core：`volumemount / pending / imagepull / crashloop / configerror / oomkilled / notready` 七个 group。当前代码已经继续新增了可自动化 backlog case，后续应按 `terminating / sandbox / evicted` 单独补跑新报告。还不能低风险自动化的 group 主要剩 `unknown`，以及 sandbox/evicted/terminating 中依赖节点或 CNI/CSI 故障注入的子场景。

参考口径：

- Kubernetes 官方 Pod lifecycle：`Unknown` 通常表示无法获取 Pod 状态，典型原因是无法和 Pod 所在节点通信；`Terminating` 是 kubectl 展示状态，不是 Pod phase。
- ACK Pod 异常排查：`Terminating` 常见原因包括 Node NotReady、Finalizers、preStop、terminationGracePeriodSeconds、容器不响应 SIGTERM；`Evicted` 常见原因包括 memory/disk/PID 压力、NoExecute 污点和节点驱逐速率配置。

| Group | 具体场景 | 自动化状态 | 默认夜跑 | 关键证据 / 说明 |
|-------|----------|:----------:|:--------:|----------------|
| `terminating` | `terminating-finalizer-stuck` | ✅ | ⚠️ | Pod YAML 有 `deletionTimestamp` 和 `metadata.finalizers`，对象长时间存在 |
| `terminating` | `terminating-prestop-stuck` | ✅ | ⚠️ | Pod spec 有 `preStop`，删除后停留在终止流程 |
| `terminating` | `terminating-long-grace-period` | ✅ | ⚠️ | `terminationGracePeriodSeconds` 很长，删除后仍在等待优雅退出 |
| `sandbox` | `sandbox-runtimeclass-invalid` | ✅ | ⚠️ | `runtimeClassName` 指向不存在的 RuntimeClass；不同集群事件文本可能不同 |
| `evicted` | `evicted-ephemeral-storage` | ✅ | ⚠️ | Pod status/reason=`Evicted`，Message 含 `ephemeral-storage` / `emptyDir` / size limit |
| `evicted` | `evicted-noexecute-taint` | ⏳ | ❌ | 可脚本化，但需要给节点打 NoExecute taint，可能影响同节点其他 Pod |
| `unknown` | `unknown-node-notready` | ❌ | ❌ | 需要停止 kubelet 或让节点失联；Node `Ready=False/Unknown` |
| `unknown` | `unknown-node-unreachable` | ❌ | ❌ | 需要隔离节点网络；Node taint 含 `node.kubernetes.io/unreachable` |
| `unknown` | `unknown-container-status-unknown` | ❌ | ❌ | 依赖节点短暂失联和恢复时机，稳定性较差 |
| `sandbox` | `sandbox-runtime-disk-full` | ❌ | ❌ | 需要填满节点 runtime 目录，风险高 |
| `sandbox` | `sandbox-cni-config-missing` | ❌ | ❌ | 需要改节点 CNI 配置或插件文件 |
| `sandbox` | `sandbox-ipam-exhausted` | ❌ | ❌ | 需要可控 CNI/IP 池 |
| `evicted` | `evicted-disk-pressure` / `evicted-memory-pressure` | ❌ | ❌ | 需要制造节点级资源压力 |
| `terminating` | `terminating-node-notready` / `terminating-volume-unmount-stuck` | ❌ | ❌ | 需要节点失联或真实 CSI/NFS 故障 |

## 怎么继续测试

全量夜间自动化：

```bash
nohup .venv/bin/python test/pod_rootcause_e2e/run_rootcause_suite.py --scenarios-file test/pod_rootcause_e2e/test.txt -n 50 -c 2 --question "我的集群有什么问题" --url http://10.2.0.48:30800 > testreports/pod_rootcause_nightly.log 2>&1 &
```

单 group 自动化：

```bash
printf "group:volumemount\n" > /tmp/rootcause_group.txt && .venv/bin/python test/pod_rootcause_e2e/run_rootcause_suite.py --scenarios-file /tmp/rootcause_group.txt -n 50 -c 2 --question "我的集群有什么问题" --url http://10.2.0.48:30800
```

查看进度：

```bash
tail -f testreports/pod_rootcause_nightly.log
find testreports/pod_rootcause_suite_* -maxdepth 4 -name stats.json | wc -l
```
