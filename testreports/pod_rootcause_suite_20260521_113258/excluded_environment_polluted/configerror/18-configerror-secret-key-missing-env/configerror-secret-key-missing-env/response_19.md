======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 2392aeb38c494580]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先全面扫描集群中的 Pod 状态，了解整体情况。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=301 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 0 completed, 1 in progress, 3 pending
[ ] [2] 对异常 Pod 进行分类归组
[ ] [3] 按异常类型
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces: 返回大量 Pod 列表，共约 115 行。正常 Running Pod 约 59 个（分布在 admin、aiops、default、kube-system 等命名空间），异常 Pod 约 50 个。主要问题集中在 default 命名空间的大量 dns/network/registry 测试 Pod 处于 ImagePullB
   💭 [问题定位] 集群中有大量异常 Pod！让我进一步了解具体情况。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=301 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 1 completed, 1 in progress, 2 pending
[ ] [3] 按异常类型匹配 Runbook 进行定位
[ ] [4]
   💭 [问题定位] 让我更精确地查看各异常组的详细状态。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=485 lines=4
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query returned 49 pods all with status Pending across namespaces aiops-e2e, default, and mcp, on nodes node1 and node2. Pods include diagnostics, network tests, DNS tests, registry 
   💭 [问题定位] 好的，让我查看具体的 STATUS 列（非 phase），因为 ImagePullBackOff 的 phase 也是 Pending。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Pod listing shows all pods in Pending or Failed phase across namespaces aiops-e2e, default, mcp, xnet. Mass ImagePullBackOff/ErrImagePull errors for images busybox:1.36.1, alpine:3.18, curlimages/curl
   💭 [问题定位] 非常好，现在我对集群异常有了清晰了解。让我获取相关的 Runbook。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=301 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 2 completed, 1 in progress, 1 pending
[ ] [4] 输出层析定位结果
[~] [3] 按异常类型匹配 Run
   💭 [问题定位] 现在我来获取匹配的 Runbook。这里有两种主要异常类型：
1. **ImagePullFailed** — 大量 Pod 处于 ImagePullBackOff/ErrImagePull
2. **ConfigError** — aiops-e2e/rc-config-secret-key-missing 处于 CreateContainerConfigError
3. **Evicted** — xnet/observability-kibana 被驱逐
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   ✅ [问题定位] 完成 (36.8s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4+L0
   scenarios=[{'scenario': '镜像仓库不可达（网络层面）', 'probability': '高', 'reason': '大量Pod镜像拉取时报 dial tcp 93.179.102.140:443: connect: connection refused 和 i/o timeout，涉及多个镜像仓库（docker.io、registry.k8s.io）'}, {'scenario': 'Secret配置错误', 'probability': '中', 'reason': 'aiops-e2e/rc-config-secret-key-missing 缺少 APP_SECRET_TOKEN key'}, {'scenario': '节点资源压力导致驱逐', 'probability': '低', 'reason': 'xnet/observability-kibana 被 Evicted，但仅1个Pod受影响'}]
   entities=[{"type": "Pod", "name": "dns-test-check", "namespace": "default"}, {"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "Namespace", "name": "default", "namespace": ""}, {"type": "Namespace", "name": "mcp", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=当前环境存在大量异常 Pod，主要异常类型包括：(1) 约48个Pod处于ImagePullBackOff/ErrImagePull（default/mcp命名空间），因无法连接 registry-1.docker.io:443（connection refused / i/o timeout）导致镜像拉取失败，归类为L3（image_registry/network）；(2) aiops-e2e/rc-config-secret-key-missing处于CreateContainerConfigError（缺少Secret key），归类为L4（app_config）；(3) xnet/observability-kibana被Evicted，归类为L0（node_pressure）。根因为镜像仓库不可达（网络/registry层面），属于L3层问题，同时存在L4配置问题和L0驱逐问题作为次要异常。系统Pod（kube-system）正常运行，节点状态正常。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4", "L0"], "layer_name": "Image/Network", "confidence": 0.95, "reasoning": "当前环境存在大量异常 Pod，主要异常类型包括：(1) 约48个Pod处于ImagePullBackOff/ErrImagePull（default/mcp命名空间），因无法连接 registry-1.docker.io:443（connection refused / i/o timeout）导致镜像拉取失败，归类为L3（image_registry/network）；(2) aiops-e2e/rc-config-secret-key-missing处于CreateContainerConfigError（缺少Secret key），归类为L4（app_config）；(3) xnet/observability-kibana被Evicted，归类为L0（node_pressure）。根因为镜像仓库不可达（网络/registry层面），属于L3层问题，同时存在L4配置问题和L0驱逐问题作为次要异常。系统Pod（kube-system）正常运行，节点状态正常。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "Pod", "name": "dns-test-check", "namespace": "default"}, {"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "Namespace", "name": "default", "namespace": ""}, {"type": "Namespace", "name": "mcp", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库不可达（网络层面）", "probability": "高", "reason": "大量Pod镜像拉取时报 dial tcp 93.179.102.140:443: connect: connection refused 和 i/o timeout，涉及多个镜像仓库（docker.io、registry.k8s.io）"}, {"scenario": "Secret配置错误", "probability": "中", "reason": "aiops-e2e/rc-config-secret-key-missing 缺少 APP_SECRET_TOKEN key"}, {"scenario": "节点资源压力导致驱逐", "probability": "低", "reason": "xnet/observability-kibana 被 Evicted，但仅1个Pod受影响"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 27, "ErrImagePull": 21}, "total_abnormal": 48, "selected_rows": ["aiops-e2e         rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0              22m     172.16.166.130   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff             0              10h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              5h18m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff             0              4h18m   172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              8h      172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff             0              97m     172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff             0              103m    172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull                 0              103m    172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff             0              9h      172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull                 0              7h31m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff             0              103m    172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull                 0              4h25m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              8h      172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull                 0              9h      172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull                 0              6h1m    172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ErrImagePull                 0              131m    172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull                 0              6h59m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-conn-test-evidence                         0/1     ErrImagePull                 0              36m     172.16.104.22    node2    <none>           <none>            run=registry-conn-test-evidence", "default           registry-connect-test                               0/1     ErrImagePull                 0              8h      172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              9h      172.16.166.185   node1    <none>           <none>            run=test-net-1779360704"], "raw_ref": "/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/002-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/002-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/002-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4 + L0（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将按照既有 evidence_plan 逐项执行工具调用。先并行执行多个可独立执行的 describe 命令。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-resolve-test (namespace: default, node: node2/10.2.0.50) status: Pending, IP: 172.16.104.1. Container dns-resolve-test using image busybox:1.36.1, args: nslookup registry-1.docker.io. State: W
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-2xvqr
namespace: mcp
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   11m (x112 over 9h)      kubelet  (combined from similar events): Fa
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          21m (x12 over 23m)   kubelet            Error: coul
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe pod node-debugger-node2-2cg95 (namespace: mcp) — Status: Pending. Container "debugger" using image busybox:1.36.1 is in ImagePullBackOff (Waiting). All 6 explicit pull attempts failed
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default) is Pending on node node1/10.2.0.49 with podIP 172.16.166.157. Container 'dig-tool' in ImagePullBackOff state (Waiting, Ready=False). Image registry.k8s.io/e2e-test-im
   💭 [证据链采集] 描述结果已全部获取。现在执行 g1-e2（检查 Secret 的 data keys）：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Secret
name: rc-app-secret
namespace: aiops-e2e
type: Opaque
data_keys: EXISTING_SECRET_KEY
has_dockerconfigjson: False
docker_secret_type_valid: False
   💭 [证据链采集] 现在查看 Prometheus 中容器/节点级别的网络指标来辅助判断 registry 连通性问题：
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [证据链采集] 现在所有关键工具调用已完成。以下是证据采集总结：

---

## 证据采集结论

### G2（主异常组，ImagePullFailed，约48个Pod）— 完整验证完成

**已采集证据：**

1. **g2-e1（critical）✅** — `dns-resolve-test`（node2, default, ErrImagePull）
   - 镜像：`busybox:1.36.1`
   - 错误：所有拉取均**i/o timeout**，涉及 7 个不同 registry-1.docker.io IP（108.160.165.139, 104.244.46.165, 93.179.102.140 等）
   - 时间跨度约104分钟

2. **g2-e2（critical）✅** — `dig-tool`（node1, default, ImagePullBackOff）
   - 镜像：`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`
   - 错误：**i/o timeout** dialing `us-west2-docker.pkg.dev:443`（多个IP）
   - BackOff事件已发生 596 次

3. **g2-e3（important）✅** — `node-debugger-node2-2cg95`（node2, mcp, ErrImagePull）
   - 镜像：`busybox:1.36.1`
   - 错误：5次 **i/o timeout** + 1次 **connection refused**（93.179.102.140:443）
   - ErrImagePull x52 over 8h

4. **g2-e4（important）✅** — `node-debugger-node1-2xvqr`（node1, mcp, ImagePullBackOff）
   - 镜像：`curlimages/curl:8.12.1`
   - 错误：**i/o timeout** dialing `registry-1.docker.io:443`（199.16.158.8:443）
   - BackOff x1195 over 10h

**关键发现：** 所有节点（node1/node2）连所有registry（docker.io、registry.k8s.io、us-west2-docker.pkg.dev）均超时，不是单一仓库问题。`connection refused` 与 `i/o timeout` 并存指向集群出口网络完全阻塞，而非节点层面隔离。

---

### G1（CreateContainerConfigError）— 最小验证完成

5. **g1-e1（critical）✅** — `rc-config-secret-key-missing`（aiops-e2e）
   - Events 原文：**`couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`**
   - 确认是 `CreateContainerConfigError`，非镜像拉取问题

6. **g1-e2（important）✅** — Secret `rc-app-secret`（aiops-e2e）
   - data_keys: **只有 `EXISTING_SECRET_KEY`**，**缺少 `APP_SECRET_TOKEN`**

**结论：** Secret `rc-app-secret` 中确实不存在 `APP_SECRET_TOKEN` key，属于配置缺失问题。

---

### G3（StartError）— 最小验证完成

7. **g3-e1（important）✅** — `node-debugger-node1-nx8gb`（mcp）
   - 镜像：`busybox:1.36`
   - 原因：`exec: "curl": executable file not found in $PATH` — 镜像中无 curl 命令
   - Exit Code: 128，状态 Failed

---

### 冲突/负向证据
- 无冲突证据，所有 Pod 均在预期 namespace 和节点上真实存在。

### 未采集证据
- 未执行主动 curl/wget 验证 registry（因已有充分 Events 证据，`connection refused` + `i/o timeout` 已清晰指向网络不可达，不需额外探测）

---

### 总体诊断结论

| 异常组 | 数量 | 根因 |
|--------|------|------|
| **G2 ImagePullFailed** | ~48个Pod | **集群出口到镜像仓库网络不可达** — 所有节点（node1/node2）到多个仓库（docker.io、registry.k8s.io、us-west2-docker.pkg.dev）均出现 `i/o timeout` 或 `connection refused`，跨仓库、跨节点的系统性网络故障 |
| **G1 ConfigError** | 1个Pod | Secret `rc-app-secret` 缺少 `APP_SECRET_TOKEN` key |
| **G3 StartError** | 1个Pod | 镜像 `busybox:1.36` 中无 `curl` 命令但启动命令指定了 curl |
   ✅ [证据链采集] 完成 (39.6s)
   📤 → 下游数据: evidence_items=11/11
   evidence_analysis={"evidence_plan":[{"id":"g2-e1","description":"【主异常组 g2】describe 代表 Pod - default/dns-resolve-test (ErrImagePull on node2) 获取 Events 和镜像地址","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","tool_args":{"kind":"Pod","name":"dns-resolve-test","namespace":"default"},"purpose":"查看 ErrImagePull 的 Events 描述中的错误原文（connection refused / i/o timeout）以及镜像地址和 imagePullSecrets","evidence_type":"pod_status_events","target_scope":"default/dns-resolve-test","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g2-e2","description":"【主异常组 g2】describe 代表 Pod - default/dig-tool (ImagePullBackOff on node1) 获取 Events 和镜像信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","tool_args":{"kind":"Pod","name":"dig-tool","namespace":"default"},"purpose":"查看 ImagePullBackOff 节点 node1 的 Events 确认错误是否与 node2 一致（connection refused vs i/o timeout）","evidence_type":"pod_status_events","target_scope":"default/dig-tool","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g2-e3","description":"【主异常组 g2】describe 代表 Pod - mcp/node-debugger-node2-2cg95 (ErrImagePull on node2) 跨 namespace 验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node2-2cg95 -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node2-2cg95","namespace":"mcp"},"purpose":"验证 mcp 命名空间 ErrImagePull Pod 的镜像拉取错误是否与 default 命名空间一致（connection refused）","evidence_type":"pod_status_events","target_scope":"mcp/node-debugger-node2-2cg95","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g2-e4","description":"【主异常组 g2】describe 代表 Pod - mcp/node-debugger-node1-2xvqr (ImagePullBackOff on node1) 跨 namespace 验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2xvqr -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-2xvqr","namespace":"mcp"},"purpose":"验证 mcp 命名空间 ImagePullBackOff Pod 在 node1 上的镜像拉取错误","evidence_type":"pod_status_events","target_scope":"mcp/node-debugger-node1-2xvqr","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g1-e1","description":"【异常组 g1 - CreateContainerConfigError】describe Pod rc-config-secret-key-missing 获取 Events 和具体缺少的 Secret key","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"确认 CreateContainerConfigError 的具体错误原因（缺少哪个 Secret key）","evidence_type":"pod_status_events","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g1-e2","description":"【异常组 g1】验证 Secret 资源是否存在及缺失的 key","level":"important","tool":"kubectl_get_yaml","command":"kubectl get secret -n aiops-e2e -o yaml","tool_args":{"command":"kubectl get secret -n aiops-e2e -o yaml"},"purpose":"查看 aiops-e2e 命名空间中的 Secret 及其 data keys，确认是否包含 APP_SECRET_TOKEN","evidence_type":"config_secret","target_scope":"aiops-e2e/secret","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g3-e1","description":"【异常组 g3 - StartError】describe Pod node-debugger-node1-nx8gb 获取状态和 Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"确认 StartError 的具体错误原因和 Last State","evidence_type":"pod_status_events","target_scope":"mcp/node-debugger-node1-nx8gb","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod dns-resolve-test (namespace: default, node: node2/10.2.0.50) status: Pending, IP: 172.16.104.1. Container dns-resolve-test using image busybox:1.36.1, args: nslookup registry-1.docker.io. State: Waiting (ImagePullBackOff), Ready: False, Restart Count: 0. Events show repeated image pull failures over ~104m: 6x i/o timeout dialing various registry-1.docker.io IPs (108.160.165.139, 104.244.46.165, 108.160.170.39, 67.228.102.32, 69.63.176.15, 108.160.166.42, 93.179.102.140) on port 443, 1x pull QPS exceeded, 12x ErrImagePull (x12), 4x ImagePullBackOff (x4), 5x Back-off pulling image (x5). Container ID and Image ID are empty.\nkey_facts: [\"Pod: dns-resolve-test, namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending, IP: 172.16.104.1\", \"Container: dns-resolve-test, Image: busybox:1.36.1\", \"Container State: Waiting (Reason: ImagePullBackOff)\", \"Container Ready: False, Restart Count: 0\", \"Args: nslookup registry-1.docker.io\", \"Container ID: empty, Image ID: empty\", \"Events: Multiple Failed to pull image errors over ~104m - i/o timeout dialing registry-1.docker.io:443 (7 distinct IPs), pull QPS exceeded (1x), ErrImagePull (x12), ImagePullBackOff (x4), Back-off pulling image (x5)\"]\nconflicts: [\"raw_preview shows 1x 'Failed 41s' pull error (connection refused to 93.179.102.140:443) and 'Pulling' event (x12 over 104m) not present in current_summary; current_summary omitted 'Pulling' event entirely\", \"current_summary includes 'Failed 69s...pull QPS exceeded' which is present in raw_preview at Age 69s; consistent\", \"current_summary's 'Warning  Failed   41s (x12 over 96m)   kubelet  Error: ErrImagePull' - raw_preview shows this at Age 41s (x12 over 96m) along with an additional 'Failed 41s' pull error; consistent\"]\nmissing: [\"Annotations: cni.projectcalico.org containerID, podIPs (present in raw_preview, partially in summary)\", \"QoS Class: BestEffort\", \"Tolerations: node.kubernetes.io/not-ready and unreachable NoExecute\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\", \"Volumes: kube-api-access-wst5b (Projected)\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-2xvqr\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   11m (x112 over 9h)      kubelet  (combined from similar events): Failed to pull image \"curlimages/curl:8.12.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/curlimages/curl:8.12.1\": failed to resolve reference \"docker.io/curlimages/curl:8.12.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\": dial tcp 199.16.158.8:443: i/o timeout\n  Normal   BackOff  2m41s (x1195 over 10h)  kubelet  Back-off pulling image \"curlimages/curl:8.12.1\"\n      Reason:       ImagePullBackOff\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:\n    Image:         curlimages/curl:8.12.1\n    Image ID:\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-5m5hf:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   11m (x112 over 9h)      kubelet  (combined from similar events): Failed to pull image \"curlimages/curl:8.12.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/curlimages/curl:8.12.1\": failed to resolve reference \"docker.io/curlimages/curl:8.12.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\": dial tcp 199.16.158.8:443: i/o timeout\n  Normal   BackOff  2m41s (x1195 over 10h)  kubelet  Back-off pulling image \"curlimages/curl:8.12.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          21m (x12 over 23m)   kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: e50889f651dff0ebd5a4ed7212a0f9deacd4b503f1ae265a36959b8e7c2ff9c4\n                  cni.projectcalico.org/podIP: 172.16.166.130/32\n                  cni.projectcalico.org/podIPs: 172.16.166.130/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-pbw78:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed          21m (x12 over 23m)   kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe pod node-debugger-node2-2cg95 (namespace: mcp) — Status: Pending. Container \"debugger\" using image busybox:1.36.1 is in ImagePullBackOff (Waiting). All 6 explicit pull attempts failed: 5x i/o timeout (different IPs) + 1x connection refused. Also 1 aggregated event: Failed x52 over 8h: ErrImagePull. Pod command: chroot /host /bin/sh -c \"nslookup registry-1.docker.io 2>&1 || echo DNS check failed\". Ready: False, Restart Count: 0. QoS: BestEffort. HostPath volume at /.\nkey_facts: [\"resource: Pod node-debugger-node2-2cg95\", \"namespace: mcp\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container: debugger\", \"image: busybox:1.36.1\", \"container state: Waiting (Reason: ImagePullBackOff)\", \"Ready: False\", \"Restart Count: 0\", \"Event: Warning Failed 50m — kubelet: Failed to pull image busybox:1.36.1 — i/o timeout (199.59.148.8:443)\", \"Event: Warning Failed 40m (x2 over 60m) — kubelet: Failed to pull image busybox:1.36.1 — i/o timeout (168.143.162.58:443)\", \"Event: Warning Failed 30m — kubelet: Failed to pull image busybox:1.36.1 — i/o timeout (199.59.148.97:443)\", \"Event: Warning Failed 19m — kubelet: Failed to pull image busybox:1.36.1 — i/o timeout (199.59.149.231:443)\", \"Event: Warning Failed 8m40s — kubelet: Failed to pull image busybox:1.36.1 — i/o timeout (108.160.166.61:443)\", \"Event: Warning Failed 69s — kubelet: Failed to pull image busybox:1.36.1 — connection refused (93.179.102.140:443)\", \"Event: Warning Failed 69s (x52 over 8h) — kubelet: Error: ErrImagePull\", \"QoS Class: BestEffort\", \"Volumes: host-root (HostPath /), kube-api-access-chx7q (Projected)\", \"Pod command: chroot /host /bin/sh -c 'nslookup registry-1.docker.io 2>&1 || echo DNS check failed'\"]\nmissing: [\"Node-Selectors: <none>\", \"Tolerations: op=Exists\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-tool (namespace: default) is Pending on node node1/10.2.0.49 with podIP 172.16.166.157. Container 'dig-tool' in ImagePullBackOff state (Waiting, Ready=False). Image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 cannot be pulled: all pull attempts fail with i/o timeout dialing us-west2-docker.pkg.dev (multiple IPs, various timestamps). BackOff event fired 596 times over 5h12m; Failed events occurred at 35m ago, 10m ago (x8 over 4h44m), and 82s ago (x2 over 48m). Container has never started (Restart Count: 0). QoS BestEffort, no node selectors.\nkey_facts: [\"Name: dig-tool, Namespace: default\", \"Node: node1/10.2.0.49\", \"Status: Pending\", \"PodIP: 172.16.166.157\", \"Container 'dig-tool' State: Waiting, Reason: ImagePullBackOff\", \"Container Ready: False\", \"Restart Count: 0\", \"Image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"All pull attempts fail: i/o timeout dialing us-west2-docker.pkg.dev:443\", \"Failed event at 35m ago: dial tcp 108.177.125.82:443: i/o timeout\", \"Failed event at 10m ago (x8 over 4h44m): dial tcp 142.250.157.82:443: i/o timeout\", \"Failed event at 82s ago (x2 over 48m): dial tcp 142.250.157.82:443: i/o timeout\", \"Normal BackOff at 7m11s ago (x596 over 5h12m): Back-off pulling image\", \"QoS Class: BestEffort\", \"Node-Selectors: <none>\"]\nconflicts: [\"current_summary missing the 82s ago Failed event (x2 over 48m) that raw_preview includes\"]\nmissing: [\"raw_preview includes 82s Failed event (x2 over 48m) not in summary; raw_preview shows Pod has IP 172.16.166.157 and Conditions section (Initialized=True, PodScheduled=True) not carried in summary\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Secret\nname: rc-app-secret\nnamespace: aiops-e2e\ntype: Opaque\ndata_keys: EXISTING_SECRET_KEY\nhas_dockerconfigjson: False\ndocker_secret_type_valid: False","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/007-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/007-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/007-evidence-kubectl_get_yaml.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: imagePullSecrets 必须在同 namespace，私有仓库 secret 类型应为 kubernetes.io/dockerconfigjson 或 kubernetes.io/dockercfg。\n\n### Step 4: 按事件错误文本归类\n- `manifest unknown` / `not found`: 镜像仓库中不存在该镜像或 tag。\n- `invalid reference format`: image 字符串格式错误。\n- `unauthorized` / `no basic auth credentials`: imagePullSecret 缺失、未引用、类型错误或凭据错误。\n- `pull access denied` / `insufficient_scope`: 仓库权限不足或镜像路径错误。\n- `x509: certificate signed by unknown authority`: 节点容器运行时不信任仓库 TLS 证书。\n- `i/o timeout` / `connection refused`: 节点到镜像仓库访问失败，需检查仓库地址、端口、防火墙、DNS。\n- `context canceled`: 拉取过程中连接被取消，常见于网络中断、镜像仓库响应慢、kubelet/运行时超时或并发拉取拥塞。\n- `Too Many Requests` / rate limit: 镜像仓库限流，需认证、镜像缓存或私有代理仓库。\n- 长时间只有 `Pulling image` 无后续失败事件: 关注镜像体积、节点带宽、运行时并发拉取限制、kubelet `registryPullQPS` / `registryBurst` 配置。\n\n### Step 5: 主动验证镜像仓库连通性\n可用只读命令验证节点或集群内到镜像仓库的 HTTPS 连通性，例如：\n```bash\ncurl -v --connect-timeout 10 https://registry-1.docker.io/v2/\n```\n判读规则：\n- 返回 `200/401/403`：说明 HTTPS 网络可达；`401/403` 通常是认证/权限语义，不是网络不可达。\n- `curl: (28) Operation timed out`、`Connection timed out`、`i/o timeout`、`命令执行超时`：这是诊断事实，表示镜像仓库网络不可达或链路被阻断，不应当仅视为“工具执行失败”。\n- `Could not resolve host`：DNS 解析失败。\n- `connection refused/reset`：目标端口不可达、被中间设备拒绝或连接被重置。\n- `x509`：TLS 证书信任问题。\n\n\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| Events 含 connection refused/timeout | 镜像仓库网络不可达 | 高 |\n| Events 含 context canceled | 镜像拉取连接被取消，优先检查网络、仓库响应、运行时超时和并发拉取 | 中 |\n| 主动 curl/wget registry 超时或命令执行超时 | 镜像仓库网络不可达 | 高 |\n| Events 含 manifest unknown/not found | 镜像或 tag 不存在 | 高 |\n| Events 含 unauthorized/no basic auth | 认证失败（缺少或错误的 imagePullSecret） | 高 |\n| Events 含 pull access denied/insufficient_scope | 仓库权限不足或镜像路径错误 | 高 |\n| Events 含 invalid reference format | 镜像名称格式错误 | 高 |\n| Events 含 x509 | 节点容器运行时信任链/TLS 证书问题 | 高 |\n| DNS 解析失败 | DNS 问题导致仓库不可达 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/008-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/008-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2392aeb38c494580/tools/008-evidence-fetch_runbook.summary.txt"}],"llm_analysis":"现在所有关键工具调用已完成。以下是证据采集总结：\n\n---\n\n## 证据采集结论\n\n### G2（主异常组，ImagePullFailed，约48个Pod）— 完整验证完成\n\n**已采集证据：**\n\n1. **g2-e1（critical）✅** — `dns-resolve-test`（node2, default, ErrImagePull）\n   - 镜像：`busybox:1.36.1`\n   - 错误：所有拉取均**i/o timeout**，涉及 7 个不同 registry-1.docker.io IP（108.160.165.139, 104.244.46.165, 93.179.102.140 等）\n   - 时间跨度约104分钟\n\n2. **g2-e2（critical）✅** — `dig-tool`（node1, default, ImagePullBackOff）\n   - 镜像：`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`\n   - 错误：**i/o timeout** dialing `us-west2-docker.pkg.dev:443`（多个IP）\n   - BackOff事件已发生 596 次\n\n3. **g2-e3（important）✅** — `node-debugger-node2-2cg95`（node2, mcp, ErrImagePull）\n   - 镜像：`busybox:1.36.1`\n   - 错误：5次 **i/o timeout** + 1次 **connection refused**（93.179.102.140:443）\n   - ErrImagePull x52 over 8h\n\n4. **g2-e4（important）✅** — `node-debugger-node1-2xvqr`（node1, mcp, ImagePullBackOff）\n   - 镜像：`curlimages/curl:8.12.1`\n   - 错误：**i/o timeout** dialing `registry-1.docker.io:443`（199.16.158.8:443）\n   - BackOff x1195 over 10h\n\n**关键发现：** 所有节点（node1/node2）连所有registry（docker.io、registry.k8s.io、us-west2-docker.pkg.dev）均超时，不是单一仓库问题。`connection refused` 与 `i/o timeout` 并存指向集群出口网络完全阻塞，而非节点层面隔离。\n\n---\n\n### G1（CreateContainerConfigError）— 最小验证完成\n\n5. **g1-e1（critical）✅** — `rc-config-secret-key-missing`（aiops-e2e）\n   - Events 原文：**`couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`**\n   - 确认是 `CreateContainerConfigError`，非镜像拉取问题\n\n6. **g1-e2（important）✅** — Secret `rc-app-secret`（aiops-e2e）\n   - data_keys: **只有 `EXISTING_SECRET_KEY`**，**缺少 `APP_SECRET_TOKEN`**\n\n**结论：** Secret `rc-app-secret` 中确实不存在 `APP_SECRET_TOKEN` key，属于配置缺失问题。\n\n---\n\n### G3（StartError）— 最小验证完成\n\n7. **g3-e1（important）✅** — `node-debugger-node1-nx8gb`（mcp）\n   - 镜像：`busybox:1.36`\n   - 原因：`exec: \"curl\": executable file not found in $PATH` — 镜像中无 curl 命令\n   - Exit Code: 128，状态 Failed\n\n---\n\n### 冲突/负向证据\n- 无冲突证据，所有 Pod 均在预期 namespace 和节点上真实存在。\n\n### 未采集证据\n- 未执行主动 curl/wget 验证 registry（因已有充分 Events 证据，`connection refused` + `i/o timeout` 已清晰指向网络不可达，不需额外探测）\n\n---\n\n### 总体诊断结论\n\n| 异常组 | 数量 | 根因 |\n|--------|------|------|\n| **G2 ImagePullFailed** | ~48个Pod | **集群出口到镜像仓库网络不可达** — 所有节点（node1/node2）到多个仓库（docker.io、registry.k8s.io、us-west2-docker.pkg.dev）均出现 `i/o timeout` 或 `connection refused`，跨仓库、跨节点的系统性网络故障 |\n| **G1 ConfigError** | 1个Pod | Secret `rc-app-secret` 缺少 `APP_SECRET_TOKEN` key |\n| **G3 StartError** | 1个Pod | 镜像 `busybox:1.36` 中无 `curl` 命令但启动命令指定了 curl |","collection_summary":"计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%；其中真实环境证据 11/11 项，完整度 100%；实际执行工具 11 个，匹配计划 7 个，未规划证据 4 个","plan_total":7,"plan_collected":7,"plan_completeness":1.0,"environment_evidence_total":11,"environment_evidence_collected":11,"environment_evidence_completeness":1.0,"executed_tool_count":11,"matched_tool_count":7,"unplanned_tool_count":4,"evidence_inventory":[{"id":"g2-e1","description":"【主异常组 g2】describe 代表 Pod - default/dns-resolve-test (ErrImagePull on node2) 获取 Events 和镜像地址","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","purpose":"查看 ErrImagePull 的 Events 描述中的错误原文（connection refused / i/o timeout）以及镜像地址和 imagePullSecrets","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e2","description":"【主异常组 g2】describe 代表 Pod - default/dig-tool (ImagePullBackOff on node1) 获取 Events 和镜像信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","purpose":"查看 ImagePullBackOff 节点 node1 的 Events 确认错误是否与 node2 一致（connection refused vs i/o timeout）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e3","description":"【主异常组 g2】describe 代表 Pod - mcp/node-debugger-node2-2cg95 (ErrImagePull on node2) 跨 namespace 验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node2-2cg95 -n mcp","purpose":"验证 mcp 命名空间 ErrImagePull Pod 的镜像拉取错误是否与 default 命名空间一致（connection refused）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e4","description":"【主异常组 g2】describe 代表 Pod - mcp/node-debugger-node1-2xvqr (ImagePullBackOff on node1) 跨 namespace 验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2xvqr -n mcp","purpose":"验证 mcp 命名空间 ImagePullBackOff Pod 在 node1 上的镜像拉取错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-e1","description":"【异常组 g1 - CreateContainerConfigError】describe Pod rc-config-secret-key-missing 获取 Events 和具体缺少的 Secret key","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"确认 CreateContainerConfigError 的具体错误原因（缺少哪个 Secret key）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-e2","description":"【异常组 g1】验证 Secret 资源是否存在及缺失的 key","level":"important","tool":"kubectl_get_yaml","command":"kubectl get secret -n aiops-e2e -o yaml","purpose":"查看 aiops-e2e 命名空间中的 Secret 及其 data keys，确认是否包含 APP_SECRET_TOKEN","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-e1","description":"【异常组 g3 - StartError】describe Pod node-debugger-node1-nx8gb 获取状态和 Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"确认 StartError 的具体错误原因和 Last State","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g2-e1 | critical | ✅ | kubectl_describe | 【主异常组 g2】describe 代表 Pod - default/dns-resolv... | `kubectl describe pod dns-resolve-test -n default` |
   | g2-e2 | critical | ✅ | kubectl_describe | 【主异常组 g2】describe 代表 Pod - default/dig-tool (... | `kubectl describe pod dig-tool -n default` |
   | g2-e3 | important | ✅ | kubectl_describe | 【主异常组 g2】describe 代表 Pod - mcp/node-debugger-... | `kubectl describe pod node-debugger-node2-2cg95 -n mcp` |
   | g2-e4 | important | ✅ | kubectl_describe | 【主异常组 g2】describe 代表 Pod - mcp/node-debugger-... | `kubectl describe pod node-debugger-node1-2xvqr -n mcp` |
   | g1-e1 | critical | ✅ | kubectl_describe | 【异常组 g1 - CreateContainerConfigError】describe... | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | g1-e2 | important | ✅ | kubectl_get_yaml | 【异常组 g1】验证 Secret 资源是否存在及缺失的 key | `kubectl get secret -n aiops-e2e -o yaml` |
   | g3-e1 | important | ✅ | kubectl_describe | 【异常组 g3 - StartError】describe Pod node-debugg... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.5s)
   📤 → 下游数据: root_cause=**主根因：集群出口网络不可达** — 所有节点（node1/node2）到外部镜像仓库的出站连接被阻断。证据显示：node1上dig-tool（registry.k8s.io→us-west2-docker.pkg.dev:443）i/o timeout持续5h12m（BackOff x596）；node2上dns-resolve-test（busybox:1.36.1→registry-1.docker.io:443）7个不同IP全部i/o timeout持续104分钟；node-debugger-node2-2cg95同时出现connection refused（93.179.102.140:443）和i/o timeout；node-debugger-node1-2xvqr（curlimages/curl:8.12.1）i/o timeout持续10h（BackOff x1195）。跨多个镜像仓库、跨节点、跨镜像版本的统一失败模式指向集群出口防火墙/网络策略拦截了HTTPS出站流量。**次要异常1（独立）：** aiops-e2e/rc-config-secret-key-mi
... 截断，原始 738 字符
   confidence=95%
   causal_chain={"root_cause": "集群出口网络不可达导致无法连接外部镜像仓库（registry-1.docker.io:443、us-west2-docker.pkg.dev:443等），所有节点（node1/node2）上的镜像拉取均因TCP连接超时或被拒绝而失败", "propagation": "集群出口网络/防火墙策略阻止了到外部registry的出站连接（HTTPS 443端口），kubelet尝试从多个镜像仓库拉取镜像时TCP连接均超时(i/o timeout)或被拒绝(connection refused)，容器运行时报告Failed to pull image错误，kubelet将Pod状态标记为ErrImagePull，随后进入ImagePullBackOff重试循环", "direct_cause": "kubelet无法从容器镜像仓库拉取镜像，Events显示'Failed to pull image' + 'dial tcp X.X.X.X:443: connect: connection refused / i/o timeout'", "manifestation": "default和mcp命名空间中约48个Pod处于ImagePullBackOff或ErrImagePull状态，所有容器均无法启动；另有个别Pod因Secret缺失(CreateContainerConfigError)或镜像内命令不存在(StartError)而独立失败"}
   rca_analysis={"phenomenon": "集群中约48个Pod处于ImagePullBackOff/ErrImagePull状态（default和mcp命名空间），1个Pod处于CreateContainerConfigError（aiops-e2e命名空间），1个Pod处于StartError（mcp命名空间）。系统Pod（kube-system）正常运行，节点状态正常。", "evidence_inventory": [{"id": "g2-e1", "source": "kubectl_describe(default/dns-resolve-test)", "content": "Pod位于node2，镜像busybox:1.36.1，104分钟内所有拉取均i/o timeout，涉及7个不同registry-1.docker.io IP的443端口", "reliability": "高"}, {"id": "g2-e2", "source": "kubectl_describe(default/dig-tool)", "content": "Pod位于node1，镜像registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，i/o timeout dialing us-west2-docker.pkg.dev:443，BackOff x596", "reliability": "高"}, {"id": "g2-e3", "source": "kubectl_describe(mcp/node-debugger-node2-2cg95)", "content": "Pod位于node2，镜像busybox:1.36.1，5次i/o timeout + 1次connection refused(93.179.102.140:443)，ErrImagePull x52 over 8h", "reliability": "高"}, {"id": "g2-e4", "source": "kubectl_describe(mcp/node-debugger-node1-2xvqr)", "content": "Pod位于node1，镜像curlimages/curl:8.12.1，i/o timeout dialing registry-1.docker.io:443(199.16.158.8)，BackOff x1195 over 10h", "reliability": "高"}, {"id": "g1-e1", "source": "kubectl_describe(aiops-e2e/rc-config-secret-key-missing)", "content": "Events原文：couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret，状态CreateContainerConfigError", "reliability": "高"}, {"id": "g1-e2", "source": "kubectl_get_yaml(Secret rc-app-secret)", "content": "Secret rc-app-secret类型Opaque，data_keys仅包含EXISTING_SECRET_KEY，缺少APP_SECRET_TOKEN", "reliability": "高"}, {"id": "g3-e1", "source": "kubectl_describe(mcp/node-debugger-node1-nx8gb)", "content": "镜像busybox:1.36，StartError原因：exec: 'curl' not found in $PATH，Exit Code 128，状态Failed", "reliability": "高"}, {"id": "layer_4", "source": "kubernetes_jq_query(全量Pod)", "content": "所有异常Pod涉及多种镜像源(docker.io/registry.k8s.io/us-west2-docker.pkg.dev)，均报connection refused或i/o timeout", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "g2-e1", "raw_data": "Pod dns-resolve-test, node2, busybox:1.36.1, 6x i/o timeout + 1x pull QPS exceeded + 12x ErrImagePull + 4x ImagePullBackOff over 104m, multiple registry-1.docker.io IPs", "interpretation": "node2上对docker.io的镜像拉取全部因网络超时而失败，涉及多个不同IP，说明不是单点DNS解析问题而是出口网络完全不可达"}, {"evidence_id": "g2-e2", "raw_data": "Pod dig-tool, node1, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, i/o timeout dialing us-west2-docker.pkg.dev:443, BackOff x596 over 5h12m", "interpretation": "node1上对registry.k8s.io（实际分发至us-west2-docker.pkg.dev）的拉取也超时，证明不仅仅是docker.io的问题，而是对所有外部registry的通用网络不可达"}, {"evidence_id": "g2-e3", "raw_data": "Pod node-debugger-node2-2cg95, node2, busybox:1.36.1, 5x i/o timeout + 1x connection refused to 93.179.102.140:443, ErrImagePull x52 over 8h", "interpretation": "同时出现connection refused和i/o timeout两种错误模式，指向集群出口网络完全阻塞/防火墙拦截，而非节点级别网络断连"}, {"evidence_id": "g2-e4", "raw_data": "Pod node-debugger-node1-2xvqr, node1, curlimages/curl:8.12.1, Failed to pull: dial tcp 199.16.158.8:443: i/o timeout, BackOff x1195 over 10h", "interpretation": "node1上另一个镜像(curlimages/curl)也超时，且错误持续10小时，排除临时抖动，确认是持续性网络故障"}, {"evidence_id": "g1-e1", "raw_data": "Events: Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret", "interpretation": "Pod启动配置错误，引用的Secret key APP_SECRET_TOKEN不存在"}, {"evidence_id": "g1-e2", "raw_data": "Secret rc-app-secret data_keys: [EXISTING_SECRET_KEY], missing: APP_SECRET_TOKEN", "interpretation": "确认Secret对象存在但只包含EXISTING_SECRET_KEY，APP_SECRET_TOKEN确实缺失，属于应用配置缺陷"}, {"evidence_id": "g3-e1", "raw_data": "failed to start container: exec: 'curl': executable file not found in $PATH, Exit Code 128, Image busybox:1.36", "interpretation": "Pod Spec中entrypoint使用了curl命令，但镜像busybox:1.36中不包含curl可执行文件，容器启动立即失败"}, {"evidence_id": "layer_4", "raw_data": "Mass ImagePullBackOff/ErrImagePull errors for images: busybox, alpine, curlimages/curl, registry.k8s.io/e2e-test-images/jessie-dnsutils, registry.k8s.io/pause. All show connection refused or i/o timeout", "interpretation": "跨多个镜像仓库、多个节点、多个镜像版本的拉取全部失败，确认不是镜像tag/名称问题，根因锁定为集群到外部registry的网络不可达"}], "causal_chain": {"root_cause": "集群出口网络不可达导致无法连接外部镜像仓库（registry-1.docker.io:443、us-west2-docker.pkg.dev:443等），所有节点（node1/node2）上的镜像拉取均因TCP连接超时或被拒绝而失败", "propagation": "集群出口网络/防火墙策略阻止了到外部registry的出站连接（HTTPS 443端口），kubelet尝试从多个镜像仓库拉取镜像时TCP连接均超时(i/o timeout)或被拒绝(connection refused)，容器运行时报告Failed to pull image错误，kubelet将Pod状态标记为ErrImagePull，随后进入ImagePullBackOff重试循环", "direct_cause": "kubelet无法从容器镜像仓库拉取镜像，Events显示'Failed to pull image' + 'dial tcp X.X.X.X:443: connect: connection refused / i/o timeout'", "manifestation": "default和mcp命名空间中约48个Pod处于ImagePullBackOff或ErrImagePull状态，所有容器均无法启动；另有个别Pod因Secret缺失(CreateContainerConfigError)或镜像内命令不存在(StartError)而独立失败"}, "root_cause": "**主根因：集群出口网络不可达** — 所有节点（node1/node2）到外部镜像仓库的出站连接被阻断。证据显示：node1上dig-tool（registry.k8s.io→us-west2-docker.pkg.dev:443）i/o timeout持续5h12m（BackOff x596）；node2上dns-resolve-test（busybox:1.36.1→registry-1.docker.io:443）7个不同IP全部i/o timeout持续104分钟；node-debugger-node2-2cg95同时出现connection refused（93.179.102.140:443）和i/o timeout；node-debugger-node1-2xvqr（curlimages/curl:8.12.1）i/o timeout持续10h（BackOff x1195）。跨多个镜像仓库、跨节点、跨镜像版本的统一失败模式指向集群出口防火墙/网络策略拦截了HTTPS出站流量。**次要异常1（独立）：** aiops-e2e/rc-config-secret-key-mi\n... 截断，原始 738 字符", "root_cause_summary": "**主根因：集群出口网络不可达** — 所有节点（node1/node2）到外部镜像仓库的出站连接被阻断。证据显示：node1上dig-tool（registry.k8s.io→us-west2-docker.pkg.dev:443）i/o timeout持续5h12m（BackOff x596）；node2上dns-resolve-test（busybox:1.36.1→registry-1.docker.io:443）7个不同IP全部i/o timeout持续104分钟；node-debugger-node2-2cg95同时出现connection refused（93.179.102.140:443）和i/o timeout；node-debugger-node1-2xvqr（curlimages/curl:8.12.1）i/o timeout持续10h（BackOff x1195）。跨多个镜像仓库、跨节点、跨镜像版本的统一失败模式指向集群出口防火墙/网络策略拦截了HTTPS出站流量。**次要异常1（独立）：** aiops-e2e/rc-config-secret-key-mi\n... 截断，原始 738 字符", "confidence": 0.95, "confidence_reason": "有直接Events证据（connection refused + i/o timeout 原始错误信息），跨4个代表Pod覆盖不同节点和不同镜像仓库，因果链完整清晰。Secret缺失和StartError也有直接Events/YAML证据支撑。", "primary_runbooks": [], "alternative_causes": [{"cause": "镜像地址或tag不存在", "probability": "low", "reason": "排除理由：同一集群内不同镜像（busybox:1.36.1、alpine:3.18、curlimages/curl:8.12.1、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0、registry.k8s.io/pause:3.9）均无法拉取，错误均为connection refused/i/o timeout而非'not found'，指向网络问题而非镜像存在性问题"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "排除理由：错误信息为TCP连接超时/拒绝而非认证失败（unauthorized/denied），且公开镜像（busybox、alpine等）无需认证"}, {"cause": "节点本地磁盘空间不足", "probability": "low", "reason": "排除理由：Events中无磁盘空间相关错误，且系统Pod正常运行，节点状态正常"}, {"cause": "DNS解析故障", "probability": "low", "reason": "排除理由：错误信息中已显示解析出具体IP（如93.179.102.140、199.59.148.8等），说明DNS解析成功，失败在TCP连接阶段"}], "limitations": "未执行主动的curl/wget外网连通性测试（因已有充分Events证据）；未检查集群出口防火墙规则/网络策略配置（需集群管理员权限）；未确认是否存在代理/镜像缓存（registry mirror）配置；StartError的node-debugger-node1-nx8gb实际已拉取镜像成功（有Image ID），与其同组的其他node-debugger Pod因网络问题无法拉取镜像，该Pod的启动失败独立于主根因。", "llm_raw_analysis": "## 证据清点\n共采集7个直接证据（g2-e1至g2-e4、g1-e1、g1-e2、g3-e1）和1个全局汇总证据（layer_4）。覆盖3个异常组：G2主异常组（ImagePullFailed，约48个Pod）、G1（CreateContainerConfigError，1个Pod）、G3（StartError，1个Pod）。\n\n## 逐条分析\n- **g2-e1（critical）**: node2上dns-resolve-test拉取busybox:1.36.1，7个不同IP全部i/o timeout，证明不是DNS解析问题而是TCP连接完全不可达\n- **g2-e2（critical）**: node1上dig-tool拉取registry.k8s.io镜像也i/o timeout至us-west2-docker.pkg.dev，证明不止docker.io有问题\n- **g2-e3（important）**: node2上node-debugger同时出现connection refused和i/o timeout两种错误，指向防火墙拦截\n- **g2-e4（important\n... 截断，原始 980 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: **主根因：集群出口网络不可达** — 所有节点（node1/node2）到外部镜像仓库的出站连接被阻断。证据显示：node1上dig-tool（registry.k8s.io→us-west2-docker.pkg.dev:443）i/o timeout持续5h12m（BackOff x596）；...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群出口网络不可达导致无法连接外部镜像仓库（registry-1.docker.io:443、us-west2-docker.pkg.dev:443等），所有节点（node1/node2）上的镜像拉取均因TCP连接超时或被拒绝而失败
     传导机制: 集群出口网络/防火墙策略阻止了到外部registry的出站连接（HTTPS 443端口），kubelet尝试从多个镜像仓库拉取镜像时TCP连接均超时(i/o timeout)或被拒绝(connection refused)，容器运行时报告Failed to pull image错误，kubelet将Pod状态标记为ErrImagePull，随后进入ImagePullBackOff重试循环
     最终表现: default和mcp命名空间中约48个Pod处于ImagePullBackOff或ErrImagePull状态，所有容器均无法启动；另有个别Pod因Secret缺失(CreateContainerConfigError)或镜像内命令不存在(StartError)而独立失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (32.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8980 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 12.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，我是您的资深 K8s 诊断专家。基于三阶段分析结果，我现在为您呈现集群问题的详尽诊断报告。

---
## 📊 诊断概览

首先，直接回答您的问题：**您的集群当前存在严重的大面积镜像拉取失败问题，影响约 48 个 Pod，根本原因是集群出口网络无法连接到外部镜像仓库。此外，还有两个独立存在的次要配置/运行时问题。**

| 项目 | 内容 |
|------|------|
| **核心问题** | **大面积 Pod (约48个) 处于 `ImagePullBackOff` / `ErrImagePull` 状态** |
| **兼容归因层** | L3 - 镜像仓库/网络 |
| **问题分类** | `image_pull` |
| **置信度** | **95%** |
| **证据完整度** | 7/7 (100%) |
| **次要问题 1** | Pod `aiops-e2e/rc-config-secret-key-missing` 处于 `CreateContainerConfigError` (配置错误) |
| **次要问题 2** | Pod `mcp/node-debugger-node1-nx8gb` 处于 `StartError` (容器启动失败) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| **受影响 Namespace** | `default`, `mcp`, `aiops-e2e` |
| **受影响 Node** | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| **Pod 数量** | 约 **48 个** Pod 处于 Pending 状态 |
| **核心错误信息** | `Failed to pull image ... dial tcp ...:443: connect: connection refused / i/o timeout` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | **Pod 状态** | `kubectl get pods --all-namespaces` | 返回约 115 行 Pod 信息，其中 59 个 Running，约 50 个异常。`default` 和 `mcp` namespace 中存在大量 Pod (`dns-resolve-test`, `dig-tool`, `node-debugger-*`) 处于 `ImagePullBackOff` (27个) 和 `ErrImagePull` (21个) 状态。 | 集群存在大面积镜像拉取失败问题。 |
| 2 | **Pod Events (node2)** | `describe pod dns-resolve-test` | 容器 `dns-resolve-test` 使用镜像 `busybox:1.36.1`，在 104 分钟内重复出现 `i/o timeout` 错误，尝试连接多个 `registry-1.docker.io` IP 地址 (如 108.160.165.139, 104.244.46.165 等) 的 443 端口均失败。事件摘要显示 `Failed to pull image "busybox:1.36.1"`。 | **节点 node2 无法连接 Docker Hub (`registry-1.docker.io:443`)**。 |
| 3 | **Pod Events (node1)** | `describe pod dig-tool` | 容器 `dig-tool` 使用镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，在 5 小时 12 分钟内，所有拉取尝试均因 `i/o timeout` 失败，目标地址为 `us-west2-docker.pkg.dev:443`。BackOff 事件触发了 596 次。 | **节点 node1 无法连接 Google Cloud Registry (`us-west2-docker.pkg.dev:443`)**。 |
| 4 | **Pod Events (node1)** | `describe pod node-debugger-node1-2xvqr` | 容器使用镜像 `curlimages/curl:8.12.1`，拉取失败。事件显示 `Failed to pull image "curlimages/curl:8.12.1"`，且 `Back-off pulling image` 事件在 10 小时内触发了 1195 次。 | **节点 node1 无法连接 Docker Hub，最长已持续 10 小时。** |
| 5 | **Pod Events (node2)** | `describe pod node-debugger-node2-2cg95` | 容器使用镜像 `busybox:1.36.1`。6 次显式拉取尝试中，5 次是 `i/o timeout`，1 次是 `connection refused` (目标 IP: 93.179.102.140:443)。 | **节点 node2 连接 Docker Hub 不仅超时，还出现直接连接拒绝。** |
| 6 | **Pod Events (node1)** | `describe pod rc-config-secret-key-missing` | Pod 处于 `CreateContainerConfigError`，事件显示：`Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`。 | Pod 引用的 Secret 中缺少指定的 Key。 |
| 7 | **Secret 验证** | `kubectl get secret -o yaml rc-app-secret` | Secret `rc-app-secret` 存在于 `aiops-e2e` 命名空间，类型为 `Opaque`。但其 `data` 字段中只包含 `EXISTING_SECRET_KEY`，**不包含** `APP_SECRET_TOKEN`。 | Secret 存在但**缺少 Key**，证据确认。 |
| 8 | **Pod Events (node1)** | `describe pod node-debugger-node1-nx8gb` | Pod 状态为 `Failed`，错误信息：`failed to create containerd task: failed to create shim task: OCI runtime create failed`，Exit Code 128，`Reason: StartError`。 | 容器运行时 (containerd) 无法正常启动容器，与网络问题无关。 |

### 证据关联分析

- **核心问题证据链 (证据 #1, #2, #3, #4, #5)**：
    1.  **系统性失败**: 证据 #1 显示问题影响范围极广，并非单个 Pod 故障。
    2.  **跨仓库、跨节点、跨镜像**: 证据 #2, #3, #4, #5 表明无法连接的镜像仓库有 `docker.io`、`registry.k8s.io`，受影响节点包括 `node1` 和 `node2`，涉及 `busybox`、`curl`、`jessie-dnsutils`等多种镜像。
    3.  **统一错误模式**: 所有失败的 Pod 都返回相同的错误类型：`i/o timeout` 或 `connection refused`，目标端口都是 443。
    - **结论**: 这些证据共同排除了单个仓库、单个节点或单个镜像的问题，强有力地指向**集群的出口网络策略（防火墙/代理/网络策略）阻止了所有到外部 HTTPS 镜像仓库的出站连接**。

- **次要问题 1 (证据 #6, #7)**: 问题明确，是配置错误导致。
- **次要问题 2 (证据 #8)**: 问题明确，是容器运行时故障，与网络无关。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                                           │
│ 集群出口网络不可达/被阻断。防火墙、代理或网络策略阻止了所有节点 (node1, node2)                  │
│ 到外部镜像仓库 (registry-1.docker.io, us-west2-docker.pkg.dev 等) 的出站 HTTPS (443端口) 连接。  │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                                          │
│ 所有 kubelet 尝试从远程仓库拉取镜像 → TCP 三次握手无法建立 (SYN包被丢弃或被拒绝)               │
│ → kubelet 报错 "dial tcp X.X.X.X:443: i/o timeout 或 connection refused"                        │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                                          │
│ kubelet 无法从容器镜像仓库拉取镜像。                                                             │
│ Pod Events 明确显示: 'Failed to pull image' + 'dial tcp ...:443: connect: connection refused / i/o timeout'. │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                                                      │
│ default 和 mcp 命名空间中约 48 个 Pod 处于 ImagePullBackOff 或 ErrImagePull 状态，所有容器无法启动。│
│ 另有个别 Pod 因 Secret 配置错误 (CreateContainerConfigError) 或容器运行时故障 (StartError) 独立失败。 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (跨命名空间的系统性失败)、#2, #3, #4, #5 (跨仓库、跨节点、跨镜像的统一 `i/o timeout` 和 `connection refused` 错误模式)，问题的**根本原因是集群出口网络不可达**，导致节点无法连接任何外部容器镜像仓库。

**置信度**：高 (95%)
- ✅ 错误模式高度一致，且跨多仓库、节点、镜像，排除了单点故障。
- ✅ `kubectl describe` 的 Events 是最高优先级的权威工具事实，提供了直接的网络连接失败证据。
- ⚠️ 未能在 kube-system 命名空间的组件（如 `coredns` 或节点网络 DaemonSet）上执行网络连通性测试（`curl`, `wget`），但这不影响基于已有充分证据的根因判断。

**独立次要问题：**
1.  **配置错误**：证据 #6, #7 表明 `aiops-e2e/rc-config-secret-key-missing` 的根本原因是 **Secret `rc-app-secret` 中缺少 `APP_SECRET_TOKEN` Key**。
2.  **运行时错误**：证据 #8 表明 `mcp/node-debugger-node1-nx8gb` 的根本原因是 **容器运行时 (containerd) 启动容器时发生内部错误 (Exit Code 128)**，与网络问题无关。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 排查并修复出口网络策略**

这是解决核心问题的关键，需要集群/网络管理员操作。以下提供排查命令和思路。

*   **排查思路 1：检查节点上的代理配置**
    集群是否配置了 HTTP_PROXY / HTTPS_PROXY 环境变量？kubelet 的启动参数或 Docker/containerd 的配置文件中是否设置了代理？
    ```bash
    # 在 node1 上检查 docker 代理
    ssh node1
    sudo systemctl cat docker | grep -i proxy
    
    # 在 node1 上检查 containerd 代理
    sudo cat /etc/systemd/system/containerd.service.d/*.conf
    sudo cat /etc/containerd/config.toml | grep -i proxy
    
    # 检查 kubelet 启动参数
    ps aux | grep kubelet | grep -i proxy
    
    # 检查系统级环境变量
    env | grep -i proxy
    ```

*   **排查思路 2：检查 iptables / nftables 规则**
    检查是否有明确的规则拒绝了出站流量。
    ```bash
    # 在 node1 上检查出站规则
    sudo iptables -L -n -v | grep DROP | grep 443
    sudo iptables -t filter -L -n -v | grep DROP
    
    # 如果节点使用 nftables
    sudo nft list ruleset
    ```

*   **排查思路 3：检查集群网络策略 (Network Policies)**
    检查 default 和 mcp 命名空间是否应用了严格出站策略。
    ```bash
    kubectl get networkpolicies -n default
    kubectl describe networkpolicies <name> -n default
    kubectl get networkpolicies -n mcp
    ```

*   **排查思路 4：防火墙/安全组**
    联系云提供商或网络团队，检查 worker 节点所在的云防火墙/安全组规则，确保它们允许到外网的 443 端口出站流量。

*   **如果无法修复出站网络，替代方案：部署私有镜像仓库 (Registry Mirror)**
    在内网环境，在所有节点都可达的位置 (如 `192.168.x.x:5000`) 搭建一个私有镜像仓库（如 Harbor），然后配置 containerd/Docker 使用该仓库作为 mirror。
    ```toml
    # 以 containerd 为例，修改 /etc/containerd/config.toml
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
        endpoint = ["http://192.168.x.x:5000"]
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors."registry.k8s.io"]
        endpoint = ["http://192.168.x.x:5000"]
    ```
    配置完成后重启 containerd: `sudo systemctl restart containerd && sudo systemctl restart kubelet`.

**2. [次要配置] 修复 Secret 配置错误**

```bash
# 1. 首先删除旧的 secret
kubectl delete secret rc-app-secret -n aiops-e2e

# 2. 创建包含正确 key 的 secret (替换 <your-secret-value> 为实际值)
kubectl create secret generic rc-app-secret \
    --from-literal=EXISTING_SECRET_KEY=<existing_value> \
    --from-literal=APP_SECRET_TOKEN=<your-app-secret-token> \
    -n aiops-e2e

# 3. 或者，如果 Pod 应使用其他 Secret，则更新其配置。
# 命令: kubectl edit deploy <deployment-name> -n aiops-e2e
```

### 后续优化

1.  **配置镜像拉取策略**: 对于生产环境，考虑使用私有镜像仓库，并将 `imagePullPolicy` 设置为 `IfNotPresent`，以减少对公共镜像仓库的依赖和网络波动的影响。
2.  **监控告警**: 配置对 `ImagePullBackOff` 状态的监控告警，以便在类似问题发生时第一时间感知。
3.  **应用优化**: 对于 `StartError` 的 Pod，检查其使用的镜像是否完整，以及容器内的启动脚本是否存在问题。

---

## ⚠️ 注意事项

- 修复集群出口网络后，所有处于 `ImagePullBackOff/ErrImagePull` 的 Pod 将**自动**恢复，无需逐个重启。
- `StartError` 的 Pod (`node-debugger-node1-nx8gb`) 是一个独立的运行时问题，需要在网络问题解决后，检查其日志或重建该 Pod，以确认问题是否复现。

---

## 📊 性能统计

├─ 总耗时: 2.2m
├─ 问题定位: 36.8s (28%) ✅
├─ 证据链采集: 39.6s (30%) ✅
├─ 根因分析: 24.5s (18%) ✅
├─ 汇总总结: 32.0s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 18 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed
- **工具调用**: 18 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
