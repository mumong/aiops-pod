## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod Spec 引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`，导致 Kubelet 无法注入配置，容器进入 `CreateContainerConfigError` 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-1a3b5d8ad4a5, fact-6515a4ae41af) | 直接定位到 Pod 无法启动的具体配置错误。 |
| 2 | K8s State | kubernetes | Pod `workload-6584f97c76-wvcb2` 状态为 `Pending` (fact-26a309f82c99) | 验证异常实体当前处于不可用状态。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason: `CreateContainerConfigError`) = 1 (fact-1f3ec54ab5a4) | 确认容器等待原因确认为配置错误。 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` = 0 (fact-97bda071202f) | 排除因 OOM 或 CrashLoopBackOff 导致重启的可能性。 |
| 5 | Logging | 失败 | `container "app" in pod ... is waiting to start: CreateContainerConfigError` (kubectl 执行失败，因容器未成功拉起无法获取日志) | 佐证容器无法进入运行态，无法采集应用日志。 |

**证据说明：**
1. **Kubernetes 事件与指标交叉印证**：事实 #1（事件报错）明确指出找不到 Secret 中的 `unavailable-key`，与事实 #3（Metric 显示的 `CreateContainerConfigError`）完全一致，共同锁定故障机制为配置注入失败。
2. **状态一致性**：事实 #2 显示的 `Pending` 状态与事实 #4 显示的 `0` 次重启，符合 Kubelet 在配置注入阶段即失败、尚未启动容器的典型特征。
3. **日志缺失原因**：事实 #5 展示了尝试获取日志时的真实报错，由于容器根本未拉起，因此无业务日志可采，日志维度的缺失是由“无法注入配置”这一根因直接导致的，不影响当前诊断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 Secret Key (`unavailable-key`) → Kubelet 获取配置/注入失败 → 容器启动中止 (CreateContainerConfigError) → Pod 持续 Pending，应用不可用
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的 Spec 中硬编码或引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`。Kubelet 在尝试挂载该配置时校验失败，导致容器无法进入 Running 状态（表现为 `CreateContainerConfigError`）。这一结论得到 K8s Event（事实 #1）、Pod 状态（事实 #2）以及等待原因 Metric（事实 #3）的三重印证。

**未解决的疑问：**
为何 `aiops-case-04/workload-input` Secret 中未包含预期的 `unavailable-key`。现有数据仅能证明 Key 不存在这一**现象**，但未能捕获 Secret 被修改、遗漏创建或密钥轮转等管理层面的**原因**（未知项：为何 `workload-input` Secret 中未包含预期的 `unavailable-key`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.4s
├─ 并发证据采集: 51.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 51.8s (Evidence 45.8s, RCA 5.8s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
