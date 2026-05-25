======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 41d230e7ff104066]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先全局扫描所有 Pod 的状态，来识别当前集群中的异常情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods -A: 109 pods total. Running=59, ImagePullBackOff=41, ErrImagePull=2, CreateContainerConfigError=1, Completed=3. 44 abnormal pods across aiops-e2e, default, mcp namespaces.
key_facts: 
   💭 [问题定位] 很好，数据很清晰。我来再确认一下详细信息，特别是有 41 个 ImagePullBackOff 和 1 个 CreateContainerConfigError。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=356 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=4827 lines=271
Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "rc-config-configmap-key-missing",
  "phase": "Pending",
  "reason": "Pending"
   💭 [问题定位] 让我看一下更详细的 Pod 状态（STATUS 列），而不仅仅是 phase。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=7679 lines=271
Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "rc-config-configmap-key-missing",
  "status": "CreateContainerConfigError",
 
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=7679 lines=271
Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "rc-config-configmap-key-missing",
  "status": "CreateContainerConfigError",
 
   💭 [问题定位] 让我获取所有异常 Pod 的完整列表。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=4235 lines=226
Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "rc-config-configmap-key-missing",
  "status": "CreateContainerConfigError"
}

   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=2075 lines=46
Executing jq query for pods...
aiops-e2e/rc-config-configmap-key-missing: CreateContainerConfigError
aiops-e2e/test-dns-1779360358: ImagePullBackOff
d
   💭 [问题定位] 现在我来获取匹配的 runbook，先看主要的异常类型。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (38.4s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '镜像仓库不可达或镜像不存在', 'probability': 'high', 'reason': '41个ImagePullBackOff和2个ErrImagePull分布在default、aiops-e2e、mcp三个namespace，涉及不同镜像(busybox:1.36.1, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, node-debugger镜像等)，表明不是单个镜像问题，而是镜像仓库访问问题'}, {'scenario': '镜像拉取凭证/权限配置错误', 'probability': 'medium', 'reason': '如果私有仓库需要认证但缺少imagePullSecrets或凭证过期，会导致大量镜像拉取失败'}, {'scenario': 'ConfigMap配置错误（L4）', 'probability': 'low', 'reason': 'rc-config-configmap-key-missing处于CreateContainerConfigError，原因是找不到ConfigMap key APP_BOOT_MODE，属于独立的应用配置问题'}]
   entities=[{"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "pod", "name": "test-dns-1779360358", "namespace": "aiops-e2e"}, {"type": "pod", "name": "dig-tool", "namespace": "default"}]
   reasoning=集群中存在大量当前仍异常的Pod：41个ImagePullBackOff、1个CreateContainerConfigError、2个ErrImagePull（mcp/node-debugger-node2-2cg95等），总计44个异常Pod。所有Running状态的Pod（59个）以及kube-system、admin等核心组件正常。根因归类：ImagePullBackOff和ErrImagePull占绝大多数（43/44），属于镜像拉取失败问题，对应L3（image_registry/network_cni_runtime）；另有1个CreateContainerConfigError（ConfigMap key missing）属于L4（app_config）。由于ImagePullBackOff是主要异常类型且影响面最大，derived_layer设为L3。Pod状态关键字为ImagePullBackOff，Pod异常类型为ImagePullFailed。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "image_registry_network", "confidence": 0.95, "reasoning": "集群中存在大量当前仍异常的Pod：41个ImagePullBackOff、1个CreateContainerConfigError、2个ErrImagePull（mcp/node-debugger-node2-2cg95等），总计44个异常Pod。所有Running状态的Pod（59个）以及kube-system、admin等核心组件正常。根因归类：ImagePullBackOff和ErrImagePull占绝大多数（43/44），属于镜像拉取失败问题，对应L3（image_registry/network_cni_runtime）；另有1个CreateContainerConfigError（ConfigMap key missing）属于L4（app_config）。由于ImagePullBackOff是主要异常类型且影响面最大，derived_layer设为L3。Pod状态关键字为ImagePullBackOff，Pod异常类型为ImagePullFailed。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-check-node2", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "pod", "name": "test-dns-1779360358", "namespace": "aiops-e2e"}, {"type": "pod", "name": "dig-tool", "namespace": "default"}], "possible_scenarios": [{"scenario": "镜像仓库不可达或镜像不存在", "probability": "high", "reason": "41个ImagePullBackOff和2个ErrImagePull分布在default、aiops-e2e、mcp三个namespace，涉及不同镜像(busybox:1.36.1, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, node-debugger镜像等)，表明不是单个镜像问题，而是镜像仓库访问问题"}, {"scenario": "镜像拉取凭证/权限配置错误", "probability": "medium", "reason": "如果私有仓库需要认证但缺少imagePullSecrets或凭证过期，会导致大量镜像拉取失败"}, {"scenario": "ConfigMap配置错误（L4）", "probability": "low", "reason": "rc-config-configmap-key-missing处于CreateContainerConfigError，原因是找不到ConfigMap key APP_BOOT_MODE，属于独立的应用配置问题"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 41, "ErrImagePull": 2}, "total_abnormal": 43, "selected_rows": ["aiops-e2e         rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0              27s     172.16.166.142   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff             0              8h      172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              3h31m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff             0              151m    172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              7h2m    172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff             0              8h      172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff             0              5h44m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-tmp                                        0/1     ImagePullBackOff             0              158m    172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              6h50m   172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff             0              7h18m   172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff             0              4h14m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ImagePullBackOff             0              24m     172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff             0              5h12m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff             0              6h59m   172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              8h      172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff             0              7h21m   172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               curl-check-tmp                                      0/1     ImagePullBackOff             0              3h40m   172.16.104.58    node2    <none>           <none>            run=curl-check-tmp", "mcp               curls                                               0/1     ImagePullBackOff             0              120m    172.16.104.2     node2    <none>           <none>            run=curls", "mcp               dns-check-tmp                                       0/1     ImagePullBackOff             0              3h40m   172.16.104.13    node2    <none>           <none>            run=dns-check-tmp", "mcp               net-check-1779365549                                0/1     ImagePullBackOff             0              6h47m   172.16.166.179   node1    <none>           <none>            run=net-check-1779365549"], "raw_ref": "/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我先获取 ImagePullFailed 的 runbook 参考，然后按既有 evidence_plan 执行关键工具调用。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [证据链采集] 好，现在按照既有 evidence_plan 执行关键工具调用。先并行执行多个核心 describe，覆盖三个 namespace 的代表 Pod：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-check
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   8m33s (x50 over 5h11m)    kubelet  (combined from similar events): Failed 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default) is Pending on node node1/10.2.0.49. Container dig-tool image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 cannot be pulled — multiple DeadlineExceeded errors d
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
48m (x4 over 3h16m)       Warning   Failed    Pod/dig-tool   Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0": rpc error: code = DeadlineExceeded de
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod test-dns-1779360358 in namespace aiops-e2e on node node1/10.2.0.49 is Pending, container waiting with Reason ImagePullBackOff. Image busybox:1.36.1 fails to pull from docker.io due to network erro
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
53m                     Warning   Failed    Pod/test-dns-1779360358   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and unpa
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node2-2cg95
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Normal   BackOff  9m44s (x1162 over 6h14m)  kubelet  Back-off pulling image "busybox:
   💭 [证据链采集] 好，三个 namespace 的 Pod describe 和 events 已经显示核心规律。现在继续执行 plan 中剩余的工具，验证 CreateContainerConfigError 的组 g1，以及集群级别事件：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          12s (x9 over 88s)  kubelet            Error: cou
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-app-config
namespace: aiops-e2e
   💭 [证据链采集] 让我确认一下 ConfigMap 的实际内容：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "apiVersion: v1\ndata:\n  EXISTING_KEY: present\nkind: ConfigMap\nmetadata:\n  annotations:\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":
   💭 [证据链采集] 现在我已经完成了所有计划中的关键工具调用。以下是证据采集结论：

---

## ✅ 证据采集完成

### 已采集证据

**1. 主异常组 g2 — ImagePullBackOff / ErrImagePull（43 个异常 Pod）**

| 维度 | 证据 |
|------|------|
| **aiops-e2e/test-dns-1779360358** | 镜像 `busybox:1.36.1`，Events 显示 `i/o timeout` + `connection reset by peer` 到 `registry-1.docker.io` 的多个 IP（162.125.17.131:443, 3.233.166.60:443, 3.91.167.191:443），x1000 次 BackOff 持续 8h |
| **default/dig-tool** | 镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，Events 显示 `i/o timeout` 到 `asia-east1-docker.pkg.dev:443` 和 `us-west2-docker.pkg.dev:443`，不同镜像也不同仓库 |
| **mcp/node-debugger-node2-2cg95** | 镜像 `busybox:1.36.1` 在 node2，Events 显示 `dial tcp 108.160.161.83:443: i/o timeout` 到 `registry-1.docker.io` |
| **default/dns-test-check** | 镜像 `busybox:1.36.1` 在 node2，Events 显示 `dial tcp 74.86.118.24:443: i/o timeout` 到 `registry-1.docker.io` |
| **跨 namespace 一致性** | aiops-e2e、default、mcp 三个 namespace 的 Pod 无论跑在 node1 还是 node2，均出现 **i/o timeout** 无法连接到外部镜像仓库（docker.io 和 registry.k8s.io）|
| **不同镜像均失败** | `busybox:1.36.1`（docker.io）、`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`（k8s artifacts registry）均无法拉取 |

**2. 次异常组 g1 — CreateContainerConfigError（1 个 Pod）**

| 维度 | 证据 |
|------|------|
| **aiops-e2e/rc-config-configmap-key-missing** | Pod Events 明确显示：`couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config` |
| **ConfigMap rc-app-config 内容** | 该 ConfigMap **只包含 key `EXISTING_KEY`**，**不存在 `APP_BOOT_MODE`** 这个 key。Pod env 引用了不存在的 key，属于应用配置错误 |

### 关键结论

1. **根因：集群节点（node1 和 node2）无法访问外部镜像仓库** — 所有节点访问 `registry-1.docker.io`、`asia-east1-docker.pkg.dev`、`us-west2-docker.pkg.dev` 均出现 `i/o timeout`（TCP 连接超时）。这不是单个镜像问题，而是**集群到公网镜像仓库的网络连通性故障**（可能是出口防火墙/代理/NAT 问题）。

2. **独立问题：ConfigMap key 缺失** — `rc-config-configmap-key-missing` 是独立的 L4 配置错误，与镜像拉取无关，需在 ConfigMap `rc-app-config` 中添加 `APP_BOOT_MODE` key。
   ✅ [证据链采集] 完成 (34.2s)
   📤 → 下游数据: evidence_items=14/14
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"检查主异常组g2的代表Pod - aiops-e2e/test-dns-1779360358 (ImagePullBackOff) 的Pod Events和当前状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e test-dns-1779360358","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"查看ImagePullBackOff的详细Events和错误原因","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"检查主异常组g2中default/dig-tool (ImagePullBackOff, node1) 的Pod Events和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dig-tool","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"交叉验证default命名空间的ImagePullBackOff原因是否与aiops-e2e一致","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"检查主异常组g2中mcp/node-debugger-node2-2cg95 (ErrImagePull, node2) 的Pod Events和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n mcp node-debugger-node2-2cg95","tool_args":{"kind":"pod","name":"node-debugger-node2-2cg95","namespace":"mcp"},"purpose":"验证mcp命名空间不同节点上ErrImagePull与ImagePullBackOff的错误是否一致","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"检查主异常组g2中default/dns-test-check (ImagePullBackOff, node2) 的Pod Events，覆盖node2节点","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n default dns-test-check","tool_args":{"kind":"pod","name":"dns-test-check","namespace":"default"},"purpose":"验证node2上的ImagePullBackOff是否有不同的错误信息","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"获取所有命名空间涉及ImagePull的Events，搜索Failed/Error/BackOff","level":"critical","tool":"kubectl_events","command":"kubectl events -A --types=Warning | grep -iE 'image|pull|backoff|error|fail'","tool_args":{},"purpose":"从集群事件层面统一查看所有镜像拉取相关告警","evidence_type":"cluster_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6","description":"检查非主异常组g1 - aiops-e2e/rc-config-configmap-key-missing (CreateContainerConfigError) 的Pod Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-config-configmap-key-missing","tool_args":{"kind":"pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e"},"purpose":"验证CreateContainerConfigError的具体缺失key和引用的ConfigMap","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7","description":"验证ConfigMap aiops-e2e/rc-app-config是否存在及内容","level":"important","tool":"kubectl_get_yaml","command":"kubectl get configmap -n aiops-e2e rc-app-config -o yaml","tool_args":{"kind":"configmap","name":"rc-app-config","namespace":"aiops-e2e"},"purpose":"验证CreateContainerConfigError引用的ConfigMap是否存在及包含APP_BOOT_MODE key","evidence_type":"configmap_content","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: imagePullSecrets 必须在同 namespace，私有仓库 secret 类型应为 kubernetes.io/dockerconfigjson 或 kubernetes.io/dockercfg。\n\n### Step 4: 按事件错误文本归类\n- `manifest unknown` / `not found`: 镜像仓库中不存在该镜像或 tag。\n- `invalid reference format`: image 字符串格式错误。\n- `unauthorized` / `no basic auth credentials`: imagePullSecret 缺失、未引用、类型错误或凭据错误。\n- `pull access denied` / `insufficient_scope`: 仓库权限不足或镜像路径错误。\n- `x509: certificate signed by unknown authority`: 节点容器运行时不信任仓库 TLS 证书。\n- `i/o timeout` / `connection refused`: 节点到镜像仓库访问失败，需检查仓库地址、端口、防火墙、DNS。\n- `context canceled`: 拉取过程中连接被取消，常见于网络中断、镜像仓库响应慢、kubelet/运行时超时或并发拉取拥塞。\n- `Too Many Requests` / rate limit: 镜像仓库限流，需认证、镜像缓存或私有代理仓库。\n- 长时间只有 `Pulling image` 无后续失败事件: 关注镜像体积、节点带宽、运行时并发拉取限制、kubelet `registryPullQPS` / `registryBurst` 配置。\n\n### Step 5: 主动验证镜像仓库连通性\n可用只读命令验证节点或集群内到镜像仓库的 HTTPS 连通性，例如：\n```bash\ncurl -v --connect-timeout 10 https://registry-1.docker.io/v2/\n```\n判读规则：\n- 返回 `200/401/403`：说明 HTTPS 网络可达；`401/403` 通常是认证/权限语义，不是网络不可达。\n- `curl: (28) Operation timed out`、`Connection timed out`、`i/o timeout`、`命令执行超时`：这是诊断事实，表示镜像仓库网络不可达或链路被阻断，不应当仅视为“工具执行失败”。\n- `Could not resolve host`：DNS 解析失败。\n- `connection refused/reset`：目标端口不可达、被中间设备拒绝或连接被重置。\n- `x509`：TLS 证书信任问题。\n\n\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| Events 含 connection refused/timeout | 镜像仓库网络不可达 | 高 |\n| Events 含 context canceled | 镜像拉取连接被取消，优先检查网络、仓库响应、运行时超时和并发拉取 | 中 |\n| 主动 curl/wget registry 超时或命令执行超时 | 镜像仓库网络不可达 | 高 |\n| Events 含 manifest unknown/not found | 镜像或 tag 不存在 | 高 |\n| Events 含 unauthorized/no basic auth | 认证失败（缺少或错误的 imagePullSecret） | 高 |\n| Events 含 pull access denied/insufficient_scope | 仓库权限不足或镜像路径错误 | 高 |\n| Events 含 invalid reference format | 镜像名称格式错误 | 高 |\n| Events 含 x509 | 节点容器运行时信任链/TLS 证书问题 | 高 |\n| DNS 解析失败 | DNS 问题导致仓库不可达 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-test-check\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   8m33s (x50 over 5h11m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 74.86.118.24:443: i/o timeout\n  Normal   BackOff  5m17s (x1052 over 5h44m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   44m (x50 over 5h44m)      kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 9e22290236797aa5f25c53b51c38e8bf6856c341e86020f57967c39f91341d92\n                  cni.projectcalico.org/podIP: 172.16.104.53/32\n                  cni.projectcalico.org/podIPs: 172.16.104.53/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-test-check:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      nslookup\n      registry.invalid\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-9z4n9:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   44m (x50 over 5h44m)      kubelet  Error: ErrImagePull\n  Warning  Failed   8m33s (x50 over 5h11m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 74.86.118.24:443: i/o timeout\n  Normal   BackOff  5m17s (x1052 over 5h44m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-tool (namespace: default) is Pending on node node1/10.2.0.49. Container dig-tool image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 cannot be pulled — multiple DeadlineExceeded errors dialing asia-east1-docker.pkg.dev and us-west2-docker.pkg.dev (i/o timeout). Container State: Waiting, Reason: ImagePullBackOff. Events show repeated Failed (ErrImagePull), Failed to pull image (x4, x6, x5), and BackOff (x293 over 3h25m). Pod IP 172.16.166.157. Ready=False, ContainersReady=False. Restart Count=0. QoS BestEffort.\nkey_facts: [\"name: dig-tool\", \"namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: dig-tool\", \"image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"container State: Waiting, Reason: ImagePullBackOff\", \"container Ready: False\", \"Restart Count: 0\", \"QoS Class: BestEffort\", \"Event Warning Failed 48m (x27 over 3h25m): Error: ErrImagePull\", \"Event Warning Failed 48m (x4 over 3h16m): Failed to pull image — dial tcp asia-east1-docker.pkg.dev:443 i/o timeout\", \"Event Warning Failed 35m (x6 over 3h25m): Failed to pull image — dial tcp us-west2-docker.pkg.dev:443 i/o timeout\", \"Event Warning Failed 18m (x5 over 177m): Failed to pull image — dial tcp us-west2-docker.pkg.dev:443 i/o timeout\", \"Event Normal BackOff 5m36s (x293 over 3h25m): Back-off pulling image\"]\nmissing: [\"Container ID and Image ID are empty — image never pulled\", \"No successful pull or running state observed\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n48m (x4 over 3h16m)       Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://asia-east1-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 142.250.157.82:443: i/o timeout\n35m (x6 over 3h25m)       Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 108.177.125.82:443: i/o timeout\n18m (x5 over 177m)        Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 142.250.157.82:443: i/o timeout\n5m37s (x293 over 3h25m)   Normal    BackOff   Pod/dig-tool   Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\n48m (x27 over 3h25m)      Warning   Failed    Pod/dig-tool   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"Pod test-dns-1779360358 in namespace aiops-e2e on node node1/10.2.0.49 is Pending, container waiting with Reason ImagePullBackOff. Image busybox:1.36.1 fails to pull from docker.io due to network errors (i/o timeout, connection reset by peer) across multiple registry IPs. Back-off pulling image x1000 over 8h.\nkey_facts: [\"name: test-dns-1779360358\", \"namespace: aiops-e2e\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: test-dns-1779360358, image: busybox:1.36.1\", \"container State: Waiting, Reason: ImagePullBackOff\", \"container Ready: False, Restart Count: 0\", \"QoS Class: BestEffort\", \"Events: Warning Failed x107 over 7h38m - combined: Failed to pull image 'busybox:1.36.1' - failed to resolve reference 'docker.io/library/busybox:1.36.1' - network errors (i/o timeout, connection reset by peer) to registry-1.docker.io IPs 162.125.17.131:443, 3.233.166.60:443, 3.91.167.191:443\", \"Events: Normal BackOff 4m40s (x1000 over 8h) - Back-off pulling image 'busybox:1.36.1'\", \"PodScheduled: True, Initialized: True, ContainersReady: False, Ready: False\"]\nconflicts: [\"current_summary says 'Normal BackOff 4m40s (x1000 over 8h)' — raw_preview confirms this, no conflict.\", \"current_summary lists only 3 Warning events; raw_preview also has a 'Normal Pulling 39m (x82 over 8h)' event not in current_summary — minor omission, no contradiction.\"]\nmissing: [\"raw_preview includes 'Normal Pulling 39m (x82 over 8h)' event not captured in current_summary\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n53m                     Warning   Failed    Pod/test-dns-1779360358   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 162.125.17.131:443: i/o timeout\n42m                     Warning   Failed    Pod/test-dns-1779360358   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:38564->3.233.166.60:443: read: connection reset by peer\n18m (x107 over 7h38m)   Warning   Failed    Pod/test-dns-1779360358   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:55694->3.91.167.191:443: read: connection reset by peer\n4m40s (x1000 over 8h)   Normal    BackOff   Pod/test-dns-1779360358   Back-off pulling image \"busybox:1.36.1\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/006-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/006-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/006-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node2-2cg95\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  9m44s (x1162 over 6h14m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   64s (x84 over 5h43m)      kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.161.83:443: i/o timeout\n      Reason:       ErrImagePull\n  Warning  Failed   58m (x37 over 6h14m)      kubelet  Error: ErrImagePull\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Command:\n      chroot\n      /host\n      /bin/sh\n      -c\n      nslookup registry-1.docker.io 2>&1 || echo \"DNS check failed\"\n    State:          Waiting\n      Reason:       ErrImagePull\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-chx7q:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   58m (x37 over 6h14m)      kubelet  Error: ErrImagePull\n  Normal   BackOff  9m44s (x1162 over 6h14m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   64s (x84 over 5h43m)      kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.161.83:443: i/o timeout\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          12s (x9 over 88s)  kubelet            Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config\n                  cni.projectcalico.org/containerID: c3f68f3c291432ef6dcdea4afa9ea904811c43850537021eafd2f80e4b705cd1\n                  cni.projectcalico.org/podIP: 172.16.166.142/32\n                  cni.projectcalico.org/podIPs: 172.16.166.142/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-vr7b6:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed          12s (x9 over 88s)  kubelet            Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/008-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/008-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/008-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-app-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/009-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/009-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/009-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"apiVersion: v1\\ndata:\\n  EXISTING_KEY: present\\nkind: ConfigMap\\nmetadata:\\n  annotations:\\n    kubectl.kubernetes.io/last-applied-configuration: |\\n      {\\\"apiVersion\\\":\\\"v1\\\",\\\"data\\\":{\\\"EXISTING_KEY\\\":\\\"present\\\"},\\\"kind\\\":\\\"ConfigMap\\\",\\\"metadata\\\":{\\\"annotations\\\":{},\\\"labels\\\":{\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-app-config\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"}}\\n  creationTimestamp: \\\"2026-05-21T18:59:23Z\\\"\\n  labels:\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-app-config\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52787325\\\"\\n  uid: 84b902b0-288b-4ffb-ae96-6c3f62a72d12\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/010-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/010-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/41d230e7ff104066/tools/010-evidence-run_bash_command.summary.txt"}],"llm_analysis":"现在我已经完成了所有计划中的关键工具调用。以下是证据采集结论：\n\n---\n\n## ✅ 证据采集完成\n\n### 已采集证据\n\n**1. 主异常组 g2 — ImagePullBackOff / ErrImagePull（43 个异常 Pod）**\n\n| 维度 | 证据 |\n|------|------|\n| **aiops-e2e/test-dns-1779360358** | 镜像 `busybox:1.36.1`，Events 显示 `i/o timeout` + `connection reset by peer` 到 `registry-1.docker.io` 的多个 IP（162.125.17.131:443, 3.233.166.60:443, 3.91.167.191:443），x1000 次 BackOff 持续 8h |\n| **default/dig-tool** | 镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，Events 显示 `i/o timeout` 到 `asia-east1-docker.pkg.dev:443` 和 `us-west2-docker.pkg.dev:443`，不同镜像也不同仓库 |\n| **mcp/node-debugger-node2-2cg95** | 镜像 `busybox:1.36.1` 在 node2，Events 显示 `dial tcp 108.160.161.83:443: i/o timeout` 到 `registry-1.docker.io` |\n| **default/dns-test-check** | 镜像 `busybox:1.36.1` 在 node2，Events 显示 `dial tcp 74.86.118.24:443: i/o timeout` 到 `registry-1.docker.io` |\n| **跨 namespace 一致性** | aiops-e2e、default、mcp 三个 namespace 的 Pod 无论跑在 node1 还是 node2，均出现 **i/o timeout** 无法连接到外部镜像仓库（docker.io 和 registry.k8s.io）|\n| **不同镜像均失败** | `busybox:1.36.1`（docker.io）、`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`（k8s artifacts registry）均无法拉取 |\n\n**2. 次异常组 g1 — CreateContainerConfigError（1 个 Pod）**\n\n| 维度 | 证据 |\n|------|------|\n| **aiops-e2e/rc-config-configmap-key-missing** | Pod Events 明确显示：`couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config` |\n| **ConfigMap rc-app-config 内容** | 该 ConfigMap **只包含 key `EXISTING_KEY`**，**不存在 `APP_BOOT_MODE`** 这个 key。Pod env 引用了不存在的 key，属于应用配置错误 |\n\n### 关键结论\n\n1. **根因：集群节点（node1 和 node2）无法访问外部镜像仓库** — 所有节点访问 `registry-1.docker.io`、`asia-east1-docker.pkg.dev`、`us-west2-docker.pkg.dev` 均出现 `i/o timeout`（TCP 连接超时）。这不是单个镜像问题，而是**集群到公网镜像仓库的网络连通性故障**（可能是出口防火墙/代理/NAT 问题）。\n\n2. **独立问题：ConfigMap key 缺失** — `rc-config-configmap-key-missing` 是独立的 L4 配置错误，与镜像拉取无关，需在 ConfigMap `rc-app-config` 中添加 `APP_BOOT_MODE` key。","collection_summary":"计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%；其中真实环境证据 14/14 项，完整度 100%；实际执行工具 16 个，匹配计划 7 个，未规划证据 9 个","plan_total":7,"plan_collected":7,"plan_completeness":1.0,"environment_evidence_total":14,"environment_evidence_collected":14,"environment_evidence_completeness":1.0,"executed_tool_count":16,"matched_tool_count":7,"unplanned_tool_count":9,"evidence_inventory":[{"id":"e1","description":"检查主异常组g2的代表Pod - aiops-e2e/test-dns-1779360358 (ImagePullBackOff) 的Pod Events和当前状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e test-dns-1779360358","purpose":"查看ImagePullBackOff的详细Events和错误原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查主异常组g2中default/dig-tool (ImagePullBackOff, node1) 的Pod Events和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dig-tool","purpose":"交叉验证default命名空间的ImagePullBackOff原因是否与aiops-e2e一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查主异常组g2中mcp/node-debugger-node2-2cg95 (ErrImagePull, node2) 的Pod Events和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n mcp node-debugger-node2-2cg95","purpose":"验证mcp命名空间不同节点上ErrImagePull与ImagePullBackOff的错误是否一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"检查主异常组g2中default/dns-test-check (ImagePullBackOff, node2) 的Pod Events，覆盖node2节点","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n default dns-test-check","purpose":"验证node2上的ImagePullBackOff是否有不同的错误信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"获取所有命名空间涉及ImagePull的Events，搜索Failed/Error/BackOff","level":"critical","tool":"kubectl_events","command":"kubectl events -A --types=Warning | grep -iE 'image|pull|backoff|error|fail'","purpose":"从集群事件层面统一查看所有镜像拉取相关告警","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"检查非主异常组g1 - aiops-e2e/rc-config-configmap-key-missing (CreateContainerConfigError) 的Pod Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-config-configmap-key-missing","purpose":"验证CreateContainerConfigError的具体缺失key和引用的ConfigMap","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7","description":"验证ConfigMap aiops-e2e/rc-app-config是否存在及内容","level":"important","tool":"kubectl_get_yaml","command":"kubectl get configmap -n aiops-e2e rc-app-config -o yaml","purpose":"验证CreateContainerConfigError引用的ConfigMap是否存在及包含APP_BOOT_MODE key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 检查主异常组g2的代表Pod - aiops-e2e/test-dns-177936035... | `kubectl describe pod -n aiops-e2e test-dns-1779360358` |
   | e2 | critical | ✅ | kubectl_describe | 检查主异常组g2中default/dig-tool (ImagePullBackOff, ... | `kubectl describe pod -n default dig-tool` |
   | e3 | critical | ✅ | kubectl_describe | 检查主异常组g2中mcp/node-debugger-node2-2cg95 (ErrIm... | `kubectl describe pod -n mcp node-debugger-node2-2cg95` |
   | e4 | important | ✅ | kubectl_describe | 检查主异常组g2中default/dns-test-check (ImagePullBac... | `kubectl describe pod -n default dns-test-check` |
   | e5 | critical | ✅ | kubectl_events | 获取所有命名空间涉及ImagePull的Events，搜索Failed/Error/Bac... | `kubectl events -A --types=Warning | grep -iE 'image|pull|backoff|error|fail'` |
   | e6 | critical | ✅ | kubectl_describe | 检查非主异常组g1 - aiops-e2e/rc-config-configmap-key... | `kubectl describe pod -n aiops-e2e rc-config-configmap-key-missing` |
   | e7 | important | ✅ | kubectl_get_yaml | 验证ConfigMap aiops-e2e/rc-app-config是否存在及内容 | `kubectl get configmap -n aiops-e2e rc-app-config -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (23.4s)
   📤 → 下游数据: root_cause=集群主异常组g2（43个ImagePullBackOff/ErrImagePull Pod）的根因是集群节点（node1/10.2.0.49，node2/10.2.0.50）到公网镜像仓库的出站网络连接故障。证据：（1）default/dns-test-check on node2访问registry-1.docker.io:443报i/o timeout（IP 74.86.118.24）；（2）default/dig-tool on node1访问asia-east1-docker.pkg.dev:443和us-west2-docker.pkg.dev:443均i/o timeout；（3）aiops-e2e/test-dns-1779360358 on node1访问registry-1.docker.io多个IP（162.125.17.131, 3.233.166.60, 3.91.167.191）全部超时或连接重置；（4）mcp/node-debugger-node2-2cg95 on node2访问registry-1.docker.io（IP 108.160.161.83:
... 截断，原始 768 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1和node2）到公网镜像仓库的出站网络连接故障：节点无法通过TCP 443端口连接到docker.io（registry-1.docker.io）和registry.k8s.io（asia-east1-docker.pkg.dev、us-west2-docker.pkg.dev）的CDN端点，所有连接均返回i/o timeout", "propagation": "当kubelet尝试拉取容器镜像时，containerd向镜像仓库发起HTTPS请求 → TCP握手阶段超时（i/o timeout）→ 拉取失败 → kubelet重试并触发BackOff机制 → Pod状态变为ErrImagePull → 最终回退到ImagePullBackOff循环 → 43个Pod进入持续的BackOff退避状态", "direct_cause": "kubelet/containerd无法从外部镜像仓库下载容器镜像，HTTPS请求在TCP dial阶段超时", "manifestation": "43个Pod（分布在aiops-e2e、default、mcp三个namespace，node1和node2两个节点上）处于ImagePullBackOff（41个）或ErrImagePull（2个）状态，容器无法启动，Pod处于Pending状态"}
   rca_analysis={"phenomenon": "集群中存在44个异常Pod分布在3个namespace（aiops-e2e、default、mcp）：43个Pod处于ImagePullBackOff/ErrImagePull状态（ImagePullFailed），1个Pod（rc-config-configmap-key-missing）处于CreateContainerConfigError状态。Running=59个正常，kube-system/admin等核心组件正常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe - default/dns-test-check (node2)", "content": "busybox:1.36.1拉取失败: dial tcp 74.86.118.24:443: i/o timeout", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe - default/dig-tool (node1)", "content": "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0拉取失败: dial tcp asia-east1-docker.pkg.dev:443 i/o timeout + us-west2-docker.pkg.dev:443 i/o timeout", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe - aiops-e2e/test-dns-1779360358 (node1)", "content": "busybox:1.36.1拉取失败: i/o timeout + connection reset by peer 到registry-1.docker.io多IP(162.125.17.131, 3.233.166.60, 3.91.167.191)", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe - mcp/node-debugger-node2-2cg95 (node2)", "content": "busybox:1.36.1拉取失败: dial tcp 108.160.161.83:443: i/o timeout", "reliability": "高"}, {"id": "e5", "source": "kubectl_events - 跨namespace Events筛选", "content": "所有Failed事件均为网络超时(i/o timeout): dig-tool→asia-east1/us-west2-docker.pkg.dev, test-dns→registry-1.docker.io, 均返回tcp连接超时", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe - aiops-e2e/rc-config-configmap-key-missing", "content": "Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_yaml / run_bash_command - ConfigMap rc-app-config", "content": "ConfigMap aiops-e2e/rc-app-config 只包含key EXISTING_KEY，不存在APP_BOOT_MODE", "reliability": "高"}, {"id": "e8", "source": "kubectl_get_by_kind_in_cluster", "content": "109 Pods总计: Running=59, ImagePullBackOff=41, ErrImagePull=2, CreateContainerConfigError=1, Completed=3", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Failed to pull image \"busybox:1.36.1\": dial tcp 74.86.118.24:443: i/o timeout", "interpretation": "node2上的Pod dns-test-check无法通过TCP连接到docker.io registry IP 74.86.118.24:443，连接超时说明节点到公网镜像仓库的网络路径不通"}, {"evidence_id": "e2", "raw_data": "Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": dial tcp asia-east1-docker.pkg.dev:443 i/o timeout + us-west2-docker.pkg.dev:443 i/o timeout", "interpretation": "node1上的dig-tool无法连接到两个不同的registry.k8s.io CDN端点（asia-east1和us-west2），同样都是TCP连接超时，说明不是单个端点问题"}, {"evidence_id": "e3", "raw_data": "Failed to pull image \"busybox:1.36.1\": i/o timeout + connection reset by peer 到registry-1.docker.io IPs 162.125.17.131, 3.233.166.60, 3.91.167.191", "interpretation": "node1上的test-dns-1779360358尝试多个registry-1.docker.io IP均失败，包含超时和连接重置，排除DNS解析问题、确认是网络层故障"}, {"evidence_id": "e4", "raw_data": "Failed to pull image \"busybox:1.36.1\": dial tcp 108.160.161.83:443: i/o timeout", "interpretation": "node2上的node-debugger-node2-2cg95同样连接到registry-1.docker.io的不同IP(108.160.161.83)也超时，node1和node2均受影响"}, {"evidence_id": "e5", "raw_data": "所有Events摘要：dig-tool→asia-east1/us-west2-docker.pkg.dev超时；test-dns→registry-1.docker.io超时；node-debugger-node2-2cg95→registry-1.docker.io超时", "interpretation": "跨namespace、跨node、跨不同镜像仓库(docker.io和registry.k8s.io)均出现相同的TCP i/o timeout模式，这是集群级出口网络故障的强证据"}, {"evidence_id": "e6", "raw_data": "Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config", "interpretation": "Pod rc-config-configmap-key-missing的CreateContainerConfigError原因是引用了ConfigMap中不存在的key，这是独立的应用配置问题"}, {"evidence_id": "e7", "raw_data": "ConfigMap rc-app-config只有key EXISTING_KEY，无APP_BOOT_MODE", "interpretation": "确认ConfigMap确实缺少APP_BOOT_MODE key，验证了e6的错误信息，属于Pod spec中env引用错误"}, {"evidence_id": "e8", "raw_data": "ImagePullBackOff=41, ErrImagePull=2, CreateContainerConfigError=1", "interpretation": "44个异常Pod中43个是镜像拉取失败，1个是ConfigMap配置错误；集群其他59个Running Pod正常，说明应用本身无故障"}], "causal_chain": {"root_cause": "集群节点（node1和node2）到公网镜像仓库的出站网络连接故障：节点无法通过TCP 443端口连接到docker.io（registry-1.docker.io）和registry.k8s.io（asia-east1-docker.pkg.dev、us-west2-docker.pkg.dev）的CDN端点，所有连接均返回i/o timeout", "propagation": "当kubelet尝试拉取容器镜像时，containerd向镜像仓库发起HTTPS请求 → TCP握手阶段超时（i/o timeout）→ 拉取失败 → kubelet重试并触发BackOff机制 → Pod状态变为ErrImagePull → 最终回退到ImagePullBackOff循环 → 43个Pod进入持续的BackOff退避状态", "direct_cause": "kubelet/containerd无法从外部镜像仓库下载容器镜像，HTTPS请求在TCP dial阶段超时", "manifestation": "43个Pod（分布在aiops-e2e、default、mcp三个namespace，node1和node2两个节点上）处于ImagePullBackOff（41个）或ErrImagePull（2个）状态，容器无法启动，Pod处于Pending状态"}, "root_cause": "集群主异常组g2（43个ImagePullBackOff/ErrImagePull Pod）的根因是集群节点（node1/10.2.0.49，node2/10.2.0.50）到公网镜像仓库的出站网络连接故障。证据：（1）default/dns-test-check on node2访问registry-1.docker.io:443报i/o timeout（IP 74.86.118.24）；（2）default/dig-tool on node1访问asia-east1-docker.pkg.dev:443和us-west2-docker.pkg.dev:443均i/o timeout；（3）aiops-e2e/test-dns-1779360358 on node1访问registry-1.docker.io多个IP（162.125.17.131, 3.233.166.60, 3.91.167.191）全部超时或连接重置；（4）mcp/node-debugger-node2-2cg95 on node2访问registry-1.docker.io（IP 108.160.161.83:\n... 截断，原始 768 字符", "root_cause_summary": "集群主异常组g2（43个ImagePullBackOff/ErrImagePull Pod）的根因是集群节点（node1/10.2.0.49，node2/10.2.0.50）到公网镜像仓库的出站网络连接故障。证据：（1）default/dns-test-check on node2访问registry-1.docker.io:443报i/o timeout（IP 74.86.118.24）；（2）default/dig-tool on node1访问asia-east1-docker.pkg.dev:443和us-west2-docker.pkg.dev:443均i/o timeout；（3）aiops-e2e/test-dns-1779360358 on node1访问registry-1.docker.io多个IP（162.125.17.131, 3.233.166.60, 3.91.167.191）全部超时或连接重置；（4）mcp/node-debugger-node2-2cg95 on node2访问registry-1.docker.io（IP 108.160.161.83:\n... 截断，原始 768 字符", "confidence": 0.95, "confidence_reason": "有4个Pod的kubectl_describe直接证据、1个跨namespace Events汇总证据、ConfigMap内容验证证据，所有证据指向一致的结论：TCP i/o timeout。因果链完整清晰，无矛盾证据。", "primary_runbooks": [], "alternative_causes": [{"cause": "镜像地址或tag不存在", "probability": "low", "reason": "busybox:1.36.1是合法tag，且dig-tool使用registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0也是标准镜像；Events显示是网络超时而非manifest not found，排除镜像不存在"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "busybox:1.36.1和registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0均为公开镜像，不需要认证；且错误信息是网络超时而非认证拒绝(denied/unauthorized)"}, {"cause": "镜像仓库DNS解析失败", "probability": "low", "reason": "Events显示域名已成功解析为具体IP地址（如registry-1.docker.io→74.86.118.24, 162.125.17.131等），超时发生在TCP dial阶段而非DNS阶段"}], "limitations": "未采集集群出口网络配置（防火墙规则、代理设置、NAT配置）、未在节点上直接执行curl/wget测试公网连通性、未检查containerd配置中的mirror/registry配置。但这些缺失不影响根因结论，因为i/o timeout已明确指向网络层问题。", "llm_raw_analysis": "上游layer_handoff已识别出两个异常组：g1（CreateContainerConfigError，1个Pod）和g2（ImagePullBackOff/ErrImagePull，43个Pod）。evidence节点已采集8个关键证据。g2是主异常组，影响面覆盖43个Pod。所有g2的Pod Events一致显示TCP连接超时(i/o timeout)到不同公网镜像仓库IP，跨越node1/node2。g1已最小验证为ConfigMap key缺失。置信度0.95。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群主异常组g2（43个ImagePullBackOff/ErrImagePull Pod）的根因是集群节点（node1/10.2.0.49，node2/10.2.0.50）到公网镜像仓库的出站网络连接故障。证据：（1）default/dns-test-check on node2访问registr...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1和node2）到公网镜像仓库的出站网络连接故障：节点无法通过TCP 443端口连接到docker.io（registry-1.docker.io）和registry.k8s.io（asia-east1-docker.pkg.dev、us-west2-docker.pkg.dev）的CDN端点，所有连接均返回i/o timeout
     传导机制: 当kubelet尝试拉取容器镜像时，containerd向镜像仓库发起HTTPS请求 → TCP握手阶段超时（i/o timeout）→ 拉取失败 → kubelet重试并触发BackOff机制 → Pod状态变为ErrImagePull → 最终回退到ImagePullBackOff循环 → 43个Pod进入持续的BackOff退避状态
     最终表现: 43个Pod（分布在aiops-e2e、default、mcp三个namespace，node1和node2两个节点上）处于ImagePullBackOff（41个）或ErrImagePull（2个）状态，容器无法启动，Pod处于Pending状态


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (26.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6407 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 2.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您分析当前集群状态并出具诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **核心问题** | 集群中存在 **44 个异常 Pod**，主要问题是大量 Pod 无法拉取镜像，以及 1 个 Pod 配置错误。 |
| **Pod 异常状态** | `ImagePullBackOff` (41个), `ErrImagePull` (2个), `CreateContainerConfigError` (1个) |
| **兼容归因层** | L3 - 镜像仓库/网络/运行时环境 |
| **问题分类** | 集群级别网络故障导致的大规模镜像拉取失败 |
| **置信度** | 高 (95%) |
| **证据完整度** | 7/7 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键发现**：
集群在 `aiops-e2e`, `default`, `mcp` 三个命名空间下共发现 44 个异常 Pod，其中：
*   **43 个 Pod** 处于 `ImagePullBackOff` (41个) 或 `ErrImagePull` (2个) 状态，表明无法从镜像仓库拉取容器镜像。
*   **1 个 Pod** (`aiops-e2e/rc-config-configmap-key-missing`) 处于 `CreateContainerConfigError` 状态，表明 ConfigMap 配置错误。

**关键实体**：
| 类型 | 值 |
|------|-----|
| 受影响命名空间 | `aiops-e2e`, `default`, `mcp` |
| 受影响节点 | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| 错误信息 (例) | `Failed to pull image "busybox:1.36.1": ... i/o timeout`, `Error: ErrImagePull` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 (关键行) | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pods -A` | `ImagePullBackOff=41, ErrImagePull=2, CreateContainerConfigError=1` | 确认集群存在大规模镜像拉取失败和配置错误问题。 |
| 2 | Pod 详情 | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` | `Failed to pull image 'busybox:1.36.1' ... network errors (i/o timeout, connection reset by peer)'` | 节点 `node1` 无法连接到 `docker.io` 拉取镜像，出现超时/连接重置。 |
| 3 | Pod 详情 | `kubectl describe pod dig-tool -n default` | `Failed to pull image ... dial tcp asia-east1-docker.pkg.dev:443 i/o timeout` | 节点 `node1` 无法连接到 `registry.k8s.io` 的 CDN 端点。 |
| 4 | Pod 详情 | `kubectl describe pod dns-test-check -n default` | `Failed to pull image ... dial tcp registry-1.docker.io:443 i/o timeout` | 节点 `node2` 也无法连接到 `docker.io`，出现超时。 |
| 5 | Pod 详情 | `kubectl describe pod node-debugger-node2-2cg95 -n mcp` | `Back-off pulling image "busybox:1.36.1"` | 节点 `node2` 上的 Pod 也因镜像拉取失败进入BackOff状态，确认问题影响两个节点。 |
| 6 | Pod 详情 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | `Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config` | 一个独立的 Pod 因为 ConfigMap 中缺少必填配置项而启动失败。 |
| 7 | ConfigMap 验证 | `kubectl get configmap rc-app-config -n aiops-e2e -o yaml` | `data: EXISTING_KEY: present` | 确认 ConfigMap 存在，但确实不包含 `APP_BOOT_MODE` 这个 key，导致 Pod 无法创建。 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 + #5 印证**: 分布在 `node1` 和 `node2` 上、拉取不同仓库 (`docker.io`, `registry.k8s.io`) 镜像的 Pod 均出现 `i/o timeout` 错误。这明确指向**集群级别的出站网络连接故障**，而不是单个镜像或仓库的问题。
- **证据 #6 + #7 印证**: `CreateContainerConfigError` 是一个独立的、配置层面的问题，与网络故障无关。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点出口网络配置（防火墙、NAT、代理） | medium | 可以进一步确诊网络故障的根本原因，但 `i/o timeout` 已锁定问题层面，不影响当前根因结论。 |

---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────┐
│ 根本原因                                                         │
│ 集群节点（node1 和 node2）到公网镜像仓库的出站网络连接故障。     │
│ (例如: 防火墙规则、NAT 网关故障或代理配置错误)                   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 传导机制                                                         │
│ kubelet 尝试拉取镜像 -> containerd 向镜像仓库发起 HTTPS 请求    │
│ -> TCP 三次握手超时 (i/o timeout) -> 拉取请求被放弃              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 直接原因                                                         │
│ kubelet/containerd 无法从外部镜像仓库 (`docker.io`, `registry.k8s.io`) 下载容器镜像。 |
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                     │
│ 43 个 Pod 处于 ImagePullBackOff / ErrImagePull 状态，持续重启拉取镜像失败  |
└──────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2, #3, #4, #5 (所有 Pod 的事件均显示 `i/o timeout` 错误)，问题的根本原因是**集群两个工作节点 (`node1`, `node2`) 到外部公网镜像仓库 (`docker.io`, `registry.k8s.io` 等) 的网络连接中断**。这导致 kubelet 无法拉取镜像，43 个相关的 Pod 进入 `ImagePullBackOff` 状态。

**置信度**：高 (95%)
- ✅ `i/o timeout` 错误是网络问题的直接证据。
- ✅ 跨节点、跨镜像仓库的错误类型一致，排除了单个仓库或镜像的问题。
- ✅ 没有其他（如凭证错误、镜像不存在）的错误信息出现。

**独立问题**: Pod `rc-config-configmap-key-missing` 的 `CreateContainerConfigError` 是一个独立的配置问题，原因是应用的 ConfigMap 缺少 `APP_BOOT_MODE` 键值对。

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [首要] 修复集群出口网络（请与您的网络/基础设施团队合作）**
此问题需排查并修复从 Kubernetes 节点到互联网的出站连接。可能的原因包括：
- **防火墙/NAT 规则**：检查集群节点的安全组或防火墙出站规则，确保允许访问 `docker.io` 和 `registry.k8s.io` 的 `443` 端口。
- **代理配置**：如果集群通过代理访问外网，检查 `containerd` 或 `kubelet` 的代理配置是否正确。
- **云服务商 NAT 网关**：如果集群节点位于私有子网，请检查 NAT 网关或 Egress 网关状态。

**2. [备用方案] 配置镜像仓库镜像 (Mirror)**
为避免公网依赖，建议配置私有镜像仓库或使用集群节点的本地缓存作为 mirror，将关键镜像 `busybox:1.36.1` 等提前拉取并托管。
```bash
# 示例：在 containerd config.toml 中配置 mirror
# 将 docker.io 的请求转发到内部仓库 <your-harbor>/library
# 此操作需在所有节点上执行，具体路径请参考您的 containerd 配置
```

**3. [简单修复] 修复 ConfigMap 配置错误**
为 `rc-config-configmap-key-missing` Pod 添加缺失的 ConfigMap 配置。
```bash
kubectl edit configmap rc-app-config -n aiops-e2e
```
在 `data` 字段下添加：
```yaml
data:
  APP_BOOT_MODE: <desired_value>  # 例如: "production"
  EXISTING_KEY: present
```
然后删除旧的 Pod 以重新创建：
```bash
kubectl delete pod rc-config-configmap-key-missing -n aiops-e2e
```

**4. [排查工具] 在节点上直接测试网络连通性**
```bash
# 在 node1 和 node2 上执行
curl -v https://registry-1.docker.io/v2/ 2>&1 | head -20
curl -v https://registry.k8s.io/v2/ 2>&1 | head -20
```
*预期结果*: 如果网络正常，应返回 HTTP 响应。如果出现 `Connection timed out`，则确认根因。

### 后续优化
1. **监控告警**： 配置对 `ImagePullBackOff` 和 `ErrImagePull` 状态的告警，以便快速发现此类大规模问题。
2. **资源评估**： 建议将常用业务镜像托管在内部可信的私有镜像仓库 (如 Harbor)，避免对公网仓库的强依赖，提高部署稳定性。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认异常 Pod 减少 | `kubectl get pods -A \| grep -E 'ImagePullBackOff\|ErrImagePull'` | 数量应显著减少或减少为 0。 |
| 2. 确认 Pod 重新拉取镜像 | `kubectl describe pod <pod-name> -n <namespace>` | 应看到 `Normal Pulling ...` 或 `Normal Pulled ...` 事件。 |
| 3. 确认 Pod 进入运行态 | `kubectl get pods <pod-name> -n <namespace>` | `STATUS` 应为 `Running`。 |
| 4. 验证 ConfigMap 修复 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e` | `STATUS` 应为 `Running`。 |

---
## ⚠️ 注意事项
- **停机影响**： 修复网络问题可能导致短暂的服务中断，请与业务方沟通并安排在维护窗口进行。
- **操作权限**： 网络配置和 containerd 配置修改需要集群管理员或系统管理员权限。
- **安全扫描**： 引入私有镜像仓库后，务必集成镜像安全扫描，确保不引入恶意软件。

---

## 📊 性能统计

├─ 总耗时: 2.0m
├─ 问题定位: 38.4s (31%) ✅
├─ 证据链采集: 34.2s (28%) ✅
├─ 根因分析: 23.4s (19%) ✅
├─ 汇总总结: 26.6s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 19 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed
- **工具调用**: 19 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
