======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 655c48f0d9934cee]

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
19m (x4 over 21m)    Warning   Failed           Pod/rc-imagepull-invalid-registry   Failed to pull image "registry.invalid/aiops/rootcause:v0": rpc error: code = Unknown desc
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                            READY   STATUS         RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-imagepull-invalid-registry   0/1     ErrImagePull   0     
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": [
    "L3"
  ],
  "layer_name": "ImagePullFailed",
  "confidence": "high",
  "reasoning": "异常 Pod rc-imagepull-invalid-registry（namespace: aiops-e2e）的状态为 ErrImagePull / ImagePullBackOff，Events 显示镜像拉取失败，具体错误为 registry.invalid DNS 解析失败。这属于镜像仓库网络不可达问题，符合 L3 分层的 ImagePullFailed 类型。当前异常类型为 ImagePullFailed，兼容归因 L3。未发现其他异常 Pod 或异常类型。",
  "abnormal_pods": [
    {
      "name": "rc-imagepull-invalid-registry",
      "namespace": "aiops-e2e",
      "status": "ImagePullBackOff",
      "age": "21m",
      "ip": "172.16.166.156"
    }
  ],
  "abnormal_groups": {
    "ImagePullFailed": {
      "count": 1,
      "pods": [
        "rc-imagepull-invalid-registry"
      ]
    }
  },
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "L3",
  "key_entities": [
    "Pod rc-imagepull-invalid-registry",
    "镜像 registry.invalid/aiops/rootcause:v0",
    "DNS registry.invalid"
  ],
  "possible_scenarios": [
    "DNS 解析失败导致镜像仓库不可达",
    "镜像地址配置错误或仓库不存在",
    "镜像仓库网络策略或防火墙阻止拉取"
  ]
}
   ✅ [问题定位] 完成 (36.1s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[]
   entities=[]
   reasoning=异常 Pod rc-imagepull-invalid-registry（namespace: aiops-e2e）的状态为 ErrImagePull / ImagePullBackOff，Events 显示镜像拉取失败，具体错误为 registry.invalid DNS 解析失败。这属于镜像仓库网络不可达问题，符合 L3 分层的 ImagePullFailed 类型。当前异常类型为 ImagePullFailed，兼容归因 L3。未发现其他异常 Pod 或异常类型。
   layer_analysis={"layer": "L3", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "异常 Pod rc-imagepull-invalid-registry（namespace: aiops-e2e）的状态为 ErrImagePull / ImagePullBackOff，Events 显示镜像拉取失败，具体错误为 registry.invalid DNS 解析失败。这属于镜像仓库网络不可达问题，符合 L3 分层的 ImagePullFailed 类型。当前异常类型为 ImagePullFailed，兼容归因 L3。未发现其他异常 Pod 或异常类型。", "abnormal_pods": [{"name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-invalid-registry                       0/1     ImagePullBackOff   0             21m    172.16.166.156   node1    <none>           <none>            app=rc-imagepull-invalid-registry,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/655c48f0d9934cee/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/655c48f0d9934cee/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/655c48f0d9934cee/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          22m (x4 over 23m)     kubelet            Failed to
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (2m 7.6s)
   📤 → 下游数据: evidence_items=5/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod rc-imagepull-invalid-registry 的详细描述信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-imagepull-invalid-registry","namespace":"aiops-e2e"},"purpose":"验证 Pod 的详细状态、事件和配置，以确定导致 ImagePullBackOff 的原因","evidence_type":"Pod 详细描述信息","target_scope":"aiops-e2e/rc-imagepull-invalid-registry","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_events","kubectl_previous_logs"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod rc-imagepull-invalid-registry 的事件信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-imagepull-invalid-registry","tool_args":{"kind":"Event","namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-imagepull-invalid-registry"},"purpose":"验证 Pod 的事件记录，确认镜像拉取失败的具体原因","evidence_type":"Pod 事件信息","target_scope":"aiops-e2e/rc-imagepull-invalid-registry","acceptable_tools":["kubectl_events","kubectl_get_by_name","kubectl_describe"],"counts_for_completeness":true},{"id":"e4","description":"获取异常 Pod rc-imagepull-invalid-registry 的 previous logs","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-imagepull-invalid-registry -n aiops-e2e --previous","tool_args":{"kind":"Pod","name":"rc-imagepull-invalid-registry","namespace":"aiops-e2e","container":null,"previous":true},"purpose":"验证 Pod 的 previous logs，确认镜像拉取失败的具体原因","evidence_type":"Pod previous logs","target_scope":"aiops-e2e/rc-imagepull-invalid-registry","acceptable_tools":["kubectl_previous_logs","kubectl_logs","kubectl_logs_all_containers"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          22m (x4 over 23m)     kubelet            Failed to pull image \"registry.invalid/aiops/rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n  Normal   BackOff         3m37s (x87 over 23m)  kubelet            Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n      Reason:       ImagePullBackOff\n  Warning  Failed          22m (x4 over 23m)     kubelet            Error: ErrImagePull\n  Warning  Failed          22m (x6 over 23m)     kubelet            Error: ImagePullBackOff\n                  cni.projectcalico.org/containerID: 82174088e8d254fd04c994cc2744d2fc71d880e8291a39a8e865fe71718ad3db\n                  cni.projectcalico.org/podIP: 172.16.166.156/32\n                  cni.projectcalico.org/podIPs: 172.16.166.156/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed\n    State:          Waiting","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/655c48f0d9934cee/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/655c48f0d9934cee/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/655c48f0d9934cee/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 5/6 项，完整度 83%；实际执行工具 4 个，匹配计划 2 个，未规划证据 2 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":6,"environment_evidence_collected":5,"environment_evidence_completeness":0.8333333333333334,"executed_tool_count":4,"matched_tool_count":2,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod rc-imagepull-invalid-registry 的详细描述信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","purpose":"验证 Pod 的详细状态、事件和配置，以确定导致 ImagePullBackOff 的原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod rc-imagepull-invalid-registry 的事件信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-imagepull-invalid-registry","purpose":"验证 Pod 的事件记录，确认镜像拉取失败的具体原因","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e4","description":"获取异常 Pod rc-imagepull-invalid-registry 的 previous logs","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-imagepull-invalid-registry -n aiops-e2e --previous","purpose":"验证 Pod 的 previous logs，确认镜像拉取失败的具体原因","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e4(获取异常 Pod rc-imagepull-invalid-registry 的 previous logs): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 83%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod rc-imagepull-invalid-registry 的详细描述信息 | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取异常 Pod rc-imagepull-invalid-registry 的事件信息 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-image...` |
   | e4 | important | ❌ | kubectl_previous_logs | 获取异常 Pod rc-imagepull-invalid-registry 的 prev... | `kubectl logs rc-imagepull-invalid-registry -n aiops-e2e --previous` |

   ⚠️ 未采集原因:
   - e4(获取异常 Pod rc-imagepull-invalid-registry 的 previous logs): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (30.2s)
   📤 → 下游数据: root_cause=Pod rc-imagepull-invalid-registry（namespace: aiops-e2e）状态为 ImagePullBackOff，Events 显示镜像拉取失败，具体错误为 registry.invalid DNS 解析失败。这表明节点到镜像仓库网络不可达，属于 L3 分层的 ImagePullFailed 类型。
   confidence=80%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod rc-imagepull-invalid-registry（namespace: aiops-e2e）状态为 ImagePullBackOff，Events 显示镜像拉取失败，具体错误为 registry.invalid DNS 解析失败。这表明节点到镜像仓库网络不可达，属于 L3 分层的 ImagePullFailed 类型。", "root_cause_summary": "Pod rc-imagepull-invalid-registry（namespace: aiops-e2e）状态为 ImagePullBackOff，Events 显示镜像拉取失败，具体错误为 registry.invalid DNS 解析失败。这表明节点到镜像仓库网络不可达，属于 L3 分层的 ImagePullFailed 类型。", "confidence": 0.8, "confidence_reason": "有直接证据表明镜像拉取失败是由于 DNS 解析失败，因果链清晰。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [], "limitations": "未获取异常 Pod 的 previous logs，可能缺少额外上下文信息。", "llm_raw_analysis": "基于提供的证据，Pod rc-imagepull-invalid-registry（namespace: aiops-e2e）状态为 ImagePullBackOff，Events 显示镜像拉取失败，具体错误为 registry.invalid DNS 解析失败。这表明节点到镜像仓库网络不可达，属于 L3 分层的 ImagePullFailed 类型。证据显示镜像拉取失败是由于 DNS 解析失败，因此这是主要的根因。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-imagepull-invalid-registry（namespace: aiops-e2e）状态为 ImagePullBackOff，Events 显示镜像拉取失败，具体错误为 registry.invalid DNS 解析失败。这表明节点到镜像仓库网络不可达，属于 L3 分层的 ...
   置信度: 80%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 39.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4478 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 53.2s
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
| 错误信息 | registry.invalid DNS 解析失败 |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ImagePullBackOff` | Pod 无法拉取镜像，处于重试状态 |
| 2 | Pod 事件 | `kubectl events` | `Warning Failed: Failed to pull image "registry.invalid/aiops/rootcause:v0": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 镜像拉取失败，DNS 解析失败 |
| 3 | Pod 描述 | `kubectl describe pod` | `Warning  Failed  22m (x4 over 23m)     kubelet            Failed to pull image` | kubelet 无法拉取镜像 |
| 4 | 镜像地址 | `kubectl get pod -o json` | `"image": "registry.invalid/aiops/rootcause:v0"` | 镜像地址为 registry.invalid，DNS 解析失败 |
| 5 | 镜像拉取策略 | `kubectl get pod -o json` | `"imagePullPolicy": "Always"` | 拉取策略为 Always，强制从远程仓库拉取 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 `ImagePullBackOff`，事件中明确指出 `registry.invalid` 无法解析，表明问题出在 DNS。
- **证据 #3 印证**：kubelet 报告镜像拉取失败，进一步确认镜像仓库不可达。
- **证据 #4 印证**：镜像地址为 registry.invalid，且 DNS 解析失败，说明镜像仓库地址配置错误或 DNS 配置问题。
- **证据 #5 印证**：镜像拉取策略为 Always，强制从 registry.invalid 拉取，即使本地有镜像也会覆盖，加重问题。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 容器崩溃前日志 | important | 无影响，因 Pod 未成功启动，无容器日志 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ registry.invalid 镜像仓库地址配置错误，DNS 解析失败             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 尝试拉取 registry.invalid/aiops/rootcause:v0 镜像失败   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 状态为 ImagePullBackOff，Events 明确指出 DNS 解析失败        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-imagepull-invalid-registry 无法启动，处于 ImagePullBackOff 状态 |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (Events 显示 DNS 解析失败) 和证据 #4 (镜像地址为 registry.invalid)，问题的根本原因是**镜像仓库地址 registry.invalid 配置错误，无法解析**，导致镜像拉取失败，Pod 无法启动。
**置信度**：高 (80%)
- ✅ Events 明确显示 `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host`
- ✅ Pod 描述中 `Failed to pull image` 进一步确认镜像拉取失败
- ⚠️ 未获取 previous logs，但对本场景无影响

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修正镜像地址或 DNS 配置**
```bash
kubectl edit deployment rc-imagepull-invalid-registry -n aiops-e2e
```
*操作*：将镜像地址更正为有效的镜像仓库地址，例如 `docker.io/aiops/rootcause:v0`，或修复 DNS 配置使 registry.invalid 可解析。

**2. [可选] 配置 imagePullSecret（如使用私有仓库）**
```bash
kubectl create secret docker-registry registry-secret \
  --docker-server=registry.invalid \
  --docker-username=<user> \
  --docker-password=<password> \
  --docker-email=<email> \
  -n aiops-e2e
```
*目的*：如果 registry.invalid 是私有仓库，需配置认证信息。

**3. [可选] 调整镜像拉取策略为 IfNotPresent**
```bash
kubectl edit deployment rc-imagepull-invalid-registry -n aiops-e2e
```
*修改*：
```yaml
imagePullPolicy: IfNotPresent
```
*目的*：避免强制拉取远程镜像，优先使用本地缓存。

### 后续优化
1. **DNS 配置检查**：确认节点的 `/etc/resolv.conf` 配置正确，可解析 registry.invalid。
2. **镜像仓库连通性测试**：在节点上执行 `curl -v https://registry.invalid`，确认网络可达。
3. **镜像仓库白名单**：如使用代理或防火墙，确认 registry.invalid 在白名单中。
4. **K8s 节点网络配置检查**：确认节点网络策略、路由表、防火墙未阻止到 registry.invalid 的连接。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-imagepull-invalid-registry -n aiops-e2e` | STATUS: Running |
| 2. 检查镜像拉取状态 | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` | 无 Failed 事件，拉取成功 |
| 3. 检查 DNS 解析 | `nslookup registry.invalid` | 成功解析 registry.invalid 的 IP 地址 |

---

## ⚠️ 注意事项
- 如果 registry.invalid 是测试用的无效地址，应立即修正为真实可用的镜像仓库地址。
- 如果 registry.invalid 是私有仓库，必须配置 imagePullSecret，否则无法拉取镜像。
- 如果镜像地址正确但仍然失败，需进一步排查网络、TLS、镜像标签等问题。

---

## 📊 性能统计

├─ 总耗时: 4.9m
├─ 问题定位: 36.1s (12%) ✅
├─ 证据链采集: 127.6s (44%) ✅
├─ 根因分析: 30.2s (10%) ✅
├─ 汇总总结: 99.1s (34%) ✅
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
