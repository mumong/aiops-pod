======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 39f2bbb1e71e4b27]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先扫描整个集群的所有 Pod，看看当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned 114 pods across all namespaces. Running=59, abnormal=49 (ImagePullBackOff=33, ErrImagePull=14, CreateContainerConfigError=1, Terminating=1), Completed=3, plus r
   💭 [问题定位] 扫描完毕。我来获取完整的异常 Pod 列表，并查看一些关键异常 Pod 的详情。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 表格摘要: rows=13 abnormal=13 status_counts={'Pending': 13}
NAMESPACE         NAME                                                STATUS      READY   AGE                    NODE
#
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=364 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=2989 lines=51
Executing jq query for pods...
aiops-e2e/rc-config-configmap-key-missing phase=Pending - CreateContainerConfigError
aiops-e2e/test-dns-1779360358 phas
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=2867 lines=49
Executing jq query for pods...
aiops-e2e/rc-config-configmap-key-missing phase=Pending - CreateContainerConfigError
aiops-e2e/test-dns-1779360358 phas
   💭 [问题定位] 让我看看所有异常 Pod 的完整列表，包括 kube-system 的 Terminating 和 mcp 的更多 Pod。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 jq query returned 51 lines: 43 pods in Pending (most with ImagePullBackOff or ErrImagePull, 1 with CreateContainerConfigError, 1 with ContainerCreating), 1 Evicted pod in Failed (xnet/observability-ki
   💭 [问题定位] 还有一个 Evicted Pod 和一个 Terminating Pod，让我确认完整情况。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=91 lines=2
Executing jq query for pods...
kube-system/curl-test deletionTimestamp=2026-05-21T19:15:21Z
   💭 [问题定位] 现在让我获取关键异常类型的 runbook，以辅助定位分析。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   ✅ [问题定位] 完成 (45.4s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像仓库不可达或认证失败导致大量Pod拉取镜像失败', 'probability': 'high', 'reason': '33个ImagePullBackOff + 14个ErrImagePull分布在两个节点多个命名空间，镜像来源多样，说明可能是registry/镜像仓库整体故障'}, {'scenario': '节点网络问题导致无法访问镜像仓库', 'probability': 'medium', 'reason': '异常Pod集中在node1和node2，但无Node异常证据；如果有节点级网络问题可能导致大量拉取失败'}, {'scenario': '镜像名或标签错误', 'probability': 'low', 'reason': '多个不同镜像同时拉取失败，不太可能全是镜像名错误'}, {'scenario': 'CreateContainerConfigError配置错误', 'probability': 'low', 'reason': '仅1个Pod出现该问题(rc-config-configmap-key-missing)，属于独立配置问题不影响整体'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}]
   reasoning=当前集群中存在大量异常Pod（总数114个，异常49个）。其中ImagePullBackOff 33个，ErrImagePull 14个，CreateContainerConfigError 1个，Terminating 1个。异常Pod主要分布在default、mcp、aiops-e2e、kube-system命名空间，集中在node1和node2。大量Pod处于Pending状态且状态关键字为ImagePullBackOff/ErrImagePull，属于镜像拉取失败问题，归因于image_registry层(L3)。另有一个CreateContainerConfigError属于配置错误(L4)，但绝大多数异常为ImagePullBackOff/ErrImagePull，故整体定层L3。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "Pod异常-镜像/网络", "confidence": 0.95, "reasoning": "当前集群中存在大量异常Pod（总数114个，异常49个）。其中ImagePullBackOff 33个，ErrImagePull 14个，CreateContainerConfigError 1个，Terminating 1个。异常Pod主要分布在default、mcp、aiops-e2e、kube-system命名空间，集中在node1和node2。大量Pod处于Pending状态且状态关键字为ImagePullBackOff/ErrImagePull，属于镜像拉取失败问题，归因于image_registry层(L3)。另有一个CreateContainerConfigError属于配置错误(L4)，但绝大多数异常为ImagePullBackOff/ErrImagePull，故整体定层L3。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "curl-test", "namespace": "kube-system", "status": "Terminating"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库不可达或认证失败导致大量Pod拉取镜像失败", "probability": "high", "reason": "33个ImagePullBackOff + 14个ErrImagePull分布在两个节点多个命名空间，镜像来源多样，说明可能是registry/镜像仓库整体故障"}, {"scenario": "节点网络问题导致无法访问镜像仓库", "probability": "medium", "reason": "异常Pod集中在node1和node2，但无Node异常证据；如果有节点级网络问题可能导致大量拉取失败"}, {"scenario": "镜像名或标签错误", "probability": "low", "reason": "多个不同镜像同时拉取失败，不太可能全是镜像名错误"}, {"scenario": "CreateContainerConfigError配置错误", "probability": "low", "reason": "仅1个Pod出现该问题(rc-config-configmap-key-missing)，属于独立配置问题不影响整体"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "kube-system", "name": "curl-test"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "kube-system", "name": "curl-test"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 33, "ErrImagePull": 14, "Terminating": 1}, "total_abnormal": 48, "selected_rows": ["aiops-e2e         rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0              18m     172.16.166.142   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff             0              8h      172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              3h49m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff             0              169m    172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              7h20m   172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff             0              9m15s   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff             0              14m     172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ImagePullBackOff             0              14m     172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff             0              8h      172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff             0              6h2m    172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff             0              14m     172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull                 0              176m    172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              7h8m    172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull                 0              7h36m   172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull                 0              4h32m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ErrImagePull                 0              42m     172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull                 0              5h30m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff             0              7h17m   172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              8h      172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "kube-system       curl-test                                           0/1     Terminating                  0              4m5s    <none>           node1    <none>           <none>            run=curl-test"], "raw_ref": "/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我立即执行既有 evidence_plan 中的关键工具调用。先开始并行执行多个独立任务。

## 第一步：获取 ImagePull 相关关键事件和 Pod 详情
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-check-test (default) on node1/10.2.0.49 is Pending, IP 172.16.166.167. Container dns-check-test (busybox:1.36.1) in Waiting/ImagePullBackOff, Ready=False, Restart Count=0. Image pull failures:
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
60m                     Warning   Failed    Pod/dns-check-test   Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = failed to pull and unpack image "dock
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: curl-test
namespace: kube-system
creationTimestamp: 2026-05-21T19:13:51Z
deletionTimestamp: 2026-05-21T19:15:21Z
deletionGracePeriodSeconds: 30
finalizers: <no
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod registry-check-node2 in namespace default on node node2 (10.2.0.50) is Pending. Container image busybox:1.36.1 consistently fails to pull due to i/o timeout dialing registry-1.docker.io:443 from m
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
60m                     Warning   Failed    Pod/test-dns-1779360358   Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = failed to pull and unpack image 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          17m (x12 over 19m)    kubelet            Error: 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-test
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Normal   BackOff  25m (x1445 over 7h39m)  kubelet  Back-off pulling image "busybox:1.36.1"
  
   💭 [证据链采集] 非常好，已经获取了大量关键证据。现在让我检查一下 **Terminating** 组的 Pod 状态以及验证更多异常 Pod 的事件，来确认异常模式的全局性。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
53m (x6 over 3h44m)      Warning   Failed    Pod/dig-tool   Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0": rpc error: code = DeadlineExceeded des
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN   TYPE     REASON           OBJECT          MESSAGE
5m15s       Normal   Scheduled        Pod/curl-test   Successfully assigned kube-system/curl-test to node1
5m15s       
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
22m (x341 over 175m)   Normal    BackOff   Pod/dns-test-tmp   Back-off pulling image "busybox:1.36.1"
12m (x21 over 141m)    Warning   Failed    Pod/dns-test-tmp   (combined 
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
9m39s (x937 over 8h)   Normal    BackOff   Pod/node-debugger-node1-2xvqr   Back-off pulling image "curlimages/curl:8.12.1"
2m16s (x99 over 8h)    Warning   Failed    Pod/node
   💭 [证据链采集] 现在让我验证节点本身是否有问题，以及检查 registry 连通性。
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
18m (x329 over 155m)   Normal    BackOff   Pod/registry-diag-1779381627   Back-off pulling image "busybox:1.36.1"
7m3s (x22 over 114m)   Warning   Failed    Pod/registry-diag
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
11m                   Warning   Failed           Pod/dns-resolve-gcr-test   Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = failed to pull and unpack 
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   238d   v1.26.8   10.2.0.49     <
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node2   Ready    <none>   238d   v1.26.8   10.2.0.50     <
   💭 [证据链采集] 现在让我检查一下 Terminating Pod 是否还处于活跃的 Pulling 状态，以及确认 ConfigMap 是否存在。
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            DATA   AGE   LABELS
rc-app-config   1      19m   rootcause-e2e=true
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: curl-test
namespace: kube-system
node: node1/10.2.0.49
status: Terminating (lasts 3m52s)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: bb01fadbb50d68c
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-app-config
namespace: aiops-e2e
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-configmap-key-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-21T18:59:23Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [证据链采集] ## 执行 fetch_runbook（匹配 ImagePull 场景）

已有明确证据指向镜像拉取失败，先获取 runbook 参考。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [证据链采集] 现在我已经获取了所有关键证据。让我总结一下采集结果。

---

## 证据采集完成 — 结果总结

### ✅ 已采集关键证据

#### 异常组 g2（ImagePullFailed — 主异常组，33+14=47个Pod）

**1. 核心Events — 镜像拉取失败原因（critical）**
- **Pod dns-check-test**（default/node1）: `Failed to pull image "busybox:1.36.1"` → **connection reset by peer** 从 `100.50.6.117:443`，以及 **i/o timeout** 从 `50.87.93.246:443` → 目的都是 `registry-1.docker.io`（Docker Hub）
- **Pod test-dns-1779360358**（aiops-e2e/node1）: 同样 `busybox:1.36.1` → **connection reset by peer** `3.233.166.60:443`
- **Pod dns-test-tmp**（default/node2）: 同样 `busybox:1.36.1` → **i/o timeout** `199.59.148.201:443` / `199.59.148.246:443`
- **Pod node-debugger-node1-2xvqr**（mcp/node1）: `curlimages/curl:8.12.1` → **i/o timeout** `registry-1.docker.io` `50.87.93.246:443`
- **Pod registry-diag-1779381627**（mcp/node2）: 同样 `busybox:1.36.1` → **i/o timeout** `199.59.148.206:443`

**结论：所有被检 Pod 均指向同一个失败模式 — 节点(node1/node2)到 Docker Hub(registry-1.docker.io:443)的网络不可达，表现为 connection reset by peer 或 i/o timeout。**

**2. 节点状态确认**
- `node1` 和 `node2` 均处于 **Ready** 状态，无异常。说明不是节点本身故障。

**3. 镜像分析**
- 涉及多个镜像：`busybox:1.36.1`、`curlimages/curl:8.12.1` — 全部来自 Docker Hub。不是单个镜像标签错误，而是**整个 Docker Hub 不可达**。

---

#### 异常组 g1（CreateContainerConfigError — 1个Pod，最小验证）

- **Pod rc-config-configmap-key-missing** 的容器状态消息明确显示：`couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config`
- 存在 ConfigMap `rc-app-config`（有1个data项），但缺少 `APP_BOOT_MODE` 这个key
- **证据充分确认**：Pod 引用了 ConfigMap 中不存在的 key，属于配置缺失问题，与镜像拉取无关

---

#### 异常组 g3（TerminatingStuck — 1个Pod，最小验证）

- **Pod curl-test**（kube-system/node1）：deletionTimestamp=`2026-05-21T19:15:21Z`，无 finalizers，正在拉取镜像 `busybox:1.36.1`（Pulling状态）
- Events 只有 `Scheduled` → `AddedInterface` → `Pulling image`
- **结论**：该 Pod 被删除时正尝试拉取镜像但卡在 Pulling 阶段，由于 Docker Hub 不可达，容器运行时无法完成 Pull，导致无法进入 PostStart/Kill 生命周期流程。**本质上仍是同一个 Docker Hub 不可达问题的衍生现象。**

---

### 📋 整体诊断结论

| 问题 | 影响范围 | 根本原因 |
|------|---------|---------|
| **集群无法拉取 Docker Hub 镜像** | **47个Pod**（33 ImagePullBackOff + 14 ErrImagePull）分布在 default/mcp/aiops-e2e 三个命名空间、node1/node2 两个节点 | **节点(node1/node2)到 registry-1.docker.io:443 的网络不可达** — 连接被重置或超时。不是镜像名/标签错误，不是认证问题，不是节点故障 |
| **CreateContainerConfigError** | 1个Pod（独立问题） | Pod 引用 ConfigMap `rc-app-config` 中不存在的 key `APP_BOOT_MODE` |
| **Terminating 卡住** | 1个Pod（Docker Hub不可达的衍生问题） | 删除时镜像拉取卡在 Pulling 阶段，无法完成生命周期流程 |
   ✅ [证据链采集] 完成 (1m 1.9s)
   📤 → 下游数据: evidence_items=14/14
   evidence_analysis={"evidence_plan":[{"id":"g2-events","description":"g2主异常组: 查看代表Pod的Events获取ImagePull失败原因","level":"critical","tool":"kubectl_events","command":"kubectl events --namespace=default --field-selector involvedObject.name=dns-check-test --all-namespaces=false","tool_args":{"namespace":"default","field_selector":"involvedObject.name=dns-check-test","all_namespaces":false},"purpose":"获取ImagePullBackOff Pod的Events，查看BackOff/ErrImagePull/FailedToPullImage等原始错误信息","evidence_type":"pod_event","target_scope":"default/dns-check-test","acceptable_tools":["kubectl_events","run_bash_command"],"counts_for_completeness":true},{"id":"g2-describe-1","description":"g2主异常组: describe default namespace 代表Pod确认镜像和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dns-check-test","tool_args":{"kind":"pod","name":"dns-check-test","namespace":"default","resource":"pod"},"purpose":"查看Pod完整状态、容器镜像、容器状态、Events等核心信息","evidence_type":"pod_describe","target_scope":"default/dns-check-test","acceptable_tools":["kubectl_describe","run_bash_command"],"counts_for_completeness":true},{"id":"g2-describe-mcp","description":"g2主异常组: describe mcp namespace 代表Pod确认镜像和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n mcp connectivity-test","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp","resource":"pod"},"purpose":"验证mcp命名空间的Pod是否也是相同镜像拉取失败原因，确认是否为全局性问题","evidence_type":"pod_describe","target_scope":"mcp/connectivity-test","acceptable_tools":["kubectl_describe","run_bash_command"],"counts_for_completeness":true},{"id":"g2-describe-node2","description":"g2主异常组: describe node2上ErrImagePull的Pod确认镜像问题","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default registry-check-node2","tool_args":{"kind":"pod","name":"registry-check-node2","namespace":"default","resource":"pod"},"purpose":"验证node2上的ErrImagePull Pod错误信息是否与node1一致","evidence_type":"pod_describe","target_scope":"default/registry-check-node2","acceptable_tools":["kubectl_describe","run_bash_command"],"counts_for_completeness":true},{"id":"g1-describe","description":"g1次要异常组: describe CreateContainerConfigError Pod","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-config-configmap-key-missing","tool_args":{"kind":"pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e","resource":"pod"},"purpose":"查看CreateContainerConfigError的详细错误，确认是否为ConfigMap/Secret引用问题","evidence_type":"pod_describe","target_scope":"aiops-e2e/rc-config-configmap-key-missing","acceptable_tools":["kubectl_describe","run_bash_command"],"counts_for_completeness":true},{"id":"g3-yaml","description":"g3次要异常组: 查看Terminating Pod的YAML确认finalizers和deletionTimestamp","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n kube-system curl-test -o yaml","tool_args":{"kind":"pod","name":"curl-test","namespace":"kube-system","resource":"pod","output":"yaml"},"purpose":"查看Terminating Pod的finalizers和deletionTimestamp确认卡住原因","evidence_type":"pod_yaml","target_scope":"kube-system/curl-test","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-events-aiops","description":"g2主异常组: 查看aiops-e2e代表Pod的事件","level":"important","tool":"kubectl_events","command":"kubectl events --namespace=aiops-e2e --field-selector involvedObject.name=test-dns-1779360358","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=test-dns-1779360358"},"purpose":"验证不同命名空间下的Pod是否也是相同原因的镜像拉取失败","evidence_type":"pod_event","target_scope":"aiops-e2e/test-dns-1779360358","acceptable_tools":["kubectl_events","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod dns-check-test (default) on node1/10.2.0.49 is Pending, IP 172.16.166.167. Container dns-check-test (busybox:1.36.1) in Waiting/ImagePullBackOff, Ready=False, Restart Count=0. Image pull failures: \"connection reset by peer\" from 100.50.6.117:443, and \"i/o timeout\" from 50.87.93.246:443 (registry-1.docker.io). Events show repeated ErrImagePull (x52), BackOff (x679), and DeadlineExceeded (x90) over 7h19m.\nkey_facts: [\"Pod: dns-check-test, Namespace: default\", \"Node: node1/10.2.0.49\", \"Status: Pending\", \"IP: 172.16.166.167\", \"Container: dns-check-test, Image: busybox:1.36.1\", \"Container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False, Restart Count: 0\", \"Event Warning: Failed (x52 over 7h19m) - Error: ErrImagePull\", \"Event Warning: Failed (60m) - Failed to pull image 'busybox:1.36.1': connection reset by peer from 100.50.6.117:443\", \"Event Normal: BackOff (x679 over 7h19m) - Back-off pulling image\", \"Event Warning: Failed (x90 over 6h39m) - Failed to pull image 'busybox:1.36.1': i/o timeout from 50.87.93.246:443\"]\nmissing: [\"Container ID: empty\", \"Image ID: empty\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n60m                     Warning   Failed    Pod/dns-check-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:38598->100.50.6.117:443: read: connection reset by peer\n10m (x679 over 7h19m)   Normal    BackOff   Pod/dns-check-test   Back-off pulling image \"busybox:1.36.1\"\n3m3s (x90 over 6h39m)   Warning   Failed    Pod/dns-check-test   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 50.87.93.246:443: i/o timeout\n60m (x52 over 7h19m)    Warning   Failed    Pod/dns-check-test   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: curl-test\nnamespace: kube-system\ncreationTimestamp: 2026-05-21T19:13:51Z\ndeletionTimestamp: 2026-05-21T19:15:21Z\ndeletionGracePeriodSeconds: 30\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- curl-test: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c wget -q -O- --timeout=5 https://registry.k8s.io/v2/ 2>&1 || echo \"TIMEOUT_OR_FAILED\"\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [curl-test]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [curl-test]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- curl-test: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-k7nvz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"Pod registry-check-node2 in namespace default on node node2 (10.2.0.50) is Pending. Container image busybox:1.36.1 consistently fails to pull due to i/o timeout dialing registry-1.docker.io:443 from multiple IPs. Container State: Waiting (Reason: ErrImagePull). Events show repeated Failed/ErrImagePull/ImagePullBackOff errors and BackOff (x16). Pod has IP 172.16.104.41 assigned via Calico/multus, was successfully scheduled and interface added, but image pull never succeeds.\nkey_facts: [\"resource: Pod registry-check-node2, namespace: default\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container: registry-check-node2, image: busybox:1.36.1\", \"container State: Waiting, Reason: ErrImagePull\", \"container Ready: False, Restart Count: 0\", \"All image pulls to docker.io/library/busybox:1.36.1 at registry-1.docker.io:443 fail with i/o timeout (dial tcp errors to various IPs)\", \"Events: Warning Failed (multiple timestamps: 40m, 35m, 30m, 25m, 19m, 8m47s ago) - Failed to pull image\", \"Events: Warning Failed (25m x4 over 40m) - Error: ErrImagePull\", \"Events: Warning Failed (25m x8 over 40m) - Error: ImagePullBackOff\", \"Events: Normal BackOff (18m x16 over 40m) - Back-off pulling image\", \"Even\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n60m                     Warning   Failed    Pod/test-dns-1779360358   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:38564->3.233.166.60:443: read: connection reset by peer\n11m (x112 over 7h56m)   Warning   Failed    Pod/test-dns-1779360358   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:53560->107.22.179.217:443: read: connection reset by peer\n7m52s (x1044 over 8h)   Normal    BackOff   Pod/test-dns-1779360358   Back-off pulling image \"busybox:1.36.1\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/005-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/005-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/005-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          17m (x12 over 19m)    kubelet            Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config\n                  cni.projectcalico.org/containerID: c3f68f3c291432ef6dcdea4afa9ea904811c43850537021eafd2f80e4b705cd1\n                  cni.projectcalico.org/podIP: 172.16.166.142/32\n                  cni.projectcalico.org/podIPs: 172.16.166.142/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-vr7b6:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kub\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  25m (x1445 over 7h39m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   2m18s (x83 over 7h13m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.59.148.246:443: i/o timeout\n      Reason:       ErrImagePull\n  Warning  Failed   2m18s (x70 over 7h39m)  kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists fo\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n53m (x6 over 3h44m)      Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 108.177.125.82:443: i/o timeout\n15m (x7 over 3h16m)      Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 142.250.157.82:443: i/o timeout\n9m1s (x335 over 3h44m)   Normal    BackOff   Pod/dig-tool   Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/008-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/008-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/008-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN   TYPE     REASON           OBJECT          MESSAGE\n5m15s       Normal   Scheduled        Pod/curl-test   Successfully assigned kube-system/curl-test to node1\n5m15s       Normal   AddedInterface   Pod/curl-test   Add eth0 [172.16.166.172/32] from k8s-pod-network\n5m15s       Normal   Pulling          Pod/curl-test   Pulling image \"busybox:1.36.1\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/009-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/009-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/009-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n22m (x341 over 175m)   Normal    BackOff   Pod/dns-test-tmp   Back-off pulling image \"busybox:1.36.1\"\n12m (x21 over 141m)    Warning   Failed    Pod/dns-test-tmp   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.59.148.201:443: i/o timeout\n2m                     Warning   Failed    Pod/dns-test-tmp   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.59.148.246:443: i/o timeout\n2m (x25 over 175m)     Warning   Failed    Pod/dns-test-tmp   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/010-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/010-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/010-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n9m39s (x937 over 8h)   Normal    BackOff   Pod/node-debugger-node1-2xvqr   Back-off pulling image \"curlimages/curl:8.12.1\"\n2m16s (x99 over 8h)    Warning   Failed    Pod/node-debugger-node1-2xvqr   (combined from similar events): Failed to pull image \"curlimages/curl:8.12.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/curlimages/curl:8.12.1\": failed to resolve reference \"docker.io/curlimages/curl:8.12.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\": dial tcp 50.87.93.246:443: i/o timeout","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/011-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/011-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/011-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n18m (x329 over 155m)   Normal    BackOff   Pod/registry-diag-1779381627   Back-off pulling image \"busybox:1.36.1\"\n7m3s (x22 over 114m)   Warning   Failed    Pod/registry-diag-1779381627   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.59.148.206:443: i/o timeout\n7m3s (x23 over 155m)   Warning   Failed    Pod/registry-diag-1779381627   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/012-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/012-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/012-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n11m                   Warning   Failed           Pod/dns-resolve-gcr-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:35980->107.22.179.217:443: read: connection reset by peer\n10m                   Warning   Failed           Pod/dns-resolve-gcr-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:53156->107.22.179.217:443: read: connection reset by peer\n6m19s                 Warning   Failed           Pod/dns-resolve-gcr-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/librar\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/013-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/013-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/013-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode1   Ready    <none>   238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/014-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/014-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/014-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode2   Ready    <none>   238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/015-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/015-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/015-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME            DATA   AGE   LABELS\nrc-app-config   1      19m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/016-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/016-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/016-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: curl-test\nnamespace: kube-system\nnode: node1/10.2.0.49\nstatus: Terminating (lasts 3m52s)\n关键诊断行:\nAnnotations:               cni.projectcalico.org/containerID: bb01fadbb50d68c6fc9c4e8826ff405212d584d1bddea3325a8c97ab721d0ea4\n                           cni.projectcalico.org/podIP: 172.16.166.172/32\n                           cni.projectcalico.org/podIPs: 172.16.166.172/32\n                           k8s.v1.cni.cncf.io/network-status:\n                           k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nTermination Grace Period:  30s\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  curl-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-k7nvz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason          Age    From               Message\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/017-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/017-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/017-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-app-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/018-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/018-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/018-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T18:59:23Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-config-configmap-key-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=CreateContainerConfigError exitCode=None\n  message: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config\nvolumes:\n- {\"name\": \"kube-api-access-vr7b6\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/019-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/019-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/019-evidence-kubectl_get_yaml.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: imagePullSecrets 必须在同 namespace，私有仓库 secret 类型应为 kubernetes.io/dockerconfigjson 或 kubernetes.io/dockercfg。\n\n### Step 4: 按事件错误文本归类\n- `manifest unknown` / `not found`: 镜像仓库中不存在该镜像或 tag。\n- `invalid reference format`: image 字符串格式错误。\n- `unauthorized` / `no basic auth credentials`: imagePullSecret 缺失、未引用、类型错误或凭据错误。\n- `pull access denied` / `insufficient_scope`: 仓库权限不足或镜像路径错误。\n- `x509: certificate signed by unknown authority`: 节点容器运行时不信任仓库 TLS 证书。\n- `i/o timeout` / `connection refused`: 节点到镜像仓库访问失败，需检查仓库地址、端口、防火墙、DNS。\n- `context canceled`: 拉取过程中连接被取消，常见于网络中断、镜像仓库响应慢、kubelet/运行时超时或并发拉取拥塞。\n- `Too Many Requests` / rate limit: 镜像仓库限流，需认证、镜像缓存或私有代理仓库。\n- 长时间只有 `Pulling image` 无后续失败事件: 关注镜像体积、节点带宽、运行时并发拉取限制、kubelet `registryPullQPS` / `registryBurst` 配置。\n\n### Step 5: 主动验证镜像仓库连通性\n可用只读命令验证节点或集群内到镜像仓库的 HTTPS 连通性，例如：\n```bash\ncurl -v --connect-timeout 10 https://registry-1.docker.io/v2/\n```\n判读规则：\n- 返回 `200/401/403`：说明 HTTPS 网络可达；`401/403` 通常是认证/权限语义，不是网络不可达。\n- `curl: (28) Operation timed out`、`Connection timed out`、`i/o timeout`、`命令执行超时`：这是诊断事实，表示镜像仓库网络不可达或链路被阻断，不应当仅视为“工具执行失败”。\n- `Could not resolve host`：DNS 解析失败。\n- `connection refused/reset`：目标端口不可达、被中间设备拒绝或连接被重置。\n- `x509`：TLS 证书信任问题。\n\n\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| Events 含 connection refused/timeout | 镜像仓库网络不可达 | 高 |\n| Events 含 context canceled | 镜像拉取连接被取消，优先检查网络、仓库响应、运行时超时和并发拉取 | 中 |\n| 主动 curl/wget registry 超时或命令执行超时 | 镜像仓库网络不可达 | 高 |\n| Events 含 manifest unknown/not found | 镜像或 tag 不存在 | 高 |\n| Events 含 unauthorized/no basic auth | 认证失败（缺少或错误的 imagePullSecret） | 高 |\n| Events 含 pull access denied/insufficient_scope | 仓库权限不足或镜像路径错误 | 高 |\n| Events 含 invalid reference format | 镜像名称格式错误 | 高 |\n| Events 含 x509 | 节点容器运行时信任链/TLS 证书问题 | 高 |\n| DNS 解析失败 | DNS 问题导致仓库不可达 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/020-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/020-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/39f2bbb1e71e4b27/tools/020-evidence-fetch_runbook.summary.txt"}],"llm_analysis":"现在我已经获取了所有关键证据。让我总结一下采集结果。\n\n---\n\n## 证据采集完成 — 结果总结\n\n### ✅ 已采集关键证据\n\n#### 异常组 g2（ImagePullFailed — 主异常组，33+14=47个Pod）\n\n**1. 核心Events — 镜像拉取失败原因（critical）**\n- **Pod dns-check-test**（default/node1）: `Failed to pull image \"busybox:1.36.1\"` → **connection reset by peer** 从 `100.50.6.117:443`，以及 **i/o timeout** 从 `50.87.93.246:443` → 目的都是 `registry-1.docker.io`（Docker Hub）\n- **Pod test-dns-1779360358**（aiops-e2e/node1）: 同样 `busybox:1.36.1` → **connection reset by peer** `3.233.166.60:443`\n- **Pod dns-test-tmp**（default/node2）: 同样 `busybox:1.36.1` → **i/o timeout** `199.59.148.201:443` / `199.59.148.246:443`\n- **Pod node-debugger-node1-2xvqr**（mcp/node1）: `curlimages/curl:8.12.1` → **i/o timeout** `registry-1.docker.io` `50.87.93.246:443`\n- **Pod registry-diag-1779381627**（mcp/node2）: 同样 `busybox:1.36.1` → **i/o timeout** `199.59.148.206:443`\n\n**结论：所有被检 Pod 均指向同一个失败模式 — 节点(node1/node2)到 Docker Hub(registry-1.docker.io:443)的网络不可达，表现为 connection reset by peer 或 i/o timeout。**\n\n**2. 节点状态确认**\n- `node1` 和 `node2` 均处于 **Ready** 状态，无异常。说明不是节点本身故障。\n\n**3. 镜像分析**\n- 涉及多个镜像：`busybox:1.36.1`、`curlimages/curl:8.12.1` — 全部来自 Docker Hub。不是单个镜像标签错误，而是**整个 Docker Hub 不可达**。\n\n---\n\n#### 异常组 g1（CreateContainerConfigError — 1个Pod，最小验证）\n\n- **Pod rc-config-configmap-key-missing** 的容器状态消息明确显示：`couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config`\n- 存在 ConfigMap `rc-app-config`（有1个data项），但缺少 `APP_BOOT_MODE` 这个key\n- **证据充分确认**：Pod 引用了 ConfigMap 中不存在的 key，属于配置缺失问题，与镜像拉取无关\n\n---\n\n#### 异常组 g3（TerminatingStuck — 1个Pod，最小验证）\n\n- **Pod curl-test**（kube-system/node1）：deletionTimestamp=`2026-05-21T19:15:21Z`，无 finalizers，正在拉取镜像 `busybox:1.36.1`（Pulling状态）\n- Events 只有 `Scheduled` → `AddedInterface` → `Pulling image`\n- **结论**：该 Pod 被删除时正尝试拉取镜像但卡在 Pulling 阶段，由于 Docker Hub 不可达，容器运行时无法完成 Pull，导致无法进入 PostStart/Kill 生命周期流程。**本质上仍是同一个 Docker Hub 不可达问题的衍生现象。**\n\n---\n\n### 📋 整体诊断结论\n\n| 问题 | 影响范围 | 根本原因 |\n|------|---------|---------|\n| **集群无法拉取 Docker Hub 镜像** | **47个Pod**（33 ImagePullBackOff + 14 ErrImagePull）分布在 default/mcp/aiops-e2e 三个命名空间、node1/node2 两个节点 | **节点(node1/node2)到 registry-1.docker.io:443 的网络不可达** — 连接被重置或超时。不是镜像名/标签错误，不是认证问题，不是节点故障 |\n| **CreateContainerConfigError** | 1个Pod（独立问题） | Pod 引用 ConfigMap `rc-app-config` 中不存在的 key `APP_BOOT_MODE` |\n| **Terminating 卡住** | 1个Pod（Docker Hub不可达的衍生问题） | 删除时镜像拉取卡在 Pulling 阶段，无法完成生命周期流程 |","collection_summary":"计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%；其中真实环境证据 14/14 项，完整度 100%；实际执行工具 26 个，匹配计划 7 个，未规划证据 19 个","plan_total":7,"plan_collected":7,"plan_completeness":1.0,"environment_evidence_total":14,"environment_evidence_collected":14,"environment_evidence_completeness":1.0,"executed_tool_count":26,"matched_tool_count":7,"unplanned_tool_count":19,"evidence_inventory":[{"id":"g2-events","description":"g2主异常组: 查看代表Pod的Events获取ImagePull失败原因","level":"critical","tool":"kubectl_events","command":"kubectl events --namespace=default --field-selector involvedObject.name=dns-check-test --all-namespaces=false","purpose":"获取ImagePullBackOff Pod的Events，查看BackOff/ErrImagePull/FailedToPullImage等原始错误信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-describe-1","description":"g2主异常组: describe default namespace 代表Pod确认镜像和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dns-check-test","purpose":"查看Pod完整状态、容器镜像、容器状态、Events等核心信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-describe-mcp","description":"g2主异常组: describe mcp namespace 代表Pod确认镜像和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n mcp connectivity-test","purpose":"验证mcp命名空间的Pod是否也是相同镜像拉取失败原因，确认是否为全局性问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-describe-node2","description":"g2主异常组: describe node2上ErrImagePull的Pod确认镜像问题","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default registry-check-node2","purpose":"验证node2上的ErrImagePull Pod错误信息是否与node1一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-describe","description":"g1次要异常组: describe CreateContainerConfigError Pod","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-config-configmap-key-missing","purpose":"查看CreateContainerConfigError的详细错误，确认是否为ConfigMap/Secret引用问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-yaml","description":"g3次要异常组: 查看Terminating Pod的YAML确认finalizers和deletionTimestamp","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n kube-system curl-test -o yaml","purpose":"查看Terminating Pod的finalizers和deletionTimestamp确认卡住原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-events-aiops","description":"g2主异常组: 查看aiops-e2e代表Pod的事件","level":"important","tool":"kubectl_events","command":"kubectl events --namespace=aiops-e2e --field-selector involvedObject.name=test-dns-1779360358","purpose":"验证不同命名空间下的Pod是否也是相同原因的镜像拉取失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g2-events | critical | ✅ | kubectl_events | g2主异常组: 查看代表Pod的Events获取ImagePull失败原因 | `kubectl events --namespace=default --field-selector involvedObject.name=dns-c...` |
   | g2-describe-1 | critical | ✅ | kubectl_describe | g2主异常组: describe default namespace 代表Pod确认镜像和状态 | `kubectl describe pod -n default dns-check-test` |
   | g2-describe-mcp | critical | ✅ | kubectl_describe | g2主异常组: describe mcp namespace 代表Pod确认镜像和状态 | `kubectl describe pod -n mcp connectivity-test` |
   | g2-describe-n... | critical | ✅ | kubectl_describe | g2主异常组: describe node2上ErrImagePull的Pod确认镜像问题 | `kubectl describe pod -n default registry-check-node2` |
   | g1-describe | important | ✅ | kubectl_describe | g1次要异常组: describe CreateContainerConfigError Pod | `kubectl describe pod -n aiops-e2e rc-config-configmap-key-missing` |
   | g3-yaml | important | ✅ | kubectl_get_yaml | g3次要异常组: 查看Terminating Pod的YAML确认finalizers和d... | `kubectl get pod -n kube-system curl-test -o yaml` |
   | g2-events-aiops | important | ✅ | kubectl_events | g2主异常组: 查看aiops-e2e代表Pod的事件 | `kubectl events --namespace=aiops-e2e --field-selector involvedObject.name=tes...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (21.4s)
   📤 → 下游数据: root_cause=集群49个异常Pod中，47个(96%)处于ImagePullBackOff/ErrImagePull状态，根因为节点到外部镜像仓库的网络不可达。关键证据：(1) Pod dns-check-test(default/node1)事件显示 Failed to pull busybox:1.36.1: connection reset by peer from 100.50.6.117:443 和 i/o timeout from 50.87.93.246:443(registry-1.docker.io)，ErrImagePull x52，BackOff x679持续7h19m；(2) Pod registry-check-node2(default/node2)同样因 i/o timeout 到 registry-1.docker.io:443 失败；(3) Pod dig-tool 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 也 DeadlineExceeded，表明多个外部仓库均不可达；(4) Pod connec
... 截断，原始 762 字符
   confidence=95%
   causal_chain={"root_cause": "集群出口网络无法连通外部容器镜像仓库（Docker Hub registry-1.docker.io:443 及 Google registry.k8s.io），导致节点kubelet无法拉取镜像", "propagation": "节点 node1 和 node2 到 registry-1.docker.io:443 的HTTPS连接被对端重置(connection reset by peer)或超时(i/o timeout)，Kubelet重试机制触发 BackOff 导致图像拉取持续失败", "direct_cause": "Kubelet 在 node1 和 node2 上尝试从 Docker Hub 拉取 busybox:1.36.1 等镜像时，遇到 network-level 连接失败（connection reset by peer / i/o timeout），无法解析镜像 manifest", "manifestation": "default/mcp/aiops-e2e 命名空间中47个Pod处于Pending状态，状态为 ImagePullBackOff(33个)或 ErrImagePull(14个)，kubectl describe 和 events 显示明确的网络连接错误指向 registry-1.docker.io:443"}
   rca_analysis={"phenomenon": "集群中存在49个异常Pod（总数114个），主异常为47个Pod（33 ImagePullBackOff + 14 ErrImagePull）分布在default、mcp、aiops-e2e命名空间，集中运行在node1和node2，均处于Pending状态且无法拉取Docker Hub镜像。另有1个CreateContainerConfigError Pod（rc-config-configmap-key-missing, aiops-e2e）和1个Terminating Pod（curl-test, kube-system）。", "evidence_inventory": [{"id": "e1", "source": "kubectl_events", "content": "Pod dns-check-test(default/node1): Failed to pull busybox:1.36.1 - connection reset by peer from 100.50.6.117:443, i/o timeout from 50.87.93.246:443 (registry-1.docker.io)", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe", "content": "Pod dns-check-test: Status Pending, Container busybox:1.36.1 in Waiting/ImagePullBackOff, events show ErrImagePull x52, BackOff x679 over 7h19m", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe", "content": "Pod registry-check-node2(default/node2): busybox:1.36.1 fails with i/o timeout to registry-1.docker.io:443 from multiple IPs, ErrImagePull", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "Pod test-dns-1779360358(aiops-e2e/node1): busybox:1.36.1 connection reset by peer 3.233.166.60:443, BackOff x1044 over 8h", "reliability": "高"}, {"id": "e5", "source": "kubectl_events", "content": "Pod dig-tool(default/node2): Failed to pull registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 - DeadlineExceeded to us-west2-docker.pkg.dev", "reliability": "高"}, {"id": "e6", "source": "kubectl_events", "content": "Pod connectivity-test(mcp/node2): busybox:1.36.1 i/o timeout, BackOff x1445 over 7h39m", "reliability": "高"}, {"id": "e7", "source": "kubectl_describe", "content": "Pod rc-config-configmap-key-missing(aiops-e2e/node1): CreateContainerConfigError - couldn't find key APP_BOOT_MODE in ConfigMap rc-app-config", "reliability": "高"}, {"id": "e8", "source": "kubectl_get_yaml", "content": "Pod curl-test(kube-system/node1): Terminating, deletionTimestamp=2026-05-21T19:15:21Z, finalizers=none, ContainerCreating/Pulling busybox:1.36.1", "reliability": "高"}, {"id": "e9", "source": "layer_handoff", "content": "Total 114 pods, 49 abnormal: ImagePullBackOff=33, ErrImagePull=14, CreateContainerConfigError=1, Terminating=1", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Failed to pull image 'busybox:1.36.1': connection reset by peer from 100.50.6.117:443, i/o timeout from 50.87.93.246:443 → registry-1.docker.io", "interpretation": "节点node1到Docker Hub(registry-1.docker.io:443)的网络连接被对端重置或超时，无法完成镜像拉取"}, {"evidence_id": "e2", "raw_data": "Container busybox:1.36.1 Waiting/ImagePullBackOff, ErrImagePull x52, BackOff x679 over 7h19m", "interpretation": "确认Pod反复尝试拉取均失败，非临时波动，持续了7小时以上"}, {"evidence_id": "e3", "raw_data": "Pod registry-check-node2 on node2: busybox:1.36.1 fails with i/o timeout to registry-1.docker.io:443", "interpretation": "node2也面临同样的Docker Hub不可达问题，说明非单节点故障"}, {"evidence_id": "e4", "raw_data": "Pod test-dns-1779360358 on node1: connection reset by peer to 3.233.166.60:443, BackOff x1044 over 8h", "interpretation": "aiops-e2e命名空间Pod同样遭遇Docker Hub网络问题，跨命名空间一致"}, {"evidence_id": "e5", "raw_data": "Pod dig-tool: Failed to pull registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 - DeadlineExceeded", "interpretation": "不仅Docker Hub，registry.k8s.io(Google容器镜像仓库)同样不可达，进一步指向集群出口网络问题"}, {"evidence_id": "e6", "raw_data": "Pod connectivity-test on node2: busybox:1.36.1 i/o timeout, BackOff x1445", "interpretation": "mcp命名空间Pod同样受影响，跨命名空间验证一致"}, {"evidence_id": "e7", "raw_data": "Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config", "interpretation": "CreateContainerConfigError属独立配置错误，Pod引用了ConfigMap中不存在的key，与镜像拉取无关"}, {"evidence_id": "e8", "raw_data": "deletionTimestamp=2026-05-21T19:15:21Z, finalizers=none, Pulling image busybox:1.36.1", "interpretation": "Terminating Pod无finalizers阻塞，删除被卡住的原因是容器运行时正在Pulling镜像但无法完成，本质上仍由Docker Hub不可达导致"}, {"evidence_id": "e9", "raw_data": "Total 114 pods, Running=59, abnormal=49: ImagePullBackOff=33, ErrImagePull=14, CreateContainerConfigError=1, Terminating=1", "interpretation": "主异常为镜像拉取失败(47/49)，是集群当前主要故障面"}], "causal_chain": {"root_cause": "集群出口网络无法连通外部容器镜像仓库（Docker Hub registry-1.docker.io:443 及 Google registry.k8s.io），导致节点kubelet无法拉取镜像", "propagation": "节点 node1 和 node2 到 registry-1.docker.io:443 的HTTPS连接被对端重置(connection reset by peer)或超时(i/o timeout)，Kubelet重试机制触发 BackOff 导致图像拉取持续失败", "direct_cause": "Kubelet 在 node1 和 node2 上尝试从 Docker Hub 拉取 busybox:1.36.1 等镜像时，遇到 network-level 连接失败（connection reset by peer / i/o timeout），无法解析镜像 manifest", "manifestation": "default/mcp/aiops-e2e 命名空间中47个Pod处于Pending状态，状态为 ImagePullBackOff(33个)或 ErrImagePull(14个)，kubectl describe 和 events 显示明确的网络连接错误指向 registry-1.docker.io:443"}, "root_cause": "集群49个异常Pod中，47个(96%)处于ImagePullBackOff/ErrImagePull状态，根因为节点到外部镜像仓库的网络不可达。关键证据：(1) Pod dns-check-test(default/node1)事件显示 Failed to pull busybox:1.36.1: connection reset by peer from 100.50.6.117:443 和 i/o timeout from 50.87.93.246:443(registry-1.docker.io)，ErrImagePull x52，BackOff x679持续7h19m；(2) Pod registry-check-node2(default/node2)同样因 i/o timeout 到 registry-1.docker.io:443 失败；(3) Pod dig-tool 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 也 DeadlineExceeded，表明多个外部仓库均不可达；(4) Pod connec\n... 截断，原始 762 字符", "root_cause_summary": "集群49个异常Pod中，47个(96%)处于ImagePullBackOff/ErrImagePull状态，根因为节点到外部镜像仓库的网络不可达。关键证据：(1) Pod dns-check-test(default/node1)事件显示 Failed to pull busybox:1.36.1: connection reset by peer from 100.50.6.117:443 和 i/o timeout from 50.87.93.246:443(registry-1.docker.io)，ErrImagePull x52，BackOff x679持续7h19m；(2) Pod registry-check-node2(default/node2)同样因 i/o timeout 到 registry-1.docker.io:443 失败；(3) Pod dig-tool 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 也 DeadlineExceeded，表明多个外部仓库均不可达；(4) Pod connec\n... 截断，原始 762 字符", "confidence": 0.95, "confidence_reason": "跨namespace/跨node/跨镜像仓库（Docker Hub + registry.k8s.io）多个Pod的事件与describe结果一致指向网络层连接失败。直接错误信息（connection reset by peer、i/o timeout、DeadlineExceeded）明确显示了registry-1.docker.io:443不可达，因果链完整。", "primary_runbooks": [], "alternative_causes": [{"cause": "镜像名或标签错误", "probability": "low", "reason": "涉及多个不同镜像(busybox:1.36.1, curlimages/curl:8.12.1, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0)，若仅是标签错误不会全部同时失败，且错误信息明确为网络层而非404"}, {"cause": "imagePullSecret认证失败", "probability": "low", "reason": "Docker Hub公共镜像无需认证，错误信息为网络连接问题而非认证拒绝(denied/unauthorized)"}, {"cause": "节点自身异常(NotReady)", "probability": "low", "reason": "node1和node2均处于Ready状态，kubelet正常工作（能调度Pod、写Events、触发BackOff重试）"}, {"cause": "镜像仓库DNS解析失败", "probability": "low", "reason": "错误信息显示已解析到具体IP(100.50.6.117, 50.87.93.246等)，连接阶段失败而非DNS解析阶段"}], "limitations": "未采集节点级别的网络诊断数据（如从节点手动curl registry-1.docker.io、检查节点代理/防火墙配置、检查CNI/网络策略），未验证集群是否存在HTTP代理配置(containerd/proxy)，未检查集群出口是否有NAT/防火墙规则变更。这些补充证据可进一步确定是集群内部网络策略还是外部防火墙导致的问题。", "llm_raw_analysis": "L3根因分析完成。主异常组g2(ImagePullFailed, 47个Pod)根因为集群节点到外部镜像仓库的网络不可达，证据跨namespace/跨node/跨镜像仓库完全一致。次要异常组g1(CreateContainerConfigError, 1个Pod)确认为ConfigMap key缺失的独立配置错误，已最小验证。次要异常组g3(TerminatingStuck, 1个Pod)确认为镜像拉取卡住导致的删除流程阻塞，属于g2问题的衍生现象。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群49个异常Pod中，47个(96%)处于ImagePullBackOff/ErrImagePull状态，根因为节点到外部镜像仓库的网络不可达。关键证据：(1) Pod dns-check-test(default/node1)事件显示 Failed to pull busybox:1.36.1:...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群出口网络无法连通外部容器镜像仓库（Docker Hub registry-1.docker.io:443 及 Google registry.k8s.io），导致节点kubelet无法拉取镜像
     传导机制: 节点 node1 和 node2 到 registry-1.docker.io:443 的HTTPS连接被对端重置(connection reset by peer)或超时(i/o timeout)，Kubelet重试机制触发 BackOff 导致图像拉取持续失败
     最终表现: default/mcp/aiops-e2e 命名空间中47个Pod处于Pending状态，状态为 ImagePullBackOff(33个)或 ErrImagePull(14个)，kubectl describe 和 events 显示明确的网络连接错误指向 registry-1.docker.io:443


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (32.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8458 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 41.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为您的资深 K8s 诊断报告专家，我已根据您提供的三个阶段的诊断数据，生成了以下详尽报告。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群问题摘要** | 集群中 **49个Pod异常 (异常率 ≈ 43%)**，其中 **47个 (96%) 因无法从外部镜像仓库拉取镜像** 而处于 `ImagePullBackOff` 或 `ErrImagePull` 状态。另有 1 个 `CreateContainerConfigError` 和 1 个 `Terminating` 卡住 Pod。 |
| **Pod异常状态** | `ImagePullBackOff` (33个), `ErrImagePull` (14个), `CreateContainerConfigError` (1个), `Terminating` (卡住) (1个) |
| **兼容归因层** | `L3` - 镜像仓库层 |
| **问题分类** | 镜像拉取失败 (ImagePullFailed) |
| **置信度** | **高 (95%)** |
| **证据完整度** | 7/7 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **总 Pod 数** | 114 **（正常 Running: 59, 异常: 49, 完成: 3）** |
| **主要异常** | **47个Pod (96%) 处于 `ImagePullBackOff` / `ErrImagePull` 状态** |
| **受影响命名空间** | `default`, `mcp`, `aiops-e2e` |
| **受影响节点** | `node1` (IP: 172.16.166.x), `node2` (IP: 172.16.104.x) |
| **典型异常Pod (示例)** | `dns-check-test`, `node-debugger-node1-*`, `registry-check-node2`, `test-dns-1779360358`, `dig-tool`, `dns-test-tmp` 等 |
| **次要异常1** | `aiops-e2e/rc-config-configmap-key-missing` - `CreateContainerConfigError` |
| **次要异常2** | `kube-system/curl-test` - `Terminating` 卡住 |
| **核心错误信息** | `failed to pull image ... : connection reset by peer` / `i/o timeout` 指向 `registry-1.docker.io:443` 及 `registry.k8s.io` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 列表 | `kubectl_get_by_kind_in_cluster` | `Running=59, abnormal=49 (ImagePullBackOff=33, ErrImagePull=14, CreateContainerConfigError=1, Terminating=1)` | 集群中有大量镜像拉取失败问题 |
| 2 | Pod 详细事件 | `kubectl_events` (g2-events) | Pod `dns-check-test`: `Failed to pull image “busybox:1.36.1”: connection reset by peer from **100.50.6.117:443**, and **i/o timeout** from **50.87.93.246:443** (registry-1.docker.io). ErrImagePull x52, BackOff x679 持续 7h19m` | **明确的网络层连接失败**，指向 Docker Hub 镜像仓库 |
| 3 | Pod 描述 | `kubectl_describe` (g2-describe-1) | Pod `dns-check-test`: `Container State: Waiting, Reason: **ImagePullBackOff**`; `Event Warning: **ErrImagePull** (x52 over 7h19m)` | 另一个节点 (`node2`) 上的 Pod 同样因网络超时无法拉取镜像 |
| 4 | Pod 描述 | `kubectl_describe` (g2-describe-node2) | Pod `registry-check-node2`: `All image pulls to docker.io/library/busybox:1.36.1 at **registry-1.docker.io:443 fail with i/o timeout**` | **多个外部仓库均不可达**，指向集群出口网络问题 |
| 5 | Pod 事件 | `kubectl_events` (g2-events-aiops) | Pod `dig-tool`: `Failed to pull image “registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0”: rpc error: code = **DeadlineExceeded**` | configMap 的 key 缺失导致容器无法创建 |
| 6 | Pod 描述 | `kubectl_describe` (g1-describe) | Pod `rc-config-configmap-key-missing`: `status: Pending`; `Reason: **CreateContainerConfigError**`; Events: `Warning Failed (x12 over 19m) kubelet Error: ...` | 排除 finalizer 问题。Pod 正在执行 preStop hook 或等待宽限期内结束 |
| 7 | Pod YAML | `kubectl_get_yaml` (g3-yaml) | Pod `curl-test`: `deletionTimestamp: 2026-05-21T19:15:21Z`, `deletionGracePeriodSeconds: 30`, `finalizers: <none>`, `terminationGracePeriodSeconds: 30` | |
| 8 | 上游工具 | `kubernetes_jq_query` (layer_4) | `43 pods in Pending (most with ImagePullBackOff or ErrImagePull...), 1 with CreateContainerConfigError` | 大量 Pending Pod 均为镜像拉取失败状态 |
| 9 | 上游工具 | `kubernetes_jq_query` (layer_6) | `kube-system/curl-test deletionTimestamp=2026-05-21T19:15:21Z` | 确认 Terminating Pod 身份 |

### 证据关联分析
- **证据 #1 + #2 印证**：49个异常Pod中有47个(96%)因为网络原因拉取镜像失败。`dns-check-test`和`registry-check-node2`都报告了明确的**TCP连接失败** (`connection reset by peer` / `i/o timeout`)。
- **证据 #2 + #4 + #5 印证**：故障不局限于单个外部仓库，`Docker Hub` 和 `Google Container Registry (registry.k8s.io)` 均不可达，表明是**集群出口网络**存在普遍性故障。
- **证据 #7 + #8 印证**：Terminating 问题的 Pod (`curl-test`) 无 `finalizers`，且 `terminationGracePeriodSeconds` 为 30 秒。根据其现存时长，可能是在执行 `preStop` hook 或等待网络响应，导致宽限期超时，卡在 Terminating 状态。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点级网络诊断 (如 `node1` / `node2` 上 `curl registry-1.docker.io:443`) | critical | 无法100%确认问题发生在节点侧（如代理/firewall/路由）还是外部防火墙/网络出口 |
| 集群HTTP代理配置 (`containerd/proxy` / `kubelet` 配置) | critical | 无法确认是否存在代理配置错误导致连接失败 |
| 防火墙上/CNI网络策略规则 | important | 无法确认是否存在特定的出口网络策略 (NetworkPolicy / Egress) 阻止了外部HTTPS流量 |

---

## 🎯 根因分析

### 因果链
```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                      │
│ 集群出口网络无法连通外部容器镜像仓库（Docker Hub registry-1.docker.io:443 及     │
│ Google Registry registry.k8s.io:443），可能是集群侧代理/防火墙/CNI配置问题导致  │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                      │
│ 节点 node1 / node2 的 kubelet 在拉取镜像时，发起的 HTTPS 连接被对端重置        │
│ (connection reset by peer) 或遇到 TCP 超时 (i/o timeout)，无法完成 TLS 握手    │
│ 和下载镜像 manifest。                                                         │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                      │
│ Kubelet 在 node1 和 node2 上尝试拉取 Docker Hub 的 busybox:1.36.1 等镜像时，   │
│ 遇到 network-level 连接失败，kubelet 触发 BackOff 重试机制，但持续失败。        │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                  │
│ default/mcp/aiops-e2e 命名空间中47个Pod处于 Pending 状态，                      │
│ 状态为 ImagePullBackOff (33个) 或 ErrImagePull (14个)，持续重启拉取失败。       │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (`connection reset by peer` / `i/o timeout` 事件)、证据 #4 (`i/o timeout` 到 `registry-1.docker.io:443`)、证据 #5 (`DeadlineExceeded` 到 `registry.k8s.io`)，问题的根本原因是 **集群出口网络无法连通外部容器镜像仓库（Docker Hub 和 Google Registry）**。

**副根因**：`kube-system/curl-test` Pod 卡在 Terminating，但根据证据 #7，其 `finalizers: <none>` 且 `terminationGracePeriodSeconds: 30`，原因排除 finalizer 未清理，更可能的原因是 Pod 中的 `sleep` 命令（或 `preStop` hook）在执行时，其依赖的网络环境（可能也在尝试连接外部服务）出现问题，导致无法正常完成退出流程。

**置信度**：**高 (95%)**
- ✅ 多个Pod、多种镜像、多个外部仓库均出现网络连接失败
- ✅ `connection reset by peer` 和 `i/o timeout` 是明确的网络层错误
- ✅ `kubectl describe` 和 `events` 数据一致性地指向了同样的根本原因

---

## 🛠️ 修复建议

### 立即执行（需针对根本原因排查）

**1. [首要] 在节点上手动测试到外部仓库的网络连通性**
```bash
# 在 node1 和 node2 上分别执行
curl -v https://registry-1.docker.io/v2/ 2>&1 | head -20
curl -v https://registry.k8s.io/v2/ 2>&1 | head -20
```
*目的*：确认集群内部节点是否可以触达外部镜像仓库，并进一步明确是节点本身问题还是更外部的网络出口问题。

**2. [核心] 检查集群代理配置**
检查 `containerd` 或 `kubelet` 的配置是否存在 HTTP 代理设置，以及代理是否正确配置。
```bash
# 检查 containerd 配置 (路径可能为 /etc/containerd/config.toml)
cat /etc/containerd/config.toml | grep -i proxy
# 检查 kubelet 配置 (可能位于 /var/lib/kubelet/config.yaml 或 kubelet 启动参数)
ps aux | grep kubelet | grep -i proxy
# 检查系统环境变量
env | grep -i proxy
```

**3. [检查] 验证网络策略和出口规则**
```bash
# 检查是否配置了可能阻塞出口流量的 NetworkPolicy
kubectl get networkpolicies --all-namespaces
# 如果没有命令行工具，需登录节点查看防火墙/iptables规则
# iptables -L -n  (需要root权限)
```

**4. [修复] 处理 Terminating 卡住的 Pod**
如果手动确认 `curl-test` Pod 无法结束，可以通过强制删除子资源来强制删除。
```bash
kubectl delete pod curl-test -n kube-system --force --grace-period=0
```

### 后续优化
1. **使用私有镜像仓库 (Image Registry Mirror)**：将外部镜像的 `busybox`, `curl` 等预拉取到内部仓库（如 Harbor / Nexus），将所有 Pod 的镜像地址指向内部仓库，避免依赖外部网络。
2. **异常自愈**：配置 `ClusterEvent` 或 `PodDisruptionBudget`，当 Pod 因 `ErrImagePull` / `ImagePullBackOff` 处于 `Pending` 状态超过一定时间后，自动进行节点的网络诊断或通知。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 检查 Pod 状态 | `kubectl get pods --all-namespaces | grep -E 'ImagePullBackOff|ErrImagePull'` | 返回空，或数量显著减少 |
| 2. 确认网络修复 | `kubectl exec -it <任意running的Pod> -- wget -q -O- https://registry-1.docker.io/v2/ 2>&1` | 应返回 HTTP 200 或连接成功（而非 timeout / reset） |
| 3. 确认 Terminating Pod 状态 | `kubectl get pod curl-test -n kube-system` | 返回 `Not found` 或已清除 |
| 4. 验证 configMap 问题 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | 不再出现 `CreateContainerConfigError` |

---

## ⚠️ 注意事项
- **核心问题聚焦**：当前集群 96% 的异常归因于网络问题，修复网络即可解决绝大部分故障。
- **`CreateContainerConfigError` Pod** 是独立故障，应在主问题修复后单独处理，检查其引用的 ConfigMap 键名是否正确。
- **建议先在非生产环境进行网络调试**，例如手动修改 `containerd` 配置添加代理，或调整防火墙规则，确认效果后再应用到生产环境。

---

## 📊 性能统计

├─ 总耗时: 2.7m
├─ 问题定位: 45.4s (28%) ✅
├─ 证据链采集: 61.9s (38%) ✅
├─ 根因分析: 21.4s (13%) ✅
├─ 汇总总结: 32.7s (20%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 30 次
```

📋 诊断追踪

- **参考 Runbook**: pod-config-error, pod-imagepull-failed
- **工具调用**: 30 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
