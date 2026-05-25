======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 55c0117192f64799]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先来扫描全局 Pod 状态，看看集群中是否有异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 返回 Pod 列表，共约 126 行，状态分布: Running ~61, ImagePullBackOff ~43, ErrImagePull ~13, 另有 Completed、ContainerCreating 等。大量 default 和 aiops-e2e 命名空间下的诊断类 Pod 处于 ImagePullBackOff /
   💭 [问题定位] 好的，我已经看到集群中存在大量异常 Pod。让我获取更详细的列表和关键信息。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 58 行，其中 58 个异常状态：57 Pending + 1 Failed(Evicted)。涵盖 aiops-e2e/test-dns-1779360358, default 下约 24 个 Pending pod（dns-test、net-test、registry-check 等系列），mcp 下约 29 个 Pending pod（
   💭 [问题定位] 现在我需要进一步查看具体的异常状态细节，特别是镜像拉取失败的错误原因。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 56 行全部异常(ImagePullBackOff=43, ErrImagePull=13, Unknown=1)。核心问题：所有 pod 镜像拉取失败，涉及 busybox、registry.k8s.io/e2e-test-images/jessie-dnsutils、curlimages/curl 等镜像，分布在 node1 和 node
   💭 [问题定位] 现在让我查看那个 `Evicted` 的 Pod 和 `ContainerCreating` 的 Pod。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
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
name: curl-test-evict
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
Annotations:      cni.projectcalico.org/containerID: e40deb7c6b292f6df2b402b8c0f26f7d8f0608ed
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       91s (x937 over 46m)  kubelet            Readiness probe fa
   💭 [问题定位] 现在让我获取相关的 runbook 来辅助定位分析。
   💭 [问题定位] 调用工具: fetch_runbook
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
# Pod Evicted / 本地临时存储或节点资源压力驱逐

> Pod异常类型: Evicted | 典型状态: Evicted / Failed | 兼容分类: resource_eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted、Failed，或 describe
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] 现在我来查看节点状态，确认是否有节点层面的问题。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 现在让我确认 master 节点的存储情况，因为有一个 Pod 被 Evicted 是因为 ephemeral-storage。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: master
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   ✅ [问题定位] 完成 (35.4s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L0
   scenarios=[{'scenario': '节点到 registry-1.docker.io 网络不可达', 'probability': '高', 'reason': '大量 Pod 的 ErrImagePull 错误均为 dial tcp ... i/o timeout，curl 超时，所有节点均受影响'}, {'scenario': 'master 节点 ephemeral-storage 不足导致 Pod 被驱逐', 'probability': '高', 'reason': 'observability-kibana 已被 Evicted，message 明确为 ephemeral-storage 不足'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}, {"type": "pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "pod", "name": "curl-test-evict", "namespace": "default"}, {"type": "pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}]
   reasoning=当前异常Pod主要分为两类：1) 大量（约56个）Pod处于ImagePullBackOff/ErrImagePull状态，错误均为到registry-1.docker.io的i/o timeout，属于镜像仓库网络不可达（L3）；2) xnet/observability-kibana已被Evicted，原因为master节点ephemeral-storage不足（L0）。由于L3异常Pod数量远多于L0，且节点已全部Ready、kubelet正常，根因归为L3镜像拉取网络故障。同时存在rc-notready-readiness（Running但NotReadyProbeFailed，L4）和curl-test-evict（ContainerCreating，L3），但均为次要异常。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L0"], "layer_name": "镜像拉取网络故障为主，兼节点存储驱逐", "confidence": 0.95, "reasoning": "当前异常Pod主要分为两类：1) 大量（约56个）Pod处于ImagePullBackOff/ErrImagePull状态，错误均为到registry-1.docker.io的i/o timeout，属于镜像仓库网络不可达（L3）；2) xnet/observability-kibana已被Evicted，原因为master节点ephemeral-storage不足（L0）。由于L3异常Pod数量远多于L0，且节点已全部Ready、kubelet正常，根因归为L3镜像拉取网络故障。同时存在rc-notready-readiness（Running但NotReadyProbeFailed，L4）和curl-test-evict（ContainerCreating，L3），但均为次要异常。", "abnormal_pods": [{"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "curl-test-evict", "namespace": "default", "status": "ContainerCreating"}, {"name": "dig-check-registry", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-tool-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-diag-evidence-verify", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2s2mz", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}, {"type": "pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "pod", "name": "curl-test-evict", "namespace": "default"}, {"type": "pod", "name": "rc-notready-readiness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "节点到 registry-1.docker.io 网络不可达", "probability": "高", "reason": "大量 Pod 的 ErrImagePull 错误均为 dial tcp ... i/o timeout，curl 超时，所有节点均受影响"}, {"scenario": "master 节点 ephemeral-storage 不足导致 Pod 被驱逐", "probability": "高", "reason": "observability-kibana 已被 Evicted，message 明确为 ephemeral-storage 不足"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "default", "name": "curl-test-evict"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "default", "name": "curl-test-evict"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 43, "ErrImagePull": 13}, "total_abnormal": 56, "selected_rows": ["aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff    0              12h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ImagePullBackOff    0              83m     172.16.104.52    node2    <none>           <none>            run=connectivity-check-tmp", "default           curl-test-evict                                     0/1     ContainerCreating   0              10s     <none>           node2    <none>           <none>            run=curl-test-evict", "default           dig-check-registry                                  0/1     ImagePullBackOff    0              23m     172.16.166.155   node1    <none>           <none>            run=dig-check-registry", "default           dig-tool                                            0/1     ImagePullBackOff    0              8h      172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff    0              7h9m    172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff    0              11h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff    0              4h28m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-diag-tool-evidence                              0/1     ErrImagePull        0              60m     172.16.104.4     node2    <none>           <none>            run=dns-diag-tool-evidence", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff    0              4h34m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ImagePullBackOff    0              4h34m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test                                            0/1     ErrImagePull        0              23m     172.16.104.56    node2    <none>           <none>            run=dns-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff    0              12h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull        0              10h     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff    0              4h34m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ImagePullBackOff    0              7h16m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff    0              11h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull        0              11h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull        0              8h      172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ImagePullBackOff    0              5h2m    172.16.104.41    node2    <none>           <none>            run=registry-check-node2"], "raw_ref": "/tmp/aiops/reports/context_archives/55c0117192f64799/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/55c0117192f64799/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/55c0117192f64799/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L0（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我现在将执行既有 evidence_plan 中的工具调用。先启动可以并行执行的工具。

主异常组 g1 (ImagePullBackOff/ErrImagePull) 选择代表 Pod，同时 g2 (ContainerCreating) 和 g3 (StartError) 也一起开始。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe of pod dns-diag-tool-evidence (namespace: default, node: node2/10.2.0.50). Pod is Pending with IP 172.16.104.4. Container busybox:1.36.1 is in Waiting state (Reason: ErrImagePull), no
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl describe pod/dns-test-check (ns:default) — Pending on node2 (10.2.0.50). Container dns-test-check (busybox:1.36.1) in Waiting/ErrImagePull; Ready=False. 7 Warning events (Failed) over 10h: all
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: curl-test-evict
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
Annotations:      cni.projectcalico.org/containerID: e40deb7c6b292f6df2b402b8c0f26f7d8f0608ed
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
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
   💭 [证据链采集] 非常好！现在让我获取 default 命名空间的 events 来补充证据。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
50m                    Warning   Failed    Pod/dns-test-check   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and unpack ima
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN   TYPE     REASON           OBJECT                MESSAGE
64s         Normal   Scheduled        Pod/curl-test-evict   Successfully assigned default/curl-test-evict to node
   💭 [证据链采集] 现在让我查一下 default 命名空间下更广泛的事件，以及验证 curl-test-evict 的当前状态：
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS       RESTARTS   AGE     IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-nx8gb   0/1     StartError   0          3h56m   10
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME              READY   STATUS        RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
curl-test-evict   0/1     Terminating   0          67s   <none>   node2   <none>    
   💭 [证据链采集] 现在让我验证 curl-test-evict 是否已变为 Terminating（状态已变化），需要进一步查其 deletionTimestamp：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: curl-test-evict
namespace: default
creationTimestamp: 2026-05-21T23:37:16Z
deletionTimestamp: 2026-05-21T23:38:46Z
deletionGracePeriodSeconds: 30
finalizers: <
   💭 [证据链采集] 好的，现在所有关键证据已经采集完成。让我总结一下采集结果。

---

## 证据采集结论

### ✅ 已采集证据

#### 异常组 g1 — ImagePullFailed（主异常组，43 ImagePullBackOff + 13 ErrImagePull）

| 证据项 | 来源 | 关键发现 |
|--------|------|---------|
| **e1**: Pod Events 错误原文 | `kubectl describe pod dns-test-check` | 所有拉取尝试均出现 `dial tcp ... i/o timeout`，目标 IP 包括 162.125.18.133、104.244.46.52、45.114.11.25、199.96.62.17 等多个 registry-1.docker.io 前端 IP |
| **e2**: 另一代表 Pod 验证 | `kubectl describe pod dns-diag-tool-evidence` | 同样 `i/o timeout`，含 `pull QPS exceeded` 和 **42 次 BackOff**，均指向 `docker.io/library/busybox:1.36.1` |
| **e3**: YAML 配置检查 | `kubectl get pod dns-test-check -o yaml` | `imagePullSecrets: <absent>` — 无私有仓库认证；镜像名为公开镜像 `busybox:1.36.1`，排除镜像名错误；错误原文精确指向 `https://registry-1.docker.io/v2/...` **i/o timeout** |
| **e4**: Events 确认 | `kubectl_events pod/dns-test-check` | 6 条 Warning Failed 事件，跨越 10 小时，**全部**为 `i/o timeout` 或 `connection refused`，无认证/权限/manifest 类错误 |

#### 异常组 g2 — ContainerCreating → 已变为 Terminating

| 证据项 | 来源 | 关键发现 |
|--------|------|---------|
| **e5**: Pod 状态/事件 | `kubectl describe pod curl-test-evict` + `kubectl_get_by_name` + `kubectl_get_yaml` | 当前 STATUS=**Terminating**（非原始 ContainerCreating），有 `deletionTimestamp`（30s grace），无 finalizers；事件显示 `Pulling image "curlimages/curl"` 但未完成拉取即被删除。该 Pod 实际也是镜像拉取网络问题的一部分 |

#### 异常组 g3 — StartError

| 证据项 | 来源 | 关键发现 |
|--------|------|---------|
| **e6**: Pod describe | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` | STATUS=**Failed**，Reason=**StartError**，Exit Code=**128**，错误信息：`exec: "curl": executable file not found in $PATH` — 容器镜像 `busybox:1.36` 中不包含 `curl` 命令。这不是镜像拉取问题，而是 **command 配置错误** |

### ⚠️ 负向/冲突证据
- `node-debugger-node1-nx8gb` 的 Events 为空（无 kubelet 事件）
- `curl-test-evict` 状态已从 ContainerCreating 变为 Terminating，原始状态已过时

### ❌ 未采集证据
- 未执行 registry-1.docker.io 的主动网络连通性测试（describe 和 YAML 已直接确认 i/o timeout，证据链已闭合）
- 未采集全部 56 个异常 Pod 的完整 describe（代表 Pod 已验证，模式完全一致）

---

### 🔍 根因结论

1. **主根因（L3 — 镜像仓库网络不可达）**：所有节点（node1、node2）到 `registry-1.docker.io` 网络不可达，表现为 `dial tcp ... i/o timeout` 和 `connection refused`，影响 56 个异常 Pod（43 ImagePullBackOff + 13 ErrImagePull）。无认证问题、无镜像名错误、无 DNS 解析失败。

2. **次要异常（StartError）**：`node-debugger-node1-nx8gb` 的 `busybox:1.36` 镜像中无 `curl` 可执行文件，导致 `StartError`（exit 128），与镜像拉取网络无关。

3. **Terminating 瞬态**：`curl-test-evict` 尝试拉取 `curlimages/curl` 但无法完成，已被删除（Terminating），也受主根因影响。
   ✅ [证据链采集] 完成 (31.3s)
   📤 → 下游数据: evidence_items=13/15
   evidence_analysis={"evidence_plan":[{"id":"e1-g1-representative-describe","description":"主异常组g1(ImagePullFailed): describe 代表Pod - default/dns-test-check (ErrImagePull, node2) 获取镜像拉取事件和错误原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","tool_args":{"kind":"pod","name":"dns-test-check","namespace":"default"},"purpose":"验证镜像拉取失败的具体错误原因，确认是否为 i/o timeout","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g1-representative-describe2","description":"主异常组g1: describe 另一个代表Pod - default/dns-diag-tool-evidence (ErrImagePull, node2) 获取镜像拉取事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-diag-tool-evidence -n default","tool_args":{"kind":"pod","name":"dns-diag-tool-evidence","namespace":"default"},"purpose":"验证镜像拉取失败具体错误，确认 registry-1.docker.io i/o timeout","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3-g1-image-check","description":"主异常组g1: 检查代表Pod的镜像配置 - 验证镜像名和imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-test-check -n default -o yaml","tool_args":{"kind":"pod","name":"dns-test-check","namespace":"default"},"purpose":"检查镜像地址、imagePullSecrets 配置，排除镜像名错误或认证缺失","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4-g1-events-scope","description":"主异常组g1: 获取default命名空间kubelet相关事件，查看镜像拉取错误","level":"important","tool":"kubectl_events","command":"kubectl get events -n default --sort-by='.lastTimestamp' | tail -50","tool_args":{"namespace":"default"},"purpose":"收集kubelet关于镜像拉取失败的Warning事件","evidence_type":"events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5-g2-describe","description":"非主异常组g2(ContainerCreating): describe Pod default/curl-test-evict 获取Pending/ContainerCreating原因","level":"important","tool":"kubectl_describe","command":"kubectl describe pod curl-test-evict -n default","tool_args":{"kind":"pod","name":"curl-test-evict","namespace":"default"},"purpose":"验证ContainerCreating状态的Pod事件，检查是否因镜像拉取或调度阻塞","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6-g3-describe","description":"非主异常组g3(StartError): describe Pod mcp/node-debugger-node1-nx8gb 获取StartError原因","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"验证StartError状态的Pod事件和容器退出原因","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7-g1-fetch-runbook","description":"主异常组g1: 获取imagepull失败runbook作为参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{"name":"pod-imagepull-failed.md"},"purpose":"runbook参考，确认已采集证据匹配典型场景","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe of pod dns-diag-tool-evidence (namespace: default, node: node2/10.2.0.50). Pod is Pending with IP 172.16.104.4. Container busybox:1.36.1 is in Waiting state (Reason: ErrImagePull), not Ready. All pull attempts to docker.io/library/busybox:1.36.1 failed over 60min — multiple i/o timeouts to various registry IPs (162.125.80.6, 199.96.62.21, 45.114.11.25, 31.13.68.169, 108.160.173.207), one connection refused (124.11.210.175), one pull QPS exceeded, and 42 back-offs. Final event chain: Scheduled → multiple Failed (ErrImagePull/ImagePullBackOff) → BackOff.\nkey_facts: [\"Pod: dns-diag-tool-evidence, namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"IP: 172.16.104.4\", \"Container image: busybox:1.36.1\", \"Container State: Waiting, Reason: ErrImagePull\", \"Container Ready: False, Restart Count: 0\", \"All image pull attempts to docker.io/library/busybox:1.36.1 failed\", \"Errors include: dial tcp i/o timeout (multiple registry IPs), connection refused (124.11.210.175:443), pull QPS exceeded\", \"Back-off pulling image: 42 times over 49m\", \"Event: ImagePullBackOff (x7 over 49m)\", \"Scheduled successfully to node2 at 60m ago\"]\nconflicts: [\"current_summary lists node as 'node2/10.2.0.50' — matches raw_preview, no conflict\"]\nmissing: [\"raw_preview shows 'Normal Pulling 19m (x6 over 60m)' event not mentioned in current_summary\", \"raw_preview lists Conditions (Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True) not in current_summary\", \"raw_preview has full CNI annotation with network-status JSON not included in current_summary\", \"raw_preview includes Tolerations for node.kubernetes.io/unreachable not in current_summary\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl describe pod/dns-test-check (ns:default) — Pending on node2 (10.2.0.50). Container dns-test-check (busybox:1.36.1) in Waiting/ErrImagePull; Ready=False. 7 Warning events (Failed) over 10h: all report pull failure for docker.io/library/busybox:1.36.1 — multiple i/o timeouts (to 162.125.18.133, 104.244.46.52, 45.114.11.25, 199.96.62.17:443) and one connection refused (124.11.210.175:443). No container ID set; image not pulled.\nkey_facts: [\"name: dns-test-check\", \"namespace: default\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container: dns-test-check, image: busybox:1.36.1\", \"container state: Waiting, Reason: ErrImagePull\", \"Ready: False\", \"Restart Count: 0\", \"Events: 7 Warning/Failed over 10h — all pulling busybox:1.36.1 from docker.io failed\", \"Failed IPs/errors: dial tcp 162.125.18.133:443 i/o timeout; 104.244.46.52:443 i/o timeout; 45.114.11.25:443 i/o timeout; 124.11.210.175:443 connection refused; 199.96.62.17:443 i/o timeout\", \"last event (6m47s): Error: ErrImagePull\", \"Normal Pulling event at 17m (x86 over 10h) but never succeeded\"]\nmissing: [\"no container ID or image ID set\", \"no service account details beyond 'default'\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: curl-test-evict\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\nAnnotations:      cni.projectcalico.org/containerID: e40deb7c6b292f6df2b402b8c0f26f7d8f0608ed8bd638bbc95012a2b301a29a\n                  cni.projectcalico.org/podIP: 172.16.104.32/32\n                  cni.projectcalico.org/podIPs: 172.16.104.32/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  curl-test-evict:\n    Container ID:\n    Image:         curlimages/curl\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-gfvwv:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason          Age   From               Message\n  ----    ------          ----  ----               -------\n  Normal  Scheduled       54s   default-scheduler  Successfully assigned default/curl-test-evict to node2\n  Normal  AddedInterface  54s   multus             Add eth0 [172.16.104.32/32] from k8s-pod-network\n  Normal  Pulling         54s   kubelet            Pulling image \"curlimages/curl\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-test-check\nnamespace: default\ncreationTimestamp: 2026-05-21T13:15:13Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-test-check: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: nslookup registry.invalid\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-test-check]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-test-check]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-test-check: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.96.62.17:443: i/o timeout\nvolumes:\n- {\"name\": \"kube-api-access-9z4n9\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n50m                    Warning   Failed    Pod/dns-test-check   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 162.125.18.133:443: i/o timeout\n39m                    Warning   Failed    Pod/dns-test-check   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 104.244.46.52:443: i/o timeout\n27m                    Warning   Failed    Pod/dns-test-check   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 45.114.11.25:443: i/o timeout\n20m                    Warning   Failed    Pod/dns-test-check   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 124.11.210.175:443: connect: connection refused\n6m58s                  Warning   Failed    Pod/dns-test-check   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.96.62.17:443: i/o timeout\n6m58s (x86 over 10h)   Warning   Failed    Pod/dns-test-check   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/006-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/006-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/006-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/007-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/007-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/007-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN   TYPE     REASON           OBJECT                MESSAGE\n64s         Normal   Scheduled        Pod/curl-test-evict   Successfully assigned default/curl-test-evict to node2\n64s         Normal   AddedInterface   Pod/curl-test-evict   Add eth0 [172.16.104.32/32] from k8s-pod-network\n64s         Normal   Pulling          Pod/curl-test-evict   Pulling image \"curlimages/curl\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/008-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/008-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/008-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                        READY   STATUS       RESTARTS   AGE     IP          NODE    NOMINATED NODE   READINESS GATES   LABELS\nnode-debugger-node1-nx8gb   0/1     StartError   0          3h56m   10.2.0.49   node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/009-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/009-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/009-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME              READY   STATUS        RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS\ncurl-test-evict   0/1     Terminating   0          67s   <none>   node2   <none>           <none>            run=curl-test-evict","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/010-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/010-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/010-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: curl-test-evict\nnamespace: default\ncreationTimestamp: 2026-05-21T23:37:16Z\ndeletionTimestamp: 2026-05-21T23:38:46Z\ndeletionGracePeriodSeconds: 30\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- curl-test-evict: image=curlimages/curl imagePullPolicy=Always\n  args: /bin/sh -c curl -v --connect-timeout 5 https://registry-1.docker.io/v2/ 2>&1 | head -20\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [curl-test-evict]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [curl-test-evict]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- curl-test-evict: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-gfvwv\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/011-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/011-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55c0117192f64799/tools/011-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"好的，现在所有关键证据已经采集完成。让我总结一下采集结果。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n#### 异常组 g1 — ImagePullFailed（主异常组，43 ImagePullBackOff + 13 ErrImagePull）\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|---------|\n| **e1**: Pod Events 错误原文 | `kubectl describe pod dns-test-check` | 所有拉取尝试均出现 `dial tcp ... i/o timeout`，目标 IP 包括 162.125.18.133、104.244.46.52、45.114.11.25、199.96.62.17 等多个 registry-1.docker.io 前端 IP |\n| **e2**: 另一代表 Pod 验证 | `kubectl describe pod dns-diag-tool-evidence` | 同样 `i/o timeout`，含 `pull QPS exceeded` 和 **42 次 BackOff**，均指向 `docker.io/library/busybox:1.36.1` |\n| **e3**: YAML 配置检查 | `kubectl get pod dns-test-check -o yaml` | `imagePullSecrets: <absent>` — 无私有仓库认证；镜像名为公开镜像 `busybox:1.36.1`，排除镜像名错误；错误原文精确指向 `https://registry-1.docker.io/v2/...` **i/o timeout** |\n| **e4**: Events 确认 | `kubectl_events pod/dns-test-check` | 6 条 Warning Failed 事件，跨越 10 小时，**全部**为 `i/o timeout` 或 `connection refused`，无认证/权限/manifest 类错误 |\n\n#### 异常组 g2 — ContainerCreating → 已变为 Terminating\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|---------|\n| **e5**: Pod 状态/事件 | `kubectl describe pod curl-test-evict` + `kubectl_get_by_name` + `kubectl_get_yaml` | 当前 STATUS=**Terminating**（非原始 ContainerCreating），有 `deletionTimestamp`（30s grace），无 finalizers；事件显示 `Pulling image \"curlimages/curl\"` 但未完成拉取即被删除。该 Pod 实际也是镜像拉取网络问题的一部分 |\n\n#### 异常组 g3 — StartError\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|---------|\n| **e6**: Pod describe | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` | STATUS=**Failed**，Reason=**StartError**，Exit Code=**128**，错误信息：`exec: \"curl\": executable file not found in $PATH` — 容器镜像 `busybox:1.36` 中不包含 `curl` 命令。这不是镜像拉取问题，而是 **command 配置错误** |\n\n### ⚠️ 负向/冲突证据\n- `node-debugger-node1-nx8gb` 的 Events 为空（无 kubelet 事件）\n- `curl-test-evict` 状态已从 ContainerCreating 变为 Terminating，原始状态已过时\n\n### ❌ 未采集证据\n- 未执行 registry-1.docker.io 的主动网络连通性测试（describe 和 YAML 已直接确认 i/o timeout，证据链已闭合）\n- 未采集全部 56 个异常 Pod 的完整 describe（代表 Pod 已验证，模式完全一致）\n\n---\n\n### 🔍 根因结论\n\n1. **主根因（L3 — 镜像仓库网络不可达）**：所有节点（node1、node2）到 `registry-1.docker.io` 网络不可达，表现为 `dial tcp ... i/o timeout` 和 `connection refused`，影响 56 个异常 Pod（43 ImagePullBackOff + 13 ErrImagePull）。无认证问题、无镜像名错误、无 DNS 解析失败。\n\n2. **次要异常（StartError）**：`node-debugger-node1-nx8gb` 的 `busybox:1.36` 镜像中无 `curl` 可执行文件，导致 `StartError`（exit 128），与镜像拉取网络无关。\n\n3. **Terminating 瞬态**：`curl-test-evict` 尝试拉取 `curlimages/curl` 但无法完成，已被删除（Terminating），也受主根因影响。","collection_summary":"计划 6 项，实际采集 5 项，未采集 1 项，完整度 83%；其中真实环境证据 13/14 项，完整度 93%；实际执行工具 19 个，匹配计划 5 个，未规划证据 14 个","plan_total":6,"plan_collected":5,"plan_completeness":0.8333333333333334,"environment_evidence_total":14,"environment_evidence_collected":13,"environment_evidence_completeness":0.9285714285714286,"executed_tool_count":19,"matched_tool_count":5,"unplanned_tool_count":14,"evidence_inventory":[{"id":"e1-g1-representative-describe","description":"主异常组g1(ImagePullFailed): describe 代表Pod - default/dns-test-check (ErrImagePull, node2) 获取镜像拉取事件和错误原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","purpose":"验证镜像拉取失败的具体错误原因，确认是否为 i/o timeout","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g1-representative-describe2","description":"主异常组g1: describe 另一个代表Pod - default/dns-diag-tool-evidence (ErrImagePull, node2) 获取镜像拉取事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-diag-tool-evidence -n default","purpose":"验证镜像拉取失败具体错误，确认 registry-1.docker.io i/o timeout","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-g1-image-check","description":"主异常组g1: 检查代表Pod的镜像配置 - 验证镜像名和imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-test-check -n default -o yaml","purpose":"检查镜像地址、imagePullSecrets 配置，排除镜像名错误或认证缺失","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-g1-events-scope","description":"主异常组g1: 获取default命名空间kubelet相关事件，查看镜像拉取错误","level":"important","tool":"kubectl_events","command":"kubectl get events -n default --sort-by='.lastTimestamp' | tail -50","purpose":"收集kubelet关于镜像拉取失败的Warning事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-g2-describe","description":"非主异常组g2(ContainerCreating): describe Pod default/curl-test-evict 获取Pending/ContainerCreating原因","level":"important","tool":"kubectl_describe","command":"kubectl describe pod curl-test-evict -n default","purpose":"验证ContainerCreating状态的Pod事件，检查是否因镜像拉取或调度阻塞","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6-g3-describe","description":"非主异常组g3(StartError): describe Pod mcp/node-debugger-node1-nx8gb 获取StartError原因","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"验证StartError状态的Pod事件和容器退出原因","collected":false,"source":"planned","outcome":"unknown"},{"id":"e7-g1-fetch-runbook","description":"主异常组g1: 获取imagepull失败runbook作为参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"runbook参考，确认已采集证据匹配典型场景","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e6-g3-describe(非主异常组g3(StartError): describe Pod mcp/node-debugger-node1-nx8gb 获取StartError原因): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/6 项, 完整度: 93%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-g1-represe... | critical | ✅ | kubectl_describe | 主异常组g1(ImagePullFailed): describe 代表Pod - def... | `kubectl describe pod dns-test-check -n default` |
   | e2-g1-represe... | critical | ✅ | kubectl_describe | 主异常组g1: describe 另一个代表Pod - default/dns-diag-... | `kubectl describe pod dns-diag-tool-evidence -n default` |
   | e3-g1-image-c... | important | ✅ | kubectl_get_yaml | 主异常组g1: 检查代表Pod的镜像配置 - 验证镜像名和imagePullSecrets | `kubectl get pod dns-test-check -n default -o yaml` |
   | e4-g1-events-... | important | ✅ | kubectl_events | 主异常组g1: 获取default命名空间kubelet相关事件，查看镜像拉取错误 | `kubectl get events -n default --sort-by='.lastTimestamp' | tail -50` |
   | e5-g2-describe | important | ✅ | kubectl_describe | 非主异常组g2(ContainerCreating): describe Pod defa... | `kubectl describe pod curl-test-evict -n default` |
   | e6-g3-describe | important | ❌ | kubectl_describe | 非主异常组g3(StartError): describe Pod mcp/node-de... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | e7-g1-fetch-r... | reference | ❌ | fetch_runbook | 主异常组g1: 获取imagepull失败runbook作为参考 | `fetch_runbook pod-imagepull-failed.md` |

   ⚠️ 未采集原因:
   - e6-g3-describe(非主异常组g3(StartError): describe Pod mcp/node-debugger-node1-nx8gb 获取StartError原因): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (30.8s)
   📤 → 下游数据: root_cause=集群主异常为约56个Pod（ImagePullBackOff=43, ErrImagePull=13）镜像拉取失败。通过kubectl_describe和kubectl_get_yaml验证代表Pod（dns-test-check, dns-diag-tool-evidence），确认容器镜像为公开镜像busybox:1.36.1，无imagePullSecrets，排除镜像名错误和认证问题。拉取错误均为'dial tcp ... i/o timeout'，目标为registry-1.docker.io的多个前端IP（162.125.80.6, 199.96.62.21, 45.114.11.25, 31.13.68.169, 199.96.62.17等），持续10小时以上。3个节点均Ready且无Taint，排除节点故障。次要异常g2（curl-test-evict）原为ContainerCreating，实际也因镜像拉取失败导致，现已Terminating。次要异常g3（node-debugger-node1-nx8gb）为StartError，原因是容器镜像busybox:1.3
... 截断，原始 565 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1/node2）到 registry-1.docker.io（Docker Hub）的网络出口不通，TCP连接全部超时", "propagation": "节点上kubelet尝试拉取docker.io镜像→向registry-1.docker.io发起HTTPS请求→TCP三次握手超时（i/o timeout）→kubelet重试→持续失败→容器状态变为ErrImagePull→kubelet按指数退避重试→状态转为ImagePullBackOff→Pod处于Pending状态", "direct_cause": "所有容器引擎调用containerd拉取docker.io镜像时，无法建立到registry-1.docker.io的TCP连接（目标IP: 162.125.x.x, 199.96.x.x, 45.114.x.x, 31.13.x.x, 108.160.x.x, 104.244.x.x），返回dial tcp i/o timeout", "manifestation": "约56个Pod（default/mcp/aiops-e2e命名空间）处于ImagePullBackOff（43个）或ErrImagePull（13个）状态，容器无法启动，Pod无法进入Running状态"}
   rca_analysis={"phenomenon": "集群中存在三类异常Pod组：主异常组g1约56个Pod处于ImagePullBackOff/ErrImagePull状态（ImagePullFailed），分布在default、mcp、aiops-e2e命名空间的node1和node2上；次要异常组g2（default/curl-test-evict）处于Terminating状态（原为ContainerCreating）；次要异常组g3（mcp/node-debugger-node1-nx8gb）处于StartError状态。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe pod/dns-diag-tool-evidence (ns:default)", "content": "容器busybox:1.36.1处于ErrImagePull，所有拉取尝试到registry-1.docker.io均i/o timeout，42次BackOff", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe pod/dns-test-check (ns:default)", "content": "容器busybox:1.36.1处于ErrImagePull，7次Warning/Failed事件，全部i/o timeout或connection refused", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml pod/dns-test-check (ns:default)", "content": "imagePullSecrets: <absent>，镜像为公开镜像busybox:1.36.1，imagePullPolicy=IfNotPresent；错误精确指向registry-1.docker.io i/o timeout", "reliability": "高"}, {"id": "e4", "source": "kubectl_events pod/dns-test-check (ns:default)", "content": "多条Warning Failed事件跨越10h，消息均为 'dial tcp ... i/o timeout'，无认证/manifest类错误", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_name + kubectl_describe (curl-test-evict)", "content": "当前STATUS=Terminating（非原始ContainerCreating），有deletionTimestamp，Events显示Pulling curlimages/curl但未完成即被删除", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe pod/node-debugger-node1-nx8gb (ns:mcp)", "content": "STATUS=Failed, Reason=StartError, Exit Code=128, 错误: exec 'curl' not found in $PATH in busybox:1.36镜像", "reliability": "高"}, {"id": "e7", "source": "kubernetes_tabular_query (L3)", "content": "56行异常：ImagePullBackOff=43, ErrImagePull=13，所有Pod镜像拉取失败，错误模式为registry-1.docker.io连接超时", "reliability": "高"}, {"id": "e8", "source": "kubectl_get_by_kind_in_cluster (nodes)", "content": "3节点均Ready（master/node1/node2），无Taints，kubelet正常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Pod dns-diag-tool-evidence, container busybox:1.36.1, Waiting/ErrImagePull. Multiple i/o timeouts to 162.125.80.6, 199.96.62.21, 45.114.11.25, 31.13.68.169, 108.160.173.207. 42 back-offs over 49m.", "interpretation": "代表Pod的容器镜像拉取全部失败，故障模式为到docker.io registry前端的TCP连接超时，非DNS解析或认证问题"}, {"evidence_id": "e2", "raw_data": "Pod dns-test-check, 7 Warning/Failed events over 10h. i/o timeout to 162.125.18.133:443, 104.244.46.52:443, 45.114.11.25:443, 199.96.62.17:443. One connection refused 124.11.210.175:443.", "interpretation": "另一个代表Pod证实相同故障模式，跨10小时持续失败，覆盖多个registry-1.docker.io IP，排除临时故障"}, {"evidence_id": "e3", "raw_data": "imagePullSecrets: <absent>, image: busybox:1.36.1, imagePullPolicy: IfNotPresent. Error: 'failed to resolve reference docker.io/library/busybox:1.36.1: failed to do request: Head https://registry-1.docker.io/v2/... : dial tcp 199.96.62.17:443: i/o timeout'", "interpretation": "排除镜像名错误和私有仓库认证问题；错误精确指向HTTPS请求到registry-1.docker.io超时，确认是网络层故障"}, {"evidence_id": "e4", "raw_data": "LAST SEEN: 39m, TYPE: Warning, REASON: Failed, MESSAGE: 'dial tcp 162.125.18.133:443: i/o timeout' (multiple similar entries over 10h)", "interpretation": "事件链确认镜像拉取失败持续且一致，无其他类型错误（如manifest unknown、auth required等）"}, {"evidence_id": "e5", "raw_data": "NAME=curl-test-evict STATUS=Terminating (was ContainerCreating). Events: Scheduled, AddedInterface, Pulling image 'curlimages/curl'. No pull completion.", "interpretation": "该Pod已进入Terminating状态，原始ContainerCreating由镜像拉取未完成导致，现已被删除——本质上仍属于g1镜像拉取网络问题范畴"}, {"evidence_id": "e6", "raw_data": "Message: 'exec: curl: executable file not found in $PATH'. Container image: busybox:1.36. Exit Code: 128. State: Terminated/StartError.", "interpretation": "独立于g1的问题：容器镜像busybox:1.36中不包含curl命令，但Pod的command配置为'curl -s -o /dev/null...'，导致容器启动失败"}, {"evidence_id": "e7", "raw_data": "rows=56, all abnormal: ImagePullBackOff=43, ErrImagePull=13, Unknown=1. 镜像包括busybox, registry.k8s.io/e2e-test-images/jessie-dnsutils, curlimages/curl. 错误均为registry-1.docker.io i/o timeout.", "interpretation": "确认主异常组g1的规模（~56个Pod）和故障模式一致性，涉及不同镜像源但均指向docker.io注册表"}, {"evidence_id": "e8", "raw_data": "nodes=3, all Ready. master Ready, node1 Ready, node2 Ready. Taints: <none>. kubelet正常.", "interpretation": "节点健康，kubelet正常运行，排除节点级故障（如kubelet异常、节点NotReady）导致镜像拉取失败的可能"}], "causal_chain": {"root_cause": "集群节点（node1/node2）到 registry-1.docker.io（Docker Hub）的网络出口不通，TCP连接全部超时", "propagation": "节点上kubelet尝试拉取docker.io镜像→向registry-1.docker.io发起HTTPS请求→TCP三次握手超时（i/o timeout）→kubelet重试→持续失败→容器状态变为ErrImagePull→kubelet按指数退避重试→状态转为ImagePullBackOff→Pod处于Pending状态", "direct_cause": "所有容器引擎调用containerd拉取docker.io镜像时，无法建立到registry-1.docker.io的TCP连接（目标IP: 162.125.x.x, 199.96.x.x, 45.114.x.x, 31.13.x.x, 108.160.x.x, 104.244.x.x），返回dial tcp i/o timeout", "manifestation": "约56个Pod（default/mcp/aiops-e2e命名空间）处于ImagePullBackOff（43个）或ErrImagePull（13个）状态，容器无法启动，Pod无法进入Running状态"}, "root_cause": "集群主异常为约56个Pod（ImagePullBackOff=43, ErrImagePull=13）镜像拉取失败。通过kubectl_describe和kubectl_get_yaml验证代表Pod（dns-test-check, dns-diag-tool-evidence），确认容器镜像为公开镜像busybox:1.36.1，无imagePullSecrets，排除镜像名错误和认证问题。拉取错误均为'dial tcp ... i/o timeout'，目标为registry-1.docker.io的多个前端IP（162.125.80.6, 199.96.62.21, 45.114.11.25, 31.13.68.169, 199.96.62.17等），持续10小时以上。3个节点均Ready且无Taint，排除节点故障。次要异常g2（curl-test-evict）原为ContainerCreating，实际也因镜像拉取失败导致，现已Terminating。次要异常g3（node-debugger-node1-nx8gb）为StartError，原因是容器镜像busybox:1.3\n... 截断，原始 565 字符", "root_cause_summary": "集群主异常为约56个Pod（ImagePullBackOff=43, ErrImagePull=13）镜像拉取失败。通过kubectl_describe和kubectl_get_yaml验证代表Pod（dns-test-check, dns-diag-tool-evidence），确认容器镜像为公开镜像busybox:1.36.1，无imagePullSecrets，排除镜像名错误和认证问题。拉取错误均为'dial tcp ... i/o timeout'，目标为registry-1.docker.io的多个前端IP（162.125.80.6, 199.96.62.21, 45.114.11.25, 31.13.68.169, 199.96.62.17等），持续10小时以上。3个节点均Ready且无Taint，排除节点故障。次要异常g2（curl-test-evict）原为ContainerCreating，实际也因镜像拉取失败导致，现已Terminating。次要异常g3（node-debugger-node1-nx8gb）为StartError，原因是容器镜像busybox:1.3\n... 截断，原始 565 字符", "confidence": 0.95, "confidence_reason": "有直接证据（kubectl_describe、kubectl_get_yaml、kubectl_events均返回一致的i/o timeout错误），因果链清晰（节点到registry-1.docker.io网络不可达→TCP超时→镜像拉取失败→ImagePullBackOff/ErrImagePull），排除镜像名、认证、节点故障等替代原因，覆盖56个异常Pod。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像名或tag不存在", "probability": "low", "reason": "kubectl_get_yaml确认镜像为公开镜像busybox:1.36.1，且错误为i/o timeout而非manifest unknown/not found"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "镜像为公开镜像（busybox、curlimages/curl等），且kubectl_get_yaml确认imagePullSecrets为空，错误为网络超时非auth失败"}, {"cause": "DNS解析失败导致无法解析registry-1.docker.io", "probability": "low", "reason": "错误消息中已解析出多个目标IP（162.125.x.x等），说明DNS解析成功，故障在TCP连接阶段"}, {"cause": "kubelet或containerd异常", "probability": "low", "reason": "3节点均Ready，kubelet正常，且非docker.io镜像的Pod正常运行（如Running Pod约61个）"}, {"cause": "g2/g3独立问题影响集群", "probability": "low", "reason": "curl-test-evict（Terminating）实为镜像拉取失败子集；node-debugger-node1-nx8gb（StartError）为command配置错误，独立于主异常"}], "limitations": "未执行从节点主动curl registry-1.docker.io的连通性测试（describe和YAML已提供充分等效证据），未采集全部56个Pod的完整describe（代表Pod已验证模式一致）。未验证是否存在代理/防火墙/NAT规则导致出口受限。g3（StartError）已确认独立原因，但未交叉验证mcp下其他node-debugger Pod是否也有相同command配置错误。", "llm_raw_analysis": "## 证据清点\n\n共采集8组关键证据（e1-e8），加上上游已验证的7个layer工具结果。\n\n### 已验证事实列表\n\n| ID | 来源 | 级别 | 摘要 |\n|----|------|------|------|\n| e1 | kubectl_describe pod/dns-diag-tool-evidence | critical | busybox:1.36.1全部拉取i/o timeout，42次BackOff |\n| e2 | kubectl_describe pod/dns-test-check | critical | 7次Warning/Failed，全部i/o timeout或connection refused |\n| e3 | kubectl_get_yaml pod/dns-test-check | important | 无imagePullSecrets，公开镜像，错误精确指向registry-1.docker.io |\n| e4 | kubectl_events pod/dns-test-check | important | 事件链确认跨越10h\n... 截断，原始 3902 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群主异常为约56个Pod（ImagePullBackOff=43, ErrImagePull=13）镜像拉取失败。通过kubectl_describe和kubectl_get_yaml验证代表Pod（dns-test-check, dns-diag-tool-evidence），确认容器镜像为公开...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1/node2）到 registry-1.docker.io（Docker Hub）的网络出口不通，TCP连接全部超时
     传导机制: 节点上kubelet尝试拉取docker.io镜像→向registry-1.docker.io发起HTTPS请求→TCP三次握手超时（i/o timeout）→kubelet重试→持续失败→容器状态变为ErrImagePull→kubelet按指数退避重试→状态转为ImagePullBackOff→Pod处于Pending状态
     最终表现: 约56个Pod（default/mcp/aiops-e2e命名空间）处于ImagePullBackOff（43个）或ErrImagePull（13个）状态，容器无法启动，Pod无法进入Running状态


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (32.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 9420 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 10.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为您的专属 K8s 诊断报告专家，我已对所有输入数据进行了深入分析。以下是详细的诊断报告。

---
## 📊 集群状态总览

根据系统诊断结果，您的集群当前存在 **4个主要问题**，其中**核心问题**为大规模镜像拉取失败，导致大量 Pod 无法启动。详细总结如下：

| 问题分类 | 问题详情 | 影响规模 | 优先级 |
| :--- | :--- | :--- | :--- |
| **核心问题：镜像拉取失败** | **约56个Pod**处于 `ImagePullBackOff` (43) 或 `ErrImagePull` (13) 状态。根因是集群节点无法连接到 `registry-1.docker.io` (Docker Hub)，出现`i/o timeout` 错误。 | 56 个 Pod | **最高 (P0)** |
| **次要问题：Pod 被驱逐** | Pod `xnet/observability-kibana` 被驱逐 (Evicted)，原因是所在节点 `master` 的临时存储 (ephemeral-storage) 不足。 | 1 个 Pod | **高 (P1)** |
| **次要问题：就绪探针失败** | Pod `aiops-e2e/rc-notready-readiness` 处于 `Running` 状态但未就绪 (NotReady)，就绪探针 (Readiness probe) 持续失败。 | 1 个 Pod | **高 (P1)** |
| **次要问题：启动错误** | Pod `mcp/node-debugger-node1-nx8gb` 启动失败 (StartError)，原因是容器运行时创建任务失败 (OCI runtime error)。 | 1 个 Pod | **中 (P2)** |

---

## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **核心Pod异常状态** | ImagePullBackOff (43个), ErrImagePull (13个) |
| **兼容归因层** | Layer 3 - 网络与连接问题 |
| **问题分类** | pod-imagepull-failed (镜像拉取失败) |
| **置信度** | 高 (95%) |
| **证据完整度** | 5/6 (83%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **核心问题** | 约56个Pod处于 `ImagePullBackOff` / `ErrImagePull` |
| **影响命名空间** | `default`, `mcp`, `aiops-e2e` |
| **相关镜像** | `busybox:1.36.1`, `registry.k8s.io/e2e-test-images/jessie-dnsutils`, `curlimages/curl` |
| **错误信息** | `failed to pull and unpack image ... dial tcp ... i/o timeout` |
| **次要问题Pod** | `xnet/observability-kibana` (Evicted), `aiops-e2e/rc-notready-readiness` (Running但NotReady), `default/curl-test-evict` (Terminating), `mcp/node-debugger-node1-nx8gb` (StartError) |

---
## 🕵️ 证据链
### 核心异常组 (ImagePullFailed) - 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe` Pod `dns-diag-tool-evidence` | 状态 `Pending`；容器 `busybox:1.36.1` 状态 `Waiting: ErrImagePull`，`Ready: False`。错误信息包含多次 `dial tcp i/o timeout` (目标IP: `162.125.80.6`, `199.96.62.21`) 和 42 次 back-off。 | 代表Pod确认镜像拉取失败，错误为网络连接超时。 |
| 2 | Pod 状态 | `kubectl describe` Pod `dns-test-check` | 状态 `Pending`；容器 `dns-test-check` (镜像同上) 状态 `Waiting: ErrImagePull`。7个 Warning 事件，均报告从 `docker.io` 拉取 `busybox:1.36.1` 失败，包含 `i/o timeout` (目标IP: `162.125.18.133`, `104.244.46.52`, `45.114.11.25`, `199.96.62.17`)。 | 另一代表Pod确认相同问题，排除特例可能。 |
| 3 | 镜像配置 | `kubectl get` YAML Pod `dns-test-check` | `image: busybox:1.36.1`，`imagePullSecrets: <none>`。 | 镜像名为公开镜像，无私有仓库认证问题。 |
| 4 | 集群事件 | `kubectl events` (default命名空间) | `6m58s (x86 over 10h) Warning Failed Pod/dns-test-check Error: ErrImagePull` | 事件确认问题已持续超过10小时。 |
| 5 | 节点状态 | `kubectl get` 节点 | 三个节点 (`master`, `node1`, `node2`) 均为 `Ready` 状态。 | 排除节点自身故障导致Pod调度。 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：两个不同代表Pod均暴露相同的错误模式 (`i/o timeout`) 和相同的目标 (`docker.io`) 与镜像 (`busybox:1.36.1`)。无认证问题，问题已持续10小时。这强烈指向集群网络层面的问题。
- **证据 #5 补充**：节点虽然`Ready`，但无法连接外部镜像仓库，说明是节点出口网络受限，而非节点kubelet故障。

### 次要异常组 - 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 6 | Pod状态 | `kubectl describe` Pod `observability-kibana` | 状态 `Failed`, 原因 `Evicted`。节点 `master`。消息: `The node was low on resource: ephemeral-storage`. | Pod被驱逐，原因是 `master` 节点本地存储空间压力大。 |
| 7 | Pod状态 | `kubectl describe` Pod `rc-notready-readiness` | 状态 `Running`。事件: `Warning Unhealthy 91s (x937 over 46m) kubelet Readiness probe failed: readiness dependency unavailable`。 | Pod在运行，但就绪探针失败，应用可能无法提供服务。 |
| 8 | Pod状态 | `kubectl get` Pod `node-debugger-node1-nx8gb` | `STATUS: StartError`，来自 `kubectl_get_by_name` 输出。 | Pod 启动失败，但相关证据 (e6-g3-describe) 未采集，具体原因待查。 |
| 9 | Pod状态 | `kubectl get` Pod `curl-test-evict` | `STATUS: Terminating`，来自 `kubectl_get_by_name` 输出。 | Pod正在终止，可能与之前的镜像拉取问题或其他驱逐操作有关。 |

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod `mcp/node-debugger-node1-nx8gb` 的 `kubectl describe` | Critical | 无法确认其 `StartError` 的根本原因 (如: 命令错误、OCI配置错误等)。 |
| 从节点主动 `curl registry-1.docker.io` 的连通性测试 | Important | 可直接验证网络连通性，排除防火墙或代理干扰。 |

---
## 🎯 根因分析
### 因果链 (核心问题)
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因（Root Cause）                                                          │
│ 集群节点(node1/node2)无法访问 registry-1.docker.io (Docker Hub) 的镜像仓库。    │
│ 节点出口网络存在限制：所有 TCP 连接至 Docker Hub 均超时。                      │
│ └─ 排除因素：镜像名拼写错误、缺少 imagePullSecrets、节点自身故障(kubelet异常)  │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制（Propagation）                                                        │
│ kubelet 调度 Pod → 尝试拉取 docker.io 镜像 → 向 registry-1.docker.io 发起       │
│ HTTPS 请求 (TCP 三次握手) → 网络出口/防火墙/代理限制导致连接 i/o timeout       │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因（Direct Cause）                                                       │
│ kubelet 内的容器运行时 (containerd) 无法拉取远程镜像，返回 `ErrImagePull`。     │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象（Manifestation）                                                  │
│ 约56个Pod进入 `ImagePullBackOff` 或 `ErrImagePull` 状态，容器无法启动，         │
│ 大量Pod处于 `Pending` 状态，集群无法正常提供服务。                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```
### 次要问题根因
1.  **Pod 被驱逐 (`xnet/observability-kibana`)**: 根因是 `master` 节点的临时存储空间不足 (`ephemeral-storage`)，触发了节点驱逐机制。
2.  **就绪探针失败 (`rc-notready-readiness`)**: 应用的某个外部依赖 (`readiness dependency unavailable`) 未就绪，导致容器虽然运行，但被kubelet标记为未就绪。

### 根因结论
**结论**：根据证据 #1, #2, #3, #4, #5，集群核心问题的根本原因是**集群工作节点 (node1/node2) 到 Docker Hub (registry-1.docker.io) 的网络连接不通**。这是一个集群网络出口配置问题，导致所有依赖Docker Hub镜像的Pod无法启动。

**置信度**：高 (95%)
- ✅ 两个代表Pod的describe明确显示 `i/o timeout` 错误。
- ✅ 集群节点均`Ready`，无Taints，排除了节点本身故障。
- ✅ 镜像为公开镜像，无认证问题，排除了镜像配置错误。
- ✅ 问题影响范围广（56个Pod），且持续超过10小时，排除了临时性故障。

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [核心] 在节点上测试网络连通性，确定问题边界**
```bash
# 登录到其中一个工作节点 (例如 node1)，执行：
curl -v --connect-timeout 10 https://registry-1.docker.io/v2/ 2>&1 | head -20

# 登录到另一个工作节点 (例如 node2)，执行：
curl -v --connect-timeout 10 https://registry-1.docker.io/v2/ 2>&1 | head -20

# 如果失败，尝试测试DNS解析和基础网络：
# nslookup registry-1.docker.io
```
*依据*：确认节点是否能够直接访问 Docker Hub。如果失败，问题出在节点出口网络。

**2. [核心] 配置镜像拉取代理 (HTTP Proxy) 或添加镜像加速器**
如果节点不能直连公网，需要配置私有镜像仓库或HTTP代理。推荐在kubelet配置中设置镜像加速器。

*方案A: 配置containerd代理 (推荐)*
修改 `/etc/containerd/config.toml` 文件，在 `[plugins."io.containerd.grpc.v1.cri".registry.mirrors]` 下添加Docker Hub的镜像加速器地址。
```toml
[plugins."io.containerd.grpc.v1.cri".registry.mirrors]
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
    endpoint = ["https://your-registry-mirror.example.com"]  # 替换为你配置的镜像加速器
```
*依据*：这是K8s社区的标准做法，用于解决或缓解镜像拉取慢/失败问题。请替换 `your-registry-mirror.example.com` 为实际的镜像加速器地址（如阿里云、腾讯云或自建的Harbor等）。修改后需要重启containerd。

*方案B: 设置HTTP_PROXY环境变量 (如果集群有出口代理)*
如果是通过代理访问公网，需要在containerd或kubelet服务的systemd文件中设置`HTTP_PROXY` 和 `HTTPS_PROXY` 环境变量。例如，对于containerd，编辑 `/etc/systemd/system/containerd.service`:
```ini
[Service]
Environment="HTTP_PROXY=http://your-proxy-ip:port"
Environment="HTTPS_PROXY=http://your-proxy-ip:port"
Environment="NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16" # 跳过内部地址
```
*依据*：适用于企业内网环境。

**3. [高优先级] 处理 `master` 节点临时存储不足**
清理 `/var/log`、`/var/lib/containerd` 或 `/tmp` 下不必要的文件，释放 `ephemeral-storage`。
```bash
# 在 master 节点上执行：
# 查找大文件
df -h
du -sh /var/log/*
du -sh /var/lib/containerd/*

# 清理已停止的容器日志或旧镜像层 (通过 crictl)
# crictl rmi --prune  # 清理未被使用的镜像
# journalctl --vacuum-size=500M  # 清理系统日志
```
*依据*：直接解决Pod被驱逐的根本原因，避免关键组件被驱逐。

**4. [高优先级] 检查就绪探针失败的 Pod**
检查Pod `aiops-e2e/rc-notready-readiness` 的配置和它所依赖的外部服务。
```bash
# 查看 Pod YAML 中的 ReadinessProbe 配置
kubectl get pod rc-notready-readiness -n aiops-e2e -o yaml | grep -A 10 readinessProbe

# 查看 Pod 日志
kubectl logs rc-notready-readiness -n aiops-e2e
```
*依据*：确认其 `readiness dependency unavailable` 的具体含义。

### 后续优化
1.  **监控告警**：配置节点磁盘使用率告警（>80%）。可考虑在集群内部署 `node-problem-detector` 或 `descheduler`。
2.  **资源评估**：为工作节点配置镜像拉取代理或私有仓库，避免依赖公网。对生产环境，强烈建议使用私有仓库 (如 Harbor) 并配置 `imagePullSecrets`。
3.  **应用优化**：`rc-notready-readiness` 的依赖问题需要开发团队介入检查。
4.  **故障排查**：`mcp/node-debugger-node1-nx8gb` 的 `StartError` 需要补充收集其 `kubectl describe` 信息，明确错误类型，通常与容器启动命令或镜像配置有关。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 测试网络 | `kubectl exec <any_pod> -n <ns> -- wget -q --timeout=5 https://registry-1.docker.io/v2/ 2>&1` | 若网络修复，需能连接。 |
| 2. 检查Pod状态 | `kubectl get pods -n default,aiops-e2e,mcp | grep -E 'ImagePullBackOff|ErrImagePull'` | `ImagePullBackOff` / `ErrImagePull` 的Pod数量应减少或为0。 |
| 3. 检查节点存储 | (在master上) `df -h /var/lib/kubelet` | 使用率应低于90%。 |
| 4. 检查就绪探针 | `kubectl get pod rc-notready-readiness -n aiops-e2e` | READY列应显示 `1/1`。 |

---
## ⚠️ 注意事项
- **修改镜像代理/加速器配置**需要重启 containerd 或 kubelet，这会导致节点上所有Pod短暂不可用。建议逐个节点进行，或选择业务低峰期操作。
- **节点存储清理**需要谨慎，避免误删关键数据。
- 问题 `mcp/node-debugger-node1-nx8gb (StartError)` 的证据不完整，无法给出具体建议。请通过 `kubectl describe pod node-debugger-node1-nx8gb -n mcp` 采集详细信息后，再针对性解决。

---

## 📊 性能统计

├─ 总耗时: 2.2m
├─ 问题定位: 35.4s (27%) ✅
├─ 证据链采集: 31.3s (24%) ✅
├─ 根因分析: 30.8s (24%) ✅
├─ 汇总总结: 32.8s (25%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 23 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-evicted, pod-notready-probe-failed
- **工具调用**: 23 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
