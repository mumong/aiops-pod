## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod spec 引用了不存在的 ConfigMap 'unavailable-config' (Optional: false) 导致 Volume 'input' 挂载永久失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-00115bdd72de) | `Warning FailedMount 102s (x11 over 7m54s) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接指出 Pod 因找不到指定 ConfigMap 导致 Volume 'input' 挂载永久失败 |
| 2 | K8s State | kubernetes (fact-17873089ef55) | `Pending` | 确认 Pod 因挂载失败而处于 Pending 状态 |
| 3 | Metric | prometheus (fact-e8c980478580) | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 确认 Pod 正等待挂载，且未发生重启 (fact-73c75cd31a77: restart_count=0) |
| 4 | K8s Config | kubernetes (fact-38b9cb181029) | `resource_request.cpu = 5m` | 排除因资源请求过高导致节点无法满足而 Pending 的可能性 |

Kubernetes 事件 (fact-00115bdd72de) 直接锁定了挂载失败的根本原因是 ConfigMap 'unavailable-config' 缺失，且由于挂载是启动的前提，该事件解释了 Metric 中观察到的 `ContainerCreating` 挂起状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用不存在的 ConfigMap 'unavailable-config' (Optional: false) → Volume 'input' 挂载永久失败 → kubelet 阻止容器启动 (WaitReason: ContainerCreating) → Pod 处于 Pending 状态，无法提供服务
```

### 根因结论

已确认根因：**Pod 配置引用了不存在的 ConfigMap 'unavailable-config'。**

该 ConfigMap 被声明为 `Optional: false`，导致 Kubernetes 在 Pod 启动时无法完成 Volume 'input' 的挂载。这一失败被 kubelet 记录在 Warning 事件 (fact-00115bdd72de) 中，并直接导致 Pod 停留在 `ContainerCreating` 状态，无法进入运行状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.1s
├─ 并发证据采集: 47.3s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 47.3s (Evidence 42.5s, RCA 4.6s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
