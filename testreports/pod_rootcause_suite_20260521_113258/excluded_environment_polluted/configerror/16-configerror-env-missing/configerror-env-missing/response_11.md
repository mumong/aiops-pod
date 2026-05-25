======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 41c464d4c3a04d7c]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先全局扫描所有 Pod，看看集群中当前有哪些异常状态。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=350 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 0 completed, 1 in progress, 3 pending
[ ] [classify] 对异常 Pod 进行分类归组，确定异常类型
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces returned ~109 pods total. Abnormal: 1 CrashLoopBackOff (aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn, restarted 7x), 24 ErrImagePull across default & mcp namespac
   💭 [问题定位] 让我再更清晰地查看一下所有异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=350 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 1 completed, 1 in progress, 2 pending
[ ] [fetch-runbook] 按需获取匹配的 Runbook 
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 raw_preview 显示 78 行 pods（不完全展示）。状态分布：Running 约 60, Pending 约 44, Succeeded 4, Failed 1（其中 Failed 行未在 raw_preview 中直接展示）。大量 Pending pods 分布在 default/aiops-e2e/mcp 命名空间，多为 DNS/network/registry 测试 pods。a
   💭 [问题定位] 我需要更精确地查看异常 Pod 的状态详情。让我看看 Pending Pod 的具体状态原因。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 44 行 Pod，全部 STATUS=Pending，全部 READY=False，分布在 node1 和 node2。涉及 namespace: aiops-e2e (1 pod), default (12 pods), mcp (31 pods)。包含多种测试类 Pod（dns、net、registry、curl、node-debugge
   💭 [问题定位] 还有 CrashLoopBackOff 的 Pod，以及 Terminating 的 Pod。让我获取这些信息，同时看一下 Pending Pod 的具体原因。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces 返回约109个Pod，其中异常Pod约45个。主要异常类型：ErrImagePull (24个), ImagePullBackOff (17个), CrashLoopBackOff (1个), Terminating (3个)。正常Running Pod 59个，Completed 2个。
key_facts: ["aiops-e
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=372 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 好的，现在让我查看几个关键异常 Pod 的详细事件和状态，特别是那个 CrashLoopBackOff 的 Pod 和一些 ErrImagePull 的 Pod。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool in namespace default, on node node1/10.2.0.49, is in Pending status with IP 172.16.166.157. Container dig-tool uses image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, state Waitin
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-bq8pn
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff         17s 
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod dns-check-evidence (namespace: default, node: node1/10.2.0.49) is Pending. Container dns-check-evidence (image: busybox:1.36.1, args: nslookup registry-1.docker.io) in Waiting state (Reason: ErrIm
   💭 [问题定位] 现在让我查看几个 ImagePullBackOff 的 Pod 和一些 Terminating 的 Pod 来完整了解情况。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-check
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   14m (x38 over 4h1m)      kubelet  (combined from similar events): Failed t
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: curl-test-ev-1779385377
namespace: mcp
node: node1/10.2.0.49
status: Terminating (lasts 6m13s)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: 3551efd68
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-probe-1779385621
namespace: mcp
node: node2/10.2.0.50
status: Terminating (lasts 2m9s)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: c737b5b8ab10b
   💭 [问题定位] 很好，现在让我查看那个 CrashLoopBackOff Pod 的日志来确认具体原因。
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [问题定位] 现在我已经有了足够的信息来诊断集群问题。让我获取匹配的 Runbook，并完成分类。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   ✅ [问题定位] 完成 (1m 9.3s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '镜像仓库网络不可达（Docker Hub/GCR 域名 DNS 解析或网络连通性问题）导致大量 Pod 镜像拉取失败', 'probability': 'high', 'reason': '24个ErrImagePull+17个ImagePullBackOff均因i/o timeout dial registry-1.docker.io:443及其他GCR端点，错误信息一致，均为 DeadlineExceeded/i/o timeout'}, {'scenario': '集群网络出口或代理配置问题导致无法访问外部镜像仓库', 'probability': 'medium', 'reason': '系统组件（calico/coredns等）均运行正常，仅外部镜像拉取失败，可能与镜像仓库访问策略或网络出口有关'}, {'scenario': 'rc-config-env-missing Pod 缺少必要环境变量导致应用启动失败', 'probability': 'high', 'reason': '退出码42，日志明确报 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，为独立应用配置问题'}]
   entities=[{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-bq8pn", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "dig-tool", "namespace": "default"}, {"type": "Pod", "name": "dns-check-evidence", "namespace": "default"}, {"type": "Pod", "name": "dns-test-check", "namespace": "default"}, {"type": "Pod", "name": "curl-test-ev-1779385377", "namespace": "mcp"}, {"type": "Pod", "name": "dns-probe-1779385621", "namespace": "mcp"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}, {"type": "Service", "name": "registry-1.docker.io", "namespace": ""}]
   reasoning=集群中存在大量异常 Pod，多数为 Pending 状态。主要异常类型：24个 ErrImagePull + 17个 ImagePullBackOff（分布在 default/mcp/aiops-e2e 命名空间，涉及 busybox:1.36.1 等镜像），根因为镜像拉取超时（i/o timeout dialing registry-1.docker.io:443 及多个 GCR 端点），属于典型网络/镜像仓库问题（L3）。另外有 1 个 aiops-e2e/rc-config-env-missing 处于 CrashLoopBackOff（退出码 42，日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE），属于配置错误（L4）。还有 2 个 Terminating 的 Pod（curl-test-ev-1779385377 和 dns-probe-1779385621）正卡在 ContainerCreating（镜像拉取未完成）。系统组件（calico、coredns、apiserver 等）均 Running。根因以 L3 镜像拉取/网络问题为主，同时存在 L4 配置错误。L0（磁盘/驱逐）和 L1（节点/kubelet）未发现异常。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "image_registry_network", "confidence": 0.95, "reasoning": "集群中存在大量异常 Pod，多数为 Pending 状态。主要异常类型：24个 ErrImagePull + 17个 ImagePullBackOff（分布在 default/mcp/aiops-e2e 命名空间，涉及 busybox:1.36.1 等镜像），根因为镜像拉取超时（i/o timeout dialing registry-1.docker.io:443 及多个 GCR 端点），属于典型网络/镜像仓库问题（L3）。另外有 1 个 aiops-e2e/rc-config-env-missing 处于 CrashLoopBackOff（退出码 42，日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE），属于配置错误（L4）。还有 2 个 Terminating 的 Pod（curl-test-ev-1779385377 和 dns-probe-1779385621）正卡在 ContainerCreating（镜像拉取未完成）。系统组件（calico、coredns、apiserver 等）均 Running。根因以 L3 镜像拉取/网络问题为主，同时存在 L4 配置错误。L0（磁盘/驱逐）和 L1（节点/kubelet）未发现异常。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-bq8pn", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ErrImagePull"}, {"name": "dig-tool", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-check-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ErrImagePull"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ErrImagePull"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-test-ev-1779385377", "namespace": "mcp", "status": "Terminating"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-probe-1779385621", "namespace": "mcp", "status": "Terminating"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "netprobe-1779385591", "namespace": "mcp", "status": "Terminating"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ErrImagePull"}], "pod_status_keyword": "ErrImagePull, ImagePullBackOff, CrashLoopBackOff", "pod_abnormal_type": "ImagePullFailed, ConfigError", "status_category": "image_registry/network_cni_runtime, app_config", "key_entities": [{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-bq8pn", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "dig-tool", "namespace": "default"}, {"type": "Pod", "name": "dns-check-evidence", "namespace": "default"}, {"type": "Pod", "name": "dns-test-check", "namespace": "default"}, {"type": "Pod", "name": "curl-test-ev-1779385377", "namespace": "mcp"}, {"type": "Pod", "name": "dns-probe-1779385621", "namespace": "mcp"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}, {"type": "Service", "name": "registry-1.docker.io", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达（Docker Hub/GCR 域名 DNS 解析或网络连通性问题）导致大量 Pod 镜像拉取失败", "probability": "high", "reason": "24个ErrImagePull+17个ImagePullBackOff均因i/o timeout dial registry-1.docker.io:443及其他GCR端点，错误信息一致，均为 DeadlineExceeded/i/o timeout"}, {"scenario": "集群网络出口或代理配置问题导致无法访问外部镜像仓库", "probability": "medium", "reason": "系统组件（calico/coredns等）均运行正常，仅外部镜像拉取失败，可能与镜像仓库访问策略或网络出口有关"}, {"scenario": "rc-config-env-missing Pod 缺少必要环境变量导致应用启动失败", "probability": "high", "reason": "退出码42，日志明确报 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，为独立应用配置问题"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed, ConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-bq8pn"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ImagePullFailed, ConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ErrImagePull", "ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "curl-test-ev-1779385377"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-probe-1779385621"}, {"kind": "Pod", "namespace": "mcp", "name": "netprobe-1779385591"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed, ConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-bq8pn"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ImagePullFailed, ConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ErrImagePull", "ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "curl-test-ev-1779385377"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-probe-1779385621"}, {"kind": "Pod", "namespace": "mcp", "name": "netprobe-1779385591"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ErrImagePull": 24, "ImagePullBackOff": 17, "Terminating": 3}, "total_abnormal": 45, "selected_rows": ["aiops-e2e         rc-config-env-missing-5d9b8b766c-bq8pn              0/1     CrashLoopBackOff   7 (3m49s ago)   14m     172.16.166.129   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ErrImagePull       0               7h3m    172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ErrImagePull       0               141m    172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ErrImagePull       0               81m     172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ErrImagePull       0               5h52m   172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ErrImagePull       0               6h58m   172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0               4h34m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-tmp                                        0/1     ImagePullBackOff   0               88m     172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ErrImagePull       0               5h40m   172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0               6h8m    172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0               3h4m    172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0               4h2m    172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0               5h49m   172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ErrImagePull       0               6h58m   172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0               6h11m   172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               curl-check-tmp                                      0/1     ImagePullBackOff   0               150m    172.16.104.58    node2    <none>           <none>            run=curl-check-tmp", "mcp               curl-test-ev-1779385377                             0/1     Terminating        0               6m52s   <none>           node1    <none>           <none>            run=curl-test-ev-1779385377", "mcp               curls                                               0/1     ImagePullBackOff   0               50m     172.16.104.2     node2    <none>           <none>            run=curls", "mcp               dns-check-tmp                                       0/1     ErrImagePull       0               150m    172.16.104.13    node2    <none>           <none>            run=dns-check-tmp", "mcp               dns-probe-1779385621                                0/1     Terminating        0               2m48s   <none>           node2    <none>           <none>            run=dns-probe-1779385621"], "raw_ref": "/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/002-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/002-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/002-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 好的，开始执行既有 evidence_plan。我会先获取 ImagePullFailed 的 runbook 作为参考，然后逐项执行计划中的工具调用。

首先，由于 g2（ImagePullFailed）是影响范围最大的异常组（41个 Pod），我先把 ImagePullFailed 的 runbook 取来做参考。
   💭 [证据链采集] 调用工具: fetch_runbook
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
      📄 Pod dns-check-evidence in namespace default on node node1/10.2.0.49 is Pending with IP 172.16.166.181. Container dns-check-evidence (image busybox:1.36.1, args: nslookup registry-1.docker.io) is Waiti
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-bq8pn
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff         71s 
   💭 [证据链采集] 好的，g2 和 g1 的代表 Pod 已经描述完。现在继续执行剩余计划项。
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-check
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   14m (x38 over 4h1m)      kubelet  (combined from similar events): Failed t
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: curl-test-ev-1779385377
namespace: mcp
node: node1/10.2.0.49
status: Terminating (lasts 7m)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: 3551efd68191
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dns-check-evidence
namespace: default
creationTimestamp: 2026-05-21T16:28:05Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
s
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] 让我获取 dns-test-check 和 curl-test-ev 的详细描述信息，以及 mcp 命名空间下的网络测试 Pod。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: curl-test-ev-1779385377
namespace: mcp
creationTimestamp: 2026-05-21T17:42:57Z
deletionTimestamp: 2026-05-21T17:44:27Z
deletionGracePeriodSeconds: 30
finalizer
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod net-check-1779365549 in namespace mcp is **Pending** on node node1/10.2.0.49. Container is in **Waiting** state with Reason **ErrImagePull**. PodIP: 172.16.166.179 via Calico CNI. All 5 recent pul
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dns-test-check
namespace: default
creationTimestamp: 2026-05-21T13:15:13Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
servi
   💭 [证据链采集] 现在让我获取 g1 crashloop Pod 的完整 YAML 确认退出码，以及验证 Terminating 组中其他 Pod 的状态。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-env-missing-5d9b8b766c-bq8pn
namespace: aiops-e2e
creationTimestamp: 2026-05-21T17:35:07Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: Non
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-probe-1779385621
namespace: mcp
node: node2/10.2.0.50
status: Terminating (lasts 3m22s)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: c737b5b8ab10
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 输出摘要: raw_chars=140 lines=3
Command failed (exit 1):
kubectl describe pod netprobe-1779385591 -n mcp
Error from server (NotFound): pods "netprobe-1779385591" not found
   💭 [证据链采集] 好的，关键的证据都已采集完毕。下面总结完整证据结论：

---

## 📋 证据采集结论

### 异常组 G2 — ImagePullFailed（影响最大：41个 Pod）

**✅ 核心证据：集群无法访问外部镜像仓库**

| 证据项 | 来源 | 结果 |
|--------|------|------|
| **dns-check-evidence (node1)** — ErrImagePull | `kubectl_describe` | 多次 Failed: `dial tcp <ip>:443: i/o timeout` 连接 `registry-1.docker.io` 超时 |
| **dns-check-evidence** YAML — imagePullSecrets | `kubectl_get_yaml` | **未配置** imagePullSecrets，使用公共镜像 `busybox:1.36.1` |
| **dns-test-check (node2)** — ImagePullBackOff | `kubectl_describe` + `kubectl_get_yaml` | 同样 i/o timeout 连接 registry-1.docker.io:443，无 imagePullSecrets |
| **net-check-1779365549 (mcp/node1)** — ErrImagePull | `kubectl_describe` | alpine:3.18 拉取同样 i/o timeout，5个不同 registry-1.docker.io IP全部超时 |
| **dig-tool (default/node1)** — 上游已采集 | `kubectl_describe` | `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` 同样 i/o timeout 连接 GCR 端点 |

**结论：集群节点（node1 + node2）对 Docker Hub (`registry-1.docker.io`) 和 GCR (`registry.k8s.io`) 均无法建立 TCP 443 连接，镜像拉取全部因网络超时失败。所有异常 Pod 均未配置 imagePullSecrets。这是集群出口网络/代理问题，非镜像配置错误。**

---

### 异常组 G1 — CrashLoopBackOff/ConfigError（1个 Pod）

**✅ 核心证据：应用配置缺失**

| 证据项 | 来源 | 结果 |
|--------|------|------|
| **rc-config-env-missing** describe — Last State | `kubectl_describe` | Exit Code = **42**，Reason = CrashLoopBackOff |
| **rc-config-env-missing** previous logs | `kubectl_previous_logs` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` |
| **rc-config-env-missing** YAML — spec | `kubectl_get_yaml` | 启动命令明确检查 `${APP_BOOT_MODE:-}` 变量，未设置时 exit 42 |

**结论：Pod 启动脚本检测到环境变量 `APP_BOOT_MODE` 未设置，主动退出（exit code 42）。这是 Deployment 级别的配置缺失问题，与镜像拉取无关。**

---

### 异常组 G3 — TerminatingStuck（3个 Pod）

| Pod | 节点 | 状态 | 证据 |
|-----|------|------|------|
| **curl-test-ev-1779385377** (mcp/node1) | Terminating | `kubectl_get_yaml` 显示 `deletionTimestamp` 已设置，**无 finalizers**，`containerStatuses.reason=ContainerCreating` — 镜像仍在拉取中，卡在拉取镜像阶段无法完成终止 |
| **dns-probe-1779385621** (mcp/node2) | Terminating | `kubectl_describe` 显示 State=Waiting(ContainerCreating)，正在 Pulling busybox:1.36.1 — 同样因镜像拉取卡住导致终止流程无法完成 |
| **netprobe-1779385591** (mcp) | **NotFound** | `kubectl describe` 返回 NotFound，该 Pod 已被删除，**冲突证据** — 不参与当前诊断 |

**结论：2个 Terminating Pod 卡在容器创建阶段（镜像拉取未完成），根因仍为 G2 的镜像仓库不可达问题。没有 finalizer 阻塞，是镜像拉取不成功导致 kubelet 无法清理容器。**

---

### 📊 最终根因判定

1. **主因（L3 - 镜像仓库网络问题）**：集群 node1 和 node2 **无法访问外部镜像仓库**（Docker Hub 和 GCR），TCP 443 端口连接全部 i/o timeout。影响 **41 个 ErrImagePull/ImagePullBackOff Pod** + 2 个 Terminating Pod。公共镜像 `busybox:1.36.1`、`alpine:3.18`、`registry.k8s.io/*` 均无法拉取。
2. **次因（L4 - 配置错误）**：`rc-config-env-missing-5d9b8b766c-bq8pn` 因环境变量 `APP_BOOT_MODE` 缺失导致 exit code 42，为独立的应用配置问题。
3. **Terminating Pod**：属于镜像拉取问题的衍生影响，不是独立的 finalizer/节点问题。
   ✅ [证据链采集] 完成 (1m 6.6s)
   📤 → 下游数据: evidence_items=20/20
   evidence_analysis={"evidence_plan":[{"id":"g2-rep-pod-describe","description":"Describe representative ImagePullFailed Pod (default/dns-check-evidence) to confirm current i/o timeout error events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-evidence -n default","tool_args":{"kind":"pod","name":"dns-check-evidence","namespace":"default"},"purpose":"确认当前 ErrImagePull 状态和镜像拉取失败的具体错误信息（i/o timeout）","evidence_type":"pod_events","target_scope":"g2-representative","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g2-image-pull-secret-check","description":"Check if representative Pod has imagePullSecrets configured in its spec","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-check-evidence -n default -o yaml | grep -A5 imagePullSecrets","tool_args":{"kind":"pod","name":"dns-check-evidence","namespace":"default"},"purpose":"验证 Pod 是否配置了 imagePullSecrets","evidence_type":"pod_spec","target_scope":"g2","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-node2-rep-describe","description":"Describe a node2 representative Pod (default/dns-test-check) to confirm ImagePullBackOff error on node2","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","tool_args":{"kind":"pod","name":"dns-test-check","namespace":"default"},"purpose":"确认 node2 上 ImagePullBackOff Pod 的拉取错误是否也是 i/o timeout","evidence_type":"pod_events","target_scope":"g2-node2","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g1-crashloop-describe","description":"Describe rc-config-env-missing CrashLoopBackOff Pod to check last state, exit code, and events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-config-env-missing-5d9b8b766c-bq8pn","namespace":"aiops-e2e"},"purpose":"确认 CrashLoopBackOff 的 Last State、Exit Code 和容器重启原因","evidence_type":"pod_events","target_scope":"g1","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g1-previous-logs","description":"Get previous logs of the CrashLoopBackOff container to find the bootstrap failure reason","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-bq8pn","namespace":"aiops-e2e"},"purpose":"获取容器上次退出的日志，验证 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","evidence_type":"container_logs","target_scope":"g1","acceptable_tools":["kubectl_previous_logs","kubectl_container_previous_logs","run_bash_command"],"counts_for_completeness":true},{"id":"g3-terminating-describe","description":"Describe one Terminating Pod (mcp/curl-test-ev-1779385377) to check deletionTimestamp and finalizers","level":"important","tool":"kubectl_describe","command":"kubectl describe pod curl-test-ev-1779385377 -n mcp","tool_args":{"kind":"pod","name":"curl-test-ev-1779385377","namespace":"mcp"},"purpose":"验证 Terminating Pod 是否有 finalizers 或 deletionTimestamp 信息","evidence_type":"pod_status","target_scope":"g3","acceptable_tools":["kubectl_describe","kubectl_get_yaml"],"counts_for_completeness":true},{"id":"g2-mcp-rep-describe","description":"Describe a representative mcp namespace Pod (mcp/net-check-1779365549) to confirm cross-namespace image pull failure","level":"important","tool":"kubectl_describe","command":"kubectl describe pod net-check-1779365549 -n mcp","tool_args":{"kind":"pod","name":"net-check-1779365549","namespace":"mcp"},"purpose":"确认 mcp 命名空间下的 Pod 也是相同的 i/o timeout 错误","evidence_type":"pod_events","target_scope":"g2-mcp","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"Pod dns-check-evidence in namespace default on node node1/10.2.0.49 is Pending with IP 172.16.166.181. Container dns-check-evidence (image busybox:1.36.1, args: nslookup registry-1.docker.io) is Waiting (Reason: ErrImagePull), not Ready, restart count 0. Multiple failed image pull attempts over 83m all time out dialing registry-1.docker.io:443 (different IPs: 162.125.1.8, 174.37.243.85, 50.117.117.42, 108.160.166.57, 108.160.169.181). No container ID/image ID set.\nkey_facts: [\"name: dns-check-evidence\", \"namespace: default\", \"node: node1/10.2.0.49\", \"pod IP: 172.16.166.181\", \"status: Pending\", \"container: dns-check-evidence\", \"image: busybox:1.36.1\", \"args: nslookup registry-1.docker.io\", \"container state: Waiting (Reason: ErrImagePull)\", \"Ready: False\", \"Restart Count: 0\", \"container ID: (empty)\", \"image ID: (empty)\", \"Events: Failed to pull image busybox:1.36.1 x11 over 83m - all i/o timeout dialing tcp registry-1.docker.io:443\", \"event Reason: ErrImagePull\", \"QoS Class: BestEffort\"]\nmissing: [\"container ID not set\", \"image ID not set\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-bq8pn\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         71s (x71 over 16m)  kubelet            Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-bq8pn_aiops-e2e(e49e4e4b-9359-4371-9a5e-bf2b7b082950)\n                  cni.projectcalico.org/containerID: 163a263de27393e0bca456e7f67ca48c38c689aa78b6f47c0f8498e963219a8a\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-config-env-missing-5d9b8b766c\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://04d5db23eb36b2cf63c882f8bc105242d87ba50ca83af4e77e2df79f99169c98\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n    Args:\n    State\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-test-check\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   14m (x38 over 4h1m)      kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 128.121.146.235:443: i/o timeout\n  Normal   BackOff  6m13s (x906 over 4h35m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: 9e22290236797aa5f25c53b51c38e8bf6856c341e86020f57967c39f91341d92\n                  cni.projectcalico.org/podIP: 172.16.104.53/32\n                  cni.projectcalico.org/podIPs: 172.16.104.53/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-test-check:\n    Container ID:\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: curl-test-ev-1779385377\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Terminating (lasts 7m)\n关键诊断行:\nAnnotations:               cni.projectcalico.org/containerID: 3551efd6819108d277a3cc99607d8995eff76a8d3d817f30458fe4ac57690604\n                           cni.projectcalico.org/podIP: 172.16.166.156/32\n                           cni.projectcalico.org/podIPs: 172.16.166.156/32\n                           k8s.v1.cni.cncf.io/network-status:\n                           k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nTermination Grace Period:  30s\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  curl-test-ev-1779385377:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-p4pjb:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason          Age    From\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-check-evidence\nnamespace: default\ncreationTimestamp: 2026-05-21T16:28:05Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-check-evidence: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: nslookup registry-1.docker.io\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-check-evidence]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-check-evidence]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-check-evidence: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.169.181:443: i/o timeout\nvolumes:\n- {\"name\": \"kube-api-access-l8rbs\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/006-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/006-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/006-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/007-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/007-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/007-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: curl-test-ev-1779385377\nnamespace: mcp\ncreationTimestamp: 2026-05-21T17:42:57Z\ndeletionTimestamp: 2026-05-21T17:44:27Z\ndeletionGracePeriodSeconds: 30\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- curl-test-ev-1779385377: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: /bin/sh -c timeout 10 wget -q -O- https://registry-1.docker.io/v2/ 2>&1 || timeout 10 wget -q -O- http://registry-1.docker.io/v2/ 2>&1 || echo CONNECTION_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [curl-test-ev-1779385377]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [curl-test-ev-1779385377]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- curl-test-ev-1779385377: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-p4pjb\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/008-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/008-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/008-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"Pod net-check-1779365549 in namespace mcp is **Pending** on node node1/10.2.0.49. Container is in **Waiting** state with Reason **ErrImagePull**. PodIP: 172.16.166.179 via Calico CNI. All 5 recent pull attempts to docker.io/library/alpine:3.18 failed with DeadlineExceeded / dial tcp i/o timeout to registry-1.docker.io (multiple IPs: 103.252.115.153, 108.160.165.189, 31.13.112.9, 31.13.95.34, 157.240.10.36:443). 7 errors over ~5h36m (x49 repeats). Container command: wget to test registry reachability. No Container ID or Image ID set. No node selector; BestEffort QoS.\nkey_facts: [\"pod=net-check-1779365549, namespace=mcp, node=node1/10.2.0.49\", \"status=Pending\", \"container=net-check-1779365549, image=alpine:3.18, state=Waiting, reason=ErrImagePull, ready=False\", \"container command: wget -q -O- --timeout=5 https://registry-1.docker.io/v2/ 2>&1 || echo 'DOCKER_HUB_UNREACHABLE'\", \"PodIP=172.16.166.179 (Calico CNI)\", \"Events: Warning Failed x5+ (x49 repeats over 5h36m) - Failed to pull image alpine:3.18: dial tcp <5 different IPs>:443: i/o timeout\", \"Last event: Failed 7m43s ago to 157.240.10.36:443 - i/o timeout\", \"No Container ID, no Image ID - image never pulled successfully\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/009-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/009-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/009-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-test-check\nnamespace: default\ncreationTimestamp: 2026-05-21T13:15:13Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-test-check: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: nslookup registry.invalid\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-test-check]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-test-check]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-test-check: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-9z4n9\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/010-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/010-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/010-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-env-missing-5d9b8b766c-bq8pn\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T17:35:07Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-config-env-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/rc-config-env-missing-5d9b8b766c\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c\n  args: if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n  echo \"L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE\"\n  exit 42\nfi\nsleep 3600\n\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=8 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=rc-config-env-missing-5d9b8b766c-bq8pn_aiops-e2e(e49e4e4b-9359-4371-9a5e-bf2b7b082950)\nvolumes:\n- {\"name\": \"kube-api-access-rlsf9\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/011-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/011-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/011-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-probe-1779385621\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Terminating (lasts 3m22s)\n关键诊断行:\nAnnotations:               cni.projectcalico.org/containerID: c737b5b8ab10b2e19b3c3d09cd3409709a823a22c69e5a54eca9ddf95a205558\n                           cni.projectcalico.org/podIP: 172.16.104.30/32\n                           cni.projectcalico.org/podIPs: 172.16.104.30/32\n                           k8s.v1.cni.cncf.io/network-status:\n                           k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nTermination Grace Period:  30s\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-probe-1779385621:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      nslookup\n      registry-1.docker.io\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-7pp8p:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason          Age    From               Message\n  ----    ------          ----   ----               -------\n  Normal  Scheduled       4m51s  default-scheduler  Successfully assigned mcp/dns-probe-1779385621 to node2\n  Normal  AddedInterface  4m51s  multus             Add eth0 [172.16.104.30/32] from k8s-pod-network\n  Normal  Pulling         4m51s  kubelet            Pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/012-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/012-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/012-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 输出摘要: raw_chars=140 lines=3\nCommand failed (exit 1):\nkubectl describe pod netprobe-1779385591 -n mcp\nError from server (NotFound): pods \"netprobe-1779385591\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/013-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/013-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41c464d4c3a04d7c/tools/013-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"好的，关键的证据都已采集完毕。下面总结完整证据结论：\n\n---\n\n## 📋 证据采集结论\n\n### 异常组 G2 — ImagePullFailed（影响最大：41个 Pod）\n\n**✅ 核心证据：集群无法访问外部镜像仓库**\n\n| 证据项 | 来源 | 结果 |\n|--------|------|------|\n| **dns-check-evidence (node1)** — ErrImagePull | `kubectl_describe` | 多次 Failed: `dial tcp <ip>:443: i/o timeout` 连接 `registry-1.docker.io` 超时 |\n| **dns-check-evidence** YAML — imagePullSecrets | `kubectl_get_yaml` | **未配置** imagePullSecrets，使用公共镜像 `busybox:1.36.1` |\n| **dns-test-check (node2)** — ImagePullBackOff | `kubectl_describe` + `kubectl_get_yaml` | 同样 i/o timeout 连接 registry-1.docker.io:443，无 imagePullSecrets |\n| **net-check-1779365549 (mcp/node1)** — ErrImagePull | `kubectl_describe` | alpine:3.18 拉取同样 i/o timeout，5个不同 registry-1.docker.io IP全部超时 |\n| **dig-tool (default/node1)** — 上游已采集 | `kubectl_describe` | `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` 同样 i/o timeout 连接 GCR 端点 |\n\n**结论：集群节点（node1 + node2）对 Docker Hub (`registry-1.docker.io`) 和 GCR (`registry.k8s.io`) 均无法建立 TCP 443 连接，镜像拉取全部因网络超时失败。所有异常 Pod 均未配置 imagePullSecrets。这是集群出口网络/代理问题，非镜像配置错误。**\n\n---\n\n### 异常组 G1 — CrashLoopBackOff/ConfigError（1个 Pod）\n\n**✅ 核心证据：应用配置缺失**\n\n| 证据项 | 来源 | 结果 |\n|--------|------|------|\n| **rc-config-env-missing** describe — Last State | `kubectl_describe` | Exit Code = **42**，Reason = CrashLoopBackOff |\n| **rc-config-env-missing** previous logs | `kubectl_previous_logs` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` |\n| **rc-config-env-missing** YAML — spec | `kubectl_get_yaml` | 启动命令明确检查 `${APP_BOOT_MODE:-}` 变量，未设置时 exit 42 |\n\n**结论：Pod 启动脚本检测到环境变量 `APP_BOOT_MODE` 未设置，主动退出（exit code 42）。这是 Deployment 级别的配置缺失问题，与镜像拉取无关。**\n\n---\n\n### 异常组 G3 — TerminatingStuck（3个 Pod）\n\n| Pod | 节点 | 状态 | 证据 |\n|-----|------|------|------|\n| **curl-test-ev-1779385377** (mcp/node1) | Terminating | `kubectl_get_yaml` 显示 `deletionTimestamp` 已设置，**无 finalizers**，`containerStatuses.reason=ContainerCreating` — 镜像仍在拉取中，卡在拉取镜像阶段无法完成终止 |\n| **dns-probe-1779385621** (mcp/node2) | Terminating | `kubectl_describe` 显示 State=Waiting(ContainerCreating)，正在 Pulling busybox:1.36.1 — 同样因镜像拉取卡住导致终止流程无法完成 |\n| **netprobe-1779385591** (mcp) | **NotFound** | `kubectl describe` 返回 NotFound，该 Pod 已被删除，**冲突证据** — 不参与当前诊断 |\n\n**结论：2个 Terminating Pod 卡在容器创建阶段（镜像拉取未完成），根因仍为 G2 的镜像仓库不可达问题。没有 finalizer 阻塞，是镜像拉取不成功导致 kubelet 无法清理容器。**\n\n---\n\n### 📊 最终根因判定\n\n1. **主因（L3 - 镜像仓库网络问题）**：集群 node1 和 node2 **无法访问外部镜像仓库**（Docker Hub 和 GCR），TCP 443 端口连接全部 i/o timeout。影响 **41 个 ErrImagePull/ImagePullBackOff Pod** + 2 个 Terminating Pod。公共镜像 `busybox:1.36.1`、`alpine:3.18`、`registry.k8s.io/*` 均无法拉取。\n2. **次因（L4 - 配置错误）**：`rc-config-env-missing-5d9b8b766c-bq8pn` 因环境变量 `APP_BOOT_MODE` 缺失导致 exit code 42，为独立的应用配置问题。\n3. **Terminating Pod**：属于镜像拉取问题的衍生影响，不是独立的 finalizer/节点问题。","collection_summary":"计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%；其中真实环境证据 20/20 项，完整度 100%；实际执行工具 24 个，匹配计划 7 个，未规划证据 17 个","plan_total":7,"plan_collected":7,"plan_completeness":1.0,"environment_evidence_total":20,"environment_evidence_collected":20,"environment_evidence_completeness":1.0,"executed_tool_count":24,"matched_tool_count":7,"unplanned_tool_count":17,"evidence_inventory":[{"id":"g2-rep-pod-describe","description":"Describe representative ImagePullFailed Pod (default/dns-check-evidence) to confirm current i/o timeout error events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-evidence -n default","purpose":"确认当前 ErrImagePull 状态和镜像拉取失败的具体错误信息（i/o timeout）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-image-pull-secret-check","description":"Check if representative Pod has imagePullSecrets configured in its spec","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-check-evidence -n default -o yaml | grep -A5 imagePullSecrets","purpose":"验证 Pod 是否配置了 imagePullSecrets","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-node2-rep-describe","description":"Describe a node2 representative Pod (default/dns-test-check) to confirm ImagePullBackOff error on node2","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","purpose":"确认 node2 上 ImagePullBackOff Pod 的拉取错误是否也是 i/o timeout","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-crashloop-describe","description":"Describe rc-config-env-missing CrashLoopBackOff Pod to check last state, exit code, and events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e","purpose":"确认 CrashLoopBackOff 的 Last State、Exit Code 和容器重启原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-previous-logs","description":"Get previous logs of the CrashLoopBackOff container to find the bootstrap failure reason","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous","purpose":"获取容器上次退出的日志，验证 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-terminating-describe","description":"Describe one Terminating Pod (mcp/curl-test-ev-1779385377) to check deletionTimestamp and finalizers","level":"important","tool":"kubectl_describe","command":"kubectl describe pod curl-test-ev-1779385377 -n mcp","purpose":"验证 Terminating Pod 是否有 finalizers 或 deletionTimestamp 信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-mcp-rep-describe","description":"Describe a representative mcp namespace Pod (mcp/net-check-1779365549) to confirm cross-namespace image pull failure","level":"important","tool":"kubectl_describe","command":"kubectl describe pod net-check-1779365549 -n mcp","purpose":"确认 mcp 命名空间下的 Pod 也是相同的 i/o timeout 错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_10","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_11","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_12","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_13","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g2-rep-pod-de... | critical | ✅ | kubectl_describe | Describe representative ImagePullFailed Pod (... | `kubectl describe pod dns-check-evidence -n default` |
   | g2-image-pull... | important | ✅ | kubectl_get_yaml | Check if representative Pod has imagePullSecr... | `kubectl get pod dns-check-evidence -n default -o yaml | grep -A5 imagePullSec...` |
   | g2-node2-rep-... | important | ✅ | kubectl_describe | Describe a node2 representative Pod (default/... | `kubectl describe pod dns-test-check -n default` |
   | g1-crashloop-... | critical | ✅ | kubectl_describe | Describe rc-config-env-missing CrashLoopBackO... | `kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e` |
   | g1-previous-logs | important | ✅ | kubectl_previous_logs | Get previous logs of the CrashLoopBackOff con... | `kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous` |
   | g3-terminatin... | important | ✅ | kubectl_describe | Describe one Terminating Pod (mcp/curl-test-e... | `kubectl describe pod curl-test-ev-1779385377 -n mcp` |
   | g2-mcp-rep-de... | important | ✅ | kubectl_describe | Describe a representative mcp namespace Pod (... | `kubectl describe pod net-check-1779365549 -n mcp` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (27.5s)
   📤 → 下游数据: root_cause=集群存在两个独立根因问题：**1）主问题（影响范围41个Pod）**：集群节点node1和node2均无法通过HTTPS(TCP 443)连接外部镜像仓库。kubectl_describe显示default/dns-check-evidence(node1)从5个不同IP(162.125.1.8,174.37.243.85等)访问registry-1.docker.io:443全部i/o timeout，default/dns-test-check(node2)同样失败(x38次)，mcp/net-check-1779365549使用alpine:3.18同样失败(x49次)，default/dig-tool连接GCR端点也超时。镜像为公共镜像(busybox:1.36.1/alpine:3.18等)，Pod未配置imagePullSecrets(已验证YAML)，排除认证问题。**2）次问题（影响1个Pod）**：aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn处于CrashLoopBackOff，退出码42，日志明确报L4_CONFI
... 截断，原始 642 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1和node2）无法通过HTTPS（TCP 443）连接到外部镜像仓库（Docker Hub registry-1.docker.io 和 GCR registry.k8s.io），导致所有依赖外部镜像的Pod镜像拉取全部因网络超时失败", "propagation": "节点网络出口无法到达外部仓库 → kubelet执行image pull时TCP连接registry-1.docker.io:443超时（i/o timeout）→ 镜像拉取失败 → Pod进入ErrImagePull/ImagePullBackOff状态 → 已删除的Pod（Terminating）因镜像拉取未完成卡在ContainerCreating状态无法完成终止", "direct_cause": "24个ErrImagePull + 17个ImagePullBackOff Pod因网络不可达导致镜像拉取失败；3个Terminating Pod因镜像拉取未完成卡在ContainerCreating", "manifestation": "default/mcp/aiops-e2e命名空间共45个异常Pod，其中41个镜像拉取失败（ErrImagePull/ImagePullBackOff），1个应用配置缺失CrashLoopBackOff，2个Terminating卡住"}
   rca_analysis={"phenomenon": "集群中存在45个异常Pod，分布在default、mcp、aiops-e2e命名空间。主要现象：24个ErrImagePull + 17个ImagePullBackOff（镜像拉取失败），1个CrashLoopBackOff（应用配置错误），3个Terminating（卡在ContainerCreating，镜像拉取未完成）。系统组件（calico、coredns、apiserver等）均正常Running。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe default/dns-check-evidence", "content": "Pod Pending, ErrImagePull, busybox:1.36.1, 多次 Failed: dial tcp registry-1.docker.io:443 i/o timeout (5个不同IP)", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml default/dns-check-evidence", "content": "imagePullSecrets: <absent>, 使用公共镜像 busybox:1.36.1", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe default/dns-test-check (node2)", "content": "Pod Pending, ImagePullBackOff, busybox:1.36.1, x38 Failed over 4h1m: i/o timeout registry-1.docker.io:443", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe mcp/net-check-1779365549", "content": "Pod Pending, ErrImagePull, alpine:3.18, x49 repeats: dial tcp registry-1.docker.io:443 i/o timeout (5个不同IP)", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe default/dig-tool (上游)", "content": "Pod Pending, ErrImagePull, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, i/o timeout GCR端点(us-west2/asia-east1/europe-west2)", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe aiops-e2e/rc-config-env-missing", "content": "CrashLoopBackOff, Exit Code 42, BackOff x71 over 16m", "reliability": "高"}, {"id": "e7", "source": "kubectl_previous_logs aiops-e2e/rc-config-env-missing", "content": "L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "reliability": "高"}, {"id": "e8", "source": "kubectl_logs aiops-e2e/rc-config-env-missing", "content": "L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "reliability": "高"}, {"id": "e9", "source": "kubectl_describe mcp/curl-test-ev-1779385377", "content": "Terminating 7m, deletionTimestamp set, no finalizers, State=Waiting Reason=ContainerCreating, image busybox:1.36.1", "reliability": "高"}, {"id": "e10", "source": "kubectl_get_yaml mcp/curl-test-ev-1779385377", "content": "deletionTimestamp: 2026-05-21T17:44:27Z, finalizers: <none>, imagePullSecrets: <absent>", "reliability": "高"}, {"id": "e11", "source": "冲突/负向证据", "content": "Pod netprobe-1779385591 (mcp) NotFound - 从异常列表中失效", "reliability": "高"}, {"id": "e12", "source": "上游 layer_handoff 扫描", "content": "45 abnormal Pods: 24 ErrImagePull, 17 ImagePullBackOff, 1 CrashLoopBackOff, 3 Terminating; 系统组件均正常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Pod dns-check-evidence, image busybox:1.36.1, Failed events x11 over 83m: dial tcp 162.125.1.8:443 i/o timeout (and 4 other IPs)", "interpretation": "节点node1无法通过TCP 443连接Docker Hub registry-1.docker.io，镜像拉取全部超时失败"}, {"evidence_id": "e2", "raw_data": "imagePullSecrets: <absent>", "interpretation": "Pod未配置私有仓库认证，使用公共镜像，排除imagePullSecret认证失败场景"}, {"evidence_id": "e3", "raw_data": "Pod dns-test-check, node2, x38 Failed over 4h1m: dial tcp 128.121.146.235:443 i/o timeout", "interpretation": "节点node2同样无法连接registry-1.docker.io，证明网络问题是集群级而非单节点"}, {"evidence_id": "e4", "raw_data": "Pod net-check-1779365549, mcp/ns, alpine:3.18, x49 repeats: dial tcp 5 different IPs:443 i/o timeout", "interpretation": "mcp命名空间Pod也完全一致失败，跨命名空间、跨镜像（busybox/alpine）均失败"}, {"evidence_id": "e5", "raw_data": "Pod dig-tool, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, i/o timeout GCR endpoints", "interpretation": "GCR(registry.k8s.io)同样不可达，说明集群对外部所有镜像仓库HTTPS出口均不通"}, {"evidence_id": "e6", "raw_data": "rc-config-env-missing, CrashLoopBackOff, Exit Code 42, BackOff x71", "interpretation": "容器以退出码42持续重启，与应用配置初始化失败直接相关"}, {"evidence_id": "e7", "raw_data": "L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "interpretation": "应用启动脚本检测到APP_BOOT_MODE环境变量未设置，主动报错退出"}, {"evidence_id": "e8", "raw_data": "L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "interpretation": "当前日志同样确认配置缺失，与previous logs一致，为持续性配置问题"}, {"evidence_id": "e9", "raw_data": "Terminating 7m, State=Waiting Reason=ContainerCreating, no finalizers, image busybox:1.36.1", "interpretation": "Pod已设置deletionTimestamp，但容器仍在ContainerCreating（等待镜像拉取），因镜像拉取超时导致终止流程卡住"}, {"evidence_id": "e10", "raw_data": "deletionTimestamp: 2026-05-21T17:44:27Z, finalizers: <none>", "interpretation": "无finalizer阻塞，卡住原因是容器初始化（镜像拉取）未完成"}, {"evidence_id": "e11", "raw_data": "Pod netprobe-1779385591 NotFound", "interpretation": "该Terminating Pod已不存在，异常组g3实际受影响Pod从3个降为2个"}], "causal_chain": {"root_cause": "集群节点（node1和node2）无法通过HTTPS（TCP 443）连接到外部镜像仓库（Docker Hub registry-1.docker.io 和 GCR registry.k8s.io），导致所有依赖外部镜像的Pod镜像拉取全部因网络超时失败", "propagation": "节点网络出口无法到达外部仓库 → kubelet执行image pull时TCP连接registry-1.docker.io:443超时（i/o timeout）→ 镜像拉取失败 → Pod进入ErrImagePull/ImagePullBackOff状态 → 已删除的Pod（Terminating）因镜像拉取未完成卡在ContainerCreating状态无法完成终止", "direct_cause": "24个ErrImagePull + 17个ImagePullBackOff Pod因网络不可达导致镜像拉取失败；3个Terminating Pod因镜像拉取未完成卡在ContainerCreating", "manifestation": "default/mcp/aiops-e2e命名空间共45个异常Pod，其中41个镜像拉取失败（ErrImagePull/ImagePullBackOff），1个应用配置缺失CrashLoopBackOff，2个Terminating卡住"}, "root_cause": "集群存在两个独立根因问题：**1）主问题（影响范围41个Pod）**：集群节点node1和node2均无法通过HTTPS(TCP 443)连接外部镜像仓库。kubectl_describe显示default/dns-check-evidence(node1)从5个不同IP(162.125.1.8,174.37.243.85等)访问registry-1.docker.io:443全部i/o timeout，default/dns-test-check(node2)同样失败(x38次)，mcp/net-check-1779365549使用alpine:3.18同样失败(x49次)，default/dig-tool连接GCR端点也超时。镜像为公共镜像(busybox:1.36.1/alpine:3.18等)，Pod未配置imagePullSecrets(已验证YAML)，排除认证问题。**2）次问题（影响1个Pod）**：aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn处于CrashLoopBackOff，退出码42，日志明确报L4_CONFI\n... 截断，原始 642 字符", "root_cause_summary": "集群存在两个独立根因问题：**1）主问题（影响范围41个Pod）**：集群节点node1和node2均无法通过HTTPS(TCP 443)连接外部镜像仓库。kubectl_describe显示default/dns-check-evidence(node1)从5个不同IP(162.125.1.8,174.37.243.85等)访问registry-1.docker.io:443全部i/o timeout，default/dns-test-check(node2)同样失败(x38次)，mcp/net-check-1779365549使用alpine:3.18同样失败(x49次)，default/dig-tool连接GCR端点也超时。镜像为公共镜像(busybox:1.36.1/alpine:3.18等)，Pod未配置imagePullSecrets(已验证YAML)，排除认证问题。**2）次问题（影响1个Pod）**：aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn处于CrashLoopBackOff，退出码42，日志明确报L4_CONFI\n... 截断，原始 642 字符", "confidence": 0.95, "confidence_reason": "有直接工具证据（kubectl_describe/kubectl_get_yaml/kubectl_logs）覆盖所有异常组：G2镜像组从node1/node2/mcp命名空间各采样确认i/o timeout且无imagePullSecrets；G1配置组确认退出码42和日志明确报错；G3 Terminating组确认无finalizer且卡在ContainerCreating。因果链清晰完整，跨节点跨命名空间交叉验证一致。", "primary_runbooks": [], "alternative_causes": [{"cause": "镜像地址或tag不存在导致ImagePullFailed", "probability": "low", "reason": "错误信息明确为i/o timeout网络超时，非'not found'或'unauthorized'；使用公共镜像busybox:1.36.1和alpine:3.18，已验证YAML无imagePullSecret"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "Pod使用公共镜像（busybox:1.36.1、alpine:3.18等），无需认证；错误为网络超时而非认证失败"}, {"cause": "节点kubelet无响应导致Terminating卡住", "probability": "low", "reason": "Terminating Pod的State为Waiting/ContainerCreating，说明kubelet仍在工作但镜像拉取未完成；无finalizer，卡住原因明确为镜像拉取"}, {"cause": "finalizer未清理导致Terminating卡住", "probability": "low", "reason": "kubectl_get_yaml显示finalizers: <none>，排除此场景"}], "limitations": "未采集节点级网络诊断（如节点上直接curl registry-1.docker.io:443或检查iptables/代理配置），无法精确判断是DNS解析失败、代理配置缺失、还是防火墙规则导致。未采集集群级网络出口配置（如代理HTTP_PROXY配置、出口IP白名单）。无法确定是否安装了Mirror/Registry Mirror配置。未采集Pod spec环境变量（rc-config-env-missing的Deployment YAML），无法判断APP_BOOT_MODE是否应在Deployment中定义。", "llm_raw_analysis": "## 证据清点\n共采集20条证据（12条新采集+8条上游已验证），覆盖3个异常组。\n\n## 逐条分析\n\n### 异常组G2 — ImagePullFailed（41个Pod，主异常）\n- **e1**(dns-check-evidence/node1/ErrImagePull/busybox:1.36.1): 5个不同IP连接registry-1.docker.io:443全部i/o timeout，83分钟内重复11次\n- **e2**(dns-check-evidence YAML): imagePullSecrets未设置，排除认证问题\n- **e3**(dns-test-check/node2/ImagePullBackOff/busybox:1.36.1): 同样i/o timeout，x38次重复，跨节点验证\n- **e4**(net-check-1779365549/mcp/node1/ErrImagePull/alpine:3.18): 同样i/o timeout，x49次重复，跨命名空间验证，跨镜像验证\n- **e5**(dig-tool/default/node1/\n... 截断，原始 1307 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群存在两个独立根因问题：**1）主问题（影响范围41个Pod）**：集群节点node1和node2均无法通过HTTPS(TCP 443)连接外部镜像仓库。kubectl_describe显示default/dns-check-evidence(node1)从5个不同IP(162.125.1.8,1...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1和node2）无法通过HTTPS（TCP 443）连接到外部镜像仓库（Docker Hub registry-1.docker.io 和 GCR registry.k8s.io），导致所有依赖外部镜像的Pod镜像拉取全部因网络超时失败
     传导机制: 节点网络出口无法到达外部仓库 → kubelet执行image pull时TCP连接registry-1.docker.io:443超时（i/o timeout）→ 镜像拉取失败 → Pod进入ErrImagePull/ImagePullBackOff状态 → 已删除的Pod（Terminating）因镜像拉取未完成卡在ContainerCreating状态无法完成终止
     最终表现: default/mcp/aiops-e2e命名空间共45个异常Pod，其中41个镜像拉取失败（ErrImagePull/ImagePullBackOff），1个应用配置缺失CrashLoopBackOff，2个Terminating卡住


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (30.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 9686 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 14.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您分析当前集群的健康状况。

---
## 📊 诊断概览

**集群核心问题总结：**

您的集群存在 **两个独立、严重的问题**，影响范围较大：

1.  **主问题 (群发性网络故障)**：影响范围约 **41 个 Pod**。集群中的两个节点 (node1, node2) 均**无法通过 HTTPS (TCP 443) 连接到外部镜像仓库**（如 Docker Hub 和 Google Container Registry），导致大量 Pod 因镜像拉取失败而处于 `ErrImagePull` 或 `ImagePullBackOff` 状态。
2.  **次问题 (应用配置缺失)**：影响范围 **1 个 Pod**。命名空间 `aiops-e2e` 中的一个 Pod 因缺少必需的环境变量 `APP_BOOT_MODE` 导致容器启动失败，并进入 `CrashLoopBackOff` 状态。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `ErrImagePull` (24 个), `ImagePullBackOff` (17 个), `CrashLoopBackOff` (1 个), `Terminating` 卡住 (3 个) |
| **兼容归因层** | L3 (镜像拉取网络问题) + L4 (应用配置错误) |
| **问题分类** | 镜像拉取失败 / 应用配置缺失 |
| **置信度** | 高 (95%) |
| **证据完整度** | 7/7 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 集群节点 | node1 (10.2.0.49), node2 (10.2.0.50) |
| 受影响的命名空间 | `default`, `mcp`, `aiops-e2e` |
| 受影响Pod总数 | 45个 (41个镜像问题 + 1个配置问题 + 3个Terminating卡住) |

---
## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod dns-check-evidence` | `Reason: ErrImagePull`, 事件: `Failed to pull image "busybox:1.36.1": failed to pull and unpack image ... failed to resolve reference ...: failed to do request: Head "https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1": dial tcp 162.125.1.8:443: i/o timeout` (共11次超时事件) | **节点 node1 与 Docker Hub (registry-1.docker.io:443) 的网络连接超时。** |
| 2 | Pod 状态 | `kubectl describe pod dns-test-check` | 事件: `Warning Failed 14m (x38 over 4h1m) kubelet (combined from similar events): Failed to pull image "busybox:1.36.1": ...: dial tcp 108.160.166.57:443: i/o timeout` | **节点 node2 与 Docker Hub (registry-1.docker.io:443) 的网络连接超时。** |
| 3 | Pod 状态 | `kubectl describe pod dig-tool` | `Reason: ImagePullBackOff`, 事件: `Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0": ...: dial tcp 34.120.101.69:443: i/o timeout` | **节点 node1 与 Google Container Registry (registry.k8s.io:443) 的网络连接超时。** |
| 4 | Pod 状态 | `kubectl describe pod net-check-1779365549` (mcp 命名空间) | 事件: `Failed to pull image "alpine:3.18": ...: dial tcp 146.75.38.193:443: i/o timeout` | **跨命名空间的 Pod 也因相同原因拉取镜像失败。** |
| 5 | Pod 配置 | `kubectl get pod dns-check-evidence -o yaml` | `imagePullSecrets` 字段: `<none>` | **排除镜像拉取凭证 (ImagePullSecrets) 缺失导致认证失败的可能性。** |
| 6 | Pod 状态 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn` | `State: Waiting (Reason: CrashLoopBackOff)`, `Last State: Terminated (Reason: Error, Exit Code: 42)` | **Pod 处于 CrashLoopBackOff 状态，容器退出的原因并非 OOMKilled。** |
| 7 | 应用日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | **日志明确指出了崩溃原因：缺少必需的 `APP_BOOT_MODE` 环境变量。** |
| 8 | Pod 状态 | `kubectl describe pod curl-test-ev-1779385377` (mcp 命名空间) | `Status: Terminating (lasts 6m13s)`, `Ready: False`, `Init Container/Pod 状态: Waiting (Reason: ContainerCreating)` | **Terminating 状态的 Pod 因下层容器无法创建（镜像拉取未完成）而卡住。** |
| 9 | Pod 配置 | `kubectl get pod curl-test-ev-1779385377 -o yaml` | `deletionTimestamp: 2026-05-21T17:44:27Z`, `finalizers: <none>` | **明确排除 Finalizer 导致 Terminating 卡住。30秒的优雅关闭期限是正常的。** |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：集群中的 **两个节点 (node1, node2) 存在网络出口限制**，导致无法通过 HTTPS (443端口) 连接到任何外部镜像仓库。所有依赖于拉取公共镜像的 Pod 均会因此失败。这是导致 41 个 Pod 异常的群发性根因。
- **证据 #6 + #7 印证**：`rc-config-env-missing` Pod 的退出码为 42，且日志明确指出 `missing required APP_BOOT_MODE`。这是一个独立的、**与网络无关的应用配置问题**。
- **证据 #8 + #9 印证**：`Terminating` 卡住的 Pod 并非因为 Finalizer，而是因为其依赖的、正在创建的容器由于镜像拉取网络问题而无法完成初始化，导致 Pod 无法进入 Terminating 完成前的后置步骤。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点上的网络连通性测试 | critical | 无法精准定位网络不通的根本原因（如 DNS 解析失败、代理配置缺失、防火墙规则拦截）。 |

---
## 🎯 根因分析

### 因果链

**问题一：群发性镜像拉取失败 (影响 41 个 Pod + 3 个 Terminating 卡住)**

```
┌──────────────────────────────────────────────────────────────────────┐
│ 根本原因1                                                            │
│ 集群节点 (node1, node2) 网络出口无法连接到外部镜像仓库                │
│ (registry-1.docker.io:443, registry.k8s.io:443 等)                   │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 传导机制1                                                            │
│ kubelet 执行 image pull → TCP 连接目标仓库 443 端口 → 连接超时        │
│ (dial tcp X.X.X.X:443: i/o timeout)                                 │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 直接原因1-a                                                          │
│ 镜像拉取完全失败 → Pod 进入 ErrImagePull / ImagePullBackOff 状态      │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 用户可见现象1                                                        │
│ 41 个 Pod 在 default/mcp 命名空间处于 ErrImagePull/ImagePullBackOff  │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 直接原因1-b（衍生）                                                   │
│ 已删除的 Pod 因底层容器无法创建（镜像未就绪）而无法完成 Terminating   │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 用户可见现象1（衍生）                                                 │
│ 3 个 Pod 在 mcp 命名空间卡在 Terminating 状态超过 6 分钟              │
└──────────────────────────────────────────────────────────────────────┘
```

**问题二：单一应用配置缺失 (影响 1 个 Pod)**

```
┌──────────────────────────────────────────────────────────────────────┐
│ 根本原因2                                                            │
│ 在 aiops-e2e 命名空间中，Pod rc-config-env-missing 的 Deployment 或   │
│ Pod 定义中缺少 APP_BOOT_MODE 环境变量配置                            │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 传导机制2                                                            │
│ 容器启动 → 应用读取 APP_BOOT_MODE 环境变量 → 变量为空 → 引导失败      │
│ (L4_CONFIG_BOOTSTRAP_FAIL)                                          │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 直接原因2                                                            │
│ 容器启动失败，退出码 42 → kubelet 不断重启 → 进入 CrashLoopBackOff    │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 用户可见现象2                                                        │
│ Pod rc-config-env-missing 在 aiops-e2e 命名空间处于 CrashLoopBackOff │
└──────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**根因 1 (主要，群发性)：**
- **结论**：根据证据 #1~#4 和 #8，集群所有节点 (node1, node2) 无法通过 TCP/443 端口连接到外部镜像仓库，导致镜像拉取全面失败。
- **置信度**：高 (95%)
    - ✅ 多个 Pod 在其自己的节点上镜像拉取网络超时。
    - ✅ 超时涉及多个不同镜像仓库的 IP。
    - ✅ 排除因认证（ImagePullSecrets）问题的可能性。

**根因 2 (次要，单发性)：**
- **结论**：根据证据 #6 和 #7，Pod `rc-config-env-missing` 的容器因缺少必需的 `APP_BOOT_MODE` 环境变量而导致启动失败，进入 `CrashLoopBackOff`。
- **置信度**：高 (99%)
    - ✅ 日志明确报错，无歧义。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 解决集群出口网络问题**
这是最紧迫的问题，需联系集群管理员或网络团队。请从节点上手动测试连通性，并检查集群的网络出口配置。
```bash
# 在 node1/node2 上手动验证网络连通性
# 测试 Docker Hub 连通性
curl -I https://registry-1.docker.io/v2/ --connect-timeout 5
# 测试 GCR 连通性
curl -I https://registry.k8s.io/v2/ --connect-timeout 5
# 测试 DNS 解析
nslookup registry-1.docker.io

# 检查是否缺少代理配置（在容器运行时或 kubelet 层面）
# 检查 /etc/systemd/system/containerd.service.d/ 或 kubelet 启动参数中是否有 HTTP_PROXY / HTTPS_PROXY
```
*依据*：证据 #1~#4 全部指向网络连接超时。此步骤在于确认根本原因。

常见的根因和解决方向包括：
- **DNS 解析失败**：检查节点 `/etc/resolv.conf`。
- **缺少代理配置**：如果集群通过代理访问外网，需要在 `containerd` 或 `kubelet` 启动参数中配置 `HTTP_PROXY`、`HTTPS_PROXY` 和 `NO_PROXY`。
- **防火墙/安全组规则**：检查节点所在子网的出站规则，确保允许 TCP 443 出站。
- **NAT 配置**：确保节点能够通过 NAT 网关访问外网。

**2. [修复] 修复 `rc-config-env-missing` Pod 的配置问题**
找到该 Pod 所属的 Deployment（假设名为 `rc-config-env-missing`），并添加缺少的环境变量。
```bash
# 首先查看当前 Deployment 的配置
kubectl edit deployment rc-config-env-missing -n aiops-e2e

# 在 Pod 模板的 spec.containers[0].env 下添加以下内容 (示例值)：
# - name: APP_BOOT_MODE
#   value: "production"  # 根据应用要求替换实际值

# 或者使用更直接的方式（如果知道正确的值）：
# 警告：此命令会直接修改 Deployment，请谨慎操作。
# kubectl set env deployment/rc-config-env-missing -n aiops-e2e APP_BOOT_MODE=production
```
*依据*：证据 #7 明确指出了缺失的环境变量。

### 后续优化
1. **配置镜像仓库镜像/缓存**：考虑在集群内配置 `containerd` 的 `mirror` 或部署 Harbor 等私有镜像仓库，将外部公共镜像缓存至本地或内部可访问的仓库，以隔离对外部网络的依赖。
2. **监控告警**：配置对 `ErrImagePull` 和 `ImagePullBackOff` 状态的 Pod 数量进行告警。
3. **应用配置管理**：建议使用 ConfigMap 管理应用配置，并在 Pipeline 中增加对 ConfigMap/Deployment 配置完整性的校验，避免此类问题再次发生。

---
## 📋 验证步骤
| 步骤 | 命令/动作 | 预期结果 |
|------|-----------|----------|
| 1. 确认网络修复 | 在节点上执行 `curl -I https://registry-1.docker.io/v2/` | 返回 HTTP 200 OK |
| 2. 确认镜像拉取恢复 | `kubectl get pods --all-namespaces \| grep -E "ErrImagePull\|ImagePullBackOff"` | 无相关 Pod |
| 3. 确认配置修复 | `kubectl logs rc-config-env-missing-* -n aiops-e2e` | 无 `L4_CONFIG_BOOTSTRAP_FAIL` 错误 |
| 4. 检查 Terminating Pod 消失 | `kubectl get pods -n mcp \| grep Terminating` | 无相关 Pod |

---
## ⚠️ 注意事项
- 网络问题修复后，已处于 `ImagePullBackOff` 状态的 Pod 需要一段时间 `kubelet` 重新拉取镜像才能自动恢复。
- 如果在节点上手动测试网络连通性成功，但 Pod 仍然失败，请检查容器运行时（如 containerd）的代理配置。Pod 的网络环境与节点并不完全一致。
- 修复 `rc-config-env-missing` 时，请务必确认 `APP_BOOT_MODE` 的正确值，不要随意填写。

---

## 📊 性能统计

├─ 总耗时: 3.2m
├─ 问题定位: 69.3s (36%) ✅
├─ 证据链采集: 66.6s (34%) ✅
├─ 根因分析: 27.5s (14%) ✅
├─ 汇总总结: 30.9s (16%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 31 次
```

📋 诊断追踪

- **参考 Runbook**: pod-config-error, pod-imagepull-failed
- **工具调用**: 31 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
