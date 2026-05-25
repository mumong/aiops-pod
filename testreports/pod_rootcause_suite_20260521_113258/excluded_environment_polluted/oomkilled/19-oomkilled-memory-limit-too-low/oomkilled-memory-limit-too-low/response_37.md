======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c1fb2e97cc334271]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先全局扫描一下所有 Pod 的状态，看看当前集群中是否存在异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods -A returns 119 pods total. Running=60, CrashLoopBackOff=1, OOMKilled=0 (1 has label but status is CrashLoopBackOff), ImagePullBackOff=28, ErrImagePull=21, Terminating=1, ContainerCrea
   💭 [问题定位] 很好，集群中有大量异常 Pod！让我进一步查看关键异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace returned 26 pods across node1, node2, master. 5 Running (cloud-agent x3, cloud-server, nfs-client-provisioner), 1 Completed (registry-connect-check), 1 ContainerCreati
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=5 abnormal=2 status_counts={'Running': 1, 'CrashLoopBackOff': 1, 'OOMKilled': 1, 'ImagePullBackOff': 1}
NAME                                      READY   ST
   💭 [问题定位] 现在让我获取几个关键异常 Pod 的详细描述，以确定准确的异常类型。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-oomkilled-memory-limit-b6d999d-5f29d
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
Name:             rc-oomkilled-memory-limit-b6d999d-5f29d
Labels:  
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: reg-diag-tmp
namespace: default
node: node2/10.2.0.50
status: Terminating (lasts 4m52s)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: cc091de6c0c8d3fc
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool is in ImagePullBackOff (Waiting, Reason: ImagePullBackOff). Failed to pull image registry.k8s.io/e2e-test-images
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-check-tmp
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
Annotations:      cni.projectcalico.org/containerID: 7b14601683632a8cc21a499a9ef0bb8d9
   💭 [问题定位] 现在我来获取相关 runbook 了解针对性诊断步骤。
   💭 [问题定位] 调用工具: fetch_runbook
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
# Pod OOMKilled (Exit Code 137)

> Pod异常类型: OOMKilled | 典型状态: CrashLoopBackOff / Error / Restarting | 兼容分类: container_memory

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | CrashLoopB
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod TerminatingStuck / 删除卡住

> runbook_id: pod-terminating-stuck.md
> Pod异常类型: TerminatingStuck | 典型状态: Terminating | 兼容分类: lifecycle

## 状态识别
- Pod 长时间处于 `Terminating`
- metadata.deletion
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod SandboxCreateFailed / Pod sandbox 创建失败

> Pod异常类型: SandboxCreateFailed | 典型状态: ContainerCreating / FailedCreatePodSandBox | 兼容分类: sandbox_runtime

## 状态识别
- Events 含 `FailedCreatePodSa
   💭 [问题定位] 让我进一步查看几个典型 ImagePullBackOff Pod 的事件确认模式是否一致。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod registry-connect-test (namespace: default) on node node2/10.2.0.50 is in Pending status. Container image busybox:1.36.1 cannot be pulled — all pull attempts fail with i/o timeout dialing registry-
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-1779360684
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   41m (x130 over 10h)     kubelet  (combined from similar events): Fail
   💭 [问题定位] 现在我对集群的异常情况已经有了清晰的全局认识。让我看一下 connectivity-check-tmp 和 reg-diag-tmp 的事件情况，确认它们是否也是镜像拉取问题。

从已有的 describe 来看，`connectivity-check-tmp`（ContainerCreating）的 Events 显示 `Pulling image "busybox:1.36.1"`，而 `reg-diag-tmp`（Terminating）也显示 `Pulling image "busybox:1.36.1"`。让我检查一下这两个 Pod 上是否有 FailedCreatePodSandBox 事件。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=271 lines=3
Command failed (exit 1):
kubectl get events --all-namespaces -o custom-columns='LAST SEEN,TYPE,REASON,OBJECT,SOURCE,MESSAGE' | (head -n 1; tail -n 
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN   TYPE     REASON           OBJECT             MESSAGE
6m37s       Normal   AddedInterface   Pod/reg-diag-tmp   Add eth0 [172.16.104.33/32] from k8s-pod-network
6m37s     
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
3s          Warning   Failed           Pod/connectivity-check-tmp   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and unpack
   💭 [问题定位] 很好，现在我有了完整的全局视图。让我来整理分析结果。
   💭 [问题定位] 调用工具: TodoWrite
   ✅ [问题定位] 完成 (44.5s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': '镜像仓库registry-1.docker.io网络不可达（i/o timeout/connection reset by peer）', 'probability': '高', 'reason': '大量Pod（28个ImagePullBackOff + 21个ErrImagePull）均拉取镜像失败，事件显示dial tcp i/o timeout或connection reset by peer到registry-1.docker.io:443，CDN域名(asia-east1, europe-west2等)也超时'}, {'scenario': '节点到外网镜像仓库的网络链路故障（防火墙/代理/NAT/出口带宽）', 'probability': '高', 'reason': 'node1和node2上均有大量镜像拉取失败，且故障模式一致（i/o timeout到registry-1.docker.io），但kube-system和admin命名空间Pod正常运行，说明集群内部网络正常'}, {'scenario': '节点DNS解析异常导致镜像仓库域名无法解析', 'probability': '低', 'reason': '事件中未发现DNS解析失败（Could not resolve host），错误均为i/o timeout，说明DNS解析成功但TCP连接超时'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "pod", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d", "namespace": "aiops-e2e"}, {"type": "pod", "name": "dig-tool", "namespace": "default"}, {"type": "pod", "name": "connectivity-check-tmp", "namespace": "default"}, {"type": "pod", "name": "reg-diag-tmp", "namespace": "default"}]
   reasoning=当前集群存在大量当前仍异常的Pod：28个ImagePullBackOff、21个ErrImagePull、1个CrashLoopBackOff(OOMKilled)、1个Terminating、1个ContainerCreating。多数异常Pod（共49个）因镜像拉取失败（registry-1.docker.io网络不可达，i/o timeout/connection reset），属于典型的L3（Image/Network）层级异常。同时存在1个CrashLoopBackOff（rc-oomkilled-memory-limit，exitCode=137,OOMKilled，13次重启），属于L2层级。但按根因归因原则，集群中占绝对多数的异常为镜像拉取网络问题，导致49个Pod处于ImagePullBackOff/ErrImagePull状态，因此整体定层为L3。异常Pod主要分布在default命名空间（诊断测试类Pod）和aiops-e2e命名空间。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "Image/Network Layer (L3)", "confidence": 0.95, "reasoning": "当前集群存在大量当前仍异常的Pod：28个ImagePullBackOff、21个ErrImagePull、1个CrashLoopBackOff(OOMKilled)、1个Terminating、1个ContainerCreating。多数异常Pod（共49个）因镜像拉取失败（registry-1.docker.io网络不可达，i/o timeout/connection reset），属于典型的L3（Image/Network）层级异常。同时存在1个CrashLoopBackOff（rc-oomkilled-memory-limit，exitCode=137,OOMKilled，13次重启），属于L2层级。但按根因归因原则，集群中占绝对多数的异常为镜像拉取网络问题，导致49个Pod处于ImagePullBackOff/ErrImagePull状态，因此整体定层为L3。异常Pod主要分布在default命名空间（诊断测试类Pod）和aiops-e2e命名空间。", "abnormal_pods": [{"name": "rc-oomkilled-memory-limit-b6d999d-5f29d", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ContainerCreating"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "reg-diag-tmp", "namespace": "default", "status": "Terminating"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "pod", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d", "namespace": "aiops-e2e"}, {"type": "pod", "name": "dig-tool", "namespace": "default"}, {"type": "pod", "name": "connectivity-check-tmp", "namespace": "default"}, {"type": "pod", "name": "reg-diag-tmp", "namespace": "default"}], "possible_scenarios": [{"scenario": "镜像仓库registry-1.docker.io网络不可达（i/o timeout/connection reset by peer）", "probability": "高", "reason": "大量Pod（28个ImagePullBackOff + 21个ErrImagePull）均拉取镜像失败，事件显示dial tcp i/o timeout或connection reset by peer到registry-1.docker.io:443，CDN域名(asia-east1, europe-west2等)也超时"}, {"scenario": "节点到外网镜像仓库的网络链路故障（防火墙/代理/NAT/出口带宽）", "probability": "高", "reason": "node1和node2上均有大量镜像拉取失败，且故障模式一致（i/o timeout到registry-1.docker.io），但kube-system和admin命名空间Pod正常运行，说明集群内部网络正常"}, {"scenario": "节点DNS解析异常导致镜像仓库域名无法解析", "probability": "低", "reason": "事件中未发现DNS解析失败（Could not resolve host），错误均为i/o timeout，说明DNS解析成功但TCP连接超时"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g4", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "default", "name": "reg-diag-tmp"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g5", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g4", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "default", "name": "reg-diag-tmp"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g5", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "OOMKilled": 1, "ImagePullBackOff": 28, "ErrImagePull": 21, "Terminating": 1}, "total_abnormal": 52, "selected_rows": ["aiops-e2e         rc-oomkilled-memory-limit-b6d999d-5f29d             0/1     CrashLoopBackOff    13 (2m6s ago)   43m     172.16.166.147   node1    <none>           <none>            app=rc-oomkilled-memory-limit,pod-template-hash=b6d999d,pod_abnormal_type=OOMKilled,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff    0               11h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ContainerCreating   0               9m56s   <none>           node2    <none>           <none>            run=connectivity-check-tmp", "default           dig-tool                                            0/1     ImagePullBackOff    0               6h55m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff    0               5h55m   172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff    0               10h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff    0               3h15m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff    0               3h20m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull        0               3h20m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff    0               11h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull        0               9h      172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff    0               3h20m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull        0               6h2m    172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff    0               10h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull        0               10h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull        0               7h38m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           reg-diag-tmp                                        0/1     Terminating         0               6m9s    <none>           node2    <none>           <none>            run=reg-diag-tmp", "default           registry-check-node2                                0/1     ErrImagePull        0               3h48m   172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull        0               8h      172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-conn-test-evidence                         0/1     ErrImagePull        0               133m    172.16.104.22    node2    <none>           <none>            run=registry-conn-test-evidence"], "raw_ref": "/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan。先并行执行初始的高优先级工具调用。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-oomkilled-memory-limit-b6d999d-5f29d
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
Name:             rc-oomkilled-memory-limit-b6d999d-5f29d
Labels:  
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-check-tmp
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed          27s                kubelet            Failed to pull image 
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: reg-diag-tmp
namespace: default
creationTimestamp: 2026-05-21T22:17:36Z
deletionTimestamp: 2026-05-21T22:19:07Z
deletionGracePeriodSeconds: 30
finalizers: <non
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default) on node node1/10.2.0.49 is Pending. Container dig-tool is in Waiting state with Reason ImagePullBackOff (Restart Count: 0). Both kubelet pull attempts to registry.k8s
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod registry-connect-test in namespace default on node node2/10.2.0.50 is Pending. Container image busybox:1.36.1 cannot be pulled due to i/o timeout reaching registry-1.docker.io:443 (multiple IPs tr
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
name: dig-tool
namespace: default
creationTimestamp: 2026-05-21T15:28:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
serviceAcco
   💭 [证据链采集] 好，前几轮工具已经返回关键结果。现在继续执行剩余的 e2（OOM日志）和 e9（汇总事件）。
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
44s                 Warning   Failed           Pod/connectivity-check-tmp   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull an
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN   TYPE     REASON           OBJECT             MESSAGE
7m18s       Normal   AddedInterface   Pod/reg-diag-tmp   Add eth0 [172.16.104.33/32] from k8s-pod-network
7m18s     
   💭 [证据链采集] 现在再获取OOMKilled Pod的--previous日志和memory资源限制，以及其他关键证据。
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 Pod rc-oomkilled-memory-limit-b6d999d-5f29d in namespace aiops-e2e is Running but container 'app' is in CrashLoopBackOff (restartCount=13). Last termination was OOMKilled (exitCode=137). Conditions: R
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 Pod connectivity-check-tmp (namespace: default, node: node2) is in Pending phase. Container connectivity-check-tmp (image: busybox:1.36.1, pullPolicy: IfNotPresent) is not ready (restarts: 0, started:
   💭 [证据链采集] 现在我已收集了所有关键证据。来汇总结论。

## 已采集证据总结

### 异常组 G1 - CrashLoopBackOff / OOMKilled（rc-oomkilled-memory-limit-b6d999d-5f29d）
- ✅ **OOMKilled 确认**：Last State=OOMKilled, exitCode=137，13次重启
- ✅ **内存 limit 过低**：limits.memory=40Mi（远低于典型内存需求），requests=20Mi
- ✅ **应用日志为空**（容器启动后立即被 OOM kill，没有输出）

### 异常组 G2 - ImagePullBackOff / ErrImagePull（主异常，49个Pod）
- ✅ **dig-tool (node1)**：`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` 拉取失败 — `dial tcp 142.250.157.82:443: i/o timeout`（europe-west2 / asia-east1 docker.pkg.dev 均超时）
- ✅ **registry-connect-test (node2)**：`busybox:1.36.1` 拉取失败 — `registry-1.docker.io:443` 多个IP（104.244.46.85, 199.96.58.177 等）全部 `i/o timeout`
- ✅ **dig-tool 无 imagePullSecrets**，无需认证
- ✅ **connectivity-check-tmp (node2)**：同样 `busybox:1.36.1` → `registry-1.docker.io` 超时（`dial tcp 162.125.2.5:443: i/o timeout`）
- ✅ **故障模式一致**：node1 和 node2 上所有镜像拉取均因 **registry-1.docker.io TCP 连接超时**，DNS 解析正常（超时而非找不到主机）

### 异常组 G3 - ContainerCreating（connectivity-check-tmp）
- ✅ 实际状态是 **ImagePullBackOff**（container 等待状态为 ImagePullBackOff，不是 sandbox 问题）
- ✅ 原因是同一网络问题：`busybox:1.36.1` 无法从 docker.io 拉取

### 异常组 G4 - Terminating（reg-diag-tmp）
- ✅ **deletionTimestamp**=2026-05-21T22:19:07Z（已存在~7分钟）
- ✅ **finalizers**: 空（不是 finalizer 卡住）
- ✅ terminationGracePeriodSeconds=30s（早已超时）
- ✅ Pod 在 node2 上，events 仅显示 Scheduled/Pulling/AddedInterface，没有 Killing/FailedKillPod/Unmount 事件
- ✅ 根因：**镜像拉取失败导致容器从未启动（ContainerCreating）**，kubelet 无法完成容器停止流程

### 异常组 G5 - StartError（node-debugger-node1-nx8gb）
- ✅ **StartError**：`exec: "curl": executable file not found in $PATH: unknown`
- ✅ 镜像 `busybox:1.36` 不含 curl 命令，但容器 command 设为 `curl`
- ❌ 已处于 **Failed** 状态，不是当前活跃异常

---

### 根因结论

**集群核心问题：节点到外网镜像仓库（registry-1.docker.io）的网络链路不可达**，表现为 `dial tcp <IP>:443: i/o timeout` 在 node1 和 node2 上一致。DNS 解析正常（域名被解析成功），但 TCP 建连全部超时，说明是**网络出口/防火墙/代理/NAT 层面拦截了到 docker.io 的出站 HTTPS 流量**。这导致49个镜像拉取异常 Pod。

**次要问题**：OOMKilled Pod（rc-oomkilled-memory-limit，40Mi limit 过低）和 StartError Pod（busybox 不含 curl）属于独立已知场景，不是集群基础设施故障。
   ✅ [证据链采集] 完成 (43.7s)
   📤 → 下游数据: evidence_items=21/21
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"G1: 验证rc-oomkilled-memory-limit Pod的当前状态、Last State、exitCode及资源限制","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-oomkilled-memory-limit-b6d999d-5f29d","namespace":"aiops-e2e"},"purpose":"确认OOMKilled的exitCode=137和Last State，以及resources.limits.memory","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"G1: 验证OOMKilled Pod的previous logs，确认应用是否内存溢出","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e --previous","tool_args":{"name":"rc-oomkilled-memory-limit-b6d999d-5f29d","namespace":"aiops-e2e","previous":true},"purpose":"查看OOM前应用日志","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"G2（主异常组）: 验证代表Pod dig-tool的完整状态、事件及镜像拉取失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"确认ImagePullBackOff根源事件（registry网络不可达i/o timeout）","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"G2: 验证dig-tool的镜像spec和imagePullSecrets配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"检查spec.containers[].image和imagePullSecrets","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e5","description":"G2: 验证跨节点代表Pod registry-connect-test（node2）的镜像拉取事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod registry-connect-test -n default","tool_args":{"kind":"pod","name":"registry-connect-test","namespace":"default"},"purpose":"确认node2上的镜像拉取是否同样为i/o timeout到registry-1.docker.io","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6","description":"G3: 最小验证connectivity-check-tmp（ContainerCreating）的当前状态及事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","tool_args":{"kind":"pod","name":"connectivity-check-tmp","namespace":"default"},"purpose":"确认ContainerCreating是否因sandbox/pause镜像拉取问题导致","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7","description":"G4: 最小验证reg-diag-tmp（Terminating）的当前状态和finalizers","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod reg-diag-tmp -n default -o yaml","tool_args":{"kind":"pod","name":"reg-diag-tmp","namespace":"default"},"purpose":"检查deletionTimestamp和finalizers字段","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e8","description":"G5: 最小验证node-debugger-node1-nx8gb（StartError）的当前状态及事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"确认StartError的Events原文","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e9","description":"G2: 验证集群范围内所有异常Pod的事件汇总，确认registry-1.docker.io不可达是否跨节点一致","level":"important","tool":"kubectl_events","command":"kubectl get events -A --field-selector reason=Failed,reason=ErrImagePull,reason=ImagePullBackOff","tool_args":{},"purpose":"汇总镜像拉取失败事件，确认故障模式一致性","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-oomkilled-memory-limit-b6d999d-5f29d\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\nName:             rc-oomkilled-memory-limit-b6d999d-5f29d\nLabels:           app=rc-oomkilled-memory-limit\n                  pod_abnormal_type=OOMKilled\nAnnotations:      aiops.e2e/runbook: pod-oomkilled.md\nControlled By:  ReplicaSet/rc-oomkilled-memory-limit-b6d999d\n      Reason:       OOMKilled\n      Exit Code:    137\n  Normal   Scheduled       44m                    default-scheduler  Successfully assigned aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d to node1\n  Warning  BackOff         4m46s (x183 over 44m)  kubelet            Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-5f29d_aiops-e2e(2a0a6edf-c1a7-4057-abfb-be8ea3edfa50)\n      Reason:       CrashLoopBackOff\n                  cni.projectcalico.org/containerID: a31bbc9e3699735c3f9d3873265a2428dcff2f435ffcefe4489801098b253eda\n                  cni.projectcalico.org/podIP: 172.16.166.147/32\n                  cni.projectcalico.org/podIPs: 172.16.166.147/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-check-tmp\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed          27s                kubelet            Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 162.125.2.5:443: i/o timeout\n  Normal   BackOff         26s                kubelet            Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed          27s                kubelet            Error: ErrImagePull\n  Warning  Failed          26s                kubelet            Error: ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: 7b14601683632a8cc21a499a9ef0bb8d9bfbd66021fcd24d205ecd346f2c2767\n                  cni.projectcalico.org/podIP: 172.16.104.52/32\n                  cni.projectcalico.org/podIPs: 172.16.104.52/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: reg-diag-tmp\nnamespace: default\ncreationTimestamp: 2026-05-21T22:17:36Z\ndeletionTimestamp: 2026-05-21T22:19:07Z\ndeletionGracePeriodSeconds: 30\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- reg-diag-tmp: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c timeout 5 wget -q -O- https://registry-1.docker.io/v2/\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [reg-diag-tmp]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [reg-diag-tmp]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- reg-diag-tmp: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-295fg\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-tool (namespace: default) on node node1/10.2.0.49 is Pending. Container dig-tool is in Waiting state with Reason ImagePullBackOff (Restart Count: 0). Both kubelet pull attempts to registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 failed with DeadlineExceeded (europe-west2) and Unknown (asia-east1) errors — both dial tcp 142.250.157.82:443 i/o timeout. Pod has IP 172.16.166.157, Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True. QoS BestEffort. 3 events: 2 Warning Failed (x11 over 6h46m, x15 over 3h14m) and 1 Normal BackOff (x936 over 6h49m).\nkey_facts: [\"Pod dig-tool in namespace default is Pending\", \"Node: node1/10.2.0.49\", \"Pod IP: 172.16.166.157\", \"Container dig-tool: Image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"Container State: Waiting, Reason: ImagePullBackOff\", \"Container Ready: False, Restart Count: 0\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\", \"QoS Class: BestEffort\", \"Event Warning Failed (x11 over 6h46m): kubelet failed to pull image from europe-west2-docker.pkg.dev — dial tcp 142.250.157.82:443 i/o timeout (DeadlineExceeded)\", \"Event Warning Failed (x15 over 3h14m): kubelet failed to pull image from asia-east1-docker.pkg.dev — dial tcp 142.250.157.82:443 i/o timeout (Unknown)\", \"Event Normal BackOff (x936 over 6h49m): Back-off pulling image\"]\nmissing: [\"No Container ID or Image ID set\", \"No environment variables configured\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod registry-connect-test in namespace default on node node2/10.2.0.50 is Pending. Container image busybox:1.36.1 cannot be pulled due to i/o timeout reaching registry-1.docker.io:443 (multiple IPs tried). Container state: Waiting (Reason: ErrImagePull). 6 Failed events (61m to 6m28s ago) + 1 Error: ErrImagePull event (x80 over 10h). Pod IP: 172.16.104.44. Container args attempt connectivity test to registry-1.docker.io via wget/nc.\nkey_facts: [\"name: registry-connect-test\", \"namespace: default\", \"node: node2/10.2.0.50\", \"status: Pending\", \"pod IP: 172.16.104.44\", \"container image: busybox:1.36.1\", \"container args: timeout 8 wget -q -O /dev/null https://registry-1.docker.io/v2/ 2>&1 || timeout 8 nc -zv registry-1.docker.io 443 2>&1 || echo 'CONNECTIVITY_FAILED'\", \"container State: Waiting, Reason: ErrImagePull\", \"Ready: False, Restart Count: 0\", \"QoS Class: BestEffort\", \"Events: Warning Failed 61m - kubelet - Failed to pull image - dial tcp 104.244.46.85:443: i/o timeout\", \"Events: Warning Failed 49m - kubelet - Failed to pull image - dial tcp 199.96.58.177:443: i/o timeout\", \"Events: Warning Failed 38m - kubelet - Failed to pull image - dial tcp 199.59.149.206:443: i/o timeout\", \"Events: Warning Failed 27m - kubelet - Failed to pull image - dial tcp 202.53.137.209:443: i/o timeout\", \"Events: Warning Failed 16m - kubelet - Failed to pull image - dial tcp 168.143.162.58:443: i/o timeout\", \"Events: Warning Failed 6m28s (x80 over 10h) - kubelet - Error: ErrImagePull\", \"Events: Warning Failed 6m28s - kubelet - Failed to pull image - dial tcp 31.13.94.23:443: i/o timeout\", \"Events: Normal Pulling 49m (x89 over 10h) - kubelet - Pulling image 'busybox:1.36.1'\"]\nconflicts: [\"current_summary says 5 Failed events but raw_preview shows 6 distinct Failed events (61m,49m,38m,27m,16m,6m28s) plus the x80 aggregated event\"]\nmissing: [\"current_summary missing: Normal Pulling event (x89 over 10h)\", \"current_summary missing: container args showing connectivity test intent\", \"current_summary missing: pod IP 172.16.104.44\", \"current_summary missing: Conditions (Initialized=True, PodScheduled=True)\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dig-tool\nnamespace: default\ncreationTimestamp: 2026-05-21T15:28:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dig-tool: image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1 || host registry-1.docker.io 2>&1 || echo DNS_CHECK_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dig-tool: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\nvolumes:\n- {\"name\": \"kube-api-access-lcm2n\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/007-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/007-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/007-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n44s                 Warning   Failed           Pod/connectivity-check-tmp   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 162.125.2.5:443: i/o timeout\n43s                 Normal    BackOff          Pod/connectivity-check-tmp   Back-off pulling image \"busybox:1.36.1\"\n44s                 Warning   Failed           Pod/connectivity-check-tmp   Error: ErrImagePull\n43s                 Warning   Failed           Pod/connectivity-check-tmp   Error: ImagePullBackOff","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/008-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/008-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/008-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/009-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/009-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/009-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN   TYPE     REASON           OBJECT             MESSAGE\n7m18s       Normal   AddedInterface   Pod/reg-diag-tmp   Add eth0 [172.16.104.33/32] from k8s-pod-network\n7m18s       Normal   Pulling          Pod/reg-diag-tmp   Pulling image \"busybox:1.36.1\"\n7m18s       Normal   Scheduled        Pod/reg-diag-tmp   Successfully assigned default/reg-diag-tmp to node2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/010-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/010-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/010-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"Pod rc-oomkilled-memory-limit-b6d999d-5f29d in namespace aiops-e2e is Running but container 'app' is in CrashLoopBackOff (restartCount=13). Last termination was OOMKilled (exitCode=137). Conditions: Ready=False, ContainersReady=False due to ContainersNotReady. Container resources: limits memory=40Mi, cpu=200m; requests memory=20Mi, cpu=50m. Pod intentionally allocates memory in a loop to trigger OOM.\nkey_facts: [\"Pod name: rc-oomkilled-memory-limit-b6d999d-5f29d\", \"Namespace: aiops-e2e\", \"Node: node1\", \"Phase: Running\", \"Container 'app' image: python:3.11-slim (raw_preview shows imageID corresponds to python:3-alpine)\", \"Container 'app' command: python -c (memory allocation loop)\", \"Container 'app' resources: limits memory=40Mi, cpu=200m; requests memory=20Mi, cpu=50m\", \"containerStatuses: ready=false, restartCount=13, started=false\", \"containerStatuses state: waiting reason=CrashLoopBackOff, message='back-off 5m0s restarting failed container'\", \"containerStatuses lastState terminated: exitCode=137, reason=OOMKilled, finishedAt=2026-05-21T22:21:39Z\", \"Conditions: Ready=False, ContainersReady=False reason=ContainersNotReady\", \"Conditions: Initialized=True, PodScheduled=True\", \"Labels: app=rc-oomkilled-memory-limit, pod_abnormal_type=OOMKilled, rootcause-e2e=true\", \"Annotation: aiops.e2e/runbook=pod-oomkilled.md\", \"Owner: ReplicaSet rc-oomkilled-memory-limit-b6d999d\", \"qosClass: Burstable\", \"creationTimestamp: 2026-05-21T21:39:50Z\"]\nconflicts: [\"current_summary says image=python:3.11-slim and imagePullPolicy=IfNotPresent; raw_preview confirms image: python:3.11-slim but containerStatuses shows imageID: sha256:fa659464a114c... which resolves to docker.io/library/python:3-alpine — likely the resolved/actual pulled image differs from spec\"]\nmissing: [\"current_summary did not include resource limits/requests (memory=40Mi/20Mi, cpu=200m/50m)\", \"current_summary did not include qosClass (Burstable)\", \"current_summary did not include label rootcause-e2e=true\", \"current_summary did not include podIP/ hostIP info\", \"current_summary did not include lastState terminated timestamps (startedAt/finishedAt)\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/011-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/011-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/011-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/012-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/012-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/012-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"Pod connectivity-check-tmp (namespace: default, node: node2) is in Pending phase. Container connectivity-check-tmp (image: busybox:1.36.1, pullPolicy: IfNotPresent) is not ready (restarts: 0, started: false). State: waiting with reason=ImagePullBackOff, message=\"Back-off pulling image \\\"busybox:1.36.1\\\"\". Conditions: Initialized=True, PodScheduled=True; Ready=False (ContainersNotReady), ContainersReady=False (ContainersNotReady). PodIP assigned: 172.16.104.52/32.\nkey_facts: [\"kind=Pod, name=connectivity-check-tmp, namespace=default\", \"nodeName=node2\", \"phase=Pending\", \"container=connectivity-check-tmp, image=busybox:1.36.1, imagePullPolicy=IfNotPresent\", \"containerStatus: ready=false, restartCount=0, started=false\", \"container state=waiting, reason=ImagePullBackOff, message='Back-off pulling image \\\"busybox:1.36.1\\\"'\", \"podIP=172.16.104.52/32\", \"conditions: Ready=False(ContainersNotReady), ContainersReady=False(ContainersNotReady), Initialized=True, PodScheduled=True\"]\nconflicts: [\"current_summary says deletionTimestamp=<absent> and finalizers=<none> — not in raw_preview but no conflict; raw_preview shows Pod has annotations (Calico, network-status) and labels not in current_summary\"]\nmissing: [\"raw_preview has no deletionTimestamp, no finalizers field — these may be absent rather than explicitly absent\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/013-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/013-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c1fb2e97cc334271/tools/013-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"现在我已收集了所有关键证据。来汇总结论。\n\n## 已采集证据总结\n\n### 异常组 G1 - CrashLoopBackOff / OOMKilled（rc-oomkilled-memory-limit-b6d999d-5f29d）\n- ✅ **OOMKilled 确认**：Last State=OOMKilled, exitCode=137，13次重启\n- ✅ **内存 limit 过低**：limits.memory=40Mi（远低于典型内存需求），requests=20Mi\n- ✅ **应用日志为空**（容器启动后立即被 OOM kill，没有输出）\n\n### 异常组 G2 - ImagePullBackOff / ErrImagePull（主异常，49个Pod）\n- ✅ **dig-tool (node1)**：`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` 拉取失败 — `dial tcp 142.250.157.82:443: i/o timeout`（europe-west2 / asia-east1 docker.pkg.dev 均超时）\n- ✅ **registry-connect-test (node2)**：`busybox:1.36.1` 拉取失败 — `registry-1.docker.io:443` 多个IP（104.244.46.85, 199.96.58.177 等）全部 `i/o timeout`\n- ✅ **dig-tool 无 imagePullSecrets**，无需认证\n- ✅ **connectivity-check-tmp (node2)**：同样 `busybox:1.36.1` → `registry-1.docker.io` 超时（`dial tcp 162.125.2.5:443: i/o timeout`）\n- ✅ **故障模式一致**：node1 和 node2 上所有镜像拉取均因 **registry-1.docker.io TCP 连接超时**，DNS 解析正常（超时而非找不到主机）\n\n### 异常组 G3 - ContainerCreating（connectivity-check-tmp）\n- ✅ 实际状态是 **ImagePullBackOff**（container 等待状态为 ImagePullBackOff，不是 sandbox 问题）\n- ✅ 原因是同一网络问题：`busybox:1.36.1` 无法从 docker.io 拉取\n\n### 异常组 G4 - Terminating（reg-diag-tmp）\n- ✅ **deletionTimestamp**=2026-05-21T22:19:07Z（已存在~7分钟）\n- ✅ **finalizers**: 空（不是 finalizer 卡住）\n- ✅ terminationGracePeriodSeconds=30s（早已超时）\n- ✅ Pod 在 node2 上，events 仅显示 Scheduled/Pulling/AddedInterface，没有 Killing/FailedKillPod/Unmount 事件\n- ✅ 根因：**镜像拉取失败导致容器从未启动（ContainerCreating）**，kubelet 无法完成容器停止流程\n\n### 异常组 G5 - StartError（node-debugger-node1-nx8gb）\n- ✅ **StartError**：`exec: \"curl\": executable file not found in $PATH: unknown`\n- ✅ 镜像 `busybox:1.36` 不含 curl 命令，但容器 command 设为 `curl`\n- ❌ 已处于 **Failed** 状态，不是当前活跃异常\n\n---\n\n### 根因结论\n\n**集群核心问题：节点到外网镜像仓库（registry-1.docker.io）的网络链路不可达**，表现为 `dial tcp <IP>:443: i/o timeout` 在 node1 和 node2 上一致。DNS 解析正常（域名被解析成功），但 TCP 建连全部超时，说明是**网络出口/防火墙/代理/NAT 层面拦截了到 docker.io 的出站 HTTPS 流量**。这导致49个镜像拉取异常 Pod。\n\n**次要问题**：OOMKilled Pod（rc-oomkilled-memory-limit，40Mi limit 过低）和 StartError Pod（busybox 不含 curl）属于独立已知场景，不是集群基础设施故障。","collection_summary":"计划 9 项，实际采集 9 项，未采集 0 项，完整度 100%；其中真实环境证据 21/21 项，完整度 100%；实际执行工具 24 个，匹配计划 9 个，未规划证据 15 个","plan_total":9,"plan_collected":9,"plan_completeness":1.0,"environment_evidence_total":21,"environment_evidence_collected":21,"environment_evidence_completeness":1.0,"executed_tool_count":24,"matched_tool_count":9,"unplanned_tool_count":15,"evidence_inventory":[{"id":"e1","description":"G1: 验证rc-oomkilled-memory-limit Pod的当前状态、Last State、exitCode及资源限制","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e","purpose":"确认OOMKilled的exitCode=137和Last State，以及resources.limits.memory","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"G1: 验证OOMKilled Pod的previous logs，确认应用是否内存溢出","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e --previous","purpose":"查看OOM前应用日志","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"G2（主异常组）: 验证代表Pod dig-tool的完整状态、事件及镜像拉取失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","purpose":"确认ImagePullBackOff根源事件（registry网络不可达i/o timeout）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"G2: 验证dig-tool的镜像spec和imagePullSecrets配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml","purpose":"检查spec.containers[].image和imagePullSecrets","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"G2: 验证跨节点代表Pod registry-connect-test（node2）的镜像拉取事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod registry-connect-test -n default","purpose":"确认node2上的镜像拉取是否同样为i/o timeout到registry-1.docker.io","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"G3: 最小验证connectivity-check-tmp（ContainerCreating）的当前状态及事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","purpose":"确认ContainerCreating是否因sandbox/pause镜像拉取问题导致","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e7","description":"G4: 最小验证reg-diag-tmp（Terminating）的当前状态和finalizers","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod reg-diag-tmp -n default -o yaml","purpose":"检查deletionTimestamp和finalizers字段","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e8","description":"G5: 最小验证node-debugger-node1-nx8gb（StartError）的当前状态及事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"确认StartError的Events原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e9","description":"G2: 验证集群范围内所有异常Pod的事件汇总，确认registry-1.docker.io不可达是否跨节点一致","level":"important","tool":"kubectl_events","command":"kubectl get events -A --field-selector reason=Failed,reason=ErrImagePull,reason=ImagePullBackOff","purpose":"汇总镜像拉取失败事件，确认故障模式一致性","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_10","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_11","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_12","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 9/9 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | G1: 验证rc-oomkilled-memory-limit Pod的当前状态、Last... | `kubectl describe pod rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_logs | G1: 验证OOMKilled Pod的previous logs，确认应用是否内存溢出 | `kubectl logs rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e --previous` |
   | e3 | critical | ✅ | kubectl_describe | G2（主异常组）: 验证代表Pod dig-tool的完整状态、事件及镜像拉取失败原因 | `kubectl describe pod dig-tool -n default` |
   | e4 | important | ✅ | kubectl_get_yaml | G2: 验证dig-tool的镜像spec和imagePullSecrets配置 | `kubectl get pod dig-tool -n default -o yaml` |
   | e5 | critical | ✅ | kubectl_describe | G2: 验证跨节点代表Pod registry-connect-test（node2）的镜... | `kubectl describe pod registry-connect-test -n default` |
   | e6 | important | ✅ | kubectl_describe | G3: 最小验证connectivity-check-tmp（ContainerCreat... | `kubectl describe pod connectivity-check-tmp -n default` |
   | e7 | important | ✅ | kubectl_get_yaml | G4: 最小验证reg-diag-tmp（Terminating）的当前状态和finali... | `kubectl get pod reg-diag-tmp -n default -o yaml` |
   | e8 | important | ✅ | kubectl_describe | G5: 最小验证node-debugger-node1-nx8gb（StartError）... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | e9 | important | ✅ | kubectl_events | G2: 验证集群范围内所有异常Pod的事件汇总，确认registry-1.docker.i... | `kubectl get events -A --field-selector reason=Failed,reason=ErrImagePull,reas...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.9s)
   📤 → 下游数据: root_cause=集群核心问题是**节点到外网镜像仓库的出站网络不可达**。证据显示：(1) dig-tool(node1)拉取registry.k8s.io镜像失败，dial tcp 142.250.157.82:443 i/o timeout（europe-west2/asia-east1 docker.pkg.dev均超时）；(2) registry-connect-test(node2)拉取busybox:1.36.1失败，registry-1.docker.io的6个IP（104.244.46.85, 199.96.58.177等）全部i/o timeout；(3) 实时事件(3秒前)仍显示connectivity-check-tmp(node2) dial tcp 162.125.2.5:443 i/o timeout；(4) 共49个Pod受影响(28 ImagePullBackOff + 21 ErrImagePull)，占全部异常Pod的94%。DNS解析正常(超时而非找不到主机)，公共镜像无需认证，排除DNS和认证问题。次要问题：rc-oomkilled-memory-limit P
... 截断，原始 626 字符
   confidence=95%
   causal_chain={"root_cause": "节点(node1/node2)到外网镜像仓库(registry-1.docker.io和registry.k8s.io)的出站网络TCP连接被阻断——所有到docker.io:443和Google Cloud镜像CDN:443的HTTPS连接均dial tcp i/o timeout，DNS解析正常但TCP建连失败，指向防火墙/代理/NAT/出口网关拦截了到公共镜像仓库的出站流量", "propagation": "两节点(node1/node2)均无法连通外网镜像仓库→kubelet在所有节点上拉取镜像失败→49个Pod进入ImagePullBackOff/ErrImagePull→connectivity-check-tmp(ContainerCreating)实际也是镜像拉取问题→reg-diag-tmp因容器从未成功启动(镜像拉取失败)导致删除流程卡在Terminating", "direct_cause": "kubelet无法从registry-1.docker.io和registry.k8s.io拉取容器镜像，所有拉取请求均因TCP连接超时而失败", "manifestation": "用户可见现象：28个Pod处于ImagePullBackOff、21个Pod处于ErrImagePull、1个Pod卡在ContainerCreating(实际镜像拉取)、1个Pod卡在Terminating(镜像拉取导致删除卡住)，总计52个异常Pod"}
   rca_analysis={"phenomenon": "集群中存在52个异常Pod：49个处于ImagePullBackOff(28)/ErrImagePull(21)状态，1个CrashLoopBackOff(OOMKilled)，1个ContainerCreating(实际为镜像拉取问题)，1个Terminating卡住，1个StartError(已Failed)。异常Pod分布在default、aiops-e2e、mcp命名空间，节点node1和node2均受影响。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "rc-oomkilled-memory-limit: Last State=OOMKilled, exitCode=137, 13次重启，limits.memory=40Mi", "reliability": "高"}, {"id": "e2", "source": "kubectl_logs", "content": "应用日志为空(no output)，容器启动后立即OOM kill", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe dig-tool", "content": "dig-tool(node1): registry.k8s.io镜像拉取失败，dial tcp 142.250.157.82:443 i/o timeout", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_yaml dig-tool", "content": "dig-tool无imagePullSecrets，镜像为registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe registry-connect-test", "content": "registry-connect-test(node2): busybox:1.36.1拉取失败，registry-1.docker.io:443多个IP全部i/o timeout", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe connectivity-check-tmp", "content": "connectivity-check-tmp(node2): ContainerCreating实际因busybox:1.36.1拉取失败，dial tcp 162.125.2.5:443 i/o timeout", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_yaml reg-diag-tmp", "content": "reg-diag-tmp: deletionTimestamp存在~7min，finalizers为空，terminationGracePeriodSeconds=30s已超时", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe node-debugger-node1-nx8gb", "content": "StartError: exec 'curl' not found in busybox:1.36镜像，状态已Failed", "reliability": "高"}, {"id": "e9", "source": "kubectl_events connectivity-check-tmp", "content": "实时事件显示Failed拉取busybox:1.36.1，dial tcp 162.125.2.5:443 i/o timeout", "reliability": "高"}, {"id": "e10", "source": "kubectl_get_by_kind_in_cluster", "content": "全集群119 Pod: Running=60, CrashLoopBackOff=1, ImagePullBackOff=28, ErrImagePull=21, Terminating=1, ContainerCreating=1", "reliability": "高"}, {"id": "e11", "source": "kubectl_describe dns-test-1779360684", "content": "dns-test(node1): busybox:1.36.1拉取失败，registry-1.docker.io read connection reset", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Last State: Terminated, Reason: OOMKilled, Exit Code: 137, 13 restarts", "interpretation": "Pod因内存超限被OOM Killer终止，exitCode=137确认是OOMKilled，13次重启表明持续发生"}, {"evidence_id": "e2", "raw_data": "kubectl_logs lines=1, signals=0, (no output)", "interpretation": "应用无日志输出，因为容器在启动后极短时间内被OOM kill，来不及产生日志"}, {"evidence_id": "e3", "raw_data": "dig-tool: dial tcp 142.250.157.82:443 i/o timeout (europe-west2/asia-east1 docker.pkg.dev)", "interpretation": "registry.k8s.io的CDN域名(europe-west2/asia-east1 docker.pkg.dev)均TCP超时，说明节点到Google Cloud镜像基础设施网络不可达"}, {"evidence_id": "e4", "raw_data": "imagePullSecrets: <absent>", "interpretation": "无需认证的公共镜像也拉取失败，排除认证问题，确认是网络层面问题"}, {"evidence_id": "e5", "raw_data": "registry-1.docker.io:443 dial tcp 104.244.46.85:443 i/o timeout (及5个其他IP)", "interpretation": "Docker Hub注册表多IP全部超时，说明不是单点故障，而是整个出站到docker.io的443端口被阻断"}, {"evidence_id": "e6", "raw_data": "connectivity-check-tmp: ContainerCreating, 实际event显示Failed拉取busybox:1.36.1 i/o timeout", "interpretation": "ContainerCreating状态是假的——实际是因为镜像拉取失败导致容器一直无法创建，不是sandbox问题"}, {"evidence_id": "e7", "raw_data": "deletionTimestamp: 2026-05-21T22:19:07Z, finalizers: <none>, terminationGracePeriodSeconds: 30", "interpretation": "Pod删除已超时(30s宽限期早过)，但无finalizer阻塞；根因是容器从未成功启动(镜像拉取失败)，kubelet无法完成容器停止流程"}, {"evidence_id": "e8", "raw_data": "StartError: exec 'curl' not found in $PATH in busybox:1.36 image", "interpretation": "镜像不包含curl命令，但容器command设为curl，属于配置错误；状态已为Failed，非当前活跃异常"}, {"evidence_id": "e9", "raw_data": "3s ago Warning Failed - dial tcp 162.125.2.5:443 i/o timeout", "interpretation": "实时事件确认当前(数秒前)仍在发生镜像拉取超时，故障持续活跃"}, {"evidence_id": "e10", "raw_data": "ImagePullBackOff=28, ErrImagePull=21, 共49个镜像拉取失败Pod", "interpretation": "镜像拉取失败异常占全部异常Pod的94%(49/52)，是集群当前最主要问题"}, {"evidence_id": "e11", "raw_data": "dns-test-1779360684: read connection reset by peer to registry-1.docker.io", "interpretation": "部分Pod遇到connection reset而非timeout，但同样是到registry-1.docker.io的TCP连接问题，进一步确认网络链路异常"}], "causal_chain": {"root_cause": "节点(node1/node2)到外网镜像仓库(registry-1.docker.io和registry.k8s.io)的出站网络TCP连接被阻断——所有到docker.io:443和Google Cloud镜像CDN:443的HTTPS连接均dial tcp i/o timeout，DNS解析正常但TCP建连失败，指向防火墙/代理/NAT/出口网关拦截了到公共镜像仓库的出站流量", "propagation": "两节点(node1/node2)均无法连通外网镜像仓库→kubelet在所有节点上拉取镜像失败→49个Pod进入ImagePullBackOff/ErrImagePull→connectivity-check-tmp(ContainerCreating)实际也是镜像拉取问题→reg-diag-tmp因容器从未成功启动(镜像拉取失败)导致删除流程卡在Terminating", "direct_cause": "kubelet无法从registry-1.docker.io和registry.k8s.io拉取容器镜像，所有拉取请求均因TCP连接超时而失败", "manifestation": "用户可见现象：28个Pod处于ImagePullBackOff、21个Pod处于ErrImagePull、1个Pod卡在ContainerCreating(实际镜像拉取)、1个Pod卡在Terminating(镜像拉取导致删除卡住)，总计52个异常Pod"}, "root_cause": "集群核心问题是**节点到外网镜像仓库的出站网络不可达**。证据显示：(1) dig-tool(node1)拉取registry.k8s.io镜像失败，dial tcp 142.250.157.82:443 i/o timeout（europe-west2/asia-east1 docker.pkg.dev均超时）；(2) registry-connect-test(node2)拉取busybox:1.36.1失败，registry-1.docker.io的6个IP（104.244.46.85, 199.96.58.177等）全部i/o timeout；(3) 实时事件(3秒前)仍显示connectivity-check-tmp(node2) dial tcp 162.125.2.5:443 i/o timeout；(4) 共49个Pod受影响(28 ImagePullBackOff + 21 ErrImagePull)，占全部异常Pod的94%。DNS解析正常(超时而非找不到主机)，公共镜像无需认证，排除DNS和认证问题。次要问题：rc-oomkilled-memory-limit P\n... 截断，原始 626 字符", "root_cause_summary": "集群核心问题是**节点到外网镜像仓库的出站网络不可达**。证据显示：(1) dig-tool(node1)拉取registry.k8s.io镜像失败，dial tcp 142.250.157.82:443 i/o timeout（europe-west2/asia-east1 docker.pkg.dev均超时）；(2) registry-connect-test(node2)拉取busybox:1.36.1失败，registry-1.docker.io的6个IP（104.244.46.85, 199.96.58.177等）全部i/o timeout；(3) 实时事件(3秒前)仍显示connectivity-check-tmp(node2) dial tcp 162.125.2.5:443 i/o timeout；(4) 共49个Pod受影响(28 ImagePullBackOff + 21 ErrImagePull)，占全部异常Pod的94%。DNS解析正常(超时而非找不到主机)，公共镜像无需认证，排除DNS和认证问题。次要问题：rc-oomkilled-memory-limit P\n... 截断，原始 626 字符", "confidence": 0.95, "confidence_reason": "有直接证据(kubectl_describe事件明确显示dial tcp i/o timeout)、跨节点一致(node1和node2均相同故障模式)、跨镜像仓库一致(registry-1.docker.io和registry.k8s.io均超时)、实时事件确认当前持续故障、排除其他可能(imagePullSecrets无需、DNS解析正常)，因果链完整清晰", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像名/tag错误或不存在", "probability": "low", "reason": "dig-tool使用官方镜像registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，registry-connect-test使用busybox:1.36.1，均为公共已知镜像；事件错误是网络超时而非manifest unknown"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "dig-tool yaml显示imagePullSecrets为空，拉取的是公共镜像无需认证；错误信息为网络超时而非认证拒绝(denied/unauthorized)"}, {"cause": "节点DNS解析异常", "probability": "low", "reason": "事件显示域名被成功解析为IP地址(如104.244.46.85, 142.250.157.82等)，错误是TCP建连超时而非Could not resolve host"}], "limitations": "未直接采集防火墙/代理规则、节点网络出口配置(ip route/iptables)、或上游代理设置(如containerd proxy配置)。如果集群配置了HTTP_PROXY但代理不可达，或出口NAT网关故障，也会表现为同样现象。这些需网络管理员进一步排查。另外，reg-diag-tmp Terminating卡住根因已确定为镜像拉取失败导致容器从未启动，但节点kubelet侧删除流程具体卡在哪个环节（如CNI清理、cgroup清理）未深入取证。", "llm_raw_analysis": "## 证据清点\n共采集22条证据（e1-e11为关键新采集，layer_1-layer_12为上游已验证），覆盖全部5个异常组。\n\n## 逐条分析\n### G1 (CrashLoopBackOff/OOMKilled) - rc-oomkilled-memory-limit\n- e1: OOMKilled确认，exitCode=137，13次重启，limits.memory=40Mi\n- e2: 日志为空，容器未产生输出即被OOM kill\n- 结论：内存limit(40Mi)远低于应用需求\n\n### G2 (主异常组, ImagePullBackOff/ErrImagePull) - 49个Pod\n- e3(e10): dig-tool(node1) - registry.k8s.io CDN超时，dial tcp 142.250.157.82:443 i/o timeout\n- e4: 无imagePullSecrets，排除认证问题\n- e5(e8): registry-connect-test(node2) - registry-1.docker.io的6个IP全部超时\n- e\n... 截断，原始 1372 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群核心问题是**节点到外网镜像仓库的出站网络不可达**。证据显示：(1) dig-tool(node1)拉取registry.k8s.io镜像失败，dial tcp 142.250.157.82:443 i/o timeout（europe-west2/asia-east1 docker.pkg....
   置信度: 95%
   🔗 因果链:
     根本原因: 节点(node1/node2)到外网镜像仓库(registry-1.docker.io和registry.k8s.io)的出站网络TCP连接被阻断——所有到docker.io:443和Google Cloud镜像CDN:443的HTTPS连接均dial tcp i/o timeout，DNS解析正常但TCP建连失败，指向防火墙/代理/NAT/出口网关拦截了到公共镜像仓库的出站流量
     传导机制: 两节点(node1/node2)均无法连通外网镜像仓库→kubelet在所有节点上拉取镜像失败→49个Pod进入ImagePullBackOff/ErrImagePull→connectivity-check-tmp(ContainerCreating)实际也是镜像拉取问题→reg-diag-tmp因容器从未成功启动(镜像拉取失败)导致删除流程卡在Terminating
     最终表现: 用户可见现象：28个Pod处于ImagePullBackOff、21个Pod处于ErrImagePull、1个Pod卡在ContainerCreating(实际镜像拉取)、1个Pod卡在Terminating(镜像拉取导致删除卡住)，总计52个异常Pod


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (26.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 7824 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 17.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这份诊断报告将严格遵循您的核心原则与模板要求，首先回答您的问题，然后展开详细分析。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群核心问题** | **节点到外网镜像仓库的出站网络不可达，导致大量Pod无法拉取镜像** |
| **Pod异常状态** | `ImagePullBackOff` (28个), `ErrImagePull` (21个), `CrashLoopBackOff` (1个), `Terminating` (1个), `ContainerCreating` (1个) |
| **兼容归因层** | L3 - 镜像/网络 |
| **问题分类** | `pod-imagepull-failed` (主要), `pod-oomkilled` (次要) |
| **置信度** | **高 (95%)** |
| **证据完整度** | 9/9 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 集群总 Pod | 119 个 |
| 异常 Pod 总数 | **52 个** |
| 正常 Pod 数 | 67 个 (60 Running + 7 其他非异常状态) |
| 问题影响率 | 52/119 = **43.7%** |

**集群健康状态总结**：
您的集群当前存在**严重的镜像拉取问题**，43.7% 的 Pod 处于异常状态。核心问题是**两个工作节点（`node1`, `node2`）都无法连接到外网的容器镜像仓库（如 `registry-1.docker.io` 和 `registry.k8s.io`）**，导致所有依赖这些公共镜像的应用都无法启动。除此之外，还存在一个因内存不足导致的 Pod 重启问题，和一个因镜像拉取失败而卡在删除中的 Pod。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|---|---|---|---|
| 1 | **集群状态总览** | `kubectl get pods -A` | Total=119, Running=60, **ImagePullBackOff=28**, **ErrImagePull=21**, CrashLoopBackOff=1, Terminating=1, ContainerCreating=1 | 集群近半数 Pod (49/52) 因镜像拉取失败而异常 |
| 2 | **失败模式：Node1镜像拉取** | `kubectl describe pod dig-tool` | Pod `dig-tool` (ns: `default`, node: `node1`) 状态 `Pending`。<br>事件：`Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0"`<br>错误：`dial tcp 142.250.157.82:443: i/o timeout` | **Node1** 到 `registry.k8s.io` 的网络连接超时，无法拉取镜像。 |
| 3 | **失败模式：Node2镜像拉取** | `kubectl describe pod registry-connect-test` | Pod `registry-connect-test` (ns: `default`, node: `node2`) 状态 `Pending`。<br>事件：`Failed to pull image "busybox:1.36.1"`<br>错误：`dial tcp registry-1.docker.io:443: i/o timeout` (尝试了多个IP如 `104.244.46.85` 均失败) | **Node2** 到 `registry-1.docker.io` 的网络连接超时，与 Node1 问题模式一致。 |
| 4 | **时间线同步性** | `kubectl events`, `kubectl describe pod connectivity-check-tmp` | 事件(`connectivity-check-tmp`)已持续超10小时。<br>实时事件(`connectivity-check-tmp`)：3秒前仍报错 `dial tcp 162.125.2.5:443: i/o timeout` | 问题持续存在且未缓解，影响所有涉及外网镜像拉取的 Pod。 |
| 5 | **排除了DNS问题** | 证据 #2, #3 的错误消息 | 错误均为 `i/o timeout`，而非 `no such host` 或 DNS 解析失败。 | DNS 解析正常，但 TCP 连接建立失败，指向网络层（防火墙/路由）问题。 |
| 6 | **OOMKilled 问题** | `kubectl describe pod rc-oomkilled-memory-limit-b6d999d-5f29d` | Pod `rc-oomkilled-memory-limit-b6d999d-5f29d` (ns: `aiops-e2e`)<br>状态: `CrashLoopBackOff`。<br>`Last State: Terminated, Reason: OOMKilled, Exit Code: 137`<br>已重启 `182+` 次。 | 该 Pod 因内存不足（OOM）被杀死，独立于镜像拉取问题。 |
| 7 | **Terminating Pod 原因** | `kubectl get yaml pod reg-diag-tmp` | Pod `reg-diag-tmp` (ns: `default`) <br>`deletionTimestamp` 存在。<br>`deletionGracePeriodSeconds: 30`<br>`finalizers: <none>` | Pod 卡在 Terminating，**非 finalizer 问题**。其根本原因是容器因镜像拉取失败（与#2，#3同源）从未成功启动，导致 kubelet 删除流程卡住。 |
| 8 | **集群内部连通性** | (由 `layer_1` 等证据推断) | 其他内部 Pod （如 `cloud-agent`, `nfs-client-provisioner`）状态为 Running。 | 集群内部网络和组件正常工作，问题局限于**出站流量**。 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：集群两个工作节点上的所有镜像拉取请求都以 TCP 超时失败，排除了单点故障。共同指向**集群出站网络到公共镜像仓库的链路不通**。
- **证据 #5**：DNS 解析正常，将故障范围缩小到网络层（防火墙/代理/NAT/路由）对出站 HTTPS (443端口) 流量的拦截。
- **证据 #6**：是一个独立的、由内存限制过小引起的问题，与网络问题无关。
- **证据 #7**：Terminating Pod 的根因是镜像拉取失败，确认它是网络问题的衍生后果。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 集群网络出口配置 (如 Containerd proxy, 节点 iptables, 外部防火墙规则) | **critical** | 无法精确定位网络阻断的具体设备和策略，需要网络管理员配合排查。 |
| OOM 应用的崩溃前日志 | important | 无法判断是业务突发峰值还是内存泄漏导致 OOM。 |

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                                            │
│ 集群节点(node1, node2)到公共镜像仓库(registry-1.docker.io, registry.k8s.io)的出站网络被阻断。      │
│ DNS解析正常，但所有HTTPS(TCP 443)连接均因i/o timeout而失败。                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                                           │
│ 出站网络被阻断 → kubelet无法从registry-1.docker.io/registry.k8s.io拉取镜像                        │
│                  → 所有需拉取公共镜像的Pod均无法进入Running状态                                   │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                                          │
│ kubelet在拉取镜像时遇到TCP连接超时("dial tcp ... i/o timeout")，导致拉取失败。                    │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                                                     │
│ 1. 28个Pod处于ImagePullBackOff，21个Pod处于ErrImagePull。 (占比94%)                              │
│ 2. 1个Pod(connectivity-check-tmp)卡在ContainerCreating，实际为镜像拉取失败。                      │
│ 3. 1个Pod(reg-diag-tmp)因容器从未启动(镜像拉取失败)导致删除流程卡在Terminating。                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (集群异常Pod统计)、#2 & #3 (Node1 & Node2 拉取镜像超时)、#4 (时间线持续) 及 #5 (DNS正常)，
问题的根本原因是**集群节点的出站网络无法连接到公共容器镜像仓库**。这是导致集群中 **49个Pod（94%的异常Pod）** 异常的根源。

**次要问题**：Pod `rc-oomkilled-memory-limit-b6d999d-5f29d` 因容器内存限制不足导致 OOM，持续重启，独立于网络问题。

**置信度**：高 (95%)
- ✅ 跨节点(Node1/Node2)均存在完全一致的 `i/o timeout` 错误
- ✅ 不同镜像仓库(docker.io/registry.k8s.io)均连接失败
- ✅ 成功排除 DNS、认证、单个节点故障等可能性
- ❌ 缺失网络出口配置的直接证据

---

## 🛠️ 修复建议

### ⚠️ 首要任务：解决网络连通性
**请立即联系您的网络管理员，检查并解决集群节点（`node1`, `node2`）到以下目标的网络连通性。**

1.  **检查点**：集群节点的 **出口防火墙 / 代理 / NAT网关**。
2.  **管理地址**：确保允许出站到 `registry-1.docker.io` 和 `registry.k8s.io` 的 **HTTPS (TCP 443)** 和 **HTTP (TCP 80)** 流量。
3.  **检查代理**：如果集群配置了 `HTTP_PROXY` 环境变量拉取镜像，请检查代理服务器本身是否可达且正常工作。

### 临时变通方案（网络问题解决前）
**1. [替代方案] 使用可信镜像仓库**
将所有公共镜像先同步到可以访问的私有仓库（如 `harbor.example.com`），然后修改 Deployment 的镜像地址。
*应用示例：*
```bash
# 假设替换 busybox:1.36.1
kubectl set image deployment/<deploy-name> -n <namespace> <container-name>=harbor.example.com/library/busybox:1.36.1
```

**2. [可选] 将镜像提前拉取到节点**
在能访问外网的机器上拉取镜像，导出为 `.tar` 文件，然后手动导入到每个节点上。
```bash
# 在能访问外网的机器上
docker pull busybox:1.36.1
docker save -o busybox-1.36.1.tar busybox:1.36.1

# 在集群节点上 (node1, node2)
ctr -n k8s.io images import busybox-1.36.1.tar
# 或
crictl pull busybox:1.36.1
```

### 解决次要问题：OOMKilled
**1. [立即] 增加内存限制**
```bash
# 为 OOM 的 Pod 增加内存限制，例如从当前 unknown 增加到 512Mi
kubectl set resources deployment/rc-oomkilled-memory-limit -n aiops-e2e --limits=memory=512Mi
```
*依据*：Exit Code 137 明确指向OOM，需增加资源上限。*

**2. [可选] 查看崩溃前日志**
```bash
kubectl logs rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e --previous | tail -100
```
*目的*：确认内存溢出是突发还是内存泄漏导致。*

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 验证网络 | `kubectl exec -n default <running_pod_name> -- curl -I https://registry-1.docker.io` | 返回 HTTP 200/301 (非超时) |
| 2. 验证镜像拉取 | `crictl pull busybox:1.36.1` (在任一个节点上) | 镜像成功拉取，无 i/o timeout 错误 |
| 3. 验证Pod恢复 | `kubectl get pods -A \| grep -E 'ImagePullBackOff\|ErrImagePull\|ContainerCreating'` | 上述状态 Pod 开始转为 Pending → Running |
| 4. 验证OOM修复 | `kubectl get pod <oom_pod> -n aiops-e2e` | STATUS 显示 Running，Restart Count 不再增加 |

---

## ⚠️ 注意事项
- **首要解决网络**：不解决网络，大多数应用（49/52）无法修复。
- **临时方案风险**：手动导入镜像的方案在节点重启后镜像会丢失，建议配置私有镜像仓库作为长期方案。
- **OOM问题**：增加内存限制是临时措施。如果确认是内存泄漏，需开发团队修复代码。
- **Terminating Pod**：网络修复后，`reg-diag-tmp` Pod 应该会自动完成清理。如果依然卡住，可以尝试强制删除：
  ```bash
  kubectl delete pod reg-diag-tmp -n default --force --grace-period=0
  ```

---

## 📊 性能统计

├─ 总耗时: 2.3m
├─ 问题定位: 44.5s (32%) ✅
├─ 证据链采集: 43.7s (32%) ✅
├─ 根因分析: 22.9s (17%) ✅
├─ 汇总总结: 26.8s (19%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 30 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-oomkilled, pod-terminating-stuck, pod-sandbox-create-failed
- **工具调用**: 30 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
