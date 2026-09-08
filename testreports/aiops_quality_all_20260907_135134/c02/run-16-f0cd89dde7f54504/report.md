## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | 1 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` (fact-1bd1c8f3af04) | 确认 `app` 容器处于镜像拉取退避状态 |
| 2 | Metric | prometheus | `kube_pod_status_phase{container="app", phase="Pending"} = 1` (fact-c3bae095eb4c) | 确认 Pod 卡在 Pending 阶段，未进入 Running 或 Failed |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total{container="app"} = 0` (fact-366c1aea6bde) | 确认容器从未启动过，排除了运行时崩溃重启的可能 |

现有证据仅能确认容器因镜像拉取失败被 Kubernetes 挂起，但缺乏关键维度支撑以锁定具体根因：
- **Kubernetes 状态缺失**：未采集到 `Events` 中的具体错误码（如 401/404/DNS 错误）或 YAML 中的 `imagePullSecrets` 配置，无法区分是鉴权、地址还是网络问题。
- **日志/追踪无数据**：因容器未启动，物理上不存在应用日志或 Trace 记录。

## 🎯 根因分析 · g1

### 因果链

```text
镜像拉取机制失败（具体原因未确认） → kubelet 重试后进入 BackOff 退避状态 → Pod 状态变更为 ImagePullBackOff → 应用不可用
```

### 根因结论

**证据不足。**

目前仅有指标证实容器因 `ImagePullBackOff` 处于等待状态。由于缺乏决定性事实，无法区分以下具体故障原因：
1. 镜像名错误或不存（404）；
2. 镜像仓库鉴权失败（401）；
3. 节点网络/DNS 无法解析或连接镜像仓库。

要确诊根因，必须获取 `Kubernetes Events` 中的 `ImagePullError` 详细报错原文或校验 `Pod YAML` 中的镜像名与 `imagePullSecrets` 配置。

---

## 📊 性能统计

```text
├─ 总耗时: 56.6s
├─ 问题定位: 17.4s
├─ 并发证据采集: 31.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 31.7s (Evidence 23.4s, RCA 8.2s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
