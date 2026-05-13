## E2E 故障注入与验收

当前 `/ask` 主链已经切到“异常 Pod 状态优先”的诊断模式。

这份 E2E 只覆盖会直接表现为 Pod 异常状态的主线场景，不再把 `service selector mismatch` 这类“Pod 本身正常但服务拓扑异常”的案例放进主验收矩阵。

为 Pod 异常状态主线提供可复现的故障环境与验收脚本。每个主线异常类型都有一个专属 manifest，并通过 `aiops.e2e/*` annotations 标注期望状态、关联 runbook 和关键证据。

### 场景矩阵

| Pod 异常类型 | 典型状态 | Manifest | Runbook | 注入方式 |
|------|------|----------|---------|----------|
| Evicted | Evicted | `pod-evicted.yaml` | `pod-evicted.md` | emptyDir sizeLimit 30Mi 写满，触发本地临时存储驱逐 |
| VolumeMountFailed | Pending/ContainerCreating | `pod-volume-mount-failed.yaml` | `pod-volume-mount-failed.md` | 引用不存在的 ConfigMap 卷，触发 FailedMount |
| PendingUnschedulable | Pending | `pod-pending-unschedulable.yaml` | `pod-pending-unschedulable.md` | nodeSelector 指定不存在的节点标签，触发 FailedScheduling |
| NodeLostOrUnknown | Unknown | `pod-node-lost-unknown.yaml` | `pod-node-lost-unknown.md` | 先部署候选 Pod，再手动隔离所在节点或停止 kubelet |
| TerminatingStuck | Terminating | `pod-terminating-stuck.yaml` | `pod-terminating-stuck.md` | Pod 带 finalizer，`run_all.sh` 自动执行 delete 使其卡住 |
| OOMKilled | CrashLoopBackOff/Error | `pod-oomkilled.yaml` | `pod-oomkilled.md` | 小内存 limit + 持续内存分配 |
| CrashLoopBackOffRuntime | CrashLoopBackOff | `pod-crashloop-runtime.yaml` | `pod-crashloop-runtime.md` | 容器启动后输出运行时错误并 exit 2 |
| ImagePullFailed | ImagePullBackOff/ErrImagePull | `pod-imagepull-failed.yaml` | `pod-imagepull-failed.md` | 使用 `registry.invalid` 镜像地址强制拉取失败 |
| SandboxCreateFailed | ContainerCreating/Pending | `pod-sandbox-create-failed.yaml` | `pod-sandbox-create-failed.md` | 使用不存在的 runtimeClassName |
| ConfigError | CrashLoopBackOff/CreateContainerConfigError/CreateContainerError | `pod-config-error.yaml` | `pod-config-error.md` | 启动打印配置错误并进入 CrashLoopBackOff |
| NotReadyProbeFailed | Running 但 READY=0/1 | `pod-notready-probe-failed.yaml` | `pod-notready-probe-failed.md` | readinessProbe 固定失败 |

### 使用方式

```bash
cd test/e2e

# 1. 部署所有场景
./run_all.sh

# 2. 手动取证（确认场景注入成功）
./validate.sh

# 3. 运行验收测试（需要 AIOps 服务已启动）
AIOPS_ENDPOINT=http://10.2.0.48:30800 ./test_scenarios.sh

# 4. 单独测试某个场景
./test_scenarios.sh l0   # 兼容分类 L0
./test_scenarios.sh l2   # 兼容分类 L2
```

### 特殊场景说明

- `NodeLostOrUnknown` 无法只靠 Kubernetes manifest 安全、稳定地制造；manifest 会创建带标识的候选 Pod，需在测试环境中停止该 Pod 所在节点 kubelet 或隔离节点网络后再验证 Unknown 状态。
- `TerminatingStuck` 需要删除动作触发；`run_all.sh` 会先清理旧 finalizer，再 apply manifest，最后执行 `kubectl delete pod terminating-stuck --wait=false`。

### 前置依赖

- `kubectl`（已配置集群访问）
- `curl`
- AIOps 服务已启动（`/health` 返回 healthy）

---

## 准确率测试 (`test_accuracy.py`)

### 概述

向 `/ask?stream=false` 发送同步请求，获取完整 Markdown 诊断报告，用正则从报告文本中提取四项质量指标，与预期值对比。

### 测试流程

```
1. 选择场景（如 pod-imagepull-failed），场景包含预定义的 query + 期望层级 + 期望 Runbook
2. 发送 N 次 HTTP 请求（可并发）
   → GET /ask?q=<场景预定义问题>&stream=false
   → 等待完整 Markdown 报告返回
3. 对每次返回的报告文本，用正则提取四项指标
4. 汇总 N 次结果，计算通过率和平均值
```

### 用法

```bash
# 单场景单次
python test_accuracy.py --scenario pod-imagepull-failed

# 单场景 50 次，5 并发（压力/稳定性测试）
python test_accuracy.py --scenario pod-imagepull-failed -n 50 -c 5

# 所有场景各 3 次，2 并发
python test_accuracy.py --scenario all -n 3 -c 2

# 自定义问题
python test_accuracy.py -q "namespace=aiops-e2e pod xxx 异常" \
  --expect-layer L2 --expect-runbook pod-oomkilled
```

### 四项质量指标详解

#### 1. MTTR（平均修复时间）

| 项目 | 说明 |
|------|------|
| **定义** | 从请求发出到诊断报告返回的总耗时 |
| **阈值** | < 15 分钟（900 秒） |
| **数据来源** | 优先从报告中提取 `总耗时: X.Xm`，回退到 HTTP 请求 wall clock 计时 |
| **提取正则** | `总耗时[：:\s]*([\d.]+)(s\|m\|h)` |
| **汇总方式** | N 次请求的 MTTR 取算术平均值 |

报告中的原始格式（由 `metrics.format_stats_block()` 生成）：

```
## 📊 性能统计
├─ 总耗时: 2.2m
├─ 问题定位: 45.3s (34%) ✅
├─ 证据采集: 28.1s (21%) ✅
├─ 根因分析: 35.2s (27%) ✅
├─ 汇总总结: 23.4s (18%) ✅
├─ LLM 调用: 8 次
└─ 工具调用: 12 次
```

#### 2. 层级准确率

| 项目 | 说明 |
|------|------|
| **定义** | 诊断报告中识别的问题层级是否与场景预期一致 |
| **阈值** | >= 80% |
| **数据来源** | 报告中的层级字段（L0-L4 / QUERY / HEALTHY） |
| **汇总方式** | `正确次数 / 成功请求总数 × 100%` |

提取优先级（三级回退）：

1. **表格格式**：`| **问题层级** | L3 ...` → 提取 `L3`
2. **文本格式**：`层级: L3` 或 `**层级**: L3` → 提取 `L3`
3. **频率统计**：统计报告中所有 `L0`-`L4` 出现次数，取最多的

场景预期值（内置矩阵）：

| 场景 ID | 预期层级 | 预期 Runbook |
|---------|---------|-------------|
| pod-evicted | L0 | pod-evicted |
| pod-pending-unschedulable | L1 | pod-pending-unschedulable |
| pod-oomkilled | L2 | pod-oomkilled |
| pod-imagepull-failed | L3 | pod-imagepull-failed |
| pod-config-error | L4 | pod-config-error |

这些场景都要求 layer 节点先锁定异常 Pod，再给出：

- `primary_pod`
- `pod_status_keyword`
- `pod_abnormal_type`

**计算示例**：50 次请求，45 次成功返回，其中 40 次层级正确 → `40/45 = 88.9%` ✅

#### 3. 证据完整率

| 项目 | 说明 |
|------|------|
| **定义** | 诊断过程中实际采集的证据项占计划采集项的比例 |
| **阈值** | >= 80% |
| **数据来源** | 报告中质量指标表格的证据完整率字段 |
| **提取正则** | `证据完整率.*?\|\s*(\d+)%\s*\((\d+)/(\d+)\)` |
| **汇总方式** | N 次请求的证据完整率取算术平均值 |

报告中的原始格式（由 `metrics.format_metrics_block()` 生成）：

```
## 📈 质量指标

| 指标 | 要求 | 实际 | 状态 |
|------|------|------|------|
| **MTTR** | < 10m | 2.2m | ✅ 达标 |
| **根因置信度** | >= 80% | 85% | ✅ 达标 |
| **证据完整率** | > 90% | 80% (4/5) | ⚠️ 不足 |
| **Runbook 覆盖率** | >= 80% | 100% | ✅ 达标 |
```

**`4/5` 的含义**：
- `5` = evidence 节点 LLM 规划的证据项总数（`evidence_planned`）
- `4` = 其中实际采集成功的项数（`evidence_collected`，标记为 `collected=True`）
- 比率 = `4/5 = 80%`

这些数字由 `WorkflowExecutor` 在 evidence 节点完成后从 `state["evidence_items"]` 统计。

**计算示例**：50 次请求，45 次成功，证据完整率分别为 80%, 100%, 60%, ... → 取平均值 82.5% ✅

#### 4. Runbook 覆盖率

| 项目 | 说明 |
|------|------|
| **定义** | 诊断报告是否引用了与场景匹配的 Runbook |
| **阈值** | >= 80% |
| **数据来源** | 报告中的「核心 Runbook」和「参考 Runbook」字段，以及 `fetch_runbook` 日志提取到的 Runbook ID |
| **提取正则** | `核心\s*Runbook[：:\s]*(.*)` / `参考\s*Runbook[：:\s]*(.*)` |
| **匹配逻辑** | 只要核心 Runbook、参考 Runbook 列表、或日志提取的 Runbook ID 中任意一个包含场景预期 Runbook ID（大小写不敏感），就判定为匹配 |
| **汇总方式** | `匹配次数 / 成功请求总数 × 100%` |

报告中的原始格式（由 `metrics.format_metrics_block()` 生成）：

```
📋 诊断追踪
- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed
- **工具调用**: 7 次
- **LLM 调用**: 4 次
```

**匹配示例**：场景 `pod-oomkilled` 的 `expect_runbook = "pod-oomkilled"`。只要报告中的 `核心 Runbook`、`参考 Runbook`、或 `fetch_runbook` 日志里出现 `pod-oomkilled`，就会判定匹配成功 ✅

**计算示例**：50 次请求，45 次成功，其中 41 次 Runbook 匹配 → `41/45 = 91.1%` ✅

### 汇总报告示例

```
============================================================
  质量指标汇总
============================================================
| 指标                 | 阈值         | 实际         | 状态     |
|----------------------|--------------|--------------|----------|
| MTTR                 | < 15m        | 3.2m         | ✅       |
| 层级准确率            | >= 80%       | 88.9%        | ✅       |
| Runbook 覆盖率        | >= 80%       | 91.1%        | ✅       |
| 证据采集率            | >= 80%       | 82.5%        | ✅       |
```

### 输出文件

每次运行在 `testreports/<timestamp>/` 下生成：

| 文件 | 说明 |
|------|------|
| `<scenario_id>/response_N.md` | 每次请求的完整 Markdown 诊断报告 |
| `stats.json` | 结构化 JSON 汇总（含每次运行的原始指标） |

### 指标产生链路

```
用户请求 → WorkflowExecutor 执行 4 节点工作流
  │
  ├─ layer 节点 → 输出层级 (L0-L4)
  ├─ evidence 节点 → 输出 evidence_items（每项有 collected 标记）
  ├─ rca 节点 → 输出 root_cause + confidence
  └─ conclusion 节点 → 输出完整 Markdown 报告
  │
  ├─ metrics.format_stats_block() → 性能统计（总耗时、各节点耗时）
  └─ metrics.format_metrics_block() → 质量指标表格（MTTR、置信度、证据率、Runbook）
  │
  └─ 拼接为最终报告文本 → 返回给 test_accuracy.py
  │
  └─ test_accuracy.py 用正则提取 → 与预期对比 → 汇总报告
```
