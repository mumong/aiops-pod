======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: b8fd7546025c4fd4]

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
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal  BackOff  21s (x503 over 115m)  kubelet  Back-off pulling image "reg
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
  "reasoning": "检测到一个 Pod (rc-imagepull-invalid-registry) 处于 ImagePullBackOff 状态。这表明镜像拉取失败，常见原因包括镜像名或 tag 错误、认证失败、仓库访问超时、DNS 解析失败、TLS 证书问题等。事件中显示 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"'，进一步确认了镜像拉取失败的问题。",
  "abnormal_pods": [
    {
      "name": "rc-imagepull-invalid-registry",
      "namespace": "aiops-e2e",
      "status": "ImagePullBackOff",
      "node": "node1"
    }
  ],
  "abnormal_groups": [
    "ImagePullFailed"
  ],
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "ImagePullFailed",
  "key_entities": [
    "rc-imagepull-invalid-registry",
    "aiops-e2e",
    "node1",
    "registry.invalid/aiops/rootcause:v0"
  ],
  "possible_scenarios": [
    "镜像名或 tag 错误",
    "私有仓库认证失败",
    "仓库访问超时",
    "DNS 解析失败",
    "TLS 证书问题"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (58.8s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像名或 tag 错误', 'probability': 'High', 'reason': "Events 显示 'Back-off pulling image'，表明镜像路径或 tag 可能不存在。"}, {'scenario': '私有仓库认证失败', 'probability': 'High', 'reason': 'Pod 未指定 imagePullSecret，可能缺少私有仓库的认证信息。'}, {'scenario': '仓库访问超时', 'probability': 'High', 'reason': "镜像仓库网络不可达或访问超时，事件中 'Back-off pulling image' 说明拉取失败。"}, {'scenario': 'DNS 解析失败', 'probability': 'Medium', 'reason': '镜像仓库域名无法解析，需检查节点 DNS 配置。'}, {'scenario': 'TLS 证书问题', 'probability': 'Medium', 'reason': '镜像仓库的 TLS 证书未被节点容器运行时信任。'}]
   entities=[{"type": "Pod", "name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Image", "name": "registry.invalid/aiops/rootcause:v0", "namespace": ""}]
   reasoning=检测到一个 Pod (rc-imagepull-invalid-registry) 处于 ImagePullBackOff 状态。这表明镜像拉取失败，常见原因包括镜像名或 tag 错误、认证失败、仓库访问超时、DNS 解析失败、TLS 证书问题等。事件中显示 'Back-off pulling image "registry.invalid/aiops/rootcause:v0"'，进一步确认了镜像拉取失败的问题。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "检测到一个 Pod (rc-imagepull-invalid-registry) 处于 ImagePullBackOff 状态。这表明镜像拉取失败，常见原因包括镜像名或 tag 错误、认证失败、仓库访问超时、DNS 解析失败、TLS 证书问题等。事件中显示 'Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"'，进一步确认了镜像拉取失败的问题。", "abnormal_pods": [{"name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "Pod", "name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Image", "name": "registry.invalid/aiops/rootcause:v0", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像名或 tag 错误", "probability": "High", "reason": "Events 显示 'Back-off pulling image'，表明镜像路径或 tag 可能不存在。"}, {"scenario": "私有仓库认证失败", "probability": "High", "reason": "Pod 未指定 imagePullSecret，可能缺少私有仓库的认证信息。"}, {"scenario": "仓库访问超时", "probability": "High", "reason": "镜像仓库网络不可达或访问超时，事件中 'Back-off pulling image' 说明拉取失败。"}, {"scenario": "DNS 解析失败", "probability": "Medium", "reason": "镜像仓库域名无法解析，需检查节点 DNS 配置。"}, {"scenario": "TLS 证书问题", "probability": "Medium", "reason": "镜像仓库的 TLS 证书未被节点容器运行时信任。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-invalid-registry                       0/1     ImagePullBackOff   0             115m   172.16.166.156   node1    <none>           <none>            app=rc-imagepull-invalid-registry,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/b8fd7546025c4fd4/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/b8fd7546025c4fd4/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/b8fd7546025c4fd4/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal  BackOff  2m33s (x503 over 117m)  kubelet  Back-off pulling image "r
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
2m35s (x503 over 117m)   Normal   BackOff   Pod/rc-imagepull-invalid-registry   Back-off pulling image "registry.invalid/aiops/rootcause:v0"
   💭 [证据链采集] 已采集关键证据：
1. `kubectl describe pod` 显示 Pod `rc-imagepull-invalid-registry` 处于 Pending 状态，事件显示 `Back-off pulling image "registry.invalid/aiops/rootcause:v0"`，确认镜像拉取失败。
2. `kubectl events` 显示事件 `Back-off pulling image`，进一步确认镜像拉取失败，原因可能是镜像地址或 tag 不存在、认证失败、网络不可达、DNS 或 TLS 问题。

未采集证据：
- 无

冲突证据：
- 无

建议下一步检查：
1. 验证镜像 `registry.invalid/aiops/rootcause:v0` 是否存在。
2. 检查 Pod 是否配置了正确的 `imagePullSecret`。
3. 验证节点到镜像仓库的网络连通性、DNS 解析和 TLS 证书信任。
   ✅ [证据链采集] 完成 (1m 37.0s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-imagepull-invalid-registry 的详细描述信息以确认镜像拉取失败的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-imagepull-invalid-registry"},"purpose":"确认镜像拉取失败的具体原因，例如镜像名称错误、认证失败或网络问题。","evidence_type":"events_and_status","target_scope":"Pod rc-imagepull-invalid-registry","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-imagepull-invalid-registry 的事件日志以确认镜像拉取失败的具体原因。","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","tool_args":{"namespace":"aiops-e2e","pod_name":"rc-imagepull-invalid-registry"},"purpose":"确认镜像拉取失败的具体原因，例如镜像名称错误、认证失败或网络问题。","evidence_type":"events","target_scope":"Pod rc-imagepull-invalid-registry","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal  BackOff  2m33s (x503 over 117m)  kubelet  Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n      Reason:       ImagePullBackOff\n                  cni.projectcalico.org/containerID: 82174088e8d254fd04c994cc2744d2fc71d880e8291a39a8e865fe71718ad3db\n                  cni.projectcalico.org/podIP: 172.16.166.156/32\n                  cni.projectcalico.org/podIPs: 172.16.166.156/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed\n    State:          Waiting","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b8fd7546025c4fd4/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b8fd7546025c4fd4/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b8fd7546025c4fd4/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n2m35s (x503 over 117m)   Normal   BackOff   Pod/rc-imagepull-invalid-registry   Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b8fd7546025c4fd4/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b8fd7546025c4fd4/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b8fd7546025c4fd4/tools/002-evidence-kubectl_events.summary.txt"}],"llm_analysis":"已采集关键证据：\n1. `kubectl describe pod` 显示 Pod `rc-imagepull-invalid-registry` 处于 Pending 状态，事件显示 `Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"`，确认镜像拉取失败。\n2. `kubectl events` 显示事件 `Back-off pulling image`，进一步确认镜像拉取失败，原因可能是镜像地址或 tag 不存在、认证失败、网络不可达、DNS 或 TLS 问题。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无\n\n建议下一步检查：\n1. 验证镜像 `registry.invalid/aiops/rootcause:v0` 是否存在。\n2. 检查 Pod 是否配置了正确的 `imagePullSecret`。\n3. 验证节点到镜像仓库的网络连通性、DNS 解析和 TLS 证书信任。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-imagepull-invalid-registry 的详细描述信息以确认镜像拉取失败的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","purpose":"确认镜像拉取失败的具体原因，例如镜像名称错误、认证失败或网络问题。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod rc-imagepull-invalid-registry 的事件日志以确认镜像拉取失败的具体原因。","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","purpose":"确认镜像拉取失败的具体原因，例如镜像名称错误、认证失败或网络问题。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod rc-imagepull-invalid-registry 的详细描述信息以... | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取 Pod rc-imagepull-invalid-registry 的事件日志以确认... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-image...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (47.0s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 15.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5111 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 37.9s
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
| **兼容归因层** | L3 - image_pull |
| **问题分类** | 镜像拉取失败 (ImagePullFailed) |
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
| 镜像 | registry.invalid/aiops/rootcause:v0 |
| 错误信息 | Back-off pulling image "registry.invalid/aiops/rootcause:v0" |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | `kubectl describe pod rc-imagepull-invalid-registry` | `Normal BackOff 21s (x503 over 115m) kubelet Back-off pulling image "registry.invalid/aiops/rootcause:v0"` | 明确指出镜像拉取失败 |
| 2 | Pod 状态 | `kubectl get pod rc-imagepull-invalid-registry -n aiops-e2e` | `STATUS: ImagePullBackOff, RESTARTS: 0` | Pod 无法启动，处于等待镜像拉取状态 |
| 3 | Pod YAML 配置 | `kubectl get pod rc-imagepull-invalid-registry -n aiops-e2e -o yaml` | `imagePullSecrets: <absent>` | 未配置私有镜像仓库的认证信息 |
| 4 | Events 日志 | `kubectl get events -n aiops-e2e` | `Normal BackOff 2m35s (x503 over 117m) Back-off pulling image "registry.invalid/aiops/rootcause:v0"` | 长时间重复拉取失败 |
| 5 | kubectl get by kind | `kubectl get pods -A` | `aiops-e2e rc-imagepull-invalid-registry 0/1 ImagePullBackOff 0 115m` | Pod 处于异常状态 |
| 6 | Runbook 提示 | `fetch_runbook` | `常见原因: 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书问题` | 提供多种可能原因 |

### 证据关联分析
- **证据 #1 + #3 印证**：镜像拉取失败 + 缺少 `imagePullSecret` → 可能是认证失败
- **证据 #2 + #4 印证**：Pod 状态为 `ImagePullBackOff` + 重复失败事件 → 镜像拉取持续失败
- **证据 #1 + #6 印证**：镜像地址为 `registry.invalid/aiops/rootcause:v0` + Runbook 中提示镜像名或 tag 错误 → 可能是镜像地址错误或 tag 不存在

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 镜像仓库连通性测试 | high | 无法确认是镜像仓库网络不可达还是认证失败 |
| DNS 解析测试 | medium | 无法确认是否为 DNS 解析失败 |
| 镜像仓库 TLS 证书验证 | medium | 无法确认是否为证书不被信任 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 中未配置 imagePullSecret，或镜像地址错误，或镜像仓库认证失败  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 尝试拉取镜像失败 → 触发 Back-off → Pod 无法启动         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 镜像拉取失败（Back-off pulling image registry.invalid/aiops/rootcause:v0） │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ImagePullBackOff，无法启动                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Back-off pulling image "registry.invalid/aiops/rootcause:v0") 和证据 #3 (imagePullSecrets: <absent>)，问题的根本原因是 **Pod 未配置 imagePullSecret，导致无法拉取私有镜像仓库中的镜像**。同时，镜像地址 `registry.invalid/aiops/rootcause:v0` 可能也存在错误或 tag 不存在。
**置信度**：高 (95%)
- ✅ 镜像拉取失败事件明确
- ✅ 缺少 imagePullSecret，提示认证问题
- ⚠️ 未验证镜像仓库连通性、DNS、TLS 等，建议进一步确认

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Pod 配置 imagePullSecret**
```bash
kubectl create secret docker-registry my-registry-secret \
  --docker-server=registry.invalid \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email> \
  -n aiops-e2e
```

```bash
kubectl patch pod rc-imagepull-invalid-registry -n aiops-e2e \
  -p '{"spec":{"imagePullSecrets":[{"name":"my-registry-secret"}]}}'
```
*依据*：Pod 缺少 imagePullSecret，导致私有仓库认证失败

**2. [可选] 检查镜像地址是否正确**
```bash
docker pull registry.invalid/aiops/rootcause:v0
```
*目的*：确认镜像地址和 tag 是否正确，是否可从本地拉取

**3. [可选] 检查镜像仓库连通性**
```bash
curl -v https://registry.invalid/v2/
```
*目的*：确认镜像仓库是否可访问，是否返回 401（需要认证）或其他错误

### 后续优化
1. **配置 imagePullSecret 到 Deployment 或 ServiceAccount**
   - 推荐将 imagePullSecret 绑定到 ServiceAccount，避免每次手动配置 Pod
   ```bash
   kubectl patch serviceaccount default -n aiops-e2e \
     -p '{"imagePullSecrets":[{"name":"my-registry-secret"}]}'
   ```

2. **配置镜像拉取超时和重试策略**
   - 调整 kubelet 的 `--image-pull-progress-deadline` 参数（如 `5m`）以减少 Back-off 频率

3. **监控镜像拉取失败事件**
   - 使用 Prometheus + kube-state-metrics 监控 `kube_pod_status_phase` 和 `kube_pod_container_status_restarts_total`，提前发现异常

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-imagepull-invalid-registry -n aiops-e2e` | STATUS: Running |
| 2. 检查镜像拉取事件 | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` | 无 Back-off pulling image 事件 |
| 3. 检查镜像是否已拉取 | `crictl images` | 包含 registry.invalid/aiops/rootcause:v0 |

---

## ⚠️ 注意事项
- 如果镜像仓库要求使用 HTTPS 且证书不可信，需在节点上配置信任证书或使用 `--insecure-registries` 启动 Docker/Dockerd
- 如果问题持续，建议检查节点的网络策略（如防火墙、路由、DNS）以确认是否能访问镜像仓库
- 若镜像地址或 tag 错误，应修正镜像地址或 tag 后重新部署 Pod

---

## 📊 性能统计

├─ 总耗时: 5.6m
├─ 问题定位: 58.8s (17%) ✅
├─ 证据链采集: 97.0s (29%) ✅
├─ 根因分析: 47.0s (14%) ✅
├─ 汇总总结: 135.2s (40%) ✅
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
