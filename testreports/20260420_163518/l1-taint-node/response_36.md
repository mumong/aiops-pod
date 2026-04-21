======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: e35402b310d5470b]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来检查一下集群的整体状态，看看有什么问题。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     l1-test-ng
   💭 [问题定位] 我看到了一个异常 Pod：`l1-test-nginx-6c69dc7c76-67g52` 处于 Pending 状态。让我检查一下这个 Pod 的详细信息，看看为什么它无法调度。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-67g52
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [问题定位] 现在让我检查一下节点的状态，看看是否有节点被标记了 taint：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   207d   v1.26.8  
   💭 [问题定位] 让我检查一下 node2 的详细信息，因为 Pod 的 node selector 指定了 `kubernetes.io/hostname=node2`：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 现在我看到了问题！node2 节点有一个 taint：`test-unschedulable=true:NoSchedule`。这导致 Pod 无法调度到该节点上。让我检查一下是否有相关的 runbook 可以参考：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L1 Node NotReady / Taint 导致不可调度

> 层级: L1 - 集群与节点层 | 场景: 节点 NotReady 或被 Taint 标记为不可调度

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| 节点状态 | `kubectl get nodes` 显示 STATUS=NotReady 或 Unknown 
   ✅ [问题定位] 完成 (41.9s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '节点 Taint 导致不可调度', 'probability': '高', 'reason': '节点 node2 被标记了 NoSchedule taint，Pod 因节点选择器匹配 node2 但无法容忍该 taint 而无法调度。'}]
   entities=[{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-67g52"}]
   reasoning=用户明确在诊断问题，发现 node2 节点存在 taint `test-unschedulable=true:NoSchedule`，导致 Pod `l1-test-nginx-6c69dc7c76-67g52` 处于 Pending 状态，事件显示 '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}'。节点状态为 Ready，但 taint 阻止了调度。
   layer_analysis={"layer": "L1", "layers": ["L1"], "layer_name": "集群与节点层", "confidence": 0.95, "reasoning": "用户明确在诊断问题，发现 node2 节点存在 taint `test-unschedulable=true:NoSchedule`，导致 Pod `l1-test-nginx-6c69dc7c76-67g52` 处于 Pending 状态，事件显示 '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}'。节点状态为 Ready，但 taint 阻止了调度。", "key_entities": [{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-67g52"}], "possible_scenarios": [{"scenario": "节点 Taint 导致不可调度", "probability": "高", "reason": "节点 node2 被标记了 NoSchedule taint，Pod 因节点选择器匹配 node2 但无法容忍该 taint 而无法调度。"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，我已经识别到问题：**node2 节点有一个 `test-unschedulable=true:NoSchedule` taint，导致 Pod 无法调度到该节点上**。现在我将制定证据采集计划并执行工具采集真实数据。

```json
{
  "layer": "L1",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "确认 node2 节点的 taint 详情",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get node node2 -o yaml",
      "purpose": "获取完整的节点配置，确认 taint 的完整信息"
    },
    {
      "id": "e2",
      "description": "检查受影响的 Pod 详情",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e -o yaml",
      "purpose": "确认 Pod 的 nodeSelector 和 tolerations 配置"
    },
    {
      "id": "e3",
      "description": "检查所有 Pending 状态的 Pod",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.reason' --field-selector status.phase=Pending",
      "purpose": "确认有多少 Pod 因 taint 而无法调度"
    },
    {
      "id": "e4",
      "description": "检查节点资源使用情况",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "node_memory_MemAvailable_bytes{instance=~'.*node2.*'} / node_memory_MemTotal_bytes{instance=~'.*node2.*'} * 100",
      "purpose": "确认 node2 节点内存使用率是否正常"
    },
    {
      "id": "e5",
      "description": "检查节点事件历史",
      "level": "optional",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get events -A -o custom-columns='LAST SEEN:.lastTimestamp,TYPE:.type,REASON:.reason,OBJECT:.involvedObject.kind/.involvedObject.name,MESSAGE:.message' --field-selector involvedObject.kind=Node,involvedObject.name=node2",
      "purpose": "查看节点相关事件，了解 taint 何时添加"
    }
  ],
  "collection_strategy": "首先确认 taint 的完整配置，然后检查受影响的 Pod 详情，最后查看是否有其他 Pod 受到影响。同时检查节点资源状况以排除资源压力导致的 taint。"
}
```

现在开始逐项执行工具采集证据：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Node
metadata:
  annotations:
    kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock
    node.alpha.kubernetes.io/ttl: "0"
    projectcalico.org/IP
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: "2026-04-20T08:34:50Z"
  generateName: l1-test-nginx-6c69dc7c76-
  labels:
    app: nginx
    e2e-test: "true"
    pod-template-hash: 6c69dc7c76
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.reason' | (head 
   ✅ [证据链采集] 完成 (46.3s)
   📤 → 下游数据: evidence_items=3/5
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "确认 node2 节点的 taint 详情", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get node node2 -o yaml", "purpose": "获取完整的节点配置，确认 taint 的完整信息"}, {"id": "e2", "description": "检查受影响的 Pod 详情", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e -o yaml", "purpose": "确认 Pod 的 nodeSelector 和 tolerations 配置"}, {"id": "e3", "description": "检查所有 Pending 状态的 Pod", "level": "important", "tool": "kubernetes_tabular_query", "command": "kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.reason' --field-selector status.phase=Pending", "purpose": "确认有多少 Pod 因 taint 而无法调度"}, {"id": "e4", "description": "检查节点资源使用情况", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "node_memory_MemAvailable_bytes{instance=~'.*node2.*'} / node_memory_MemTotal_bytes{instance=~'.*node2.*'} * 100", "purpose": "确认 node2 节点内存使用率是否正常"}, {"id": "e5", "description": "检查节点事件历史", "level": "optional", "tool": "kubernetes_tabular_query", "command": "kubectl get events -A -o custom-columns='LAST SEEN:.lastTimestamp,TYPE:.type,REASON:.reason,OBJECT:.involvedObject.kind/.involvedObject.name,MESSAGE:.message' --field-selector involvedObject.kind=Node,involvedObject.name=node2", "purpose": "查看节点相关事件，了解 taint 何时添加"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Node\nmetadata:\n  annotations:\n    kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n    node.alpha.kubernetes.io/ttl: \"0\"\n    projectcalico.org/IP", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  creationTimestamp: \"2026-04-20T08:34:50Z\"\n  generateName: l1-test-nginx-6c69dc7c76-\n  labels:\n    app: nginx\n    e2e-test: \"true\"\n    pod-template-hash: 6c69dc7c76", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "Command failed (exit 1):\nkubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.reason' | (head ", "duration_s": 0}], "llm_analysis": "根据上游定位结果，我已经识别到问题：**node2 节点有一个 `test-unschedulable=true:NoSchedule` taint，导致 Pod 无法调度到该节点上**。现在我将制定证据采集计划并执行工具采集真实数据。\n\n```json\n{\n  \"layer\": \"L1\",\n  \"evidence_plan\": [\n    {\n      \"id\": \"e1\",\n      \"description\": \"确认 node2 节点的 taint 详情\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_get_yaml\",\n      \"command\": \"kubectl get node node2 -o yaml\",\n      \"purpose\": \"获取完整的节点配置，确认 taint 的完整信息\"\n    },\n    {\n      \"id\": \"e2\",\n      \"description\": \"检查受影响的 Pod 详情\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_get_yaml\",\n      \"command\": \"kubectl get pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e -o yaml\",\n      \"purpose\": \"确认 Pod 的 nodeSelector 和 tolerations 配置\"\n    },\n    {\n      \"id\": \"e3\",\n      \"description\": \"检查所有 Pending 状态的 Pod\",\n      \"level\": \"important\",\n      \"tool\": \"kubernetes_tabular_query\",\n      \"command\": \"kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.reason' --field-selector status.phase=Pending\",\n      \"purpose\": \"确认有多少 Pod 因 taint 而无法调度\"\n    },\n    {\n      \"id\": \"e4\",\n      \"description\": \"检查节点资源使用情况\",\n      \"level\": \"optional\",\n      \"tool\": \"execute_prometheus_instant_query\",\n      \"command\": \"node_memory_MemAvailable_bytes{instance=~'.*node2.*'} / node_memory_MemTotal_bytes{instance=~'.*node2.*'} * 100\",\n      \"purpose\": \"确认 node2 节点内存使用率是否正常\"\n    },\n    {\n      \"id\": \"e5\",\n      \"description\": \"检查节点事件历史\",\n      \"level\": \"optional\",\n      \"tool\": \"kubernetes_tabular_query\",\n      \"command\": \"kubectl get events -A -o custom-columns='LAST SEEN:.lastTimestamp,TYPE:.type,REASON:.reason,OBJECT:.involvedObject.kind/.involvedObject.name,MESSAGE:.message' --field-selector involvedObject.kind=Node,involvedObject.name=node2\",\n      \"purpose\": \"查看节点相关事件，了解 taint 何时添加\"\n    }\n  ],\n  \"collection_strategy\": \"首先确认 taint 的完整配置，然后检查受影响的 Pod 详情，最后查看是否有其他 Pod 受到影响。同时检查节点资源状况以排除资源压力导致的 taint。\"\n}\n```\n\n现在开始逐项执行工具采集证据：", "collection_summary": "计划 5 项，实际采集 3 项，未采集 2 项，完整度 60%", "evidence_inventory": [{"id": "e1", "description": "确认 node2 节点的 taint 详情", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "检查受影响的 Pod 详情", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "检查所有 Pending 状态的 Pod", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查节点资源使用情况", "level": "optional", "collected": false, "source": "planned"}, {"id": "e5", "description": "检查节点事件历史", "level": "optional", "collected": false, "source": "planned"}], "missing_reasons": ["e4(检查节点资源使用情况): 已规划但工具执行失败或无匹配结果", "e5(检查节点事件历史): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/5 项, 完整度: 60%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (50.7s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "node2 节点被添加了 test-unschedulable=true:NoSchedule taint", "propagation": "taint 阻止新 Pod 调度到该节点 → Pod 的 nodeSelector 强制要求调度到 node2 → Pod 没有对应的 toleration", "direct_cause": "Pod 无法容忍节点的 taint，调度器找不到符合条件的节点", "manifestation": "Pod l1-test-nginx-6c69dc7c76-67g52 处于 Pending 状态，调度失败事件显示 taint 冲突"}
   rca_analysis={"phenomenon": "Pod l1-test-nginx-6c69dc7c76-67g52 处于 Pending 状态，无法调度到指定节点", "evidence_inventory": [{"id": "e1", "content": "node2 节点存在 taint: test-unschedulable=true:NoSchedule", "source": "kubectl_get_by_kind_in_cluster, kubectl_describe, 证据采集结果1", "reliability": "高"}, {"id": "e2", "content": "Pod l1-test-nginx-6c69dc7c76-67g52 的 nodeSelector 为 kubernetes.io/hostname=node2，且没有对应的 toleration", "source": "kubectl_describe, 证据采集结果2", "reliability": "高"}, {"id": "e3", "content": "Pod 调度失败事件显示 '1 node(s) had untolerated taint {test-unschedulable: true}'", "source": "kubectl_describe", "reliability": "高"}, {"id": "e4", "content": "node2 节点状态 Ready=True，资源使用率正常（CPU 请求 8%，内存请求 5%）", "source": "kubectl_describe", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "node2 节点 spec.taints: [{effect: NoSchedule, key: test-unschedulable, value: 'true'}]", "interpretation": "node2 被标记了 NoSchedule taint，阻止新 Pod 调度到该节点"}, {"evidence_id": "e2", "raw_data": "Pod spec.nodeSelector: {kubernetes.io/hostname: node2}, spec.tolerations: 只有 node.kubernetes.io/not-ready 和 node.kubernetes.io/unreachable", "interpretation": "Pod 强制要求调度到 node2，但没有容忍 test-unschedulable taint"}, {"evidence_id": "e3", "raw_data": "Pod 事件: '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector'", "interpretation": "调度器确认 taint 是导致调度失败的直接原因"}, {"evidence_id": "e4", "raw_data": "node2 Conditions: Ready=True (KubeletReady), MemoryPressure=False, DiskPressure=False, PIDPressure=False; Allocated resources: CPU 请求 1 core (8%), 内存请求 1828375040 bytes (5%)", "interpretation": "节点运行正常，无资源压力，taint 是人为添加而非系统自动添加"}], "causal_chain": {"root_cause": "node2 节点被添加了 test-unschedulable=true:NoSchedule taint", "propagation": "taint 阻止新 Pod 调度到该节点 → Pod 的 nodeSelector 强制要求调度到 node2 → Pod 没有对应的 toleration", "direct_cause": "Pod 无法容忍节点的 taint，调度器找不到符合条件的节点", "manifestation": "Pod l1-test-nginx-6c69dc7c76-67g52 处于 Pending 状态，调度失败事件显示 taint 冲突"}, "root_cause_summary": "根因是 node2 节点存在 test-unschedulable=true:NoSchedule taint（证据 e1）。该 taint 阻止新 Pod 调度到该节点。Pod l1-test-nginx-6c69dc7c76-67g52 通过 nodeSelector 强制要求调度到 node2（证据 e2），但没有对应的 toleration，导致调度失败。调度器事件明确显示 '1 node(s) had untolerated taint {test-unschedulable: true}'（证据 e3）。节点本身状态正常（Ready=True，资源使用率低），表明 taint 是人为添加而非系统自动添加（证据 e4）。", "confidence": 0.95, "primary_runbooks": ["L1 Node NotReady / Taint 导致不可调度"], "alternative_causes": [], "limitations": "1. 未采集到节点事件历史，无法确定 taint 何时添加及添加原因（维护、测试等）。2. 未检查是否有其他 Pod 也因相同原因处于 Pending 状态（证据 e3 采集失败）。3. 未通过 Prometheus 验证节点实时资源使用率，但 kubectl describe 显示资源充足。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: node2 节点被添加了 test-unschedulable=true:NoSchedule taint
     传导机制: taint 阻止新 Pod 调度到该节点 → Pod 的 nodeSelector 强制要求调度到 node2 → Pod 没有对应的 toleration
     最终表现: Pod l1-test-nginx-6c69dc7c76-67g52 处于 Pending 状态，调度失败事件显示 taint 冲突


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 24.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4960 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 43.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **问题层级** | L1 - 集群与节点层 |
| **问题分类** | 节点 Taint 导致 Pod 不可调度 |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/5 (60%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键发现**：
您的集群存在一个调度问题：**`node2` 工作节点被添加了一个 `NoSchedule` 污点（Taint），导致新 Pod 无法调度到该节点**。一个名为 `l1-test-nginx-6c69dc7c76-67g52` 的 Pod 因此处于 `Pending` 状态。

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `l1-test-nginx-6c69dc7c76-67g52` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| 错误信息 | `0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}` |

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | 节点 Taint | `kubectl describe node node2` | `Taints: test-unschedulable=true:NoSchedule` | node2 节点被标记为不可调度 |
| 2 | Pod 状态与事件 | `kubectl describe pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e` | `Status: Pending`<br>`Events: Warning FailedScheduling ... 1 node(s) had untolerated taint {test-unschedulable: true}` | Pod 因节点污点而调度失败 |
| 3 | Pod 节点选择器 | `kubectl describe pod ...` | `Node-Selectors: kubernetes.io/hostname=node2`<br>`Tolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s` | Pod 强制要求调度到 node2，但未容忍 `test-unschedulable` 污点 |
| 4 | 节点状态 | `kubectl describe node node2` | `Conditions: Ready=True (KubeletReady)`<br>`Allocated resources: CPU 1 (8%), memory 1828375040 (5%)` | 节点运行正常，资源充足，污点为人为添加 |

### 证据关联分析
- **证据 #1 + #2 印证**：节点存在 `NoSchedule` 污点 + Pod 调度事件显示 `untolerated taint` → 污点是调度失败的直接原因。
- **证据 #2 + #3 印证**：Pod 的 `nodeSelector` 强制指定 `node2` + 没有对应的 `toleration` → Pod 无法绕过污点限制。
- **证据 #1 + #4 印证**：节点状态 `Ready=True` 且资源使用率低 + 存在 `test-unschedulable` 污点 → 污点很可能是人为添加（例如用于测试或维护），而非系统因资源压力自动添加。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 检查所有 Pending 状态的 Pod | important | 无法确认是否还有其他 Pod 受此污点影响 |
| 节点事件历史 | optional | 无法确定污点是何时、由谁、为何添加 |
| 节点实时资源使用率 (Prometheus) | optional | 已通过 `kubectl describe` 确认资源充足，影响较小 |

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ node2 节点被添加了 test-unschedulable=true:NoSchedule 污点       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 污点阻止新 Pod 调度到 node2 → Pod 的 nodeSelector 强制要求调度到 │
│ node2 → Pod 没有对应的 toleration                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度器找不到满足 Pod nodeSelector 且能容忍污点的节点             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod l1-test-nginx-6c69dc7c76-67g52 状态为 Pending，持续调度失败  │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (`Taints: test-unschedulable=true:NoSchedule`) 和证据 #2 (`Events: ... had untolerated taint`)，问题的根本原因是 **`node2` 节点上存在一个 `NoSchedule` 污点，而需要调度到该节点的 Pod 没有对应的容忍度**，导致调度失败。
**置信度**：高 (95%)
- ✅ 节点污点明确存在（证据 #1）
- ✅ Pod 调度事件直接指出污点冲突（证据 #2）
- ✅ Pod 配置强制要求调度到 `node2`（证据 #3）
- ✅ 节点本身健康，排除资源压力等自动添加污点的可能（证据 #4）
- ⚠️ 缺少污点添加的历史事件，无法确认其意图。

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Pod 添加对应的容忍度 (Toleration)**
如果此 Pod 必须运行在 `node2` 上，修改其部署（Deployment/DaemonSet）或 Pod 模板，添加容忍度。
```bash
# 编辑 Deployment（假设名为 l1-test-nginx）
kubectl edit deployment l1-test-nginx -n aiops-e2e
```
在 `spec.template.spec` 下添加：
```yaml
tolerations:
- key: "test-unschedulable"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```
*依据*：使 Pod 能够容忍节点的污点，从而被调度。

**2. [替代方案] 移除 node2 节点的污点**
如果 `node2` 节点不应被标记为不可调度，移除该污点。
```bash
kubectl taint node node2 test-unschedulable:NoSchedule-
```
*依据*：清除调度障碍，恢复节点正常的可调度性。**执行前请确认此操作是否符合集群维护计划。**

**3. [检查] 确认修复效果**
```bash
# 等待新 Pod 生成并检查状态
kubectl get pod -n aiops-e2e -l app=nginx
# 查看 Pod 事件，确认调度成功
kubectl describe pod -n aiops-e2e <新的pod名称>
```

### 后续优化
1.  **污点管理规范**：建立节点污点的添加、记录和清理流程，避免因测试或临时维护遗留污点影响生产调度。
2.  **Pod 容忍度设计**：对于需要调度到特定节点的关键 Pod，考虑预先配置常见的维护性污点容忍度（如 `node.kubernetes.io/unschedulable`）。
3.  **监控告警**：配置对 `Pending` 状态超过一定时间的 Pod 进行告警。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 node2 污点状态 | `kubectl describe node node2 \| grep -A5 Taints` | 污点已被移除或 Pod 已添加容忍度 |
| 2. 确认目标 Pod 状态 | `kubectl get pod -n aiops-e2e -l app=nginx` | STATUS: Running，且 NODE 列为 node2 |
| 3. 查看 Pod 事件 | `kubectl describe pod -n aiops-e2e <pod-name>` | 无 `FailedScheduling` 警告事件 |

## ⚠️ 注意事项
- 在执行移除污点操作前，请确认该污点是否用于特定的维护、测试或隔离目的，盲目移除可能干扰原有计划。
- 如果选择为 Pod 添加容忍度，需评估是否所有需要调度到 `node2` 的 Pod 都应添加此容忍度。
- 此问题仅影响**新调度**的 Pod，已在 `node2` 上运行的 Pod 不受 `NoSchedule` 污点影响。

---

## 📊 性能统计

├─ 总耗时: 3.7m
├─ 问题定位: 41.9s (19%) ✅
├─ 证据链采集: 46.3s (21%) ✅
├─ 根因分析: 50.7s (23%) ✅
├─ 汇总总结: 84.9s (38%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: L1 Node NotReady / Taint 导致不可调度
- **参考 Runbook**: L1 Node NotReady / Taint 导致不可调度
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
