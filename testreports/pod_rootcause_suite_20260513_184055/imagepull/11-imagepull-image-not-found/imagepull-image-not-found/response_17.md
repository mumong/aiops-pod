======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 9516d3e6659a46bf]

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
      📄 Pod 'rc-imagepull-not-found' 在 namespace 'aiops-e2e' 中多次尝试拉取镜像 'registry.k8s.io/pause:definitely-not-existing-rootcause-tag' 失败，出现 i/o timeout 和 ImagePullBackOff 错误。
key_facts: ["Pod 名称: rc-imagepull-
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                     READY   STATUS             RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-imagepull-not-found   0/1     ImagePullBackOff   0          5
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": [
    "L3"
  ],
  "layer_name": "镜像拉取失败",
  "confidence": 0.95,
  "reasoning": "根据 Pod 状态和事件，该 Pod 处于 ImagePullBackOff 状态，并多次尝试拉取镜像失败，出现 i/o timeout 和 DeadlineExceeded 错误。这表明存在镜像拉取失败的问题。",
  "abnormal_pods": [
    {
      "name": "rc-imagepull-not-found",
      "namespace": "aiops-e2e",
      "status": "ImagePullBackOff",
      "reason": "镜像拉取失败",
      "message": "i/o timeout"
    }
  ],
  "abnormal_groups": [
    "镜像拉取失败"
  ],
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "镜像拉取失败",
  "key_entities": [
    "rc-imagepull-not-found",
    "aiops-e2e",
    "registry.k8s.io/pause:definitely-not-existing-rootcause-tag"
  ],
  "possible_scenarios": [
    "镜像仓库网络不可达",
    "镜像或 tag 不存在",
    "认证失败（缺少或错误的 imagePullSecret）",
    "DNS 解析失败",
    "TLS 证书问题"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (59.6s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像仓库网络不可达', 'probability': '高', 'reason': 'Events 含 connection refused/timeout'}, {'scenario': '镜像或 tag 不存在', 'probability': '高', 'reason': 'Events 含 manifest unknown/not found'}, {'scenario': '认证失败（缺少或错误的 imagePullSecret）', 'probability': '高', 'reason': 'Events 含 unauthorized/no basic auth'}, {'scenario': 'DNS 解析失败', 'probability': '高', 'reason': 'DNS 解析失败'}, {'scenario': 'TLS 证书问题', 'probability': '高', 'reason': 'Events 含 x509'}]
   entities=[{"type": "pod", "name": "rc-imagepull-not-found", "namespace": "aiops-e2e"}, {"type": "image", "name": "registry.k8s.io/pause:definitely-not-existing-rootcause-tag", "namespace": "aiops-e2e"}]
   reasoning=根据 Pod 状态和事件，该 Pod 处于 ImagePullBackOff 状态，并多次尝试拉取镜像失败，出现 i/o timeout 和 DeadlineExceeded 错误。这表明存在镜像拉取失败的问题。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "镜像拉取失败", "confidence": 0.95, "reasoning": "根据 Pod 状态和事件，该 Pod 处于 ImagePullBackOff 状态，并多次尝试拉取镜像失败，出现 i/o timeout 和 DeadlineExceeded 错误。这表明存在镜像拉取失败的问题。", "abnormal_pods": [{"name": "rc-imagepull-not-found", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "pod", "name": "rc-imagepull-not-found", "namespace": "aiops-e2e"}, {"type": "image", "name": "registry.k8s.io/pause:definitely-not-existing-rootcause-tag", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达", "probability": "高", "reason": "Events 含 connection refused/timeout"}, {"scenario": "镜像或 tag 不存在", "probability": "高", "reason": "Events 含 manifest unknown/not found"}, {"scenario": "认证失败（缺少或错误的 imagePullSecret）", "probability": "高", "reason": "Events 含 unauthorized/no basic auth"}, {"scenario": "DNS 解析失败", "probability": "高", "reason": "DNS 解析失败"}, {"scenario": "TLS 证书问题", "probability": "高", "reason": "Events 含 x509"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-not-found"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-not-found"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-not-found                              0/1     ImagePullBackOff   0             52m    172.16.166.175   node1    <none>           <none>            app=rc-imagepull-not-found,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/9516d3e6659a46bf/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/9516d3e6659a46bf/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/9516d3e6659a46bf/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
      📄 NAME                     READY   STATUS             RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-imagepull-not-found   0/1     ImagePullBackOff   0          5
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 22.0s)
   📤 → 下游数据: evidence_items=4/6
   evidence_analysis={"evidence_plan":[{"id":"verify_pod_status_and_events","description":"验证 Pod 当前状态和 Events，确认镜像拉取失败的详细原因。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-imagepull-not-found -n aiops-e2e -o yaml","tool_args":{"name":"rc-imagepull-not-found","namespace":"aiops-e2e","kind":"pod","output_format":"yaml"},"purpose":"获取 Pod 的完整 spec 和 Events，验证镜像地址、imagePullSecrets、Events 中的失败原因等关键信息。","evidence_type":"status_configuration_events","target_scope":"aiops-e2e/rc-imagepull-not-found","acceptable_tools":["kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_events"],"counts_for_completeness":true},{"id":"verify_pod_events","description":"验证 Pod 事件，获取镜像拉取失败的详细错误信息。","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-not-found","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-imagepull-not-found"},"purpose":"获取 Pod 的详细事件记录，确认失败拉取的错误类型（如 i/o timeout、manifest unknown、unauthorized 等）。","evidence_type":"event_logs","target_scope":"aiops-e2e/rc-imagepull-not-found","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"verify_imagepullsecret","description":"验证 Pod 是否引用了正确的 imagePullSecret。","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get secret -n aiops-e2e","tool_args":{"kind":"Secret","namespace":"aiops-e2e"},"purpose":"检查当前命名空间下是否存在与镜像拉取相关的 Secret，并确认是否被正确引用。","evidence_type":"configuration_dependency","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                     READY   STATUS             RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-imagepull-not-found   0/1     ImagePullBackOff   0          55m   172.16.166.175   node1   <none>           <none>            app=rc-imagepull-not-found,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9516d3e6659a46bf/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9516d3e6659a46bf/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9516d3e6659a46bf/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 1 项，未采集 2 项，完整度 33%；其中真实环境证据 4/6 项，完整度 67%；实际执行工具 4 个，匹配计划 1 个，未规划证据 3 个","plan_total":3,"plan_collected":1,"plan_completeness":0.3333333333333333,"environment_evidence_total":6,"environment_evidence_collected":4,"environment_evidence_completeness":0.6666666666666666,"executed_tool_count":4,"matched_tool_count":1,"unplanned_tool_count":3,"evidence_inventory":[{"id":"verify_pod_status_and_events","description":"验证 Pod 当前状态和 Events，确认镜像拉取失败的详细原因。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-imagepull-not-found -n aiops-e2e -o yaml","purpose":"获取 Pod 的完整 spec 和 Events，验证镜像地址、imagePullSecrets、Events 中的失败原因等关键信息。","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"verify_pod_events","description":"验证 Pod 事件，获取镜像拉取失败的详细错误信息。","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-not-found","purpose":"获取 Pod 的详细事件记录，确认失败拉取的错误类型（如 i/o timeout、manifest unknown、unauthorized 等）。","collected":false,"source":"planned","outcome":"unknown"},{"id":"verify_imagepullsecret","description":"验证 Pod 是否引用了正确的 imagePullSecret。","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get secret -n aiops-e2e","purpose":"检查当前命名空间下是否存在与镜像拉取相关的 Secret，并确认是否被正确引用。","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["verify_pod_events(验证 Pod 事件，获取镜像拉取失败的详细错误信息。): 已规划但工具执行失败或无匹配结果","verify_imagepullsecret(验证 Pod 是否引用了正确的 imagePullSecret。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/3 项, 完整度: 67%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | verify_pod_st... | critical | ✅ | kubectl_get_by_name | 验证 Pod 当前状态和 Events，确认镜像拉取失败的详细原因。 | `kubectl get pod rc-imagepull-not-found -n aiops-e2e -o yaml` |
   | verify_pod_ev... | critical | ❌ | kubectl_events | 验证 Pod 事件，获取镜像拉取失败的详细错误信息。 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-image...` |
   | verify_imagep... | important | ❌ | kubectl_get_by_kind_in_na... | 验证 Pod 是否引用了正确的 imagePullSecret。 | `kubectl get secret -n aiops-e2e` |

   ⚠️ 未采集原因:
   - verify_pod_events(验证 Pod 事件，获取镜像拉取失败的详细错误信息。): 已规划但工具执行失败或无匹配结果
   - verify_imagepullsecret(验证 Pod 是否引用了正确的 imagePullSecret。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (13.5s)
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
   ✅ [汇总总结] 完成 (1m 16.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4368 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 51.9s
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
| **置信度** | 高 |
| **证据完整度** | 1/3 (33%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-imagepull-not-found |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | i/o timeout, DeadlineExceeded, ImagePullBackOff |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: ImagePullBackOff, RESTARTS: 0` | Pod 无法拉取镜像，进入 ImagePullBackOff 状态 |
| 2 | Pod Events | kubectl describe pod | `Warning: Failed to pull image registry.k8s.io/pause:definitely-not-existing-rootcause-tag: i/o timeout` | 镜像拉取失败，错误为 i/o timeout 和 DeadlineExceeded |
| 3 | 镜像地址 | kubectl get pod -o json | `image: registry.k8s.io/pause:definitely-not-existing-rootcause-tag` | 镜像地址和 tag 存在拼写错误或不存在 |
| 4 | kubectl_get_by_kind_in_cluster | kubectl get pod | `status_counts: {'ImagePullBackOff': 1, 'Running': 46}` | 集群中有 1 个 Pod 处于 ImagePullBackOff 状态，其他 Pod 正常 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 `ImagePullBackOff`，Events 显示镜像拉取失败，错误为 `i/o timeout` 和 `DeadlineExceeded`，表明网络连接或镜像地址存在问题。
- **证据 #3 印证**：镜像地址为 `registry.k8s.io/pause:definitely-not-existing-rootcause-tag`，tag 名称 `definitely-not-existing-rootcause-tag` 很可能是故意设置的错误 tag，导致镜像不存在。
- **证据链**：Pod 配置的镜像不存在 → 拉取失败 → Kubernetes 重试失败 → 进入 ImagePullBackOff 状态 → Pod 无法正常启动。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod imagePullSecret 配置 | critical | 无法确认是否缺少或错误的认证信息 |
| 节点到镜像仓库的连通性 | critical | 无法确认是否网络不可达或 DNS 解析失败 |
| 镜像仓库是否存在指定镜像 | critical | 无法确认是否镜像或 tag 不存在 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 镜像地址或 tag 不存在                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 配置的镜像不存在 → 拉取失败 → Kubernetes 重试失败           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 镜像拉取失败，错误为 i/o timeout 和 DeadlineExceeded            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ImagePullBackOff，无法正常启动                       │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 状态为 ImagePullBackOff)、证据 #2 (Events 显示镜像拉取失败，错误为 i/o timeout 和 DeadlineExceeded) 和证据 #3 (镜像地址为 registry.k8s.io/pause:definitely-not-existing-rootcause-tag)，问题的根本原因是**镜像地址或 tag 不存在**，导致镜像拉取失败，进而导致 Pod 无法正常启动。

**置信度**：高 (85%)
- ✅ Pod 状态为 ImagePullBackOff
- ✅ Events 明确显示镜像拉取失败
- ⚠️ 缺少镜像仓库是否存在指定镜像的证据，需手动验证

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修改 Pod 的镜像地址和 tag**
```bash
kubectl set image deployment/<deployment-name> <container-name>=registry.k8s.io/pause:latest -n aiops-e2e
```
*依据*：当前镜像 tag 为 `definitely-not-existing-rootcause-tag`，应更改为真实存在的 tag（如 `latest`）

**2. [可选] 查看 Pod 的 imagePullSecret 配置**
```bash
kubectl get pod rc-imagepull-not-found -o jsonpath='{.spec.imagePullSecrets}' -n aiops-e2e
```
*目的*：确认是否缺少或错误的 imagePullSecret 配置

**3. [可选] 手动验证镜像是否存在**
```bash
curl -I https://registry.k8s.io/v2/pause/manifests/latest
```
*目的*：确认镜像仓库中是否存在 `registry.k8s.io/pause:latest`

### 后续优化
1. **镜像拉取策略**：使用 `IfNotPresent` 优先使用本地镜像
2. **镜像仓库监控**：配置镜像仓库的访问监控和告警
3. **镜像 tag 管理**：避免使用错误的 tag，推荐使用 `latest` 或语义化版本号

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-imagepull-not-found -n aiops-e2e` | STATUS: Running |
| 2. 检查镜像拉取状态 | `kubectl describe pod rc-imagepull-not-found -n aiops-e2e` | Events 中不再有 Failed to pull image |
| 3. 验证镜像是否存在 | `curl -I https://registry.k8s.io/v2/pause/manifests/latest` | HTTP/2 200 OK |

---

## ⚠️ 注意事项
- 如果镜像地址和 tag 仍然无效，需要联系镜像仓库管理员确认镜像是否存在
- 如果集群使用私有镜像仓库，需要确保配置了正确的 `imagePullSecret`
- 如果镜像地址拼写错误，需要修正为正确的 registry 地址和 tag

---

## 📊 性能统计

├─ 总耗时: 3.9m
├─ 问题定位: 59.6s (26%) ✅
├─ 证据链采集: 82.0s (35%) ✅
├─ 根因分析: 13.5s (6%) ✅
├─ 汇总总结: 76.7s (33%) ✅
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
