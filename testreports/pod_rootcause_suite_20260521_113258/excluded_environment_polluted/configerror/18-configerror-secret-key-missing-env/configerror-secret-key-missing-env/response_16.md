======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 108a5676017146fc]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先全局扫描 Pod 状态，看看集群中有什么异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned raw pods table from all namespaces. Total rows ~115 (partial raw_preview). Abnormal pods: ImagePullBackOff=26, ErrImagePull=22, CreateContainerConfigError=1 (pe
   💭 [问题定位] 扫描结果已经清楚了。现在让我获取相关的 Runbook 来帮助定位问题。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [问题定位] 现在让我获取更详细的信息，看看具体的异常 Pod 和它们的镜像问题。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=367 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=322 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=25834 lines=977
Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "rc-config-secret-key-missing",
  "status": "Pending",
  "phase": "Pending",

   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=7771 lines=529
Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "test-dns-1779360358",
  "node": "node1",
  "reason": [
    "ImagePullBackOff"
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 jq query returned 49 pods across namespaces aiops-e2e, default, mcp — all in ImagePullBackOff or ErrImagePull on node1 and node2. Images involved: busybox:1.36.1, registry.k8s.io/e2e-test-images/jessi
   💭 [问题定位] 好的，信息已经非常充分了。让我再快速看一下那个 ConfigError Pod 的详情，以及确认一下节点状态。
   💭 [问题定位] 调用工具: kubectl_describe
   ✅ [问题定位] 完成 (41.5s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '镜像仓库网络不可达 - node1和node2均无法拉取镜像', 'probability': '高', 'reason': '大量Pod（49个）在node1和node2上同时出现ImagePullBackOff/ErrImagePull，涉及多种镜像仓库（busybox、registry.k8s.io、curlimages、alpine），表明不是单个镜像问题而是镜像仓库网络可达性问题'}, {'scenario': '镜像仓库认证/权限问题', 'probability': '低', 'reason': '涉及多个公开镜像仓库（docker.io、registry.k8s.io），如果是认证问题应出现unauthorized/denied错误，但目前广泛表现为拉取失败'}, {'scenario': 'ConfigError - aiops-e2e/rc-config-secret-key-missing Secret key缺失', 'probability': '高', 'reason': "Pod详情明确显示couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret，是独立的L4配置错误"}]
   entities=[{"type": "pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}]
   reasoning=集群中存在大量当前仍异常的Pod：(1) 26个ImagePullBackOff Pod + 22个ErrImagePull Pod（分布在default/aiops-e2e/mcp命名空间，涉及数十种镜像如busybox:1.36.1、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0、alpine:3.18、curlimages/curl等），属于L3 ImagePullFailed异常类型；(2) 1个CreateContainerConfigError Pod（aiops-e2e/rc-config-secret-key-missing），Secret key 'APP_SECRET_TOKEN'找不到，属于L4 ConfigError。按根因归因优先原则：大量镜像拉取失败（ImagePullBackOff/ErrImagePull）是当前集群最广泛的异常，根因在镜像仓库网络可达性或镜像拉取能力（L3），因此主层级定L3。同时存在L4配置问题作为次要层。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "Image Pull / Network", "confidence": 0.95, "reasoning": "集群中存在大量当前仍异常的Pod：(1) 26个ImagePullBackOff Pod + 22个ErrImagePull Pod（分布在default/aiops-e2e/mcp命名空间，涉及数十种镜像如busybox:1.36.1、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0、alpine:3.18、curlimages/curl等），属于L3 ImagePullFailed异常类型；(2) 1个CreateContainerConfigError Pod（aiops-e2e/rc-config-secret-key-missing），Secret key 'APP_SECRET_TOKEN'找不到，属于L4 ConfigError。按根因归因优先原则：大量镜像拉取失败（ImagePullBackOff/ErrImagePull）是当前集群最广泛的异常，根因在镜像仓库网络可达性或镜像拉取能力（L3），因此主层级定L3。同时存在L4配置问题作为次要层。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff, ErrImagePull, CreateContainerConfigError", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达 - node1和node2均无法拉取镜像", "probability": "高", "reason": "大量Pod（49个）在node1和node2上同时出现ImagePullBackOff/ErrImagePull，涉及多种镜像仓库（busybox、registry.k8s.io、curlimages、alpine），表明不是单个镜像问题而是镜像仓库网络可达性问题"}, {"scenario": "镜像仓库认证/权限问题", "probability": "低", "reason": "涉及多个公开镜像仓库（docker.io、registry.k8s.io），如果是认证问题应出现unauthorized/denied错误，但目前广泛表现为拉取失败"}, {"scenario": "ConfigError - aiops-e2e/rc-config-secret-key-missing Secret key缺失", "probability": "高", "reason": "Pod详情明确显示couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret，是独立的L4配置错误"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 26, "ErrImagePull": 22}, "total_abnormal": 48, "selected_rows": ["aiops-e2e         rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0              18m     172.16.166.130   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff             0              9h      172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              5h14m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff             0              4h14m   172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              8h      172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff             0              93m     172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff             0              99m     172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull                 0              99m     172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff             0              9h      172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull                 0              7h27m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff             0              99m     172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull                 0              4h20m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              8h      172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull                 0              9h      172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull                 0              5h56m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ErrImagePull                 0              127m    172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull                 0              6h55m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-conn-test-evidence                         0/1     ErrImagePull                 0              32m     172.16.104.22    node2    <none>           <none>            run=registry-conn-test-evidence", "default           registry-connect-test                               0/1     ErrImagePull                 0              8h      172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              9h      172.16.166.185   node1    <none>           <none>            run=test-net-1779360704"], "raw_ref": "/tmp/aiops/reports/context_archives/108a5676017146fc/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/108a5676017146fc/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/108a5676017146fc/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] # 开始执行证据采集

首先获取两个已匹配的 Runbook 作为参考，同时开始采集证据。

## Step 1: 并行获取 Runbook + 各异常组关键证据

先并行获取参考 runbook 和多个 Pod 的 describe/events/YAML。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
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
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-resolve-test (default) on node2 is Pending. Container busybox:1.36.1 with args ['nslookup', 'registry-1.docker.io'] is Waiting (Reason: ErrImagePull). 6 Failed events (60m to 8m59s ago) show r
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   31m (x119 over 9h)    kubelet  (combined from similar events): Fail
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          17m (x12 over 18m)    kubelet            Error: cou
   💭 [证据链采集] 非常好！关键证据已获取。现在继续执行剩余计划项：获取命名空间事件和 YAML 配置。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_get_yaml
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
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
50m                     Warning   Failed    Pod/dns-resolve-test   Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = failed to pull and unpack image "do
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
32m (x119 over 9h)     Warning   Failed    Pod/test-dns-1779360358   (combined from similar events): Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = f
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: test-dns-1779360358
namespace: aiops-e2e
creationTimestamp: 2026-05-21T10:45:58Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
17m (x12 over 19m)     Warning   Failed           Pod/rc-config-secret-key-missing   Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
50m                    Warning   Failed    Pod/dns-resolve-test   Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = failed to pull and unpack image "doc
   💭 [证据链采集] 现在让我继续按计划采集 default 和 mcp 命名空间的事件，验证跨命名空间的镜像拉取是否同一根因。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
60m                      Warning   Failed   Pod/registry-diag-1779381627   Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = failed to pull and unpack i
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
53m                 Warning   Failed    Pod/registry-connect-test   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and unpack
   💭 [证据链采集] 所有关键工具调用已完成。以下是证据采集结论：

---

## 证据采集结论

### ✅ 已采集证据

**异常组 g1 (CreateContainerConfigError) — rc-config-secret-key-missing**
- **🟢 describe pod 确认**：容器处于 waiting 状态，reason=`CreateContainerConfigError`，message=`couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`
- **🟢 Events 确认**：19分钟内重复12次 `couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`
- **🟢 Secret YAML 确认**：`rc-app-secret` 只包含 key `EXISTING_SECRET_KEY`，**缺少 `APP_SECRET_TOKEN` 键**
- **结论**：ConfigError 确认为 Secret 缺少 `APP_SECRET_TOKEN` 键 → **pod-config-error.md runbook 匹配**

**异常组 g2 (ImagePullFailed) — 跨命名空间大规模镜像拉取失败**
- **🟢 node1 (aiops-e2e/test-dns-1779360358)**：Event 明确显示 `connection reset by peer` 连接 `registry-1.docker.io:443` → 网络层不稳定
- **🟢 node2 (default/dns-resolve-test)**：Event 明确显示 `i/o timeout` 连接 `registry-1.docker.io:443` → 网络超时
- **🟢 node2 (default/registry-connect-test)**：8小时内68次 `i/o timeout` 连接 docker.io
- **🟢 mcp/registry-diag-1779381627**：4小时内31次 `i/o timeout` 连接 docker.io
- **🟢 Pod YAML 确认**：无 `imagePullSecrets`，镜像为公开仓库 `busybox:1.36.1`，不是认证问题
- **结论**：node1 和 node2 **都无法稳定连接 docker.io（registry-1.docker.io:443）**，表现为 node1 偶有 `connection reset`，node2 持续 `i/o timeout` → **镜像仓库网络不可达，pod-imagepull-failed.md runbook 匹配**

**异常组 g3 (StartError) — node-debugger-node1-nx8gb**
- **🟢 describe pod 确认**：实际状态为 `Init:Error`，属于 mcp 命名空间的调试 Pod，与集群主故障无关
- **最小验证完成**

### ❌ 冲突/负向证据
- 无冲突证据；所有目标 Pod 均存在于预期 namespace，状态与上游描述一致

### 📋 根因总结
1. **主根因（L3 - 影响 48 个 Pod）**：集群节点（node1/node2）到 **registry-1.docker.io:443** 的网络连接不稳定/不可达——node1 出现 `connection reset by peer`，node2 出现持续 `i/o timeout`。这导致所有依赖 docker.io 公共镜像的 Pod 全部拉取失败。
2. **次要根因（L4 - 影响 1 个 Pod）**：Secret `aiops-e2e/rc-app-secret` 中缺少键 `APP_SECRET_TOKEN`，导致 Pod `rc-config-secret-key-missing` 无法创建容器。
   ✅ [证据链采集] 完成 (45.2s)
   📤 → 下游数据: evidence_items=15/15
   evidence_analysis={"evidence_plan":[{"id":"e1-p1","description":"Describe Pod rc-config-secret-key-missing in aiops-e2e for CreateContainerConfigError details (Secret key missing)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"Verify the exact CreateContainerConfigError message about missing Secret key APP_SECRET_TOKEN in Secret rc-app-secret","evidence_type":"current_state","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e1-p2","description":"Check events for aiops-e2e namespace to capture any relevant warnings","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by='.lastTimestamp' | tail -30","tool_args":{"namespace":"aiops-e2e"},"purpose":"Capture events related to CreateContainerConfigError and any image pull issues in aiops-e2e namespace","evidence_type":"current_state","target_scope":"aiops-e2e","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e2-p1","description":"Describe a representative ImagePullBackOff pod on node1 (e.g. test-dns-1779360358) to get exact Events showing pull failure reason","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"Get exact Events reason for ImagePullBackOff (connection refused/timeout/manifest unknown/auth failure) to diagnose root cause","evidence_type":"current_state","target_scope":"aiops-e2e/test-dns-1779360358","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2-p2","description":"Describe a representative ErrImagePull pod on node2 (e.g. dns-resolve-test) to compare events on different node","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","tool_args":{"kind":"pod","name":"dns-resolve-test","namespace":"default"},"purpose":"Get exact Events from node2 to see if ErrImagePull reason differs from node1's ImagePullBackOff","evidence_type":"current_state","target_scope":"default/dns-resolve-test","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2-p3","description":"Check events across default and mcp namespaces for image pull failure patterns","level":"important","tool":"kubectl_events","command":"kubectl get events -n default --sort-by='.lastTimestamp' | tail -30","tool_args":{"namespace":"default"},"purpose":"Find common image pull failure events in default namespace where most image pull failures occur","evidence_type":"current_state","target_scope":"default","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e2-p4","description":"Check events in mcp namespace where many node-debugger pods also have image pull failures","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --sort-by='.lastTimestamp' | tail -30","tool_args":{"namespace":"mcp"},"purpose":"Verify image pull failures extend to mcp namespace, confirming cross-namespace registry reachability issue","evidence_type":"current_state","target_scope":"mcp","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e2-p5","description":"Get YAML of a representative pod to check imagePullSecrets and image spec","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"Check imagePullSecrets, image spec, and registry details for the ImagePullBackOff pod","evidence_type":"current_state","target_scope":"aiops-e2e/test-dns-1779360358","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3-p1","description":"Minimal verification for StartError pod node-debugger-node1-nx8gb in mcp - describe to see current state","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"Check the StartError pod's current state and events for minimal verification","evidence_type":"current_state","target_scope":"mcp/node-debugger-node1-nx8gb","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"r1","description":"Fetch runbook for ImagePullFailed (matched_runbook from upstream)","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{},"purpose":"Reference runbook for image pull failure diagnosis patterns","evidence_type":"reference","target_scope":"reference","acceptable_tools":["fetch_runbook"],"counts_for_completeness":false}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod ConfigError / 启动配置失败\n\n> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | `CrashLoopBackOff` / `Error`，重启次数持续增加 |\n| Pod 配置错误 | `CreateContainerConfigError` / `CreateContainerError`，Events 含 ConfigMap/Secret/key not found、invalid env、executable file not found |\n| Init 容器错误 | `Init:*`、initContainer Waiting/Terminated，先检查 initContainer 的 image/env/volume/command/logs |\n| 应用配置错误 | 容器已启动后退出，日志含 `missing required`、`config validation failed`、`bootstrap` |\n| Describe | `Last State: Terminated`，`Exit Code: 42` 或其他非 137 业务退出码 |\n| 排除 OOM | 无 `OOMKilled`、无 `Exit Code 137` |\n| 排除拉镜像失败 | 无 `ImagePullBackOff`、容器实际已启动并输出业务日志 |\n| 排除驱逐 | 无 `Evicted`、无 `disk pressure`、无 `ENOSPC` |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 是否处于 CrashLoopBackOff\n```bash\nkubectl get pods -n <namespace> -l app=<app-name> -o wide\n```\n关注:\n- `STATUS` 是否为 `CrashLoopBackOff`\n- `RESTARTS` 是否持续增长\n\n### Step 2: 查看 describe 中的退出状态（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注:\n- `State: Waiting, Reason: CrashLoopBackOff`\n- `Last State: Terminated`\n- `Reason: Error`\n- `Exit Code:\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/002-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/002-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/002-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"Pod dns-resolve-test (default) on node2 is Pending. Container busybox:1.36.1 with args ['nslookup', 'registry-1.docker.io'] is Waiting (Reason: ErrImagePull). 6 Failed events (60m to 8m59s ago) show repeated pull failures for docker.io/library/busybox:1.36.1 — all i/o timeout dialing various registry-1.docker.io IPs (199.59.149.230, 108.160.165.139, 104.244.46.165, 108.160.170.39, 67.228.102.32, 69.63.176.15) on port 443. x9 over 91m for ErrImagePull. Normal Pulling x10 over 100m.\nkey_facts: [\"Pod dns-resolve-test in namespace default is Pending on node node2/10.2.0.50\", \"Container dns-resolve-test uses image busybox:1.36.1\", \"Container args: ['nslookup', 'registry-1.docker.io']\", \"Container State: Waiting, Reason: ErrImagePull, Ready: False\", \"6 Warning Failed events for image pull: all dial tcp to registry-1.docker.io:443 i/o timeout (different IPs each attempt)\", \"Latest Failed event at 8m59s ago, repeated x9 over 91m for Reason ErrImagePull\", \"Normal Pulling event x10 over 100m\", \"Pod has Calico network, IP 172.16.104.1\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary mentions only 5 Failed events with timestamps 60m/50m/40m/30m/19m; raw_preview shows 6 Failed events (60\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   31m (x119 over 9h)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:55574->54.224.154.163:443: read: connection reset by peer\n  Normal   BackOff  2m1s (x1306 over 9h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\n  Warning  Failed   60m   kubelet  Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:1\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          17m (x12 over 18m)    kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: e50889f651dff0ebd5a4ed7212a0f9deacd4b503f1ae265a36959b8e7c2ff9c4\n                  cni.projectcalico.org/podIP: 172.16.166.130/32\n                  cni.projectcalico.org/podIPs: 172.16.166.130/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-pbw78:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-r\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Secret\nname: rc-app-secret\nnamespace: aiops-e2e\ntype: Opaque\ndata_keys: EXISTING_SECRET_KEY\nhas_dockerconfigjson: False\ndocker_secret_type_valid: False","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/007-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/007-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/007-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n50m                     Warning   Failed    Pod/dns-resolve-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.165.139:443: i/o timeout\n40m                     Warning   Failed    Pod/dns-resolve-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 104.244.46.165:443: i/o timeout\n30m                     Warning   Failed    Pod/dns-resolve-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/bu\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/008-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/008-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/008-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n32m (x119 over 9h)     Warning   Failed    Pod/test-dns-1779360358   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:55574->54.224.154.163:443: read: connection reset by peer\n2m9s (x1306 over 9h)   Normal    BackOff   Pod/test-dns-1779360358   Back-off pulling image \"busybox:1.36.1\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/009-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/009-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/009-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: test-dns-1779360358\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T10:45:58Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- test-dns-1779360358: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: /bin/sh -c nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- test-dns-1779360358: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-g4sbz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/010-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/010-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/010-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n17m (x12 over 19m)     Warning   Failed           Pod/rc-config-secret-key-missing   Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/011-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/011-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/011-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n50m                    Warning   Failed    Pod/dns-resolve-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.165.139:443: i/o timeout\n40m                    Warning   Failed    Pod/dns-resolve-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 104.244.46.165:443: i/o timeout\n30m                    Warning   Failed    Pod/dns-resolve-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.170.39:443: i/o timeout\n19m                    Warning   Failed    Pod/dns-resolve-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 67.228.102.32:443: i/o timeout\n9m24s                  Warning   Failed    Pod/dns-resolve-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.176.15:443: i/o timeout\n9m24s (x9 over 92m)    Warning   Failed    Pod/dns-resolve-test   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/012-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/012-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/012-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n60m                      Warning   Failed   Pod/registry-diag-1779381627   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.59.149.230:443: i/o timeout\n49m                      Warning   Failed   Pod/registry-diag-1779381627   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.165.139:443: i/o timeout\n39m                      Warning   Failed   Pod/registry-diag-1779381627   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 202.160.129.6:443: i/o timeout\n29m                      Warning   Failed   Pod/registry-diag-1779381627   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.170.39:443: i/o timeout\n18m                      Warning   Failed   Pod/registry-diag-1779381627   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 104.244.46.165:443: i/o timeout\n8m26s                    Warning   Failed   Pod/registry-diag-1779381627   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 157.240.3.8:443: i/o timeout\n8m26s (x31 over 3h59m)   Warning   Failed   Pod/registry-diag-1779381627   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/013-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/013-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/013-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n53m                 Warning   Failed    Pod/registry-connect-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.165.139:443: i/o timeout\n43m                 Warning   Failed    Pod/registry-connect-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 104.244.46.165:443: i/o timeout\n33m                 Warning   Failed    Pod/registry-connect-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.166.61:443: i/o timeout\n22m                 Warning   Failed    Pod/registry-connect-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 67.228.102.32:443: i/o timeout\n11m                 Warning   Failed    Pod/registry-connect-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.176.15:443: i/o timeout\n86s                 Warning   Failed    Pod/registry-connect-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.166.42:443: i/o timeout\n86s (x68 over 8h)   Warning   Failed    Pod/registry-connect-test   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/014-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/014-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/108a5676017146fc/tools/014-evidence-kubectl_events.summary.txt"}],"llm_analysis":"所有关键工具调用已完成。以下是证据采集结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n**异常组 g1 (CreateContainerConfigError) — rc-config-secret-key-missing**\n- **🟢 describe pod 确认**：容器处于 waiting 状态，reason=`CreateContainerConfigError`，message=`couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`\n- **🟢 Events 确认**：19分钟内重复12次 `couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`\n- **🟢 Secret YAML 确认**：`rc-app-secret` 只包含 key `EXISTING_SECRET_KEY`，**缺少 `APP_SECRET_TOKEN` 键**\n- **结论**：ConfigError 确认为 Secret 缺少 `APP_SECRET_TOKEN` 键 → **pod-config-error.md runbook 匹配**\n\n**异常组 g2 (ImagePullFailed) — 跨命名空间大规模镜像拉取失败**\n- **🟢 node1 (aiops-e2e/test-dns-1779360358)**：Event 明确显示 `connection reset by peer` 连接 `registry-1.docker.io:443` → 网络层不稳定\n- **🟢 node2 (default/dns-resolve-test)**：Event 明确显示 `i/o timeout` 连接 `registry-1.docker.io:443` → 网络超时\n- **🟢 node2 (default/registry-connect-test)**：8小时内68次 `i/o timeout` 连接 docker.io\n- **🟢 mcp/registry-diag-1779381627**：4小时内31次 `i/o timeout` 连接 docker.io\n- **🟢 Pod YAML 确认**：无 `imagePullSecrets`，镜像为公开仓库 `busybox:1.36.1`，不是认证问题\n- **结论**：node1 和 node2 **都无法稳定连接 docker.io（registry-1.docker.io:443）**，表现为 node1 偶有 `connection reset`，node2 持续 `i/o timeout` → **镜像仓库网络不可达，pod-imagepull-failed.md runbook 匹配**\n\n**异常组 g3 (StartError) — node-debugger-node1-nx8gb**\n- **🟢 describe pod 确认**：实际状态为 `Init:Error`，属于 mcp 命名空间的调试 Pod，与集群主故障无关\n- **最小验证完成**\n\n### ❌ 冲突/负向证据\n- 无冲突证据；所有目标 Pod 均存在于预期 namespace，状态与上游描述一致\n\n### 📋 根因总结\n1. **主根因（L3 - 影响 48 个 Pod）**：集群节点（node1/node2）到 **registry-1.docker.io:443** 的网络连接不稳定/不可达——node1 出现 `connection reset by peer`，node2 出现持续 `i/o timeout`。这导致所有依赖 docker.io 公共镜像的 Pod 全部拉取失败。\n2. **次要根因（L4 - 影响 1 个 Pod）**：Secret `aiops-e2e/rc-app-secret` 中缺少键 `APP_SECRET_TOKEN`，导致 Pod `rc-config-secret-key-missing` 无法创建容器。","collection_summary":"计划 8 项，实际采集 8 项，未采集 0 项，完整度 100%；其中真实环境证据 14/14 项，完整度 100%；实际执行工具 17 个，匹配计划 9 个，未规划证据 8 个","plan_total":8,"plan_collected":8,"plan_completeness":1.0,"environment_evidence_total":14,"environment_evidence_collected":14,"environment_evidence_completeness":1.0,"executed_tool_count":17,"matched_tool_count":9,"unplanned_tool_count":8,"evidence_inventory":[{"id":"e1-p1","description":"Describe Pod rc-config-secret-key-missing in aiops-e2e for CreateContainerConfigError details (Secret key missing)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"Verify the exact CreateContainerConfigError message about missing Secret key APP_SECRET_TOKEN in Secret rc-app-secret","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e1-p2","description":"Check events for aiops-e2e namespace to capture any relevant warnings","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by='.lastTimestamp' | tail -30","purpose":"Capture events related to CreateContainerConfigError and any image pull issues in aiops-e2e namespace","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-p1","description":"Describe a representative ImagePullBackOff pod on node1 (e.g. test-dns-1779360358) to get exact Events showing pull failure reason","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"Get exact Events reason for ImagePullBackOff (connection refused/timeout/manifest unknown/auth failure) to diagnose root cause","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-p2","description":"Describe a representative ErrImagePull pod on node2 (e.g. dns-resolve-test) to compare events on different node","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","purpose":"Get exact Events from node2 to see if ErrImagePull reason differs from node1's ImagePullBackOff","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-p3","description":"Check events across default and mcp namespaces for image pull failure patterns","level":"important","tool":"kubectl_events","command":"kubectl get events -n default --sort-by='.lastTimestamp' | tail -30","purpose":"Find common image pull failure events in default namespace where most image pull failures occur","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-p4","description":"Check events in mcp namespace where many node-debugger pods also have image pull failures","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --sort-by='.lastTimestamp' | tail -30","purpose":"Verify image pull failures extend to mcp namespace, confirming cross-namespace registry reachability issue","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-p5","description":"Get YAML of a representative pod to check imagePullSecrets and image spec","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml","purpose":"Check imagePullSecrets, image spec, and registry details for the ImagePullBackOff pod","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-p1","description":"Minimal verification for StartError pod node-debugger-node1-nx8gb in mcp - describe to see current state","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"Check the StartError pod's current state and events for minimal verification","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"r1","description":"Fetch runbook for ImagePullFailed (matched_runbook from upstream)","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"Reference runbook for image pull failure diagnosis patterns","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/8 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-p1 | critical | ✅ | kubectl_describe | Describe Pod rc-config-secret-key-missing in ... | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | e1-p2 | important | ✅ | kubectl_events | Check events for aiops-e2e namespace to captu... | `kubectl get events -n aiops-e2e --sort-by='.lastTimestamp' | tail -30` |
   | e2-p1 | critical | ✅ | kubectl_describe | Describe a representative ImagePullBackOff po... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | e2-p2 | critical | ✅ | kubectl_describe | Describe a representative ErrImagePull pod on... | `kubectl describe pod dns-resolve-test -n default` |
   | e2-p3 | important | ✅ | kubectl_events | Check events across default and mcp namespace... | `kubectl get events -n default --sort-by='.lastTimestamp' | tail -30` |
   | e2-p4 | important | ✅ | kubectl_events | Check events in mcp namespace where many node... | `kubectl get events -n mcp --sort-by='.lastTimestamp' | tail -30` |
   | e2-p5 | important | ✅ | kubectl_get_yaml | Get YAML of a representative pod to check ima... | `kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml` |
   | e3-p1 | important | ✅ | kubectl_describe | Minimal verification for StartError pod node-... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | r1 | reference | ✅ | fetch_runbook | Fetch runbook for ImagePullFailed (matched_ru... | `fetch_runbook pod-imagepull-failed.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (20.5s)
   📤 → 下游数据: root_cause=主根因（影响48个Pod，L3 ImagePullFailed）：集群节点到 registry-1.docker.io:443 网络不可达。事件证据：(1) node2 代表 Pod dns-resolve-test 的6次 Failed 事件全部显示 i/o timeout 连接 registry-1.docker.io:443（IPs: 199.59.149.230, 108.160.165.139 等）；(2) node1 代表 Pod test-dns-1779360358 的 x119 次 Failed 事件显示 connection reset by peer（54.224.154.163:443）；(3) 涉及镜像涵盖 busybox:1.36.1、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0、alpine:3.18、curlimages/curl 等多个公共仓库，排除单个镜像问题；(4) Pod YAML 确认无 imagePullSecrets，镜像为公共仓库，排除认证失败。次要根因（影响1个Pod，L4 Co
... 截断，原始 776 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1/node2）到 Docker Hub 镜像仓库（registry-1.docker.io:443）的网络连接不稳定/不可达", "propagation": "kubelet 在 node1/node2 上尝试拉取所有 docker.io 公共镜像时，TCP 连接 registry-1.docker.io:443 失败（node1: connection reset by peer; node2: i/o timeout）→ 镜像拉取失败 → Pod 进入 ImagePullBackOff/ErrImagePull 状态", "direct_cause": "节点到 registry-1.docker.io:443 网络不可达（node2 持续超时）或不稳定（node1 被对端重置）", "manifestation": "48 个 Pod 分布在 default/aiops-e2e/mcp 命名空间，全部处于 ImagePullBackOff（26个）或 ErrImagePull（22个）状态"}
   rca_analysis={"phenomenon": "集群中存在3个异常组共50个异常Pod：主异常组g2（ImagePullFailed，48个Pod）在default/aiops-e2e/mcp命名空间处于ImagePullBackOff/ErrImagePull状态；次要异常组g1（CreateContainerConfigError，1个Pod rc-config-secret-key-missing在aiops-e2e）；次要异常组g3（StartError，1个Pod node-debugger-node1-nx8gb在mcp）。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe_rc-config-secret-key-missing", "content": "Pod rc-config-secret-key-missing: CreateContainerConfigError, 找不到key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml_rc-app-secret", "content": "Secret rc-app-secret type=Opaque, data_keys=[EXISTING_SECRET_KEY], 缺少APP_SECRET_TOKEN", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe_dns-resolve-test_node2", "content": "Pod dns-resolve-test on node2: 6次ErrImagePull事件, 全部i/o timeout dial registry-1.docker.io:443 (多IP)", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe_test-dns-1779360358_node1", "content": "Pod test-dns-1779360358 on node1: x119次Failed over 9h, connection reset by peer dial registry-1.docker.io:443", "reliability": "高"}, {"id": "e5", "source": "kubectl_events_default_mcp", "content": "跨namespace Events: node1 Pods显示connection reset by peer, node2 Pods显示i/o timeout, 均针对docker.io/library/busybox:1.36.1", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_yaml_test-dns-1779360358", "content": "Pod spec: imagePullSecrets=absent, 镜像busybox:1.36.1为公共镜像, 不需要认证", "reliability": "高"}, {"id": "e7", "source": "kubernetes_jq_query_49pods", "content": "49个ImagePullFailed Pod跨3命名空间, 镜像涉及busybox/registry.k8s.io/alpine/curlimages等公开仓库", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe_node-debugger-node1-nx8gb", "content": "Pod node-debugger-node1-nx8gb: StartError, exec: curl not found in $PATH, 使用busybox:1.36镜像但命令需要curl", "reliability": "高"}, {"id": "e9", "source": "kubectl_get_by_kind_in_cluster", "content": "当前异常Pod统计: ImagePullBackOff=26, ErrImagePull=22, CreateContainerConfigError=1, 分布在node1/node2", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret", "interpretation": "Pod rc-config-secret-key-missing 明确因 Secret 中缺少 APP_SECRET_TOKEN 键而无法创建容器配置"}, {"evidence_id": "e2", "raw_data": "data_keys: EXISTING_SECRET_KEY, 无APP_SECRET_TOKEN", "interpretation": "Secret rc-app-secret 确实只包含 EXISTING_SECRET_KEY，APP_SECRET_TOKEN 键根本不存在，确认配置缺失"}, {"evidence_id": "e3", "raw_data": "dial tcp 108.160.165.139:443: i/o timeout (x6次不同IP)", "interpretation": "node2 上所有拉取尝试均因对 registry-1.docker.io:443 的 TCP 连接超时而失败，说明 node2 到 docker.io 网络不可达"}, {"evidence_id": "e4", "raw_data": "read tcp 10.2.0.49:55574->54.224.154.163:443: read: connection reset by peer", "interpretation": "node1 能部分建立 TCP 连接，但被对端重置（RST），说明网络不稳定而非完全不可达"}, {"evidence_id": "e5", "raw_data": "node1: connection reset by peer; node2: i/o timeout", "interpretation": "两个节点表现不同但都指向 registry-1.docker.io:443 不可靠，跨命名空间所有 Pod 共享相同基础设施，排除单个 Pod 或命名空间配置问题"}, {"evidence_id": "e6", "raw_data": "imagePullSecrets: <absent>", "interpretation": "Pod 未配置 imagePullSecrets，且镜像 busybox 为公共镜像，排除认证失败场景"}, {"evidence_id": "e7", "raw_data": "49 Pods, 镜像涉及busybox/registry.k8s.io/alpine/curlimages", "interpretation": "跨多个公共镜像仓库的广泛拉取失败，进一步确认不是特定镜像问题而是通用网络层问题"}, {"evidence_id": "e8", "raw_data": "exec: \"curl\": executable file not found in $PATH", "interpretation": "Pod 使用 busybox:1.36 镜像但不包含 curl 命令，导致 StartError。此 Pod 为调试工具，与集群主故障无关"}, {"evidence_id": "e9", "raw_data": "ImagePullBackOff=26, ErrImagePull=22, CreateContainerConfigError=1", "interpretation": "确认主异常组 g2 占 48 个 Pod，配置问题 g1 占 1 个，StartError g3 占 1 个"}], "causal_chain": {"root_cause": "集群节点（node1/node2）到 Docker Hub 镜像仓库（registry-1.docker.io:443）的网络连接不稳定/不可达", "propagation": "kubelet 在 node1/node2 上尝试拉取所有 docker.io 公共镜像时，TCP 连接 registry-1.docker.io:443 失败（node1: connection reset by peer; node2: i/o timeout）→ 镜像拉取失败 → Pod 进入 ImagePullBackOff/ErrImagePull 状态", "direct_cause": "节点到 registry-1.docker.io:443 网络不可达（node2 持续超时）或不稳定（node1 被对端重置）", "manifestation": "48 个 Pod 分布在 default/aiops-e2e/mcp 命名空间，全部处于 ImagePullBackOff（26个）或 ErrImagePull（22个）状态"}, "root_cause": "主根因（影响48个Pod，L3 ImagePullFailed）：集群节点到 registry-1.docker.io:443 网络不可达。事件证据：(1) node2 代表 Pod dns-resolve-test 的6次 Failed 事件全部显示 i/o timeout 连接 registry-1.docker.io:443（IPs: 199.59.149.230, 108.160.165.139 等）；(2) node1 代表 Pod test-dns-1779360358 的 x119 次 Failed 事件显示 connection reset by peer（54.224.154.163:443）；(3) 涉及镜像涵盖 busybox:1.36.1、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0、alpine:3.18、curlimages/curl 等多个公共仓库，排除单个镜像问题；(4) Pod YAML 确认无 imagePullSecrets，镜像为公共仓库，排除认证失败。次要根因（影响1个Pod，L4 Co\n... 截断，原始 776 字符", "root_cause_summary": "主根因（影响48个Pod，L3 ImagePullFailed）：集群节点到 registry-1.docker.io:443 网络不可达。事件证据：(1) node2 代表 Pod dns-resolve-test 的6次 Failed 事件全部显示 i/o timeout 连接 registry-1.docker.io:443（IPs: 199.59.149.230, 108.160.165.139 等）；(2) node1 代表 Pod test-dns-1779360358 的 x119 次 Failed 事件显示 connection reset by peer（54.224.154.163:443）；(3) 涉及镜像涵盖 busybox:1.36.1、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0、alpine:3.18、curlimages/curl 等多个公共仓库，排除单个镜像问题；(4) Pod YAML 确认无 imagePullSecrets，镜像为公共仓库，排除认证失败。次要根因（影响1个Pod，L4 Co\n... 截断，原始 776 字符", "confidence": 0.95, "confidence_reason": "有直接事件证据（describe Pod 输出明确显示 i/o timeout 和 connection reset by peer）、有跨节点/跨命名空间一致性证据（49个Pod涉及多种镜像）、有排除性证据（YAML确认无imagePullSecrets排除认证问题），因果链完整清晰", "primary_runbooks": ["pod-imagepull-failed.md", "pod-config-error.md"], "alternative_causes": [{"cause": "镜像地址或 tag 不存在", "probability": "low", "reason": "涉及多种镜像和 tag（busybox:1.36.1 是已知有效镜像），且 Error 信息是网络超时/重置而非 'manifest unknown' 或 'not found'"}, {"cause": "imagePullSecret 缺失或认证失败", "probability": "low", "reason": "Pod YAML 确认无 imagePullSecrets，镜像为公共仓库（docker.io、registry.k8s.io），且错误信息是网络层错误而非 'unauthorized' 或 'denied'"}, {"cause": "私有仓库 DNS 解析失败", "probability": "low", "reason": "事件显示 TCP 连接已到达 registry-1.docker.io 的 IP 地址（多种IP），说明 DNS 解析成功，是后续 TCP 层失败"}], "limitations": "未在节点上直接执行 curl/wget 到 registry-1.docker.io:443 的节点级网络诊断（如 curl -v 或 ping 测试），当前证据均来自 Pod 层面的 kubelet 事件。未检查节点是否配置了代理/镜像仓库缓存（如 harbor mirror）。未确认是否是集群出口防火墙/代理配置问题。", "llm_raw_analysis": "## 证据清点\n上游已采集9组关键证据，涵盖所有3个异常组。\n\n## 逐条分析\n\n### 异常组g1 (CreateContainerConfigError) — rc-config-secret-key-missing\n- **e1/e2**：describe Pod 确认 waiting reason=CreateContainerConfigError, message='couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'。Secret YAML 确认只包含 EXISTING_SECRET_KEY，缺少 APP_SECRET_TOKEN。根因明确：Secret 键缺失。\n\n### 异常组g2 (ImagePullFailed) — 48个Pod 主故障\n- **e3**：node2 上 dns-resolve-test Pod 显示6次 i/o timeout 连接 registry-1.docker.io:443（不同IP），表明 node2 完全无法连接 Docker Hub。\n- **e\n... 截断，原始 1304 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 主根因（影响48个Pod，L3 ImagePullFailed）：集群节点到 registry-1.docker.io:443 网络不可达。事件证据：(1) node2 代表 Pod dns-resolve-test 的6次 Failed 事件全部显示 i/o timeout 连接 registry...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1/node2）到 Docker Hub 镜像仓库（registry-1.docker.io:443）的网络连接不稳定/不可达
     传导机制: kubelet 在 node1/node2 上尝试拉取所有 docker.io 公共镜像时，TCP 连接 registry-1.docker.io:443 失败（node1: connection reset by peer; node2: i/o timeout）→ 镜像拉取失败 → Pod 进入 ImagePullBackOff/ErrImagePull 状态
     最终表现: 48 个 Pod 分布在 default/aiops-e2e/mcp 命名空间，全部处于 ImagePullBackOff（26个）或 ErrImagePull（22个）状态


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (33.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 9478 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 20.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您提供的三个阶段的诊断结果生成的详尽诊断报告。

---
## 📊 诊断概览

**集群问题概要：**

您的集群当前存在 **49 个**异常 Pod，主要问题分为两类：

1.  **主要问题：镜像拉取失败 (影响 48 个 Pod)**
    *   **Pod异常状态**: `ImagePullBackOff` (26个) / `ErrImagePull` (22个)
    *   **兼容归因层**: L3 - 镜像拉取故障 (ImagePullFailed)
    *   **问题分类**: ImagePullFailed
    *   **置信度**: **高 (95%)**
    *   **证据完整度**: 8/8 (100%)

2.  **次要问题：配置错误 (影响 1 个 Pod)**
    *   **Pod异常状态**: `CreateContainerConfigError`
    *   **兼容归因层**: L4 - 配置错误 (ConfigError)
    *   **问题分类**: ConfigError
    *   **置信度**: **高 (95%)**
    *   **证据完整度**: 8/8 (100%)

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **受影响命名空间** | `default`, `mcp`, `aiops-e2e` |
| **受影响节点** | `node1` (IP 10.2.0.49), `node2` (IP 10.2.0.50) |
| **异常Pod总数** | 49 个 |
| **错误信息 (主要)** | `Failed to pull image "busybox:1.36.1": ... dial tcp ... i/o timeout` / `connection reset by peer` |
| **错误信息 (次要)** | `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | `kubectl_describe` Pod `dns-resolve-test` (default, node2) | `6 Warning Failed events (60m to 8m59s ago): ... dial tcp 199.59.149.230:443 i/o timeout`; `Normal BackOff x1306 over 9h` | 节点 `node2` 无法连接 Docker Hub (`registry-1.docker.io`)，网络超时导致 `ErrImagePull`。 |
| 2 | Pod 事件 | `kubectl_describe` Pod `test-dns-1779360358` (aiops-e2e, node1) | `Warning Failed x119 over 9h: ... dial tcp 54.224.154.163:443 connection reset by peer` | 节点 `node1` 连接 Docker Hub 不稳定，连接被远端重置导致 `ImagePullBackOff`。 |
| 3 | 集群事件 | `kubectl_events` (default, mcp, aiops-e2e 命名空间) | 所有命名空间中的镜像拉取失败事件均与 `busybox`, `alpine`, `curlimages/curl` 等公共仓库镜像相关，错误类型为 `i/o timeout` 或 `connection reset by peer`。 | 镜像拉取失败不是个别镜像的问题，而是集群到 Docker Hub 的整体网络问题。 |
| 4 | Pod YAML | `kubectl_get_yaml` Pod `test-dns-1779360358` | `imagePullSecrets: <none>`; `finalizers: <none>` | 排除了镜像拉取认证失败和 `finalizer` 残留导致 Pod 挂起的原因。 |
| 5 | Pod 状态 | `kubectl_describe` Pod `rc-config-secret-key-missing` (aiops-e2e) | `Reason: CreateContainerConfigError`; `Warning Failed x12 over 18m: ... couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | Pod 因引用的 Secret 中缺少指定 key 而无法启动。 |
| 6 | Secret YAML | `kubectl_get_yaml` Secret `rc-app-secret` (aiops-e2e) | `data_keys: EXISTING_SECRET_KEY`; 缺失 `APP_SECRET_TOKEN` 键 | 确认 Secret `rc-app-secret` 中不存在 `APP_SECRET_TOKEN` 这个键。 |
| 7 | Pod 状态 | `kubectl_describe` Pod `node-debugger-node1-nx8gb` (mcp) | `Reason: StartError`; `Exit Code: 128`; `Message: failed to create containerd task: OCI runtime create failed` | 该 Pod 由于 `OCI runtime` 错误导致启动失败，属于独立异常，与网络问题无关。 |
| 8 | 全局扫描 | `kubectl_get_by_kind_in_cluster` | `ImagePullBackOff=26`, `ErrImagePull=22`, `CreateContainerConfigError=1` | 明确了集群异常 Pod 的分布和精确数量。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：位于不同节点 (`node1`, `node2`)、不同命名空间 (`default`, `aiops-e2e`, `mcp`)、尝试拉取不同公共镜像 (`busybox`, `alpine`, `curlimages/curl`) 均失败，且错误类型均为网络层问题（`i/o timeout` 或 `connection reset`），强力证明了根因是**集群到外部容器镜像仓库（Docker Hub）的网络连接故障**。
- **证据 #5 + #6 印证**：Pod 报错 `CreateContainerConfigError` 与 Secret YAML 中 `APP_SECRET_TOKEN` 键的缺失完全对应，问题明确。
- **证据链**：节点网络不可达 → kubelet 镜像拉取失败 → 48个 Pod 卡在 `ImagePullBackOff`/`ErrImagePull`。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点级网络连通性测试（如 `curl -v https://registry-1.docker.io` 或 `ping 8.8.8.8`） | high | 未在节点上直接执行，无法精确判断是 DNS 解析、代理配置还是出口防火墙导致的问题。 |
| 节点级镜像仓库配置（如 `/etc/containerd/config.toml` 中的 `mirrors` 配置） | medium | 无法确认是否已配置镜像仓库缓存或代理，影响修复策略的选择。 |

---
## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ 集群节点（node1, node2）到外部容器镜像仓库（registry-1.docker.io:443）的     │
│ 网络连接不稳定/不可达（node1: connection reset, node2: i/o timeout）         │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ kubelet 在节点上尝试从 Docker Hub 拉取公共镜像（busybox, alpine 等）         │
│ TCP 连接到 registry-1.docker.io:443 失败，无法下载镜像层                     │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 镜像拉取失败（ImagePullFailure）                                             │
│ - node2: 持续超时（i/o timeout）                                            │
│ - node1: 连接被对端重置（connection reset by peer）                         │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ 48 个 Pod 分布在 default/mcp/aiops-e2e 命名空间，                            │
│ 全部处于 ImagePullBackOff（26个）或 ErrImagePull（22个）状态，持续重启。    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**次要问题因果链**：
```
┌──────────────────────────────────────────────────────────────┐
│ 根本原因                                                     │
│ Secret aiops-e2e/rc-app-secret 缺少 Pod 引用的 key          │
│ APP_SECRET_TOKEN                                              │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ 直接原因                                                     │
│ Pod rc-config-secret-key-missing 启动时无法找到所需的         │
│ Secret key，容器无法创建                                      │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                 │
│ Pod rc-config-secret-key-missing 状态为                       │
│ CreateContainerConfigError                                   │
└──────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论 1 (影响48个Pod，L3 ImagePullFailed)：** 根据证据 #1, #2, #3, #4，
问题的根本原因是**集群节点（node1, node2）到 Docker Hub 镜像仓库（`registry-1.docker.io:443`）的网络连接存在问题**。`node1` 侧表现为连接被对端重置 (`connection reset by peer`)，`node2` 侧表现为请求超时 (`i/o timeout`)，导致 kubelet 无法拉取公共镜像，所有依赖这些镜像的 Pod 均无法启动。
- **置信度**：**高 (95%)**
    - ✅ 多命名空间、多节点、多镜像的故障模式完全一致
    - ✅ Pod 事件错误信息明确指向 TCP 连接层故障
    - ✅ Pod YAML 已排除 imagePullSecrets 认证问题

**结论 2 (影响1个Pod，L4 ConfigError)：** 根据证据 #5, #6，
问题的根本原因是**Secret `aiops-e2e/rc-app-secret` 中缺少 Pod `rc-config-secret-key-missing` 引用的 `APP_SECRET_TOKEN` 键**。这属于配置管理错误。
- **置信度**：**高 (95%)**
    - ✅ 报错信息 (`couldn't find key APP_SECRET_TOKEN in Secret...`) 与工具查询 (`data_keys: EXISTING_SECRET_KEY`，缺失`APP_SECRET_TOKEN`) 完全吻合

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 解决网络问题 (镜像拉取失败)**
此问题为集群级配置问题，需在节点上操作。

**步骤一：排查并验证网络**
登录到 `node1` 和 `node2`，执行以下命令定位具体问题。
```bash
# 测试 DNS 解析
nslookup registry-1.docker.io

# 测试网络连通性 (注意：某些节点可能没有 curl)
curl -v --connect-timeout 10 https://registry-1.docker.io/v2/

# 检查代理设置
echo $HTTP_PROXY $HTTPS_PROXY $NO_PROXY

# 检查容器运行时配置 (如果使用 containerd)
cat /etc/containerd/config.toml | grep -A 10 "\[plugins.\"io.containerd.grpc.v1.cri\".registry.mirrors\]"
```
*依据*：需要区分是 DNS、防火墙还是代理问题，才能采取正确的解决方案。

**步骤二：根据排查结果修复**
常见的修复方案：
*   **配置 HTTP 代理**：如果集群有代理服务器，确保 kubelet 和 containerd 已正确配置代理。
*   **配置镜像仓库镜像 (Mirror)**：在 containerd 配置中添加可信的镜像仓库缓存（如 Harbor）或国内镜像加速器（如 `registry.docker-cn.com`）。
    *在 `/etc/containerd/config.toml` 中添加类似配置后，执行 `systemctl restart containerd`。*
*   **调整出口防火墙规则**：确保节点可以出站访问 `registry-1.docker.io` 等域名及其 IP 段。

**2. [次要] 修复 Secret 配置错误**
```bash
# 方式一：修复现有的 Secret，添加缺失的键
# 将 APP_SECRET_TOKEN 替换为实际的密钥值
kubectl patch secret rc-app-secret -n aiops-e2e -p '{"data":{"APP_SECRET_TOKEN":"'$(echo -n 'your-actual-secret-value' | base64)'"}}'

# 方式二（推荐）：重新创建或更新 Secret 的 YAML 文件并应用
# 1. 获取现有 Secret 并导出
kubectl get secret rc-app-secret -n aiops-e2e -o yaml > rc-app-secret.yaml
# 2. 编辑文件，在 data 字段下添加 APP_SECRET_TOKEN: <base64编码的值>
# 3. 应用修改
kubectl apply -f rc-app-secret.yaml
```
*依据*：证据 #6 明确了 Secret 缺少 key。

**3. [可选] 检查 StartError Pod**
使用 `kubectl describe pod node-debugger-node1-nx8gb -n mcp` 查看更详细的 OCI 错误信息，可能涉及容器运行时配置不兼容或镜像损坏问题。

### 后续优化
1.  **监控告警**：配置对 `ImagePullBackOff` 和 `Pod 状态` 的监控告警，以便在问题发生时第一时间感知。
2.  **节点级网络监控**：增加对集群节点到关键外部服务（如镜像仓库、对象存储）的网络连通性监控。
3.  **配置管理**：将 Secret 等关键配置纳入 GitOps 或 CI/CD 流程，防止手动配置错误。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 修复网络后验证 | `kubectl get pods --all-namespaces \| grep -E 'ImagePullBackOff\|ErrImagePull'` | 无输出，表明没有 Pod 处于镜像拉取失败状态。 |
| 2. 修复 Secret 后验证 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running 或 Completed |
| 3. 监控 Pod 状态 | `kubectl get pods --all-namespaces -w` | 所有异常 Pod 的 STATUS 应逐渐变为 `Running`。 |
| 4. 检查节点网络 | 在节点上再次执行 `curl -v --connect-timeout 10 https://registry-1.docker.io/v2/` | 返回 HTTP 2xx 响应。 |

---
## ⚠️ 注意事项
- **修正阶段总结**：问题定位阶段提到的 “`node-debugger-node1-nx8gb` 状态为 `StartError` (1个)” 是准确的。该 Pod 的 `Exit Code: 128` 和 `OCI runtime create failed` 错误与网络问题和 Secret 问题无关，属于另一个独立的 `OCI runtime` 异常，应单独排查。
- **优先级**：优先解决影响 48 个 Pod 的网络问题，这将恢复集群大部分功能。
- **操作风险**：修改 `containerd` 配置后需重启服务，会导致该节点上所有 Pod 重启。请选择在业务低峰期操作，或先处理一个不关键的节点。

---

## 📊 性能统计

├─ 总耗时: 2.3m
├─ 问题定位: 41.5s (29%) ✅
├─ 证据链采集: 45.2s (32%) ✅
├─ 根因分析: 20.5s (15%) ✅
├─ 汇总总结: 33.6s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 23 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-config-error
- **参考 Runbook**: pod-imagepull-failed, pod-config-error
- **工具调用**: 23 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
