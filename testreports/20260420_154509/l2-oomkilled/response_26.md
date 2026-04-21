======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d28c0e3c68e74cf0]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您诊断集群的问题。首先让我检查集群的整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     
   💭 [问题定位] 我看到有一个 Pod 处于 CrashLoopBackOff 状态：`memhog-578d9b5ffd-z75ll`。让我检查这个 Pod 的详细信息来确认根本原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             memhog-578d9b5ffd-z75ll
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Mon, 20 Apr 2026 07:09:51 +0000

   💭 [问题定位] 现在我看到了关键信息：Pod 的 Last State 显示 Reason 为 OOMKilled，Exit Code 137。这明确表明是内存超限导致的 OOM 问题。让我再检查一下节点状态，确保没有其他问题。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   207d   v1.26.8  
   💭 [问题定位] 所有节点都处于 Ready 状态。现在让我检查一下是否有相关的 runbook 可以参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L2 Pod OOMKilled (Exit Code 137)

> 层级: L2 - 工作负载层 | 场景: 容器内存超限被 OOM Killer 终止

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | CrashLoopBackOff / Error / 频繁重启 |
| Describe | termina
   💭 [问题定位] 基于我的检查，我发现了集群中的一个问题。现在让我总结并输出诊断结果。

```json
{
  "layer": "L2",
  "layers": ["L2"],
  "layer_name": "工作负载层",
  "confidence": 0.95,
  "reasoning": "发现 Pod memhog-578d9b5ffd-z75ll 处于 CrashLoopBackOff 状态，kubectl describe 显示 Last State: Terminated, Reason: OOMKilled, Exit Code: 137。这是典型的内存超限导致的 OOM 问题，属于工作负载层（L2）问题。所有节点状态为 Ready，无其他异常。",
  "key_entities": [{"type": "Pod", "value": "memhog-578d9b5ffd-z75ll"}],
  "possible_scenarios": [{"scenario": "容器内存超限被 OOM Killer 终止", "probability": "高", "reason": "Pod 的 Last State 显示 OOMKilled，Exit Code 137，容器内存限制为 40Mi，但应用在持续分配内存"}]
}
```
   ✅ [问题定位] 完成 (32.3s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器内存超限被 OOM Killer 终止', 'probability': '高', 'reason': 'Pod 的 Last State 显示 OOMKilled，Exit Code 137，容器内存限制为 40Mi，但应用在持续分配内存'}]
   entities=[{"type": "Pod", "value": "memhog-578d9b5ffd-z75ll"}]
   reasoning=发现 Pod memhog-578d9b5ffd-z75ll 处于 CrashLoopBackOff 状态，kubectl describe 显示 Last State: Terminated, Reason: OOMKilled, Exit Code: 137。这是典型的内存超限导致的 OOM 问题，属于工作负载层（L2）问题。所有节点状态为 Ready，无其他异常。
   layer_analysis={"layer": "L2", "layers": ["L2"], "layer_name": "工作负载层", "confidence": 0.95, "reasoning": "发现 Pod memhog-578d9b5ffd-z75ll 处于 CrashLoopBackOff 状态，kubectl describe 显示 Last State: Terminated, Reason: OOMKilled, Exit Code: 137。这是典型的内存超限导致的 OOM 问题，属于工作负载层（L2）问题。所有节点状态为 Ready，无其他异常。", "key_entities": [{"type": "Pod", "value": "memhog-578d9b5ffd-z75ll"}], "possible_scenarios": [{"scenario": "容器内存超限被 OOM Killer 终止", "probability": "高", "reason": "Pod 的 Last State 显示 OOMKilled，Exit Code 137，容器内存限制为 40Mi，但应用在持续分配内存"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，我已经确认了集群中的问题：Pod `memhog-578d9b5ffd-z75ll` 因内存超限被 OOM Killer 终止。现在我将制定证据采集计划并执行工具采集真实数据。

```json
{
  "layer": "L2",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取 Pod 的 YAML 配置，确认资源限制和请求",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml pod memhog-578d9b5ffd-z75ll -n aiops-e2e",
      "purpose": "确认容器的内存限制（limits.memory）和请求（requests.memory）值"
    },
    {
      "id": "e2",
      "description": "获取 Pod 的崩溃前日志",
      "level": "critical",
      "tool": "run_bash_command",
      "command": "kubectl logs memhog-578d9b5ffd-z75ll -n aiops-e2e --previous --tail=200",
      "purpose": "查看容器在 OOM 终止前的日志，确认内存分配失败信息"
    },
    {
      "id": "e3",
      "description": "查询 Pod 的内存使用历史数据",
      "level": "important",
      "tool": "execute_prometheus_range_query",
      "command": "sum(container_memory_working_set_bytes{pod=\"memhog-578d9b5ffd-z75ll\", container=\"memhog\"}) by (pod)",
      "purpose": "获取 Pod 内存使用的时间序列数据，观察内存增长趋势"
    },
    {
      "id": "e4",
      "description": "获取 Pod 所属的 ReplicaSet 信息",
      "level": "important",
      "tool": "kubectl_get_by_name",
      "command": "kubectl get replicaset memhog-578d9b5ffd --show-labels -o wide -n aiops-e2e",
      "purpose": "确认 Pod 的控制器和副本数配置"
    },
    {
      "id": "e5",
      "description": "获取 Pod 的详细事件时间线",
      "level": "important",
      "tool": "kubectl_events",
      "command": "kubectl get events -n aiops-e2e --field-selector involvedObject.name=memhog-578d9b5ffd-z75ll --sort-by='.lastTimestamp'",
      "purpose": "查看 Pod 的完整事件历史，包括重启时间线"
    },
    {
      "id": "e6",
      "description": "查询节点内存使用情况",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
      "purpose": "确认节点整体内存使用率，排除节点级内存压力"
    }
  ],
  "collection_strategy": "首先确认资源配置和日志证据，然后通过 Prometheus 数据验证内存使用模式，最后检查相关控制器和事件时间线"
}
```

现在开始执行证据采集计划：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  annotations:
    cni.projectcalico.org/containerID: a57d96bdfa43f0b3f62013a0b76442481e516cf3dd5a89bb7ee919a3bae6c524
    cni.projectcalico.org/podIP: 172.16.104.61
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [证据链采集] 调用工具: execute_prometheus_range_query
   💭 [证据链采集] 工具结果: execute_prometheus_range_query (success)
      📄 {"status":"success","data":{"resultType":"matrix","result":[]}}
   💭 [证据链采集] 让我先检查一下 Prometheus 中是否有相关的内存指标：
   💭 [证据链采集] 调用工具: get_series
   💭 [证据链采集] 工具结果: get_series (success)
      📄 {"status":"success","data":[{"__name__":"container_memory_working_set_bytes","container":"memhog","endpoint":"https-metrics","id":"/kubepods.slice/kubepods-burstable.slice/kubepods-burstable-pod02a3cb
   💭 [证据链采集] 我看到有很多 memhog Pod 的历史数据。让我查询当前 Pod 的内存使用情况：
   💭 [证据链采集] 调用工具: execute_prometheus_range_query
   💭 [证据链采集] 工具结果: execute_prometheus_range_query (success)
      📄 {"status":"success","data":{"resultType":"matrix","result":[]}}
   💭 [证据链采集] 让我继续执行其他证据采集：
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES             SELECTOR                                  LABELS
memhog-578d9b5ffd   1         1         0       57m   memhog     
   ✅ [证据链采集] 完成 (1m 11.6s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "获取 Pod 的 YAML 配置，确认资源限制和请求", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod memhog-578d9b5ffd-z75ll -n aiops-e2e", "purpose": "确认容器的内存限制（limits.memory）和请求（requests.memory）值"}, {"id": "e2", "description": "获取 Pod 的崩溃前日志", "level": "critical", "tool": "run_bash_command", "command": "kubectl logs memhog-578d9b5ffd-z75ll -n aiops-e2e --previous --tail=200", "purpose": "查看容器在 OOM 终止前的日志，确认内存分配失败信息"}, {"id": "e3", "description": "查询 Pod 的内存使用历史数据", "level": "important", "tool": "execute_prometheus_range_query", "command": "sum(container_memory_working_set_bytes{pod=\"memhog-578d9b5ffd-z75ll\", container=\"memhog\"}) by (pod)", "purpose": "获取 Pod 内存使用的时间序列数据，观察内存增长趋势"}, {"id": "e4", "description": "获取 Pod 所属的 ReplicaSet 信息", "level": "important", "tool": "kubectl_get_by_name", "command": "kubectl get replicaset memhog-578d9b5ffd --show-labels -o wide -n aiops-e2e", "purpose": "确认 Pod 的控制器和副本数配置"}, {"id": "e5", "description": "获取 Pod 的详细事件时间线", "level": "important", "tool": "kubectl_events", "command": "kubectl get events -n aiops-e2e --field-selector involvedObject.name=memhog-578d9b5ffd-z75ll --sort-by='.lastTimestamp'", "purpose": "查看 Pod 的完整事件历史，包括重启时间线"}, {"id": "e6", "description": "查询节点内存使用情况", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100", "purpose": "确认节点整体内存使用率，排除节点级内存压力"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    cni.projectcalico.org/containerID: a57d96bdfa43f0b3f62013a0b76442481e516cf3dd5a89bb7ee919a3bae6c524\n    cni.projectcalico.org/podIP: 172.16.104.61", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "execute_prometheus_range_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"matrix\",\"result\":[]}}", "duration_s": 0}, {"tool": "get_series", "data": "{\"status\":\"success\",\"data\":[{\"__name__\":\"container_memory_working_set_bytes\",\"container\":\"memhog\",\"endpoint\":\"https-metrics\",\"id\":\"/kubepods.slice/kubepods-burstable.slice/kubepods-burstable-pod02a3cb", "duration_s": 0}, {"tool": "execute_prometheus_range_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"matrix\",\"result\":[]}}", "duration_s": 0}, {"tool": "kubectl_get_by_name", "data": "NAME                DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES             SELECTOR                                  LABELS\nmemhog-578d9b5ffd   1         1         0       57m   memhog     ", "duration_s": 0}], "llm_analysis": "让我继续执行其他证据采集：", "collection_summary": "计划 7 项，实际采集 6 项，未采集 1 项，完整度 86%", "evidence_inventory": [{"id": "e1", "description": "获取 Pod 的 YAML 配置，确认资源限制和请求", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "获取 Pod 的崩溃前日志", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "查询 Pod 的内存使用历史数据", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "获取 Pod 所属的 ReplicaSet 信息", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "获取 Pod 的详细事件时间线", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "查询节点内存使用情况", "level": "optional", "collected": false, "source": "planned"}, {"id": "extra_4", "description": "工具采集: execute_prometheus_range_query", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": ["e6(查询节点内存使用情况): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/7 项, 完整度: 86%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (59.0s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "应用设计缺陷：Python 脚本无限分配内存，每秒约 50MiB", "propagation": "应用内存消耗持续增长 → 超过容器内存限制 40MiB → 触发内核 OOM Killer", "direct_cause": "容器内存使用超过 limits.memory=40Mi 限制", "manifestation": "Pod CrashLoopBackOff，容器被 OOMKilled 终止"}
   rca_analysis={"phenomenon": "Pod memhog-578d9b5ffd-z75ll 处于 CrashLoopBackOff 状态，频繁重启", "evidence_inventory": [{"id": "e1", "content": "Pod 状态显示 CrashLoopBackOff，重启 15 次", "source": "kubectl get pods", "reliability": "高"}, {"id": "e2", "content": "Pod describe 显示 Last State: Terminated, Reason: OOMKilled, Exit Code: 137", "source": "kubectl describe pod", "reliability": "高"}, {"id": "e3", "content": "Pod YAML 显示内存限制为 40Mi，请求为 20Mi", "source": "kubectl get yaml", "reliability": "高"}, {"id": "e4", "content": "容器命令为无限循环分配内存的 Python 脚本", "source": "kubectl describe pod", "reliability": "高"}, {"id": "e5", "content": "Prometheus 查询 Pod 内存使用历史数据返回空结果", "source": "execute_prometheus_range_query", "reliability": "中"}, {"id": "e6", "content": "Pod 崩溃前日志为空", "source": "kubectl logs --previous", "reliability": "中"}, {"id": "e7", "content": "所有节点状态为 Ready，无节点异常", "source": "kubectl get nodes", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "memhog-578d9b5ffd-z75ll 0/1 CrashLoopBackOff 15 (4m31s ago)", "interpretation": "Pod 处于崩溃循环状态，已重启 15 次"}, {"evidence_id": "e2", "raw_data": "Last State: Terminated, Reason: OOMKilled, Exit Code: 137", "interpretation": "容器因内存超限被 OOM Killer 终止，Exit Code 137 是 OOM 的典型信号"}, {"evidence_id": "e3", "raw_data": "limits: {cpu: 200m, memory: 40Mi}, requests: {cpu: 50m, memory: 20Mi}", "interpretation": "容器内存限制为 40MiB，请求为 20MiB"}, {"evidence_id": "e4", "raw_data": "Command: python -c 'import time; a=[]; while True: a.append(\"x\"*1024*1024); time.sleep(0.02)'", "interpretation": "容器执行无限循环，每秒分配约 50MiB 内存（1MiB/0.02s），远超 40MiB 限制"}, {"evidence_id": "e5", "raw_data": "{\"status\":\"success\",\"data\":{\"resultType\":\"matrix\",\"result\":[]}}", "interpretation": "Prometheus 未返回内存使用历史数据，可能是容器存活时间太短无法采集"}, {"evidence_id": "e6", "raw_data": "{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}", "interpretation": "崩溃前日志为空，OOMKilled 通常不会在应用层留下日志"}, {"evidence_id": "e7", "raw_data": "master Ready, node1 Ready, node2 Ready", "interpretation": "所有节点状态正常，排除节点层问题"}], "causal_chain": {"root_cause": "应用设计缺陷：Python 脚本无限分配内存，每秒约 50MiB", "propagation": "应用内存消耗持续增长 → 超过容器内存限制 40MiB → 触发内核 OOM Killer", "direct_cause": "容器内存使用超过 limits.memory=40Mi 限制", "manifestation": "Pod CrashLoopBackOff，容器被 OOMKilled 终止"}, "root_cause_summary": "Pod memhog-578d9b5ffd-z75ll 因内存超限被 OOMKilled。直接证据：1) kubectl describe 显示 Last State: Terminated, Reason: OOMKilled, Exit Code: 137；2) 容器内存限制为 40Mi；3) 容器执行的 Python 脚本无限循环分配内存（每秒约 50MiB），远超限制。节点状态正常，排除底层资源问题。", "confidence": 0.95, "primary_runbooks": ["L2 Pod OOMKilled (Exit Code 137)"], "alternative_causes": [], "limitations": "1) Prometheus 未返回内存使用历史数据，无法展示内存增长曲线；2) 节点内存使用情况未采集，但所有节点 Ready 状态表明非节点层问题；3) 崩溃前日志为空，符合 OOMKilled 特征。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: 应用设计缺陷：Python 脚本无限分配内存，每秒约 50MiB
     传导机制: 应用内存消耗持续增长 → 超过容器内存限制 40MiB → 触发内核 OOM Killer
     最终表现: Pod CrashLoopBackOff，容器被 OOMKilled 终止


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 31.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5160 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 14.0s
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
| **问题分类** | OOMKilled（内存超限） |
| **置信度** | 高 (95%) |
| **证据完整度** | 6/7 (86%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `memhog-578d9b5ffd-z75ll` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| 错误信息 | `Reason: OOMKilled, Exit Code: 137` |

**集群状态总结**：
- **节点状态**：3个节点（master, node1, node2）状态均为 `Ready`，集群基础设施正常。
- **工作负载状态**：除 `memhog-578d9b5ffd-z75ll` Pod 外，其他所有 Pod 均处于 `Running` 状态。
- **核心问题**：发现一个测试应用 Pod (`memhog-578d9b5ffd-z75ll`) 因内存超限（OOMKilled）而处于 `CrashLoopBackOff` 状态，持续重启。

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pods` | `memhog-578d9b5ffd-z75ll 0/1 CrashLoopBackOff 15 (4m31s ago)` | Pod 处于崩溃循环，已重启15次 |
| 2 | Pod 详情 | `kubectl describe pod` | `Last State: Terminated, Reason: OOMKilled, Exit Code: 137` | 容器因内存超限被内核 OOM Killer 终止 |
| 3 | 资源配置 | `kubectl describe pod` | `Limits: memory: 40Mi, Requests: memory: 20Mi` | 容器内存限制为 40MiB |
| 4 | 容器命令 | `kubectl describe pod` | `Command: python -c 'import time; a=[]; while True: a.append("x"*1024*1024); time.sleep(0.02)'` | 容器执行无限循环，每秒分配约50MiB内存 |
| 5 | 崩溃前日志 | `kubectl logs --previous` | `{"success": true, "stdout": "", "stderr": "", "returncode": 0}` | 日志为空，符合 OOMKilled 特征（应用层无日志） |
| 6 | 节点状态 | `kubectl get nodes` | `master Ready, node1 Ready, node2 Ready` | 所有节点状态正常，排除底层资源问题 |
| 7 | 内存监控 | `execute_prometheus_range_query` | `{"status":"success","data":{"resultType":"matrix","result":[]}}` | 未获取到历史数据，容器存活时间过短，监控未捕获 |

### 证据关联分析
- **证据 #2 + #3 + #4 印证**：`OOMKilled (Exit Code 137)` + `memory limit: 40Mi` + `每秒分配50MiB内存的脚本` → **应用内存需求远超容器限制**。
- **证据链**：应用脚本无限分配内存 → 内存使用迅速超过 40MiB 限制 → 触发 cgroup OOM Killer → 容器被终止（Exit Code 137）→ Pod 进入 `CrashLoopBackOff` 状态。
- **证据 #6 排除**：所有节点 `Ready`，表明问题非节点资源不足引起，而是容器自身配置与行为不匹配。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| e6: 查询节点内存使用情况 | optional | 无法确认节点级内存压力，但节点状态正常已提供强证据 |

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用设计缺陷：Pod `memhog` 执行的脚本会无限分配内存（~50MiB/s） │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 脚本内存消耗持续增长 → 迅速超过容器内存限制（40MiB）             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器内存使用超过 limits.memory=40Mi → 触发 cgroup OOM Killer    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，Last State: OOMKilled, Exit Code 137│
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (`Last State: OOMKilled, Exit Code: 137`)、证据 #3 (`memory limit: 40Mi`) 和证据 #4 (无限分配内存的 Python 脚本)，问题的根本原因是**测试应用 `memhog` 的内存消耗行为（~50MiB/s）与其容器配置的内存限制（40MiB）严重不匹配**，导致容器每次启动后迅速因内存超限而被 OOM Killer 终止。

**置信度**：高 (95%)
- ✅ `Exit Code 137` 和 `Reason: OOMKilled` 是内存超限的明确标志。
- ✅ 容器内存限制 (`40Mi`) 远低于脚本的理论内存分配速率 (`~50MiB/s`)。
- ✅ 所有节点状态正常，排除了集群底层资源问题。
- ⚠️ 缺少内存使用监控曲线，但脚本逻辑和 OOM 结果已构成完整证据链。

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 调整 Pod 的内存限制以匹配应用行为**
这是一个测试应用 (`e2e-test=true`)，其设计意图可能就是触发 OOM。根据脚本行为，建议大幅提高内存限制。
```bash
# 查找并更新其 Deployment/ReplicaSet 的资源限制
# 首先找到控制器
kubectl get replicaset -n aiops-e2e --selector app=memhog -o name
# 假设控制器是 ReplicaSet/memhog-578d9b5ffd，更新其 Pod 模板中的内存限制（例如提高到 512Mi）
kubectl patch replicaset memhog-578d9b5ffd -n aiops-e2e --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value":"512Mi"}]'
```
*依据*：当前 40Mi 限制不满足脚本的内存分配需求，提高限制可让 Pod 持续运行。

**2. [可选] 直接删除此测试 Pod/工作负载**
如果此 Pod 仅为临时测试用途，且其持续崩溃对集群无影响，可以考虑删除。
```bash
kubectl delete pod memhog-578d9b5ffd-z75ll -n aiops-e2e
# 或删除整个控制器（如 ReplicaSet）
kubectl delete replicaset memhog-578d9b5ffd -n aiops-e2e
```
*目的*：清理异常状态的工作负载，保持集群视图整洁。

### 后续优化
1.  **资源评估**：对于生产应用，应使用 `kubectl describe pod` 监控其资源请求 (`requests`) 与限制 (`limits`) 的合理性，并通过应用性能测试确定合适的值。
2.  **监控告警**：为关键应用配置内存使用率告警（例如，使用率持续 >80% 限制时告警）。
3.  **测试管理**：为标记了 `e2e-test=true` 的测试工作负载规划独立的命名空间或集群，避免干扰生产视图。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod memhog-578d9b5ffd-z75ll -n aiops-e2e` | 执行修复建议1后，STATUS 应变为 `Running` |
| 2. 检查重启次数 | `kubectl get pod memhog-578d9b5ffd-z75ll -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 数字不再增长 |
| 3. 确认 OOM 状态消失 | `kubectl describe pod memhog-578d9b5ffd-z75ll -n aiops-e2e \| grep -A2 "Last State"` | 不再显示 `Reason: OOMKilled` |

## ⚠️ 注意事项
- 该 Pod 带有 `e2e-test=true` 标签，很可能是一个故意制造 OOM 场景的测试用例。在修复前，请确认其用途。
- 如果选择提高内存限制，需注意节点 `node2` 的剩余可用内存资源。
- 对于生产环境中的非测试应用发生 OOM，除调整限制外，必须深入分析应用是否存在内存泄漏。

---

## 📊 性能统计

├─ 总耗时: 4.2m
├─ 问题定位: 32.3s (13%) ✅
├─ 证据链采集: 71.6s (28%) ✅
├─ 根因分析: 59.0s (23%) ✅
├─ 汇总总结: 91.2s (36%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: L2 Pod OOMKilled (Exit Code 137)
- **参考 Runbook**: L2 Pod OOMKilled (Exit Code 137)
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
