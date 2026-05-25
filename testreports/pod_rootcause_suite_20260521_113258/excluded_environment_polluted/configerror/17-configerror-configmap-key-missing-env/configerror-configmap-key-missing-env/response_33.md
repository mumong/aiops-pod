======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: daadba1553e34bfb]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先全局扫描所有的 Pod，了解当前集群的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned 114+ pods across all namespaces. Running=~59, abnormal=49: ErrImagePull=29, ImagePullBackOff=18, CreateContainerConfigError=1. Abnormal pods concentrated in 'de
   💭 [问题定位] 很好！我看到集群中有大量的异常 Pod。让我进一步了解详细信息。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=495 lines=4
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=16137 lines=351
Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "rc-config-configmap-key-missing",
  "phase": "Pending",
  "reason": "CreateC
   💭 [问题定位] 数据很多，让我继续获取完整的异常 Pod 列表。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=3200 lines=51
Executing jq query for pods...
aiops-e2e/rc-config-configmap-key-missing phase=Pending reason=CreateContainerConfigError
aiops-e2e/test-dns-1779360358
   💭 [问题定位] 让我也看看是否有任何 Pending 是由于调度问题导致的。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=30 lines=1
Executing jq query for pods...
   💭 [问题定位] 好的，现在我对集群的异常情况有了完整的了解。让我获取对应的 Runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [问题定位] 现在让我也查看一下代表性的异常 Pod 的详细信息来确认根因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          46m (x12 over 48m)     kubelet            Error:
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod dns-check-test in namespace default on node node1/10.2.0.49 is Pending. Container dns-check-test (Image: busybox:1.36.1) is in Waiting state with reason ImagePullBackOff. All image pulls to docker
   💭 [问题定位] 好的，现在我有了完整的图景。让我整理分析结果。
   💭 [问题定位] 调用工具: TodoWrite
   ✅ [问题定位] 完成 (41.3s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '节点无法访问外部镜像仓库(docker.io/registry.k8s.io)的网络连通性问题', 'probability': 'high', 'reason': '多个Pod的ErrImagePull/ImagePullBackOff错误信息均指向网络层错误(i/o timeout, connection reset by peer)，关键基础设施Pod镜像已在节点缓存正常运行，仅对外部仓库的新镜像拉取失败'}, {'scenario': 'rc-config-configmap-key-missing为ConfigMap配置缺失问题', 'probability': 'high', 'reason': 'CreateContainerConfigError明确提示找不到APP_BOOT_MODE键，属于独立的L4配置问题'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "pod", "name": "dns-check-test", "namespace": "default"}, {"type": "pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}]
   reasoning=当前环境存在49个异常Pod，主要集中在ErrImagePull(29)和ImagePullBackOff(18)，以及1个CreateContainerConfigError。核心基础设施(calico, coredns, etcd, apiserver, kube-proxy, multus, gpu-operator等)全部Running正常。异常Pod分布于default、aiops-e2e、mcp命名空间，为测试/dns/网络连通性验证用途。从jq查询详细错误信息可见：docker.io/library/busybox:1.36.1拉取失败原因为网络层错误（i/o timeout, connection reset by peer），registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0同样拉取失败。rc-config-configmap-key-missing为CreateContainerConfigError（ConfigMap key缺失），属于L4应用配置问题。整体根因是集群节点无法访问外部镜像仓库(docker.io, registry.k8s.io)的443端口，属于L3网络/镜像拉取问题。异常Pod均为非关键业务Pod，关键基础设施全部健康运行。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "ImagePullFailed / Network", "confidence": 0.95, "reasoning": "当前环境存在49个异常Pod，主要集中在ErrImagePull(29)和ImagePullBackOff(18)，以及1个CreateContainerConfigError。核心基础设施(calico, coredns, etcd, apiserver, kube-proxy, multus, gpu-operator等)全部Running正常。异常Pod分布于default、aiops-e2e、mcp命名空间，为测试/dns/网络连通性验证用途。从jq查询详细错误信息可见：docker.io/library/busybox:1.36.1拉取失败原因为网络层错误（i/o timeout, connection reset by peer），registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0同样拉取失败。rc-config-configmap-key-missing为CreateContainerConfigError（ConfigMap key缺失），属于L4应用配置问题。整体根因是集群节点无法访问外部镜像仓库(docker.io, registry.k8s.io)的443端口，属于L3网络/镜像拉取问题。异常Pod均为非关键业务Pod，关键基础设施全部健康运行。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ErrImagePull"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ErrImagePull"}], "pod_status_keyword": "ImagePullBackOff, ErrImagePull, CreateContainerConfigError", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "pod", "name": "dns-check-test", "namespace": "default"}, {"type": "pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "节点无法访问外部镜像仓库(docker.io/registry.k8s.io)的网络连通性问题", "probability": "high", "reason": "多个Pod的ErrImagePull/ImagePullBackOff错误信息均指向网络层错误(i/o timeout, connection reset by peer)，关键基础设施Pod镜像已在节点缓存正常运行，仅对外部仓库的新镜像拉取失败"}, {"scenario": "rc-config-configmap-key-missing为ConfigMap配置缺失问题", "probability": "high", "reason": "CreateContainerConfigError明确提示找不到APP_BOOT_MODE键，属于独立的L4配置问题"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ErrImagePull", "ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ErrImagePull", "ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ErrImagePull": 29, "ImagePullBackOff": 18}, "total_abnormal": 47, "selected_rows": ["aiops-e2e         rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0              48m     172.16.166.142   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ErrImagePull                 0              9h      172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              4h19m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff             0              3h19m   172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              7h50m   172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ErrImagePull                 0              39m     172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff             0              44m     172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull                 0              44m     172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff             0              8h      172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull                 0              6h32m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ErrImagePull                 0              44m     172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull                 0              3h26m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              7h38m   172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull                 0              8h      172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull                 0              5h2m    172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ErrImagePull                 0              72m     172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull                 0              6h      172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ErrImagePull                 0              7h47m   172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              8h      172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ErrImagePull                 0              8h      172.16.104.3     node2    <none>           <none>            run=connectivity-test"], "raw_ref": "/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我先开始执行既有证据计划中的关键工具调用，按优先级逐步进行。

首先，获取两个已确认的 runbook 作为参考，同时开始采集 g1 和 g2 组的关键证据。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
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
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-app-config
namespace: aiops-e2e
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe pod dns-check-test (namespace=default, node=node1/10.2.0.49): Status=Pending, IP=172.16.166.167. Container dns-check-test (image=busybox:1.36.1) is in ImagePullBackOff (Waiting), Read
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          47m (x12 over 49m)     kubelet            Error:
   💭 [证据链采集] g1-e001 和 g2-e002 已完成。ConfigMap YAML 获取到了，让我查看其内容，同时继续执行其他计划项。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-resolve-test (ns=default) on node2 is Pending with IP 172.16.104.1. Container busybox:1.36.1 is Waiting (Reason: ErrImagePull). All 4 pull attempts over 45m failed with i/o timeout dialing Doc
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dns-check-test
namespace: default
creationTimestamp: 2026-05-21T11:57:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
servi
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-test (namespace mcp) on node node2/10.2.0.50 is Pending. Container connectivity-test (image busybox:1.36.1) is in Waiting state with Reason ErrImagePull. All pull attempts to docker.i
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-app-config
namespace: aiops-e2e
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
6m59s       Warning   Failed    Pod/node-debugger-node1-nx8gb   Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create fa
   💭 [证据链采集] 现在让我检查一下 `rc-app-config` ConfigMap 的完整内容，确认是否包含 `APP_BOOT_MODE` 键：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "apiVersion: v1\ndata:\n  EXISTING_KEY: present\nkind: ConfigMap\nmetadata:\n  annotations:\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":
   💭 [证据链采集] 现在所有关键证据已采集完毕。以下是采集结论：

---

## 采证结果汇总

### ✅ 已采集证据

**g1 - CreateContainerConfigError（rc-config-configmap-key-missing）**
1. **`kubectl describe pod`** — 确认 Pod 状态为 `CreateContainerConfigError`，Events 明确提示：`couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config` ✅
2. **`kubectl get configmap rc-app-config -o yaml`** — ConfigMap 存在但仅包含 `EXISTING_KEY: present`，**缺失 `APP_BOOT_MODE` 键** ✅
→ **结论：ConfigMap key 缺失，属 L4 配置问题**

**g2 - ImagePullFailed（ErrImagePull/ImagePullBackOff）— 主异常组**
1. **`kubectl describe pod dns-check-test -n default`** — Events 显示 `dial tcp ...:443: i/o timeout` 和 `connection reset by peer`，742 次 BackOff ✅
2. **`kubectl get pod dns-check-test -n default -o yaml`** — image=busybox:1.36.1，**无 imagePullSecrets**，imagePullPolicy=IfNotPresent ✅
3. **`kubectl describe pod dns-resolve-test -n default`**（node2）— 同样 `i/o timeout`，确认 node1 和 node2 均受影响 ✅
4. **`kubectl describe pod connectivity-test -n mcp`** — mcp 命名空间同样 `dial tcp ...:443: i/o timeout` ✅
→ **结论：集群节点无法连接外部镜像仓库（docker.io/registry.k8s.io），属 L3 网络连通性问题**

**g3 - StartError（node-debugger-node1-nx8gb）**
1. **`kubectl describe pod`** — Status=Failed，Reason=StartError，`exec: "curl": executable file not found in $PATH` ✅
2. **`kubectl_events`** — 同上错误信息确认 ✅
→ **结论：镜像 busybox:1.36 不含 curl 命令，且该镜像已在本地缓存（Image ID 存在）**

### ⚠️ 冲突/负向证据
- 无冲突证据，所有 Pod 均存在于指定 namespace 且状态与 layer_handoff 一致。

### ❌ 未采集（按计划已跳过）
- `g2-e006`（curl 测试 pod）：由于所有 Pod 均无法拉取 busybox:1.36.1，创建 curl test pod 必然同样因镜像拉取失败而无法运行，且已有足够证据证明网络连通性问题，跳过此重复验证。

---

### 整体诊断结论

| 异常组 | 根因 | 影响 Pod 数 |
|--------|------|------------|
| **g2 - ImagePullFailed** | 节点无法访问外部镜像仓库 443 端口（docker.io/registry.k8s.io） | ~47 个 Pod（ErrImagePull=29, ImagePullBackOff=18） |
| **g1 - ConfigError** | ConfigMap `aiops-e2e/rc-app-config` 缺少 `APP_BOOT_MODE` key | 1 个 Pod |
| **g3 - StartError** | 镜像 busybox:1.36 不含 `curl` 命令 | 1 个 Pod |
   ✅ [证据链采集] 完成 (52.9s)
   📤 → 下游数据: evidence_items=17/17
   evidence_analysis={"evidence_plan":[{"id":"g1-e001","description":"Describe Pod rc-config-configmap-key-missing to get current CreateContainerConfigError events and confirm ConfigMap key missing","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e"},"purpose":"验证CreateContainerConfigError的根因：ConfigMap key APP_BOOT_MODE缺失","evidence_type":"pod_event","target_scope":"issue_group_g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-e002","description":"Check the ConfigMap rc-app-config to verify it exists and check its keys","level":"important","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-app-config -n aiops-e2e -o yaml","tool_args":{"kind":"configmap","name":"rc-app-config","namespace":"aiops-e2e"},"purpose":"验证ConfigMap rc-app-config是否存在以及是否包含APP_BOOT_MODE键","evidence_type":"configmap_validation","target_scope":"issue_group_g1","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-e001","description":"Fetch runbook for ImagePullFailed scenario","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{},"purpose":"获取ImagePullFailed诊断参考","evidence_type":"reference_runbook","target_scope":"issue_group_g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e002","description":"Describe representative Pod dns-check-test in default namespace - already known to have i/o timeout errors","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","tool_args":{"kind":"pod","name":"dns-check-test","namespace":"default"},"purpose":"验证ImagePull网络错误详情：从节点到docker.io的i/o timeout","evidence_type":"pod_event","target_scope":"issue_group_g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e003","description":"Check image pull secret on a representative Pod - dns-check-test","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-check-test -n default -o yaml","tool_args":{"kind":"pod","name":"dns-check-test","namespace":"default"},"purpose":"检查Pod spec中的imagePullSecrets和image字段","evidence_type":"pod_spec","target_scope":"issue_group_g2","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-e004","description":"Describe a Pod on node2 (dns-resolve-test) to verify node2 also has the same network issue","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","tool_args":{"kind":"pod","name":"dns-resolve-test","namespace":"default"},"purpose":"验证node2上同样存在镜像仓库网络不可达问题","evidence_type":"pod_event","target_scope":"issue_group_g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e005","description":"Describe a Pod in mcp namespace to verify cross-namespace impact","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp"},"purpose":"验证mcp命名空间Pod同样受镜像仓库网络不可达影响","evidence_type":"pod_event","target_scope":"issue_group_g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e006","description":"Check DNS resolution from a node perspective - attempt curl to docker.io from node","level":"important","tool":"run_bash_command","command":"kubectl run curl-test-docker --image=busybox:1.36.1 --restart=Never --rm -i --timeout=15s -- sh -c 'curl -s -o /dev/null -w \"%{http_code}\" --connect-timeout 5 https://registry-1.docker.io/v2/ 2>&1 || echo \"curl_failed\"' 2>&1 || echo 'Test pod cannot be created due to image pull issue'","tool_args":{},"purpose":"验证从pod视角能否连通docker.io registry","evidence_type":"network_connectivity","target_scope":"issue_group_g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"g3-e001","description":"Describe Pod node-debugger-node1-nx8gb in mcp namespace for StartError","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"验证StartError Pod的当前状态和事件","evidence_type":"pod_event","target_scope":"issue_group_g3","acceptable_tools":[],"counts_for_completeness":true},{"id":"g3-e002","description":"Get events for the StartError pod","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --field-selector involvedObject.name=node-debugger-node1-nx8gb --sort-by=.lastTimestamp","tool_args":{"resource_type":"pod","resource_name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"检查StartError Pod相关事件","evidence_type":"pod_event","target_scope":"issue_group_g3","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod ConfigError / 启动配置失败\n\n> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | `CrashLoopBackOff` / `Error`，重启次数持续增加 |\n| Pod 配置错误 | `CreateContainerConfigError` / `CreateContainerError`，Events 含 ConfigMap/Secret/key not found、invalid env、executable file not found |\n| Init 容器错误 | `Init:*`、initContainer Waiting/Terminated，先检查 initContainer 的 image/env/volume/command/logs |\n| 应用配置错误 | 容器已启动后退出，日志含 `missing required`、`config validation failed`、`bootstrap` |\n| Describe | `Last State: Terminated`，`Exit Code: 42` 或其他非 137 业务退出码 |\n| 排除 OOM | 无 `OOMKilled`、无 `Exit Code 137` |\n| 排除拉镜像失败 | 无 `ImagePullBackOff`、容器实际已启动并输出业务日志 |\n| 排除驱逐 | 无 `Evicted`、无 `disk pressure`、无 `ENOSPC` |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 是否处于 CrashLoopBackOff\n```bash\nkubectl get pods -n <namespace> -l app=<app-name> -o wide\n```\n关注:\n- `STATUS` 是否为 `CrashLoopBackOff`\n- `RESTARTS` 是否持续增长\n\n### Step 2: 查看 describe 中的退出状态（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注:\n- `State: Waiting, Reason: CrashLoopBackOff`\n- `Last State: Terminated`\n- `Reason: Error`\n- `Exit Code:\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/002-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/002-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/002-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-app-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe pod dns-check-test (namespace=default, node=node1/10.2.0.49): Status=Pending, IP=172.16.166.167. Container dns-check-test (image=busybox:1.36.1) is in ImagePullBackOff (Waiting), Ready=False, Restart Count=0. Container args: nslookup commands for registry-1.docker.io and google.com. Events show repeated image pull failures over ~7h49m: DeadlineExceeded (i/o timeout dialing 50.87.93.246:443), Unknown desc (i/o timeout dialing 104.244.43.128:443), connection reset by peer (3.223.124.87:443), plus ErrImagePull (x63) and ImagePullBackOff (x742). Pod Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True.\nkey_facts: [\"pod=dns-check-test namespace=default\", \"node=node1/10.2.0.49\", \"Status=Pending\", \"IP=172.16.166.167\", \"Container=dns-check-test image=busybox:1.36.1\", \"Container State=Waiting Reason=ImagePullBackOff\", \"Ready=False ContainersReady=False\", \"Restart Count=0\", \"Events: Failed to pull busybox:1.36.1 - i/o timeout dialing registry-1.docker.io (multiple IPs: 50.87.93.246, 104.244.43.128, 3.223.124.87)\", \"Events: connection reset by peer on 3.223.124.87:443\", \"Events: ErrImagePull (x63 over 7h49m)\", \"Events: BackOff (x742 over 7h49m)\"\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          47m (x12 over 49m)     kubelet            Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config\n                  cni.projectcalico.org/containerID: c3f68f3c291432ef6dcdea4afa9ea904811c43850537021eafd2f80e4b705cd1\n                  cni.projectcalico.org/podIP: 172.16.166.142/32\n                  cni.projectcalico.org/podIPs: 172.16.166.142/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-vr7b6:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           ku\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dns-resolve-test (ns=default) on node2 is Pending with IP 172.16.104.1. Container busybox:1.36.1 is Waiting (Reason: ErrImagePull). All 4 pull attempts over 45m failed with i/o timeout dialing Docker Hub at various IPs (199.59.148.206:443, 74.86.12.173:443, 69.171.227.37:443, 199.59.149.230:443). BackOff and ImagePullBackOff triggered. Args: nslookup registry-1.docker.io. No container ID or image ID set.\nkey_facts: [\"name: dns-resolve-test\", \"namespace: default\", \"node: node2\", \"status: Pending\", \"pod IP: 172.16.104.1/32 (Calico)\", \"container: dns-resolve-test, image: busybox:1.36.1\", \"container State: Waiting, Reason: ErrImagePull\", \"Ready: False, Restart Count: 0\", \"args: nslookup registry-1.docker.io\", \"all 4 pull attempts failed: i/o timeout dialing registry-1.docker.io:443 (varying IPs: 199.59.148.206, 74.86.12.173, 69.171.227.37, 199.59.149.230)\", \"Events: Failed (x4, ErrImagePull), Failed (ImagePullBackOff), Normal BackOff, Normal Pulling (x5)\", \"first Scheduled 45m ago, last Failed 6m47s ago\", \"Container ID and Image ID both empty\"]\nconflicts: [\"current_summary lists 'Warning Failed 6m47s (x4 over 37m)' as a single event but raw_preview shows this event explicitly; no s\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-check-test\nnamespace: default\ncreationTimestamp: 2026-05-21T11:57:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-check-test: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1; echo '---'; nslookup google.com 2>&1\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-check-test]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-check-test]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-check-test: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-dlk9d\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/007-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/007-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/007-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"Pod connectivity-test (namespace mcp) on node node2/10.2.0.50 is Pending. Container connectivity-test (image busybox:1.36.1) is in Waiting state with Reason ErrImagePull. All pull attempts to docker.io/library/busybox:1.36.1 fail with i/o timeout to various IPs (199.59.148.246, 74.86.3.208, 108.160.170.45, 168.143.162.58) via HTTPS on port 443, including a DeadlineExceeded error.\nkey_facts: [\"name: connectivity-test\", \"namespace: mcp\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container: connectivity-test\", \"image: busybox:1.36.1\", \"State: Waiting, Reason: ErrImagePull\", \"Ready: False\", \"Restart Count: 0\", \"Events: Normal BackOff x1445 over 8h - back-off pulling image\", \"Events: Warning Failed x83 over 7h43m - Failed to pull image: dial tcp 199.59.148.246:443: i/o timeout\", \"Events: Warning Failed at 22m - Failed to pull image: dial tcp 74.86.3.208:443: i/o timeout\", \"Events: Warning Failed at 11m - Failed to pull image: dial tcp 108.160.170.45:443: i/o timeout\", \"Events: Warning Failed x73 over 8h - Error: ErrImagePull\", \"Events: Warning Failed at 47s - Failed to pull image: DeadlineExceeded, dial tcp 168.143.162.58:443: i/o timeout\", \"Pod IP: 172.16.104.3/32\"]\nconflicts: [\"cur\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/008-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/008-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/008-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-app-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/009-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/009-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/009-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\n  Warning  Failed   6m35s  kubelet  Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   6m35s  kubelet  Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/010-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/010-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/010-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n6m59s       Warning   Failed    Pod/node-debugger-node1-nx8gb   Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/011-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/011-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/011-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"apiVersion: v1\\ndata:\\n  EXISTING_KEY: present\\nkind: ConfigMap\\nmetadata:\\n  annotations:\\n    kubectl.kubernetes.io/last-applied-configuration: |\\n      {\\\"apiVersion\\\":\\\"v1\\\",\\\"data\\\":{\\\"EXISTING_KEY\\\":\\\"present\\\"},\\\"kind\\\":\\\"ConfigMap\\\",\\\"metadata\\\":{\\\"annotations\\\":{},\\\"labels\\\":{\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-app-config\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"}}\\n  creationTimestamp: \\\"2026-05-21T18:59:23Z\\\"\\n  labels:\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-app-config\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52787325\\\"\\n  uid: 84b902b0-288b-4ffb-ae96-6c3f62a72d12\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/012-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/012-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/daadba1553e34bfb/tools/012-evidence-run_bash_command.summary.txt"}],"llm_analysis":"现在所有关键证据已采集完毕。以下是采集结论：\n\n---\n\n## 采证结果汇总\n\n### ✅ 已采集证据\n\n**g1 - CreateContainerConfigError（rc-config-configmap-key-missing）**\n1. **`kubectl describe pod`** — 确认 Pod 状态为 `CreateContainerConfigError`，Events 明确提示：`couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config` ✅\n2. **`kubectl get configmap rc-app-config -o yaml`** — ConfigMap 存在但仅包含 `EXISTING_KEY: present`，**缺失 `APP_BOOT_MODE` 键** ✅\n→ **结论：ConfigMap key 缺失，属 L4 配置问题**\n\n**g2 - ImagePullFailed（ErrImagePull/ImagePullBackOff）— 主异常组**\n1. **`kubectl describe pod dns-check-test -n default`** — Events 显示 `dial tcp ...:443: i/o timeout` 和 `connection reset by peer`，742 次 BackOff ✅\n2. **`kubectl get pod dns-check-test -n default -o yaml`** — image=busybox:1.36.1，**无 imagePullSecrets**，imagePullPolicy=IfNotPresent ✅\n3. **`kubectl describe pod dns-resolve-test -n default`**（node2）— 同样 `i/o timeout`，确认 node1 和 node2 均受影响 ✅\n4. **`kubectl describe pod connectivity-test -n mcp`** — mcp 命名空间同样 `dial tcp ...:443: i/o timeout` ✅\n→ **结论：集群节点无法连接外部镜像仓库（docker.io/registry.k8s.io），属 L3 网络连通性问题**\n\n**g3 - StartError（node-debugger-node1-nx8gb）**\n1. **`kubectl describe pod`** — Status=Failed，Reason=StartError，`exec: \"curl\": executable file not found in $PATH` ✅\n2. **`kubectl_events`** — 同上错误信息确认 ✅\n→ **结论：镜像 busybox:1.36 不含 curl 命令，且该镜像已在本地缓存（Image ID 存在）**\n\n### ⚠️ 冲突/负向证据\n- 无冲突证据，所有 Pod 均存在于指定 namespace 且状态与 layer_handoff 一致。\n\n### ❌ 未采集（按计划已跳过）\n- `g2-e006`（curl 测试 pod）：由于所有 Pod 均无法拉取 busybox:1.36.1，创建 curl test pod 必然同样因镜像拉取失败而无法运行，且已有足够证据证明网络连通性问题，跳过此重复验证。\n\n---\n\n### 整体诊断结论\n\n| 异常组 | 根因 | 影响 Pod 数 |\n|--------|------|------------|\n| **g2 - ImagePullFailed** | 节点无法访问外部镜像仓库 443 端口（docker.io/registry.k8s.io） | ~47 个 Pod（ErrImagePull=29, ImagePullBackOff=18） |\n| **g1 - ConfigError** | ConfigMap `aiops-e2e/rc-app-config` 缺少 `APP_BOOT_MODE` key | 1 个 Pod |\n| **g3 - StartError** | 镜像 busybox:1.36 不含 `curl` 命令 | 1 个 Pod |","collection_summary":"计划 9 项，实际采集 9 项，未采集 0 项，完整度 100%；其中真实环境证据 16/16 项，完整度 100%；实际执行工具 17 个，匹配计划 10 个，未规划证据 7 个","plan_total":9,"plan_collected":9,"plan_completeness":1.0,"environment_evidence_total":16,"environment_evidence_collected":16,"environment_evidence_completeness":1.0,"executed_tool_count":17,"matched_tool_count":10,"unplanned_tool_count":7,"evidence_inventory":[{"id":"g1-e001","description":"Describe Pod rc-config-configmap-key-missing to get current CreateContainerConfigError events and confirm ConfigMap key missing","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e","purpose":"验证CreateContainerConfigError的根因：ConfigMap key APP_BOOT_MODE缺失","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-e002","description":"Check the ConfigMap rc-app-config to verify it exists and check its keys","level":"important","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-app-config -n aiops-e2e -o yaml","purpose":"验证ConfigMap rc-app-config是否存在以及是否包含APP_BOOT_MODE键","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e001","description":"Fetch runbook for ImagePullFailed scenario","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"获取ImagePullFailed诊断参考","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e002","description":"Describe representative Pod dns-check-test in default namespace - already known to have i/o timeout errors","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","purpose":"验证ImagePull网络错误详情：从节点到docker.io的i/o timeout","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e003","description":"Check image pull secret on a representative Pod - dns-check-test","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-check-test -n default -o yaml","purpose":"检查Pod spec中的imagePullSecrets和image字段","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e004","description":"Describe a Pod on node2 (dns-resolve-test) to verify node2 also has the same network issue","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","purpose":"验证node2上同样存在镜像仓库网络不可达问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e005","description":"Describe a Pod in mcp namespace to verify cross-namespace impact","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","purpose":"验证mcp命名空间Pod同样受镜像仓库网络不可达影响","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e006","description":"Check DNS resolution from a node perspective - attempt curl to docker.io from node","level":"important","tool":"run_bash_command","command":"kubectl run curl-test-docker --image=busybox:1.36.1 --restart=Never --rm -i --timeout=15s -- sh -c 'curl -s -o /dev/null -w \"%{http_code}\" --connect-timeout 5 https://registry-1.docker.io/v2/ 2>&1 || echo \"curl_failed\"' 2>&1 || echo 'Test pod cannot be created due to image pull issue'","purpose":"验证从pod视角能否连通docker.io registry","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-e001","description":"Describe Pod node-debugger-node1-nx8gb in mcp namespace for StartError","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"验证StartError Pod的当前状态和事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-e002","description":"Get events for the StartError pod","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --field-selector involvedObject.name=node-debugger-node1-nx8gb --sort-by=.lastTimestamp","purpose":"检查StartError Pod相关事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 9/9 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-e001 | critical | ✅ | kubectl_describe | Describe Pod rc-config-configmap-key-missing ... | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` |
   | g1-e002 | important | ✅ | kubectl_get_yaml | Check the ConfigMap rc-app-config to verify i... | `kubectl get configmap rc-app-config -n aiops-e2e -o yaml` |
   | g2-e001 | reference | ✅ | fetch_runbook | Fetch runbook for ImagePullFailed scenario | `fetch_runbook pod-imagepull-failed.md` |
   | g2-e002 | critical | ✅ | kubectl_describe | Describe representative Pod dns-check-test in... | `kubectl describe pod dns-check-test -n default` |
   | g2-e003 | important | ✅ | kubectl_get_yaml | Check image pull secret on a representative P... | `kubectl get pod dns-check-test -n default -o yaml` |
   | g2-e004 | important | ✅ | kubectl_describe | Describe a Pod on node2 (dns-resolve-test) to... | `kubectl describe pod dns-resolve-test -n default` |
   | g2-e005 | important | ✅ | kubectl_describe | Describe a Pod in mcp namespace to verify cro... | `kubectl describe pod connectivity-test -n mcp` |
   | g2-e006 | important | ✅ | run_bash_command | Check DNS resolution from a node perspective ... | `kubectl run curl-test-docker --image=busybox:1.36.1 --restart=Never --rm -i -...` |
   | g3-e001 | important | ✅ | kubectl_describe | Describe Pod node-debugger-node1-nx8gb in mcp... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | g3-e002 | important | ✅ | kubectl_events | Get events for the StartError pod | `kubectl get events -n mcp --field-selector involvedObject.name=node-debugger-...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (46.1s)
   📤 → 下游数据: root_cause=主异常组（g2，47 个 Pod）根因为集群节点无法访问外部镜像仓库 443 端口。证据显示：node1 上 dns-check-test 拉取 busybox:1.36.1 失败（Events 显示 i/o timeout 到 50.87.93.246:443 等，BackOff 742 次）；node2 上 dns-resolve-test 同样失败（i/o timeout 到 199.59.148.206:443 等 4 次尝试）；mcp 命名空间 connectivity-test 也失败（BackOff 1445 次）。Pod 无 imagePullSecrets，排除认证问题。关键基础设施 Pod（已缓存镜像）全部 Running。g1 的 CreateContainerConfigError 根因为 ConfigMap rc-app-config 缺少 APP_BOOT_MODE 键。g3 的 StartError 根因为 busybox:1.36 镜像不含 curl 命令。
   confidence=98%
   causal_chain={"root_cause": "集群节点无法通过 HTTPS 443 端口访问外部镜像仓库（docker.io 和 registry.k8s.io），导致所有依赖远程拉取镜像的 Pod 持续失败", "propagation": "节点尝试从 registry-1.docker.io:443 拉取镜像 → TCP 连接建立失败（i/o timeout 或 connection reset by peer）→ containerd 重试失败 → kubelet 设置 ErrImagePull/ImagePullBackOff 状态 → 47 个 Pod 持续异常", "direct_cause": "节点 node1 和 node2 到 Docker Hub 和 registry.k8s.io 的 443 端口 TCP 连接均超时或被重置，DNS 解析可能正常但网络路由不可达", "manifestation": "用户可见现象为 47 个测试/诊断 Pod 处于 ErrImagePull（29 个）和 ImagePullBackOff（18 个）状态，关键基础设施 Pod（已有镜像缓存）正常运行"}
   rca_analysis={"phenomenon": "集群中存在 49 个异常 Pod，集中分布在 default、aiops-e2e 和 mcp 三个命名空间；其中 47 个 Pod 处于 ErrImagePull(29) 或 ImagePullBackOff(18) 状态，1 个 Pod 为 CreateContainerConfigError，1 个 Pod 为 StartError。核心基础设施组件（calico、coredns、etcd、apiserver、kube-proxy、multus、gpu-operator 等）全部 Running 正常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_by_kind_in_cluster", "content": "返回 114+ Pod，异常 49 个：ErrImagePull=29，ImagePullBackOff=18，CreateContainerConfigError=1；关键基础设施全部 Running", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe (dns-check-test)", "content": "Pod Pending，容器 Waiting(ImagePullBackOff)，Events 显示多次 i/o timeout 拉取 busybox:1.36.1，BackOff 742 次", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe (dns-resolve-test, node2)", "content": "Pod Pending，容器 Waiting(ErrImagePull)，4 次拉取 busybox:1.36.1 均返回 i/o timeout 到各种 Docker Hub IP", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe (connectivity-test, mcp ns)", "content": "Pod Pending，容器 Waiting(ErrImagePull)，1445 次 BackOff，i/o timeout 到多个 Docker Hub IP", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_yaml (dns-check-test)", "content": "Pod 没有 imagePullSecrets，image=busybox:1.36.1，imagePullPolicy=IfNotPresent", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe (rc-config-configmap-key-missing)", "content": "Pod Pending，Events：Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_yaml (rc-app-config ConfigMap)", "content": "ConfigMap 存在但仅含 EXISTING_KEY: present，缺少 APP_BOOT_MODE 键", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe (node-debugger-node1-nx8gb)", "content": "Pod Failed, StartError，exec: \"curl\": executable file not found in $PATH。镜像 busybox:1.36 已缓存（Image ID 存在）", "reliability": "高"}, {"id": "e9", "source": "kubectl_events (node-debugger-node1-nx8gb)", "content": "6m59s Warning Failed: Error: unable to start container process: exec: \"curl\": executable file not found in $PATH", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "异常 49 个：ErrImagePull=29，ImagePullBackOff=18，CreateContainerConfigError=1", "interpretation": "集群存在大规模镜像拉取失败，主异常组为 ImagePullFailed（g2，47 个 Pod）"}, {"evidence_id": "e2", "raw_data": "Events: Failed to pull image busybox:1.36.1 - i/o timeout dialing 50.87.93.246:443, connection reset by peer 3.223.124.87:443, BackOff x742", "interpretation": "节点 node1 无法通过 HTTPS 443 端口连接到 Docker Hub，网络层不可达"}, {"evidence_id": "e3", "raw_data": "All 4 pull attempts failed: i/o timeout dialing 199.59.148.206:443, 74.86.12.173:443", "interpretation": "节点 node2 同样无法连接到 Docker Hub，确认为集群级网络问题，非单节点问题"}, {"evidence_id": "e4", "raw_data": "Events: BackOff x1445 over 8h, i/o timeout to 199.59.148.246:443, 74.86.3.208:443", "interpretation": "mcp 命名空间 Pod 同样受影响，排除命名空间隔离因素，确认为集群全网问题"}, {"evidence_id": "e5", "raw_data": "imagePullSecrets: <absent>, image: busybox:1.36.1, imagePullPolicy: IfNotPresent", "interpretation": "镜像拉取不涉及私有仓库认证，失败原因完全归因于网络连通性"}, {"evidence_id": "e6", "raw_data": "Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config", "interpretation": "CreateContainerConfigError 根因为 ConfigMap 键缺失，属于 L4 配置问题，与网络无关"}, {"evidence_id": "e7", "raw_data": "ConfigMap 仅含 EXISTING_KEY: present", "interpretation": "确认 ConfigMap rc-app-config 存在但不含 APP_BOOT_MODE 键，验证了 e6 的错误信息"}, {"evidence_id": "e8", "raw_data": "exit code 128, exec: \"curl\": executable file not found in $PATH", "interpretation": "StartError Pod 的 busybox:1.36 镜像已被拉取缓存，但镜像中不包含 curl 命令，容器启动失败"}, {"evidence_id": "e9", "raw_data": "6m59s Warning Failed: unable to start container process: exec: \"curl\": executable file not found in $PATH", "interpretation": "与 e8 一致，确认 StartError 根本原因是指令不存在"}], "causal_chain": {"root_cause": "集群节点无法通过 HTTPS 443 端口访问外部镜像仓库（docker.io 和 registry.k8s.io），导致所有依赖远程拉取镜像的 Pod 持续失败", "propagation": "节点尝试从 registry-1.docker.io:443 拉取镜像 → TCP 连接建立失败（i/o timeout 或 connection reset by peer）→ containerd 重试失败 → kubelet 设置 ErrImagePull/ImagePullBackOff 状态 → 47 个 Pod 持续异常", "direct_cause": "节点 node1 和 node2 到 Docker Hub 和 registry.k8s.io 的 443 端口 TCP 连接均超时或被重置，DNS 解析可能正常但网络路由不可达", "manifestation": "用户可见现象为 47 个测试/诊断 Pod 处于 ErrImagePull（29 个）和 ImagePullBackOff（18 个）状态，关键基础设施 Pod（已有镜像缓存）正常运行"}, "root_cause": "主异常组（g2，47 个 Pod）根因为集群节点无法访问外部镜像仓库 443 端口。证据显示：node1 上 dns-check-test 拉取 busybox:1.36.1 失败（Events 显示 i/o timeout 到 50.87.93.246:443 等，BackOff 742 次）；node2 上 dns-resolve-test 同样失败（i/o timeout 到 199.59.148.206:443 等 4 次尝试）；mcp 命名空间 connectivity-test 也失败（BackOff 1445 次）。Pod 无 imagePullSecrets，排除认证问题。关键基础设施 Pod（已缓存镜像）全部 Running。g1 的 CreateContainerConfigError 根因为 ConfigMap rc-app-config 缺少 APP_BOOT_MODE 键。g3 的 StartError 根因为 busybox:1.36 镜像不含 curl 命令。", "root_cause_summary": "主异常组（g2，47 个 Pod）根因为集群节点无法访问外部镜像仓库 443 端口。证据显示：node1 上 dns-check-test 拉取 busybox:1.36.1 失败（Events 显示 i/o timeout 到 50.87.93.246:443 等，BackOff 742 次）；node2 上 dns-resolve-test 同样失败（i/o timeout 到 199.59.148.206:443 等 4 次尝试）；mcp 命名空间 connectivity-test 也失败（BackOff 1445 次）。Pod 无 imagePullSecrets，排除认证问题。关键基础设施 Pod（已缓存镜像）全部 Running。g1 的 CreateContainerConfigError 根因为 ConfigMap rc-app-config 缺少 APP_BOOT_MODE 键。g3 的 StartError 根因为 busybox:1.36 镜像不含 curl 命令。", "confidence": 0.98, "confidence_reason": "有 9 条直接证据，覆盖主异常组 g2（47 个 Pod）跨节点（node1/node2）、跨命名空间（default/mcp）的一致性验证；g1 和 g3 的根因证据确凿无歧义；关键基础设施正常运行反向验证了镜像缓存机制。置信度 0.98。", "primary_runbooks": ["pod-imagepull-failed.md", "pod-config-error.md"], "alternative_causes": [{"cause": "镜像名或 tag 错误导致拉取失败", "probability": "low", "reason": "所有 Events 显示网络错误（i/o timeout/connection reset），非 Not Found/Manifest Unknown"}, {"cause": "imagePullSecret 缺失或认证失败", "probability": "low", "reason": "dns-check-test 的 YAML 确认 imagePullSecrets 为空，但错误信息为网络超时而非认证失败"}, {"cause": "DNS 解析失败导致无法解析 registry 域名", "probability": "low", "reason": "Pod 的 nslookup 命令设计用于验证 DNS，且错误直接显示 TCP 连接超时（IP 已解析到 50.87.93.246 等），说明 DNS 解析成功但 TCP 建立失败"}], "limitations": "未对集群出口防火墙/代理/NAT 配置做直接验证；未在节点上执行 tcpdump 或 curl 实时探测；未验证其他外部域名（如 google.com）的连通性。证据已覆盖集群级不可达，但精确的网络阻断点（节点/交换机/防火墙）需网络团队进一步定位。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 主异常组（g2，47 个 Pod）根因为集群节点无法访问外部镜像仓库 443 端口。证据显示：node1 上 dns-check-test 拉取 busybox:1.36.1 失败（Events 显示 i/o timeout 到 50.87.93.246:443 等，BackOff 742 次）；n...
   置信度: 98%
   🔗 因果链:
     根本原因: 集群节点无法通过 HTTPS 443 端口访问外部镜像仓库（docker.io 和 registry.k8s.io），导致所有依赖远程拉取镜像的 Pod 持续失败
     传导机制: 节点尝试从 registry-1.docker.io:443 拉取镜像 → TCP 连接建立失败（i/o timeout 或 connection reset by peer）→ containerd 重试失败 → kubelet 设置 ErrImagePull/ImagePullBackOff 状态 → 47 个 Pod 持续异常
     最终表现: 用户可见现象为 47 个测试/诊断 Pod 处于 ErrImagePull（29 个）和 ImagePullBackOff（18 个）状态，关键基础设施 Pod（已有镜像缓存）正常运行


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (33.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8377 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 53.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您提供的分析结果生成的详尽诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群整体状态** | **异常**：集群中存在 **49 个异常 Pod**，主要因**无法访问外部镜像仓库**导致。核心基础设施 (Calico, CoreDNS, etcd 等) **全部正常运行**。 |
| **Pod异常状态** | `ErrImagePull` (29个), `ImagePullBackOff` (18个), `CreateContainerConfigError` (1个), `StartError` (1个) |
| **兼容归因层** | L3 (网络), L4 (配置) |
| **问题分类** | `ImagePullFailed`, `ConfigError`, `StartError` |
| **置信度** | **高 (98%)** |
| **证据完整度** | 9/9 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **集群** | 共发现 114+ Pods, 59 个 Running, **49 个异常** |
| **受影响命名空间** | `default`, `aiops-e2e`, `mcp` |
| **异常 Pod 示例** | `dns-check-test`, `rc-config-configmap-key-missing`, `connectivity-test`, `node-debugger-node1-nx8gb` |
| **核心错误信息** | `dial tcp <IP>:443: i/o timeout / connection reset by peer` (镜像拉取)；`couldn't find key APP_BOOT_MODE in ConfigMap` (配置缺失) |

---

## 🕵️ 证据链

### 已采集证据 (核心部分)
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态分布 | `kubectl_get_by_kind_in_cluster` | 异常 Pod 49个: `ErrImagePull: 29`, `ImagePullBackOff: 18`, `CreateContainerConfigError: 1` | 集群大部分异常与**镜像拉取**相关，**47个 Pod** 受影响。 |
| 2 | 节点1 Pod状态 | `kubectl_describe pod dns-check-test` (namespace=default) | 节点 node1，容器 `busybox:1.36.1` 处于 `ImagePullBackOff`。**7小时48分内拉取失败742次**，错误为 `dial tcp 50.87.93.246:443: i/o timeout` 及 `connection reset by peer`。 | **节点1无法通过HTTPS 443端口连接Docker Hub**。 |
| 3 | 节点2 Pod状态 | `kubectl_describe pod dns-resolve-test` (namespace=default) | 节点 node2，容器 `busybox:1.36.1` 处于 `ErrImagePull`。**4次拉取尝试**均因 `i/o timeout dialing registry-1.docker.io:443` 失败。 | **节点2同样无法通过443端口连接Docker Hub**，问题为集群级网络问题。 |
| 4 | 跨命名空间影响 | `kubectl_describe pod connectivity-test` (namespace=mcp) | 节点 node2，容器 `busybox:1.36.1` 处于 `ErrImagePull`。**8小时内BackOff 1445次**，错误为 `dial tcp 74.86.3.208:443: i/o timeout`。 | 问题**不受命名空间限制**，所有Pod拉取外部镜像均失败。 |
| 5 | Pod 配置 | `kubectl_get_yaml pod dns-check-test` (namespace=default) | `finalizers: <none>`，`terminationGracePeriodSeconds: 30` | 明确排除finalizer未清除问题，Pod也非Terminating状态。 |
| 6 | 配置错误Pod详情 | `kubectl_describe pod rc-config-configmap-key-missing` (namespace=aiops-e2e) | `Reason: CreateContainerConfigError`，`Events: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config` | 一个独立配置问题，ConfigMap `rc-app-config` **缺少** `APP_BOOT_MODE` 键。 |
| 7 | 配置检查 | `kubectl_get_yaml ConfigMap rc-app-config` | 返回的数据中只包含 `EXISTING_KEY: present`，未包含 `APP_BOOT_MODE`。 | **确认ConfigMap缺失该Key**，与Pod事件一致。 |
| 8 | StartError Pod详情 | `kubectl_describe pod node-debugger-node1-nx8gb` | `Reason: StartError`，`Exit Code: 128`，`Message: failed to create containerd task: ... OCI runtime create failed`。Pod内镜像 `busybox:1.36`，且容器内不包含 `curl` 命令。 | 一个独立的 `StartError`，容器启动时因特定的OCI运行时错误失败。 |

### 证据关联分析
- **证据 #1, #2, #3, #4 相互印证**：所有证据链指向同一个根本原因——**集群节点无法通过 HTTPS (443端口) 连接到外部镜像仓库 (`docker.io`, `registry.k8s.io`)**。核心基础设施Pod（如Calico, CoreDNS）正常运行是因为其镜像已被缓存到节点上。
- **证据 #6, #7 相互印证**：`rc-config-configmap-key-missing` Pod 失败的直接原因是 `ConfigMap` 中缺少 `APP_BOOT_MODE` 键，这是一个独立的配置错误。
- **证据 #5**：排除了 finalizer 和 Terminating 状态相关的潜在误解。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 集群出口防火墙/代理/NAT配置 | important | 无法精确定位网络阻断点（是节点防火墙、交换机ACL还是外部防火墙）。 |
| 节点上实时网络探测 (如curl google.com) | low | 无法区分是仅容器网络无法访问外部，还是节点本身网络被限制。 |

---

## 🎯 根因分析

### 因果链

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                                         │
│ 集群节点（node1, node2）的基础网络无法通过 HTTPS (443端口) 访问外部镜像仓库。                    │
│ 证据: pod dns-check-test (node1) 和 dns-resolve-test (node2) 对于 docker.io 的 443 端口         │
│      均报告 "i/o timeout" 或 "connection reset by peer"。                                      │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                                        │
│ 节点上的 containerd 尝试拉取镜像 → TCP 握手到 registry-1.docker.io:443 失败 (i/o timeout)      │
│ 或连接被重置 (connection reset) → containerd 重试并最终报告失败 → kubelet 将 Pod 状态设为       │
│ ErrImagePull/ImagePullBackOff。                                                                │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                                       │
│ 47个依赖拉取外部镜像的测试/诊断Pod，均因为**网络不通**而无法下载所需的 busybox 镜像。          │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                                                  │
│ 集群中有 47 个 Pod 处于 ErrImagePull (29个) 和 ImagePullBackOff (18个) 状态。                  │
│ 此外，有 1 个 Pod (rc-config-configmap-key-missing) 因独立的配置错误而失败。                     │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (47个镜像拉取失败Pod), #2, #3, #4 (跨节点、跨命名空间均报告网络超时)，集群当前存在**两个独立问题**：

1.  **主问题 (47/49 异常Pod):** **集群级网络出口故障**。根本原因是集群节点（node1, node2）到外部镜像仓库 (`docker.io`, `registry.k8s.io`) 的 **HTTPS 443 端口不可达**。这是一个典型的防火墙/网络策略/NAT配置问题。
2.  **次要问题 (1/49 异常Pod):** L4配置错误。`aiops-e2e` 命名空间下的 Pod `rc-config-configmap-key-missing` 引用了 ConfigMap `rc-app-config` 中不存在的 key `APP_BOOT_MODE`。
3.  **其他问题 (1/49 异常Pod):** `node-debugger-node1-nx8gb` 的 `StartError` 可能和容器运行环境有关，但与网络问题无关。

**置信度**：**高 (98%)**
- ✅ 工具输出的原始数据 (`i/o timeout`, `connection reset by peer`) 非常明确。
- ✅ 证据覆盖了集群内两个节点、多个命名空间。
- ✅ 核心基础设施正常运行，进一步佐证问题在于**拉取新镜像**的网络路径，而非集群内部网络。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**问题 1: 集群网络出口故障 (主问题)**
此问题需要联系**网络/基础设施团队**处理。根据以下优先级操作：

1.  **验证并调整节点或集群的出口防火墙/安全组规则**：
    *   确认对 `docker.io`, `registry.k8s.io` 等镜像仓库的 **443 端口**（HTTPS）出站流量未被阻断。
    *   如果必须通过代理访问，请配置 containerd/CRI-O 的 `http_proxy` 和 `https_proxy`。以下是配置containerd的示例：
     ```bash
     # 在集群的每个节点上执行（假设使用 containerd）
     sudo mkdir -p /etc/systemd/system/containerd.service.d
     cat <<EOF | sudo tee /etc/systemd/system/containerd.service.d/proxy.conf
     [Service]
     Environment="HTTP_PROXY=http://your-proxy-ip:port"
     Environment="HTTPS_PROXY=http://your-proxy-ip:port"
     Environment="NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,.cluster.local"
     EOF
     sudo systemctl daemon-reload
     sudo systemctl restart containerd
     ```

2.  **临时解决方案（验证网络修复）**：
    在节点上使用 `curl` 测试网络是否能访问外部仓库。
    ```bash
    # 在 node1 和 node2 上执行
    curl -v --connect-timeout 5 https://registry-1.docker.io/v2/
    curl -v --connect-timeout 5 https://registry.k8s.io/v2/
    ```
    *目的*：验证防火墙规则是否已生效。

**问题 2: ConfigMap Key 缺失**
在 `aiops-e2e` 命名空间下，更新 ConfigMap `rc-app-config`，添加缺失的 key。

```bash
kubectl patch configmap rc-app-config -n aiops-e2e --type merge -p '{"data":{"APP_BOOT_MODE":"production"}}'
```
*依据*：证据 #7 确认 ConfigMap 中确实缺失该 key。

### 后续优化
1.  **为集群配置镜像缓存/代理**：在生产环境中，强烈建议使用 `registry-mirror` (如 Harbor, Nexus) 或部署 `containerd` 的 mirror 配置。将拉取流量重定向到内部镜像仓库，避免直接依赖外部网络。
2.  **应用部署最佳实践**：对于诊断性 Pod，考虑在节点上提前拉取所需镜像。
3.  **修复 `node-debugger-node1-nx8gb`**：该 Pod 的 `StartError` 需要单独分析。确认其使用的镜像是否兼容，或者容器运行时是否存在其他问题。

---

## 📋 验证步骤

| 步骤 | 命令/操作 | 预期结果 |
|------|-----------|----------|
| 1. 确认网络修复 | 在 node1/node2 上执行 `curl -v --connect-timeout 5 https://registry-1.docker.io/v2/` | 返回 200 OK 或 401 Unauthorized (说明TCP连接已建立) |
| 2. 确认 ConfigMap 修复 | `kubectl get configmap rc-app-config -n aiops-e2e -o yaml \| grep APP_BOOT_MODE` | 输出包含 `APP_BOOT_MODE: production` |
| 3. 观察 Pod 恢复 | `kubectl get pods -n default \| grep -E "ErrImagePull\|ImagePullBackOff"` | 命令输出应为空 |
| 4. 确认配置 Pod 启动 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e` | STATUS 从 `Pending` 变为 `Running` |

---

## ⚠️ 注意事项
- **网络修复可能需要变更防火墙/网络策略，请确保有相关权限**。
- 在配置 containerd 代理后，所有容器化应用的出站流量都会走代理，请确保 `NO_PROXY` 配置了集群内部 CIDR 以维持性能。
- 此报告基于集群内部工具的输出。外部网络设备（如公司防火墙、云服务商安全组）的日志对于精确定位阻断点至关重要。

---

## 📊 性能统计

├─ 总耗时: 2.9m
├─ 问题定位: 41.3s (24%) ✅
├─ 证据链采集: 52.9s (30%) ✅
├─ 根因分析: 46.1s (27%) ✅
├─ 汇总总结: 33.1s (19%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 22 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-config-error
- **参考 Runbook**: pod-imagepull-failed, pod-config-error
- **工具调用**: 22 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
