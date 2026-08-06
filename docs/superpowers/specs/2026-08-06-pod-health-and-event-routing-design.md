# Pod-only 健康判定与 Event 路由设计

## 背景

真实诊断 `7a4acaa9814c44d7` 中，当前 Pod 扫描已经返回 `abnormal_count=0`、`recent_restart_count=0`，但 Layer LLM 仍把多日前的累计重启次数解释成当前 `HighRestarts`，导致健康集群进入 Evidence/RCA，并产生大量重复 Event、describe 和可观测性调用。

本设计只处理 Pod 异常。Node、PVC、Prometheus 告警和其他资源不参与当前健康判定。

## 目标

1. 用确定性代码判定 Pod 健康，不允许 LLM 用历史日志、历史 Event、Runbook 或累计 `restartCount` 推翻健康事实。
2. 最近重启窗口固定为 30 分钟。
3. 健康集群从 Layer 直接进入 Conclusion，不执行 Evidence、RCA 或 Event。
4. 异常诊断中的 Event 按异常类型按需调用，同一 Pod 最多执行一次；空结果也视为该维度已完成。
5. 保留 Kubernetes 日志和 Elastic 日志为独立证据维度，即使内容重复也分别呈现。

## 非目标

- 不扩展 Node、PVC、Service 或告警级健康诊断。
- 不因本次改动重构完整 Evidence Collector。
- 不改变多异常并发扇出的阈值和并发模型。
- 不删除 Event 工具。

## 权威健康规则

健康判定只使用本轮成功的全局 Pod 表格扫描所产生的结构化事实。

对所有活跃 Pod：

- `STATUS=Running`；
- `READY` 当前容器数等于期望容器数；
- 没有明确证据证明最近 30 分钟发生过容器重启。

以上条件全部成立时，结果固定为 `HEALTHY`。成功终止的 Job Pod（`Completed` / `Succeeded`）不是活跃异常，从检查集合中排除。

以下任意条件成立时为当前 Pod 异常：

- 状态不是 `Running`、`Completed` 或 `Succeeded`；
- `Running` 但 `READY` 不完整，例如 `0/1`；
- 存在最近 30 分钟新增重启的明确证据。

### 最近重启证据

以下任一正向信号可证明最近重启：

1. kubectl 表格的 `RESTARTS` 为 `N (age ago)`，且 `N > 0`、`age <= 30m`；
2. Pod `lastState.terminated.finishedAt >= now - 30m`；
3. `increase(kube_pod_container_status_restarts_total[30m]) > 0`。

累计次数本身不是当前异常：

- `0`：没有重启，正常；
- `46 (6d3h ago)`：最近重启超过窗口，正常；
- 只有 `46`、没有时间：不能证明最近 30 分钟重启，不触发异常；
- Prometheus、Last State 或时间信息缺失：不创造异常，继续按当前状态和 READY 判定。

时间边界按 `<= 30m` 纳入近期重启。ObservationProcessor 输出 `restart_window_seconds=1800`，避免下游自行猜测窗口。

## 确定性数据流

```text
kubectl get pods -A
  -> ObservationProcessor
       row_count
       scan_confirmed
       abnormal_count
       recent_restart_count
       recent_restart_rows
       restart_window_seconds=1800
  -> LayerClassifier handoff
  -> PodHealthDecision
       active abnormality present -> force ABNORMAL
       confirmed scan + zero abnormality -> force HEALTHY
       no confirmed scan -> preserve normal failure/fallback behavior
  -> graph router
       HEALTHY -> conclusion
       ABNORMAL -> evidence / parallel_evidence
```

`PodHealthDecision` 是双向保护：不仅把错误的 `HEALTHY` 修正为 `ABNORMAL`，还会在成功扫描明确无异常时把 LLM 编造的 `ABNORMAL` 修正为 `HEALTHY`。构建 handoff 时，只要存在已确认的当前扫描，`abnormal_pods` 和 `issue_groups` 必须完全以扫描结果为准；扫描为空时清除 LLM 生成的异常对象。

如果全局扫描失败、为空、输出无法识别为 Pod 表格，不能声称扫描确认健康；此时不执行强制 HEALTHY，保留既有错误/回退路径。

## HEALTHY 输出

HEALTHY 报告由代码模板生成，不调用 LLM：

- 结论：当前 Pod 运行健康；
- 检查范围：本轮扫描的 Pod 数；
- 判定：所有活跃 Pod Running、Ready 完整；
- 重启窗口：最近 30 分钟未发现新增重启；
- 明确说明累计历史重启不代表当前异常。

报告不得引用历史日志、历史 Event 或 Runbook 形成故障结论。

## Event 调用矩阵

Event 不是健康检查的固定首轮采集项，只在 Kubernetes 生命周期类异常中调用：

| Pod 异常 | Event | 主要证据 |
| --- | --- | --- |
| `PendingUnschedulable` / `FailedScheduling` | 调用 | status、Event、Pod spec |
| `ImagePullFailed` | 调用 | status、Event、image/imagePullSecrets |
| `VolumeMountFailed` | 调用 | status、Event、volume/PVC 配置 |
| `SandboxCreateFailed` | 调用 | status、Event、CNI/runtime 信号 |
| `NotReadyProbeFailed` | 调用 | status、probe 配置、Event、日志 |
| `Evicted` | 调用 | status、Event、Pod/Node 压力事实 |
| `TerminatingStuck` | 调用 | YAML/finalizer、Event、lifecycle |
| `CrashLoopBackOffRuntime` | 非固定 | Last State、previous K8s logs、ES logs、Metrics，必要时 Trace/Topology |
| `OOMKilled` | 非固定 | Last State/exit 137、K8s logs、ES logs、Metrics |
| `ConfigError` | 按事件原因需要时调用 | status、YAML、配置引用、日志 |
| `HEALTHY` | 禁止 | Layer 结构化 Pod 扫描 |

Event 去重键为 `(namespace, pod_name)`。同一诊断 run 内，无论计划、LLM 补证或多个 purpose 如何描述，同一 Pod 的 `kubectl_events` 最多真实执行一次。第一次成功、空结果、NotFound 或工具错误都算“已尝试”，后续调用返回去重事件而不再次访问 MCP。空 Event 作为负向证据保留，不能触发重复补采。

提示词只负责帮助选择；调用矩阵和最多一次约束必须由确定性代码执行，不能仅依赖 LLM 遵守。

## 独立证据维度

Kubernetes 容器日志与 Elastic/Filebeat 日志是两个独立来源。即使时间、文本和错误行相同，也必须分别保留来源、查询条件、结果和引用。去重只能发生在同一工具、同一来源、同一参数的重复调用之间，不能跨来源合并。

## 错误处理

- Pod 扫描命令失败：不强制 HEALTHY，报告采集失败而不是伪造健康。
- Event 为空：记录 `empty`，视为已完成，不重试。
- Event 工具失败：记录 `error`，视为已尝试，不在同一 run 重复调用。
- 近期重启时间缺失：不以累计次数推断近期重启。
- LLM 与结构化扫描冲突：结构化扫描胜出，并在 Layer reasoning 中记录确定性修正原因。

## 配置

新增或明确以下配置，默认值即产品规则：

```yaml
workflow:
  layer:
    health:
      restart_window_minutes: 30
      deterministic_fast_path: true
  evidence:
    event_policy:
      mode: by_abnormal_type
      max_calls_per_pod: 1
```

即使配置缺失，代码默认仍为 30 分钟和单 Pod 一次，避免旧配置部署后退回误报行为。

## 测试与验收

必须覆盖：

1. 所有 Pod `Running + Ready`、restart=0，强制 HEALTHY。
2. 累计 restart=46、最后一次 6 天前，强制 HEALTHY。
3. 累计 restart>0 但无时间，且无其他近期正向证据，强制 HEALTHY。
4. `Running 0/1` 判 ABNORMAL。
5. `Running 1/1` 且 `1 (29m59s ago)` 判 ABNORMAL。
6. `Running 1/1` 且 `1 (30m01s ago)` 判 HEALTHY。
7. LLM 输出 HighRestarts，但结构化扫描为零异常，清除异常组并强制 HEALTHY。
8. LLM 输出 HEALTHY，但结构化扫描包含异常，强制 ABNORMAL。
9. HEALTHY 路径不进入 Evidence/RCA，不执行 Event。
10. Event 矩阵中的生命周期异常会调用 Event；CrashLoop/OOM 不把 Event 作为固定项。
11. 同一 Pod 多次 Event 请求只真实执行一次；首次为空或失败也不重试。
12. Kubernetes 日志和 Elastic 日志内容相同时，最终证据中仍保留两个独立维度。
13. 原有多异常并发、QUERY direct 和异常 Case 测试继续通过。

真实回归使用类似 `7a4acaa9814c44d7` 的集群状态：控制面 Pod 累计重启较高但最后重启在 6 天前，预期秒级进入 HEALTHY 快速路径，工具调用仅保留 Layer 所需 Pod 状态扫描，不再出现 50+ 次采证调用。
