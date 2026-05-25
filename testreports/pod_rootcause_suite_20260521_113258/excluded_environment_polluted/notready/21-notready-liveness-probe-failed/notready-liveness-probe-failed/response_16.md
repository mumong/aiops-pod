======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: fe7715dfc17c47e0]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先全局扫描所有 Pod 的状态，看看哪些 Pod 存在异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces returned ~127 pods across admin, aiops-e2e, aiops, default, kube-system namespaces. Running: 60 (healthy system pods + admin/metax/gpu + cloud-agent + some aiops). Ab
   💭 [问题定位] 让我详细查看所有异常 Pod 的精确状态，以完整识别：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=331 lines=4
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 60 pods across namespaces aiops-e2e, default, mcp, xnet are all in Pending or Failed status with condition=False. Key observations: 1 pod in xnet (observability-kibana) status=Failed reason=Evicted; 1
   💭 [问题定位] 让我再看一下容器级别的状态，特别是 CrashLoopBackOff 和实际容器退出状态：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 All 39 pods across namespaces aiops-e2e, default, and mcp are in Pending phase with containers in waiting state. The dominant failure reasons are ImagePullBackOff and ErrImagePull; only net-test-evide
   💭 [问题定位] 现在让我看看 xnet/observability-kibana (Evicted) 和 mcp/node-debugger-node1-nx8gb (Failed) 的详情，以及 CrashLoopBackOff 的那个 Pod：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=335 lines=4
Executing jq query for pods...
aiops-e2e/rc-notready-liveness: app state=waiting wait_reason=CrashLoopBackOff ready=false
default/net-test-evidence: net
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                    READY   STATUS      RESTARTS   AGE   IP              NODE     NOMINATED NODE   READINESS GATES   LABELS
observability-kibana-65d7c45f6d-7zc9l   0/1     Complete
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   READY   STATUS    RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-liveness   1/1     Running   10 (5m9s ago)   21m   172.16.
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS       RESTARTS   AGE     IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-nx8gb   0/1     StartError   0          4h42m   10
   💭 [问题定位] 让我再看看几个关键 Pod 的详细描述：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       19m (x10 over 21m)   kubelet       
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: observability-kibana-65d7c45f6d-7zc9l
namespace: xnet
node: master/10.2.0.48
status: Failed
reason: Evicted
message: The node was low on resource: ephemeral-storage. Thresho
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [问题定位] 现在让我获取与 ImagePull 问题相关的 runbook，以及 Evicted 和 CrashLoopBackOff 的 runbook：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   ✅ [问题定位] 完成 (47.8s)
   📤 → 下游数据: layer=Layer.L3, layers=L0+L3+L4
   scenarios=[{'scenario': '镜像仓库无法访问或认证失败，导致大量Pod无法拉取镜像', 'probability': 'high', 'reason': '59个Pod处于ImagePullBackOff/ErrImagePull状态，涉及多个命名空间和镜像'}, {'scenario': '节点node2的ephemeral-storage资源不足，导致Pod被Evicted', 'probability': 'confirmed', 'reason': 'observability-kibana被Evicted，描述明确提示ephemeral-storage不足'}, {'scenario': '应用层Liveness Probe配置错误导致CrashLoopBackOff', 'probability': 'confirmed', 'reason': 'rc-notready-liveness运行中但liveness probe故意失败，退出码137'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}, {"type": "pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}]
   reasoning=当前异常Pod数量庞大(~60个)，以ImagePullBackOff(29)和ErrImagePull(27)为主，集中在default和aiops-e2e命名空间的网络/连通性/注册表测试Pod中。同时存在L0级别异常：xnet/observability-kibana被Evicted（ephemeral-storage资源不足），以及mcp/node-debugger-node1-nx8gb因StartError（curl命令不存在）Failed。L4异常：aiops-e2e/rc-notready-liveness处于CrashLoopBackOff状态，根源为Liveness probe失败(NotReadyProbeFailed)。另有2个Terminating Pod。系统级Pod（calico、coredns、kube-apiserver等）均正常运行。综合判断：绝大多数异常Pod由镜像拉取失败(ImagePullBackOff/ErrImagePull)导致，根因在L3（镜像仓库/网络连通性）；同时存在L0（Evicted）和L4（probe失败）的个别异常。选择L3作为主要层级，因为59/60的异常集中在镜像拉取问题上。
   layer_analysis={"layer": "L3", "derived_layer": "L3, L4", "layers": ["L0", "L3", "L4"], "layer_name": "Image/Network/DNS & Application Probe", "confidence": 0.85, "reasoning": "当前异常Pod数量庞大(~60个)，以ImagePullBackOff(29)和ErrImagePull(27)为主，集中在default和aiops-e2e命名空间的网络/连通性/注册表测试Pod中。同时存在L0级别异常：xnet/observability-kibana被Evicted（ephemeral-storage资源不足），以及mcp/node-debugger-node1-nx8gb因StartError（curl命令不存在）Failed。L4异常：aiops-e2e/rc-notready-liveness处于CrashLoopBackOff状态，根源为Liveness probe失败(NotReadyProbeFailed)。另有2个Terminating Pod。系统级Pod（calico、coredns、kube-apiserver等）均正常运行。综合判断：绝大多数异常Pod由镜像拉取失败(ImagePullBackOff/ErrImagePull)导致，根因在L3（镜像仓库/网络连通性）；同时存在L0（Evicted）和L4（probe失败）的个别异常。选择L3作为主要层级，因为59/60的异常集中在镜像拉取问题上。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "dig-check-registry", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-tool-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-evidence", "namespace": "default", "status": "Terminating"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-verify", "namespace": "default", "status": "Terminating"}, {"name": "registry-diag-evidence-verify", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2s2mz", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}, {"type": "pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库无法访问或认证失败，导致大量Pod无法拉取镜像", "probability": "high", "reason": "59个Pod处于ImagePullBackOff/ErrImagePull状态，涉及多个命名空间和镜像"}, {"scenario": "节点node2的ephemeral-storage资源不足，导致Pod被Evicted", "probability": "confirmed", "reason": "observability-kibana被Evicted，描述明确提示ephemeral-storage不足"}, {"scenario": "应用层Liveness Probe配置错误导致CrashLoopBackOff", "probability": "confirmed", "reason": "rc-notready-liveness运行中但liveness probe故意失败，退出码137"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "default", "name": "net-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-verify"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g4", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "default", "name": "net-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-verify"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g4", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 29, "ErrImagePull": 27, "Terminating": 2}, "total_abnormal": 59, "selected_rows": ["aiops-e2e         rc-notready-liveness                                0/1     CrashLoopBackOff   9 (4m41s ago)   21m     172.16.166.129   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0               13h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ErrImagePull       0               130m    172.16.104.52    node2    <none>           <none>            run=connectivity-check-tmp", "default           dig-check-registry                                  0/1     ImagePullBackOff   0               70m     172.16.166.155   node1    <none>           <none>            run=dig-check-registry", "default           dig-tool                                            0/1     ImagePullBackOff   0               8h      172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff   0               7h56m   172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff   0               12h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff   0               5h15m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-diag-tool-evidence                              0/1     ErrImagePull       0               106m    172.16.104.4     node2    <none>           <none>            run=dns-diag-tool-evidence", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff   0               5h21m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull       0               5h21m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test                                            0/1     ErrImagePull       0               70m     172.16.104.56    node2    <none>           <none>            run=dns-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0               13h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull       0               11h     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff   0               5h21m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull       0               8h      172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-evidence                                   0/1     Terminating        0               2m5s    <none>           node2    <none>           <none>            run=net-test-evidence", "default           net-test-pod                                        0/1     ImagePullBackOff   0               12h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull       0               12h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull       0               9h      172.16.104.62    node2    <none>           <none>            run=network-test-1779374716"], "raw_ref": "/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L0 + L3 + L4（主层级: Layer.L3）
   置信度: 85%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将直接执行既有 evidence_plan 中的工具调用。先从 g1（ImagePullBackOff 主异常组）和 g3（Terminating）的关键证据开始采集。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-check-tmp (namespace: default, node: node2/10.2.0.50) is Pending. Container state Waiting (Reason: ErrImagePull). All 7 pull attempts to docker.io/library/busybox:1.36.1 failed with i
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: test-dns-1779360358
namespace: aiops-e2e
creationTimestamp: 2026-05-21T10:45:58Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  9m1s (x1953 over 13h)  kubelet  Back-off pulling image "busybox:1.3
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: net-test-evidence
namespace: default
creationTimestamp: 2026-05-22T00:22:04Z
deletionTimestamp: 2026-05-22T00:23:34Z
deletionGracePeriodSeconds: 30
finalizers:
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: registry-connect-verify
namespace: default
creationTimestamp: 2026-05-22T00:14:53Z
deletionTimestamp: 2026-05-22T00:16:24Z
deletionGracePeriodSeconds: 30
final
   💭 [证据链采集] 关键发现！所有 Pod 镜像拉取失败的原因已明确——**集群无法访问 Docker Hub**。让我继续采集 g2（CrashLoopBackOff）和 g4（StartError）的证据。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=3149 lines=117
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: "2026-05-21T19:42:18Z"
  name: node-debugger-node1-nx8gb
  namespace: mcp
  resourceVersion: "52
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace Secret 表摘要: rows=1 abnormal=0
docker_secret_count: 0
未发现 type 为 kubernetes.io/dockerconfigjson 或 kubernetes.io/dockercfg 的 Secret。
# 全量 Secret 行已落盘到 raw_ref，selected_r
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       20m (x10 over 22m)    kubelet      
   💭 [证据链采集] 好，让我也检查一下另一个命名空间下是否有镜像拉取密钥，以及 Terminating Pod 的事件。
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN   TYPE     REASON           OBJECT                        MESSAGE
10m         Normal   Scheduled        Pod/registry-connect-verify   Successfully assigned default/registr
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN   TYPE     REASON           OBJECT                  MESSAGE
3m15s       Normal   AddedInterface   Pod/net-test-evidence   Add eth0 [172.16.104.19/32] from k8s-pod-network

   💭 [证据链采集] 再检查一下 node2 上是否有 Terminating 卡住的关键原因，以及快速确认镜像拉取问题的全貌。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS        RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
registry-connect-verify   0/1     Terminating   0          10m   <none>   no
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                READY   STATUS        RESTARTS   AGE     IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
net-test-evidence   0/1     Terminating   0          3m18s   <none>   node2   <n
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: net-test-evidence
namespace: default
node: node2/10.2.0.50
status: Terminating (lasts 108s)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: de1ef5cd433a
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 好，现在让我查看一下关键的事件详情和 g1 代表 Pod 的详细事件。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Name:                      net-test-evidence\nNamespace:                 default\nPriority:                  0\nService Account:           default\nNode:                  
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      Reason:       ErrImagePull\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceac
   💭 [证据链采集] 现在再验证一下 node2 上 ErrImagePull 的 Pod 和 node1 上 ImagePullBackOff 的 Pod 是否也是同样的 i/o timeout 问题。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      Reason:       ErrImagePull\n  Type     Reason   Age                     From     Message\n  Warning  Failed   58m                     kubelet  Failed to pull image \
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      Reason:       ErrImagePull\n  Type     Reason   Age                    From     Message\n  Warning  Failed   59m                    kubelet  Failed to pull image \"b
   💭 [证据链采集] 现在让我也验证一下 rc-notready-liveness 的日志（Empty stdout 已返回），以及获取 g2 CrashLoopBackOff 的更多细节。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    137\n      Started:      Fri, 22 May 2026 00:24:34 +0000\n      Finished:     Fri, 22 May 20
   💭 [证据链采集] 现在我已经收集了足够的证据，以下是完整证据采集结论。

---

## 证据采集结论

### ✅ 已采集的主异常证据（g2 — ImagePullBackOff / ErrImagePull，~56个Pod）

**关键证据1 — 拉取错误的确认原因（i/o timeout）**
- `kubectl describe pod -n default connectivity-check-tmp` 显示 Events：
  ```
  Failed to pull image "busybox:1.36.1": ... failed to resolve reference "...":
  dial tcp <IP>:443: i/o timeout
  ```
- `kubectl describe pod -n default dns-resolve-test`（node2）同样：
  ```
  dial tcp 108.160.165.141:443: i/o timeout
  ```
- `kubectl describe pod -n mcp connectivity-test`（node1）同样：
  ```
  dial tcp 108.160.165.141:443: i/o timeout
  ```

**关键证据2 — 镜像均为 `busybox:1.36.1`，无 imagePullSecrets**
- `kubectl get yaml pod test-dns-1779360358`：image=`busybox:1.36.1`，imagePullSecrets=`<absent>`
- `kubectl get secrets -n default`：无 `dockerconfigjson` 类型 Secret
- `kubectl get secrets -n aiops-e2e`：无 Secret
- `kubectl get secrets -n mcp`：无 Secret

**关键证据3 — 跨节点、跨命名空间一致故障**
- node1 上 Pod（test-dns-1779360358）→ ImagePullBackOff
- node2 上 Pod（connectivity-check-tmp、dns-resolve-test）→ ErrImagePull / i/o timeout
- mcp 命名空间（connectivity-test）→ 同样 i/o timeout
- **根因明确**：集群无法连接到 `registry-1.docker.io`（docker.io），TCP 超时，与镜像名/tag/认证无关

---

### ✅ 已采集的异常组 g1（CrashLoopBackOff — rc-notready-liveness）

**关键证据1 — Exit Code 137 + Liveness probe 故意失败**
- Last State: Terminated, Reason: Error, **Exit Code: 137**
- Liveness 配置：`exec [sh -c echo liveness endpoint failed; exit 1]` — **这是测试用故意的配置**
- 事件：`Liveness probe failed: liveness endpoint failed`
- `kubectl logs --previous` 返回空（容器启动后立即被 probe 杀死，无业务输出）

**结论**：这是人工标记的 e2e 测试 Pod（标签 `rootcause-e2e=true, pod_abnormal_type=NotReadyProbeFailed`），属于预期异常。

---

### ✅ 已采集的异常组 g3（Terminating — 2个Pod）

**关键证据1 — net-test-evidence**
- `deletionTimestamp`: 已设置（30s 前），`finalizers`: 无
- Pod 状态：Waiting → ContainerCreating（镜像还在拉取中就被删除）
- Events 只有 `Scheduled → AddedInterface → Pulling`，无异常事件
- **根因**：deletionGracePeriodSeconds=30s，镜像拉取超时（i/o timeout）导致容器创建卡住，删除流程等待容器创建完成或超时

**关键证据2 — registry-connect-verify**
- 同样 `deletionTimestamp` 已设置，`finalizers` 无，状态 ContainerCreating
- 同样卡在 `busybox:1.36.1` 镜像拉取 i/o timeout

---

### ✅ 已采集的异常组 g4（StartError — node-debugger-node1-nx8gb）

**关键证据1 — 命令不存在**
- Message: `failed to create containerd task: ... exec: \"curl\": executable file not found in $PATH`
- 容器镜像 `busybox:1.36`（非 1.36.1），command 为 `curl -s -o /dev/null ...`
- **根因**：busybox 镜像不含 curl 命令

---

### ⚠️ 冲突/负向证据说明
- 所有异常 Pod 均能在环境中确认存在，无 NotFound 冲突
- `kubectl logs --previous rc-notready-liveness` 返回空（正常，因为容器被 probe 杀死未产生日志）
- Terminating Pod 无 finalizers，说明不是 finalizer 卡住，而是容器创建未完成

---

### 📋 核心结论

| 异常组 | 数量 | 已确认根因 |
|--------|------|-----------|
| **ImagePullBackOff/ErrImagePull** | **~56 个 Pod** | **集群无法访问 registry-1.docker.io（docker.io），TCP i/o timeout**。跨 node1/node2 一致，与 Secret/镜像名无关 |
| **CrashLoopBackOff (rc-notready-liveness)** | 1 个 | 人工注入的 Liveness probe 故意失败测试（exit 137） |
| **Terminating (2个)** | 2 个 | 删除时镜像仍卡在拉取中，容器创建未完成导致删除流程等待 |
| **StartError (1个)** | 1 个 | busybox 镜像中无 curl 可执行文件 |
   ✅ [证据链采集] 完成 (1m 2.5s)
   📤 → 下游数据: evidence_items=19/20
   evidence_analysis={"evidence_plan":[{"id":"g1-representative","description":"主异常组g2: 从ImagePullBackOff/ErrImagePull组选代表Pod(test-dns-1779360358, aiops-e2e)做完整describe，查看Events和镜像拉取失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e test-dns-1779360358","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"获取ImagePullBackOff的Events和具体错误原因","evidence_type":"event","target_scope":"aiops-e2e/test-dns-1779360358","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-image","description":"主异常组g2: 查看代表Pod的镜像配置，验证镜像地址是否正确","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e test-dns-1779360358 -o yaml","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"查看Pod spec中的image和imagePullSecrets","evidence_type":"config","target_scope":"aiops-e2e/test-dns-1779360358","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g1-other-node2","description":"主异常组g2: 选一个node2上的ErrImagePull Pod(connectivity-check-tmp)验证节点分布","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n default connectivity-check-tmp","tool_args":{"kind":"pod","name":"connectivity-check-tmp","namespace":"default"},"purpose":"验证node2上Pod的镜像拉取错误事件","evidence_type":"event","target_scope":"default/connectivity-check-tmp","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-crashloop","description":"异常组g1(CrashLoopBackOff): 对rc-notready-liveness做describe验证last state和events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-notready-liveness","tool_args":{"kind":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"验证CrashLoopBackOff的Last State和Exit Code","evidence_type":"event","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-logs","description":"异常组g1(CrashLoopBackOff): 查看rc-notready-liveness的previous日志确认应用崩溃原因","level":"important","tool":"run_bash_command","command":"kubectl logs -n aiops-e2e rc-notready-liveness --previous","tool_args":{"command":"kubectl logs -n aiops-e2e rc-notready-liveness --previous"},"purpose":"获取CrashLoopBackOff容器崩溃前的日志","evidence_type":"log","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"g3-terminating","description":"异常组g3(Terminating): 查看net-test-evidence的YAML确认deletionTimestamp和finalizers","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n default net-test-evidence -o yaml","tool_args":{"kind":"pod","name":"net-test-evidence","namespace":"default"},"purpose":"验证Terminating Pod是否卡在finalizers或deletionTimestamp","evidence_type":"config","target_scope":"default/net-test-evidence","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g3-terminating-2","description":"异常组g3(Terminating): 查看registry-connect-verify的YAML","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n default registry-connect-verify -o yaml","tool_args":{"kind":"pod","name":"registry-connect-verify","namespace":"default"},"purpose":"验证另一个Terminating Pod的状态","evidence_type":"config","target_scope":"default/registry-connect-verify","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g4-start-error","description":"异常组g4(StartError): 查看node-debugger-node1-nx8gb的YAML确认当前状态","level":"optional","tool":"kubectl_get_yaml","command":"kubectl get pod -n mcp node-debugger-node1-nx8gb -o yaml","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"验证StartError Pod的当前状态和容器状态","evidence_type":"state","target_scope":"mcp/node-debugger-node1-nx8gb","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-cross-node-secret","description":"主异常组g2: 检查default namespace中是否有imagePullSecrets相关的Secret","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get secrets -n default","tool_args":{"kind":"secret","namespace":"default"},"purpose":"确认是否有镜像拉取凭据","evidence_type":"config","target_scope":"default","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod connectivity-check-tmp (namespace: default, node: node2/10.2.0.50) is Pending. Container state Waiting (Reason: ErrImagePull). All 7 pull attempts to docker.io/library/busybox:1.36.1 failed with i/o timeout to various registry IPs (199.96.62.17, 69.30.25.21, 108.160.169.181, 108.160.165.173, 128.242.245.125) on port 443. BackOff event repeated 46 times over 120m. Pulling event repeated 14x over 131m. Pod IP: 172.16.104.52, Calico CNI configured. Pod scheduled and initialized, but containers not ready.\nkey_facts: [\"name: connectivity-check-tmp\", \"namespace: default\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container: connectivity-check-tmp\", \"image: busybox:1.36.1\", \"State: Waiting (Reason: ErrImagePull)\", \"Ready: False\", \"Restart Count: 0\", \"Pod IP: 172.16.104.52\", \"Events: Failed to pull image - all i/o timeout to registry-1.docker.io:443 (IPs: 199.96.62.17, 69.30.25.21, 108.160.169.181, 108.160.165.173, 128.242.245.125)\", \"Normal BackOff: x46 over 120m\", \"Normal Pulling: x14 over 131m\", \"Warning Failed (Error: ErrImagePull): x14 over 120m\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\"]\nconflicts: [\"current_summary reports 5 Failed\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: test-dns-1779360358\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T10:45:58Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- test-dns-1779360358: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: /bin/sh -c nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- test-dns-1779360358: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-g4sbz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  9m1s (x1953 over 13h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   2m49s (x183 over 13h)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.184.142:443: i/o timeout\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Conta\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: net-test-evidence\nnamespace: default\ncreationTimestamp: 2026-05-22T00:22:04Z\ndeletionTimestamp: 2026-05-22T00:23:34Z\ndeletionGracePeriodSeconds: 30\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- net-test-evidence: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c wget -q --timeout=5 -O- https://registry-1.docker.io/v2/\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [net-test-evidence]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [net-test-evidence]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- net-test-evidence: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-hdmdx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: registry-connect-verify\nnamespace: default\ncreationTimestamp: 2026-05-22T00:14:53Z\ndeletionTimestamp: 2026-05-22T00:16:24Z\ndeletionGracePeriodSeconds: 30\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- registry-connect-verify: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c wget -q --timeout=10 -O- https://registry-1.docker.io/v2/\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [registry-connect-verify]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [registry-connect-verify]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- registry-connect-verify: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-5bsh7\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/006-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=3149 lines=117\napiVersion: v1\nkind: Pod\nmetadata:\n  creationTimestamp: \"2026-05-21T19:42:18Z\"\n  name: node-debugger-node1-nx8gb\n  namespace: mcp\n  resourceVersion: \"52801137\"\n  uid: 4cc072ec-47f2-456e-8741-97a2d7f108d8\nspec:\n  containers:\n  - command:\n    - curl\n    - -s\n    - -o\n    - /dev/null\n    - -w\n    - '%{http_code}'\n    - --connect-timeout\n    - \"5\"\n    - https://registry-1.docker.io/v2/\n    image: busybox:1.36\n    imagePullPolicy: IfNotPresent\n    name: debugger\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /host\n      name: host-root\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-hl45s\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  hostIPC: true\n  hostNetwork: true\n  hostPID: true\n  nodeName: node1\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/007-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/007-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/007-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace Secret 表摘要: rows=1 abnormal=0\ndocker_secret_count: 0\n未发现 type 为 kubernetes.io/dockerconfigjson 或 kubernetes.io/dockercfg 的 Secret。\n# 全量 Secret 行已落盘到 raw_ref，selected_rows 已落盘到 structured_ref。","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/008-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/008-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/008-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       20m (x10 over 22m)    kubelet            Liveness probe failed: liveness endpoint failed\n  Warning  BackOff         2m26s (x67 over 19m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         21m (x3 over 22m)     kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: f997c06136714184f9866361b3eab26ff46c280103b276058ecb6da12e4ce2e4\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       22m                   default-scheduler  Successful\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/009-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/009-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/009-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/010-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/010-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/010-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/011-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/011-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/011-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN   TYPE     REASON           OBJECT                        MESSAGE\n10m         Normal   Scheduled        Pod/registry-connect-verify   Successfully assigned default/registry-connect-verify to node2\n10m         Normal   AddedInterface   Pod/registry-connect-verify   Add eth0 [172.16.104.5/32] from k8s-pod-network\n10m         Normal   Pulling          Pod/registry-connect-verify   Pulling image \"busybox:1.36.1\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/012-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/012-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/012-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN   TYPE     REASON           OBJECT                  MESSAGE\n3m15s       Normal   AddedInterface   Pod/net-test-evidence   Add eth0 [172.16.104.19/32] from k8s-pod-network\n3m15s       Normal   Scheduled        Pod/net-test-evidence   Successfully assigned default/net-test-evidence to node2\n3m14s       Normal   Pulling          Pod/net-test-evidence   Pulling image \"busybox:1.36.1\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/013-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/013-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/013-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                      READY   STATUS        RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS\nregistry-connect-verify   0/1     Terminating   0          10m   <none>   node2   <none>           <none>            run=registry-connect-verify","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/014-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/014-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/014-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                READY   STATUS        RESTARTS   AGE     IP       NODE    NOMINATED NODE   READINESS GATES   LABELS\nnet-test-evidence   0/1     Terminating   0          3m18s   <none>   node2   <none>           <none>            run=net-test-evidence","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/015-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/015-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/015-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: net-test-evidence\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Terminating (lasts 108s)\n关键诊断行:\nAnnotations:               cni.projectcalico.org/containerID: de1ef5cd433a58851b63ae854f7640b6e7d5030af8bf8db479fced75454f4a56\n                           cni.projectcalico.org/podIP: 172.16.104.19/32\n                           cni.projectcalico.org/podIPs: 172.16.104.19/32\n                           k8s.v1.cni.cncf.io/network-status:\n                           k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nTermination Grace Period:  30s\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  net-test-evidence:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n      wget\n      -q\n      --timeout=5\n      -O-\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-hdmdx:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/016-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/016-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/016-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Name:                      net-test-evidence\\nNamespace:                 default\\nPriority:                  0\\nService Account:           default\\nNode:                      node2/10.2.0.50\\nStart Time:                Fri, 22 May 2026 00:22:04 +0000\\nLabels:                    run=net-test-evidence\\nAnnotations:               cni.projectcalico.org/containerID: de1ef5cd433a58851b63ae854f7640b6e7d5030af8bf8db479fced75454f4a56\\n                           cni.projectcalico.org/podIP: 172.16.104.19/32\\n                           cni.projectcalico.org/podIPs: 172.16.104.19/32\\n                           k8s.v1.cni.cncf.io/network-status:\\n                             [{\\n                                 \\\"name\\\": \\\"k8s-pod-network\\\",\\n                                 \\\"ips\\\": [\\n                                     \\\"172.16.104.19\\\"\\n                                 ],\\n                                 \\\"default\\\": true,\\n                                 \\\"dns\\\": {}\\n                             }]\\n                           k8s.v1.cni.cncf.io/networks-status:\\n                             [{\\n                                 \\\"name\\\": \\\"k8s-pod-network\\\",\\n                                 \\\"ips\\\": [\\n                                     \\\"172.16.104.19\\\"\\n                                 ],\\n                                 \\\"default\\\": true,\\n                                 \\\"dns\\\": {}\\n                             }]\\nStatus:                    Terminating (lasts 2m9s)\\nTermination Grace Period:  30s\\nIP:                        \\nIPs:                       <none>\\nContainers:\\n  net-test-evidence:\\n    Container ID:  \\n    Image:         busybox:1.36.1\\n    Image ID:      \\n    Port:          <none>\\n    Host Port:     <none>\\n    Args:\\n      sh\\n      -c\\n      wget\\n      -q\\n      --timeout=5\\n      -O-\\n      https://registry-1.docker.io/v2/\\n    State:          Waiting\\n      Reason:       ContainerCreating\\n    Ready:          False\\n    Restart Count:  0\\n    Environment:    <none>\\n    Mounts:\\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-hdmdx (ro)\\nConditions:\\n  Type              Status\\n  Initialized       True \\n  Ready             False \\n  ContainersReady   False \\n  PodScheduled      True \\nVolumes:\\n  kube-api-access-hdmdx:\\n    Type:                    Projected (a volume that contains injected data from multiple sources)\\n    TokenExpirationSeconds:  3607\\n    ConfigMapName:           kube-root-ca.crt\\n    ConfigMapOptional:       <nil>\\n    DownwardAPI:             true\\nQoS Class:                   BestEffort\\nNode-Selectors:              <none>\\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\\nEvents:\\n  Type    Reason          Age    From               Message\\n  ----    ------          ----   ----               -------\\n  Normal  Scheduled       3m38s  default-scheduler  Successfully assigned default/net-test-evidence to node2\\n  Normal  AddedInterface  3m39s  multus             Add eth0 [172.16.104.19/32] from k8s-pod-network\\n  Normal  Pulling         3m38s  kubelet            Pulling image \\\"busybox:1.36.1\\\"\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/017-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/017-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/017-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      Reason:       ErrImagePull\\n    Ready:          False\\n    Restart Count:  0\\n    Environment:    <none>\\n    Mounts:\\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-8qvlz (ro)\\n--\\nEvents:\\n  Type     Reason   Age                    From     Message\\n  ----     ------   ----                   ----     -------\\n  Warning  Failed   56m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 199.96.62.17:443: i/o timeout\\n  Normal   BackOff  51m (x46 over 121m)    kubelet  Back-off pulling image \\\"busybox:1.36.1\\\"\\n  Warning  Failed   40m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 69.30.25.21:443: i/o timeout\\n  Warning  Failed   27m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 108.160.169.181:443: i/o timeout\\n  Warning  Failed   14m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 108.160.165.173:443: i/o timeout\\n  Normal   Pulling  14m (x14 over 131m)    kubelet  Pulling image \\\"busybox:1.36.1\\\"\\n  Warning  Failed   2m19s (x14 over 121m)  kubelet  Error: ErrImagePull\\n  Warning  Failed   2m19s                  kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 128.242.245.125:443: i/o timeout\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/018-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/018-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/018-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      Reason:       ErrImagePull\\n  Type     Reason   Age                     From     Message\\n  Warning  Failed   58m                     kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 108.160.165.141:443: i/o timeout\\n  Warning  Failed   44m (x2 over 88m)       kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 104.244.46.52:443: i/o timeout\\n  Warning  Failed   31m                     kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 168.143.162.58:443: i/o timeout\\n  Warning  Failed   18m                     kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 108.160.167.158:443: i/o timeout\\n  Warning  Failed   6m51s (x35 over 5h14m)  kubelet  Error: ErrImagePull\\n  Warning  Failed   6m51s                   kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 202.160.128.210:443: i/o timeout\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/019-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/019-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/019-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      Reason:       ErrImagePull\\n  Type     Reason   Age                    From     Message\\n  Warning  Failed   59m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 108.160.165.141:443: i/o timeout\\n  Warning  Failed   47m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 185.60.216.11:443: i/o timeout\\n  Warning  Failed   34m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 65.49.26.99:443: i/o timeout\\n  Warning  Failed   21m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 108.160.167.158:443: i/o timeout\\n  Warning  Failed   9m21s (x103 over 12h)  kubelet  Error: ErrImagePull\\n  Warning  Failed   9m21s                  kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 208.43.170.231:443: i/o timeout\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/020-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/020-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/020-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"    Last State:     Terminated\\n      Reason:       Error\\n      Exit Code:    137\\n      Started:      Fri, 22 May 2026 00:24:34 +0000\\n      Finished:     Fri, 22 May 2026 00:25:13 +0000\\n    Ready:          True\\n    Restart Count:  11\\n    Liveness:       exec [sh -c echo liveness endpoint failed; exit 1] delay=1s timeout=1s period=3s #success=1 #failure=3\\n    Environment:    <none>\\n    Mounts:\\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-84xz2 (ro)\\nConditions:\\n  Type              Status\\n  Initialized       True \\n  Ready             True \\n  ContainersReady   True \\n  PodScheduled      True \\nVolumes:\\n  kube-api-access-84xz2:\\n    Type:                    Projected (a volume that contains injected data from multiple sources)\\n    TokenExpirationSeconds:  3607\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/021-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/021-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fe7715dfc17c47e0/tools/021-evidence-run_bash_command.summary.txt"}],"llm_analysis":"现在我已经收集了足够的证据，以下是完整证据采集结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集的主异常证据（g2 — ImagePullBackOff / ErrImagePull，~56个Pod）\n\n**关键证据1 — 拉取错误的确认原因（i/o timeout）**\n- `kubectl describe pod -n default connectivity-check-tmp` 显示 Events：\n  ```\n  Failed to pull image \"busybox:1.36.1\": ... failed to resolve reference \"...\":\n  dial tcp <IP>:443: i/o timeout\n  ```\n- `kubectl describe pod -n default dns-resolve-test`（node2）同样：\n  ```\n  dial tcp 108.160.165.141:443: i/o timeout\n  ```\n- `kubectl describe pod -n mcp connectivity-test`（node1）同样：\n  ```\n  dial tcp 108.160.165.141:443: i/o timeout\n  ```\n\n**关键证据2 — 镜像均为 `busybox:1.36.1`，无 imagePullSecrets**\n- `kubectl get yaml pod test-dns-1779360358`：image=`busybox:1.36.1`，imagePullSecrets=`<absent>`\n- `kubectl get secrets -n default`：无 `dockerconfigjson` 类型 Secret\n- `kubectl get secrets -n aiops-e2e`：无 Secret\n- `kubectl get secrets -n mcp`：无 Secret\n\n**关键证据3 — 跨节点、跨命名空间一致故障**\n- node1 上 Pod（test-dns-1779360358）→ ImagePullBackOff\n- node2 上 Pod（connectivity-check-tmp、dns-resolve-test）→ ErrImagePull / i/o timeout\n- mcp 命名空间（connectivity-test）→ 同样 i/o timeout\n- **根因明确**：集群无法连接到 `registry-1.docker.io`（docker.io），TCP 超时，与镜像名/tag/认证无关\n\n---\n\n### ✅ 已采集的异常组 g1（CrashLoopBackOff — rc-notready-liveness）\n\n**关键证据1 — Exit Code 137 + Liveness probe 故意失败**\n- Last State: Terminated, Reason: Error, **Exit Code: 137**\n- Liveness 配置：`exec [sh -c echo liveness endpoint failed; exit 1]` — **这是测试用故意的配置**\n- 事件：`Liveness probe failed: liveness endpoint failed`\n- `kubectl logs --previous` 返回空（容器启动后立即被 probe 杀死，无业务输出）\n\n**结论**：这是人工标记的 e2e 测试 Pod（标签 `rootcause-e2e=true, pod_abnormal_type=NotReadyProbeFailed`），属于预期异常。\n\n---\n\n### ✅ 已采集的异常组 g3（Terminating — 2个Pod）\n\n**关键证据1 — net-test-evidence**\n- `deletionTimestamp`: 已设置（30s 前），`finalizers`: 无\n- Pod 状态：Waiting → ContainerCreating（镜像还在拉取中就被删除）\n- Events 只有 `Scheduled → AddedInterface → Pulling`，无异常事件\n- **根因**：deletionGracePeriodSeconds=30s，镜像拉取超时（i/o timeout）导致容器创建卡住，删除流程等待容器创建完成或超时\n\n**关键证据2 — registry-connect-verify**\n- 同样 `deletionTimestamp` 已设置，`finalizers` 无，状态 ContainerCreating\n- 同样卡在 `busybox:1.36.1` 镜像拉取 i/o timeout\n\n---\n\n### ✅ 已采集的异常组 g4（StartError — node-debugger-node1-nx8gb）\n\n**关键证据1 — 命令不存在**\n- Message: `failed to create containerd task: ... exec: \\\"curl\\\": executable file not found in $PATH`\n- 容器镜像 `busybox:1.36`（非 1.36.1），command 为 `curl -s -o /dev/null ...`\n- **根因**：busybox 镜像不含 curl 命令\n\n---\n\n### ⚠️ 冲突/负向证据说明\n- 所有异常 Pod 均能在环境中确认存在，无 NotFound 冲突\n- `kubectl logs --previous rc-notready-liveness` 返回空（正常，因为容器被 probe 杀死未产生日志）\n- Terminating Pod 无 finalizers，说明不是 finalizer 卡住，而是容器创建未完成\n\n---\n\n### 📋 核心结论\n\n| 异常组 | 数量 | 已确认根因 |\n|--------|------|-----------|\n| **ImagePullBackOff/ErrImagePull** | **~56 个 Pod** | **集群无法访问 registry-1.docker.io（docker.io），TCP i/o timeout**。跨 node1/node2 一致，与 Secret/镜像名无关 |\n| **CrashLoopBackOff (rc-notready-liveness)** | 1 个 | 人工注入的 Liveness probe 故意失败测试（exit 137） |\n| **Terminating (2个)** | 2 个 | 删除时镜像仍卡在拉取中，容器创建未完成导致删除流程等待 |\n| **StartError (1个)** | 1 个 | busybox 镜像中无 curl 可执行文件 |","collection_summary":"计划 8 项，实际采集 8 项，未采集 0 项，完整度 100%；其中真实环境证据 19/19 项，完整度 100%；实际执行工具 28 个，匹配计划 8 个，未规划证据 20 个","plan_total":8,"plan_collected":8,"plan_completeness":1.0,"environment_evidence_total":19,"environment_evidence_collected":19,"environment_evidence_completeness":1.0,"executed_tool_count":28,"matched_tool_count":8,"unplanned_tool_count":20,"evidence_inventory":[{"id":"g1-representative","description":"主异常组g2: 从ImagePullBackOff/ErrImagePull组选代表Pod(test-dns-1779360358, aiops-e2e)做完整describe，查看Events和镜像拉取失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e test-dns-1779360358","purpose":"获取ImagePullBackOff的Events和具体错误原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-image","description":"主异常组g2: 查看代表Pod的镜像配置，验证镜像地址是否正确","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e test-dns-1779360358 -o yaml","purpose":"查看Pod spec中的image和imagePullSecrets","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-other-node2","description":"主异常组g2: 选一个node2上的ErrImagePull Pod(connectivity-check-tmp)验证节点分布","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n default connectivity-check-tmp","purpose":"验证node2上Pod的镜像拉取错误事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-crashloop","description":"异常组g1(CrashLoopBackOff): 对rc-notready-liveness做describe验证last state和events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-notready-liveness","purpose":"验证CrashLoopBackOff的Last State和Exit Code","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-logs","description":"异常组g1(CrashLoopBackOff): 查看rc-notready-liveness的previous日志确认应用崩溃原因","level":"important","tool":"run_bash_command","command":"kubectl logs -n aiops-e2e rc-notready-liveness --previous","purpose":"获取CrashLoopBackOff容器崩溃前的日志","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-terminating","description":"异常组g3(Terminating): 查看net-test-evidence的YAML确认deletionTimestamp和finalizers","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n default net-test-evidence -o yaml","purpose":"验证Terminating Pod是否卡在finalizers或deletionTimestamp","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-terminating-2","description":"异常组g3(Terminating): 查看registry-connect-verify的YAML","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n default registry-connect-verify -o yaml","purpose":"验证另一个Terminating Pod的状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g4-start-error","description":"异常组g4(StartError): 查看node-debugger-node1-nx8gb的YAML确认当前状态","level":"optional","tool":"kubectl_get_yaml","command":"kubectl get pod -n mcp node-debugger-node1-nx8gb -o yaml","purpose":"验证StartError Pod的当前状态和容器状态","collected":false,"source":"planned","outcome":"unknown"},{"id":"g2-cross-node-secret","description":"主异常组g2: 检查default namespace中是否有imagePullSecrets相关的Secret","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get secrets -n default","purpose":"确认是否有镜像拉取凭据","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_10","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_11","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/8 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-representa... | critical | ✅ | kubectl_describe | 主异常组g2: 从ImagePullBackOff/ErrImagePull组选代表Pod... | `kubectl describe pod -n aiops-e2e test-dns-1779360358` |
   | g1-image | critical | ✅ | kubectl_get_yaml | 主异常组g2: 查看代表Pod的镜像配置，验证镜像地址是否正确 | `kubectl get pod -n aiops-e2e test-dns-1779360358 -o yaml` |
   | g1-other-node2 | important | ✅ | kubectl_describe | 主异常组g2: 选一个node2上的ErrImagePull Pod(connectivi... | `kubectl describe pod -n default connectivity-check-tmp` |
   | g2-crashloop | important | ✅ | kubectl_describe | 异常组g1(CrashLoopBackOff): 对rc-notready-livenes... | `kubectl describe pod -n aiops-e2e rc-notready-liveness` |
   | g2-logs | important | ✅ | run_bash_command | 异常组g1(CrashLoopBackOff): 查看rc-notready-livene... | `kubectl logs -n aiops-e2e rc-notready-liveness --previous` |
   | g3-terminating | important | ✅ | kubectl_get_yaml | 异常组g3(Terminating): 查看net-test-evidence的YAML确... | `kubectl get pod -n default net-test-evidence -o yaml` |
   | g3-terminating-2 | important | ✅ | kubectl_get_yaml | 异常组g3(Terminating): 查看registry-connect-verify... | `kubectl get pod -n default registry-connect-verify -o yaml` |
   | g4-start-error | optional | ❌ | kubectl_get_yaml | 异常组g4(StartError): 查看node-debugger-node1-nx8g... | `kubectl get pod -n mcp node-debugger-node1-nx8gb -o yaml` |
   | g2-cross-node... | important | ✅ | kubectl_get_by_kind_in_na... | 主异常组g2: 检查default namespace中是否有imagePullSecre... | `kubectl get secrets -n default` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (26.0s)
   📤 → 下游数据: root_cause=集群主异常（g2组~56个Pod）的根本原因是节点到docker.io的公网出口网络不通。关键证据：(1) connectivity-check-tmp（default/node2）拉取busybox:1.36.1失败，7次尝试均i/o timeout到registry-1.docker.io:443（IP: 199.96.62.17, 69.30.25.21, 108.160.169.181等）；(2) test-dns-1779360358（aiops-e2e/node1）相同i/o timeout（dial tcp 69.63.184.142:443），持续13小时重试1953次；(3) 镜像地址busybox:1.36.1为有效公开镜像，所有命名空间无imagePullSecrets，排除镜像地址错误和认证问题；(4) 跨node1/node2、跨命名空间(default/aiops-e2e/mcp)一致故障，排除单节点路由问题。另有两个次要独立问题：(a) rc-notready-liveness（aiops-e2e）为人工e2e测试Pod（标签pod_abnormal_ty
... 截断，原始 791 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1、node2）无法通过公网访问 registry-1.docker.io:443，所有到docker.io的TCP连接均超时（i/o timeout），导致所有使用docker.io镜像（busybox:1.36.1等）的Pod无法拉取镜像，表现为ImagePullBackOff/ErrImagePull", "propagation": "集群出口网络不通 → containerd拉取镜像时DNS解析registry-1.docker.io成功但TCP连接超时 → kubelet重试多次后标记为ImagePullBackOff/ErrImagePull → 持续13小时无法恢复 → 同一根因也导致Terminating Pod（net-test-evidence、registry-connect-verify）卡住（容器创建阶段因镜像拉取超时未完成，删除流程等待中）→ rc-notready-liveness为独立e2e测试Pod（Liveness probe故意失败），与网络问题无关 → node-debugger-node1-nx8gb为独立容器镜像/命令问题 → observability-kibana为独立ephemeral-storage Eviction", "direct_cause": "集群节点无法与registry-1.docker.io:443建立TCP连接，所有使用busybox:1.36.1镜像的Pod拉取失败，返回i/o timeout", "manifestation": "用户可见：default/aiops-e2e/mcp命名空间共~56个Pod处于ImagePullBackOff(29)或ErrImagePull(27)状态，另外2个Pod处于Terminating卡住状态（net-test-evidence、registry-connect-verify），1个Pod处于CrashLoopBackOff（rc-notready-liveness为预期测试），1个Pod处于StartError（node-debugger-node1-nx8gb），1个Pod被Evicted（observability-kibana）"}
   rca_analysis={"phenomenon": "集群中存在约60个异常Pod，主要分布在default、aiops-e2e、mcp、xnet命名空间。主异常组g2（56个Pod）处于ImagePullBackOff/ErrImagePull状态，为busybox:1.36.1镜像拉取超时。异常组g1（aiops-e2e/rc-notready-liveness）处于CrashLoopBackOff，由Liveness probe故意失败导致。异常组g3（2个Pod）处于Terminating卡住状态。异常组g4（mcp/node-debugger-node1-nx8gb）处于StartError，因容器内curl命令不存在。另有xnet/observability-kibana被Evicted（ephemeral-storage不足）。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe -n default connectivity-check-tmp", "content": "Pod Pending, 容器状态Waiting(ErrImagePull), 7次拉取busybox:1.36.1均i/o timeout到registry-1.docker.io:443 (IPs: 199.96.62.17等5个地址)", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe -n aiops-e2e test-dns-1779360358", "content": "Pod Pending, BackOff x1953 over 13h, Failed with i/o timeout dial tcp 69.63.184.142:443", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml test-dns-1779360358", "content": "镜像busybox:1.36.1, imagePullPolicy=IfNotPresent, imagePullSecrets=absent, 无finalizers", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_by_kind_in_namespace Secret -n default", "content": "无dockerconfigjson类型Secret, docker_secret_count=0", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe -n aiops-e2e rc-notready-liveness", "content": "Running状态但Liveness probe故意失败(exit code 137), 标签pod_abnormal_type=NotReadyProbeFailed, 有runbook标注", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_yaml net-test-evidence", "content": "deletionTimestamp已设, deletionGracePeriodSeconds=30, finalizers=无, 容器状态ContainerCreating因镜像拉取卡住", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_yaml registry-connect-verify", "content": "deletionTimestamp已设, deletionGracePeriodSeconds=30, finalizers=无, 容器状态ContainerCreating因镜像拉取卡住", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe -n mcp node-debugger-node1-nx8gb", "content": "StartError: exec 'curl' not found in $PATH, 镜像busybox:1.36, command=curl -s -o /dev/null ...", "reliability": "高"}, {"id": "e9", "source": "kubectl_get_yaml node-debugger-node1-nx8gb", "content": "镜像busybox:1.36(非1.36.1), command=curl, imagePullPolicy=IfNotPresent", "reliability": "高"}, {"id": "e10", "source": "kubectl_describe -n xnet observability-kibana", "content": "Evicted due to ephemeral-storage不足, Threshold: 46993491787, available: 45494108Ki", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "7次拉取busybox:1.36.1均i/o timeout到registry-1.docker.io:443 (199.96.62.17等)", "interpretation": "集群节点(node2)到docker.io的公网出口TCP 443端口不通，这是镜像拉取失败的直接证据"}, {"evidence_id": "e2", "raw_data": "BackOff x1953 over 13h, dial tcp 69.63.184.142:443: i/o timeout", "interpretation": "node1上同样出现相同模式的i/o timeout，确认不是单节点问题，而是集群级出口网络问题持续了13小时以上"}, {"evidence_id": "e3", "raw_data": "image=busybox:1.36.1, imagePullSecrets=absent", "interpretation": "镜像地址正确(busybox官方镜像)，无认证需求；排除镜像地址错误和认证失败两个候选场景"}, {"evidence_id": "e4", "raw_data": "docker_secret_count=0, 无dockerconfigjson类型Secret", "interpretation": "default/aiops-e2e/mcp命名空间均无镜像拉取凭证，但镜像为公开镜像busybox，此因素可排除"}, {"evidence_id": "e5", "raw_data": "Exit Code 137, Liveness probe failed: liveness endpoint failed, 标签pod_abnormal_type=NotReadyProbeFailed", "interpretation": "该Pod是人工部署的e2e测试Pod，Liveness probe被故意配置为失败以模拟CrashLoopBackOff场景，不是真实故障"}, {"evidence_id": "e6", "raw_data": "deletionTimestamp=2026-05-22T00:23:34Z, finalizers=无, ContainerCreating", "interpretation": "Terminating卡住是因为容器尚未完成创建（镜像拉取超时卡住ContainerCreating阶段），没有finalizer堵塞；deletionGracePeriodSeconds=30s到期后由于容器未就绪，kubelet无法完成清理"}, {"evidence_id": "e7", "raw_data": "deletionTimestamp=2026-05-22T00:16:24Z, finalizers=无, ContainerCreating", "interpretation": "与e6完全相同的终止卡住场景，根因同样是镜像拉取超时导致容器创建未完成"}, {"evidence_id": "e8", "raw_data": "exec: 'curl': executable file not found in $PATH", "interpretation": "容器使用busybox:1.36镜像，但command要求执行curl命令，而busybox镜像中不包含curl，导致StartError"}, {"evidence_id": "e9", "raw_data": "image=busybox:1.36, command=[curl -s -o /dev/null ...]", "interpretation": "确认镜像版本为busybox:1.36（非1.36.1），busybox镜像默认不带curl，容器启动即失败"}, {"evidence_id": "e10", "raw_data": "Evicted, ephemeral-storage不足, Threshold: 46993491787, available: 45494108Ki", "interpretation": "master节点ephemeral-storage资源不足导致Pod被驱逐，这是一个独立的L0问题，与镜像拉取问题无关"}], "causal_chain": {"root_cause": "集群节点（node1、node2）无法通过公网访问 registry-1.docker.io:443，所有到docker.io的TCP连接均超时（i/o timeout），导致所有使用docker.io镜像（busybox:1.36.1等）的Pod无法拉取镜像，表现为ImagePullBackOff/ErrImagePull", "propagation": "集群出口网络不通 → containerd拉取镜像时DNS解析registry-1.docker.io成功但TCP连接超时 → kubelet重试多次后标记为ImagePullBackOff/ErrImagePull → 持续13小时无法恢复 → 同一根因也导致Terminating Pod（net-test-evidence、registry-connect-verify）卡住（容器创建阶段因镜像拉取超时未完成，删除流程等待中）→ rc-notready-liveness为独立e2e测试Pod（Liveness probe故意失败），与网络问题无关 → node-debugger-node1-nx8gb为独立容器镜像/命令问题 → observability-kibana为独立ephemeral-storage Eviction", "direct_cause": "集群节点无法与registry-1.docker.io:443建立TCP连接，所有使用busybox:1.36.1镜像的Pod拉取失败，返回i/o timeout", "manifestation": "用户可见：default/aiops-e2e/mcp命名空间共~56个Pod处于ImagePullBackOff(29)或ErrImagePull(27)状态，另外2个Pod处于Terminating卡住状态（net-test-evidence、registry-connect-verify），1个Pod处于CrashLoopBackOff（rc-notready-liveness为预期测试），1个Pod处于StartError（node-debugger-node1-nx8gb），1个Pod被Evicted（observability-kibana）"}, "root_cause": "集群主异常（g2组~56个Pod）的根本原因是节点到docker.io的公网出口网络不通。关键证据：(1) connectivity-check-tmp（default/node2）拉取busybox:1.36.1失败，7次尝试均i/o timeout到registry-1.docker.io:443（IP: 199.96.62.17, 69.30.25.21, 108.160.169.181等）；(2) test-dns-1779360358（aiops-e2e/node1）相同i/o timeout（dial tcp 69.63.184.142:443），持续13小时重试1953次；(3) 镜像地址busybox:1.36.1为有效公开镜像，所有命名空间无imagePullSecrets，排除镜像地址错误和认证问题；(4) 跨node1/node2、跨命名空间(default/aiops-e2e/mcp)一致故障，排除单节点路由问题。另有两个次要独立问题：(a) rc-notready-liveness（aiops-e2e）为人工e2e测试Pod（标签pod_abnormal_ty\n... 截断，原始 791 字符", "root_cause_summary": "集群主异常（g2组~56个Pod）的根本原因是节点到docker.io的公网出口网络不通。关键证据：(1) connectivity-check-tmp（default/node2）拉取busybox:1.36.1失败，7次尝试均i/o timeout到registry-1.docker.io:443（IP: 199.96.62.17, 69.30.25.21, 108.160.169.181等）；(2) test-dns-1779360358（aiops-e2e/node1）相同i/o timeout（dial tcp 69.63.184.142:443），持续13小时重试1953次；(3) 镜像地址busybox:1.36.1为有效公开镜像，所有命名空间无imagePullSecrets，排除镜像地址错误和认证问题；(4) 跨node1/node2、跨命名空间(default/aiops-e2e/mcp)一致故障，排除单节点路由问题。另有两个次要独立问题：(a) rc-notready-liveness（aiops-e2e）为人工e2e测试Pod（标签pod_abnormal_ty\n... 截断，原始 791 字符", "confidence": 0.95, "confidence_reason": "有直接证据：多个Pod的describe明确显示i/o timeout错误（e1、e2），跨节点跨命名空间一致验证（e3排除镜像地址，e4排除认证），因果链清晰完整。rc-notready-liveness通过标签和runbook确认是测试Pod。StartError和Evicted均有明确的kubelet错误消息。置信度0.95。", "primary_runbooks": [], "alternative_causes": [{"cause": "镜像地址或tag不存在", "probability": "low", "reason": "已被e3排除：busybox:1.36.1为有效公开镜像，且错误类型为i/o timeout而非manifest not found"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "已被e4排除：busybox为公开镜像无需认证，各命名空间均无dockerconfigjson Secret"}, {"cause": "DNS解析故障导致无法解析registry-1.docker.io", "probability": "low", "reason": "错误消息中显示已解析到具体IP地址（199.96.62.17等），说明DNS解析成功，故障在TCP连接层"}, {"cause": "Calico网络策略限制出口流量", "probability": "low", "reason": "Pod已成功获得Calico IP并完成CNI初始化，无网络策略相关事件；但未验证集群级egress网络策略，概率较低"}], "limitations": "缺失证据：未验证集群的出口网络配置（NAT网关、防火墙规则、代理配置等），无法确定i/o timeout的具体网络瓶颈位置。未验证其他镜像仓库（如registry.k8s.io、gcr.io）的连通性作为对照。未采集集群节点级别的网络连通性测试（如从节点直接curl registry-1.docker.io）。Terminating Pod的证据仅基于YAML和状态，未检查对应节点kubelet状态。", "llm_raw_analysis": "## 证据清点\n共计10条关键证据，覆盖所有4个异常组(g1-g4)和1个独立异常(observability-kibana Evicted)。\n\n## 逐条分析\n- **e1/e2**: 直接证明镜像拉取失败的根因是i/o timeout到registry-1.docker.io:443，跨节点一致\n- **e3/e4**: 排除镜像地址错误和认证失败两个候选场景，缩小根因范围到网络层\n- **e5**: 确认rc-notready-liveness为人工测试Pod，非真实故障\n- **e6/e7**: Terminating卡住的Pod无finalizer，根因是镜像拉取超时导致容器未创建完成\n- **e8/e9**: StartError因busybox:1.36镜像不含curl命令\n- **e10**: Evicted因ephemeral-storage不足，独立于主问题\n\n## 关联分析\n主异常组g2(~56个Pod)共享同一根因：集群出口到docker.io的网络不通。g3的2个Terminating Pod是g2根因的次级影响（镜像拉不下来的同时被删除导致卡住）。g1(C\n... 截断，原始 687 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群主异常（g2组~56个Pod）的根本原因是节点到docker.io的公网出口网络不通。关键证据：(1) connectivity-check-tmp（default/node2）拉取busybox:1.36.1失败，7次尝试均i/o timeout到registry-1.docker.io:44...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1、node2）无法通过公网访问 registry-1.docker.io:443，所有到docker.io的TCP连接均超时（i/o timeout），导致所有使用docker.io镜像（busybox:1.36.1等）的Pod无法拉取镜像，表现为ImagePullBackOff/ErrImagePull
     传导机制: 集群出口网络不通 → containerd拉取镜像时DNS解析registry-1.docker.io成功但TCP连接超时 → kubelet重试多次后标记为ImagePullBackOff/ErrImagePull → 持续13小时无法恢复 → 同一根因也导致Terminating Pod（net-test-evidence、registry-connect-verify）卡住（容器创建阶段因镜像拉取超时未完成，删除流程等待中）→ rc-notready-liveness为独立e2e测试Pod（Liveness probe故意失败），与网络问题无关 → node-debugger-node1-nx8gb为独立容器镜像/命令问题 → observability-kibana为独立ephemeral-storage Eviction
     最终表现: 用户可见：default/aiops-e2e/mcp命名空间共~56个Pod处于ImagePullBackOff(29)或ErrImagePull(27)状态，另外2个Pod处于Terminating卡住状态（net-test-evidence、registry-connect-verify），1个Pod处于CrashLoopBackOff（rc-notready-liveness为预期测试），1个Pod处于StartError（node-debugger-node1-nx8gb），1个Pod被Evicted（observability-kibana）


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (30.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8356 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 46.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 当前集群状态与问题总结

您的集群总计约 **127 个 Pod** 分布在 `admin`、`aiops-e2e`、`aiops`、`default`、`kube-system`、`mcp`、`xnet` 等命名空间。**系统级 Pod（Calico、CoreDNS、kube-apiserver 等 60 个）运行正常**。

| 问题分类 | 数量 | 严重程度 | 作用范围 |
|---------|------|---------|---------|
| 🚨 **镜像拉取失败（ImagePullBackOff / ErrImagePull）** | **56 个 Pod** | ❌ 致命 | default、aiops-e2e、mcp 命名空间 |
| ⏳ **Terminating 卡住** | **2 个 Pod** | ⚠️ 次要 | default 命名空间 |
| 🔄 **CrashLoopBackOff（Liveness Probe 失败）** | **1 个 Pod** | ℹ️ 已知/测试 Pod | aiops-e2e 命名空间 |
| ❌ **StartError（容器启动命令错误）** | **1 个 Pod** | ℹ️ 个例 | mcp 命名空间 |
| 🗑️ **Evicted（节点磁盘不足）** | **1 个 Pod** | ℹ️ 已清理 | xnet 命名空间 |

**核心结论**：集群**主问题是所有节点无法访问 docker.io 公网镜像仓库**，导致 56 个测试/诊断 Pod 镜像拉取失败，且其中 2 个 Pod 因此卡在 Terminating 状态。其余 3 个异常为独立个例。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff (29)、ErrImagePull (27)、Terminating (2)、CrashLoopBackOff (1)、StartError (1)、Evicted (1) |
| **兼容归因层** | L3 - 镜像问题（主）+ L0（个例）+ L4（个例） |
| **问题分类** | **镜像拉取失败（网络不可达）** |
| **置信度** | **高 (95%)** |
| **证据完整度** | 8/8 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| 问题命名空间 | `default`、`aiops-e2e`、`mcp` |
| 受影响节点 | `node1` (10.2.0.49)、`node2` (10.2.0.50) |
| 目标镜像 | `docker.io/library/busybox:1.36.1` |
| 根因错误 | `i/o timeout` 到 `registry-1.docker.io:443` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 (connectivity-check-tmp) | `kubectl describe pod` | `Reason: ErrImagePull`, 7次拉取均 `i/o timeout` 到 `registry-1.docker.io:443`，IPs: 199.96.62.17, 69.30.25.21, 108.160.169.181 等 | **node2 无法连接 docker.io，TCP 超时** |
| 2 | Pod 状态 (test-dns-1779360358) | `kubectl describe pod` | `ImagePullBackOff`, `Back-off pulling image "busybox:1.36.1"`, 重试 1953 次持续 13 小时 | **node1 同样无法连接 docker.io，问题跨节点** |
| 3 | 镜像配置 | `kubectl get pod -o yaml` | 镜像地址为 `busybox:1.36.1`，是有效公开镜像 | **排除镜像地址错误** |
| 4 | Secret 检查 | `kubectl get secret` | default 命名空间**没有** `kubernetes.io/dockerconfigjson` 或 `dockercfg` 类型的 Secret | **排除镜像认证问题** |
| 5 | 节点分布 | 综合 describe | 问题 Pod 分布在 node1 和 node2，跨 `default/aiops-e2e/mcp` 命名空间 | **不是单节点或单命名空间问题** |
| 6 | Pod YAML (net-test-evidence) | `kubectl get pod -o yaml` | `deletionTimestamp: 2026-05-22T00:23:34Z`, `deletionGracePeriodSeconds: 30`, `finalizers: <none>` | **排除 finalizer 导致 Terminating，容器因镜像拉取失败未完成初始化** |
| 7 | Pod YAML (registry-connect-verify) | `kubectl get pod -o yaml` | 同上，`deletionTimestamp: 2026-05-22T00:16:24Z`, `finalizers: <none>` | **同理，镜像拉取超时导致删除卡住** |
| 8 | Pod 描述 (rc-notready-liveness) | `kubectl describe pod` | `Exit Code: 137`, `Liveness probe failed (x10)`, `Back-off restarting (x67)`, 注解 `aiops.e2e/runbook: pod-notready-probe-failed.md` | **是 e2e 测试 Pod，Liveness probe 故意失败，与主问题无关** |
| 9 | Pod 描述 (node-debugger-node1-nx8gb) | `kubectl describe pod` | `Message: failed to create containerd task: OCI runtime exec failed: exec: "curl" not found in $PATH` | **容器镜像缺少 `curl` 命令，独立问题** |
| 10 | Pod 描述 (observability-kibana) | `kubectl describe pod` | `reason: Evicted`, `message: The node was low on resource: ephemeral-storage. Threshold: 46993491787, available: 45494108Ki` | **节点 master 临时存储不足导致驱逐** |

### 证据关联分析

- **证据 #1 + #2 + #5 印证**：跨节点（node1、node2）、跨命名空间的 Pod 拉取 `busybox:1.36.1` 均出现 `i/o timeout`，确认是**集群级公网出口网络问题**。
- **证据 #3 + #4 排除**：镜像地址正确且无认证配置，排除镜像配置和认证问题。
- **证据 #6 + #7 确认**：两个 Terminating Pod 的 `finalizers: <none>`，排除 finalizer 未清理；`deletionGracePeriodSeconds: 30` 正常，卡住原因是容器从未成功启动，删除流程在等待容器终止。
- **证据 #8**：独立的 e2e 测试 Pod（CrashLoopBackOff），其注解表明为预期行为。
- **证据 #9**：`curl` 未在容器 PATH 中找到，镜像差异问题。
- **证据 #10**：master 节点磁盘压力，独立事件。

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| 集群出口网络配置（NAT、防火墙、代理） | critical | 无法定位网络瓶颈具体位置（如缺 SNAT 规则、防火墙拦截） |
| 节点直接对 docker.io 的连通性测试 | important | 不能从节点层独立验证 `curl registry-1.docker.io` |
| 其他镜像仓库（registry.k8s.io、gcr.io）连通性 | optional | 无法判断是所有公网不通还是仅 docker.io |

---

## 🎯 根因分析

### 因果链

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                          │
│ 集群节点（node1、node2）到 registry-1.docker.io:443 的公网出口 TCP 不通            │
│ 7 次拉取尝试均 i/o timeout（超时 IPs: 199.96.62.17, 69.30.25.21, 108.160.169.181 等）│
└───────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ DNS 解析成功（registry-1.docker.io → IP） → TCP 连接 443 端口超时失败        │
│ → containerd 无其他 registry 镜像源 → 持续重试 13h（1953 次） → 最终超时    │
└────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 所有使用 docker.io/busybox:1.36.1 镜像的 Pod 拉取失败，状态为 ImagePullBackOff    │
│ 或 ErrImagePull，持续无法恢复                                                │
└────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                  │
│ default/aiops-e2e/mcp 共 56 个 Pod 处于 ImagePullBackOff/ErrImagePull          │
│ 2 个 Pod（net-test-evidence、registry-connect-verify）卡在 Terminating       │
│ 其余 3 个为独立个例：e2e 测试、镜像命令错误、节点 Evicted                      │
└────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：集群**所有节点（node1、node2）到 docker.io 的公网出口网络不通**，导致所有使用 `busybox:1.36.1` 等 docker.io 镜像的 Pod 拉取失败。

**关键证据链**：
- **证据 #1**：`connectivity-check-tmp` (node2) 拉取失败：`i/o timeout`（IP: 199.96.62.17, 69.30.25.21, 108.160.169.181, 108.160.165.173, 128.242.245.125）
- **证据 #2**：`test-dns-1779360358` (node1) 拉取失败：`i/o timeout`，13 小时重试 1953 次
- **证据 #3** + **#4**：排除镜像地址和认证原因
- **证据 #5**：跨节点、跨命名空间一致故障，排除局部问题

**置信度**：**高 (95%)**
- ✅ 直接抓取到 TCP i/o timeout 的明确错误
- ✅ 两个节点、四个命名空间一致症状
- ✅ 镜像地址正确、无认证问题
- ⚠️ 未验证出口网络具体配置（NAT/防火墙/代理）

---

## 🛠️ 修复建议

### 立即执行

#### 1. [🔴 优先] 恢复集群公网出口网络

请检查集群节点的**出站网络配置**（以下为排查命令，非根因修复）：

```bash
# 在任意集群节点上执行（需 SSH 登录）
# 验证到 registry-1.docker.io 的连通性
curl -v https://registry-1.docker.io/v2/ 2>&1 | head -20

# 或使用 telnet 测试端口
timeout 5 telnet registry-1.docker.io 443

# 测试其他公网地址以区分问题范围
curl -v https://registry.k8s.io/v2/ 2>&1 | head -10
```

**预期排查方向**：
- ✅ **检查 NAT 网关**：是否缺少 Docker Hub 的 SNAT 规则
- ✅ **检查防火墙/安全组**：是否拦截了目标 IP 的 443 端口出站
- ✅ **检查代理配置**：节点是否配置了 HTTP_PROXY（`echo $HTTP_PROXY` / `cat /etc/environment | grep proxy`）
- ✅ **检查 DNS 解析**：`nslookup registry-1.docker.io` 是否正常返回 IP

#### 2. [🟠 立即] 强制清理卡在 Terminating 的 Pod

```bash
# 强制删除（无需等待宽限期）
kubectl delete pod net-test-evidence -n default --force --grace-period=0
kubectl delete pod registry-connect-verify -n default --force --grace-period=0
```

#### 3. [🟡 确认] 检查独立个例

```bash
# 查看 e2e 测试 Pod（预期行为，如非测试可忽略）
kubectl logs rc-notready-liveness -n aiops-e2e --previous | tail -10

# 查看 node-debugger StartError（容器内无 curl 命令）
kubectl get pod node-debugger-node1-nx8gb -n mcp -o yaml | grep -A5 command

# 确认 Evicted Pod 是否已删除
kubectl get pods -n xnet | grep observability-kibana
```

### 后续优化

1. **监控网络出口**：配置集群出口网络监控（如 Prometheus Blackbox Exporter 探测 registry-1.docker.io）
2. **使用镜像缓存/代理**：在集群内部署 Harbor 或 Sonatype Nexus 作为镜像缓存代理，减少公网依赖
3. **资源预留**：master 节点 ephemeral-storage 设置告警（>80% 发告警）

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 修复出口网络后查看 Pod | `kubectl get pods --all-namespaces \| grep -E "ImagePullBackOff\|ErrImagePull"` | 数量逐步减少 |
| 2. 强制删除 Terminating Pod | `kubectl delete pod net-test-evidence -n default --force --grace-period=0` | `pod "net-test-evidence" deleted` |
| 3. 检查节点网络 | 节点 `curl registry-1.docker.io` | 返回 HTTP 200 |
| 4. 确认独立个例可忽略 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | Running（重启计数稳定） |

---

## ⚠️ 注意事项

- **根因不是镜像或 Pod 配置错误**，而是**底层网络基础设施问题**（节点无法出站到 docker.io），需协调网络运维团队排查出口防火墙、NAT 规则或代理配置
- 集群中的 **Calico、CoreDNS、kube-apiserver 等 60 个系统 Pod 运行正常**，说明集群内部网络和 Kubernetes 控制面未受影响
- `rc-notready-liveness` Pod 标注了 `aiops.e2e/runbook: pod-notready-probe-failed.md`，是人为的 e2e 测试，无需处理
- 如果集群无公网访问需求（如离线环境），建议将所有镜像切换到私有仓库或镜像代理，彻底消除此问题

---

## 📊 性能统计

├─ 总耗时: 2.8m
├─ 问题定位: 47.8s (29%) ✅
├─ 证据链采集: 62.5s (38%) ✅
├─ 根因分析: 26.0s (16%) ✅
├─ 汇总总结: 30.3s (18%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 36 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 36 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
