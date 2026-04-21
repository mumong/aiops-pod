======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 8090be15f1e94cfc]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您检查集群的整体健康状况。首先让我查看所有Pod的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     l1-test-ng
   💭 [问题定位] 我发现了1个异常Pod：`l1-test-nginx-6c69dc7c76-67g52` 处于 Pending 状态。让我查看这个Pod的详细信息来了解原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             l1-test-nginx-6c69dc7c76-67g52
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             <none>
Labels:           app=nginx
                  e2e-te
   💭 [问题定位] 现在让我查看节点状态，看看是否有节点被标记了 taint 或者处于 NotReady 状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   207d   v1.26.8  
   💭 [问题定位] 所有节点都显示为 Ready 状态。让我查看节点2的详细信息，因为Pod有节点亲和性要求 `kubernetes.io/hostname=node2`。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:               node2
Roles:              <none>
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
    
   💭 [问题定位] 现在我明白了问题所在。节点 `node2` 被标记了一个 taint：`test-unschedulable=true:NoSchedule`。这个 taint 阻止了 Pod 调度到该节点上。让我获取相关的 runbook 来参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L1 Node NotReady / Taint 导致不可调度

> 层级: L1 - 集群与节点层 | 场景: 节点 NotReady 或被 Taint 标记为不可调度

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| 节点状态 | `kubectl get nodes` 显示 STATUS=NotReady 或 Unknown 
   ✅ [问题定位] 完成 (43.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '节点被 Taint 标记为不可调度', 'probability': '高', 'reason': '节点 node2 存在明确的 NoSchedule 污点，且 Pod 调度失败事件与此吻合。'}]
   entities=[{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-67g52"}]
   reasoning=用户明确在诊断问题，发现节点 node2 被标记了 taint `test-unschedulable=true:NoSchedule`，导致 Pod `l1-test-nginx-6c69dc7c76-67g52` 处于 Pending 状态，事件显示调度失败原因为节点有不可容忍的污点。节点状态为 Ready，但污点阻止了调度。
   layer_analysis={"layer": "L1", "layers": ["L1"], "layer_name": "集群与节点层", "confidence": 0.95, "reasoning": "用户明确在诊断问题，发现节点 node2 被标记了 taint `test-unschedulable=true:NoSchedule`，导致 Pod `l1-test-nginx-6c69dc7c76-67g52` 处于 Pending 状态，事件显示调度失败原因为节点有不可容忍的污点。节点状态为 Ready，但污点阻止了调度。", "key_entities": [{"type": "Node", "value": "node2"}, {"type": "Pod", "value": "l1-test-nginx-6c69dc7c76-67g52"}], "possible_scenarios": [{"scenario": "节点被 Taint 标记为不可调度", "probability": "高", "reason": "节点 node2 存在明确的 NoSchedule 污点，且 Pod 调度失败事件与此吻合。"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，我已经识别出问题：**节点 `node2` 被标记了一个 `test-unschedulable=true:NoSchedule` taint，导致 Pod 无法调度到该节点**。让我制定详细的证据采集计划并执行。

```json
{
  "layer": "L1",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "确认 node2 的 taint 详情",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml node node2",
      "purpose": "获取节点完整的 taint 配置和状态信息"
    },
    {
      "id": "e2",
      "description": "检查受影响的 Pod 调度事件详情",
      "level": "critical",
      "tool": "kubectl_events",
      "command": "kubectl events pod l1-test-nginx-6c69dc7c76-67g52 -n aiops-e2e",
      "purpose": "查看 Pod 调度失败的具体事件信息"
    },
    {
      "id": "e3",
      "description": "检查节点上现有 Pod 的状态",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,AGE:.metadata.creationTimestamp --field-selector spec.nodeName=node2",
      "purpose": "确认 node2 上已有 Pod 的运行状态，验证 taint 是否影响现有 Pod"
    },
    {
      "id": "e4",
      "description": "检查集群中所有 Pending 状态的 Pod",
      "level": "important",
      "tool": "kubernetes_tabular_query",
      "command": "kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,AGE:.metadata.creationTimestamp --field-selector status.phase=Pending",
      "purpose": "确认是否有其他 Pod 也因 taint 而无法调度"
    },
    {
      "id": "e5",
      "description": "检查节点的资源使用情况",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "execute_prometheus_instant_query('(1 - avg(rate(node_cpu_seconds_total{instance=~".*node2.*"}[5m])) by (instance)) * 100')",
      "purpose": "确认 node2 的 CPU 使用率是否正常"
    }
  ],
  "collection_strategy": "首先确认 taint 的完整配置，然后检查受影响的 Pod 事件，最后验证节点状态和资源使用情况。优先采集关键证据以确认问题根源。"
}
```

现在开始逐项执行证据采集：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Node
metadata:
  annotations:
    kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock
    node.alpha.kubernetes.io/ttl: "0"
    projectcalico.org/IP
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 LAST SEEN           TYPE      REASON             OBJECT                               MESSAGE
39m                 Warning   FailedScheduling   Pod/l1-test-nginx-6c69dc7c76-67g52   0/3 nodes are availa
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    NODE     AGE
default       exec-test                                           Running   node2    2026-04-20T03:22:35Z
defau
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,AGE:.metadata.creationTimestamp
   💭 [证据链采集] 让我用正确的方法查询 Pending 状态的 Pod：
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 NAMESPACE     NAME                                                STATUS    NODE     AGE
aiops-e2e     l1-test-nginx-6c69dc7c76-67g52                      Pending   <none>   2026-04-20T08:34:50Z
aiops
   💭 [证据链采集] 现在让我检查 Pod 的详细信息，看看是否有节点亲和性设置：
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
   ✅ [证据链采集] 完成 (1m 7.8s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan": [{"id": "cmd_0", "description": "执行命令: kubectl get -o yaml node node2\",", "level": "important", "command": "kubectl get -o yaml node node2\",", "tool": "kubectl", "purpose": "获取集群状态或资源信息"}, {"id": "cmd_1", "description": "执行命令: kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,AGE:.metadata.creationTimestamp --field-selector spec.nodeName=node2\",", "level": "important", "command": "kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,AGE:.metadata.creationTimestamp --field-selector spec.nodeName=node2\",", "tool": "kubectl", "purpose": "获取集群状态或资源信息"}, {"id": "cmd_2", "description": "执行命令: kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,AGE:.metadata.creationTimestamp --field-selector status.phase=Pending\",", "level": "important", "command": "kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,AGE:.metadata.creationTimestamp --field-selector status.phase=Pending\",", "tool": "kubectl", "purpose": "获取集群状态或资源信息"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Node\nmetadata:\n  annotations:\n    kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n    node.alpha.kubernetes.io/ttl: \"0\"\n    projectcalico.org/IP", "duration_s": 0}, {"tool": "kubectl_events", "data": "LAST SEEN           TYPE      REASON             OBJECT                               MESSAGE\n39m                 Warning   FailedScheduling   Pod/l1-test-nginx-6c69dc7c76-67g52   0/3 nodes are availa", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "NAMESPACE     NAME                                                STATUS    NODE     AGE\ndefault       exec-test                                           Running   node2    2026-04-20T03:22:35Z\ndefau", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "Command failed (exit 1):\nkubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,AGE:.metadata.creationTimestamp", "duration_s": 0}, {"tool": "kubernetes_tabular_query", "data": "NAMESPACE     NAME                                                STATUS    NODE     AGE\naiops-e2e     l1-test-nginx-6c69dc7c76-67g52                      Pending   <none>   2026-04-20T08:34:50Z\naiops", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  creationTimestamp: \"2026-04-20T08:34:50Z\"\n  generateName: l1-test-nginx-6c69dc7c76-\n  labels:\n    app: nginx\n    e2e-test: \"true\"\n    pod-template-hash: 6c69dc7c76", "duration_s": 0}], "llm_analysis": "现在让我检查 Pod 的详细信息，看看是否有节点亲和性设置：", "collection_summary": "计划 6 项，实际采集 6 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "cmd_0", "description": "执行命令: kubectl get -o yaml node node2\",", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "cmd_1", "description": "执行命令: kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,AGE:.metadata.creationTimestamp --field-selector spec.nodeName=node2\",", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "cmd_2", "description": "执行命令: kubectl get pods -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,AGE:.metadata.creationTimestamp --field-selector status.phase=Pending\",", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "extra_2", "description": "工具采集: kubernetes_tabular_query", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_3", "description": "工具采集: kubernetes_tabular_query", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_4", "description": "工具采集: kubernetes_tabular_query", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": [], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/6 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 13.9s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "节点 node2 被标记了 taint: test-unschedulable=true:NoSchedule", "propagation": "该 taint 阻止调度器将新 Pod 分配到 node2", "direct_cause": "Pod l1-test-nginx-6c69dc7c76-67g52 配置了 nodeSelector: kubernetes.io/hostname=node2，必须调度到 node2，但无法容忍该 taint", "manifestation": "Pod 处于 Pending 状态，调度事件显示 'node(s) had untolerated taint'"}
   rca_analysis={"phenomenon": "Pod l1-test-nginx-6c69dc7c76-67g52 处于 Pending 状态，无法调度到节点 node2", "evidence_inventory": [{"id": "e1", "content": "Pod l1-test-nginx-6c69dc7c76-67g52 状态为 Pending，NODE 列为 <none>，AGE 为 38m", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e2", "content": "Pod 事件显示 FailedScheduling，原因为 '0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector'", "source": "kubectl_describe (Pod)", "reliability": "高"}, {"id": "e3", "content": "节点 node2 状态为 Ready，但存在 Taint: test-unschedulable=true:NoSchedule", "source": "kubectl_describe (Node)", "reliability": "高"}, {"id": "e4", "content": "节点 node2 的 spec.taints 字段包含 - effect: NoSchedule, key: test-unschedulable, value: \"true\"", "source": "kubectl_get_yaml (Node)", "reliability": "高"}, {"id": "e5", "content": "Pod spec 包含 nodeSelector: kubernetes.io/hostname=node2，强制要求调度到 node2", "source": "kubectl_get_yaml (Pod)", "reliability": "高"}, {"id": "e6", "content": "节点 node2 资源使用率正常：CPU 请求 1 (8%)，内存请求 1828375040 (5%)", "source": "kubectl_describe (Node)", "reliability": "高"}, {"id": "e7", "content": "节点 node2 上已有 14 个 Pod 在运行，包括 aiops-copilot、calico-node 等", "source": "kubernetes_tabular_query (node2 Pods)", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "NAMESPACE: aiops-e2e, NAME: l1-test-nginx-6c69dc7c76-67g52, READY: 0/1, STATUS: Pending, AGE: 38m, NODE: <none>", "interpretation": "Pod 处于 Pending 状态，未被调度到任何节点"}, {"evidence_id": "e2", "raw_data": "Events: Warning FailedScheduling 38m default-scheduler 0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度失败的直接原因是：1) 节点 node2 有无法容忍的 taint；2) 其他节点不匹配 Pod 的节点选择器"}, {"evidence_id": "e3", "raw_data": "Taints: test-unschedulable=true:NoSchedule, Conditions: Ready True, MemoryPressure False, DiskPressure False, PIDPressure False", "interpretation": "节点 node2 被标记了 NoSchedule taint，但节点本身健康（Ready=True），无资源压力"}, {"evidence_id": "e4", "raw_data": "spec: taints: - effect: NoSchedule, key: test-unschedulable, value: \"true\"", "interpretation": "节点配置中明确设置了 taint，阻止新 Pod 调度"}, {"evidence_id": "e5", "raw_data": "spec: nodeSelector: kubernetes.io/hostname: node2", "interpretation": "Pod 配置强制要求调度到 node2，无法调度到其他节点"}, {"evidence_id": "e6", "raw_data": "Allocated resources: cpu 1 (8%), memory 1828375040 (5%)", "interpretation": "节点资源充足，不是资源不足导致的调度失败"}, {"evidence_id": "e7", "raw_data": "NAMESPACE: default, NAME: exec-test, STATUS: Running, NODE: node2, AGE: 2026-04-20T03:22:35Z (等14个Pod)", "interpretation": "节点上已有 Pod 在运行，证明节点功能正常，只是新调度被 taint 阻止"}], "causal_chain": {"root_cause": "节点 node2 被标记了 taint: test-unschedulable=true:NoSchedule", "propagation": "该 taint 阻止调度器将新 Pod 分配到 node2", "direct_cause": "Pod l1-test-nginx-6c69dc7c76-67g52 配置了 nodeSelector: kubernetes.io/hostname=node2，必须调度到 node2，但无法容忍该 taint", "manifestation": "Pod 处于 Pending 状态，调度事件显示 'node(s) had untolerated taint'"}, "root_cause_summary": "根因是节点 node2 上存在人为设置的 taint `test-unschedulable=true:NoSchedule`（证据 e3、e4）。该 taint 阻止新 Pod 调度到该节点。Pod `l1-test-nginx-6c69dc7c76-67g52` 配置了 `nodeSelector: kubernetes.io/hostname=node2`（证据 e5），强制要求调度到 node2，但无法容忍此 taint，导致调度失败（证据 e2）。节点本身健康（Ready=True）且资源充足（CPU 8%，内存 5%），排除节点故障或资源不足（证据 e3、e6）。", "confidence": 0.95, "primary_runbooks": ["L1 Node NotReady / Taint 导致不可调度"], "alternative_causes": [], "limitations": "证据已充分证明 taint 是根因。未采集到谁/何时设置了此 taint 的信息（可能是人为操作或自动化工具）。Pod 的 tolerations 配置未包含对此 taint 的容忍，这也是调度失败的原因之一。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: 节点 node2 被标记了 taint: test-unschedulable=true:NoSchedule
     传导机制: 该 taint 阻止调度器将新 Pod 分配到 node2
     最终表现: Pod 处于 Pending 状态，调度事件显示 'node(s) had untolerated taint'


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 42.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5406 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 47.5s
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
| **问题分类** | 节点 Taint 导致不可调度 |
| **置信度** | 高 (95%) |
| **证据完整度** | 6/6 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键发现**：
您的集群存在一个调度问题。一个名为 `l1-test-nginx-6c69dc7c76-67g52` 的 Pod 处于 `Pending` 状态，无法被调度到任何节点。其根本原因是目标节点 `node2` 被设置了一个阻止调度的污点（Taint），而该 Pod 又强制要求调度到该节点。

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `l1-test-nginx-6c69dc7c76-67g52` (Namespace: `aiops-e2e`) |
| Node | `node2` |
| 错误信息 | `0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pods` | `NAMESPACE: aiops-e2e, NAME: l1-test-nginx-6c69dc7c76-67g52, READY: 0/1, STATUS: Pending, AGE: 38m, NODE: <none>` | Pod 处于 Pending 状态，未被调度到任何节点 |
| 2 | Pod 调度事件 | `kubectl describe pod` | `Events: Warning FailedScheduling ... 0/3 nodes are available: 1 node(s) had untolerated taint {test-unschedulable: true}, 2 node(s) didn't match Pod's node affinity/selector` | 调度失败的直接原因：node2 有污点，其他节点不匹配 Pod 选择器 |
| 3 | 节点污点 (Taint) | `kubectl describe node node2` | `Taints: test-unschedulable=true:NoSchedule` | 节点 `node2` 被标记了 `NoSchedule` 污点，阻止新 Pod 调度 |
| 4 | 节点污点详情 | `kubectl get -o yaml node node2` | `spec: taints: - effect: NoSchedule, key: test-unschedulable, value: "true"` | 污点配置明确，键为 `test-unschedulable`，效果为 `NoSchedule` |
| 5 | Pod 节点选择器 | `kubectl get -o yaml pod` | `spec: nodeSelector: kubernetes.io/hostname: node2` | Pod 配置强制要求调度到 `node2`，无法调度到其他节点 |
| 6 | 节点资源状态 | `kubectl describe node node2` | `Allocated resources: cpu 1 (8%), memory 1828375040 (5%)` | 节点资源充足（CPU 8%，内存 5%），排除资源不足问题 |
| 7 | 节点运行状态 | `kubectl describe node node2` | `Conditions: Ready True, MemoryPressure False, DiskPressure False, PIDPressure False` | 节点本身健康（Ready=True），无资源压力 |

### 证据关联分析
- **证据 #2 + #3 + #4 印证**：调度事件报告 `untolerated taint {test-unschedulable: true}`，与节点 `node2` 上存在的 `test-unschedulable=true:NoSchedule` 污点完全匹配。
- **证据 #1 + #5 印证**：Pod 状态为 `Pending` 且 `NODE: <none>`，因为其 `nodeSelector` 强制要求调度到 `node2`，但该节点有污点。
- **证据 #3 + #6 + #7 印证**：节点 `node2` 状态为 `Ready`，资源使用率低，表明污点是人为设置或维护操作，而非节点故障。

### 证据链
```
Pod 配置 nodeSelector 强制调度到 node2 → node2 存在 NoSchedule 污点 → Pod 无法容忍该污点 → 调度器找不到合适节点 → Pod 状态为 Pending
```

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 节点 node2 被标记了污点：test-unschedulable=true:NoSchedule      │
│ (可能是人为维护操作或自动化工具设置)                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 该污点阻止调度器将任何新 Pod 分配到 node2（除非 Pod 有对应容忍） │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod l1-test-nginx-... 配置了 nodeSelector: kubernetes.io/hostname=node2， │
│ 必须调度到 node2，但无法容忍 test-unschedulable 污点              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，事件显示 FailedScheduling                    │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #3、#4（节点 `node2` 存在 `test-unschedulable=true:NoSchedule` 污点）和证据 #5（Pod 强制调度到 `node2`），问题的根本原因是**节点 `node2` 上的污点阻止了具有特定节点选择器的 Pod 调度**。

**置信度**：高 (95%)
- ✅ 证据 #2 调度事件明确指向 `untolerated taint {test-unschedulable: true}`
- ✅ 证据 #3、#4 确认节点 `node2` 上存在该污点
- ✅ 证据 #5 确认 Pod 被强制绑定到 `node2`
- ✅ 证据 #6、#7 排除节点故障或资源不足的可能性

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 移除节点污点（如果维护已完成）**
如果 `node2` 的维护或测试已经完成，应移除污点以恢复其可调度性。
```bash
kubectl taint nodes node2 test-unschedulable-
```
*依据*：污点 `test-unschedulable=true:NoSchedule` 是导致调度的直接障碍。

**2. [可选] 为 Pod 添加污点容忍（如果必须调度到 node2）**
如果 Pod 必须运行在 `node2` 上且污点需要保留，可以修改 Pod 或其控制器（如 Deployment）的配置，添加对应的容忍。
```yaml
# 在 Pod spec 中添加
tolerations:
- key: "test-unschedulable"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```
*目的*：使 Pod 能够容忍该污点并被调度到 `node2`。

**3. [可选] 修改 Pod 的节点选择器（如果节点不固定）**
如果 Pod 不一定非要运行在 `node2` 上，可以移除或修改其 `nodeSelector`，允许调度到其他可用节点。
```bash
# 需要编辑 Deployment 或 Pod 的 YAML 文件，移除或修改 nodeSelector
kubectl edit deployment -n aiops-e2e l1-test-nginx
```
### 后续优化
1.  **污点管理流程**：建立清晰的流程，对生产节点添加/移除污点时进行记录和通知，避免影响业务 Pod 调度。
2.  **Pod 容忍策略**：对于必须运行在特定节点上的系统或中间件 Pod，预先配置好对常见维护污点（如 `node.kubernetes.io/maintenance`）的容忍。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认节点污点已移除 | `kubectl describe node node2 \| grep Taints` | `Taints: <none>` |
| 2. 确认 Pod 状态 | `kubectl get pod -n aiops-e2e l1-test-nginx-6c69dc7c76-67g52` | `STATUS: Running` 或 `ContainerCreating` |
| 3. 确认 Pod 被调度到 node2 | `kubectl get pod -n aiops-e2e l1-test-nginx-6c69dc7c76-67g52 -o wide` | `NODE` 列显示为 `node2` |

---
## ⚠️ 注意事项
- 移除污点前，请确认 `node2` 已准备好接收新工作负载（例如，维护已完成）。
- 如果选择为 Pod 添加容忍，请确保理解其含义：该 Pod 将能够调度到带有此污点的节点上，这可能是在节点处于“测试”或“不可调度”状态时。
- 集群中其他节点（`master`, `node1`）状态均为 `Ready`，整体集群健康。

---

## 📊 性能统计

├─ 总耗时: 4.8m
├─ 问题定位: 43.2s (15%) ✅
├─ 证据链采集: 67.8s (24%) ✅
├─ 根因分析: 73.9s (26%) ✅
├─ 汇总总结: 102.5s (36%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: L1 Node NotReady / Taint 导致不可调度
- **参考 Runbook**: L1 Node NotReady / Taint 导致不可调度
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
