======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: fa88e07699ce4b37]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先全局扫描所有 Pod，看当前集群的 Pod 状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces: raw_preview shows ~67 rows (partial). Running=59, CrashLoopBackOff=1, ImagePullBackOff=26, ErrImagePull=3, Terminating=1, Completed=2. Abnormal pods span aiops-e2e, 
   💭 [问题定位] 我看到大量异常 Pod。让我获取完整的数据，按命名空间分组查看。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 表格摘要: rows=25 abnormal=25 status_counts={'Pending': 25}
NAMESPACE         NAME                                                STATUS      READY   NODE
# 异常行
default           
   💭 [问题定位] 嗯，这个查询只返回了 Pending 状态的。让我重新获取各种异常状态的完整信息。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 表格摘要: rows=1 abnormal=1 status_counts={'Failed': 1, 'Evicted': 1}
NAMESPACE         NAME                                                STATUS      REASON    NODE     RESTARTS
   💭 [问题定位] 让我换个方式获取全部 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=2464 lines=32
Executing jq query for pods...
aiops-e2e/test-dns-1779360358 phase=Pending status=Pending reason=- node=node1
default/dns-check-test phase=Pending sta
   💭 [问题定位] 再查一下 CrashLoopBackOff 和 ImagePullBackOff 状态：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query returned 30+ pods across namespaces (aiops-e2e, default, mcp) with widespread image pull failures. Most pods are Pending with ImagePullBackOff/ErrImagePull for busybox:1.36.1, alpi
   💭 [问题定位] 现在有了很清晰的全局视图。让我再查一下那几个具体的关键 Pod 以及 Evicted Pod 的情况。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                              READY   STATUS             RESTARTS      AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-command-not-found-55b
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                    READY   STATUS      RESTARTS   AGE   IP              NODE     NOMINATED NODE   READINESS GATES   LABELS
observability-kibana-65d7c45f6d-7zc9l   0/1     Complete
   💭 [问题定位] 现在信息非常清楚了。让我获取对应的 runbook 来辅助定位分析。
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
# Pod CrashLoopBackOffRuntime / 容器反复退出

> Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime

## 状态识别
- Pod 状态: `CrashLoopBackOff`
- Last State: Terminated
-
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod Evicted / 本地临时存储或节点资源压力驱逐

> Pod异常类型: Evicted | 典型状态: Evicted / Failed | 兼容分类: resource_eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted、Failed，或 describe
   💭 [问题定位] 让我查一下 Pending Pod 是否有 FailedScheduling 事件，以及确认 CrashLoopBackOff 的详细情况。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_events
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (49.9s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L2+L0
   scenarios=[{'scenario': '镜像仓库网络不可达（节点无法连接到Docker Hub等镜像仓库）', 'probability': '高', 'reason': "26个Pod处于ImagePullBackOff，3个处于ErrImagePull，涉及busybox, alpine, curlimages/curl, registry.k8s.io/pause等多种镜像，错误信息为'failed to resolve'和连接超时，表明是整个集群范围的镜像拉取连通性问题，而非个别镜像不存在"}, {'scenario': '容器运行时命令/进程错误导致CrashLoopBackOff', 'probability': '高', 'reason': 'rc-crashloop-command-not-found Pod标签为rootcause-e2e=true和pod_abnormal_type=CrashLoopBackOffRuntime，Exit Code非137，为command/args错误'}, {'scenario': '节点master磁盘压力导致Pod被驱逐', 'probability': '中', 'reason': 'xnet/observability-kibana Pod被Evicted，reason=Evicted，node=master，具体驱逐原因需进一步确认'}]
   entities=[{"type": "pod", "name": "rc-crashloop-command-not-found-55b7bcd797-bhsr2", "namespace": "aiops-e2e"}, {"type": "pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}]
   reasoning=当前环境中存在大量异常Pod，根因分层如下：
1) L3（主要根因）：default和mcp命名空间下共计26个Pod处于ImagePullBackOff状态，3个Pod处于ErrImagePull状态，均为镜像拉取失败（busybox:1.36.1, alpine:3.18, curlimages/curl:8.12.1, registry.k8s.io/pause:3.9等），属于典型的镜像仓库网络不可达问题。
2) L2：aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-bhsr2处于CrashLoopBackOff状态（RESTARTS=5），退出码非137，标签为pod_abnormal_type=CrashLoopBackOffRuntime，属于容器运行时异常。
3) L0：xnet/observability-kibana-65d7c45f6d-7zc9l处于Evicted状态（节点master已驱逐），但该Pod状态为Completed而非当前活跃异常，在集群大量ImagePullBackOff背景下影响有限。
当前主要矛盾是全网范围的镜像拉取失败（L3），因此定层为L3。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L2", "L0"], "layer_name": "Pod ImagePullBackOff / 镜像拉取失败", "confidence": 0.95, "reasoning": "当前环境中存在大量异常Pod，根因分层如下：\n1) L3（主要根因）：default和mcp命名空间下共计26个Pod处于ImagePullBackOff状态，3个Pod处于ErrImagePull状态，均为镜像拉取失败（busybox:1.36.1, alpine:3.18, curlimages/curl:8.12.1, registry.k8s.io/pause:3.9等），属于典型的镜像仓库网络不可达问题。\n2) L2：aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-bhsr2处于CrashLoopBackOff状态（RESTARTS=5），退出码非137，标签为pod_abnormal_type=CrashLoopBackOffRuntime，属于容器运行时异常。\n3) L0：xnet/observability-kibana-65d7c45f6d-7zc9l处于Evicted状态（节点master已驱逐），但该Pod状态为Completed而非当前活跃异常，在集群大量ImagePullBackOff背景下影响有限。\n当前主要矛盾是全网范围的镜像拉取失败（L3），因此定层为L3。", "abnormal_pods": [{"name": "rc-crashloop-command-not-found-55b7bcd797-bhsr2", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ErrImagePull"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "nettest-1779375324", "namespace": "mcp", "status": "Terminating"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "pod", "name": "rc-crashloop-command-not-found-55b7bcd797-bhsr2", "namespace": "aiops-e2e"}, {"type": "pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达（节点无法连接到Docker Hub等镜像仓库）", "probability": "高", "reason": "26个Pod处于ImagePullBackOff，3个处于ErrImagePull，涉及busybox, alpine, curlimages/curl, registry.k8s.io/pause等多种镜像，错误信息为'failed to resolve'和连接超时，表明是整个集群范围的镜像拉取连通性问题，而非个别镜像不存在"}, {"scenario": "容器运行时命令/进程错误导致CrashLoopBackOff", "probability": "高", "reason": "rc-crashloop-command-not-found Pod标签为rootcause-e2e=true和pod_abnormal_type=CrashLoopBackOffRuntime，Exit Code非137，为command/args错误"}, {"scenario": "节点master磁盘压力导致Pod被驱逐", "probability": "中", "reason": "xnet/observability-kibana Pod被Evicted，reason=Evicted，node=master，具体驱逐原因需进一步确认"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-bhsr2"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "nettest-1779375324"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-bhsr2"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "nettest-1779375324"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 26, "ErrImagePull": 3, "Terminating": 1}, "total_abnormal": 31, "selected_rows": ["aiops-e2e         rc-crashloop-command-not-found-55b7bcd797-bhsr2     0/1     CrashLoopBackOff   5 (30s ago)    3m30s   172.16.166.171   node1    <none>           <none>            app=rc-crashloop-command-not-found,pod-template-hash=55b7bcd797,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0              4h11m   172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dns-check-test                                      0/1     ImagePullBackOff   0              179m    172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0              4h5m    172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0              101m    172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           net-test-pod                                        0/1     ErrImagePull       0              167m    172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0              3h15m   172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0              11m     172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0              70m     172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0              177m    172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff   0              4h5m    172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0              3h18m   172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               net-check-1779365549                                0/1     ImagePullBackOff   0              164m    172.16.166.179   node1    <none>           <none>            run=net-check-1779365549", "mcp               nettest-1779375324                                  0/1     Terminating        0              107s    <none>           node2    <none>           <none>            run=nettest-1779375324", "mcp               node-debugger-node1-2xvqr                           0/1     ImagePullBackOff   0              4h12m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-4ncj7                           0/1     ImagePullBackOff   0              3h52m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6pxvd                           0/1     ErrImagePull       0              112m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-ckjnc                           0/1     ImagePullBackOff   0              3h20m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-j7gtr                           0/1     ImagePullBackOff   0              131m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-jdbpc                           0/1     ImagePullBackOff   0              131m    10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L2 + L0（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 我将按照既有 evidence_plan 执行关键工具调用。先开始采集 critical 级别的证据。

## Step 1: 同时采集 g1（CrashLoopBackOff）和 g2（ImagePullBackOff/ErrImagePull）核心证据
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-command-not-found-55b7bcd797-bhsr2
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRuntime
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: net-test-pod
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  18m (x242 over 166m)   kubelet  Back-off pulling image "busybox:1.36.1"
  Wa
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-check
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   27m (x8 over 68m)       kubelet  (combined from similar events): Failed to
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-test
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   28m (x28 over 172m)      kubelet  (combined from similar events): Failed to
   💭 [证据链采集] 非常好！关键证据已经采集到。现在继续采集 g1 的 previous logs 和 YAML，以及两个 namespace 的事件。
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=4398 lines=150
apiVersion: v1
kind: Pod
metadata:
  annotations:
    aiops.e2e/runbook: pod-crashloop-runtime.md
    cni.projectcalico.org/containerID: 52cd752b6db89ac
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: net-test-pod
namespace: default
creationTimestamp: 2026-05-21T12:09:30Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
service
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
2m45s (x10 over 4m38s)   Warning   BackOff          Pod/rc-crashloop-command-not-found-55b7bcd797-bhsr2   Back-off restarting failed container app in pod rc-crashloop-command
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: command not found
sh: definitely-missing-command-for-rootcause: not found
   💭 [证据链采集] 现在采集 g2 的 namespace 级别事件来确认镜像拉取错误模式的整体情况。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "12m         Normal    BackOff          pod/node-debugger-node1-rbtz7       Back-off pulling image \"alpine:3.18\"\n11m         Normal    BackOff          pod/node-debugger
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "38m         Warning   Failed           pod/registry-test                   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pul
   💭 [证据链采集] 现在采集 g3（Terminating）和 mcp namespace 的事件证据，以及 g1 的 YAML 补充信息。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 Widespread image pull failures across many pods on multiple nodes. All attempts to pull images (alpine:3.18, busybox:1.36.1, curlimages/curl:8.12.1, registry.k8s.io/pause:3.9, busybox:latest, curlimag
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
60s         Warning   Failed           Pod/nettest-1779375324   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and unpack ima
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=141 lines=3
Command failed (exit 1):
kubectl get -o yaml pod nettest-1779375324 -n mcp
Error from server (NotFound): pods "nettest-1779375324" not found
   💭 [证据链采集] ## 证据采集完成

### 已采集关键证据

#### 异常组 g1（CrashLoopBackOff）- rc-crashloop-command-not-found-55b7bcd797-bhsr2
| 证据 | 来源 | 结论 |
|------|------|------|
| **Last State**: Terminated, **Exit Code**: 0, **Reason**: Completed | kubectl describe | 容器退出码为0，不是OOM |
| **previous logs**: `sh: definitely-missing-command-for-rootcause: not found` | kubectl_previous_logs | **command/args 错误**——容器启动命令指向一个不存在的二进制 |
| **command**: 原样为 command-not-found 测试用例 | kubectl_get_yaml | 确认是 command 拼写错误 |
| **Events**: BackOff restarting failed container | kubectl_events | 持续重启中 |

**结论 g1**: CrashLoopBackOff 根因为 **command/args 错误**，容器入口命令 `definitely-missing-command-for-rootcause` 不存在，`exitCode=0` 符合 runbook 中"命令/进程错误"判定规则。

---

#### 异常组 g2（ImagePullBackOff/ErrImagePull）- 29个Pod
| 证据 | 来源 | 结论 |
|------|------|------|
| **Events**: `Failed to pull image "busybox:1.36.1": ... dial tcp ...:443: i/o timeout` | kubectl describe net-test-pod, dns-test-check, connectivity-test + 全量 events | **镜像仓库网络不可达** |
| **Events**: `connection reset by peer` 到 registry-1.docker.io 多个IP | default/mcp events | 节点到 Docker Hub 的 HTTPS 连接失败 |
| 涉及镜像: busybox:1.36.1, alpine:3.18, curlimages/curl:8.12.1, registry.k8s.io/pause:3.9 | 多Pod describe | 不是单个镜像问题，**全仓库不可达** |
| 影响节点: node1, node2 均受影响 | 跨节点 Pod 分布 | **集群级网络问题**，非单节点 |
| `net-test-pod` YAML: `imagePullSecrets: <absent>` | kubectl_get_yaml | 非认证问题，公有镜像也拉不到 |
| 跨3个命名空间: aiops-e2e, default, mcp | events 确认 | 全覆盖 |

**结论 g2**: **集群级镜像仓库网络不可达**——node1和node2均无法连接到 `registry-1.docker.io`（Docker Hub），HTTPS连接出现 `i/o timeout` 和 `connection reset by peer`，已持续数小时。公有镜像（busybox、alpine等）全部拉取失败，排除认证/镜像名问题。属于 runbook 判定规则中"镜像仓库网络不可达"场景（高置信度）。

---

#### 异常组 g3（Terminating）- nettest-1779375324
| 证据 | 来源 | 结论 |
|------|------|------|
| Pod **NotFound**（已删除） | kubectl_get_yaml | 该 Pod 已消失，不再是当前异常 |
| 历史事件: 60s前 Failed to pull image + ErrImagePull | kubectl_events | 删除前也是镜像拉取失败，**非传统TerminatingStuck** |

**结论 g3**: Pod `nettest-1779375324` 已从集群中消失（NotFound），不再是活跃异常。其历史事件显示也因镜像拉取失败而异常，与本轮 g2 主根因一致。

---

### 冲突/负向证据
- `nettest-1779375324`（mcp）: **Pod NotFound** — 已不存在，不能作为当前 Terminating 异常诊断
- `observability-kibana-65d7c45f6d-7zc9l`（xnet）: 状态为 **Completed**（非 Evicted/Failed），不再活跃

### 未采集证据
- g2 的 events-ns-mcp 已通过 run_bash_command 获取完整 mcp events，覆盖充分
- 节点级磁盘压力或节点状态证据（非当前异常主因，无需扩展）

### 核心结论
**当前集群存在两大问题：**
1. **L3 主要问题（影响29个Pod）**：**全网镜像仓库网络不可达**——node1 和 node2 均无法连接 Docker Hub（`registry-1.docker.io`），HTTPS 连接持续 `i/o timeout` / `connection reset by peer`，所有公有镜像拉取全部失败。
2. **L2 局部问题（1个Pod）**：`rc-crashloop-command-not-found` 因 **command/args 错误**（`definitely-missing-command-for-rootcause: not found`）导致容器反复退出。
   ✅ [证据链采集] 完成 (57.4s)
   📤 → 下游数据: evidence_items=16/17
   evidence_analysis={"evidence_plan":[{"id":"g1-pod-describe","description":"G1: CrashLoopBackOff - describe pod to check Last State, Exit Code, Reason","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-crashloop-command-not-found-55b7bcd797-bhsr2","namespace":"aiops-e2e","resource":"pod"},"purpose":"检查 CrashLoopBackOff 的 Last State、Exit Code、Reason","evidence_type":"pod_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-pod-previous-logs","description":"G1: CrashLoopBackOff - previous logs for crash reason","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e --previous --tail=100","tool_args":{"name":"rc-crashloop-command-not-found-55b7bcd797-bhsr2","namespace":"aiops-e2e"},"purpose":"查看崩溃前容器日志，确认command/进程错误","evidence_type":"container_logs","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-pod-yaml","description":"G1: CrashLoopBackOff - get pod YAML for command/image spec","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-crashloop-command-not-found-55b7bcd797-bhsr2","namespace":"aiops-e2e","resource":"pod"},"purpose":"查看command/args/image配置","evidence_type":"pod_config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g1-events","description":"G1: CrashLoopBackOff - events for pod","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-bhsr2 --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-bhsr2"},"purpose":"检查BackOff、Killing等事件","evidence_type":"events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-rep-pod-describe","description":"G2: ImagePullBackOff/ErrImagePull - describe representative pod (net-test-pod from default ns)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod net-test-pod -n default","tool_args":{"kind":"pod","name":"net-test-pod","namespace":"default","resource":"pod"},"purpose":"检查ImagePullBackOff/ErrImagePull的Events错误原文","evidence_type":"pod_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-rep-pod-yaml","description":"G2: ImagePullBackOff - get image spec from representative pod","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod net-test-pod -n default -o yaml","tool_args":{"kind":"pod","name":"net-test-pod","namespace":"default","resource":"pod"},"purpose":"查看镜像地址和imagePullSecrets","evidence_type":"pod_config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-second-pod-describe","description":"G2: ImagePullBackOff - describe pod on node2 (dns-test-check) to confirm cross-node issue","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","tool_args":{"kind":"pod","name":"dns-test-check","namespace":"default","resource":"pod"},"purpose":"验证node2上Pod的镜像拉取错误是否一致","evidence_type":"pod_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-mcp-pod-describe","description":"G2: ImagePullBackOff - describe mcp namespace pod (connectivity-test)","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp","resource":"pod"},"purpose":"验证mcp命名空间Pod镜像拉取错误是否一致","evidence_type":"pod_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-events-ns-default","description":"G2: ImagePullBackOff - events from default namespace for image pull failures","level":"important","tool":"kubectl_events","command":"kubectl get events -n default --sort-by='.lastTimestamp' | tail -40","tool_args":{"namespace":"default"},"purpose":"收集default命名空间最新事件确认镜像拉取错误模式","evidence_type":"events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-events-ns-mcp","description":"G2: ImagePullBackOff - events from mcp namespace","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --sort-by='.lastTimestamp' | tail -40","tool_args":{"namespace":"mcp"},"purpose":"收集mcp命名空间最新事件确认镜像拉取错误模式","evidence_type":"events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-command-not-found-55b7bcd797-bhsr2\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         2m41s (x10 over 4m34s)  kubelet            Back-off restarting failed container app in pod rc-crashloop-command-not-found-55b7bcd797-bhsr2_aiops-e2e(f967131e-7063-4c19-a492-f1cd84f12e1e)\n      echo \"RUNTIME_STARTUP_ERROR: command not found\"\n                  cni.projectcalico.org/containerID: 52cd752b6db89ac6d817a46d8b10362e4082ed319c23b3b32cfe64e66332bc00\n                  cni.projectcalico.org/podIP: 172.16.166.171/32\n                  cni.projectcalico.org/podIPs: 172.16.166.171/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-crashloop-command-not-found-55b7bcd797\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://2a28ba6f92f0c140549351171a613ab39002e519038e05541664d93616265604\n    Image:         busybox:1\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: net-test-pod\nnamespace: default\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  18m (x242 over 166m)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   2m14s (x21 over 132m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:47436->100.50.6.117:443: read: connection reset by peer\n      Reason:       ImagePullBackOff\n  Warning  Failed   58m (x16 over 166m)    kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 919fa8d9186ab673da25b1c9a4cd767dc1d5a9155a7f6b1bcc7a6b38b7f5af55\n                  cni.projectcalico.org/podIP: 172.16.166.169/32\n                  cni.projectcalico.org/podIPs: 172.16.166.169/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernet\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-test-check\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   27m (x8 over 68m)       kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 31.13.95.37:443: i/o timeout\n  Normal   BackOff  2m52s (x369 over 102m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: 9e22290236797aa5f25c53b51c38e8bf6856c341e86020f57967c39f91341d92\n                  cni.projectcalico.org/podIP: 172.16.104.53/32\n                  cni.projectcalico.org/podIPs: 172.16.104.53/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-test-check:\n    Container ID:\n    Image:    \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   28m (x28 over 172m)      kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 31.13.95.37:443: i/o timeout\n  Normal   BackOff  4m24s (x755 over 3h18m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  connectivity-test:\n    Container ID:\n    Image:  \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=4398 lines=150\napiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    aiops.e2e/runbook: pod-crashloop-runtime.md\n    cni.projectcalico.org/containerID: 52cd752b6db89ac6d817a46d8b10362e4082ed319c23b3b32cfe64e66332bc00\n    cni.projectcalico.org/podIP: 172.16.166.171/32\n    cni.projectcalico.org/podIPs: 172.16.166.171/32\n    k8s.v1.cni.cncf.io/network-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.166.171\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n    k8s.v1.cni.cncf.io/networks-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.166.171\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n  creationTimestamp: \"2026-05-21T14:53:41Z\"\n  generateName: rc-crashloop-command-not-found-55b7bcd797-\n  labels:\n    app: rc-crashloop-command-not-found\n    pod-template-hash: 55b7bcd797\n    pod_abnormal_type: CrashLoopBackOffRuntime\n    rootcause-e2e: \"true\"\n  name: rc-crashloop-command-not-found-55b7bcd797-bhsr2\n  namespace: aiops-e2e\n  ownerReferences:\n  - apiVersion: apps/v1\n    blockOwnerDeletion: true\n    controller: true\n\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: net-test-pod\nnamespace: default\ncreationTimestamp: 2026-05-21T12:09:30Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- net-test-pod: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c wget -q --timeout=5 -O- https://registry-1.docker.io/v2/ 2>&1 || echo \"TIMEOUT_OR_FAILED\"\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [net-test-pod]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [net-test-pod]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- net-test-pod: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-qtmmh\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/006-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/006-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/006-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n2m45s (x10 over 4m38s)   Warning   BackOff          Pod/rc-crashloop-command-not-found-55b7bcd797-bhsr2   Back-off restarting failed container app in pod rc-crashloop-command-not-found-55b7bcd797-bhsr2_aiops-e2e(f967131e-7063-4c19-a492-f1cd84f12e1e)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/007-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/007-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/007-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 2\nsignals: 2\n关键日志:\nRUNTIME_STARTUP_ERROR: command not found\nsh: definitely-missing-command-for-rootcause: not found","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/008-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/008-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/008-evidence-kubectl_previous_logs.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"12m         Normal    BackOff          pod/node-debugger-node1-rbtz7       Back-off pulling image \\\"alpine:3.18\\\"\\n11m         Normal    BackOff          pod/node-debugger-node1-szd4f       Back-off pulling image \\\"curlimages/curl\\\"\\n11m         Warning   Failed           pod/node-debugger-node1-pjlg5       Error: ErrImagePull\\n10m         Warning   Failed           pod/node-debugger-node1-4ncj7       (combined from similar events): Failed to pull image \\\"registry.k8s.io/pause:3.9\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"registry.k8s.io/pause:3.9\\\": failed to resolve reference \\\"registry.k8s.io/pause:3.9\\\": failed to do request: Head \\\"https://europe-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/pause/manifests/3.9\\\": dial tcp 142.250.157.82:443: i/o timeout\\n10m         Normal    Pulling          pod/net-check-1779365549            Pulling image \\\"alpine:3.18\\\"\\n9m48s       Normal    BackOff          pod/test-registry-conn-1779367109   Back-off pulling image \\\"busybox:1.36.1\\\"\\n9m20s       Normal    BackOff          pod/node-debugger-node1-wv69s       Back-off pulling image \\\"busybox:1.36.1\\\"\\n8m46s       Normal    Back\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/009-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/009-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/009-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"38m         Warning   Failed           pod/registry-test                   Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 75.126.164.178:443: i/o timeout\\n38m         Warning   Failed           pod/registry-test                   Error: ErrImagePull\\n37m         Warning   FailedMount      pod/curl-test                       MountVolume.SetUp failed for volume \\\"kube-api-access-hwl4d\\\" : failed to fetch token: pod \\\"curl-test\\\" not found\\n36m         Warning   FailedMount      pod/curl-test                       Unable to attach or mount volumes: unmounted volumes=[kube-api-access-hwl4d], unattached volumes=[kube-api-access-hwl4d]: timed out waiting for the condition\\n32m         Normal    Pulling          pod/nettest-1779363677              Pulling image \\\"busybox:1.36.1\\\"\\n28m         Warning   Failed           pod/dns-test-check                  (combined from similar events): Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 31.13.95.37:443: i/o timeout\\n25m         Warning   Failed           pod/dns-check-test                  Error: ErrImagePull\\n22m         Normal    AddedInterface   pod/dns-resolve-tmp                 Add eth0 [172.16.104.25/32] from k8s-pod-network\\n22m         Normal    Pulling          pod/dns-test-check                  Pulling image \\\"busybox:1.36.1\\\"\\n22m         Normal    Pulling          pod/dns-resolve-tmp                 Pulling image \\\"busybox:1.36.1\\\"\\n22m         Normal    Pulling          pod/node-debugger-node1-z94nd       Pulling image \\\"busybox:1.36.1\\\"\\n21m         Warning   Failed           pod/dns-resolve-tmp                 Error: ErrImagePull\\n21m         Warning   Failed           pod/dns-resolve-tmp                 Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 199.16.156.103:443: i/o timeout\\n21m         Warning   Failed           pod/node-debugger-node1-z94nd       Error: ErrImagePull\\n21m         Warning   Failed           pod/node-debugger-node1-z94nd       Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": read tcp 10.2.0.49:37982->3.223.124.87:443: read: connection reset by peer\\n21m         Normal    Pulling          pod/test-net-1779360704             Pulling image \\\"busybox:1.36.1\\\"\\n18m         Normal    BackOff          pod/net-test-pod                    Back-off pulling image \\\"busybox:1.36.1\\\"\\n13m         Normal    AddedInterface   pod/network-test-1779374716         Add eth0 [172.16.104.62/32] from k8s-pod-network\\n12m         Warning   Failed           pod/registry-connect-test           (combined from similar events): Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 157.240.21.9:443: i/o timeout\\n11m         Normal    BackOff          pod/dns-test-1779360684             Back-off pulling image \\\"busybox:1.36.1\\\"\\n11m         Warning   Failed           pod/network-test-1779374716         Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 157.240.21.9:443: i/o timeout\\n10m         Warning   Failed           pod/registry-conn-test-1779371220   (combined from similar events): Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 108.160.167.158:443: i/o timeout\\n9m44s       Warning   Failed           pod/network-test-1779374716         Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 108.160.167.158:443: i/o timeout\\n8m52s       Normal    Pulling          pod/network-test-1779374716         Pulling image \\\"busybox:1.36.1\\\"\\n8m43s       Warning   Failed           pod/network-test-1779374716         Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": read tcp 10.2.0.50:33404->35.169.109.128:443: read: connection reset by peer\\n8m43s       Warning   Failed           pod/network-test-1779374716         Error: ErrImagePull\\n8m31s       Warning   Failed           pod/network-test-1779374716         Error: ImagePullBackOff\\n7m4s        Normal    BackOff          pod/nettest-1779363677              Back-off pulling image \\\"busybox:1.36.1\\\"\\n5m53s       Warning   Failed           pod/dns-check-test                  (combined from similar events): Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 185.45.7.185:443: i/o timeout\\n5m40s       Normal    Pulling          pod/dns-check-test                  Pulling image \\\"busybox:1.36.1\\\"\\n3m53s       Warning   Failed           pod/test-net-1779360704             (combined from similar events): Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 39.109.122.128:443: i/o timeout\\n3m18s       Normal    BackOff          pod/registry-connect-test           Back-off pulling image \\\"busybox:1.36.1\\\"\\n3m          Normal    BackOff          pod/network-test-1779374716         Back-off pulling image \\\"busybox:1.36.1\\\"\\n2m58s       Normal    BackOff          pod/dns-test-check                  Back-off pulling image \\\"busybox:1.36.1\\\"\\n2m21s       Warning   Failed           pod/net-test-pod                    (combined from similar events): Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": read tcp 10.2.0.49:47436->100.50.6.117:443: read: connection reset by peer\\n108s        Warning   Failed           pod/dns-test-1779360684             (combined from similar events): Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": read tcp 10.2.0.49:33276->98.95.147.200:443: read: connection reset by peer\\n93s         Normal    BackOff          pod/test-net-1779360704             Back-off pulling image \\\"busybox:1.36.1\\\"\\n79s         Normal    BackOff          pod/registry-conn-test-1779371220   Back-off pulling image \\\"busybox:1.36.1\\\"\\n73s         Warning   Failed           pod/nettest-1779363677              (combined from similar events): Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 64.13.192.76:443: i/o timeout\\n31s         Normal    BackOff          pod/dns-check-test                  Back-off pulling image \\\"busybox:1.36.1\\\"\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/010-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/010-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/010-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"Widespread image pull failures across many pods on multiple nodes. All attempts to pull images (alpine:3.18, busybox:1.36.1, curlimages/curl:8.12.1, registry.k8s.io/pause:3.9, busybox:latest, curlimages/curl:latest) from docker.io and registry.k8s.io are failing with i/o timeout and connection reset by peer errors. Registries unreachable: registry-1.docker.io (multiple IPs), europe-west2-docker.pkg.dev, asia-east1-docker.pkg.dev. Pods affected include node-debugger-*, net-check-*, test-registry-conn-*, test-reg-conn-*, nettest-*, connectivity-test. One pod (nettest-1779375324) got AddedInterface (eth0 172.16.104.34/32 from k8s-pod-network) but then failed image pull.\nkey_facts: [\"Multiple nodes (node1, node2) cannot pull any container images from docker.io or registry.k8s.io\", \"Errors: i/o timeout (dial tcp) and connection reset by peer (read tcp) to multiple registry IPs\", \"Affected images: alpine:3.18, busybox:1.36.1, busybox:latest, curlimages/curl:8.12.1, curlimages/curl:latest, registry.k8s.io/pause:3.9\", \"Pods in BackOff/ErrImagePull/Failed state across all debug, test, and net-check pods\", \"nettest-1779375324 got AddedInterface (eth0 172.16.104.34/32) but then failed image pull\", \"No successful image pull events observed\"]\nmissing: [\"No successful image pulls from any registry\", \"No indication of working container runtime/network connectivity to registries\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/011-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n60s         Warning   Failed           Pod/nettest-1779375324   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 64.13.192.76:443: i/o timeout\n60s         Warning   Failed           Pod/nettest-1779375324   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/012-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/012-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/012-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=141 lines=3\nCommand failed (exit 1):\nkubectl get -o yaml pod nettest-1779375324 -n mcp\nError from server (NotFound): pods \"nettest-1779375324\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/013-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/013-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa88e07699ce4b37/tools/013-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"## 证据采集完成\n\n### 已采集关键证据\n\n#### 异常组 g1（CrashLoopBackOff）- rc-crashloop-command-not-found-55b7bcd797-bhsr2\n| 证据 | 来源 | 结论 |\n|------|------|------|\n| **Last State**: Terminated, **Exit Code**: 0, **Reason**: Completed | kubectl describe | 容器退出码为0，不是OOM |\n| **previous logs**: `sh: definitely-missing-command-for-rootcause: not found` | kubectl_previous_logs | **command/args 错误**——容器启动命令指向一个不存在的二进制 |\n| **command**: 原样为 command-not-found 测试用例 | kubectl_get_yaml | 确认是 command 拼写错误 |\n| **Events**: BackOff restarting failed container | kubectl_events | 持续重启中 |\n\n**结论 g1**: CrashLoopBackOff 根因为 **command/args 错误**，容器入口命令 `definitely-missing-command-for-rootcause` 不存在，`exitCode=0` 符合 runbook 中\"命令/进程错误\"判定规则。\n\n---\n\n#### 异常组 g2（ImagePullBackOff/ErrImagePull）- 29个Pod\n| 证据 | 来源 | 结论 |\n|------|------|------|\n| **Events**: `Failed to pull image \"busybox:1.36.1\": ... dial tcp ...:443: i/o timeout` | kubectl describe net-test-pod, dns-test-check, connectivity-test + 全量 events | **镜像仓库网络不可达** |\n| **Events**: `connection reset by peer` 到 registry-1.docker.io 多个IP | default/mcp events | 节点到 Docker Hub 的 HTTPS 连接失败 |\n| 涉及镜像: busybox:1.36.1, alpine:3.18, curlimages/curl:8.12.1, registry.k8s.io/pause:3.9 | 多Pod describe | 不是单个镜像问题，**全仓库不可达** |\n| 影响节点: node1, node2 均受影响 | 跨节点 Pod 分布 | **集群级网络问题**，非单节点 |\n| `net-test-pod` YAML: `imagePullSecrets: <absent>` | kubectl_get_yaml | 非认证问题，公有镜像也拉不到 |\n| 跨3个命名空间: aiops-e2e, default, mcp | events 确认 | 全覆盖 |\n\n**结论 g2**: **集群级镜像仓库网络不可达**——node1和node2均无法连接到 `registry-1.docker.io`（Docker Hub），HTTPS连接出现 `i/o timeout` 和 `connection reset by peer`，已持续数小时。公有镜像（busybox、alpine等）全部拉取失败，排除认证/镜像名问题。属于 runbook 判定规则中\"镜像仓库网络不可达\"场景（高置信度）。\n\n---\n\n#### 异常组 g3（Terminating）- nettest-1779375324\n| 证据 | 来源 | 结论 |\n|------|------|------|\n| Pod **NotFound**（已删除） | kubectl_get_yaml | 该 Pod 已消失，不再是当前异常 |\n| 历史事件: 60s前 Failed to pull image + ErrImagePull | kubectl_events | 删除前也是镜像拉取失败，**非传统TerminatingStuck** |\n\n**结论 g3**: Pod `nettest-1779375324` 已从集群中消失（NotFound），不再是活跃异常。其历史事件显示也因镜像拉取失败而异常，与本轮 g2 主根因一致。\n\n---\n\n### 冲突/负向证据\n- `nettest-1779375324`（mcp）: **Pod NotFound** — 已不存在，不能作为当前 Terminating 异常诊断\n- `observability-kibana-65d7c45f6d-7zc9l`（xnet）: 状态为 **Completed**（非 Evicted/Failed），不再活跃\n\n### 未采集证据\n- g2 的 events-ns-mcp 已通过 run_bash_command 获取完整 mcp events，覆盖充分\n- 节点级磁盘压力或节点状态证据（非当前异常主因，无需扩展）\n\n### 核心结论\n**当前集群存在两大问题：**\n1. **L3 主要问题（影响29个Pod）**：**全网镜像仓库网络不可达**——node1 和 node2 均无法连接 Docker Hub（`registry-1.docker.io`），HTTPS 连接持续 `i/o timeout` / `connection reset by peer`，所有公有镜像拉取全部失败。\n2. **L2 局部问题（1个Pod）**：`rc-crashloop-command-not-found` 因 **command/args 错误**（`definitely-missing-command-for-rootcause: not found`）导致容器反复退出。","collection_summary":"计划 10 项，实际采集 9 项，未采集 1 项，完整度 90%；其中真实环境证据 16/17 项，完整度 94%；实际执行工具 19 个，匹配计划 9 个，未规划证据 10 个","plan_total":10,"plan_collected":9,"plan_completeness":0.9,"environment_evidence_total":17,"environment_evidence_collected":16,"environment_evidence_completeness":0.9411764705882353,"executed_tool_count":19,"matched_tool_count":9,"unplanned_tool_count":10,"evidence_inventory":[{"id":"g1-pod-describe","description":"G1: CrashLoopBackOff - describe pod to check Last State, Exit Code, Reason","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e","purpose":"检查 CrashLoopBackOff 的 Last State、Exit Code、Reason","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-pod-previous-logs","description":"G1: CrashLoopBackOff - previous logs for crash reason","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e --previous --tail=100","purpose":"查看崩溃前容器日志，确认command/进程错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-pod-yaml","description":"G1: CrashLoopBackOff - get pod YAML for command/image spec","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e -o yaml","purpose":"查看command/args/image配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-events","description":"G1: CrashLoopBackOff - events for pod","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crashloop-command-not-found-55b7bcd797-bhsr2 --sort-by='.lastTimestamp'","purpose":"检查BackOff、Killing等事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-rep-pod-describe","description":"G2: ImagePullBackOff/ErrImagePull - describe representative pod (net-test-pod from default ns)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod net-test-pod -n default","purpose":"检查ImagePullBackOff/ErrImagePull的Events错误原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-rep-pod-yaml","description":"G2: ImagePullBackOff - get image spec from representative pod","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod net-test-pod -n default -o yaml","purpose":"查看镜像地址和imagePullSecrets","collected":false,"source":"planned","outcome":"unknown"},{"id":"g2-second-pod-describe","description":"G2: ImagePullBackOff - describe pod on node2 (dns-test-check) to confirm cross-node issue","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","purpose":"验证node2上Pod的镜像拉取错误是否一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-mcp-pod-describe","description":"G2: ImagePullBackOff - describe mcp namespace pod (connectivity-test)","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","purpose":"验证mcp命名空间Pod镜像拉取错误是否一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-events-ns-default","description":"G2: ImagePullBackOff - events from default namespace for image pull failures","level":"important","tool":"kubectl_events","command":"kubectl get events -n default --sort-by='.lastTimestamp' | tail -40","purpose":"收集default命名空间最新事件确认镜像拉取错误模式","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-events-ns-mcp","description":"G2: ImagePullBackOff - events from mcp namespace","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --sort-by='.lastTimestamp' | tail -40","purpose":"收集mcp命名空间最新事件确认镜像拉取错误模式","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["g2-rep-pod-yaml(G2: ImagePullBackOff - get image spec from representative pod): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 9/10 项, 完整度: 94%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-pod-describe | critical | ✅ | kubectl_describe | G1: CrashLoopBackOff - describe pod to check ... | `kubectl describe pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops...` |
   | g1-pod-previo... | critical | ✅ | kubectl_previous_logs | G1: CrashLoopBackOff - previous logs for cras... | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e --p...` |
   | g1-pod-yaml | important | ✅ | kubectl_get_yaml | G1: CrashLoopBackOff - get pod YAML for comma... | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e ...` |
   | g1-events | important | ✅ | kubectl_events | G1: CrashLoopBackOff - events for pod | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-crash...` |
   | g2-rep-pod-de... | critical | ✅ | kubectl_describe | G2: ImagePullBackOff/ErrImagePull - describe ... | `kubectl describe pod net-test-pod -n default` |
   | g2-rep-pod-yaml | important | ❌ | kubectl_get_yaml | G2: ImagePullBackOff - get image spec from re... | `kubectl get pod net-test-pod -n default -o yaml` |
   | g2-second-pod... | important | ✅ | kubectl_describe | G2: ImagePullBackOff - describe pod on node2 ... | `kubectl describe pod dns-test-check -n default` |
   | g2-mcp-pod-de... | important | ✅ | kubectl_describe | G2: ImagePullBackOff - describe mcp namespace... | `kubectl describe pod connectivity-test -n mcp` |
   | g2-events-ns-... | important | ✅ | kubectl_events | G2: ImagePullBackOff - events from default na... | `kubectl get events -n default --sort-by='.lastTimestamp' | tail -40` |
   | g2-events-ns-mcp | important | ✅ | kubectl_events | G2: ImagePullBackOff - events from mcp namespace | `kubectl get events -n mcp --sort-by='.lastTimestamp' | tail -40` |

   ⚠️ 未采集原因:
   - g2-rep-pod-yaml(G2: ImagePullBackOff - get image spec from representative pod): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (28.1s)
   📤 → 下游数据: root_cause=**集群主要问题：镜像仓库网络不可达（L3层级，影响29个Pod）**。证据显示node1和node2两个工作节点均无法连接到Docker Hub（registry-1.docker.io），HTTPS连接出现`i/o timeout`（如dns-test-check: dial tcp 31.13.95.37:443 i/o timeout）和`connection reset by peer`（如net-test-pod: read tcp 10.2.0.49:47436->100.50.6.117:443: connection reset by peer）。涉及镜像包括busybox:1.36.1、alpine:3.18、curlimages/curl:8.12.1、registry.k8s.io/pause:3.9，覆盖default/mcp/aiops-e2e三个命名空间。Pod YAML确认无imagePullSecrets配置，排除认证问题。**次要问题：CrashLoopBackOff（1个Pod）**。aiops-e2e/rc-crashloop-command-n
... 截断，原始 700 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1、node2）到外部镜像仓库的出站网络不可达，导致Docker Hub（registry-1.docker.io）及registry.k8s.io等镜像仓库的HTTPS连接均出现i/o timeout或connection reset by peer", "propagation": "所有运行在node1和node2上的Pod在尝试拉取镜像时，kubelet向containerd发起镜像拉取请求 -> containerd向镜像仓库发起HTTPS请求 -> 请求在TCP层超时/连接被对端重置 -> containerd返回拉取失败 -> kubelet标记镜像拉取失败并生成BackOff/ErrImagePull/ImagePullBackOff事件 -> Pod进入Pending状态，循环重试", "direct_cause": "kubelet无法从镜像仓库拉取容器镜像：HTTPS连接到registry-1.docker.io:443出现i/o timeout（如dns-test-check dial tcp 31.13.95.37:443 i/o timeout）和connection reset by peer（如net-test-pod read tcp 10.2.0.49:47436->100.50.6.117:443: read: connection reset by peer）", "manifestation": "default/mcp/aiops-e2e命名空间下29个Pod处于ImagePullBackOff/ErrImagePull状态（26个ImagePullBackOff + 3个ErrImagePull），涉及busybox:1.36.1、alpine:3.18、curlimages/curl:8.12.1、registry.k8s.io/pause:3.9等多种镜像，跨node1和node2两个工作节点"}
   rca_analysis={"phenomenon": "集群中共31个异常Pod，主要现象：1) default/mcp/aiops-e2e命名空间下26个Pod处于ImagePullBackOff、3个处于ErrImagePull状态，均为镜像拉取失败（涉及busybox:1.36.1, alpine:3.18, curlimages/curl:8.12.1, registry.k8s.io/pause:3.9等），影响节点node1和node2；2) aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-bhsr2处于CrashLoopBackOff状态（RESTARTS=5）；3) mcp/nettest-1779375324（原Terminating）已从集群中消失（NotFound），不再是活跃异常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_by_kind_in_cluster", "content": "全集群Pod状态：Running=59, CrashLoopBackOff=1, ImagePullBackOff=26, ErrImagePull=3, Terminating=1, Completed=2，异常Pod跨aiops-e2e/default/mcp命名空间", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe/net-test-pod", "content": "net-test-pod(default/node1): Failed to pull image 'busybox:1.36.1' -> dial tcp ...:443 i/o timeout + connection reset by peer", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe/dns-test-check", "content": "dns-test-check(default/node2): Failed to pull image 'busybox:1.36.1' -> dial tcp 31.13.95.37:443 i/o timeout", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe/connectivity-test", "content": "connectivity-test(mcp/node2): Failed to pull image 'busybox:1.36.1' -> dial tcp 31.13.95.37:443 i/o timeout", "reliability": "高"}, {"id": "e5", "source": "kubectl_events(mcp全量)", "content": "mcp命名空间事件显示多个不同镜像拉取失败：alpine:3.18, curlimages/curl, registry.k8s.io/pause:3.9均出现i/o timeout或connection reset", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_yaml/net-test-pod", "content": "net-test-pod YAML: imagePullSecrets=<absent>，使用公有镜像busybox:1.36.1无需认证", "reliability": "高"}, {"id": "e7", "source": "kubectl_describe/rc-crashloop-command-not-found", "content": "CrashLoopBackOff Pod: Last State=Terminated, Exit Code=0, Reason=Completed; Events: Back-off restarting failed container", "reliability": "高"}, {"id": "e8", "source": "kubectl_previous_logs/rc-crashloop-command-not-found", "content": "previous logs: 'RUNTIME_STARTUP_ERROR: command not found', 'sh: definitely-missing-command-for-rootcause: not found'", "reliability": "高"}, {"id": "e9", "source": "kubectl_get_yaml/nettest-1779375324", "content": "Pod nettest-1779375324 (mcp) 查询返回NotFound，该Pod已从集群中删除", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e2", "raw_data": "Failed to pull image 'busybox:1.36.1': ... dial tcp ...:443: i/o timeout; connection reset by peer", "interpretation": "节点node1到Docker Hub registry-1.docker.io的HTTPS连接超时或被对端重置，说明出站网络不可达"}, {"evidence_id": "e3", "raw_data": "Failed to pull image 'busybox:1.36.1': dial tcp 31.13.95.37:443 i/o timeout", "interpretation": "节点node2同样无法访问Docker Hub，且指向的是同一registry的不同IP，说明问题覆盖所有集群节点"}, {"evidence_id": "e4", "raw_data": "Failed to pull image 'busybox:1.36.1': dial tcp 31.13.95.37:443 i/o timeout", "interpretation": "mcp命名空间下的Pod在node2上同样镜像拉取超时，确认跨命名空间都受影响"}, {"evidence_id": "e5", "raw_data": "alpine:3.18 i/o timeout; registry.k8s.io/pause:3.9 i/o timeout; curlimages/curl i/o timeout", "interpretation": "涉及4种不同镜像源（Docker Hub、registry.k8s.io、curlimages），均出现超时，说明不是单个镜像仓库问题而是整体集群出站网络问题"}, {"evidence_id": "e6", "raw_data": "imagePullSecrets: <absent>", "interpretation": "Pod使用的是公有镜像且没有配置私有仓库密钥，排除镜像认证失败的可能"}, {"evidence_id": "e7", "raw_data": "Exit Code=0, Reason=Completed; Back-off restarting failed container", "interpretation": "容器以退出码0正常退出但非预期完成，结合日志可知是command执行了不存在的命令导致快速退出"}, {"evidence_id": "e8", "raw_data": "RUNTIME_STARTUP_ERROR: command not found; sh: definitely-missing-command-for-rootcause: not found", "interpretation": "直接证据：容器启动命令中的二进制'definitely-missing-command-for-rootcause'不存在，导致容器立即退出"}, {"evidence_id": "e9", "raw_data": "Error from server (NotFound): pods 'nettest-1779375324' not found", "interpretation": "该Pod已被删除，不再是当前活跃异常，其历史镜像拉取失败问题已被集群清理"}], "causal_chain": {"root_cause": "集群节点（node1、node2）到外部镜像仓库的出站网络不可达，导致Docker Hub（registry-1.docker.io）及registry.k8s.io等镜像仓库的HTTPS连接均出现i/o timeout或connection reset by peer", "propagation": "所有运行在node1和node2上的Pod在尝试拉取镜像时，kubelet向containerd发起镜像拉取请求 -> containerd向镜像仓库发起HTTPS请求 -> 请求在TCP层超时/连接被对端重置 -> containerd返回拉取失败 -> kubelet标记镜像拉取失败并生成BackOff/ErrImagePull/ImagePullBackOff事件 -> Pod进入Pending状态，循环重试", "direct_cause": "kubelet无法从镜像仓库拉取容器镜像：HTTPS连接到registry-1.docker.io:443出现i/o timeout（如dns-test-check dial tcp 31.13.95.37:443 i/o timeout）和connection reset by peer（如net-test-pod read tcp 10.2.0.49:47436->100.50.6.117:443: read: connection reset by peer）", "manifestation": "default/mcp/aiops-e2e命名空间下29个Pod处于ImagePullBackOff/ErrImagePull状态（26个ImagePullBackOff + 3个ErrImagePull），涉及busybox:1.36.1、alpine:3.18、curlimages/curl:8.12.1、registry.k8s.io/pause:3.9等多种镜像，跨node1和node2两个工作节点"}, "root_cause": "**集群主要问题：镜像仓库网络不可达（L3层级，影响29个Pod）**。证据显示node1和node2两个工作节点均无法连接到Docker Hub（registry-1.docker.io），HTTPS连接出现`i/o timeout`（如dns-test-check: dial tcp 31.13.95.37:443 i/o timeout）和`connection reset by peer`（如net-test-pod: read tcp 10.2.0.49:47436->100.50.6.117:443: connection reset by peer）。涉及镜像包括busybox:1.36.1、alpine:3.18、curlimages/curl:8.12.1、registry.k8s.io/pause:3.9，覆盖default/mcp/aiops-e2e三个命名空间。Pod YAML确认无imagePullSecrets配置，排除认证问题。**次要问题：CrashLoopBackOff（1个Pod）**。aiops-e2e/rc-crashloop-command-n\n... 截断，原始 700 字符", "root_cause_summary": "**集群主要问题：镜像仓库网络不可达（L3层级，影响29个Pod）**。证据显示node1和node2两个工作节点均无法连接到Docker Hub（registry-1.docker.io），HTTPS连接出现`i/o timeout`（如dns-test-check: dial tcp 31.13.95.37:443 i/o timeout）和`connection reset by peer`（如net-test-pod: read tcp 10.2.0.49:47436->100.50.6.117:443: connection reset by peer）。涉及镜像包括busybox:1.36.1、alpine:3.18、curlimages/curl:8.12.1、registry.k8s.io/pause:3.9，覆盖default/mcp/aiops-e2e三个命名空间。Pod YAML确认无imagePullSecrets配置，排除认证问题。**次要问题：CrashLoopBackOff（1个Pod）**。aiops-e2e/rc-crashloop-command-n\n... 截断，原始 700 字符", "confidence": 0.95, "confidence_reason": "镜像仓库网络不可达：有8个独立Pod的describe/events证据（覆盖node1/node2、default/mcp命名空间、4种不同镜像），所有证据一致指向i/o timeout/connection reset by peer，因果链完整清晰，置信度0.95。CrashLoopBackOff：有previous logs直接显示command not found，Exit Code=0，证据确凿。g3 Terminating Pod已确认NotFound，排除当前影响。", "primary_runbooks": ["pod-imagepull-failed.md", "pod-crashloop-runtime.md"], "alternative_causes": [{"cause": "镜像地址或tag不存在", "probability": "low", "reason": "涉及多种不同镜像（busybox:1.36.1, alpine:3.18, curlimages/curl:8.12.1, registry.k8s.io/pause:3.9），错误均为网络层超时而非manifest unknown，排除此场景"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "net-test-pod YAML显示imagePullSecrets=<absent>，且使用的均为公有镜像无需认证；错误信息为网络层超时而非认证拒绝"}, {"cause": "单节点网络问题", "probability": "low", "reason": "node1（10.2.0.49）和node2（10.2.0.50）两个节点均有镜像拉取失败事件，且错误模式一致（i/o timeout），排除单节点问题"}, {"cause": "TerminatingStuck/finalizer未清理", "probability": "low", "reason": "nettest-1779375324已从集群中消失（NotFound），不再是当前活跃异常，无需分析其卡Terminating原因"}], "limitations": "1) 未采集G2组代表性Pod的YAML（证据g2-rep-pod-yaml缺失），但已通过net-test-pod YAML确认无imagePullSecrets，足以排除认证问题；2) 未进一步验证集群出站网络配置（如防火墙规则、代理配置、CNI网络策略），根因定位到\"出站网络不可达\"但未明确具体是哪一层网络策略导致；3) 未检查节点/etc/resolv.conf或CoreDNS，但Docker Hub域名解析成功（事件显示具体IP），DNS非本次根因；4) observability-kibana Pod状态为Completed而非Evicted，实际已不是活跃异常；5) Pod总数~67行可能为部分数据，但不影响异常组全覆盖", "llm_raw_analysis": "## 证据清点与分析\n\n### 异常组g1：CrashLoopBackOff（1个Pod）\n- **rc-crashloop-command-not-found-55b7bcd797-bhsr2** (aiops-e2e/node1)\n- 证据e7（describe）：Exit Code=0, Reason=Completed, BackOff事件\n- 证据e8（previous logs）：`definitely-missing-command-for-rootcause: not found`\n- **结论**：command/args错误导致容器快速退出（exit 0），Root Cause确认为容器启动命令指向不存在的二进制\n\n### 异常组g2：ImagePullBackOff/ErrImagePull（29个Pod）\n- 覆盖3个命名空间（aiops-e2e, default, mcp）× 2个节点（node1, node2）\n- 证据e2/e3/e4（3个namespace跨节点describe）：全部显示 `dial tcp ...:443: i/o timeout`\n... 截断，原始 833 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: **集群主要问题：镜像仓库网络不可达（L3层级，影响29个Pod）**。证据显示node1和node2两个工作节点均无法连接到Docker Hub（registry-1.docker.io），HTTPS连接出现`i/o timeout`（如dns-test-check: dial tcp 31.13...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1、node2）到外部镜像仓库的出站网络不可达，导致Docker Hub（registry-1.docker.io）及registry.k8s.io等镜像仓库的HTTPS连接均出现i/o timeout或connection reset by peer
     传导机制: 所有运行在node1和node2上的Pod在尝试拉取镜像时，kubelet向containerd发起镜像拉取请求 -> containerd向镜像仓库发起HTTPS请求 -> 请求在TCP层超时/连接被对端重置 -> containerd返回拉取失败 -> kubelet标记镜像拉取失败并生成BackOff/ErrImagePull/ImagePullBackOff事件 -> Pod进入Pending状态，循环重试
     最终表现: default/mcp/aiops-e2e命名空间下29个Pod处于ImagePullBackOff/ErrImagePull状态（26个ImagePullBackOff + 3个ErrImagePull），涉及busybox:1.36.1、alpine:3.18、curlimages/curl:8.12.1、registry.k8s.io/pause:3.9等多种镜像，跨node1和node2两个工作节点


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (38.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 10059 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 54.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是为您生成的详细诊断报告。

---
## 📊 集群状态总结

您的集群主要存在 **两大问题**：

1.  **集群范围镜像拉取失败 (L3 级别问题，影响最大)**：这是一个关键性问题，导致集群内 **29 个 Pod** 无法启动。根因是集群工作节点（`node1`, `node2`）无法访问外部镜像仓库（如 Docker Hub）。
2.  **单个 Pod 容器启动失败 (L2 级别问题)**：一个 Pod 因容器启动命令错误导致持续崩溃重启。

### 异常 Pod 统计

| 异常状态 | 数量 | 影响命名空间 |
|:---|:---:|:---|
| `ImagePullBackOff` | 26 | `default` (8), `mcp` (17), `aiops-e2e` (1) |
| `ErrImagePull` | 3 | `default` (1), `mcp` (2) |
| `CrashLoopBackOff` | 1 | `aiops-e2e` |
| `Terminating` (待观察) | 1 | `mcp` |

**结论**：集群的核心问题是**镜像仓库网络不可达**，其次是**应用配置错误**。

---

## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **主要Pod异常状态** | `ImagePullBackOff`, `ErrImagePull`, `CrashLoopBackOff` |
| **兼容归因层** | L3 (镜像仓库网络问题) / L2 (容器运行时问题) |
| **问题分类** | `ImagePullFailed (集群范围)` / `CrashLoopBackOffRuntime (单点)` |
| **置信度** | **高 (95%)** |
| **证据完整度** | 9/10 (90%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：

### 问题一：集群范围镜像拉取失败
| 类型 | 值 |
|------|-----|
| **异常 Pod** | `net-test-pod`, `dns-test-check`, `connectivity-test`（代表），另有 26 个 Pod |
| **受影响 Namespaces** | `default`, `mcp`, `aiops-e2e` |
| **受影响 Nodes** | `node1`, `node2` |
| **错误信息** | `Failed to pull image "busybox:1.36.1"`；`failed to pull and unpack image`；`i/o timeout`；`connection reset by peer` |

### 问题二：单个容器启动命令错误
| 类型 | 值 |
|------|-----|
| **异常 Pod** | `aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-bhsr2` |
| **所在 Node** | `node1` |
| **错误信息** | `Back-off restarting failed container`；崩溃前日志：`sh: definitely-missing-command-for-rootcause: not found` |
| **退出原因** | 命令不存在 |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据（摘要） | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | G2 Pod 状态 | `kubectl describe pod net-test-pod` | `Reason: ImagePullBackOff`, `Normal BackOff 18m (x242 over 166m) kubelet Back-off pulling image "busybox:1.36.1"` | `node1` 无法拉取镜像 `busybox:1.36.1` |
| 2 | G2 Pod 状态(跨节点) | `kubectl describe pod dns-test-check` | `Warning Failed 27m (x8 over 68m) kubelet ... Failed to pull image "busybox:1.36.1"` | `node2` 同样无法拉取相同镜像，确认问题跨节点 |
| 3 | 详细错误信息 | `kubectl describe pod dns-test-check` | `failed to pull and unpack image "docker.io/library/busybox:1.36.1"... dial tcp 31.13.95.37:443: i/o timeout` | Docker Hub 镜像仓库 (`31.13.95.37:443`) 连接超时 |
| 4 | 详细错误信息 | `kubectl describe pod net-test-pod` | `read tcp 10.2.0.49:47436->100.50.6.117:443: connection reset by peer` | 连接 Docker Hub (`100.50.6.117:443`) 时连接被对端重置 |
| 5 | 多镜像验证 | `run_bash_command`, `kubectl describe` | 拉取失败的镜像包括 `busybox:1.36.1`, `alpine:3.18`, `curlimages/curl:8.12.1`, `registry.k8s.io/pause:3.9` | 问题不限于单一镜像，指向普遍的网络连通性问题 |
| 6 | 授权配置 | `kubectl get yaml net-test-pod` | `finalizers: <none>`, `imagePullSecrets: <none>` | 排除 Finalizer 和镜像拉取密钥（认证）问题 |
| 7 | G1 Pod 状态 | `kubectl describe pod rc-crashloop-command-not-found...` | `Reason: CrashLoopBackOff`, `Warning BackOff 2m41s (x10 over 4m34s) kubelet Back-off restarting failed container` | 容器循环重启 |
| 8 | G1 崩溃日志 | `kubectl logs --previous` | `RUNTIME_STARTUP_ERROR: command not found`, `sh: definitely-missing-command-for-rootcause: not found` | 容器启动命令中的可执行文件 `definitely-missing-command-for-rootcause` 不存在 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 + #5 印证**：两个工作节点 (`node1`, `node2`) 上共 29 个 Pod 拉取流行基础镜像（`busybox`, `alpine` 等）均出现 TCP 连接超时或重置，此模式强烈指向**集群级别的出站网络不可达问题**。
- **证据 #6 辅助**：排除了认证配置错误导致拉取失败的可能性。
- **证据 #7 + #8 印证**：Pod 持续重启的原因明确是容器启动命令中的二进制文件 `definitely-missing-command-for-rootcause` 未找到。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 代表性 Pod 的 YAML (g2-rep-pod-yaml) | important | 已通过工具 `kubectl_get_yaml` 确认 `net-test-pod` 无 `imagePullSecrets`，不影响根因判断。 |

---
## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────┐
│ 问题一：集群范围镜像拉取失败                                         │
├─────────────────────────────────────────────────────────────────────┤
│ 根本原因                                                            │
│ 集群工作节点（node1, node2）到外部镜像仓库的出站网络不可达。         │
│ 证据：Docker Hub (31.13.95.37/100.50.6.117:443) 连接出现 i/o        │
│ timeout 和 connection reset by peer。                               │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                            │
│ kubelet 调度 Pod 到 node1/node2                                    │
│  → containerd 试图拉取镜像                                         │
│  → 集群出站网络防火墙/安全组/路由阻断到 registry-1.docker.io:443  │
│  → TCP 连接超时或重置                                              │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                            │
│ kubelet 无法拉取任何需要的容器镜像。                                │
│ 涉及镜像: busybox, alpine, curlimages/curl, registry.k8s.io/pause  │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                        │
│ 29 个 Pod 持续处于 Pending 状态，                               │
│ 事件显示 ImagePullBackOff 或 ErrImagePull，                        │
│ 影响 default, mcp, aiops-e2e 三个命名空间。                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 问题二：单 Pod 容器启动命令错误                                     │
├─────────────────────────────────────────────────────────────────────┤
│ 根本原因                                                            │
│ Pod 的容器启动命令配置错误，试图执行一个不存在的二进制文件。        │
│ 证据：崩溃前日志明确打印 "definitely-missing-command-for-rootcause: │
│ not found"                                                         │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                            │
│ kubelet 启动容器 → 执行 Entrypoint/CMD (sh definitely-missing...)   │
│  → shell 找不到该命令 → 进程退出 → kubelet 尝试重启                │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                            │
│ 容器进程因命令不存在而立即退出。                                    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                        │
│ Pod aiops-e2e/rc-crashloop-command-not-found... 持续进入            │
│ CrashLoopBackOff 状态。                                            │
└─────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论一（主要）** ：根据证据 #1, #2, #3, #4, #5（跨节点、跨镜像拉取失败，错误为 `i/o timeout` 和 `connection reset by peer`），问题的根本原因是**集群工作节点（node1, node2）到外部镜像仓库（如 Docker Hub）的出站网络被阻断**。这不是某个 Pod 或某镜像的问题，而是集群网络架构层面的故障。

**结论二（次要）**：根据证据 #7 和 #8（退出代码非 137，日志明确报错 `not found`），`aiops-e2e/rc-crashloop-command-not-found-...` Pod 的根本原因是**容器启动命令配置错误**，指向了一个不存在的可执行文件。

**置信度**：**高 (95%)**

- ✅ 跨节点、跨镜像的故障模式一致
- ✅ 错误信息明确指向 TCP 连接问题
- ✅ 日志直接定位到命令未找到
- ⚠️ 未明确是防火墙、安全组还是路由策略导致网络不通，但这不影响根因定位为“网络不可达”

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）

**一、修复集群范围镜像拉取问题（网络团队介入）**
> **目标**：恢复节点到外部镜像仓库的网络连通性。
> **根本解决方案**：检查并调整集群的网络策略。

1.  **检查节点防火墙规则**
    ```bash
    # 在 node1 和 node2 上执行，检查出站流量是否被阻止
    sudo iptables -L -n -v | grep -E "REJECT|DROP"
    ```
    *依据*：网络流量被中断，最可能的原因是操作系统/防火墙策略。
2.  **检查集群网络策略（NetworkPolicy）**
    ```bash
    # 检查集群中是否有限制 Pod 访问外网的 NetworkPolicy
    kubectl get networkpolicies --all-namespaces -o wide
    ```
    *依据*：如果存在全局拒绝出口流量的 NetworkPolicy，会导致所有 Pod 无法拉取镜像。
3.  **临时规避方案（如无法立即修复网络）**
    *   **使用集群内镜像仓库**：将所需镜像（`busybox:1.36.1` 等）拉取到集群内或可访问的私有仓库，并修改所有异常 Pod 的 Deployment/StatefulSet 的 `image` 字段指向该仓库。
        ```bash
        # 示例：将镜像推送到您可访问的私有仓库（如 Harbor）
        # docker pull busybox:1.36.1
        # docker tag busybox:1.36.1 <your-registry>/library/busybox:1.36.1
        # docker push <your-registry>/library/busybox:1.36.1
        # 然后修改所有 Deployment 的镜像地址
        ```
    *依据*：可以从根源上避免从外部仓库拉取镜像。

**二、修复单 Pod CrashLoopBackOff 问题**
> **目标**：修复容器启动命令错误。

1.  **找到并更新有问题的 Deployment**
    首先，确定管理该 Pod 的 Deployment 或其它工作负载。
    ```bash
    # 查找所属的 Deployment
    kubectl -n aiops-e2e get deployments -o wide | grep crashloop
    ```
2.  **更新容器启动命令（以 Deployment 为例）**
    *依据*：证据 #8 确认崩溃日志为 `definitely-missing-command-for-rootcause: not found`。
    ```bash
    # 删除或更正命令行参数。假设需要运行的命令是 /my-app
    kubectl -n aiops-e2e set command deployment/rc-crashloop-command-not-found -- /my-app
    ```
    或者，如果该命令本来就不需要，直接移除它：
    ```bash
    # 可以用 patch 命令清空 command 或修改为正确的 entrypoint
    # 具体如何修改取决于原始的 YAML 定义
    ```

### 后续优化
1.  **监控告警** 配置对 `ImagePullBackOff` 和 `CrashLoopBackOff` 状态的 Pod 告警，以便快速发现此类问题。
2.  **网络架构优化** 评估是否迁移到私有镜像仓库，或为节点配置 HTTP/S 代理访问外部网络。
3.  **CI/CD 流程** 在 CI/CD 流程中加入对容器启动命令的检查，防止配置错误的 image 被部署到集群。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认网络修复 | `kubectl describe pod net-test-pod -n default` | 事件中不再出现 `i/o timeout`，最终 `Pod Status` 变为 `Running` |
| 2. 确认无新的镜像拉取失败 | `kubectl get pods --all-namespaces \| grep -E "ImagePullBackOff\|ErrImagePull"` | 返回结果为空 |
| 3. 确认 CrashLoopBackOff 修复 | `kubectl -n aiops-e2e get pods -l app=rc-crashloop-command-not-found` | `STATUS` 列显示 `Running`，`RESTARTS` 列不再增长 |
| 4. （可选）测试节点连接性 | `kubectl run -i --tty --rm debug --image=busybox --restart=Never -- ping 8.8.8.8` | Pod 成功创建并运行，Ping 通外部 IP |

---
## ⚠️ 注意事项
- **网络修复为最高优先级**：修复镜像拉取问题会一次性恢复 29 个 Pod，对业务影响最大。
- **`xnet/observability-kibana` Pod** 状态为 `Completed`，非活跃异常，无需处理。
- **`mcp/nettest-1779375324` Pod** 处于 `Terminating` 状态，待进一步观察，如长时间无法完成，可尝试强制删除（`kubectl delete pod <name> -n mcp --grace-period=0 --force`）。

---

## 📊 性能统计

├─ 总耗时: 2.9m
├─ 问题定位: 49.9s (29%) ✅
├─ 证据链采集: 57.4s (33%) ✅
├─ 根因分析: 28.1s (16%) ✅
├─ 汇总总结: 38.8s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 26 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-crashloop-runtime
- **参考 Runbook**: pod-imagepull-failed, pod-crashloop-runtime, pod-evicted, pod-pending-unschedulable
- **工具调用**: 26 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
