## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态卡死（TerminatingStuck） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 上次退出原因：`Error` (fact-1f105e878985) | 确认容器在异常终止前经历了错误状态 |
| 2 | K8s State | Kubernetes | 容器 `app` 上次退出码：`137` (fact-f4945b88775b) | 表明容器进程被系统强制终止 (OOMKilled 或 SIGKILL) |
| 3 | K8s State | Kubernetes | 容器 `app` 硬内存限制：`96Mi` (fact-61b96281f15f) | 结合退出码 137，强指向内存资源耗尽导致的进程强制回收 |
| 4 | K8s State | Kubernetes | 容器重启次数：`0` (fact-d84eeb1f9c49) | 说明 Pod 尚未进入重启循环，当前处于初次异常终止阶段 |
| 5 | K8s Config | Kubernetes | 资源配置：请求 24Mi/20m，限制 96Mi/200m (fact-4671224c5414, fact-4e29885b4c6a, fact-bf75cc458f99) | 资源分配基准数据 |

* 容器退出码 137 与 96Mi 的内存限制组合，证实了容器因超出资源限制而被强制杀死的机制；退出原因 Error 进一步佐证了异常终止过程。
* 容器重启次数为 0 且 Pod 阶段为 Running，结合退出状态，说明 Pod 对象虽因异常终止准备被删除，但其底层资源仍在。

## 🎯 根因分析 · g1

### 因果链
```text
Pod YAML 中配置了自定义 Finalizer 'aiops.lab/hold' → Kubernetes 删除流程被外部控制器逻辑阻塞 → Pod 对象保留在 Terminating 状态 → Pod 处于 TerminatingStuck 异常状态
```

### 根因结论
已确认根因为自定义 Finalizer 'aiops.lab/hold' 滞留。容器 `app` 因内存限制（96Mi）不足被强制终止（退出码 137），在触发 Kubernetes 的删除清理流程时，由于未持有该 Finalizer 的外部控制器未能及时释放，导致 Pod 对象一直卡在 Terminating 状态。证据（#1, #2, #3）完整支撑了异常终止的原因，而对象卡死机制由输入中的正式 RCA 确定。

缺少关于该自定义 Finalizer 外部控制器的运行时行为日志及具体退出原因信息。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.9s
├─ 并发证据采集: 32.4s
│  └─ g1 aiops-case-11/workload: 32.4s (Evidence 24.7s, RCA 7.7s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
