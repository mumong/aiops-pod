======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6de5f1d8361b4aff]

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
  Warning  FailedScheduling  19m (x9 over 59m)  default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          65m   <none>   <none>   
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   230d   v1.26.8  
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   230d   v1.26.8   10.2.0.49     <
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ✅ [问题定位] 完成 (29.5s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[]
   reasoning=当前环境中存在异常 Pod 'rc-pending-nodeselector'，其状态为 'Pending'，异常类型归一化为 'PendingUnschedulable'。根据 runbook 和诊断信息，Pod 调度失败的原因是 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，这表明节点选择器或节点亲和性配置与节点标签不匹配，属于调度层面的问题，因此归类为 L1 层级。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在异常 Pod 'rc-pending-nodeselector'，其状态为 'Pending'，异常类型归一化为 'PendingUnschedulable'。根据 runbook 和诊断信息，Pod 调度失败的原因是 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'，这表明节点选择器或节点亲和性配置与节点标签不匹配，属于调度层面的问题，因此归类为 L1 层级。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                64m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 50%

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
  Warning  FailedScheduling  21m (x9 over 61m)  default-scheduler  0/3 nodes are available: 
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
   💭 [证据链采集] # 证据采集结论

## 已采集证据
1. **kubectl_describe**: Pod `rc-pending-nodeselector` 的 `FailedScheduling` 事件显示：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。表明 Pod 的调度失败是由于节点选择器不匹配。
2. **kubectl_get_yaml**: Pod 的 `nodeSelector` 配置为 `{"aiops.e2e/nonexistent-node-label": "true"}`，但集群中没有任何节点拥有该标签。
3. **kubectl_get_by_kind_in_cluster**: 集群中所有节点的标签均不包含 `aiops.e2e/nonexistent-node-label`，且节点状态为 `Ready`，没有资源不足问题。

## 未采集证据
无

## 冲突证据
无

## 归纳结论
Pod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 配置的标签 `aiops.e2e/nonexistent-node-label` 在集群中不存在，导致没有节点满足调度条件。修复方案是修改 Pod 的 `nodeSelector` 以匹配集群中某个节点的标签，或为某个节点添加该标签。
   ✅ [证据链采集] 完成 (1m 27.9s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细描述信息以验证调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"name":"rc-pending-nodeselector","namespace":"aiops-e2e","kind":"Pod"},"purpose":"验证 Pod 的调度失败原因，查看 FailedScheduling 事件的具体信息","evidence_type":"diagnostic","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的 YAML 配置以检查 nodeSelector/affinity/tolerations 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"name":"rc-pending-nodeselector","namespace":"aiops-e2e","kind":"Pod","output_format":"yaml"},"purpose":"检查 Pod 的 nodeSelector/affinity/tolerations 配置是否与节点标签匹配","evidence_type":"configuration","target_scope":"aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取集群节点信息以检查节点标签和状态是否符合 Pod 调度条件","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","tool_args":{"kind":"Node"},"purpose":"检查集群节点的标签和状态，确认是否满足 Pod 的调度条件","evidence_type":"diagnostic","target_scope":"cluster","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  21m (x9 over 61m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/003-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/003-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6de5f1d8361b4aff/tools/003-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"# 证据采集结论\n\n## 已采集证据\n1. **kubectl_describe**: Pod `rc-pending-nodeselector` 的 `FailedScheduling` 事件显示：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。表明 Pod 的调度失败是由于节点选择器不匹配。\n2. **kubectl_get_yaml**: Pod 的 `nodeSelector` 配置为 `{\"aiops.e2e/nonexistent-node-label\": \"true\"}`，但集群中没有任何节点拥有该标签。\n3. **kubectl_get_by_kind_in_cluster**: 集群中所有节点的标签均不包含 `aiops.e2e/nonexistent-node-label`，且节点状态为 `Ready`，没有资源不足问题。\n\n## 未采集证据\n无\n\n## 冲突证据\n无\n\n## 归纳结论\nPod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 配置的标签 `aiops.e2e/nonexistent-node-label` 在集群中不存在，导致没有节点满足调度条件。修复方案是修改 Pod 的 `nodeSelector` 以匹配集群中某个节点的标签，或为某个节点添加该标签。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细描述信息以验证调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证 Pod 的调度失败原因，查看 FailedScheduling 事件的具体信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的 YAML 配置以检查 nodeSelector/affinity/tolerations 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"检查 Pod 的 nodeSelector/affinity/tolerations 配置是否与节点标签匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取集群节点信息以检查节点标签和状态是否符合 Pod 调度条件","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","purpose":"检查集群节点的标签和状态，确认是否满足 Pod 的调度条件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细描述信息以验证调度失败原因 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 获取异常 Pod 的 YAML 配置以检查 nodeSelector/affinity/t... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_by_kind_in_cl... | 获取集群节点信息以检查节点标签和状态是否符合 Pod 调度条件 | `kubectl get nodes -o wide` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (37.4s)
   📤 → 下游数据: root_cause=Pod `rc-pending-nodeselector` 的 `nodeSelector` 配置的标签 `aiops.e2e/nonexistent-node-label` 在集群中不存在，导致没有节点满足调度条件。
   confidence=90%
   causal_chain={"root_cause": "Pod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 配置的标签 `aiops.e2e/nonexistent-node-label` 在集群中不存在，导致没有节点满足调度条件。", "direct_cause": "Pod 的 `nodeSelector` 配置为 `\"aiops.e2e/nonexistent-node-label\": \"true\"`，但集群中没有任何节点拥有该标签。", "symptom": "Pod `rc-pending-nodeselector` 的状态为 `Pending`，调度失败。"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "获取异常 Pod 的详细描述信息以验证调度失败原因"}, {"e2": "获取异常 Pod 的 YAML 配置以检查 nodeSelector/affinity/tolerations 配置"}, {"e3": "获取集群节点信息以检查节点标签和状态是否符合 Pod 调度条件"}, {"layer_1": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}, {"layer_2": "上游已验证工具结果: kubectl_describe"}, {"layer_3": "上游已验证工具结果: kubectl_get_by_name"}, {"layer_4": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}, {"layer_5": "上游已验证工具结果: kubectl_get_by_name"}, {"layer_6": "上游已验证工具结果: kubectl_get_by_name"}], "evidence_analysis": [{"e1": "Pod `rc-pending-nodeselector` 的 `FailedScheduling` 事件显示：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。表明 Pod 的调度失败是由于节点选择器不匹配。"}, {"e2": "Pod 的 `nodeSelector` 配置为 `\"aiops.e2e/nonexistent-node-label\": \"true\"`，但集群中没有任何节点拥有该标签。"}, {"e3": "集群中所有节点的标签均不包含 `aiops.e2e/nonexistent-node-label`，且节点状态为 `Ready`，没有资源不足问题。"}], "causal_chain": {"root_cause": "Pod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 配置的标签 `aiops.e2e/nonexistent-node-label` 在集群中不存在，导致没有节点满足调度条件。", "direct_cause": "Pod 的 `nodeSelector` 配置为 `\"aiops.e2e/nonexistent-node-label\": \"true\"`，但集群中没有任何节点拥有该标签。", "symptom": "Pod `rc-pending-nodeselector` 的状态为 `Pending`，调度失败。"}, "root_cause": "Pod `rc-pending-nodeselector` 的 `nodeSelector` 配置的标签 `aiops.e2e/nonexistent-node-label` 在集群中不存在，导致没有节点满足调度条件。", "root_cause_summary": "Pod `rc-pending-nodeselector` 的 `nodeSelector` 配置的标签 `aiops.e2e/nonexistent-node-label` 在集群中不存在，导致没有节点满足调度条件。", "confidence": 0.9, "confidence_reason": "有直接证据表明 Pod 的调度失败是由于节点选择器不匹配。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "未发现其他可能影响 Pod 调度的因素。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod `rc-pending-nodeselector` 的 `nodeSelector` 配置的标签 `aiops.e2e/nonexistent-node-label` 在集群中不存在，导致没有节点满足调度条件。
   置信度: 90%
   🔗 因果链:
     根本原因: Pod `rc-pending-nodeselector` 无法调度的根本原因是其 `nodeSelector` 配置的标签 `aiops.e2e/nonexistent-node-label` 在集群中不存在，导致没有节点满足调度条件。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 35.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4111 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 10.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | PendingUnschedulable |
| **兼容归因层** | L1 - 调度问题 |
| **问题分类** | 调度失败（NodeSelector/NodeAffinity 不匹配） |
| **置信度** | 高 (90%) |
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
| 错误信息 | 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector |

**集群状态**：
- 1 个 Pod 处于 `Pending` 状态
- 46 个 Pod 处于 `Running` 状态
- 3 个节点（master、node1、node2）均处于 `Ready` 状态

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl describe pod rc-pending-nodeselector | `Warning  FailedScheduling  19m (x9 over 59m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | Pod 无法调度，因为节点选择器不匹配 |
| 2 | Pod YAML 配置 | kubectl get pod rc-pending-nodeselector -o yaml | `nodeSelector: { "aiops.e2e/nonexistent-node-label": "true" }` | Pod 的 nodeSelector 指定了不存在的节点标签 |
| 3 | 节点标签 | kubectl get nodes | `node1: beta.kubernetes.io/arch=amd64, kubernetes.io/os=linux` | 集群节点上不存在标签 `aiops.e2e/nonexistent-node-label` |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 的 `nodeSelector` 指定了不存在的标签，导致所有节点均不满足调度条件
- **证据链**：Pod 指定了不存在的标签 → 调度器找不到满足条件的节点 → Pod 无法调度 → 状态为 `Pending`

### 缺失证据（无）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 证据完整度为 100%，无需补充 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod rc-pending-nodeselector 的 nodeSelector 指定了不存在的标签 "aiops.e2e/nonexistent-node-label" |
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器无法找到满足 nodeSelector 条件的节点                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度失败，Pod 无法被调度到任何节点                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-pending-nodeselector 状态为 Pending，持续无法调度        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (FailedScheduling 事件) 和证据 #2 (nodeSelector 配置)，
问题的根本原因是**Pod 的 nodeSelector 指定了不存在的标签 "aiops.e2e/nonexistent-node-label"**，
导致调度器无法找到满足条件的节点。
**置信度**：高 (90%)
- ✅ kubectl describe 明确指出调度失败原因
- ✅ kubectl get pod -o yaml 显示 nodeSelector 配置错误
- ✅ kubectl get nodes 证明节点上不存在该标签

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修复 Pod 的 nodeSelector 配置**
```bash
kubectl patch pod rc-pending-nodeselector -n aiops-e2e -p '{"spec":{"nodeSelector":{}}}' --type=merge
```
*依据*：移除错误的 nodeSelector 配置，让调度器可以使用默认策略调度

**2. [可选] 删除并重新创建 Pod**
```bash
kubectl delete pod rc-pending-nodeselector -n aiops-e2e
```
*目的*：触发调度器重新尝试调度

**3. [可选] 添加正确的节点标签**
```bash
kubectl label nodes node1 aiops.e2e/nonexistent-node-label=true
```
*目的*：如果 nodeSelector 是有意设置的，则添加标签以满足调度条件

### 后续优化
1. **验证标签一致性**：确保 Pod 的 nodeSelector/tolerations 与节点标签/污点匹配
2. **配置默认调度策略**：避免过度依赖 nodeSelector，可使用 nodeAffinity 提供更灵活的调度规则
3. **监控调度事件**：配置 Prometheus 或 Event Watcher 监控调度失败事件

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 被调度 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查 Pod 所在节点 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o jsonpath='{.spec.nodeName}'` | 返回具体节点名（如 node1） |
| 3. 检查事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |

---
## ⚠️ 注意事项
- 如果 nodeSelector 是有意设置的，需确保集群中有节点拥有该标签
- 如果集群中节点标签频繁变更，建议使用 nodeAffinity 替代 nodeSelector 以提高灵活性
- 可配置调度器容忍策略（Tolerations）配合节点污点（Taints）进一步控制调度行为

---

## 📊 性能统计

├─ 总耗时: 4.2m
├─ 问题定位: 29.5s (12%) ✅
├─ 证据链采集: 87.9s (35%) ✅
├─ 根因分析: 37.4s (15%) ✅
├─ 汇总总结: 95.7s (38%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
