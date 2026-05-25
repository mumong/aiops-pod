======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 2e26a18f16464dfe]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先扫描全局 Pod 状态，看看当前集群中有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces 返回 106 行 pod 数据。Running=59, CrashLoopBackOff=1, ImagePullBackOff=40, Completed=2, ErrImagePull=1 (但 raw_preview 中未见 ErrImagePull)。异常集中: 1) CrashLoopBackOff: aiops-e2e
   💭 [问题定位] 全局扫描结果出来了。让我再看看具体的异常 Pod 详情。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=512 lines=4
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=382 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 让我用更直接的方式获取异常 Pod 信息。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=2801 lines=43
Executing jq query for pods...
aiops-e2e/test-dns-1779360358 phase=Pending waiting=ImagePullBackOff
default/dig-tool phase=Pending waiting=ImagePullBa
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=112 lines=2
Executing jq query for pods...
aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn restartCount=13 lastReason=Error
   💭 [问题定位] 现在来看一下这两个关键 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: registry-diag-1779381627
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Normal   BackOff  6m26s (x217 over 97m)  kubelet  Back-off pulling image "busybox:1.36
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-bq8pn
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
  Warning  BackOff         111s (x209 over 46m)  kubelet            
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe pod test-dns-1779360358 (namespace aiops-e2e) on node node1/10.2.0.49: status Pending. Container state Waiting (Reason: ImagePullBackOff), Ready=False. Image busybox:1.36.1 cannot be 
   💭 [问题定位] 现在我已经掌握了足够的信息。让我获取相关的 runbook 来辅助定位。
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
   💭 [问题定位] 现在让我看一下那个 CrashLoopBackOff Pod 的日志，确认它的退出原因。
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 调用工具: kubectl_previous_logs
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (42.6s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '镜像仓库网络不可达', 'probability': '高', 'reason': '多个Pod（test-dns、registry-diag）describe均显示Failed to pull image busybox:1.36.1 from docker.io，错误为dial tcp i/o timeout，节点无法连接到Docker Hub'}, {'scenario': 'DNS/网络连通性问题导致镜像拉取失败', 'probability': '中', 'reason': '大量网络测试类Pod（dns-*, net-*, registry-*）同时失败，可能集群出口网络或DNS配置存在问题'}, {'scenario': '应用配置错误（L4）', 'probability': '高', 'reason': 'rc-config-env-missing Pod CrashLoopBackOff，Exit Code 42，13次重启，标签标注ConfigError'}]
   entities=[{"type": "pod", "name": "rc-config-env-missing-5d9b8b766c-bq8pn", "namespace": "aiops-e2e"}, {"type": "pod", "name": "test-dns-1779360358", "namespace": "aiops-e2e"}, {"type": "pod", "name": "registry-diag-1779381627", "namespace": "mcp"}, {"type": "pod_group", "name": "约40个ImagePullBackOff Pod", "namespace": "default,mcp,aiops-e2e"}]
   reasoning=当前环境存在41个异常Pod，其中1个CrashLoopBackOff（aiops-e2e/rc-config-env-missing）和40个ImagePullBackOff/ErrImagePull。40个ImagePullBackOff Pod分布在default(12)、mcp(27)、aiops-e2e(1)命名空间，涉及dns-*, net-*, registry-*, node-debugger等测试类Pod，均为busybox:1.36.1镜像拉取失败。describe确认registry-diag-1779381627和test-dns-1779360358的ErrImagePull原因为docker.io网络超时（dial tcp i/o timeout）。这是典型的镜像仓库网络不可达问题，归类L3（ImagePullFailed）。同时，rc-config-env-missing Pod处于CrashLoopBackOff（13次重启，Exit Code 42，无OOM），标签标注ConfigError，属于应用配置错误（L4）。但L3（ImagePullBackOff数量40个）是当前最广泛、影响最大的异常层，且网络连通性是更底层的根因，因此定层L3。系统组件（kube-system、admin）全部Running正常。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "ImagePullFailed", "confidence": 0.92, "reasoning": "当前环境存在41个异常Pod，其中1个CrashLoopBackOff（aiops-e2e/rc-config-env-missing）和40个ImagePullBackOff/ErrImagePull。40个ImagePullBackOff Pod分布在default(12)、mcp(27)、aiops-e2e(1)命名空间，涉及dns-*, net-*, registry-*, node-debugger等测试类Pod，均为busybox:1.36.1镜像拉取失败。describe确认registry-diag-1779381627和test-dns-1779360358的ErrImagePull原因为docker.io网络超时（dial tcp i/o timeout）。这是典型的镜像仓库网络不可达问题，归类L3（ImagePullFailed）。同时，rc-config-env-missing Pod处于CrashLoopBackOff（13次重启，Exit Code 42，无OOM），标签标注ConfigError，属于应用配置错误（L4）。但L3（ImagePullBackOff数量40个）是当前最广泛、影响最大的异常层，且网络连通性是更底层的根因，因此定层L3。系统组件（kube-system、admin）全部Running正常。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-bq8pn", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "pod", "name": "rc-config-env-missing-5d9b8b766c-bq8pn", "namespace": "aiops-e2e"}, {"type": "pod", "name": "test-dns-1779360358", "namespace": "aiops-e2e"}, {"type": "pod", "name": "registry-diag-1779381627", "namespace": "mcp"}, {"type": "pod_group", "name": "约40个ImagePullBackOff Pod", "namespace": "default,mcp,aiops-e2e"}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达", "probability": "高", "reason": "多个Pod（test-dns、registry-diag）describe均显示Failed to pull image busybox:1.36.1 from docker.io，错误为dial tcp i/o timeout，节点无法连接到Docker Hub"}, {"scenario": "DNS/网络连通性问题导致镜像拉取失败", "probability": "中", "reason": "大量网络测试类Pod（dns-*, net-*, registry-*）同时失败，可能集群出口网络或DNS配置存在问题"}, {"scenario": "应用配置错误（L4）", "probability": "高", "reason": "rc-config-env-missing Pod CrashLoopBackOff，Exit Code 42，13次重启，标签标注ConfigError"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-bq8pn"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-bq8pn"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 40, "ErrImagePull": 1}, "total_abnormal": 42, "selected_rows": ["aiops-e2e         rc-config-env-missing-5d9b8b766c-bq8pn              0/1     CrashLoopBackOff   13 (5m ago)    46m     172.16.166.129   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0              7h35m   172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff   0              173m    172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff   0              113m    172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff   0              6h23m   172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0              7h30m   172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0              5h6m    172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-tmp                                        0/1     ImagePullBackOff   0              120m    172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff   0              6h12m   172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0              6h40m   172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0              3h36m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0              4h34m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0              6h21m   172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff   0              7h29m   172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0              6h42m   172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               curl-check-tmp                                      0/1     ImagePullBackOff   0              3h1m    172.16.104.58    node2    <none>           <none>            run=curl-check-tmp", "mcp               curls                                               0/1     ImagePullBackOff   0              82m     172.16.104.2     node2    <none>           <none>            run=curls", "mcp               dns-check-tmp                                       0/1     ImagePullBackOff   0              3h1m    172.16.104.13    node2    <none>           <none>            run=dns-check-tmp", "mcp               net-check-1779365549                                0/1     ImagePullBackOff   0              6h9m    172.16.166.179   node1    <none>           <none>            run=net-check-1779365549", "mcp               net-check-tool                                      0/1     ImagePullBackOff   0              38m     172.16.104.50    node2    <none>           <none>            run=net-check-tool"], "raw_ref": "/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 92%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将执行既有 evidence_plan 中的关键工具来采集证据。先从影响范围最大的 ImagePullBackOff 异常组开始，同时覆盖各个 namespace 的代表性 Pod。

## 第一步：执行 critical 级别的工具调用
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending (IP: 172.16.166.157). Container dig-tool is Waiting (Reason: ImagePullBackOff), not Ready. Image registry.k8s.io/e2e-test-images/jes
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod test-dns-1779360358 in namespace aiops-e2e on node node1/10.2.0.49 is in Pending status with ImagePullBackOff. Container image busybox:1.36.1 failed to pull over the last ~7h34m due to multiple ne
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-bq8pn
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff         2m28
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: registry-diag-1779381627
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Normal   BackOff  7m3s (x217 over 98m)  kubelet  Back-off pulling image "busybox:1.36.
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-check
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   6m30s (x46 over 4h33m)  kubelet  (combined from similar events): Failed to
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-test
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   8m30s (x75 over 6h16m)    kubelet  (combined from similar events): Failed t
   💭 [证据链采集] 所有 describe 工具已经完成。现在执行剩余的 important 级工具：

## 第二步：执行 important 级别的工具
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: test-dns-1779360358
namespace: aiops-e2e
creationTimestamp: 2026-05-21T10:45:58Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none
   💭 [证据链采集] ## 第三步：补充检查不同镜像源的异常Pod（dig-tool 使用的不是docker.io，而是registry.k8s.io）

让我再看一下 dig-tool 的具体镜像情况，以及 node-debugger 系列的镜像。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: node-debugger-node1-j7gtr
namespace: mcp
creationTimestamp: 2026-05-21T12:45:57Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                    READY   STATUS             RESTARTS   AGE     IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
registry-connect-test   0/1     ImagePullBackOff   0          6h
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-bq8pn   0/1
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME             READY   STATUS             RESTARTS   AGE    IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
dns-test-check   0/1     ImagePullBackOff   0          5h7m   172.16.104
   💭 [证据链采集] ## 证据采集结论

### ✅ 已采集的关键证据

#### 异常组 g2：ImagePullBackOff/ErrImagePull（40+ Pod，影响范围最大）

| 证据项 | 结果 |
|--------|------|
| **test-dns-1779360358** (aiops-e2e/node1) | Image `busybox:1.36.1` — Events 连续 `dial tcp ...:443: i/o timeout`，Pod 无 `imagePullSecrets`，容器镜像为公共镜像无需认证 |
| **dig-tool** (default/node1) | Image `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` — ImagePullBackOff，同样无 `imagePullSecrets` |
| **connectivity-test** (mcp/node2) | Image `busybox:1.36.1` — Failed to pull image: `dial tcp i/o timeout`，无 `imagePullSecrets` |
| **dns-test-check** (default/node2) | ImagePullBackOff，node2 同样受影响 |
| **registry-diag-1779381627** (mcp/node2) | 持续 ErrImagePull: `dial tcp 162.125.32.15:443: i/o timeout` |
| **node-debugger-node1-j7gtr** (mcp/node1) | Image `alpine:3.18` — 也是公共镜像拉取失败，ImagePullBackOff |
| **registry-connect-test** (default/node2) | ImagePullBackOff，node2 同样受影响 |

**核心发现**：跨 node1/node2 两个节点，涉及 docker.io、registry.k8s.io、alpine 三个公共仓库镜像全部拉取失败。Pod 均无 imagePullSecrets，说明**不是认证问题**。错误统一为 `dial tcp i/o timeout`，指向**集群出口网络到公共镜像仓库不可达**。

#### 异常组 g1：CrashLoopBackOff - rc-config-env-missing（1个 Pod）

| 证据项 | 结果 |
|--------|------|
| **kubectl describe** | Container State: Waiting (CrashLoopBackOff), Last State: Terminated (Error), Exit Code: 42，14次重启 |
| **previous logs** | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` |
| **kubectl get** | 当前状态 CrashLoopBackOff，restarts=14，标签 `pod_abnormal_type=ConfigError` |

**核心发现**：Exit Code 42 + 日志明确 `missing required APP_BOOT_MODE` — 这是**应用启动配置缺失**（ConfigError/L4），与镜像拉取无关。该 Pod 镜像应该已在之前拉取成功，但应用启动时缺少环境变量 `APP_BOOT_MODE`。

### 🔴 未发现冲突证据
- 所有计划中的 Pod 均存在于指定 namespace，状态与上游一致
- 无 NotFound、无 Terminating、无 Pending 冲突

### 📋 总体结论
1. **主问题（L3，影响40+ Pod）**：集群节点(node1/node2)到公共镜像仓库(docker.io/registry.k8s.io)的**出口网络不可达**，所有依赖公共镜像的 Pod 拉取失败，表现为 ImagePullBackOff/ErrImagePull，错误原文均为 `dial tcp i/o timeout`
2. **独立问题（L4，1个Pod）**：`rc-config-env-missing` Pod CrashLoopBackOff 是独立的**应用配置错误**，日志明确 `missing required APP_BOOT_MODE`，与镜像拉取无关
   ✅ [证据链采集] 完成 (54.9s)
   📤 → 下游数据: evidence_items=16/16
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"g2主异常组：describe代表Pod test-dns-1779360358(aiops-e2e)获取当前Events确认镜像拉取失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"验证当前ImagePullBackOff状态与Events中的拉取失败错误原文","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"g2主异常组：describe跨namespace代表Pod dig-tool(default)确认镜像拉取错误是否一致","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"验证default namespace的ImagePullBackOff Pod是否也是docker.io超时","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"g2主异常组：describe跨namespace代表Pod connectivity-test(mcp)确认镜像拉取错误是否一致","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp"},"purpose":"验证mcp namespace的ImagePullBackOff Pod是否也是docker.io超时","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"g1非主异常组：describe Pod rc-config-env-missing获取当前状态和Events确认CrashLoopBackOff原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-config-env-missing-5d9b8b766c-bq8pn","namespace":"aiops-e2e"},"purpose":"验证CrashLoopBackOff Pod的当前状态、Events和容器Last State","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"g1非主异常组：查看rc-config-env-missing的previous logs确认Exit Code 42具体错误","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous","tool_args":{},"purpose":"获取前一个实例的日志，确认Exit Code 42对应的ConfigError","evidence_type":"pod_logs","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6","description":"g2主异常组：从selected_rows中选一个node2上的Pod(dns-test-check)describe验证跨节点一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","tool_args":{"kind":"pod","name":"dns-test-check","namespace":"default"},"purpose":"验证node2上的ImagePullBackOff Pod是否也是docker.io超时","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7","description":"g2主异常组：获取test-dns-1779360358的Pod YAML检查imagePullSecrets和image配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"验证Pod spec中的image和imagePullSecrets配置","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e8","description":"g2主异常组：获取registry-diag-1779381627(mcp)的describe验证其ErrImagePull原因是否也是docker.io超时","level":"important","tool":"kubectl_describe","command":"kubectl describe pod registry-diag-1779381627 -n mcp","tool_args":{"kind":"pod","name":"registry-diag-1779381627","namespace":"mcp"},"purpose":"验证之前已发现ErrImagePull的Pod是否持续相同错误","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending (IP: 172.16.166.157). Container dig-tool is Waiting (Reason: ImagePullBackOff), not Ready. Image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 fails to pull due to i/o timeout dialing various gcr.io regional endpoints (europe-west2, us-west2, asia-east1). Events show repeated Failed (ErrImagePull, pull failure with DeadlineExceeded/Unknown), Normal BackOff (x187), and Normal Pulling. Container args: nslookup/host registry-1.docker.io. QoS: BestEffort. No container ID/image ID set. Restart Count: 0.\nkey_facts: [\"pod: dig-tool, namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"IP: 172.16.166.157\", \"container dig-tool image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False, ContainersReady: False\", \"Restart Count: 0\", \"container args: sh -c 'nslookup registry-1.docker.io 2>&1 || host registry-1.docker.io 2>&1 || echo DNS_CHECK_FAILED'\", \"Events: Warning Failed - ErrImagePull (x27 over 167m)\", \"Events: Warning Failed - pull i/o timeout to europe-west2-docker.pkg.dev (x3 over 163m, Unknown)\", \"Events: Warning Failed - pull i/o\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod test-dns-1779360358 in namespace aiops-e2e on node node1/10.2.0.49 is in Pending status with ImagePullBackOff. Container image busybox:1.36.1 failed to pull over the last ~7h34m due to multiple network errors (i/o timeout, connection reset by peer) when contacting registry-1.docker.io. Events show repeated Failed/ErrImagePull warnings (x59), BackOff (x889), and ongoing Pulling retries (x82). Container state: Waiting (Reason: ImagePullBackOff), Ready=False, Restart Count=0.\nkey_facts: [\"Pod: test-dns-1779360358\", \"Namespace: aiops-e2e\", \"Node: node1/10.2.0.49\", \"Status: Pending\", \"Container: test-dns-1779360358\", \"Image: busybox:1.36.1\", \"Container State: Waiting (Reason: ImagePullBackOff)\", \"Ready: False\", \"Restart Count: 0\", \"Pod IP: 172.16.166.148\", \"Events: Warning Failed (multiple, up to 54m ago) - Failed to pull image 'busybox:1.36.1' - errors include i/o timeout dialing various Docker Hub IPs (108.160.166.57:443, 198.44.185.131:443, 199.59.148.229:443, 162.125.17.131:443) and connection reset by peer (10.2.0.49:38564->3.233.166.60:443)\", \"Events: Warning Failed (31m, x59 over 7h34m) - Error: ErrImagePull\", \"Events: Normal BackOff (11m, x889 over 7h34m) - Back-off pulling \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-bq8pn\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         2m28s (x209 over 47m)  kubelet            Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-bq8pn_aiops-e2e(e49e4e4b-9359-4371-9a5e-bf2b7b082950)\n                  cni.projectcalico.org/containerID: 163a263de27393e0bca456e7f67ca48c38c689aa78b6f47c0f8498e963219a8a\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-config-env-missing-5d9b8b766c\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://68f19ef4d64bf1d76ab79472df75ec67ed80aec7942e3511fb44d720f79f783c\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n    Args:\n    St\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: registry-diag-1779381627\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  7m3s (x217 over 98m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   60s (x13 over 57m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 162.125.32.15:443: i/o timeout\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: c98704970288267abf43946b5b6ffe9364cf78a45cbcea537ecbdbf9d510c03a\n                  cni.projectcalico.org/podIP: 172.16.104.14/32\n                  cni.projectcalico.org/podIPs: 172.16.104.14/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  registry-diag-1779381627:\n    Conta\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-test-check\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   6m30s (x46 over 4h33m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 168.143.162.42:443: i/o timeout\n  Normal   BackOff  2m21s (x964 over 5h6m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   6m30s (x50 over 5h6m)   kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 9e22290236797aa5f25c53b51c38e8bf6856c341e86020f57967c39f91341d92\n                  cni.projectcalico.org/podIP: 172.16.104.53/32\n                  cni.projectcalico.org/podIPs: 172.16.104.53/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExec\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   8m30s (x75 over 6h16m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 103.226.246.99:443: i/o timeout\n  Normal   BackOff  3m41s (x1359 over 6h43m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   8m30s (x63 over 6h43m)    kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoE\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/007-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/007-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/007-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: test-dns-1779360358\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T10:45:58Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- test-dns-1779360358: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: /bin/sh -c nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- test-dns-1779360358: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-g4sbz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/008-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/008-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/008-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: node-debugger-node1-j7gtr\nnamespace: mcp\ncreationTimestamp: 2026-05-21T12:45:57Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 1\ncontainers:\n- debugger: image=alpine:3.18 imagePullPolicy=IfNotPresent\n  command: chroot /host sh -c cat /etc/resolv.conf\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [debugger]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [debugger]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- debugger: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"alpine:3.18\"\nvolumes:\n- {\"name\": \"host-root\"}\n- {\"name\": \"kube-api-access-9jwnd\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/009-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/009-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/009-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dig-tool\nnamespace: default\ncreationTimestamp: 2026-05-21T15:28:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dig-tool: image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1 || host registry-1.docker.io 2>&1 || echo DNS_CHECK_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dig-tool: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\nvolumes:\n- {\"name\": \"kube-api-access-lcm2n\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/010-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/010-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/010-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                    READY   STATUS             RESTARTS   AGE     IP              NODE    NOMINATED NODE   READINESS GATES   LABELS\nregistry-connect-test   0/1     ImagePullBackOff   0          6h23m   172.16.104.44   node2   <none>           <none>            run=registry-connect-test","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/011-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/011-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/011-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                                     READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-config-env-missing-5d9b8b766c-bq8pn   0/1     CrashLoopBackOff   14 (75s ago)   48m   172.16.166.129   node1   <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/012-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/012-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/012-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME             READY   STATUS             RESTARTS   AGE    IP              NODE    NOMINATED NODE   READINESS GATES   LABELS\ndns-test-check   0/1     ImagePullBackOff   0          5h7m   172.16.104.53   node2   <none>           <none>            run=dns-test-check","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/013-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/013-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2e26a18f16464dfe/tools/013-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"## 证据采集结论\n\n### ✅ 已采集的关键证据\n\n#### 异常组 g2：ImagePullBackOff/ErrImagePull（40+ Pod，影响范围最大）\n\n| 证据项 | 结果 |\n|--------|------|\n| **test-dns-1779360358** (aiops-e2e/node1) | Image `busybox:1.36.1` — Events 连续 `dial tcp ...:443: i/o timeout`，Pod 无 `imagePullSecrets`，容器镜像为公共镜像无需认证 |\n| **dig-tool** (default/node1) | Image `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` — ImagePullBackOff，同样无 `imagePullSecrets` |\n| **connectivity-test** (mcp/node2) | Image `busybox:1.36.1` — Failed to pull image: `dial tcp i/o timeout`，无 `imagePullSecrets` |\n| **dns-test-check** (default/node2) | ImagePullBackOff，node2 同样受影响 |\n| **registry-diag-1779381627** (mcp/node2) | 持续 ErrImagePull: `dial tcp 162.125.32.15:443: i/o timeout` |\n| **node-debugger-node1-j7gtr** (mcp/node1) | Image `alpine:3.18` — 也是公共镜像拉取失败，ImagePullBackOff |\n| **registry-connect-test** (default/node2) | ImagePullBackOff，node2 同样受影响 |\n\n**核心发现**：跨 node1/node2 两个节点，涉及 docker.io、registry.k8s.io、alpine 三个公共仓库镜像全部拉取失败。Pod 均无 imagePullSecrets，说明**不是认证问题**。错误统一为 `dial tcp i/o timeout`，指向**集群出口网络到公共镜像仓库不可达**。\n\n#### 异常组 g1：CrashLoopBackOff - rc-config-env-missing（1个 Pod）\n\n| 证据项 | 结果 |\n|--------|------|\n| **kubectl describe** | Container State: Waiting (CrashLoopBackOff), Last State: Terminated (Error), Exit Code: 42，14次重启 |\n| **previous logs** | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` |\n| **kubectl get** | 当前状态 CrashLoopBackOff，restarts=14，标签 `pod_abnormal_type=ConfigError` |\n\n**核心发现**：Exit Code 42 + 日志明确 `missing required APP_BOOT_MODE` — 这是**应用启动配置缺失**（ConfigError/L4），与镜像拉取无关。该 Pod 镜像应该已在之前拉取成功，但应用启动时缺少环境变量 `APP_BOOT_MODE`。\n\n### 🔴 未发现冲突证据\n- 所有计划中的 Pod 均存在于指定 namespace，状态与上游一致\n- 无 NotFound、无 Terminating、无 Pending 冲突\n\n### 📋 总体结论\n1. **主问题（L3，影响40+ Pod）**：集群节点(node1/node2)到公共镜像仓库(docker.io/registry.k8s.io)的**出口网络不可达**，所有依赖公共镜像的 Pod 拉取失败，表现为 ImagePullBackOff/ErrImagePull，错误原文均为 `dial tcp i/o timeout`\n2. **独立问题（L4，1个Pod）**：`rc-config-env-missing` Pod CrashLoopBackOff 是独立的**应用配置错误**，日志明确 `missing required APP_BOOT_MODE`，与镜像拉取无关","collection_summary":"计划 8 项，实际采集 8 项，未采集 0 项，完整度 100%；其中真实环境证据 16/16 项，完整度 100%；实际执行工具 21 个，匹配计划 8 个，未规划证据 13 个","plan_total":8,"plan_collected":8,"plan_completeness":1.0,"environment_evidence_total":16,"environment_evidence_collected":16,"environment_evidence_completeness":1.0,"executed_tool_count":21,"matched_tool_count":8,"unplanned_tool_count":13,"evidence_inventory":[{"id":"e1","description":"g2主异常组：describe代表Pod test-dns-1779360358(aiops-e2e)获取当前Events确认镜像拉取失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"验证当前ImagePullBackOff状态与Events中的拉取失败错误原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"g2主异常组：describe跨namespace代表Pod dig-tool(default)确认镜像拉取错误是否一致","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","purpose":"验证default namespace的ImagePullBackOff Pod是否也是docker.io超时","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"g2主异常组：describe跨namespace代表Pod connectivity-test(mcp)确认镜像拉取错误是否一致","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","purpose":"验证mcp namespace的ImagePullBackOff Pod是否也是docker.io超时","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"g1非主异常组：describe Pod rc-config-env-missing获取当前状态和Events确认CrashLoopBackOff原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e","purpose":"验证CrashLoopBackOff Pod的当前状态、Events和容器Last State","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"g1非主异常组：查看rc-config-env-missing的previous logs确认Exit Code 42具体错误","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous","purpose":"获取前一个实例的日志，确认Exit Code 42对应的ConfigError","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"g2主异常组：从selected_rows中选一个node2上的Pod(dns-test-check)describe验证跨节点一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","purpose":"验证node2上的ImagePullBackOff Pod是否也是docker.io超时","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7","description":"g2主异常组：获取test-dns-1779360358的Pod YAML检查imagePullSecrets和image配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml","purpose":"验证Pod spec中的image和imagePullSecrets配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e8","description":"g2主异常组：获取registry-diag-1779381627(mcp)的describe验证其ErrImagePull原因是否也是docker.io超时","level":"important","tool":"kubectl_describe","command":"kubectl describe pod registry-diag-1779381627 -n mcp","purpose":"验证之前已发现ErrImagePull的Pod是否持续相同错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/8 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | g2主异常组：describe代表Pod test-dns-1779360358(aiop... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_describe | g2主异常组：describe跨namespace代表Pod dig-tool(defau... | `kubectl describe pod dig-tool -n default` |
   | e3 | critical | ✅ | kubectl_describe | g2主异常组：describe跨namespace代表Pod connectivity-t... | `kubectl describe pod connectivity-test -n mcp` |
   | e4 | critical | ✅ | kubectl_describe | g1非主异常组：describe Pod rc-config-env-missing获取当... | `kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e` |
   | e5 | important | ✅ | kubectl_previous_logs | g1非主异常组：查看rc-config-env-missing的previous logs... | `kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous` |
   | e6 | important | ✅ | kubectl_describe | g2主异常组：从selected_rows中选一个node2上的Pod(dns-test-... | `kubectl describe pod dns-test-check -n default` |
   | e7 | important | ✅ | kubectl_get_yaml | g2主异常组：获取test-dns-1779360358的Pod YAML检查imageP... | `kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml` |
   | e8 | important | ✅ | kubectl_describe | g2主异常组：获取registry-diag-1779381627(mcp)的descri... | `kubectl describe pod registry-diag-1779381627 -n mcp` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (27.2s)
   📤 → 下游数据: root_cause=集群存在两个独立问题：1）【主问题·影响40个Pod】集群节点(node1/node2)到公共镜像仓库的出口网络不可达。跨5个Pod(覆盖default/mcp/aiops-e2e命名空间、node1/node2节点)的describe均确认错误为`dial tcp ...:443: i/o timeout`，涉及三个公共仓库：docker.io/busybox:1.36.1、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0、alpine:3.18。Pod YAML确认imagePullSecrets=absent，排除认证问题。错误持续7h+，BackOff次数最大x1359。系统组件(coredns/calico/kube-apiserver)全部Running正常，集群控制面健康。2）【独立问题·影响1个Pod】aiops-e2e/rc-config-env-missing CrashLoopBackOff(重启13次，Exit Code 42)，previous日志明确`L4_CONFIG_BOOTSTRAP_FAIL: m
... 截断，原始 547 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点(node1/node2)出口网络到公共镜像仓库(docker.io, registry.k8s.io, alpine)的TCP连接不可达，导致所有依赖公共镜像的Pod拉取失败", "propagation": "集群出口网络策略/防火墙/NAT网关阻断了对公共镜像仓库的出站HTTPS(443)连接 → kubelet在节点上尝试拉取镜像时，containerd向仓库发起HTTPS请求 → TCP三次握手在dial阶段超时(i/o timeout) → containerd返回DeadlineExceeded错误 → kubelet将Pod状态标记为ErrImagePull → 经过重试退避后转为ImagePullBackOff", "direct_cause": "kubelet无法从docker.io、registry.k8s.io、alpine等公共镜像仓库拉取镜像，所有拉取请求均因TCP连接超时(i/o timeout)失败", "manifestation": "40个Pod处于ImagePullBackOff/ErrImagePull状态（default=12, mcp=27, aiops-e2e=1），分布在node1和node2，跨越7个多小时，所有测试/诊断类Pod无法启动"}
   rca_analysis={"phenomenon": "集群存在42个异常Pod：40个ImagePullBackOff/ErrImagePull（分布在default、mcp、aiops-e2e命名空间，node1和node2节点），1个CrashLoopBackOff（aiops-e2e/rc-config-env-missing）。系统组件（coredns、calico、kube-apiserver等）全部Running正常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe (dig-tool)", "content": "default/dig-tool: ImagePullBackOff, image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, i/o timeout dialing gcr.io regional endpoints", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe (test-dns-1779360358)", "content": "aiops-e2e/test-dns-1779360358: ImagePullBackOff, image busybox:1.36.1, dial tcp to registry-1.docker.io i/o timeout (x59 failures, 7h34m)", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe (connectivity-test)", "content": "mcp/connectivity-test: ImagePullBackOff, image busybox:1.36.1, dial tcp 103.226.246.99:443 i/o timeout (x75 failures, 6h16m)", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe (dns-test-check)", "content": "default/dns-test-check on node2: ImagePullBackOff, image busybox:1.36.1, dial tcp 168.143.162.42:443 i/o timeout (x46 failures, 4h33m)", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe (registry-diag-1779381627)", "content": "mcp/registry-diag-1779381627 on node2: ErrImagePull, image busybox:1.36.1, dial tcp 162.125.32.15:443 i/o timeout (x13 failures, 57m)", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_yaml (test-dns-1779360358)", "content": "Pod YAML: imagePullSecrets=<absent>, image=busybox:1.36.1 (public), no auth required", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_yaml (dig-tool)", "content": "Pod YAML: imagePullSecrets=<absent>, image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 (public)", "reliability": "高"}, {"id": "e8", "source": "kubectl_get_yaml (node-debugger-node1-j7gtr)", "content": "mcp/node-debugger-node1-j7gtr on node1: imagePullSecrets=<absent>, image=alpine:3.18 (public)", "reliability": "高"}, {"id": "e9", "source": "kubectl_describe (rc-config-env-missing)", "content": "aiops-e2e/rc-config-env-missing: CrashLoopBackOff, restartCount=13, Exit Code 42, label pod_abnormal_type=ConfigError", "reliability": "高"}, {"id": "e10", "source": "kubectl_previous_logs (rc-config-env-missing)", "content": "L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "reliability": "高"}, {"id": "e11", "source": "kubectl_get_by_kind_in_cluster", "content": "106 pods total: Running=59, CrashLoopBackOff=1, ImagePullBackOff=40, Completed=2; system components all Running", "reliability": "高"}, {"id": "e12", "source": "kubernetes_jq_query (rc-config-env-missing)", "content": "restartCount=13, lastReason=Error", "reliability": "高"}, {"summary": "... 截断，原始 13 项"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "dig-tool: Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\" - i/o timeout to europe-west2-docker.pkg.dev, us-west2-docker.pkg.dev, asia-east1-docker.pkg.dev", "interpretation": "node1无法连接到Google Container Registry (gcr.io)区域端点，表明到k8s.gcr.io/registry.k8s.io上游的出口网络不通"}, {"evidence_id": "e2", "raw_data": "test-dns-1779360358: Failed to pull image \"busybox:1.36.1\" - dial tcp 108.160.166.57:443 i/o timeout, dial tcp 198.44.185.131:443 i/o timeout, dial tcp 199.59.148.229:443 i/o timeout", "interpretation": "node1连续7.5小时无法连接到Docker Hub (registry-1.docker.io)的多个IP地址，全部返回i/o timeout，不是DNS解析失败而是TCP连接超时"}, {"evidence_id": "e3", "raw_data": "connectivity-test: Failed to pull image \"busybox:1.36.1\" - dial tcp 103.226.246.99:443 i/o timeout (x75 over 6h16m)", "interpretation": "node2同样无法连接到Docker Hub，表明这是集群级别的出口网络问题而非单节点问题"}, {"evidence_id": "e4", "raw_data": "dns-test-check: Failed to pull image \"busybox:1.36.1\" - dial tcp 168.143.162.42:443 i/o timeout (x46 over 4h33m)", "interpretation": "node2上另一个Pod的确认，跨节点(node1/node2)一致性成立"}, {"evidence_id": "e5", "raw_data": "registry-diag-1779381627: Failed to pull image \"busybox:1.36.1\" - dial tcp 162.125.32.15:443 i/o timeout (x13 over 57m)", "interpretation": "node2上registry诊断Pod也发生同样错误，证明是Docker Hub整体不可达"}, {"evidence_id": "e6", "raw_data": "test-dns-1779360358 YAML: imagePullSecrets: <absent>, image: busybox:1.36.1 (public)", "interpretation": "排除imagePullSecret认证问题——镜像为公共镜像无需认证"}, {"evidence_id": "e7", "raw_data": "dig-tool YAML: imagePullSecrets: <absent>, image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 (public)", "interpretation": "第二个公共镜像同样无证书需求，进一步排除认证问题"}, {"evidence_id": "e8", "raw_data": "node-debugger-node1-j7gtr YAML: imagePullSecrets: <absent>, image: alpine:3.18 (public)", "interpretation": "第三个公共仓库(alpine)同样拉取失败，指向通用出口网络问题而非特定仓库问题"}, {"evidence_id": "e9", "raw_data": "rc-config-env-missing: CrashLoopBackOff, restartCount=13, Exit Code 42, label ConfigError", "interpretation": "该Pod镜像已成功拉取但应用启动失败；Exit Code 42指示配置缺失"}, {"evidence_id": "e10", "raw_data": "Previous log: L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "interpretation": "应用启动时缺少必要环境变量APP_BOOT_MODE，导致初始化失败"}, {"evidence_id": "e11", "raw_data": "Running=59, CrashLoopBackOff=1, ImagePullBackOff=40, Completed=2; system components all Running", "interpretation": "系统组件正常，说明集群控制面和网络插件(Calico)本身健康；异常全部集中在测试/诊断类Pod"}, {"evidence_id": "e12", "raw_data": "rc-config-env-missing: restartCount=13, lastReason=Error", "interpretation": "持续重启13次，每次都是相同错误（Exit Code 42），非偶发问题"}, {"summary": "... 截断，原始 13 项"}], "causal_chain": {"root_cause": "集群节点(node1/node2)出口网络到公共镜像仓库(docker.io, registry.k8s.io, alpine)的TCP连接不可达，导致所有依赖公共镜像的Pod拉取失败", "propagation": "集群出口网络策略/防火墙/NAT网关阻断了对公共镜像仓库的出站HTTPS(443)连接 → kubelet在节点上尝试拉取镜像时，containerd向仓库发起HTTPS请求 → TCP三次握手在dial阶段超时(i/o timeout) → containerd返回DeadlineExceeded错误 → kubelet将Pod状态标记为ErrImagePull → 经过重试退避后转为ImagePullBackOff", "direct_cause": "kubelet无法从docker.io、registry.k8s.io、alpine等公共镜像仓库拉取镜像，所有拉取请求均因TCP连接超时(i/o timeout)失败", "manifestation": "40个Pod处于ImagePullBackOff/ErrImagePull状态（default=12, mcp=27, aiops-e2e=1），分布在node1和node2，跨越7个多小时，所有测试/诊断类Pod无法启动"}, "root_cause": "集群存在两个独立问题：1）【主问题·影响40个Pod】集群节点(node1/node2)到公共镜像仓库的出口网络不可达。跨5个Pod(覆盖default/mcp/aiops-e2e命名空间、node1/node2节点)的describe均确认错误为`dial tcp ...:443: i/o timeout`，涉及三个公共仓库：docker.io/busybox:1.36.1、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0、alpine:3.18。Pod YAML确认imagePullSecrets=absent，排除认证问题。错误持续7h+，BackOff次数最大x1359。系统组件(coredns/calico/kube-apiserver)全部Running正常，集群控制面健康。2）【独立问题·影响1个Pod】aiops-e2e/rc-config-env-missing CrashLoopBackOff(重启13次，Exit Code 42)，previous日志明确`L4_CONFIG_BOOTSTRAP_FAIL: m\n... 截断，原始 547 字符", "root_cause_summary": "集群存在两个独立问题：1）【主问题·影响40个Pod】集群节点(node1/node2)到公共镜像仓库的出口网络不可达。跨5个Pod(覆盖default/mcp/aiops-e2e命名空间、node1/node2节点)的describe均确认错误为`dial tcp ...:443: i/o timeout`，涉及三个公共仓库：docker.io/busybox:1.36.1、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0、alpine:3.18。Pod YAML确认imagePullSecrets=absent，排除认证问题。错误持续7h+，BackOff次数最大x1359。系统组件(coredns/calico/kube-apiserver)全部Running正常，集群控制面健康。2）【独立问题·影响1个Pod】aiops-e2e/rc-config-env-missing CrashLoopBackOff(重启13次，Exit Code 42)，previous日志明确`L4_CONFIG_BOOTSTRAP_FAIL: m\n... 截断，原始 547 字符", "confidence": 0.95, "confidence_reason": "因果链完整：5个跨节点跨命名空间的Pod describe确认一致i/o timeout错误、3种不同公共镜像仓库均不可达、Pod YAML排除imagePullSecret认证问题、系统组件正常排除集群控制面故障。证据充分且相互印证，置信度高。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像名/tag不存在", "probability": "low", "reason": "多个Pod使用不同镜像(busybox:1.36.1, jessie-dnsutils:1.0, alpine:3.18)全部失败，但错误是网络超时而非manifest unknown，排除"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "Pod YAML确认imagePullSecrets=absent，且镜像均为公共镜像无需认证；错误是网络超时而非认证拒绝(denied/unauthorized)"}, {"cause": "DNS解析失败", "probability": "low", "reason": "错误是dial tcp i/o timeout而非lookup失败，说明域名解析成功但TCP连接无法建立"}, {"cause": "单节点网络问题", "probability": "low", "reason": "node1和node2两个节点均出现相同i/o timeout错误，排除单节点故障"}, {"cause": "rc-config-env-missing的CrashLoopBackOff与镜像拉取问题相关", "probability": "low", "reason": "该Pod镜像busybox:1.36已在之前成功拉取(Container ID已生成)，日志明确是APP_BOOT_MODE环境变量缺失，完全独立问题"}], "limitations": "未采集节点层面网络诊断证据（如节点上直接curl/wget docker.io、检查iptables规则、检查代理配置），无法精确定位是防火墙规则、NAT网关、还是上游ISP问题导致的出口网络不可达。rc-config-env-missing的Pod YAML未采集，无法确认是否定义了env字段。", "llm_raw_analysis": "## 证据清点\\n共采集13条关键证据，覆盖：5个跨节点跨命名空间Pod的describe确认镜像拉取错误、3个Pod的YAML确认无imagePullSecret、1个CrashLoopBackOff Pod的logs确认Exit Code 42原因、集群级Pod列表确认异常分布。\\n\\n## 逐条分析\\n- e1~e8：一致指向集群节点到公共镜像仓库的出口网络TCP连接不可达\\n- e6~e8：排除imagePullSecret认证问题\\n- e9~e10：独立于镜像拉取的ConfigError问题\\n- e11~e13：集群整体健康，异常集中且一致\\n\\n## 关联分析\\n40个ImagePullBackOff Pod跨node1/node2、跨3个命名空间，涉及3种不同公共仓库，错误统一为dial tcp i/o timeout，表明是集群级出口网络问题而非仓库或认证问题。rc-config-env-missing CrashLoopBackOff的Exit Code 42+日志明确APP_BOOT_MODE缺失，与镜像拉取完全无关。\\n\\n## 因果链\\n根因：集群出口网络阻\n... 截断，原始 637 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群存在两个独立问题：1）【主问题·影响40个Pod】集群节点(node1/node2)到公共镜像仓库的出口网络不可达。跨5个Pod(覆盖default/mcp/aiops-e2e命名空间、node1/node2节点)的describe均确认错误为`dial tcp ...:443: i/o tim...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点(node1/node2)出口网络到公共镜像仓库(docker.io, registry.k8s.io, alpine)的TCP连接不可达，导致所有依赖公共镜像的Pod拉取失败
     传导机制: 集群出口网络策略/防火墙/NAT网关阻断了对公共镜像仓库的出站HTTPS(443)连接 → kubelet在节点上尝试拉取镜像时，containerd向仓库发起HTTPS请求 → TCP三次握手在dial阶段超时(i/o timeout) → containerd返回DeadlineExceeded错误 → kubelet将Pod状态标记为ErrImagePull → 经过重试退避后转为ImagePullBackOff
     最终表现: 40个Pod处于ImagePullBackOff/ErrImagePull状态（default=12, mcp=27, aiops-e2e=1），分布在node1和node2，跨越7个多小时，所有测试/诊断类Pod无法启动


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (31.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6654 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 35.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的分析结果，为您生成一份详尽、完整的诊断报告。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `ImagePullBackOff` (40个), `CrashLoopBackOff` (1个) |
| **兼容归因层** | L3 - ImagePullFailed, L4 - ConfigError |
| **问题分类** | **主问题**: 镜像仓库网络不可达，**次问题**: 应用配置错误 |
| **置信度** | 主问题: 高 (95%)，次问题: 高 (90%) |
| **证据完整度** | 8/8 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **集群问题总结** | 集群当前有 **41个异常Pod**，包含两个独立的问题：**
1. **【主问题·影响40个Pod】** 集群节点无法从公共镜像仓库拉取镜像，导致大量Pod处于 `ImagePullBackOff` / `ErrImagePull` 状态。
2. **【次问题·影响1个Pod】** 应用 `rc-config-env-missing` 因缺少环境变量配置而处于 `CrashLoopBackOff` 状态。
 |
**Pod 异常分布：**
| 状态 | 数量 | 分布命名空间 |
|------|------|--------------|
| `ImagePullBackOff` | 40 | `default(12)`, `mcp(27)`, `aiops-e2e(1)` |
| `CrashLoopBackOff` | 1 | `aiops-e2e` |
| **总计** | **41** | |

**影响范围：**
*   所有依赖公共镜像（如 `busybox`, `registry.k8s.io`, `alpine`）的测试、诊断、巡检类Pod均无法启动。
*   一个配置错误的 `rc-config-env-missing` 应用持续重启。

**正常范围：**
*   集群关键系统组件（kube-system, admin命名空间下的 `coredns`, `calico`, `kube-apiserver` 等）均正常运行，集群控制面健康。
*   集群节点状态正常。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 (代表) | 原始数据 (代表) | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pods --all-namespaces` | `Running=59, CrashLoopBackOff=1, ImagePullBackOff=40, ...` | 集群40个Pod处于镜像拉取失败状态，1个应用配置错误。 |
| 2 | Pod 事件 | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` | `Failed to pull image "busybox:1.36.1"` -> `i/o timeout dialing ... registry-1.docker.io:443`，重复x59。 | **核心证据**: 拉取 `docker.io` 镜像失败，原因为目的主机 `i/o timeout`。 |
| 3 | Pod 事件 | `kubectl describe pod dig-tool -n default` | `Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0"` -> `i/o timeout dialing ... gcr.io` | 拉取 `registry.k8s.io` 镜像也因网络超时失败。 |
| 4 | Pod 事件 | `kubectl describe pod registry-diag-1779381627 -n mcp` | `Back-off pulling image "busybox:1.36.1"` | 跨命名空间 (`mcp`) 的Pod同样因拉取 `busybox` 失败。 |
| 5 | Pod 事件 | `kubectl describe pod dns-test-check -n default` | `Failed to pull image "busybox:1.36.1"` -> `i/o timeout` | 位于 `node2` (10.2.0.50) 的Pod也报同样的网络超时错误。 |
| 6 | Pod YAML | `kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml` | `imagePullSecrets: <absent>`, `finalizers: <none>` | Pod没有配置私有镜像仓库凭证，排除认证问题。同时排除 `finalizer` 导致的终止卡住。 |
| 7 | Pod 状态 | `kubectl describe pod rc-config-env-missing-... -n aiops-e2e` | `Reason: CrashLoopBackOff`, `Restart Count: 13` | 独立的应用容器持续重启。 |
| 8 | Pod 日志 | `kubectl logs rc-config-env-missing-... -n aiops-e2e --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | **核心证据**: 应用日志明确报错，因缺少`APP_BOOT_MODE`环境变量导致启动失败。 |

### 证据关联分析

- **证据 #1 + #2 + #3 + #4 + #5 印证**：跨命名空间、跨节点（`node1`, `node2`）、跨公有仓库（`docker.io`, `registry.k8s.io`, `alpine`）的 **40个Pod** 拉取镜像失败的根本原因是统一的 `i/o timeout` 错误。这说明问题出在集群**出口网络层面**，而非单个节点或单个镜像仓库的问题。

- **证据 #6 排除替代假设**：Pod YAML 确认未配置 `imagePullSecrets`，排除了因私有仓库认证失败的可能性。

- **证据 #7 + #8 印证**：一个独立的 `CrashLoopBackOff` 问题，其根本原因由应用日志直接指出：缺少 `APP_BOOT_MODE` 环境变量。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 节点上的网络诊断（如 `curl docker.io`, `iptables -L`） | important | 无法定位出口网络故障的具体点（防火墙？NAT？代理？） |
| Pod `rc-config-env-missing` 的完整 YAML | informational | 无法确认其 `env` 字段是否定义，但应用日志已给出确定性结论。 |

---

## 🎯 根因分析

### 因果链

```mermaid
graph TD
    subgraph 问题1: 镜像拉取失败 (影响40个Pod)
        A[根本原因: 集群节点出口网络到公共镜像仓库的TCP连接不可达] --> B[传播机制: 节点向仓库发起HTTPS连接 -> TCP握手超时(i/o timeout)]
        B --> C[直接原因: kubelet无法拉取镜像，报错 ErrImagePull]
        C --> D[用户可见现象: 40个Pod处于 ImagePullBackOff 状态，持续重试]
    end

    subgraph 问题2: 应用配置错误 (影响1个Pod)
        E[根本原因: Deployment未定义 APP_BOOT_MODE 环境变量] --> F[传播机制: 应用启动时读取配置失败]
        F --> G[直接原因: 容器进程因致命错误退出 (Exit Code 1)]
        G --> H[用户可见现象: Pod rc-config-env-missing 持续 CrashLoopBackOff]
    end
```

### 根因结论

**结论一：主问题 - 镜像仓库网络不可达 (置信度: 高 - 95%)**

根据 **证据 #2, #3, #4, #5**，40个Pod拉取镜像失败的根本原因是**集群中的所有节点（node1, node2）到公共镜像仓库（docker.io, registry.k8s.io等）的出口网络不可达**。所有拉取请求均因 `i/o timeout` 连接失败，持续超过7小时。

- ✅ 跨命名空间、跨节点、跨仓库的 **5个** Pod 描述均指向统一错误。
- ✅ Pod YAML 排除了镜像认证问题 (证据 #6)。
- ✅ 集群控制面（coredns, calico）正常运行，排除了集群内部网络或DNS问题。

**结论二：次问题 - 应用配置错误 (置信度: 高 - 90%)**

根据 **证据 #8**，Pod `rc-config-env-missing` 持续重启的根本原因是**缺少必要环境变量 `APP_BOOT_MODE`**，导致应用启动时配置引导失败并退出。

- ✅ 应用日志明确报告 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`。

---

## 🛠️ 修复建议

### 立即执行（需分别处理两个问题）

**1. [优先] 处理出口网络问题（主问题）**
*   **目标**：恢复集群节点到外部网络（尤其是 `443` 端口）的访问。
*   **命令/步骤**：此问题无法通过kubectl命令解决，需联系基础设施或网络团队：
    *   **检查节点代理配置**：确认节点是否配置了 `HTTP_PROXY`/`HTTPS_PROXY` 环境变量。如果是，确保 containerd 或 kubelet 正确使用代理。查看节点配置：
        ```bash
        # 在节点上执行 (需ssh到node1/node2)
        env | grep -i proxy
        ```
    *   **检查防火墙规则**：检查节点的 `iptables` 规则是否有阻止出站 `443` 端口的策略。
        ```bash
        # 在节点上执行 (需ssh到node1/node2)
        sudo iptables -L -n -t filter | grep 443
        ```
    *   **检查网络策略/路由**：确认集群CNI（如Calico）没有配置意外的出口策略，或路由规则导致流量无法出站。
    *   **临时绕过**：如果无法立即修复网络，可以考虑配置 `imagePullSecrets` 拉取已经在本地区或镜像仓库的镜像。
        ```yaml
        # 示例: 创建一个Secret，指向一个可访问的私有仓库
        kubectl create secret docker-registry <secret-name> \
          --docker-server=<your-private-registry> \
          --docker-username=<username> \
          --docker-password=<password> \
          -n <namespace>
        ```

**2. [立即] 修复应用配置（次问题）**
*   **目标**：为 `rc-config-env-missing` Pod 注入 `APP_BOOT_MODE` 环境变量。
*   **命令**：需要修改其控制器（可能是Deployment）的配置。假设控制器名为 `rc-config-env-missing`:
    ```bash
    # 编辑Deployment，在containers[].env下添加环境变量
    kubectl edit deployment rc-config-env-missing -n aiops-e2e
    ```
    在编辑器中的 `containers:` 下的 `env:` 字段（若无则新建）添加：
    ```yaml
          env:
          - name: APP_BOOT_MODE
            value: "production"
    ```
*   **验证**：保存并退出后，新的Pod会自动创建，检查新Pod状态：
    ```bash
    kubectl get pods -n aiops-e2e | grep rc-config-env-missing
    # 预期: 很快变为 Running 状态
    ```

### 后续优化
1.  **镜像仓库策略**：考虑在集群内部部署私有镜像仓库（如 Harbor）作为代理缓存，解决对外部网络的依赖并提升拉取速度。
2.  **配置管理**：将环境配置（如环境变量）统一使用 `ConfigMap` 或 `Secret` 管理，避免潜在配置缺失问题。
3.  **监控告警**：为Pod的 `ImagePullBackOff` 和 `CrashLoopBackOff` 状态配置告警，尽早发现此类集群级别的故障。

---

## 📋 验证步骤

| 步骤 | 命令/动作 | 预期结果 |
|------|------|------|
| 1. 验证网络修复 | 使用一个诊断Pod测试，或检查之前异常的Pod | `ImagePullBackOff` 状态的Pod数量开始减少，变为 `Running` |
| 2. 确认应用修复 | `kubectl get pods -n aiops-e2e -w` | `rc-config-env-missing-*` Pod 状态变为 `Running`，重启次数归零 |
| 3. 最终确认 | `kubectl get pods --all-namespaces | grep -E "(Error|BackOff|Pull)"` | 查询结果应为空，表示无异常Pod |

---

## ⚠️ 注意事项

-   **主问题排查优先级最高**：因为影响范围大（40个Pod），且系统组件虽然运行，但会阻碍未来所有使用公共镜像的Pod部署。
-   **节点网络排查需要 root/管理员权限**：大多数 `iptables`, `route`, 网络配置查看命令都需要 `sudo` 权限。
-   `rc-config-env-missing` 是独立问题，修复它不影响主问题的解决。但建议优先修复此问题，以消除一个次要告警。

---

## 📊 性能统计

├─ 总耗时: 2.6m
├─ 问题定位: 42.6s (27%) ✅
├─ 证据链采集: 54.9s (35%) ✅
├─ 根因分析: 27.2s (17%) ✅
├─ 汇总总结: 31.2s (20%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 25 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-config-error
- **工具调用**: 25 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
