======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 2c759dc672914c34]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先对集群进行全局 Pod 状态扫描，看看当前有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster output: 78 pods listed. 51 abnormal (CrashLoopBackOff:1, OOMKilled:1, ErrImagePull:22, ImagePullBackOff:27). Running:27 (including system components on master/node1/node
   💭 [问题定位] 很好，发现了大量异常 Pod。我来获取更多细节，按状态分组查看。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 49 个 Pod，全部处于 Pending 状态（READY=false），分布在 namespace aiops-e2e、default、mcp 中，调度到 node1 和 node2 上。最早创建 2026-05-21T10:44:28（node-debugger-node1-2xvqr），最晚 2026-05-21T21:14:02（c
   💭 [问题定位] 这里显示的都是 Pending 状态，但刚才扫描显示有 ImagePullBackOff/ErrImagePull。让我用更精确的方式查询。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=14687 lines=358
Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "test-dns-1779360358",
  "phase": "Pending",
  "reason": "ErrImagePull",
  "m
   💭 [问题定位] 数据很多，让我把完整的异常 Pod 列表整理出来。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=3251 lines=52
Executing jq query for pods...
aiops-e2e/test-dns-1779360358 phase=Pending reason=ImagePullBackOff
default/dig-tool phase=Pending reason=ImagePullBack
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=3251 lines=52
Executing jq query for pods...
aiops-e2e/test-dns-1779360358 phase=Pending reason=ImagePullBackOff
default/dig-tool phase=Pending reason=ImagePullBack
   💭 [问题定位] 还有一部分没显示完，让我获取完整列表。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=182 lines=52
Executing jq query for pods...
29
16
26
22
27
28
24
27
22
20
20
20
26
31
28
37
35
29
27
21
18
22
9
17
24
18
23
23
20
29
29
29
29
29
29
29
29
29
29
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=1140 lines=52
Executing jq query for pods...
test-dns-1779360358
dig-tool
dns-check-evidence
dns-check-test
dns-diag-1779390521
dns-resolve-gcr-test
dns-resolve-tes
   💭 [问题定位] 还有遗漏，让我检查一下之前看到的那个 OOMKilled/CrashLoopBackOff 的 Pod。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   ✅ [问题定位] 完成 (35.4s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L2
   scenarios=[{'scenario': '集群节点无法访问外部镜像仓库（docker.io、registry.k8s.io）导致大规模镜像拉取失败', 'probability': '高', 'reason': "49个Pending Pod中有40+个处于ImagePullBackOff/ErrImagePull，test-dns-1779360358明确报错'dial tcp 154.83.15.20:443: i/o timeout'，表明网络出口不通Docker Hub"}, {'scenario': '集群DNS或网络CNI组件存在缺陷导致域名解析/路由异常', 'probability': '中', 'reason': '大量DNS测试Pod和网络连通性测试Pod异常，表明用户正在主动诊断DNS/网络问题'}, {'scenario': 'Pod内存超限导致OOMKilled（单一Pod）', 'probability': '低', 'reason': '仅aiops-e2e/rc-oomkilled-memory-limit存在OOMKilled/CrashLoopBackOff问题，范围局限'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "pod", "name": "test-dns-1779360358", "namespace": "aiops-e2e"}, {"type": "pod", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d", "namespace": "aiops-e2e"}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}]
   reasoning=集群存在大量异常Pod，以ImagePullBackOff(27个)、ErrImagePull(22个)为主，同时有一个OOMKilled/CrashLoopBackOff Pod。49个Pending Pod中绝大多数原因是镜像拉取失败（超时或无法解析镜像仓库），核心根因是网络连通性问题（registry-1.docker.io i/o timeout），属于L3层。同时存在一个OOMKilled/CrashLoopBackOff Pod（aiops-e2e/rc-oomkilled-memory-limit）属于L2层补充。当前所有异常Pod均未恢复，活跃异常对象覆盖了L3（镜像/网络）和L2（OOM），但L3是主要根因。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L2"], "layer_name": "网络与镜像层", "confidence": 0.95, "reasoning": "集群存在大量异常Pod，以ImagePullBackOff(27个)、ErrImagePull(22个)为主，同时有一个OOMKilled/CrashLoopBackOff Pod。49个Pending Pod中绝大多数原因是镜像拉取失败（超时或无法解析镜像仓库），核心根因是网络连通性问题（registry-1.docker.io i/o timeout），属于L3层。同时存在一个OOMKilled/CrashLoopBackOff Pod（aiops-e2e/rc-oomkilled-memory-limit）属于L2层补充。当前所有异常Pod均未恢复，活跃异常对象覆盖了L3（镜像/网络）和L2（OOM），但L3是主要根因。", "abnormal_pods": [{"name": "rc-oomkilled-memory-limit-b6d999d-5f29d", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ErrImagePull"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ErrImagePull"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "pod", "name": "test-dns-1779360358", "namespace": "aiops-e2e"}, {"type": "pod", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d", "namespace": "aiops-e2e"}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "集群节点无法访问外部镜像仓库（docker.io、registry.k8s.io）导致大规模镜像拉取失败", "probability": "高", "reason": "49个Pending Pod中有40+个处于ImagePullBackOff/ErrImagePull，test-dns-1779360358明确报错'dial tcp 154.83.15.20:443: i/o timeout'，表明网络出口不通Docker Hub"}, {"scenario": "集群DNS或网络CNI组件存在缺陷导致域名解析/路由异常", "probability": "中", "reason": "大量DNS测试Pod和网络连通性测试Pod异常，表明用户正在主动诊断DNS/网络问题"}, {"scenario": "Pod内存超限导致OOMKilled（单一Pod）", "probability": "低", "reason": "仅aiops-e2e/rc-oomkilled-memory-limit存在OOMKilled/CrashLoopBackOff问题，范围局限"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ErrImagePull", "ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ErrImagePull", "ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "OOMKilled": 1, "ErrImagePull": 22, "ImagePullBackOff": 27}, "total_abnormal": 51, "selected_rows": ["aiops-e2e         rc-oomkilled-memory-limit-b6d999d-5f29d             0/1     CrashLoopBackOff   11 (20s ago)   31m     172.16.166.147   node1    <none>           <none>            app=rc-oomkilled-memory-limit,pod-template-hash=b6d999d,pod_abnormal_type=OOMKilled,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ErrImagePull       0              11h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff   0              6h43m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff   0              5h43m   172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff   0              10h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff   0              3h3m    172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff   0              3h8m    172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull       0              3h8m    172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0              11h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull       0              8h      172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff   0              3h8m    172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull       0              5h50m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff   0              10h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull       0              10h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull       0              7h26m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ErrImagePull       0              3h36m   172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull       0              8h      172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-conn-test-evidence                         0/1     ErrImagePull       0              121m    172.16.104.22    node2    <none>           <none>            run=registry-conn-test-evidence", "default           registry-connect-test                               0/1     ErrImagePull       0              10h     172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff   0              11h     172.16.166.185   node1    <none>           <none>            run=test-net-1779360704"], "raw_ref": "/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L2（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有的 evidence_plan 中的关键工具。先同时启动多个独立的 describe 和日志采集任务。

## 执行证据计划

首先，同时调用所有独立的 kubectl describe 和日志工具：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 调用工具: kubectl_previous_logs
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
      📄 kubectl_describe pod dns-resolve-test (namespace=default, node=node2/10.2.0.50) shows Status=Pending, container state=Waiting(Reason=ErrImagePull). All 5 pull attempts to docker.io/library/busybox:1.3
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool is Waiting with Reason ImagePullBackOff, not Ready, restart count 0. Image pull repeatedly fails for registry.k8
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod curls in namespace mcp on node node2/10.2.0.50 is Pending. Container curls (image: curlimages/curl:7.88.1) is Waiting with Reason ErrImagePull. All 6 pull attempts to docker.io/curlimages/curl:7.8
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 很好，基础 describe 信息都回来了。现在执行剩下的计划项：获取 Pod YAML 配置和集群级镜像拉取失败事件。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: curls
namespace: mcp
creationTimestamp: 2026-05-21T16:59:07Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
serviceAccountName
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dns-resolve-test
namespace: default
creationTimestamp: 2026-05-21T19:02:58Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
ser
   💭 [证据链采集] 事件查询没有输出，让我换个方式获取镜像拉取失败事件：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "mcp         4m43s       Warning   Failed   pod/registry-diag-1779381627         Error: ErrImagePull\nmcp         4m43s       Warning   Failed   pod/registry-diag-177938162
   💭 [证据链采集] 现在让我读取详细的描述输出和 YAML 结果来提取关键证据。
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=6262 lines=135
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-evidence-kubectl_describe.structured.json
offset: 0
r
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2810 lines=63
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2119 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/002-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1679 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/003-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1807 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/004-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1565 lines=50
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/006-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 现在让我也查看一下 YAML 配置信息：
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1456 lines=35
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/010-evidence-kubectl_get_yaml.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1451 lines=35
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/009-evidence-kubectl_get_yaml.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 All 10 pods across namespaces mcp and default failed with ErrImagePull. Every pull attempt to docker.io (busybox:1.36.1, alpine:3.18, curlimages/curl:8.12.1) timed out dialing registry-1.docker.io:443
   💭 [证据链采集] 现在让我查看 OOMKilled Pod 的完整 describe 原始内容，了解关键配置细节：
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=3272 lines=94
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-evidence-kubectl_describe.raw.txt
offset: 0
returned_c
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1345 lines=19
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-evidence-kubectl_describe.raw.txt
offset: 3000
returne
   💭 [证据链采集] ## 已有工具结果完整分析

所有关键工具已调用完毕。以下是基于所有真实工具结果汇总的证据结论。

---

## 📋 证据采集结论

### ✅ 已采集证据

#### 【异常组 g2 — 主异常】镜像拉取失败（22 ErrImagePull + 27 ImagePullBackOff）
| 证据项 | 来源 | 关键内容 |
|--------|------|---------|
| **g2-e1** `dns-resolve-test` (default, node2) | `kubectl describe` | 镜像 `busybox:1.36.1`，5次拉取全部 `dial tcp <ip>:443: i/o timeout` 到 `registry-1.docker.io`，20次 ErrImagePull 事件持续 3h1m |
| **g2-e2** `dig-tool` (default, node1) | `kubectl describe` | 镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，超时 `dial tcp 142.250.157.82:443: i/o timeout`（europe-west2 + asia-east1），BackOff x897 |
| **g2-e3** `curls` (mcp, node2) | `kubectl describe` | 镜像 `curlimages/curl:7.88.1`，6次 `i/o timeout` 到 `registry-1.docker.io`（6个不同IP），Failed x41 |
| **g2-e4** `dns-resolve-test` YAML (default) | `kubectl_get_yaml` | 镜像: `busybox:1.36.1`，**无 imagePullSecrets**，错误信息：`dial tcp 108.160.170.39:443: i/o timeout` |
| **g2-e5** `curls` YAML (mcp) | `kubectl_get_yaml` | 镜像: `curlimages/curl:7.88.1`，**无 imagePullSecrets**，错误信息：`dial tcp 168.143.162.58:443: i/o timeout` |
| **g2-e6** 全集群镜像拉取失败事件 | `run_bash_command (events)` | 10 个 Pod（mcp + default）全部 `ErrImagePull`，所有尝试 `docker.io`/`registry.k8s.io` 均 i/o timeout，无一次成功拉取 |

**核心发现**：集群节点（node1 和 node2）均无法访问 `registry-1.docker.io:443`，域名解析成功（DNS 能解出不同 IP），但 TCP 连接全部超时。同时 `registry.k8s.io` 也超时。不存在镜像名/tag错误或认证失败问题，根因是**出口网络无法到达外部镜像仓库**。

---

#### 【异常组 g1 — 次异常】OOMKilled / CrashLoopBackOff
| 证据项 | 来源 | 关键内容 |
|--------|------|---------|
| **g1-e1** `rc-oomkilled-memory-limit` (aiops-e2e) | `kubectl describe` | Last State: **OOMKilled**, Exit Code: **137**, Restart Count: **11**，QoS Class: Burstable，镜像 `python:3.11-slim` 已在本地存在 |
| **g1-e2** 日志（当前+previous） | `kubectl logs` / `logs --previous` | 当前日志和 previous 日志均无输出（容器启动后立即 OOM 退出） |

**核心发现**：这是一个独立的 L2 异常——容器 `python:3.11-slim` 执行 `python -c "import time data = []"` 因 **memory limit 超限**而被 OOMKilled。与镜像拉取故障无关。

---

#### 【异常组 g3 — 最小验证】StartError
| 证据项 | 来源 | 关键内容 |
|--------|------|---------|
| **g3-e1** `node-debugger-node1-nx8gb` (mcp) | `kubectl describe` | Status: **Failed**，Reason: **StartError**，Exit Code: **128**，Message: `exec: "curl": executable file not found in $PATH: unknown` — 镜像 `busybox:1.36` 中无 `curl` 二进制文件 |

**核心发现**：Pod 配置错误——镜像 `busybox:1.36` 不包含 `curl` 命令，但 Pod command 指定了 `curl`。这是 L4 配置错误，不是网络问题。已成功拉取镜像（Image ID 已存在），但无法启动。

---

### ❌ 未采集证据 / 冲突证据
- **无冲突证据**——所有计划中的 Pod 均存在于指定 namespace，工具均成功返回结果。
- **events 全局查询**：`kubectl get events --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff` 返回空，原因是当前 Kubernetes 版本可能使用 `reason=Failed` + 子消息描述而非独立 Reason；已通过 grep 方式获取到完整失败事件。

---

### 🎯 根因总结

**首要问题（L3 — 影响范围49个Pod）**：集群出口网络无法访问 `registry-1.docker.io:443` 和 `registry.k8s.io`，导致所有需要从外部仓库拉取镜像的 Pod 全部失败（ErrImagePull / ImagePullBackOff）。DNS 解析正常，但 TCP 连接在 443 端口全部 i/o timeout。影响 node1 和 node2 两个节点。

**次要问题（L2 — 孤立Pod）**：`aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d` 因 memory limit 超限反复 OOMKilled（exit 137）。

**个例问题（L4 — 配置错误）**：`mcp/node-debugger-node1-nx8gb` 镜像 busybox 中无 curl 二进制，导致 StartError。
   ✅ [证据链采集] 完成 (1m 4.6s)
   📤 → 下游数据: evidence_items=15/16
   evidence_analysis={"evidence_plan":[{"id":"g1-e1","description":"完整验证 g1 (CrashLoopBackOff): describe Pod rc-oomkilled-memory-limit-b6d999d-5f29d 查看 Last State/Exit Code/Restarts/Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-oomkilled-memory-limit-b6d999d-5f29d","tool_args":{"kind":"Pod","name":"rc-oomkilled-memory-limit-b6d999d-5f29d","namespace":"aiops-e2e"},"purpose":"获取 OOMKilled/CrashLoopBackOff Pod 的 Last State Exit Code、Events 和 Restart 次数","evidence_type":"pod_describe","target_scope":"Pod/aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-e2","description":"CrashLoopBackOff: 查看 previous logs 确认 OOM 或其他错误","level":"critical","tool":"kubectl_logs","command":"kubectl logs -n aiops-e2e rc-oomkilled-memory-limit-b6d999d-5f29d --previous","tool_args":{"namespace":"aiops-e2e","name":"rc-oomkilled-memory-limit-b6d999d-5f29d","previous":true},"purpose":"获取容器上次 crash 的日志输出确认 OOM 或应用错误","evidence_type":"pod_logs","target_scope":"Pod/aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e1","description":"主异常组 g2 (ErrImagePull/ImagePullBackOff): describe 代表 Pod（跨 node1/node2）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dns-resolve-test","tool_args":{"kind":"Pod","name":"dns-resolve-test","namespace":"default"},"purpose":"获取 ErrImagePull Pod 的 Events 和镜像错误详情，验证 i/o timeout 错误","evidence_type":"pod_describe","target_scope":"Pod/default/dns-resolve-test","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e2","description":"主异常组 g2: describe 另一个代表 Pod 在 node1 上（node1 代表）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dig-tool","tool_args":{"kind":"Pod","name":"dig-tool","namespace":"default"},"purpose":"获取 ImagePullBackOff Pod 的 Events 和镜像错误详情","evidence_type":"pod_describe","target_scope":"Pod/default/dig-tool","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e3","description":"主异常组 g2: describe mcp namespace 代表 Pod","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp curls","tool_args":{"kind":"Pod","name":"curls","namespace":"mcp"},"purpose":"获取 mcp namespace ErrImagePull Pod 的 Events 和镜像错误详情","evidence_type":"pod_describe","target_scope":"Pod/mcp/curls","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e4","description":"查看 g2 组 Pod 的 spec.image 确认镜像来源","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n default dns-resolve-test -o yaml","tool_args":{"kind":"pod","name":"dns-resolve-test","namespace":"default","format":"yaml"},"purpose":"检查镜像地址和 imagePullSecrets 配置","evidence_type":"pod_spec","target_scope":"Pod/default/dns-resolve-test","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-e5","description":"查看 mcp namespace 代表 Pod 的 spec.image","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n mcp curls -o yaml","tool_args":{"kind":"pod","name":"curls","namespace":"mcp","format":"yaml"},"purpose":"检查 mcp 命名空间下 Pod 的镜像地址和 imagePullSecrets","evidence_type":"pod_spec","target_scope":"Pod/mcp/curls","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-e6","description":"查看 namespace 级别的 events，确认镜像拉取失败相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by=.lastTimestamp 2>/dev/null | tail -30","tool_args":{},"purpose":"采集集群中所有镜像拉取失败的事件摘要","evidence_type":"cluster_events","target_scope":"cluster-wide","acceptable_tools":[],"counts_for_completeness":true},{"id":"g3-e1","description":"最小验证 g3 (StartError): describe pod node-debugger-node1-nx8gb","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp node-debugger-node1-nx8gb","tool_args":{"kind":"Pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"获取 StartError Pod 的当前状态和 Events 确认错误详情","evidence_type":"pod_describe","target_scope":"Pod/mcp/node-debugger-node1-nx8gb","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-oomkilled-memory-limit-b6d999d-5f29d\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\nName:             rc-oomkilled-memory-limit-b6d999d-5f29d\nLabels:           app=rc-oomkilled-memory-limit\n                  pod_abnormal_type=OOMKilled\nAnnotations:      aiops.e2e/runbook: pod-oomkilled.md\nControlled By:  ReplicaSet/rc-oomkilled-memory-limit-b6d999d\n      Reason:       OOMKilled\n      Exit Code:    137\n  Normal   Scheduled       32m                    default-scheduler  Successfully assigned aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d to node1\n  Warning  BackOff         2m39s (x138 over 32m)  kubelet            Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-5f29d_aiops-e2e(2a0a6edf-c1a7-4057-abfb-be8ea3edfa50)\n      Reason:       CrashLoopBackOff\n                  cni.projectcalico.org/containerID: a31bbc9e3699735c3f9d3873265a2428dcff2f435ffcefe4489801098b253eda\n                  cni.projectcalico.org/podIP: 172.16.166.147/32\n                  cni.projectcalico.org/podIPs: 172.16.166.147/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe pod dns-resolve-test (namespace=default, node=node2/10.2.0.50) shows Status=Pending, container state=Waiting(Reason=ErrImagePull). All 5 pull attempts to docker.io/library/busybox:1.36.1 failed with i/o timeout dialing different registry IPs (69.63.180.173, 159.138.20.20, 98.159.108.57, 199.59.150.45, 108.160.170.39) on port 443 - network connectivity to registry-1.docker.io is unreachable from node2. Pod has IP 172.16.104.1/32 via Calico. 20 ErrImagePull events over 3h1m.\nkey_facts: [\"pod: dns-resolve-test\", \"namespace: default\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container: dns-resolve-test\", \"image: busybox:1.36.1\", \"container state: Waiting, Reason: ErrImagePull\", \"Ready: False\", \"Restart Count: 0\", \"QoS Class: BestEffort\", \"pod IP: 172.16.104.1/32 (Calico)\", \"5 Failed pull events all show dial tcp <ip>:443: i/o timeout to registry-1.docker.io\", \"target IPs timed out: 69.63.180.173, 159.138.20.20, 98.159.108.57, 199.59.150.45, 108.160.170.39\", \"Error codes: DeadlineExceeded (x3) and Unknown (x2)\", \"Events: 20 occurrences of ErrImagePull over 3h1m\", \"Pulling event seen 19 times over 3h9m (still retrying)\", \"Conditions: Initialized=True, Ready=False, Co\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool is Waiting with Reason ImagePullBackOff, not Ready, restart count 0. Image pull repeatedly fails for registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0: two distinct network timeouts (DeadlineExceeded on europe-west2, Unknown desc on asia-east1) both dial tcp 142.250.157.82:443 i/o timeout. BackOff events: x897 over 6h37m.\nkey_facts: [\"resource: pod dig-tool, namespace: default\", \"node: node1/10.2.0.49\", \"pod status: Pending\", \"container dig-tool state: Waiting, Reason: ImagePullBackOff\", \"container Ready: False, Restart Count: 0\", \"image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"Warning Failed x11 over 6h34m: Failed to pull image - DeadlineExceeded, dial tcp 142.250.157.82:443: i/o timeout (europe-west2-docker.pkg.dev)\", \"Warning Failed x15 over 3h2m: Failed to pull image - Unknown desc, dial tcp 142.250.157.82:443: i/o timeout (asia-east1-docker.pkg.dev)\", \"Normal BackOff x897 over 6h37m: Back-off pulling image\"]\nconflicts: [\"current_summary says 'Warning Failed 37m (x11 over 6h34m)' and 'Warning Failed 7m10s (x15 over 3h2m)' — matches raw_preview, no conflict\", \"current_summary\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod curls in namespace mcp on node node2/10.2.0.50 is Pending. Container curls (image: curlimages/curl:7.88.1) is Waiting with Reason ErrImagePull. All 6 pull attempts to docker.io/curlimages/curl:7.88.1 failed due to i/o timeout dialing registry-1.docker.io (multiple IPs). Event: Failed x41 over 5h10m → Error: ErrImagePull. Pod has IP 172.16.104.2, QoS BestEffort, no environment, args run curl against registry.k8s.io.\nkey_facts: [\"pod: curls, namespace: mcp\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container curls: State Waiting, Reason ErrImagePull, Ready False, Restart Count 0\", \"image: curlimages/curl:7.88.1\", \"Container ID and Image ID are empty (not pulled)\", \"Events: Warning Failed x41 over 5h10m → Error: ErrImagePull\", \"6 pull failures, all i/o timeout dialing registry-1.docker.io:443 (IPs: 199.96.62.41, 104.244.46.85, 199.96.58.177, 199.59.149.206, 202.53.137.209, 168.143.162.58)\", \"rpc errors: DeadlineExceeded (5x), Unknown (1x)\", \"pod IP: 172.16.104.2\", \"container args: sh -c 'curl -sI -m5 https://registry.k8s.io/v2/ 2>&1 || echo FAILED'\", \"QoS Class: BestEffort\", \"no Node-Selectors\"]\nconflicts: [\"current_summary says 'Error: ErrImagePull' at 5m53s (x41) — raw_previ\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/005-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/005-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/005-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:               \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/007-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/007-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/007-evidence-kubectl_logs.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/008-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/008-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/008-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: curls\nnamespace: mcp\ncreationTimestamp: 2026-05-21T16:59:07Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- curls: image=curlimages/curl:7.88.1 imagePullPolicy=IfNotPresent\n  args: sh -c curl -sI -m5 https://registry.k8s.io/v2/ 2>&1 || echo FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [curls]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [curls]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- curls: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/curlimages/curl:7.88.1\": failed to resolve reference \"docker.io/curlimages/curl:7.88.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/7.88.1\": dial tcp 168.143.162.58:443: i/o timeout\nvol\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/009-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/009-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/009-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-resolve-test\nnamespace: default\ncreationTimestamp: 2026-05-21T19:02:58Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-resolve-test: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: nslookup registry-1.docker.io\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-resolve-test]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-resolve-test]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-resolve-test: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.170.39:443: i/o timeou\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/010-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/010-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/010-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/011-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/012-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/012-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/012-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"mcp         4m43s       Warning   Failed   pod/registry-diag-1779381627         Error: ErrImagePull\\nmcp         4m43s       Warning   Failed   pod/registry-diag-1779381627         Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 168.143.162.58:443: i/o timeout\\nmcp         4m13s       Warning   Failed   pod/net-check-tool                   Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 108.160.167.167:443: i/o timeout\\nmcp         4m13s       Warning   Failed   pod/net-check-tool                   Error: ErrImagePull\\ndefault     3m43s       Warning   Failed   pod/dns-test-tmp                     Error: ErrImagePull\\n\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/013-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/013-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/013-evidence-run_bash_command.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=6262 lines=135\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-evidence-kubectl_describe.structured.json\noffset: 0\nreturned_chars: 6048\ntotal_chars: 6048\ncontent:\n{\n  \"name\": \"rc-oomkilled-memory-limit-b6d999d-5f29d\",\n  \"namespace\": \"aiops-e2e\",\n  \"node\": \"node1/10.2.0.49\",\n  \"status\": \"Running\",\n  \"lifecycle\": {\n    \"controlled_by\": \"ReplicaSet/rc-oomkilled-memory-limit-b6d999d\",\n    \"qos_class\": \"Burstable\"\n  },\n  \"containers\": [\n    {\n      \"name\": \"app\",\n      \"container_id\": \"containerd://deb3fe2a59e4fddd653c200b9b63e675090d967ead4762d21120ac3e4fba3c72\",\n      \"image\": \"python:3.11-slim\",\n      \"image_id\": \"sha256:fa659464a114c340e31c7b7954a1aa679de7e7f5346e4b5804e8422b2596aff9\",\n      \"command\": \"python -c\",\n      \"args\": \"import time data = []\",\n      \"state\": \"Waiting\",\n      \"reason\": \"OOMKilled\",\n      \"last_state\": \"Terminated\",\n      \"exit_code\": \"137\",\n      \"started\": \"Thu, 21 May 2026 22:11:25 +0000\",\n      \"finished\": \"Thu, 21 May 2026 22:11:26 +0000\",\n      \"ready\": \"False\",\n      \"restart_count\": \"11\",\n      \"environment\": \"<none>\",\n      \"mounts\": \"\",\n      \"signals\": [\n        \"    Container ID:  containerd://deb3fe2a59e4fddd653c200b9b63e675090d967ead4762d21120ac3e4fba3c72\",\n        \"    Image:         python:3.11-slim\",\n        \"    Image ID:      sha256:fa659464a114c340e31c7b7954a1aa679de7e7f5346e4b5804e8422b2596aff9\",\n        \"    Command:\",\n        \"      python\",\n        \"      -c\",","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/014-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/014-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/014-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2810 lines=63\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2600\ntotal_chars: 2600\ncontent:\nkubectl_describe 摘要:\nname: rc-oomkilled-memory-limit-b6d999d-5f29d\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\nName:             rc-oomkilled-memory-limit-b6d999d-5f29d\nLabels:           app=rc-oomkilled-memory-limit\n                  pod_abnormal_type=OOMKilled\nAnnotations:      aiops.e2e/runbook: pod-oomkilled.md\nControlled By:  ReplicaSet/rc-oomkilled-memory-limit-b6d999d\n      Reason:       OOMKilled\n      Exit Code:    137\n  Normal   Scheduled       32m                    default-scheduler  Successfully assigned aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d to node1\n  Warning  BackOff         2m39s (x138 over 32m)  kubelet            Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-5f29d_aiops-e2e(2a0a6edf-c1a7-4057-abfb-be8ea3edfa50)\n      Reason:       CrashLoopBackOff\n                  cni.projectcalico.org/containerID: a31bbc9e3699735c3f9d3873265a2428dcff2f435ffcefe4489801098b253eda\n                  cni.projectcalico.org/podIP: 172.16.166.147/32\n                  cni.projectcalico.org/podIPs: 172.16.166.147/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-oomkilled-memory-limit-b6d999d\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://deb3fe2a59e4fddd653c200b9b63e675090d967ead4762d21120ac3e4fba3c72\n    Image:         python:3.11-slim\n    Image ID:      sha256:fa659464a114c340e31c7b7954a1aa679de7e7f5346e4b5804e8422b2596aff9\n    Command:\n      python\n      -c","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/015-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/015-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/015-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2119 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/002-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1909\ntotal_chars: 1909\ncontent:\nkubectl_describe pod dns-resolve-test (namespace=default, node=node2/10.2.0.50) shows Status=Pending, container state=Waiting(Reason=ErrImagePull). All 5 pull attempts to docker.io/library/busybox:1.36.1 failed with i/o timeout dialing different registry IPs (69.63.180.173, 159.138.20.20, 98.159.108.57, 199.59.150.45, 108.160.170.39) on port 443 - network connectivity to registry-1.docker.io is unreachable from node2. Pod has IP 172.16.104.1/32 via Calico. 20 ErrImagePull events over 3h1m.\nkey_facts: [\"pod: dns-resolve-test\", \"namespace: default\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container: dns-resolve-test\", \"image: busybox:1.36.1\", \"container state: Waiting, Reason: ErrImagePull\", \"Ready: False\", \"Restart Count: 0\", \"QoS Class: BestEffort\", \"pod IP: 172.16.104.1/32 (Calico)\", \"5 Failed pull events all show dial tcp <ip>:443: i/o timeout to registry-1.docker.io\", \"target IPs timed out: 69.63.180.173, 159.138.20.20, 98.159.108.57, 199.59.150.45, 108.160.170.39\", \"Error codes: DeadlineExceeded (x3) and Unknown (x2)\", \"Events: 20 occurrences of ErrImagePull over 3h1m\", \"Pulling event seen 19 times over 3h9m (still retrying)\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\"]\nconflicts: [\"current_summary says 'Failed 10m (x20 over 3h1m) Error: ErrImagePull' but raw_preview shows this event is separate from the individual Failed pull events with dial tcp messages; raw_preview has 7 total events (1 Pulling, 6 Failed) with the last Failed being Error: ErrImagePull. The structure is consistent but current_summary omits the Normal Pulling event (x19 over 3h9m).\"]\nmissing: [\"current_summary does not mention the Normal Pulling event (x19 over 3h9m) present in raw_preview\", \"current_summary omits pod IP 172.16.104.1/32\", \"current_summary omits Conditions (Initialized=True, PodScheduled=True)\", \"current_summary omits QoS Class: BestEffort\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/016-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/016-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/016-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1679 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/003-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1469\ntotal_chars: 1469\ncontent:\nPod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool is Waiting with Reason ImagePullBackOff, not Ready, restart count 0. Image pull repeatedly fails for registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0: two distinct network timeouts (DeadlineExceeded on europe-west2, Unknown desc on asia-east1) both dial tcp 142.250.157.82:443 i/o timeout. BackOff events: x897 over 6h37m.\nkey_facts: [\"resource: pod dig-tool, namespace: default\", \"node: node1/10.2.0.49\", \"pod status: Pending\", \"container dig-tool state: Waiting, Reason: ImagePullBackOff\", \"container Ready: False, Restart Count: 0\", \"image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"Warning Failed x11 over 6h34m: Failed to pull image - DeadlineExceeded, dial tcp 142.250.157.82:443: i/o timeout (europe-west2-docker.pkg.dev)\", \"Warning Failed x15 over 3h2m: Failed to pull image - Unknown desc, dial tcp 142.250.157.82:443: i/o timeout (asia-east1-docker.pkg.dev)\", \"Normal BackOff x897 over 6h37m: Back-off pulling image\"]\nconflicts: [\"current_summary says 'Warning Failed 37m (x11 over 6h34m)' and 'Warning Failed 7m10s (x15 over 3h2m)' — matches raw_preview, no conflict\", \"current_summary says 'Key Events: BackOff 2m32s (x897 over 6h37m)' — raw_preview confirms this, no conflict\"]\nmissing: [\"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\", \"PodIP: 172.16.166.157\", \"QoS Class: BestEffort\", \"service account: default\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/017-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/017-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/017-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1807 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/004-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1597\ntotal_chars: 1597\ncontent:\nPod curls in namespace mcp on node node2/10.2.0.50 is Pending. Container curls (image: curlimages/curl:7.88.1) is Waiting with Reason ErrImagePull. All 6 pull attempts to docker.io/curlimages/curl:7.88.1 failed due to i/o timeout dialing registry-1.docker.io (multiple IPs). Event: Failed x41 over 5h10m → Error: ErrImagePull. Pod has IP 172.16.104.2, QoS BestEffort, no environment, args run curl against registry.k8s.io.\nkey_facts: [\"pod: curls, namespace: mcp\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container curls: State Waiting, Reason ErrImagePull, Ready False, Restart Count 0\", \"image: curlimages/curl:7.88.1\", \"Container ID and Image ID are empty (not pulled)\", \"Events: Warning Failed x41 over 5h10m → Error: ErrImagePull\", \"6 pull failures, all i/o timeout dialing registry-1.docker.io:443 (IPs: 199.96.62.41, 104.244.46.85, 199.96.58.177, 199.59.149.206, 202.53.137.209, 168.143.162.58)\", \"rpc errors: DeadlineExceeded (5x), Unknown (1x)\", \"pod IP: 172.16.104.2\", \"container args: sh -c 'curl -sI -m5 https://registry.k8s.io/v2/ 2>&1 || echo FAILED'\", \"QoS Class: BestEffort\", \"no Node-Selectors\"]\nconflicts: [\"current_summary says 'Error: ErrImagePull' at 5m53s (x41) — raw_preview also shows this, consistent.\", \"current_summary omitted the Normal Pulling event (x39 over 5h13m) — not a conflict, just missing info.\"]\nmissing: [\"raw_preview shows container args (curl against registry.k8s.io) not mentioned in current_summary\", \"raw_preview shows Normal Pulling event (x39 over 5h13m) not in current_summary\", \"raw_preview shows pod IP (172.16.104.2) not in current_summary\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/018-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/018-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/018-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1565 lines=50\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/006-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1355\ntotal_chars: 1355\ncontent:\nkubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/019-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/019-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/019-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1456 lines=35\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/010-evidence-kubectl_get_yaml.summary.txt\noffset: 0\nreturned_chars: 1246\ntotal_chars: 1246\ncontent:\nkubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-resolve-test\nnamespace: default\ncreationTimestamp: 2026-05-21T19:02:58Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-resolve-test: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: nslookup registry-1.docker.io\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-resolve-test]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-resolve-test]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-resolve-test: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.170.39:443: i/o timeout\nvolumes:\n- {\"name\": \"kube-api-access-wst5b\"}\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/020-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/020-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/020-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1451 lines=35\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/009-evidence-kubectl_get_yaml.summary.txt\noffset: 0\nreturned_chars: 1241\ntotal_chars: 1241\ncontent:\nkubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: curls\nnamespace: mcp\ncreationTimestamp: 2026-05-21T16:59:07Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- curls: image=curlimages/curl:7.88.1 imagePullPolicy=IfNotPresent\n  args: sh -c curl -sI -m5 https://registry.k8s.io/v2/ 2>&1 || echo FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [curls]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [curls]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- curls: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/curlimages/curl:7.88.1\": failed to resolve reference \"docker.io/curlimages/curl:7.88.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/7.88.1\": dial tcp 168.143.162.58:443: i/o timeout\nvolumes:\n- {\"name\": \"kube-api-access-56mdx\"}\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/021-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/021-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/021-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"All 10 pods across namespaces mcp and default failed with ErrImagePull. Every pull attempt to docker.io (busybox:1.36.1, alpine:3.18, curlimages/curl:8.12.1) timed out dialing registry-1.docker.io:443 (i/o timeout). No successful pulls.\nkey_facts: [\"Namespace mcp: pods registry-diag-1779381627, net-check-tool, dns-check-tmp, node-debugger-node2-cztgc, curl-check-tmp, connectivity-test, node-debugger-node2-q6htb — all Failed/Warning, ErrImagePull\", \"Namespace default: pods dns-test-tmp, registry-conn-test-1779371220, registry-conn-test-evidence — all Failed/Warning, ErrImagePull\", \"Images attempted: busybox:1.36.1, alpine:3.18, curlimages/curl:8.12.1\", \"Error details: failed to pull/unpack image from docker.io — dial tcp {IP}:443 i/o timeout (DeadlineExceeded or Unknown desc variants)\", \"Destination: registry-1.docker.io:443 — multiple target IPs tried (168.143.162.58, 108.160.167.167) all timed out\", \"Returncode 0, command succeeded but all pulls failed\"]\nmissing: [\"No successful image pulls observed\", \"No events for non-Failed pods in these namespaces\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/022-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/022-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/022-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=3272 lines=94\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-evidence-kubectl_describe.raw.txt\noffset: 0\nreturned_chars: 3000\ntotal_chars: 4136\ncontent:\nName:             rc-oomkilled-memory-limit-b6d999d-5f29d\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             node1/10.2.0.49\nStart Time:       Thu, 21 May 2026 21:39:51 +0000\nLabels:           app=rc-oomkilled-memory-limit\n                  pod-template-hash=b6d999d\n                  pod_abnormal_type=OOMKilled\n                  rootcause-e2e=true\nAnnotations:      aiops.e2e/runbook: pod-oomkilled.md\n                  cni.projectcalico.org/containerID: a31bbc9e3699735c3f9d3873265a2428dcff2f435ffcefe4489801098b253eda\n                  cni.projectcalico.org/podIP: 172.16.166.147/32\n                  cni.projectcalico.org/podIPs: 172.16.166.147/32\n                  k8s.v1.cni.cncf.io/network-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.166.147\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\n                  k8s.v1.cni.cncf.io/networks-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.166.147\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\nStatus:           Running\nIP:               172.16.166.147","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/023-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/023-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/023-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1345 lines=19\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/2c759dc672914c34/tools/001-evidence-kubectl_describe.raw.txt\noffset: 3000\nreturned_chars: 1136\ntotal_chars: 4136\ncontent:\n     <none>\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason          Age                    From               Message\n  ----     ------          ----                   ----               -------\n  Normal   Scheduled       32m                    default-scheduler  Successfully assigned aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d to node1\n  Normal   AddedInterface  32m                    multus             Add eth0 [172.16.166.147/32] from k8s-pod-network\n  Normal   Pulled          31m (x5 over 32m)      kubelet            Container image \"python:3.11-slim\" already present on machine\n  Normal   Created         31m (x5 over 32m)      kubelet            Created container app\n  Normal   Started         31m (x5 over 32m)      kubelet            Started container app\n  Warning  BackOff         2m39s (x138 over 32m)  kubelet            Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-5f29d_aiops-e2e(2a0a6edf-c1a7-4057-abfb-be8ea3edfa50)\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/024-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/024-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c759dc672914c34/tools/024-evidence-read_context_archive.summary.txt"}],"llm_analysis":"## 已有工具结果完整分析\n\n所有关键工具已调用完毕。以下是基于所有真实工具结果汇总的证据结论。\n\n---\n\n## 📋 证据采集结论\n\n### ✅ 已采集证据\n\n#### 【异常组 g2 — 主异常】镜像拉取失败（22 ErrImagePull + 27 ImagePullBackOff）\n| 证据项 | 来源 | 关键内容 |\n|--------|------|---------|\n| **g2-e1** `dns-resolve-test` (default, node2) | `kubectl describe` | 镜像 `busybox:1.36.1`，5次拉取全部 `dial tcp <ip>:443: i/o timeout` 到 `registry-1.docker.io`，20次 ErrImagePull 事件持续 3h1m |\n| **g2-e2** `dig-tool` (default, node1) | `kubectl describe` | 镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，超时 `dial tcp 142.250.157.82:443: i/o timeout`（europe-west2 + asia-east1），BackOff x897 |\n| **g2-e3** `curls` (mcp, node2) | `kubectl describe` | 镜像 `curlimages/curl:7.88.1`，6次 `i/o timeout` 到 `registry-1.docker.io`（6个不同IP），Failed x41 |\n| **g2-e4** `dns-resolve-test` YAML (default) | `kubectl_get_yaml` | 镜像: `busybox:1.36.1`，**无 imagePullSecrets**，错误信息：`dial tcp 108.160.170.39:443: i/o timeout` |\n| **g2-e5** `curls` YAML (mcp) | `kubectl_get_yaml` | 镜像: `curlimages/curl:7.88.1`，**无 imagePullSecrets**，错误信息：`dial tcp 168.143.162.58:443: i/o timeout` |\n| **g2-e6** 全集群镜像拉取失败事件 | `run_bash_command (events)` | 10 个 Pod（mcp + default）全部 `ErrImagePull`，所有尝试 `docker.io`/`registry.k8s.io` 均 i/o timeout，无一次成功拉取 |\n\n**核心发现**：集群节点（node1 和 node2）均无法访问 `registry-1.docker.io:443`，域名解析成功（DNS 能解出不同 IP），但 TCP 连接全部超时。同时 `registry.k8s.io` 也超时。不存在镜像名/tag错误或认证失败问题，根因是**出口网络无法到达外部镜像仓库**。\n\n---\n\n#### 【异常组 g1 — 次异常】OOMKilled / CrashLoopBackOff\n| 证据项 | 来源 | 关键内容 |\n|--------|------|---------|\n| **g1-e1** `rc-oomkilled-memory-limit` (aiops-e2e) | `kubectl describe` | Last State: **OOMKilled**, Exit Code: **137**, Restart Count: **11**，QoS Class: Burstable，镜像 `python:3.11-slim` 已在本地存在 |\n| **g1-e2** 日志（当前+previous） | `kubectl logs` / `logs --previous` | 当前日志和 previous 日志均无输出（容器启动后立即 OOM 退出） |\n\n**核心发现**：这是一个独立的 L2 异常——容器 `python:3.11-slim` 执行 `python -c \"import time data = []\"` 因 **memory limit 超限**而被 OOMKilled。与镜像拉取故障无关。\n\n---\n\n#### 【异常组 g3 — 最小验证】StartError\n| 证据项 | 来源 | 关键内容 |\n|--------|------|---------|\n| **g3-e1** `node-debugger-node1-nx8gb` (mcp) | `kubectl describe` | Status: **Failed**，Reason: **StartError**，Exit Code: **128**，Message: `exec: \"curl\": executable file not found in $PATH: unknown` — 镜像 `busybox:1.36` 中无 `curl` 二进制文件 |\n\n**核心发现**：Pod 配置错误——镜像 `busybox:1.36` 不包含 `curl` 命令，但 Pod command 指定了 `curl`。这是 L4 配置错误，不是网络问题。已成功拉取镜像（Image ID 已存在），但无法启动。\n\n---\n\n### ❌ 未采集证据 / 冲突证据\n- **无冲突证据**——所有计划中的 Pod 均存在于指定 namespace，工具均成功返回结果。\n- **events 全局查询**：`kubectl get events --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff` 返回空，原因是当前 Kubernetes 版本可能使用 `reason=Failed` + 子消息描述而非独立 Reason；已通过 grep 方式获取到完整失败事件。\n\n---\n\n### 🎯 根因总结\n\n**首要问题（L3 — 影响范围49个Pod）**：集群出口网络无法访问 `registry-1.docker.io:443` 和 `registry.k8s.io`，导致所有需要从外部仓库拉取镜像的 Pod 全部失败（ErrImagePull / ImagePullBackOff）。DNS 解析正常，但 TCP 连接在 443 端口全部 i/o timeout。影响 node1 和 node2 两个节点。\n\n**次要问题（L2 — 孤立Pod）**：`aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d` 因 memory limit 超限反复 OOMKilled（exit 137）。\n\n**个例问题（L4 — 配置错误）*","collection_summary":"计划 9 项，实际采集 8 项，未采集 1 项，完整度 89%；其中真实环境证据 15/16 项，完整度 94%；实际执行工具 20 个，匹配计划 8 个，未规划证据 12 个","plan_total":9,"plan_collected":8,"plan_completeness":0.8888888888888888,"environment_evidence_total":16,"environment_evidence_collected":15,"environment_evidence_completeness":0.9375,"executed_tool_count":20,"matched_tool_count":8,"unplanned_tool_count":12,"evidence_inventory":[{"id":"g1-e1","description":"完整验证 g1 (CrashLoopBackOff): describe Pod rc-oomkilled-memory-limit-b6d999d-5f29d 查看 Last State/Exit Code/Restarts/Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-oomkilled-memory-limit-b6d999d-5f29d","purpose":"获取 OOMKilled/CrashLoopBackOff Pod 的 Last State Exit Code、Events 和 Restart 次数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-e2","description":"CrashLoopBackOff: 查看 previous logs 确认 OOM 或其他错误","level":"critical","tool":"kubectl_logs","command":"kubectl logs -n aiops-e2e rc-oomkilled-memory-limit-b6d999d-5f29d --previous","purpose":"获取容器上次 crash 的日志输出确认 OOM 或应用错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e1","description":"主异常组 g2 (ErrImagePull/ImagePullBackOff): describe 代表 Pod（跨 node1/node2）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dns-resolve-test","purpose":"获取 ErrImagePull Pod 的 Events 和镜像错误详情，验证 i/o timeout 错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e2","description":"主异常组 g2: describe 另一个代表 Pod 在 node1 上（node1 代表）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dig-tool","purpose":"获取 ImagePullBackOff Pod 的 Events 和镜像错误详情","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e3","description":"主异常组 g2: describe mcp namespace 代表 Pod","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp curls","purpose":"获取 mcp namespace ErrImagePull Pod 的 Events 和镜像错误详情","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e4","description":"查看 g2 组 Pod 的 spec.image 确认镜像来源","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n default dns-resolve-test -o yaml","purpose":"检查镜像地址和 imagePullSecrets 配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e5","description":"查看 mcp namespace 代表 Pod 的 spec.image","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n mcp curls -o yaml","purpose":"检查 mcp 命名空间下 Pod 的镜像地址和 imagePullSecrets","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e6","description":"查看 namespace 级别的 events，确认镜像拉取失败相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by=.lastTimestamp 2>/dev/null | tail -30","purpose":"采集集群中所有镜像拉取失败的事件摘要","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-e1","description":"最小验证 g3 (StartError): describe pod node-debugger-node1-nx8gb","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp node-debugger-node1-nx8gb","purpose":"获取 StartError Pod 的当前状态和 Events 确认错误详情","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["g3-e1(最小验证 g3 (StartError): describe pod node-debugger-node1-nx8gb): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/9 项, 完整度: 94%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-e1 | critical | ✅ | kubectl_describe | 完整验证 g1 (CrashLoopBackOff): describe Pod rc-o... | `kubectl describe pod -n aiops-e2e rc-oomkilled-memory-limit-b6d999d-5f29d` |
   | g1-e2 | critical | ✅ | kubectl_logs | CrashLoopBackOff: 查看 previous logs 确认 OOM 或其他错误 | `kubectl logs -n aiops-e2e rc-oomkilled-memory-limit-b6d999d-5f29d --previous` |
   | g2-e1 | critical | ✅ | kubectl_describe | 主异常组 g2 (ErrImagePull/ImagePullBackOff): desc... | `kubectl describe pod -n default dns-resolve-test` |
   | g2-e2 | critical | ✅ | kubectl_describe | 主异常组 g2: describe 另一个代表 Pod 在 node1 上（node1 代表） | `kubectl describe pod -n default dig-tool` |
   | g2-e3 | important | ✅ | kubectl_describe | 主异常组 g2: describe mcp namespace 代表 Pod | `kubectl describe pod -n mcp curls` |
   | g2-e4 | important | ✅ | kubectl_get_yaml | 查看 g2 组 Pod 的 spec.image 确认镜像来源 | `kubectl get pod -n default dns-resolve-test -o yaml` |
   | g2-e5 | important | ✅ | kubectl_get_yaml | 查看 mcp namespace 代表 Pod 的 spec.image | `kubectl get pod -n mcp curls -o yaml` |
   | g2-e6 | important | ✅ | kubectl_events | 查看 namespace 级别的 events，确认镜像拉取失败相关事件 | `kubectl get events --all-namespaces --field-selector reason=FailedToPullImage...` |
   | g3-e1 | important | ❌ | kubectl_describe | 最小验证 g3 (StartError): describe pod node-debug... | `kubectl describe pod -n mcp node-debugger-node1-nx8gb` |

   ⚠️ 未采集原因:
   - g3-e1(最小验证 g3 (StartError): describe pod node-debugger-node1-nx8gb): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.6s)
   📤 → 下游数据: root_cause=主根因（L3 层）：集群节点（node1 和 node2）到外部镜像仓库的出口网络连接中断。证据表明：DNS 解析正常（registry-1.docker.io 成功解析出 69.63.180.173、159.138.20.20 等多个 IP），但所有 TCP 连接 443 端口均 i/o timeout。Pod dns-resolve-test（default/node2）5 次拉取 busybox:1.36.1 全部超时；Pod dig-tool（default/node1）拉取 registry.k8s.io 镜像同样 i/o timeout（BackOff x897/6h37m）；Pod curls（mcp/node2）6 次尝试 curlimages/curl 全部超时（Failed x41/5h10m）。跨 namespace（aiops-e2e、default、mcp）、跨节点（node1、node2）、跨镜像仓库（docker.io、registry.k8s.io）一致失败，排除 DNS 故障、镜像名错误、imagePullSecret 缺失等场景。次异常（L2 层）：
... 截断，原始 668 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1、node2）到外部镜像仓库（registry-1.docker.io、registry.k8s.io）的出口网络连接全部超时，导致 49 个 Pod 镜像拉取失败", "propagation": "集群出口网络不通 → kubelet 无法从 registry-1.docker.io:443 拉取镜像 → 容器状态变为 Waiting(ErrImagePull) → 重试机制触发 ImagePullBackOff（指数退避）→ 49 个 Pod 持续 Pending，其中 27 个进入 ImagePullBackOff、22 个停留在 ErrImagePull", "direct_cause": "节点无法建立到 registry-1.docker.io:443 的 TCP 连接，DNS 解析正常但 TCP 握手超时", "manifestation": "aiops-e2e/default/mcp 三个 namespace 共 49 个 Pod 处于 Pending 状态，容器状态为 ErrImagePull/ImagePullBackOff，kubelet Events 反复报告 'dial tcp <ip>:443: i/o timeout'"}
   rca_analysis={"phenomenon": "集群存在 51 个异常 Pod：27 个 ImagePullBackOff、22 个 ErrImagePull、1 个 CrashLoopBackOff（含 OOMKilled 历史）、1 个 StartError。主异常（49 个 Pod）均处于 Pending 状态，分布在 default、mcp、aiops-e2e 三个 namespace，涉及 node1 和 node2 两个节点。", "evidence_inventory": [{"id": "g2-e1", "source": "kubectl_describe pod dns-resolve-test (default, node2)", "content": "镜像 busybox:1.36.1，5 次拉取全部 i/o timeout 到 registry-1.docker.io，20 次 ErrImagePull 事件持续 3h1m", "reliability": "高"}, {"id": "g2-e2", "source": "kubectl_describe pod dig-tool (default, node1)", "content": "镜像 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，i/o timeout 到 142.250.157.82:443，BackOff x897", "reliability": "高"}, {"id": "g2-e3", "source": "kubectl_describe pod curls (mcp, node2)", "content": "镜像 curlimages/curl:7.88.1，6 次 i/o timeout 到 registry-1.docker.io，Failed x41", "reliability": "高"}, {"id": "g2-e4", "source": "kubectl_get_yaml curls", "content": "imagePullSecrets 为空，容器状态 ErrImagePull，错误 dial tcp 168.143.162.58:443: i/o timeout", "reliability": "高"}, {"id": "g2-e5", "source": "kubectl_get_yaml dns-resolve-test", "content": "imagePullSecrets 为空，容器状态 ErrImagePull，错误 dial tcp 108.160.170.39:443: i/o timeout", "reliability": "高"}, {"id": "g1-e1", "source": "kubectl_describe rc-oomkilled-memory-limit (aiops-e2e, node1)", "content": "Last State OOMKilled, Exit Code 137, Restarts 11, 当前 CrashLoopBackOff", "reliability": "高"}, {"id": "g1-e2", "source": "kubectl_logs + kubectl_previous_logs", "content": "当前日志和 previous 日志均无输出", "reliability": "高"}, {"id": "g3-e1", "source": "kubectl_describe node-debugger-node1-nx8gb (mcp, node1)", "content": "StartError: exec 'curl' not found in $PATH, 镜像 busybox:1.36 不包含 curl 命令", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "78 Pods, 51 abnormal: CrashLoopBackOff=1, OOMKilled=1, ErrImagePull=22, ImagePullBackOff=27", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "g2-e1", "raw_data": "5 pull attempts to docker.io/library/busybox:1.36.1 failed with i/o timeout dialing different registry IPs (69.63.180.173, 159.138.20.20, 98.159.108.57, 199.59.150.45, 108.160.170.39) on port 443", "interpretation": "DNS 解析 registry-1.docker.io 成功（能解出多个不同 IP），但 TCP 连接 443 端口全部超时，说明集群出口网络到 docker.io 不可达"}, {"evidence_id": "g2-e2", "raw_data": "dig-tool image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 — DeadlineExceeded on europe-west2, Unknown desc on asia-east1 both dial tcp 142.250.157.82:443 i/o timeout. BackOff x897 over 6h37m", "interpretation": "不仅 docker.io 不可达，registry.k8s.io（GCR 镜像）也同样 i/o timeout，说明问题不是单一镜像仓库故障，而是整体外部网络出口问题"}, {"evidence_id": "g2-e3", "raw_data": "curls image curlimages/curl:7.88.1 — 6 pull failures all i/o timeout dialing registry-1.docker.io:443 (6 different IPs). Failed x41 over 5h10m", "interpretation": "从 mcp namespace 的 Pod 验证同样超时，跨 namespace 一致，排除 namespace 级别的网络策略限制"}, {"evidence_id": "g2-e4", "raw_data": "imagePullSecrets: <absent> ; message: dial tcp 168.143.162.58:443: i/o timeout", "interpretation": "Pod 未配置 imagePullSecrets，但错误类型是 i/o timeout 而非认证失败（401/403），排除 imagePullSecret 缺失场景"}, {"evidence_id": "g2-e5", "raw_data": "imagePullSecrets: <absent> ; message: dial tcp 108.160.170.39:443: i/o timeout", "interpretation": "另一 Pod 同样无 imagePullSecrets，错误仍是 i/o timeout，进一步确认非认证问题"}, {"evidence_id": "g1-e1", "raw_data": "Last State: OOMKilled, Exit Code: 137, Restarts: 11, QoS Class: Burstable", "interpretation": "容器因内存超限被 OOMKill（Exit Code 137 为 SIGKILL），独立于镜像拉取故障"}, {"evidence_id": "g1-e2", "raw_data": "logs: (no output)", "interpretation": "容器启动后立即 OOM 退出，无日志输出，符合 OOMKilled 特征"}, {"evidence_id": "g3-e1", "raw_data": "StartError: failed to create shim task: exec: 'curl': executable file not found in $PATH", "interpretation": "Pod 使用 busybox:1.36 镜像但指定 command 'curl'，而 busybox 镜像不包含 curl 可执行文件，属于镜像/命令不匹配的配置错误"}], "causal_chain": {"root_cause": "集群节点（node1、node2）到外部镜像仓库（registry-1.docker.io、registry.k8s.io）的出口网络连接全部超时，导致 49 个 Pod 镜像拉取失败", "propagation": "集群出口网络不通 → kubelet 无法从 registry-1.docker.io:443 拉取镜像 → 容器状态变为 Waiting(ErrImagePull) → 重试机制触发 ImagePullBackOff（指数退避）→ 49 个 Pod 持续 Pending，其中 27 个进入 ImagePullBackOff、22 个停留在 ErrImagePull", "direct_cause": "节点无法建立到 registry-1.docker.io:443 的 TCP 连接，DNS 解析正常但 TCP 握手超时", "manifestation": "aiops-e2e/default/mcp 三个 namespace 共 49 个 Pod 处于 Pending 状态，容器状态为 ErrImagePull/ImagePullBackOff，kubelet Events 反复报告 'dial tcp <ip>:443: i/o timeout'"}, "root_cause": "主根因（L3 层）：集群节点（node1 和 node2）到外部镜像仓库的出口网络连接中断。证据表明：DNS 解析正常（registry-1.docker.io 成功解析出 69.63.180.173、159.138.20.20 等多个 IP），但所有 TCP 连接 443 端口均 i/o timeout。Pod dns-resolve-test（default/node2）5 次拉取 busybox:1.36.1 全部超时；Pod dig-tool（default/node1）拉取 registry.k8s.io 镜像同样 i/o timeout（BackOff x897/6h37m）；Pod curls（mcp/node2）6 次尝试 curlimages/curl 全部超时（Failed x41/5h10m）。跨 namespace（aiops-e2e、default、mcp）、跨节点（node1、node2）、跨镜像仓库（docker.io、registry.k8s.io）一致失败，排除 DNS 故障、镜像名错误、imagePullSecret 缺失等场景。次异常（L2 层）：\n... 截断，原始 668 字符", "root_cause_summary": "主根因（L3 层）：集群节点（node1 和 node2）到外部镜像仓库的出口网络连接中断。证据表明：DNS 解析正常（registry-1.docker.io 成功解析出 69.63.180.173、159.138.20.20 等多个 IP），但所有 TCP 连接 443 端口均 i/o timeout。Pod dns-resolve-test（default/node2）5 次拉取 busybox:1.36.1 全部超时；Pod dig-tool（default/node1）拉取 registry.k8s.io 镜像同样 i/o timeout（BackOff x897/6h37m）；Pod curls（mcp/node2）6 次尝试 curlimages/curl 全部超时（Failed x41/5h10m）。跨 namespace（aiops-e2e、default、mcp）、跨节点（node1、node2）、跨镜像仓库（docker.io、registry.k8s.io）一致失败，排除 DNS 故障、镜像名错误、imagePullSecret 缺失等场景。次异常（L2 层）：\n... 截断，原始 668 字符", "confidence": 0.95, "confidence_reason": "直接证据充分：跨 3 个 namespace、2 个节点、3 种镜像仓库（docker.io、registry.k8s.io、curlimages）的 Pod 描述和 YAML 均一致显示 i/o timeout，DNS 解析成功但 TCP 连接超时，因果链清晰完整。g1（OOMKilled）和 g3（StartError）独立验证完毕且有明确证据。", "primary_runbooks": [], "alternative_causes": [{"cause": "镜像名或 tag 不存在导致拉取失败", "probability": "low", "reason": "错误信息明确为 i/o timeout，不是 'not found' 或 'manifest unknown'，排除"}, {"cause": "imagePullSecret 缺失或认证失败", "probability": "low", "reason": "Pod YAML 确认无 imagePullSecrets，但错误类型是网络超时（i/o timeout）而非认证拒绝（401/403），排除"}, {"cause": "集群 DNS 解析异常导致无法解析镜像仓库域名", "probability": "low", "reason": "DNS 解析成功（每个 Pod 的超时报文中 registry-1.docker.io 解析出不同的目标 IP），表明 DNS 正常工作"}, {"cause": "CNI 网络组件故障", "probability": "low", "reason": "Calico 正常工作（Pod 均成功获取到 172.16.x.x/32 IP 且已调度到节点），CNI 本身未报错"}, {"cause": "镜像仓库本身故障", "probability": "low", "reason": "跨三个不同仓库（docker.io、registry.k8s.io、curlimages）一致超时，概率极低"}], "limitations": "未在节点上直接执行 curl 或 ping 验证出口网络（需节点级 shell 权限）；未检查集群代理（HTTP_PROXY）或网络出口防火墙规则；未验证 containerd/cri-o 的 mirror 配置；g3（StartError）描述已由 kubectl_describe 覆盖，但无独立工具验证其当前状态是否已恢复。", "llm_raw_analysis": "## 证据清点\\n共采集 13 项证据，其中 g2 组（主异常组）7 项、g1 组 2 项、g3 组 1 项、上游工具汇总 3 项。\\n\\n## 逐条分析\\n- g2-e1/g2-e2/g2-e3：跨 node1/node2、跨 namespace default/mcp、跨镜像 docker.io/registry.k8s.io/curlimages，全部 i/o timeout。5+2+6=13 次拉取尝试全部超时，不同 IP 不同超时时间点。\\n- g2-e4/g2-e5：YAML 确认无 imagePullSecrets，但错误是 i/o timeout 而非认证失败。\\n- g1-e1：OOMKilled Exit Code 137，11 次重启，独立于网络问题。\\n- g1-e2：无日志输出，符合 OOM。\\n- g3-e1：StartError 源自 busybox 无 curl 命令。\\n\\n## 关联分析\\ng2 组所有证据指向同一个根因：出口网络不通。DNS 能解析但 TCP 不通，且跨仓库、跨节点、跨 namespace 一致，排除了局部问题。g1 完全独立。g3\n... 截断，原始 616 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 主根因（L3 层）：集群节点（node1 和 node2）到外部镜像仓库的出口网络连接中断。证据表明：DNS 解析正常（registry-1.docker.io 成功解析出 69.63.180.173、159.138.20.20 等多个 IP），但所有 TCP 连接 443 端口均 i/o time...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1、node2）到外部镜像仓库（registry-1.docker.io、registry.k8s.io）的出口网络连接全部超时，导致 49 个 Pod 镜像拉取失败
     传导机制: 集群出口网络不通 → kubelet 无法从 registry-1.docker.io:443 拉取镜像 → 容器状态变为 Waiting(ErrImagePull) → 重试机制触发 ImagePullBackOff（指数退避）→ 49 个 Pod 持续 Pending，其中 27 个进入 ImagePullBackOff、22 个停留在 ErrImagePull
     最终表现: aiops-e2e/default/mcp 三个 namespace 共 49 个 Pod 处于 Pending 状态，容器状态为 ErrImagePull/ImagePullBackOff，kubelet Events 反复报告 'dial tcp <ip>:443: i/o timeout'


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (32.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 9580 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 31.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的全面诊断数据，为您生成一份详尽、完整的集群问题诊断报告。

---

## 📊 诊断概览

**核心问题回答**：您的集群当前存在 **严重的网络连通性故障**，导致绝大多数（49/78）Pod 无法正常启动，同时存在一个因内存不足（OOM）而反复重启的特定 Pod。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff (1个), OOMKilled (1个), ErrImagePull (22个), ImagePullBackOff (27个) |
| **兼容归因层** | L3 - 镜像/网络问题 |
| **问题分类** | **主要问题**: 集群节点无法访问外部镜像仓库（Network Timeout）；**次要问题**: Pod 内存限制不足 (OOMKilled) |
| **置信度** | **高 (95%)** |
| **证据完整度** | 8/9 (89%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 集群范围 | 78 个 Pod 中，51 个处于异常状态，27 个正常运行 |
| 核心异常 Namespace | `default`, `mcp`, `aiops-e2e` |
| 受影响 Node | `node1`, `node2` |
| 核心异常 Pod (L3) | `dns-resolve-test`, `dig-tool`, `curls`, `registry-diag-*` 等 49 个 Pod |
| 核心异常 Pod (L2) | `rc-oomkilled-memory-limit-b6d999d-5f29d` |
| 其他异常 | `node-debugger-node1-nx8gb` (StartError) |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 (摘要) | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | **集群Pod概览** | `kubectl_get_by_kind_in_cluster` | 78 Pods: 51 abnormal. **ErrImagePull:22, ImagePullBackOff:27**, OOMKilled:1, CrashLoopBackOff:1. Running:27. | 集群存在两大类异常(网络瘫痪 & 内存不足)，且与系统组件无关。 |
| 2 | **异常Pod数量** | `kubernetes_tabular_query` | **49 个 Pod 全部处于 Pending 状态**，分布在 `aiops-e2e`, `default`, `mcp` Namespace。 | 确认大规模 Pod 启动失败，核心原因是镜像拉取失败。 |
| 3 | **镜像拉取失败原因** | `kubectl_describe` (Pod: `dns-resolve-test`) | `Status=Pending`, `Reason=ErrImagePull`。5次拉取 `docker.io/library/busybox:1.36.1` 全部失败。**失败消息: `dial tcp <ip>:443: i/o timeout`**，连接 `registry-1.docker.io` 超时。 | **确认网络层故障**：节点无法与 Docker Hub 建立 TCP 连接，而非 DNS 或认证问题。 |
| 4 | **跨仓库/跨节点验证** | `kubectl_describe` (Pod: `dig-tool`) | `ImagePullBackOff`。拉取 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` 失败。同样**`dial tcp 142.250.157.82:443: i/o timeout`**。Pod 运行在 node1。 | **排除特定仓库问题**：问题不限于 Docker Hub，也影响 `registry.k8s.io`。 |
| 5 | **跨Namespace验证** | `kubectl_describe` (Pod: `curls`) | `ErrImagePull`。拉取 `curlimages/curl:7.88.1` 失败。失败消息：`i/o timeout dialing registry-1.docker.io`。Pod 运行在 node2 的 `mcp` namespace。 | **排除Namespace隔离**：问题在 `default` 和 `mcp` 命名空间同时存在，是集群级的网络问题。 |
| 6 | **事件层确认** | `run_bash_command` (Namespace Events) | 仅 `mcp` Namespace 的事件就包含大量 `Warning Failed pod/registry-diag-* Error: ErrImagePull` 事件。 | 大量重复的镜像拉取失败事件，与 Pod 状态一致。 |
| 7 | **OOMKilled Pod 诊断** | `kubectl_describe` (Pod: `rc-oomkilled-*`) | `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`。**Back-off restarting failed container (x138 over 32m)**。 | 确认该Pod因内存超限被OOM Killer杀死，并持续重启。 |
| 8 | **OOMKilled Pod 日志** | `kubectl_logs` / `kubectl_previous_logs` | 日志输出为空。 | 可能是由于OOM瞬间发生，进程来不及输出日志，或日志被截断。 |
| 9 | **Pod YAML 验证** | `kubectl_get_yaml` | Pod `curls` 和 `dns-resolve-test` 均显示 `finalizers: <none>`, `terminationGracePeriodSeconds: 30`。 | **明确排除 “finalizer 未清理” 作为任何 Pod 的根因。** |

### 证据关联分析
- **证据 #2, #3, #4, #5, #6 印证**：所有证据都指向一个共同结论——集群节点（node1和node2）无法建立到外部镜像仓库（如 `registry-1.docker.io`, `registry.k8s.io`）的 TCP 连接。49 个处于 ErrImagePull/ImagePullBackOff 状态的 Pod 是其直接后果。
- **证据链**：集群出口网络不通 → kubelet 无法拉取镜像 → Pod 容器无法启动 → 状态变为 `ErrImagePull` → 重试机制触发 `ImagePullBackOff` → 最终表现为 49 个 Pod 持续 Pending。
- **证据 #7, #8 印证**：`aiops-e2e` 命名空间下的 Pod `rc-oomkilled-memory-limit-*` 的问题与上述网络问题无关，是一个独立的内存不足问题。
- **证据 #9 排除干扰**：明确排除了 finalizer 导致 Pod 删除阻塞的可能性，确认集群问题根源在网络层。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| **g3-e1**: Pod `node-debugger-node1-x` 的 `kubectl_describe` | important | 无法确认该 Pod `StartError` 的根本原因。根据已采集的证据，`StartError` 可能是底层容器运行时（containerd）的问题，或网络故障导致的连锁反应。 |
| **节点层面网络诊断** | critical | 未在 Node 层面执行 `ping` 或 `curl` 验证，无法判断问题出在防火墙规则、代理配置还是底层网络。 |

---

## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                             根本原因: 集群出口网络中断                                          │
│ 集群节点 (node1, node2) 无法建立到外部镜像仓库 (registry-1.docker.io, registry.k8s.io)          │
│ 的 TCP (443端口) 连接。 (证据 #3, #4, #5)                                                     │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                         ↓
                             传导机制: Kubernetes 镜像拉取流程
           Kubelet 尝试拉取镜像 -> TCP 连接超时 -> 镜像拉取失败 -> 触发指数退避重试
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                        直接原因: 镜像拉取失败 (ErrImagePull / ImagePullBackOff)                │
│ 所有镜像拉取请求均因 `i/o timeout` 失败，容器状态卡在 `Waiting`。 (证据 #3, #4)                │
└──────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                        ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                          用户可见现象: 大规模 Pod 处于 Pending 状态                            │
│ **49个 Pod** 分布在 `default`, `mcp`, `aiops-e2e` 命名空间，持续处于 `Pending` 状态。           │
│ (证据 #2)                                                                                     │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                              (独立分支)
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                             次要问题: 单个 Pod 内存超限                                        │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                         ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                             直接原因: OOMKilled (Exit Code 137)                                │
│ `rc-oomkilled-memory-limit-*` Pod 因内存使用超出限制，被 cgroup OOM Killer 终止。 (证据 #7)    │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论-主要问题**: 根据证据 `#1` 到 `#6`，问题的根本原因是**集群节点（node1 和 node2）到外部镜像仓库（registry-1.docker.io, registry.k8s.io）的出口网络连接中断**。这导致所有需要从外部仓库拉取镜像的 Pod（49个）持续处于 `ErrImagePull` 或 `ImagePullBackOff` 状态，无法启动。

**结论-次要问题**: 根据证据 `#7`，这是一个独立的内存问题。Pod `rc-oomkilled-memory-limit-b6d999d-5f29d` 的根本原因是**容器的内存限制（可能为 256Mi）不足以满足应用的运行需求**，导致被 OOM Killer 杀死并持续重启。

**置信度**：**高 (95%)**
- ✅ **多个跨Namespace、跨节点、跨镜像仓库的Pod** 报错信息完全一致，均指向 `i/o timeout`，证据链完整且无矛盾。
- ✅ 已通过 `kubectl_get_yaml` 明确排除了`finalizer`和`TerminationGracePeriod`等常见干扰项。
- ⚠️ 缺少节点层面（如 `iptables`、`HTTP_PROXY`环境变量或 containerd 配置）的直接证据，无法确定网络中断的具体原因。

---

## 🛠️ 修复建议

**警告**：在执行任何修复前，请先解决主要问题，集群才能恢复。次要问题可以同步处理。

### 主要问题：修复出口网络连通性

**核心思路**：集群节点无法连接到外部网络。这可能由防火墙规则、代理配置、底层网络设备或 DNS 解析（虽然看起来没问题）等多种原因导致。请按顺序排查以下命令的执行结果。

**1. [优先] 在节点上测试网络连通性**
请登录到 `node1` 或 `node2`，执行以下命令，并将结果告知集群管理员或网络团队。

```bash
# 尝试直接解析域名
ping registry-1.docker.io -c 3

# 尝试直接连接 docker hub 的 443 端口
nc -zv registry-1.docker.io 443
# 或
timeout 10 curl -v https://registry-1.docker.io/v2/ 

# 检查是否存在 HTTP 代理环境变量
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

*依据*：这些是验证网络层连通性的命令行基础操作，可以快速定位问题是否在节点本身。
*预期结果*：如果能 `ping` 通但 `nc` 或 `curl` 失败，则问题在出口防火墙或代理。
*如果命令不适用*：上述命令在某些基础镜像中可能不存在。请根据集群实际操作系统使用替代命令（如 `telnet`, `wget`）。

**2. [次优] 检查节点 containerd/cri-o 配置**
在节点上检查容器运行时的镜像代理或 mirror 配置。

```bash
# 如果使用 containerd
cat /etc/containerd/config.toml | grep -A 10 "\[plugins.\"io.containerd.grpc.v1.cri\".registry\]"

# 如果使用 crio
cat /etc/crio/crio.conf | grep -A 5 "registries"
```
*检查点*：确认是否有配置 mirror 或代理，以及这些配置是否正确指向了可用的内部仓库。

**3. [临时规避] 使用内部镜像仓库**
如果无法快速修复网络问题，可以考虑将所有所需的镜像（如 `busybox:1.36.1`）拉取到内部仓库（如 Harbor），然后修改 Pod 的 `image` 字段引用内部仓库地址。

```bash
# 示例：修改 Pod 的镜像（前提是内部仓库已推入该镜像）
kubectl patch pod <pod-name> -p '{"spec":{"containers":[{"name":"dns-resolve-test","image":"<your-internal-registry>/library/busybox:1.36.1"}]}}' 
```

### 次要问题：修复 OOMKilled Pod

**1. [优先] 增加内存限制**
此修改将触发 Pod 滚动更新。

```bash
# 获取当前 deployment 的内存限制（如果有的话）
kubectl get deployment -n aiops-e2e rc-oomkilled-memory-limit -o yaml | grep -A5 'limits:'

# 假设部署名称为 rc-oomkilled-memory-limit，将内存限制从当前值（假设为256Mi）提升到512Mi
kubectl set resources deployment/rc-oomkilled-memory-limit -n aiops-e2e --limits=memory=512Mi
```
*依据*：根据 Exit Code 137 和 OOMKilled 状态，增加资源限制是直接有效的解决方案。
*如果命令失败*：请先确认 Deployment 名称是否正确。如果 Pod 不属于 Deployment，请使用 `kubectl edit` 命令手动修改 Pod 或其他控制器。

**2. [后续] 分析内存增长原因**
在 Pod 稳定运行后，连接到 Pod 内部或查看监控数据，分析内存消耗的来源。

```bash
# 等 Pod 再次运行后，查看其实时内存使用
kubectl exec -it -n aiops-e2e rc-oomkilled-memory-limit-b6d999d-5f29d -- top

# 或通过 kubectl top pod 查看（如果此命令在您的环境中可用）
kubectl top pod rc-oomkilled-memory-limit-* -n aiops-e2e
```

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 验证网络 | 在节点上执行 `netstat -r` 或查看路由表 | 确认有到外网的默认路由 |
| 2. 验证网络 | 在节点上执行 `curl -v https://registry-1.docker.io/v2/` | 返回 `200 OK` 或 301 重定向 |
| 3. 验证镜像拉取 | `kubectl describe pod dns-resolve-test` (等待约 1-2 分钟) | `State: Running` 不再是 `ErrImagePull` |
| 4. 验证 Pod 启动 | `kubectl get pods -A` | 原先 Pending 的 49 个 Pod 数量开始下降，或状态变为 Running |
| 5. 验证 OOM 修复 | `kubectl get pod rc-oomkilled-* -n aiops-e2e` | `STATUS: Running`, `RESTARTS: 0` 或停止增长 |
| 6. 确认 StartError | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` | 状态已从 Failed 变为其他状态，如 Running |

---

## ⚠️ 注意事项

- **网络问题是第一优先级**：集群 60% 以上的 Pod 异常都是因此而起。在未解决网络问题前，尝试其他修复（如修改 Pod 配置）几乎无效。
- **StartError Pod**：未采集到详细证据，其根本原因不确定。但它可能也与底层容器运行时或节点网络有关，建议在网络问题解决后观察其状态是否自动恢复。
- **谨慎操作**：在排查网络问题时，如果您的集群配置了网络策略（NetworkPolicy）或任何安全机制，请先确认这些规则不会误伤正常的网络流量。修改任何节点级别的配置都应格外小心。
- **长期建议**：
    - **部署镜像缓存/代理**：在集群内部署 `registry mirror`（如 Docker Registry 的 proxy cache 功能）或使用专业的镜像加速服务，以减少对外部网络的依赖。
    - **资源监控**：配置 Prometheus + Grafana 监控集群资源。OOM 问题可以通过设置内存使用率的告警提前发现。

---

## 📊 性能统计

├─ 总耗时: 2.5m
├─ 问题定位: 35.4s (23%) ✅
├─ 证据链采集: 64.6s (43%) ✅
├─ 根因分析: 18.6s (12%) ✅
├─ 汇总总结: 32.8s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 32 次
```

📋 诊断追踪

- **核心 Runbook**: pod-oomkilled
- **参考 Runbook**: pod-oomkilled
- **工具调用**: 32 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
