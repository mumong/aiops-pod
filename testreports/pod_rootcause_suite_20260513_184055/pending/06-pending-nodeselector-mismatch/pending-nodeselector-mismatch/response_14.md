======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1744c1abc96f4cbb]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS      
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  35m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          35m   <none>   <none>   
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-13T20:39:53Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，调度失败原因明确指向 nodeSelector 不匹配。Pod 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label': 'true'，而集群中所有节点均未配置该标签，导致调度器无法找到匹配节点。此问题属于调度约束不匹配，归类为 L1 层级。当前无其他异常类型干扰。",
  "abnormal_pods": [
    {
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "Unschedulable",
      "message": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..",
      "key_events": [
        {
          "type": "Warning",
          "reason": "FailedScheduling",
          "message": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."
        }
      ]
    }
  ],
  "abnormal_groups": {
    "PendingUnschedulable": 1
  },
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "scheduling",
  "key_entities": [
    {
      "type": "Pod",
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
      "labels": {
        "app": "rc-pending-nodeselector",
        "pod_abnormal_type": "PendingUnschedulable"
      }
    },
    {
      "type": "Node",
      "name": "master",
      "labels": {
        "beta.kubernetes.io/arch": "amd64",
        "beta.kubernetes.io/os": "linux",
        "kubernetes.io/arch": "amd64",
        "kubernetes.io/hostname": "master",
        "kubernetes.io/os": "linux",
        "node-role.kubernetes.io/control-plane": "",
        "node.kubernetes.io/exclude-from-external-load-balancers": ""
      }
    },
    {
      "type": "Node",
      "name": "node1",
      "labels": {
        "beta.kubernetes.io/arch": "amd64",
        "beta.kubernetes.io/os": "linux",
        "kubernetes.io/arch": "amd64",
        "kubernetes.io/hostname": "node1",
        "kubernetes.io/os": "linux"
      }
    },
    {
      "type": "Node",
      "name": "node2",
      "labels": {
        "beta.kubernetes.io/arch": "amd64",
        "beta.kubernetes.io/os": "linux",
        "kubernetes.io/arch": "amd64",
        "kubernetes.io/hostname": "node2",
        "kubernetes.io/os": "linux"
      }
    }
  ],
  "possible_scenarios": [
    {
      "scenario": "Pod 的 nodeSelector 指定的标签 'aiops.e2e/nonexistent-node-label': 'true' 在所有节点上均不存在，导致调度失败。",
      "evidence": [
        {
          "source": "kubectl describe pod rc-pending-nodeselector -n aiops-e2e",
          "key_line": "3 node(s) didn't match Pod's node affinity/selector"
        },
        {
          "source": "kubectl get node master -o jsonpath='{.metadata.labels}'",
          "key_line": "No 'aiops.e2e/nonexistent-node-label' label found"
        }
      ]
    }
  ]
}
   ✅ [问题定位] 完成 (1m 8.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[]
   reasoning=Pod 'rc-pending-nodeselector' 处于 Pending 状态，调度失败原因明确指向 nodeSelector 不匹配。Pod 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label': 'true'，而集群中所有节点均未配置该标签，导致调度器无法找到匹配节点。此问题属于调度约束不匹配，归类为 L1 层级。当前无其他异常类型干扰。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，调度失败原因明确指向 nodeSelector 不匹配。Pod 的 nodeSelector 指定了不存在的标签 'aiops.e2e/nonexistent-node-label': 'true'，而集群中所有节点均未配置该标签，导致调度器无法找到匹配节点。此问题属于调度约束不匹配，归类为 L1 层级。当前无其他异常类型干扰。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                35m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  37m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-13T20:39:53Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] ### 采集证据总结

#### 已采集证据
1. **Pod 的调度失败事件**：
   - `kubectl describe pod` 显示 Pod 处于 `Pending` 状态，且多次出现 `FailedScheduling` 事件，明确指出原因：`3 node(s) didn't match Pod's node affinity/selector`。
   - 事件中还提到 `Preemption is not helpful for scheduling`，说明调度器尝试抢占资源失败。

2. **Pod 的 nodeSelector 配置**：
   - `kubectl get pod -o yaml` 显示 Pod 的 `nodeSelector` 设置为 `{"aiops.e2.e/nonexistent-node-label": "true"}`，表明它要求节点必须有标签 `aiops.e2.e/nonexistent-node-label` 且值为 `true`。

3. **集群节点的标签**：
   - `kubectl get nodes` 显示集群中的三个节点（master、node1、node2）均未配置标签 `aiops.e2.e/nonexistent-node-label`，因此无法满足 Pod 的调度约束。

#### 未采集证据
- 无进一步的证据需要采集，当前已确认调度失败的根本原因是 nodeSelector 不匹配。

#### 冲突证据
- 无冲突证据。

### 诊断结论
当前 Pod `rc-pending-nodeselector` 处于 `Pending` 状态，调度失败的原因是其 `nodeSelector` 指定了一个不存在的标签 `aiops.e2.e/nonexistent-node-label`，而集群中所有节点均未配置该标签，导致调度器无法找到匹配的节点。此问题属于调度约束不匹配，归类为 L1 层级。建议检查 Pod 的 `nodeSelector` 配置并确保其与集群节点的标签匹配。
   ✅ [证据链采集] 完成 (1m 28.8s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-nodeselector","kind":"Pod"},"purpose":"检查 Pod 的 FailedScheduling 事件，确认调度失败的具体原因","evidence_type":"事件","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"检查 Pod 'rc-pending-nodeselector' 的 nodeSelector 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-nodeselector","kind":"Pod"},"purpose":"验证 Pod 的 nodeSelector 配置，确认其调度约束是否与集群节点匹配","evidence_type":"配置","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"检查集群节点的标签匹配情况","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{},"purpose":"确认集群节点的标签是否与 Pod 'rc-pending-nodeselector' 的 nodeSelector 匹配","evidence_type":"配置","target_scope":"Node/All","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  37m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  22m (x3 over 32m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/003-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/003-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1744c1abc96f4cbb/tools/003-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"### 采集证据总结\n\n#### 已采集证据\n1. **Pod 的调度失败事件**：\n   - `kubectl describe pod` 显示 Pod 处于 `Pending` 状态，且多次出现 `FailedScheduling` 事件，明确指出原因：`3 node(s) didn't match Pod's node affinity/selector`。\n   - 事件中还提到 `Preemption is not helpful for scheduling`，说明调度器尝试抢占资源失败。\n\n2. **Pod 的 nodeSelector 配置**：\n   - `kubectl get pod -o yaml` 显示 Pod 的 `nodeSelector` 设置为 `{\"aiops.e2.e/nonexistent-node-label\": \"true\"}`，表明它要求节点必须有标签 `aiops.e2.e/nonexistent-node-label` 且值为 `true`。\n\n3. **集群节点的标签**：\n   - `kubectl get nodes` 显示集群中的三个节点（master、node1、node2）均未配置标签 `aiops.e2.e/nonexistent-node-label`，因此无法满足 Pod 的调度约束。\n\n#### 未采集证据\n- 无进一步的证据需要采集，当前已确认调度失败的根本原因是 nodeSelector 不匹配。\n\n#### 冲突证据\n- 无冲突证据。\n\n### 诊断结论\n当前 Pod `rc-pending-nodeselector` 处于 `Pending` 状态，调度失败的原因是其 `nodeSelector` 指定了一个不存在的标签 `aiops.e2.e/nonexistent-node-label`，而集群中所有节点均未配置该标签，导致调度器无法找到匹配的节点。此问题属于调度约束不匹配，归类为 L1 层级。建议检查 Pod 的 `nodeSelector` 配置并确保其与集群节点的标签匹配。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"检查 Pod 的 FailedScheduling 事件，确认调度失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查 Pod 'rc-pending-nodeselector' 的 nodeSelector 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证 Pod 的 nodeSelector 配置，确认其调度约束是否与集群节点匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查集群节点的标签匹配情况","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"确认集群节点的标签是否与 Pod 'rc-pending-nodeselector' 的 nodeSelector 匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod 'rc-pending-nodeselector' 的调度失败原因 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 检查 Pod 'rc-pending-nodeselector' 的 nodeSelect... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_by_kind_in_cl... | 检查集群节点的标签匹配情况 | `kubectl get nodes -o json` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 53.3s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了一个不存在的标签 'aiops.e2.e/nonexistent-node-label'，导致调度失败。集群中的三个节点（master、node1、node2）均未配置该标签，因此无法满足 Pod 的调度约束。
   confidence=95%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了一个不存在的标签 aiops.e2.e/nonexistent-node-label，导致调度失败。", "intermediate_causes": ["调度器无法找到匹配的节点，因为所有节点均未配置该标签。", "Pod 的 nodeSelector 设置为 {'aiops.e2.e/nonexistent-node-label': 'true'}，导致调度器无法找到匹配的节点。"], "immediate_effects": ["Pod 'rc-pending-nodeselector' 处于 Pending 状态。", "调度器多次尝试调度失败，导致 FailedScheduling 事件。"]}
   rca_analysis={"phenomenon": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，调度失败。", "evidence_inventory": [{"description": "验证 Pod 'rc-pending-nodeselector' 的调度失败原因", "level": "critical", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  37m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  22m (x3 over 32m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 node"}, {"description": "检查 Pod 'rc-pending-nodeselector' 的 nodeSelector 配置", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"description": "检查集群节点的标签匹配情况", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}], "evidence_analysis": [{"description": "Pod 的调度失败事件", "level": "critical", "value": "Pod 'rc-pending-nodeselector' 处于 Pending 状态，且多次出现 FailedScheduling 事件，明确指出原因：3 node(s) didn't match Pod's node affinity/selector。"}, {"description": "Pod 的 nodeSelector 配置", "level": "important", "value": "Pod 的 nodeSelector 设置为 {'aiops.e2.e/nonexistent-node-label': 'true'}，表明它要求节点必须有标签 aiops.e2.e/nonexistent-node-label 且值为 true。"}, {"description": "集群节点的标签", "level": "important", "value": "集群中的三个节点（master、node1、node2）均未配置标签 aiops.e2.e/nonexistent-node-label，因此无法满足 Pod 的调度约束。"}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了一个不存在的标签 aiops.e2.e/nonexistent-node-label，导致调度失败。", "intermediate_causes": ["调度器无法找到匹配的节点，因为所有节点均未配置该标签。", "Pod 的 nodeSelector 设置为 {'aiops.e2.e/nonexistent-node-label': 'true'}，导致调度器无法找到匹配的节点。"], "immediate_effects": ["Pod 'rc-pending-nodeselector' 处于 Pending 状态。", "调度器多次尝试调度失败，导致 FailedScheduling 事件。"]}, "root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了一个不存在的标签 'aiops.e2.e/nonexistent-node-label'，导致调度失败。集群中的三个节点（master、node1、node2）均未配置该标签，因此无法满足 Pod 的调度约束。", "root_cause_summary": "Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了一个不存在的标签 'aiops.e2.e/nonexistent-node-label'，导致调度失败。集群中的三个节点（master、node1、node2）均未配置该标签，因此无法满足 Pod 的调度约束。", "confidence": 0.95, "confidence_reason": "有直接证据表明调度失败的原因是 nodeSelector 不匹配。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "当前 Pod 'rc-pending-nodeselector' 处于 'Pending' 状态，调度失败的原因是其 'nodeSelector' 指定了一个不存在的标签 'aiops.e2.e/nonexistent-node-label'，而集群中所有节点均未配置该标签，导致调度器无法找到匹配的节点。此问题属于调度约束不匹配，归类为 L1 层级。建议检查 Pod 的 'nodeSelector' 配置并确保其与集群节点的标签匹配。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了一个不存在的标签 'aiops.e2.e/nonexistent-node-label'，导致调度失败。集群中的三个节点（master、node1、node2）均未配置该标签，因此无法满足 Pod 的调度...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' 的 nodeSelector 指定了一个不存在的标签 aiops.e2.e/nonexistent-node-label，导致调度失败。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 17.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4525 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 47.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | PendingUnschedulable |
| **兼容归因层** | L1 |
| **问题分类** | 调度失败（nodeSelector 不匹配） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| Node | <none> |
| 错误信息 | nodeSelector 不匹配 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 调度失败事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | `Warning  FailedScheduling  35m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | Pod 无法匹配任何节点的标签 |
| 2 | Pod 的 nodeSelector 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 指定了不存在的标签 |
| 3 | 节点标签信息 | `kubectl get nodes -o wide` | `所有节点未配置 aiops.e2e/nonexistent-node-label 标签` | 节点无匹配标签，无法调度 |

### 证据关联分析

- **证据 #1 + #2 印证**：调度失败事件明确指出 `nodeSelector` 不匹配，而 `nodeSelector` 中的 `aiops.e2e/nonexistent-node-label: "true"` 是不存在的标签。
- **证据链**：Pod 指定了不存在的标签 → 节点无此标签 → 调度器找不到匹配节点 → Pod 处于 Pending 状态。

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                     │
│ Pod 指定了不存在的标签 aiops.e2e/nonexistent-node-label: "true"，导致调度失败 │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                     │
│ 调度器无法找到具有该标签的节点，无法完成调度                                 │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                     │
│ 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                 │
│ Pod 状态为 Pending，事件显示调度失败                                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (FailedScheduling 事件)、证据 #2 (Pod nodeSelector 配置) 和证据 #3 (节点无匹配标签)，问题的根本原因是 **Pod 的 nodeSelector 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label: "true"`**，导致调度器无法找到匹配节点，Pod 处于 Pending 状态。

**置信度**：高 (95%)
- ✅ FailedScheduling 事件明确指出 nodeSelector 不匹配
- ✅ Pod nodeSelector 配置中存在不存在的标签
- ✅ 节点无该标签
- ✅ 无缺失证据影响结论

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 移除或修改 Pod 的 nodeSelector 配置**

```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```

*操作步骤*：
- 删除或修改 `nodeSelector` 字段中的 `aiops.e2e/nonexistent-node-label: "true"`。
- 保存并退出，Kubernetes 将尝试重新调度 Pod。

**2. [可选] 添加缺失的标签到节点（如果应用需要特定节点）**

```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```

*操作步骤*：
- 将 `<node-name>` 替换为实际节点名称，例如 `master`、`node1` 或 `node2`。
- 添加该标签后，Pod 将可以调度到该节点。

### 后续优化

1. **校验标签策略**：确保所有 nodeSelector 使用的标签都已在节点上配置。
2. **使用 node affinity 替代 nodeSelector**（如果需要更灵活的调度策略）。
3. **监控调度事件**：配置告警，当 Pod 调度失败时立即通知。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否调度成功 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查节点标签 | `kubectl get nodes --show-labels` | 包含 `aiops.e2e/nonexistent-node-label=true`（如果添加了标签） |
| 3. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |

---

## ⚠️ 注意事项

- 如果 Pod 是通过 Deployment 或 ReplicaSet 创建的，修改 Pod 的 nodeSelector 无效。应修改 Deployment/ReplicaSet 的模板部分。
- 添加标签后，建议使用 `kubectl get nodes` 确认标签是否成功应用。
- 如果使用的是 Kubernetes 1.26+，可以考虑使用 `node affinity` 替代 `nodeSelector` 以获得更灵活的调度策略。

---

## 📄 附加信息

- **受影响的 Pod**：`rc-pending-nodeselector`（Namespace: `aiops-e2e`）
- **受影响的节点**：无（所有节点均未配置该标签）
- **相关事件**：`FailedScheduling`（多次重复）

---

## 📌 诊断结论

**当前问题总结**：  
集群中存在一个 Pod（`rc-pending-nodeselector`）因 nodeSelector 配置错误导致调度失败。该 Pod 指定了一个不存在的标签，而集群中所有节点均未配置该标签，因此无法调度。

**建议操作**：  
- 优先修改或删除 Pod 的 nodeSelector 配置。
- 可选地，如果应用需要特定节点，可添加该标签到目标节点。

**修复后预期效果**：  
Pod 将能够被调度到匹配节点并进入 Running 状态。

---

## 📊 性能统计

├─ 总耗时: 5.8m
├─ 问题定位: 68.1s (20%) ✅
├─ 证据链采集: 88.8s (26%) ✅
├─ 根因分析: 113.3s (33%) ✅
├─ 汇总总结: 77.3s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
