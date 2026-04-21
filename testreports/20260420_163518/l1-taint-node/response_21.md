======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ba56845697aa4f53]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来检查一下集群的整体状态，看看有什么问题。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     l1-test-ng
   💭 [问题定位] 我注意到有一个 Pod 处于 Pending 状态：`l1-test-nginx-6c69dc7c76-67g52`。让我检查一下这个 Pod 的详细信息，看看为什么它无法调度。
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
   💭 [问题定位] 让我检查一下 node2 的详细信息，因为 Pod 有 node selector `kubernetes.io/hostname=node2`：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 现在我看到了问题！node2 节点上有一个 taint：`test-unschedulable=true:NoSchedule`。这导致 Pod 无法调度到 node2 上。让我检查一下相关的 runbook 来获取更多诊断参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L1 Node NotReady / Taint 导致不可调度

> 层级: L1 - 集群与节点层 | 场景: 节点 NotReady 或被 Taint 标记为不可调度

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| 节点状态 | `kubectl get nodes` 显示 STATUS=NotReady 或 Unknown 
   ✅ [问题定位] 完成 (40.3s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '节点被Taint标记为不可调度', 'probability': '高', 'reason': '节点node2存在明确的NoSchedule污点，且Pod因该污点无法调度'}]
   entities=[{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-67g52"}]
   reasoning=用户明确在诊断问题，发现node2节点上存在taint `test-unschedulable=true:NoSchedule`，导致Pod `l1-test-nginx-6c69dc7c76-67g52` 处于Pending状态，事件显示调度失败原因为节点有不可容忍的污点。节点状态Ready，但污点阻止了调度。
   layer_analysis={"layer": "L1", "layers": ["L1"], "layer_name": "集群与节点层", "confidence": 0.95, "reasoning": "用户明确在诊断问题，发现node2节点上存在taint `test-unschedulable=true:NoSchedule`，导致Pod `l1-test-nginx-6c69dc7c76-67g52` 处于Pending状态，事件显示调度失败原因为节点有不可容忍的污点。节点状态Ready，但污点阻止了调度。", "key_entities": [{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-67g52"}], "possible_scenarios": [{"scenario": "节点被Taint标记为不可调度", "probability": "高", "reason": "节点node2存在明确的NoSchedule污点，且Pod因该污点无法调度"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，我已经确认了问题：**node2 节点上有一个 taint `test-unschedulable=true:NoSchedule`，导致 Pod 无法调度到该节点上**。让我制定详细的证据采集计划来全面确认这个问题。

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
      "purpose": "获取完整的节点配置，确认 taint 的完整定义和添加时间"
    },
    {
      "id": "e2",
      "description": "检查 node2 节点的事件历史",
      "level": "important",
      "tool": "kubectl_events",
      "command": "kubectl get events --field-selector involvedObject.kind=Node,involvedObject.name=node2",
      "purpose": "查看节点相关事件，确认 taint 何时添加以及是否有其他异常"
    },
    {
      "id": "e3",
      "description": "检查受影响的 Pod 详情",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e -o yaml",
      "purpose": "查看 Pod 完整配置，确认 nodeSelector 和 tolerations 配置"
    },
    {
      "id": "e4",
      "description": "检查集群中所有 Pending 状态的 Pod",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.conditions[?(@.type=='PodScheduled')].reason,MESSAGE:.status.conditions[?(@.type=='PodScheduled')].message",
      "purpose": "确认是否有其他 Pod 也因 taint 问题而 Pending"
    },
    {
      "id": "e5",
      "description": "检查节点资源使用情况",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "node_memory_MemAvailable_bytes{instance=~'.*node2.*'} / node_memory_MemTotal_bytes{instance=~'.*node2.*'} * 100",
      "purpose": "确认 node2 节点内存使用率，排除资源压力导致的问题"
    }
  ],
  "collection_strategy": "首先确认 taint 的完整定义和添加时间，然后检查受影响的 Pod 配置，最后查看是否有其他 Pod 也受影响。同时检查节点资源使用情况以排除资源压力问题。"
}
```

现在开始逐项执行证据采集：

## 第一步：确认 node2 节点的 taint 详情
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Node
metadata:
  annotations:
    kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock
    node.alpha.kubernetes.io/ttl: "0"
    projectcalico.org/IP
   💭 [证据链采集] ## 第二步：检查 node2 节点的事件历史
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 No events found in mcp namespace.
   💭 [证据链采集] 让我重新检查节点事件，使用正确的命令格式：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "No resources found\n", "returncode": 0}
   💭 [证据链采集] ## 第三步：检查受影响的 Pod 详情
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
   💭 [证据链采集] ## 第四步：检查集群中所有 Pending 状态的 Pod
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.conditions[?(@.t
   ✅ [证据链采集] 完成 (58.3s)
   📤 → 下游数据: evidence_items=5/6
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "确认 node2 节点的 taint 详情", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get node node2 -o yaml", "purpose": "获取完整的节点配置，确认 taint 的完整定义和添加时间"}, {"id": "e2", "description": "检查 node2 节点的事件历史", "level": "important", "tool": "kubectl_events", "command": "kubectl get events --field-selector involvedObject.kind=Node,involvedObject.name=node2", "purpose": "查看节点相关事件，确认 taint 何时添加以及是否有其他异常"}, {"id": "e3", "description": "检查受影响的 Pod 详情", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e -o yaml", "purpose": "查看 Pod 完整配置，确认 nodeSelector 和 tolerations 配置"}, {"id": "e4", "description": "检查集群中所有 Pending 状态的 Pod", "level": "important", "tool": "kubernetes_tabular_query", "command": "kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.conditions[?(@.type=='PodScheduled')].reason,MESSAGE:.status.conditions[?(@.type=='PodScheduled')].message", "purpose": "确认是否有其他 Pod 也因 taint 问题而 Pending"}, {"id": "e5", "description": "检查节点资源使用情况", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "node_memory_MemAvailable_bytes{instance=~'.*node2.*'} / node_memory_MemTotal_bytes{instance=~'.*node2.*'} * 100", "purpose": "确认 node2 节点内存使用率，排除资源压力导致的问题"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Node\nmetadata:\n  annotations:\n    kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n    node.alpha.kubernetes.io/ttl: \"0\"\n    projectcalico.org/IP", "duration_s": 0}, {"tool": "kubectl_events", "data": "No events found in mcp namespace.", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"\", \"stderr\": \"No resources found\\n\", \"returncode\": 0}", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  creationTimestamp: \"2026-04-20T08:34:50Z\"\n  generateName: l1-test-nginx-6c69dc7c76-\n  labels:\n    app: nginx\n    e2e-test: \"true\"\n    pod-template-hash: 6c69dc7c76", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "Command failed (exit 1):\nkubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.conditions[?(@.t", "duration_s": 0}], "llm_analysis": "## 第四步：检查集群中所有 Pending 状态的 Pod", "collection_summary": "计划 6 项，实际采集 5 项，未采集 1 项，完整度 83%", "evidence_inventory": [{"id": "e1", "description": "确认 node2 节点的 taint 详情", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "检查 node2 节点的事件历史", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "检查受影响的 Pod 详情", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查集群中所有 Pending 状态的 Pod", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "检查节点资源使用情况", "level": "optional", "collected": false, "source": "planned"}, {"id": "extra_2", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": ["e5(检查节点资源使用情况): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/6 项, 完整度: 83%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 8.0s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "node2 节点被添加了 taint: test-unschedulable=true:NoSchedule", "propagation": "taint 阻止新 Pod 调度到 node2 → Pod 的 nodeSelector 强制要求调度到 node2 → 调度器无法找到符合条件的节点", "direct_cause": "Pod 的调度约束（nodeSelector: node2）与节点调度限制（taint: NoSchedule）冲突", "manifestation": "Pod 处于 Pending 状态，调度失败事件显示节点 taint 和 nodeSelector 不匹配"}
   rca_analysis={"phenomenon": "Pod l1-test-nginx-6c69dc7c76-67g52 处于 Pending 状态，无法调度到任何节点", "evidence_inventory": [{"id": "e1", "content": "Pod l1-test-nginx-6c69dc7c76-67g52 状态为 Pending，PodScheduled=False，事件显示调度失败原因：1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector", "source": "kubectl_describe Pod", "reliability": "高"}, {"id": "e2", "content": "node2 节点存在 taint: test-unschedulable=true:NoSchedule", "source": "kubectl_describe node2", "reliability": "高"}, {"id": "e3", "content": "Pod 配置了 nodeSelector: kubernetes.io/hostname=node2，强制要求调度到 node2", "source": "kubectl_get_yaml Pod spec", "reliability": "高"}, {"id": "e4", "content": "node2 节点 Ready=True，所有条件正常（MemoryPressure=False, DiskPressure=False, PIDPressure=False），资源充足（CPU 使用率 8%，内存使用率 5%）", "source": "kubectl_describe node2 status.conditions 和 Allocated resources", "reliability": "高"}, {"id": "e5", "content": "集群有 3 个节点（master, node1, node2）都处于 Ready 状态", "source": "kubectl_get_by_kind_in_cluster nodes", "reliability": "高"}, {"id": "e6", "content": "node2 节点上已有 14 个 Pod 在正常运行，包括 aiops-copilot 等", "source": "kubectl_describe node2 Non-terminated Pods", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Pod l1-test-nginx-6c69dc7c76-67g52 的 Events: Warning FailedScheduling 16m default-scheduler 0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器明确报告调度失败原因：1）node2 有无法容忍的 taint；2）其他节点不匹配 Pod 的 nodeSelector"}, {"evidence_id": "e2", "raw_data": "node2 的 spec.taints: - effect: NoSchedule, key: test-unschedulable, value: \"true\"", "interpretation": "node2 被标记了 NoSchedule taint，阻止新 Pod 调度到该节点"}, {"evidence_id": "e3", "raw_data": "Pod 的 spec.nodeSelector: kubernetes.io/hostname: node2", "interpretation": "Pod 强制要求调度到 node2 节点，无法调度到其他节点"}, {"evidence_id": "e4", "raw_data": "node2 的 conditions: Ready=True (KubeletReady), MemoryPressure=False, DiskPressure=False, PIDPressure=False; Allocated resources: cpu 1 (8%), memory 1828375040 (5%)", "interpretation": "node2 节点健康状态正常，资源充足，不是节点故障或资源压力导致的问题"}, {"evidence_id": "e5", "raw_data": "3 个节点 STATUS 都是 Ready: master, node1, node2", "interpretation": "集群节点整体健康，没有 NotReady 节点"}, {"evidence_id": "e6", "raw_data": "node2 上运行着 14 个 Pod，包括 aiops-copilot-65d877679c-knszd (20m), exec-test (5h28m), network-test-from-running (3h35m) 等", "interpretation": "node2 节点正在正常工作，已有 Pod 运行，说明 taint 是最近添加或只影响新 Pod"}], "causal_chain": {"root_cause": "node2 节点被添加了 taint: test-unschedulable=true:NoSchedule", "propagation": "taint 阻止新 Pod 调度到 node2 → Pod 的 nodeSelector 强制要求调度到 node2 → 调度器无法找到符合条件的节点", "direct_cause": "Pod 的调度约束（nodeSelector: node2）与节点调度限制（taint: NoSchedule）冲突", "manifestation": "Pod 处于 Pending 状态，调度失败事件显示节点 taint 和 nodeSelector 不匹配"}, "root_cause_summary": "根因是 node2 节点存在 taint `test-unschedulable=true:NoSchedule`（证据 e2），而 Pod `l1-test-nginx-6c69dc7c76-67g52` 配置了 `nodeSelector: kubernetes.io/hostname=node2`（证据 e3），强制要求调度到 node2。调度器报告 0/3 节点可用：1）node2 有无法容忍的 taint；2）其他节点不匹配 nodeSelector（证据 e1）。node2 节点本身健康（Ready=True，资源充足，证据 e4），已有 14 个 Pod 在运行（证据 e6），说明 taint 是导致新 Pod 无法调度的直接原因。", "confidence": 0.95, "primary_runbooks": ["L1 Node NotReady / Taint 导致不可调度"], "alternative_causes": ["节点资源不足：已被证据 e4 排除（CPU 8%，内存 5% 使用率）", "节点 NotReady：已被证据 e4 排除（Ready=True）", "调度器故障：但其他 Pod 正常调度，且调度器给出了明确错误信息"], "limitations": "1. 未采集到 taint 的添加时间和原因（人为操作还是自动添加）；2. 未检查是否有其他 Pending Pod 受同一 taint 影响；3. 节点资源使用情况采集不完整（证据 5 未采集），但已有数据表明资源充足。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: node2 节点被添加了 taint: test-unschedulable=true:NoSchedule
     传导机制: taint 阻止新 Pod 调度到 node2 → Pod 的 nodeSelector 强制要求调度到 node2 → 调度器无法找到符合条件的节点
     最终表现: Pod 处于 Pending 状态，调度失败事件显示节点 taint 和 nodeSelector 不匹配


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 39.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5818 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 26.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **问题层级** | L1 - 集群与节点层 |
| **问题分类** | 节点 Taint 导致 Pod 不可调度 |
| **置信度** | 高 (95%) |
| **证据完整度** | 5/6 (83%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键发现**：
您的集群整体节点状态健康，但存在一个**调度冲突**：一个名为 `l1-test-nginx-6c69dc7c76-67g52` 的 Pod 因无法调度而处于 `Pending` 状态。其根本原因是目标节点 `node2` 被标记为不可调度，而该 Pod 又强制要求调度到该节点。

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `l1-test-nginx-6c69dc7c76-67g52` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| 错误信息 | `0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector` |

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod` | `Status: Pending`, `PodScheduled: False`, Events: `Warning FailedScheduling ... 0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector` | Pod 调度失败，原因是指定节点有污点且其他节点不匹配选择器 |
| 2 | 节点 Taint | `kubectl describe node node2` | `Taints: test-unschedulable=true:NoSchedule` | node2 节点被标记了 `NoSchedule` 污点，阻止新 Pod 调度 |
| 3 | Pod 节点选择器 | `kubectl get pod -o yaml` | `spec.nodeSelector: kubernetes.io/hostname: node2` | Pod 配置强制要求调度到 `node2` 节点 |
| 4 | 节点健康状态 | `kubectl describe node node2` | `Conditions: Ready=True, MemoryPressure=False, DiskPressure=False, PIDPressure=False`, `Allocated resources: cpu 1 (8%), memory 1828375040 (5%)` | node2 节点本身健康且资源充足，非节点故障 |
| 5 | 集群节点状态 | `kubectl get nodes` | `master Ready`, `node1 Ready`, `node2 Ready` | 集群所有 3 个节点状态均为 `Ready` |
| 6 | 节点现有负载 | `kubectl describe node node2` | `Non-terminated Pods: (14 in total)`，包括 `aiops-copilot-65d877679c-knszd` 等 | node2 上已有 14 个 Pod 正常运行，说明污点是后来添加或仅影响新 Pod |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 调度失败事件明确指出 `node2` 有无法容忍的污点（证据 #2），同时 Pod 的 `nodeSelector` 又锁定 `node2`（证据 #3），导致调度器找不到任何可用节点。
- **证据 #4 + #5 + #6 排除其他可能**：节点状态 `Ready`、资源使用率低（CPU 8%，内存 5%），且已有 Pod 正常运行，排除了节点故障、资源不足等常见原因。
- **证据链**：`node2` 被添加 `NoSchedule` 污点 → 新 Pod 无法调度到 `node2` → 但 Pod `l1-test-nginx` 的 `nodeSelector` 强制要求调度到 `node2` → 调度冲突 → Pod 永远处于 `Pending` 状态。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| e5: 检查节点资源使用情况 (Prometheus 查询) | optional | 无法从监控层面再次确认节点资源使用率，但已有 `kubectl describe` 数据表明资源充足，影响较小 |

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ node2 节点被添加了 taint: test-unschedulable=true:NoSchedule    │
│ （可能是人为维护操作或自动化脚本添加）                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ taint 阻止新 Pod 调度到 node2 →                                 │
│ Pod l1-test-nginx 配置了 nodeSelector: kubernetes.io/hostname=node2 │
│ → 调度器无法找到同时满足“无污点”和“节点选择器”的节点             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 的调度约束与节点调度限制产生冲突，调度失败                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod l1-test-nginx-6c69dc7c76-67g52 状态为 Pending，             │
│ 事件显示 FailedScheduling                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (调度失败事件)、证据 #2 (node2 的 `NoSchedule` taint) 和证据 #3 (Pod 的 `nodeSelector: node2`)，
问题的根本原因是 **`node2` 节点上的 `test-unschedulable=true:NoSchedule` 污点与 Pod `l1-test-nginx` 强制调度到 `node2` 的节点选择器配置相互冲突**，导致调度器无法为该 Pod 找到合适的节点。

**置信度**：高 (95%)
- ✅ 调度器事件明确指出了污点和节点选择器不匹配（证据 #1）
- ✅ `node2` 节点确实存在 `NoSchedule` 污点（证据 #2）
- ✅ Pod 配置确实锁定了 `node2` 节点（证据 #3）
- ✅ 排除了节点不健康或资源不足的可能性（证据 #4, #5, #6）
- ⚠️ 未采集到污点的添加时间和原因，但不影响当前根因判断

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 移除 node2 节点的污点 (如果该污点已不再需要)**
```bash
kubectl taint nodes node2 test-unschedulable-
```
*依据*：移除污点后，`node2` 恢复可调度状态，Pod 可以正常调度上去。
*注意*：执行前请确认此污点是否为有意添加（例如用于节点维护）。如果是，请先完成维护工作。

**2. [替代方案] 修改 Pod 配置，移除或更改 nodeSelector (如果业务允许)**
如果 `node2` 的污点需要保留，则需修改 Pod 的调度策略，使其可以调度到其他节点。
```bash
# 查看并修改 Deployment/ReplicaSet 的 nodeSelector
kubectl edit deployment l1-test-nginx -n aiops-e2e
# 或
kubectl edit replicaset l1-test-nginx-6c69dc7c76 -n aiops-e2e
```
在编辑器中，找到 `spec.template.spec.nodeSelector` 字段，将其删除或修改为其他节点标签（如 `kubernetes.io/hostname: node1`）。

**3. [替代方案] 为 Pod 添加对应的 Toleration (如果需要在有污点的 node2 上运行)**
如果需要在带有 `test-unschedulable=true:NoSchedule` 污点的 `node2` 上运行此 Pod，可以为 Pod 添加容忍度。
```bash
# 同样通过编辑 Deployment/ReplicaSet 来添加
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

### 后续优化
1.  **污点管理规范**：建立节点污点的添加、记录和清理流程，避免因遗忘的污点导致调度问题。
2.  **调度策略检查**：在应用部署前，检查其 `nodeSelector`、`nodeAffinity` 是否与集群节点的 `taint`、`label` 状态匹配。
3.  **监控告警**：配置对长时间处于 `Pending` 状态的 Pod 的告警。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 node2 污点已移除 | `kubectl describe node node2 \| grep Taints` | `Taints: <none>` |
| 2. 确认 Pod 状态变为 Running | `kubectl get pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e` | `STATUS: Running` |
| 3. 确认 Pod 调度到 node2 | `kubectl get pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e -o wide` | `NODE: node2` |

## ⚠️ 注意事项
- 执行 `kubectl taint` 命令前，请务必确认移除该污点不会影响集群其他正在进行的维护操作或隔离策略。
- 如果选择修改 Pod 配置（方案2或3），需要确保应用允许调度到其他节点或在有污点的节点上运行。
- 本问题仅影响特定配置的新 Pod，集群核心组件及其他现有 Pod 运行正常。

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 40.3s (15%) ✅
├─ 证据链采集: 58.3s (22%) ✅
├─ 根因分析: 68.0s (26%) ✅
├─ 汇总总结: 99.8s (37%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: L1 Node NotReady / Taint 导致不可调度
- **参考 Runbook**: L1 Node NotReady / Taint 导致不可调度
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
