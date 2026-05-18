======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 820d3011a72840a3]

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
95s (x307 over 71m)   Normal   BackOff   Pod/rc-imagepull-invalid-registry   Back-off pulling image "registry.invalid/aiops/rootcause:v0"
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
  "confidence": 0.95,
  "reasoning": "Pod 'rc-imagepull-invalid-registry' 在命名空间 'aiops-e2e' 中处于 'ImagePullBackOff' 状态。Events 显示错误信息 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"'，表明镜像拉取失败。结合诊断手册，该错误属于镜像仓库网络不可达或镜像路径错误。当前异常归因于镜像拉取失败 (L3)。建议进一步确认镜像仓库地址、网络连通性、镜像存在性及认证信息。",
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-imagepull-invalid-registry",
      "status": "ImagePullBackOff",
      "reason": "BackOff",
      "message": "Back-off pulling image \"registry.invalid/aiops/rootcause:v0\""
    }
  ],
  "abnormal_groups": [
    {
      "status": "ImagePullBackOff",
      "count": 1
    }
  ],
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "镜像拉取失败",
  "key_entities": [
    "Pod: rc-imagepull-invalid-registry (aiops-e2e)",
    "Image: registry.invalid/aiops/rootcause:v0"
  ],
  "possible_scenarios": [
    "镜像仓库地址错误或无法访问",
    "镜像名称或 tag 不存在",
    "镜像拉取认证失败",
    "网络连通性问题导致镜像拉取超时"
  ]
}
   ✅ [问题定位] 完成 (40.6s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[]
   entities=[]
   reasoning=Pod 'rc-imagepull-invalid-registry' 在命名空间 'aiops-e2e' 中处于 'ImagePullBackOff' 状态。Events 显示错误信息 'Back-off pulling image "registry.invalid/aiops/rootcause:v0"'，表明镜像拉取失败。结合诊断手册，该错误属于镜像仓库网络不可达或镜像路径错误。当前异常归因于镜像拉取失败 (L3)。建议进一步确认镜像仓库地址、网络连通性、镜像存在性及认证信息。
   layer_analysis={"layer": "L3", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "Pod 'rc-imagepull-invalid-registry' 在命名空间 'aiops-e2e' 中处于 'ImagePullBackOff' 状态。Events 显示错误信息 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"'，表明镜像拉取失败。结合诊断手册，该错误属于镜像仓库网络不可达或镜像路径错误。当前异常归因于镜像拉取失败 (L3)。建议进一步确认镜像仓库地址、网络连通性、镜像存在性及认证信息。", "abnormal_pods": [{"name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "", "status_category": "", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-invalid-registry                       0/1     ImagePullBackOff   0             71m    172.16.166.156   node1    <none>           <none>            app=rc-imagepull-invalid-registry,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 50%

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
  Normal  BackOff  4m4s (x307 over 74m)  kubelet  Back-off pulling image "reg
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m7s (x307 over 74m)   Normal   BackOff   Pod/rc-imagepull-invalid-registry   Back-off pulling image "registry.invalid/aiops/rootcause:v0"
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\n                                 Dload  Upload   Total   Spent    Left  Spe
   💭 [证据链采集] # 证据结论

**已采集证据:**
1. **kubectl_describe**: Pod `rc-imagepull-invalid-registry` 在命名空间 `aiops-e2e` 中处于 `Pending` 状态，关键事件显示 `ImagePullBackOff`，表明镜像拉取失败。
2. **kubectl_events**: 事件显示 `Back-off pulling image "registry.invalid/aiops/rootcause:v0"`，进一步确认镜像拉取失败。
3. **run_bash_command**: 使用 `curl` 尝试访问镜像仓库，返回错误 `Could not resolve host: registry.invalid`，表明节点无法解析镜像仓库的主机名。

**未采集证据:**
- 无

**冲突证据:**
- 无

**结论:** 镜像仓库 `registry.invalid` 无法解析，导致 Pod `rc-imagepull-invalid-registry` 无法拉取镜像，从而处于 `ImagePullBackOff` 状态。建议检查 DNS 配置或镜像仓库地址的正确性。
   ✅ [证据链采集] 完成 (2m 14.7s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Describe Pod 'rc-imagepull-invalid-registry' in namespace 'aiops-e2e' to check detailed status and events related to the ImagePullBackOff error.","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","tool_args":{"pod_name":"rc-imagepull-invalid-registry","namespace":"aiops-e2e"},"purpose":"Verify current status, events, and detailed conditions of the Pod to identify why the image pull is failing.","evidence_type":"status_events","target_scope":"Pod/rc-imagepull-invalid-registry","acceptable_tools":["kubectl_describe","kubectl_events","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e3","description":"List all events for the Pod 'rc-imagepull-invalid-registry' in namespace 'aiops-e2e' to identify any additional clues about the failure.","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","tool_args":{"pod_name":"rc-imagepull-invalid-registry","namespace":"aiops-e2e"},"purpose":"Identify any additional events or warnings that may provide context for the ImagePullBackOff status.","evidence_type":"events","target_scope":"Pod/rc-imagepull-invalid-registry","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e4","description":"Verify if the image 'registry.invalid/aiops/rootcause:v0' is accessible from the node 'node1' where the Pod is scheduled.","level":"optional","tool":"run_bash_command","command":"curl -v https://registry.invalid/v2/aiops/rootcause/manifests/v0","tool_args":{"node":"node1","command":"curl -v https://registry.invalid/v2/aiops/rootcause/manifests/v0"},"purpose":"Confirm network connectivity and accessibility of the image from the node to rule out network or TLS issues.","evidence_type":"network","target_scope":"Node/node1","acceptable_tools":["run_bash_command"],"counts_for_completeness":false}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal  BackOff  4m4s (x307 over 74m)  kubelet  Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n      Reason:       ImagePullBackOff\n                  cni.projectcalico.org/containerID: 82174088e8d254fd04c994cc2744d2fc71d880e8291a39a8e865fe71718ad3db\n                  cni.projectcalico.org/podIP: 172.16.166.156/32\n                  cni.projectcalico.org/podIPs: 172.16.166.156/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed\n    State:          Waiting","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n4m7s (x307 over 74m)   Normal   BackOff   Pod/rc-imagepull-invalid-registry   Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\\n                                 Dload  Upload   Total   Spent    Left  Speed\\n\\n  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0\\n  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0* Could not resolve host: registry.invalid\\n* shutting down connection #0\\ncurl: (6) Could not resolve host: registry.invalid\\n\", \"returncode\": 6}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/003-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/003-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/820d3011a72840a3/tools/003-evidence-run_bash_command.summary.txt"}],"llm_analysis":"# 证据结论\n\n**已采集证据:**\n1. **kubectl_describe**: Pod `rc-imagepull-invalid-registry` 在命名空间 `aiops-e2e` 中处于 `Pending` 状态，关键事件显示 `ImagePullBackOff`，表明镜像拉取失败。\n2. **kubectl_events**: 事件显示 `Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"`，进一步确认镜像拉取失败。\n3. **run_bash_command**: 使用 `curl` 尝试访问镜像仓库，返回错误 `Could not resolve host: registry.invalid`，表明节点无法解析镜像仓库的主机名。\n\n**未采集证据:**\n- 无\n\n**冲突证据:**\n- 无\n\n**结论:** 镜像仓库 `registry.invalid` 无法解析，导致 Pod `rc-imagepull-invalid-registry` 无法拉取镜像，从而处于 `ImagePullBackOff` 状态。建议检查 DNS 配置或镜像仓库地址的正确性。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"Describe Pod 'rc-imagepull-invalid-registry' in namespace 'aiops-e2e' to check detailed status and events related to the ImagePullBackOff error.","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","purpose":"Verify current status, events, and detailed conditions of the Pod to identify why the image pull is failing.","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"List all events for the Pod 'rc-imagepull-invalid-registry' in namespace 'aiops-e2e' to identify any additional clues about the failure.","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","purpose":"Identify any additional events or warnings that may provide context for the ImagePullBackOff status.","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"Verify if the image 'registry.invalid/aiops/rootcause:v0' is accessible from the node 'node1' where the Pod is scheduled.","level":"optional","tool":"run_bash_command","command":"curl -v https://registry.invalid/v2/aiops/rootcause/manifests/v0","purpose":"Confirm network connectivity and accessibility of the image from the node to rule out network or TLS issues.","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | Describe Pod 'rc-imagepull-invalid-registry' ... | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` |
   | e3 | important | ✅ | kubectl_events | List all events for the Pod 'rc-imagepull-inv... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-image...` |
   | e4 | optional | ✅ | run_bash_command | Verify if the image 'registry.invalid/aiops/r... | `curl -v https://registry.invalid/v2/aiops/rootcause/manifests/v0` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (19.1s)
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
   ✅ [汇总总结] 完成 (1m 22.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3976 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 36.6s
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
| **Pod异常状态** | ImagePullBackOff |
| **兼容归因层** | L3 |
| **问题分类** | ImagePullFailed |
| **置信度** | 高 |
| **证据完整度** | 2/2 (100%) |

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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ImagePullBackOff` | Pod 无法拉取镜像，处于回退状态 |
| 2 | Pod Events | `kubectl describe pod` | `Normal BackOff: Back-off pulling image "registry.invalid/aiops/rootcause:v0"` | 明确指出镜像拉取失败 |
| 3 | 全局 Pod 状态 | `kubectl get pod -A` | `status_counts={'ImagePullBackOff': 1, 'Running': 46}` | 仅 1 个 Pod 处于镜像拉取失败状态 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 `ImagePullBackOff`，Events 明确记录 `Back-off pulling image`，表明镜像拉取失败
- **证据链**：镜像地址错误/不可达 → kubelet 尝试拉取失败 → 进入 `ImagePullBackOff` 回退机制 → Pod 无法启动

### 缺失证据（无）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 无 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 镜像仓库地址 'registry.invalid/aiops/rootcause:v0' 不可达或镜像不存在 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 无法从 registry.invalid 拉取镜像，触发 ImagePullBackOff 机制 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 镜像拉取失败（Events 明确记录 `Back-off pulling image ...`）     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ImagePullBackOff，无法正常启动                       │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 状态为 `ImagePullBackOff`) 和证据 #2 (Events 明确记录 `Back-off pulling image "registry.invalid/aiops/rootcause:v0"`)，问题的根本原因是**镜像仓库地址 `registry.invalid/aiops/rootcause:v0` 不可达或镜像不存在**，导致 kubelet 无法拉取镜像。
**置信度**：高 (95%)
- ✅ Pod 状态和 Events 都明确指向镜像拉取失败
- ✅ 无冲突证据

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 检查镜像地址是否正确**
```bash
kubectl get pod rc-imagepull-invalid-registry -n aiops-e2e -o jsonpath='{.spec.containers[*].image}'
```
*目的*：确认 Pod spec 中的镜像地址是否为 `registry.invalid/aiops/rootcause:v0`

**2. [可选] 验证镜像是否存在或可达**
```bash
docker pull registry.invalid/aiops/rootcause:v0
```
*目的*：确认镜像是否可被本地拉取（需在可访问 registry.invalid 的环境中执行）

**3. [可选] 检查 imagePullSecret**
```bash
kubectl get pod rc-imagepull-invalid-registry -n aiops-e2e -o jsonpath='{.spec.imagePullSecrets[*].name}'
kubectl get secret -n aiops-e2e
```
*目的*：确认是否配置了正确的 `imagePullSecret`，用于访问私有镜像仓库

**4. [紧急] 替换为有效镜像**
```bash
kubectl set image deployment/<deployment_name> -n aiops-e2e <container_name>=<valid-image>
```
*目的*：如果镜像地址错误或不可用，立即替换为已知可用镜像

### 后续优化
1. **镜像仓库连通性监控**：配置镜像仓库连通性检测，确保镜像仓库可访问
2. **镜像标签管理**：使用标签 `latest` 或语义化版本标签（如 `v1.0.0`），避免镜像丢失
3. **镜像签名与认证**：如果镜像仓库为私有仓库，确保配置了 `imagePullSecret` 并正确使用

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-imagepull-invalid-registry -n aiops-e2e` | STATUS: Running |
| 2. 检查镜像是否成功拉取 | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` | 无 `ImagePullBackOff` 或 `ErrImagePull` |
| 3. 查看 Events | `kubectl get events -n aiops-e2e` | 无 `Back-off pulling image` 事件 |

---

## ⚠️ 注意事项
- 如果镜像地址错误，需要联系镜像仓库管理员确认镜像是否存在
- 如果镜像仓库为私有仓库，需确保 `imagePullSecret` 配置正确
- 如果镜像地址正确但拉取失败，可能涉及网络策略、DNS 解析、TLS 证书等问题，需进一步排查节点到镜像仓库的连通性

---

## 📊 性能统计

├─ 总耗时: 4.6m
├─ 问题定位: 40.6s (15%) ✅
├─ 证据链采集: 134.7s (49%) ✅
├─ 根因分析: 19.1s (7%) ✅
├─ 汇总总结: 82.2s (30%) ✅
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
