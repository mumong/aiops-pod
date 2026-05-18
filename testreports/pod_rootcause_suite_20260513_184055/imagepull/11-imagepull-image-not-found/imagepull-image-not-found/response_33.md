======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 9578053cf22b41c2]

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
28m (x5 over 93m)       Warning   Failed    Pod/rc-imagepull-not-found   Failed to pull image "registry.k8s.io/pause:definitely-not-existing-rootcause-tag": rpc error: code =
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-imagepull-not-found
namespace: aiops-e2e
creationTimestamp: 2026-05-14T08:48:00Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <n
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": [
    "L3"
  ],
  "layer_name": "ImagePullFailed",
  "confidence": "high",
  "reasoning": "异常 Pod 'rc-imagepull-not-found' 的状态为 ImagePullBackOff，Events 显示 'i/o timeout'，表明镜像仓库网络不可达。诊断显示镜像 'registry.k8s.io/pause:definitely-not-existing-rootcause-tag' 无法拉取，且没有 imagePullSecret。此问题属于镜像拉取失败（L3）。",
  "abnormal_pods": [
    {
      "name": "rc-imagepull-not-found",
      "namespace": "aiops-e2e",
      "status": "ImagePullBackOff",
      "reason": "Failed to pull image",
      "message": "dial tcp 74.125.204.82:443: i/o timeout"
    }
  ],
  "abnormal_groups": {
    "ImagePullFailed": [
      "rc-imagepull-not-found"
    ]
  },
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "ImagePullFailed",
  "key_entities": [
    {
      "type": "Pod",
      "name": "rc-imagepull-not-found",
      "namespace": "aiops-e2e"
    },
    {
      "type": "Image",
      "name": "registry.k8s.io/pause:definitely-not-existing-rootcause-tag"
    }
  ],
  "possible_scenarios": [
    "镜像仓库网络不可达导致镜像拉取失败",
    "缺少或错误的 imagePullSecret",
    "镜像名称或 tag 不存在"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 26.9s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像仓库网络不可达导致镜像拉取失败', 'probability': 'high', 'reason': "Events 显示 'i/o timeout'，说明镜像仓库网络不可达"}, {'scenario': '缺少或错误的 imagePullSecret', 'probability': 'high', 'reason': 'Pod 未配置 imagePullSecret'}, {'scenario': '镜像名称或 tag 不存在', 'probability': 'high', 'reason': "镜像地址 'registry.k8s.io/pause:definitely-not-existing-rootcause-tag' 不存在"}]
   entities=[{"type": "Pod", "name": "rc-imagepull-not-found", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.k8s.io/pause:definitely-not-existing-rootcause-tag", "namespace": ""}]
   reasoning=异常 Pod 'rc-imagepull-not-found' 的状态为 ImagePullBackOff，Events 显示 'i/o timeout'，表明镜像仓库网络不可达。诊断显示镜像 'registry.k8s.io/pause:definitely-not-existing-rootcause-tag' 无法拉取，且没有 imagePullSecret。此问题属于镜像拉取失败（L3）。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "ImagePullFailed", "confidence": 1.0, "reasoning": "异常 Pod 'rc-imagepull-not-found' 的状态为 ImagePullBackOff，Events 显示 'i/o timeout'，表明镜像仓库网络不可达。诊断显示镜像 'registry.k8s.io/pause:definitely-not-existing-rootcause-tag' 无法拉取，且没有 imagePullSecret。此问题属于镜像拉取失败（L3）。", "abnormal_pods": [{"name": "rc-imagepull-not-found", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "ImagePullFailed", "key_entities": [{"type": "Pod", "name": "rc-imagepull-not-found", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.k8s.io/pause:definitely-not-existing-rootcause-tag", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达导致镜像拉取失败", "probability": "high", "reason": "Events 显示 'i/o timeout'，说明镜像仓库网络不可达"}, {"scenario": "缺少或错误的 imagePullSecret", "probability": "high", "reason": "Pod 未配置 imagePullSecret"}, {"scenario": "镜像名称或 tag 不存在", "probability": "high", "reason": "镜像地址 'registry.k8s.io/pause:definitely-not-existing-rootcause-tag' 不存在"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-not-found"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-not-found"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-not-found                              0/1     ImagePullBackOff   0             98m    172.16.166.175   node1    <none>           <none>            app=rc-imagepull-not-found,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/9578053cf22b41c2/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/9578053cf22b41c2/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/9578053cf22b41c2/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-not-found
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   30m (x5 over 95m)     kubelet  Failed to pull image "registry.k8
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 19.0s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-imagepull-not-found 的详细信息以验证镜像拉取失败的具体原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-not-found -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-imagepull-not-found","namespace":"aiops-e2e"},"purpose":"验证镜像拉取失败的具体原因，例如镜像名称、imagePullSecret 是否缺失","evidence_type":"current_state","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-imagepull-not-found 的 Events 以确认镜像拉取失败的具体错误信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-not-found","tool_args":{"kind":"Event","namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-imagepull-not-found"},"purpose":"确认镜像拉取失败的具体错误信息，例如 'i/o timeout'","evidence_type":"event_signal","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod rc-imagepull-not-found 的 YAML 配置以验证 imagePullSecret 是否缺失","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-imagepull-not-found -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-imagepull-not-found","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 Pod 是否配置了 imagePullSecret","evidence_type":"configuration","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-not-found\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   30m (x5 over 95m)     kubelet  Failed to pull image \"registry.k8s.io/pause:definitely-not-existing-rootcause-tag\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/pause:definitely-not-existing-rootcause-tag\": failed to resolve reference \"registry.k8s.io/pause:definitely-not-existing-rootcause-tag\": failed to do request: Head \"https://europe-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/pause/manifests/definitely-not-existing-rootcause-tag\": dial tcp 74.125.204.82:443: i/o timeout\n  Normal   BackOff  65s (x391 over 100m)  kubelet  Back-off pulling image \"registry.k8s.io/pause:definitely-not-existing-rootcause-tag\"\n      Reason:       ImagePullBackOff\n                  cni.projectcalico.org/containerID: 3f9ee302bd7902dc441225739145345a525e16df39cd8ae32620ab7e9d3cfbff\n                  cni.projectcalico.org/podIP: 172.16.166.175/32\n                  cni.projectcalico.org/podIPs: 172.16.166.175/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed\n    State:          Waiting","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9578053cf22b41c2/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9578053cf22b41c2/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9578053cf22b41c2/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 4 个，匹配计划 3 个，未规划证据 1 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":4,"matched_tool_count":3,"unplanned_tool_count":1,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-imagepull-not-found 的详细信息以验证镜像拉取失败的具体原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-not-found -n aiops-e2e","purpose":"验证镜像拉取失败的具体原因，例如镜像名称、imagePullSecret 是否缺失","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod rc-imagepull-not-found 的 Events 以确认镜像拉取失败的具体错误信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-not-found","purpose":"确认镜像拉取失败的具体错误信息，例如 'i/o timeout'","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e3","description":"获取 Pod rc-imagepull-not-found 的 YAML 配置以验证 imagePullSecret 是否缺失","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-imagepull-not-found -n aiops-e2e -o yaml","purpose":"验证 Pod 是否配置了 imagePullSecret","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod rc-imagepull-not-found 的详细信息以验证镜像拉取失败的... | `kubectl describe pod rc-imagepull-not-found -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取 Pod rc-imagepull-not-found 的 Events 以确认镜像拉... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-image...` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 Pod rc-imagepull-not-found 的 YAML 配置以验证 im... | `kubectl get pod rc-imagepull-not-found -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (27.0s)
   📤 → 下游数据: root_cause=异常 Pod 'rc-imagepull-not-found' 的状态为 ImagePullBackOff，Events 显示 'i/o timeout'，表明镜像仓库网络不可达。诊断显示镜像 'registry.k8s.io/pause:definitely-not-existing-rootcause-tag' 无法拉取，且没有 imagePullSecret。此问题属于镜像拉取失败（L3）
   confidence=100%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "异常 Pod 'rc-imagepull-not-found' 的状态为 ImagePullBackOff，Events 显示 'i/o timeout'，表明镜像仓库网络不可达。诊断显示镜像 'registry.k8s.io/pause:definitely-not-existing-rootcause-tag' 无法拉取，且没有 imagePullSecret。此问题属于镜像拉取失败（L3）", "root_cause_summary": "异常 Pod 'rc-imagepull-not-found' 的状态为 ImagePullBackOff，Events 显示 'i/o timeout'，表明镜像仓库网络不可达。诊断显示镜像 'registry.k8s.io/pause:definitely-not-existing-rootcause-tag' 无法拉取，且没有 imagePullSecret。此问题属于镜像拉取失败（L3）", "confidence": 1.0, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": "证据清点：\n1. kubectl_describe 显示 Pod 'rc-imagepull-not-found' 的状态为 Pending，且有多个 Warning 事件表明镜像拉取失败。\n2. kubectl_events 显示 'i/o timeout' 错误，表明镜像仓库网络不可达。\n3. kubectl_get_yaml 显示 Pod 未配置 imagePullSecret。\n\n逐条分析：\n1. kubectl_describe 显示镜像拉取失败的具体错误信息，表明镜像仓库网络不可达。\n2. kubectl_events 显示 'i/o timeout' 错误，表明镜像仓库网络不可达。\n3. kubectl_get_yaml 显示 Pod 未配置 imagePullSecret，可能导致镜像拉取失败。\n\n关联分析：\n1. 镜像仓库网络不可达导致镜像拉取失败。\n2. 镜像拉取失败导致 Pod 状态为 ImagePullBackOff。\n\n因果链构建：\n1. 镜像仓库网络不可达 → 镜像拉取失败 → Pod 状态为 ImagePullBackOff\n\n置信度评估：\n1. 有直接证\n... 截断，原始 517 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 异常 Pod 'rc-imagepull-not-found' 的状态为 ImagePullBackOff，Events 显示 'i/o timeout'，表明镜像仓库网络不可达。诊断显示镜像 'registry.k8s.io/pause:definitely-not-existing-rootca...
   置信度: 100%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 9.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4165 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 22.4s
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
| **置信度** | 高 (100%) |
| **证据完整度** | 3/3 (100%) |

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
| 错误信息 | i/o timeout |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `STATUS: ImagePullBackOff` | Pod 无法启动，镜像拉取失败 |
| 2 | Pod Events | `kubectl describe pod rc-imagepull-not-found -n aiops-e2e` | `Failed to pull image "registry.k8s.io/pause:definitely-not-existing-rootcause-tag": i/o timeout` | 镜像仓库网络不可达 |
| 3 | Pod YAML 配置 | `kubectl get pod rc-imagepull-not-found -n aiops-e2e -o yaml` | `imagePullSecrets: <absent>` | 缺少 imagePullSecret，无法认证私有仓库 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `ImagePullBackOff`，Events 显示 `i/o timeout`，说明镜像拉取失败的根本原因是网络不通。
- **证据 #3 印证**：Pod 缺少 `imagePullSecret`，进一步限制了拉取私有仓库镜像的可能性，但当前问题中，`i/o timeout` 指向网络问题，而非认证失败。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 镜像仓库实际连通性测试 | important | 无法确认是节点网络问题还是镜像仓库服务不可达 |
| 其他相同镜像拉取行为 | important | 无法判断是否为单一 Pod 问题或集群范围问题 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 镜像仓库 registry.k8s.io 不可达，网络连接超时（i/o timeout）      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 尝试拉取镜像 registry.k8s.io/pause:definitely-not-existing-rootcause-tag，但因网络不通失败 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod rc-imagepull-not-found 的镜像拉取失败，触发 kubelet 重试逻辑，进入 ImagePullBackOff 状态 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ImagePullBackOff，持续重试拉取镜像但失败              │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 ImagePullBackOff)、证据 #2 (Events 显示 i/o timeout) 和证据 #3 (Pod 缺少 imagePullSecret)，问题的根本原因是**镜像仓库 registry.k8s.io 不可达，导致镜像拉取失败**。

**置信度**：高 (100%)
- ✅ Pod 状态为 ImagePullBackOff
- ✅ Events 明确指出 i/o timeout
- ✅ Pod 缺少 imagePullSecret（次要原因）

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修复节点到镜像仓库的网络连接**

- **检查节点网络状态**：
  ```bash
  ping registry.k8s.io
  curl -v https://registry.k8s.io
  ```
  *目的*：确认节点是否能正常访问 registry.k8s.io

- **检查 DNS 解析**：
  ```bash
  nslookup registry.k8s.io
  dig registry.k8s.io
  ```
  *目的*：确认节点 DNS 是否能正确解析 registry.k8s.io

- **检查防火墙或网络策略**：
  ```bash
  iptables -L -n -v
  ```
  *目的*：确认是否有规则阻止访问 registry.k8s.io

**2. [可选] 配置 imagePullSecret**

如果镜像仓库是私有的，可为 Pod 配置 `imagePullSecret`：

```bash
kubectl create secret docker-registry regcred \
  --docker-server=registry.k8s.io \
  --docker-username=<your-name> \
  --docker-password=<your-pword> \
  --docker-email=<your-email> \
  -n aiops-e2e
```

然后在 Pod YAML 中添加：

```yaml
imagePullSecrets:
  - name: regcred
```

**3. [可选] 替换为镜像仓库可用的镜像地址**

如果当前镜像地址无效，可替换为已知存在的镜像，例如：

```bash
kubectl set image pod/rc-imagepull-not-found \
  container=registry.k8s.io/pause:latest \
  -n aiops-e2e
```

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-imagepull-not-found -n aiops-e2e` | STATUS: Running |
| 2. 检查镜像拉取状态 | `kubectl describe pod rc-imagepull-not-found -n aiops-e2e` | No Failed events |
| 3. 检查 Events | `kubectl get events -n aiops-e2e` | 无 Failed 或 Warning 事件 |

---

## ⚠️ 注意事项

- 如果镜像仓库是 GCP 的 registry (`europe-west2-docker.pkg.dev`)，请确认节点是否在 GCP VPC 中，或是否能通过 GCP 网络访问。
- 如果问题在多个 Pod 中出现，可能需要检查节点网络配置或集群的 DNS 设置。
- 如果镜像地址错误（如 tag 不存在），应更换为有效的镜像地址。

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 86.9s (33%) ✅
├─ 证据链采集: 79.0s (30%) ✅
├─ 根因分析: 27.0s (10%) ✅
├─ 汇总总结: 69.4s (26%) ✅
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
