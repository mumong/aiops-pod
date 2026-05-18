======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a2bbd717ded94a40]

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
2m34s (x616 over 142m)   Normal   BackOff   Pod/rc-imagepull-invalid-registry   Back-off pulling image "registry.invalid/aiops/rootcause:v0"
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                            READY   STATUS             RESTARTS   AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-imagepull-invalid-registry   0/1     ImagePullBackOff
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": [
    "L3"
  ],
  "layer_name": "ImagePullFailed",
  "confidence": 0.95,
  "reasoning": "当前异常 Pod 状态为 ImagePullBackOff，Events 显示镜像拉取失败，归因于镜像仓库不可达或镜像路径错误。",
  "abnormal_pods": [
    {
      "name": "rc-imagepull-invalid-registry",
      "namespace": "aiops-e2e",
      "status": "ImagePullBackOff",
      "ready": "0/1"
    }
  ],
  "abnormal_groups": [
    "ImagePullFailed"
  ],
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "L3",
  "key_entities": [
    "Pod/rc-imagepull-invalid-registry",
    "镜像 registry.invalid/aiops/rootcause:v0",
    "节点 node1"
  ],
  "possible_scenarios": [
    "镜像仓库地址 registry.invalid 不可达",
    "镜像 registry.invalid/aiops/rootcause:v0 不存在或 tag 错误",
    "节点 node1 缺少 imagePullSecret 或认证失败",
    "节点 node1 DNS 解析失败",
    "节点 node1 TLS 证书信任问题"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (49.1s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像仓库地址 registry.invalid 不可达', 'probability': '高', 'reason': 'Events 显示 connection refused 或 timeout'}, {'scenario': '镜像 registry.invalid/aiops/rootcause:v0 不存在或 tag 错误', 'probability': '高', 'reason': 'Events 显示 manifest unknown 或 not found'}, {'scenario': '节点 node1 缺少 imagePullSecret 或认证失败', 'probability': '高', 'reason': 'Events 显示 unauthorized 或 no basic auth'}, {'scenario': '节点 node1 DNS 解析失败', 'probability': '高', 'reason': 'Events 显示 Could not resolve host'}, {'scenario': '节点 node1 TLS 证书信任问题', 'probability': '高', 'reason': 'Events 显示 x509 certificate signed by unknown authority'}]
   entities=[{"type": "Pod", "name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e"}, {"type": "镜像", "name": "registry.invalid/aiops/rootcause:v0", "namespace": ""}, {"type": "节点", "name": "node1", "namespace": ""}]
   reasoning=当前异常 Pod 状态为 ImagePullBackOff，Events 显示镜像拉取失败，归因于镜像仓库不可达或镜像路径错误。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "当前异常 Pod 状态为 ImagePullBackOff，Events 显示镜像拉取失败，归因于镜像仓库不可达或镜像路径错误。", "abnormal_pods": [{"name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "Pod", "name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e"}, {"type": "镜像", "name": "registry.invalid/aiops/rootcause:v0", "namespace": ""}, {"type": "节点", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库地址 registry.invalid 不可达", "probability": "高", "reason": "Events 显示 connection refused 或 timeout"}, {"scenario": "镜像 registry.invalid/aiops/rootcause:v0 不存在或 tag 错误", "probability": "高", "reason": "Events 显示 manifest unknown 或 not found"}, {"scenario": "节点 node1 缺少 imagePullSecret 或认证失败", "probability": "高", "reason": "Events 显示 unauthorized 或 no basic auth"}, {"scenario": "节点 node1 DNS 解析失败", "probability": "高", "reason": "Events 显示 Could not resolve host"}, {"scenario": "节点 node1 TLS 证书信任问题", "probability": "高", "reason": "Events 显示 x509 certificate signed by unknown authority"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-invalid-registry                       0/1     ImagePullBackOff   0             142m   172.16.166.156   node1    <none>           <none>            app=rc-imagepull-invalid-registry,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 95%

📍 [证据链采集] 执行中...
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
  Normal  BackOff  8s (x638 over 145m)  kubelet  Back-off pulling image "regi
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
10s (x638 over 145m)   Normal   BackOff   Pod/rc-imagepull-invalid-registry   Back-off pulling image "registry.invalid/aiops/rootcause:v0"
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [证据链采集] 已采集证据：
- `kubectl describe pod` 显示 Pod 状态为 Pending，镜像拉取失败，错误信息为 "Back-off pulling image 'registry.invalid/aiops/rootcause:v0'"。
- `kubectl events` 显示事件信息为 "Back-off pulling image 'registry.invalid/aiops/rootcause:v0'"，表明镜像拉取失败。
- `kubectl get secret` 没有返回任何 secret，表明异常 Pod 所在命名空间中不存在用于访问 registry.invalid 的 imagePullSecret。

未采集证据：
- 无

冲突证据：
- 无
   ✅ [证据链采集] 完成 (2m 3.2s)
   📤 → 下游数据: evidence_items=5/6
   evidence_analysis={"evidence_plan":[{"id":"imagepullbackoff_pod_inspect","description":"获取异常 Pod 'rc-imagepull-invalid-registry' 的详细描述，确认镜像拉取失败的具体原因和配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-imagepull-invalid-registry"},"purpose":"确认镜像拉取失败的具体原因，例如镜像地址错误、认证失败、网络不可达等","evidence_type":"pod_events_configuration","target_scope":"aiops-e2e/rc-imagepull-invalid-registry","acceptable_tools":["kubectl_describe","kubectl_events","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"imagepullbackoff_pod_events","description":"获取异常 Pod 'rc-imagepull-invalid-registry' 的 Events 事件，确认镜像拉取失败的详细错误信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","tool_args":{"namespace":"aiops-e2e","name":"rc-imagepull-invalid-registry"},"purpose":"获取镜像拉取失败的详细错误信息，如 connection refused、timeout、manifest unknown 等","evidence_type":"event_logs","target_scope":"aiops-e2e/rc-imagepull-invalid-registry","acceptable_tools":["kubectl_events","kubectl_describe"],"counts_for_completeness":true},{"id":"imagepullsecret_check","description":"验证节点 node1 是否配置了正确的 imagePullSecret 以访问 registry.invalid","level":"important","tool":"run_bash_command","command":"kubectl get secret -n aiops-e2e -o jsonpath='{.items[*].metadata.name}'","tool_args":{"namespace":"aiops-e2e"},"purpose":"确认异常 Pod 所在命名空间中是否存在用于访问 registry.invalid 的 imagePullSecret","evidence_type":"secret_configuration","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_kind_in_namespace","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal  BackOff  8s (x638 over 145m)  kubelet  Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n      Reason:       ImagePullBackOff\n                  cni.projectcalico.org/containerID: 82174088e8d254fd04c994cc2744d2fc71d880e8291a39a8e865fe71718ad3db\n                  cni.projectcalico.org/podIP: 172.16.166.156/32\n                  cni.projectcalico.org/podIPs: 172.16.166.156/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed\n    State:          Waiting","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n10s (x638 over 145m)   Normal   BackOff   Pod/rc-imagepull-invalid-registry   Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/003-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/003-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a2bbd717ded94a40/tools/003-evidence-run_bash_command.summary.txt"}],"llm_analysis":"已采集证据：\n- `kubectl describe pod` 显示 Pod 状态为 Pending，镜像拉取失败，错误信息为 \"Back-off pulling image 'registry.invalid/aiops/rootcause:v0'\"。\n- `kubectl events` 显示事件信息为 \"Back-off pulling image 'registry.invalid/aiops/rootcause:v0'\"，表明镜像拉取失败。\n- `kubectl get secret` 没有返回任何 secret，表明异常 Pod 所在命名空间中不存在用于访问 registry.invalid 的 imagePullSecret。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 5/6 项，完整度 83%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":6,"environment_evidence_collected":5,"environment_evidence_completeness":0.8333333333333334,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"imagepullbackoff_pod_inspect","description":"获取异常 Pod 'rc-imagepull-invalid-registry' 的详细描述，确认镜像拉取失败的具体原因和配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","purpose":"确认镜像拉取失败的具体原因，例如镜像地址错误、认证失败、网络不可达等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"imagepullbackoff_pod_events","description":"获取异常 Pod 'rc-imagepull-invalid-registry' 的 Events 事件，确认镜像拉取失败的详细错误信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","purpose":"获取镜像拉取失败的详细错误信息，如 connection refused、timeout、manifest unknown 等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"imagepullsecret_check","description":"验证节点 node1 是否配置了正确的 imagePullSecret 以访问 registry.invalid","level":"important","tool":"run_bash_command","command":"kubectl get secret -n aiops-e2e -o jsonpath='{.items[*].metadata.name}'","purpose":"确认异常 Pod 所在命名空间中是否存在用于访问 registry.invalid 的 imagePullSecret","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["imagepullsecret_check(验证节点 node1 是否配置了正确的 imagePullSecret 以访问 registry.invalid): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 83%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | imagepullback... | critical | ✅ | kubectl_describe | 获取异常 Pod 'rc-imagepull-invalid-registry' 的详细描... | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` |
   | imagepullback... | critical | ✅ | kubectl_events | 获取异常 Pod 'rc-imagepull-invalid-registry' 的 Ev... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-image...` |
   | imagepullsecr... | important | ❌ | run_bash_command | 验证节点 node1 是否配置了正确的 imagePullSecret 以访问 regis... | `kubectl get secret -n aiops-e2e -o jsonpath='{.items[*].metadata.name}'` |

   ⚠️ 未采集原因:
   - imagepullsecret_check(验证节点 node1 是否配置了正确的 imagePullSecret 以访问 registry.invalid): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (14.2s)
   📤 → 下游数据: root_cause=[L3层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L3层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L3层] 当前无法基于 LLM 输出确定根本原因
   置信度: 10%
   🔗 因果链:
     根本原因: LLM 未生成可靠因果链
     传导机制: 缺少可用的结构化根因分析结果
     最终表现: 我的集群有什么问题


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 15.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3966 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 21.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff |
| **兼容归因层** | L3 |
| **问题分类** | ImagePullFailed |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ImagePullBackOff, RESTARTS: 0` | Pod 无法启动，镜像拉取失败 |
| 2 | Events | `kubectl events` | `Back-off pulling image "registry.invalid/aiops/rootcause:v0"` | 明确指向镜像拉取失败 |
| 3 | Pod describe | `kubectl describe pod` | `Normal  BackOff  8s (x638 over 145m)  kubelet  Back-off pulling image` | 镜像拉取失败，持续重试 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `ImagePullBackOff`，Events 明确指出拉取镜像失败，说明问题出在镜像拉取环节。
- **证据链**：镜像地址无效 → kubelet 无法拉取镜像 → Pod 无法启动 → 状态为 `ImagePullBackOff`。

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| imagePullSecret 配置检查 | critical | 无法确认是否缺少认证凭据，导致镜像仓库访问失败 |
| registry.invalid 连通性测试 | critical | 无法确认节点是否能访问 registry.invalid |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ registry.invalid/aiops/rootcause:v0 镜像无法访问                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ registry.invalid 无法解析或访问 → kubelet 拉取失败              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ kubelet 报错: "Back-off pulling image registry.invalid/aiops/rootcause:v0" │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ImagePullBackOff，无法启动                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态 `ImagePullBackOff`) 和证据 #2 (Events 显示 `Back-off pulling image "registry.invalid/aiops/rootcause:v0"`), 问题的根本原因是 **镜像地址 registry.invalid/aiops/rootcause:v0 无效或不可访问**，导致 kubelet 无法拉取镜像，进而无法启动 Pod。

**置信度**：高 (95%)
- ✅ Pod 状态为 `ImagePullBackOff`
- ✅ Events 明确指出镜像拉取失败
- ⚠️ 未采集 imagePullSecret 配置和 registry.invalid 连通性证据，无法确认是否涉及认证或网络问题

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 验证镜像地址是否有效**
```bash
docker pull registry.invalid/aiops/rootcause:v0
```
*依据*：直接验证镜像是否可拉取，确认 registry.invalid 是否可达

**2. [可选] 检查 imagePullSecret 配置**
```bash
kubectl get secret -n aiops-e2e | grep docker-registry
```
*目的*：确认是否存在用于访问 registry.invalid 的 imagePullSecret

**3. [可选] 检查节点 node1 到 registry.invalid 的连通性**
```bash
kubectl exec -it <working_pod> -- nslookup registry.invalid
kubectl exec -it <working_pod> -- curl -v https://registry.invalid
```
*目的*：确认 DNS 解析和 HTTPS 访问是否正常

### 后续优化

1. **修复镜像地址或 tag**：确保镜像地址正确，tag 存在
2. **配置 imagePullSecret**：如需访问私有仓库，配置正确的 imagePullSecret
3. **网络排查**：如节点无法访问 registry.invalid，检查节点防火墙、DNS 配置或 TLS 证书

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-imagepull-invalid-registry -n aiops-e2e` | STATUS: Running |
| 2. 检查镜像拉取日志 | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` | 无 `Back-off pulling image` |
| 3. 检查 imagePullSecret | `kubectl get secret -n aiops-e2e` | 存在用于 registry.invalid 的 secret |

---

## ⚠️ 注意事项

- 如果 registry.invalid 是私有仓库，必须配置 imagePullSecret
- 如果 registry.invalid 不存在，需修改镜像地址为有效的地址
- 如果网络策略限制了 registry.invalid 的访问，需调整节点防火墙或路由规则

---

## 📊 性能统计

├─ 总耗时: 5.4m
├─ 问题定位: 49.1s (15%) ✅
├─ 证据链采集: 123.2s (38%) ✅
├─ 根因分析: 14.2s (4%) ✅
├─ 汇总总结: 135.1s (42%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
