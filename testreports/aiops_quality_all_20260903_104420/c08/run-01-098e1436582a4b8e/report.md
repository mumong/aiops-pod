## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | Running | Pod workload-5c9c7b6489-fl85h 出现容器崩溃重启 (OOMKilled) 事件，目前实例已恢复 Running 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_terminated_reason` | reason=OOMKilled (fact-f07ab9c125ac) | 直接证据：容器最后一次终止原因是内存超限被系统杀死 |
| 2 | K8s State | `container.last_exit_code` | exit_code=137 (fact-fd6e7b48300d) | 佐证证据：Exit 137 为容器被 SIGKILL 的标准退出码，与 OOMKilled 对应 |
| 3 | K8s Config | `container.resource_limit.memory` | value=64Mi (fact-81567a4120ff) | 触发条件：容器内存限制仅为 64Mi，触发 OOMKilled 的阈值 |
| 4 | K8s State | `container.restart_count` | restart_count=2 (fact-dc71700629b5) | 现象确认：容器已因该异常重启 2 次，目前处于 Running 状态 |
| 5 | K8s Event | `kube_pod_container_status_last_terminated_reason` | reason=OOMKilled (fact-0509b8d9de9a) | 交叉印证：Metrics 中 Prometheus 捕获到的最终终止原因同样指向 OOMKilled |
| 6 | Logging | `numeric_fields.allocated_mib` | first=10 MiB, last=48 MiB (fact-11f7b78c4b58 等) | 趋势限定：在观测窗口 (15:30:29-15:31:07) 内，内存分配从 10 MiB 持续增长至 48 MiB，逼近 64Mi 限制 |

**证据间关系说明：**
- 编号 1、2、5 共同确认了导致 Pod 重启的**根本机制**为 `OOMKilled`。
- 编号 3 明确了触发该机制的**硬性约束**（64Mi 限制），与编号 6 的日志增长趋势（增至 48 MiB）形成了**因果闭环**，表明应用内存需求快速膨胀并触达阈值。
- 编号 4 反映了该机制的**直接后果**，即 Pod 进入崩溃重启循环后，当前时刻已恢复至 `Running` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
容器 app 内存限制过小 (64Mi) → 应用运行中内存快速分配增长 (10 MiB 增至 48 MiB) → 触发 OOMKilled 机制 (exitCode 137) → Pod 容器崩溃重启 2 次 (当前 Running)
```

### 根因结论

**已确认的根因：容器应用内存分配超出硬限制 (64Mi)，触发 OOMKilled 导致崩溃。**

证据分析：
1. **致命机制确认**：K8s 状态显示容器以 `OOMKilled` (fact-f07ab9c125ac) 终止且退出码为 `137` (fact-fd6e7b48300d)，Prometheus 指标也独立记录了相同的终止原因 (fact-0509b8d9de9a)。
2. **内存耗尽证据**：容器配置中内存上限仅为 `64Mi` (fact-81567a4120ff)。日志证据 (fact-11f7b78c4b58) 明确记录在观测窗口内内存分配从 `10 MiB` 持续快速攀升至 `48 MiB`。结合 64Mi 的硬限制，内存资源耗尽是直接导致 OOMKilled 的物理事实。
3. **现象还原**：Pod 经历了因内存耗尽引发的两次崩溃重启 (fact-dc71700629b5)，目前状态为 `Running`。

**未确认信息（证据不足部分）：**
根据输入事实，无法获取 OOMKilled 发生瞬间的**精确内存峰值数据**以及**应用内部堆栈日志**（unknowns），因此无法断定 48 MiB 是否为最终崩溃点之前的精确峰值，也无法定位具体触发内存分配激增的代码逻辑行。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 20.6s
├─ 并发证据采集: 88.4s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 88.4s (Evidence 78.2s, RCA 10.0s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled
