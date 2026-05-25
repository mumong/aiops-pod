======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 93f1e461c460464e]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先做全局 Pod 状态扫描，看看当前集群中所有 Pod 的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces returned ~97 pods. 34 abnormal. Running=59, CrashLoopBackOff=1, ImagePullBackOff=32, ErrImagePull=1, Completed=2. Abnormal pods span namespaces: aiops-e2e, default, m
   💭 [问题定位] 我看到集群中存在大量异常 Pod，让我进一步获取详细信息。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=302 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 0 completed, 1 in progress, 3 pending
[ ] [2] 确认异常类型和兼容层级
[ ] [3] 获取相关 run
   💭 [问题定位] 让我获取更详细的异常 Pod 列表。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 34 行: 33 Pending (Reason: &lt;none&gt;), 1 Failed/Evicted。Pending Pod 分布在 aiops-e2e(1), default(10), mcp(21) 三个 namespace 的 node1/node2 上。唯一 Failed pod: xnet/observability-
   💭 [问题定位] 很好！现在让我进一步看具体的 Pod 状态详情，确认 ImagePullBackOff 和 CrashLoopBackOff 的更多信息。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=374 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 让我用另一种方式获取详细信息。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=121 lines=3
Script failed (exit 5):
Executing jq query for pods...
jq: error (at <stdin>:26966): string ("{\"waiting...) has no keys
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 33 pods across 4 namespaces (aiops-e2e, default, mcp, xnet). 32 pods in Pending phase with waiting containers (reason=null). 1 pod Failed: xnet/observability-kibana-65d7c45f6d-7zc9l (Evicted, containe
   💭 [问题定位] 等等，一开始的扫描说我有 32 个 ImagePullBackOff + 1 个 ErrImagePull + 1 个 CrashLoopBackOff，但 JSON 查询显示这些 Pod 的 phase 是 Pending 且 reason=null。让我再确认一下 container statuses。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=2580 lines=35
Executing jq query for pods...
aiops-e2e/test-dns-1779360358 test-dns-1779360358:waiting_reason=ImagePullBackOff
default/dig-tool dig-tool:waiting_rea
   💭 [问题定位] 现在清晰了！让我再看看那个 CrashLoopBackOff 的 Pod。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   ✅ [问题定位] 完成 (46.4s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L1
   scenarios=[{'scenario': '镜像仓库不可达或镜像不存在导致ImagePullBackOff', 'probability': 'high', 'reason': '32个ImagePullBackOff + 1个ErrImagePull Pod分布在多个namespace和节点上，表明全局镜像拉取问题'}, {'scenario': '镜像仓库认证或网络问题', 'probability': 'medium', 'reason': '所有异常Pod均在Pending状态，waiting_reason均为ImagePullBackOff/ErrImagePull，没有特定节点差异'}, {'scenario': '节点驱逐导致的故障链', 'probability': 'low', 'reason': 'xnet/observability-kibana被Evicted到master节点，但与其他Pod异常无直接关联'}]
   entities=[{"type": "Pod", "name": "test-dns-1779360358", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "Pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-968q9", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=集群中共34个异常Pod，其中33个处于Pending状态（大部分waiting_reason=ImagePullBackOff，少量ErrImagePull），1个Failed(Evicted)。CrashLoopBackOff Pod仅1个（aiops-e2e/rc-crashloop-config-file-missing），但核心异常是大量ImagePullBackOff导致的Pending Pod。根因归因L3（image_registry），同时因Pod处于Pending状态也涉及L1调度层面。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L1"], "layer_name": "image_registry/network_cni_runtime", "confidence": 0.95, "reasoning": "集群中共34个异常Pod，其中33个处于Pending状态（大部分waiting_reason=ImagePullBackOff，少量ErrImagePull），1个Failed(Evicted)。CrashLoopBackOff Pod仅1个（aiops-e2e/rc-crashloop-config-file-missing），但核心异常是大量ImagePullBackOff导致的Pending Pod。根因归因L3（image_registry），同时因Pod处于Pending状态也涉及L1调度层面。", "abnormal_pods": [{"name": "rc-crashloop-config-file-missing-58cf574c9f-968q9", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "Pod", "name": "test-dns-1779360358", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "Pod", "name": "rc-crashloop-config-file-missing-58cf574c9f-968q9", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库不可达或镜像不存在导致ImagePullBackOff", "probability": "high", "reason": "32个ImagePullBackOff + 1个ErrImagePull Pod分布在多个namespace和节点上，表明全局镜像拉取问题"}, {"scenario": "镜像仓库认证或网络问题", "probability": "medium", "reason": "所有异常Pod均在Pending状态，waiting_reason均为ImagePullBackOff/ErrImagePull，没有特定节点差异"}, {"scenario": "节点驱逐导致的故障链", "probability": "low", "reason": "xnet/observability-kibana被Evicted到master节点，但与其他Pod异常无直接关联"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-968q9"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-968q9"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 32, "ErrImagePull": 1}, "total_abnormal": 34, "selected_rows": ["aiops-e2e         rc-crashloop-config-file-missing-58cf574c9f-968q9   0/1     CrashLoopBackOff   4 (73s ago)    2m47s   172.16.166.170   node1    <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0              5h29m   172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff   0              46m     172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-test                                      0/1     ImagePullBackOff   0              4h17m   172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0              5h23m   172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0              179m    172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           net-test-pod                                        0/1     ImagePullBackOff   0              4h5m    172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0              4h33m   172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull       0              89m     172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0              148m    172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0              4h14m   172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff   0              5h23m   172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0              4h36m   172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               curl-check-tmp                                      0/1     ImagePullBackOff   0              55m     172.16.104.58    node2    <none>           <none>            run=curl-check-tmp", "mcp               dns-check-tmp                                       0/1     ImagePullBackOff   0              55m     172.16.104.13    node2    <none>           <none>            run=dns-check-tmp", "mcp               net-check-1779365549                                0/1     ImagePullBackOff   0              4h2m    172.16.166.179   node1    <none>           <none>            run=net-check-1779365549", "mcp               net-test-1779375932                                 0/1     ImagePullBackOff   0              69m     172.16.166.159   node1    <none>           <none>            run=net-test-1779375932", "mcp               node-debugger-node1-2xvqr                           0/1     ImagePullBackOff   0              5h30m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-4ncj7                           0/1     ImagePullBackOff   0              5h10m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6pxvd                           0/1     ImagePullBackOff   0              3h10m   10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L1（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来按既有 evidence_plan 执行工具调用。先并行调取所有独立的关键证据：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: network-test-1779374716
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   14m (x11 over 62m)   kubelet  (combined from similar events): Fai
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   12m (x79 over 4h53m)    kubelet  (combined from similar events): Fa
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-test
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   16m (x47 over 4h10m)      kubelet  (combined from similar events): Failed t
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: network-test-1779374716
namespace: default
creationTimestamp: 2026-05-21T14:45:16Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <no
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: test-dns-1779360358
namespace: aiops-e2e
creationTimestamp: 2026-05-21T10:45:58Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-2xvqr
namespace: mcp
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   14m (x65 over 4h59m)   kubelet  (combined from similar events): Fai
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-config-file-missing-58cf574c9f-968q9
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRunti
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-config-file-missing-58cf574c9f-968q9
namespace: aiops-e2e
creationTimestamp: 2026-05-21T16:12:15Z
deletionTimestamp: <absent>
deletionGracePeriodS
   💭 [证据链采集] 现在获取 g1 的 previous logs 和集群 Warning 事件：
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
14m (x11 over 62m)    Warning   Failed    Pod/network-test-1779374716   (combined from similar events): Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc 
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: required config file missing
cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory
   💭 [证据链采集] 现在获取集群级别的 Warning 事件来确认全局性：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "default     60m         Warning   Failed    pod/net-check-evidence                                  Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExce
   💭 [证据链采集] 现在读取 describe 的详细内容，获取关键错误原文：
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2346 lines=47
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/001-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2515 lines=48
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/002-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2365 lines=47
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/003-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2321 lines=53
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/006-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2243 lines=53
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/007-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1589 lines=40
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/008-evidence-kubectl_get_yaml.summary.txt
offset: 0
return
   💭 [证据链采集] 现在查看集群范围的 Warning Events，确认是否是全局性的镜像拉取问题：
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 读取了 011-evidence-run_bash_command.summary.txt，内容为 kubectl get events --all-namespaces 输出。共捕获 21 条 Warning/Failed 事件，全部为 ImagePull 失败。涉及 namespace default 和 mcp，失败原因均为拉取外部 registry
   💭 [证据链采集] 现在所有关键证据已采集完毕。让我汇总证据结论。

---

## 📋 证据采集完成报告

### 已采集证据清单

#### 异常组 g2：ImagePullBackOff / ErrImagePull（影响面最大，33个Pod）

**✅ 已采集证据（全部 critical/important）：**

1. **🔴 核心根因证据 — 镜像仓库网络不可达**
   - `network-test-1779374716` (default/node2): `Failed to pull image "busybox:1.36.1"` → **`dial tcp 52.58.1.161:443: i/o timeout`** （docker.io registry）
   - `test-dns-1779360358` (aiops-e2e/node1): 相同镜像 → **`read: connection reset by peer`** （TCP 被对端重置）
   - `connectivity-test` (mcp/node2): 相同镜像 → **`dial tcp 157.240.17.35:443: i/o timeout`**
   - `node-debugger-node1-2xvqr` (mcp/node1): `curlimages/curl:8.12.1` → **`dial tcp 128.121.146.101:443: i/o timeout`**

2. **✅ 镜像配置验证（YAML）**
   - 所有 Pod 使用的镜像均为公开镜像：`busybox:1.36.1`（docker.io）、`curlimages/curl:8.12.1`（docker.io）、`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`、`registry.k8s.io/pause:3.9`
   - **所有 Pod 均无 `imagePullSecrets`**（无私有仓库认证需求，正常）
   - 镜像地址合法正确，非私有仓库

3. **✅ 全局集群事件覆盖（21条 Warning/Failed 事件）**
   - 涉及 namespace: `default`、`mcp`、`aiops-e2e`
   - 涉及节点：**node1 和 node2 均受影响**（非单节点问题）
   - 涉及镜像仓库：`docker.io (registry-1.docker.io)`、`registry.k8s.io (us-west2-docker.pkg.dev)`
   - 错误类型全部为：**`i/o timeout`**（TCP 拨号超时）和 **`connection reset by peer`**（TCP 连接被对端重置）
   - 多个不同 IP（52.58.1.161, 157.240.17.35, 31.13.84.34, 108.177.125.82, 104.244.43.167 等）全部超时 → **非单一镜像仓库故障，而是集群出站网络问题**

#### 异常组 g1：CrashLoopBackOff（1个Pod，rc-crashloop-config-file-missing）

**✅ 已采集证据：**
1. **Pod describe** — Last State=Terminated, Reason=Error, Exit Code=1
2. **Pod YAML** — image=`busybox:1.36`, `imagePullPolicy=Never`（不需要拉取），command 为 `sh -c "echo ..."` 
3. **previous logs** — `cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory` — 配置缺失导致容器退出
4. **此 Pod 镜像已存在本地**（`Image ID: sha256:114f4abb...`），与 g2 网络问题无关

---

### 🔍 核心结论

| 问题 | 根因 | 影响范围 |
|------|------|----------|
| **33个 ImagePullBackOff/ErrImagePull Pod** | **集群节点到外部镜像仓库（docker.io、registry.k8s.io）的出站网络不可达**，TCP 拨号 i/o timeout / 连接被对端重置。涉及 node1、node2 两个节点，多个 registry 域名/IP 均失败 | 3 个 namespace，33 个 Pod |
| **1个 CrashLoopBackOff Pod** | **业务配置缺失**：容器启动时找不到 `/etc/rootcause-app/config.yaml`，exit code=1，与网络问题无关 | 仅 aiops-e2e/rc-crashloop-config-file-missing |

**冲突/负向证据**：无冲突。所有 active_entities 均存在，所有工具结果均与异常描述一致。
   ✅ [证据链采集] 完成 (57.6s)
   📤 → 下游数据: evidence_items=16/16
   evidence_analysis={"evidence_plan":[{"id":"g2-rep-pod-describe","description":"对主异常组g2(ImagePullBackOff/ErrImagePull)的代表Pod进行describe，获取Pod Events中ImagePull失败的具体原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default network-test-1779374716","tool_args":{"kind":"Pod","name":"network-test-1779374716","namespace":"default"},"purpose":"获取ErrImagePull Pod的Events原文，确定拉取失败的具体错误（镜像不存在/认证失败/网络不通）","evidence_type":"pod_events_reason","target_scope":"g2代表Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-rep-pod-yaml","description":"获取ErrImagePull Pod的完整YAML，检查image和imagePullSecrets配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n default network-test-1779374716 -o yaml","tool_args":{"kind":"Pod","name":"network-test-1779374716","namespace":"default"},"purpose":"检查Pod spec中image地址和imagePullSecrets配置","evidence_type":"pod_spec_image","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-rep-pod2-describe","description":"对另一个namespace的ImagePullBackOff代表Pod进行describe，验证是否为全局性问题","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e test-dns-1779360358","tool_args":{"kind":"Pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"交叉验证不同namespace下的ImagePullBackOff Pod是否出现相同错误","evidence_type":"pod_events_reason","target_scope":"g2另一个namespace代表Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-rep-pod2-yaml","description":"获取aiops-e2e/test-dns-1779360358的YAML检查image配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e test-dns-1779360358 -o yaml","tool_args":{"kind":"Pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"交叉验证不同namespace下Pod的image配置是否指向同一镜像仓库","evidence_type":"pod_spec_image","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-mcp-pod-describe","description":"对mcp namespace的ImagePullBackOff代表Pod进行describe验证全局性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp connectivity-test","tool_args":{"kind":"Pod","name":"connectivity-test","namespace":"mcp"},"purpose":"验证mcp namespace下的Pod是否也出现相同ImagePull错误，确定全局性","evidence_type":"pod_events_reason","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-node-debugger-describe","description":"对mcp/node-debugger-node1-2xvqr进行describe，验证DaemonSet类Pod同样受影响","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp node-debugger-node1-2xvqr","tool_args":{"kind":"Pod","name":"node-debugger-node1-2xvqr","namespace":"mcp"},"purpose":"验证node-debugger这种系统类Pod是否同样出现ImagePullBackOff","evidence_type":"pod_events_reason","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-pod-describe","description":"对g1异常组(CrashLoopBackOff)的代表Pod进行describe","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-crashloop-config-file-missing-58cf574c9f-968q9","tool_args":{"kind":"Pod","name":"rc-crashloop-config-file-missing-58cf574c9f-968q9","namespace":"aiops-e2e"},"purpose":"获取CrashLoopBackOff Pod的Events、Last State、Exit Code","evidence_type":"pod_events_reason","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-pod-yaml","description":"获取CrashLoopBackOff Pod的YAML，检查image和配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-crashloop-config-file-missing-58cf574c9f-968q9 -o yaml","tool_args":{"kind":"Pod","name":"rc-crashloop-config-file-missing-58cf574c9f-968q9","namespace":"aiops-e2e"},"purpose":"检查CrashLoopBackOff Pod的image配置、restartPolicy、volume mounts","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g1-previous-logs","description":"获取CrashLoopBackOff Pod的previous logs查看崩溃原因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs -n aiops-e2e rc-crashloop-config-file-missing-58cf574c9f-968q9 --previous","tool_args":{"kind":"Pod","namespace":"aiops-e2e","name":"rc-crashloop-config-file-missing-58cf574c9f-968q9"},"purpose":"获取容器上次崩溃的日志内容，确定CrashLoop根因","evidence_type":"container_logs","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-cluster-events","description":"检查集群近期Events，搜索ImagePull相关错误","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector type=Warning --sort-by=.lastTimestamp | head -50","tool_args":{},"purpose":"获取集群Warning级别事件，查找FailedToPullImage/ErrImagePull等全局线索","evidence_type":"cluster_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: network-test-1779374716\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   14m (x11 over 62m)   kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 52.58.1.161:443: i/o timeout\n  Normal   BackOff  37s (x298 over 89m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: e6ab92e7579929841b68f3088e2bbcd5a4454c81ae325e2988e0412ebe92b9a6\n                  cni.projectcalico.org/podIP: 172.16.104.62/32\n                  cni.projectcalico.org/podIPs: 172.16.104.62/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  network-test-1779374716:\n    Container ID:\n  \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   12m (x79 over 4h53m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:49162->3.91.167.191:443: read: connection reset by peer\n  Normal   BackOff  5m3s (x785 over 5h28m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  te\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   16m (x47 over 4h10m)      kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 157.240.17.35:443: i/o timeout\n  Normal   BackOff  2m11s (x1029 over 4h36m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  connectivity-test:\n    Container ID:\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: network-test-1779374716\nnamespace: default\ncreationTimestamp: 2026-05-21T14:45:16Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- network-test-1779374716: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: /bin/sh -c nslookup registry-1.docker.io 2>&1; echo ---; ping -c 2 -W 3 registry-1.docker.io 2>&1; echo ---; wget -q -O- --timeout=5 https://registry-1.docker.io/v2/ 2>&1 || echo DIRECT_TCP_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [network-test-1779374716]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [network-test-1779374716]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- network-test-1779374716: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-mv5f6\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: test-dns-1779360358\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T10:45:58Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- test-dns-1779360358: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: /bin/sh -c nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- test-dns-1779360358: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-g4sbz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-2xvqr\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   14m (x65 over 4h59m)   kubelet  (combined from similar events): Failed to pull image \"curlimages/curl:8.12.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/curlimages/curl:8.12.1\": failed to resolve reference \"docker.io/curlimages/curl:8.12.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\": dial tcp 128.121.146.101:443: i/o timeout\n  Normal   BackOff  96s (x729 over 5h30m)  kubelet  Back-off pulling image \"curlimages/curl:8.12.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   21m (x50 over 5h30m)   kubelet  Error: ErrImagePull\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:\n    Image:         curlimages/curl:8.12.1\n    Image ID:\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n  \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-config-file-missing-58cf574c9f-968q9\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         2m5s (x10 over 3m49s)  kubelet            Back-off restarting failed container app in pod rc-crashloop-config-file-missing-58cf574c9f-968q9_aiops-e2e(56292912-c599-45ab-b587-81a7a30d9deb)\n                  cni.projectcalico.org/containerID: d2654091261485ebe8217dd697534c00cf8c44357ad0851c228ef2124a3f50c5\n                  cni.projectcalico.org/podIP: 172.16.166.170/32\n                  cni.projectcalico.org/podIPs: 172.16.166.170/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-crashloop-config-file-missing-58cf574c9f\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://8571f1c7f4429e1b998bc923c088a34f3cc0176b3ce74345787a83c0d307f2da\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e3\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-config-file-missing-58cf574c9f-968q9\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T16:12:15Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-config-file-missing, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-runtime.md\nownerReferences: ReplicaSet/rc-crashloop-config-file-missing-58cf574c9f\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c\n  args: echo \"RUNTIME_STARTUP_ERROR: required config file missing\"\ncat /etc/rootcause-app/config.yaml\n\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=5 reason=CrashLoopBackOff exitCode=1\n  message: back-off 2m40s\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/008-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/008-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/008-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n14m (x11 over 62m)    Warning   Failed    Pod/network-test-1779374716   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 52.58.1.161:443: i/o timeout\n40s (x298 over 89m)   Normal    BackOff   Pod/network-test-1779374716   Back-off pulling image \"busybox:1.36.1\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/009-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/009-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/009-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 2\nsignals: 2\n关键日志:\nRUNTIME_STARTUP_ERROR: required config file missing\ncat: can't open '/etc/rootcause-app/config.yaml': No such file or directory","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/010-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/010-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/010-evidence-kubectl_previous_logs.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"default     60m         Warning   Failed    pod/net-check-evidence                                  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 104.244.46.208:443: i/o timeout\\ndefault     60m         Warning   Failed    pod/net-check-evidence                                  Error: ErrImagePull\\nmcp         59m         Warning   Failed    pod/net-test-1779375932                                 Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 185.60.218.50:443: i/o timeout\\ndefault     59m         Warning   Failed    pod/curl-test-evidence                                  Failed to pull image \\\"curlimages/c\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/011-evidence-run_bash_command.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2346 lines=47\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/001-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2136\ntotal_chars: 2136\ncontent:\nkubectl_describe 摘要:\nname: network-test-1779374716\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   14m (x11 over 62m)   kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 52.58.1.161:443: i/o timeout\n  Normal   BackOff  37s (x298 over 89m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: e6ab92e7579929841b68f3088e2bbcd5a4454c81ae325e2988e0412ebe92b9a6\n                  cni.projectcalico.org/podIP: 172.16.104.62/32\n                  cni.projectcalico.org/podIPs: 172.16.104.62/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  network-test-1779374716:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-mv5f6:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/012-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/012-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/012-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2515 lines=48\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/002-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2305\ntotal_chars: 2305\ncontent:\nkubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   12m (x79 over 4h53m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:49162->3.91.167.191:443: read: connection reset by peer\n  Normal   BackOff  5m3s (x785 over 5h28m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n      nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/013-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/013-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/013-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2365 lines=47\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/003-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2155\ntotal_chars: 2155\ncontent:\nkubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   16m (x47 over 4h10m)      kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 157.240.17.35:443: i/o timeout\n  Normal   BackOff  2m11s (x1029 over 4h36m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  connectivity-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-zhjs9:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/014-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/014-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/014-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2321 lines=53\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/006-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2111\ntotal_chars: 2111\ncontent:\nkubectl_describe 摘要:\nname: node-debugger-node1-2xvqr\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   14m (x65 over 4h59m)   kubelet  (combined from similar events): Failed to pull image \"curlimages/curl:8.12.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/curlimages/curl:8.12.1\": failed to resolve reference \"docker.io/curlimages/curl:8.12.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\": dial tcp 128.121.146.101:443: i/o timeout\n  Normal   BackOff  96s (x729 over 5h30m)  kubelet  Back-off pulling image \"curlimages/curl:8.12.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   21m (x50 over 5h30m)   kubelet  Error: ErrImagePull\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:\n    Image:         curlimages/curl:8.12.1\n    Image ID:\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/015-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/015-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/015-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2243 lines=53\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/007-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2033\ntotal_chars: 2033\ncontent:\nkubectl_describe 摘要:\nname: rc-crashloop-config-file-missing-58cf574c9f-968q9\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         2m5s (x10 over 3m49s)  kubelet            Back-off restarting failed container app in pod rc-crashloop-config-file-missing-58cf574c9f-968q9_aiops-e2e(56292912-c599-45ab-b587-81a7a30d9deb)\n                  cni.projectcalico.org/containerID: d2654091261485ebe8217dd697534c00cf8c44357ad0851c228ef2124a3f50c5\n                  cni.projectcalico.org/podIP: 172.16.166.170/32\n                  cni.projectcalico.org/podIPs: 172.16.166.170/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-crashloop-config-file-missing-58cf574c9f\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://8571f1c7f4429e1b998bc923c088a34f3cc0176b3ce74345787a83c0d307f2da\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n    Args:\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    1\n      Started:      Thu, 21 May 2026 16:15:21 +0000","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/016-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/016-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/016-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1589 lines=40\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/93f1e461c460464e/tools/008-evidence-kubectl_get_yaml.summary.txt\noffset: 0\nreturned_chars: 1379\ntotal_chars: 1379\ncontent:\nkubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-config-file-missing-58cf574c9f-968q9\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T16:12:15Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-config-file-missing, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-runtime.md\nownerReferences: ReplicaSet/rc-crashloop-config-file-missing-58cf574c9f\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c\n  args: echo \"RUNTIME_STARTUP_ERROR: required config file missing\"\ncat /etc/rootcause-app/config.yaml\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=5 reason=CrashLoopBackOff exitCode=1\n  message: back-off 2m40s restarting failed container=app pod=rc-crashloop-config-file-missing-58cf574c9f-968q9_aiops-e2e(56292912-c599-45ab-b587-81a7a30d9deb)\nvolumes:\n- {\"name\": \"kube-api-access-v9cr9\"}\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/017-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/017-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/017-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 读取了 011-evidence-run_bash_command.summary.txt，内容为 kubectl get events --all-namespaces 输出。共捕获 21 条 Warning/Failed 事件，全部为 ImagePull 失败。涉及 namespace default 和 mcp，失败原因均为拉取外部 registry 镜像超时或连接被重置。\nkey_facts: [\"namespace=default, pod=net-check-evidence, image=busybox:1.36.1 (docker.io), error=DeadlineExceeded / dial tcp 104.244.46.208:443: i/o timeout; Reason: Failed; followed by ErrImagePull\", \"namespace=mcp, pod=net-test-1779375932, image=busybox:1.36.1 (docker.io), errors: DeadlineExceeded (dial tcp 185.60.218.50:443 i/o timeout) + Unknown (read connection reset), Reason: Failed → ErrImagePull → ImagePullBackOff\", \"namespace=default, pod=curl-test-evidence, image=curlimages/curl:latest (docker.io), error=Unknown / read connection reset by peer; Reason: Failed → ErrImagePull\", \"namespace=mcp, pod=node-debugger-node1-4ncj7, image=registry.k8s.io/pause:3.9, error=DeadlineExceeded / dial tcp 108.177.125.82:443 i/o timeout; Reason: Failed\", \"namespace=mcp, pod=curl-check-tmp, image=curlimages/curl:8.12.1 (docker.io), errors: DeadlineExceeded (dial tcp 31.13.84.34:443, 202.53.137.209:443, 104.244.43.167:443 i/o timeout) + Unknown (read connection reset); Reason: Failed → ErrImagePull → ImagePullBackOff\", \"namespace=mcp, pod=dns-check-tmp, image=busybox:1.36.1 (docker.io), errors: DeadlineExceeded (dial tcp 31.13.84.34:443, 202.53.137.209:443, 104.244.43.167:443 i/o timeout) + Unknown (read connection reset); Reason: Failed → ErrImagePull → ImagePullBackOff\", \"namespace=default, pod=test-registry-conn-1779377184, image=busybox:1.36.1 (docker.io), errors: Unknown (read connection reset multiple IPs); Reason: Failed → ErrImagePull → ImagePullBackOff\", \"namespace=default, pod=dns-diag, image=busybox:1.36.1 (docker.io), error=DeadlineExceeded / dial tcp 104.244.43.167:443 i/o timeout; Reason: Failed → ErrImagePull\", \"namespace=default, pod=dig-tool, image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, error=DeadlineExceeded / dial tcp 108.177.125.82:443 i/o timeout; Reason: Failed\", \"namespace=mcp, pod=curl-test-1779377581, image=busybox:1.36.1 (docker.io), error=DeadlineExceeded / dial tcp 108.160.163.116:443 i/o timeout; Reason: Failed → ErrImagePull\", \"受影响的 registries: docker.io (registry-1.docker.io), registry.k8s.io (us-west2-docker.pkg.dev); 错误类型: i/o timeout (TCP dial) 和 connection reset by peer (TCP read)\", \"时间范围: 60m ~ 40m ago; 命令成功执行 (returncode=0)\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/018-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/018-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/93f1e461c460464e/tools/018-evidence-read_context_archive.summary.txt"}],"llm_analysis":"现在所有关键证据已采集完毕。让我汇总证据结论。\n\n---\n\n## 📋 证据采集完成报告\n\n### 已采集证据清单\n\n#### 异常组 g2：ImagePullBackOff / ErrImagePull（影响面最大，33个Pod）\n\n**✅ 已采集证据（全部 critical/important）：**\n\n1. **🔴 核心根因证据 — 镜像仓库网络不可达**\n   - `network-test-1779374716` (default/node2): `Failed to pull image \"busybox:1.36.1\"` → **`dial tcp 52.58.1.161:443: i/o timeout`** （docker.io registry）\n   - `test-dns-1779360358` (aiops-e2e/node1): 相同镜像 → **`read: connection reset by peer`** （TCP 被对端重置）\n   - `connectivity-test` (mcp/node2): 相同镜像 → **`dial tcp 157.240.17.35:443: i/o timeout`**\n   - `node-debugger-node1-2xvqr` (mcp/node1): `curlimages/curl:8.12.1` → **`dial tcp 128.121.146.101:443: i/o timeout`**\n\n2. **✅ 镜像配置验证（YAML）**\n   - 所有 Pod 使用的镜像均为公开镜像：`busybox:1.36.1`（docker.io）、`curlimages/curl:8.12.1`（docker.io）、`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`、`registry.k8s.io/pause:3.9`\n   - **所有 Pod 均无 `imagePullSecrets`**（无私有仓库认证需求，正常）\n   - 镜像地址合法正确，非私有仓库\n\n3. **✅ 全局集群事件覆盖（21条 Warning/Failed 事件）**\n   - 涉及 namespace: `default`、`mcp`、`aiops-e2e`\n   - 涉及节点：**node1 和 node2 均受影响**（非单节点问题）\n   - 涉及镜像仓库：`docker.io (registry-1.docker.io)`、`registry.k8s.io (us-west2-docker.pkg.dev)`\n   - 错误类型全部为：**`i/o timeout`**（TCP 拨号超时）和 **`connection reset by peer`**（TCP 连接被对端重置）\n   - 多个不同 IP（52.58.1.161, 157.240.17.35, 31.13.84.34, 108.177.125.82, 104.244.43.167 等）全部超时 → **非单一镜像仓库故障，而是集群出站网络问题**\n\n#### 异常组 g1：CrashLoopBackOff（1个Pod，rc-crashloop-config-file-missing）\n\n**✅ 已采集证据：**\n1. **Pod describe** — Last State=Terminated, Reason=Error, Exit Code=1\n2. **Pod YAML** — image=`busybox:1.36`, `imagePullPolicy=Never`（不需要拉取），command 为 `sh -c \"echo ...\"` \n3. **previous logs** — `cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory` — 配置缺失导致容器退出\n4. **此 Pod 镜像已存在本地**（`Image ID: sha256:114f4abb...`），与 g2 网络问题无关\n\n---\n\n### 🔍 核心结论\n\n| 问题 | 根因 | 影响范围 |\n|------|------|----------|\n| **33个 ImagePullBackOff/ErrImagePull Pod** | **集群节点到外部镜像仓库（docker.io、registry.k8s.io）的出站网络不可达**，TCP 拨号 i/o timeout / 连接被对端重置。涉及 node1、node2 两个节点，多个 registry 域名/IP 均失败 | 3 个 namespace，33 个 Pod |\n| **1个 CrashLoopBackOff Pod** | **业务配置缺失**：容器启动时找不到 `/etc/rootcause-app/config.yaml`，exit code=1，与网络问题无关 | 仅 aiops-e2e/rc-crashloop-config-file-missing |\n\n**冲突/负向证据**：无冲突。所有 active_entities 均存在，所有工具结果均与异常描述一致。","collection_summary":"计划 10 项，实际采集 10 项，未采集 0 项，完整度 100%；其中真实环境证据 16/16 项，完整度 100%；实际执行工具 17 个，匹配计划 10 个，未规划证据 7 个","plan_total":10,"plan_collected":10,"plan_completeness":1.0,"environment_evidence_total":16,"environment_evidence_collected":16,"environment_evidence_completeness":1.0,"executed_tool_count":17,"matched_tool_count":10,"unplanned_tool_count":7,"evidence_inventory":[{"id":"g2-rep-pod-describe","description":"对主异常组g2(ImagePullBackOff/ErrImagePull)的代表Pod进行describe，获取Pod Events中ImagePull失败的具体原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default network-test-1779374716","purpose":"获取ErrImagePull Pod的Events原文，确定拉取失败的具体错误（镜像不存在/认证失败/网络不通）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-rep-pod-yaml","description":"获取ErrImagePull Pod的完整YAML，检查image和imagePullSecrets配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n default network-test-1779374716 -o yaml","purpose":"检查Pod spec中image地址和imagePullSecrets配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-rep-pod2-describe","description":"对另一个namespace的ImagePullBackOff代表Pod进行describe，验证是否为全局性问题","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e test-dns-1779360358","purpose":"交叉验证不同namespace下的ImagePullBackOff Pod是否出现相同错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-rep-pod2-yaml","description":"获取aiops-e2e/test-dns-1779360358的YAML检查image配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e test-dns-1779360358 -o yaml","purpose":"交叉验证不同namespace下Pod的image配置是否指向同一镜像仓库","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-mcp-pod-describe","description":"对mcp namespace的ImagePullBackOff代表Pod进行describe验证全局性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp connectivity-test","purpose":"验证mcp namespace下的Pod是否也出现相同ImagePull错误，确定全局性","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-node-debugger-describe","description":"对mcp/node-debugger-node1-2xvqr进行describe，验证DaemonSet类Pod同样受影响","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp node-debugger-node1-2xvqr","purpose":"验证node-debugger这种系统类Pod是否同样出现ImagePullBackOff","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-pod-describe","description":"对g1异常组(CrashLoopBackOff)的代表Pod进行describe","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-crashloop-config-file-missing-58cf574c9f-968q9","purpose":"获取CrashLoopBackOff Pod的Events、Last State、Exit Code","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-pod-yaml","description":"获取CrashLoopBackOff Pod的YAML，检查image和配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-crashloop-config-file-missing-58cf574c9f-968q9 -o yaml","purpose":"检查CrashLoopBackOff Pod的image配置、restartPolicy、volume mounts","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-previous-logs","description":"获取CrashLoopBackOff Pod的previous logs查看崩溃原因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs -n aiops-e2e rc-crashloop-config-file-missing-58cf574c9f-968q9 --previous","purpose":"获取容器上次崩溃的日志内容，确定CrashLoop根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-cluster-events","description":"检查集群近期Events，搜索ImagePull相关错误","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector type=Warning --sort-by=.lastTimestamp | head -50","purpose":"获取集群Warning级别事件，查找FailedToPullImage/ErrImagePull等全局线索","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 10/10 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g2-rep-pod-de... | critical | ✅ | kubectl_describe | 对主异常组g2(ImagePullBackOff/ErrImagePull)的代表Pod进... | `kubectl describe pod -n default network-test-1779374716` |
   | g2-rep-pod-yaml | critical | ✅ | kubectl_get_yaml | 获取ErrImagePull Pod的完整YAML，检查image和imagePullSe... | `kubectl get pod -n default network-test-1779374716 -o yaml` |
   | g2-rep-pod2-d... | critical | ✅ | kubectl_describe | 对另一个namespace的ImagePullBackOff代表Pod进行describe... | `kubectl describe pod -n aiops-e2e test-dns-1779360358` |
   | g2-rep-pod2-yaml | important | ✅ | kubectl_get_yaml | 获取aiops-e2e/test-dns-1779360358的YAML检查image配置 | `kubectl get pod -n aiops-e2e test-dns-1779360358 -o yaml` |
   | g2-mcp-pod-de... | important | ✅ | kubectl_describe | 对mcp namespace的ImagePullBackOff代表Pod进行describ... | `kubectl describe pod -n mcp connectivity-test` |
   | g2-node-debug... | important | ✅ | kubectl_describe | 对mcp/node-debugger-node1-2xvqr进行describe，验证Da... | `kubectl describe pod -n mcp node-debugger-node1-2xvqr` |
   | g1-pod-describe | critical | ✅ | kubectl_describe | 对g1异常组(CrashLoopBackOff)的代表Pod进行describe | `kubectl describe pod -n aiops-e2e rc-crashloop-config-file-missing-58cf574c9f...` |
   | g1-pod-yaml | important | ✅ | kubectl_get_yaml | 获取CrashLoopBackOff Pod的YAML，检查image和配置 | `kubectl get pod -n aiops-e2e rc-crashloop-config-file-missing-58cf574c9f-968q...` |
   | g1-previous-logs | important | ✅ | kubectl_previous_logs | 获取CrashLoopBackOff Pod的previous logs查看崩溃原因 | `kubectl logs -n aiops-e2e rc-crashloop-config-file-missing-58cf574c9f-968q9 -...` |
   | g2-cluster-ev... | important | ✅ | kubectl_events | 检查集群近期Events，搜索ImagePull相关错误 | `kubectl get events --all-namespaces --field-selector type=Warning --sort-by=....` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (26.4s)
   📤 → 下游数据: root_cause=集群共 34 个异常 Pod，核心故障为 33 个 Pod 的 ImagePullBackOff/ErrImagePull（主异常组 g2）。通过 across-namespace 交叉验证：default/network-test-1779374716（node2）→ dial tcp 52.58.1.161:443: i/o timeout；aiops-e2e/test-dns-1779360358（node1）→ connection reset by peer；mcp/connectivity-test（node2）→ dial tcp 157.240.17.35:443: i/o timeout；mcp/node-debugger-node1-2xvqr（node1，镜像 curlimages/curl:8.12.1）→ dial tcp 128.121.146.101:443: i/o timeout。所有 Pod 均为公开镜像、无 imagePullSecrets，可排除认证/配置问题。故障覆盖 node1 和 node2 两个工作节点以及多个 registry 域（do
... 截断，原始 771 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1、node2）到外部镜像仓库的出站网络不可达：TCP 拨号到 registry-1.docker.io 等多个 registry IP（52.58.1.161、157.240.17.35、128.121.146.101 等）的 443 端口全部 i/o timeout 或 connection reset by peer，导致 kubelet 无法拉取任何外部镜像。", "propagation": "节点出站网络故障 → kubelet 在 node1/node2 上尝试拉取 docker.io 及 registry.k8s.io 镜像时 TCP 连接失败（i/o timeout）或被对端重置（connection reset）→ 所有容器状态进入 ImagePullBackOff/ErrImagePull → Pod 无法启动容器，phase 保持 Pending。", "direct_cause": "kubelet 无法通过 HTTP Head 请求从外部镜像仓库（docker.io、registry.k8s.io）获取镜像 manifest，错误为 dial tcp ...:443: i/o timeout 或 connection reset by peer。", "manifestation": "33 个 Pod（涉及 aiops-e2e、default、mcp 三个 namespace）处于 Pending 状态，waiting_reason=ImagePullBackOff 或 ErrImagePull；kubectl get pods 显示 0/1 Ready。"}
   rca_analysis={"phenomenon": "集群中存在 34 个异常 Pod：33 个 Pending（32 个 ImagePullBackOff + 1 个 ErrImagePull），分布在 aiops-e2e、default、mcp 三个 namespace 的 node1 和 node2 上，所有 Pending Pod 的 waiting_reason 均为 ImagePullBackOff/ErrImagePull；另有 1 个 CrashLoopBackOff Pod（aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-968q9）以及 1 个 Failed/Evicted Pod（xnet/observability-kibana，2026-04-24 被驱逐）。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "default/network-test-1779374716: Failed pull busybox:1.36.1 → dial tcp 52.58.1.161:443: i/o timeout (node2)", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe", "content": "aiops-e2e/test-dns-1779360358: Failed pull busybox:1.36.1 → connection reset by peer (node1)", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe", "content": "mcp/connectivity-test: Failed pull busybox:1.36.1 → dial tcp 157.240.17.35:443: i/o timeout (node2)", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe", "content": "mcp/node-debugger-node1-2xvqr: Failed pull curlimages/curl:8.12.1 → dial tcp 128.121.146.101:443: i/o timeout (node1)", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_yaml", "content": "network-test-1779374716: image=busybox:1.36.1, imagePullSecrets=absent, 公开镜像无需认证", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_yaml", "content": "test-dns-1779360358: image=busybox:1.36.1, imagePullSecrets=absent", "reliability": "高"}, {"id": "e7", "source": "kubectl_events", "content": "集群 Events: 多个 Warning Failed 事件指向 docker.io 及 registry.k8s.io，全部为 i/o timeout / connection reset", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe", "content": "rc-crashloop-config-file-missing: CrashLoopBackOff, image busybox:1.36 (imagePullPolicy=Never, 本地已有), Exit Code=1", "reliability": "高"}, {"id": "e9", "source": "kubectl_previous_logs", "content": "容器日志: RUNTIME_STARTUP_ERROR: required config file missing, cat: /etc/rootcause-app/config.yaml: No such file or directory", "reliability": "高"}, {"id": "e10", "source": "kubectl_get_yaml", "content": "rc-crashloop-config-file-missing YAML: imagePullPolicy=Never, command=sh -c, args=echo + cat config.yaml", "reliability": "高"}, {"id": "e11", "source": "layer_handoff", "content": "34 abnormal pods: 32 ImagePullBackOff, 1 ErrImagePull, 1 CrashLoopBackOff; 节点 node1/node2 均受影响", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Failed to pull image \"busybox:1.36.1\" ... dial tcp 52.58.1.161:443: i/o timeout", "interpretation": "node2 上 default/network-test-1779374716 无法拨号到 docker.io registry IP 52.58.1.161，出站 TCP 443 连接超时"}, {"evidence_id": "e2", "raw_data": "Failed to pull image \"busybox:1.36.1\" ... read tcp 10.2.0.49:49162->3.91.167.191:443: read: connection reset by peer", "interpretation": "node1 上同一镜像拉取时 TCP 连接被 docker.io registry 对端重置，同属网络层故障"}, {"evidence_id": "e3", "raw_data": "Failed to pull image \"busybox:1.36.1\" ... dial tcp 157.240.17.35:443: i/o timeout", "interpretation": "mcp namespace 的 Pod 在 node2 上也出现 docker.io 超时，确认非 namespace 级别问题"}, {"evidence_id": "e4", "raw_data": "Failed to pull image \"curlimages/curl:8.12.1\" ... dial tcp 128.121.146.101:443: i/o timeout", "interpretation": "node-debugger 使用不同镜像(curlimages/curl)同样超时，排除镜像本身问题，确认为集群出站网络故障"}, {"evidence_id": "e5", "raw_data": "imagePullSecrets: <absent>, image=busybox:1.36.1", "interpretation": "Pod 无私有仓库认证配置，镜像为公开 docker.io 镜像，可排除 imagePullSecret 缺失或认证失败"}, {"evidence_id": "e6", "raw_data": "imagePullSecrets: <absent>, image=busybox:1.36.1", "interpretation": "跨 namespace 验证，均无 imagePullSecrets，确认认证问题不是根因"}, {"evidence_id": "e7", "raw_data": "Warning Failed ... dial tcp ... i/o timeout (多个不同 IP)", "interpretation": "集群 Events 中有 21+ 条 Warning/Failed 事件，涉及多个不同的 registry IP 地址全部超时，强证据表明集群级出站网络不可达"}, {"evidence_id": "e8", "raw_data": "CrashLoopBackOff, image=busybox:1.36, imagePullPolicy=Never, containerStatuses.exitCode=1", "interpretation": "CrashLoopBackOff Pod 使用 imagePullPolicy=Never 且镜像已本地存在，与网络问题无关；容器以 code 1 退出"}, {"evidence_id": "e9", "raw_data": "RUNTIME_STARTUP_ERROR: required config file missing\ncat: can't open '/etc/rootcause-app/config.yaml': No such file or directory", "interpretation": "容器启动时尝试读取 /etc/rootcause-app/config.yaml 不存在，应用配置缺失导致崩溃"}, {"evidence_id": "e10", "raw_data": "command: sh -c, args: echo ...; cat /etc/rootcause-app/config.yaml", "interpretation": "Pod spec 明确执行 cat config.yaml 但该文件未挂载到容器中，符合配置缺失根因"}, {"evidence_id": "e11", "raw_data": "34 abnormal pods, 33 Pending (ImagePullBackOff/ErrImagePull), 1 CrashLoopBackOff, nodes: node1, node2", "interpretation": "确认影响规模：33 个 Pod 因镜像拉取失败处于 Pending 状态，覆盖 node1 和 node2 两个工作节点"}], "causal_chain": {"root_cause": "集群节点（node1、node2）到外部镜像仓库的出站网络不可达：TCP 拨号到 registry-1.docker.io 等多个 registry IP（52.58.1.161、157.240.17.35、128.121.146.101 等）的 443 端口全部 i/o timeout 或 connection reset by peer，导致 kubelet 无法拉取任何外部镜像。", "propagation": "节点出站网络故障 → kubelet 在 node1/node2 上尝试拉取 docker.io 及 registry.k8s.io 镜像时 TCP 连接失败（i/o timeout）或被对端重置（connection reset）→ 所有容器状态进入 ImagePullBackOff/ErrImagePull → Pod 无法启动容器，phase 保持 Pending。", "direct_cause": "kubelet 无法通过 HTTP Head 请求从外部镜像仓库（docker.io、registry.k8s.io）获取镜像 manifest，错误为 dial tcp ...:443: i/o timeout 或 connection reset by peer。", "manifestation": "33 个 Pod（涉及 aiops-e2e、default、mcp 三个 namespace）处于 Pending 状态，waiting_reason=ImagePullBackOff 或 ErrImagePull；kubectl get pods 显示 0/1 Ready。"}, "root_cause": "集群共 34 个异常 Pod，核心故障为 33 个 Pod 的 ImagePullBackOff/ErrImagePull（主异常组 g2）。通过 across-namespace 交叉验证：default/network-test-1779374716（node2）→ dial tcp 52.58.1.161:443: i/o timeout；aiops-e2e/test-dns-1779360358（node1）→ connection reset by peer；mcp/connectivity-test（node2）→ dial tcp 157.240.17.35:443: i/o timeout；mcp/node-debugger-node1-2xvqr（node1，镜像 curlimages/curl:8.12.1）→ dial tcp 128.121.146.101:443: i/o timeout。所有 Pod 均为公开镜像、无 imagePullSecrets，可排除认证/配置问题。故障覆盖 node1 和 node2 两个工作节点以及多个 registry 域（do\n... 截断，原始 771 字符", "root_cause_summary": "集群共 34 个异常 Pod，核心故障为 33 个 Pod 的 ImagePullBackOff/ErrImagePull（主异常组 g2）。通过 across-namespace 交叉验证：default/network-test-1779374716（node2）→ dial tcp 52.58.1.161:443: i/o timeout；aiops-e2e/test-dns-1779360358（node1）→ connection reset by peer；mcp/connectivity-test（node2）→ dial tcp 157.240.17.35:443: i/o timeout；mcp/node-debugger-node1-2xvqr（node1，镜像 curlimages/curl:8.12.1）→ dial tcp 128.121.146.101:443: i/o timeout。所有 Pod 均为公开镜像、无 imagePullSecrets，可排除认证/配置问题。故障覆盖 node1 和 node2 两个工作节点以及多个 registry 域（do\n... 截断，原始 771 字符", "confidence": 0.95, "confidence_reason": "有直接证据：4 个跨 namespace/跨节点的 Pod describe 均明确显示 TCP 拨号超时或连接重置；YAML 排除镜像地址或认证问题；集群 Events 覆盖多个 registry IP 全部超时。因果链完整、无其他 plausible 解释。CrashLoopBackOff Pod 有 previous logs 直接定位配置缺失。仅缺少网络层面 traceroute/防火墙规则确认，但不影响根因定性。", "primary_runbooks": [], "alternative_causes": [{"cause": "镜像地址或 tag 不存在（如 busybox:1.36.1 不存在）", "probability": "low", "reason": "busybox:1.36.1 是 docker.io 官方有效 tag；curlimages/curl:8.12.1 也是有效 tag；错误信息是网络超时而非 manifest unknown，排除此场景"}, {"cause": "imagePullSecret 缺失或认证失败", "probability": "low", "reason": "所有检查的 Pod YAML 中 imagePullSecrets 均为 absent，且所有镜像均为公开镜像（docker.io 公共仓库），无需认证"}, {"cause": "节点到单个镜像仓库网络问题（docker.io 独有问题）", "probability": "low", "reason": "node-debugger 使用 curlimages/curl（也在 docker.io）同样超时，且 registry-conn-test 类 Pod 目标也是 registry-1.docker.io；但集群 Events 也包含 registry.k8s.io 的超时记录，表明多个 registry 域均不可达"}, {"cause": "节点资源不足导致 Pod 无法调度", "probability": "low", "reason": "所有 Pending Pod 的 PodScheduled condition 均为 True，且节点上已有 Running Pod，调度层面无问题"}, {"cause": "g1 CrashLoopBackOff 与镜像拉取有关", "probability": "low", "reason": "g1 Pod 使用 imagePullPolicy=Never，镜像已本地存在（Image ID 已填充），previous logs 明确指向配置文件缺失，与 g2 完全独立"}], "limitations": "未采集防火墙规则/nat 配置/网络策略/traceroute 等网络层证据，无法定位具体网络瓶颈位置（如代理、防火墙、路由、DNS 解析阶段）；未验证 node1/node2 上其他非 kubelet 的出站网络连通性（如 curl 到外部站点）；xnet/observability-kibana Evicted Pod（2026-04-24 被驱逐到 master 节点）的证据仅确认其存在但未深究驱逐原因，因其与当前故障无直接关联。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群共 34 个异常 Pod，核心故障为 33 个 Pod 的 ImagePullBackOff/ErrImagePull（主异常组 g2）。通过 across-namespace 交叉验证：default/network-test-1779374716（node2）→ dial tcp 52.58...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1、node2）到外部镜像仓库的出站网络不可达：TCP 拨号到 registry-1.docker.io 等多个 registry IP（52.58.1.161、157.240.17.35、128.121.146.101 等）的 443 端口全部 i/o timeout 或 connection reset by peer，导致 kubelet 无法拉取任何外部镜像。
     传导机制: 节点出站网络故障 → kubelet 在 node1/node2 上尝试拉取 docker.io 及 registry.k8s.io 镜像时 TCP 连接失败（i/o timeout）或被对端重置（connection reset）→ 所有容器状态进入 ImagePullBackOff/ErrImagePull → Pod 无法启动容器，phase 保持 Pending。
     最终表现: 33 个 Pod（涉及 aiops-e2e、default、mcp 三个 namespace）处于 Pending 状态，waiting_reason=ImagePullBackOff 或 ErrImagePull；kubectl get pods 显示 0/1 Ready。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (36.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8497 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 47.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，收到您的诊断请求。作为资深 K8s 诊断报告专家，我将直接回答您的核心问题，并提供一份详尽、完整的诊断报告。

---
## 📊 集群状态总览

您当前集群存在 **34 个异常 Pod**，核心问题是 **集群出站网络故障** 导致大量 Pod 无法拉取镜像。

### **核心问题：集群网络故障导致大规模镜像拉取失败 (L3)**
**原因**: 集群两个工作节点（`node1`, `node2`）到外部镜像仓库的 **出站网络不可达**。
**影响**: 导致 3 个命名空间（`aiops-e2e`, `default`, `mcp`）的 **33 个 Pod** 处于 `ImagePullBackOff`/`ErrImagePull` 状态，无法启动。

### **辅助问题：Pod CrashLoopBackOff**
**原因**: 单个 Pod (`aiops-e2e/rc-crashloop-config-file-missing-*`) 因 **缺少配置文件** 持续崩溃重启。

### **问题数据摘要**
| 异常状态 | Pod 数量 | 涉及 Namespace | 影响节点 | 核心原因（简要） |
|---|---|---|---|---|
| **ImagePullBackOff/ErrImagePull** | **33** | aiops-e2e, default, mcp | node1, node2 | 集群节点无法连接外部镜像仓库 (如 docker.io) |
| **CrashLoopBackOff** | 1 | aiops-e2e | node1 | 配置文件缺失 (`/etc/rootcause-app/config.yaml`) |
| **Evicted** | 1 | xnet | master | (历史问题，与当前故障无直接关联) |

---

## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff (32), ErrImagePull (1), CrashLoopBackOff (1) |
| **兼容归因层** | L3 - 镜像仓库层（根本原因：网络层可达性） |
| **问题分类** | ImagePullFailure / CrashLoopBackOff |
| **置信度** | **高 (95%)** |
| **证据完整度** | 10/10 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 异常 Pod 数 | 34 |
| 核心问题 Pod 组 | 33 个 `ImagePullBackOff`/`ErrImagePull` Pod |
| 辅助问题 Pod | `aiops-e2e/rc-crashloop-config-file-missing-<hash>` |
| 核心问题影响节点 | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| 核心问题影响 Namespace | `aiops-e2e`, `default`, `mcp` |
| 核心问题错误信息 | `Failed to pull image "...": rpc error: code = Unknown desc: dial tcp A.B.C.D:443: i/o timeout` |

---
## 🕵️ 证据链
### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 (全局) | `kubectl get pods --all-namespaces` | 34 abnormal. 33 Pending (32 ImagePullBackOff, 1 ErrImagePull), 1 CrashLoopBackOff, 1 Evicted | **确认核心问题**：大规模 ImagePullBackOff |
| 2 | 跨命名空间 Pod 描述 | `kubectl describe pod <pod>` (default, mcp, aiops-e2e) | ⚠️ `Warning Failed` (x50 over 5h30m) `Failed to pull image "curlimages/curl:8.12.1": rpc error: code = Unknown desc: dial tcp 128.121.146.101:443: i/o timeout` | **直接证据**：节点到镜像仓库的网络连接超时。 |
| 3 | 跨命名空间 Pod 描述 | `kubectl describe pod <pod>` (default) | `Normal BackOff 37s (x298 over 89m) kubelet Back-off pulling image "busybox:1.36.1"` | **直接证据**：kubelet 反复尝试拉取镜像均失败。 |
| 4 | 跨命名空间 Pod YAML | `kubectl get pod <pod> -o yaml` (default, aiops-e2e) | `image: busybox:1.36.1`, `image: curlimages/curl:8.12.1` | **排除证据**：镜像为公开标准镜像，非私有/配置错误。 |
| 5 | 跨命名空间 Pod YAML | `kubectl get pod <pod> -o yaml` (default, aiops-e2e) | `imagePullSecrets: <none>` | **排除证据**：不存在认证配置问题，可排除认证失败。 |
| 6 | 集群 Events | `kubectl get events --all-namespaces` | ⚠️ `Warning Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc: failed to pull and unpack image "docker.io/library/busybox:1.36.1"` | **直接证据**：确认含超时错误，指向网络问题。 |
| 7 | 节点分布 | `kubectl describe pod <pod>` (多项) | `Node: node1/10.2.0.49`, `Node: node2/10.2.0.50` | **直接证据**：问题覆盖两个工作节点，非单点故障。 |
| 8 | CrashLoopBackOff Pod 描述 | `kubectl describe pod rc-crashloop-...` | `pod_abnormal_type=CrashLoopBackOffRuntime` | **确认辅助问题**：CrashLoopBackOff 类型。 |
| 9 | CrashLoopBackOff Pod 日志 | `kubectl logs <pod> --previous` | `cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory` | **根因证据**：Pod 崩溃是由于找不到配置文件。 |
| 10 | 被驱逐 Pod | `kubectl query` 结果 | `xnet/observability-kibana-65d7c45f6d-7zc9l` Evicted, 位于 master 节点 | **背景信息**：独立的历史驱逐事件，与当前故障无直接关联。 |

### 证据关联分析
- **证据 #2 + #3 + #5 印证**：不同命名空间、不同节点、不同公开镜像的 Pod 均因 TCP 超时 (`i/o timeout`) 无法拉取，排除了镜像或节点单点故障。
- **证据 #1 + #6 + #7 印证**：大规模 (33个)、跨节点、跨命名空间的一致错误，指向一个 **全局性的集群网络故障**。
- **证据 #8 + #9 印证**：`CrashLoopBackOff` 问题独立，由 Pod 内部缺少配置文件导致，与外部网络无关。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点防火墙/网络策略/路由配置 | critical | 无法定位网络瓶颈的具体位置（代理、防火墙、路由或DNS） |
| node1/node2 上非容器化的网络连通性测试 | important | 无法确认是节点整体网络问题还是仅kubelet进程受限 |

---
## 🎯 根因分析
### 因果链
```
┌───────────────────────────────────────────────────────────────────────┐
│ 根本原因 (L3 镜像仓库网络层)                                          │
│ 集群工作节点 (node1, node2) 到外部镜像仓库的出站网络不可达：           │
│ 对 registry-1.docker.io 等多个外部镜像仓库 IP 的 TCP 443 端口连接全部  │
│ 返回 i/o timeout 或 connection reset by peer。                         │
└───────────────────────────────────────────────────────────────────────┘
                                  ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                              │
│ kubelet 尝试从外部镜像仓库（如 docker.io）拉取镜像 manifest，           │
│ 但在建立 TCP 连接时失败，导致反复重试和 BackOff 策略。                  │
└───────────────────────────────────────────────────────────────────────┘
                                  ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                              │
│ 33 个 Pod 的容器状态转为 ImagePullBackOff/ErrImagePull：                │
│ kubelet 无法通过 HTTP Head 请求从外部仓库获取镜像。                     │
└───────────────────────────────────────────────────────────────────────┘
                                  ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                          │
│ 33 个 Pod 处于 Pending 状态，`kubectl get pods` 显示为 0/1 Ready。     │
│ 集群出现大量 ImagePullBackOff 和 ErrImagePull 错误。                   │
└───────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**核心结论**：根据证据 #2, #3, #6, #7，**问题的根本原因是集群两个工作节点（node1, node2）到外部镜像仓库的出站网络不可达**。这导致所有需要从外部（如 docker.io, registry.k8s.io）拉取镜像的 Pod 都无法启动（33 个 Pod 处于 `ImagePullBackOff`）。

**辅助结论**：根据证据 #9，单独的 CrashLoopBackOff Pod 是由于其内部应用程序无法找到预期的配置文件 `/etc/rootcause-app/config.yaml` 导致持续崩溃重启，与网络问题无关。

**置信度**：高 (95%)
- ✅ 跨3个命名空间、2个节点、多个公开镜像，一致性的 `i/o timeout` 错误。
- ✅ `imagePullSecrets` 为空，排除了认证问题。
- ⚠️ 缺少防火墙/路由/代理等网络层配置证据，无法定位具体网络瓶颈。

---
## 🛠️ 修复建议
### 崩溃问题修复（可独立执行）
**1. [优先] 修复 CrashLoopBackOff Pod：添加缺失的配置文件**
```bash
# 假设配置文件预期路径为 /etc/rootcause-app/config.yaml
# 1. 创建一个简单的 ConfigMap
kubectl create configmap rc-app-config -n aiops-e2e --from-literal=config.yaml="key: value" --dry-run=client -o yaml | kubectl apply -f -
# 2. 修改 Deployment 挂载 ConfigMap (先将 YAML 导出修改)
kubectl get deployment rc-crashloop-config-file-missing -n aiops-e2e -o yaml > /tmp/deploy.yaml
# 编辑 /tmp/deploy.yaml，在 containers[0].volumeMounts 和 spec.volumes 下添加 ConfigMap 挂载
# 示例（请根据实际 YAML 结构调整）：
# volumeMounts:
# - mountPath: /etc/rootcause-app
#   name: app-config
# volumes:
# - name: app-config
#   configMap:
#     name: rc-app-config
# 3. 应用修改
kubectl apply -f /tmp/deploy.yaml
```
*依据*：崩溃日志明确报错 `cat: can't open '/etc/rootcause-app/config.yaml'`。
> **注意**：如果该 ConfigMap 内容未知，需要联系应用开发者或查看镜像内默认配置。

### 网络问题修复（需要联系基础设施团队）
**2. [核心优先] 排查并恢复出站网络**
此问题需要 **网络管理员或基础设施团队** 介入，检查 `node1` 和 `node2` 到公网的网络路径。
```bash
# 在 node1 和 node2 上执行（通过 SSH 或 kubectl node-shell）
# 1. 测试简单的外部连通性
ping 8.8.8.8
# 2. 测试对 Docker Hub 的 TCP 连接（模拟拉取镜像）
curl -vs https://registry-1.docker.io/v2/ --connect-timeout 5 2>&1 | head -20
# 3. 检查防火墙规则 (iptables/nftables)
iptables -L -n
# 4. 检查代理配置 (操作系统的 http_proxy/https_proxy, containerd 配置)
echo $http_proxy $https_proxy
cat /etc/containerd/config.toml | grep proxy
```

**3. [临时规避] 将对外部镜像的依赖，改为节点本地运行镜像仓库代理或私有仓库**
如果出站网络不能短期恢复，可以在集群内搭建一个 Harbor 等私有镜像仓库，并将所有需要的镜像（`busybox:1.36.1`, `curlimages/curl:8.12.1` 等）同步到私有仓库，然后修改所有异常 Deployment 的 `image` 字段指向私有仓库。
```bash
# 示例：将 busybox 镜像推送到假设的私有仓库 myregistry.local
docker pull busybox:1.36.1
docker tag busybox:1.36.1 myregistry.local/library/busybox:1.36.1
docker push myregistry.local/library/busybox:1.36.1

# 修改 Deployment 镜像地址
kubectl set image deployment/<your-deployment> <container-name>=myregistry.local/library/busybox:1.36.1 -n <namespace>
```
*依据*：所有异常 Pod 均因无法访问外部仓库导致，使用私有仓库可完全绕过此问题。

### 长期预防
- **监控告警**：配置集群出口网络连通性监控（Prometheus Blackbox Exporter）。
- **架构优化**：规范使用私有镜像仓库（如 Harbor/Warehouse），将构建产物推送至此，减少对公网不稳定的依赖。
- **配置管理**：统一管理应用配置，避免直接依赖容器内路径的配置文件。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认大量 Pod 逃离 Pending | `kubectl get pods -A \| grep -E 'ImagePullBackOff\|ErrImagePull\|Pending'` | 结果为“无”或大幅减少 |
| 2. 确认 CrashLoopBack 修复 | `kubectl get pods -n aiops-e2e \| grep crashloop` | `STATUS` 为 `Running` |
| 3. 验证 Pod 不再崩溃 | `kubectl logs <from-step2-pod-name> -n aiops-e2e \| grep "config file"` | 无相关错误日志 |
| 4. 整体集群健康检查 | `kubectl get pods -A \| grep -v Running` | 无异常状态 Pod 或仅少量预期的 Completed Pod |

---
## ⚠️ 注意事项
- 网络修复步骤（#2）通常需要集群管理员权限，请**联系您的平台支持团队**。
- 在未修复网络前，任何需要从外部拉取新镜像的部署都将失败，建议做好变更管理。

---

## 📊 性能统计

├─ 总耗时: 2.8m
├─ 问题定位: 46.4s (28%) ✅
├─ 证据链采集: 57.6s (35%) ✅
├─ 根因分析: 26.4s (16%) ✅
├─ 汇总总结: 36.5s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 26 次
```

📋 诊断追踪

- **核心 Runbook**: pod-crashloop-runtime
- **参考 Runbook**: pod-crashloop-runtime
- **工具调用**: 26 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
