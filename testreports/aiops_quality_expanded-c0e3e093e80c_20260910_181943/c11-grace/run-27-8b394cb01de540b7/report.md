## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Normal Killing 39s kubelet Stopping container app` (fact-38dd4e9a1ee6) | 确认kubelet已收到删除请求并下发停止指令 |
| 2 | Logging | Elasticsearch | `application started` (fact-e5787f4c38f5, 07:19:37Z) | 确立应用正常运行基线，为后续状态突变提供时间参照 |
| 3 | Logging | Elasticsearch | `SIGTERM received; waiting` (fact-d73fc1302c41, 07:19:39Z) | 证明进程已响应信号并进入阻塞等待逻辑，未直接退出 |
| 4 | K8s Config | Kubernetes | 内存 Request: 8Mi, Limit: 32Mi; CPU Request: 5m, Limit: 50m (fact-0215873318f7, fact-7dc66e5274f5, fact-ff66b02f5354, fact-e317782f64cc) | 排除因资源耗尽（OOM/CPU Throttling）导致容器卡死的可能性 |
| 5 | K8s State | Kubernetes | Pod Phase: `Running`, Status: `Terminating` (fact-ff66b02f5354, fact-5353d1fef004) | 现象层证据，容器进程仍在运行导致Pod无法完成Terminating阶段 |

**证据关联说明**
K8s事件（#1）显示停止动作已发生，但容器状态（#5）与日志（#3）表明进程卡在“收到信号等待”阶段。资源配置（#4）证明环境资源充足，结合应用启动日志（#2）可推断这是应用层逻辑阻塞而非环境异常。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑设计为等待特定文件 `/state/teardown-requested` 出现 → 删除请求触发 SIGTERM，应用收到信号但未检查到文件 → 进程在 while 循环中无限等待，容器状态保持 Running → Pod 因容器未退出而长期停留在 Terminating 状态
```

### 根因结论

**根因确认：** 应用层的优雅终止（Graceful Shutdown）逻辑存在阻塞性缺陷。
**分析依据：**
1.  **现象与证据对应：** 日志记录显示应用在收到 `SIGTERM` 信号后输出 `waiting` (fact-38dd4e9a1ee6, fact-d73fc1302c41)，而非正常的终止退出流程。
2.  **环境排他性：** Kubernetes状态确认Pod已调度且条件正常 (fact-47e8ef7cf6d1 等)，资源限制配置 (fact-7dc66e5274f5) 合理且非瓶颈，排除底层K8s调度或资源故障。
3.  **结论：** 进程因持续等待外部未交付的条件（特定文件存在）而无法响应终止信号，导致Pod卡在 `Terminating` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 11.2s
├─ 并发证据采集: 52.4s
│  └─ g1 aiops-case-v13/workload: 52.4s (Evidence 42.0s, RCA 10.2s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
