======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 124d902986d8447b]

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
47s (x489 over 110m)   Normal   BackOff   Pod/rc-imagepull-missing-secret   Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"
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
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": [
    "L3"
  ],
  "layer_name": "ImagePullFailed",
  "confidence": "high",
  "reasoning": "检测到 Pod 状态为 ImagePullBackOff，并且事件表明镜像拉取失败。进一步检查发现指定的 imagePullSecret 'rc-definitely-missing-pull-secret' 不存在，导致认证失败。",
  "abnormal_pods": [
    "rc-imagepull-missing-secret"
  ],
  "abnormal_groups": {
    "ImagePullFailed": [
      "rc-imagepull-missing-secret"
    ]
  },
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "ImagePullFailed",
  "key_entities": [
    "Pod: rc-imagepull-missing-secret",
    "Image: registry.invalid/aiops/private-rootcause:v0",
    "ImagePullSecret: rc-definitely-missing-pull-secret"
  ],
  "possible_scenarios": [
    "指定的 imagePullSecret 'rc-definitely-missing-pull-secret' 不存在，导致镜像拉取认证失败。",
    "镜像仓库地址 'registry.invalid/aiops/private-rootcause:v0' 可能不正确或镜像不存在。",
    "ServiceAccount 'default' 没有正确配置 imagePullSecret。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (54.8s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': "指定的 imagePullSecret 'rc-definitely-missing-pull-secret' 不存在，导致镜像拉取认证失败。", 'probability': 'high', 'reason': 'kubectl_get_by_name 显示 rc-definitely-missing-pull-secret 不存在。'}, {'scenario': "镜像仓库地址 'registry.invalid/aiops/private-rootcause:v0' 可能不正确或镜像不存在。", 'probability': 'medium', 'reason': '事件中显示镜像拉取失败，可能镜像路径或 tag 错误。'}, {'scenario': "ServiceAccount 'default' 没有正确配置 imagePullSecret。", 'probability': 'medium', 'reason': 'kubectl_get_yaml 显示 ServiceAccountName 为 default，但未正确引用 imagePullSecret。'}]
   entities=[{"type": "Pod", "name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.invalid/aiops/private-rootcause:v0", "namespace": "aiops-e2e"}, {"type": "ImagePullSecret", "name": "rc-definitely-missing-pull-secret", "namespace": "aiops-e2e"}]
   reasoning=检测到 Pod 状态为 ImagePullBackOff，并且事件表明镜像拉取失败。进一步检查发现指定的 imagePullSecret 'rc-definitely-missing-pull-secret' 不存在，导致认证失败。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "ImagePullFailed", "confidence": 1.0, "reasoning": "检测到 Pod 状态为 ImagePullBackOff，并且事件表明镜像拉取失败。进一步检查发现指定的 imagePullSecret 'rc-definitely-missing-pull-secret' 不存在，导致认证失败。", "abnormal_pods": [{"name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "Pod", "name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e"}, {"type": "Image", "name": "registry.invalid/aiops/private-rootcause:v0", "namespace": "aiops-e2e"}, {"type": "ImagePullSecret", "name": "rc-definitely-missing-pull-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "指定的 imagePullSecret 'rc-definitely-missing-pull-secret' 不存在，导致镜像拉取认证失败。", "probability": "high", "reason": "kubectl_get_by_name 显示 rc-definitely-missing-pull-secret 不存在。"}, {"scenario": "镜像仓库地址 'registry.invalid/aiops/private-rootcause:v0' 可能不正确或镜像不存在。", "probability": "medium", "reason": "事件中显示镜像拉取失败，可能镜像路径或 tag 错误。"}, {"scenario": "ServiceAccount 'default' 没有正确配置 imagePullSecret。", "probability": "medium", "reason": "kubectl_get_yaml 显示 ServiceAccountName 为 default，但未正确引用 imagePullSecret。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-missing-secret                         0/1     ImagePullBackOff   0             110m   172.16.166.166   node1    <none>           <none>            app=rc-imagepull-missing-secret,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/124d902986d8447b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/124d902986d8447b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/124d902986d8447b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-missing-secret
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal  BackOff  3m12s (x489 over 113m)  kubelet  Back-off pulling image "reg
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=197 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-definitely-missing-pull-secret -n aiops-e2e
Error from server (NotFound): secrets "
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME      SECRETS   AGE    LABELS
default   0         111d   <none>
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
   💭 [证据链采集] 已采集证据：
1. `kubectl_describe` 显示 Pod 状态为 Pending，事件表明镜像拉取失败（`ImagePullBackOff`）。
2. `kubectl_get_by_name` 确认 `rc-definitely-missing-pull-secret` 不存在。
3. `kubectl_get_by_name` 显示 `default` ServiceAccount 没有关联任何 Secret。
4. `kubectl_get_yaml` 显示 Pod 配置中引用了缺失的 `rc-definitely-missing-pull-secret` 作为 `imagePullSecrets`。

未采集证据：
- 无

冲突证据：
- 无

总结：
- Pod `rc-imagepull-missing-secret` 状态为 `ImagePullBackOff`。
- 指定的 `imagePullSecret` `rc-definitely-missing-pull-secret` 不存在。
- `default` ServiceAccount 未配置 `imagePullSecrets`。
- Pod 配置中引用了不存在的 `imagePullSecret`。
   ✅ [证据链采集] 完成 (1m 57.0s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 'rc-imagepull-missing-secret' 的详细描述信息，确认镜像拉取失败原因和 imagePullSecret 配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-imagepull-missing-secret","kind":"pod"},"purpose":"获取 Pod 详细状态、Events、imagePullSecret 配置等信息","evidence_type":"pod_status","target_scope":"aiops-e2e/rc-imagepull-missing-secret","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"检查 Pod 所引用的 imagePullSecret 'rc-definitely-missing-pull-secret' 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-pull-secret -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-definitely-missing-pull-secret","kind":"secret"},"purpose":"验证 imagePullSecret 是否存在","evidence_type":"secret_verification","target_scope":"aiops-e2e/rc-definitely-missing-pull-secret","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod 所属 ServiceAccount 'default' 是否正确配置了 imagePullSecret 'rc-definitely-missing-pull-secret'","level":"important","tool":"kubectl_get_by_name","command":"kubectl get serviceaccount default -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"default","kind":"serviceaccount"},"purpose":"检查 ServiceAccount 是否引用了缺失的 imagePullSecret","evidence_type":"serviceaccount_verification","target_scope":"aiops-e2e/default","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"检查 Pod 'rc-imagepull-missing-secret' 的完整 YAML 定义，确认 image 字段、imagePullPolicy 和 imagePullSecret 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-imagepull-missing-secret -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-imagepull-missing-secret","kind":"pod"},"purpose":"获取 Pod 完整配置以检查镜像和拉取策略","evidence_type":"yaml_verification","target_scope":"aiops-e2e/rc-imagepull-missing-secret","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-missing-secret\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal  BackOff  3m12s (x489 over 113m)  kubelet  Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"\n      Reason:       ImagePullBackOff\n                  cni.projectcalico.org/containerID: 15f21d5a2bf23a2e830e964c48d8c66a8fd40e50e94b550106a5ce8726d9507f\n                  cni.projectcalico.org/podIP: 172.16.166.166/32\n                  cni.projectcalico.org/podIPs: 172.16.166.166/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed\n    State:          Waiting","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=197 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret rc-definitely-missing-pull-secret -n aiops-e2e\nError from server (NotFound): secrets \"rc-definitely-missing-pull-secret\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME      SECRETS   AGE    LABELS\ndefault   0         111d   <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/003-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-imagepull-missing-secret\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T11:21:51Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: rc-definitely-missing-pull-secret\nphase: Pending\nlabels: app=rc-imagepull-missing-secret, pod_abnormal_type=ImagePullFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-imagepull-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=registry.invalid/aiops/private-rootcause:v0 imagePullPolicy=Always\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"\nvolumes:\n- {\"name\": \"kube-api-access-bnw7m\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/124d902986d8447b/tools/004-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_describe` 显示 Pod 状态为 Pending，事件表明镜像拉取失败（`ImagePullBackOff`）。\n2. `kubectl_get_by_name` 确认 `rc-definitely-missing-pull-secret` 不存在。\n3. `kubectl_get_by_name` 显示 `default` ServiceAccount 没有关联任何 Secret。\n4. `kubectl_get_yaml` 显示 Pod 配置中引用了缺失的 `rc-definitely-missing-pull-secret` 作为 `imagePullSecrets`。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无\n\n总结：\n- Pod `rc-imagepull-missing-secret` 状态为 `ImagePullBackOff`。\n- 指定的 `imagePullSecret` `rc-definitely-missing-pull-secret` 不存在。\n- `default` ServiceAccount 未配置 `imagePullSecrets`。\n- Pod 配置中引用了不存在的 `imagePullSecret`。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 4 个，未规划证据 5 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":4,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 'rc-imagepull-missing-secret' 的详细描述信息，确认镜像拉取失败原因和 imagePullSecret 配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e","purpose":"获取 Pod 详细状态、Events、imagePullSecret 配置等信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查 Pod 所引用的 imagePullSecret 'rc-definitely-missing-pull-secret' 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-pull-secret -n aiops-e2e","purpose":"验证 imagePullSecret 是否存在","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e3","description":"验证 Pod 所属 ServiceAccount 'default' 是否正确配置了 imagePullSecret 'rc-definitely-missing-pull-secret'","level":"important","tool":"kubectl_get_by_name","command":"kubectl get serviceaccount default -n aiops-e2e","purpose":"检查 ServiceAccount 是否引用了缺失的 imagePullSecret","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"检查 Pod 'rc-imagepull-missing-secret' 的完整 YAML 定义，确认 image 字段、imagePullPolicy 和 imagePullSecret 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-imagepull-missing-secret -n aiops-e2e -o yaml","purpose":"获取 Pod 完整配置以检查镜像和拉取策略","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常 Pod 'rc-imagepull-missing-secret' 的详细描述信... | `kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_name | 检查 Pod 所引用的 imagePullSecret 'rc-definitely-mi... | `kubectl get secret rc-definitely-missing-pull-secret -n aiops-e2e` |
   | e3 | important | ✅ | kubectl_get_by_name | 验证 Pod 所属 ServiceAccount 'default' 是否正确配置了 im... | `kubectl get serviceaccount default -n aiops-e2e` |
   | e4 | important | ✅ | kubectl_get_yaml | 检查 Pod 'rc-imagepull-missing-secret' 的完整 YAML... | `kubectl get pod rc-imagepull-missing-secret -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (11.6s)
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
   ✅ [汇总总结] 完成 (2m 9.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4298 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 12.4s
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
| **证据完整度** | 4/4 (100%) |

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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ImagePullBackOff` | Pod 因镜像拉取失败进入 ImagePullBackOff 状态 |
| 2 | Events 信息 | `kubectl describe pod` | `Normal  BackOff  3m12s (x489 over 113m)  kubelet  Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"` | 明确指出镜像拉取失败 |
| 3 | imagePullSecret 存在性 | `kubectl get secret` | `Error from server (NotFound): secrets "rc-definitely-missing-pull-secret" not found` | 指定的 imagePullSecret 不存在 |
| 4 | Pod YAML 配置 | `kubectl get pod -o yaml` | `imagePullSecrets: rc-definitely-missing-pull-secret` | Pod 引用了不存在的 imagePullSecret |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `ImagePullBackOff`，Events 明确指出镜像拉取失败，指向 `registry.invalid/aiops/private-rootcause:v0`。
- **证据 #3 印证**：imagePullSecret `rc-definitely-missing-pull-secret` 不存在，导致认证失败。
- **证据 #4 印证**：Pod 配置中引用了不存在的 imagePullSecret，导致镜像拉取失败。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ imagePullSecret 'rc-definitely-missing-pull-secret' 不存在，导致镜像拉取认证失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 尝试拉取镜像，但缺少认证凭证，导致拉取失败。            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 拉取镜像失败，进入 ImagePullBackOff 状态。                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ImagePullBackOff，无法正常启动。                     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #3 和 #4，问题的根本原因是 **Pod 引用了不存在的 imagePullSecret `rc-definitely-missing-pull-secret`**，导致镜像拉取认证失败，从而进入 `ImagePullBackOff` 状态。

**置信度**：高 (100%)
- ✅ `kubectl get secret` 明确显示该 Secret 不存在
- ✅ `kubectl describe pod` 显示镜像拉取失败
- ✅ `kubectl get pod -o yaml` 显示引用了该不存在的 Secret

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 imagePullSecret**

```bash
kubectl create secret docker-registry rc-definitely-missing-pull-secret \
  -n aiops-e2e \
  --docker-server=registry.invalid \
  --docker-username=<your-username> \
  --docker-password=<your-password> \
  --docker-email=<your-email>
```

*依据*：当前 imagePullSecret 不存在，需要创建后重新尝试拉取镜像。

**2. [可选] 检查镜像地址是否正确**

```bash
kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e
```

*目的*：确认镜像地址 `registry.invalid/aiops/private-rootcause:v0` 是否正确，是否存在拼写错误。

**3. [可选] 验证镜像仓库连通性（在节点上执行）**

```bash
docker login registry.invalid -u <your-username> -p <your-password>
docker pull registry.invalid/aiops/private-rootcause:v0
```

*目的*：确认节点上是否可以成功拉取镜像，排除网络或 TLS 问题。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-imagepull-missing-secret -n aiops-e2e` | STATUS: Running |
| 2. 确认 imagePullSecret 存在 | `kubectl get secret rc-definitely-missing-pull-secret -n aiops-e2e` | 输出包含该 Secret 信息 |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e` | 无 `Back-off pulling image` 事件 |

---

## ⚠️ 注意事项

- 如果镜像地址错误，需要修改 Deployment 或 Pod 的 `image` 字段。
- 如果镜像仓库地址不正确或镜像不存在，需联系镜像仓库管理员确认镜像地址和版本。
- 如果镜像仓库使用 HTTPS 但证书不可信，需在节点上添加信任证书或使用 `--insecure-registries` 启动 kubelet（不推荐生产环境）。

---

## 📌 附注

- **镜像地址**：`registry.invalid/aiops/private-rootcause:v0`
- **Pod 命名空间**：`aiops-e2e`
- **ServiceAccount**：`default`（未正确配置 imagePullSecret）

---

---

## 📊 性能统计

├─ 总耗时: 5.2m
├─ 问题定位: 54.8s (18%) ✅
├─ 证据链采集: 117.0s (37%) ✅
├─ 根因分析: 11.6s (4%) ✅
├─ 汇总总结: 129.0s (41%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
