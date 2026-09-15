## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod 的 command 指定了可执行文件 /opt/app/unavailable-command，但该文件在基础镜像 python:3-alpine 中不存在，导致容器启动即因 'not found' 退出 (Exit Code 127)，Kubelet 反复重启导致 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff restarting failed container app in pod workload_aiops-case-v08` | 确认容器频繁重启进入 CrashLoopBackOff 状态 |
| 2 | K8s State | kubernetes | `last_terminated_reason: Error`, `last_exit_code: 127` | 证实容器异常终止原因及特定的命令未找到退出码 |
| 3 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 提供具体执行失败的日志，指出缺少的可执行文件路径 |

**证据关联说明：**
K8s 侧显示的 Exit Code 127 与 Elasticsearch 侧 `not found` 的 Shell 报错直接对应，确认了容器启动时执行指定二进制文件失败是导致 CrashLoopBackOff 的致命原因。

## 🎯 根因分析 · g1

### 因果链

```text
Command 配置引用了镜像中不存在的二进制文件 → 容器启动执行命令失败 (Exit Code 127) → Kubelet 检测退出触发重启退避 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：Pod 的 command 配置指定了可执行文件 `/opt/app/unavailable-command`，但该文件在基础镜像 `python:3-alpine` 中不存在。
- 这直接导致容器启动即因 'not found' 错误退出，返回 `Exit Code 127`（见证据 #2、#3）。
- 进而触发 Kubelet 的 CrashLoopBackOff 机制，表现为 Pod 持续重启（见证据 #1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.8s
├─ 并发证据采集: 42.8s
│  └─ g1 aiops-case-v08/workload: 42.8s (Evidence 35.0s, RCA 7.6s)
└─ 汇总总结: 6.1s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
