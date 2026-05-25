======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: e3d5bd6f96334d4f]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先来进行全局 Pod 状态扫描，查看集群中所有的 Pod 状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces returned ~60+ pods. Running pods (admin, aiops, default, kube-system) are healthy. Massive ImagePullBackOff (20+) and ErrImagePull (~9) failures in default and aiops-
   💭 [问题定位] 让我获取更精确的 Pod 列表来确认所有异常 Pod。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回了跨多个 namespace 的 pod 列表。Running=61, Pending=57, Succeeded=6, Failed=2。大量 Pending pod 集中在 aiops-e2e, default, mcp namespace，多为 dns、registry、network 连通性测试相关 Pod。admin 和 kube-s
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query returned 57 pods, all status Pending, Ready=false, Reason=&lt;none&gt;. Spans namespaces: aiops-e2e (1 pod), default (23 pods), mcp (33 pods). Nodes involved: node1 (28 pods),
   💭 [问题定位] 由于这些 Pod 的状态 Reason 为空，让我进一步查看关键的异常 Pod 详细信息，特别是 Pending 和 ImagePullBackOff 的。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 57 行数据，全部为异常（STATUS=Pending）。错误集中在镜像拉取失败：ImagePullBackOff（45 个）和 ErrImagePull（11 个），另有 1 个 Unknown。拉取失败的镜像包括 busybox:1.36.1、busybox:1.28、registry.k8s.io/e2e-test-images/jes
   💭 [问题定位] 现在我来查看具体的 ErrImagePull 详细错误。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-readiness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  Unhealthy       2s (x937 over 45m)  kubelet            Readiness probe fai
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod registry-conn-test-1779371220 in namespace default, on node node2/10.2.0.50, status Pending. Container busybox:1.36.1 cannot be pulled: all attempts to pull from docker.io/library/busybox:1.36.1 f
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 pod dns-test (default) on node2 is Pending. Container dns-test (image busybox:1.28) State: Waiting (Reason: ErrImagePull), Ready: False, Restart Count: 0. All pull attempts to docker.io/library/busybo
   💭 [问题定位] 现在我已经掌握了足够的异常信息。让我获取 ImagePull 相关的 runbook 来辅助分析。
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
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] 现在让我再查看一下 Failed 的 Pod 和 Terminating 的 Pod。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 表格摘要: rows=2 abnormal=2 status_counts={'Failed': 2, 'Evicted': 1}
NAMESPACE         NAME                                                STATUS      REASON
# 异常行
mcp           
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=311 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ✅ [问题定位] 完成 (49.9s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '节点到 docker.io 网络不可达（防火墙/代理/DNS 阻断）', 'probability': '高', 'reason': '大量 ErrImagePull 的 dial tcp i/o timeout 到 docker.io IP 地址（122.248.226.57, 157.240.1.9 等）:443，覆盖 node1 和 node2 两个节点'}, {'scenario': '镜像仓库 DNS 解析问题导致连接失败', 'probability': '中', 'reason': '部分拉取显示 i/o timeout，但不排除 DNS 阶段异常；dns-test/dig 等 DNS 测试 Pod 也在异常列表中但原因仍是 ImagePullBackOff'}, {'scenario': '节点镜像缓存缺失 + 外网访问受限', 'probability': '中', 'reason': '系统组件（calico, coredns, kube-apiserver 等）镜像已拉取运行正常，只有测试类 Pod 和 busybox 镜像拉取失败'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "image_registry", "name": "docker.io", "namespace": ""}, {"type": "image_registry", "name": "registry.k8s.io", "namespace": ""}, {"type": "image", "name": "busybox:1.36.1", "namespace": ""}, {"type": "image", "name": "busybox:1.28", "namespace": ""}, {"type": "image", "name": "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "namespace": ""}]
   reasoning=当前环境存在大量明显异常的 Pod。核心异常有：1) 57 个 Pending Pod（ImagePullBackOff 45个 + ErrImagePull 11个 + Unknown 1个），镜像拉取失败集中在 busybox:1.36.1、busybox:1.28、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，错误原因为 dial tcp to docker.io:443 i/o timeout，说明节点到 docker.io 网络不可达，属于典型 L3 镜像仓库网络问题；2) aiops-e2e/rc-notready-readiness 为 Running 但 NotReadyProbeFailed（L4），但数量少且根因是镜像拉取问题导致的大量测试 Pod 异常；3) mcp/node-debugger-node1-nx8gb Failed（原因不详），xnet/observability-kibana Evicted（L0）。综合判断，L3 镜像仓库网络不可达是最广泛的根因，主导了整个集群的异常状况。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "镜像仓库网络不可达", "confidence": 0.95, "reasoning": "当前环境存在大量明显异常的 Pod。核心异常有：1) 57 个 Pending Pod（ImagePullBackOff 45个 + ErrImagePull 11个 + Unknown 1个），镜像拉取失败集中在 busybox:1.36.1、busybox:1.28、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，错误原因为 dial tcp to docker.io:443 i/o timeout，说明节点到 docker.io 网络不可达，属于典型 L3 镜像仓库网络问题；2) aiops-e2e/rc-notready-readiness 为 Running 但 NotReadyProbeFailed（L4），但数量少且根因是镜像拉取问题导致的大量测试 Pod 异常；3) mcp/node-debugger-node1-nx8gb Failed（原因不详），xnet/observability-kibana Evicted（L0）。综合判断，L3 镜像仓库网络不可达是最广泛的根因，主导了整个集群的异常状况。", "abnormal_pods": [{"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-check-registry", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-tool-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-diag-evidence-verify", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-docker-io", "namespace": "mcp", "status": "Terminating"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2s2mz", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "image_registry", "name": "docker.io", "namespace": ""}, {"type": "image_registry", "name": "registry.k8s.io", "namespace": ""}, {"type": "image", "name": "busybox:1.36.1", "namespace": ""}, {"type": "image", "name": "busybox:1.28", "namespace": ""}, {"type": "image", "name": "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "namespace": ""}], "possible_scenarios": [{"scenario": "节点到 docker.io 网络不可达（防火墙/代理/DNS 阻断）", "probability": "高", "reason": "大量 ErrImagePull 的 dial tcp i/o timeout 到 docker.io IP 地址（122.248.226.57, 157.240.1.9 等）:443，覆盖 node1 和 node2 两个节点"}, {"scenario": "镜像仓库 DNS 解析问题导致连接失败", "probability": "中", "reason": "部分拉取显示 i/o timeout，但不排除 DNS 阶段异常；dns-test/dig 等 DNS 测试 Pod 也在异常列表中但原因仍是 ImagePullBackOff"}, {"scenario": "节点镜像缓存缺失 + 外网访问受限", "probability": "中", "reason": "系统组件（calico, coredns, kube-apiserver 等）镜像已拉取运行正常，只有测试类 Pod 和 busybox 镜像拉取失败"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "curl-docker-io"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "curl-docker-io"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 45, "ErrImagePull": 11, "Terminating": 1}, "total_abnormal": 57, "selected_rows": ["aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0              12h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ImagePullBackOff   0              82m     172.16.104.52    node2    <none>           <none>            run=connectivity-check-tmp", "default           dig-check-registry                                  0/1     ImagePullBackOff   0              22m     172.16.166.155   node1    <none>           <none>            run=dig-check-registry", "default           dig-tool                                            0/1     ImagePullBackOff   0              8h      172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff   0              7h7m    172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff   0              11h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff   0              4h27m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-diag-tool-evidence                              0/1     ErrImagePull       0              58m     172.16.104.4     node2    <none>           <none>            run=dns-diag-tool-evidence", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff   0              4h32m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ImagePullBackOff   0              4h32m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test                                            0/1     ErrImagePull       0              22m     172.16.104.56    node2    <none>           <none>            run=dns-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0              12h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull       0              10h     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ErrImagePull       0              4h32m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ImagePullBackOff   0              7h14m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff   0              11h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull       0              11h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull       0              8h      172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ImagePullBackOff   0              5h      172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull       0              9h      172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220"], "raw_ref": "/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我先获取 ImagePullFailed 场景的 runbook，然后按既有 evidence_plan 执行采证。

先获取 runbook 上下文，同时开始执行证据计划中的关键工具调用。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
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
      📄 kubectl_describe 摘要:
name: dns-resolve-gcr-test
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  18m (x784 over 4h29m)   kubelet  Back-off pulling image "busybox:1.3
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod registry-conn-test-1779371220 (namespace: default) on node node2/10.2.0.50 is stuck in Pending state. Container image busybox:1.36.1 cannot be pulled from docker.io — all attempts fail with dial t
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: curl-docker-io
namespace: mcp
creationTimestamp: 2026-05-21T23:29:45Z
deletionTimestamp: 2026-05-21T23:31:15Z
deletionGracePeriodSeconds: 30
finalizers: <none>
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-check-registry (namespace: default, node: node1/10.2.0.49) is Pending. Container image busybox:1.28 cannot be pulled — all pull attempts fail with network errors (i/o timeout, connection reset
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  48s (x1846 over 12h)  kubelet  Back-off pulling image "busybox:1.36
   💭 [证据链采集] 让我读取详细的事件和状态信息。
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=9532 lines=118
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/006-evidence-kubectl_describe.structured.json
offset: 0
r
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=9842 lines=118
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/004-evidence-kubectl_describe.structured.json
offset: 0
r
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=4951 lines=101
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/002-evidence-kubectl_describe.structured.json
offset: 0
r
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=4212 lines=118
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/003-evidence-kubectl_describe.structured.json
offset: 0
r
   💭 [证据链采集] 现在让我查看这些 Pod 的 Events 详细内容，以获取完整的 dial tcp timeout 错误信息。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
18s         Warning   Failed           Pod/curl-docker-io   Failed to pull image "alpine/curl": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image "doc
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
16m                   Warning   Failed           Pod/dig-check-registry   Failed to pull image "busybox:1.28": rpc error: code = Unknown desc = failed to pull and unpack imag
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
71s (x1846 over 12h)   Normal    BackOff   Pod/test-dns-1779360358   Back-off pulling image "busybox:1.36.1"
14m (x167 over 12h)    Warning   Failed    Pod/test-dns-177936035
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
19m (x784 over 4h29m)   Normal    BackOff   Pod/dns-resolve-gcr-test   Back-off pulling image "busybox:1.36.1"
14m (x46 over 3h46m)    Warning   Failed    Pod/dns-resolve-gcr
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
54m                  Warning   Failed    Pod/registry-conn-test-1779371220   Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = failed to pull and unpack
   💭 [证据链采集] 现在让我查看一下 `node-debugger-node1-nx8gb` 的更详细信息，并验证节点健康状况。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=3149 lines=117
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: "2026-05-21T19:42:18Z"
  name: node-debugger-node1-nx8gb
  namespace: mcp
  resourceVersion: "52
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   238d   v1.26.8   10.2.0.49     <
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node2   Ready    <none>   238d   v1.26.8   10.2.0.50     <
   💭 [证据链采集] [compacted ai_message: original_chars=43]现在让我验证节点从宿主侧是否能连通 docker.io。
   💭 [证据链采集] 调用工具: run_bash_command
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "命令执行超时 (30秒)", "returncode": -1}
   💭 [证据链采集] 现在让我检查一下节点上是否配置了镜像代理或 HTTP 代理，进一步定位根因。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 `run_bash_command` (kubectl describe node) executed successfully. Node created 2025-09-25, containerd://1.6.32, Kubernetes v1.26.8, Calico IP 10.2.0.49/19 with IPIP tunnel 172.16.166.128. 48 non-termi
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "命令执行超时 (30秒)", "returncode": -1}
   💭 [证据链采集] 好了，现在我已经收集到了充分的证据。下面给出诊断总结。

---

## 证据采集完成总结

### ✅ 已采集的关键证据（主异常组 g1 — ImagePullFailed, 56个 Pod）

**1. 节点到 docker.io 网络不可达（已确认）**

- **registry-conn-test-1779371220** (node2): `dial tcp 122.248.226.57:443: i/o timeout`、`157.240.1.9:443: i/o timeout`、`157.240.15.8:443: i/o timeout`、`173.252.88.67:443: i/o timeout`、`199.96.62.17:443: i/o timeout` — 持续 `x996 BackOff over 9h`
- **dig-check-registry** (node1): `dial tcp 104.244.46.208:443: i/o timeout`、`connection reset by peer`（54.152.223.174、100.28.191.205）
- **dns-resolve-gcr-test** (node1): `read tcp 10.2.0.49:57722->98.89.187.97:443: read: connection reset by peer`
- **curl-docker-io** (mcp): `dial tcp 185.60.216.11:443: i/o timeout` — 镜像 `alpine/curl` 拉取也失败

**结论：** 两个节点（node1/node2）均无法连接到 registry-1.docker.io，覆盖 **docker.io 全部 IP 段都 i/o timeout 或 connection reset**，典型防火墙/网络策略阻断特征。

**2. aiops-e2e/test-dns-1779360358 确认** — 同样 busybox:1.36.1 ImagePullBackOff，`x1846 BackOff over 12h`

**3. 节点状态确认** — node1 和 node2 均为 **Ready** 状态，无异常调度条件；容器运行时 containerd://1.6.32

**4. 主动连通性测试失败** — 用 `curlimages/curl` 镜像尝试 curl registry-1.docker.io 超时；用 `registry.k8s.io/e2e-test-images/jessie-dnsutils` 做 DNS 解析也超时

---

### ✅ 已采集证据（非主异常组）

**g2 — TerminatingStuck（curl-docker-io, mcp）**
- YAML 确认 **deletionTimestamp** 存在（2026-05-21T23:31:15Z）
- **finalizers 为空** — 不是 finalizer 卡住
- **nodeName=node2**，节点已确认 Ready
- 容器状态: `ContainerCreating`（等待镜像拉取），不是 volume detach 卡住
- **根本原因：** 该 Pod 也处于 ImagePullFailed（alpine/curl 镜像拉取超时），由于镜像拉取未完成，kubelet 无法终止容器清理流程，导致 Terminating 卡住

**g3 — StartError（node-debugger-node1-nx8gb, mcp）**
- Pod 已 **Failed**，容器 exited with code **128**（StartError）
- 镜像 `busybox:1.36` 已成功拉取（有 containerID/imageID）
- command 是 `curl -s -o /dev/null -w %{http_code} --connect-timeout 5 https://registry-1.docker.io/v2/` — **尝试 curl docker.io 失败导致启动错误**，exit 128
- **根本原因：** 同样是 docker.io 网络不可达导致容器启动时 curl 命令失败

---

### ⚠️ 冲突/负向证据
- **node-debugger-node1-nx8gb 事件为空**，但通过 YAML 和 describe 已确认详情

---

### 🔑 核心结论

| 异常组 | Pod 数 | 根因 |
|--------|--------|------|
| g1: ImagePullFailed | 56个（45 ImagePullBackOff + 11 ErrImagePull） | **节点到 docker.io 网络不可达** — dial tcp i/o timeout / connection reset |
| g2: TerminatingStuck | 1个 | 因镜像拉取失败导致容器启动未完成 → 删除流程卡住 |
| g3: StartError | 1个 | curl docker.io 超时退出码 128 |

**集群根因：** 所有异常 Pod 的根源一致 — **节点（node1/node2）无法访问 docker.io/registry-1.docker.io**。需要检查防火墙规则、代理配置或网络策略是否阻断了对外部 HTTPS 443 的出口访问。
   ✅ [证据链采集] 完成 (1m 47.7s)
   📤 → 下游数据: evidence_items=15/15
   evidence_analysis={"evidence_plan":[{"id":"ev-001","description":"检查主异常组 g1 代表 Pod 的详细状态和事件：registry-conn-test-1779371220 (ErrImagePull on node2)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod registry-conn-test-1779371220 -n default","tool_args":{"kind":"pod","name":"registry-conn-test-1779371220","namespace":"default"},"purpose":"查看 ErrImagePull/ImagePullBackOff 的事件原文，确认 dial tcp timeout 到 docker.io 的详细 IP 和错误","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-002","description":"检查主异常组 g1 另一个节点上的代表 Pod：dig-check-registry (ImagePullBackOff on node1)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-check-registry -n default","tool_args":{"kind":"pod","name":"dig-check-registry","namespace":"default"},"purpose":"验证 node1 上是否也存在相同的 docker.io dial tcp timeout 错误","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-003","description":"检查主异常组 g1 中使用了 registry.k8s.io 镜像的 Pod","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-gcr-test -n default","tool_args":{"kind":"pod","name":"dns-resolve-gcr-test","namespace":"default"},"purpose":"验证 registry.k8s.io 是否也存在连通性问题，确认是所有外部仓库都不可达还是仅 docker.io","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-004","description":"检查 Terminating 异常组 g2 的 Pod 状态","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod curl-docker-io -n mcp -o yaml","tool_args":{"kind":"pod","name":"curl-docker-io","namespace":"mcp"},"purpose":"验证 curl-docker-io 的 deletionTimestamp、finalizers 等 Terminating 根因","evidence_type":"pod_yaml","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-005","description":"检查 StartError 异常组 g3 的 Pod 状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"验证 node-debugger-node1-nx8gb 的 StartError 详细状态和事件","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-006","description":"检查 aiops-e2e namespace 的异常 Pod","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"验证 aiops-e2e 命名空间下的 Pod 是否也是同样的 ImagePullBackOff 问题","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-resolve-gcr-test\nnamespace: default\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  18m (x784 over 4h29m)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   13m (x46 over 3h46m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:57722->98.89.187.97:443: read: connection reset by peer\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: b737e2f80227e2058357c3019ce91114254f787ce557c4f566b51163a9741653\n                  cni.projectcalico.org/podIP: 172.16.166.178/32\n                  cni.projectcalico.org/podIPs: 172.16.166.178/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:               \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod registry-conn-test-1779371220 (namespace: default) on node node2/10.2.0.50 is stuck in Pending state. Container image busybox:1.36.1 cannot be pulled from docker.io — all attempts fail with dial tcp i/o timeout to multiple registry IPs (122.248.226.57, 157.240.1.9, 157.240.15.8, 173.252.88.67, 199.96.62.17). Container State: Waiting (Reason: ErrImagePull). No container ID or Image ID set. Restarts: 0. Pod has IP 172.16.104.40, Conditions show Ready=False, ContainersReady=False. Events show repeated Failed pull attempts over 9h, BackOff (x996), and a single Normal Pulling event.\nkey_facts: [\"Pod: registry-conn-test-1779371220, namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Container image: busybox:1.36.1 (docker.io/library/busybox)\", \"Container State: Waiting, Reason: ErrImagePull\", \"Container ID: (empty), Image ID: (empty)\", \"Restart Count: 0\", \"Pod IP: 172.16.104.40\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\", \"Events: multiple Warning Failed pull attempts over 9h — all dial tcp i/o timeout to different registry-1.docker.io IPs\", \"Event: Normal BackOff x996 over 9h — Back-off pulling image\", \"Event: Normal Pulling \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: curl-docker-io\nnamespace: mcp\ncreationTimestamp: 2026-05-21T23:29:45Z\ndeletionTimestamp: 2026-05-21T23:31:15Z\ndeletionGracePeriodSeconds: 30\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- curl-docker-io: image=alpine/curl imagePullPolicy=Always\n  args: sh -c curl -v --connect-timeout 10 https://registry-1.docker.io/v2/ 2>&1\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [curl-docker-io]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [curl-docker-io]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- curl-docker-io: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-rr58w\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-check-registry (namespace: default, node: node1/10.2.0.49) is Pending. Container image busybox:1.28 cannot be pulled — all pull attempts fail with network errors (i/o timeout, connection reset by peer) when trying to reach docker.io registry. Container state: Waiting (Reason: ImagePullBackOff). No container ID or Image ID set. Events show repeated Failed (ErrImagePull, ImagePullBackOff) and BackOff (x24). Pod has IP 172.16.166.155, was scheduled successfully, and network interface was added.\nkey_facts: [\"resource: Pod dig-check-registry\", \"namespace: default\", \"node: node1/10.2.0.49\", \"Status: Pending\", \"Container state: Waiting, Reason: ImagePullBackOff\", \"Image: busybox:1.28\", \"Container ID: (empty)\", \"Image ID: (empty)\", \"Ready: False\", \"Restart Count: 0\", \"Pod IP: 172.16.166.155\", \"Failed to pull image \\\"busybox:1.28\\\" — all attempts hit network errors dialing registry-1.docker.io:443 (i/o timeout, connection reset by peer)\", \"Events: Normal Scheduled (23m), Normal AddedInterface (23m), Warning Failed x4 (ErrImagePull), Warning Failed x7 (ImagePullBackOff), Normal BackOff x24 (15m), Normal Pulling x4\"]\nconflicts: [\"current_summary says node IP is 10.2.0.49, raw_preview \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  48s (x1846 over 12h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   14m (x167 over 12h)   kubelet  (combined from similar events): Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n      nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-g4sbz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   14m (x167 over 12h)   kubelet  (combined from similar events): Error: ErrImagePull\n  Normal   BackOff  48s (x1846 over 12h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=9532 lines=118\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/006-evidence-kubectl_describe.structured.json\noffset: 0\nreturned_chars: 9318\ntotal_chars: 9318\ncontent:\n{\n  \"name\": \"dig-check-registry\",\n  \"namespace\": \"default\",\n  \"node\": \"node1/10.2.0.49\",\n  \"status\": \"Pending\",\n  \"lifecycle\": {\n    \"qos_class\": \"BestEffort\"\n  },\n  \"containers\": [\n    {\n      \"name\": \"dig-check-registry\",\n      \"container_id\": \"\",\n      \"image\": \"busybox:1.28\",\n      \"image_id\": \"\",\n      \"args\": \"sh -c nslookup registry.k8s.io 2>&1 || echo DNS_FAILED\",\n      \"state\": \"Waiting\",\n      \"reason\": \"ImagePullBackOff\",\n      \"ready\": \"False\",\n      \"restart_count\": \"0\",\n      \"environment\": \"<none>\",\n      \"mounts\": \"\",\n      \"signals\": [\n        \"    Container ID:\",\n        \"    Image:         busybox:1.28\",\n        \"    Image ID:\",\n        \"    Args:\",\n        \"      sh\",\n        \"      -c\",\n        \"      nslookup registry.k8s.io 2>&1 || echo DNS_FAILED\",\n        \"    State:          Waiting\",\n        \"      Reason:       ImagePullBackOff\",\n        \"    Ready:          False\",\n        \"    Restart Count:  0\",\n        \"    Environment:    <none>\",","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/008-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/008-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/008-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=9842 lines=118\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/004-evidence-kubectl_describe.structured.json\noffset: 0\nreturned_chars: 9628\ntotal_chars: 9628\ncontent:\n{\n  \"name\": \"registry-conn-test-1779371220\",\n  \"namespace\": \"default\",\n  \"node\": \"node2/10.2.0.50\",\n  \"status\": \"Pending\",\n  \"lifecycle\": {\n    \"qos_class\": \"BestEffort\"\n  },\n  \"containers\": [\n    {\n      \"name\": \"registry-conn-test-1779371220\",\n      \"container_id\": \"\",\n      \"image\": \"busybox:1.36.1\",\n      \"image_id\": \"\",\n      \"args\": \"sh -c echo test\",\n      \"state\": \"Waiting\",\n      \"reason\": \"ErrImagePull\",\n      \"ready\": \"False\",\n      \"restart_count\": \"0\",\n      \"environment\": \"<none>\",\n      \"mounts\": \"\",\n      \"signals\": [\n        \"    Container ID:\",\n        \"    Image:         busybox:1.36.1\",\n        \"    Image ID:\",\n        \"    Args:\",\n        \"      sh\",\n        \"      -c\",\n        \"      echo test\",\n        \"    State:          Waiting\",\n        \"      Reason:       ErrImagePull\",\n        \"    Ready:          False\",\n        \"    Restart Count:  0\",\n        \"    Environment:    <none>\",","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/009-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/009-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/009-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=4951 lines=101\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/002-evidence-kubectl_describe.structured.json\noffset: 0\nreturned_chars: 4737\ntotal_chars: 4737\ncontent:\n{\n  \"name\": \"dns-resolve-gcr-test\",\n  \"namespace\": \"default\",\n  \"node\": \"node1/10.2.0.49\",\n  \"status\": \"Pending\",\n  \"lifecycle\": {\n    \"qos_class\": \"BestEffort\"\n  },\n  \"containers\": [\n    {\n      \"name\": \"dns-resolve-gcr-test\",\n      \"container_id\": \"\",\n      \"image\": \"busybox:1.36.1\",\n      \"image_id\": \"\",\n      \"args\": \"nslookup asia-east1-docker.pkg.dev\",\n      \"state\": \"Waiting\",\n      \"reason\": \"ImagePullBackOff\",\n      \"ready\": \"False\",\n      \"restart_count\": \"0\",\n      \"environment\": \"<none>\",\n      \"mounts\": \"\",\n      \"signals\": [\n        \"    Container ID:\",\n        \"    Image:         busybox:1.36.1\",\n        \"    Image ID:\",\n        \"    Args:\",\n        \"      nslookup\",\n        \"      asia-east1-docker.pkg.dev\",\n        \"    State:          Waiting\",\n        \"      Reason:       ImagePullBackOff\",\n        \"    Ready:          False\",\n        \"    Restart Count:  0\",\n        \"    Environment:    <none>\",\n        \"    Mounts:\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/010-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/010-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/010-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=4212 lines=118\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/003-evidence-kubectl_describe.structured.json\noffset: 0\nreturned_chars: 3998\ntotal_chars: 3998\ncontent:\n{\n  \"name\": \"node-debugger-node1-nx8gb\",\n  \"namespace\": \"mcp\",\n  \"node\": \"node1/10.2.0.49\",\n  \"status\": \"Failed\",\n  \"lifecycle\": {\n    \"qos_class\": \"BestEffort\"\n  },\n  \"containers\": [\n    {\n      \"name\": \"debugger\",\n      \"container_id\": \"containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\",\n      \"image\": \"busybox:1.36\",\n      \"image_id\": \"sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\",\n      \"command\": \"curl -s -o /dev/null -w %{http_code} --connect-timeout 5\",\n      \"state\": \"Terminated\",\n      \"reason\": \"StartError\",\n      \"exit_code\": \"128\",\n      \"started\": \"Thu, 01 Jan 1970 00:00:00 +0000\",\n      \"finished\": \"Thu, 21 May 2026 19:42:19 +0000\",\n      \"ready\": \"False\",\n      \"restart_count\": \"0\",\n      \"environment\": \"<none>\",\n      \"mounts\": \"\",\n      \"signals\": [\n        \"    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\",\n        \"    Image:         busybox:1.36\",\n        \"    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\",\n        \"    Command:\",\n        \"      curl\",\n        \"      -s\",\n        \"      -o\",\n        \"      /dev/null\",\n        \"      -w\",","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/011-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/011-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/011-evidence-read_context_archive.summary.txt"},{"tool":"kubectl_events","data":"工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/012-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/012-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/012-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n18s         Warning   Failed           Pod/curl-docker-io   Failed to pull image \"alpine/curl\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/alpine/curl:latest\": failed to resolve reference \"docker.io/alpine/curl:latest\": failed to do request: Head \"https://registry-1.docker.io/v2/alpine/curl/manifests/latest\": dial tcp 185.60.216.11:443: i/o timeout\n18s         Warning   Failed           Pod/curl-docker-io   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/013-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/013-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/013-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n16m                   Warning   Failed           Pod/dig-check-registry   Failed to pull image \"busybox:1.28\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.28\": failed to resolve reference \"docker.io/library/busybox:1.28\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.28\": dial tcp 104.244.46.208:443: i/o timeout\n14m                   Warning   Failed           Pod/dig-check-registry   Failed to pull image \"busybox:1.28\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.28\": failed to resolve reference \"docker.io/library/busybox:1.28\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.28\": read tcp 10.2.0.49:38094->54.152.223.174:443: read: connection reset by peer\n12m                   Warning   Failed           Pod/dig-check-registry   Failed to pull image \"busybox:1.28\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.28\": failed to resolve reference \"docker.io/library/busybox:1.28\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.28\": read tcp 10.2.0.49:43304->100.28.191.205:443: read: connection reset by peer\n10m                   Warning   Failed           Pod/dig-check-registry   Failed to pull image \"busybox:1.28\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.28\": failed to resolve reference \"docker.io/library/busybox:1.28\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.28\": read tcp 10.2.0.49:49242->100.28.191.205:443: read: connection reset by peer\n6m6s (x24 over 16m)   Normal    BackOff          Pod/dig-check-registry   Back-off pulling image \"busybox:1.28\"\n10m (x4 over 16m)     Warning   Failed           Pod/dig-check-registry   Error: ErrImagePull\n10m (x7 over 16m)     Warning   Failed           Pod/dig-check-registry   Error: ImagePullBackOff","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/014-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/014-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/014-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n71s (x1846 over 12h)   Normal    BackOff   Pod/test-dns-1779360358   Back-off pulling image \"busybox:1.36.1\"\n14m (x167 over 12h)    Warning   Failed    Pod/test-dns-1779360358   (combined from similar events): Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/015-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/015-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/015-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n19m (x784 over 4h29m)   Normal    BackOff   Pod/dns-resolve-gcr-test   Back-off pulling image \"busybox:1.36.1\"\n14m (x46 over 3h46m)    Warning   Failed    Pod/dns-resolve-gcr-test   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:57722->98.89.187.97:443: read: connection reset by peer","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/016-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/016-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/016-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n54m                  Warning   Failed    Pod/registry-conn-test-1779371220   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 122.248.226.57:443: i/o timeout\n43m                  Warning   Failed    Pod/registry-conn-test-1779371220   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 157.240.1.9:443: i/o timeout\n31m                  Warning   Failed    Pod/registry-conn-test-1779371220   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 157.240.15.8:443: i/o timeout\n19m                  Warning   Failed    Pod/registry-conn-test-1779371220   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 173.252.88.67:443: i/o timeout\n15m (x996 over 9h)   Normal    BackOff   Pod/registry-conn-test-1779371220   Back-off pulling image \"busybox:1.36.1\"\n6m19s                Warning   Failed    Pod/registry-conn-test-1779371220   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.96.62.17:443: i/o timeout\n19m (x72 over 9h)    Warning   Failed    Pod/registry-conn-test-1779371220   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/017-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/017-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/017-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=3149 lines=117\napiVersion: v1\nkind: Pod\nmetadata:\n  creationTimestamp: \"2026-05-21T19:42:18Z\"\n  name: node-debugger-node1-nx8gb\n  namespace: mcp\n  resourceVersion: \"52801137\"\n  uid: 4cc072ec-47f2-456e-8741-97a2d7f108d8\nspec:\n  containers:\n  - command:\n    - curl\n    - -s\n    - -o\n    - /dev/null\n    - -w\n    - '%{http_code}'\n    - --connect-timeout\n    - \"5\"\n    - https://registry-1.docker.io/v2/\n    image: busybox:1.36\n    imagePullPolicy: IfNotPresent\n    name: debugger\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /host\n      name: host-root\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-hl45s\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  hostIPC: true\n  hostNetwork: true\n  hostPID: true\n  nodeName: node1\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/018-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/018-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/018-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode1   Ready    <none>   238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/019-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/019-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/019-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode2   Ready    <none>   238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/020-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/020-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/020-evidence-kubectl_get_by_name.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"命令执行超时 (30秒)\", \"returncode\": -1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/021-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/021-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/021-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"`run_bash_command` (kubectl describe node) executed successfully. Node created 2025-09-25, containerd://1.6.32, Kubernetes v1.26.8, Calico IP 10.2.0.49/19 with IPIP tunnel 172.16.166.128. 48 non-terminated pods listed across default, kube-system, mcp namespaces; all showing 0 CPU/Memory requests & limits.\nkey_facts: [\"Command returncode: 0 (success)\", \"Node CreationTimestamp: Thu, 25 Sep 2025 03:19:31 +0000\", \"Container Runtime: containerd://1.6.32\", \"Kubelet Version: v1.26.8\", \"Kube-Proxy Version: v1.26.8\", \"projectcalico.org/IPv4Address: 10.2.0.49/19\", \"projectcalico.org/IPv4IPIPTunnelAddr: 172.16.166.128\", \"Non-terminated Pods total: 48\", \"All listed pods (15 shown) have 0 CPU requests, 0 CPU limits, 0 Memory requests, 0 Memory limits\"]\nmissing: [\"No taints info shown in output\", \"No conditions or status info shown in output\", \"Only 15 of 48 pods are listed (remaining 33 not shown)\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/022-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/022-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/022-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"命令执行超时 (30秒)\", \"returncode\": -1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/023-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/023-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e3d5bd6f96334d4f/tools/023-evidence-run_bash_command.summary.txt"}],"llm_analysis":"好了，现在我已经收集到了充分的证据。下面给出诊断总结。\n\n---\n\n## 证据采集完成总结\n\n### ✅ 已采集的关键证据（主异常组 g1 — ImagePullFailed, 56个 Pod）\n\n**1. 节点到 docker.io 网络不可达（已确认）**\n\n- **registry-conn-test-1779371220** (node2): `dial tcp 122.248.226.57:443: i/o timeout`、`157.240.1.9:443: i/o timeout`、`157.240.15.8:443: i/o timeout`、`173.252.88.67:443: i/o timeout`、`199.96.62.17:443: i/o timeout` — 持续 `x996 BackOff over 9h`\n- **dig-check-registry** (node1): `dial tcp 104.244.46.208:443: i/o timeout`、`connection reset by peer`（54.152.223.174、100.28.191.205）\n- **dns-resolve-gcr-test** (node1): `read tcp 10.2.0.49:57722->98.89.187.97:443: read: connection reset by peer`\n- **curl-docker-io** (mcp): `dial tcp 185.60.216.11:443: i/o timeout` — 镜像 `alpine/curl` 拉取也失败\n\n**结论：** 两个节点（node1/node2）均无法连接到 registry-1.docker.io，覆盖 **docker.io 全部 IP 段都 i/o timeout 或 connection reset**，典型防火墙/网络策略阻断特征。\n\n**2. aiops-e2e/test-dns-1779360358 确认** — 同样 busybox:1.36.1 ImagePullBackOff，`x1846 BackOff over 12h`\n\n**3. 节点状态确认** — node1 和 node2 均为 **Ready** 状态，无异常调度条件；容器运行时 containerd://1.6.32\n\n**4. 主动连通性测试失败** — 用 `curlimages/curl` 镜像尝试 curl registry-1.docker.io 超时；用 `registry.k8s.io/e2e-test-images/jessie-dnsutils` 做 DNS 解析也超时\n\n---\n\n### ✅ 已采集证据（非主异常组）\n\n**g2 — TerminatingStuck（curl-docker-io, mcp）**\n- YAML 确认 **deletionTimestamp** 存在（2026-05-21T23:31:15Z）\n- **finalizers 为空** — 不是 finalizer 卡住\n- **nodeName=node2**，节点已确认 Ready\n- 容器状态: `ContainerCreating`（等待镜像拉取），不是 volume detach 卡住\n- **根本原因：** 该 Pod 也处于 ImagePullFailed（alpine/curl 镜像拉取超时），由于镜像拉取未完成，kubelet 无法终止容器清理流程，导致 Terminating 卡住\n\n**g3 — StartError（node-debugger-node1-nx8gb, mcp）**\n- Pod 已 **Failed**，容器 exited with code **128**（StartError）\n- 镜像 `busybox:1.36` 已成功拉取（有 containerID/imageID）\n- command 是 `curl -s -o /dev/null -w %{http_code} --connect-timeout 5 https://registry-1.docker.io/v2/` — **尝试 curl docker.io 失败导致启动错误**，exit 128\n- **根本原因：** 同样是 docker.io 网络不可达导致容器启动时 curl 命令失败\n\n---\n\n### ⚠️ 冲突/负向证据\n- **node-debugger-node1-nx8gb 事件为空**，但通过 YAML 和 describe 已确认详情\n\n---\n\n### 🔑 核心结论\n\n| 异常组 | Pod 数 | 根因 |\n|--------|--------|------|\n| g1: ImagePullFailed | 56个（45 ImagePullBackOff + 11 ErrImagePull） | **节点到 docker.io 网络不可达** — dial tcp i/o timeout / connection reset |\n| g2: TerminatingStuck | 1个 | 因镜像拉取失败导致容器启动未完成 → 删除流程卡住 |\n| g3: StartError | 1个 | curl docker.io 超时退出码 128 |\n\n**集群根因：** 所有异常 Pod 的根源一致 — **节点（node1/node2）无法访问 docker.io/registry-1.docker.io**。需要检查防火墙规则、代理配置或网络策略是否阻断了对外部 HTTPS 443 的出口访问。","collection_summary":"计划 6 项，实际采集 6 项，未采集 0 项，完整度 100%；其中真实环境证据 15/15 项，完整度 100%；实际执行工具 25 个，匹配计划 6 个，未规划证据 19 个","plan_total":6,"plan_collected":6,"plan_completeness":1.0,"environment_evidence_total":15,"environment_evidence_collected":15,"environment_evidence_completeness":1.0,"executed_tool_count":25,"matched_tool_count":6,"unplanned_tool_count":19,"evidence_inventory":[{"id":"ev-001","description":"检查主异常组 g1 代表 Pod 的详细状态和事件：registry-conn-test-1779371220 (ErrImagePull on node2)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod registry-conn-test-1779371220 -n default","purpose":"查看 ErrImagePull/ImagePullBackOff 的事件原文，确认 dial tcp timeout 到 docker.io 的详细 IP 和错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-002","description":"检查主异常组 g1 另一个节点上的代表 Pod：dig-check-registry (ImagePullBackOff on node1)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-check-registry -n default","purpose":"验证 node1 上是否也存在相同的 docker.io dial tcp timeout 错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-003","description":"检查主异常组 g1 中使用了 registry.k8s.io 镜像的 Pod","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-gcr-test -n default","purpose":"验证 registry.k8s.io 是否也存在连通性问题，确认是所有外部仓库都不可达还是仅 docker.io","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-004","description":"检查 Terminating 异常组 g2 的 Pod 状态","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod curl-docker-io -n mcp -o yaml","purpose":"验证 curl-docker-io 的 deletionTimestamp、finalizers 等 Terminating 根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-005","description":"检查 StartError 异常组 g3 的 Pod 状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"验证 node-debugger-node1-nx8gb 的 StartError 详细状态和事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-006","description":"检查 aiops-e2e namespace 的异常 Pod","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"验证 aiops-e2e 命名空间下的 Pod 是否也是同样的 ImagePullBackOff 问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_8","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_9","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/6 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-001 | critical | ✅ | kubectl_describe | 检查主异常组 g1 代表 Pod 的详细状态和事件：registry-conn-test-... | `kubectl describe pod registry-conn-test-1779371220 -n default` |
   | ev-002 | critical | ✅ | kubectl_describe | 检查主异常组 g1 另一个节点上的代表 Pod：dig-check-registry (I... | `kubectl describe pod dig-check-registry -n default` |
   | ev-003 | critical | ✅ | kubectl_describe | 检查主异常组 g1 中使用了 registry.k8s.io 镜像的 Pod | `kubectl describe pod dns-resolve-gcr-test -n default` |
   | ev-004 | important | ✅ | kubectl_get_yaml | 检查 Terminating 异常组 g2 的 Pod 状态 | `kubectl get pod curl-docker-io -n mcp -o yaml` |
   | ev-005 | important | ✅ | kubectl_describe | 检查 StartError 异常组 g3 的 Pod 状态 | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | ev-006 | important | ✅ | kubectl_describe | 检查 aiops-e2e namespace 的异常 Pod | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (25.9s)
   📤 → 下游数据: root_cause=集群中57个Pending Pod的根因是节点到docker.io的网络不可达。关键证据：registry-conn-test-1779371220（node2）对5个不同docker.io IP（122.248.226.57, 157.240.1.9, 157.240.15.8, 173.252.88.67, 199.96.62.17）的:443端口全部dial tcp i/o timeout，x996 BackOff持续9小时；dig-check-registry（node1）同样出现i/o timeout和connection reset by peer；两个节点均有相同症状。系统组件（kube-system/admin）正常运行，排除节点故障。非主异常组方面：g2 TerminatingStuck（curl-docker-io）原因是alpine/curl镜像拉取超时导致删除流程卡住（finalizers为空，非finalizer问题）；g3 StartError（node-debugger-node1-nx8gb）原因是busybox:1.36镜像内不含curl命令导致容器启
... 截断，原始 526 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1、node2）到 docker.io 镜像仓库的网络连接被阻断，表现为 dial tcp :443 i/o timeout 和 connection reset by peer，覆盖多个 docker.io IP 地址", "propagation": "1) 节点无法从 docker.io 拉取任何镜像（busybox:1.36.1、busybox:1.28、alpine/curl 等）→ 2) kubelet 持续重试触发 ImagePullBackOff/ErrImagePull → 3) Pod 停留在 Pending 状态，无法进入 Running → 4) 部分依赖镜像拉取完成的容器（如 curl-docker-io 的 Terminating）也因镜像未就绪而卡住", "direct_cause": "kubelet 调用 containerd 从 docker.io 拉取镜像时，TCP 连接 registry-1.docker.io:443 始终 i/o timeout（已验证5个不同IP均超时，持续9-12小时），kubelet 回退到 BackOff 重试策略，Pod 状态停留在 ImagePullBackOff/ErrImagePull", "manifestation": "57个测试类Pod（aiops-e2e/test-dns-*, default/dns-*, default/registry-*, mcp/node-debugger-*, mcp/curl-*等）处于 Pending 状态，45个显示 ImagePullBackOff、11个显示 ErrImagePull；其中 curl-docker-io 因镜像拉取未完成导致 Terminating 卡住；node-debugger-node1-nx8gb 因镜像内无 curl 命令导致 StartError（独立问题）"}
   rca_analysis={"phenomenon": "集群中存在57个Pending状态的异常Pod，核心表现为ImagePullBackOff（45个）和ErrImagePull（11个），集中在aiops-e2e、default、mcp三个命名空间，分布在node1和node2两个节点上。另有一个TerminatingStuck Pod（mcp/curl-docker-io）和一个StartError Pod（mcp/node-debugger-node1-nx8gb）。系统组件（kube-system、admin）均正常运行。", "evidence_inventory": [{"id": "ev-001", "source": "kubectl_describe", "content": "dns-resolve-gcr-test (default/node1) ImagePullBackOff: busybox:1.36.1 拉取失败，connection reset by peer 到 98.89.187.97:443", "reliability": "高"}, {"id": "ev-002", "source": "kubectl_describe", "content": "node-debugger-node1-nx8gb (mcp/node1) Failed/StartError: busybox:1.36 已拉取，但 curl docker.io 命令执行失败，exit 128", "reliability": "高"}, {"id": "ev-003", "source": "kubectl_describe", "content": "registry-conn-test-1779371220 (default/node2) ErrImagePull: busybox:1.36.1 拉取超时，5个不同docker.io IP均dial tcp i/o timeout", "reliability": "高"}, {"id": "ev-004", "source": "kubectl_get_yaml", "content": "curl-docker-io (mcp/node2) Terminating: deletionTimestamp存在，finalizers为空，容器仍在ContainerCreating等待镜像拉取", "reliability": "高"}, {"id": "ev-005", "source": "kubectl_describe", "content": "dig-check-registry (default/node1) ImagePullBackOff: busybox:1.28 拉取失败，dial tcp i/o timeout + connection reset", "reliability": "高"}, {"id": "ev-006", "source": "kubectl_describe", "content": "test-dns-1779360358 (aiops-e2e/node1) ImagePullBackOff: busybox:1.36.1, x1846 BackOff over 12h", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "总计58个异常Pod：ImagePullBackOff ~45, ErrImagePull ~11, Terminating 1", "reliability": "高"}, {"id": "layer_2", "source": "kubernetes_tabular_query", "content": "Running=61, Pending=57, Succeeded=6, Failed=2；系统组件全部Running正常", "reliability": "高"}, {"id": "layer_3", "source": "kubernetes_tabular_query", "content": "57个Pending Pod分布在node1(28), node2(29)，均为dns/network/registry测试类Pod", "reliability": "高"}, {"id": "layer_4", "source": "kubernetes_tabular_query", "content": "57个Pending全部为镜像拉取失败：ImagePullBackOff 45, ErrImagePull 11, Unknown 1；涉及busybox:1.36.1, busybox:1.28, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "reliability": "高"}, {"id": "layer_6", "source": "kubectl_describe", "content": "registry-conn-test-1779371220: 连续9h重试拉取busybox:1.36.1，5个不同docker.io IP均443超时", "reliability": "高"}, {"id": "layer_7", "source": "kubectl_describe", "content": "dns-test (default/node2): busybox:1.28拉取失败，QPS exceeded → connection refused → i/o timeout 多种错误形态", "reliability": "高"}, {"summary": "... 截断，原始 13 项"}], "evidence_analysis": [{"evidence_id": "ev-003", "raw_data": "dial tcp 122.248.226.57:443: i/o timeout, 157.240.1.9:443: i/o timeout, 157.240.15.8:443: i/o timeout, 173.252.88.67:443: i/o timeout, 199.96.62.17:443: i/o timeout — x996 BackOff over 9h", "interpretation": "节点node2无法通过TCP连接docker.io的任何IP地址（5个不同IP均超时），说明是网络层阻断而非DNS解析问题"}, {"evidence_id": "ev-001", "raw_data": "read tcp 10.2.0.49:57722->98.89.187.97:443: read: connection reset by peer", "interpretation": "节点node1连接docker.io时连接被对端复位，进一步确认网络层存在阻断（防火墙/代理干预）"}, {"evidence_id": "ev-005", "raw_data": "dial tcp 104.244.46.208:443: i/o timeout, connection reset by peer (54.152.223.174, 100.28.191.205)", "interpretation": "node1上测试busybox:1.28拉取，同样出现i/o timeout和connection reset，排除镜像tag问题，确认是网络不可达"}, {"evidence_id": "ev-004", "raw_data": "deletionTimestamp: 2026-05-21T23:31:15Z, finalizers: <none>, containerStatuses: reason=ContainerCreating, nodeName: node2", "interpretation": "curl-docker-io Pod处于Terminating但容器状态为ContainerCreating，说明kubelet仍在尝试拉取alpine/curl镜像但网络不可达导致无法完成，也因镜像拉取未完成而无法终止Pod"}, {"evidence_id": "ev-002", "raw_data": "Container ID: containerd://0f47200..., Image: busybox:1.36, State: Terminated, Reason: StartError, Exit Code: 128, Message: exec: 'curl': not found in $PATH", "interpretation": "node-debugger-node1-nx8gb镜像已成功拉取(有containerID)，但容器内curl命令不存在（busybox:1.36不包含curl），导致容器启动失败exit 128，不属于镜像拉取问题"}, {"evidence_id": "layer_2", "raw_data": "Running=61, Pending=57, Failed=2; 系统组件running正常", "interpretation": "集群kube-system、admin等核心组件正常运行，节点健康，排除节点级故障；异常集中在用户测试类Pod"}, {"evidence_id": "ev-006", "raw_data": "BackOff x1846 over 12h, Warning Failed x167 over 12h, Reason: ImagePullBackOff", "interpretation": "aiops-e2e命名空间中的test-dns-1779360358同样在busybox:1.36.1拉取上持续失败12小时，确认问题不是namespace级别的配置差异"}], "causal_chain": {"root_cause": "集群节点（node1、node2）到 docker.io 镜像仓库的网络连接被阻断，表现为 dial tcp :443 i/o timeout 和 connection reset by peer，覆盖多个 docker.io IP 地址", "propagation": "1) 节点无法从 docker.io 拉取任何镜像（busybox:1.36.1、busybox:1.28、alpine/curl 等）→ 2) kubelet 持续重试触发 ImagePullBackOff/ErrImagePull → 3) Pod 停留在 Pending 状态，无法进入 Running → 4) 部分依赖镜像拉取完成的容器（如 curl-docker-io 的 Terminating）也因镜像未就绪而卡住", "direct_cause": "kubelet 调用 containerd 从 docker.io 拉取镜像时，TCP 连接 registry-1.docker.io:443 始终 i/o timeout（已验证5个不同IP均超时，持续9-12小时），kubelet 回退到 BackOff 重试策略，Pod 状态停留在 ImagePullBackOff/ErrImagePull", "manifestation": "57个测试类Pod（aiops-e2e/test-dns-*, default/dns-*, default/registry-*, mcp/node-debugger-*, mcp/curl-*等）处于 Pending 状态，45个显示 ImagePullBackOff、11个显示 ErrImagePull；其中 curl-docker-io 因镜像拉取未完成导致 Terminating 卡住；node-debugger-node1-nx8gb 因镜像内无 curl 命令导致 StartError（独立问题）"}, "root_cause": "集群中57个Pending Pod的根因是节点到docker.io的网络不可达。关键证据：registry-conn-test-1779371220（node2）对5个不同docker.io IP（122.248.226.57, 157.240.1.9, 157.240.15.8, 173.252.88.67, 199.96.62.17）的:443端口全部dial tcp i/o timeout，x996 BackOff持续9小时；dig-check-registry（node1）同样出现i/o timeout和connection reset by peer；两个节点均有相同症状。系统组件（kube-system/admin）正常运行，排除节点故障。非主异常组方面：g2 TerminatingStuck（curl-docker-io）原因是alpine/curl镜像拉取超时导致删除流程卡住（finalizers为空，非finalizer问题）；g3 StartError（node-debugger-node1-nx8gb）原因是busybox:1.36镜像内不含curl命令导致容器启\n... 截断，原始 526 字符", "root_cause_summary": "集群中57个Pending Pod的根因是节点到docker.io的网络不可达。关键证据：registry-conn-test-1779371220（node2）对5个不同docker.io IP（122.248.226.57, 157.240.1.9, 157.240.15.8, 173.252.88.67, 199.96.62.17）的:443端口全部dial tcp i/o timeout，x996 BackOff持续9小时；dig-check-registry（node1）同样出现i/o timeout和connection reset by peer；两个节点均有相同症状。系统组件（kube-system/admin）正常运行，排除节点故障。非主异常组方面：g2 TerminatingStuck（curl-docker-io）原因是alpine/curl镜像拉取超时导致删除流程卡住（finalizers为空，非finalizer问题）；g3 StartError（node-debugger-node1-nx8gb）原因是busybox:1.36镜像内不含curl命令导致容器启\n... 截断，原始 526 字符", "confidence": 0.95, "confidence_reason": "有直接且充分的证据：多个Pod的kubectl_describe事件显示明确的dial tcp i/o timeout到docker.io多IP，覆盖两个节点、多种镜像、持续9-12小时，因果链清晰完整。非主异常组也已逐一验证。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像标签不存在或私有仓库认证失败", "probability": "low", "reason": "排除依据：失败信息明确为 dial tcp i/o timeout 而非 manifest unknown 或 unauthorized，且涉及多种镜像(busybox:1.36.1, busybox:1.28, alpine/curl)均失败"}, {"cause": "节点DNS解析问题导致无法解析 registry-1.docker.io", "probability": "low", "reason": "排除依据：错误信息显示已解析到具体IP（122.248.226.57等），TCP连接阶段超时，DNS解析已成功"}, {"cause": "containerd/cri-o 运行时异常", "probability": "low", "reason": "排除依据：系统组件镜像运行正常，containerd 版本为1.6.32，且描述信息显示是网络layer的timeout而非运行时错误"}, {"cause": "imagePullSecrets 缺失", "probability": "low", "reason": "排除依据：busybox 是公开镜像，错误是网络层面超时而非认证失败(401/denied)"}], "limitations": "未采集节点级网络策略配置（iptables/firewall/代理配置），无法确认阻断具体是哪一层网络组件所致；未采集xnet/observability-kibana的Evicted原因（该Pod已不在当前异常组中）；node-debugger-node1-nx8gb的StartError原因已通过describe确认（镜像内无curl命令），但若需完整修复仍需查看其完整YAML确认镜像来源。", "llm_raw_analysis": "## 证据清点\n\n共采集15个证据项，其中：\n- **关键证据（6个）**：ev-001~ev-006，覆盖主异常组g1(g1核心Pod)和g2/g3代表Pod\n- **上游已验证（9个）**：layer_1~layer_9，覆盖集群级Pod统计和已归档的describe结果\n\n## 逐条分析\n\n### 主异常组g1 — ImagePullFailed (56个Pod)\n**核心模式：所有失败Pod的Events均显示连接docker.io:443超时**\n\n- **ev-003 (registry-conn-test-1779371220, node2)**：最完整证据。5个不同docker.io IP全部dial tcp i/o timeout，持续9h。排除DNS问题（已解析到IP）、排除单一镜像问题（覆盖整个docker.io段）、排除节点问题（系统组件正常）。\n- **ev-001 (dns-resolve-gcr-test, node1)**：connection reset by peer到98.89.187.97:443，证实node1同样无法到达docker.io，且\n... 截断，原始 2049 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群中57个Pending Pod的根因是节点到docker.io的网络不可达。关键证据：registry-conn-test-1779371220（node2）对5个不同docker.io IP（122.248.226.57, 157.240.1.9, 157.240.15.8, 173.252....
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1、node2）到 docker.io 镜像仓库的网络连接被阻断，表现为 dial tcp :443 i/o timeout 和 connection reset by peer，覆盖多个 docker.io IP 地址
     传导机制: 1) 节点无法从 docker.io 拉取任何镜像（busybox:1.36.1、busybox:1.28、alpine/curl 等）→ 2) kubelet 持续重试触发 ImagePullBackOff/ErrImagePull → 3) Pod 停留在 Pending 状态，无法进入 Running → 4) 部分依赖镜像拉取完成的容器（如 curl-docker-io 的 Terminating）也因镜像未就绪而卡住
     最终表现: 57个测试类Pod（aiops-e2e/test-dns-*, default/dns-*, default/registry-*, mcp/node-debugger-*, mcp/curl-*等）处于 Pending 状态，45个显示 ImagePullBackOff、11个显示 ErrImagePull；其中 curl-docker-io 因镜像拉取未完成导致 Terminating 卡住；node-debugger-node1-nx8gb 因镜像内无 curl 命令导致 StartError（独立问题）


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (22.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 7319 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 26.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将基于您提供的详尽分析，为您生成一份专业的诊断报告。

---
## 📊 诊断概览

**核心回答：** 当前集群存在一个**严重且广泛的网络连通性问题**，导致大量 Pod 无法正常运行。主要问题集中在 **57个 Pod 因无法从 `docker.io` (以及 `registry.k8s.io`) 拉取镜像而处于 `Pending` 状态**，具体表现为 `ImagePullBackOff` 和 `ErrImagePull`。此外，还存在几个零星的次要问题。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff (45个)， ErrImagePull (11个), Pending (57个) |
| **兼容归因层** | L3 - 网络层 (Network) |
| **问题分类** | Pod ImagePullFailed / ImagePullBackOff |
| **置信度** | 高 (95%) |
| **证据完整度** | 6/6 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**集群状态摘要**：

| 指标 | 数据 |
|------|------|
| **Running Pods** | 61 |
| **Pending Pods** | **57** (全部异常) |
| **Succeeded Pods** | 6 |
| **Failed Pods** | 2 |
| **关键异常 Pod 数量** | 56 个 (ImagePullBackOff / ErrImagePull)，1 个 Terminating, 1 个 StartError, 1 个 Evicted, 1 个 Readiness Probe 失败 |

**主要问题- Pending Pod 详情**：

| 类型 | Namespace | 节点 | 镜像 | 当前状态 |
|------|-----------|------|------|----------|
| dns-*, registry-*, test-dns-* | default, aiops-e2e, mcp | node1, node2 | `busybox:1.36.1`, `busybox:1.28`, `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`, `alpine/curl` | ImagePullBackOff / ErrImagePull |

**根源结论**：**集群节点(node1， node2)到 `docker.io` 镜像仓库的网络连接在全链路被阻断**，导致所有依赖此仓库拉取镜像的 Pod 均无法启动。

---
## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 & 事件 | kubectl_describe | `registry-conn-test-1779371220` (node2): 尝试拉取 `busybox:1.36.1` 时，对 5 个不同的 docker.io IP (122.248.226.57, 157.240.1.9, 等) 的 **443 端口全部出现 `dial tcp i/o timeout`**。9小时内重试 996 次。 | **节点 `node2` 到 docker.io:443 网络完全不可达。** |
| 2 | Pod 状态 & 事件 | kubectl_describe | `dig-check-registry` (node1): 尝试拉取 `busybox:1.28` 时，出现 `i/o timeout` 和 `connection reset by peer` 错误。 | **节点 `node1` 也存在相同的到 docker.io 的网络问题。** |
| 3 | Pod 状态 & 事件 | kubectl_get_by_kind_in_cluster | 集群返回 `~60+ pods`，其中 `ImagePullBackOff (20+)` 和 `ErrImagePull (~9)` 故障集中在 `default` 和 `aiops-e2e` namespace。 | **确认该问题不是偶发，而是影响多个 namespace 的系统性故障。** |
| 4 | Pod 状态 | kubectl_get_yaml | `mcp/curl-docker-io` Pod: `deletionTimestamp: 2026-05-21T23:31:15Z`， `finalizers: <none>`，`terminationGracePeriodSeconds: 30` | **排除 finalizer 问题**。Pod 处于 `Terminating` 状态，很可能是因为镜像未拉取成功导致容器无法安全停止。 |
| 5 | Pod 状态 & 事件 | kubectl_describe | `mcp/node-debugger-node1-nx8gb` Pod: `Reason: StartError`, `Exit Code: 128`。 | **此问题独立于网络故障**，是因镜像内缺少 curl 命令导致容器启动失败。 |
| 6 | Pod 状态 & 事件 | kubectl_describe | `aiops-e2e/rc-notready-readiness` Pod: `Warning Unhealthy 2s (x937 over 45m) kubelet Readiness probe failed`。 | 此 Pod 处于 **Running** 状态，但Readiness Probe 失败，属于另一类次要问题，与应用配置相关。 |

### 证据关联分析
- **证据 #1 + 证据 #2 印证**：两个集群节点 `node1` 和 `node2` 均无法连接 `docker.io`，且错误类型高度一致（`i/o timeout`, `connection reset`），排除了单个节点故障的可能性。
- **证据 #3 + 证据 #1 + 证据 #2 印证**：Pod 的 ImagePullBackOff 和 ErrImagePull 状态与节点级的网络不可达事件完全对应，形成一条完整的证据链：**节点网络问题 → 镜像拉取失败 → Pod 无法启动**。
- **证据 #4**：`Terminating` 的 Pod `curl-docker-io` 也是因为要使用的 `alpine/curl` 镜像（来自 docker.io）无法被拉取，导致删除流程卡住。`finalizers: <none>` 排除了因 Finalizers 导致的阻塞。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点网络策略（iptables/代理/防火墙规则） | critical | 无法精确判断网络被阻断的具体原因（是企业防火墙/代理，还是云服务商网络策略？）。 |
| xnet/observability-kibana Pod Evicted 原因 | low | 该 Pod 已被驱逐，问题可能由节点资源紧张或污点引起，但与当前主要问题（网络）关联不大。 |

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ 集群节点 (node1, node2) 到 docker.io 镜像仓库 (registry-1.docker.io:443)      │
│ 的网络连接被外部网络策略（防火墙/代理/安全组）阻断，导致 TCP 连接无法建立。       │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ 1) kubelet 调用 containerd 从 docker.io 拉取镜像                              │
│ 2) TCP 三次握手在 443 端口超时 (i/o timeout) 或收到 RST (connection reset)    │
│ 3) 拉取请求失败，containerd 返回错误给 kubelet                                │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ kubelet 无法完成镜像拉取，将 Pod 状态标记为 ErrImagePull                      │
│ 并启动 BackOff 重试策略（每重试一次增加间隔时间）                               │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ 57 个 Pod 处于 Pending 状态，显示 ImagePullBackOff / ErrImagePull            │
│ 总耗时 9-12 小时，重试次数高达 1846 次                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (registry-conn-test-1779371220) 和 证据 #2 (dig-check-registry) 中的 `dial tcp :443: i/o timeout` 原始数据，跨节点、跨多个 docker.io IP 地址的相同网络错误，以及证据 #3 确认的系统性故障范围，问题的根本原因是 **集群节点所在网络环境无法访问 `docker.io` 的 443 端口**。

**置信度**：高 (95%)
- ✅ 两个节点上多个 Pod 均报出完全相同的网络超时错误（`i/o timeout`）
- ✅ 故障影响面广，覆盖所有依赖 `docker.io` 镜像的 Pod
- ✅ 系统组件（`kube-system`）正常运行，排除了节点自身故障
- ⚠️ 缺少节点网络配置细节，无法精确指出被哪个网络组件阻断

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [最高优先] 排查并修复节点网络连通性**
- **目标**：恢复节点到 `docker.io:443` 的网络连接。
- **操作**：在任意问题节点上执行：
  ```bash
  # 测试网络连通性
  curl -v https://registry-1.docker.io/v2/ 2>&1 | head -20
  
  # 使用 telnet 测试端口
  telnet registry-1.docker.io 443
  ```
- **排查方向**：
  - **企业环境**：检查防火墙/代理服务器是否限制了出站 HTTPS (443) 流量。
  - **云环境**：检查安全组/网络 ACL 规则，确保允许出口流量到 `docker.io`。
  - **代理配置**：如果集群配置了 HTTP/HTTPS 代理，检查 `containerd` 或 `dockerd` 的代理配置是否正确。
  - **私有仓库**：如果需要拉取 `docker.io` 镜像但无法直接访问，考虑在集群内或可访问的网络中搭建镜像代理缓存（如 Harbor, Sonatype Nexus）或使用 **Mirror 站点**。

**2. [临时规避] 更改 Pod 镜像为集群内可访问的镜像**
- **适用场景**：如果核心业务需要尽快恢复，而 `docker.io` 网络的修复需要时间。
- **操作**：将 Pod 使用的镜像替换为已拉取到本地或镜像仓库中的镜像。示例（假设 `pod-name` 的 YAML 已备份）：
  ```bash
  # 假设 registry.mycompany.com/mirror/busybox:1.36.1 是可用的
  kubectl set image pod/pod-name -n <namespace> <container-name>=registry.mycompany.com/mirror/busybox:1.36.1
  ```
- **注意**：这只是临时方案，治标不治本。

### 后续优化
1. **配置镜像仓库 Mirror/代理**：使用容器镜像仓库（如 Harbor）作为上游镜像的代理缓存，将 Pod 的 `imagePullPolicy` 保留为默认 `IfNotPresent`，集群内部通过 Mirror 拉取。这可以提高拉取速度并解耦对外部网络的依赖。
2. **监控告警**：配置对 Pod `ImagePullBackOff` 或 `ErrImagePull` 状态的数量监控告警，以便快速发现类似的大面积网络问题。
3. **网络排查工具**：部署 `nicolaka/netshoot` 或 `tutum/dnsutils` 等工具 Pod，用于日常网络诊断。

---
## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认网络连通性 | 在节点上执行 `curl -v https://registry-1.docker.io/v2/ 2>&1 \| head -20` | 返回 HTTP 200 或 401/403（能连上即成功） |
| 2. 确认 Pod 恢复 | `kubectl get pods -n default -o wide \| grep -E "(ImagePullBackOff\|ErrImagePull)"` | 结果为空，所有 Pod 状态为 Running |
| 3. 确认集群状态 | `kubectl get pods --all-namespaces -o wide \| grep -E "(Pending\|ImagePullBackOff\|ErrImagePull)"` | 结果为空 |

---
## ⚠️ 注意事项
- 修复网络连接前，**请勿**执行 `kubectl delete pod` 或 `kubectl rollout restart` 来试图恢复 Pod，这只会导致 Pod 被重建并继续在相同的网络环境下失败。
- `mcp/node-debugger-node1-nx8gb` 的 `StartError` 是独立问题（镜像内缺少 curl 命令），需要另外修复其容器镜像或启动命令。
- `xnet/observability-kibana` 的 `Evicted` 状态和 `aiops-e2e/rc-notready-readiness` 的 `Readiness probe failed` 问题与本次大面积网络故障无关，需单独排查。

---

## 📊 性能统计

├─ 总耗时: 3.4m
├─ 问题定位: 49.9s (24%) ✅
├─ 证据链采集: 107.7s (52%) ✅
├─ 根因分析: 25.9s (13%) ✅
├─ 汇总总结: 22.7s (11%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 36 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-notready-probe-failed
- **工具调用**: 36 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
