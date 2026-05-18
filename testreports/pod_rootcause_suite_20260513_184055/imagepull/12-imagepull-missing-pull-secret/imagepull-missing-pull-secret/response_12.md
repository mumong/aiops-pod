======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c5cb0906f5944deb]

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
28m (x4 over 29m)       Warning   Failed           Pod/rc-imagepull-missing-secret   Failed to pull image "registry.invalid/aiops/private-rootcause:v0": rpc error: code = Unk
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS             RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-imagepull-missing-secret   0/1     ImagePullBackOff   0 
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": [
    "L3"
  ],
  "layer_name": "ImagePullFailed",
  "confidence": 0.95,
  "reasoning": "检测到 Pod 'rc-imagepull-missing-secret' 处于 'ImagePullBackOff' 状态，且 Events 显示镜像拉取失败，错误信息为 DNS 解析失败（'lookup registry.invalid on 127.0.0.53:53: no such host'），表明镜像仓库地址不可达或存在 DNS 配置问题。根据 runbook 'pod-imagepull-failed.md' 的诊断规则，这属于 L3 异常类型，与镜像拉取失败相关。",
  "abnormal_pods": [
    {
      "name": "rc-imagepull-missing-secret",
      "namespace": "aiops-e2e",
      "status": "ImagePullBackOff",
      "age": "29m",
      "ip": "172.16.166.166",
      "node": "node1"
    }
  ],
  "abnormal_groups": [
    "ImagePullFailed"
  ],
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "L3",
  "key_entities": [
    "Pod rc-imagepull-missing-secret",
    "镜像 registry.invalid/aiops/private-rootcause:v0",
    "DNS 解析失败"
  ],
  "possible_scenarios": [
    "镜像仓库地址错误或无法访问",
    "DNS 配置问题导致无法解析 registry.invalid",
    "缺少或错误的 imagePullSecret 导致认证失败",
    "镜像仓库网络隔离或防火墙限制"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 22.5s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像仓库地址错误或无法访问', 'probability': 'high', 'reason': 'Events 显示镜像仓库地址不可达'}, {'scenario': 'DNS 配置问题导致无法解析 registry.invalid', 'probability': 'high', 'reason': 'Events 显示 lookup registry.invalid on 127.0.0.53:53: no such host'}, {'scenario': '缺少或错误的 imagePullSecret 导致认证失败', 'probability': 'medium', 'reason': '镜像拉取失败可能与认证缺失有关'}, {'scenario': '镜像仓库网络隔离或防火墙限制', 'probability': 'medium', 'reason': '镜像仓库可能被隔离或有访问限制'}]
   entities=[{"type": "Pod", "name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.invalid/aiops/private-rootcause:v0", "namespace": ""}, {"type": "Error", "name": "DNS 解析失败", "namespace": ""}]
   reasoning=检测到 Pod 'rc-imagepull-missing-secret' 处于 'ImagePullBackOff' 状态，且 Events 显示镜像拉取失败，错误信息为 DNS 解析失败（'lookup registry.invalid on 127.0.0.53:53: no such host'），表明镜像仓库地址不可达或存在 DNS 配置问题。根据 runbook 'pod-imagepull-failed.md' 的诊断规则，这属于 L3 异常类型，与镜像拉取失败相关。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "检测到 Pod 'rc-imagepull-missing-secret' 处于 'ImagePullBackOff' 状态，且 Events 显示镜像拉取失败，错误信息为 DNS 解析失败（'lookup registry.invalid on 127.0.0.53:53: no such host'），表明镜像仓库地址不可达或存在 DNS 配置问题。根据 runbook 'pod-imagepull-failed.md' 的诊断规则，这属于 L3 异常类型，与镜像拉取失败相关。", "abnormal_pods": [{"name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "Pod", "name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.invalid/aiops/private-rootcause:v0", "namespace": ""}, {"type": "Error", "name": "DNS 解析失败", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库地址错误或无法访问", "probability": "high", "reason": "Events 显示镜像仓库地址不可达"}, {"scenario": "DNS 配置问题导致无法解析 registry.invalid", "probability": "high", "reason": "Events 显示 lookup registry.invalid on 127.0.0.53:53: no such host"}, {"scenario": "缺少或错误的 imagePullSecret 导致认证失败", "probability": "medium", "reason": "镜像拉取失败可能与认证缺失有关"}, {"scenario": "镜像仓库网络隔离或防火墙限制", "probability": "medium", "reason": "镜像仓库可能被隔离或有访问限制"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-missing-secret                         0/1     ImagePullBackOff   0             29m    172.16.166.166   node1    <none>           <none>            app=rc-imagepull-missing-secret,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/c5cb0906f5944deb/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c5cb0906f5944deb/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c5cb0906f5944deb/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-missing-secret
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          30m (x4 over 31m)    kubelet            Failed to pu
   💭 [证据链采集] 已采集证据：
1. `kubectl_describe` 显示 Pod `rc-imagepull-missing-secret` 处于 Pending 状态，且镜像拉取失败，错误信息为 DNS 解析失败（`lookup registry.invalid on 127.0.0.53:53: no such host`）。
2. 事件记录显示镜像拉取失败的具体原因：`Failed to pull image "registry.invalid/aiops/private-rootcause:v0"`，并提示 `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host`，这表明镜像仓库地址无法解析，可能是 DNS 配置问题或镜像地址错误。

未采集证据：
1. 没有执行针对 `imagePullSecret` 的验证，以确认是否存在认证问题。
2. 没有执行节点级别的网络诊断（如 `nslookup` 或 `dig`）来确认节点是否能解析 `registry.invalid`。

冲突证据：
无。
   ✅ [证据链采集] 完成 (1m 10.4s)
   📤 → 下游数据: evidence_items=4/4
   evidence_analysis={"evidence_plan":[{"id":"image-pull-failure-validation","description":"验证镜像拉取失败的原因，包括镜像地址、DNS解析、imagePullSecret和网络连通性","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e","tool_args":{"pod":"rc-imagepull-missing-secret","namespace":"aiops-e2e"},"purpose":"确认镜像拉取失败的具体原因，包括镜像地址、DNS解析、imagePullSecret和网络连通性","evidence_type":"current_state","target_scope":"aiops-e2e/rc-imagepull-missing-secret","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_events","kubectl_get_yaml","kubectl_find_resource","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-missing-secret\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          30m (x4 over 31m)    kubelet            Failed to pull image \"registry.invalid/aiops/private-rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/private-rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/private-rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/private-rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n  Normal   BackOff         91s (x135 over 31m)  kubelet            Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"\n      Reason:       ErrImagePull\n  Warning  Failed          30m (x6 over 31m)    kubelet            Error: ImagePullBackOff\n  Warning  Failed          30m (x4 over 31m)    kubelet            Error: ErrImagePull\n                  cni.projectcalico.org/containerID: 15f21d5a2bf23a2e830e964c48d8c66a8fd40e50e94b550106a5ce8726d9507f\n                  cni.projectcalico.org/podIP: 172.16.166.166/32\n                  cni.projectcalico.org/podIPs: 172.16.166.166/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed\n    State:          Waiting","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c5cb0906f5944deb/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c5cb0906f5944deb/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c5cb0906f5944deb/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_describe` 显示 Pod `rc-imagepull-missing-secret` 处于 Pending 状态，且镜像拉取失败，错误信息为 DNS 解析失败（`lookup registry.invalid on 127.0.0.53:53: no such host`）。\n2. 事件记录显示镜像拉取失败的具体原因：`Failed to pull image \"registry.invalid/aiops/private-rootcause:v0\"`，并提示 `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host`，这表明镜像仓库地址无法解析，可能是 DNS 配置问题或镜像地址错误。\n\n未采集证据：\n1. 没有执行针对 `imagePullSecret` 的验证，以确认是否存在认证问题。\n2. 没有执行节点级别的网络诊断（如 `nslookup` 或 `dig`）来确认节点是否能解析 `registry.invalid`。\n\n冲突证据：\n无。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 4/4 项，完整度 100%；实际执行工具 4 个，匹配计划 1 个，未规划证据 3 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":4,"environment_evidence_collected":4,"environment_evidence_completeness":1.0,"executed_tool_count":4,"matched_tool_count":1,"unplanned_tool_count":3,"evidence_inventory":[{"id":"image-pull-failure-validation","description":"验证镜像拉取失败的原因，包括镜像地址、DNS解析、imagePullSecret和网络连通性","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e","purpose":"确认镜像拉取失败的具体原因，包括镜像地址、DNS解析、imagePullSecret和网络连通性","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | image-pull-fa... | critical | ✅ | kubectl_describe | 验证镜像拉取失败的原因，包括镜像地址、DNS解析、imagePullSecret和网络连通性 | `kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (23.8s)
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
   ✅ [汇总总结] 完成 (1m 7.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4114 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 4.6s
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
| **问题分类** | ImagePullFailed（镜像拉取失败） |
| **置信度** | 高 (95%) |
| **证据完整度** | 1/1 (100%) |

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
| 错误信息 | lookup registry.invalid on 127.0.0.53:53: no such host |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ImagePullBackOff` | Pod 因镜像拉取失败进入 ImagePullBackOff 状态 |
| 2 | Events | `kubectl events` | `Failed to pull image "registry.invalid/aiops/private-rootcause:v0": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | DNS 解析失败导致镜像拉取失败 |
| 3 | Describe Pod | `kubectl describe pod` | `Warning: Failed to pull image` | 确认镜像拉取失败的具体错误信息 |
| 4 | 镜像地址 | `kubectl describe pod` | `Image: registry.invalid/aiops/private-rootcause:v0` | 确认镜像地址为 registry.invalid |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 处于 ImagePullBackOff 状态，Events 显示 DNS 解析失败，确认镜像拉取失败的原因是 DNS 无法解析 registry.invalid。
- **证据链**：Pod 尝试拉取镜像 → DNS 解析失败 → 镜像拉取失败 → Pod 进入 ImagePullBackOff 状态。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| imagePullSecret 配置 | medium | 无法确认是否因认证失败导致镜像拉取失败 |
| 节点网络连通性 | medium | 无法确认是否因节点网络问题导致 registry.invalid 不可达 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ DNS 解析失败导致 registry.invalid 不可达                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 镜像拉取时尝试解析 registry.invalid，但 DNS 解析失败            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 镜像拉取失败（Failed to pull image），错误信息为 DNS 解析失败   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 ImagePullBackOff，持续尝试拉取镜像                     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (Events 中的 `lookup registry.invalid on 127.0.0.53:53: no such host`) 和证据 #4 (镜像地址为 `registry.invalid`)，问题的根本原因是**DNS 无法解析 registry.invalid，导致镜像拉取失败**。
**置信度**：高 (95%)
- ✅ Events 明确指出 DNS 解析失败
- ✅ Describe Pod 显示镜像地址为 registry.invalid
- ⚠️ 缺少 imagePullSecret 和节点网络检查，无法确认是否为其他原因导致的镜像拉取失败

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修复 DNS 配置或使用可解析的 registry 地址**
```bash
# 如果 registry.invalid 是错误的域名，请修改镜像地址为正确的 registry
kubectl set image deployment/<name> -n <namespace> <container>=<correct-registry>/aiops/private-rootcause:v0
```
*依据*：Events 显示 registry.invalid 无法解析，需确保镜像地址正确且可解析。

**2. [可选] 检查节点 DNS 配置**
```bash
# 在节点上执行 DNS 解析测试
nslookup registry.invalid
```
*目的*：确认节点是否能解析 registry.invalid，排查节点 DNS 配置问题。

**3. [可选] 检查 imagePullSecret 配置**
```bash
# 查看 Pod 使用的 imagePullSecret
kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e

# 查看 Secret 内容
kubectl get secret <secret-name> -n aiops-e2e -o yaml
```
*目的*：确认镜像拉取失败是否与认证缺失有关。

### 后续优化
1. **配置镜像地址验证机制**：确保镜像地址正确、可解析。
2. **配置镜像拉取失败告警**：监控 Pod 状态变化，及时发现镜像拉取失败。
3. **配置镜像仓库高可用或镜像缓存**：避免单一 registry 不可达导致拉取失败。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-imagepull-missing-secret -n aiops-e2e` | STATUS: Running |
| 2. 检查 Events | `kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e` | 无 "Failed to pull image" 错误 |
| 3. 检查 DNS 解析 | `nslookup registry.invalid` | registry.invalid 被正确解析 |

---
## ⚠️ 注意事项
- 如果 registry.invalid 是内部域名，请确保集群节点的 DNS 配置正确。
- 如果 registry.invalid 是外部域名，请确认其存在且可访问。
- 如果镜像仓库为私有仓库，确保 imagePullSecret 正确配置并绑定到 Pod。

---

## 📊 性能统计

├─ 总耗时: 4.1m
├─ 问题定位: 82.5s (34%) ✅
├─ 证据链采集: 70.4s (29%) ✅
├─ 根因分析: 23.8s (10%) ✅
├─ 汇总总结: 67.9s (28%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 5 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed
- **工具调用**: 5 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
