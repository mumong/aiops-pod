======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: b03bc680e7b54811]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先做全局 Pod 状态扫描，看看集群中所有 Pod 的当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned pod list across all namespaces. 43+ pods shown; status mix: Running, Completed, ImagePullBackOff, ErrImagePull, CreateContainerConfigError, ContainerCreating. H
   💭 [问题定位] 让我获取更完整的 Pod 状态，尤其是异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Kubernetes 查询返回 51 个 Pod，全部为 Pending 状态。分布在 3 个 namespace（aiops-e2e, default, mcp）和 2 个 node（node1, node2）上。Pod 包括 DNS 测试、网络测试、registry 连接测试、节点调试等多种用途。
key_facts: ["所有 51 个 Pod 的 STATUS 均为 'Pending'",
   💭 [问题定位] 看起来查询只显示了 phase=Pending 的 Pod。让我获取更完整的状态信息，包括具体 STATUS 字段。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 all pods across namespaces. 总计 117 个 pod, 其中 Running=59, Pending=51, Succeeded=5, Failed=2, Evicted=1。大量 Pending 和 Failed/Evicted pod 集中在 default(17 Pending), mcp(20 Pendin
   💭 [问题定位] 现在我需要更详细的异常 Pod 状态信息，包括 kubectl get -o wide 的 STATUS 列。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 raw_preview shows 52 pods in Pending/Failed status across namespaces aiops-e2e, default, mcp, xnet. Dominant issues: ImagePullBackOff and ErrImagePull for images like busybox:1.36.1, busybox:1.36, cur
   💭 [问题定位] 很好，现在我来获取更准确的状态信息。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster: 共117个Pod（raw_preview显示约59行，含部分截断）。Running 59个，异常48个：ImagePullBackOff 约14个、ErrImagePull 约12个、CreateContainerConfigError 1个、ContainerCreating 1个（test-reg-connect-17793974
   💭 [问题定位] 现在我需要查看 mcp namespace 的异常 Pod 情况，因为之前查询显示 mcp 也有大量异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl get pods (all namespaces) returned 33 rows: 1 Running (mcp-server-manager), 1 Completed (node-debugger-node1-hzpmz), 31 abnormal. Status breakdown: ErrImagePull=14, ImagePullBackOff=16, StartE
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl get pods --all-namespaces (or specific ns): 32 pods listed. 30 Running, 2 Completed (observability-kibana-65d7c45f6d-7zc9l, pre-install-observability-kibana-dpzvp). No CrashLoopBackOff, ImageP
   💭 [问题定位] 我注意到 xnet/observability-kibana 之前显示为 Failed/Evicted，让我查一下这个异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                    READY   STATUS      RESTARTS   AGE   IP              NODE     NOMINATED NODE   READINESS GATES   LABELS
observability-kibana-65d7c45f6d-7zc9l   0/1     Complete
   💭 [问题定位] 好的，这个 Pod 实际上是 Completed 状态，之前查询的 Failed/Evicted 信息可能是旧数据。让我再看看 mcp 的异常 Pod 详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ✅ [问题定位] 完成 (1m 4.1s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '镜像仓库无法访问或镜像不存在（私有仓库认证/网络问题）', 'probability': 'high', 'reason': '大量 Pod 使用 busybox, curl, alpine, registry.k8s.io 等公共镜像，均在 node1/node2 上出现 ImagePullBackOff/ErrImagePull，涉及多个命名空间，可能是节点访问外部镜像仓库的网络/认证问题'}, {'scenario': 'Harbor/私有 Registry 配置错误或不可用', 'probability': 'medium', 'reason': '部分 registry 连接测试 Pod 均失败（registry-conn-*, registry-connect-*），且 xnet/observability-kibana 使用私有 registry 也 Failed'}, {'scenario': 'Secret 配置错误导致 ConfigError', 'probability': 'low', 'reason': 'aiops-e2e/rc-config-secret-key-missing 明确处于 CreateContainerConfigError，表明 Secret 配置缺失，但仅影响 1 个 Pod'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "pod", "name": "node-debugger-node1-nx8gb", "namespace": "mcp"}]
   reasoning=当前环境中存在大量异常 Pod（至少 48 个），主要为 Pending 状态，根因是 ImagePullBackOff（约 14+ 个）和 ErrImagePull（约 12+ 个），对应 L3 层 Image/Network 问题。同时存在 1 个 CreateContainerConfigError（rc-config-secret-key-missing）属于 L4 ConfigError，以及 1 个 Failed Pod（node-debugger-node1-nx8gb StartError）和 1 个 Evicted Pod（observability-kibana-65d7c45f6d-7zc9l，但已 Completed 非当前异常）。大量 DNS/registry/network 测试 Pod 无法拉取镜像（busybox, curl, alpine, registry.k8s.io 等），涉及 node1 和 node2 两个节点。kube-system 组件全部 Running 正常。核心问题是镜像拉取失败导致的 Pending/ImagePullBackOff/ErrImagePull，归为 L3 层。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "Image/Network", "confidence": 0.92, "reasoning": "当前环境中存在大量异常 Pod（至少 48 个），主要为 Pending 状态，根因是 ImagePullBackOff（约 14+ 个）和 ErrImagePull（约 12+ 个），对应 L3 层 Image/Network 问题。同时存在 1 个 CreateContainerConfigError（rc-config-secret-key-missing）属于 L4 ConfigError，以及 1 个 Failed Pod（node-debugger-node1-nx8gb StartError）和 1 个 Evicted Pod（observability-kibana-65d7c45f6d-7zc9l，但已 Completed 非当前异常）。大量 DNS/registry/network 测试 Pod 无法拉取镜像（busybox, curl, alpine, registry.k8s.io 等），涉及 node1 和 node2 两个节点。kube-system 组件全部 Running 正常。核心问题是镜像拉取失败导致的 Pending/ImagePullBackOff/ErrImagePull，归为 L3 层。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-dig", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-reg-connect-1779397479", "namespace": "default", "status": "ContainerCreating"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-test-1779397511", "namespace": "default", "status": "ErrImagePull"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "pod", "name": "node-debugger-node1-nx8gb", "namespace": "mcp"}], "possible_scenarios": [{"scenario": "镜像仓库无法访问或镜像不存在（私有仓库认证/网络问题）", "probability": "high", "reason": "大量 Pod 使用 busybox, curl, alpine, registry.k8s.io 等公共镜像，均在 node1/node2 上出现 ImagePullBackOff/ErrImagePull，涉及多个命名空间，可能是节点访问外部镜像仓库的网络/认证问题"}, {"scenario": "Harbor/私有 Registry 配置错误或不可用", "probability": "medium", "reason": "部分 registry 连接测试 Pod 均失败（registry-conn-*, registry-connect-*），且 xnet/observability-kibana 使用私有 registry 也 Failed"}, {"scenario": "Secret 配置错误导致 ConfigError", "probability": "low", "reason": "aiops-e2e/rc-config-secret-key-missing 明确处于 CreateContainerConfigError，表明 Secret 配置缺失，但仅影响 1 个 Pod"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "default", "name": "curl-test-1779397511"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "default", "name": "test-reg-connect-1779397479"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g4", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "default", "name": "curl-test-1779397511"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "default", "name": "test-reg-connect-1779397479"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g4", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 28, "ErrImagePull": 20}, "total_abnormal": 48, "selected_rows": ["aiops-e2e         rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0              40m     172.16.166.130   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff             0              10h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              5h36m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ErrImagePull                 0              4h37m   172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              9h      172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff             0              116m    172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff             0              122m    172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ImagePullBackOff             0              122m    172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ErrImagePull                 0              10h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff             0              7h49m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ErrImagePull                 0              121m    172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull                 0              4h43m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              8h      172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull                 0              9h      172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull                 0              6h19m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ErrImagePull                 0              149m    172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull                 0              7h18m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-conn-test-evidence                         0/1     ErrImagePull                 0              55m     172.16.104.22    node2    <none>           <none>            run=registry-conn-test-evidence", "default           registry-connect-test                               0/1     ErrImagePull                 0              9h      172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              10h     172.16.166.185   node1    <none>           <none>            run=test-net-1779360704"], "raw_ref": "/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 92%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将按照既有 evidence_plan 执行工具调用。先从 critical 级别工具开始，逐步采集证据。由于工具调用无依赖关系，可以并行执行多组。

先执行 g1-state、g2-representative、g2-image-check 等核心项：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          40m (x12 over 42m)    kubelet            Error: cou
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dig-tool
namespace: default
creationTimestamp: 2026-05-21T15:28:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
serviceAcco
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool is in ImagePullBackOff (Waiting, Reason: ImagePullBackOff, Restart Count: 0). Image registry.k8s.io/e2e-test-ima
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-secret-key-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-21T20:24:08Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalize
   💭 [证据链采集] g1-state、g1-secret-check、g2-representative、g2-image-check 已完成。现在继续执行 g2-cross-node、g2-mcp-check 和 g2-events：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "aiops-e2e   40m         Warning   Failed      pod/rc-config-secret-key-missing            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\naiop
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-test (ns: mcp) on node2 (10.2.0.50) is Pending, container in Waiting(ErrImagePull). Repeated Failed to pull busybox:1.36.1 from docker.io — all attempts hit network errors: i/o timeou
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-resolve-test (namespace: default, node: node2/10.2.0.50) is Pending. Container dns-resolve-test (image busybox:1.36.1, args: nslookup registry-1.docker.io) is in ImagePullBackOff (State Waitin
   💭 [证据链采集] 现在执行 g3-state、g4-state、g4-logs：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Error from server (BadRequest): previous terminated container \"debugger\" in pod \"node-debugger-node1-nx8gb\" not found\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-reg-connect-1779397479
namespace: default
node: node2/10.2.0.50
status: Terminating (lasts 42s)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: 8d1
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 所有工具调用已完成。现在对采集到的证据进行整理和总结。

---

## 证据采集结论

### ✅ 已采集证据

#### 异常组 g1 — CreateContainerConfigError（Pod: rc-config-secret-key-missing, aiops-e2e）
- **g1-state** ✅：`kubectl describe` 确认 Pod 处于 `CreateContainerConfigError`，错误原因：`couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`
- **g1-secret-check** ✅：`kubectl get yaml` 确认 Pod 引用了 Secret `rc-app-secret` 中的键 `APP_SECRET_TOKEN`，但该 Secret 中不包含此 key（ConfigError）

#### 异常组 g2 — ImagePullBackOff/ErrImagePull（主异常组，48 个 Pod）
- **g2-representative** ✅：`kubectl describe pod dig-tool`（node1）确认容器 `dig-tool` 使用镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，Reason=`ImagePullBackOff`，Message=`Back-off pulling image`
- **g2-image-check** ✅：`kubectl get yaml dig-tool` 确认镜像为 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，**无 `imagePullSecrets`**
- **g2-cross-node** ✅：`kubectl describe pod dns-resolve-test`（node2）使用镜像 `busybox:1.36.1`，关键证据：**kubelet 拉取 docker.io 镜像时 i/o timeout（多个 IP）+ connection refused（93.179.102.140:443）+ pull QPS exceeded**
- **g2-mcp-check** ✅：`kubectl describe pod connectivity-test`（mcp/ns, node2）使用镜像 `busybox:1.36.1`，关键证据：**x83 次 Failed 事件，全部为 i/o timeout 或 connection refused 到 registry-1.docker.io**
- **g2-events** ✅：全集群 Warning Events 确认大量 `Failed to pull image` + `ErrImagePull` + `ImagePullBackOff` 事件，均指向 docker.io 和 registry.k8s.io 网络不可达

#### 异常组 g3 — ContainerCreating（Pod: test-reg-connect-1779397479, default）
- **g3-state** ✅：Pod 当前处于 **Terminating** 状态（最后 42s），之前卡在 ContainerCreating，镜像为 `busybox:1.36.1`，持续 Pulling 但已进入终止流程

#### 异常组 g4 — StartError（Pod: node-debugger-node1-nx8gb, mcp）
- **g4-state** ✅：Pod 状态 `Failed`，Reason=`StartError`，Exit Code=128。关键错误信息：**`exec: "curl": executable file not found in $PATH: unknown`** — 容器镜像 `busybox:1.36` 中没有 `curl` 命令，但 Pod 的 command 是 `curl`
- **g4-logs** ✅：`kubectl logs --previous` 返回 "previous terminated container not found"（符合预期，未成功启动过）

### ⚠️ 冲突/负向证据
- **rc-config-secret-key-missing** 的 `imagePullPolicy=Never` 镜像 `busybox:1.36` 在本地存在（因为 node-debugger-node1-nx8gb 成功拉取了该镜像），因此它的 ImagePullPolicy=Never 没有触发拉取问题，它的问题是 Secret 缺少 key 而非镜像拉取问题
- **test-reg-connect-1779397479** 当前状态是 Terminating 而非 ContainerCreating——这反映该 Pod 已被清理

### 根因判断
1. **主因（L3 镜像拉取失败）**：大量 Pod（48 个）无法从 `docker.io`（busybox:1.36.1）和 `registry.k8s.io`（jessie-dnsutils:1.0）拉取镜像。**node1 和 node2 均无法访问外部镜像仓库**，具体表现为：
   - `i/o timeout`（到多个 docker.io registry IP）
   - `connection refused`（93.179.102.140:443）
   - `pull QPS exceeded`
   - 非认证问题，是**集群出口网络不通**，需要检查节点的网络出口/NAT/代理配置或防火墙规则

2. **g1 ConfigError（独立问题）**：`rc-config-secret-key-missing` 拉取镜像不需要网络（imagePullPolicy=Never），故障是 Secret `rc-app-secret` 缺少 `APP_SECRET_TOKEN` 键

3. **g4 StartError（独立问题）**：`node-debugger-node1-nx8gb` 镜像 `busybox:1.36` 不包含 `curl` 命令，但 command 要求执行 `curl`，导致 `executable file not found`
   ✅ [证据链采集] 完成 (52.2s)
   📤 → 下游数据: evidence_items=18/18
   evidence_analysis={"evidence_plan":[{"id":"g1-state","description":"验证 g1(CreateContainerConfigError): rc-config-secret-key-missing 当前状态和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-config-secret-key-missing","tool_args":{"kind":"pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"获取 CreateContainerConfigError 的具体错误事件和容器状态","evidence_type":"pod_status","target_scope":"Pod/aiops-e2e/rc-config-secret-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-secret-check","description":"检查 rc-config-secret-key-missing 引用的 Secret 是否存在","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-config-secret-key-missing -o yaml | grep -A5 -i secret","tool_args":{"kind":"pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"确认 Pod spec 中引用的 Secret 是否存在","evidence_type":"configuration","target_scope":"Pod/aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-representative","description":"验证 g2(ImagePullFailed): 选择代表 Pod 查看 Events 和镜像信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dig-tool","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"获取 ImagePullBackOff 代表 Pod 的 Events，查看具体拉取错误原因","evidence_type":"pod_events","target_scope":"Pod/default/dig-tool","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-image-check","description":"检查代表 Pod 的镜像地址和 imagePullSecrets","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n default dig-tool -o yaml | grep -E 'image:|imagePullSecrets|name:'","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"查看 Pod 使用的镜像地址和是否有 imagePullSecrets","evidence_type":"configuration","target_scope":"Pod/default/dig-tool","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-cross-node","description":"验证 node2 上的代表 Pod 是否同样镜像拉取失败","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n default dns-resolve-test","tool_args":{"kind":"pod","name":"dns-resolve-test","namespace":"default"},"purpose":"验证 node2 上 Pod 的 Events 是否与 node1 一致","evidence_type":"pod_events","target_scope":"Pod/default/dns-resolve-test","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-mcp-check","description":"验证 mcp namespace 代表 Pod 的镜像拉取问题","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp connectivity-test","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp"},"purpose":"验证 mcp namespace 的 Pod 是否与其他 namespace 异常一致","evidence_type":"pod_events","target_scope":"Pod/mcp/connectivity-test","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-events","description":"查看集群级 Events，聚焦 ImagePullBackOff/ErrImagePull","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector type=Warning | grep -i -E 'Failed|ImagePull|ErrImage|BackOff' | head -30","tool_args":{},"purpose":"获取全集群的 Warning Events，聚焦镜像拉取失败事件","evidence_type":"cluster_events","target_scope":"Cluster","acceptable_tools":[],"counts_for_completeness":true},{"id":"g3-state","description":"验证 g3(ContainerCreating): test-reg-connect-1779397479 当前状态和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n default test-reg-connect-1779397479","tool_args":{"kind":"pod","name":"test-reg-connect-1779397479","namespace":"default"},"purpose":"确认 ContainerCreating 是否已恢复正常或仍卡住","evidence_type":"pod_status","target_scope":"Pod/default/test-reg-connect-1779397479","acceptable_tools":[],"counts_for_completeness":true},{"id":"g4-state","description":"验证 g4(StartError): node-debugger-node1-nx8gb 当前状态和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp node-debugger-node1-nx8gb","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"获取 StartError 的具体错误原因","evidence_type":"pod_status","target_scope":"Pod/mcp/node-debugger-node1-nx8gb","acceptable_tools":[],"counts_for_completeness":true},{"id":"g4-logs","description":"查看 StartError Pod 的日志","level":"important","tool":"run_bash_command","command":"kubectl logs -n mcp node-debugger-node1-nx8gb --previous 2>&1 || kubectl logs -n mcp node-debugger-node1-nx8gb 2>&1","tool_args":{},"purpose":"获取 StartError Pod 容器日志排查启动失败原因","evidence_type":"container_logs","target_scope":"Pod/mcp/node-debugger-node1-nx8gb","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          40m (x12 over 42m)    kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: e50889f651dff0ebd5a4ed7212a0f9deacd4b503f1ae265a36959b8e7c2ff9c4\n                  cni.projectcalico.org/podIP: 172.16.166.130/32\n                  cni.projectcalico.org/podIPs: 172.16.166.130/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-pbw78:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-r\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dig-tool\nnamespace: default\ncreationTimestamp: 2026-05-21T15:28:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dig-tool: image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1 || host registry-1.docker.io 2>&1 || echo DNS_CHECK_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dig-tool: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\nvolumes:\n- {\"name\": \"kube-api-access-lcm2n\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool is in ImagePullBackOff (Waiting, Reason: ImagePullBackOff, Restart Count: 0). Image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 fails to pull due to i/o timeout dialing registry endpoints (us-west2-docker.pkg.dev, europe-west2-docker.pkg.dev) on TCP 443 across multiple regions. 5 Failed events (some repeated x2/x5/x8 over 5h3m) and 667 BackOff events in 5h31m. Pod has IP 172.16.166.157, Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True. QoS: BestEffort.\nkey_facts: [\"pod: dig-tool\", \"namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: dig-tool\", \"image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"State: Waiting (ImagePullBackOff)\", \"Ready: False\", \"Restart Count: 0\", \"Events: Warning Failed - Failed to pull image (i/o timeout to registry endpoints on TCP 443)\", \"Events: Normal BackOff x667 over 5h31m - Back-off pulling image\", \"Pod IP: 172.16.166.157\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\", \"QoS Class: BestEffort\"]\nmissing: [\"Container ID and Image ID are empty (image neve\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T20:24:08Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-config-secret-key-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=CreateContainerConfigError exitCode=None\n  message: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\nvolumes:\n- {\"name\": \"kube-api-access-pbw78\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"aiops-e2e   40m         Warning   Failed      pod/rc-config-secret-key-missing            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\\naiops-e2e   8m49s       Warning   Failed      pod/test-dns-1779360358                     (combined from similar events): Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 31.13.96.195:443: i/o timeout\\ndefault     53s         Warning   Failed      pod/curl-test-1779397511                    Failed to pull image \\\"appropriate/curl\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/appropriate/curl:latest\\\": failed to resolve reference \\\"docker.io/appropriate/curl:latest\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/appropriate/curl/manifests/latest\\\": read tcp 10.2.0.49:45750->23.20.95.219:443: read: connection reset by peer\\ndefault     38s         Warning   Failed      pod/curl-te\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/005-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_describe","data":"Pod connectivity-test (ns: mcp) on node2 (10.2.0.50) is Pending, container in Waiting(ErrImagePull). Repeated Failed to pull busybox:1.36.1 from docker.io — all attempts hit network errors: i/o timeout (multiple IPs) and connection refused (93.179.102.140). 87 Pulling events over 9h, 83 Failed retries. PodIP: 172.16.104.3 via Calico. QoS: BestEffort.\nkey_facts: [\"name: connectivity-test\", \"namespace: mcp\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container state: Waiting (Reason: ErrImagePull)\", \"Ready: False\", \"image: busybox:1.36.1\", \"container ID: empty (not pulled)\", \"Events: Warning Failed x83 over 9h — kubelet Error: ErrImagePull\", \"Events: Warning Failed (58m,48m,37m,26m,20m,8m47s,17s) — all i/o timeout or connection refused to registry-1.docker.io\", \"Events: Normal Pulling x87 over 9h\", \"podIP: 172.16.104.3/32 (Calico CNI)\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary says 'Failed 17s (x83 over 9h)' as the last Failed event; raw_preview also shows a more recent 'Failed 17s' (DeadlineExceeded dial tcp 103.200.31.172:443: i/o timeout) not captured in summary — raw_preview used\"]\nmissing: [\"start time: Thu, 21 May 2026 11:38:46 +0000\", \"pod args: curl -v --connect-timeout 10 https://registry-1.docker.io/v2/\", \"service account: default\", \"conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\", \"Tolerations: also includes node.kubernetes.io/unreachable:NoExecute\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dns-resolve-test (namespace: default, node: node2/10.2.0.50) is Pending. Container dns-resolve-test (image busybox:1.36.1, args: nslookup registry-1.docker.io) is in ImagePullBackOff (State Waiting, Reason: ImagePullBackOff). Kubelet repeatedly fails to pull the image from docker.io with i/o timeouts to multiple registry IPs (108.160.170.39, 67.228.102.32, 69.63.176.15, 108.160.166.42, 168.143.171.189), one connection refused (93.179.102.140:443), and one pull QPS exceeded. BackOff event occurred x14 over 115m. Error: ErrImagePull (x12 over 115m) and ImagePullBackOff (x4 over 115m) also reported. Pod IP: 172.16.104.1. Calico CNI annotations present. Ready: False, Restart Count: 0.\nkey_facts: [\"Pod: dns-resolve-test, namespace: default, node: node2/10.2.0.50\", \"Status: Pending\", \"Container image: busybox:1.36.1\", \"Container args: nslookup registry-1.docker.io\", \"Container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False, Restart Count: 0\", \"Pod IP: 172.16.104.1\", \"Kubelet Failed to pull image - DeadlineExceeded - i/o timeout to multiple docker.io registry IPs (108.160.170.39:443, 67.228.102.32:443, 69.63.176.15:443, 108.160.166.42:443, 168.143.171.189:443)\", \"Kubelet Failed: connection refused to 93.179.102.140:443\", \"Kubelet Failed: pull QPS exceeded\", \"Error: ErrImagePull (x12 over 115m)\", \"Error: ImagePullBackOff (x4 over 115m)\", \"BackOff pulling image (x14 over 115m)\"]\nconflicts: [\"current_summary says 'Warning Failed 19m (x12 over 115m) kubelet Error: ErrImagePull' but raw_preview shows the Pulling event at 19m (x12 over 123m) and Failed events at different ages - no direct contradiction, raw_preview used for precise detail\"]\nmissing: [\"No missing critical info; all key facts captured from raw_preview\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Error from server (BadRequest): previous terminated container \\\"debugger\\\" in pod \\\"node-debugger-node1-nx8gb\\\" not found\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/008-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/008-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/008-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-reg-connect-1779397479\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Terminating (lasts 42s)\n关键诊断行:\nAnnotations:               cni.projectcalico.org/containerID: 8d19b260b675886ecba6aed46914f1ca201159ee38f6e58a8345a8e3639ed821\n                           cni.projectcalico.org/podIP: 172.16.104.60/32\n                           cni.projectcalico.org/podIPs: 172.16.104.60/32\n                           k8s.v1.cni.cncf.io/network-status:\n                           k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nTermination Grace Period:  30s\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-reg-connect-1779397479:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-7g257:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason          Age    From               Message\n  ----    ------          ----   ----               -------\n  Normal  Scheduled       2m11s  default-scheduler  Successfully assigned default/test-reg-connect-1779397479 to node2\n  Normal  AddedInterface  2m11s  multus             Add eth0 [172.16.104.60/32] from k8s-pod-network\n  Normal  Pulling         2m11s  kubelet            Pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/009-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/009-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/009-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/010-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/010-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b03bc680e7b54811/tools/010-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"所有工具调用已完成。现在对采集到的证据进行整理和总结。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n#### 异常组 g1 — CreateContainerConfigError（Pod: rc-config-secret-key-missing, aiops-e2e）\n- **g1-state** ✅：`kubectl describe` 确认 Pod 处于 `CreateContainerConfigError`，错误原因：`couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`\n- **g1-secret-check** ✅：`kubectl get yaml` 确认 Pod 引用了 Secret `rc-app-secret` 中的键 `APP_SECRET_TOKEN`，但该 Secret 中不包含此 key（ConfigError）\n\n#### 异常组 g2 — ImagePullBackOff/ErrImagePull（主异常组，48 个 Pod）\n- **g2-representative** ✅：`kubectl describe pod dig-tool`（node1）确认容器 `dig-tool` 使用镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，Reason=`ImagePullBackOff`，Message=`Back-off pulling image`\n- **g2-image-check** ✅：`kubectl get yaml dig-tool` 确认镜像为 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，**无 `imagePullSecrets`**\n- **g2-cross-node** ✅：`kubectl describe pod dns-resolve-test`（node2）使用镜像 `busybox:1.36.1`，关键证据：**kubelet 拉取 docker.io 镜像时 i/o timeout（多个 IP）+ connection refused（93.179.102.140:443）+ pull QPS exceeded**\n- **g2-mcp-check** ✅：`kubectl describe pod connectivity-test`（mcp/ns, node2）使用镜像 `busybox:1.36.1`，关键证据：**x83 次 Failed 事件，全部为 i/o timeout 或 connection refused 到 registry-1.docker.io**\n- **g2-events** ✅：全集群 Warning Events 确认大量 `Failed to pull image` + `ErrImagePull` + `ImagePullBackOff` 事件，均指向 docker.io 和 registry.k8s.io 网络不可达\n\n#### 异常组 g3 — ContainerCreating（Pod: test-reg-connect-1779397479, default）\n- **g3-state** ✅：Pod 当前处于 **Terminating** 状态（最后 42s），之前卡在 ContainerCreating，镜像为 `busybox:1.36.1`，持续 Pulling 但已进入终止流程\n\n#### 异常组 g4 — StartError（Pod: node-debugger-node1-nx8gb, mcp）\n- **g4-state** ✅：Pod 状态 `Failed`，Reason=`StartError`，Exit Code=128。关键错误信息：**`exec: \"curl\": executable file not found in $PATH: unknown`** — 容器镜像 `busybox:1.36` 中没有 `curl` 命令，但 Pod 的 command 是 `curl`\n- **g4-logs** ✅：`kubectl logs --previous` 返回 \"previous terminated container not found\"（符合预期，未成功启动过）\n\n### ⚠️ 冲突/负向证据\n- **rc-config-secret-key-missing** 的 `imagePullPolicy=Never` 镜像 `busybox:1.36` 在本地存在（因为 node-debugger-node1-nx8gb 成功拉取了该镜像），因此它的 ImagePullPolicy=Never 没有触发拉取问题，它的问题是 Secret 缺少 key 而非镜像拉取问题\n- **test-reg-connect-1779397479** 当前状态是 Terminating 而非 ContainerCreating——这反映该 Pod 已被清理\n\n### 根因判断\n1. **主因（L3 镜像拉取失败）**：大量 Pod（48 个）无法从 `docker.io`（busybox:1.36.1）和 `registry.k8s.io`（jessie-dnsutils:1.0）拉取镜像。**node1 和 node2 均无法访问外部镜像仓库**，具体表现为：\n   - `i/o timeout`（到多个 docker.io registry IP）\n   - `connection refused`（93.179.102.140:443）\n   - `pull QPS exceeded`\n   - 非认证问题，是**集群出口网络不通**，需要检查节点的网络出口/NAT/代理配置或防火墙规则\n\n2. **g1 ConfigError（独立问题）**：`rc-config-secret-key-missing` 拉取镜像不需要网络（imagePullPolicy=Never），故障是 Secret `rc-app-secret` 缺少 `APP_SECRET_TOKEN` 键\n\n3. **g4 StartError（独立问题）**：`node-debugger-node1-nx8gb` 镜像 `busybox:1.36` 不包含 `curl` 命令，但 command 要求执行 `curl`，导致 `executable file not found`","collection_summary":"计划 10 项，实际采集 10 项，未采集 0 项，完整度 100%；其中真实环境证据 18/18 项，完整度 100%；实际执行工具 18 个，匹配计划 10 个，未规划证据 8 个","plan_total":10,"plan_collected":10,"plan_completeness":1.0,"environment_evidence_total":18,"environment_evidence_collected":18,"environment_evidence_completeness":1.0,"executed_tool_count":18,"matched_tool_count":10,"unplanned_tool_count":8,"evidence_inventory":[{"id":"g1-state","description":"验证 g1(CreateContainerConfigError): rc-config-secret-key-missing 当前状态和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-config-secret-key-missing","purpose":"获取 CreateContainerConfigError 的具体错误事件和容器状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-secret-check","description":"检查 rc-config-secret-key-missing 引用的 Secret 是否存在","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-config-secret-key-missing -o yaml | grep -A5 -i secret","purpose":"确认 Pod spec 中引用的 Secret 是否存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-representative","description":"验证 g2(ImagePullFailed): 选择代表 Pod 查看 Events 和镜像信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dig-tool","purpose":"获取 ImagePullBackOff 代表 Pod 的 Events，查看具体拉取错误原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-image-check","description":"检查代表 Pod 的镜像地址和 imagePullSecrets","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n default dig-tool -o yaml | grep -E 'image:|imagePullSecrets|name:'","purpose":"查看 Pod 使用的镜像地址和是否有 imagePullSecrets","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-cross-node","description":"验证 node2 上的代表 Pod 是否同样镜像拉取失败","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n default dns-resolve-test","purpose":"验证 node2 上 Pod 的 Events 是否与 node1 一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-mcp-check","description":"验证 mcp namespace 代表 Pod 的镜像拉取问题","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp connectivity-test","purpose":"验证 mcp namespace 的 Pod 是否与其他 namespace 异常一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-events","description":"查看集群级 Events，聚焦 ImagePullBackOff/ErrImagePull","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector type=Warning | grep -i -E 'Failed|ImagePull|ErrImage|BackOff' | head -30","purpose":"获取全集群的 Warning Events，聚焦镜像拉取失败事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-state","description":"验证 g3(ContainerCreating): test-reg-connect-1779397479 当前状态和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n default test-reg-connect-1779397479","purpose":"确认 ContainerCreating 是否已恢复正常或仍卡住","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g4-state","description":"验证 g4(StartError): node-debugger-node1-nx8gb 当前状态和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp node-debugger-node1-nx8gb","purpose":"获取 StartError 的具体错误原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g4-logs","description":"查看 StartError Pod 的日志","level":"important","tool":"run_bash_command","command":"kubectl logs -n mcp node-debugger-node1-nx8gb --previous 2>&1 || kubectl logs -n mcp node-debugger-node1-nx8gb 2>&1","purpose":"获取 StartError Pod 容器日志排查启动失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 10/10 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-state | critical | ✅ | kubectl_describe | 验证 g1(CreateContainerConfigError): rc-config-... | `kubectl describe pod -n aiops-e2e rc-config-secret-key-missing` |
   | g1-secret-check | critical | ✅ | kubectl_get_yaml | 检查 rc-config-secret-key-missing 引用的 Secret 是否存在 | `kubectl get pod -n aiops-e2e rc-config-secret-key-missing -o yaml | grep -A5 ...` |
   | g2-representa... | critical | ✅ | kubectl_describe | 验证 g2(ImagePullFailed): 选择代表 Pod 查看 Events 和镜像信息 | `kubectl describe pod -n default dig-tool` |
   | g2-image-check | critical | ✅ | kubectl_get_yaml | 检查代表 Pod 的镜像地址和 imagePullSecrets | `kubectl get pod -n default dig-tool -o yaml | grep -E 'image:|imagePullSecret...` |
   | g2-cross-node | important | ✅ | kubectl_describe | 验证 node2 上的代表 Pod 是否同样镜像拉取失败 | `kubectl describe pod -n default dns-resolve-test` |
   | g2-mcp-check | important | ✅ | kubectl_describe | 验证 mcp namespace 代表 Pod 的镜像拉取问题 | `kubectl describe pod -n mcp connectivity-test` |
   | g2-events | important | ✅ | kubectl_events | 查看集群级 Events，聚焦 ImagePullBackOff/ErrImagePull | `kubectl get events --all-namespaces --field-selector type=Warning | grep -i -...` |
   | g3-state | important | ✅ | kubectl_describe | 验证 g3(ContainerCreating): test-reg-connect-17... | `kubectl describe pod -n default test-reg-connect-1779397479` |
   | g4-state | important | ✅ | kubectl_describe | 验证 g4(StartError): node-debugger-node1-nx8gb ... | `kubectl describe pod -n mcp node-debugger-node1-nx8gb` |
   | g4-logs | important | ✅ | run_bash_command | 查看 StartError Pod 的日志 | `kubectl logs -n mcp node-debugger-node1-nx8gb --previous 2>&1 || kubectl logs...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (26.1s)
   📤 → 下游数据: root_cause=核心根因是集群两个工作节点（node1, node2）的出站网络无法到达外部镜像仓库。具体证据：(1) dig-tool(node1) 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 时报 i/o timeout dialing us-west2-docker.pkg.dev:443 和 europe-west2-docker.pkg.dev:443；(2) connectivity-test(node2) 拉取 busybox:1.36.1 时 83 次 Failed 全部为 i/o timeout 或 connection refused 到 registry-1.docker.io；(3) dns-resolve-test(node2) 拉取 busybox:1.36.1 时报多个 Docker Hub IP（108.160.170.39, 67.228.102.32 等）i/o timeout 和 93.179.102.140:443 connection refused 以及 pull QPS exceeded。同
... 截断，原始 738 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1 和 node2）到外部镜像仓库（docker.io 和 registry.k8s.io）的出站网络不可达，表现为 TCP 443 i/o timeout 和 connection refused，导致所有依赖公共镜像的 Pod 镜像拉取失败", "propagation": "节点出站网络不通 → kubelet 无法从 registry-1.docker.io 和 registry.k8s.io 拉取镜像 → 容器状态进入 ErrImagePull → 重试后进入 ImagePullBackOff → Pod 持续 Pending 无法启动", "direct_cause": "kubelet 在 node1 和 node2 上执行 'docker pull' 时，TCP 连接 registry-1.docker.io (31.13.96.195, 108.160.170.39 等多 IP) 和 registry.k8s.io (us-west2-docker.pkg.dev) 的 443 端口全部超时或连接被拒绝", "manifestation": "default/mcp/aiops-e2e 三个 Namespace 下 48+ 个 Pod（DNS 测试、网络测试、registry 测试、节点调试工具）统一处于 ImagePullBackOff/ErrImagePull/Pending，kube-system 组件（使用本地/私有镜像）正常运行"}
   rca_analysis={"phenomenon": "集群中存在 48+ 个异常 Pod，主要分布在 default(20)、mcp(29)、aiops-e2e(2) 三个 Namespace，跨 node1/node2 两个节点。异常类型分布：ImagePullBackOff ~28 个、ErrImagePull ~20 个（主异常组 g2-ImagePullFailed）、CreateContainerConfigError 1 个（g1）、StartError 1 个（g4）、ContainerCreating 转为 Terminating 1 个（g3）。kube-system 全部 Running 正常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "g1: rc-config-secret-key-missing CreateContainerConfigError — 找不到 Secret aiops-e2e/rc-app-secret 中的 APP_SECRET_TOKEN 键", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "g1 Pod 配置确认引用 Secret，且 imagePullSecrets 不存在", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe", "content": "g2 代表 Pod dig-tool: ImagePullBackOff, registry.k8s.io 镜像拉取 i/o timeout (us-west2/europe-west2)", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe", "content": "g2 代表 Pod connectivity-test (mcp/node2): ErrImagePull, 83 次 Failed, busybox:1.36.1 拉取 i/o timeout + connection refused", "relability": "高"}, {"id": "e5", "source": "kubectl_describe", "content": "g2 代表 Pod dns-resolve-test (node2): ImagePullBackOff, docker.io 多 IP i/o timeout + connection refused + pull QPS exceeded", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe", "content": "g3: test-reg-connect-1779397479 当前 Terminating, 之前 ContainerCreating, Pulling busybox:1.36.1 失败", "reliability": "高"}, {"id": "e7", "source": "kubectl_describe", "content": "g4: node-debugger-node1-nx8gb StartError — busybox:1.36 中无 curl 命令导致 exec 失败 Exit Code 128", "reliability": "高"}, {"id": "e8", "source": "run_bash_command", "content": "g4: kubectl logs --previous 返回 'previous terminated container not found'", "reliability": "高"}, {"id": "e9", "source": "layer_handoff_current_abnormal_summary", "content": "集群总计 117 Pod: Running=59, Pending=51, Succeeded=5, Failed=2, Evicted=1", "reliability": "高"}, {"id": "e10", "source": "run_bash_command (get_events)", "content": "全集群 Events 确认大量 Failed to pull image/i/o timeout/ErrImagePull/ImagePullBackOff", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning Failed 40m (x12 over 42m) kubelet Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret", "interpretation": "Pod rc-config-secret-key-missing 引用了 Secret rc-app-secret 中的 APP_SECRET_TOKEN 键，但该 Secret 中不存在该键，导致 CreateContainerConfigError"}, {"evidence_id": "e2", "raw_data": "Pod dig-tool: imagePullSecrets: <absent>, container image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "interpretation": "代表 Pod 无 imagePullSecrets 配置，公共镜像无需认证，排除 imagePullSecret 缺失问题"}, {"evidence_id": "e3", "raw_data": "Failed to pull image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 — i/o timeout dialing us-west2-docker.pkg.dev, europe-west2-docker.pkg.dev on TCP 443", "interpretation": "node1 从 registry.k8s.io 拉取镜像时 TCP 连接超时，表明节点到外部 registry 的网络出口存在连通性问题"}, {"evidence_id": "e4", "raw_data": "Warning Failed x83 over 9h — i/o timeout to registry-1.docker.io (multiple IPs), connection refused 93.179.102.140:443", "interpretation": "node2 上的 Pod connectivity-test 拉取 busybox:1.36.1 时全部失败，既有超时也有连接被拒绝，进一步确认节点出站到 Docker Hub 的网络不可用"}, {"evidence_id": "e5", "raw_data": "i/o timeout to 108.160.170.39:443, 67.228.102.32:443, 69.63.176.15:443, 108.160.166.42:443, 168.143.171.189:443; connection refused to 93.179.102.140:443; pull QPS exceeded", "interpretation": "node2 尝试连接多个 Docker Hub registry IP 全部超时，且出现 QPS 限制，表明节点出口网络完全无法到达 Docker Hub"}, {"evidence_id": "e6", "raw_data": "Pod test-reg-connect-1779397479: Terminating(42s), before ContainerCreating, Pulling busybox:1.36.1, no successful pull", "interpretation": "该 Pod 是新创建的测试 Pod，卡在 ContainerCreating 后进入 Terminating，印证镜像拉取持续失败"}, {"evidence_id": "e7", "raw_data": "failed to create containerd task: OCI runtime create failed: exec: \"curl\": executable file not found in $PATH: unknown", "interpretation": "Pod node-debugger-node1-nx8gb 使用 busybox:1.36 镜像，但 command 设置为 'curl'，而 busybox 镜像不包含 curl 命令，导致容器启动失败 StartError"}, {"evidence_id": "e8", "raw_data": "Error from server (BadRequest): previous terminated container not found", "interpretation": "容器从未成功启动过，因此没有 previous 日志可获取，与 StartError 状态一致"}, {"evidence_id": "e9", "raw_data": "total=117, Running=59, Pending=51, Succeeded=5, Failed=2, Evicted=1", "interpretation": "集群整体健康度较低：43.6% 的 Pod 处于异常状态（Pending/Failed/Evicted），其中绝大多数是镜像拉取失败"}, {"evidence_id": "e10", "raw_data": "Events: Warning Failed (i/o timeout), Warning Failed (connection refused), Warning Failed (pull QPS exceeded), Normal BackOff (x667 in 5h31m for dig-tool)", "interpretation": "全集群统一模式：所有镜像拉取失败均因节点无法通过 TCP 443 连接到外部 registry (docker.io, registry.k8s.io) 导致，非个别 Pod 配置问题"}], "causal_chain": {"root_cause": "集群节点（node1 和 node2）到外部镜像仓库（docker.io 和 registry.k8s.io）的出站网络不可达，表现为 TCP 443 i/o timeout 和 connection refused，导致所有依赖公共镜像的 Pod 镜像拉取失败", "propagation": "节点出站网络不通 → kubelet 无法从 registry-1.docker.io 和 registry.k8s.io 拉取镜像 → 容器状态进入 ErrImagePull → 重试后进入 ImagePullBackOff → Pod 持续 Pending 无法启动", "direct_cause": "kubelet 在 node1 和 node2 上执行 'docker pull' 时，TCP 连接 registry-1.docker.io (31.13.96.195, 108.160.170.39 等多 IP) 和 registry.k8s.io (us-west2-docker.pkg.dev) 的 443 端口全部超时或连接被拒绝", "manifestation": "default/mcp/aiops-e2e 三个 Namespace 下 48+ 个 Pod（DNS 测试、网络测试、registry 测试、节点调试工具）统一处于 ImagePullBackOff/ErrImagePull/Pending，kube-system 组件（使用本地/私有镜像）正常运行"}, "root_cause": "核心根因是集群两个工作节点（node1, node2）的出站网络无法到达外部镜像仓库。具体证据：(1) dig-tool(node1) 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 时报 i/o timeout dialing us-west2-docker.pkg.dev:443 和 europe-west2-docker.pkg.dev:443；(2) connectivity-test(node2) 拉取 busybox:1.36.1 时 83 次 Failed 全部为 i/o timeout 或 connection refused 到 registry-1.docker.io；(3) dns-resolve-test(node2) 拉取 busybox:1.36.1 时报多个 Docker Hub IP（108.160.170.39, 67.228.102.32 等）i/o timeout 和 93.179.102.140:443 connection refused 以及 pull QPS exceeded。同\n... 截断，原始 738 字符", "root_cause_summary": "核心根因是集群两个工作节点（node1, node2）的出站网络无法到达外部镜像仓库。具体证据：(1) dig-tool(node1) 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 时报 i/o timeout dialing us-west2-docker.pkg.dev:443 和 europe-west2-docker.pkg.dev:443；(2) connectivity-test(node2) 拉取 busybox:1.36.1 时 83 次 Failed 全部为 i/o timeout 或 connection refused 到 registry-1.docker.io；(3) dns-resolve-test(node2) 拉取 busybox:1.36.1 时报多个 Docker Hub IP（108.160.170.39, 67.228.102.32 等）i/o timeout 和 93.179.102.140:443 connection refused 以及 pull QPS exceeded。同\n... 截断，原始 738 字符", "confidence": 0.95, "confidence_reason": "直接证据充分：通过 kubectl describe 在 node1 和 node2 上分别采集了多个代表 Pod 的 Events，明确显示 i/o timeout 和 connection refused 到外部 registry 的多个 IP，且涉及不同镜像（busybox, registry.k8s.io, curl, alpine）和不同命名空间，排除个别配置问题。g1/g4 各自有明确的错误消息作为直接证据。因果链完整清晰。", "primary_runbooks": [], "alternative_causes": [{"cause": "镜像地址或 tag 不存在（私有镜像仓库问题）", "probability": "low", "reason": "涉及的镜像均为公共镜像（busybox:1.36.1, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, appropriate/curl, alpine:3.18），且 kubelet Events 明确报告网络超时而非镜像不存在"}, {"cause": "imagePullSecret 缺失或认证失败", "probability": "low", "reason": "所有测试 Pod 均使用公共镜像且无 imagePullSecrets，错误信息为网络超时而非认证失败或权限拒绝"}, {"cause": "kubelet 或 containerd 配置问题", "probability": "low", "reason": "错误模式是标准 TCP 超时和连接拒绝，非镜像仓库配置错误或证书问题；且 kube-system 组件正常运行表明 containerd 本身无故障"}, {"cause": "DNS 解析失败导致无法解析 registry 域名", "probability": "low", "reason": "kubelet 日志显示已解析到具体 IP（如 31.13.96.195, 108.160.170.39 等）但在 TCP 连接阶段超时，说明 DNS 解析成功"}], "limitations": "未验证节点防火墙/安全组规则、NAT 网关、代理配置或网络策略等基础设施层面原因；未验证 harbor/私有 registry 是否可访问；g3 Pod test-reg-connect-1779397479 已进入 Terminating 状态，其镜像拉取失败归因于网络问题但无法单独确认；node-debugger-node1-nx8gb(g4) 的 StartError 与网络问题无关，属于独立配置错误。", "llm_raw_analysis": "## 证据清点\\n共采集 10 条关键证据：\\n- e1/e2: g1 CreateContainerConfigError — Secret 键缺失\\n- e3/e4/e5/e10: g2 ImagePullFailed — 网络不可达（i/o timeout + connection refused）\\n- e6: g3 ContainerCreating→Terminating — 镜像拉取失败\\n- e7/e8: g4 StartError — busybox 无 curl 命令\\n- e9: 集群整体状态\\n\\n## 逐条分析\\n### g2 主异常组（ImagePullFailed，48 个 Pod）\\ne3( dig-tool/node1): registry.k8s.io 镜像拉取超时，目标 IP us-west2-docker.pkg.dev/europe-west2-docker.pkg.dev TCP 443\\ne4(connectivity-test/node2): busybox:1.36.1 拉取 83 次 Failed, i/o timeout + con\n... 截断，原始 1407 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 核心根因是集群两个工作节点（node1, node2）的出站网络无法到达外部镜像仓库。具体证据：(1) dig-tool(node1) 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 时报 i/o timeout dialing us-w...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1 和 node2）到外部镜像仓库（docker.io 和 registry.k8s.io）的出站网络不可达，表现为 TCP 443 i/o timeout 和 connection refused，导致所有依赖公共镜像的 Pod 镜像拉取失败
     传导机制: 节点出站网络不通 → kubelet 无法从 registry-1.docker.io 和 registry.k8s.io 拉取镜像 → 容器状态进入 ErrImagePull → 重试后进入 ImagePullBackOff → Pod 持续 Pending 无法启动
     最终表现: default/mcp/aiops-e2e 三个 Namespace 下 48+ 个 Pod（DNS 测试、网络测试、registry 测试、节点调试工具）统一处于 ImagePullBackOff/ErrImagePull/Pending，kube-system 组件（使用本地/私有镜像）正常运行


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (30.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8060 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 52.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您详细分析集群状况。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群整体状态** | **异常** - 大量 Pod (至少 48 个) 处于 Pending 状态 |
| **核心问题** | **集群节点无法连接外部镜像仓库** (docker.io, registry.k8s.io) |
| **受影响范围** | 2个工作节点 (node1, node2)，3个命名空间 (default, mcp, aiops-e2e) |
| **证据完整度** | 10/10 (100%) |

**问题摘要**：您的集群中，**`node1` 和 `node2` 两个工作节点的出站网络**出现问题，无法访问 `docker.io` 和 `registry.k8s.io` 等公共镜像仓库。这导致集群中 48 个依赖公共镜像的 Pod 全部陷入 `Pending` 状态（主要表现 `ImagePullBackOff` 和 `ErrImagePull`）。此外，还存在一个 Secret 配置错误和一个容器运行时启动错误这两个独立问题。

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 集群 | 整个集群 |
| 受影响节点 | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| 受影响命名空间 | `default`, `mcp`, `aiops-e2e` |
| 受影响 Pod 数量 | **51 个 Pending, 48 个异常** |
| 主要异常状态 | `ImagePullBackOff` (28个), `ErrImagePull` (20个) |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| **1** | Pod 状态统计 | `kubectl get pods --all-namespaces` | 117 个Pod: Running=59, **Pending=51**, Succeeded=5, Failed=2, Evicted=1。异常Pod: ImagePullBackOff=28, ErrImagePull=20, CreateContainerConfigError=1, StartError=1 | 集群中存在大量异常Pod，主要问题是镜像拉取失败。 |
| **2** | 镜像拉取失败-节点1 | `kubectl describe pod dig-tool -n default` | 节点 `node1`。镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`。拉取失败原因: **`i/o timeout dialing us-west2-docker.pkg.dev:443` 和 `europe-west2-docker.pkg.dev:443`**。共发生5次Failed事件，667次BackOff事件。 | 证实 `node1` 无法连接到 `registry.k8s.io` 的注册端点，导致镜像拉取超时。 |
| **3** | 镜像拉取失败-节点2 | `kubectl describe pod connectivity-test -n mcp` | 节点 `node2`。镜像 `busybox:1.36.1`。83次拉取尝试全部失败，原因均为 **`i/o timeout` 或 `connection refused` 到 `registry-1.docker.io`** 的多组IP地址。 | 证实 `node2` 也无法连接到 `docker.io`，83次失败排除了偶发故障的可能。 |
| **4** | DNS解析问题 | `kubectl describe pod dns-resolve-test -n default` | 节点 `node2`。镜像 `busybox:1.36.1`。拉取失败原因为 `i/o timeout` 连接 `registry-1.docker.io` 的多个IP (`108.160.170.39`, `67.228.102.32`等)，并出现一次 `pull QPS exceeded`。 | 进一步确认网络完全不通，且集群可能因为大量尝试拉取镜像触发了上游Docker Hub的QPS限制。 |
| **5** | Secret配置错误 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | 状态 `CreateContainerConfigError`。事件: `Warning Failed Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | Pod引用的Secret中缺少指定的Key，导致无法创建容器。 |
| **6** | 启动错误 | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` | 状态 `Failed`。消息: `failed to create containerd task: failed to create shim task: OCI runtime ...` | 容器运行时 (containerd) 在创建容器时遇到OCI运行时错误，需要进一步分析。 |

### 证据关联分析
- **证据 #1, #2, #3, #4 印证**：大量Pod（28个ImagePullBackOff + 20个ErrImagePull）集中在两个工作节点，拉取 `busybox`, `curlimages/curl`, `registry.k8s.io/e2e-test-images/jessie-dnsutils` 等多个公共镜像时，都报告 `i/o timeout` 或 `connection refused`。这构成了一条完整的证据链，证明**集群节点出站网络到 `docker.io` 和 `registry.k8s.io` 的443端口不通**。
- **证据 #5 独立**：`rc-config-secret-key-missing` Pod的问题与网络无关，是应用配置错误。
- **证据 #6 独立**：`node-debugger-node1-nx8gb` Pod的`StartError`与网络无关，是节点上容器运行时环境的故障。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点防火墙/安全组规则 | **critical** | 无法确定网络不通的根本原因是防火墙、NAT网关还是公司代理策略。 |
| 节点上的网络连通性测试 | important | 可以手动在节点上 `curl registry-1.docker.io` 或 `nslookup` 来直接验证。 |
| `StartError` Pod 的详细日志 | medium | 当前日志缺失 (`previous terminated container not found`)，限制了对此问题的深入分析。 |

---

## 🎯 根因分析

### 因果链

```
┌───────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                  │
│ 集群工作节点 (node1, node2) 的出站网络无法访问公共镜像仓库                  │
│ (registry-1.docker.io:443, registry.k8s.io:443)                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    │ (网络不通)
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                  │
│ kubelet 尝试从远端 registry 拉取镜像 → TCP 连接 443 端口超时或被拒绝       │
│ → 拉取操作失败 (ErrImagePull) → kubelet 按策略重试 → 持续失败             │
│ → 状态变为 ImagePullBackOff → Pod 无法启动，维持 Pending                    │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                  │
│ 48 个 Pod 处于 ImagePullBackOff 或 ErrImagePull状态。                      │
│ 事件记录明确显示 "i/o timeout dialing registry-1.docker.io:443"           │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                              │
│ 大量用于网络连通性测试、DNS解析、节点调试的Pod无法启动，处于 Pending状态     │
└───────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2, #3, #4的详细事件日志，问题的根本原因是**集群的两个工作节点 (`node1` 和 `node2`) 无法通过出站网络连接到公共镜像仓库 (`docker.io` 和 `registry.k8s.io`) 的 443 端口**。这导致了所有依赖公共镜像的 Pod（如 dig-tool, connectivity-test, dns-resolve-test）在拉取镜像时发生 `i/o timeout`，并最终卡在 `ImagePullBackOff` 或 `ErrImagePull` 状态。

**置信度**：高 (95%)
-   ✅ 证据 #2, #3, #4 直接在 Pod 事件中提供了 `i/o timeout` 和 `connection refused` 的明确错误。
-   ✅ 问题在 `node1` 和 `node2` 两个节点上同时出现，排除了单节点故障。
-   ✅ 问题影响了多个命名空间和多种镜像，排除了单个镜像或应用的问题。
-   ⚠️ 缺失证据（防火墙/代理配置）无法确认根本网络故障的源头。

**独立问题：**
-   **配置错误**：`rc-config-secret-key-missing` Pod 因为 Secret `rc-app-secret` 中缺少 `APP_SECRET_TOKEN` 键而无法启动。
-   **运行时错误**：`node-debugger-node1-nx8gb` Pod 因 `containerd` OCI 运行时错误而启动失败。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [最优先] 检查并修复节点出站网络连接**

**目的**：这是集群当前最核心的问题，必须恢复节点到公共镜像仓库的网络连接。

*   **检查防火墙/安全组**：登录云服务商控制台，检查`node1`和`node2`关联的安全组/防火墙规则，确保出站到 `0.0.0.0/0` 的 TCP/443 端口是允许的。
*   **检查代理设置 (如有)**：如果集群配置了 HTTP/HTTPS 代理，需要确认代理规则是否正确放行了对外镜像仓库的流量。可以在节点上测试。
*   **检查DNS解析**：确认节点能否正确解析 `registry-1.docker.io` 和 `registry.k8s.io` 的域名。
    ```bash
    # 在 node1 和 node2 上手动执行，验证DNS
    nslookup registry-1.docker.io
    ```
*   **直接连接测试**：在节点上验证网络连通性。
    ```bash
    # 在 node1 和 node2 上手动执行，测试网络连通性
    curl -v --connect-timeout 10 https://registry-1.docker.io/v2/
    ```

**2. [高优先] 修复 Secret 配置错误**
```bash
# 1. 查看 Secret 中的现有 key
kubectl get secret rc-app-secret -n aiops-e2e -o yaml

# 2. 如果APP_SECRET_TOKEN确实缺失，需要手动添加。
# 假设Secret是以 yaml 文件存在
# 将value的base64编码字符串填入
echo -n 'your_actual_secret_value' | base64
# 然后编辑Secret，添加该字段
kubectl edit secret rc-app-secret -n aiops-e2e -o yaml
# 在data字段下添加: APP_SECRET_TOKEN: <base64_encoded_value>

# 3. 编辑完成后，手动删除旧Pod，让控制器重建
kubectl delete pod rc-config-secret-key-missing -n aiops-e2e
```

**3. [中等优先] 诊断 `StartError` Pod**
虽然只有1个，但可能预示着节点上容器运行时环境的问题。
```bash
# 查看该Pod的详细日志
kubectl logs node-debugger-node1-nx8gb -n mcp --previous
# 获取更详细的Pod状态
kubectl describe pod node-debugger-node1-nx8gb -n mcp
```
*依据*：当前日志无内容，需要检查节点上 `containerd` 或 `dockerd` 的日志来确定 OCI 运行时失败的具体原因。

### 后续优化

1.  **部署私有镜像仓库 (Harbor)**：将 `busybox`, `alpine`, `curlimages/curl` 等公共依赖镜像同步到私有仓库中，并使用私有仓库地址部署 Pod，彻底避免对外部网络的依赖。
2.  **监控告警**：配置对 Pod 状态 (`Pending`, `ImagePullBackOff`) 的监控和告警，确保能第一时间发现此类大规模问题。
3.  **配置网络策略**：如果集群支持，可为调试测试 Pod 单独配置网络策略，或使用 `hostNetwork: true` 进行特定诊断。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 恢复网络后，检查Pod状态 | `kubectl get pods -n default` (或其他 namespace) | 大量 `ImagePullBackOff` Pod 变为 `ContainerCreating` 或 `Running` |
| 2. 确认 Secret 修复 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | Pod 状态从 `CreateContainerConfigError` 变为 `Running` 或 `ContainerCreating` |
| 3. 确认网络连通性 | 在节点上再次执行 `curl -v --connect-timeout 10 https://registry-1.docker.io/v2/` | 返回 HTTP 200/401 等正常响应，而不是 `timeout`。 |

---

## ⚠️ 注意事项

-   **网络恢复后**，由于之前有大量重试和历史事件，`kubectl get pods` 可能会短暂显示大量 `ContainerCreating` 状态，等待镜像被拉取即可。
-   **Cluster Autoscaler (如有)**：建议在修复网络前暂停 Cluster Autoscaler 的扩展操作，否则它可能因为 Pod 无法调度而尝试创建新节点，而这些新节点可能同样无法访问外网。
-   **`node-debugger-node1-nx8gb` 的 `StartError`** 问题如果持续出现，可能需要检查 `containerd` 服务的运行状态和其配置，这可能是节点层面的更严重问题。

---

## 📊 性能统计

├─ 总耗时: 2.9m
├─ 问题定位: 64.1s (37%) ✅
├─ 证据链采集: 52.2s (30%) ✅
├─ 根因分析: 26.1s (15%) ✅
├─ 汇总总结: 30.3s (18%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 19 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 19 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
