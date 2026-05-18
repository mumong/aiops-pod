======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f973795bde3f406f]

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
53m (x4 over 54m)       Warning   Failed           Pod/rc-imagepull-invalid-registry   Failed to pull image "registry.invalid/aiops/rootcause:v0": rpc error: code = Unknown d
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
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ServiceAccount
name: default
namespace: aiops-e2e
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
   💭 [问题定位] 调用工具: run_bash_command
   💭 [问题定位] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\n                                 Dload  Upload   Total   Spent    Left  Spe
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": ["L3"],
  "layer_name": "镜像拉取失败",
  "confidence": "高",
  "reasoning": "Pod 'rc-imagepull-invalid-registry' 的状态为 'ImagePullBackOff'，Events 显示镜像拉取失败，错误信息 'lookup registry.invalid on 127.0.0.53:53: no such host' 表明镜像仓库地址无法解析。进一步通过 curl 命令验证镜像仓库连通性失败，错误信息 'Could not resolve host: registry.invalid' 确认 DNS 解析失败。这些证据表明镜像仓库网络不可达，属于 L3 层问题。",
  "abnormal_pods": ["rc-imagepull-invalid-registry"],
  "abnormal_groups": ["ImagePullBackOff"],
  "pod_status_keyword": "ImagePullBackOff",
  "pod_abnormal_type": "ImagePullFailed",
  "status_category": "镜像拉取失败",
  "key_entities": ["Pod/rc-imagepull-invalid-registry", "镜像仓库 registry.invalid"],
  "possible_scenarios": [
    "镜像仓库地址错误或 DNS 配置不当导致无法解析 registry.invalid",
    "节点缺少到 registry.invalid 的网络连接",
    "镜像仓库 registry.invalid 不存在或配置错误",
    "镜像名称或 tag 错误，导致镜像拉取失败"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 6.6s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像仓库地址错误或 DNS 配置不当导致无法解析 registry.invalid', 'probability': '高', 'reason': "Events 显示 'lookup registry.invalid on 127.0.0.53:53: no such host'，curl 命令也显示 'Could not resolve host: registry.invalid'，表明 DNS 解析失败。"}, {'scenario': '节点缺少到 registry.invalid 的网络连接', 'probability': '中', 'reason': '镜像仓库地址可能无法通过当前节点访问，需检查网络策略、防火墙或路由配置。'}, {'scenario': '镜像仓库 registry.invalid 不存在或配置错误', 'probability': '中', 'reason': '镜像仓库地址可能无效，或镜像名称/版本不存在。'}, {'scenario': '镜像名称或 tag 错误，导致镜像拉取失败', 'probability': '低', 'reason': '镜像名称或 tag 错误是可能原因之一，但当前证据更指向网络或 DNS 问题。'}]
   entities=[{"type": "Pod", "name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e"}, {"type": "镜像仓库", "name": "registry.invalid", "namespace": ""}]
   reasoning=Pod 'rc-imagepull-invalid-registry' 的状态为 'ImagePullBackOff'，Events 显示镜像拉取失败，错误信息 'lookup registry.invalid on 127.0.0.53:53: no such host' 表明镜像仓库地址无法解析。进一步通过 curl 命令验证镜像仓库连通性失败，错误信息 'Could not resolve host: registry.invalid' 确认 DNS 解析失败。这些证据表明镜像仓库网络不可达，属于 L3 层问题。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "镜像拉取失败", "confidence": 0.8, "reasoning": "Pod 'rc-imagepull-invalid-registry' 的状态为 'ImagePullBackOff'，Events 显示镜像拉取失败，错误信息 'lookup registry.invalid on 127.0.0.53:53: no such host' 表明镜像仓库地址无法解析。进一步通过 curl 命令验证镜像仓库连通性失败，错误信息 'Could not resolve host: registry.invalid' 确认 DNS 解析失败。这些证据表明镜像仓库网络不可达，属于 L3 层问题。", "abnormal_pods": [{"name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "Pod", "name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e"}, {"type": "镜像仓库", "name": "registry.invalid", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库地址错误或 DNS 配置不当导致无法解析 registry.invalid", "probability": "高", "reason": "Events 显示 'lookup registry.invalid on 127.0.0.53:53: no such host'，curl 命令也显示 'Could not resolve host: registry.invalid'，表明 DNS 解析失败。"}, {"scenario": "节点缺少到 registry.invalid 的网络连接", "probability": "中", "reason": "镜像仓库地址可能无法通过当前节点访问，需检查网络策略、防火墙或路由配置。"}, {"scenario": "镜像仓库 registry.invalid 不存在或配置错误", "probability": "中", "reason": "镜像仓库地址可能无效，或镜像名称/版本不存在。"}, {"scenario": "镜像名称或 tag 错误，导致镜像拉取失败", "probability": "低", "reason": "镜像名称或 tag 错误是可能原因之一，但当前证据更指向网络或 DNS 问题。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-imagepull-invalid-registry                       0/1     ImagePullBackOff   0             54m    172.16.166.156   node1    <none>           <none>            app=rc-imagepull-invalid-registry,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 80%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
creationTimestamp: 2026-05-14T06:17:48Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finaliz
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
55m (x4 over 57m)       Warning   Failed           Pod/rc-imagepull-invalid-registry   Failed to pull image "registry.invalid/aiops/rootcause:v0": rpc error: code = Unknown d
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\n                                 Dload  Upload   Total   Spent    Left  Spe
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=197 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret app=rc-imagepull-invalid-registry -n aiops-e2e
Error from server (NotFound): secrets "
   💭 [证据链采集] 已采集证据：
1. Pod `rc-imagepull-invalid-registry` 的 YAML 配置显示镜像地址为 `registry.invalid/aiops/rootcause:v0`，镜像拉取策略为 `Always`，且未配置 `imagePullSecrets`。
2. Pod 的事件日志显示镜像拉取失败，错误信息为 `lookup registry.invalid on 127.0.0.53:53: no such host`，表明 DNS 解析失败。
3. 通过 `curl` 命令尝试访问镜像仓库 `registry.invalid/v2/aiops/rootcause/manifests/v0` 失败，错误信息 `Could not resolve host: registry.invalid` 确认了 DNS 解析失败。
4. 在命名空间 `aiops-e2e` 中未找到与标签 `app=rc-imagepull-invalid-registry` 匹配的 `Secret`，表明未配置用于私有仓库认证的 `imagePullSecret`。

未采集证据：
- 无

冲突证据：
- 无

结论：当前异常组中的 Pod `rc-imagepull-invalid-registry` 无法拉取镜像，主要原因是镜像仓库地址 `registry.invalid` 无法解析，即 DNS 配置不当。此外，未配置 `imagePullSecrets` 也可能导致认证失败。建议检查 DNS 配置并确保镜像仓库地址正确。
   ✅ [证据链采集] 完成 (2m 9.1s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 'rc-imagepull-invalid-registry' 的详细状态，包括其镜像配置和拉取策略。","level":"critical","tool":"kubectl_get_yaml","command":"get pod rc-imagepull-invalid-registry -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","kind":"Pod","name":"rc-imagepull-invalid-registry"},"purpose":"验证 Pod spec 中的镜像名称、镜像拉取策略及 imagePullSecrets 配置。","evidence_type":"pod_spec","target_scope":"Pod/aiops-e2e/rc-imagepull-invalid-registry","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 'rc-imagepull-invalid-registry' 的 Events，验证镜像拉取失败的具体原因。","level":"critical","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","tool_args":{"namespace":"aiops-e2e","kind":"Pod","name":"rc-imagepull-invalid-registry"},"purpose":"确认 Pod 事件中是否包含 'Failed to pull image'、'ImagePullBackOff'、'ErrImagePull' 等信号。","evidence_type":"events","target_scope":"Pod/aiops-e2e/rc-imagepull-invalid-registry","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"验证镜像仓库 registry.invalid 的连通性与 DNS 解析。","level":"critical","tool":"run_bash_command","command":"curl -v https://registry.invalid/v2/aiops/rootcause/manifests/v0","tool_args":{"command":"curl -v https://registry.invalid/v2/aiops/rootcause/manifests/v0"},"purpose":"确认 registry.invalid 是否可解析并响应请求，验证网络与 DNS 问题。","evidence_type":"network_dns","target_scope":"镜像仓库/registry.invalid","acceptable_tools":["run_bash_command"],"counts_for_completeness":true},{"id":"e4","description":"验证 Pod 'rc-imagepull-invalid-registry' 的 imagePullSecrets 是否存在并有效。","level":"important","tool":"kubectl_get_by_name","command":"get secret -n aiops-e2e -l app=rc-imagepull-invalid-registry","tool_args":{"namespace":"aiops-e2e","kind":"Secret","label_selector":"app=rc-imagepull-invalid-registry"},"purpose":"检查是否存在 imagePullSecret 并验证其配置是否正确。","evidence_type":"imagepullsecret","target_scope":"Secret/aiops-e2e/related-to-rc-imagepull-invalid-registry","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T06:17:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-imagepull-invalid-registry, pod_abnormal_type=ImagePullFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-imagepull-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=registry.invalid/aiops/rootcause:v0 imagePullPolicy=Always\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\nvolumes:\n- {\"name\": \"kube-api-access-nszzv\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n55m (x4 over 57m)       Warning   Failed           Pod/rc-imagepull-invalid-registry   Failed to pull image \"registry.invalid/aiops/rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n2m19s (x241 over 57m)   Normal    BackOff          Pod/rc-imagepull-invalid-registry   Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n55m (x4 over 57m)       Warning   Failed           Pod/rc-imagepull-invalid-registry   Error: ErrImagePull\n55m (x6 over 57m)       Warning   Failed           Pod/rc-imagepull-invalid-registry   Error: ImagePullBackOff","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\\n                                 Dload  Upload   Total   Spent    Left  Speed\\n\\n  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0* Could not resolve host: registry.invalid\\n* shutting down connection #0\\ncurl: (6) Could not resolve host: registry.invalid\\n\", \"returncode\": 6}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/003-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/003-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/003-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=197 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret app=rc-imagepull-invalid-registry -n aiops-e2e\nError from server (NotFound): secrets \"app=rc-imagepull-invalid-registry\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/004-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/004-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f973795bde3f406f/tools/004-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n1. Pod `rc-imagepull-invalid-registry` 的 YAML 配置显示镜像地址为 `registry.invalid/aiops/rootcause:v0`，镜像拉取策略为 `Always`，且未配置 `imagePullSecrets`。\n2. Pod 的事件日志显示镜像拉取失败，错误信息为 `lookup registry.invalid on 127.0.0.53:53: no such host`，表明 DNS 解析失败。\n3. 通过 `curl` 命令尝试访问镜像仓库 `registry.invalid/v2/aiops/rootcause/manifests/v0` 失败，错误信息 `Could not resolve host: registry.invalid` 确认了 DNS 解析失败。\n4. 在命名空间 `aiops-e2e` 中未找到与标签 `app=rc-imagepull-invalid-registry` 匹配的 `Secret`，表明未配置用于私有仓库认证的 `imagePullSecret`。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无\n\n结论：当前异常组中的 Pod `rc-imagepull-invalid-registry` 无法拉取镜像，主要原因是镜像仓库地址 `registry.invalid` 无法解析，即 DNS 配置不当。此外，未配置 `imagePullSecrets` 也可能导致认证失败。建议检查 DNS 配置并确保镜像仓库地址正确。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 10 个，匹配计划 4 个，未规划证据 6 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":10,"matched_tool_count":4,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 'rc-imagepull-invalid-registry' 的详细状态，包括其镜像配置和拉取策略。","level":"critical","tool":"kubectl_get_yaml","command":"get pod rc-imagepull-invalid-registry -n aiops-e2e -o yaml","purpose":"验证 Pod spec 中的镜像名称、镜像拉取策略及 imagePullSecrets 配置。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 'rc-imagepull-invalid-registry' 的 Events，验证镜像拉取失败的具体原因。","level":"critical","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-invalid-registry","purpose":"确认 Pod 事件中是否包含 'Failed to pull image'、'ImagePullBackOff'、'ErrImagePull' 等信号。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证镜像仓库 registry.invalid 的连通性与 DNS 解析。","level":"critical","tool":"run_bash_command","command":"curl -v https://registry.invalid/v2/aiops/rootcause/manifests/v0","purpose":"确认 registry.invalid 是否可解析并响应请求，验证网络与 DNS 问题。","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e4","description":"验证 Pod 'rc-imagepull-invalid-registry' 的 imagePullSecrets 是否存在并有效。","level":"important","tool":"kubectl_get_by_name","command":"get secret -n aiops-e2e -l app=rc-imagepull-invalid-registry","purpose":"检查是否存在 imagePullSecret 并验证其配置是否正确。","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: run_bash_command","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 获取异常 Pod 'rc-imagepull-invalid-registry' 的详细状... | `get pod rc-imagepull-invalid-registry -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_events | 获取异常 Pod 'rc-imagepull-invalid-registry' 的 Ev... | `get events -n aiops-e2e --field-selector=involvedObject.name=rc-imagepull-inv...` |
   | e3 | critical | ✅ | run_bash_command | 验证镜像仓库 registry.invalid 的连通性与 DNS 解析。 | `curl -v https://registry.invalid/v2/aiops/rootcause/manifests/v0` |
   | e4 | important | ✅ | kubectl_get_by_name | 验证 Pod 'rc-imagepull-invalid-registry' 的 imag... | `get secret -n aiops-e2e -l app=rc-imagepull-invalid-registry` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (2m 31.5s)
   📤 → 下游数据: root_cause=镜像仓库地址 registry.invalid 无法解析，导致镜像拉取失败。证据包括 Pod 的事件日志显示 lookup registry.invalid on 127.0.0.53:53: no such host，以及 curl 命令验证镜像仓库连通性失败，错误信息 Could not resolve host: registry.invalid。
   confidence=80%
   causal_chain={"root_cause": "镜像仓库地址 registry.invalid 无法解析，导致镜像拉取失败。", "intermediate_causes": ["Pod 的镜像配置为 registry.invalid/aiops/rootcause:v0，镜像拉取策略为 Always，但未配置 imagePullSecrets。", "Pod 的事件日志显示镜像拉取失败，错误信息为 lookup registry.invalid on 127.0.0.53:53: no such host，表明 DNS 解析失败。", "通过 curl 命令验证镜像仓库连通性失败，错误信息 Could not resolve host: registry.invalid 确认了 DNS 解析失败。"], "direct_causes": ["镜像仓库地址 registry.invalid 无法解析，导致镜像拉取失败。"], "symptoms": ["Pod 'rc-imagepull-invalid-registry' 的状态为 ImagePullBackOff。", "Pod 的事件日志显示镜像拉取失败。", "镜像仓库地址 registry.invalid 无法解析。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"description": "获取异常 Pod 'rc-imagepull-invalid-registry' 的详细状态，包括其镜像配置和拉取策略。", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T06:17:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-imagepull-invalid-registry, pod_abnormal_type=ImagePullFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-imagepull-failed.md\ntole"}, {"description": "获取异常 Pod 'rc-imagepull-invalid-registry' 的 Events，验证镜像拉取失败的具体原因。", "level": "critical", "value": "kubectl_events 摘要:\n关键诊断行:\n55m (x4 over 57m)       Warning   Failed           Pod/rc-imagepull-invalid-registry   Failed to pull image \"registry.invalid/aiops/rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n2m19"}, {"description": "验证镜像仓库 registry.invalid 的连通性与 DNS 解析。", "level": "critical", "value": "{\"success\": false, \"stdout\": \"\", \"stderr\": \"  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\\n                                 Dload  Upload   Total   Spent    Left  Speed\\n\\n  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0* Could not resolve host: registry.invalid\\n* shutting down connection #0\\ncurl: (6) Could not resolve host: registry.invalid\\n\", \"returncode\": 6}"}, {"description": "验证 Pod 'rc-imagepull-invalid-registry' 的 imagePullSecrets 是否存在并有效。", "level": "important", "value": "kubectl_get_by_name 输出摘要: raw_chars=197 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret app=rc-imagepull-invalid-registry -n aiops-e2e\nError from server (NotFound): secrets \"app=rc-imagepull-invalid-registry\" not found"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'ImagePullBackOff': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS             RESTARTS      AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-imagepull-invalid-registry                       0/1     ImagePullBackOff   0             54m    172.16.166.156   node1    <none>           <none>            app=rc-imagepull-invalid-reg"}, {"description": "上游已验证工具结果: kubectl_events", "level": "important", "value": "kubectl_events 摘要:\n关键诊断行:\n53m (x4 over 54m)       Warning   Failed           Pod/rc-imagepull-invalid-registry   Failed to pull image \"registry.invalid/aiops/rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n4m27"}, {"description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T06:17:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-imagepull-invalid-registry, pod_abnormal_type=ImagePullFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-imagepull-failed.md\ntole"}, {"description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: ServiceAccount\nname: default\nnamespace: aiops-e2e"}, {"description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T06:17:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-imagepull-invalid-registry, pod_abnormal_type=ImagePullFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-imagepull-failed.md\ntole"}, {"description": "上游已验证工具结果: run_bash_command", "level": "important", "value": "{\"success\": false, \"stdout\": \"\", \"stderr\": \"  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\\n                                 Dload  Upload   Total   Spent    Left  Speed\\n\\n  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0* Could not resolve host: registry.invalid\\n* shutting down connection #0\\ncurl: (6) Could not resolve host: registry.invalid\\n\", \"returncode\": 6}"}], "evidence_analysis": [{"description": "获取异常 Pod 'rc-imagepull-invalid-registry' 的详细状态，包括其镜像配置和拉取策略。", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T06:17:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-imagepull-invalid-registry, pod_abnormal_type=ImagePullFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-imagepull-failed.md\ntole"}, {"description": "获取异常 Pod 'rc-imagepull-invalid-registry' 的 Events，验证镜像拉取失败的具体原因。", "level": "critical", "value": "kubectl_events 摘要:\n关键诊断行:\n55m (x4 over 57m)       Warning   Failed           Pod/rc-imagepull-invalid-registry   Failed to pull image \"registry.invalid/aiops/rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n2m19"}, {"description": "验证镜像仓库 registry.invalid 的连通性与 DNS 解析。", "level": "critical", "value": "{\"success\": false, \"stdout\": \"\", \"stderr\": \"  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\\n                                 Dload  Upload   Total   Spent    Left  Speed\\n\\n  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0* Could not resolve host: registry.invalid\\n* shutting down connection #0\\ncurl: (6) Could not resolve host: registry.invalid\\n\", \"returncode\": 6}"}], "causal_chain": {"root_cause": "镜像仓库地址 registry.invalid 无法解析，导致镜像拉取失败。", "intermediate_causes": ["Pod 的镜像配置为 registry.invalid/aiops/rootcause:v0，镜像拉取策略为 Always，但未配置 imagePullSecrets。", "Pod 的事件日志显示镜像拉取失败，错误信息为 lookup registry.invalid on 127.0.0.53:53: no such host，表明 DNS 解析失败。", "通过 curl 命令验证镜像仓库连通性失败，错误信息 Could not resolve host: registry.invalid 确认了 DNS 解析失败。"], "direct_causes": ["镜像仓库地址 registry.invalid 无法解析，导致镜像拉取失败。"], "symptoms": ["Pod 'rc-imagepull-invalid-registry' 的状态为 ImagePullBackOff。", "Pod 的事件日志显示镜像拉取失败。", "镜像仓库地址 registry.invalid 无法解析。"]}, "root_cause": "镜像仓库地址 registry.invalid 无法解析，导致镜像拉取失败。证据包括 Pod 的事件日志显示 lookup registry.invalid on 127.0.0.53:53: no such host，以及 curl 命令验证镜像仓库连通性失败，错误信息 Could not resolve host: registry.invalid。", "root_cause_summary": "镜像仓库地址 registry.invalid 无法解析，导致镜像拉取失败。证据包括 Pod 的事件日志显示 lookup registry.invalid on 127.0.0.53:53: no such host，以及 curl 命令验证镜像仓库连通性失败，错误信息 Could not resolve host: registry.invalid。", "confidence": 0.8, "confidence_reason": "有直接证据，包括 Pod 的事件日志和 curl 命令验证结果，因果链清晰。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"description": "镜像名称或 tag 错误，导致镜像拉取失败。", "probability": "低", "reason": "镜像名称或 tag 错误是可能原因之一，但当前证据更指向网络或 DNS 问题。"}], "limitations": "无", "llm_raw_analysis": "已采集证据：\n1. Pod `rc-imagepull-invalid-registry` 的 YAML 配置显示镜像地址为 `registry.invalid/aiops/rootcause:v0`，镜像拉取策略为 `Always`，且未配置 `imagePullSecrets`。\n2. Pod 的事件日志显示镜像拉取失败，错误信息为 `lookup registry.invalid on 127.0.0.53:53: no such host`，表明 DNS 解析失败。\n3. 通过 `curl` 命令尝试访问镜像仓库 `registry.invalid/v2/aiops/rootcause/manifests/v0` 失败，错误信息 `Could not resolve host: registry.invalid` 确认了 DNS 解析失败。\n4. 在命名空间 `aiops-e2e` 中未找到与标签 `app=rc-imagepull-invalid-registry` 匹配的 `Secret`，表明未配置用于私有仓库认证的 `imagePullSecret`。\n\n未采集证据：\n... 截断，原始 676 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 镜像仓库地址 registry.invalid 无法解析，导致镜像拉取失败。证据包括 Pod 的事件日志显示 lookup registry.invalid on 127.0.0.53:53: no such host，以及 curl 命令验证镜像仓库连通性失败，错误信息 Could not res...
   置信度: 80%
   🔗 因果链:
     根本原因: 镜像仓库地址 registry.invalid 无法解析，导致镜像拉取失败。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 19.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4234 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 7m 7.1s
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
| **兼容归因层** | L3 - 网络层 |
| **问题分类** | ImagePullFailed |
| **置信度** | 高 (80%) |
| **证据完整度** | 4/4 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-imagepull-invalid-registry |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | lookup registry.invalid on 127.0.0.53:53: no such host |

当前集群中有一个 Pod 处于 `ImagePullBackOff` 状态，无法成功拉取镜像。错误信息表明镜像仓库地址 `registry.invalid` 无法解析，且 curl 命令验证也失败，进一步确认了 DNS 解析失败。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `Status: ImagePullBackOff` | Pod 因镜像拉取失败进入 ImagePullBackOff 状态 |
| 2 | Pod Events | `kubectl describe pod rc-imagepull-invalid-registry` | `Warning Failed: lookup registry.invalid on 127.0.0.53:53: no such host` | DNS 解析失败导致镜像拉取失败 |
| 3 | 镜像仓库连通性 | `curl registry.invalid` | `Could not resolve host: registry.invalid` | registry.invalid 无法解析，网络不可达 |
| 4 | imagePullSecrets | `kubectl get pod rc-imagepull-invalid-registry -o yaml` | `imagePullSecrets: <absent>` | 未配置镜像拉取凭证，但当前问题不涉及认证 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `ImagePullBackOff`，Events 明确指出 DNS 解析失败，指向镜像仓库无法访问。
- **证据 #3 印证**：curl 命令失败，进一步验证了 DNS 解析失败。
- **证据链总结**：`registry.invalid` 无法解析 → 镜像拉取失败 → Pod 进入 `ImagePullBackOff` 状态。

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────┐
│ 根本原因                                                         │
│ registry.invalid 无法解析，DNS 配置错误或镜像仓库地址错误          │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 传导机制                                                         │
│ 镜像仓库地址无法解析 → 无法拉取镜像 → 镜像拉取失败                │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 直接原因                                                         │
│ Pod 无法拉取镜像 registry.invalid/aiops/rootcause:v0，报错 DNS 无法解析 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                     │
│ Pod 状态为 ImagePullBackOff，Events 显示 lookup registry.invalid 失败 │
└──────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（Pod Events 显示 lookup registry.invalid 失败）和证据 #3（curl 验证 registry.invalid 无法解析），问题的根本原因是 **镜像仓库地址 `registry.invalid` 无法解析**，属于 DNS 配置错误或镜像仓库地址错误。

**置信度**：高 (80%)

- ✅ Events 明确指出 lookup registry.invalid 失败
- ✅ curl 验证也显示无法解析 registry.invalid
- ⚠️ 未验证镜像仓库地址是否真实存在或拼写错误

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并修正镜像仓库地址**

确认镜像地址是否拼写错误或配置错误。例如：

```bash
kubectl edit pod rc-imagepull-invalid-registry -n aiops-e2e
```

将镜像地址修改为有效的镜像仓库地址（如 `registry.example.com/aiops/rootcause:v0`）。

**2. [优先] 检查节点 DNS 配置**

确保节点的 `/etc/resolv.conf` 文件中包含有效的 DNS 服务器。例如：

```bash
cat /etc/resolv.conf
```

若 DNS 配置错误，可手动修改：

```bash
echo "nameserver 8.8.8.8" > /etc/resolv.conf
```

**3. [可选] 配置 imagePullSecrets（如果镜像仓库是私有的）**

如果镜像仓库需要认证，确保 Pod 配置了正确的 `imagePullSecrets`：

```bash
kubectl create secret docker-registry my-registry-secret \
  --docker-server=registry.invalid \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email> -n aiops-e2e
```

然后在 Pod 的 YAML 中添加：

```yaml
imagePullSecrets:
  - name: my-registry-secret
```

**4. [可选] 检查镜像仓库是否存在**

验证镜像仓库 `registry.invalid` 是否真实存在，是否能通过浏览器或 curl 访问：

```bash
curl -I https://registry.invalid/v2/
```

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-imagepull-invalid-registry -n aiops-e2e` | STATUS: Running |
| 2. 检查 Events | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` | 无 Failed 消息 |
| 3. 验证镜像仓库连通性 | `curl registry.invalid` | 返回有效响应或 404，但无 DNS 解析错误 |

---

## ⚠️ 注意事项

- 如果 registry.invalid 是自建镜像仓库，请确认其服务是否正常运行，并且 DNS 配置正确。
- 如果是云服务提供的镜像仓库，请确认网络策略是否允许节点访问该地址。
- 如果镜像仓库地址正确，但仍然无法解析，请检查集群节点的 DNS 配置或联系网络管理员。

---

## 📊 性能统计

├─ 总耗时: 7.1m
├─ 问题定位: 66.6s (16%) ✅
├─ 证据链采集: 129.1s (30%) ✅
├─ 根因分析: 151.5s (35%) ✅
├─ 汇总总结: 79.9s (19%) ✅
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
