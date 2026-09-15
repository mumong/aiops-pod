## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 `app` 最近终止原因 `Error`，退出码 `137` | 确认容器异常终止，结合退出码 137 推断为操作系统发送 SIGKILL 信号 |
| 2 | K8s State | kubernetes | Pod 状态 `Terminating`，持续时间已达 `63m`；删除时间戳确认处于删除流程 | 确认 Pod 处于挂起状态，且长时间无法完成清理 |
| 3 | K8s State | kubernetes | 资源配置：内存请求 `24Mi`，限制 `96Mi`；CPU 请求 `20m`，限制 `200m` | 提供环境上下文，表明该 Pod 资源限制较紧 |
| 4 | Metric | prometheus | 容器 `app` 重启总次数 `0` | 证实该容器自启动后未经历过常规重启，直接异常退出且未恢复 |

当前证据确认了容器因信号被杀及 Pod 长时间卡在 Terminating 状态的事实。但判定根因的决定性证据缺失：日志采集（elasticsearch）和链路追踪（deepflow+tempo）均为空，且 `unknowns` 字段指出缺少关于持有 `aiops.lab/hold` 自定义终结者的控制器/资源的身份确认，以及触发 SIGKILL 的具体原因（如 OOMKilled 或手动干预），导致无法区分是资源耗尽导致的自动终止还是外部控制逻辑导致的主动阻断。

## 🎯 根因分析 · g1

### 因果链

```text
容器 app 异常退出 (Exit Code 137) → K8s 接收终止信号并设置 deletionTimestamp → 自定义终结器 'aiops.lab/hold' 未被释放导致删除阻塞 → Pod 持续停留在 Terminating 状态
```
*注：终止信号的确切来源（OOMKilled vs 其他 SIGKILL 触发源）未确认。*

### 根因结论

证据不足。

当前事实确认了 Pod 因容器退出码 `137` 进入删除流程，但因长期卡在 `Terminating` 状态而引发关注。诊断受阻于以下决定性事实的缺失：
1.  **终结器阻断源头不明**：存在名为 `aiops.lab/hold` 的自定义终结器阻止了 Pod 删除，但无法确认是哪个控制器或外部资源持有该终结器，也无法查明其未能及时释放的原因。
2.  **异常根因（Root Cause）无法判定**：由于日志和链路追踪数据缺失，且 `container.last_terminated_reason` 仅标记为 `Error` 而非标准的 `OOMKilled`，无法确定容器是死于内存超限（OOM）还是被外部强制 KILL。

在未查明终结器持有者及容器被杀确切原因前，无法将故障根因指向具体的资源限制配置错误或控制器逻辑缺陷。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 12.7s
├─ 并发证据采集: 97.4s
│  └─ g1 aiops-case-11/workload: 97.4s (Evidence 86.3s, RCA 11.1s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
