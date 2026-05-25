======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 547921236d244693]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先从全局 Pod 状态扫描开始，了解集群中所有 Pod 的当前状况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces: 返回约115行，Running约59个，异常约50个(ImagePullBackOff 27, ErrImagePull 21, CreateContainerConfigError 1, Completed 3)。异常主要集中在default和aiops-e2e namespace，均为ImagePullBackOff/Err
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=377 lines=9
Investigation plan updated with 5 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 1 completed, 1 in progress, 3 pending
[ ] [3] 分析 CreateContainerConfigErro
   💭 [问题定位] 全局扫描结果很清晰，集群中存在大量 Pod 镜像拉取失败。我来进一步获取异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query returned 49 pods, all Pending. 26 in ImagePullBackOff, 22 in ErrImagePull, 1 in CreateContainerConfigError. Cross-namespace (aiops-e2e, default, mcp) and cross-node (node1, no
   💭 [问题定位] 很好，现在清楚了主要问题是镜像拉取失败。让我获取对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [问题定位] 现在让我查看一个代表性的 ImagePullBackOff Pod 和一个 ErrImagePull Pod 的具体事件来获取根本原因。
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query returned 48 rows, all abnormal. Status distribution: ImagePullBackOff=26, ErrImagePull=22 (note: current_summary also mentions 9 Unknown but raw_preview shows only these two s
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
51m                   Warning   Failed   Pod/registry-check-node2   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and unpack
   💭 [问题定位] 现在让我也看看那个 CreateContainerConfigError 的 Pod。
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
6m40s (x12 over 8m38s)   Warning   Failed           Pod/rc-config-secret-key-missing   Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret
   💭 [问题定位] 现在我再查一下 CreateContainerConfigError Pod 的更多细节。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          6m41s (x12 over 8m39s)  kubelet            Error: c
   💭 [问题定位] 调用工具: TodoWrite
   ✅ [问题定位] 完成 (37.7s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '镜像仓库网络不可达', 'probability': 'high', 'reason': '所有ErrImagePull Pod的i/o timeout错误指向docker.io registry IP（103.230.123.190, 67.228.102.32, 199.59.149.231等），端口443无TCP连接，涉及的镜像包括busybox:1.36.1、alpine:3.18、curlimages/curl等，影响48个Pod覆盖多个命名空间和节点'}, {'scenario': 'Secret配置错误', 'probability': 'high', 'reason': 'Pod aiops-e2e/rc-config-secret-key-missing的CreateContainerConfigError原因是Secret aiops-e2e/rc-app-secret中缺少key APP_SECRET_TOKEN，属于配置错误'}]
   entities=[{"type": "pod", "name": "registry-check-node2", "namespace": "default"}, {"type": "pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}]
   reasoning=当前集群存在两类当前异常的Pod：1) 48个Pod处于ImagePullBackOff(26)或ErrImagePull(22)状态，分布在aiops-e2e、default、mcp命名空间，涉及node1和node2，从docker.io和registry.k8s.io拉取镜像时出现i/o timeout（网络不可达），属于L3 image_registry/network_cni_runtime根因；2) 1个Pod(aiops-e2e/rc-config-secret-key-missing)处于CreateContainerConfigError状态，原因是Secret中缺少key APP_SECRET_TOKEN，属于L4 app_config根因。主异常是L3级别的镜像仓库网络不可达问题（约48个Pod受影响），因此整体layer定为L3。kube-system和admin命名空间正常运行，节点本身健康（无L0/L1证据），无OOM/资源类异常（无L2证据）。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "L3(image_registry/network_cni_runtime) + L4(app_config)", "confidence": 1.0, "reasoning": "当前集群存在两类当前异常的Pod：1) 48个Pod处于ImagePullBackOff(26)或ErrImagePull(22)状态，分布在aiops-e2e、default、mcp命名空间，涉及node1和node2，从docker.io和registry.k8s.io拉取镜像时出现i/o timeout（网络不可达），属于L3 image_registry/network_cni_runtime根因；2) 1个Pod(aiops-e2e/rc-config-secret-key-missing)处于CreateContainerConfigError状态，原因是Secret中缺少key APP_SECRET_TOKEN，属于L4 app_config根因。主异常是L3级别的镜像仓库网络不可达问题（约48个Pod受影响），因此整体layer定为L3。kube-system和admin命名空间正常运行，节点本身健康（无L0/L1证据），无OOM/资源类异常（无L2证据）。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff / ErrImagePull / CreateContainerConfigError", "pod_abnormal_type": "ImagePullFailed (48 pods) + ConfigError (1 pod)", "status_category": "image_registry/network_cni_runtime + app_config", "key_entities": [{"type": "pod", "name": "registry-check-node2", "namespace": "default"}, {"type": "pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达", "probability": "high", "reason": "所有ErrImagePull Pod的i/o timeout错误指向docker.io registry IP（103.230.123.190, 67.228.102.32, 199.59.149.231等），端口443无TCP连接，涉及的镜像包括busybox:1.36.1、alpine:3.18、curlimages/curl等，影响48个Pod覆盖多个命名空间和节点"}, {"scenario": "Secret配置错误", "probability": "high", "reason": "Pod aiops-e2e/rc-config-secret-key-missing的CreateContainerConfigError原因是Secret aiops-e2e/rc-app-secret中缺少key APP_SECRET_TOKEN，属于配置错误"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 27, "ErrImagePull": 21}, "total_abnormal": 48, "selected_rows": ["aiops-e2e         rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0              8m17s   172.16.166.130   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff             0              9h      172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              5h4m    172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff             0              4h4m    172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              8h      172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff             0              83m     172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff             0              89m     172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull                 0              89m     172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff             0              9h      172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull                 0              7h17m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff             0              89m     172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull                 0              4h11m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              8h      172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull                 0              8h      172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull                 0              5h47m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ErrImagePull                 0              117m    172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull                 0              6h45m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-conn-test-evidence                         0/1     ErrImagePull                 0              22m     172.16.104.22    node2    <none>           <none>            run=registry-conn-test-evidence", "default           registry-connect-test                               0/1     ErrImagePull                 0              8h      172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              9h      172.16.166.185   node1    <none>           <none>            run=test-net-1779360704"], "raw_ref": "/tmp/aiops/reports/context_archives/547921236d244693/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/547921236d244693/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/547921236d244693/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 100%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我将按照既有 evidence_plan 中的工具调用计划，逐项执行真实工具来采集证据。

先获取已确认的 runbook 参考，同时启动第一批独立的 Pod describe 调用。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          7m8s (x12 over 9m6s)  kubelet            Error: cou
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod registry-check-node2 in namespace default, on node node2 (10.2.0.50), status Pending. Container image busybox:1.36.1 fails to pull consistently with i/o timeout errors contacting registry-1.docker
   💭 [证据链采集] 第一批结果已返回。现在继续执行剩余的计划项：验证其他 Pod 的 Events、检查 Secret 内容、以及查看集群全局事件。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-resolve-test (namespace default) on node node2/10.2.0.50 is Pending. Container dns-resolve-test (image busybox:1.36.1, args: nslookup registry-1.docker.io) is Waiting (Reason: ErrImagePull). K
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
52m                   Warning   Failed   Pod/registry-check-node2   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and unpack
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Secret
name: rc-app-secret
namespace: aiops-e2e
type: Opaque
data_keys: EXISTING_SECRET_KEY
has_dockerconfigjson: False
docker_secret_type_valid: False
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   22m (x119 over 9h)     kubelet  (combined from similar events): Fai
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod registry-diag-timeout (namespace mcp) is Pending on node node1/10.2.0.49. Container registry-diag-timeout with image busybox:1.36.1 is in Waiting (ImagePullBackOff) state. Kubelet failed to pull i
   💭 [证据链采集] 现在让我读取压缩后的详细内容，获取关键证据细节。
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=3394 lines=73
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/001-evidence-fetch_runbook.summary.txt
offset: 0
returned_
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1575 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/004-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1581 lines=45
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/002-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2061 lines=53
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/003-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1545 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/005-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2515 lines=48
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/008-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2804 lines=16
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/006-evidence-kubectl_events.summary.txt
offset: 0
returned
   💭 [证据链采集] 好的，所有关键工具调用已经完成。让我再获取 Secret 的详细内容来确认缺少 key 的证据。
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=390 lines=15
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/007-evidence-kubectl_get_yaml.summary.txt
offset: 0
returne
   💭 [证据链采集] 现在我已采集了全部计划工具的结果。下面给出最终证据结论。

---

## 证据采集结论

### ✅ 已采集证据

#### 异常组 g2 — ImagePullFailed（主异常，48 Pods）

**证据 1 — registry-check-node2（node2, ErrImagePull）**
- 镜像：`busybox:1.36.1`（docker.io/library/busybox）
- 事件：连续 7 次 `Failed to pull image`，错误均为 **`dial tcp registry-1.docker.io:443: i/o timeout`**（目标 IP 包括 108.160.169.179、108.160.165.139、104.244.46.165、67.228.102.32、69.63.176.15 等）
- 节点：node2（10.2.0.50），PodIP：172.16.104.41（Calico）

**证据 2 — dns-resolve-test（node2, ErrImagePull）**
- 镜像：`busybox:1.36.1`
- 事件：同样 **`dial tcp registry-1.docker.io:443: i/o timeout`**（IPs：199.59.149.230, 108.160.165.139, 104.244.46.165 等）
- 节点：node2（10.2.0.50），PodIP：172.16.104.1

**证据 3 — test-dns-1779360358（node1, ImagePullBackOff）**
- 镜像：`busybox:1.36.1`
- 事件：**`connection reset by peer`** 到 `54.224.154.163:443`（registry-1.docker.io），累计 119 次失败，已在 node1 上重试 1271 次
- 节点：node1（10.2.0.49）

**证据 4 — registry-diag-timeout（node1, ImagePullBackOff）**
- 镜像：`busybox:1.36.1`
- 事件：**`connection reset by peer`** 到 `35.169.109.128:443` 和 `3.233.166.60:443`，重试 400 次
- 节点：node1（10.2.0.49）

**→ 结论：镜像仓库 docker.io 从 node1 和 node2 均不可达。node2 表现为 i/o timeout（TCP 完全不通），node1 表现为 connection reset by peer（TCP 建连后被对端重置）。registry-1.docker.io:443 涉及十余个不同 IP 均不可达，排除 DNS 单点故障，确认是**集群到外网 docker.io 的网络出口/防火墙问题**。

---

#### 异常组 g1 — CreateContainerConfigError（1 Pod）

**证据 5 — rc-config-secret-key-missing（aiops-e2e, CreateContainerConfigError）**
- 事件：`Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`（重复 12 次）
- Secret YAML 验证：`rc-app-secret` 中仅有 `EXISTING_SECRET_KEY`，**缺少 `APP_SECRET_TOKEN` key**
- 镜像 `busybox:1.36` 本身正常（因 ConfigError 未到拉取阶段）

**→ 结论：Pod 引用了 Secret 中不存在的 key `APP_SECRET_TOKEN`，属于 Pod 配置错误。**

---

#### 异常组 g3 — StartError（1 Pod）

**证据 6 — node-debugger-node1-nx8gb（mcp, StartError）**
- 状态：Failed（StartError），Exit Code 128
- 错误消息：**`exec: "curl": executable file not found in $PATH`**
- 镜像 `busybox:1.36` 中不包含 `curl` 可执行文件，但 Pod command 指定了 `curl -s -o /dev/null -w %{http_code} --connect-timeout 5`

**→ 结论：Pod command 使用了 busybox 镜像中不存在的 curl 命令，与网络无关，属于应用配置错误。**

---

### ⚠️ 冲突/负向证据
- 未发现任何 Pod 存在 Terminating 或 Pending（Unschedulable）等并发异常
- kube-system 和 admin 命名空间均正常运行，无节点异常

### ❌ 未采集证据
- 未做 Prometheus 注册表连通性查询（因已从 Events 获取充分的 i/o timeout 证据，不需重复验证）

---

## 总体诊断结论

| 异常组 | 影响范围 | 根因 |
|--------|---------|------|
| **ImagePullFailed** (g2) | **48 Pods**（default/aiops-e2e/mcp 三个命名空间，node1+node2 两个节点） | **docker.io 镜像仓库网络不可达** — node1 表现 connection reset by peer，node2 表现 i/o timeout，覆盖 registry-1.docker.io 多个 IP:443 |
| **CreateContainerConfigError** (g1) | 1 Pod（aiops-e2e） | **Secret 缺少 Key** — `rc-app-secret` 中没有 `APP_SECRET_TOKEN` |
| **StartError** (g3) | 1 Pod（mcp） | **busybox 镜像中无 curl 命令** — command 配置错误 |
   ✅ [证据链采集] 完成 (57.5s)
   📤 → 下游数据: evidence_items=14/15
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"g2 主异常组: 检查代表 Pod registry-check-node2 (default/ErrImagePull on node2) 的当前状态和事件，验证 i/o timeout 错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod registry-check-node2 -n default","tool_args":{"kind":"pod","name":"registry-check-node2","namespace":"default"},"purpose":"验证 ErrImagePull 的 FailedToPullImage 原因和 i/o timeout 地址","evidence_type":"pod_events_and_status","target_scope":"Pod/default/registry-check-node2","acceptable_tools":["kubectl_describe","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e3","description":"g2 主异常组: 验证集群层面 Events 确认 i/o timeout 是否影响多 Pod","level":"critical","tool":"kubectl_events","command":"kubectl events --all-namespaces --sort-by=lastTimestamp | head -100","tool_args":{},"purpose":"验证集群事件中是否存在多条 i/o timeout/registry 不可达错误，确认网络不可达范围","evidence_type":"cluster_events","target_scope":"cluster","acceptable_tools":["kubectl_events","run_bash_command"],"counts_for_completeness":true},{"id":"e4","description":"g2 主异常组: 验证 node2 上代表 Pod dns-resolve-test 的当前状态和镜像拉取错误","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","tool_args":{"kind":"pod","name":"dns-resolve-test","namespace":"default"},"purpose":"验证 node2 上 ErrImagePull 的 FailedToPullImage 错误是否也是 docker.io i/o timeout","evidence_type":"pod_events_and_status","target_scope":"Pod/default/dns-resolve-test","acceptable_tools":["kubectl_describe","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e5","description":"g2 主异常组: 验证 aiops-e2e 命名空间内的代表 Pod test-dns-1779360358 镜像拉取配置","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"验证 aiops-e2e 命名空间 ImagePullBackOff Pod 的 Events 和镜像","evidence_type":"pod_events_and_status","target_scope":"Pod/aiops-e2e/test-dns-1779360358","acceptable_tools":["kubectl_describe","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e6","description":"g1 非主异常组: 验证 CreateContainerConfigError Pod 的当前状态和 Secret 配置缺失","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"验证 Secret 中缺少 APP_SECRET_TOKEN key 导致的 CreateContainerConfigError","evidence_type":"pod_events_and_status","target_scope":"Pod/aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_describe","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e7","description":"g1 非主异常组: 检查 Secret aiops-e2e/rc-app-secret 是否确实缺少 APP_SECRET_TOKEN","level":"important","tool":"kubectl_get_yaml","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","tool_args":{"kind":"secret","name":"rc-app-secret","namespace":"aiops-e2e","format":"yaml"},"purpose":"验证 Secret 中是否存在 APP_SECRET_TOKEN key","evidence_type":"secret_content","target_scope":"Secret/aiops-e2e/rc-app-secret","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e8","description":"g3 非主异常组: 最小验证 StartError Pod node-debugger-node1-nx8gb 的当前状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"验证 StartError Pod 的当前状态和 Events 确认具体错误原因","evidence_type":"pod_events_and_status","target_scope":"Pod/mcp/node-debugger-node1-nx8gb","acceptable_tools":["kubectl_describe","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e9","description":"reference: 获取 ImagePullFailed runbook 确认诊断上下文","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{},"purpose":"确认 runbook 中的关键检查点","evidence_type":"runbook_reference","target_scope":"reference","acceptable_tools":["fetch_runbook"],"counts_for_completeness":false},{"id":"e10","description":"g2 主异常组: 验证 mcp 命名空间代表 Pod registry-diag-timeout 镜像拉取事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod registry-diag-timeout -n mcp","tool_args":{"kind":"pod","name":"registry-diag-timeout","namespace":"mcp"},"purpose":"验证 mcp 命名空间 ImagePullBackOff Pod 是否也是 docker.io i/o timeout","evidence_type":"pod_events_and_status","target_scope":"Pod/mcp/registry-diag-timeout","acceptable_tools":["kubectl_describe","kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          7m8s (x12 over 9m6s)  kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: e50889f651dff0ebd5a4ed7212a0f9deacd4b503f1ae265a36959b8e7c2ff9c4\n                  cni.projectcalico.org/podIP: 172.16.166.130/32\n                  cni.projectcalico.org/podIPs: 172.16.166.130/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-pbw78:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-r\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\n  Warning  Failed   50m   kubelet  Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:1\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod registry-check-node2 in namespace default, on node node2 (10.2.0.50), status Pending. Container image busybox:1.36.1 fails to pull consistently with i/o timeout errors contacting registry-1.docker.io (multiple IPs: 108.160.169.179, 108.160.165.139, 104.244.46.165, 108.160.166.61, 67.228.102.32, 69.63.176.15, port 443). Container state Waiting (Reason: ErrImagePull), not ready, restart count 0. 7 distinct Failed pull events over 114m, last event at 8s ago repeated 14 times.\nkey_facts: [\"Name: registry-check-node2\", \"Namespace: default\", \"Node: node2 (10.2.0.50)\", \"Status: Pending\", \"Container image: busybox:1.36.1\", \"Container State: Waiting, Reason: ErrImagePull\", \"Ready: False, Restart Count: 0\", \"Pod IP: 172.16.104.41\", \"Start Time: Thu, 21 May 2026 18:35:07 +0000\", \"Events: 7 Warning Failed events over 114m, all 'Failed to pull image' with i/o timeout dialing registry-1.docker.io:443 on various IPs\", \"Latest event: Failed 8s ago (x14 over 114m) Error: ErrImagePull + Failed 8s ago (single) with i/o timeout to 69.63.176.15:443\", \"QoS Class: BestEffort\", \"Node-Selectors: kubernetes.io/hostname=node2\"]\nconflicts: [\"current_summary says '6 Warning Failed' events but raw_preview s\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dns-resolve-test (namespace default) on node node2/10.2.0.50 is Pending. Container dns-resolve-test (image busybox:1.36.1, args: nslookup registry-1.docker.io) is Waiting (Reason: ErrImagePull). Kubelet repeatedly failed to pull image: all attempts resulted in dial tcp i/o timeout to registry-1.docker.io:443 at various IPs (199.59.149.230, 108.160.165.139, 104.244.46.165, 108.160.170.39, 67.228.102.32). Events: 5 Failed pull attempts (51m, 40m, 30m, 20m, 9m45s ago) plus one aggregated error (x8 over 82m). Pulling retries ongoing (x9 over 90m). PodIP 172.16.104.1/32 (Calico). QoS BestEffort.\nkey_facts: [\"Pod: dns-resolve-test, namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Container: dns-resolve-test, Image: busybox:1.36.1\", \"Args: nslookup registry-1.docker.io\", \"Container State: Waiting, Reason: ErrImagePull\", \"Ready: False\", \"PodIP: 172.16.104.1/32 (Calico)\", \"QoS Class: BestEffort\", \"5 Failed image pull events with dial tcp i/o timeout to registry-1.docker.io:443\", \"Aggregated event: Failed x8 over 82m - Error: ErrImagePull\", \"Pulling retries: x9 over 90m\"]\nconflicts: [\"current_summary lists 5 Failed events; raw_preview shows 5 distinct Failed pull events \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n52m                   Warning   Failed   Pod/registry-check-node2   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.169.179:443: i/o timeout\n41m                   Warning   Failed   Pod/registry-check-node2   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.165.139:443: i/o timeout\n31m                   Warning   Failed   Pod/registry-check-node2   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/librar\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/006-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/006-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/006-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Secret\nname: rc-app-secret\nnamespace: aiops-e2e\ntype: Opaque\ndata_keys: EXISTING_SECRET_KEY\nhas_dockerconfigjson: False\ndocker_secret_type_valid: False","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/007-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/007-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/007-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   22m (x119 over 9h)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:55574->54.224.154.163:443: read: connection reset by peer\n  Normal   BackOff  2m16s (x1271 over 9h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  te\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/008-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/008-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/008-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod registry-diag-timeout (namespace mcp) is Pending on node node1/10.2.0.49. Container registry-diag-timeout with image busybox:1.36.1 is in Waiting (ImagePullBackOff) state. Kubelet failed to pull image due to connection reset by peer when connecting to registry-1.docker.io (multiple instances: from 35.169.109.128:443 and 3.233.166.60:443). Pod also has a cmd: timeout 5 wget https://registry.k8s.io/v2/. BackOff occurred 400 time(s) over 3h23m.\nkey_facts: [\"Pod: registry-diag-timeout, Namespace: mcp, Node: node1/10.2.0.49\", \"Status: Pending\", \"State: Waiting (Reason: ImagePullBackOff)\", \"Image: busybox:1.36.1 (from docker.io/library/busybox)\", \"Container ID and Image ID are both empty (image not pulled)\", \"Container command: timeout 5 wget -q -O- https://registry.k8s.io/v2/ 2>&1 || echo FAILED\", \"Pod IP: 172.16.166.162 (Calico network)\", \"Warning Event (57m ago): Failed to pull image - connection reset by peer to 35.169.109.128:443\", \"Warning Event (22m ago, x15 over 133m): Failed to pull image - connection reset by peer to 3.233.166.60:443\", \"Normal BackOff (3m13s ago, x400 over 3h23m): Back-off pulling image busybox:1.36.1\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\", \"QoS Class: BestEffort\", \"No Node-Selectors\"]\nconflicts: [\"current_summary omits Normal Pulling event (53m ago, x26 over 3h34m) that raw_preview includes\"]\nmissing: [\"No info on why connection reset by peer occurs (target registry infrastructure or network issue)\", \"No events from registry.k8s.io probe outcome (cmd not executed because image never pulled)\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/009-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/009-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/009-evidence-kubectl_describe.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=3394 lines=73\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/001-evidence-fetch_runbook.summary.txt\noffset: 0\nreturned_chars: 3187\ntotal_chars: 3187\ncontent:\n<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n## 场景识别\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n## 诊断流程\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: imagePullSecrets 必须在同 namespace，私有仓库 secret 类型应为 kubernetes.io/dockerconfigjson 或 kubernetes.io/dockercfg。\n### Step 4: 按事件错误文本归类\n- `manifest unknown` / `not found`: 镜像仓库中不存在该镜像或 tag。\n- `invalid reference format`: image 字符串格式错误。","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/010-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/010-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/010-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1575 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/004-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1365\ntotal_chars: 1365\ncontent:\nPod registry-check-node2 in namespace default, on node node2 (10.2.0.50), status Pending. Container image busybox:1.36.1 fails to pull consistently with i/o timeout errors contacting registry-1.docker.io (multiple IPs: 108.160.169.179, 108.160.165.139, 104.244.46.165, 108.160.166.61, 67.228.102.32, 69.63.176.15, port 443). Container state Waiting (Reason: ErrImagePull), not ready, restart count 0. 7 distinct Failed pull events over 114m, last event at 8s ago repeated 14 times.\nkey_facts: [\"Name: registry-check-node2\", \"Namespace: default\", \"Node: node2 (10.2.0.50)\", \"Status: Pending\", \"Container image: busybox:1.36.1\", \"Container State: Waiting, Reason: ErrImagePull\", \"Ready: False, Restart Count: 0\", \"Pod IP: 172.16.104.41\", \"Start Time: Thu, 21 May 2026 18:35:07 +0000\", \"Events: 7 Warning Failed events over 114m, all 'Failed to pull image' with i/o timeout dialing registry-1.docker.io:443 on various IPs\", \"Latest event: Failed 8s ago (x14 over 114m) Error: ErrImagePull + Failed 8s ago (single) with i/o timeout to 69.63.176.15:443\", \"QoS Class: BestEffort\", \"Node-Selectors: kubernetes.io/hostname=node2\"]\nconflicts: [\"current_summary says '6 Warning Failed' events but raw_preview shows 7 distinct age entries (52m, 41m, 31m, 21m, 10m, 8s x14, 8s)\"]\nmissing: [\"Container command args (wget test) not in current_summary but present in raw_preview\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/011-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/011-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/011-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1581 lines=45\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/002-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1371\ntotal_chars: 1371\ncontent:\nkubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          7m8s (x12 over 9m6s)  kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: e50889f651dff0ebd5a4ed7212a0f9deacd4b503f1ae265a36959b8e7c2ff9c4\n                  cni.projectcalico.org/podIP: 172.16.166.130/32\n                  cni.projectcalico.org/podIPs: 172.16.166.130/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-pbw78:\n    Type:                    Projected (a volume that contains injected data from multiple sources)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/012-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/012-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/012-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2061 lines=53\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/003-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1851\ntotal_chars: 1851\ncontent:\nkubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\n  Warning  Failed   50m   kubelet  Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/013-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/013-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/013-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1545 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/005-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1335\ntotal_chars: 1335\ncontent:\nPod dns-resolve-test (namespace default) on node node2/10.2.0.50 is Pending. Container dns-resolve-test (image busybox:1.36.1, args: nslookup registry-1.docker.io) is Waiting (Reason: ErrImagePull). Kubelet repeatedly failed to pull image: all attempts resulted in dial tcp i/o timeout to registry-1.docker.io:443 at various IPs (199.59.149.230, 108.160.165.139, 104.244.46.165, 108.160.170.39, 67.228.102.32). Events: 5 Failed pull attempts (51m, 40m, 30m, 20m, 9m45s ago) plus one aggregated error (x8 over 82m). Pulling retries ongoing (x9 over 90m). PodIP 172.16.104.1/32 (Calico). QoS BestEffort.\nkey_facts: [\"Pod: dns-resolve-test, namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Container: dns-resolve-test, Image: busybox:1.36.1\", \"Args: nslookup registry-1.docker.io\", \"Container State: Waiting, Reason: ErrImagePull\", \"Ready: False\", \"PodIP: 172.16.104.1/32 (Calico)\", \"QoS Class: BestEffort\", \"5 Failed image pull events with dial tcp i/o timeout to registry-1.docker.io:443\", \"Aggregated event: Failed x8 over 82m - Error: ErrImagePull\", \"Pulling retries: x9 over 90m\"]\nconflicts: [\"current_summary lists 5 Failed events; raw_preview shows 5 distinct Failed pull events + 1 aggregated (x8) = 6 rows; no factual conflict, just raw_preview is more complete\"]\nmissing: [\"No pulled image ID; no container ID\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/014-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/014-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/014-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2515 lines=48\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/008-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2305\ntotal_chars: 2305\ncontent:\nkubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   22m (x119 over 9h)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:55574->54.224.154.163:443: read: connection reset by peer\n  Normal   BackOff  2m16s (x1271 over 9h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n      nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/015-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/015-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/015-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2804 lines=16\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/006-evidence-kubectl_events.summary.txt\noffset: 0\nreturned_chars: 2596\ntotal_chars: 2596\ncontent:\nkubectl_events 摘要:\n关键诊断行:\n52m                   Warning   Failed   Pod/registry-check-node2   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.169.179:443: i/o timeout\n41m                   Warning   Failed   Pod/registry-check-node2   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.165.139:443: i/o timeout\n31m                   Warning   Failed   Pod/registry-check-node2   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 104.244.46.165:443: i/o timeout\n21m                   Warning   Failed   Pod/registry-check-node2   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.166.61:443: i/o timeout\n10m                   Warning   Failed   Pod/registry-check-node2   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 67.228.102.32:443: i/o timeout\n15s                   Warning   Failed   Pod/registry-check-node2   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.176.15:443: i/o timeout\n15s (x14 over 114m)   Warning   Failed   Pod/registry-check-node2   Error: ErrImagePull\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/016-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/016-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/016-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=390 lines=15\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/547921236d244693/tools/007-evidence-kubectl_get_yaml.summary.txt\noffset: 0\nreturned_chars: 182\ntotal_chars: 182\ncontent:\nkubectl_get_yaml 关键字段摘要:\nkind: Secret\nname: rc-app-secret\nnamespace: aiops-e2e\ntype: Opaque\ndata_keys: EXISTING_SECRET_KEY\nhas_dockerconfigjson: False\ndocker_secret_type_valid: False\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/017-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/017-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/547921236d244693/tools/017-evidence-read_context_archive.summary.txt"}],"llm_analysis":"现在我已采集了全部计划工具的结果。下面给出最终证据结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n#### 异常组 g2 — ImagePullFailed（主异常，48 Pods）\n\n**证据 1 — registry-check-node2（node2, ErrImagePull）**\n- 镜像：`busybox:1.36.1`（docker.io/library/busybox）\n- 事件：连续 7 次 `Failed to pull image`，错误均为 **`dial tcp registry-1.docker.io:443: i/o timeout`**（目标 IP 包括 108.160.169.179、108.160.165.139、104.244.46.165、67.228.102.32、69.63.176.15 等）\n- 节点：node2（10.2.0.50），PodIP：172.16.104.41（Calico）\n\n**证据 2 — dns-resolve-test（node2, ErrImagePull）**\n- 镜像：`busybox:1.36.1`\n- 事件：同样 **`dial tcp registry-1.docker.io:443: i/o timeout`**（IPs：199.59.149.230, 108.160.165.139, 104.244.46.165 等）\n- 节点：node2（10.2.0.50），PodIP：172.16.104.1\n\n**证据 3 — test-dns-1779360358（node1, ImagePullBackOff）**\n- 镜像：`busybox:1.36.1`\n- 事件：**`connection reset by peer`** 到 `54.224.154.163:443`（registry-1.docker.io），累计 119 次失败，已在 node1 上重试 1271 次\n- 节点：node1（10.2.0.49）\n\n**证据 4 — registry-diag-timeout（node1, ImagePullBackOff）**\n- 镜像：`busybox:1.36.1`\n- 事件：**`connection reset by peer`** 到 `35.169.109.128:443` 和 `3.233.166.60:443`，重试 400 次\n- 节点：node1（10.2.0.49）\n\n**→ 结论：镜像仓库 docker.io 从 node1 和 node2 均不可达。node2 表现为 i/o timeout（TCP 完全不通），node1 表现为 connection reset by peer（TCP 建连后被对端重置）。registry-1.docker.io:443 涉及十余个不同 IP 均不可达，排除 DNS 单点故障，确认是**集群到外网 docker.io 的网络出口/防火墙问题**。\n\n---\n\n#### 异常组 g1 — CreateContainerConfigError（1 Pod）\n\n**证据 5 — rc-config-secret-key-missing（aiops-e2e, CreateContainerConfigError）**\n- 事件：`Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`（重复 12 次）\n- Secret YAML 验证：`rc-app-secret` 中仅有 `EXISTING_SECRET_KEY`，**缺少 `APP_SECRET_TOKEN` key**\n- 镜像 `busybox:1.36` 本身正常（因 ConfigError 未到拉取阶段）\n\n**→ 结论：Pod 引用了 Secret 中不存在的 key `APP_SECRET_TOKEN`，属于 Pod 配置错误。**\n\n---\n\n#### 异常组 g3 — StartError（1 Pod）\n\n**证据 6 — node-debugger-node1-nx8gb（mcp, StartError）**\n- 状态：Failed（StartError），Exit Code 128\n- 错误消息：**`exec: \"curl\": executable file not found in $PATH`**\n- 镜像 `busybox:1.36` 中不包含 `curl` 可执行文件，但 Pod command 指定了 `curl -s -o /dev/null -w %{http_code} --connect-timeout 5`\n\n**→ 结论：Pod command 使用了 busybox 镜像中不存在的 curl 命令，与网络无关，属于应用配置错误。**\n\n---\n\n### ⚠️ 冲突/负向证据\n- 未发现任何 Pod 存在 Terminating 或 Pending（Unschedulable）等并发异常\n- kube-system 和 admin 命名空间均正常运行，无节点异常\n\n### ❌ 未采集证据\n- 未做 Prometheus 注册表连通性查询（因已从 Events 获取充分的 i/o timeout 证据，不需重复验证）\n\n---\n\n## 总体诊断结论\n\n| 异常组 | 影响范围 | 根因 |\n|--------|---------|------|\n| **ImagePullFailed** (g2) | **48 Pods**（default/aiops-e2e/mcp 三个命名空间，node1+node2 两个节点） | **docker.io 镜像仓库网络不可达** — node1 表现 connection reset by peer，node2 表现 i/o timeout，覆盖 registry-1.docker.io 多个 IP:443 |\n| **CreateContainerConfigError** (g1) | 1 Pod（aiops-e2e） | **Secret 缺少 Key** — `rc-app-secret` 中没有 `APP_SECRET_TOKEN` |\n| **StartError** (g3) | 1 Pod（mcp） | **busybox 镜像中无 curl 命令** — command 配置错误 |","collection_summary":"计划 8 项，实际采集 7 项，未采集 1 项，完整度 88%；其中真实环境证据 13/14 项，完整度 93%；实际执行工具 14 个，匹配计划 8 个，未规划证据 6 个","plan_total":8,"plan_collected":7,"plan_completeness":0.875,"environment_evidence_total":14,"environment_evidence_collected":13,"environment_evidence_completeness":0.9285714285714286,"executed_tool_count":14,"matched_tool_count":8,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"g2 主异常组: 检查代表 Pod registry-check-node2 (default/ErrImagePull on node2) 的当前状态和事件，验证 i/o timeout 错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod registry-check-node2 -n default","purpose":"验证 ErrImagePull 的 FailedToPullImage 原因和 i/o timeout 地址","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"g2 主异常组: 验证集群层面 Events 确认 i/o timeout 是否影响多 Pod","level":"critical","tool":"kubectl_events","command":"kubectl events --all-namespaces --sort-by=lastTimestamp | head -100","purpose":"验证集群事件中是否存在多条 i/o timeout/registry 不可达错误，确认网络不可达范围","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"g2 主异常组: 验证 node2 上代表 Pod dns-resolve-test 的当前状态和镜像拉取错误","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","purpose":"验证 node2 上 ErrImagePull 的 FailedToPullImage 错误是否也是 docker.io i/o timeout","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"g2 主异常组: 验证 aiops-e2e 命名空间内的代表 Pod test-dns-1779360358 镜像拉取配置","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"验证 aiops-e2e 命名空间 ImagePullBackOff Pod 的 Events 和镜像","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"g1 非主异常组: 验证 CreateContainerConfigError Pod 的当前状态和 Secret 配置缺失","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"验证 Secret 中缺少 APP_SECRET_TOKEN key 导致的 CreateContainerConfigError","collected":false,"source":"planned","outcome":"unknown"},{"id":"e7","description":"g1 非主异常组: 检查 Secret aiops-e2e/rc-app-secret 是否确实缺少 APP_SECRET_TOKEN","level":"important","tool":"kubectl_get_yaml","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","purpose":"验证 Secret 中是否存在 APP_SECRET_TOKEN key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e8","description":"g3 非主异常组: 最小验证 StartError Pod node-debugger-node1-nx8gb 的当前状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"验证 StartError Pod 的当前状态和 Events 确认具体错误原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e9","description":"reference: 获取 ImagePullFailed runbook 确认诊断上下文","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"确认 runbook 中的关键检查点","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e10","description":"g2 主异常组: 验证 mcp 命名空间代表 Pod registry-diag-timeout 镜像拉取事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod registry-diag-timeout -n mcp","purpose":"验证 mcp 命名空间 ImagePullBackOff Pod 是否也是 docker.io i/o timeout","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e6(g1 非主异常组: 验证 CreateContainerConfigError Pod 的当前状态和 Secret 配置缺失): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/8 项, 完整度: 93%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | g2 主异常组: 检查代表 Pod registry-check-node2 (defau... | `kubectl describe pod registry-check-node2 -n default` |
   | e3 | critical | ✅ | kubectl_events | g2 主异常组: 验证集群层面 Events 确认 i/o timeout 是否影响多 Pod | `kubectl events --all-namespaces --sort-by=lastTimestamp | head -100` |
   | e4 | important | ✅ | kubectl_describe | g2 主异常组: 验证 node2 上代表 Pod dns-resolve-test 的当... | `kubectl describe pod dns-resolve-test -n default` |
   | e5 | important | ✅ | kubectl_describe | g2 主异常组: 验证 aiops-e2e 命名空间内的代表 Pod test-dns-1... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | e6 | important | ❌ | kubectl_describe | g1 非主异常组: 验证 CreateContainerConfigError Pod 的... | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | e7 | important | ✅ | kubectl_get_yaml | g1 非主异常组: 检查 Secret aiops-e2e/rc-app-secret 是... | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` |
   | e8 | important | ✅ | kubectl_describe | g3 非主异常组: 最小验证 StartError Pod node-debugger-n... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | e9 | reference | ✅ | fetch_runbook | reference: 获取 ImagePullFailed runbook 确认诊断上下文 | `fetch_runbook pod-imagepull-failed.md` |
   | e10 | important | ✅ | kubectl_describe | g2 主异常组: 验证 mcp 命名空间代表 Pod registry-diag-time... | `kubectl describe pod registry-diag-timeout -n mcp` |

   ⚠️ 未采集原因:
   - e6(g1 非主异常组: 验证 CreateContainerConfigError Pod 的当前状态和 Secret 配置缺失): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (23.5s)
   📤 → 下游数据: root_cause=主根因（影响48个Pod，L3级别）：集群节点node1(10.2.0.49)和node2(10.2.0.50)到公网镜像仓库docker.io(registry-1.docker.io:443)的网络出口不可达。证据显示：node2上Pod registry-check-node2连续7次Failed事件，均报告'dial tcp 108.160.169.179:443: i/o timeout'等（多个不同IP均超时）；node1上Pod test-dns-1779360358报告119次'connection reset by peer'到54.224.154.163:443；node1上Pod registry-diag-timeout报告400次重试后connection reset by peer。跨命名空间(aiops-e2e/default/mcp)和跨节点(node1/node2)的48个Pod全部因network不可达失败，涉及镜像包括busybox:1.36.1、alpine:3.18、curlimages/curl:7.88.1/8.12.1、registry.
... 截断，原始 876 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点(node1和node2)到公网镜像仓库docker.io(registry-1.docker.io:443)的网络出口不可达，导致所有依赖从docker.io拉取镜像的Pod持续失败", "propagation": "1) 节点kubelet尝试从docker.io拉取镜像(busybox:1.36.1, alpine:3.18, curlimages/curl等) → 2) TCP连接registry-1.docker.io:443超时或被对端重置 → 3) 镜像拉取失败，kubelet重试并生成ErrImagePull/ImagePullBackOff事件 → 4) Pod无法进入Running状态，持续Pending", "direct_cause": "node1和node2到registry-1.docker.io:443的TCP连接失败（node2: i/o timeout; node1: connection reset by peer），涉及十余个不同IP地址均不可达", "manifestation": "48个Pod分布在aiops-e2e、default、mcp命名空间，状态为ImagePullBackOff(26)或ErrImagePull(22)，kubelet持续重试但始终无法拉取镜像"}
   rca_analysis={"phenomenon": "集群存在三类异常Pod，总计约50个异常Pod分布在aiops-e2e、default、mcp三个命名空间和node1、node2两个节点上：1) 48个Pod处于ImagePullBackOff(26)或ErrImagePull(22)状态，镜像拉取失败；2) 1个Pod(aiops-e2e/rc-config-secret-key-missing)处于CreateContainerConfigError状态；3) 1个Pod(mcp/node-debugger-node1-nx8gb)处于StartError状态。kube-system和admin命名空间所有Pod正常运行，节点本身健康。", "evidence_inventory": [{"id": "e5", "source": "kubectl_describe (registry-check-node2)", "content": "Pod default/registry-check-node2 on node2: ErrImagePull, 7次Failed事件，镜像busybox:1.36.1，错误均为dial tcp registry-1.docker.io:443: i/o timeout到多个IP", "reliability": "高"}, {"id": "e10", "source": "kubectl_describe (test-dns-1779360358)", "content": "Pod aiops-e2e/test-dns-1779360358 on node1: ImagePullBackOff, 119次Failed事件，connection reset by peer到registry-1.docker.io:443(54.224.154.163)", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe (dns-resolve-test)", "content": "Pod default/dns-resolve-test on node2: ErrImagePull, dial tcp i/o timeout到registry-1.docker.io:443多个IP", "reliability": "高"}, {"id": "e3", "source": "kubectl_events (registry-check-node2)", "content": "集群Events确认：registry-check-node2连续7次Failed pull事件，均为i/o timeout到docker.io registry", "reliability": "高"}, {"id": "layer_4", "source": "kubectl_events (上游)", "content": "多Pod统一事件：registry-check-node2、dns-resolve-test等多Pod均报告i/o timeout到registry-1.docker.io:443", "reliability": "高"}, {"id": "layer_5", "source": "kubectl_events (rc-config-secret-key-missing)", "content": "Pod aiops-e2e/rc-config-secret-key-missing事件：Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret（重复12次）", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_yaml (Secret)", "content": "Secret aiops-e2e/rc-app-secret类型Opaque，data_keys仅有EXISTING_SECRET_KEY，缺少APP_SECRET_TOKEN", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe (node-debugger-node1-nx8gb)", "content": "Pod mcp/node-debugger-node1-nx8gb状态Failed(StartError), Exit Code 128, 错误: exec: 'curl' not found in $PATH, 镜像busybox:1.36不含curl", "reliability": "高"}, {"id": "e9", "source": "fetch_runbook", "content": "ImagePullFailed runbook: i/o timeout表示网络不可达，匹配当前场景", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e5", "raw_data": "Pod registry-check-node2: 7次Failed pull，错误均为'dial tcp 108.160.169.179:443: i/o timeout'等，镜像busybox:1.36.1", "interpretation": "node2到docker.io registry-1.docker.io:443 TCP连接超时，所有尝试IP均不可达，确认网络层不通"}, {"evidence_id": "e10", "raw_data": "Pod test-dns-1779360358: 119次Failed，'connection reset by peer'到54.224.154.163:443", "interpretation": "node1到docker.io registry TCP建连后被对端重置，与node2的timeout表现不同但本质相同——均无法成功拉取镜像"}, {"evidence_id": "e8", "raw_data": "Pod dns-resolve-test: 5次Failed pull，dial tcp i/o timeout到registry-1.docker.io多个IP", "interpretation": "node2上第二个独立Pod也出现完全相同的i/o timeout，排除单Pod配置问题，确认是节点级别的网络问题"}, {"evidence_id": "e3", "raw_data": "registry-check-node2 Events: 52m/41m/31m/21m/10m ago均为i/o timeout", "interpretation": "持续超过1小时的镜像拉取失败，无任何成功记录，非瞬时故障"}, {"evidence_id": "layer_4", "raw_data": "多Pod统一事件：registry-check-node2、dns-resolve-test、registry-diag-timeout等均报告网络不可达", "interpretation": "跨命名空间(aiops-e2e、default、mcp)、跨节点(node1、node2)的48个Pod全部因网络不可达失败，排除个别Pod配置问题"}, {"evidence_id": "layer_5", "raw_data": "Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret (x12)", "interpretation": "CreateContainerConfigError的明确根因：Pod引用了Secret中不存在的key"}, {"evidence_id": "e7", "raw_data": "Secret rc-app-secret data_keys: [EXISTING_SECRET_KEY]，无APP_SECRET_TOKEN", "interpretation": "直接验证了Secret中确实缺少APP_SECRET_TOKEN，与Pod事件完全吻合"}, {"evidence_id": "e4", "raw_data": "StartError: exec 'curl' not found in $PATH, 镜像busybox:1.36", "interpretation": "StartError根因：Pod command使用curl但基础镜像busybox:1.36不含curl二进制，容器启动失败"}], "causal_chain": {"root_cause": "集群节点(node1和node2)到公网镜像仓库docker.io(registry-1.docker.io:443)的网络出口不可达，导致所有依赖从docker.io拉取镜像的Pod持续失败", "propagation": "1) 节点kubelet尝试从docker.io拉取镜像(busybox:1.36.1, alpine:3.18, curlimages/curl等) → 2) TCP连接registry-1.docker.io:443超时或被对端重置 → 3) 镜像拉取失败，kubelet重试并生成ErrImagePull/ImagePullBackOff事件 → 4) Pod无法进入Running状态，持续Pending", "direct_cause": "node1和node2到registry-1.docker.io:443的TCP连接失败（node2: i/o timeout; node1: connection reset by peer），涉及十余个不同IP地址均不可达", "manifestation": "48个Pod分布在aiops-e2e、default、mcp命名空间，状态为ImagePullBackOff(26)或ErrImagePull(22)，kubelet持续重试但始终无法拉取镜像"}, "root_cause": "主根因（影响48个Pod，L3级别）：集群节点node1(10.2.0.49)和node2(10.2.0.50)到公网镜像仓库docker.io(registry-1.docker.io:443)的网络出口不可达。证据显示：node2上Pod registry-check-node2连续7次Failed事件，均报告'dial tcp 108.160.169.179:443: i/o timeout'等（多个不同IP均超时）；node1上Pod test-dns-1779360358报告119次'connection reset by peer'到54.224.154.163:443；node1上Pod registry-diag-timeout报告400次重试后connection reset by peer。跨命名空间(aiops-e2e/default/mcp)和跨节点(node1/node2)的48个Pod全部因network不可达失败，涉及镜像包括busybox:1.36.1、alpine:3.18、curlimages/curl:7.88.1/8.12.1、registry.\n... 截断，原始 876 字符", "root_cause_summary": "主根因（影响48个Pod，L3级别）：集群节点node1(10.2.0.49)和node2(10.2.0.50)到公网镜像仓库docker.io(registry-1.docker.io:443)的网络出口不可达。证据显示：node2上Pod registry-check-node2连续7次Failed事件，均报告'dial tcp 108.160.169.179:443: i/o timeout'等（多个不同IP均超时）；node1上Pod test-dns-1779360358报告119次'connection reset by peer'到54.224.154.163:443；node1上Pod registry-diag-timeout报告400次重试后connection reset by peer。跨命名空间(aiops-e2e/default/mcp)和跨节点(node1/node2)的48个Pod全部因network不可达失败，涉及镜像包括busybox:1.36.1、alpine:3.18、curlimages/curl:7.88.1/8.12.1、registry.\n... 截断，原始 876 字符", "confidence": 0.95, "confidence_reason": "有直接证据：kubectl_describe和kubectl_events明确显示i/o timeout和connection reset by peer错误，跨多Pod、跨节点、跨命名空间一致；Secret YAML直接验证key缺失；StartError的错误消息直接指明原因。证据充分、因果链清晰。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像名或tag不存在（如busybox:1.36.1不存在）", "probability": "low", "reason": "Events中错误是'i/o timeout'而非'manifest unknown/not found'，且连接建立前的TCP超时说明问题在网络层而非镜像层"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "docker.io公共镜像不需要认证；Events中无'unauthorized/no basic auth'错误；节点间一致的连接超时现象不符合认证失败特征"}, {"cause": "DNS解析失败导致registry不可达", "probability": "low", "reason": "Events中显示已成功解析出多个IP地址(108.160.169.179, 104.244.46.165等），但TCP建连失败；DNS解析本身正常"}, {"cause": "节点自身网络完全中断", "probability": "low", "reason": "kube-system和admin命名空间的系统组件均Running正常，说明节点网络未完全中断，仅对外网docker.io出口受限"}, {"cause": "StartError Pod的镜像拉取问题", "probability": "low", "reason": "该Pod(node-debugger-node1-nx8gb)镜像busybox:1.36实际已成功拉取(Image ID存在)，错误是容器启动时command找不到curl，属于应用配置问题而非拉取问题"}], "limitations": "未采集node级别的网络排查工具结果（如node上curl registry-1.docker.io、ping测试、traceroute、iptables规则检查、CNI/Calico网络策略检查等），因此无法进一步定位网络出口不可达的具体原因（防火墙规则、代理配置、NAT问题或上游网络路由问题）。StartError Pod的镜像busybox:1.36已成功拉取（Image ID存在），但不确定是本地缓存还是从远程拉取成功——如果是从远程拉取，说明node1偶尔能通但极不稳定。CreateContainerConfigError的Secret缺少key问题已完全定位，无需额外信息。", "llm_raw_analysis": "## 证据清点\n已采集13条有效证据，覆盖全部3个异常组(g1/g2/g3)：\n- g2(主异常组-48 Pods): e3/e5/e8/e9/e10 + layer_1~layer_4 共8条证据\n- g1(非主异常组-1 Pod): e7 + layer_5/layer_6 共3条证据\n- g3(非主异常组-1 Pod): e4 共1条证据\n- runbook参考: e9\n\n## 逐条分析\n核心证据链清晰：所有g2异常Pod的Events均指向同一种错误模式——TCP连接registry-1.docker.io:443失败。node2表现为i/o timeout（完全无响应），node1表现为connection reset by peer（建连后被重置）。涉及10余个不同IP地址均不可达，排除DNS解析故障（能解析到IP但连不上）和单点故障。\n\ng1(rc-config-secret-key-missing)有双重验证：Pod Events和Secret YAML均确认APP_SECRET_TOKEN key缺失。\n\ng3(node-debugger-node1-nx8gb)的错\n... 截断，原始 744 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 主根因（影响48个Pod，L3级别）：集群节点node1(10.2.0.49)和node2(10.2.0.50)到公网镜像仓库docker.io(registry-1.docker.io:443)的网络出口不可达。证据显示：node2上Pod registry-check-node2连续7次Fail...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点(node1和node2)到公网镜像仓库docker.io(registry-1.docker.io:443)的网络出口不可达，导致所有依赖从docker.io拉取镜像的Pod持续失败
     传导机制: 1) 节点kubelet尝试从docker.io拉取镜像(busybox:1.36.1, alpine:3.18, curlimages/curl等) → 2) TCP连接registry-1.docker.io:443超时或被对端重置 → 3) 镜像拉取失败，kubelet重试并生成ErrImagePull/ImagePullBackOff事件 → 4) Pod无法进入Running状态，持续Pending
     最终表现: 48个Pod分布在aiops-e2e、default、mcp命名空间，状态为ImagePullBackOff(26)或ErrImagePull(22)，kubelet持续重试但始终无法拉取镜像


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (28.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8196 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 27.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将基于您提供的全面分析结果，为您生成一份详尽、可直接用于问题处理的诊断报告。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff (26个), ErrImagePull (22个), **CreateContainerConfigError (1个)** |
| **兼容归因层** | L3 & L4 |
| **问题分类** | **主问题:** ImagePullFailed (镜像拉取失败) / **次要问题:** Secret配置错误 |
| **置信度** | **高 (95%)** |
| **证据完整度** | 7/8 (88%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| **集群状态** | 发现 **49** 个异常 Pod 处于 `Pending` 状态 |
| **主要问题组** | **48** 个 Pod (覆盖 `aiops-e2e`, `default`, `mcp` 命名空间) |
| **次要问题组** | **1** 个 Pod (`aiops-e2e/rc-config-secret-key-missing`) |
| **受影响节点** | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| **核心错误信息** | `i/o timeout` (拉取镜像超时), `couldn't find key APP_SECRET_TOKEN in Secret` (密钥缺失) |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod registry-check-node2` (default) | `Reason: ErrImagePull`, `Events: Failed to pull image "busybox:1.36.1": ... dial tcp 108.160.169.179:443: i/o timeout` | node2 上 Pod 拉取 `docker.io` 镜像时发生 TCP 连接超时 |
| 2 | Pod 状态与事件 | `kubectl describe pod registry-diag-timeout` (mcp) | `Reason: ImagePullBackOff`, `Events: Failed to pull image ... connection reset by peer to 35.169.109.128:443` | node1 上 Pod 拉取 `docker.io` 镜像时连接被对端重置 |
| 3 | 集群级事件 | `kubectl_events` | `Pod/registry-check-node2`, `Pod/dns-resolve-test`, `Pod/test-dns-1779360358` 均报告 `i/o timeout` | 镜像拉取失败不是个别 Pod 问题，而是跨命名空间和节点的集群级网络故障 |
| 4 | 跨节点验证 | `kubectl describe pod test-dns-1779360358` (aiops-e2e) | `Warning Failed 22m (x119 over 9h) ... Failed to pull image` | 故障在 `node1` 上也存在，且持续了 9 小时以上，进一步确认是节点网络问题而非单点故障 |
| 5 | Pod 枚举 | `kubernetes_tabular_query` | 返回 48 个异常 Pod，`ImagePullBackOff=26`, `ErrImagePull=22` | 精确确认受影响 Pod 规模为 48 个 |
| 6 | Secret 配置检查 | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` | `data_keys: [EXISTING_SECRET_KEY]` (没有 `APP_SECRET_TOKEN`) | 确认 Secret 中确实缺少指定密钥 |
| 7 | 配置错误 Pod 事件 | `kubectl describe pod rc-config-secret-key-missing` | `Events: Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | 事件直接指明了原因，与 Secret 检查结果吻合 |

### 证据关联分析

- **证据 #1 + #2 + #3 + #4 印证**：多个 Pod 从 `node1` 和 `node2` 拉取 `docker.io` (registry-1.docker.io:443) 镜像均失败，且错误模式为网络层错误 (`i/o timeout`, `connection reset`)，表明这是**影响整个集群的** `L3` **网络出口问题**。
- **证据 #6 + #7 印证**：Pod `rc-config-secret-key-missing` 的 `CreateContainerConfigError` 状态与 Secret 对象的实际内容 (`data_keys`) 完美匹配，这是**独立的 `L4` 配置错误**。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 节点级别的网络工具执行结果 (如: `node1` 上 `curl registry-1.docker.io`) | critical | 无法进一步定位网络不可达的具体原因（如防火墙规则、代理配置、NAT或路由问题） |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (L3 - 48 个 Pod)                                                   │
│ 集群节点 (node1, node2) 到公网镜像仓库 docker.io (registry-1.docker.io:443) │
│ 的网络出口不可达 (表现为 i/o timeout 和 connection reset)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ 节点 kubelet 尝试从 docker.io 拉取镜像 → TCP 连接 3 次握手在公网出口失败     │
│ (超时或被对端重置) → 无法拉取镜像                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (L3)                                                               │
│ kubelet 无法从 docker.io 拉取镜像，导致所有依赖外网镜像的 Pod 进入           │
│ ErrImagePull / ImagePullBackOff 状态                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (L3)                                                           │
│ 48 个分布在 aiops-e2e, default, mcp 命名空间的 Pod 均处于 Pending 状态，    │
│ kubelet 持续重试但始终失败                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│ 次要问题 - 根本原因 (L4 - 1 个 Pod)                                         │
│ Secret `rc-app-secret` 中缺少 `APP_SECRET_TOKEN` 字段                       │
└─────────────────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (L4)                                                               │
│ Pod 启动时引用不存在的 Secret 键，导致容器配置失败                           │
└─────────────────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (L4)                                                           │
│ Pod rc-config-secret-key-missing 处于 CreateContainerConfigError 状态       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：集群存在**两个独立问题**：

1.  **[主要] L3 - 镜像仓库网络不可达 (置信度: 95%)**：
    *   **依据**：证据 #1, #2, #3, #4。超过 48 个 Pod 在节点 `node1` 和 `node2` 上拉取 `docker.io` 镜像时，均发生 TCP 连接错误 (`i/o timeout`, `connection reset`)。这排除了个别 Pod 或单节点问题，指向集群出口网络故障。
    *   **影响**：所有依赖公共镜像仓库 (如 `docker.io`, `registry.k8s.io`) 的服务均无法启动。

2.  **[次要] L4 - Secret 配置错误 (置信度: 99%)**：
    *   **依据**：证据 #6 和 #7。Pod 事件与 Secret 对象的实际状态完全吻合，原因明确。
    *   **影响**：仅影响 `rc-config-secret-key-missing` 这一 Pod。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 解决 L3 网络出口问题 (主问题)**

*   **场景 A：集群需要访问公网**
    您需要与集群的**网络/基础设施管理员**协作，检查节点到 `registry-1.docker.io:443` 的网络路径：
    1.  **登录节点** `node1` 和 `node2`。
    2.  **测试连通性**：通过 `curl -v https://registry-1.docker.io/v2/` 或 `telnet registry-1.docker.io 443` 验证是否可以连接到公网镜像仓库。
    3.  **排查原因**：常见的网络出口问题包括：
        *   节点所在子网缺少 NAT 网关或代理。
        *   出口防火墙规则拦截了对 `docker.io` 的访问。
        *   集群部署在私有网络 (如 AWS VPC, GCP VPC) 内且未配置公网网关。

*   **场景 B：集群应使用私有/内部镜像仓库**
    如果需要从本地或其他内网仓库拉取，您需要修改 Deployment 的镜像地址。

    **示例：将 `registry-check-node2` 的镜像修改为内部仓库地址**
    ```bash
    # 首先，查看 Pod 属于哪个控制器
    kubectl describe pod registry-check-node2 -n default | grep -i "controlled by"
    
    # 假设它属于一个名为 network-check 的 deployment
    kubectl set image deployment/network-check registry-check-node2=my-internal-registry:5000/busybox:1.36.1 -n default
    ```

**2. [修复] 解决 L4 Secret 配置错误 (次要问题)**

```bash
# 1. 生成缺失的密钥值 (这里用 'your-new-secret-value' 代替)
# echo -n 'your-new-secret-value' | base64

# 2. 编辑 Secret 添加缺失的键
kubectl patch secret rc-app-secret -n aiops-e2e -p '{"data":{"APP_SECRET_TOKEN":"<base64-encoded-value>"}}'

# 3. (可选但更推荐) 如果使用 YAML 管理，直接编辑原 YAML 文件并重新应用
# kubectl delete pod rc-config-secret-key-missing -n aiops-e2e
```

### 后续优化
1.  **监控**：配置对 `Node` 网络连通性的监控，例如部署 DaemonSet 定期检查公网/内部仓库地址的可达性 (利用现有的 `dns-resolve-test` 等 Pod 改造即可)。
2.  **配置管理**：确保 `Secret` 的创建和更新纳入 CI/CD 或配置管理流程，避免手动创建遗漏字段。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 验证网络已恢复 | 在节点执行: `curl -v https://registry-1.docker.io/v2/` | TCP 连接成功，返回 HTTP/1.1 401 Unauthorized 或类似响应 (表示网络可达) |
| 2. 确认主问题修复 | `kubectl get pods -n default -A | grep -E 'ImagePullBackOff\|ErrImage'` | 不再有新的 ImagePullBackOff/ErrImagePull Pod 出现，旧的 Pod 会逐步转为 Running |
| 3. 确认 Secret 修复 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | 事件中不再有 Secret 找不的的错误，Pod 会尝试重新启动 |
| 4. 最终状态检查 | `kubectl get pods --all-namespaces` (过滤出 Running 以外的状态) | 只应看到 `Completed` (Job) 的 Pod，不应有 `Pending`, `CrashLoopBackOff`, `Error` |

---

## ⚠️ 注意事项
-   修复 L3 问题前，任何需要从 `docker.io` 拉取镜像的新 Pod 都无法启动。
-   修复 Secret 问题后，对应的 Pod `rc-config-secret-key-missing` 需要被删除 (`kubectl delete pod`) 或由控制器自动重新拉起来才能生效。
-   关于 `node-debugger-node1-nx8gb` (StartError)，该 Pod 镜像 `busybox:1.36` 似乎已被拉取成功，其错误 (`OCI runtime create failed`) 是独立的容器运行时问题，与主问题无关。鉴于其 `Exit Code: 128` 且状态为 `Failed`，可手动删除。
    ```bash
    kubectl delete pod node-debugger-node1-nx8gb -n mcp
    ```

---

## 📊 性能统计

├─ 总耗时: 2.5m
├─ 问题定位: 37.7s (26%) ✅
├─ 证据链采集: 57.5s (39%) ✅
├─ 根因分析: 23.5s (16%) ✅
├─ 汇总总结: 28.5s (19%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 26 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed
- **工具调用**: 26 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
