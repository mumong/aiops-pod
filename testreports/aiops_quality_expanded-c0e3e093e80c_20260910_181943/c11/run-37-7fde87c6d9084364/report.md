## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload in aiops-case-11 is stuck in Terminating status for 72 minutes. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Status | status: `Terminating (lasts 72m)` | 确认 Pod 进入删除流程但卡住的时间长度 |
| 2 | K8s State | Pod Phase | phase: `Running` | 确认 Pod 仍在调度生命周期中，未被垃圾回收 |
| 3 | K8s State | Pod Condition | Ready: `False` (reason: `ContainersNotReady`) | 确认容器当前不可用 |
| 4 | K8s Event | K8s Event | 包含 `Exit Code: 137` | 指示容器此前已被强制终止，非当前删除卡点 |
| 5 | K8s Event | K8s Event | 包含 CNI 网络相关 Annotation 记录 | 确认网络插件已记录 Pod 网络状态 |
| 6 | K8s State | Container Last Exit | exit_code: `137` | 确认容器进程因 OOMKilled (137) 或信号终止退出，且 restart_count 为 0，确认这是当前唯一的存活容器 |

证据小结：
- K8s 层面确认 Pod 处于 `Terminating` 状态长达 72 分钟，且容器当前不可用 (Ready=False)，退出码 137 证明容器进程已被终止。
- 尽管容器进程已死，但 Pod 本身仍未从 API 服务器移除。
- Metrics/Logging/Tracing 数据缺失，无法追踪删除请求触发前的资源行为，但当前 K8s 层面的状态（长期 Terminating）强烈指向 API 层面对象删除受阻。

## 🎯 根因分析 · g1

### 因果链

```text
用户/系统发起 Pod 删除 → 自定义 finalizer aiops.lab/hold 阻止删除 → 拥有该 finalizer 的控制器未能清理 finalizer → API Server 拒绝删除对象 → Pod 长期卡在 Terminating 状态
```

### 根因结论

**根因：自定义 Finalizer (aiops.lab/hold) 阻止了 Pod 删除，且对应的控制器未能执行清理操作。**

- **证据支持**：K8s 状态显示 Pod 已进入 Terminating 阶段（`fact-69d08350bc68`），但持续时间异常（72分钟），且 Pod 仍保持 Running 的 Phase 但未就绪。Exit Code 137 (`fact-4055d8f36928`) 证明容器已退出，但 Pod 资源未释放，这是典型的 Finalizer 阻塞现象。
- **缺失环节**：输入数据中未包含具体的 K8s Event 显示 "finalizer" 字样，也未提供拥有 `aiops.lab/hold` finalizer 的控制器日志或状态。虽然事实来源中的 `unknowns` 和 `formal_rca` 指向该控制器失败，但根据“只用真实数据”和“每个结论必须由同一异常组、同一实体的事实支撑”的原则，直接引用正式 RCA 的特定字符串作为“证据”可能被视为间接。
- **修正与合规**：严格遵循“Agent 自主选择并组织少量高价值证据”且“正式 RCA 不可发布或证据不足时，明确写证据不足”。
    - 这里的 `formal_rca` 是输入的一部分，但根据指令“只用真实数据：数值、状态、错误原文...只能来自输入 facts... 正式 RCA 不可发布或证据不足时，明确写证据不足”，且“每个结论必须由同一异常组、同一实体的事实支撑”。
    - 输入中的 `unknowns` 明确指出了“Identity/status of the controller...”未知。
    - 证据表中**没有**任何事实明确列出了 `finalizer: aiops.lab/hold` 这个字符串。`fact-36fc68a97f01` 等是资源请求，`fact-e96e17d1ec04` 是 CNI 注释。
    - 因此，尽管 `formal_rca` 字段提供了推测，但**缺乏直接的 K8s State/Event/Config 事实来证实 finalizer 的存在及其阻碍作用**。K8s 事件仅显示了 Exit Code 和 CNI 注释，没有 finalizer 相关的警告。
    - 结论：现有证据仅能证明 Pod 在 Terminating 状态卡住，但**无法直接证实**是 `aiops.lab/hold` finalizer 导致的，因为事实列表中未包含 finalizer 配置或相关 Event。

**最终结论：证据不足。虽然 Pod 卡在 Terminating 状态 72 分钟（`fact-69d08350bc68`）且容器已因 Exit Code 137 退出（`fact-4055d8f36928`），但输入的 Kubernetes 事实（State, Event, Config）中未明确包含 `finalizer: aiops.lab/hold` 的配置记录或相关警告事件。因此，无法仅凭提供的工具事实确认为该特定 finalizer 导致，缺少决定性事实来确认 finalizer 的存在及其持有者的状态。**

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.8s
├─ 并发证据采集: 44.4s
│  └─ g1 aiops-case-11/workload: 44.4s (Evidence 37.6s, RCA 6.7s)
└─ 汇总总结: 16.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
