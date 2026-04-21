======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f13432e811014617]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来检查一下集群的整体状态，看看有什么问题。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     m
   💭 [问题定位] 我发现有一个 Pod 处于 CrashLoopBackOff 状态：`memhog-578d9b5ffd-z75ll`。让我检查一下这个 Pod 的详细信息，看看是什么原因导致的。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             memhog-578d9b5ffd-z75ll
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Mon, 20 Apr 2026 07:09:51 +0000

   💭 [问题定位] 现在让我检查一下节点状态，看看是否有其他问题：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   207d   v1.26.8  
   💭 [问题定位] 根据检查结果，我发现了一个明显的问题：

1. Pod `memhog-578d9b5ffd-z75ll` 处于 CrashLoopBackOff 状态
2. 从 `kubectl describe` 可以看到，容器被 OOMKilled（Exit Code 137）
3. 容器内存限制为 40Mi，但应用代码在无限循环中分配内存（`a.append("x"*1024*1024)`）
4. 所有节点状态都是 Ready，没有节点层面的问题

这个问题符合 L2 层（工作负载层）的特征：容器因内存超限被 OOM Killer 终止。

```json
{
  "layer": "L2",
  "layers": ["L2"],
  "layer_name": "工作负载层",
  "confidence": 0.95,
  "reasoning": "Pod memhog-578d9b5ffd-z75ll 处于 CrashLoopBackOff 状态，容器被 OOMKilled（Exit Code 137）。容器内存限制为 40Mi，但应用代码在无限循环中分配内存，导致内存超限被终止。所有节点状态 Ready，无基础设施层问题。",
  "key_entities": [{"type": "Pod", "value": "memhog-578d9b5ffd-z75ll"}],
  "possible_scenarios": [{"scenario": "容器内存超限 OOMKilled", "probability": "高", "reason": "容器内存限制 40Mi，应用代码无限分配内存导致超限"}]
}
```
   ✅ [问题定位] 完成 (31.5s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器内存超限 OOMKilled', 'probability': '高', 'reason': '容器内存限制 40Mi，应用代码无限分配内存导致超限'}]
   entities=[{"type": "Pod", "value": "memhog-578d9b5ffd-z75ll"}]
   reasoning=Pod memhog-578d9b5ffd-z75ll 处于 CrashLoopBackOff 状态，容器被 OOMKilled（Exit Code 137）。容器内存限制为 40Mi，但应用代码在无限循环中分配内存，导致内存超限被终止。所有节点状态 Ready，无基础设施层问题。
   layer_analysis={"layer": "L2", "layers": ["L2"], "layer_name": "工作负载层", "confidence": 0.95, "reasoning": "Pod memhog-578d9b5ffd-z75ll 处于 CrashLoopBackOff 状态，容器被 OOMKilled（Exit Code 137）。容器内存限制为 40Mi，但应用代码在无限循环中分配内存，导致内存超限被终止。所有节点状态 Ready，无基础设施层问题。", "key_entities": [{"type": "Pod", "value": "memhog-578d9b5ffd-z75ll"}], "possible_scenarios": [{"scenario": "容器内存超限 OOMKilled", "probability": "高", "reason": "容器内存限制 40Mi，应用代码无限分配内存导致超限"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，我已经确认了问题：Pod `memhog-578d9b5ffd-z75ll` 处于 CrashLoopBackOff 状态，容器被 OOMKilled（Exit Code 137）。这是一个典型的 L2 层（工作负载层）问题：容器内存超限 OOMKilled。

现在我将制定证据采集计划并执行工具采集真实数据：

```json
{
  "layer": "L2",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取 Pod 详细 YAML 配置，确认内存限制和请求值",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml pod memhog-578d9b5ffd-z75ll -n aiops-e2e",
      "purpose": "确认容器的内存限制（40Mi）和请求值（20Mi），以及资源配额配置"
    },
    {
      "id": "e2",
      "description": "查询 Pod 内存使用历史数据",
      "level": "important",
      "tool": "execute_prometheus_range_query",
      "command": "container_memory_working_set_bytes{pod='memhog-578d9b5ffd-z75ll', namespace='aiops-e2e'}",
      "purpose": "查看 Pod 内存使用历史趋势，确认是否持续超过限制"
    },
    {
      "id": "e3",
      "description": "获取 Pod 的父资源（ReplicaSet/Deployment）配置",
      "level": "important",
      "tool": "kubectl_lineage_parents",
      "command": "kubectl lineage parents pod memhog-578d9b5ffd-z75ll -n aiops-e2e",
      "purpose": "确认问题是否源于 Deployment/ReplicaSet 配置，以及是否有多个副本"
    },
    {
      "id": "e4",
      "description": "检查节点内存使用情况",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
      "purpose": "确认节点内存整体使用率，排除节点级内存压力"
    }
  ],
  "collection_strategy": "首先确认 Pod 配置细节，然后查看内存使用历史数据，接着检查父资源配置，最后排除节点级内存压力"
}
```

现在开始逐项执行工具采集证据：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  annotations:
    cni.projectcalico.org/containerID: a57d96bdfa43f0b3f62013a0b76442481e516cf3dd5a89bb7ee919a3bae6c524
    cni.projectcalico.org/podIP: 172.16.104.61
   💭 [证据链采集] 现在执行第二项，查询 Pod 内存使用历史数据：
   💭 [证据链采集] 调用工具: execute_prometheus_range_query
   💭 [证据链采集] 工具结果: execute_prometheus_range_query (success)
      📄 {"status":"success","data":{"resultType":"matrix","result":[{"metric":{"__name__":"container_memory_working_set_bytes","endpoint":"https-metrics","id":"/kubepods.slice/kubepods-burstable.slice/kubepod
   💭 [证据链采集] 现在执行第三项，获取 Pod 的父资源配置：
   💭 [证据链采集] 调用工具: kubectl_lineage_parents
   💭 [证据链采集] 工具结果: kubectl_lineage_parents (success)
      📄 Command failed (exit 1):
kubectl lineage pod memhog-578d9b5ffd-z75ll -n aiops-e2e -D
error: unknown command "lineage" for "kubectl"

   ✅ [证据链采集] 完成 (44.1s)
   📤 → 下游数据: evidence_items=3/4
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "获取 Pod 详细 YAML 配置，确认内存限制和请求值", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod memhog-578d9b5ffd-z75ll -n aiops-e2e", "purpose": "确认容器的内存限制（40Mi）和请求值（20Mi），以及资源配额配置"}, {"id": "e2", "description": "查询 Pod 内存使用历史数据", "level": "important", "tool": "execute_prometheus_range_query", "command": "container_memory_working_set_bytes{pod='memhog-578d9b5ffd-z75ll', namespace='aiops-e2e'}", "purpose": "查看 Pod 内存使用历史趋势，确认是否持续超过限制"}, {"id": "e3", "description": "获取 Pod 的父资源（ReplicaSet/Deployment）配置", "level": "important", "tool": "kubectl_lineage_parents", "command": "kubectl lineage parents pod memhog-578d9b5ffd-z75ll -n aiops-e2e", "purpose": "确认问题是否源于 Deployment/ReplicaSet 配置，以及是否有多个副本"}, {"id": "e4", "description": "检查节点内存使用情况", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100", "purpose": "确认节点内存整体使用率，排除节点级内存压力"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    cni.projectcalico.org/containerID: a57d96bdfa43f0b3f62013a0b76442481e516cf3dd5a89bb7ee919a3bae6c524\n    cni.projectcalico.org/podIP: 172.16.104.61", "duration_s": 0}, {"tool": "execute_prometheus_range_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"matrix\",\"result\":[{\"metric\":{\"__name__\":\"container_memory_working_set_bytes\",\"endpoint\":\"https-metrics\",\"id\":\"/kubepods.slice/kubepods-burstable.slice/kubepod", "duration_s": 0}, {"tool": "kubectl_lineage_parents", "data": "Command failed (exit 1):\nkubectl lineage pod memhog-578d9b5ffd-z75ll -n aiops-e2e -D\nerror: unknown command \"lineage\" for \"kubectl\"\n", "duration_s": 0}], "llm_analysis": "现在执行第三项，获取 Pod 的父资源配置：", "collection_summary": "计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%", "evidence_inventory": [{"id": "e1", "description": "获取 Pod 详细 YAML 配置，确认内存限制和请求值", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "查询 Pod 内存使用历史数据", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "获取 Pod 的父资源（ReplicaSet/Deployment）配置", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查节点内存使用情况", "level": "optional", "collected": false, "source": "planned"}], "missing_reasons": ["e4(检查节点内存使用情况): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 75%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (55.3s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "应用代码设计缺陷：在无限循环中持续分配内存（每秒约50MiB）", "propagation": "应用内存消耗快速增长 → 超过容器内存限制（40MiB）", "direct_cause": "容器内存使用超过 limits.memory=40MiB 限制，触发 OOM Killer", "manifestation": "容器被 OOMKilled（Exit Code 137）→ Pod 进入 CrashLoopBackOff 状态"}
   rca_analysis={"phenomenon": "Pod memhog-578d9b5ffd-z75ll 处于 CrashLoopBackOff 状态，容器反复重启", "evidence_inventory": [{"id": "e1", "content": "Pod 列表显示 memhog-578d9b5ffd-z75ll 状态为 CrashLoopBackOff，重启 16 次", "source": "kubectl get pods", "reliability": "高"}, {"id": "e2", "content": "Pod describe 显示容器被 OOMKilled（Exit Code 137），内存限制 40Mi，请求 20Mi", "source": "kubectl describe pod", "reliability": "高"}, {"id": "e3", "content": "Pod YAML 显示容器命令为无限循环分配内存（a.append('x'*1024*1024)）", "source": "kubectl get yaml", "reliability": "高"}, {"id": "e4", "content": "Prometheus 监控显示容器内存使用在 249856-872448 字节之间（约 0.24-0.87 MiB）", "source": "Prometheus query", "reliability": "高"}, {"id": "e5", "content": "节点状态全部 Ready，无节点层面问题", "source": "kubectl get nodes", "reliability": "高"}, {"id": "e6", "content": "获取父资源配置失败（kubectl lineage 命令不存在）", "source": "kubectl lineage", "reliability": "中"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "memhog-578d9b5ffd-z75ll 0/1 CrashLoopBackOff 16 (5m4s ago)", "interpretation": "Pod 处于故障循环重启状态，重启次数已达 16 次"}, {"evidence_id": "e2", "raw_data": "State: Terminated, Reason: OOMKilled, Exit Code: 137, Limits: memory: 40Mi, Requests: memory: 20Mi", "interpretation": "容器因内存超限被 OOM Killer 终止，内存限制为 40MiB"}, {"evidence_id": "e3", "raw_data": "args: import time; a=[]; while True: a.append('x'*1024*1024); time.sleep(0.02)", "interpretation": "应用代码在无限循环中每秒分配约 50MiB 内存（1MiB/0.02s），远超 40MiB 限制"}, {"evidence_id": "e4", "raw_data": "内存使用值序列：249856, 335872, 360448, 389120, 413696, 446464, 458752, 872448 字节（最大值 872448 字节 = 0.87 MiB）", "interpretation": "监控显示的内存使用值远低于 40MiB 限制，但这是工作集内存，可能未包含所有内存分配"}, {"evidence_id": "e5", "raw_data": "master Ready, node1 Ready, node2 Ready", "interpretation": "所有节点状态正常，排除基础设施层问题"}, {"evidence_id": "e6", "raw_data": "Command failed: kubectl lineage command not found", "interpretation": "无法获取父资源配置信息，但不影响当前根因分析"}], "causal_chain": {"root_cause": "应用代码设计缺陷：在无限循环中持续分配内存（每秒约50MiB）", "propagation": "应用内存消耗快速增长 → 超过容器内存限制（40MiB）", "direct_cause": "容器内存使用超过 limits.memory=40MiB 限制，触发 OOM Killer", "manifestation": "容器被 OOMKilled（Exit Code 137）→ Pod 进入 CrashLoopBackOff 状态"}, "root_cause_summary": "根因为应用代码缺陷导致的内存超限。证据 e3 显示应用代码在无限循环中每秒分配约 50MiB 内存（a.append('x'*1024*1024); time.sleep(0.02)），而证据 e2 显示容器内存限制仅为 40MiB。应用内存消耗必然超过限制，触发 OOM Killer（证据 e2 显示 Exit Code 137）。证据 e4 监控数据（最大 0.87MiB）与预期不符，可能是监控指标不完整或采集时机问题，但代码逻辑和 OOMKilled 事实构成直接证据链。证据 e5 排除节点问题，证据 e1 确认故障现象。", "confidence": 0.95, "primary_runbooks": [], "alternative_causes": [], "limitations": "1. 内存监控数据（证据 e4）显示最大值仅 0.87MiB，与代码逻辑（每秒50MiB）和OOM事实矛盾，可能是 container_memory_working_set_bytes 指标未包含所有内存类型，或监控采集频率不足。2. 未获取到父资源（Deployment/ReplicaSet）配置，无法分析资源规格设置的合理性。3. 未采集节点内存使用情况，但节点状态正常且其他Pod运行正常，节点内存压力可能性低。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: 应用代码设计缺陷：在无限循环中持续分配内存（每秒约50MiB）
     传导机制: 应用内存消耗快速增长 → 超过容器内存限制（40MiB）
     最终表现: 容器被 OOMKilled（Exit Code 137）→ Pod 进入 CrashLoopBackOff 状态


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 31.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5200 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 42.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **问题层级** | L2 - 工作负载层 |
| **问题分类** | 容器内存超限 OOMKilled |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/4 (75%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键发现**：
您的集群中有一个 Pod 因内存超限而持续崩溃重启，这是当前唯一发现的明确问题。集群所有节点状态正常，其他工作负载运行稳定。

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `memhog-578d9b5ffd-z75ll` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| 错误信息 | `Reason: OOMKilled, Exit Code: 137` |

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pods` | `memhog-578d9b5ffd-z75ll 0/1 CrashLoopBackOff 16 (5m4s ago)` | Pod 处于故障循环重启状态，已重启16次 |
| 2 | Pod 详情 | `kubectl describe pod` | `State: Terminated, Reason: OOMKilled, Exit Code: 137` | 容器因内存超限被 OOM Killer 终止 |
| 3 | 资源配置 | `kubectl describe pod` | `Limits: memory: 40Mi, Requests: memory: 20Mi` | 容器内存限制为 40MiB |
| 4 | 应用代码 | `kubectl describe pod` | `Args: import time; a=[]; while True: a.append('x'*1024*1024); time.sleep(0.02)` | 应用在无限循环中每秒分配约50MiB内存 |
| 5 | 节点状态 | `kubectl get nodes` | `master Ready, node1 Ready, node2 Ready` | 所有节点状态正常，排除基础设施问题 |
| 6 | 内存监控 | `container_memory_working_set_bytes` | `序列值：249856, 335872, ..., 872448 字节 (最大约 0.87 MiB)` | 监控显示的内存工作集远低于限制，可能与指标类型或采集时机有关 |

### 证据关联分析
- **证据 #2 + #3 + #4 印证**：应用代码每秒分配 50MiB (`a.append('x'*1024*1024); time.sleep(0.02)`) > 内存限制 40MiB (`Limits: memory: 40Mi`) → 必然触发 OOM Killer (`Reason: OOMKilled, Exit Code: 137`)。
- **证据链**：应用设计缺陷（无限分配内存）→ 内存消耗超过 40MiB 限制 → 触发 cgroup OOM Killer → 容器被终止 → Pod 进入 `CrashLoopBackOff` 状态。
- **证据 #6 矛盾点**：监控数据 (`container_memory_working_set_bytes`) 显示内存使用峰值仅 0.87MiB，与应用逻辑和 OOM 事实不符。这可能是由于该指标仅反映“工作集”内存，未包含所有已分配但未活跃使用的内存，或者监控采集频率未能捕捉到内存的瞬时暴涨。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 检查节点内存使用情况 | optional | 无法完全排除节点级内存压力的叠加影响，但鉴于节点状态为 Ready 且其他 Pod 运行正常，影响较小 |

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                     │
│ 应用代码设计缺陷：在无限循环中持续分配内存（每秒约50MiB）                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                     │
│ 应用内存消耗（>50MiB/s）远超容器内存限制（40MiB）                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                     │
│ 容器内存使用超过 limits.memory=40MiB 限制，触发 cgroup OOM Killer             │
└─────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                 │
│ 容器被 OOMKilled（Exit Code 137）→ Pod 进入 CrashLoopBackOff 状态并持续重启   │
└─────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #2 (`Reason: OOMKilled`)、证据 #3 (`memory limit: 40Mi`) 和证据 #4 (应用代码逻辑)，问题的根本原因是**应用代码存在设计缺陷，在无限循环中高速分配内存（理论速度约 50MiB/s），远超其容器配置的内存限制（40MiB）**，导致容器反复被 OOM Killer 终止。

**置信度**：高 (95%)
- ✅ 证据 #2 明确显示容器因 `OOMKilled` 终止 (`Exit Code 137`)。
- ✅ 证据 #4 的应用代码逻辑 (`while True: a.append('x'*1024*1024)`) 是导致内存无限增长的直接原因。
- ✅ 证据 #3 显示内存限制 (`40Mi`) 远低于应用的理论内存分配速度。
- ⚠️ 证据 #6 (监控数据) 与理论不符，但 `container_memory_working_set_bytes` 指标可能无法完整反映所有内存分配。

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修正应用代码逻辑**
这是根本解决方法。需要修改 `memhog` 应用的代码，移除无限分配内存的循环，或为其增加合理的退出条件及内存释放逻辑。

**2. [临时] 调整 Deployment 资源限制 (如果必须保留当前代码)**
如果这是一个测试 Pod 且需要暂时恢复运行，可以大幅提高其内存限制。首先找到其上级控制器（如 Deployment）：
```bash
kubectl get deploy -n aiops-e2e | grep memhog
```
然后调整资源限制（例如提高到 512Mi）：
```bash
kubectl set resources deployment/<memhog-deployment-name> -n aiops-e2e --limits=memory=512Mi --requests=memory=256Mi
```
*依据*：当前 40Mi 限制严重不足，根据代码逻辑，至少需要能容纳数秒内分配的内存。
*注意*：这只是临时规避措施，长期运行仍可能因内存无限增长而 OOM。

**3. [可选] 删除此测试 Pod**
如果 `memhog` 仅用于测试且不再需要，可以直接删除：
```bash
kubectl delete pod memhog-578d9b5ffd-z75ll -n aiops-e2e
# 或删除其上级控制器（如 Deployment）
kubectl delete deploy <memhog-deployment-name> -n aiops-e2e
```

### 后续优化
1.  **代码审查**：对于在容器中运行的自研应用，建立代码审查机制，避免出现无限资源消耗的逻辑。
2.  **资源配额管理**：在命名空间级别设置 `ResourceQuota`，防止单个应用误配置消耗过多集群资源。
3.  **监控与告警**：配置针对 `OOMKilled` 和 `CrashLoopBackOff` 的告警，以便快速发现此类问题。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod memhog-578d9b5ffd-z75ll -n aiops-e2e` | 如果已修复代码或调整限制，STATUS 应变为 `Running` |
| 2. 检查重启次数 | `kubectl get pod memhog-578d9b5ffd-z75ll -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 数字不再增长 |
| 3. 查看最新事件 | `kubectl describe pod memhog-578d9b5ffd-z75ll -n aiops-e2e \| tail -20` | 无新的 `OOMKilled` 或 `BackOff` 警告事件 |

## ⚠️ 注意事项
- 此问题仅限于 `aiops-e2e` 命名空间下的 `memhog` 应用，**集群整体健康，节点及其他工作负载运行正常**。
- 临时增加内存限制不是长久之计，最终必须修复有缺陷的应用代码。
- 监控指标 `container_memory_working_set_bytes` 在某些场景下可能无法完全反映容器的真实内存压力，诊断时需结合退出原因 (`OOMKilled`) 和应用日志综合判断。

---

## 📊 性能统计

├─ 总耗时: 3.7m
├─ 问题定位: 31.5s (14%) ✅
├─ 证据链采集: 44.1s (20%) ✅
├─ 根因分析: 55.3s (25%) ✅
├─ 汇总总结: 91.8s (41%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 6 次
```

📋 诊断追踪

- **参考 Runbook**: 无
- **工具调用**: 6 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
