======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 528faee93ab94add]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您诊断集群的问题。首先让我检查集群的整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     m
   💭 [问题定位] 我发现了1个异常Pod：`memhog-578d9b5ffd-z75ll` 处于 `CrashLoopBackOff` 状态，重启了17次。让我检查这个Pod的详细信息来确认具体原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             memhog-578d9b5ffd-z75ll
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Mon, 20 Apr 2026 07:09:51 +0000

   💭 [问题定位] 现在我检查节点状态，看看是否有其他问题：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   207d   v1.26.8  
   💭 [问题定位] 现在让我检查是否有其他异常事件：
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 LAST SEEN               TYPE      REASON    OBJECT                        MESSAGE
2m40s (x279 over 62m)   Warning   BackOff   Pod/memhog-578d9b5ffd-z75ll   Back-off restarting failed container memhog 
   💭 [问题定位] 基于我的检查，我发现了以下问题：

1. **主要问题**：`memhog-578d9b5ffd-z75ll` Pod 处于 `CrashLoopBackOff` 状态，重启了17次
2. **根本原因**：从 `kubectl describe` 可以看到 `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`，这是典型的 OOMKilled 场景
3. **Pod配置**：内存限制为 40Mi，但应用代码在无限循环中分配内存（`a.append("x"*1024*1024)`），导致内存超限
4. **集群状态**：所有节点都处于 Ready 状态，没有节点层面的问题

根据五层模型，这是一个 **L2（工作负载层）** 问题，因为：
- 容器因内存超限被 OOM Killer 终止（Exit Code 137）
- Reason 明确为 OOMKilled
- 没有 Evicted 相关消息，排除 L0 存储卷超限问题
- 节点状态正常，排除 L1 节点问题
- 镜像拉取正常，排除 L3 网络问题

```json
{
  "layer": "L2",
  "layers": ["L2"],
  "layer_name": "工作负载层",
  "confidence": 0.95,
  "reasoning": "memhog-578d9b5ffd-z75ll Pod 处于 CrashLoopBackOff 状态，Last State 显示 Reason: OOMKilled, Exit Code: 137。容器内存限制为 40Mi，但应用代码在无限循环中分配内存，导致内存超限被 OOM Killer 终止。",
  "key_entities": [{"type": "Pod", "value": "memhog-578d9b5ffd-z75ll"}],
  "possible_scenarios": [{"scenario": "容器内存超限 OOMKilled", "probability": "高", "reason": "Last State: OOMKilled, Exit Code 137，内存限制 40Mi 不足以支撑应用内存需求"}]
}
```
   ✅ [问题定位] 完成 (44.5s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器内存超限 OOMKilled', 'probability': '高', 'reason': 'Last State: OOMKilled, Exit Code 137，内存限制 40Mi 不足以支撑应用内存需求'}]
   entities=[{"type": "Pod", "value": "memhog-578d9b5ffd-z75ll"}]
   reasoning=memhog-578d9b5ffd-z75ll Pod 处于 CrashLoopBackOff 状态，Last State 显示 Reason: OOMKilled, Exit Code: 137。容器内存限制为 40Mi，但应用代码在无限循环中分配内存，导致内存超限被 OOM Killer 终止。
   layer_analysis={"layer": "L2", "layers": ["L2"], "layer_name": "工作负载层", "confidence": 0.95, "reasoning": "memhog-578d9b5ffd-z75ll Pod 处于 CrashLoopBackOff 状态，Last State 显示 Reason: OOMKilled, Exit Code: 137。容器内存限制为 40Mi，但应用代码在无限循环中分配内存，导致内存超限被 OOM Killer 终止。", "key_entities": [{"type": "Pod", "value": "memhog-578d9b5ffd-z75ll"}], "possible_scenarios": [{"scenario": "容器内存超限 OOMKilled", "probability": "高", "reason": "Last State: OOMKilled, Exit Code 137，内存限制 40Mi 不足以支撑应用内存需求"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，这是一个 **L2（工作负载层）** 问题，具体是 **容器内存超限 OOMKilled**。让我制定证据采集计划并执行工具采集真实数据。

```json
{
  "layer": "L2",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取 Pod 完整 YAML 配置，确认内存限制和资源请求",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get pod memhog-578d9b5ffd-z75ll -n aiops-e2e -o yaml",
      "purpose": "确认 Pod 的内存限制（limits）和请求（requests），验证 OOMKilled 的根本原因"
    },
    {
      "id": "e2",
      "description": "查询 Prometheus 获取 Pod 内存使用历史数据",
      "level": "important",
      "tool": "execute_prometheus_range_query",
      "command": "container_memory_working_set_bytes{pod='memhog-578d9b5ffd-z75ll', namespace='aiops-e2e'}",
      "purpose": "查看 Pod 内存使用历史，确认是否超过 40Mi 限制"
    },
    {
      "id": "e3",
      "description": "获取 Pod 所属的 ReplicaSet 信息",
      "level": "important",
      "tool": "kubectl_describe",
      "command": "kubectl describe replicaset memhog-578d9b5ffd -n aiops-e2e",
      "purpose": "确认 Pod 的控制器配置，了解应用的整体部署情况"
    },
    {
      "id": "e4",
      "description": "查询节点内存使用情况",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "node_memory_MemAvailable_bytes{instance=~'.*node2.*'} / node_memory_MemTotal_bytes{instance=~'.*node2.*'} * 100",
      "purpose": "确认节点 node2 的内存可用性，排除节点级内存压力"
    }
  ],
  "collection_strategy": "首先确认 Pod 配置中的内存限制，然后通过 Prometheus 验证内存使用是否超限，最后检查相关控制器和节点状态"
}
```

现在开始执行证据采集：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  annotations:
    cni.projectcalico.org/containerID: a57d96bdfa43f0b3f62013a0b76442481e516cf3dd5a89bb7ee919a3bae6c524
    cni.projectcalico.org/podIP: 172.16.104.61
   💭 [证据链采集] 现在执行第二个证据采集，查询 Pod 内存使用历史：
   💭 [证据链采集] 调用工具: execute_prometheus_range_query
   💭 [证据链采集] 工具结果: execute_prometheus_range_query (success)
      📄 {"status":"success","data":{"resultType":"matrix","result":[{"metric":{"__name__":"container_memory_working_set_bytes","endpoint":"https-metrics","id":"/kubepods.slice/kubepods-burstable.slice/kubepod
   💭 [证据链采集] 现在执行第三个证据采集，获取 ReplicaSet 信息：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:           memhog-578d9b5ffd
Namespace:      aiops-e2e
Selector:       app=memhog,pod-template-hash=578d9b5ffd
Labels:         app=memhog
                e2e-test=true
                pod-templat
   ✅ [证据链采集] 完成 (43.8s)
   📤 → 下游数据: evidence_items=3/4
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "获取 Pod 完整 YAML 配置，确认内存限制和资源请求", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get pod memhog-578d9b5ffd-z75ll -n aiops-e2e -o yaml", "purpose": "确认 Pod 的内存限制（limits）和请求（requests），验证 OOMKilled 的根本原因"}, {"id": "e2", "description": "查询 Prometheus 获取 Pod 内存使用历史数据", "level": "important", "tool": "execute_prometheus_range_query", "command": "container_memory_working_set_bytes{pod='memhog-578d9b5ffd-z75ll', namespace='aiops-e2e'}", "purpose": "查看 Pod 内存使用历史，确认是否超过 40Mi 限制"}, {"id": "e3", "description": "获取 Pod 所属的 ReplicaSet 信息", "level": "important", "tool": "kubectl_describe", "command": "kubectl describe replicaset memhog-578d9b5ffd -n aiops-e2e", "purpose": "确认 Pod 的控制器配置，了解应用的整体部署情况"}, {"id": "e4", "description": "查询节点内存使用情况", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "node_memory_MemAvailable_bytes{instance=~'.*node2.*'} / node_memory_MemTotal_bytes{instance=~'.*node2.*'} * 100", "purpose": "确认节点 node2 的内存可用性，排除节点级内存压力"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    cni.projectcalico.org/containerID: a57d96bdfa43f0b3f62013a0b76442481e516cf3dd5a89bb7ee919a3bae6c524\n    cni.projectcalico.org/podIP: 172.16.104.61", "duration_s": 0}, {"tool": "execute_prometheus_range_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"matrix\",\"result\":[{\"metric\":{\"__name__\":\"container_memory_working_set_bytes\",\"endpoint\":\"https-metrics\",\"id\":\"/kubepods.slice/kubepods-burstable.slice/kubepod", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:           memhog-578d9b5ffd\nNamespace:      aiops-e2e\nSelector:       app=memhog,pod-template-hash=578d9b5ffd\nLabels:         app=memhog\n                e2e-test=true\n                pod-templat", "duration_s": 0}], "llm_analysis": "现在执行第三个证据采集，获取 ReplicaSet 信息：", "collection_summary": "计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%", "evidence_inventory": [{"id": "e1", "description": "获取 Pod 完整 YAML 配置，确认内存限制和资源请求", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "查询 Prometheus 获取 Pod 内存使用历史数据", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "获取 Pod 所属的 ReplicaSet 信息", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "查询节点内存使用情况", "level": "optional", "collected": false, "source": "planned"}], "missing_reasons": ["e4(查询节点内存使用情况): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 75%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (57.9s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "应用设计缺陷：Python 代码在无限循环中持续分配内存（每次 1MiB），且无内存释放机制", "propagation": "缺陷代码部署到容器 → 容器内存使用持续增长 → 超过内存限制（40Mi）", "direct_cause": "容器内存使用超过 40Mi 限制，触发 Linux OOM Killer 终止进程", "manifestation": "Pod 状态 CrashLoopBackOff，容器重启17次，Last State 显示 OOMKilled"}
   rca_analysis={"phenomenon": "memhog-578d9b5ffd-z75ll Pod 处于 CrashLoopBackOff 状态，已重启17次", "evidence_inventory": [{"id": "e1", "content": "Pod 列表显示 memhog-578d9b5ffd-z75ll 状态为 CrashLoopBackOff，重启17次", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e2", "content": "Pod describe 显示 Last State: Terminated, Reason: OOMKilled, Exit Code: 137", "source": "kubectl_describe", "reliability": "高"}, {"id": "e3", "content": "Pod YAML 显示内存限制为 40Mi，应用代码为无限循环分配内存", "source": "kubectl_get_yaml", "reliability": "高"}, {"id": "e4", "content": "Prometheus 数据显示容器内存使用最高达 872448 字节（约 0.83MiB）", "source": "execute_prometheus_range_query", "reliability": "中"}, {"id": "e5", "content": "ReplicaSet 信息显示 Pod 模板与 Pod 配置一致，内存限制 40Mi", "source": "kubectl_describe", "reliability": "高"}, {"id": "e6", "content": "节点状态显示所有节点 Ready，无节点层面问题", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e7", "content": "Events 显示 BackOff 警告，容器重启失败", "source": "kubectl_events", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "memhog-578d9b5ffd-z75ll 0/1 CrashLoopBackOff 17 (39s ago) 62m", "interpretation": "Pod 处于崩溃循环状态，已重启17次，表明容器持续启动后立即失败"}, {"evidence_id": "e2", "raw_data": "Last State: Terminated, Reason: OOMKilled, Exit Code: 137", "interpretation": "容器上次终止原因为 OOMKilled（内存超限），Exit Code 137 是 Linux OOM Killer 的标准退出码"}, {"evidence_id": "e3", "raw_data": "limits: memory: 40Mi, args: a.append('x'*1024*1024) while True", "interpretation": "容器内存限制为 40MiB，但应用代码在无限循环中每次分配 1MiB 内存，必然导致内存超限"}, {"evidence_id": "e4", "raw_data": "内存使用值序列：0 → 315392 → ... → 872448 字节（最高约 0.83MiB）", "interpretation": "Prometheus 数据显示容器内存使用在短时间内从 0 增长到约 0.83MiB，但数据点间隔30秒，可能未捕获到OOM瞬间的峰值"}, {"evidence_id": "e5", "raw_data": "ReplicaSet memhog-578d9b5ffd 模板内存限制 40Mi，与 Pod 一致", "interpretation": "内存限制配置来自 ReplicaSet/Deployment 模板，非 Pod 单独配置"}, {"evidence_id": "e6", "raw_data": "master Ready, node1 Ready, node2 Ready", "interpretation": "所有节点状态正常，排除节点资源不足或节点故障导致的问题"}, {"evidence_id": "e7", "raw_data": "Warning BackOff 2m40s (x279 over 62m)", "interpretation": "kubelet 因容器持续失败而进入指数退避重启机制"}], "causal_chain": {"root_cause": "应用设计缺陷：Python 代码在无限循环中持续分配内存（每次 1MiB），且无内存释放机制", "propagation": "缺陷代码部署到容器 → 容器内存使用持续增长 → 超过内存限制（40Mi）", "direct_cause": "容器内存使用超过 40Mi 限制，触发 Linux OOM Killer 终止进程", "manifestation": "Pod 状态 CrashLoopBackOff，容器重启17次，Last State 显示 OOMKilled"}, "root_cause_summary": "根本原因是应用代码设计缺陷导致内存无限增长超过容器限制。具体证据：1) Pod describe 显示 Last State: OOMKilled, Exit Code: 137（证据 e2）；2) Pod YAML 显示内存限制为 40Mi，应用代码为 `while True: a.append('x'*1024*1024)`（证据 e3）；3) ReplicaSet 模板确认此配置来自上层工作负载（证据 e5）。应用在无限循环中每次分配 1MiB 内存，必然在短时间内超过 40Mi 限制，触发 OOM Killer。", "confidence": 0.95, "primary_runbooks": [], "alternative_causes": [], "limitations": "1) Prometheus 内存监控数据最高仅显示 872448 字节（约 0.83MiB），远低于 40Mi 限制，这可能是因为监控采集间隔（30秒）未捕获到 OOM 瞬间的内存峰值；2) 未采集节点内存使用情况，但节点状态正常且其他 Pod 运行正常，可间接排除节点内存不足问题。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: 应用设计缺陷：Python 代码在无限循环中持续分配内存（每次 1MiB），且无内存释放机制
     传导机制: 缺陷代码部署到容器 → 容器内存使用持续增长 → 超过内存限制（40Mi）
     最终表现: Pod 状态 CrashLoopBackOff，容器重启17次，Last State 显示 OOMKilled


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 21.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4727 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 47.6s
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
| **问题分类** | OOMKilled |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/4 (75%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `memhog-578d9b5ffd-z75ll` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| 错误信息 | `Last State: Terminated, Reason: OOMKilled, Exit Code: 137` |

**集群状态总结**：
您的集群中有一个名为 `memhog-578d9b5ffd-z75ll` 的 Pod 处于异常状态。该 Pod 在 `aiops-e2e` 命名空间中，运行在 `node2` 节点上，其状态为 `CrashLoopBackOff`，已重启 **17 次**。集群中所有节点（master, node1, node2）均处于 `Ready` 状态，其他 Pod 运行正常。

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `memhog-578d9b5ffd-z75ll 0/1 CrashLoopBackOff 17 (39s ago)` | Pod 处于崩溃循环，已重启17次 |
| 2 | Pod 终止原因 | `kubectl describe pod` | `Last State: Terminated, Reason: OOMKilled, Exit Code: 137` | 容器因内存超限被 OOM Killer 终止 |
| 3 | Pod 资源配置 | `kubectl describe pod` | `Limits: memory: 40Mi` | 容器内存限制为 40MiB |
| 4 | 应用代码 | `kubectl describe pod` | `Args: import time; a=[]; while True: a.append("x"*1024*1024); time.sleep(0.02)` | 应用在无限循环中持续分配内存（每次1MiB） |
| 5 | 节点状态 | `kubectl get nodes` | `master Ready, node1 Ready, node2 Ready` | 所有节点状态正常 |
| 6 | 事件记录 | `kubectl events` | `Warning BackOff 2m40s (x279 over 62m)` | kubelet 因容器持续失败而进入指数退避重启 |
| 7 | 内存监控数据 | `execute_prometheus_range_query` | `内存使用值序列：0 → 315392 → ... → 872448 字节（最高约 0.83MiB）` | 监控显示内存增长，但数据点间隔可能未捕获OOM瞬间峰值 |

### 证据关联分析
- **证据 #2 + #3 + #4 印证**：`Exit Code 137 (OOMKilled)` + `memory limit 40Mi` + `while True: a.append("x"*1024*1024)` → 应用内存需求无限增长，必然超过40Mi限制。
- **证据链**：应用代码缺陷（无限分配内存）→ 容器内存使用持续增长 → 超过40Mi限制 → 触发 cgroup OOM Killer → 容器被终止（Exit Code 137）→ Pod 重启 → 进入 `CrashLoopBackOff` 循环。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| e4: 查询节点内存使用情况 | optional | 无法完全排除节点级内存压力的可能性，但节点状态正常，影响较小。 |

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用设计缺陷：Python代码在无限循环中持续分配内存（每次1MiB），    │
│ 且无内存释放机制。                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 缺陷代码部署到容器 → 容器内存使用持续增长 → 超过内存限制（40Mi）  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器内存使用超过 40Mi 限制，触发 Linux OOM Killer 终止进程       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，容器重启17次，Last State 显示 OOMKilled│
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #2 (`Last State: OOMKilled, Exit Code: 137`)、证据 #3 (`memory limit: 40Mi`) 和证据 #4 (`while True: a.append("x"*1024*1024)`)，问题的根本原因是**应用代码设计缺陷导致内存无限增长，超过了容器设置的 40MiB 内存限制**，从而触发 OOM Killer 并导致 Pod 持续重启。
**置信度**：高 (95%)
- ✅ `Exit Code 137` 和 `Reason: OOMKilled` 明确指向内存超限。
- ✅ 应用代码逻辑 (`while True` 循环分配内存) 与 OOM 现象完全吻合。
- ⚠️ Prometheus 监控数据显示的内存峰值（~0.83MiB）远低于限制，这可能是因为监控采集间隔（30秒）未捕获到 OOM 瞬间的峰值。

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修改应用代码或调整内存限制**
此问题源于测试应用 (`memhog`) 的故意内存消耗行为。请根据实际意图选择：
- **如果是测试应用，且希望其停止消耗内存**：删除或修改此 Deployment。
    ```bash
    kubectl delete deployment memhog -n aiops-e2e
    ```
- **如果希望应用能正常运行**：大幅增加内存限制（例如增加到 1Gi），但这只是临时规避，代码缺陷仍在。
    ```bash
    kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=1Gi
    ```

**2. [可选] 查看崩溃前日志**
虽然 OOM 原因明确，但查看日志可确认应用启动过程。
```bash
kubectl logs memhog-578d9b5ffd-z75ll -n aiops-e2e --previous
```

### 后续优化
1.  **资源评估**：为生产应用设置合理的 `requests` 和 `limits`。可以使用 `kubectl describe pod <pod-name>` 观察历史资源使用情况作为参考。
2.  **应用健康检查**：为关键应用配置 `livenessProbe` 和 `readinessProbe`，以便在应用异常时更快地被发现和重启。
3.  **监控告警**：配置针对 `OOMKilled` 和 `CrashLoopBackOff` 的告警规则，以便及时发现问题。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod -n aiops-e2e -l app=memhog` | 如果删除，则无相关Pod；如果调整限制，Pod应恢复 `Running` |
| 2. 检查重启次数 | `kubectl get pod <pod-name> -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 数字不再增加 |
| 3. 确认无 OOM 事件 | `kubectl describe pod <pod-name> -n aiops-e2e \| grep -A5 -B5 "Last State"` | `Last State` 中无 `OOMKilled` |

## ⚠️ 注意事项
- `memhog` Pod 的标签包含 `e2e-test=true`，这很可能是一个用于测试的临时工作负载，处理前请确认其业务重要性。
- 如果这是生产应用，必须修复其内存泄漏的代码缺陷，仅增加内存限制是治标不治本。

---

## 📊 性能统计

├─ 总耗时: 3.8m
├─ 问题定位: 44.5s (20%) ✅
├─ 证据链采集: 43.8s (19%) ✅
├─ 根因分析: 57.9s (25%) ✅
├─ 汇总总结: 81.4s (36%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **参考 Runbook**: 无
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
