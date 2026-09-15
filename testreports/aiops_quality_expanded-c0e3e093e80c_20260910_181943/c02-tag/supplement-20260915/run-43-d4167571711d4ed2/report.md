## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 处于 ImagePullBackOff 状态，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Error: ImagePullBackOff` (over 51m) | 确认 Pod 当前处于持续拉取镜像失败的异常状态 |
| 2 | K8s Event | kubernetes | `rpc error: code = NotFound desc = ... failed to resolve reference ... registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908: not found` | 直接指出镜像 tag 不存在是导致拉取失败的具体技术原因 |
| 3 | K8s State | kubernetes | Pod `Pending`；容器重启数 `0`；镜像名 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` | 证实容器从未成功启动（无重启），故障根源在于镜像引用配置 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 独立指标验证 Pod 等待原因确认为拉取镜像失败 |

**证据说明：**
K8s Event 明确报出 `NotFound` 错误，直接锁定了根因；Metric 数据与 Pod 事件状态（`ImagePullBackOff`）完全一致，排除了其他网络或权限故障的可能；由于容器未启动，Logging 和 Tracing 维度无适用数据，当前 K8s 状态与指标已构成完整的证据闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 镜像 tag 'aiops-fixture-unavailable-20260908' 在仓库中不存在 → kubelet 拉取触发 NotFound 错误 → Pod 状态转为 ImagePullBackOff → 容器无法启动
```

### 根因结论

已确认根因：**Pod 指定的镜像 tag 不存在于远程仓库（Registry Not Found）。**

具体表现为：
1.  Pod 配置的镜像引用 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在仓库中无法解析（证据 #2、#3）；
2.  Kubelet 拉取失败后，Pod 状态持续处于 `Pending` 并进入 `ImagePullBackOff` 等待重试阶段，未产生任何容器启动日志（证据 #1、#3、#4）。

---

## 📊 性能统计

```text
├─ 总耗时: 53.8s
├─ 问题定位: 19.8s
├─ 并发证据采集: 25.6s
│  └─ g1 aiops-case-v07/workload: 25.6s (Evidence 16.0s, RCA 9.4s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
