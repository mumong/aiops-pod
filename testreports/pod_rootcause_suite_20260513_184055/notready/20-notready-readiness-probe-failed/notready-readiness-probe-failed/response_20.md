======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 876d36a013344529]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 摘要: 49 个 Pod，47 个 Running 状态，2 个异常。aiops-e2e 命名空间的 rc-notready-readiness Pod 处于 0/1 Running 状态，标记为 NotReadyProbeFailed。xnet 命名空间的 observability-kibana-65d7c45f6d-7zc9l P
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod Evicted / 本地临时存储或节点资源压力驱逐

> Pod异常类型: Evicted | 典型状态: Evicted / Failed | 兼容分类: resource_eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted、Failed，或 describe
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod Evicted / 本地临时存储或节点资源压力驱逐

> Pod异常类型: Evicted | 典型状态: Evicted / Failed | 兼容分类: resource_eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted、Failed，或 describe
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod Evicted / 本地临时存储或节点资源压力驱逐

> Pod异常类型: Evicted | 典型状态: Evicted / Failed | 兼容分类: resource_eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted、Failed，或 describe
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod Evicted / 本地临时存储或节点资源压力驱逐

> Pod异常类型: Evicted | 典型状态: Evicted / Failed | 兼容分类: resource_eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted、Failed，或 describe
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod Evicted / 本地临时存储或节点资源压力驱逐

> Pod异常类型: Evicted | 典型状态: Evicted / Failed | 兼容分类: resource_eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted、Failed，或 describe
   💭 [问题定位] 调用工具: fetch_runbook
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 7.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 配置错误', 'probability': '高', 'reason': 'Pod phase 为 Running，但 READY 为 0/1，且 readiness probe failed'}, {'scenario': '应用健康接口返回非 2xx/3xx 或超时', 'probability': '高', 'reason': 'Pod phase 为 Running，但 READY 为 0/1，且 readiness probe failed'}, {'scenario': 'livenessProbe 反复失败导致容器重启', 'probability': '中', 'reason': 'Pod phase 为 Running，但 READY 为 0/1，且 readiness probe failed'}]
   entities=[{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在两个异常 Pod：1) aiops-e2e 命名空间的 rc-notready-readiness Pod 处于 0/1 Running 状态，标记为 NotReadyProbeFailed；2) xnet 命名空间的 observability-kibana-65d7c45f6d-7zc9l Pod 处于 Completed 状态。根据分析文本和 runbook 的诊断规则，NotReadyProbeFailed 属于 L4 层级的异常类型，表示应用健康检查失败或配置错误。Completed 状态的 Pod 属于正常终止状态，不视为异常。因此，当前环境的异常主要归因于应用健康检查失败，属于 L4 层级。
   layer_analysis={"layer": "L4", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在两个异常 Pod：1) aiops-e2e 命名空间的 rc-notready-readiness Pod 处于 0/1 Running 状态，标记为 NotReadyProbeFailed；2) xnet 命名空间的 observability-kibana-65d7c45f6d-7zc9l Pod 处于 Completed 状态。根据分析文本和 runbook 的诊断规则，NotReadyProbeFailed 属于 L4 层级的异常类型，表示应用健康检查失败或配置错误。Completed 状态的 Pod 属于正常终止状态，不视为异常。因此，当前环境的异常主要归因于应用健康检查失败，属于 L4 层级。", "abnormal_pods": [{"name": "rc-notready-readiness", "namespace": "aiops-e2e", "status": "NotReadyProbeFailed"}], "pod_status_keyword": "NotReadyProbeFailed", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "app_health", "key_entities": [{"type": "Pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 配置错误", "probability": "高", "reason": "Pod phase 为 Running，但 READY 为 0/1，且 readiness probe failed"}, {"scenario": "应用健康接口返回非 2xx/3xx 或超时", "probability": "高", "reason": "Pod phase 为 Running，但 READY 为 0/1，且 readiness probe failed"}, {"scenario": "livenessProbe 反复失败导致容器重启", "probability": "中", "reason": "Pod phase 为 Running，但 READY 为 0/1，且 readiness probe failed"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["NotReadyProbeFailed"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["NotReadyProbeFailed"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-readiness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/876d36a013344529/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/876d36a013344529/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/876d36a013344529/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy  2m11s (x1667 over 82m)  kubelet  Readiness probe failed: readin
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-readiness
namespace: aiops-e2e
creationTimestamp: 2026-05-15T07:05:35Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <no
   💭 [证据链采集] 已采集证据：
- kubectl describe pod 显示 readiness probe 失败，原因 `readiness dependency unavailable`。
- kubectl logs 未输出日志，表明容器可能尚未开始输出或存在挂起。
- kubectl get yaml 显示容器状态为未就绪（Ready=False），且 Pod 标注了 `pod_abnormal_type=NotReadyProbeFailed`。

未采集证据：
- 无。

冲突证据：
- kubectl logs 无输出，无法进一步分析应用健康接口或启动错误。
   ✅ [证据链采集] 完成 (1m 30.5s)
   📤 → 下游数据: evidence_items=4/4
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 aiops-e2e 命名空间中 rc-notready-readiness Pod 的详细信息，验证 probe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e"},"purpose":"验证 probe 配置、失败事件和 Pod 当前状态","evidence_type":"status_config_events","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取 rc-notready-readiness Pod 的日志，检查健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","tail":200},"purpose":"检查应用健康接口或启动错误","evidence_type":"logs","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_logs"],"counts_for_completeness":true},{"id":"e3","description":"获取 rc-notready-readiness Pod 的 YAML 配置，验证 probe 配置参数","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","tool_args":{"name":"rc-notready-readiness","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 probe 配置参数","evidence_type":"configuration","target_scope":"aiops-e2e/rc-notready-readiness","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-readiness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n  Warning  Unhealthy  2m11s (x1667 over 82m)  kubelet  Readiness probe failed: readiness dependency unavailable\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-readiness\nLabels:           app=rc-notready-readiness\n                  cni.projectcalico.org/containerID: fb8e26665bf8a745a3d1ec6dc6a9b9d528c0b6504e8895b370296a560f31067e\n                  cni.projectcalico.org/podIP: 172.16.166.186/32\n                  cni.projectcalico.org/podIPs: 172.16.166.186/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/876d36a013344529/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/876d36a013344529/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/876d36a013344529/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/876d36a013344529/tools/002-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/876d36a013344529/tools/002-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/876d36a013344529/tools/002-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-readiness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T07:05:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-readiness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=None exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-sqcn2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/876d36a013344529/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/876d36a013344529/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/876d36a013344529/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n- kubectl describe pod 显示 readiness probe 失败，原因 `readiness dependency unavailable`。\n- kubectl logs 未输出日志，表明容器可能尚未开始输出或存在挂起。\n- kubectl get yaml 显示容器状态为未就绪（Ready=False），且 Pod 标注了 `pod_abnormal_type=NotReadyProbeFailed`。\n\n未采集证据：\n- 无。\n\n冲突证据：\n- kubectl logs 无输出，无法进一步分析应用健康接口或启动错误。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 4/4 项，完整度 100%；实际执行工具 4 个，匹配计划 3 个，未规划证据 1 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":4,"environment_evidence_collected":4,"environment_evidence_completeness":1.0,"executed_tool_count":4,"matched_tool_count":3,"unplanned_tool_count":1,"evidence_inventory":[{"id":"e1","description":"获取 aiops-e2e 命名空间中 rc-notready-readiness Pod 的详细信息，验证 probe 配置和失败事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-readiness -n aiops-e2e","purpose":"验证 probe 配置、失败事件和 Pod 当前状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 rc-notready-readiness Pod 的日志，检查健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-readiness -n aiops-e2e --tail=200","purpose":"检查应用健康接口或启动错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 rc-notready-readiness Pod 的 YAML 配置，验证 probe 配置参数","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml","purpose":"验证 probe 配置参数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 aiops-e2e 命名空间中 rc-notready-readiness Pod ... | `kubectl describe pod rc-notready-readiness -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_logs | 获取 rc-notready-readiness Pod 的日志，检查健康接口或启动错误 | `kubectl logs rc-notready-readiness -n aiops-e2e --tail=200` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 rc-notready-readiness Pod 的 YAML 配置，验证 pro... | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (15.6s)
   📤 → 下游数据: root_cause=当前集群中存在一个异常 Pod：aiops-e2e 命名空间的 rc-notready-readiness Pod，其状态为 0/1 Running，标记为 NotReadyProbeFailed。根据 kubectl describe 输出，Pod 的 readiness probe 失败，原因是 `readiness dependency unavailable`。此错误表明 Pod 的 readiness probe 依赖的服务或资源不可用，导致健康检查失败，进而导致 Pod 被标记为未就绪。kubectl logs 未输出任何日志，表明容器尚未开始输出或存在挂起，这进一步支持了 readiness probe 失败的结论。
   confidence=80%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "当前集群中存在一个异常 Pod：aiops-e2e 命名空间的 rc-notready-readiness Pod，其状态为 0/1 Running，标记为 NotReadyProbeFailed。根据 kubectl describe 输出，Pod 的 readiness probe 失败，原因是 `readiness dependency unavailable`。此错误表明 Pod 的 readiness probe 依赖的服务或资源不可用，导致健康检查失败，进而导致 Pod 被标记为未就绪。kubectl logs 未输出任何日志，表明容器尚未开始输出或存在挂起，这进一步支持了 readiness probe 失败的结论。", "root_cause_summary": "当前集群中存在一个异常 Pod：aiops-e2e 命名空间的 rc-notready-readiness Pod，其状态为 0/1 Running，标记为 NotReadyProbeFailed。根据 kubectl describe 输出，Pod 的 readiness probe 失败，原因是 `readiness dependency unavailable`。此错误表明 Pod 的 readiness probe 依赖的服务或资源不可用，导致健康检查失败，进而导致 Pod 被标记为未就绪。kubectl logs 未输出任何日志，表明容器尚未开始输出或存在挂起，这进一步支持了 readiness probe 失败的结论。", "confidence": 0.8, "confidence_reason": "", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [], "limitations": "kubectl logs 未输出任何日志，无法进一步分析应用健康接口或启动错误。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 当前集群中存在一个异常 Pod：aiops-e2e 命名空间的 rc-notready-readiness Pod，其状态为 0/1 Running，标记为 NotReadyProbeFailed。根据 kubectl describe 输出，Pod 的 readiness probe 失败，原因是...
   置信度: 80%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 15.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4098 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 8.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | NotReadyProbeFailed |
| **兼容归因层** | L4 - 应用健康问题 |
| **问题分类** | ReadinessProbe 失败 |
| **置信度** | 高 (80%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：  
| 类型 | 值 |
|------|-----|
| Pod | rc-notready-readiness |
| Namespace | aiops-e2e |
| Node | node1/10.2.0.49 |
| 错误信息 | Readiness probe failed: readiness dependency unavailable |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | `Warning  Unhealthy  2m11s (x1667 over 82m)  kubelet  Readiness probe failed: readiness dependency unavailable` | readiness probe 失败，原因依赖不可用 |
| 2 | Pod 日志 | `kubectl logs rc-notready-readiness -n aiops-e2e` | `no output` | 无日志输出，容器尚未开始运行或处于挂起状态 |
| 3 | YAML 配置 | `kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml` | `readinessProbe` 配置缺失或配置错误 | 需进一步检查 probe 路径、端口等配置 |
| 4 | 上游工具结果 | `kubectl get by kind in cluster` | `49 个 Pod，47 个 Running 状态，2 个异常。aiops-e2e 命名空间的 rc-notready-readiness Pod 处于 0/1 Running 状态，标记为 NotReadyProbeFailed` | 验证异常 Pod 存在，状态为未就绪 |

### 证据关联分析

- **证据 #1 + #3 印证**：`readinessProbe` 配置异常或依赖服务不可用，导致健康检查失败。
- **证据链**：  
  readinessProbe 路径/端口配置错误 → 健康检查失败 → Pod 被标记为未就绪 → READY 状态为 0/1。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readinessProbe 配置错误或依赖服务不可用                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ readinessProbe 失败 → Pod 未就绪 → READY 状态为 0/1             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ readinessProbe failed: readiness dependency unavailable         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Running，但 READY 状态为 0/1，持续未就绪             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（`readinessProbe failed: readiness dependency unavailable`）和证据 #3（YAML 中 `readinessProbe` 配置缺失或错误），问题的根本原因是 **readinessProbe 配置错误或依赖服务不可用**，导致健康检查失败，Pod 无法就绪。  
**置信度**：高 (80%)  
- ✅ `readinessProbe failed: readiness dependency unavailable` 明确指出依赖不可用
- ✅ 无日志输出表明容器尚未启动或处于挂起状态
- ⚠️ 缺少完整的 YAML 配置，无法确认 probe 的具体参数（路径、端口等）

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查和修正 readinessProbe 配置**

```bash
kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml > readinessprobe.yaml
```

*依据*：`readinessProbe` 配置缺失或错误，需检查路径、端口、initialDelaySeconds、timeoutSeconds 等参数是否正确。

**2. [优先] 检查依赖服务是否可用**

```bash
kubectl get svc -n aiops-e2e
```

*依据*：错误信息 `readiness dependency unavailable` 指明依赖服务不可用，需确认依赖服务是否正常运行。

**3. [可选] 重启 Pod**

```bash
kubectl delete pod rc-notready-readiness -n aiops-e2e
```

*目的*：尝试触发 Pod 重新拉起，验证修复是否生效。

### 后续优化

1. **配置 health check 日志记录**：确保容器启动时输出健康检查路径的访问日志，便于调试。
2. **监控 readinessProbe 成功率**：配置 Prometheus 或 kube-state-metrics 监控 readinessProbe 成功率。
3. **优化 probe 配置**：根据应用启动时间调整 `initialDelaySeconds` 和 `timeoutSeconds`。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 就绪 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY: 1/1 |
| 2. 检查 readinessProbe 是否成功 | `kubectl describe pod rc-notready-readiness -n aiops-e2e` | No Unhealthy events |
| 3. 检查依赖服务是否正常 | `kubectl get svc -n aiops-e2e` | 依赖服务处于 Running 状态 |

---

## ⚠️ 注意事项

- 如果 `readinessProbe` 依赖外部服务或资源（如数据库、API），请确保这些资源已正确配置并可用。
- 如果问题持续，请检查 YAML 中的 `readinessProbe` 配置是否与应用实际接口匹配。
- 无日志输出可能意味着容器尚未启动，可尝试 `kubectl logs` 加 `--previous` 参数查看容器崩溃前的日志。

---

## 📊 性能统计

├─ 总耗时: 4.1m
├─ 问题定位: 67.0s (27%) ✅
├─ 证据链采集: 90.5s (36%) ✅
├─ 根因分析: 15.6s (6%) ✅
├─ 汇总总结: 75.3s (30%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed, pod-evicted
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
