======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ebc911e433ad442e]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}
NAMESPACE     NAME                                                READY   STATUS                       RESTARTS   
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                           READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-secret-key-missing   0/1     CreateCon
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=218 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --previous --tail=200
Error from server (BadRequest): previous termina
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          41m (x12 over 43m)     kubelet            Error: co
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE   LABELS
rc-app-secret   Opaque   1      43m   rootcause-e2e=true
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                           READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-secret-key-missing   0/1     CreateCon
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod rc-config-secret-key-missing 的状态为 CreateContainerConfigError，事件显示 kubelet 无法在 Secret aiops-e2e/rc-app-secret 中找到键 APP_SECRET_TOKEN。这表明配置错误导致容器无法启动，符合 L4 层级的诊断。",
  "abnormal_pods": [
    {
      "name": "rc-config-secret-key-missing",
      "namespace": "aiops-e2e",
      "status": "CreateContainerConfigError",
      "reason": "Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret"
    }
  ],
  "abnormal_groups": [
    {
      "type": "ConfigError",
      "count": 1
    }
  ],
  "pod_status_keyword": "CreateContainerConfigError",
  "pod_abnormal_type": "ConfigError",
  "status_category": "ConfigError",
  "key_entities": [
    {
      "kind": "Pod",
      "name": "rc-config-secret-key-missing",
      "namespace": "aiops-e2e"
    },
    {
      "kind": "Secret",
      "name": "rc-app-secret",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    "Secret aiops-e2e/rc-app-secret 缺少键 APP_SECRET_TOKEN，导致 Pod 启动失败。",
    "Pod rc-config-secret-key-missing 引用了不存在的键 APP_SECRET_TOKEN，配置错误。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (56.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Secret aiops-e2e/rc-app-secret 缺少键 APP_SECRET_TOKEN，导致 Pod 启动失败。', 'probability': 'high', 'reason': 'describe 显示 kubelet 无法在 Secret 中找到指定键。'}, {'scenario': 'Pod rc-config-secret-key-missing 引用了不存在的键 APP_SECRET_TOKEN，配置错误。', 'probability': 'high', 'reason': 'Pod 的配置错误导致容器无法启动，符合 L4 层级的诊断。'}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-config-secret-key-missing 的状态为 CreateContainerConfigError，事件显示 kubelet 无法在 Secret aiops-e2e/rc-app-secret 中找到键 APP_SECRET_TOKEN。这表明配置错误导致容器无法启动，符合 L4 层级的诊断。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.9, "reasoning": "Pod rc-config-secret-key-missing 的状态为 CreateContainerConfigError，事件显示 kubelet 无法在 Secret aiops-e2e/rc-app-secret 中找到键 APP_SECRET_TOKEN。这表明配置错误导致容器无法启动，符合 L4 层级的诊断。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "ConfigError", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Secret aiops-e2e/rc-app-secret 缺少键 APP_SECRET_TOKEN，导致 Pod 启动失败。", "probability": "high", "reason": "describe 显示 kubelet 无法在 Secret 中找到指定键。"}, {"scenario": "Pod rc-config-secret-key-missing 引用了不存在的键 APP_SECRET_TOKEN，配置错误。", "probability": "high", "reason": "Pod 的配置错误导致容器无法启动，符合 L4 层级的诊断。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             43m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ebc911e433ad442e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ebc911e433ad442e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ebc911e433ad442e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 90%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          43m (x12 over 45m)   kubelet            Error: coul
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE   LABELS
rc-app-secret   Opaque   1      45m   rootcause-e2e=true
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   ✅ [证据链采集] 完成 (1m 17.8s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-config-secret-key-missing 的配置错误详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-config-secret-key-missing","kind":"pod"},"purpose":"获取 Pod 的详细事件和状态信息，验证配置错误的根源","evidence_type":"status_event","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_describe","kubectl_events","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"验证 Secret aiops-e2e/rc-app-secret 是否存在 APP_SECRET_TOKEN 键","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'","tool_args":{"namespace":"aiops-e2e","name":"rc-app-secret","kind":"secret"},"purpose":"确认 Secret 是否包含指定的键 APP_SECRET_TOKEN，验证配置缺失问题","evidence_type":"config_validation","target_scope":"aiops-e2e/rc-app-secret","acceptable_tools":["kubectl_get_by_name","kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod rc-config-secret-key-missing 的容器启动日志","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-secret-key-missing -n aiops-e2e --previous","tool_args":{"namespace":"aiops-e2e","name":"rc-config-secret-key-missing","container":"app"},"purpose":"获取 Pod 容器的上一个失败状态的日志，验证配置错误的具体表现","evidence_type":"container_logs","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_previous_logs","kubectl_logs"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          43m (x12 over 45m)   kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c3704966fe0c483b32880bd181c9fc13cf69ec95\n                  cni.projectcalico.org/podIP: 172.16.166.188/32\n                  cni.projectcalico.org/podIPs: 172.16.166.188/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n      Reason:       CreateContainerConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ebc911e433ad442e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ebc911e433ad442e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ebc911e433ad442e/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME            TYPE     DATA   AGE   LABELS\nrc-app-secret   Opaque   1      45m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ebc911e433ad442e/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ebc911e433ad442e/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ebc911e433ad442e/tools/002-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'pod_name' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-config-secret-key-missing 的配置错误详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"获取 Pod 的详细事件和状态信息，验证配置错误的根源","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 Secret aiops-e2e/rc-app-secret 是否存在 APP_SECRET_TOKEN 键","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'","purpose":"确认 Secret 是否包含指定的键 APP_SECRET_TOKEN，验证配置缺失问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 Pod rc-config-secret-key-missing 的容器启动日志","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-secret-key-missing -n aiops-e2e --previous","purpose":"获取 Pod 容器的上一个失败状态的日志，验证配置错误的具体表现","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-config-secret-key-missing 的配置错误详情 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_name | 验证 Secret aiops-e2e/rc-app-secret 是否存在 APP_SE... | `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'` |
   | e3 | important | ✅ | kubectl_previous_logs | 验证 Pod rc-config-secret-key-missing 的容器启动日志 | `kubectl logs rc-config-secret-key-missing -n aiops-e2e --previous` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (17.7s)
   📤 → 下游数据: root_cause=[L4层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L4层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L4层] 当前无法基于 LLM 输出确定根本原因
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
   ✅ [汇总总结] 完成 (1m 0.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3986 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 32.3s
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
| **Pod异常状态** | CreateContainerConfigError |
| **兼容归因层** | L4 |
| **问题分类** | Secret 缺失键（ConfigError） |
| **置信度** | 高 (90%) |
| **证据完整度** | 3/3 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-config-secret-key-missing |
| Namespace | aiops-e2e |
| Secret | aiops-e2e/rc-app-secret |
| 错误信息 | `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CreateContainerConfigError` | 容器因配置错误无法创建 |
| 2 | kubectl describe Pod | `kubectl describe pod rc-config-secret-key-missing` | `Warning Failed 41m (x12 over 43m) kubelet Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | 明确指出 Secret 缺失键 |
| 3 | Secret 内容 | `kubectl get secret rc-app-secret` | `DATA: 1` | Secret 中未包含 `APP_SECRET_TOKEN` 键 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 `CreateContainerConfigError`，结合 `describe` 事件，确认是由于 Secret 缺少 `APP_SECRET_TOKEN` 键。
- **证据链**：Pod 配置引用了 `APP_SECRET_TOKEN` → Secret 中无此键 → kubelet 无法完成容器配置 → Pod 无法启动 → 持续失败。

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 在拉取 Secret 时发现缺失键 APP_SECRET_TOKEN              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器配置失败（CreateContainerConfigError）                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError |
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #2 (`kubectl describe pod` 显示 `Error: couldn't find key APP_SECRET_TOKEN`) 和证据 #3 (`kubectl get secret` 显示 `DATA: 1` 且无该键)，问题的根本原因是 **Secret `aiops-e2e/rc-app-secret` 中缺少容器所需的 `APP_SECRET_TOKEN` 键**，导致 kubelet 无法构建容器配置，最终引发 `CreateContainerConfigError`。
**置信度**：高 (90%)
- ✅ `kubectl describe pod` 明确指出错误原因
- ✅ `kubectl get secret` 验证了键不存在

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 向 Secret 添加缺失的键**
```bash
kubectl patch secret rc-app-secret -n aiops-e2e \
  -p '{"data": {"APP_SECRET_TOKEN": "<base64-encoded-value>"}}' \
  --type=merge
```
*依据*：Secret 缺失 `APP_SECRET_TOKEN`，必须手动添加，或重新生成 Secret。
*说明*：将 `<base64-encoded-value>` 替换为实际的 base64 编码值，例如：
```bash
echo -n "my-secret-token" | base64
```

**2. [可选] 重新部署或重启 Pod**
```bash
kubectl delete pod rc-config-secret-key-missing -n aiops-e2e
```
*依据*：删除失败 Pod 后，Kubernetes 会基于控制器（Deployment/ReplicaSet）自动重建 Pod，此时 Secret 已更新。

### 后续优化
1. **Secret 管理最佳实践**：确保所有依赖 Secret 的 Pod 配置都经过验证，避免键缺失。
2. **自动化验证**：在 CI/CD 流程中加入配置校验，确保 Secret 和 Pod 配置一致。
3. **监控告警**：监控 `PodCreateError` 等事件，及时发现配置问题。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Secret 包含 `APP_SECRET_TOKEN` | `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'` | 输出中包含 `APP_SECRET_TOKEN` |
| 2. 确认 Pod 启动成功 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | 无 `Failed` 事件 |

---
## ⚠️ 注意事项
- 如果 Secret 是由外部系统（如 Vault）动态注入的，需确认注入流程是否成功。
- 如果多次添加键后仍报错，确认 Pod 中引用的键名是否拼写错误或大小写不一致。
- 避免在生产环境中使用明文 Secret，应通过加密方式管理敏感数据。

---

---

## 📊 性能统计

├─ 总耗时: 3.5m
├─ 问题定位: 56.7s (27%) ✅
├─ 证据链采集: 77.8s (37%) ✅
├─ 根因分析: 17.7s (8%) ✅
├─ 汇总总结: 60.2s (28%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
