======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 8ef84601d3904971]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来检查一下集群的整体状态，看看有什么问题。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     l1-test-ng
   💭 [问题定位] 我看到了一个异常 Pod：`l1-test-nginx-6c69dc7c76-67g52` 处于 Pending 状态。让我检查一下这个 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-67g52
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [问题定位] 现在让我检查一下节点的状态，看看是否有节点被标记了 taint。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   207d   v1.26.8  
   💭 [问题定位] 让我检查一下 node2 的详细信息，因为 Pod 有 nodeSelector 指定了 node2。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 现在我明白了问题所在。让我获取相关的 runbook 来参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L1 Node NotReady / Taint 导致不可调度

> 层级: L1 - 集群与节点层 | 场景: 节点 NotReady 或被 Taint 标记为不可调度

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| 节点状态 | `kubectl get nodes` 显示 STATUS=NotReady 或 Unknown 
   ✅ [问题定位] 完成 (38.8s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '节点 Taint 导致不可调度', 'probability': '高', 'reason': 'Pod 因节点 Taint 而无法调度，节点状态 Ready，符合 L1 层特征'}]
   entities=[{"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-67g52"}, {"type": "Node", "value": "node2"}]
   reasoning=分析文本显示用户正在诊断一个 Pending 状态的 Pod (l1-test-nginx-6c69dc7c76-67g52)。Pod 的 Events 明确显示调度失败原因为 '1 node(s) had untolerated taint {test-unschedulable: true}'。节点 node2 被标记了 Taint 'test-unschedulable=true:NoSchedule'。用户意图是获取 runbook 来参考，表明其正在排查此调度故障。
   layer_analysis={"layer": "L1", "layers": ["L1"], "layer_name": "集群与节点层", "confidence": 0.9, "reasoning": "分析文本显示用户正在诊断一个 Pending 状态的 Pod (l1-test-nginx-6c69dc7c76-67g52)。Pod 的 Events 明确显示调度失败原因为 '1 node(s) had untolerated taint {test-unschedulable: true}'。节点 node2 被标记了 Taint 'test-unschedulable=true:NoSchedule'。用户意图是获取 runbook 来参考，表明其正在排查此调度故障。", "key_entities": [{"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-67g52"}, {"type": "Node", "value": "node2"}], "possible_scenarios": [{"scenario": "节点 Taint 导致不可调度", "probability": "高", "reason": "Pod 因节点 Taint 而无法调度，节点状态 Ready，符合 L1 层特征"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 90%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据您提供的集群状态，我已经识别到一个明确的调度问题。让我制定详细的证据采集计划来深入分析这个问题。

```json
{
  "layer": "L1",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "确认节点状态和Taint详情",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe node node2",
      "purpose": "确认node2的Taint详情、节点状态和资源使用情况"
    },
    {
      "id": "e2",
      "description": "检查所有Pending状态的Pod",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.reason --sort-by=.metadata.namespace",
      "purpose": "查看集群中所有Pending状态的Pod及其原因"
    },
    {
      "id": "e3",
      "description": "检查Pod的nodeSelector配置",
      "level": "important",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e",
      "purpose": "确认Pod的nodeSelector配置，验证是否强制调度到node2"
    },
    {
      "id": "e4",
      "description": "检查节点资源使用情况",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "execute_prometheus_instant_query",
      "purpose": "通过Prometheus查询node2的CPU、内存使用率，确认是否有资源压力"
    },
    {
      "id": "e5",
      "description": "检查节点事件历史",
      "level": "optional",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=node2 --sort-by='.lastTimestamp' -o custom-columns='LAST SEEN:.lastTimestamp,TYPE:.type,REASON:.reason,OBJECT:.involvedObject.name,MESSAGE:.message'",
      "purpose": "查看node2的事件历史，了解Taint何时添加及是否有其他问题"
    }
  ],
  "collection_strategy": "首先确认节点Taint详情和状态，然后检查所有Pending Pod，接着验证Pod调度配置，最后通过监控数据确认节点资源状况"
}
```

现在让我逐项执行证据采集：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.reason' | (head 
   💭 [证据链采集] 让我用另一种方式查询Pending状态的Pod：
   💭 [证据链采集] 调用工具: kubernetes_jq_query
   💭 [证据链采集] 工具结果: kubernetes_jq_query (success)
      📄 Script failed (exit 127):
Executing jq query for pods...
/tmp/tmpnsgeab4d.sh: line 4: jq: command not found

   💭 [证据链采集] 让我用更简单的方式查询：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     l1-test-ng
   ✅ [证据链采集] 完成 (49.1s)
   📤 → 下游数据: evidence_items=4/6
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "确认节点状态和Taint详情", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe node node2", "purpose": "确认node2的Taint详情、节点状态和资源使用情况"}, {"id": "e2", "description": "检查所有Pending状态的Pod", "level": "important", "tool": "kubernetes_tabular_query", "command": "kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.reason --sort-by=.metadata.namespace", "purpose": "查看集群中所有Pending状态的Pod及其原因"}, {"id": "e3", "description": "检查Pod的nodeSelector配置", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e", "purpose": "确认Pod的nodeSelector配置，验证是否强制调度到node2"}, {"id": "e4", "description": "检查节点资源使用情况", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "execute_prometheus_instant_query", "purpose": "通过Prometheus查询node2的CPU、内存使用率，确认是否有资源压力"}, {"id": "e5", "description": "检查节点事件历史", "level": "optional", "tool": "kubernetes_tabular_query", "command": "kubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=node2 --sort-by='.lastTimestamp' -o custom-columns='LAST SEEN:.lastTimestamp,TYPE:.type,REASON:.reason,OBJECT:.involvedObject.name,MESSAGE:.message'", "purpose": "查看node2的事件历史，了解Taint何时添加及是否有其他问题"}], "tool_results": [], "tool_data": [{"tool": "kubectl_describe", "data": "Name:               node2\nRoles:              <none>\nLabels:             beta.kubernetes.io/arch=amd64\n                    beta.kubernetes.io/os=linux\n                    kubernetes.io/arch=amd64\n    ", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "Command failed (exit 1):\nkubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,REASON:.status.reason' | (head ", "duration_s": 0}, {"tool": "kubernetes_jq_query", "data": "Script failed (exit 127):\nExecuting jq query for pods...\n/tmp/tmpnsgeab4d.sh: line 4: jq: command not found\n", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\naiops-e2e     l1-test-ng", "duration_s": 0}], "llm_analysis": "让我用更简单的方式查询：", "collection_summary": "计划 6 项，实际采集 4 项，未采集 2 项，完整度 67%", "evidence_inventory": [{"id": "e1", "description": "确认节点状态和Taint详情", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "检查所有Pending状态的Pod", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "检查Pod的nodeSelector配置", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查节点资源使用情况", "level": "optional", "collected": false, "source": "planned"}, {"id": "e5", "description": "检查节点事件历史", "level": "optional", "collected": false, "source": "planned"}, {"id": "extra_2", "description": "工具采集: kubernetes_jq_query", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": ["e4(检查节点资源使用情况): 已规划但工具执行失败或无匹配结果", "e5(检查节点事件历史): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/6 项, 完整度: 67%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (59.1s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "节点 node2 被添加了 `test-unschedulable=true:NoSchedule` 污点。", "propagation": "污点阻止了调度器将任何新 Pod（除非有对应容忍）分配到 node2。同时，Pod `l1-test-nginx` 的节点选择器 `kubernetes.io/hostname=node2` 强制要求调度到 node2。", "direct_cause": "调度器无法为 Pod `l1-test-nginx` 找到符合条件的节点：唯一匹配节点选择器的 node2 有不可容忍的污点；其他节点（master, node1）不匹配节点选择器。", "manifestation": "Pod `l1-test-nginx-6c69dc7c76-67g52` 状态持续为 Pending，并产生 FailedScheduling 事件。"}
   rca_analysis={"phenomenon": "Pod l1-test-nginx-6c69dc7c76-67g52 处于 Pending 状态，无法调度到节点上。", "evidence_inventory": [{"id": "e1", "content": "Pod l1-test-nginx-6c69dc7c76-67g52 状态为 Pending，事件显示调度失败，原因为节点有不可容忍的污点和节点选择器不匹配。", "source": "kubectl_describe (Pod)", "reliability": "高"}, {"id": "e2", "content": "节点 node2 被标记了污点 `test-unschedulable=true:NoSchedule`。", "source": "kubectl_describe (Node node2)", "reliability": "高"}, {"id": "e3", "content": "Pod l1-test-nginx-6c69dc7c76-67g52 的节点选择器为 `kubernetes.io/hostname=node2`。", "source": "kubectl_describe (Pod)", "reliability": "高"}, {"id": "e4", "content": "集群所有节点（master, node1, node2）状态均为 Ready。", "source": "kubectl_get_by_kind_in_cluster (Nodes)", "reliability": "高"}, {"id": "e5", "content": "节点 node2 资源充足：CPU 请求 8%，内存请求 5%，无磁盘或内存压力。", "source": "kubectl_describe (Node node2)", "reliability": "高"}, {"id": "e6", "content": "查询所有 Pending Pod 的命令失败，但 Pod 列表显示仅有一个 Pending Pod。", "source": "证据采集结果 2", "reliability": "中"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Events: Warning FailedScheduling 17m default-scheduler 0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector.", "interpretation": "调度器失败的直接原因：1. 一个节点有不可容忍的污点。2. 两个节点不匹配 Pod 的节点选择器/亲和性。"}, {"evidence_id": "e2", "raw_data": "Taints: test-unschedulable=true:NoSchedule", "interpretation": "节点 node2 被添加了 `NoSchedule` 污点，阻止新 Pod 调度到该节点。"}, {"evidence_id": "e3", "raw_data": "Node-Selectors: kubernetes.io/hostname=node2", "interpretation": "Pod 被强制要求调度到名为 `node2` 的节点上。"}, {"evidence_id": "e4", "raw_data": "master Ready, node1 Ready, node2 Ready", "interpretation": "所有节点状态健康，排除了节点 NotReady 导致调度失败的可能性。"}, {"evidence_id": "e5", "raw_data": "Conditions: MemoryPressure=False, DiskPressure=False, PIDPressure=False, Ready=True. Allocated resources: cpu 1 (8%), memory 1828375040 (5%)", "interpretation": "节点 node2 资源充足，无压力，排除了资源不足导致调度失败的可能性。"}, {"evidence_id": "e6", "raw_data": "Command failed (exit 1): ... | grep -E 'Pending'", "interpretation": "工具执行失败，但结合 Pod 列表，确认当前集群中主要的 Pending Pod 就是 l1-test-nginx-6c69dc7c76-67g52。"}], "causal_chain": {"root_cause": "节点 node2 被添加了 `test-unschedulable=true:NoSchedule` 污点。", "propagation": "污点阻止了调度器将任何新 Pod（除非有对应容忍）分配到 node2。同时，Pod `l1-test-nginx` 的节点选择器 `kubernetes.io/hostname=node2` 强制要求调度到 node2。", "direct_cause": "调度器无法为 Pod `l1-test-nginx` 找到符合条件的节点：唯一匹配节点选择器的 node2 有不可容忍的污点；其他节点（master, node1）不匹配节点选择器。", "manifestation": "Pod `l1-test-nginx-6c69dc7c76-67g52` 状态持续为 Pending，并产生 FailedScheduling 事件。"}, "root_cause_summary": "Pod 调度失败的根因是节点 node2 上存在 `test-unschedulable=true:NoSchedule` 污点（证据 e2），而待调度的 Pod `l1-test-nginx` 又通过节点选择器 `kubernetes.io/hostname=node2`（证据 e3）强制要求调度到该节点，导致调度冲突。集群其他节点状态正常（证据 e4）且资源充足（证据 e5），但均不满足该 Pod 的节点选择器要求。", "confidence": 0.95, "primary_runbooks": ["L1 Node NotReady / Taint 导致不可调度"], "alternative_causes": [], "limitations": "1. 未采集到节点事件历史（证据采集结果 5），无法确认污点添加的原因（例如，是否为人工维护操作）。2. 查询所有 Pending Pod 的命令执行失败（证据 e6），但根据现有 Pod 列表，此问题不影响核心结论。3. 未检查 Pod 所属的 Deployment/ReplicaSet 配置，但现有证据已足够定位节点层级的调度问题。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: 节点 node2 被添加了 `test-unschedulable=true:NoSchedule` 污点。
     传导机制: 污点阻止了调度器将任何新 Pod（除非有对应容忍）分配到 node2。同时，Pod `l1-test-nginx` 的节点选择器 `kubernetes.io/hostname=node2` 强制要求调度到 node2。
     最终表现: Pod `l1-test-nginx-6c69dc7c76-67g52` 状态持续为 Pending，并产生 FailedScheduling 事件。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 24.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5060 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 51.6s
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
| **问题分类** | 节点 Taint 导致 Pod 调度失败 |
| **置信度** | 高 (95%) |
| **证据完整度** | 4/6 (67%) |
---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**集群状态总结**：
您的集群整体运行正常，所有节点（master, node1, node2）状态均为 `Ready`。但存在一个明确的调度问题：一个名为 `l1-test-nginx-6c69dc7c76-67g52` 的 Pod 因调度冲突而持续处于 `Pending` 状态。

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `l1-test-nginx-6c69dc7c76-67g52` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| 错误信息 | `0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector` |
---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod` | `Status: Pending`<br>`Events: Warning FailedScheduling ... 0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector` | Pod 因节点污点和选择器不匹配而调度失败 |
| 2 | Pod 节点选择器 | `kubectl describe pod` | `Node-Selectors: kubernetes.io/hostname=node2` | Pod 被强制要求调度到 `node2` |
| 3 | 节点状态与污点 | `kubectl describe node node2` | `Taints: test-unschedulable=true:NoSchedule`<br>`Conditions: Ready=True, MemoryPressure=False, DiskPressure=False` | 节点 `node2` 被标记为不可调度，但状态健康、资源充足 |
| 4 | 集群节点状态 | `kubectl get nodes` | `master Ready, node1 Ready, node2 Ready` | 所有节点状态正常，排除了节点故障 |
| 5 | 节点资源分配 | `kubectl describe node node2` | `Allocated resources: cpu 1 (8%), memory 1828375040 (5%)` | 节点 `node2` 资源充足，无压力 |

### 证据关联分析
- **证据 #1 + #3 印证**：调度失败事件指出节点有不可容忍的污点，而 `node2` 确实存在 `test-unschedulable=true:NoSchedule` 污点。
- **证据 #1 + #2 印证**：调度失败事件指出节点选择器不匹配，而 Pod 的节点选择器为 `kubernetes.io/hostname=node2`，强制绑定到 `node2`。
- **证据链**：Pod 要求调度到 `node2` → `node2` 有 `NoSchedule` 污点 → 调度器无法找到符合条件的节点 → Pod 状态 `Pending`。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点资源使用情况（Prometheus） | optional | 无法从监控角度确认节点负载，但 `kubectl describe` 已显示资源充足 |
| 节点事件历史 | optional | 无法确认 `test-unschedulable` 污点添加的原因和时间（如是否为人工维护操作） |
---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 节点 node2 被添加了 `test-unschedulable=true:NoSchedule` 污点   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 污点阻止调度器将新 Pod 分配到 node2，除非 Pod 有对应容忍度       │
│ 同时，Pod 的节点选择器强制要求调度到 node2                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度器无法找到同时满足以下条件的节点：                          │
│ 1. 匹配节点选择器 `kubernetes.io/hostname=node2`               │
│ 2. 没有不可容忍的污点                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod `l1-test-nginx-6c69dc7c76-67g52` 状态持续为 Pending，       │
│ 并产生 FailedScheduling 事件                                    │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #3 (`Taints: test-unschedulable=true:NoSchedule`) 和证据 #2 (`Node-Selectors: kubernetes.io/hostname=node2`)，问题的根本原因是**节点 `node2` 上的 `NoSchedule` 污点与 Pod `l1-test-nginx` 的强制节点选择器冲突**，导致调度器无法为 Pod 分配节点。

**置信度**：高 (95%)
- ✅ 调度失败事件直接指向污点和节点选择器问题
- ✅ `node2` 上明确存在 `test-unschedulable=true:NoSchedule` 污点
- ✅ Pod 配置明确要求调度到 `node2`
- ✅ 其他节点状态正常且资源充足，排除了其他干扰因素
- ⚠️ 缺少污点添加的历史事件，无法确认操作背景
---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Pod 添加容忍度（Toleration）**
如果 Pod 确实需要调度到 `node2`，且可以接受该污点，修改其 Deployment 或 Pod 模板，添加对应的容忍度。
```yaml
# 在 Pod spec 中添加
tolerations:
- key: "test-unschedulable"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```
**2. [推荐] 移除节点污点**
如果 `node2` 上的污点是测试或临时添加的，且不再需要，可以将其移除。
```bash
kubectl taint nodes node2 test-unschedulable:NoSchedule-
```
**3. [可选] 修改 Pod 节点选择器**
如果 Pod 不一定非要调度到 `node2`，可以放宽或移除其节点选择器，使其可以调度到其他可用节点（如 `node1`）。
```yaml
# 修改 Pod spec 中的 nodeSelector
# 例如，移除或修改为更宽松的选择器
# nodeSelector: {}
```
### 后续优化
1.  **污点管理规范**：建立节点污点的添加、记录和清理流程，避免因遗忘的污点导致调度问题。
2.  **Pod 调度策略**：评估是否所有 Pod 都需要强制的节点选择器，考虑使用节点亲和性（`nodeAffinity`）提供更灵活的调度策略。
---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认污点已移除 | `kubectl describe node node2 \| grep Taints` | `Taints: <none>` 或不再包含 `test-unschedulable` |
| 2. 确认 Pod 状态 | `kubectl get pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e` | `STATUS: Running` |
| 3. 检查 Pod 调度节点 | `kubectl get pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e -o wide` | `NODE` 列显示已成功调度的节点 |
---
## ⚠️ 注意事项
- 执行移除污点操作前，请确认该污点是否为有意的维护操作（例如，节点升级、故障排查）。如果是，请确保维护已完成。
- 如果选择为 Pod 添加容忍度，请评估让 Pod 运行在带有 `test-unschedulable` 污点的节点上是否符合预期。
- 本问题仅影响特定 Pod 的调度，集群核心组件及其他工作负载运行正常。

---

## 📊 性能统计

├─ 总耗时: 3.9m
├─ 问题定位: 38.8s (17%) ✅
├─ 证据链采集: 49.1s (21%) ✅
├─ 根因分析: 59.1s (26%) ✅
├─ 汇总总结: 84.6s (37%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: L1 Node NotReady / Taint 导致不可调度
- **参考 Runbook**: L1 Node NotReady / Taint 导致不可调度
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
