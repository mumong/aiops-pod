======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d73fe318d4d44a07]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先全局扫描集群中的所有 Pod，了解当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_all_pods results: ~71 rows total, abnormal pods concentrated in default namespace with mass ImagePullBackOff/ErrImagePull status. One CrashLoopBackOff (rc-notready-liveness in aiops-e2e). 
   💭 [问题定位] 让我获取更完整的异常 Pod 信息，看看具体有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=547 lines=4
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=13634 lines=407
Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "test-dns-1779360358",
  "phase": "Pending",
  "reason": "ImagePullBackOff",

   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=7749 lines=407
Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "test-dns-1779360358",
  "phase": "Pending",
  "status": "ImagePullBackOff",
 
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=6488 lines=349
Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "test-dns-1779360358",
  "status": "ImagePullBackOff",
  "node": "node1"
}
{
 
   💭 [问题定位] 让我获取更完整的异常 Pod 列表。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=3596 lines=59
Executing jq query for pods...
aiops-e2e/test-dns-1779360358 status=ImagePullBackOff node=node1
default/connectivity-check-tmp status=ErrImagePull nod
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=1121 lines=18
Executing jq query for pods...
mcp/node-debugger-node1-2s2mz status=ImagePullBackOff node=node1
mcp/node-debugger-node1-2xvqr status=ImagePullBackOff 
   💭 [问题定位] 现在让我看看那个 CrashLoopBackOff 的 Pod 和检查一下节点状态。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ✅ [问题定位] 完成 (35.7s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '集群节点无法访问外部镜像仓库（Docker Hub/registry.k8s.io）', 'probability': 'high', 'reason': '多个 Pod 错误信息均显示 dial tcp ...:443: connection refused，指向镜像仓库网络不可达'}, {'scenario': '镜像仓库配置或凭证缺失', 'probability': 'low', 'reason': '如果是凭证问题，错误信息通常是 unauthorized 或 not found，而不是 connection refused'}, {'scenario': '集群 DNS/CNI 网络故障导致无法解析镜像仓库域名', 'probability': 'medium', 'reason': '大量 ImagePullBackOff Pod 中包含 dns/dig/nettest 等诊断 Pod，暗示用户在主动排查网络问题'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}, {"type": "pod", "name": "connectivity-check-tmp", "namespace": "default"}]
   reasoning=当前集群存在大量异常 Pod，以 ImagePullBackOff 和 ErrImagePull 为主（约 30+ Pod 分布在 default、aiops-e2e、mcp 命名空间，node1 和 node2 上均有）。此外，aiops-e2e/rc-notready-liveness 处于 CrashLoopBackOff 状态（11 次重启，4 分钟前），已被标注为 NotReadyProbeFailed（L4）。但绝大多数异常 Pod（ImagePullBackOff/ErrImagePull）的原因是无法拉取镜像，如 connectivity-check-tmp 报错 "failed to do request: dial tcp 47.88.58.234:443: connect: connection refused"，指向 Docker Hub 网络不可达。这属于典型的 L3 镜像仓库/网络问题。CrashLoopBackOff 的 Pod 虽然属于 L4，但整体集群异常以 L3 镜像拉取失败为主，因此定层为 L3。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "L3 - 镜像拉取/网络问题", "confidence": 0.95, "reasoning": "当前集群存在大量异常 Pod，以 ImagePullBackOff 和 ErrImagePull 为主（约 30+ Pod 分布在 default、aiops-e2e、mcp 命名空间，node1 和 node2 上均有）。此外，aiops-e2e/rc-notready-liveness 处于 CrashLoopBackOff 状态（11 次重启，4 分钟前），已被标注为 NotReadyProbeFailed（L4）。但绝大多数异常 Pod（ImagePullBackOff/ErrImagePull）的原因是无法拉取镜像，如 connectivity-check-tmp 报错 \"failed to do request: dial tcp 47.88.58.234:443: connect: connection refused\"，指向 Docker Hub 网络不可达。这属于典型的 L3 镜像仓库/网络问题。CrashLoopBackOff 的 Pod 虽然属于 L4，但整体集群异常以 L3 镜像拉取失败为主，因此定层为 L3。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-check-registry", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-tool-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-check-node2", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-diag-evidence-verify", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2s2mz", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}, {"type": "pod", "name": "connectivity-check-tmp", "namespace": "default"}], "possible_scenarios": [{"scenario": "集群节点无法访问外部镜像仓库（Docker Hub/registry.k8s.io）", "probability": "high", "reason": "多个 Pod 错误信息均显示 dial tcp ...:443: connection refused，指向镜像仓库网络不可达"}, {"scenario": "镜像仓库配置或凭证缺失", "probability": "low", "reason": "如果是凭证问题，错误信息通常是 unauthorized 或 not found，而不是 connection refused"}, {"scenario": "集群 DNS/CNI 网络故障导致无法解析镜像仓库域名", "probability": "medium", "reason": "大量 ImagePullBackOff Pod 中包含 dns/dig/nettest 等诊断 Pod，暗示用户在主动排查网络问题"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 47, "ErrImagePull": 9}, "total_abnormal": 57, "selected_rows": ["aiops-e2e         rc-notready-liveness                                0/1     CrashLoopBackOff   11 (4m ago)    27m     172.16.166.129   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0              13h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ImagePullBackOff   0              136m    172.16.104.52    node2    <none>           <none>            run=connectivity-check-tmp", "default           dig-check-registry                                  0/1     ImagePullBackOff   0              76m     172.16.166.155   node1    <none>           <none>            run=dig-check-registry", "default           dig-tool                                            0/1     ImagePullBackOff   0              9h      172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff   0              8h      172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff   0              12h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff   0              5h21m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-diag-tool-evidence                              0/1     ErrImagePull       0              112m    172.16.104.4     node2    <none>           <none>            run=dns-diag-tool-evidence", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff   0              5h26m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ImagePullBackOff   0              5h26m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test                                            0/1     ErrImagePull       0              76m     172.16.104.56    node2    <none>           <none>            run=dns-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0              13h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0              11h     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff   0              5h26m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull       0              8h      172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff   0              12h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0              12h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0              9h      172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ImagePullBackOff   0              5h54m   172.16.104.41    node2    <none>           <none>            run=registry-check-node2"], "raw_ref": "/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有的 evidence_plan。首先从最关键的证据开始采集。

## 第一步：采集主异常组（g2 - ImagePullBackOff/ErrImagePull）的代表 Pod 信息
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-check-tmp (namespace: default, node: node2/10.2.0.50) in Pending status. Container is in Waiting state with Reason: ImagePullBackOff. Pod IP: 172.16.104.52. The kubelet repeatedly fai
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       25m (x10 over 27m)    kubelet      
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: connectivity-check-tmp
namespace: default
creationTimestamp: 2026-05-21T22:13:49Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <non
   💭 [证据链采集] 关键发现！`connectivity-check-tmp` 的 Events 明确显示了 **i/o timeout** 错误。现在继续采集 events 和 logs。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
45m                     Warning   Failed    Pod/connectivity-check-tmp   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and u
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 现在采集 default、aiops-e2e、mcp 命名空间的事件和另一个代表 Pod 的信息。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-diag-tool-evidence in namespace default on node node2/10.2.0.50 is Pending. Container dns-diag-tool-evidence is in ImagePullBackOff (Waiting, Reason: ImagePullBackOff). All 5 pull attempts to 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-check-registry (namespace default, node node1/10.2.0.49) is Pending. Container dig-check-registry (image busybox:1.28) is Waiting with reason ImagePullBackOff, not Ready. All image pull attemp
   💭 [证据链采集] 非常好，证据已经非常清晰了。让我再采集一些关键确认数据。
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS       RESTARTS   AGE     IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-nx8gb   0/1     StartError   0          4h48m   10
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                     READY   STATUS             RESTARTS   AGE    IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
connectivity-check-tmp   0/1     ImagePullBackOff   0          1
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   READY   STATUS    RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-liveness   1/1     Running   12 (5m10s ago)   28m   172.1
   💭 [证据链采集] 现在采集一下 aiops-e2e 和 mcp 命名空间的 ImagePull 事件。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
8m46s (x183 over 13h)   Warning   Failed    Pod/test-dns-1779360358   (combined from similar events): Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceede
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   8m46s (x183 over 13h)  kubelet  (combined from similar events): Fai
   💭 [证据链采集] 所有核心证据已采集完毕。现在让我快速检查一下 mcp 命名空间的事件。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-test in namespace mcp on node node2/10.2.0.50 is Pending with IP 172.16.104.3/32 (Calico). Container state: Waiting (Reason: ImagePullBackOff). All pull attempts to docker.io/library/
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl describe node-debugger-node2-cfk7z (ns:mcp) — Pending, ImagePullBackOff. Container debugger: image busybox:1.36.1 cannot be pulled; all pull attempts to docker.io registry fail with i/o timeou
   💭 [证据链采集] 非常好，关键证据已全面采集。现在我获取 rc-notready-liveness 的详细 describe 完整内容，以及查看该 Pod 的镜像信息。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-liveness
namespace: aiops-e2e
creationTimestamp: 2026-05-22T00:02:45Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <non
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=3149 lines=117
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: "2026-05-21T19:42:18Z"
  name: node-debugger-node1-nx8gb
  namespace: mcp
  resourceVersion: "52
   💭 [证据链采集] [compacted ai_message: original_chars=40]
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
26m (x10 over 28m)     Warning   Unhealthy        Pod/rc-notready-liveness   Liveness probe failed: liveness endpoint failed
3m39s (x85 over 25m)   Warning   BackOff         
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] [compacted ai_message: original_chars=42]
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
53m                      Warning   Failed    Pod/connectivity-test   Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = failed to pull and unpack image "
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
56m                     Warning   Failed    Pod/dns-diag-tool-evidence   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and u
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
47m                    Warning   Failed    Pod/dig-check-registry   Failed to pull image "busybox:1.28": rpc error: code = Unknown desc = failed to pull and unpack image "doc
   💭 [证据链采集] [compacted ai_message: original_chars=68]
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dig-check-registry
namespace: default
creationTimestamp: 2026-05-21T23:13:36Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
s
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: connectivity-test
namespace: mcp
creationTimestamp: 2026-05-21T11:38:46Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
servic
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: node-debugger-node2-cfk7z
namespace: mcp
creationTimestamp: 2026-05-21T13:04:42Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none
   ✅ [证据链采集] 完成 (1m 10.3s)
   📤 → 下游数据: evidence_items=15/17
   evidence_analysis={"evidence_plan":[{"id":"g2-representative-describe","description":"对 g2 异常组（ImagePullBackOff/ErrImagePull）代表 Pod connectivity-check-tmp 做 kubectl describe，获取 Events 中的错误原文（镜像地址、拉取失败原因）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","tool_args":{"kind":"pod","name":"connectivity-check-tmp","namespace":"default","resource_type":"pod"},"purpose":"获取 ImagePullBackOff 的详细错误信息，确认是否如 layer_handoff 所述为 dial tcp connection refused 网络不可达","evidence_type":"pod_events_and_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-representative-yaml","description":"获取 connectivity-check-tmp 的完整 YAML，检查 image、imagePullSecrets、registry 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod connectivity-check-tmp -n default -o yaml","tool_args":{"kind":"pod","name":"connectivity-check-tmp","namespace":"default","resource_type":"pod"},"purpose":"检查 Pod 的镜像地址、imagePullSecrets 等关键配置","evidence_type":"pod_spec_config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-events-default","description":"查看 default 命名空间最近事件，筛选 ImagePullBackOff/ErrImagePull 相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n default --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by=.lastTimestamp","tool_args":{"namespace":"default"},"purpose":"采集 default 命名空间所有 ImagePull 失败事件的详细信息","evidence_type":"cluster_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-crashloop-describe","description":"对 g1 异常组（CrashLoopBackOff）代表 Pod rc-notready-liveness 做 kubectl describe，获取重启原因和 Last State","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"获取 CrashLoopBackOff 的 Last State、退出码和事件，判断是否为镜像相关或探针失败","evidence_type":"pod_events_and_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-crashloop-logs-previous","description":"获取 rc-notready-liveness 的上一次日志，查看退出原因","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","tool_args":{"resource_type":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e","previous":true},"purpose":"查看 CrashLoopBackOff Pod 上一次运行时的日志输出，判断具体错误","evidence_type":"pod_logs","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g3-starterror-describe","description":"对 g3 异常组（StartError）Pod node-debugger-node1-nx8gb 做 kubectl describe，获取具体错误","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp","resource_type":"pod"},"purpose":"获取 StartError 状态的 Pod 的具体事件和状态详情","evidence_type":"pod_events_and_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-events-aiops","description":"查看 aiops-e2e 命名空间 ImagePullBackOff 事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by=.lastTimestamp","tool_args":{"namespace":"aiops-e2e"},"purpose":"采集 aiops-e2e 命名空间 ImagePull 失败事件","evidence_type":"cluster_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-events-mcp","description":"查看 mcp 命名空间 ImagePullBackOff/ErrImagePull 事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by=.lastTimestamp","tool_args":{"namespace":"mcp"},"purpose":"采集 mcp 命名空间 ImagePull 失败事件","evidence_type":"cluster_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-dns-resolution-check","description":"检查集群 DNS 是否正常解析 registry 域名（docker.io 和 registry.k8s.io）","level":"important","tool":"run_bash_command","command":"kubectl run dns-test-evidence --image=busybox:1.36.1 -n default --restart=Never -- nslookup docker.io 2>&1 || echo 'DNS check failed - likely cannot pull image'","tool_args":{"command":"kubectl run dns-test-evidence --image=busybox:1.36.1 -n default --restart=Never -- nslookup docker.io 2>&1 || echo 'DNS check failed - likely cannot pull image'"},"purpose":"验证集群 DNS 是否能解析 Docker Hub 域名","evidence_type":"dns_resolution","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-gcr-registry-check","description":"验证 registry.k8s.io 域名解析","level":"optional","tool":"run_bash_command","command":"kubectl run registry-resolve-test --image=busybox:1.36.1 -n default --restart=Never -- nslookup registry.k8s.io 2>&1 || echo 'Registry DNS check failed'","tool_args":{"command":"kubectl run registry-resolve-test --image=busybox:1.36.1 -n default --restart=Never -- nslookup registry.k8s.io 2>&1 || echo 'Registry DNS check failed'"},"purpose":"验证 registry.k8s.io 域名解析是否正常","evidence_type":"dns_resolution","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:               \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod connectivity-check-tmp (namespace: default, node: node2/10.2.0.50) in Pending status. Container is in Waiting state with Reason: ImagePullBackOff. Pod IP: 172.16.104.52. The kubelet repeatedly fails to pull image busybox:1.36.1 from docker.io — multiple i/o timeout errors hitting different registry IPs (69.30.25.21, 108.160.169.181, 108.160.165.173, 128.242.245.125) and one pull QPS exceeded event. Back-off pulling image occurred 55 times over 126m.\nkey_facts: [\"Pod: connectivity-check-tmp / namespace: default\", \"Node: node2\", \"Status: Pending\", \"Container State: Waiting (Reason: ImagePullBackOff)\", \"Container Ready: False\", \"Image: busybox:1.36.1\", \"Events: repeated Failed to pull image — i/o timeout dialing registry-1.docker.io:443 (4 distinct IPs)\", \"Events: pull QPS exceeded at 3m45s ago\", \"Events: BackOff pulling image x55 over 126m\", \"Events: ErrImagePull x14 over 126m\", \"Pod IP: 172.16.104.52\", \"QoS Class: BestEffort\"]\nmissing: [\"Container ID not set\", \"Image ID not set\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       25m (x10 over 27m)    kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         2m48s (x85 over 24m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         26m (x3 over 27m)     kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: f997c06136714184f9866361b3eab26ff46c280103b276058ecb6da12e4ce2e4\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       27m           \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: connectivity-check-tmp\nnamespace: default\ncreationTimestamp: 2026-05-21T22:13:49Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- connectivity-check-tmp: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c wget -q -O- --timeout=5 https://registry-1.docker.io/v2/ 2>&1 || echo FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [connectivity-check-tmp]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [connectivity-check-tmp]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- connectivity-check-tmp: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-8qvlz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/005-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/005-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/005-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n45m                     Warning   Failed    Pod/connectivity-check-tmp   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.30.25.21:443: i/o timeout\n32m                     Warning   Failed    Pod/connectivity-check-tmp   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.169.181:443: i/o timeout\n19m                     Warning   Failed    Pod/connectivity-check-tmp   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/006-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/006-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/006-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/007-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/007-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/007-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_describe","data":"Pod dns-diag-tool-evidence in namespace default on node node2/10.2.0.50 is Pending. Container dns-diag-tool-evidence is in ImagePullBackOff (Waiting, Reason: ImagePullBackOff). All 5 pull attempts to image busybox:1.36.1 from docker.io failed with i/o timeout dialing registry-1.docker.io:443 (multiple IPs: 108.160.173.207, 173.231.12.107, 128.121.243.228, 208.43.170.231, 108.160.167.30). Errors include DeadlineExceeded and Unknown. BackOff seen 47x over 102m. Pod has IP 172.16.104.4 assigned via Calico. Container args: nslookup registry-1.docker.io. Ready: False, Restart Count: 0.\nkey_facts: [\"Pod: dns-diag-tool-evidence, Namespace: default, Node: node2/10.2.0.50\", \"Status: Pending\", \"Container: dns-diag-tool-evidence, Image: busybox:1.36.1\", \"Container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False, Restart Count: 0\", \"Pod IP: 172.16.104.4 (Calico)\", \"Args: nslookup registry-1.docker.io\", \"All 5 pull attempts failed: i/o timeout dialing registry-1.docker.io:443 (IPs: 108.160.173.207, 173.231.12.107, 128.121.243.228, 208.43.170.231, 108.160.167.30)\", \"Errors: DeadlineExceeded (3x) and Unknown (2x)\", \"BackOff: x47 over 102m, ErrImagePull: x13 over 102m\", \"QoS Class: BestEf\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/008-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/008-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/008-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-check-registry (namespace default, node node1/10.2.0.49) is Pending. Container dig-check-registry (image busybox:1.28) is Waiting with reason ImagePullBackOff, not Ready. All image pull attempts to docker.io/library/busybox:1.28 failed: first due to dial tcp 74.86.151.167:443 i/o timeout (46m ago), then repeated failures with connection reset by peer from 10.2.0.49:55704->3.208.234.98:443. Events show x171 BackOff pulls over 69m, x7 ErrImagePull over 69m. PodIP 172.16.166.155. QoS BestEffort. Container args: nslookup registry.k8s.io 2>&1 || echo DNS_FAILED.\nkey_facts: [\"Pod dig-check-registry, namespace default, status Pending\", \"Node: node1/10.2.0.49\", \"Container: dig-check-registry, image busybox:1.28\", \"State: Waiting, Reason: ImagePullBackOff\", \"Ready: False\", \"All pull attempts to docker.io/library/busybox:1.28 failed\", \"Error: ErrImagePull (x7 over 69m)\", \"Failed pull: dial tcp 74.86.151.167:443 i/o timeout\", \"Failed pull (10x combined): read tcp 10.2.0.49:55704->3.208.234.98:443 connection reset by peer\", \"BackOff pulling image (x171 over 69m)\", \"Container args: sh -c 'nslookup registry.k8s.io 2>&1 || echo DNS_FAILED'\", \"PodIP: 172.16.166.155\", \"QoS Class: BestEffort\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/009-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/009-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/009-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                        READY   STATUS       RESTARTS   AGE     IP          NODE    NOMINATED NODE   READINESS GATES   LABELS\nnode-debugger-node1-nx8gb   0/1     StartError   0          4h48m   10.2.0.49   node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/010-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/010-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/010-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                     READY   STATUS             RESTARTS   AGE    IP              NODE    NOMINATED NODE   READINESS GATES   LABELS\nconnectivity-check-tmp   0/1     ImagePullBackOff   0          137m   172.16.104.52   node2   <none>           <none>            run=connectivity-check-tmp","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/011-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/011-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/011-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                   READY   STATUS    RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-notready-liveness   1/1     Running   12 (5m10s ago)   28m   172.16.166.129   node1   <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/012-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/012-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/012-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n8m46s (x183 over 13h)   Warning   Failed    Pod/test-dns-1779360358   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.184.142:443: i/o timeout\n5m5s (x1990 over 13h)   Normal    BackOff   Pod/test-dns-1779360358   Back-off pulling image \"busybox:1.36.1\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/013-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/013-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/013-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   8m46s (x183 over 13h)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.184.142:443: i/o timeout\n  Normal   BackOff  5m5s (x1990 over 13h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Conta\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/014-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/014-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/014-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod connectivity-test in namespace mcp on node node2/10.2.0.50 is Pending with IP 172.16.104.3/32 (Calico). Container state: Waiting (Reason: ImagePullBackOff). All pull attempts to docker.io/library/busybox:1.36.1 have failed over 12h due to network errors (i/o timeout, connection refused) connecting to registry-1.docker.io. BackOff x1511 in 12h, Failed x104 in 12h.\nkey_facts: [\"Name: connectivity-test\", \"Namespace: mcp\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"IP: 172.16.104.3/32 (Calico)\", \"Container: connectivity-test\", \"Image: busybox:1.36.1\", \"Container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False\", \"Restart Count: 0\", \"Container args: sh -c curl -v --connect-timeout 10 https://registry-1.docker.io/v2/ 2>&1 || true\", \"Events: multiple Failed pull attempts over 12h - all dial tcp errors (i/o timeout and connection refused) to registry-1.docker.io:443\", \"BackOff: Normal event x1511 over 12h\", \"ErrImagePull: Warning event x104 over 12h\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary omits the container's actual command (curl to registry-1.docker.io/v2/)\", \"current_summ\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/015-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/015-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/015-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl describe node-debugger-node2-cfk7z (ns:mcp) — Pending, ImagePullBackOff. Container debugger: image busybox:1.36.1 cannot be pulled; all pull attempts to docker.io registry fail with i/o timeout (multiple IPs: 69.30.25.21, 108.160.166.42, 108.160.165.173, 69.171.224.36:443). Also 2x pull QPS exceeded, 1184x BackOff over 11h, 87x ErrImagePull. Pod on node2/10.2.0.50, BestEffort QoS, no node selectors, tolerations op=Exists.\nkey_facts: [\"Pod: node-debugger-node2-cfk7z (ns:mcp)\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Container: debugger — State: Waiting, Reason: ImagePullBackOff\", \"Image: busybox:1.36.1 (from docker.io/library)\", \"Container ID/Image ID: empty (never pulled)\", \"Events: repeated Failed to pull image — all i/o timeout dialing registry-1.docker.io:443 (IPs: 69.30.25.21, 108.160.166.42, 108.160.165.173, 69.171.224.36)\", \"Events: 2x pull QPS exceeded (over 73m)\", \"Events: 87x ErrImagePull (over 11h)\", \"Events: 1184x BackOff (over 11h)\", \"QoS Class: BestEffort\", \"Command: sh -c with nslookup/wget/nc debug commands targeting registry-1.docker.io\", \"Volumes: host-root (Path: /), kube-api-access-kc5gj\"]\nconflicts: [\"current_summary lists 4 Failed events (44m,31m,18m,6m42s) but raw_preview shows 5 distinct Failed pull events (44m,31m,18m,6m42s with new IP 69.171.224.36, and another 6m42s), plus a Normal Pulling event (18m x93 over 11h) not in summary\"]\nmissing: [\"raw_preview has Normal Pulling event (18m, x93 over 11h) not reflected in summary\", \"raw_preview shows debugger command includes nslookup/wget/nc diagnostic commands (not just sh -c)\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/016-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/016-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/016-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-liveness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-22T00:02:45Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-liveness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 86400\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=True reason=None\n- ContainersReady: status=True reason=None\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=True restarts=12 reason=Error exitCode=137\nvolumes:\n- {\"name\": \"kube-api-access-84xz2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/017-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/017-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/017-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=3149 lines=117\napiVersion: v1\nkind: Pod\nmetadata:\n  creationTimestamp: \"2026-05-21T19:42:18Z\"\n  name: node-debugger-node1-nx8gb\n  namespace: mcp\n  resourceVersion: \"52801137\"\n  uid: 4cc072ec-47f2-456e-8741-97a2d7f108d8\nspec:\n  containers:\n  - command:\n    - curl\n    - -s\n    - -o\n    - /dev/null\n    - -w\n    - '%{http_code}'\n    - --connect-timeout\n    - \"5\"\n    - https://registry-1.docker.io/v2/\n    image: busybox:1.36\n    imagePullPolicy: IfNotPresent\n    name: debugger\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /host\n      name: host-root\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-hl45s\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  hostIPC: true\n  hostNetwork: true\n  hostPID: true\n  nodeName: node1\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/018-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/018-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/018-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n26m (x10 over 28m)     Warning   Unhealthy        Pod/rc-notready-liveness   Liveness probe failed: liveness endpoint failed\n3m39s (x85 over 25m)   Warning   BackOff          Pod/rc-notready-liveness   Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n27m (x3 over 28m)      Normal    Killing          Pod/rc-notready-liveness   Container app failed liveness probe, will be restarted\n28m                    Normal    Scheduled        Pod/rc-notready-liveness   Successfully assigned aiops-e2e/rc-notready-liveness to node1\n28m                    Normal    AddedInterface   Pod/rc-notready-liveness   Add eth0 [172.16.166.129/32] from k8s-pod-network\n26m (x4 over 28m)      Normal    Pulled           Pod/rc-notready-liveness   Container image \"busybox:1.36\" already present on machine\n26m (x4 over 28m)      Normal    Created          Pod/rc-notready-liveness   Created container app\n26m (x4 over 28m)      Normal    Started          Pod/rc-notready-liveness   Started container app","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/019-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/019-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/019-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/020-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/020-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/020-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n53m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 185.60.216.11:443: i/o timeout\n40m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 65.49.26.99:443: i/o timeout\n27m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.167.158:443: i/o timeout\n15m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 208.43.170.231:443: i/o timeout\n4m40s                    Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 54.89.135.129:443: connect: connection refused\n2m47s (x1511 over 12h)   Normal    BackOff   Pod/connectivity-test   Back-off pulling image \"busybox:1.36.1\"\n4m40s (x104 over 12h)    Warning   Failed    Pod/connectivity-test   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/021-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/021-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/021-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n56m                     Warning   Failed    Pod/dns-diag-tool-evidence   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.173.207:443: i/o timeout\n43m                     Warning   Failed    Pod/dns-diag-tool-evidence   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 173.231.12.107:443: i/o timeout\n30m                     Warning   Failed    Pod/dns-diag-tool-evidence   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 128.121.243.228:443: i/o timeout\n17m                     Warning   Failed    Pod/dns-diag-tool-evidence   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 208.43.170.231:443: i/o timeout\n5m40s                   Warning   Failed    Pod/dns-diag-tool-evidence   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.167.30:443: i/o timeout\n3m11s (x47 over 103m)   Normal    BackOff   Pod/dns-diag-tool-evidence   Back-off pulling image \"busybox:1.36.1\"\n5m40s (x13 over 103m)   Warning   Failed    Pod/dns-diag-tool-evidence   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/022-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/022-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/022-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n47m                    Warning   Failed    Pod/dig-check-registry   Failed to pull image \"busybox:1.28\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.28\": failed to resolve reference \"docker.io/library/busybox:1.28\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.28\": dial tcp 74.86.151.167:443: i/o timeout\n8m15s (x10 over 45m)   Warning   Failed    Pod/dig-check-registry   (combined from similar events): Failed to pull image \"busybox:1.28\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.28\": failed to resolve reference \"docker.io/library/busybox:1.28\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.28\": read tcp 10.2.0.49:55704->3.208.234.98:443: read: connection reset by peer\n31s (x192 over 70m)    Normal    BackOff   Pod/dig-check-registry   Back-off pulling image \"busybox:1.28\"\n47m (x7 over 70m)      Warning   Failed    Pod/dig-check-registry   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/023-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/023-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/023-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dig-check-registry\nnamespace: default\ncreationTimestamp: 2026-05-21T23:13:36Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dig-check-registry: image=busybox:1.28 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry.k8s.io 2>&1 || echo DNS_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dig-check-registry]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dig-check-registry]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dig-check-registry: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.28\"\nvolumes:\n- {\"name\": \"kube-api-access-8nxw8\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/024-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/024-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/024-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: connectivity-test\nnamespace: mcp\ncreationTimestamp: 2026-05-21T11:38:46Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- connectivity-test: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c curl -v --connect-timeout 10 https://registry-1.docker.io/v2/ 2>&1 || true\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [connectivity-test]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [connectivity-test]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- connectivity-test: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-zhjs9\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/025-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/025-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/025-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: node-debugger-node2-cfk7z\nnamespace: mcp\ncreationTimestamp: 2026-05-21T13:04:42Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 1\ncontainers:\n- debugger: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  command: sh -c nslookup registry-1.docker.io 2>&1; echo '---'; timeout 5 wget -q -O- https://registry-1.docker.io/v2/ 2>&1 || echo 'wget failed/timeout'; echo '---'; timeout 5 nc -zv registry-1.docker.io 443 2>&1 || echo 'nc failed/timeout'\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [debugger]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [debugger]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- debugger: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"host-root\"}\n- {\"name\": \"kube-api-access-kc5gj\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/026-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/026-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d73fe318d4d44a07/tools/026-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"[compacted ai_message: original_chars=68]","collection_summary":"计划 9 项，实际采集 8 项，未采集 1 项，完整度 89%；其中真实环境证据 15/16 项，完整度 94%；实际执行工具 32 个，匹配计划 8 个，未规划证据 24 个","plan_total":9,"plan_collected":8,"plan_completeness":0.8888888888888888,"environment_evidence_total":16,"environment_evidence_collected":15,"environment_evidence_completeness":0.9375,"executed_tool_count":32,"matched_tool_count":8,"unplanned_tool_count":24,"evidence_inventory":[{"id":"g2-representative-describe","description":"对 g2 异常组（ImagePullBackOff/ErrImagePull）代表 Pod connectivity-check-tmp 做 kubectl describe，获取 Events 中的错误原文（镜像地址、拉取失败原因）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","purpose":"获取 ImagePullBackOff 的详细错误信息，确认是否如 layer_handoff 所述为 dial tcp connection refused 网络不可达","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-representative-yaml","description":"获取 connectivity-check-tmp 的完整 YAML，检查 image、imagePullSecrets、registry 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod connectivity-check-tmp -n default -o yaml","purpose":"检查 Pod 的镜像地址、imagePullSecrets 等关键配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-events-default","description":"查看 default 命名空间最近事件，筛选 ImagePullBackOff/ErrImagePull 相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n default --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by=.lastTimestamp","purpose":"采集 default 命名空间所有 ImagePull 失败事件的详细信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-crashloop-describe","description":"对 g1 异常组（CrashLoopBackOff）代表 Pod rc-notready-liveness 做 kubectl describe，获取重启原因和 Last State","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"获取 CrashLoopBackOff 的 Last State、退出码和事件，判断是否为镜像相关或探针失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-crashloop-logs-previous","description":"获取 rc-notready-liveness 的上一次日志，查看退出原因","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","purpose":"查看 CrashLoopBackOff Pod 上一次运行时的日志输出，判断具体错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-starterror-describe","description":"对 g3 异常组（StartError）Pod node-debugger-node1-nx8gb 做 kubectl describe，获取具体错误","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"获取 StartError 状态的 Pod 的具体事件和状态详情","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-events-aiops","description":"查看 aiops-e2e 命名空间 ImagePullBackOff 事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by=.lastTimestamp","purpose":"采集 aiops-e2e 命名空间 ImagePull 失败事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-events-mcp","description":"查看 mcp 命名空间 ImagePullBackOff/ErrImagePull 事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by=.lastTimestamp","purpose":"采集 mcp 命名空间 ImagePull 失败事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-dns-resolution-check","description":"检查集群 DNS 是否正常解析 registry 域名（docker.io 和 registry.k8s.io）","level":"important","tool":"run_bash_command","command":"kubectl run dns-test-evidence --image=busybox:1.36.1 -n default --restart=Never -- nslookup docker.io 2>&1 || echo 'DNS check failed - likely cannot pull image'","purpose":"验证集群 DNS 是否能解析 Docker Hub 域名","collected":false,"source":"planned","outcome":"unknown"},{"id":"g2-gcr-registry-check","description":"验证 registry.k8s.io 域名解析","level":"optional","tool":"run_bash_command","command":"kubectl run registry-resolve-test --image=busybox:1.36.1 -n default --restart=Never -- nslookup registry.k8s.io 2>&1 || echo 'Registry DNS check failed'","purpose":"验证 registry.k8s.io 域名解析是否正常","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["g2-dns-resolution-check(检查集群 DNS 是否正常解析 registry 域名（docker.io 和 registry.k8s.io）): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/9 项, 完整度: 94%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g2-representa... | critical | ✅ | kubectl_describe | 对 g2 异常组（ImagePullBackOff/ErrImagePull）代表 Pod... | `kubectl describe pod connectivity-check-tmp -n default` |
   | g2-representa... | important | ✅ | kubectl_get_yaml | 获取 connectivity-check-tmp 的完整 YAML，检查 image、i... | `kubectl get pod connectivity-check-tmp -n default -o yaml` |
   | g2-events-def... | important | ✅ | kubectl_events | 查看 default 命名空间最近事件，筛选 ImagePullBackOff/ErrIm... | `kubectl get events -n default --field-selector reason=FailedToPullImage,reaso...` |
   | g1-crashloop-... | critical | ✅ | kubectl_describe | 对 g1 异常组（CrashLoopBackOff）代表 Pod rc-notready-... | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | g1-crashloop-... | important | ✅ | kubectl_logs | 获取 rc-notready-liveness 的上一次日志，查看退出原因 | `kubectl logs rc-notready-liveness -n aiops-e2e --previous` |
   | g3-starterror... | important | ✅ | kubectl_describe | 对 g3 异常组（StartError）Pod node-debugger-node1-n... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | g2-events-aiops | important | ✅ | kubectl_events | 查看 aiops-e2e 命名空间 ImagePullBackOff 事件 | `kubectl get events -n aiops-e2e --field-selector reason=FailedToPullImage,rea...` |
   | g2-events-mcp | important | ✅ | kubectl_events | 查看 mcp 命名空间 ImagePullBackOff/ErrImagePull 事件 | `kubectl get events -n mcp --field-selector reason=FailedToPullImage,reason=Er...` |
   | g2-dns-resolu... | important | ❌ | run_bash_command | 检查集群 DNS 是否正常解析 registry 域名（docker.io 和 regis... | `kubectl run dns-test-evidence --image=busybox:1.36.1 -n default --restart=Nev...` |
   | g2-gcr-regist... | optional | ❌ | run_bash_command | 验证 registry.k8s.io 域名解析 | `kubectl run registry-resolve-test --image=busybox:1.36.1 -n default --restart...` |

   ⚠️ 未采集原因:
   - g2-dns-resolution-check(检查集群 DNS 是否正常解析 registry 域名（docker.io 和 registry.k8s.io）): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (23.3s)
   📤 → 下游数据: root_cause=根因：集群节点(node1/node2)无法连接到Docker Hub镜像仓库。证据：connectivity-check-tmp的Events显示55次BackOff/126m，反复尝试连接registry-1.docker.io:443的4个不同IP(69.30.25.21,108.160.169.181,108.160.165.173,128.242.245.125)全部i/o timeout；dig-check-registry(node1)同样dial tcp 74.86.151.167:443 i/o timeout；dns-diag-tool-evidence(node2)的5次尝试全部i/o timeout(cross-node确认)。imagePullSecrets未配置(公共镜像无需)，镜像地址busybox:1.36.1/1.28/1.36均合法，排除认证和镜像不存在问题。约57个Pod受此影响。另有2个独立问题：aiops-e2e/rc-notready-liveness因liveness probe失败(SIGKILL Exit 137)CrashLoopBa
... 截断，原始 571 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点(node1/node2)无法通过HTTPS(443端口)连接到Docker Hub镜像仓库(registry-1.docker.io)，表现为TCP i/o timeout，导致所有依赖从docker.io拉取镜像的Pod无法启动", "propagation": "节点网络层到Docker Hub的公网出口不通（防火墙/NAT/出网路由问题）→ kubelet无法解析并连接registry-1.docker.io:443 → containerd拉取镜像超时 → 所有容器状态变为ErrImagePull/ImagePullBackOff → 集群内大量Pod(57个)处于Pending且无法运行", "direct_cause": "容器运行时(containerd)从docker.io拉取busybox镜像时TCP连接超时，registry-1.docker.io:443在集群节点上不可达", "manifestation": "3个命名空间(default/aiops-e2e/mcp)中约57个Pod处于ImagePullBackOff/ErrImagePull状态；另有rc-notready-liveness因liveness probe失败进入CrashLoopBackOff(独立问题)，node-debugger-node1-nx8gb因镜像内缺少curl命令进入StartError(独立问题)"}
   rca_analysis={"phenomenon": "集群中存在约57个异常Pod，分布在default、aiops-e2e、mcp命名空间，状态以ImagePullBackOff（47个）和ErrImagePull（9个）为主，另有1个CrashLoopBackOff（aiops-e2e/rc-notready-liveness）和1个StartError（mcp/node-debugger-node1-nx8gb）。大量Pod尝试从docker.io拉取busybox镜像失败，错误为\"dial tcp ...:443: i/o timeout\"。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_by_kind_in_cluster", "content": "57个异常Pod：47个ImagePullBackOff，9个ErrImagePull，1个CrashLoopBackOff，1个StartError", "reliability": "高"}, {"id": "e2", "source": "kubernetes_jq_query", "content": "Pod connectivity-check-tmp: ErrImagePull, message=\"failed to pull docker.io/library/busybox:1.36.1: dial tcp ... i/o timeout\"", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe (connectivity-check-tmp)", "content": "55次BackOff/126m，i/o timeout hitting registry IPs 69.30.25.21,108.160.169.181等，pull QPS exceeded", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_yaml (connectivity-check-tmp)", "content": "image=busybox:1.36.1, imagePullSecrets=absent, node=node2", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe (rc-notready-liveness)", "content": "CrashLoopBackOff, Exit Code 137, Liveness probe failed x10, 85次BackOff/24m", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe (node-debugger-node1-nx8gb)", "content": "StartError: exec \"curl\" not found in $PATH in busybox:1.36 image", "reliability": "高"}, {"id": "e7", "source": "kubectl_events (default)", "content": "connectivity-check-tmp: DeadlineExceeded dial tcp 69.30.25.21:443 i/o timeout", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe (dig-check-registry)", "content": "busybox:1.28拉取失败，dial tcp 74.86.151.167:443 i/o timeout，连接被重置", "reliability": "高"}, {"id": "e9", "source": "kubectl_describe (dns-diag-tool-evidence)", "content": "5次pull尝试全部i/o timeout，IPs: 108.160.173.207等", "reliability": "高"}, {"id": "e10", "source": "kubectl_previous_logs (rc-notready-liveness)", "content": "无输出日志", "reliability": "中"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "57 total abnormal: ImagePullBackOff=47, ErrImagePull=9, CrashLoopBackOff=1, StartError=1", "interpretation": "集群存在大规模镜像拉取失败，以ImagePullBackOff为主流异常模式"}, {"evidence_id": "e2", "raw_data": "connectivity-check-tmp: 'failed to resolve reference docker.io/library/busybox:1.36.1: dial tcp ... i/o timeout'", "interpretation": "kubelet无法连接到Docker Hub registry-1.docker.io:443，网络超时而非认证或镜像不存在"}, {"evidence_id": "e3", "raw_data": "55次BackOff/126m, i/o timeout to 69.30.25.21,108.160.169.181,108.160.165.173,128.242.245.125", "interpretation": "多IP均超时说明不是单点故障，而是集群到Docker Hub的整个网络路径不可达"}, {"evidence_id": "e4", "raw_data": "image=busybox:1.36.1, imagePullSecrets=absent", "interpretation": "镜像地址是公共镜像，无需认证；排除imagePullSecret缺失导致的问题"}, {"evidence_id": "e5", "raw_data": "CrashLoopBackOff, Exit Code 137, Liveness probe failed x10", "interpretation": "rc-notready-liveness被SIGKILL(Exit 137)杀死，因liveness probe持续失败，与应用自身逻辑相关，与镜像拉取无关"}, {"evidence_id": "e6", "raw_data": "StartError: exec 'curl' not found in $PATH in busybox:1.36", "interpretation": "node-debugger-node1-nx8gb的StartError是因容器镜像(busybox:1.36)不包含curl可执行文件，属于镜像/命令配置错误"}, {"evidence_id": "e7", "raw_data": "DeadlineExceeded dial tcp 69.30.25.21:443 i/o timeout", "interpretation": "kubelet向registry-1.docker.io发起HTTPS连接，TCP握手超时，确认网络不可达"}, {"evidence_id": "e8", "raw_data": "busybox:1.28拉取失败: dial tcp 74.86.151.167:443 i/o timeout, connection reset by peer", "interpretation": "不同tag(busybox:1.28)和不同目标IP均失败，排除镜像tag问题，指向Docker Hub整体不可达"}, {"evidence_id": "e9", "raw_data": "5次pull全失败, IPs: 108.160.173.207,173.231.12.107,128.121.243.228等均i/o timeout", "interpretation": "node2上同样无法连接Docker Hub，说明问题不局限于单个节点"}, {"evidence_id": "e10", "raw_data": "(no output)", "interpretation": "容器无日志输出，退出码137(SIGKILL)是OOMKill或liveness probe失败后kubelet杀死，无应用层日志"}], "causal_chain": {"root_cause": "集群节点(node1/node2)无法通过HTTPS(443端口)连接到Docker Hub镜像仓库(registry-1.docker.io)，表现为TCP i/o timeout，导致所有依赖从docker.io拉取镜像的Pod无法启动", "propagation": "节点网络层到Docker Hub的公网出口不通（防火墙/NAT/出网路由问题）→ kubelet无法解析并连接registry-1.docker.io:443 → containerd拉取镜像超时 → 所有容器状态变为ErrImagePull/ImagePullBackOff → 集群内大量Pod(57个)处于Pending且无法运行", "direct_cause": "容器运行时(containerd)从docker.io拉取busybox镜像时TCP连接超时，registry-1.docker.io:443在集群节点上不可达", "manifestation": "3个命名空间(default/aiops-e2e/mcp)中约57个Pod处于ImagePullBackOff/ErrImagePull状态；另有rc-notready-liveness因liveness probe失败进入CrashLoopBackOff(独立问题)，node-debugger-node1-nx8gb因镜像内缺少curl命令进入StartError(独立问题)"}, "root_cause": "根因：集群节点(node1/node2)无法连接到Docker Hub镜像仓库。证据：connectivity-check-tmp的Events显示55次BackOff/126m，反复尝试连接registry-1.docker.io:443的4个不同IP(69.30.25.21,108.160.169.181,108.160.165.173,128.242.245.125)全部i/o timeout；dig-check-registry(node1)同样dial tcp 74.86.151.167:443 i/o timeout；dns-diag-tool-evidence(node2)的5次尝试全部i/o timeout(cross-node确认)。imagePullSecrets未配置(公共镜像无需)，镜像地址busybox:1.36.1/1.28/1.36均合法，排除认证和镜像不存在问题。约57个Pod受此影响。另有2个独立问题：aiops-e2e/rc-notready-liveness因liveness probe失败(SIGKILL Exit 137)CrashLoopBa\n... 截断，原始 571 字符", "root_cause_summary": "根因：集群节点(node1/node2)无法连接到Docker Hub镜像仓库。证据：connectivity-check-tmp的Events显示55次BackOff/126m，反复尝试连接registry-1.docker.io:443的4个不同IP(69.30.25.21,108.160.169.181,108.160.165.173,128.242.245.125)全部i/o timeout；dig-check-registry(node1)同样dial tcp 74.86.151.167:443 i/o timeout；dns-diag-tool-evidence(node2)的5次尝试全部i/o timeout(cross-node确认)。imagePullSecrets未配置(公共镜像无需)，镜像地址busybox:1.36.1/1.28/1.36均合法，排除认证和镜像不存在问题。约57个Pod受此影响。另有2个独立问题：aiops-e2e/rc-notready-liveness因liveness probe失败(SIGKILL Exit 137)CrashLoopBa\n... 截断，原始 571 字符", "confidence": 0.95, "confidence_reason": "直接证据充分：多个Pod的Events/describe均显示同一错误模式(i/o timeout connecting to registry-1.docker.io:443)，跨越node1/node2两个节点、多个Pod、多个Docker Hub IP，排除单点故障；YAML确认镜像地址正确、无需认证；conflict证据中仅g3的StartError指向不同原因但已单独归类。因果链清晰，置信度高。", "primary_runbooks": [], "alternative_causes": [{"cause": "镜像地址或tag不存在", "probability": "low", "reason": "connectivity-check-tmp使用busybox:1.36.1，dig-check-registry使用busybox:1.28，均为Docker Hub上存在的公共镜像；错误信息是i/o timeout而非manifest unknown/not found"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "connectivity-check-tmp的YAML显示imagePullSecrets=absent，但镜像busybox:1.36.1是公共镜像无需认证；错误为网络超时而非unauthorized/denied"}, {"cause": "集群DNS无法解析registry域名", "probability": "medium", "reason": "部分Pod(dns-diag-tool-evidence)的参数是nslookup registry-1.docker.io，但证据未直接采集DNS解析结果；不过错误是dial tcp IP:i/o timeout而非DNS lookup failure，说明DNS解析已成功拿到IP但TCP连接失败"}], "limitations": "缺失g2-dns-resolution-check(检查集群DNS能否解析registry域名)证据，但根据错误信息(dial tcp IP而非lookup失败)推断DNS解析正常；未采集节点出网路由/NAT/防火墙配置，无法定位具体网络层阻断位置(如安全组、代理、出网带宽限制等)。", "llm_raw_analysis": "证据清点：共采集到17项证据，其中10项为本次采集(describe/YAML/events/logs)，7项为上游已验证工具结果。逐条分析：核心证据e2/e3/e7/e8/e9均指向同一问题——node1和node2均无法TCP连接到Docker Hub的多个IP(69.30.25.21,108.160.169.181,108.160.165.173,128.242.245.125,74.86.151.167,108.160.173.207等)，i/o timeout。e4排除镜像配置问题(imagePullSecrets缺失但公共镜像不需要)。e5/e6/e10独立说明另外两个非主异常组(g1 CrashLoopBackOff因liveness probe失败，g3 StartError因镜像内缺少curl)。主异常组g2(ImagePullBackOff/ErrImagePull)中~47+9=56个Pod均受Docker Hub不可达影响。因果链：集群出网不通→registry-1.docker.io:443不可达→containerd拉取超时→ImagePullBackOff\n... 截断，原始 514 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因：集群节点(node1/node2)无法连接到Docker Hub镜像仓库。证据：connectivity-check-tmp的Events显示55次BackOff/126m，反复尝试连接registry-1.docker.io:443的4个不同IP(69.30.25.21,108.160.16...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点(node1/node2)无法通过HTTPS(443端口)连接到Docker Hub镜像仓库(registry-1.docker.io)，表现为TCP i/o timeout，导致所有依赖从docker.io拉取镜像的Pod无法启动
     传导机制: 节点网络层到Docker Hub的公网出口不通（防火墙/NAT/出网路由问题）→ kubelet无法解析并连接registry-1.docker.io:443 → containerd拉取镜像超时 → 所有容器状态变为ErrImagePull/ImagePullBackOff → 集群内大量Pod(57个)处于Pending且无法运行
     最终表现: 3个命名空间(default/aiops-e2e/mcp)中约57个Pod处于ImagePullBackOff/ErrImagePull状态；另有rc-notready-liveness因liveness probe失败进入CrashLoopBackOff(独立问题)，node-debugger-node1-nx8gb因镜像内缺少curl命令进入StartError(独立问题)


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (34.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8894 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 43.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，我是资深 K8s 诊断报告专家。根据您的反馈和提供的所有分析数据，我已整合出一份详尽、完整的诊断报告。

---

## 📊 问题总结：您的集群当前存在三大核心问题

您集群的根因是 **网络连通性故障**，导致约 **56 个 Pod** 无法正常启动。同时，还存在一个活性和就绪检查失败的 Pod 以及一个由镜像问题导致的启动失败 Pod。

| 问题类型 | 影响范围 | 严重程度 | 根本原因 |
| :--- | :--- | :--- | :--- |
| **1. 大规模镜像拉取失败** | **47个** Pod 处于 `ImagePullBackOff`，**9个** 处于 `ErrImagePull`。涉及 `default`, `aiops-e2e`, `mcp` 命名空间。 | **🔴 严重** | 集群所有节点(`node1`, `node2`)无法访问外网镜像仓库（如 `docker.io`），拉取镜像时TCP连接超时。 |
| **2. 业务Pod活性检查失败** | Pod `aiops-e2e/rc-notready-liveness` 持续 `CrashLoopBackOff`。 | **🟡 中等** | Pod 内的 `liveness` 探测连续失败，导致容器被 Kubelet 强制杀死并重启。 |
| **3. 诊断工具镜像问题** | Pod `mcp/node-debugger-node1-nx8gb` 状态为 `StartError`。 | **🟢 低** | 容器镜像中缺少 `curl` 命令，导致启动入口命令执行失败。 |

**Pod 异常详情 (按状态分组):**

| 异常状态 | Pod 数量 | 涉及命名空间 |
| :--- | :--- | :--- |
| `ImagePullBackOff` | 47 | `default`, `aiops-e2e`, `mcp` |
| `ErrImagePull` | 9 | `default` |
| `CrashLoopBackOff` | 1 | `aiops-e2e` |
| **总计异常 Pod** | **57** | |

---

## 📊 诊断概览

| 项目 | 内容 |
| :--- | :--- |
| **核心Pod异常状态** | `ImagePullBackOff`, `ErrImagePull`, `CrashLoopBackOff` |
| **兼容归因层** | `L3` - 镜像仓库/网络问题 |
| **问题分类** | 集群层面：镜像仓库网络不可达；特定应用：活性探测失败 |
| **置信度** | **高 (95%)** |
| **证据完整度** | 8/9 (89%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
| :--- | :--- |
| **集群节点** | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| **异常核心用户** | `default`, `aiops-e2e`, `mcp` 命名空间 |
| **核心异常组 (G2)** | `ImagePullBackOff` & `ErrImagePull` |
| **核心异常组 (G1)** | `CrashLoopBackOff` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 (关键提取) | 分析结论 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Pod 状态** (G2代表) | `kubectl describe pod connectivity-check-tmp -n default` | `Reason: ImagePullBackOff` <br> `Events: Failed to pull image "busybox:1.36.1"` <br> `Events: dial tcp 69.30.25.21:443: i/o timeout` (同时出现4个不同IP的超时) | **根因证据**：Pod 无法连接到镜像仓库 `docker.io` 的网络层（TCP 443端口）。 |
| 2 | **Pod 状态** (G2代表) | `kubectl get pod dns-diag-tool-evidence -n default -o yaml` | `containerStatuses: reason: ImagePullBackOff`<br> `Events: 5次 pull 尝试均失败，错误信息均为 i/o timeout` | **交叉确认**：Node2上的另一个Pod也无法拉取镜像，排除了Node单点问题。 |
| 3 | **Pod 状态** (G2代表) | `kubectl describe pod dig-check-registry -n default` | `Events: dial tcp 74.86.151.167:443: i/o timeout` | **交叉确认**：Node1上的Pod也出现同样问题，锁定了全集群范围的网络故障。 |
| 4 | **集群事件** | `kubectl get events -A` | `Warning Failed Pod/test-dns-1779360358 ...: DeadlineExceeded desc = failed to pull and unpack image` | 集群层面有大量镜像拉取超时事件，确认了影响范围广泛。 |
| 5 | **Pod YAML** (G2代表) | `kubectl get pod connectivity-check-tmp -o yaml` | `finalizers: <none>`<br> `imagePullSecrets: []` | 排除了 `finalizer` 问题和 `凭证` 问题，镜像为公共镜像 `busybox`。 |
| 6 | **Pod 状态** (G1代表) | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | `Last State: Terminated (Exit Code: 137)`<br> `Events: Failed liveness probe, will be restarted` | **直接原因**：容器因 `liveness` 探测失败被系统（OOM或SIGKILL）强制杀死。 |
| 7 | **Pod 日志** (G1代表) | `kubectl logs pod rc-notready-liveness -n aiops-e2e --previous` | (无输出) | 容器进程在被杀前未产生有效输出（无日志），可能表明进程启动后直接卡死或无响应。 |
| 8 | **Pod 状态** (G3代表) | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` | `Status: Failed` <br> `Reason: StartError` <br> `Message: failed to create shim task: OCI runtime create failed: container_linux.go:380: starting container process caused: exec: "curl": executable file not found in $PATH` | **直接原因**：容器镜像内缺少 `curl` 命令，导致`入口`命令执行失败。 |

### 证据关联分析

- **证据 #1 + #2 + #3 相互印证**：分布在 `node1` 和 `node2` 上的不同 Pod，在尝试连接 `registry-1.docker.io` 的不同 IP 地址时，均发生 `i/o timeout` 错误。这排除了目标IP故障的可能，将问题精确指向**集群节点到外部网络（Docker Hub）的出向网络不可达**。
- **证据 #4 + #5 加强推论**：集群事件中 `DeadlineExceeded` 详细错误，结合 YAML 中 `imagePullSecrets` 为空，确认了问题是*网络层面*的，而非*认证或配置层面*的问题。
- **证据 #6 + #7 关联分析**：Exit Code 137（SIGKILL）和 `liveness probe failed` 事件，表明应用本身可能存在内存泄漏（OOM）或死锁，导致长期不响应活性探针，最终被 Kubelet 强制终止。日志无输出说明问题出现在应用启动早期或进程状态突然卡死。

### 缺失证据

| 证据 | 级别 | 影响 |
| :--- | :--- | :--- |
| 集群内部 DNS 解析能力验证 `dig docker.io` | **重要** | 虽然错误为 `dial tcp` 超时，非 `lookup failure`，但这能100%确认 DNS 功能正常，进一步锁定网络问题在路由/防火墙层。 |
| `rc-notready-liveness` 容器崩溃前内存/CPU使用情况 | **重要** | 无法确认 Exit Code 137 是否由 OOM 引起，还是由 `liveness probe` 超时导致的强制 SIGKILL。 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                   │
│ 集群节点 (node1, node2) 到外部网络 (Docker Hub registry-1.docker.io)     │
│ 的 TCP 443 端口出向网络不通。                                           │
│ 来源：证据 #1, #2, #3 (i/o timeout 跨节点复现)                          │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                  │
│ 节点网络 → 无法建立TCP连接到 registry-1.docker.io:443                   │
│ → Kubelet/containerd 拉取镜像超时 (DeadlineExceeded)                    │
│ → 容器无法创建，状态变为 ErrImagePull                                   │
│ → kubelet 重试失败，状态最终变为 ImagePullBackOff                       │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                 │
│ 1. (大规模问题) 容器运行时无法从 docker.io 拉取镜像，导致 56 个 Pod 无法启动。│
│ 2. (业务问题) 应用 rc-notready-liveness 的 liveness 探测连续失败，被强制杀死。│
│ 3. (工具问题) node-debugger 镜像缺少 curl 命令，导致启动失败。              │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                            │
│ 1. 57 个 Pod 处于 ImagePullBackOff / ErrImagePull / CrashLoopBackOff 状态。 │
│ 2. 业务服务不可用。                                                     │
│ 3. 诊断和调试工具无法运行。                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

1.  **【核心问题】集群网络故障**：根据证据 #1, #2, #3 和 #4，问题的根本原因是**集群所有节点无法连接到外部镜像仓库 `docker.io`**。这是集群级别的重大故障，影响范围最广（56个Pod）。
2.  **【独立问题】业务Pod活性检查失败**：根据证据 #6, #7，`rc-notready-liveness` 的 `CrashLoopBackOff` 是由其内部的 `liveness` 探针失败导致。虽然它和网络问题同时发生，但根本上是应用自身健康状况不佳。它也可能由网络问题间接引发。

**置信度**：**高 (95%)**
- ✅ 多个节点、多个 Pod 的 `describe` 命令输出高度一致，均指向 TCP `i/o timeout`。
- ✅ 已通过 `kubectl get yaml` 排除了 `finalizer`, `imagePullSecrets` 等常见配置错误。
- ⚠️ 缺少 `dig` 命令的输出，无法完全排除 DNS 故障的可能性，但从 `dial tcp` 的错误模式看，DNS 解析正常的可能性更高。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**【紧急】1. 解决集群出站网络问题**

这是修复大多数 Pod (56个) 的核心操作。需要联系您的集群管理员或云服务商。

**注意**：以下步骤并非 `kubectl` 命令，而是需要在 **宿主机 node1 和 node2** 上执行的操作。

1.  **验证网络连通性**：
    ```bash
    # 在 node1 和 node2 上执行
    # 检查是否能连接到 Docker Hub 的 443 端口
    nc -zv registry-1.docker.io 443
    # 或者
    curl -I https://registry-1.docker.io/v2/
    ```

2.  **检查防火墙/NAT规则**：
    检查节点的 iptables、ufw 或云服务商安全组的出站规则，确保允许 `443` 端口访问 `docker.io` 及相关镜像仓库的 IP 段。

3.  **可选：配置 HTTP 代理**：
    如果集群必须通过代理访问外网，可以配置 containerd 使用代理。
    ```bash
    # 编辑 containerd 配置文件 (通常在 /etc/systemd/system/containerd.service.d/http-proxy.conf)
    [Service]
    Environment="HTTP_PROXY=http://your-proxy-ip:port"
    Environment="HTTPS_PROXY=http://your-proxy-ip:port"
    Environment="NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    
    # 重载 systemd 并重启 containerd
    sudo systemctl daemon-reload
    sudo systemctl restart containerd
    ```

**【明确】2. 修复 `rc-notready-liveness` 应用问题**
```bash
# 1. 查看应用的日志 (如果可能)
kubectl logs rc-notready-liveness -n aiops-e2e --previous | tail -50

# 2. 调整 liveness probe 配置 (找到对应的 Deployment/StatefulSet 并修改)
kubectl edit deployment <your-deployment-name> -n aiops-e2e
```
*建议*：根据应用的实际情况，可能需要：
-   增加 `initialDelaySeconds` 和 `periodSeconds`。
-   降低探测路径的响应时间。
-   检查应用的性能瓶颈或内存泄漏问题。

**【明确】3. 修复诊断镜像 `StartError` 问题**
```bash
# 这个 Pod 是诊断工具，其使用的镜像有问题。如果您不需要它，可以删除。
kubectl delete pod node-debugger-node1-nx8gb -n mcp

# 或者，使用包含 curl 的正确镜像，例如。
# 这需要确认 mcp 控制器使用的镜像名称，然后进行修改。
```

### 后续优化

1.  **监控告警**：配置对 `ImagePullBackOff` 和 `CrashLoopBackOff` 等关键 Pod 状态的告警。
2.  **网络架构**：定期检查集群的网络连通性，可部署一个始终运行的、专门用于网络诊断的 DaemonSet 进行健康检查。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
| :--- | :--- | :--- |
| 1. 检查集群出站网络 | 在 node1/2 上运行 `nc -zv registry-1.docker.io 443` | `Connected to registry-1.docker.io` |
| 2. 确认 Pod 状态恢复 | `kubectl get pods -A \| grep -E "(ImagePullBackOff\|ErrImagePull\|CrashLoopBackOff\|StartError)"` | 输出为空 |
| 3. 确认业务 Pod 运行 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | STATUS: `Running`, RESTARTS 不再增加 |
| 4. 检查应用日志 | `kubectl logs rc-notready-liveness -n aiops-e2e \| tail -20` | 有正常的业务日志输出 |

---

## ⚠️ 注意事项

-   **根本问题**：**首要任务是解决集群网络连通性**。否则，所有依赖外部镜像的服务都将无法正常工作。
-   **CrashLoopBackOff**：`rc-notready-liveness` 的问题很可能是应用自身的健康问题（如内存泄漏、死锁），即使网络修复后也可能需要额外排查。
-   **StartError**：`node-debugger` Pod 是一个诊断工具，其镜像不适用于该启动命令，是独立的配置错误。网络修复后它依然会报错，需按前述建议处理。

---

## 📊 性能统计

├─ 总耗时: 2.7m
├─ 问题定位: 35.7s (22%) ✅
├─ 证据链采集: 70.3s (43%) ✅
├─ 根因分析: 23.3s (14%) ✅
├─ 汇总总结: 34.4s (21%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 35 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 35 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
