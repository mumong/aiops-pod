======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a078ecf94fea4a39]

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
3m18s (x467 over 108m)   Normal   BackOff   Pod/rc-imagepull-missing-secret   Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-imagepull-missing-secret
namespace: aiops-e2e
creationTimestamp: 2026-05-14T11:21:51Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME      SECRETS   AGE    LABELS
default   0         111d   <none>
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=197 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-definitely-missing-pull-secret -n aiops-e2e
Error from server (NotFound): secrets "
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (42.6s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像仓库认证失败', 'probability': 'high', 'reason': '镜像拉取失败，且指定的 imagePullSecret 不存在。'}, {'scenario': '镜像仓库网络不可达', 'probability': 'medium', 'reason': '事件中未明确提及网络错误，但镜像拉取失败可能涉及网络问题。'}, {'scenario': '镜像地址错误', 'probability': 'medium', 'reason': '镜像 registry.invalid/aiops/private-rootcause:v0 可能不存在或地址格式错误。'}]
   entities=[{"type": "Pod", "name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e"}]
   reasoning=当前环境中的活跃异常对象 rc-imagepull-missing-secret 处于 ImagePullBackOff 状态，其异常类型为 ImagePullFailed，属于 L3 层级（镜像拉取失败/网络问题）。事件信息显示镜像仓库 registry.invalid/aiops/private-rootcause:v0 拉取失败，且 imagePullSecret rc-definitely-missing-pull-secret 不存在，导致镜像拉取失败。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "当前环境中的活跃异常对象 rc-imagepull-missing-secret 处于 ImagePullBackOff 状态，其异常类型为 ImagePullFailed，属于 L3 层级（镜像拉取失败/网络问题）。事件信息显示镜像仓库 registry.invalid/aiops/private-rootcause:v0 拉取失败，且 imagePullSecret rc-definitely-missing-pull-secret 不存在，导致镜像拉取失败。", "abnormal_pods": [{"name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "Pod", "name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "镜像仓库认证失败", "probability": "high", "reason": "镜像拉取失败，且指定的 imagePullSecret 不存在。"}, {"scenario": "镜像仓库网络不可达", "probability": "medium", "reason": "事件中未明确提及网络错误，但镜像拉取失败可能涉及网络问题。"}, {"scenario": "镜像地址错误", "probability": "medium", "reason": "镜像 registry.invalid/aiops/private-rootcause:v0 可能不存在或地址格式错误。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-missing-secret                         0/1     ImagePullBackOff   0             108m   172.16.166.166   node1    <none>           <none>            app=rc-imagepull-missing-secret,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=197 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-definitely-missing-pull-secret -n aiops-e2e
Error from server (NotFound): secrets "
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
17s (x489 over 110m)   Normal   BackOff   Pod/rc-imagepull-missing-secret   Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-imagepull-missing-secret
namespace: aiops-e2e
creationTimestamp: 2026-05-14T11:21:51Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 已采集关键证据：
1. **imagePullSecret 缺失**：`kubectl_get_by_name` 明确返回 `secrets "rc-definitely-missing-pull-secret" not found`，确认镜像仓库认证配置缺失。
2. **镜像拉取失败事件**：`kubectl_events` 显示 `Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"`，确认镜像拉取失败且重试中。
3. **镜像地址与配置**：`kubectl_get_yaml` 显示 Pod 指定镜像为 `registry.invalid/aiops/private-rootcause:v0`，且依赖的 `imagePullSecret` 不存在。

结论：当前 Pod `rc-imagepull-missing-secret` 处于 `ImagePullBackOff` 状态，根本原因是缺少必要的 `imagePullSecret` 用于私有镜像仓库认证。镜像地址格式本身未显示明显错误，但仓库 `registry.invalid` 无法验证是否真实可访问。下一步建议检查镜像仓库地址是否正确、是否存在网络隔离或 TLS 问题。
   ✅ [证据链采集] 完成 (1m 39.3s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"evidence-pod-rc-imagepull-missing-secret-imagepullsecret","description":"验证 Pod rc-imagepull-missing-secret 中引用的 imagePullSecret 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-pull-secret -n aiops-e2e","tool_args":{"name":"rc-definitely-missing-pull-secret","namespace":"aiops-e2e"},"purpose":"确认 imagePullSecret 是否存在","evidence_type":"negative","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"evidence-pod-rc-imagepull-missing-secret-events","description":"查看 Pod rc-imagepull-missing-secret 的 Events 以获取镜像拉取失败的详细原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-missing-secret","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-imagepull-missing-secret"},"purpose":"确认镜像拉取失败的具体原因","evidence_type":"event","target_scope":"aiops-e2e","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"evidence-pod-rc-imagepull-missing-secret-image","description":"查看 Pod rc-imagepull-missing-secret 的镜像地址以确认格式是否正确","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-imagepull-missing-secret -n aiops-e2e -o yaml","tool_args":{"name":"rc-imagepull-missing-secret","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"确认镜像地址是否正确","evidence_type":"configuration","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=197 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret rc-definitely-missing-pull-secret -n aiops-e2e\nError from server (NotFound): secrets \"rc-definitely-missing-pull-secret\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n17s (x489 over 110m)   Normal   BackOff   Pod/rc-imagepull-missing-secret   Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-imagepull-missing-secret\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T11:21:51Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: rc-definitely-missing-pull-secret\nphase: Pending\nlabels: app=rc-imagepull-missing-secret, pod_abnormal_type=ImagePullFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-imagepull-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=registry.invalid/aiops/private-rootcause:v0 imagePullPolicy=Always\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"\nvolumes:\n- {\"name\": \"kube-api-access-bnw7m\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a078ecf94fea4a39/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集关键证据：\n1. **imagePullSecret 缺失**：`kubectl_get_by_name` 明确返回 `secrets \"rc-definitely-missing-pull-secret\" not found`，确认镜像仓库认证配置缺失。\n2. **镜像拉取失败事件**：`kubectl_events` 显示 `Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"`，确认镜像拉取失败且重试中。\n3. **镜像地址与配置**：`kubectl_get_yaml` 显示 Pod 指定镜像为 `registry.invalid/aiops/private-rootcause:v0`，且依赖的 `imagePullSecret` 不存在。\n\n结论：当前 Pod `rc-imagepull-missing-secret` 处于 `ImagePullBackOff` 状态，根本原因是缺少必要的 `imagePullSecret` 用于私有镜像仓库认证。镜像地址格式本身未显示明显错误，但仓库 `registry.invalid` 无法验证是否真实可访问。下一步建议检查镜像仓库地址是否正确、是否存在网络隔离或 TLS 问题。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"evidence-pod-rc-imagepull-missing-secret-imagepullsecret","description":"验证 Pod rc-imagepull-missing-secret 中引用的 imagePullSecret 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-pull-secret -n aiops-e2e","purpose":"确认 imagePullSecret 是否存在","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"evidence-pod-rc-imagepull-missing-secret-events","description":"查看 Pod rc-imagepull-missing-secret 的 Events 以获取镜像拉取失败的详细原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-missing-secret","purpose":"确认镜像拉取失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"evidence-pod-rc-imagepull-missing-secret-image","description":"查看 Pod rc-imagepull-missing-secret 的镜像地址以确认格式是否正确","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-imagepull-missing-secret -n aiops-e2e -o yaml","purpose":"确认镜像地址是否正确","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | evidence-pod-... | critical | ✅ | kubectl_get_by_name | 验证 Pod rc-imagepull-missing-secret 中引用的 image... | `kubectl get secret rc-definitely-missing-pull-secret -n aiops-e2e` |
   | evidence-pod-... | critical | ✅ | kubectl_events | 查看 Pod rc-imagepull-missing-secret 的 Events 以... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-image...` |
   | evidence-pod-... | important | ✅ | kubectl_get_yaml | 查看 Pod rc-imagepull-missing-secret 的镜像地址以确认格式... | `kubectl get pod rc-imagepull-missing-secret -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (23.5s)
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
   ✅ [汇总总结] 完成 (2m 17.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4362 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 3.0s
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
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-imagepull-missing-secret |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | Back-off pulling image "registry.invalid/aiops/private-rootcause:v0" |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ImagePullBackOff` | Pod 正在尝试拉取镜像，但失败并进入等待重试状态 |
| 2 | Events | `kubectl describe pod` | `Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"` | 镜像拉取失败，系统正在等待重试 |
| 3 | imagePullSecret | `kubectl get secret` | `secrets "rc-definitely-missing-pull-secret" not found` | Pod 指定的 imagePullSecret 不存在，导致认证失败 |
| 4 | Pod spec | `kubectl get pod -o yaml` | `imagePullSecrets: rc-definitely-missing-pull-secret` | Pod 配置了 imagePullSecret，但 Secret 不存在 |
| 5 | 镜像地址 | `kubectl get pod -o yaml` | `image: registry.invalid/aiops/private-rootcause:v0` | 拉取的镜像地址为 registry.invalid，可能是无效或私有仓库 |

### 证据关联分析
- **证据 #2 + #3 印证**：镜像拉取失败的 Events 与 imagePullSecret 不存在直接关联，表明认证失败是根本原因。
- **证据链**：Pod 指定了不存在的 imagePullSecret → 无法认证私有仓库 → 镜像拉取失败 → Pod 处于 ImagePullBackOff 状态。

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod rc-imagepull-missing-secret 指定了不存在的 imagePullSecret  │
│ `rc-definitely-missing-pull-secret`，导致无法认证私有仓库 registry.invalid/aiops/private-rootcause:v0 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ imagePullSecret 缺失 → 无法拉取私有镜像 registry.invalid/aiops/private-rootcause:v0 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod rc-imagepull-missing-secret 无法认证私有仓库，镜像拉取失败   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ImagePullBackOff，Events 显示 Back-off pulling image │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #2 (Events 显示 Back-off pulling image) 和证据 #3 (imagePullSecret 不存在)，问题的根本原因是**Pod 指定的 imagePullSecret 不存在，导致无法认证私有仓库 registry.invalid/aiops/private-rootcause:v0**，从而镜像拉取失败，Pod 处于 ImagePullBackOff 状态。
**置信度**：高 (95%)
- ✅ Events 明确显示镜像拉取失败
- ✅ `kubectl get secret` 证实 imagePullSecret 不存在
- ✅ Pod spec 中的 imagePullSecret 与缺失的 Secret 名称一致

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建缺失的 imagePullSecret**
```bash
kubectl create secret docker-registry rc-definitely-missing-pull-secret \
  -n aiops-e2e \
  --docker-server=registry.invalid \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email>
```
*依据*：证据 #3 显示 imagePullSecret 缺失，必须创建该 Secret 以认证私有仓库

**2. [可选] 删除并重建 Pod 以触发镜像重新拉取**
```bash
kubectl delete pod rc-imagepull-missing-secret -n aiops-e2e
```
*目的*：删除 Pod 后，Kubernetes 会尝试重新拉取镜像并使用新创建的 Secret

### 后续优化
1. **验证镜像地址是否有效**：确保 registry.invalid/aiops/private-rootcause:v0 存在且可拉取
2. **检查 imagePullPolicy**：确认是否设置了 `Always` 或 `IfNotPresent`
3. **配置镜像拉取失败告警**：监控 Pod 状态变化，及时发现镜像拉取失败

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 imagePullSecret 存在 | `kubectl get secret rc-definitely-missing-pull-secret -n aiops-e2e` | 应显示 Secret 详情 |
| 2. 确认 Pod 状态 | `kubectl get pod rc-imagepull-missing-secret -n aiops-e2e` | STATUS: Running |
| 3. 检查 Events | `kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e` | 不再出现 Back-off pulling image |
| 4. 检查镜像是否已拉取 | `kubectl get pod -o jsonpath='{.spec.containers[0].image}'` | registry.invalid/aiops/private-rootcause:v0 |

---

## ⚠️ 注意事项
- 如果 registry.invalid 是测试环境或私有仓库，请确认网络和 DNS 解析是否正常
- 如果问题仍然存在，请检查节点是否能访问 registry.invalid（如使用 `curl` 或 `telnet`）
- 避免在生产环境中硬编码 imagePullSecret，建议通过 Helm、Kustomize 或 CI/CD 流水线注入 Secret

---

## 📊 性能统计

├─ 总耗时: 5.0m
├─ 问题定位: 42.6s (14%) ✅
├─ 证据链采集: 99.3s (33%) ✅
├─ 根因分析: 23.5s (8%) ✅
├─ 汇总总结: 137.6s (45%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
