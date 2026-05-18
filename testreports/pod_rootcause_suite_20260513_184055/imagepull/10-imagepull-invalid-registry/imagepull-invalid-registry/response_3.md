======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: fca0abc61efd465a]

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
3m55s (x4 over 5m21s)   Warning   Failed           Pod/rc-imagepull-invalid-registry   Failed to pull image "registry.invalid/aiops/rootcause:v0": rpc error: code = Unknown d
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                            READY   STATUS             RESTARTS   AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-imagepull-invalid-registry   0/1     ImagePullBackOf
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
creationTimestamp: 2026-05-14T06:17:48Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finaliz
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": ["L3"],
  "layer_name": "ImagePullFailed",
  "confidence": "high",
  "reasoning": "检测到 Pod rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态，且事件中显示了镜像拉取失败的原因，包括 DNS 解析失败和镜像地址无效。这表明问题属于 L3 层次，与镜像拉取失败相关。",
  "abnormal_pods": ["rc-imagepull-invalid-registry"],
  "abnormal_groups": ["ImagePullBackOff"],
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "ImagePullFailed",
  "key_entities": ["Pod/rc-imagepull-invalid-registry", "ImagePullBackOff", "registry.invalid/aiops/rootcause:v0"],
  "possible_scenarios": [
    "镜像名称或 tag 错误",
    "私有仓库认证失败（缺少或错误的 imagePullSecret）",
    "DNS 解析失败导致镜像仓库不可达",
    "镜像仓库网络不可达",
    "TLS 证书信任问题"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (53.9s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像名称或 tag 错误', 'probability': 'high', 'reason': '事件中显示镜像地址无效'}, {'scenario': 'DNS 解析失败导致镜像仓库不可达', 'probability': 'high', 'reason': '事件中显示 lookup registry.invalid on 127.0.0.53:53: no such host'}, {'scenario': '私有仓库认证失败（缺少或错误的 imagePullSecret）', 'probability': 'medium', 'reason': '镜像拉取失败可能是由于缺少或错误的 imagePullSecret'}, {'scenario': '镜像仓库网络不可达', 'probability': 'medium', 'reason': '镜像仓库网络不可达可能导致镜像拉取失败'}, {'scenario': 'TLS 证书信任问题', 'probability': 'low', 'reason': 'TLS 证书信任问题可能导致镜像拉取失败'}]
   entities=[{"type": "Pod", "name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e"}, {"type": "ImagePullBackOff", "name": "ImagePullBackOff", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.invalid/aiops/rootcause:v0", "namespace": "aiops-e2e"}]
   reasoning=检测到 Pod rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态，且事件中显示了镜像拉取失败的原因，包括 DNS 解析失败和镜像地址无效。这表明问题属于 L3 层次，与镜像拉取失败相关。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "ImagePullFailed", "confidence": 1.0, "reasoning": "检测到 Pod rc-imagepull-invalid-registry 处于 ImagePullBackOff 状态，且事件中显示了镜像拉取失败的原因，包括 DNS 解析失败和镜像地址无效。这表明问题属于 L3 层次，与镜像拉取失败相关。", "abnormal_pods": [{"name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "Pod", "name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e"}, {"type": "ImagePullBackOff", "name": "ImagePullBackOff", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.invalid/aiops/rootcause:v0", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "镜像名称或 tag 错误", "probability": "high", "reason": "事件中显示镜像地址无效"}, {"scenario": "DNS 解析失败导致镜像仓库不可达", "probability": "high", "reason": "事件中显示 lookup registry.invalid on 127.0.0.53:53: no such host"}, {"scenario": "私有仓库认证失败（缺少或错误的 imagePullSecret）", "probability": "medium", "reason": "镜像拉取失败可能是由于缺少或错误的 imagePullSecret"}, {"scenario": "镜像仓库网络不可达", "probability": "medium", "reason": "镜像仓库网络不可达可能导致镜像拉取失败"}, {"scenario": "TLS 证书信任问题", "probability": "low", "reason": "TLS 证书信任问题可能导致镜像拉取失败"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-invalid-registry                       0/1     ImagePullBackOff   0             5m17s   172.16.166.156   node1    <none>           <none>            app=rc-imagepull-invalid-registry,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/fca0abc61efd465a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/fca0abc61efd465a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/fca0abc61efd465a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          6m (x4 over 7m26s)      kubelet            Failed 
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
6m3s (x4 over 7m29s)     Warning   Failed           Pod/rc-imagepull-invalid-registry   Failed to pull image "registry.invalid/aiops/rootcause:v0": rpc error: code = Unknown 
   💭 [证据链采集] 已采集证据:
1. `kubectl_describe` 显示 Pod `rc-imagepull-invalid-registry` 无法拉取镜像 registry.invalid/aiops/rootcause:v0，错误原因为 DNS 解析失败（lookup registry.invalid on 127.0.0.53:53: no such host）。
2. `kubectl_events` 显示镜像拉取失败，错误原因为 `ErrImagePull` 和 `ImagePullBackOff`，进一步确认了 DNS 解析失败的问题。

未采集证据: 无。

冲突证据: 无。
   ✅ [证据链采集] 完成 (1m 29.1s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-imagepull-invalid-registry 的详细信息以验证镜像拉取失败的原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-imagepull-invalid-registry"},"purpose":"获取 Pod 的详细状态和事件信息，以确认镜像拉取失败的具体原因","evidence_type":"pod_status_events","target_scope":"aiops-e2e/rc-imagepull-invalid-registry","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"检查 Pod rc-imagepull-invalid-registry 的事件日志以获取镜像拉取失败的详细信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","tool_args":{"namespace":"aiops-e2e","name":"rc-imagepull-invalid-registry"},"purpose":"获取 Pod 的事件日志，以确认镜像拉取失败的具体原因","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-imagepull-invalid-registry","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          6m (x4 over 7m26s)      kubelet            Failed to pull image \"registry.invalid/aiops/rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n  Normal   BackOff         2m17s (x22 over 7m25s)  kubelet            Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n      Reason:       ImagePullBackOff\n  Warning  Failed          6m (x4 over 7m26s)      kubelet            Error: ErrImagePull\n  Warning  Failed          5m49s (x6 over 7m25s)   kubelet            Error: ImagePullBackOff\n                  cni.projectcalico.org/containerID: 82174088e8d254fd04c994cc2744d2fc71d880e8291a39a8e865fe71718ad3db\n                  cni.projectcalico.org/podIP: 172.16.166.156/32\n                  cni.projectcalico.org/podIPs: 172.16.166.156/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed\n    State:          Waiting","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fca0abc61efd465a/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fca0abc61efd465a/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fca0abc61efd465a/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n6m3s (x4 over 7m29s)     Warning   Failed           Pod/rc-imagepull-invalid-registry   Failed to pull image \"registry.invalid/aiops/rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n2m20s (x22 over 7m28s)   Normal    BackOff          Pod/rc-imagepull-invalid-registry   Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n6m3s (x4 over 7m29s)     Warning   Failed           Pod/rc-imagepull-invalid-registry   Error: ErrImagePull\n5m52s (x6 over 7m28s)    Warning   Failed           Pod/rc-imagepull-invalid-registry   Error: ImagePullBackOff","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fca0abc61efd465a/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fca0abc61efd465a/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fca0abc61efd465a/tools/002-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集证据:\n1. `kubectl_describe` 显示 Pod `rc-imagepull-invalid-registry` 无法拉取镜像 registry.invalid/aiops/rootcause:v0，错误原因为 DNS 解析失败（lookup registry.invalid on 127.0.0.53:53: no such host）。\n2. `kubectl_events` 显示镜像拉取失败，错误原因为 `ErrImagePull` 和 `ImagePullBackOff`，进一步确认了 DNS 解析失败的问题。\n\n未采集证据: 无。\n\n冲突证据: 无。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-imagepull-invalid-registry 的详细信息以验证镜像拉取失败的原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","purpose":"获取 Pod 的详细状态和事件信息，以确认镜像拉取失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查 Pod rc-imagepull-invalid-registry 的事件日志以获取镜像拉取失败的详细信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","purpose":"获取 Pod 的事件日志，以确认镜像拉取失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod rc-imagepull-invalid-registry 的详细信息以验证... | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 检查 Pod rc-imagepull-invalid-registry 的事件日志以获取... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-image...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (27.9s)
   📤 → 下游数据: root_cause=镜像拉取失败，由于 DNS 解析失败导致镜像仓库不可达。具体表现为 Pod rc-imagepull-invalid-registry 无法拉取镜像 registry.invalid/aiops/rootcause:v0，错误原因为 lookup registry.invalid on 127.0.0.53:53: no such host。
   confidence=100%
   causal_chain={"root_cause": "DNS 解析失败导致镜像仓库不可达", "intermediate_causes": ["镜像拉取失败"], "direct_causes": ["镜像拉取失败，由于 DNS 解析失败导致镜像仓库不可达"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"tool": "kubectl_describe", "description": "Pod rc-imagepull-invalid-registry 无法拉取镜像 registry.invalid/aiops/rootcause:v0，错误原因为 DNS 解析失败（lookup registry.invalid on 127.0.0.53:53: no such host）"}, {"tool": "kubectl_events", "description": "镜像拉取失败，错误原因为 ErrImagePull 和 ImagePullBackOff，进一步确认了 DNS 解析失败的问题"}], "evidence_analysis": [{"tool": "kubectl_describe", "summary": "镜像拉取失败，由于 DNS 解析失败导致镜像仓库不可达"}, {"tool": "kubectl_events", "summary": "镜像拉取失败，由于 DNS 解析失败导致镜像仓库不可达"}], "causal_chain": {"root_cause": "DNS 解析失败导致镜像仓库不可达", "intermediate_causes": ["镜像拉取失败"], "direct_causes": ["镜像拉取失败，由于 DNS 解析失败导致镜像仓库不可达"]}, "root_cause": "镜像拉取失败，由于 DNS 解析失败导致镜像仓库不可达。具体表现为 Pod rc-imagepull-invalid-registry 无法拉取镜像 registry.invalid/aiops/rootcause:v0，错误原因为 lookup registry.invalid on 127.0.0.53:53: no such host。", "root_cause_summary": "镜像拉取失败，由于 DNS 解析失败导致镜像仓库不可达。具体表现为 Pod rc-imagepull-invalid-registry 无法拉取镜像 registry.invalid/aiops/rootcause:v0，错误原因为 lookup registry.invalid on 127.0.0.53:53: no such host。", "confidence": 1.0, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": "根因分析表明，Pod rc-imagepull-invalid-registry 无法拉取镜像 registry.invalid/aiops/rootcause:v0，错误原因为 DNS 解析失败导致镜像仓库不可达。这是由于 lookup registry.invalid on 127.0.0.53:53: no such host 错误导致的。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 镜像拉取失败，由于 DNS 解析失败导致镜像仓库不可达。具体表现为 Pod rc-imagepull-invalid-registry 无法拉取镜像 registry.invalid/aiops/rootcause:v0，错误原因为 lookup registry.invalid on 127.0....
   置信度: 100%
   🔗 因果链:
     根本原因: DNS 解析失败导致镜像仓库不可达


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 22.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4031 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 13.8s
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
| **置信度** | 高 (100%) |
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
| 错误信息 | lookup registry.invalid on 127.0.0.53:53: no such host |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ImagePullBackOff` | Pod 处于镜像拉取失败状态 |
| 2 | Pod 事件 | `kubectl describe pod rc-imagepull-invalid-registry` | `Warning: Failed to pull image "registry.invalid/aiops/rootcause:v0"` | 明确指出镜像拉取失败 |
| 3 | 事件日志 | `kubectl events` | `lookup registry.invalid on 127.0.0.53:53: no such host` | DNS 解析失败导致镜像仓库不可达 |
| 4 | Pod YAML | `kubectl get pod -o yaml` | `image: registry.invalid/aiops/rootcause:v0` | 使用了无效的镜像地址 |
| 5 | Pod 详细信息 | `kubectl describe pod rc-imagepull-invalid-registry` | `Warning: FailedPullImage: rpc error: code = Unknown desc = failed to resolve reference` | 镜像拉取失败的根本原因是 DNS 解析失败 |
| 6 | 上游工具结果 | `kubectl_get_by_kind_in_cluster` | `status_counts={'ImagePullBackOff': 1}` | 集群中存在 1 个镜像拉取失败的 Pod |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 状态为 `ImagePullBackOff`，事件中明确指出镜像拉取失败，错误信息为 DNS 解析失败，指向镜像仓库不可达。
- **证据链**：镜像地址无效或 DNS 配置错误 → 镜像仓库无法访问 → 镜像拉取失败 → Pod 无法启动 → 状态为 `ImagePullBackOff`。

### 缺失证据
无。

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ DNS 解析失败导致镜像仓库不可达                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 镜像仓库地址 registry.invalid 无法解析，导致镜像拉取失败        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Failed to pull image "registry.invalid/aiops/rootcause:v0"      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ImagePullBackOff，无法正常启动                       │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2、#3、#5，问题的根本原因是**镜像仓库地址 registry.invalid 无法解析**，导致镜像拉取失败，Pod 无法正常启动。  
**置信度**：高 (100%)  
- ✅ `kubectl describe pod` 明确指出镜像拉取失败
- ✅ `kubectl events` 显示 DNS 解析失败
- ✅ `kubectl_get_yaml` 显示使用了无效的镜像地址

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修复 DNS 配置或使用正确镜像地址**
```bash
# 检查 DNS 配置
cat /etc/resolv.conf

# 如果 registry.invalid 是内部域名，需确保 DNS 服务器能解析该域名
# 或者修改镜像地址为有效的 registry
kubectl set image deployment/<deployment-name> -n aiops-e2e <container-name>=<valid-registry-path>
```
*依据*：当前使用了无效的镜像地址 registry.invalid/aiops/rootcause:v0

**2. [可选] 检查节点网络连通性**
```bash
# 检查节点能否解析 registry.invalid
nslookup registry.invalid
# 检查节点能否访问 registry
curl -v https://registry.invalid
```
*目的*：确认节点网络是否正常，DNS 是否配置正确

### 后续优化
1. **配置镜像拉取策略为 IfNotPresent**（如果镜像已存在于节点）
2. **使用 imagePullSecret**（如果使用私有仓库）
3. **监控镜像拉取失败事件**，配置自动告警
4. **验证镜像地址是否正确**，避免使用无效或拼写错误的镜像仓库地址

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-imagepull-invalid-registry -n aiops-e2e` | STATUS: Running |
| 2. 检查事件 | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` | 无 FailedPullImage 事件 |
| 3. 检查镜像拉取 | `kubectl get pod rc-imagepull-invalid-registry -o jsonpath='{.spec.containers[0].image}'` | 输出为有效镜像地址 |

---

## ⚠️ 注意事项
- 如果 registry.invalid 是内部仓库，需确保集群节点 DNS 配置正确，并能解析该域名。
- 如果问题发生在多个 Pod 上，建议统一检查镜像地址和 DNS 配置。
- 如果镜像仓库为私有仓库，需确保配置了正确的 imagePullSecret。

---

---

## 📊 性能统计

├─ 总耗时: 4.2m
├─ 问题定位: 53.9s (21%) ✅
├─ 证据链采集: 89.1s (35%) ✅
├─ 根因分析: 27.9s (11%) ✅
├─ 汇总总结: 82.8s (33%) ✅
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
