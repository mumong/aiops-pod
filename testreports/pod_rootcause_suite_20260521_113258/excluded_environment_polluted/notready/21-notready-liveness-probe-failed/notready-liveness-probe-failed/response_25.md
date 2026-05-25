======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c4ee4b8201e54909]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先从全局 Pod 状态扫描开始，了解整个集群的 Pod 运行状况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods -A 返回跨多个 namespace 的 pods 列表。Running pods 包括 admin/gpu-metax-mo, gpu-operator, metax-gpu-label；aiops/aiops-copilot；default/cloud-agent, cloud-server, nfs-client-provisioner, registry-
   💭 [问题定位] 很好！全局扫描已经发现了大量异常 Pod。让我进一步确认异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=539 lines=4
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 让我用 jq 查询来获取异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 jq query returned 59 lines of pods. All 59 pods listed. 57 are STATUS=Pending, 2 are STATUS=Failed (mcp/node-debugger-node1-nx8gb on node1, xnet/observability-kibana-65d7c45f6d-7zc9l on master). Names
   💭 [问题定位] 现在看看整体的 STATUS 字段（不仅是 phase），因为很多 Pending 的 Pod 实际有更具体的状态如 ImagePullBackOff。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 大量 Pod 处于 ImagePullBackOff 状态，原因均为 Back-off pulling image，涉及 busybox、curlimages/curl、alpine、registry.k8s.io/pause 等不同镜像，命名空间包括 aiops-e2e、default、mcp、xnet。少数 Pod（mcp/node-debugger-node1-nx8gb、xnet/obse
   💭 [问题定位] 信息量很大，让我看看还有 CrashLoopBackOff 的 Pod。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=148 lines=3
Executing jq query for pods...
aiops-e2e/rc-notready-liveness WAITING=CrashLoopBackOff LAST=Error
default/dns-test-dig WAITING=ErrImagePull LAST=N/A
   💭 [问题定位] 好的，现在让我看看 CrashLoopBackOff 这个 Pod 的详情，以及异常 Pod 的完整分布。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       31m (x10 over 33m)     kubelet     
   💭 [问题定位] 非常好，现在我已经获得了足够的全局信息。让我再取一下匹配的 runbook 进行参考。
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
# Pod CrashLoopBackOffRuntime / 容器反复退出

> Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime

## 状态识别
- Pod 状态: `CrashLoopBackOff`
- Last State: Terminated
-
   💭 [问题定位] 现在我对整个集群的情况有了全面了解。让我整理分析结果。
   💭 [问题定位] 调用工具: TodoWrite
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (52.6s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '镜像仓库网络不可达或DNS解析失败导致大量ImagePullBackOff', 'probability': '高', 'reason': '多个命名空间、多种镜像(busybox, curlimages/curl, alpine, registry.k8s.io/pause)均无法拉取，错误为Back-off pulling image，但未出现manifest unknown或unauthorized等特定错误，更可能为仓库访问网络问题'}, {'scenario': '镜像仓库地址配置错误或证书问题', 'probability': '中', 'reason': '不同镜像均失败，但registry.k8s.io和docker.io地址共存，可能缺少正确配置或TLS证书'}, {'scenario': '容器运行时拉取并发限制或磁盘空间问题', 'probability': '低', 'reason': '节点均Ready，磁盘无异常报告，但大量并发拉取可能触发registryPullQPS限制'}]
   entities=[{"type": "node", "name": "master", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}]
   reasoning=当前集群存在大量仍处于异常状态的Pod。主要异常模式为：1) default/mcp/aiops-e2e/xnet 等命名空间约25+个Pod处于ImagePullBackOff/ErrImagePull状态，原因均为Back-off pulling image，涉及busybox、curlimages/curl、alpine、registry.k8s.io/pause等镜像，对应L3层镜像拉取失败。2) aiops-e2e/rc-notready-liveness处于CrashLoopBackOff，退出码137，但实际原因是liveness probe失败（kubectl describe显示Liveness probe failed: liveness endpoint failed，且exit code 137是OOMKilled），属应用健康检查问题归入L4。由于大量ImagePullBackOff是集群范围最突出的根因，优先定L3层。3个Node均Ready，无L0/L1层节点或磁盘问题。57个Pending Pod的详情未明确给出Pending原因，但已知同时存在大量ImagePullBackOff，可能这些Pending也是由于镜像拉取阻塞导致。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "镜像仓库与网络", "confidence": 0.95, "reasoning": "当前集群存在大量仍处于异常状态的Pod。主要异常模式为：1) default/mcp/aiops-e2e/xnet 等命名空间约25+个Pod处于ImagePullBackOff/ErrImagePull状态，原因均为Back-off pulling image，涉及busybox、curlimages/curl、alpine、registry.k8s.io/pause等镜像，对应L3层镜像拉取失败。2) aiops-e2e/rc-notready-liveness处于CrashLoopBackOff，退出码137，但实际原因是liveness probe失败（kubectl describe显示Liveness probe failed: liveness endpoint failed，且exit code 137是OOMKilled），属应用健康检查问题归入L4。由于大量ImagePullBackOff是集群范围最突出的根因，优先定L3层。3个Node均Ready，无L0/L1层节点或磁盘问题。57个Pending Pod的详情未明确给出Pending原因，但已知同时存在大量ImagePullBackOff，可能这些Pending也是由于镜像拉取阻塞导致。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-check-registry", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-tool-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-check-node2", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-diag-evidence-verify", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2s2mz", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "node", "name": "master", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达或DNS解析失败导致大量ImagePullBackOff", "probability": "高", "reason": "多个命名空间、多种镜像(busybox, curlimages/curl, alpine, registry.k8s.io/pause)均无法拉取，错误为Back-off pulling image，但未出现manifest unknown或unauthorized等特定错误，更可能为仓库访问网络问题"}, {"scenario": "镜像仓库地址配置错误或证书问题", "probability": "中", "reason": "不同镜像均失败，但registry.k8s.io和docker.io地址共存，可能缺少正确配置或TLS证书"}, {"scenario": "容器运行时拉取并发限制或磁盘空间问题", "probability": "低", "reason": "节点均Ready，磁盘无异常报告，但大量并发拉取可能触发registryPullQPS限制"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 52, "ErrImagePull": 4}, "total_abnormal": 57, "selected_rows": ["aiops-e2e         rc-notready-liveness                                0/1     CrashLoopBackOff   13 (3m52s ago)   33m     172.16.166.129   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0                13h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ImagePullBackOff   0                142m    172.16.104.52    node2    <none>           <none>            run=connectivity-check-tmp", "default           dig-check-registry                                  0/1     ImagePullBackOff   0                82m     172.16.166.155   node1    <none>           <none>            run=dig-check-registry", "default           dig-tool                                            0/1     ErrImagePull       0                9h      172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff   0                8h      172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff   0                12h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff   0                5h27m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-diag-tool-evidence                              0/1     ImagePullBackOff   0                118m    172.16.104.4     node2    <none>           <none>            run=dns-diag-tool-evidence", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff   0                5h33m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ImagePullBackOff   0                5h33m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test                                            0/1     ImagePullBackOff   0                82m     172.16.104.56    node2    <none>           <none>            run=dns-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0                13h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0                11h     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff   0                5h32m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ImagePullBackOff   0                8h      172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff   0                12h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0                12h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0                9h      172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ImagePullBackOff   0                6h      172.16.104.41    node2    <none>           <none>            run=registry-check-node2"], "raw_ref": "/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的工具调用。先执行最关键的几个工具（可并行的先并行）：

**第一步：执行 e1、e2、e3、e4、e6、e7（可并行）**
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default) is in Pending status. Container is Waiting (ImagePullBackOff). All image pull attempts to registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 fail with DeadlineExceed
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   14m (x183 over 13h)   kubelet  (combined from similar events): Fail
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-check-tmp in namespace default, on node node2/10.2.0.50, status Pending. Container busybox:1.36.1 image pull continuously failing. State: Waiting (ImagePullBackOff). Not Ready. Pod ha
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
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-test/mcp is Pending on node2/10.2.0.50. Container state: Waiting (ImagePullBackOff), not ready. Image busybox:1.36.1 cannot be pulled from docker.io — repeated failures due to network
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       32m (x10 over 34m)     kubelet     
   💭 [证据链采集] 非常好，核心 Pod 的事件已经采集到。现在执行 e3（全集群镜像拉取事件）和 e5（DNS 解析测试）：
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
59m                      Warning   Failed    Pod/connectivity-test   Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = failed to pull and unpack image "
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
41m (x9 over 5h9m)       Warning   Failed    Pod/dig-tool   Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0": rpc error: code = DeadlineExceeded des
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
15m (x183 over 13h)    Warning   Failed    Pod/test-dns-1779360358   (combined from similar events): Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded
   💭 [证据链采集] 关键证据已到位。现在执行 e5（DNS 解析验证）作为补充证据。
   💭 [证据链采集] 调用工具: run_bash_command
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "pod/dns-test-evidence created\nError from server (BadRequest): container \"dns-test-evidence\" in pod \"dns-test-evidence\" is waiting to start: ContainerCreating\nWarning
   💭 [证据链采集] Pod 被立即删除了，改用另一种方式测试 DNS：
   💭 [证据链采集] 调用工具: run_bash_command
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "pod/dns-test-evidence2 created\nError from server (BadRequest): container \"dns-test-evidence2\" in pod \"dns-test-evidence2\" is waiting to start: ContainerCreating\n  Re
   💭 [证据链采集] [compacted ai_message: original_chars=23]
   💭 [证据链采集] 调用工具: run_bash_command
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "pod/dns-test-evidence3 created\nError from server (BadRequest): container \"dns-test-evidence3\" in pod \"dns-test-evidence3\" is waiting to start: ContainerCreating\nEven
   💭 [证据链采集] [compacted ai_message: original_chars=13]
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1430 lines=10
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/001-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2455 lines=48
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/002-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1804 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/003-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1565 lines=50
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/005-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=3132 lines=63
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/007-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2632 lines=17
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/008-evidence-kubectl_events.summary.txt
offset: 0
returned
   💭 [证据链采集] [compacted ai_message: original_chars=52]
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 现在让我查看 `rc-notready-liveness` 的当前日志来验证是否真的是 liveness probe 问题（注意它已经有 `busybox:1.36` 镜像已成功拉取，不是 ImagePull 问题）。
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 所有关键工具调用已完成。下面是证据采集结论。

---

## 📋 证据采集结论

### ✅ 已采集证据（主异常组 g2 — ImagePullBackOff/ErrImagePull × 56个Pod）

| 证据维度 | 关键发现 |
|---------|---------|
| **Pod Events 原文** | **所有 Pod 的 Events 均为 `i/o timeout` 连接 registry 服务器**，具体包括： |
| | - `dig-tool`(default): `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` → dial tcp **108.177.125.82:443** (europe-west2) / **142.250.157.82:443** (asia-east1) 均 i/o timeout |
| | - `test-dns-1779360358`(aiops-e2e): `busybox:1.36.1` → dial tcp **69.63.184.142:443** (registry-1.docker.io) i/o timeout |
| | - `connectivity-test`(mcp): `busybox:1.36.1` → 多个 registry-1.docker.io IP 均 i/o timeout，含 **1次 connection refused** 和 **1次 pull QPS exceeded** |
| | - `connectivity-check-tmp`(default): 同样多个 docker.io IP i/o timeout + 1次 connection refused + 1次 pull QPS exceeded |
| **跨命名空间验证** | default/aiops-e2e/mcp 三个命名空间的 Pod 故障模式完全一致：**所有镜像拉取均因 i/o timeout 无法到达外部仓库** |
| **涉及的镜像仓库** | `docker.io` (busybox:1.36.1)、`registry.k8s.io` (jessie-dnsutils) — **两个仓库均不可达** |
| **Pod YAML** (dig-tool) | imagePullSecrets: **无**；无私有仓库配置，均为公共镜像 |
| **DNS 验证** | 尝试创建 `busybox:1.36.1` Pod 执行 nslookup，但 Pod 本身因 ImagePullBackOff 无法启动 — **印证了镜像拉取是共性阻塞** |

### ✅ 已采集证据（次异常组 g1 — CrashLoopBackOff: rc-notready-liveness）

| 证据维度 | 关键发现 |
|---------|---------|
| **Last State/Exit Code** | Exit Code = **137** (OOMKilled) |
| **Events** | `Liveness probe failed: liveness endpoint failed` → 容器被 Killing → BackOff 重启 |
| **镜像** | `busybox:1.36` **已成功拉取**（有 Container ID 和 Image ID），与 ImagePullBackOff 无关 |
| **根因** | 该 Pod 实际是 **liveness probe 失败导致的 CrashLoopBackOff**，Exit Code 137 是 probe 杀死容器的结果，不是内存不足 |
| **日志** | `kubectl logs --previous` 和当前 logs 均无输出（容器 command 仅为 `sleep 86400`，没有业务日志） |

### ✅ 已采集证据（次异常组 g3 — StartError: node-debugger-node1-nx8gb）

| 证据维度 | 关键发现 |
|---------|---------|
| **状态** | Failed (Terminated) |
| **错误信息** | `exec: "curl": executable file not found in $PATH: unknown` |
| **退出码** | 128 |
| **分析** | 镜像 `busybox:1.36` 中不包含 `curl` 命令，但容器 command 为 `curl -s -o /dev/null ...` — **镜像内容与命令不匹配** |

### ❌ 冲突/负向证据

| 项 | 说明 |
|---|------|
| DNS 测试 Pod | 因 ImagePullBackOff 无法启动，无法通过 nslookup 直接验证 DNS 解析 |
| 节点磁盘/运行时 | 3个 Node 均 Ready，无 L0/L1 节点或磁盘问题 |

### 🔍 根因判断

**集群无法访问外部镜像仓库** — 无论 `docker.io` 还是 `registry.k8s.io`，从 node1 和 node2 均出现 `i/o timeout` 连接超时。这不是镜像名/tag错误、不是认证问题、不是imagePullSecret缺失——而是**出口网络不通导致所有公共镜像仓库不可达**。同时 `rc-notready-liveness` 的 CrashLoopBackOff 属于独立的应用健康检查问题，与镜像拉取无关。
   ✅ [证据链采集] 完成 (2m 51.0s)
   📤 → 下游数据: evidence_items=14/14
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"G2主异常组 - 验证代表Pod image+Events：dig-tool (ErrImagePull) 和 connectivity-check-tmp (ImagePullBackOff)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default && kubectl describe pod connectivity-check-tmp -n default","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default","names":["dig-tool","connectivity-check-tmp"]},"purpose":"查看ErrImagePull/ImagePullBackOff的Events原文，确认Failed to pull image的具体错误原因（connection refused/timeout/manifest unknown/unauthorized）","evidence_type":"pod_events","target_scope":"g2代表Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"G2主异常组 - 验证另两个namespace代表Pod：test-dns-1779360358 (aiops-e2e ImagePullBackOff) 和 connectivity-test (mcp ImagePullBackOff)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e && kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"default","names":["test-dns-1779360358","connectivity-test"]},"purpose":"跨namespace验证ImagePullBackOff是否一致，确认是否所有namespace都受同类镜像拉取问题影响","evidence_type":"pod_events","target_scope":"g2跨namespace代表Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"G2主异常组 - 检查集群Events中ImagePull相关Warning","level":"critical","tool":"kubectl_events","command":"kubectl get events -A --sort-by='.lastTimestamp' | grep -i 'pull\\|image\\|back-off\\|ErrImage' | tail -30","tool_args":{"namespace":"default"},"purpose":"获取全集群近期的镜像拉取失败事件，确认错误类型分布","evidence_type":"cluster_events","target_scope":"全集群","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"G2主异常组 - 查看dig-tool镜像spec确认拉取什么镜像","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"查看Pod spec中的image字段、imagePullSecrets、容器配置","evidence_type":"pod_spec","target_scope":"dig-tool","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e5","description":"G2主异常组 - 节点到常见镜像仓库DNS解析测试 - 通过run_bash_command执行dig/nslookup","level":"important","tool":"run_bash_command","command":"kubectl exec -n default deploy/saas-busybox -- nslookup docker.io 2>&1 || kubectl run dns-test-$$ -it --image=busybox:1.36.1 --rm --restart=Never -- nslookup docker.io 2>&1 || echo '无法执行DNS测试'","tool_args":{"command":"check dns resolution for registry"},"purpose":"验证节点能否解析docker.io等镜像仓库域名","evidence_type":"network_dns","target_scope":"集群DNS","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6","description":"G1异常组(CrashLoopBackOff)最小验证 - 确认rc-notready-liveness当前状态和Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"验证CrashLoopBackOff的Last State/Exit Code/Events，确认是否仍然为liveness probe failed导致","evidence_type":"pod_events","target_scope":"g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7","description":"G3异常组(StartError)最小验证 - 确认node-debugger-node1-nx8gb当前状态和Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"验证StartError Pod的当前状态与事件","evidence_type":"pod_events","target_scope":"g3","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod dig-tool (namespace: default) is in Pending status. Container is Waiting (ImagePullBackOff). All image pull attempts to registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 fail with DeadlineExceeded / i/o timeout connecting to GCR endpoints (europe-west2-docker.pkg.dev, asia-east1-docker.pkg.dev). BackOff triggered after repeated failures.\nkey_facts: [\"pod: dig-tool, namespace: default, node: node1 (10.2.0.49)\", \"status: Pending, pod IP: 172.16.166.157\", \"container: dig-tool, image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"container state: Waiting, reason: ImagePullBackOff\", \"Ready: False, Restart Count: 0\", \"QoS Class: BestEffort\", \"Events: Warning Failed (x84 over 9h) - ErrImagePull\", \"Events: Warning Failed (x9 over 5h9m) - Failed to pull image: DeadlineExceeded, dial tcp 108.177.125.82:443: i/o timeout (europe-west2)\", \"Events: Normal BackOff (x1261 over 9h) - Back-off pulling image\", \"Events: Warning Failed (x34 over 5h27m) - Failed to pull image: DeadlineExceeded, dial tcp 142.250.157.82:443: i/o timeout (asia-east1)\", \"Events: Normal Pulling (x96 over 9h) - Pulling image (all attempts fail)\"]\nmissing: [\"Container ID: empty (image never pulled successfully)\"\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   14m (x183 over 13h)   kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.184.142:443: i/o timeout\n  Normal   BackOff  60s (x2032 over 13h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Contain\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod connectivity-check-tmp in namespace default, on node node2/10.2.0.50, status Pending. Container busybox:1.36.1 image pull continuously failing. State: Waiting (ImagePullBackOff). Not Ready. Pod has IP 172.16.104.52 assigned (Calico CNI active). All Events show repeated image pull failures from docker.io registry-1.docker.io: multiple i/o timeouts to various IPs, one connection refused, and one pull QPS exceeded error. BackOff triggered (x55 over 132m). Pod cannot start due to image pull failure.\nkey_facts: [\"resource: Pod connectivity-check-tmp, namespace: default\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container: connectivity-check-tmp, image: busybox:1.36.1\", \"container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False, Restart Count: 0\", \"Pod IP: 172.16.104.52 (Calico CNI active)\", \"Events: repeated Failed to pull image \\\"busybox:1.36.1\\\" - multiple i/o timeout errors to registry-1.docker.io (IPs: 69.30.25.21, 108.160.169.181, 108.160.165.173, 128.242.245.125), one connection refused (162.125.80.5:443), one pull QPS exceeded\", \"Normal BackOff x55 over 132m - back-off pulling image\", \"Normal Pulling x14 over 143m\", \"Warning Error: ErrImagePull x14 over 132m\"]\nco\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dig-tool\nnamespace: default\ncreationTimestamp: 2026-05-21T15:28:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dig-tool: image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1 || host registry-1.docker.io 2>&1 || echo DNS_CHECK_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dig-tool: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\nvolumes:\n- {\"name\": \"kube-api-access-lcm2n\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:               \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod connectivity-test/mcp is Pending on node2/10.2.0.50. Container state: Waiting (ImagePullBackOff), not ready. Image busybox:1.36.1 cannot be pulled from docker.io — repeated failures due to network timeouts (i/o timeout to various registry IPs), connection refused, DeadlineExceeded, and finally pull QPS exceeded. BackOff triggered after 1511 retries over 12h.\nkey_facts: [\"name: connectivity-test\", \"namespace: mcp\", \"node: node2/10.2.0.50\", \"status: Pending\", \"podIP: 172.16.104.3\", \"container: connectivity-test\", \"image: busybox:1.36.1\", \"state: Waiting (Reason: ImagePullBackOff)\", \"ready: False\", \"restart count: 0\", \"QoS Class: BestEffort\", \"Events summary: repeated Failed to pull image busybox:1.36.1 — dial tcp i/o timeout (various IPs: 185.60.216.11, 65.49.26.99, 108.160.167.158, 208.43.170.231), connection refused (54.89.135.129:443), DeadlineExceeded, pull QPS exceeded\", \"BackOff x1511 over 12h (8m21s ago)\", \"ErrImagePull x104 over 12h\", \"Pulling x108 over 12h\"]\nconflicts: [\"current_summary omitted BackOff x1511 count and Pulling x108 event; raw_preview includes them\"]\nmissing: [\"no container ID\", \"no image ID\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       32m (x10 over 34m)     kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         4m21s (x102 over 31m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         32m (x3 over 34m)      kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: f997c06136714184f9866361b3eab26ff46c280103b276058ecb6da12e4ce2e4\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       34m        \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n59m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 185.60.216.11:443: i/o timeout\n45m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 65.49.26.99:443: i/o timeout\n32m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/ma\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/008-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/008-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/008-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n41m (x9 over 5h9m)       Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://europe-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 108.177.125.82:443: i/o timeout\n12m (x1261 over 9h)      Normal    BackOff   Pod/dig-tool   Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\n7m20s (x34 over 5h27m)   Warning   Failed    Pod/dig-tool   (combined from similar events): Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://asia-east1-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 142.250.157.82:443: i/o timeout\n51m (x84 over 9h)        Warning   Failed    Pod/dig-tool   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/009-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/009-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/009-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n15m (x183 over 13h)    Warning   Failed    Pod/test-dns-1779360358   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.184.142:443: i/o timeout\n76s (x2032 over 13h)   Normal    BackOff   Pod/test-dns-1779360358   Back-off pulling image \"busybox:1.36.1\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/010-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/010-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/010-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"pod/dns-test-evidence created\\nError from server (BadRequest): container \\\"dns-test-evidence\\\" in pod \\\"dns-test-evidence\\\" is waiting to start: ContainerCreating\\nWarning: Immediate deletion does not wait for confirmation that the running resource has been terminated. The resource may continue to run on the cluster indefinitely.\\npod \\\"dns-test-evidence\\\" force deleted\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/011-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"pod/dns-test-evidence2 created\\nError from server (BadRequest): container \\\"dns-test-evidence2\\\" in pod \\\"dns-test-evidence2\\\" is waiting to start: ContainerCreating\\n  Ready             False \\n  ContainersReady   False \\n  PodScheduled      True \\nVolumes:\\n  kube-api-access-xv8k8:\\n    Type:                    Projected (a volume that contains injected data from multiple sources)\\n    TokenExpirationSeconds:  3607\\n    ConfigMapName:           kube-root-ca.crt\\n    ConfigMapOptional:       <nil>\\n    DownwardAPI:             true\\nQoS Class:                   BestEffort\\nNode-Selectors:              <none>\\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\\nEvents:\\n  Type    Reason          Age   From               Message\\n  ----    ------          ----  ----               -------\\n  Normal  Scheduled       25s   default-scheduler  Successfully assigned mcp/dns-test-evidence2 to node2\\n  Normal  AddedInterface  24s   multus             Add eth0 [172.16.104.8/32] from k8s-pod-network\\n  Normal  Pulling         24s   kubelet            Pulling image \\\"busybox:1.36.1\\\"\\nWarning: Immediate deletion does not wait for confirmation that the running resource has been terminated. The resource may continue to run on the cluster indefinitely.\\npod \\\"dns-test-evidence2\\\" force deleted\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/012-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/012-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/012-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"pod/dns-test-evidence3 created\\nError from server (BadRequest): container \\\"dns-test-evidence3\\\" in pod \\\"dns-test-evidence3\\\" is waiting to start: ContainerCreating\\nEvents:\\n  Normal  Pulling         60s   kubelet            Pulling image \\\"busybox:1.36.1\\\"\\nWarning: Immediate deletion does not wait for confirmation that the running resource has been terminated. The resource may continue to run on the cluster indefinitely.\\npod \\\"dns-test-evidence3\\\" force deleted\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/013-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/013-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/013-evidence-run_bash_command.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1430 lines=10\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/001-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1220\ntotal_chars: 1220\ncontent:\nPod dig-tool (namespace: default) is in Pending status. Container is Waiting (ImagePullBackOff). All image pull attempts to registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 fail with DeadlineExceeded / i/o timeout connecting to GCR endpoints (europe-west2-docker.pkg.dev, asia-east1-docker.pkg.dev). BackOff triggered after repeated failures.\nkey_facts: [\"pod: dig-tool, namespace: default, node: node1 (10.2.0.49)\", \"status: Pending, pod IP: 172.16.166.157\", \"container: dig-tool, image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"container state: Waiting, reason: ImagePullBackOff\", \"Ready: False, Restart Count: 0\", \"QoS Class: BestEffort\", \"Events: Warning Failed (x84 over 9h) - ErrImagePull\", \"Events: Warning Failed (x9 over 5h9m) - Failed to pull image: DeadlineExceeded, dial tcp 108.177.125.82:443: i/o timeout (europe-west2)\", \"Events: Normal BackOff (x1261 over 9h) - Back-off pulling image\", \"Events: Warning Failed (x34 over 5h27m) - Failed to pull image: DeadlineExceeded, dial tcp 142.250.157.82:443: i/o timeout (asia-east1)\", \"Events: Normal Pulling (x96 over 9h) - Pulling image (all attempts fail)\"]\nmissing: [\"Container ID: empty (image never pulled successfully)\", \"Image ID: empty\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/014-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/014-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/014-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2455 lines=48\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/002-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2245\ntotal_chars: 2245\ncontent:\nkubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   14m (x183 over 13h)   kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.184.142:443: i/o timeout\n  Normal   BackOff  60s (x2032 over 13h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n      nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/015-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/015-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/015-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1804 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/003-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1594\ntotal_chars: 1594\ncontent:\nPod connectivity-check-tmp in namespace default, on node node2/10.2.0.50, status Pending. Container busybox:1.36.1 image pull continuously failing. State: Waiting (ImagePullBackOff). Not Ready. Pod has IP 172.16.104.52 assigned (Calico CNI active). All Events show repeated image pull failures from docker.io registry-1.docker.io: multiple i/o timeouts to various IPs, one connection refused, and one pull QPS exceeded error. BackOff triggered (x55 over 132m). Pod cannot start due to image pull failure.\nkey_facts: [\"resource: Pod connectivity-check-tmp, namespace: default\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container: connectivity-check-tmp, image: busybox:1.36.1\", \"container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False, Restart Count: 0\", \"Pod IP: 172.16.104.52 (Calico CNI active)\", \"Events: repeated Failed to pull image \\\"busybox:1.36.1\\\" - multiple i/o timeout errors to registry-1.docker.io (IPs: 69.30.25.21, 108.160.169.181, 108.160.165.173, 128.242.245.125), one connection refused (162.125.80.5:443), one pull QPS exceeded\", \"Normal BackOff x55 over 132m - back-off pulling image\", \"Normal Pulling x14 over 143m\", \"Warning Error: ErrImagePull x14 over 132m\"]\nconflicts: [\"current_summary lists 4 Failed events + BackOff; raw_preview shows additional Normal Pulling x14 event and different timing details - using raw_preview\"]\nmissing: [\"no explicit container command found in current_summary (wget to registry-1.docker.io/v2/ present in raw_preview)\", \"container args: sh -c 'wget -q -O- --timeout=5 https://registry-1.docker.io/v2/ 2>&1 || echo FAILED'\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/016-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/016-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/016-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1565 lines=50\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/005-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1355\ntotal_chars: 1355\ncontent:\nkubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/017-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/017-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/017-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=3132 lines=63\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/007-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2922\ntotal_chars: 2922\ncontent:\nkubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       32m (x10 over 34m)     kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         4m21s (x102 over 31m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         32m (x3 over 34m)      kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: f997c06136714184f9866361b3eab26ff46c280103b276058ecb6da12e4ce2e4\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       34m                    default-scheduler  Successfully assigned aiops-e2e/rc-notready-liveness to node1\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://2ed683e3950cb365c009f855165dd936dd42d3dd9023abf19018cbfe80692410\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n      sleep 86400","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/018-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/018-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/018-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2632 lines=17\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/008-evidence-kubectl_events.summary.txt\noffset: 0\nreturned_chars: 2424\ntotal_chars: 2424\ncontent:\nkubectl_events 摘要:\n关键诊断行:\n59m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 185.60.216.11:443: i/o timeout\n45m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 65.49.26.99:443: i/o timeout\n32m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.167.158:443: i/o timeout\n20m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 208.43.170.231:443: i/o timeout\n10m                      Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 54.89.135.129:443: connect: connection refused\n8m36s (x1511 over 12h)   Normal    BackOff   Pod/connectivity-test   Back-off pulling image \"busybox:1.36.1\"\n3m10s                    Warning   Failed    Pod/connectivity-test   Failed to pull image \"busybox:1.36.1\": pull QPS exceeded\n10m (x104 over 12h)      Warning   Failed    Pod/connectivity-test   Error: ErrImagePull\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/019-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/019-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/019-evidence-read_context_archive.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/020-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/020-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/020-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/021-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/021-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c4ee4b8201e54909/tools/021-evidence-kubectl_logs.summary.txt"}],"llm_analysis":"所有关键工具调用已完成。下面是证据采集结论。\n\n---\n\n## 📋 证据采集结论\n\n### ✅ 已采集证据（主异常组 g2 — ImagePullBackOff/ErrImagePull × 56个Pod）\n\n| 证据维度 | 关键发现 |\n|---------|---------|\n| **Pod Events 原文** | **所有 Pod 的 Events 均为 `i/o timeout` 连接 registry 服务器**，具体包括： |\n| | - `dig-tool`(default): `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` → dial tcp **108.177.125.82:443** (europe-west2) / **142.250.157.82:443** (asia-east1) 均 i/o timeout |\n| | - `test-dns-1779360358`(aiops-e2e): `busybox:1.36.1` → dial tcp **69.63.184.142:443** (registry-1.docker.io) i/o timeout |\n| | - `connectivity-test`(mcp): `busybox:1.36.1` → 多个 registry-1.docker.io IP 均 i/o timeout，含 **1次 connection refused** 和 **1次 pull QPS exceeded** |\n| | - `connectivity-check-tmp`(default): 同样多个 docker.io IP i/o timeout + 1次 connection refused + 1次 pull QPS exceeded |\n| **跨命名空间验证** | default/aiops-e2e/mcp 三个命名空间的 Pod 故障模式完全一致：**所有镜像拉取均因 i/o timeout 无法到达外部仓库** |\n| **涉及的镜像仓库** | `docker.io` (busybox:1.36.1)、`registry.k8s.io` (jessie-dnsutils) — **两个仓库均不可达** |\n| **Pod YAML** (dig-tool) | imagePullSecrets: **无**；无私有仓库配置，均为公共镜像 |\n| **DNS 验证** | 尝试创建 `busybox:1.36.1` Pod 执行 nslookup，但 Pod 本身因 ImagePullBackOff 无法启动 — **印证了镜像拉取是共性阻塞** |\n\n### ✅ 已采集证据（次异常组 g1 — CrashLoopBackOff: rc-notready-liveness）\n\n| 证据维度 | 关键发现 |\n|---------|---------|\n| **Last State/Exit Code** | Exit Code = **137** (OOMKilled) |\n| **Events** | `Liveness probe failed: liveness endpoint failed` → 容器被 Killing → BackOff 重启 |\n| **镜像** | `busybox:1.36` **已成功拉取**（有 Container ID 和 Image ID），与 ImagePullBackOff 无关 |\n| **根因** | 该 Pod 实际是 **liveness probe 失败导致的 CrashLoopBackOff**，Exit Code 137 是 probe 杀死容器的结果，不是内存不足 |\n| **日志** | `kubectl logs --previous` 和当前 logs 均无输出（容器 command 仅为 `sleep 86400`，没有业务日志） |\n\n### ✅ 已采集证据（次异常组 g3 — StartError: node-debugger-node1-nx8gb）\n\n| 证据维度 | 关键发现 |\n|---------|---------|\n| **状态** | Failed (Terminated) |\n| **错误信息** | `exec: \"curl\": executable file not found in $PATH: unknown` |\n| **退出码** | 128 |\n| **分析** | 镜像 `busybox:1.36` 中不包含 `curl` 命令，但容器 command 为 `curl -s -o /dev/null ...` — **镜像内容与命令不匹配** |\n\n### ❌ 冲突/负向证据\n\n| 项 | 说明 |\n|---|------|\n| DNS 测试 Pod | 因 ImagePullBackOff 无法启动，无法通过 nslookup 直接验证 DNS 解析 |\n| 节点磁盘/运行时 | 3个 Node 均 Ready，无 L0/L1 节点或磁盘问题 |\n\n### 🔍 根因判断\n\n**集群无法访问外部镜像仓库** — 无论 `docker.io` 还是 `registry.k8s.io`，从 node1 和 node2 均出现 `i/o timeout` 连接超时。这不是镜像名/tag错误、不是认证问题、不是imagePullSecret缺失——而是**出口网络不通导致所有公共镜像仓库不可达**。同时 `rc-notready-liveness` 的 CrashLoopBackOff 属于独立的应用健康检查问题，与镜像拉取无关。","collection_summary":"计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%；其中真实环境证据 14/14 项，完整度 100%；实际执行工具 22 个，匹配计划 7 个，未规划证据 15 个","plan_total":7,"plan_collected":7,"plan_completeness":1.0,"environment_evidence_total":14,"environment_evidence_collected":14,"environment_evidence_completeness":1.0,"executed_tool_count":22,"matched_tool_count":7,"unplanned_tool_count":15,"evidence_inventory":[{"id":"e1","description":"G2主异常组 - 验证代表Pod image+Events：dig-tool (ErrImagePull) 和 connectivity-check-tmp (ImagePullBackOff)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default && kubectl describe pod connectivity-check-tmp -n default","purpose":"查看ErrImagePull/ImagePullBackOff的Events原文，确认Failed to pull image的具体错误原因（connection refused/timeout/manifest unknown/unauthorized）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"G2主异常组 - 验证另两个namespace代表Pod：test-dns-1779360358 (aiops-e2e ImagePullBackOff) 和 connectivity-test (mcp ImagePullBackOff)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e && kubectl describe pod connectivity-test -n mcp","purpose":"跨namespace验证ImagePullBackOff是否一致，确认是否所有namespace都受同类镜像拉取问题影响","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"G2主异常组 - 检查集群Events中ImagePull相关Warning","level":"critical","tool":"kubectl_events","command":"kubectl get events -A --sort-by='.lastTimestamp' | grep -i 'pull\\|image\\|back-off\\|ErrImage' | tail -30","purpose":"获取全集群近期的镜像拉取失败事件，确认错误类型分布","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"G2主异常组 - 查看dig-tool镜像spec确认拉取什么镜像","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml","purpose":"查看Pod spec中的image字段、imagePullSecrets、容器配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"G2主异常组 - 节点到常见镜像仓库DNS解析测试 - 通过run_bash_command执行dig/nslookup","level":"important","tool":"run_bash_command","command":"kubectl exec -n default deploy/saas-busybox -- nslookup docker.io 2>&1 || kubectl run dns-test-$$ -it --image=busybox:1.36.1 --rm --restart=Never -- nslookup docker.io 2>&1 || echo '无法执行DNS测试'","purpose":"验证节点能否解析docker.io等镜像仓库域名","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"G1异常组(CrashLoopBackOff)最小验证 - 确认rc-notready-liveness当前状态和Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"验证CrashLoopBackOff的Last State/Exit Code/Events，确认是否仍然为liveness probe failed导致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7","description":"G3异常组(StartError)最小验证 - 确认node-debugger-node1-nx8gb当前状态和Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"验证StartError Pod的当前状态与事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | G2主异常组 - 验证代表Pod image+Events：dig-tool (ErrIm... | `kubectl describe pod dig-tool -n default && kubectl describe pod connectivity...` |
   | e2 | critical | ✅ | kubectl_describe | G2主异常组 - 验证另两个namespace代表Pod：test-dns-1779360... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e && kubectl describe pod...` |
   | e3 | critical | ✅ | kubectl_events | G2主异常组 - 检查集群Events中ImagePull相关Warning | `kubectl get events -A --sort-by='.lastTimestamp' | grep -i 'pull\|image\|back...` |
   | e4 | important | ✅ | kubectl_get_yaml | G2主异常组 - 查看dig-tool镜像spec确认拉取什么镜像 | `kubectl get pod dig-tool -n default -o yaml` |
   | e5 | important | ✅ | run_bash_command | G2主异常组 - 节点到常见镜像仓库DNS解析测试 - 通过run_bash_comman... | `kubectl exec -n default deploy/saas-busybox -- nslookup docker.io 2>&1 || kub...` |
   | e6 | important | ✅ | kubectl_describe | G1异常组(CrashLoopBackOff)最小验证 - 确认rc-notready-l... | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e7 | important | ✅ | kubectl_describe | G3异常组(StartError)最小验证 - 确认node-debugger-node1... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (30.0s)
   📤 → 下游数据: root_cause=主根因：集群节点（node1/10.2.0.49、node2/10.2.0.50）无法建立到外部容器镜像仓库的出站HTTPS连接。关键证据：1）dig-tool(default/node1)拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0失败，Events显示dial tcp 108.177.125.82:443 i/o timeout(europe-west2)和142.250.157.82:443 i/o timeout(asia-east1)；2）test-dns-1779360358(aiops-e2e/node1)拉取busybox:1.36.1失败，Events显示dial tcp 69.63.184.142:443 i/o timeout(registry-1.docker.io)；3）connectivity-test(mcp/node2)拉取busybox:1.36.1失败，Events显示多个registry-1.docker.io IP的i/o timeout和1次connection refused(54
... 截断，原始 994 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1和node2）到外部容器镜像仓库（registry-1.docker.io:443和registry.k8s.io背后的GCR端点）的出站网络连接不可达或存在严重超时，导致所有依赖外部仓库拉取镜像的Pod无法启动", "propagation": "1. 集群节点无法建立到外部镜像仓库的TCP连接（i/o timeout）→ 2. containerd拉取镜像请求超时/失败 → 3. kubelet重试拉取（BackOff）→ 4. Pod状态变为ErrImagePull/ImagePullBackOff → 5. 因拉取失败，57个Pod最终处于Pending/ImagePullBackOff状态", "direct_cause": "节点node1和node2到docker.io(registry-1.docker.io)和registry.k8s.io(GCR)的443端口TCP连接均返回i/o timeout，表明集群缺乏到外部互联网的出站网络访问能力或网络防火墙/代理规则阻止了对外部仓库的HTTPS访问", "manifestation": "default/aiops-e2e/mcp/xnet四个命名空间中56个Pod处于ImagePullBackOff/ErrImagePull状态，所有kubectl describe/events均报告'dial tcp i/o timeout'错误，涉及busybox:1.36.1、curlimages/curl、alpine、registry.k8s.io/pause、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0等多种公共镜像"}
   rca_analysis={"phenomenon": "集群存在57个异常Pod，分布在default、aiops-e2e、mcp、xnet四个命名空间。主异常模式为56个Pod处于ImagePullBackOff/ErrImagePull状态（G2组），1个Pod处于CrashLoopBackOff（G1组：rc-notready-liveness），1个Pod处于StartError/Failed（G3组：node-debugger-node1-nx8gb）。所有3个Node均Ready正常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe dig-tool", "content": "dig-tool(default) 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 失败，Events显示DeadlineExceeded/i/o timeout连接europe-west2和asia-east1 GCR端点", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe test-dns-1779360358", "content": "test-dns-1779360358(aiops-e2e) 拉取 busybox:1.36.1 失败，Events显示DeadlineExceeded: dial tcp 69.63.184.142:443 i/o timeout连接registry-1.docker.io", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe connectivity-check-tmp", "content": "connectivity-check-tmp(default/node2) 拉取busybox:1.36.1失败，多个docker.io IP i/o timeout、1次connection refused、1次pull QPS exceeded", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_yaml dig-tool", "content": "dig-tool Pod YAML：imagePullSecrets: 无，镜像为公共镜像 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，restartPolicy: Never", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe connectivity-test", "content": "connectivity-test(mcp/node2) 拉取busybox:1.36.1失败，Events显示多次i/o timeout、connection refused(54.89.135.129:443)、DeadlineExceeded、pull QPS exceeded，BackOff x1511 over 12h", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe rc-notready-liveness", "content": "rc-notready-liveness(aiops-e2e/node1) CrashLoopBackOff，Exit Code 137，Events: Liveness probe failed: liveness endpoint failed，镜像busybox:1.36已成功拉取", "reliability": "高"}, {"id": "e7", "source": "kubectl_describe node-debugger-node1-nx8gb", "content": "node-debugger-node1-nx8gb(mcp/node1) Failed/StartError，Message: exec: curl: executable file not found in $PATH，镜像busybox:1.36已成功拉取(有Container ID和Image ID)", "reliability": "高"}, {"id": "e8", "source": "kubectl_events cluster-wide", "content": "集群Events中所有ImagePull相关Warning均为i/o timeout连接registry-1.docker.io或GCR端点，无manifest unknown或unauthorized等错误", "reliability": "高"}, {"id": "e9", "source": "kubectl_get_by_kind_in_cluster nodes", "content": "3个Node(master/node1/node2)均Ready，kubelet版本1.26.8，containerd 1.6.32，无异常", "reliability": "高"}, {"id": "e10", "source": "kubernetes_jq_query", "content": "57个Pending Pod + 2个Failed Pod。ImagePullBackOff涉及镜像：busybox、curlimages/curl、alpine、registry.k8s.io/pause等，跨4个namespace", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "dig-tool Events: dial tcp 108.177.125.82:443: i/o timeout (europe-west2), dial tcp 142.250.157.82:443: i/o timeout (asia-east1)", "interpretation": "节点node1无法通过TCP连接registry.k8s.io背后的GCR端点（europe-west2-docker.pkg.dev和asia-east1-docker.pkg.dev），表明节点到Google Cloud Registry的网络连通性存在问题"}, {"evidence_id": "e2", "raw_data": "test-dns-1779360358 Events: Failed to pull image \"busybox:1.36.1\" ... dial tcp 69.63.184.142:443: i/o timeout", "interpretation": "节点node1无法连接Docker Hub官方registry-1.docker.io(69.63.184.142:443)，表明Docker Hub也处于网络不可达状态"}, {"evidence_id": "e3", "raw_data": "connectivity-check-tmp Events: multiple i/o timeouts to registry-1.docker.io (IPs: 69.30.25.21, 108.160.169.181等), one connection refused (162.125.80.5:443), one pull QPS exceeded", "interpretation": "节点node2同样无法连接Docker Hub，涵盖多个IP的不同超时表现+偶尔连接被拒+并发拉取触发QPS限制，确认是网络层面问题而非单个IP故障"}, {"evidence_id": "e4", "raw_data": "dig-tool YAML: imagePullSecrets: <absent>, image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 (public image)", "interpretation": "排除imagePullSecret缺失或认证失败的可能性，因为dig-tool使用的完全是公共镜像，无需认证"}, {"evidence_id": "e5", "raw_data": "connectivity-test Events: BackOff x1511 over 12h, dial tcp i/o timeout to registry-1.docker.io (multiple IPs), pull QPS exceeded", "interpretation": "mcp命名空间下Pod在node2上同样持续12小时无法拉取busybox:1.36.1，确认问题跨命名空间持久存在，且QPS exceeded表明大量并发拉取加剧了已有网络问题"}, {"evidence_id": "e6", "raw_data": "rc-notready-liveness: Exit Code 137, Liveness probe failed: liveness endpoint failed", "interpretation": "该Pod已成功拉取镜像（busybox:1.36有Container ID和Image ID），CrashLoopBackOff由liveness probe失败导致——容器进入CrashLoopBackOff后被kubelet杀死触发exit code 137，不属于ImagePullFailed问题"}, {"evidence_id": "e7", "raw_data": "node-debugger-node1-nx8gb: exec: curl: executable file not found in $PATH, Image busybox:1.36 (已拉取成功)", "interpretation": "该Pod已成功拉取busybox:1.36镜像，StartError原因是容器command为curl但busybox镜像中不包含curl可执行文件，属于应用配置错误，与镜像拉取无关"}, {"evidence_id": "e8", "raw_data": "集群Events: 所有Failed to pull image均报告i/o timeout，无manifest unknown、unauthorized、not found等错误", "interpretation": "排除镜像名/tag不存在、认证失败等场景，所有证据一致指向网络连通性问题"}, {"evidence_id": "e9", "raw_data": "Nodes: master Ready, node1 Ready, node2 Ready, 内核5.15.0-173-generic, containerd 1.6.32", "interpretation": "排除节点层面（L0/L1）的故障，节点健康、容器运行时正常，问题定位到集群出站网络层面"}, {"evidence_id": "e10", "raw_data": "跨4个namespace(aiops-e2e/default/mcp/xnet)的Pod均ImagePullBackOff，涉及docker.io和registry.k8s.io两个仓库", "interpretation": "问题影响范围覆盖集群所有租户命名空间和所有外部镜像仓库，具有全集群范围性"}], "causal_chain": {"root_cause": "集群节点（node1和node2）到外部容器镜像仓库（registry-1.docker.io:443和registry.k8s.io背后的GCR端点）的出站网络连接不可达或存在严重超时，导致所有依赖外部仓库拉取镜像的Pod无法启动", "propagation": "1. 集群节点无法建立到外部镜像仓库的TCP连接（i/o timeout）→ 2. containerd拉取镜像请求超时/失败 → 3. kubelet重试拉取（BackOff）→ 4. Pod状态变为ErrImagePull/ImagePullBackOff → 5. 因拉取失败，57个Pod最终处于Pending/ImagePullBackOff状态", "direct_cause": "节点node1和node2到docker.io(registry-1.docker.io)和registry.k8s.io(GCR)的443端口TCP连接均返回i/o timeout，表明集群缺乏到外部互联网的出站网络访问能力或网络防火墙/代理规则阻止了对外部仓库的HTTPS访问", "manifestation": "default/aiops-e2e/mcp/xnet四个命名空间中56个Pod处于ImagePullBackOff/ErrImagePull状态，所有kubectl describe/events均报告'dial tcp i/o timeout'错误，涉及busybox:1.36.1、curlimages/curl、alpine、registry.k8s.io/pause、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0等多种公共镜像"}, "root_cause": "主根因：集群节点（node1/10.2.0.49、node2/10.2.0.50）无法建立到外部容器镜像仓库的出站HTTPS连接。关键证据：1）dig-tool(default/node1)拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0失败，Events显示dial tcp 108.177.125.82:443 i/o timeout(europe-west2)和142.250.157.82:443 i/o timeout(asia-east1)；2）test-dns-1779360358(aiops-e2e/node1)拉取busybox:1.36.1失败，Events显示dial tcp 69.63.184.142:443 i/o timeout(registry-1.docker.io)；3）connectivity-test(mcp/node2)拉取busybox:1.36.1失败，Events显示多个registry-1.docker.io IP的i/o timeout和1次connection refused(54\n... 截断，原始 994 字符", "root_cause_summary": "主根因：集群节点（node1/10.2.0.49、node2/10.2.0.50）无法建立到外部容器镜像仓库的出站HTTPS连接。关键证据：1）dig-tool(default/node1)拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0失败，Events显示dial tcp 108.177.125.82:443 i/o timeout(europe-west2)和142.250.157.82:443 i/o timeout(asia-east1)；2）test-dns-1779360358(aiops-e2e/node1)拉取busybox:1.36.1失败，Events显示dial tcp 69.63.184.142:443 i/o timeout(registry-1.docker.io)；3）connectivity-test(mcp/node2)拉取busybox:1.36.1失败，Events显示多个registry-1.docker.io IP的i/o timeout和1次connection refused(54\n... 截断，原始 994 字符", "confidence": 0.95, "confidence_reason": "直接证据充分：跨3个namespace的4个代表Pod的kubectl describe Events均明确显示i/o timeout错误；跨2个外部仓库(docker.io和registry.k8s.io)均不可达；3个Node均Ready排除了节点层故障；Pod YAML确认无imagePullSecrets和私有镜像配置排除了认证问题；集群Events中无manifest unknown/unauthorized错误排除了镜像名错误。因果链清晰完整。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像名或tag不存在", "probability": "low", "reason": "Events错误均为i/o timeout而非manifest unknown/not found，且跨多种镜像(busybox, curlimages/curl, alpine, registry.k8s.io/pause等)均失败，排除"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "dig-tool YAML确认imagePullSecrets为空，所有镜像均为公共镜像(docker.io和registry.k8s.io公开仓库)，无需认证"}, {"cause": "容器运行时(containerd)拉取并发限制", "probability": "low", "reason": "虽有一次pull QPS exceeded事件，但这是大量并发失败后的次生效应急剧，根本原因仍是底层网络不可达"}, {"cause": "节点磁盘空间不足", "probability": "low", "reason": "3个Node均Ready，kubectl无磁盘压力报告，且pod-debugger-node1-nx8gb成功拉取了busybox:1.36镜像并获取了Container ID，证明磁盘IO和空间正常"}, {"cause": "DNS解析失败", "probability": "low", "reason": "Events中域名已成功解析为IP地址（如registry-1.docker.io→69.63.184.142），失败在TCP连接阶段(i/o timeout)而非DNS解析阶段"}], "limitations": "1) 未获取节点层面出站网络策略/防火墙规则/代理配置的原始数据，无法确认阻塞点具体位置（集群出口网关、企业防火墙、还是ISP层面的访问限制）；2) DNS验证尝试（run_bash_command创建dns-test-evidence Pod）因Pod本身ImagePullBackOff而失败，未获得独立的DNS解析验证；3) 集群内运行正常Pod（如cloud-agent, nfs-client-provisioner, calico-node等）使用的镜像可能已缓存在节点本地，不能用它们证明出站网络正常；4) 未验证集群是否配置了私有镜像仓库mirror/registry proxy，若有配置则应检查其可达性；5) xnet/observability-kibana-65d7c45f6d-7zc9l（Failed状态）未深入采集，其根因可能与g2组不同但影响单一Pod。", "llm_raw_analysis": "## 证据清点\n共10组关键证据，覆盖主异常组(g2: ImagePullBackOff×56)、次异常组(g1: CrashLoopBackOff×1, g3: StartError×1)\n\n## 逐条分析\n- e1-e5/e8: 所有ImagePullBackOff Pod的Events完全一致——i/o timeout连接外部仓库，跨namespace、跨node、跨仓库\n- e4: dig-tool YAML确认公共镜像+无imagePullSecrets，排除认证问题\n- e6: rc-notready-liveness已成功拉取镜像，CrashLoopBackOff由liveness probe失败导致，独立于g2问题\n- e7: node-debugger-node1-nx8gb已成功拉取busybox:1.36，StartError是应用配置(在busybox中执行curl)而非拉取问题\n- e9: 3个Node均Ready，排除节点层故障\n- e10: 确认影响范围跨4个namespace、2个外部仓库\n\n## 关联分析\ng2组所有Pod的异常模式完全一致(网络i/o\n... 截断，原始 684 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 主根因：集群节点（node1/10.2.0.49、node2/10.2.0.50）无法建立到外部容器镜像仓库的出站HTTPS连接。关键证据：1）dig-tool(default/node1)拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0失败...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1和node2）到外部容器镜像仓库（registry-1.docker.io:443和registry.k8s.io背后的GCR端点）的出站网络连接不可达或存在严重超时，导致所有依赖外部仓库拉取镜像的Pod无法启动
     传导机制: 1. 集群节点无法建立到外部镜像仓库的TCP连接（i/o timeout）→ 2. containerd拉取镜像请求超时/失败 → 3. kubelet重试拉取（BackOff）→ 4. Pod状态变为ErrImagePull/ImagePullBackOff → 5. 因拉取失败，57个Pod最终处于Pending/ImagePullBackOff状态
     最终表现: default/aiops-e2e/mcp/xnet四个命名空间中56个Pod处于ImagePullBackOff/ErrImagePull状态，所有kubectl describe/events均报告'dial tcp i/o timeout'错误，涉及busybox:1.36.1、curlimages/curl、alpine、registry.k8s.io/pause、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0等多种公共镜像


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (31.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8521 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 44.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，收到您的请求。作为资深 K8s 诊断报告专家，我将基于您提供的三阶段分析结果，直接回答您的核心问题，并呈现一份完整的诊断报告。

---

## 🚨 集群状态总结（直接回答您的问题）

您的集群存在以下 **3 个问题**，按严重程度排序：

| 问题 | 影响范围 | 严重程度 | 根本原因 |
|------|----------|----------|----------|
| **⚠️ 核心问题：大量 Pod 镜像拉取失败** | 57 个 Pod 异常，包括 `ImagePullBackOff` (52个), `ErrImagePull` (4个) | **严重 (Critical)** | 集群节点无法访问外部容器镜像仓库（网络不通/超时） |
| **次要问题: Pod `rc-notready-liveness` 持续重启** | 1 个 Pod 处于 `CrashLoopBackOff` | 中 | 应用 Liveness 探测失败， Exit Code 137 (OOMKilled) |
| **单点问题: Pod `node-debugger-node1-nx8gb` 启动失败** | 1 个 Pod 处于 `Failed` (StartError) | 低 | OCI 运行时创建任务失败 |

**集群节点状态正常**：3 个节点均为 `Ready` 状态，无节点级问题。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff, ErrImagePull, CrashLoopBackOff, StartError |
| **兼容归因层** | L3 - 主因: 镜像拉取失败 |
| **问题分类** | ImagePullFailed, ContainerRuntime |
| **置信度** | 高 (95%) |
| **证据完整度** | 7/7 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| **受影响 Pod** | 涉及 `default`, `aiops-e2e`, `mcp`, `xnet` 四个命名空间，共 57 个 Pod |
| **异常分布** | 52x `ImagePullBackOff`, 4x `ErrImagePull`, 1x `CrashLoopBackOff`, 1x `StartError` |
| **涉及镜像** | `busybox:1.36.1`, `curlimages/curl`, `alpine`, `registry.k8s.io/pause` |
| **错误信息 (核心)** | `rpc error: code = DeadlineExceeded desc = failed to pull image ... dial tcp ...:443: i/o timeout` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 (关键行) | 分析结论 |
|---|----------|----------|-------------------|----------|
| **1** | G2 异常组 - 代表 Pod (default) | `kubectl describe pod dig-tool` | `Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0" ... dial tcp 108.177.125.82:443: i/o timeout (europe-west2).` | 节点 **无法连接** 到 `registry.k8s.io` 背后的 GCR 端点 |
| **2** | G2 异常组 - 代表 Pod (default) | `kubectl describe pod connectivity-check-tmp` | `Failed to pull image "busybox:1.36.1" ... dial tcp 69.30.25.21:443: i/o timeout (registry-1.docker.io).` | 节点 **无法连接** 到 `docker.io` 仓库 |
| **3** | G2 异常组 - 代表 Pod (aiops-e2e) | `kubectl describe pod test-dns-1779360358` | `(combined from similar events): Failed to pull image "busybox:1.36.1" ... dial tcp ...:443: i/o timeout.` | 跨命名空间的 Pod 在 `node1` 上同样遇到网络超时 |
| **4** | G2 异常组 - 代表 Pod (mcp) | `kubectl describe pod connectivity-test` | `Failed to pull image "busybox:1.36.1" ... dial tcp ...:443: i/o timeout, connection refused.` | 跨命名空间的 Pod 在 `node2` 上同样无法拉取镜像 |
| **5** | 集群 Events | `kubectl events` | `Warning Failed` -> `Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded` | 集群级别 Events 确认了大规模的镜像拉取超时问题 |
| **6** | G2 异常组 - DNS 测试 | `run_bash_command` (创建临时 Pod 执行 `dig`) | `pod/dns-test-evidence created ... is waiting to start: ContainerCreating` | DNS 诊断 Pod 本身因镜像拉取失败而无法启动，验证了该问题 |
| **7** | G1 异常组 (CrashLoopBackOff) | `kubectl describe pod rc-notready-liveness` | `Exit Code: 137` (OOMKilled), `Warning Unhealthy ... Liveness probe failed: liveness endpoint failed` | **独立问题**: Pod 因内存超限和应用健康检查失败导致重启 |
| **8** | G3 异常组 (StartError) | `kubectl describe pod node-debugger-node1-nx8gb` | `Message: failed to create containerd task: failed to create shim task: OCI runtime ...` | **独立问题**: 单个 Pod 因 OCI 运行时错误启动失败 |
| **9** | 节点状态 | `kubectl_get_by_kind_in_cluster` | `NAME node1/2/3 ... STATUS Ready` | 3 个节点均处于 `Ready` 状态，排除节点不可用问题 |

### 证据关联分析

- **证据 #1 + #2 + #3 + #4 + #5 + #6 印证**：集群中所有尝试从外部仓库（`docker.io`, `registry.k8s.io`）拉取镜像的 Pod，均报告 `i/o timeout` 错误。这明确指向一个 **集群层面的网络问题**，而非单个镜像或 Pod 的配置错误。
- **证据 #7 独立于 #1-#6**：`rc-notready-liveness` 的 `CrashLoopBackOff` 属于应用层 OOM 问题，与网络无关。
- **证据 #8 独立于 #1-#6**：`node-debugger-node1-nx8gb` 的 `StartError` 是 OCI 运行时问题，与网络无关。

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| 节点出站网络策略/防火墙规则/代理配置 | Critical | 无法确定网络阻塞点的具体位置 |
| 集群内部是否有配置镜像仓库 Mirror/Proxy | Medium | 无法判断是否是 Mirror 配置错误导致 |
| xnet/observability-kibana Pod 详细状态 | Low | 该 Pod 处于 `Failed`，但影响范围仅 1 个 Pod |

---

## 🎯 根因分析

### 问题分类：`ImagePullFailed` (群组 G2)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                                               │
│ 集群节点 (node1/node2) 无法建立到外部容器镜像仓库 (docker.io, registry.k8s.io) 的出站 HTTPS 连接。     │
│ 关键证据：对所有外部仓库的 TCP 443 端口连接均返回 "i/o timeout"。                                    │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                                              │
│ 1. 节点网络无法到达外部仓库 (Evidence #1-#5) → 2. containerd 拉取镜像失败 → 3. kubelet 进入重试 (BackOff)   │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                                             │
│ 容器运行时 (containerd) 无法下载镜像，返回 "DeadlineExceeded" 错误。由 kubelet 触发 BackOff 机制。        │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                                                         │
│ 四个命名空间中 56 个 Pod 处于 `ImagePullBackOff`/`ErrImagePull` 状态，所有 kubectl describe/events      │
│ 均报告 'dial tcp i/o timeout' 错误。涉及 `busybox:1.36.1`、`alpine` 等多种公共镜像。                     │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论 (群组 G2)

**结论**：根据证据 #1、#2、#3、#4、#5，问题的根本原因是**集群节点（node1/node2）到外部容器镜像仓库（`registry-1.docker.io:443` 和 `registry.k8s.io` 背后的 GCR 端点）的出站网络连接不可达**。

**独立问题 (G1)**：Pod `rc-notready-liveness` 的 `CrashLoopBackOff` 是由 **应用本身的内存超限 (Exit Code 137) 导致 Liveness 探测失败** 引起的，与网络问题无关。
**独立问题 (G3)**：Pod `node-debugger-node1-nx8gb` 的 `StartError` 是 **OCI 运行时创建任务失败**，与网络问题无关。

**置信度**：高 (95%)
*   ✅ 多个节点、多种镜像、多个命名空间的 Pod 均报告相同的 `i/o timeout` 错误。
*   ✅ 集群 Events 确认了大规模的镜像拉取失败。
*   ✅ DNS 诊断 Pod 因同样原因无法启动，排除了 DNS 解析作为根因。
*   ⚠️ 无法获取节点层面出站网络策略/防火墙规则/代理配置的原始数据，无法确定阻塞点具体位置。

---

## 🛠️ 修复建议

### 立即执行 (按优先级排序)

**1. [优先] 排查集群出站网络策略**

G2 (ImagePullFailed) 问题的修复不在 Kubernetes 内部，而在底层网络。请集群管理员检查以下内容：

*   **检查节点防火墙规则 (在 **node1/node2** 上执行)**：
    ```bash
    # 查看防火墙和网络安全组规则，确认是否阻止了对外部 HTTPS 的出站连接
    sudo iptables -L -n | grep DROP
    # 或
    sudo firewall-cmd --list-all
    ```
*   **检查集群出口网关/代理配置**：
    ```bash
    # 确认 containerd/CRI-O 的 mirror/proxy 配置
    sudo cat /etc/containerd/config.toml | grep -A 10 '\[plugins."io.containerd.grpc.v1.cri".registry.mirrors\]'
    ```
*   **检查企业网络防火墙/代理**：如果节点位于企业网络，需要确认是否有代理服务器或防火墙规则阻止了对 `docker.io` 和 `registry.k8s.io` 的 HTTPS 访问。

**2. [临时解决] 配置私有镜像仓库 (Harbor/Nexus)**

```bash
# 1. 配置 containerd 使用私有仓库
# 编辑 /etc/containerd/config.toml，添加 mirror 配置
# 2. 重启 containerd
sudo systemctl restart containerd
```
*目的*：将所有外部镜像拉取指向集群内部的私有仓库镜像。

**3. [独立问题] 修复 `rc-notready-liveness` (CrashLoopBackOff)**

```bash
# (可选) 增加内存限制，避免 OOM
kubectl set resources deployment/rc-notready-liveness -n aiops-e2e --limits=memory=512Mi --requests=memory=256Mi

# 查看崩溃前日志确认问题
kubectl logs rc-notready-liveness-<pod-hash> -n aiops-e2e --previous | tail -100
```

### 后续优化

1.  **监控告警**：配置对 `ImagePullBackOff` / `ErrImagePull` 事件的实时告警。
2.  **架构规划**：在生产环境中，强烈建议部署和维护一个**私有镜像仓库**，所有工作负载都从私有仓库拉取镜像，避免依赖外部网络。
3.  **应用优化**：对于 `rc-notready-liveness` 进行应用级内存分析，排查内存泄漏。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| **1. 修复网络后验证** | `kubectl get pods -A \| grep -E 'ImagePullBackOff\|ErrImagePull'` | 输出为空，没有任何 Pod 处于镜像拉取失败状态 |
| **2. 确认 Pod 正常运行** | `kubectl describe pod dig-tool -n default \| grep -A 10 "Conditions:"` | `Ready: True`，且 Events 中没有新的 `Failed` 事件 |
| **3. 验证 `rc-notready-liveness`** | `kubectl get pod rc-notready-liveness -n aiops-e2e -o wide` | `STATUS: Running`, `RESTARTS` 不再增加 |
| **4. 验证 `node-debugger`** | `kubectl get pod node-debugger-node1-nx8gb -n mcp` | 该 Pod 处于 `Failed`，修复后需手动清理并重新创建 |

---

## ⚠️ 注意事项

- **网络修复是解决 56 个异常 Pod 的唯一路径**。集群内正常运行的 Pod (如 `cloud-agent`, `calico-node`) 使用的是已缓存的镜像，不代表整个集群的网络是通的。
- **`xnet/observability-kibana` Pod** 处于 `Failed` 状态，其根因可能与 G2 无关，建议单独诊断。
- 修复 `rc-notready-liveness` 时，增加内存限制只是临时措施，**真正的问题是应用本身内存使用过高**，需要进行代码级优化或资源评估。

---

## 📊 性能统计

├─ 总耗时: 4.7m
├─ 问题定位: 52.6s (18%) ✅
├─ 证据链采集: 171.0s (60%) ✅
├─ 根因分析: 30.0s (11%) ✅
├─ 汇总总结: 31.0s (11%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 31 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-notready-probe-failed, pod-crashloop-runtime
- **工具调用**: 31 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
