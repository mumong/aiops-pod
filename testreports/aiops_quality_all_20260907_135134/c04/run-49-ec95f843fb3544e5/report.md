## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod spec 引用了 Secret 'workload-input' 中的 key 'unavailable-key'，但该 Secret 实际只包含 key 'available-key'，导致 Kubernetes 在容器配置阶段因找不到指定 key 而失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `CreateContainerConfigError` (container: `app`) | 确认容器因配置阶段错误无法启动 |
| 2 | K8s Event | kubernetes | `container.waiting_message`: `"couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` | 直接指明缺失的 Secret Key 名称及所属 Secret |
| 3 | K8s State | kubernetes | `pod.phase`: `Pending`；`container.restart_count`: `0` | 确认 Pod 卡在调度/启动前阶段，未发生重启循环 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}`: `1` | 独立指标印证了 Pod 处于配置错误的等待状态 |
| 5 | K8s State | kubernetes | `pod.condition`: `ContainersReady=False`, `Ready=False` (`reason: ContainersNotReady`) | 证实应用容器持续未就绪，与配置错误原因一致 |

**证据说明**：
Kubernetes 状态与事件事实明确指出了“配置阶段错误”及缺失的 Key (`unavailable-key`)；Metrics 数据独立验证了该特定等待原因的当前存在。重启次数为 0 排除了应用崩溃重启的可能，进一步将根因锁定在启动前的资源配置检查环节。

## 🎯 根因分析 · g1

### 因果链
```text
Pod spec 引用了不存在的 Secret Key ('unavailable-key') → Kubernetes 容器配置阶段校验失败 → 容器无法启动 (Pending/CreateContainerConfigError) → 用户观察到 Pod 状态为 Pending 且持续报错
```

### 根因结论
已确认根因为：Pod 定义中的 Secret 挂载配置引用了密钥 'workload-input' 中的 key 'unavailable-key'，但该 Secret 实际仅包含 key 'available-key'。

这一配置不匹配导致 Kubernetes 在执行容器配置阶段（Container configuration stage）因找不到指定 key 而直接报错，阻止了容器镜像的拉取和启动（证据 #1, #2, #4）。由于错误发生在启动前，因此未产生应用日志或重试重启（证据 #3, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 20.1s
├─ 并发证据采集: 87.9s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 87.9s (Evidence 83.4s, RCA 4.4s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
