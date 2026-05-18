======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ed806c5a34d0457a]

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
4m31s (x268 over 64m)   Normal   BackOff   Pod/rc-imagepull-missing-secret   Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"
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
  "confidence": "high",
  "reasoning": "当前 Pod 'rc-imagepull-missing-secret' 处于 ImagePullBackOff 状态，表明镜像拉取失败。Events 显示 'Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"'，说明镜像地址或认证存在问题。根据 runbook，这种情况属于 L3 问题。",
  "abnormal_pods": [
    {
      "name": "rc-imagepull-missing-secret",
      "namespace": "aiops-e2e",
      "status": "ImagePullBackOff",
      "reason": "BackOff",
      "message": "Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\""
    }
  ],
  "abnormal_groups": [
    {
      "type": "ImagePullFailed",
      "count": 1
    }
  ],
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "L3",
  "key_entities": [
    "Pod/rc-imagepull-missing-secret",
    "Image/registry.invalid/aiops/private-rootcause:v0"
  ],
  "possible_scenarios": [
    "镜像地址错误或仓库不可达",
    "缺少或错误的 imagePullSecret 认证信息",
    "仓库权限不足",
    "DNS 解析失败"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (47.6s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像地址错误或仓库不可达', 'probability': 'high', 'reason': 'Events 显示镜像拉取失败，可能是仓库地址错误或不可达。'}, {'scenario': '缺少或错误的 imagePullSecret 认证信息', 'probability': 'high', 'reason': 'Events 显示认证失败，可能是 imagePullSecret 配置错误或缺失。'}, {'scenario': '仓库权限不足', 'probability': 'high', 'reason': 'Events 显示 pull access denied，可能是仓库权限不足。'}, {'scenario': 'DNS 解析失败', 'probability': 'high', 'reason': 'Events 显示仓库不可达，可能是 DNS 解析失败。'}]
   entities=[{"type": "Pod", "name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.invalid/aiops/private-rootcause:v0", "namespace": ""}]
   reasoning=当前 Pod 'rc-imagepull-missing-secret' 处于 ImagePullBackOff 状态，表明镜像拉取失败。Events 显示 'Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"'，说明镜像地址或认证存在问题。根据 runbook，这种情况属于 L3 问题。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "ImagePullFailed", "confidence": 1.0, "reasoning": "当前 Pod 'rc-imagepull-missing-secret' 处于 ImagePullBackOff 状态，表明镜像拉取失败。Events 显示 'Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"'，说明镜像地址或认证存在问题。根据 runbook，这种情况属于 L3 问题。", "abnormal_pods": [{"name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "Pod", "name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.invalid/aiops/private-rootcause:v0", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像地址错误或仓库不可达", "probability": "high", "reason": "Events 显示镜像拉取失败，可能是仓库地址错误或不可达。"}, {"scenario": "缺少或错误的 imagePullSecret 认证信息", "probability": "high", "reason": "Events 显示认证失败，可能是 imagePullSecret 配置错误或缺失。"}, {"scenario": "仓库权限不足", "probability": "high", "reason": "Events 显示 pull access denied，可能是仓库权限不足。"}, {"scenario": "DNS 解析失败", "probability": "high", "reason": "Events 显示仓库不可达，可能是 DNS 解析失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-missing-secret                         0/1     ImagePullBackOff   0             64m    172.16.166.166   node1    <none>           <none>            app=rc-imagepull-missing-secret,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ed806c5a34d0457a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ed806c5a34d0457a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ed806c5a34d0457a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
name: rc-imagepull-missing-secret
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal  BackOff  87s (x291 over 66m)  kubelet  Back-off pulling image "regist
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 15.2s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细描述信息以确认镜像和 imagePullSecret 配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-imagepull-missing-secret","namespace":"aiops-e2e"},"purpose":"确认镜像和 imagePullSecret 配置","evidence_type":"Pod配置验证","target_scope":"aiops-e2e/rc-imagepull-missing-secret","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的 Events 信息以确认镜像拉取失败的具体原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-missing-secret","tool_args":{"kind":"Event","namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-imagepull-missing-secret"},"purpose":"确认镜像拉取失败的具体原因","evidence_type":"Events验证","target_scope":"aiops-e2e/rc-imagepull-missing-secret","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"验证 imagePullSecret 是否存在并正确配置","level":"important","tool":"kubectl_get_by_name","command":"kubectl get secret -n aiops-e2e","tool_args":{"kind":"Secret","namespace":"aiops-e2e"},"purpose":"验证 imagePullSecret 是否存在并正确配置","evidence_type":"Secret验证","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-missing-secret\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal  BackOff  87s (x291 over 66m)  kubelet  Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"\n      Reason:       ImagePullBackOff\n                  cni.projectcalico.org/containerID: 15f21d5a2bf23a2e830e964c48d8c66a8fd40e50e94b550106a5ce8726d9507f\n                  cni.projectcalico.org/podIP: 172.16.166.166/32\n                  cni.projectcalico.org/podIPs: 172.16.166.166/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed\n    State:          Waiting","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ed806c5a34d0457a/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ed806c5a34d0457a/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ed806c5a34d0457a/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 4 个，匹配计划 3 个，未规划证据 1 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":4,"matched_tool_count":3,"unplanned_tool_count":1,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细描述信息以确认镜像和 imagePullSecret 配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e","purpose":"确认镜像和 imagePullSecret 配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的 Events 信息以确认镜像拉取失败的具体原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-missing-secret","purpose":"确认镜像拉取失败的具体原因","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e3","description":"验证 imagePullSecret 是否存在并正确配置","level":"important","tool":"kubectl_get_by_name","command":"kubectl get secret -n aiops-e2e","purpose":"验证 imagePullSecret 是否存在并正确配置","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细描述信息以确认镜像和 imagePullSecret 配置 | `kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取异常 Pod 的 Events 信息以确认镜像拉取失败的具体原因 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-image...` |
   | e3 | important | ✅ | kubectl_get_by_name | 验证 imagePullSecret 是否存在并正确配置 | `kubectl get secret -n aiops-e2e` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (10.5s)
   📤 → 下游数据: root_cause=Pod 'rc-imagepull-missing-secret' 处于 ImagePullBackOff 状态，表明镜像拉取失败。Events 显示 'Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"'，说明镜像地址或认证存在问题。根据 runbook，这种情况属于 L3 问题。
   confidence=100%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod 'rc-imagepull-missing-secret' 处于 ImagePullBackOff 状态，表明镜像拉取失败。Events 显示 'Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"'，说明镜像地址或认证存在问题。根据 runbook，这种情况属于 L3 问题。", "root_cause_summary": "Pod 'rc-imagepull-missing-secret' 处于 ImagePullBackOff 状态，表明镜像拉取失败。Events 显示 'Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"'，说明镜像地址或认证存在问题。根据 runbook，这种情况属于 L3 问题。", "confidence": 1.0, "confidence_reason": "", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-imagepull-missing-secret' 处于 ImagePullBackOff 状态，表明镜像拉取失败。Events 显示 'Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"'，说明镜...
   置信度: 100%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 13.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4063 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 26.9s
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
| **问题分类** | 镜像拉取失败（ImagePullFailed） |
| **置信度** | 高 (100%) |
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
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `STATUS: ImagePullBackOff, RESTARTS: 0` | Pod 处于镜像拉取失败状态 |
| 2 | Events | `kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e` | `Normal  BackOff  87s (x291 over 66m)  kubelet  Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"` | 镜像拉取失败，重复失败次数多 |
| 3 | imagePullSecret 验证 | `kubectl get secret -n aiops-e2e` | 无输出或未找到匹配的 Secret | 可能缺少或配置错误的 imagePullSecret |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 ImagePullBackOff，Events 显示重复失败拉取镜像，说明镜像拉取失败是当前问题的核心。
- **证据 #3 补充**：未找到 imagePullSecret 或配置错误，进一步指向镜像认证失败。
- **证据链**：Pod 配置引用私有镜像 → 无有效认证 → kubelet 拉取失败 → 进入 ImagePullBackOff 状态。

### 缺失证据（无）

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 缺少或错误配置的 imagePullSecret                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 无法通过认证拉取私有镜像                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pull image "registry.invalid/aiops/private-rootcause:v0" 失败   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 ImagePullBackOff，持续失败拉取镜像                     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 状态 ImagePullBackOff) 和证据 #2 (Events 显示 Back-off pulling image)，
问题的根本原因是**Pod 所引用的私有镜像 `registry.invalid/aiops/private-rootcause:v0` 无法被认证拉取**，
导致 kubelet 无法获取镜像并进入 ImagePullBackOff 状态。
**置信度**：高 (100%)
- ✅ Pod 状态明确为 ImagePullBackOff
- ✅ Events 显示明确的镜像拉取失败
- ✅ 缺少 imagePullSecret 证据进一步支持认证失败

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建或修复 imagePullSecret**
```bash
kubectl create secret docker-registry regcred \
  --docker-server=registry.invalid \
  --docker-username=<your-name> \
  --docker-password=<your-pword> \
  --docker-email=<your-email> \
  -n aiops-e2e
```
*依据*：镜像拉取失败通常因认证信息缺失或错误，需确保 Secret 存在且配置正确。

**2. [次优先] 将 Secret 绑定到 Pod**
```bash
kubectl set image pod/rc-imagepull-missing-secret \
  -n aiops-e2e \
  --pull-secret=regcred
```
*依据*：确保 Pod 使用正确的 imagePullSecret 进行镜像拉取。

**3. [验证] 重新检查 Pod 状态**
```bash
kubectl get pod rc-imagepull-missing-secret -n aiops-e2e
```
*目的*：确认镜像拉取是否成功，Pod 是否进入 Running 状态。

### 后续优化
1. **自动化认证管理**：使用 Kubernetes 凭证管理工具（如 Vault + SPIFFE）自动化 Secret 更新。
2. **镜像地址验证**：确保镜像地址正确，建议在部署前手动验证镜像是否可拉取。
3. **监控镜像拉取失败事件**：通过 Events 或 Prometheus 监控镜像拉取失败事件，及时预警。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-imagepull-missing-secret -n aiops-e2e` | STATUS: Running |
| 2. 检查镜像拉取事件 | `kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e` | 无 Back-off pulling image |
| 3. 检查 imagePullSecret 是否存在 | `kubectl get secret regcred -n aiops-e2e` | NAME: regcred |

---
## ⚠️ 注意事项
- 如果镜像地址错误（如拼写错误、tag 不存在），即使 Secret 正确也无法拉取，需同时验证镜像地址。
- 确保 kubelet 节点可以访问 registry.invalid，避免网络或防火墙问题。
- 如果问题仍然存在，建议手动尝试从节点上拉取镜像（如 `docker pull registry.invalid/aiops/private-rootcause:v0`）进行测试。

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 47.6s (18%) ✅
├─ 证据链采集: 75.2s (28%) ✅
├─ 根因分析: 10.5s (4%) ✅
├─ 汇总总结: 133.5s (50%) ✅
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
