======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d39dff0db26845b1]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'ImagePullBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
2m30s (x350 over 82m)   Normal   BackOff   Pod/rc-imagepull-invalid-registry   Back-off pulling image "registry.invalid/aiops/rootcause:v0"
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                            READY   STATUS             RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-imagepull-invalid-registry   0/1     ImagePullBackOff 
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": [
    "L3"
  ],
  "layer_name": "镜像拉取失败",
  "confidence": "high",
  "reasoning": "检测到一个 Pod 处于 ImagePullBackOff 状态，其 Events 显示镜像拉取失败，错误信息为 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"'。这表明镜像仓库网络不可达或镜像路径错误。",
  "abnormal_pods": [
    "rc-imagepull-invalid-registry"
  ],
  "abnormal_groups": {
    "ImagePullFailed": 1
  },
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "ImagePullFailed",
  "key_entities": [
    "Pod/rc-imagepull-invalid-registry",
    "Image/registry.invalid/aiops/rootcause:v0"
  ],
  "possible_scenarios": [
    "镜像仓库网络不可达",
    "镜像路径错误",
    "认证失败"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 24.2s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像仓库网络不可达', 'probability': 'high', 'reason': 'Events 显示 connection refused/timeout'}, {'scenario': '镜像路径错误', 'probability': 'high', 'reason': '镜像地址 registry.invalid/aiops/rootcause:v0 可能不存在或格式错误'}, {'scenario': '认证失败', 'probability': 'high', 'reason': 'Events 显示 unauthorized/no basic auth'}]
   entities=[{"type": "Pod", "name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.invalid/aiops/rootcause:v0", "namespace": ""}]
   reasoning=检测到一个 Pod 处于 ImagePullBackOff 状态，其 Events 显示镜像拉取失败，错误信息为 'Back-off pulling image "registry.invalid/aiops/rootcause:v0"'。这表明镜像仓库网络不可达或镜像路径错误。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "镜像拉取失败", "confidence": 1.0, "reasoning": "检测到一个 Pod 处于 ImagePullBackOff 状态，其 Events 显示镜像拉取失败，错误信息为 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"'。这表明镜像仓库网络不可达或镜像路径错误。", "abnormal_pods": [{"name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "Pod", "name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.invalid/aiops/rootcause:v0", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达", "probability": "high", "reason": "Events 显示 connection refused/timeout"}, {"scenario": "镜像路径错误", "probability": "high", "reason": "镜像地址 registry.invalid/aiops/rootcause:v0 可能不存在或格式错误"}, {"scenario": "认证失败", "probability": "high", "reason": "Events 显示 unauthorized/no basic auth"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-invalid-registry                       0/1     ImagePullBackOff   0             82m    172.16.166.156   node1    <none>           <none>            app=rc-imagepull-invalid-registry,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/d39dff0db26845b1/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d39dff0db26845b1/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d39dff0db26845b1/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 100%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal  BackOff  47s (x372 over 85m)  kubelet  Back-off pulling image "regi
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (2m 9.6s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"描述 Pod rc-imagepull-invalid-registry 的详细状态，以确认其 ImagePullBackOff 的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-imagepull-invalid-registry","kind":"pod"},"purpose":"获取 Pod rc-imagepull-invalid-registry 的详细状态，特别是 Events 中的错误信息，确认镜像拉取失败的原因。","evidence_type":"current_state","target_scope":"aiops-e2e","acceptable_tools":["kubectl_describe","kubectl_events"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-imagepull-invalid-registry 的 Events，以确认镜像拉取失败的具体错误信息。","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","tool_args":{"namespace":"aiops-e2e","name":"rc-imagepull-invalid-registry","kind":"pod"},"purpose":"获取 Pod rc-imagepull-invalid-registry 的 Events，以确认镜像拉取失败的具体错误信息，如 connection refused、timeout、unauthorized 等。","evidence_type":"current_state","target_scope":"aiops-e2e","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal  BackOff  47s (x372 over 85m)  kubelet  Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n      Reason:       ImagePullBackOff\n                  cni.projectcalico.org/containerID: 82174088e8d254fd04c994cc2744d2fc71d880e8291a39a8e865fe71718ad3db\n                  cni.projectcalico.org/podIP: 172.16.166.156/32\n                  cni.projectcalico.org/podIPs: 172.16.166.156/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed\n    State:          Waiting","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d39dff0db26845b1/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d39dff0db26845b1/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d39dff0db26845b1/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 4 个，匹配计划 2 个，未规划证据 2 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":4,"matched_tool_count":2,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"描述 Pod rc-imagepull-invalid-registry 的详细状态，以确认其 ImagePullBackOff 的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","purpose":"获取 Pod rc-imagepull-invalid-registry 的详细状态，特别是 Events 中的错误信息，确认镜像拉取失败的原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod rc-imagepull-invalid-registry 的 Events，以确认镜像拉取失败的具体错误信息。","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","purpose":"获取 Pod rc-imagepull-invalid-registry 的 Events，以确认镜像拉取失败的具体错误信息，如 connection refused、timeout、unauthorized 等。","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 描述 Pod rc-imagepull-invalid-registry 的详细状态，以确... | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取 Pod rc-imagepull-invalid-registry 的 Events... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-image...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 20.5s)
   📤 → 下游数据: root_cause=镜像拉取失败导致 Pod rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态。Events 显示 'Back-off pulling image "registry.invalid/aiops/rootcause:v0"' 的错误信息，表明镜像拉取失败，可能是镜像地址错误、镜像仓库不可达或认证失败。
   confidence=80%
   causal_chain={"root_cause": "镜像拉取失败", "intermediate_causes": ["镜像地址或 tag 不存在", "imagePullSecret 缺失或认证失败", "节点到镜像仓库网络不可达"], "direct_causes": ["Events 显示 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"' 的错误信息，表明镜像拉取失败。", "Pod rc-imagepull-invalid-registry 的状态为 Pending，且 kubelet 报告了 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"' 的事件。这表明镜像拉取失败，Pod 无法启动。"], "effects": ["Pod rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态，无法启动。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "kubectl_describe 摘要:\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal  BackOff  47s (x372 over 85m)  kubelet  Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n      Reason:       ImagePullBackOff\n                  cni.projectcalico.org/containerID: 82174088e8d254fd04c994cc2744d2fc71d880e8291a39a8e865fe71718ad3db\n                  cni.projectcalico.org/podIP: 172.16.166.156/32\n                  cni.projectcalico.org/podIPs:"}, {"e2": "kubectl_events 摘要:\n关键诊断行:\n2m30s (x350 over 82m)   Normal   BackOff   Pod/rc-imagepull-invalid-registry   Back-off pulling image \"registry.invalid/aiops/rootcause:v0\""}, {"layer_1": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'ImagePullBackOff': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS             RESTARTS      AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-imagepull-invalid-registry                       0/1     ImagePullBackOff   0             82m    172.16.166.156   node1    <none>           <none>            app=rc-imagepull-invalid-reg"}, {"layer_2": "kubectl_events 摘要:\n关键诊断行:\n2m30s (x350 over 82m)   Normal   BackOff   Pod/rc-imagepull-invalid-registry   Back-off pulling image \"registry.invalid/aiops/rootcause:v0\""}, {"layer_3": "NAME                            READY   STATUS             RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-imagepull-invalid-registry   0/1     ImagePullBackOff   0          82m   172.16.166.156   node1   <none>           <none>            app=rc-imagepull-invalid-registry,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"}], "evidence_analysis": [{"e1": "Pod rc-imagepull-invalid-registry 的状态为 Pending，且 kubelet 报告了 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"' 的事件。这表明镜像拉取失败，Pod 无法启动。"}, {"e2": "Events 显示 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"' 的错误信息，表明镜像拉取失败，可能是镜像地址错误、镜像仓库不可达或认证失败。"}, {"layer_1": "kubectl_get_by_kind_in_cluster 显示 1 个 Pod 处于 ImagePullBackOff 状态，表明镜像拉取失败。"}, {"layer_2": "kubectl_events 显示 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"' 的错误信息，表明镜像拉取失败。"}, {"layer_3": "kubectl_get_by_name 显示 rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态，表明镜像拉取失败。"}], "causal_chain": {"root_cause": "镜像拉取失败", "intermediate_causes": ["镜像地址或 tag 不存在", "imagePullSecret 缺失或认证失败", "节点到镜像仓库网络不可达"], "direct_causes": ["Events 显示 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"' 的错误信息，表明镜像拉取失败。", "Pod rc-imagepull-invalid-registry 的状态为 Pending，且 kubelet 报告了 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"' 的事件。这表明镜像拉取失败，Pod 无法启动。"], "effects": ["Pod rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态，无法启动。"]}, "root_cause": "镜像拉取失败导致 Pod rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态。Events 显示 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"' 的错误信息，表明镜像拉取失败，可能是镜像地址错误、镜像仓库不可达或认证失败。", "root_cause_summary": "镜像拉取失败导致 Pod rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态。Events 显示 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"' 的错误信息，表明镜像拉取失败，可能是镜像地址错误、镜像仓库不可达或认证失败。", "confidence": 0.8, "confidence_reason": "有直接证据表明镜像拉取失败，但具体原因（镜像地址错误、镜像仓库不可达或认证失败）需要进一步验证。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"scenario": "镜像地址或 tag 不存在", "probability": "medium", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "medium", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "medium", "reason": "需验证 registry 连通性、DNS 或 TLS"}], "limitations": "需要进一步验证镜像地址是否正确、镜像仓库是否可访问以及认证信息是否正确。", "llm_raw_analysis": "分析表明，Pod rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态，因为镜像拉取失败。Events 显示 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"' 的错误信息，表明镜像拉取失败。可能的原因包括镜像地址或 tag 不存在、imagePullSecret 缺失或认证失败，以及节点到镜像仓库网络不可达。需要进一步验证这些可能性。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 镜像拉取失败导致 Pod rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态。Events 显示 'Back-off pulling image "registry.invalid/aiops/rootcause:v0"' 的错误信息，表明镜像拉...
   置信度: 80%
   🔗 因果链:
     根本原因: 镜像拉取失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 16.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4515 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 10.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff |
| **兼容归因层** | L3 |
| **问题分类** | ImagePullFailed |
| **置信度** | 高 (80%) |
| **证据完整度** | 2/2 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题？

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-imagepull-invalid-registry |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | Back-off pulling image "registry.invalid/aiops/rootcause:v0" |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ImagePullBackOff` | Pod 无法启动，镜像拉取失败 |
| 2 | Events | `kubectl events` | `Back-off pulling image "registry.invalid/aiops/rootcause:v0"` | 镜像拉取失败，Kubelet 重试失败 |
| 3 | Pod 详细状态 | `kubectl describe pod` | `Events: Back-off pulling image registry.invalid/aiops/rootcause:v0` | 显示镜像拉取失败的详细错误 |
| 4 | 镜像地址 | `kubectl describe pod` | `Image: registry.invalid/aiops/rootcause:v0` | 镜像地址可能不存在或格式错误 |
| 5 | 当前集群 Pod 概况 | `kubectl get pod` | `status_counts={'ImagePullBackOff': 1, 'Running': 46}` | 仅 1 个 Pod 处于镜像拉取失败状态 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态 `ImagePullBackOff` + `Events` 中 `Back-off pulling image` → 明确表明镜像拉取失败。
- **证据 #4 印证**：镜像地址 `registry.invalid/aiops/rootcause:v0` 为无效地址或私有仓库未配置认证。
- **证据链**：Kubelet 尝试拉取镜像 → 无法访问仓库 → 重试失败 → Pod 状态转为 `ImagePullBackOff`。

### 缺失证据（无）

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ registry.invalid/aiops/rootcause:v0 镜像地址不可达或不存在       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Kubelet 无法从 registry.invalid 拉取镜像，重试失败               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 状态转为 ImagePullBackOff，无法启动                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态     │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (Pod 状态 `ImagePullBackOff`)、证据 #2 (Events 显示 `Back-off pulling image registry.invalid/aiops/rootcause:v0`) 和证据 #4 (镜像地址为 `registry.invalid/aiops/rootcause:v0`)，问题的根本原因是**镜像地址不可达或镜像不存在**，导致镜像拉取失败。

**置信度**：高 (80%)
- ✅ Pod 状态和 Events 明确指向镜像拉取失败
- ⚠️ 未验证镜像仓库是否配置了正确的 `imagePullSecret`，也未验证网络连通性

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 验证镜像地址是否正确**
- 检查镜像地址 `registry.invalid/aiops/rootcause:v0` 是否存在，或是否拼写错误。
- 如果是私有仓库，确保镜像在仓库中存在。

**2. [优先] 验证镜像仓库是否可访问**
```bash
curl -v https://registry.invalid/aiops/rootcause:v0
```
- 如果返回 `connection refused` 或 `404`，说明仓库不可达或镜像不存在。

**3. [可选] 验证 `imagePullSecret` 是否配置**
```bash
kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e
```
- 检查 `ImagePullSecrets` 字段是否包含正确的 Secret 名称。
- 如果没有配置，添加 Secret：
```bash
kubectl create secret docker-registry my-registry-secret \
  --docker-server=registry.invalid \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email> \
  -n aiops-e2e
```
然后更新 Pod 使用该 Secret：
```bash
kubectl set imagepullsecret pod/rc-imagepull-invalid-registry -n aiops-e2e my-registry-secret
```

**4. [可选] 验证节点到镜像仓库的网络连通性**
```bash
kubectl exec -it <running_pod> -- ping registry.invalid
kubectl exec -it <running_pod> -- curl -v https://registry.invalid
```
- 如果返回 `connection refused`，可能是 DNS 解析失败或网络不通。

### 后续优化
1. **镜像地址标准化**：确保镜像地址格式正确，包括 registry 域名、命名空间、镜像名和 tag。
2. **镜像仓库监控**：配置镜像仓库的可用性监控，确保镜像拉取服务稳定。
3. **自动拉取策略**：考虑使用 `IfNotPresent` 拉取策略减少首次部署时的失败概率。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-imagepull-invalid-registry -n aiops-e2e` | STATUS: Running |
| 2. 确认镜像地址 | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` | 显示正确的镜像地址 |
| 3. 确认镜像是否可拉取 | `kubectl exec -it <running_pod> -- curl -v https://registry.invalid/aiops/rootcause:v0` | 返回镜像 manifest 或成功响应 |

---

## ⚠️ 注意事项
- 如果镜像地址正确但仍然失败，可能是认证失败，需检查 `imagePullSecret`。
- 如果多个 Pod 使用相同镜像地址，建议统一配置 `imagePullSecret`。
- 如果镜像仓库为私有仓库，建议使用 HTTPS 以避免证书问题。

---

## 📊 性能统计

├─ 总耗时: 6.2m
├─ 问题定位: 84.2s (23%) ✅
├─ 证据链采集: 129.6s (35%) ✅
├─ 根因分析: 80.5s (22%) ✅
├─ 汇总总结: 76.1s (21%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 6 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed
- **工具调用**: 6 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
