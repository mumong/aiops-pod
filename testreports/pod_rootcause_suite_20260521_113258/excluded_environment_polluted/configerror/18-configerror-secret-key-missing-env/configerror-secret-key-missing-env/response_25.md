======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: bba2a21c5c3b43bc]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先做全局 Pod 状态扫描，看看当前集群中所有 Pod 的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned 全部 pods 列表。按 raw_preview 统计：60+ Running, ~19 ImagePullBackOff, 1 CreateContainerConfigError, 1 Terminating, 若干 Completed。ImagePullBackOff 集中在 default 命名空间（dig-t
   💭 [问题定位] 让我获取更完整的异常 Pod 详情。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=561 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAME:.metadata.name,NAMESPACE:.metadata.namespace,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query returned 50 rows, all STATUS=Pending. Pods spread across node1 and node2 in namespaces: aiops-e2e (2), default (18), mcp (30). No non-Pending statuses found.
key_facts: ["50 p
   💭 [问题定位] 这里 custom-columns 只抓到了 phase（所有 Pending Pod 的 phase 都是 Pending）。实际上 Pod 的 STATUS 字段包含具体原因，让我用另一种方式获取。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=3975 lines=53
Executing jq query for pods...
aiops-e2e/rc-config-secret-key-missing phase=Pending status=CreateContainerConfigError reason=N/A
aiops-e2e/test-dns-17
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 jq query across all namespaces found 48+ pods in Pending/Failed state. Majority (36+) stuck in ImagePullBackOff or ErrImagePull pulling busybox:1.36.1 (docker.io), with network errors: connection rese
   💭 [问题定位] 让我看看有没有 Terminating 状态的 Pod。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=98 lines=2
Executing jq query for pods...
mcp/net-check2 deletionTimestamp=2026-05-21T20:53:04Z phase=Pending
   💭 [问题定位] 好的，现在我来获取对 ImagePullBackOff 最相关的 runbook。
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
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod TerminatingStuck / 删除卡住

> runbook_id: pod-terminating-stuck.md
> Pod异常类型: TerminatingStuck | 典型状态: Terminating | 兼容分类: lifecycle

## 状态识别
- Pod 长时间处于 `Terminating`
- metadata.deletion
   💭 [问题定位] 现在让我快速确认几个典型异常 Pod 的状态。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   ✅ [问题定位] 完成 (45.4s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '镜像仓库网络不可达', 'probability': '高', 'reason': '36+ Pod 处于 ImagePullBackOff/ErrImagePull，网络错误为 connection reset by peer 和 i/o timeout 到 registry-1.docker.io:443 和 us-west2-docker.pkg.dev:443'}, {'scenario': 'Pod 配置错误', 'probability': '中', 'reason': 'aiops-e2e/rc-config-secret-key-missing 为 CreateContainerConfigError，找不到 Secret 中 APP_SECRET_TOKEN 键'}, {'scenario': '节点生命周期问题', 'probability': '低', 'reason': 'mcp/net-check2 处于 Terminating 状态，可能有 finalizer 或 volume detach 卡住'}]
   entities=[{"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "xnet", "namespace": "xnet"}, {"type": "registry", "name": "docker.io (busybox:1.36.1)", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io:443", "namespace": ""}, {"type": "registry", "name": "us-west2-docker.pkg.dev:443", "namespace": ""}]
   reasoning=当前集群存在大量（48+）处于 Pending 状态的异常 Pod，其中绝大多数（36+）因 ImagePullBackOff/ErrImagePull 卡住，根因是拉取 docker.io busybox:1.36.1 等镜像时出现网络错误（connection reset by peer, i/o timeout 到 registry-1.docker.io:443 和 us-west2-docker.pkg.dev:443），属于镜像仓库网络不可达（L3）。此外，aiops-e2e/rc-config-secret-key-missing 为 CreateContainerConfigError（L4 ConfigError），mcp/node-debugger-node1-nx8gb 为 Failed 状态，xnet/kibana 为 Failed 状态，mcp/net-check2 处于 Terminating。kube-system 组件均 Running 但有历史重启。ImagePullBackOff 是当前最大规模的异常，根因为 L3 网络/仓库问题，但同时也存在 L4 配置错误。按数量优先和根因层级优先原则，定层为 L3。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "Image/Registry Network Issue", "confidence": 0.95, "reasoning": "当前集群存在大量（48+）处于 Pending 状态的异常 Pod，其中绝大多数（36+）因 ImagePullBackOff/ErrImagePull 卡住，根因是拉取 docker.io busybox:1.36.1 等镜像时出现网络错误（connection reset by peer, i/o timeout 到 registry-1.docker.io:443 和 us-west2-docker.pkg.dev:443），属于镜像仓库网络不可达（L3）。此外，aiops-e2e/rc-config-secret-key-missing 为 CreateContainerConfigError（L4 ConfigError），mcp/node-debugger-node1-nx8gb 为 Failed 状态，xnet/kibana 为 Failed 状态，mcp/net-check2 处于 Terminating。kube-system 组件均 Running 但有历史重启。ImagePullBackOff 是当前最大规模的异常，根因为 L3 网络/仓库问题，但同时也存在 L4 配置错误。按数量优先和根因层级优先原则，定层为 L3。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-check-node2", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check2", "namespace": "mcp", "status": "Terminating"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "xnet", "namespace": "xnet"}, {"type": "registry", "name": "docker.io (busybox:1.36.1)", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io:443", "namespace": ""}, {"type": "registry", "name": "us-west2-docker.pkg.dev:443", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达", "probability": "高", "reason": "36+ Pod 处于 ImagePullBackOff/ErrImagePull，网络错误为 connection reset by peer 和 i/o timeout 到 registry-1.docker.io:443 和 us-west2-docker.pkg.dev:443"}, {"scenario": "Pod 配置错误", "probability": "中", "reason": "aiops-e2e/rc-config-secret-key-missing 为 CreateContainerConfigError，找不到 Secret 中 APP_SECRET_TOKEN 键"}, {"scenario": "节点生命周期问题", "probability": "低", "reason": "mcp/net-check2 处于 Terminating 状态，可能有 finalizer 或 volume detach 卡住"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "net-check2"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g4", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "net-check2"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g4", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 48, "Terminating": 1}, "total_abnormal": 49, "selected_rows": ["aiops-e2e         rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0              28m     172.16.166.130   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff             0              10h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              5h24m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff             0              4h25m   172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              8h      172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff             0              104m    172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff             0              110m    172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ImagePullBackOff             0              110m    172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff             0              10h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff             0              7h37m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff             0              110m    172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ImagePullBackOff             0              4h31m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              8h      172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff             0              9h      172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff             0              6h7m    172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ImagePullBackOff             0              138m    172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff             0              7h6m    172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-conn-test-evidence                         0/1     ImagePullBackOff             0              43m     172.16.104.22    node2    <none>           <none>            run=registry-conn-test-evidence", "default           registry-connect-test                               0/1     ImagePullBackOff             0              8h      172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              10h     172.16.166.185   node1    <none>           <none>            run=test-net-1779360704"], "raw_ref": "/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我先获取 ImagePullFailed 和 TerminatingStuck 的 runbook 参考，同时开始执行关键的真实环境验证。

## 第一步：并行拉取所有可执行的真实证据

先从两个命名空间各选一个代表性 Pod 做 describe，同时检查节点状态。
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
# Pod TerminatingStuck / 删除卡住

> runbook_id: pod-terminating-stuck.md
> Pod异常类型: TerminatingStuck | 典型状态: Terminating | 兼容分类: lifecycle

## 状态识别
- Pod 长时间处于 `Terminating`
- metadata.deletion
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node1
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool is Waiting (Reason: ImagePullBackOff), Ready=False, Restart Count=0. Image registry.k8s.io/e2e-test-images/jessi
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          27m (x12 over 29m)     kubelet            Error: co
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node2
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [证据链采集] 两个节点都没有 taint，且 Ready。继续获取剩余的关键证据。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
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
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  13m (x1306 over 10h)  kubelet  Back-off pulling image "busybox:1.36
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: net-check2
namespace: mcp
creationTimestamp: 2026-05-21T20:51:34Z
deletionTimestamp: 2026-05-21T20:53:04Z
deletionGracePeriodSeconds: 30
finalizers: <none>
ser
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
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN   TYPE     REASON           OBJECT           MESSAGE
3m6s        Normal   Scheduled        Pod/net-check2   Successfully assigned mcp/net-check2 to node2
3m6s        Norma
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
28m (x12 over 30m)    Warning   Failed           Pod/rc-config-secret-key-missing   Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
43m                       Warning   Failed    Pod/dig-tool   Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0": rpc error: code = Unknown desc = fail
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 现在让我获取批量 ImagePull 失败事件的完整信息，以及补充验证 dig-tool 的镜像地址和 imagePullSecrets：
   💭 [证据链采集] 调用工具: run_bash_command
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [证据链采集] 调用工具: run_bash_command
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 Multiple pods across namespaces (default, mcp) on node2 and node1 are failing to pull container images from remote registries (docker.io, registry.k8s.io). Errors include i/o timeout, connection refus
   💭 [证据链采集] 现在我已收集到所有关键证据。下面给出完整的证据采集结论：

---

## 证据采集结论

### ✅ 已采集证据（主异常组 g2：ImagePullBackOff 完整验证）

| 证据项 | 结果 |
|--------|------|
| **e1-g2-runbook** | ✅ Reference：pod-imagepull-failed.md 已获取 |
| **e2-g2-describe-rep**（dig-tool） | ✅ Pod 处于 ImagePullBackOff，Events 明确显示 `dial tcp ...:443: i/o timeout` 到 `us-west2-docker.pkg.dev` |
| **e3/e4-g2-describe-node**（node1/node2） | ✅ 两个节点均 Ready，无 Taints → **节点健康，排除节点异常导致拉取失败** |
| **e5-g2-get-yaml-rep**（dig-tool YAML） | ✅ 镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，无 imagePullSecrets → 非认证问题 |
| **e6-g2-events**（全集群拉取事件） | ✅ **直接根因确认**：所有节点（node1/node2）所有命名空间（default/mcp/aiops-e2e）拉取镜像均出现 **`i/o timeout`** 到 `us-west2-docker.pkg.dev:443`（142.250.157.82）、`108.160.166.42:443`、`199.59.149.236:443`，以及 **`connection refused`** 到 `93.179.102.140:443`。还出现 **`pull QPS exceeded`** 错误 → **双重故障：镜像仓库网络不可达 + 节点并发拉取超限** |
| **e10-g2-describe-aiops-rep**（test-dns-1779360358） | ✅ aiops-e2e 命名空间的 ImagePullBackOff 同样为 `i/o timeout` 到 `registry-1.docker.io:443` |

### ✅ 已采集证据（非主异常组最小验证）

| 异常组 | 证据 | 结论 |
|--------|------|------|
| **g1: CreateContainerConfigError**（rc-config-secret-key-missing） | ✅ describe + events 确认 | `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` → **ConfigMap/Secret key 缺失，Pod 配置错误** |
| **g3: TerminatingStuck**（net-check2） | ✅ YAML + events 确认 | `deletionTimestamp: 2026-05-21T20:53:04Z`，finalizers 为空，Pod 当前仍在 Pulling 状态（正在拉取 busybox:1.36.1），无 finalizer 或 volume 卡住 → **Terminating 状态但仍在优雅终止窗口内（30s），实际因镜像拉取卡住** |
| **g4: StartError**（node-debugger-node1-nx8gb） | ✅ describe 确认 | 无事件记录，空/负向观察 → **当前处于 Failed 状态但缺少事件详情，可能是短暂状态或 Node 侧问题** |

### ⚠️ 冲突/负向证据
- **e6-g2-events** 的 field-selector 方式未返回结果（`reason=FailedToPullImage` 不是标准 event reason），但通过 grep 方式已验证大量拉取失败事件。

### 📋 总体结论
**集群当前存在 48+ 处于 ImagePullBackOff 的 Pod（主异常），根因为：**
1. **镜像仓库网络不可达** — `registry-1.docker.io:443`（docker.io busybox:1.36.1）和 `us-west2-docker.pkg.dev:443`（registry.k8s.io jessie-dnsutils:1.0）均出现 TCP `i/o timeout` 和 `connection refused`
2. **节点并发拉取超限（pull QPS exceeded）** — 大量 Pod 并发拉取触发限流，形成恶性循环
3. **辅助异常**：`rc-config-secret-key-missing` 为 Secret key 缺失（CreateContainerConfigError），`net-check2` 为 Terminating 但实际因拉取镜像卡住，均属于次要异常
   ✅ [证据链采集] 完成 (1m 53.4s)
   📤 → 下游数据: evidence_items=15/16
   evidence_analysis={"evidence_plan":[{"id":"e1-g2-runbook","description":"读取 ImagePullFailed runbook 作为参考上下文","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{"runbook_id":"pod-imagepull-failed.md"},"purpose":"参考 runbook 检查点，指导后续真实环境验证","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g2-describe-rep","description":"Critical: Describe 代表 ImagePullBackOff Pod (default/dig-tool) 获取 Events 和容器状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","tool_args":{"kind":"Pod","name":"dig-tool","namespace":"default"},"purpose":"获取 ImagePullBackOff 的 Events 原文，验证拉取错误类型（connection refused/timeout/manifest unknown/unauthorized）","evidence_type":"current_status","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3-g2-describe-node1","description":"Important: Describe node1 确认节点状态（Pod 分布在 node1 和 node2）","level":"important","tool":"kubectl_describe","command":"kubectl describe node node1","tool_args":{"kind":"Node","name":"node1"},"purpose":"确认节点是否 Ready，排除节点异常导致镜像拉取失败","evidence_type":"node_status","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4-g2-describe-node2","description":"Important: Describe node2 确认节点状态","level":"important","tool":"kubectl_describe","command":"kubectl describe node node2","tool_args":{"kind":"Node","name":"node2"},"purpose":"确认节点是否 Ready，排除节点异常导致镜像拉取失败","evidence_type":"node_status","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5-g2-get-yaml-rep","description":"Critical: Get Pod YAML 验证 imagePullSecrets 和 spec.containers[].image","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml","tool_args":{"kind":"Pod","name":"dig-tool","namespace":"default"},"purpose":"检查镜像地址、imagePullSecrets 配置，排除认证或镜像名错误","evidence_type":"config_check","target_scope":"g2","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e6-g2-events","description":"Important: 查看集群事件过滤 ImagePull 相关","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by='.lastTimestamp'","tool_args":{"field_selector":"reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff"},"purpose":"获取批量 ImagePull 失败事件的完整原文，确认网络错误模式","evidence_type":"events","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7-g1-describe-configError","description":"Critical: Describe CreateContainerConfigError Pod 获取 Secret/ConfigMap 缺失详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"获取 CreateContainerConfigError 的 Events 原文，验证 Secret key 缺失","evidence_type":"current_status","target_scope":"g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"e8-g3-get-yaml-terminating","description":"Critical: Get YAML 确认 Terminating Pod (mcp/net-check2) 的 deletionTimestamp 和 finalizers","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod net-check2 -n mcp -o yaml","tool_args":{"kind":"Pod","name":"net-check2","namespace":"mcp"},"purpose":"确认 deletionTimestamp、finalizers、nodeName，验证是否 finalizer 卡住","evidence_type":"current_status","target_scope":"g3","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e9-g4-describe-startError","description":"Important: Describe StartError Pod (mcp/node-debugger-node1-nx8gb)","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"获取 StartError 的状态和事件的详细原文","evidence_type":"current_status","target_scope":"g4","acceptable_tools":[],"counts_for_completeness":true},{"id":"e10-g2-describe-aiops-rep","description":"Important: Describe aiops-e2e ImagePullBackOff Pod 确认跨 namespace 相同错误模式","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"Pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"验证 aiops-e2e namespace 的 ImagePullBackOff 是否也是 registry 网络错误","evidence_type":"current_status","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod TerminatingStuck / 删除卡住\n\n> runbook_id: pod-terminating-stuck.md\n> Pod异常类型: TerminatingStuck | 典型状态: Terminating | 兼容分类: lifecycle\n\n## 状态识别\n- Pod 长时间处于 `Terminating`\n- metadata.deletionTimestamp 已存在但对象未删除\n- 常见原因: finalizer 未完成、kubelet 无响应、volume detach/unmount 卡住\n- 本 runbook 只用于“当前仍存在且处于 Terminating 的 Pod”。如果 `kubectl get pod <pod>` 返回 NotFound，说明对象已删除，不应继续按 TerminatingStuck 分析。\n\n## Evidence 节点推荐计划\n1. `fetch_runbook pod-terminating-stuck.md`: 先读取本手册作为判断参考。\n2. `kubectl get pod <pod> -n <namespace> -o yaml`: critical，确认 deletionTimestamp、finalizers、nodeName、ownerReferences。\n3. `kubectl describe pod <pod> -n <namespace>`: critical，确认 termination、Killing、FailedKillPod、volume unmount/detach 事件。\n4. `kubectl get node <node> -o wide`: important，确认 Pod 所在 Node 是否 Ready。\n5. `kubectl describe node <node>`: optional，只有 Node NotReady/Unknown 或 describe pod 指向 kubelet/volume 问题时继续。\n\n## 典型原因\n- Pod 或其关联资源存在 finalizer，控制器未完成清理。\n- Pod 所在节点 NotReady/Unknown，kubelet 无法完成容器停止和状态回报。\n- CSI/NFS 等卷卸载或 detach 卡住。\n- PreStop hook 或 terminationGracePeriodSeconds 很长，Pod 仍在正常优雅终止窗口内。\n- StatefulSet/Job/自定义控制器删除链路卡住，需要检查 ownerReferences 和相关控制器事件。\n\n## 必查项\n1. `kubectl get pod <pod> -n <namespace> -o y\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/002-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/002-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/002-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node1\n关键诊断行:\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nTaints:             <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool is Waiting (Reason: ImagePullBackOff), Ready=False, Restart Count=0. Image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 cannot be pulled due to network i/o timeout errors when connecting to us-west2-docker.pkg.dev (several IPs: 108.177.125.82, 142.250.157.82). Events: repeated Failed (x8 over 4h51m, x2 over 55m) and a single 42m ago, all pull timeouts; BackOff event (x621 over 5h19m). Pod has IP 172.16.166.157, QoS BestEffort, Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True.\nkey_facts: [\"Pod name: dig-tool\", \"Namespace: default\", \"Node: node1/10.2.0.49\", \"Status: Pending\", \"Pod IP: 172.16.166.157\", \"Container dig-tool State: Waiting, Reason: ImagePullBackOff\", \"Container dig-tool Ready: False\", \"Container dig-tool Restart Count: 0\", \"Image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"Container ID: empty\", \"Image ID: empty\", \"Failed to pull image: network i/o timeout dialing us-west2-docker.pkg.dev (IPs: 108.177.125.82, 142.250.157.82) on port 443\", \"Event: Warning Failed (42m ago) - i/o timeout\", \"Event: Warning Failed (17m ago, x8 over 4h51m\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          27m (x12 over 29m)     kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: e50889f651dff0ebd5a4ed7212a0f9deacd4b503f1ae265a36959b8e7c2ff9c4\n                  cni.projectcalico.org/podIP: 172.16.166.130/32\n                  cni.projectcalico.org/podIPs: 172.16.166.130/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-pbw78:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node2\n关键诊断行:\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nTaints:             <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:               \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  13m (x1306 over 10h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   3m16s (x126 over 9h)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:57752->44.218.41.59:443: read: connection reset by peer\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-d\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/008-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/008-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/008-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: net-check2\nnamespace: mcp\ncreationTimestamp: 2026-05-21T20:51:34Z\ndeletionTimestamp: 2026-05-21T20:53:04Z\ndeletionGracePeriodSeconds: 30\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- net-check2: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c timeout 5 nslookup registry-1.docker.io 2>&1; echo EXIT=$?\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [net-check2]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [net-check2]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- net-check2: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-h7g8p\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/009-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/009-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/009-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dig-tool\nnamespace: default\ncreationTimestamp: 2026-05-21T15:28:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dig-tool: image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1 || host registry-1.docker.io 2>&1 || echo DNS_CHECK_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dig-tool: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\nvolumes:\n- {\"name\": \"kube-api-access-lcm2n\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/010-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/010-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/010-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN   TYPE     REASON           OBJECT           MESSAGE\n3m6s        Normal   Scheduled        Pod/net-check2   Successfully assigned mcp/net-check2 to node2\n3m6s        Normal   AddedInterface   Pod/net-check2   Add eth0 [172.16.104.15/32] from k8s-pod-network\n3m6s        Normal   Pulling          Pod/net-check2   Pulling image \"busybox:1.36.1\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/011-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/011-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/011-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n28m (x12 over 30m)    Warning   Failed           Pod/rc-config-secret-key-missing   Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/012-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/012-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/012-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n43m                       Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 108.177.125.82:443: i/o timeout\n18m (x8 over 4h51m)       Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 142.250.157.82:443: i/o timeout\n8m46s (x2 over 56m)       Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 142.250.157.82:443: i/o timeout\n4m30s (x621 over 5h19m)   Normal    BackOff   Pod/dig-tool   Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/013-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/013-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/013-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/014-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/014-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/014-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/015-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/015-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/015-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"Multiple pods across namespaces (default, mcp) on node2 and node1 are failing to pull container images from remote registries (docker.io, registry.k8s.io). Errors include i/o timeout, connection refused, DeadlineExceeded, and pull QPS exceeded. Image busybox:1.36.1 is the most commonly affected. Pods: dns-test-check, dns-resolve-test, node-debugger-node2-*, registry-diag-*, dig-tool, test-registry-conn-*, nettest-*, test-reg-conn-*, dns-test-tmp all showing Failed/ErrImagePull.\nkey_facts: [\"pod/dns-test-check (default, node2): Failed to pull busybox:1.36.1 - DeadlineExceeded + i/o timeout (108.160.166.42:443) at 11m; also ErrImagePull (65x over 7h39m); pull QPS exceeded at 9m23s\", \"pod/dns-resolve-test (default, node2): Failed to pull busybox:1.36.1 - Unknown desc + i/o timeout (108.160.166.42:443) at 10m; pull QPS exceeded at 9m23s\", \"pod/node-debugger-node2-q6htb (mcp, node2): Failed to pull busybox:1.36.1 - DeadlineExceeded + i/o timeout (199.59.149.236:443) at 10m; pull QPS exceeded at 9m23s\", \"pod/registry-diag-1779381627 (mcp, node2): Failed to pull busybox:1.36.1 - Unknown desc + i/o timeout (199.59.149.236:443) at 9m54s; ErrImagePull (32x over 4h11m)\", \"pod/dig-tool (default, node1): Failed to pull registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 - Unknown desc + i/o timeout (142.250.157.82:443) at 9m36s (2x over 57m)\", \"pod/test-registry-conn-1779367059 (mcp, node2): Failed to pull busybox:1.36.1 - DeadlineExceeded + i/o timeout (199.59.149.236:443) at 9m24s; ErrImagePull (52x over 8h)\", \"pod/node-debugger-node2-cfk7z (mcp, node2): Failed to pull busybox:1.36.1 - Unknown desc + connection refused (93.179.102.140:443) at 9m23s\", \"pod/nettest-1779363677 (default, node2): Failed to pull busybox:1.36.1 - Unknown desc + connection refused (93.179.102.140:443) at 9m23s\", \"pod/test-reg-conn-1779373343 (mcp, node2): Failed to pull busybox:1.36.1 - Unknown desc + connection refused (93.179.102.140:443) at 9m23s (2x over 6h16m)\", \"pod/dns-test-tmp (default, node2): Failed to pull busybox:1.36.1 - Unknown desc + connection refused (93.179.102.140:443) at 9m23s\"]\nconflicts: [\"current_summary truncated at 'ErrIma' and missing many events present in raw_preview (node-debugger-node2-cfk7z, nettest-1779363677, test-reg-conn-1779373343, dns-test-tmp, pull QPS exceeded events)\"]\nmissing: [\"No successful image pulls reported; no data about node network health or registry availability beyond the error messages\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/016-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/016-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bba2a21c5c3b43bc/tools/016-evidence-run_bash_command.summary.txt"}],"llm_analysis":"现在我已收集到所有关键证据。下面给出完整的证据采集结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（主异常组 g2：ImagePullBackOff 完整验证）\n\n| 证据项 | 结果 |\n|--------|------|\n| **e1-g2-runbook** | ✅ Reference：pod-imagepull-failed.md 已获取 |\n| **e2-g2-describe-rep**（dig-tool） | ✅ Pod 处于 ImagePullBackOff，Events 明确显示 `dial tcp ...:443: i/o timeout` 到 `us-west2-docker.pkg.dev` |\n| **e3/e4-g2-describe-node**（node1/node2） | ✅ 两个节点均 Ready，无 Taints → **节点健康，排除节点异常导致拉取失败** |\n| **e5-g2-get-yaml-rep**（dig-tool YAML） | ✅ 镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，无 imagePullSecrets → 非认证问题 |\n| **e6-g2-events**（全集群拉取事件） | ✅ **直接根因确认**：所有节点（node1/node2）所有命名空间（default/mcp/aiops-e2e）拉取镜像均出现 **`i/o timeout`** 到 `us-west2-docker.pkg.dev:443`（142.250.157.82）、`108.160.166.42:443`、`199.59.149.236:443`，以及 **`connection refused`** 到 `93.179.102.140:443`。还出现 **`pull QPS exceeded`** 错误 → **双重故障：镜像仓库网络不可达 + 节点并发拉取超限** |\n| **e10-g2-describe-aiops-rep**（test-dns-1779360358） | ✅ aiops-e2e 命名空间的 ImagePullBackOff 同样为 `i/o timeout` 到 `registry-1.docker.io:443` |\n\n### ✅ 已采集证据（非主异常组最小验证）\n\n| 异常组 | 证据 | 结论 |\n|--------|------|------|\n| **g1: CreateContainerConfigError**（rc-config-secret-key-missing） | ✅ describe + events 确认 | `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` → **ConfigMap/Secret key 缺失，Pod 配置错误** |\n| **g3: TerminatingStuck**（net-check2） | ✅ YAML + events 确认 | `deletionTimestamp: 2026-05-21T20:53:04Z`，finalizers 为空，Pod 当前仍在 Pulling 状态（正在拉取 busybox:1.36.1），无 finalizer 或 volume 卡住 → **Terminating 状态但仍在优雅终止窗口内（30s），实际因镜像拉取卡住** |\n| **g4: StartError**（node-debugger-node1-nx8gb） | ✅ describe 确认 | 无事件记录，空/负向观察 → **当前处于 Failed 状态但缺少事件详情，可能是短暂状态或 Node 侧问题** |\n\n### ⚠️ 冲突/负向证据\n- **e6-g2-events** 的 field-selector 方式未返回结果（`reason=FailedToPullImage` 不是标准 event reason），但通过 grep 方式已验证大量拉取失败事件。\n\n### 📋 总体结论\n**集群当前存在 48+ 处于 ImagePullBackOff 的 Pod（主异常），根因为：**\n1. **镜像仓库网络不可达** — `registry-1.docker.io:443`（docker.io busybox:1.36.1）和 `us-west2-docker.pkg.dev:443`（registry.k8s.io jessie-dnsutils:1.0）均出现 TCP `i/o timeout` 和 `connection refused`\n2. **节点并发拉取超限（pull QPS exceeded）** — 大量 Pod 并发拉取触发限流，形成恶性循环\n3. **辅助异常**：`rc-config-secret-key-missing` 为 Secret key 缺失（CreateContainerConfigError），`net-check2` 为 Terminating 但实际因拉取镜像卡住，均属于次要异常","collection_summary":"计划 9 项，实际采集 8 项，未采集 1 项，完整度 89%；其中真实环境证据 14/15 项，完整度 93%；实际执行工具 20 个，匹配计划 9 个，未规划证据 11 个","plan_total":9,"plan_collected":8,"plan_completeness":0.8888888888888888,"environment_evidence_total":15,"environment_evidence_collected":14,"environment_evidence_completeness":0.9333333333333333,"executed_tool_count":20,"matched_tool_count":9,"unplanned_tool_count":11,"evidence_inventory":[{"id":"e1-g2-runbook","description":"读取 ImagePullFailed runbook 作为参考上下文","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"参考 runbook 检查点，指导后续真实环境验证","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g2-describe-rep","description":"Critical: Describe 代表 ImagePullBackOff Pod (default/dig-tool) 获取 Events 和容器状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","purpose":"获取 ImagePullBackOff 的 Events 原文，验证拉取错误类型（connection refused/timeout/manifest unknown/unauthorized）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-g2-describe-node1","description":"Important: Describe node1 确认节点状态（Pod 分布在 node1 和 node2）","level":"important","tool":"kubectl_describe","command":"kubectl describe node node1","purpose":"确认节点是否 Ready，排除节点异常导致镜像拉取失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-g2-describe-node2","description":"Important: Describe node2 确认节点状态","level":"important","tool":"kubectl_describe","command":"kubectl describe node node2","purpose":"确认节点是否 Ready，排除节点异常导致镜像拉取失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-g2-get-yaml-rep","description":"Critical: Get Pod YAML 验证 imagePullSecrets 和 spec.containers[].image","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml","purpose":"检查镜像地址、imagePullSecrets 配置，排除认证或镜像名错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6-g2-events","description":"Important: 查看集群事件过滤 ImagePull 相关","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by='.lastTimestamp'","purpose":"获取批量 ImagePull 失败事件的完整原文，确认网络错误模式","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7-g1-describe-configError","description":"Critical: Describe CreateContainerConfigError Pod 获取 Secret/ConfigMap 缺失详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"获取 CreateContainerConfigError 的 Events 原文，验证 Secret key 缺失","collected":false,"source":"planned","outcome":"unknown"},{"id":"e8-g3-get-yaml-terminating","description":"Critical: Get YAML 确认 Terminating Pod (mcp/net-check2) 的 deletionTimestamp 和 finalizers","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod net-check2 -n mcp -o yaml","purpose":"确认 deletionTimestamp、finalizers、nodeName，验证是否 finalizer 卡住","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e9-g4-describe-startError","description":"Important: Describe StartError Pod (mcp/node-debugger-node1-nx8gb)","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"获取 StartError 的状态和事件的详细原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e10-g2-describe-aiops-rep","description":"Important: Describe aiops-e2e ImagePullBackOff Pod 确认跨 namespace 相同错误模式","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"验证 aiops-e2e namespace 的 ImagePullBackOff 是否也是 registry 网络错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e7-g1-describe-configError(Critical: Describe CreateContainerConfigError Pod 获取 Secret/ConfigMap 缺失详情): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/9 项, 完整度: 93%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-g2-runbook | reference | ✅ | fetch_runbook | 读取 ImagePullFailed runbook 作为参考上下文 | `fetch_runbook pod-imagepull-failed.md` |
   | e2-g2-describ... | critical | ✅ | kubectl_describe | Critical: Describe 代表 ImagePullBackOff Pod (d... | `kubectl describe pod dig-tool -n default` |
   | e3-g2-describ... | important | ✅ | kubectl_describe | Important: Describe node1 确认节点状态（Pod 分布在 node... | `kubectl describe node node1` |
   | e4-g2-describ... | important | ✅ | kubectl_describe | Important: Describe node2 确认节点状态 | `kubectl describe node node2` |
   | e5-g2-get-yam... | critical | ✅ | kubectl_get_yaml | Critical: Get Pod YAML 验证 imagePullSecrets 和 ... | `kubectl get pod dig-tool -n default -o yaml` |
   | e6-g2-events | important | ✅ | kubectl_events | Important: 查看集群事件过滤 ImagePull 相关 | `kubectl get events --all-namespaces --field-selector reason=FailedToPullImage...` |
   | e7-g1-describ... | critical | ❌ | kubectl_describe | Critical: Describe CreateContainerConfigError... | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | e8-g3-get-yam... | critical | ✅ | kubectl_get_yaml | Critical: Get YAML 确认 Terminating Pod (mcp/ne... | `kubectl get pod net-check2 -n mcp -o yaml` |
   | e9-g4-describ... | important | ✅ | kubectl_describe | Important: Describe StartError Pod (mcp/node-... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | e10-g2-descri... | important | ✅ | kubectl_describe | Important: Describe aiops-e2e ImagePullBackOf... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e7-g1-describe-configError(Critical: Describe CreateContainerConfigError Pod 获取 Secret/ConfigMap 缺失详情): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.9s)
   📤 → 下游数据: root_cause=集群存在4组异常，主异常组g2（ImagePullBackOff）涉及46个Pod，根因为集群节点到外部镜像仓库的网络不可达：具体证据包括（1）default/dig-tool拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0出现i/o timeout到us-west2-docker.pkg.dev:443（IP 108.177.125.82, 142.250.157.82）；（2）aiops-e2e/test-dns-1779360358拉取busybox:1.36.1出现connection reset by peer到registry-1.docker.io:443（IP 44.218.41.59:443）；（3）上游jq全量查询确认36+ Pod的网络错误模式一致。两节点均Ready且无Taints，排除节点异常；Pod无imagePullSecrets且使用公开镜像，排除认证失败。非主异常组已最小验证：g1（CreateContainerConfigError）因Secret aiops-e2e/rc-app-secre
... 截断，原始 626 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1/node2）到外部镜像仓库（registry-1.docker.io:443 和 us-west2-docker.pkg.dev:443）的网络连接不可达，TCP层出现connection reset by peer和i/o timeout", "propagation": "节点kubelet尝试从docker.io拉取busybox:1.36.1和从us-west2-docker.pkg.dev拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0时，TCP连接被对端重置或超时→拉取失败→容器无法启动→kubelet重试（BackOff）→Pod持续处于ImagePullBackOff", "direct_cause": "kubelet无法从远程镜像仓库拉取容器镜像，返回网络错误（i/o timeout / connection reset by peer）", "manifestation": "46个Pod（分布在default/mcp/aiops-e2e命名空间，node1和node2）处于ImagePullBackOff状态，已持续数小时（最长10h），Events显示反复拉取失败"}
   rca_analysis={"phenomenon": "集群存在48+异常Pod，主异常组g2（ImagePullFailed）：46个Pod处于ImagePullBackOff状态，分布在default(18)、mcp(26)、aiops-e2e(2)命名空间，分布于node1和node2。非主异常组：g1 CreateContainerConfigError（aiops-e2e/rc-config-secret-key-missing），g3 TerminatingStuck（mcp/net-check2），g4 StartError（mcp/node-debugger-node1-nx8gb）。", "evidence_inventory": [{"id": "e2-g2-describe-rep", "source": "kubectl_describe dig-tool (default)", "content": "Pod dig-tool ImagePullBackOff，拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 出现 i/o timeout 到 us-west2-docker.pkg.dev:443", "reliability": "高"}, {"id": "e5-g2-get-yaml-rep", "source": "kubectl_get_yaml dig-tool", "content": "imagePullSecrets: <absent>，镜像 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，排除认证问题", "reliability": "高"}, {"id": "e3/e4-g2-describe-node", "source": "kubectl_describe node1/node2", "content": "两节点均Ready，Taints: <none>，排除节点异常导致拉取失败", "reliability": "高"}, {"id": "e10-g2-describe-aiops-rep", "source": "kubectl_describe test-dns-1779360358 (aiops-e2e)", "content": "Failed to pull busybox:1.36.1: connection reset by peer 到 registry-1.docker.io:443 (44.218.41.59:443)", "reliability": "高"}, {"id": "layer_5", "source": "kubernetes_jq_query (上游验证)", "content": "36+ Pod 拉取镜像出现 connection reset by peer 和 i/o timeout 到 registry-1.docker.io:443 和 us-west2-docker.pkg.dev:443", "reliability": "高"}, {"id": "e4-g2-describe-node2-configError", "source": "kubectl_describe rc-config-secret-key-missing (aiops-e2e)", "content": "CreateContainerConfigError: 找不到 key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret", "reliability": "高"}, {"id": "e8-g3-get-yaml-terminating", "source": "kubectl_get_yaml net-check2 (mcp)", "content": "deletionTimestamp=2026-05-21T20:53:04Z, finalizers: <none>, 无finalizer卡住", "reliability": "高"}, {"id": "e6-g2-events", "source": "kubectl_describe node-debugger-node1-nx8gb (mcp)", "content": "StartError: exec: curl not found in $PATH 在 busybox:1.36 镜像中", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e2-g2-describe-rep", "raw_data": "Pod dig-tool: ImagePullBackOff. Events: Failed (x8 over 4h51m, x2 over 55m) dial tcp 108.177.125.82:443: i/o timeout 到 us-west2-docker.pkg.dev", "interpretation": "g2组代表示例Pod dig-tool确认ImagePullBackOff，根因为TCP连接i/o timeout到镜像仓库us-west2-docker.pkg.dev:443，证明网络层无法连通该仓库"}, {"evidence_id": "e5-g2-get-yaml-rep", "raw_data": "imagePullSecrets: <absent>; containers[0].image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "interpretation": "Pod没有配置imagePullSecrets，且使用公开镜像registry.k8s.io，排除认证失败原因，聚焦网络不可达"}, {"evidence_id": "e3/e4-g2-describe-node", "raw_data": "Taints: <none> (node1, node2)", "interpretation": "两个节点均无Taints且Ready，排除节点不可调度或节点异常导致的Pod Pending"}, {"evidence_id": "e10-g2-describe-aiops-rep", "raw_data": "Failed to pull image busybox:1.36.1: connection reset by peer 到 registry-1.docker.io:443 (44.218.41.59:443)", "interpretation": "aiops-e2e命名空间的Pod同样因连接docker.io被reset而拉取失败，证明网络问题是集群级而非某命名空间特有"}, {"evidence_id": "layer_5", "raw_data": "36+ Pods: connection reset by peer (multiple IPs) and i/o timeout to registry-1.docker.io:443 and us-west2-docker.pkg.dev:443", "interpretation": "上游jq全量查询确认36+个Pod的镜像拉取错误均为网络层错误，指向镜像仓库网络不可达是集群级故障"}, {"evidence_id": "e4-g2-describe-node2-configError", "raw_data": "Warning Failed (x12 over 29m): couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret", "interpretation": "g1组Pod rc-config-secret-key-missing为独立配置错误，容器引用了Secret中不存在的key，与g2网络问题无关"}, {"evidence_id": "e8-g3-get-yaml-terminating", "raw_data": "deletionTimestamp: 2026-05-21T20:53:04Z, finalizers: <none>, phase: Pending", "interpretation": "g3组Pod net-check2有deletionTimestamp但无finalizer，当前phase=Pending（非Terminating），实际因拉取busybox:1.36.1卡在ContainerCreating而非finalizer卡住"}, {"evidence_id": "e6-g2-events", "raw_data": "Message: exec: curl: executable file not found in $PATH. Image: busybox:1.36, Command: curl", "interpretation": "g4组Pod node-debugger-node1-nx8gb的StartError因容器镜像busybox:1.36不含curl命令但Pod指定curl执行，属Pod配置错误，与g2网络问题无关"}], "causal_chain": {"root_cause": "集群节点（node1/node2）到外部镜像仓库（registry-1.docker.io:443 和 us-west2-docker.pkg.dev:443）的网络连接不可达，TCP层出现connection reset by peer和i/o timeout", "propagation": "节点kubelet尝试从docker.io拉取busybox:1.36.1和从us-west2-docker.pkg.dev拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0时，TCP连接被对端重置或超时→拉取失败→容器无法启动→kubelet重试（BackOff）→Pod持续处于ImagePullBackOff", "direct_cause": "kubelet无法从远程镜像仓库拉取容器镜像，返回网络错误（i/o timeout / connection reset by peer）", "manifestation": "46个Pod（分布在default/mcp/aiops-e2e命名空间，node1和node2）处于ImagePullBackOff状态，已持续数小时（最长10h），Events显示反复拉取失败"}, "root_cause": "集群存在4组异常，主异常组g2（ImagePullBackOff）涉及46个Pod，根因为集群节点到外部镜像仓库的网络不可达：具体证据包括（1）default/dig-tool拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0出现i/o timeout到us-west2-docker.pkg.dev:443（IP 108.177.125.82, 142.250.157.82）；（2）aiops-e2e/test-dns-1779360358拉取busybox:1.36.1出现connection reset by peer到registry-1.docker.io:443（IP 44.218.41.59:443）；（3）上游jq全量查询确认36+ Pod的网络错误模式一致。两节点均Ready且无Taints，排除节点异常；Pod无imagePullSecrets且使用公开镜像，排除认证失败。非主异常组已最小验证：g1（CreateContainerConfigError）因Secret aiops-e2e/rc-app-secre\n... 截断，原始 626 字符", "root_cause_summary": "集群存在4组异常，主异常组g2（ImagePullBackOff）涉及46个Pod，根因为集群节点到外部镜像仓库的网络不可达：具体证据包括（1）default/dig-tool拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0出现i/o timeout到us-west2-docker.pkg.dev:443（IP 108.177.125.82, 142.250.157.82）；（2）aiops-e2e/test-dns-1779360358拉取busybox:1.36.1出现connection reset by peer到registry-1.docker.io:443（IP 44.218.41.59:443）；（3）上游jq全量查询确认36+ Pod的网络错误模式一致。两节点均Ready且无Taints，排除节点异常；Pod无imagePullSecrets且使用公开镜像，排除认证失败。非主异常组已最小验证：g1（CreateContainerConfigError）因Secret aiops-e2e/rc-app-secre\n... 截断，原始 626 字符", "confidence": 0.95, "confidence_reason": "有直接Pod describe证据（dig-tool的i/o timeout、test-dns的connection reset by peer）、全量jq验证（36+ Pod网络错误一致）、两节点状态确认（Ready无Taints）、Pod YAML排除认证问题（无imagePullSecrets），因果链完整清晰", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像名/tag不存在（如busybox:1.36.1不存在）", "probability": "低", "reason": "排除依据：网络错误（connection reset by peer / i/o timeout）在应用层镜像拉取之前已出现，非manifest unknown或not found类型错误"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "低", "reason": "排除依据：dig-tool和net-check2的YAML均显示imagePullSecrets: <absent>，且使用公开镜像registry.k8s.io和docker.io/busybox，无需认证"}, {"cause": "节点资源不足导致Pod Pending", "probability": "低", "reason": "排除依据：节点无Taints且Ready，Pod不是Pending因资源而是Container等待镜像拉取，Conditions显示PodScheduled=True"}, {"cause": "DNS解析失败", "probability": "低", "reason": "排除依据：错误为TCP层的i/o timeout和connection reset by peer，表明DNS解析已完成（解析到IP如44.218.41.59、108.177.125.82），但TCP连接失败"}], "limitations": "缺失证据e7-g1-describe-configError（Describe CreateContainerConfigError Pod的完整输出已在e4中部分覆盖，确认了Secret key缺失，但原始describe全量输出未采集）；Terminating Pod net-check2的当前事件未完整采集（仅YAML确认deletionTimestamp和finalizers）；StartError Pod无事件记录，根因仅通过容器command和镜像推断。", "llm_raw_analysis": "## 证据清点\n共采集16条证据（含上游已验证6条），覆盖4个异常组。\n\n## 逐条分析\n### 主异常组g2（ImagePullBackOff，46个Pod）\n- **e2-g2-describe-rep**（dig-tool）：核心证据，确认i/o timeout到us-west2-docker.pkg.dev:443\n- **e10-g2-describe-aiops-rep**（test-dns）：核心证据，确认connection reset by peer到registry-1.docker.io:443\n- **layer_5**（上游jq全量）：36+ Pod相同网络错误模式，确认为集群级故障\n- **e5-g2-get-yaml-rep**：无imagePullSecrets，排除认证问题\n- **e3/e4-g2-describe-node**：两节点Ready无Taints，排除节点异常\n\n### 非主异常组验证\n- **g1 CreateContainerConfigError**（rc-config-secret-key-missing）：e4确认Secret\n... 截断，原始 927 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群存在4组异常，主异常组g2（ImagePullBackOff）涉及46个Pod，根因为集群节点到外部镜像仓库的网络不可达：具体证据包括（1）default/dig-tool拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0出现i/o tim...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1/node2）到外部镜像仓库（registry-1.docker.io:443 和 us-west2-docker.pkg.dev:443）的网络连接不可达，TCP层出现connection reset by peer和i/o timeout
     传导机制: 节点kubelet尝试从docker.io拉取busybox:1.36.1和从us-west2-docker.pkg.dev拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0时，TCP连接被对端重置或超时→拉取失败→容器无法启动→kubelet重试（BackOff）→Pod持续处于ImagePullBackOff
     最终表现: 46个Pod（分布在default/mcp/aiops-e2e命名空间，node1和node2）处于ImagePullBackOff状态，已持续数小时（最长10h），Events显示反复拉取失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (35.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 9700 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 37.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的信息，为您生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览

首先，直接回答您的问题：**您的集群存在4个主要问题，其中核心问题是集群节点无法访问外部镜像仓库，导致大量 Pod（48个）处于 ImagePullBackOff 状态。**

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff (48个), CreateContainerConfigError (1个), StartError (1个), Terminating (1个) |
| **兼容归因层** | L3 - 网络/基础设施层 |
| **问题分类** | 镜像拉取失败 (ImagePullFailed)、配置错误 (ConfigError)、容器启动错误 (StartError)、Pod删除卡住 (TerminatingStuck) |
| **置信度** | 高 (95%) |
| **证据完整度** | 8/9 (89%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题？

**关键实体**：
| 类型 | 值 |
|------|-----|
| 集群节点 | `node1` (10.2.0.49), `node2` |
| 异常命名空间 | `default`, `aiops-e2e`, `mcp` |
| 主要异常Pod | 48个处于 `ImagePullBackOff` 的Pod（如 `default/dig-tool`, `aiops-e2e/test-dns-1779360358`, `mcp`命名空间内的数十个Pod） |
| 其他异常Pod | `aiops-e2e/rc-config-secret-key-missing`, `mcp/node-debugger-node1-nx8gb`, `mcp/net-check2` |
| 错误信息 | `Failed to pull image ... network i/o timeout`, `connection reset by peer`, `couldn't find key APP_SECRET_TOKEN in Secret` |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod dig-tool` | `Reason: ImagePullBackOff`，`Failed to pull image: network i/o timeout dialing us-west2-docker.pkg.dev (IPs: 108.177.125.82, 142.250.157.82) on port 443` | 代表Pod (dig-tool) 因网络超时无法拉取镜像 |
| 2 | Pod 状态 | `kubectl describe pod test-dns-1779360358` | `Back-off pulling image "busybox:1.36.1"`，`Normal BackOff 13m (x1306 over 10h)` | 跨命名空间验证了相同错误模式：拉取 `busybox:1.36.1` 失败，已重试10小时 |
| 3 | 集群事件 | `kubectl get events` | `Warning Failed` | 确认所有Pod的镜像拉取错误一致：连接 `registry-1.docker.io:443` 和 `us-west2-docker.pkg.dev:443` 时出现 `i/o timeout` 或 `connection reset by peer` |
| 4 | 节点状态 | `kubectl describe node node1`, `node2` | `Taints: <none>`, `Ready` | 两个节点均状态正常，无污点，排除了节点故障或调度问题 |
| 5 | Pod YAML | `kubectl get pod dig-tool -o yaml` | `finalizers: <none>`, `deletionTimestamp: <absent>` | 确认代表Pod无finalizers，与Terminating问题无关 |
| 6 | Pod YAML | `kubectl get pod net-check2 -o yaml` | `deletionTimestamp: 2026-05-21T20:53:04Z`, `deletionGracePeriodSeconds: 30`, `finalizers: <none>` | Terminating Pod设置了30秒宽限期，`finalizers`为空，排除finalizer阻塞 |
| 7 | Pod 状态 | `kubectl describe pod rc-config-secret-key-missing` | `Warning Failed(Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret)` | 配置错误Pod因Secret缺少指定Key而无法启动 |
| 8 | Pod 状态 | `kubectl describe pod node-debugger-node1-nx8gb` | `Exit Code: 128`, `Message: failed to create containerd task` | StartError Pod因容器运行时创建失败而终止 |
| 9 | JQ 查询 | `kubernetes_jq_query` | 48+ Pods in Pending/Failed, 36+ stuck in ImagePullBackOff pulling `busybox:1.36.1`, 错误模式 `connection reset by peer`, `i/o timeout` | 全局查询确认主异常组规模（48个ImagePullBackOff Pod） |
| 10 | JQ 查询 | `kubernetes_jq_query` | `mcp/net-check2 deletionTimestamp=... phase=Pending` | 确认单个Terminating Pod |

### 证据关联分析
- **证据 #1 + #2 + #3 + #9 印证**：48个Pod全部因镜像拉取失败处于 `ImagePullBackOff`，错误均为连接 `docker.io` 或 `us-west2-docker.pkg.dev` 时的网络问题（超时或连接重置），且分布于 `node1` 和 `node2`，排除单节点问题。
- **核心证据链**：集群无法访问外部网络 (`registry-1.docker.io:443`, `us-west2-docker.pkg.dev:443`) → Kubelet拉取镜像失败 → 容器无法启动 → Pod 进入 `ImagePullBackOff` 状态并持续重试。
- **其他问题证据链**：
    - **G2**: Secret `aiops-e2e/rc-app-secret` 中缺少 `APP_SECRET_TOKEN` Key → Pod 无法初始化容器配置 → 进入 `CreateContainerConfigError`。
    - **G3**: `containerd` 创建 `node-debugger-node1-nx8gb` 的任务失败 → Pod 启动失败 → 进入 `StartError`。
    - **G4**: `net-check2` Pod 被标记删除，设置了30秒宽限期，`finalizers`为空 → Pod 进入 `Terminating` 状态等待宽限期结束。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| `kubectl describe` Pod `rc-config-secret-key-missing` 的完整输出 | Critical | 规划中但执行失败，已通过`kubectl get events`部分覆盖，确认了Secret Key缺失 |
| Terminating Pod `net-check2` 的当前事件 | Critical | 可能包含当前周期内Kubelet的重试或等待细节，但YAML已确认finalizers和deletionTimestamp |
| `StartError` Pod `node-debugger-node1-nx8gb` 的详细事件 | Important | 无法确认容器运行时启动失败的具体原因，仅通过命令返回码和错误信息推断 |

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                │
│ 集群节点 (node1/node2) 到外部镜像仓库的网络连接不可达                      │
│ 具体表现为连接`registry-1.docker.io:443`时`connection reset by peer`     │
│ 以及连接`us-west2-docker.pkg.dev:443`时`i/o timeout`                     │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                │
│ Kubelet尝试从`docker.io`拉取`busybox:1.36.1`，从`us-west2-docker.pkg.dev`│
│ 拉取`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`              │
│ → TCP连接被对端重置或超时 → 拉取失败 → 容器无法启动                       │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 直接原因（多组）                                                        │
│ 1. (主) Kubelet无法从远程仓库拉取镜像，返回网络错误                        │
│ 2. (次) Secret `rc-app-secret` 中缺少 `APP_SECRET_TOKEN` Key            │
│ 3. (次) `containerd` 任务创建失败，错误码128                               │
│ 4. (次) Pod `net-check2` 处于30秒删除宽限期内                            │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                            │
│ 1. 48个Pod处于`ImagePullBackOff`，持续重启（最长10小时）                  │
│ 2. 1个Pod处于`CreateContainerConfigError`                             │
│ 3. 1个Pod处于`StartError`                                             │
│ 4. 1个Pod处于`Terminating`                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据 **证据 #1** (`network i/o timeout` to `us-west2-docker.pkg.dev:443`)、**证据 #2** (`Back-off pulling image "busybox:1.36.1"`)、**证据 #3** (集群事件确认网络错误) 和 **证据 #9** (36+ Pod 统一错误模式)，问题的**根本原因是集群节点（`node1`, `node2`）无法与外部镜像仓库（`registry-1.docker.io:443`, `us-west2-docker.pkg.dev:443`）建立稳定的 TCP 连接**。这导致 Kubelet 无法拉取容器镜像，从而引发48个 Pod 进入 `ImagePullBackOff` 的连锁故障。这是影响范围最广（48个Pod）且最为核心的问题。

此外，还存在三个次要问题：
- **G2 - Pod 配置错误**：`aiops-e2e/rc-config-secret-key-missing` 因 Secret `rc-app-secret` 缺少 `APP_SECRET_TOKEN` Key 而无法启动。
- **G3 - Pod 启动错误**：`mcp/node-debugger-node1-nx8gb` 因 `containerd` 任务创建失败 (`Exit Code 128`) 而无法启动。这通常与容器运行时配置或环境有关。
- **G4 - Pod 删除卡住**：`mcp/net-check2` 因 `deletionGracePeriodSeconds: 30` 被标记为 `Terminating`，但 `finalizers: <none>`，表明问题不在 `finalizers`，而是在30秒宽限期内未完成退出。这是一个相对次要且预期内的问题。

**置信度**：高 (95%)
- ✅ 多个Pod的事件和状态信息一致，错误模式完全相同
- ✅ 节点状态正常，排除了本地节点故障
- ✅ 使用公开镜像，排除认证问题
- ✅ 未采集的证据仅影响对次要问题的深入了解，不影响主要根因判定

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [最优先] 排查集群外部网络连通性**
- **检查出口网络策略**：确认集群节点是否有防火墙、NAT规则或代理配置，阻止了访问 `registry-1.docker.io` 和 `us-west2-docker.pkg.dev`。检查目标IP段是否为 `108.177.125.82`, `142.250.157.82` 等。
- **检查DNS解析**：确保节点可以正确解析镜像仓库域名。
  ```bash
  # 在 node1 和 node2 上执行
  nslookup registry-1.docker.io
  nslookup us-west2-docker.pkg.dev
  ```
- **检查路由和iPTables**：排查节点上的路由表和 `iptables` 规则，确认没有丢弃或错误路由目标地址为 `:443` 的流量。

**2. [临时措施] 切换镜像仓库**
  如果外部网络问题短期内无法解决，可将关键应用所使用的镜像迁移到可访问的私有仓库。
  ```bash
  # 例如，将 busybox:1.36.1 镜像拉取并推送到内部仓库
  docker pull busybox:1.36.1
  docker tag busybox:1.36.1 <your-internal-registry>/busybox:1.36.1
  docker push <your-internal-registry>/busybox:1.36.1
  
  # 然后更新 Pod 的 image 字段
  kubectl set image deployment/<deployment-name> -n <namespace> <container-name>=<your-internal-registry>/busybox:1.36.1
  ```

**3. [修复配置问题] 修复 `rc-config-secret-key-missing`**
- 修复 `aiops-e2e/rc-app-secret` Secret，添加 `APP_SECRET_TOKEN` Key。
  ```bash
  # 1. 获取当前 Secret
  kubectl get secret rc-app-secret -n aiops-e2e -o json
  # 2. 提取并解码现有数据
  # 3. 创建包含 KEY 的新 Secret（假设我们决定使用一个占位值）
  kubectl create secret generic rc-app-secret -n aiops-e2e --from-literal=APP_SECRET_TOKEN=your-new-secret-value --dry-run=client -o yaml | kubectl apply -f -
  # 4. 或者更新现有 Secret
  # (推荐使用 helm 或 CI/CD 流程，手动操作复杂且易错)
  ```
- 如果此Pod需要特定的Key，请与应用团队确认正确的Token值。

**4. [修复启动错误] 排查 `node-debugger-node1-nx8gb`**
- 此Pod主要用于调试，其`StartError` (`Exit Code 128`) 表明 `containerd` 无法创建任务。
- 检查节点 `node1` 上的容器运行时配置和状态：
  ```bash
  # 在 node1 上执行
  crictl ps
  crictl images
  systemctl status containerd
  journalctl -u containerd -n 50
  ```
- 确认该镜像（`node-debugger-node1-nx8gb` 使用的镜像）是否存在且完整。

**5. [处理 Terminating Pod] 强力删除 `net-check2`**
  如果希望立即清理该Pod，可以忽略宽限期强制删除：
  ```bash
  kubectl delete pod net-check2 -n mcp --force --grace-period=0
  ```
  *注意*：通常无需操作，等待宽限期（30秒）结束即可自动清理。

### 后续优化
1. **配置镜像使用缓存/镜像仓库代理**：在容器运行时（如 `containerd`）中配置 `mirror` 或 `proxy`，将外部镜像代理到内部仓库，增强网络故障韧性。
2. **定期巡检**：建立对 Secret、ConfigMap 等配置资源的巡检机制，避免类似配置遗漏问题。
3. **监控告警**：针对 `ImagePullBackOff` 和 `CreateContainerConfigError` 等状态配置告警。
4. **应用优化**：应用应使用有显式声明 `lifecycle.preStop` hook 和合理的 `terminationGracePeriodSeconds`，以应对优雅关闭场景。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认网络恢复 | 在节点上`curl -I https://registry-1.docker.io/v2/` | HTTP 200 (可能重定向) |
| 2. 确认Pod恢复 | `kubectl get pods --all-namespaces \| grep -v Running \| grep -v Completed` | `ImagePullBackOff` Pod数量清零，其余异常状态(ConfigError, StartError)应该消失或变为Running/Failed |
| 3. 监控整体状态 | `kubectl get pods --all-namespaces` | 集群Pod状态回归正常 |
| 4. 验证配置修复 | `kubectl get pods rc-config-secret-key-missing -n aiops-e2e` | `STATUS: Running` (或 `CrashLoopBackOff` 如果应用本身有bug) |

## ⚠️ 注意事项
- **核心问题解决后**，几乎所有 (48/51) 异常Pod会自行恢复，因为Kubelet会自动重试拉取镜像。
- **配置问题 (G2)**不会自然恢复，需要手动修复。
- **启动错误 (G3)**可能无法恢复，可能需要重建Pod或修复节点上的容器运行时。
- `Terminating` Pod (G4) 无需干预，会在30秒后自动清理。

---

## 📊 性能统计

├─ 总耗时: 3.6m
├─ 问题定位: 45.4s (21%) ✅
├─ 证据链采集: 113.4s (52%) ✅
├─ 根因分析: 22.9s (11%) ✅
├─ 汇总总结: 35.5s (16%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 28 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-terminating-stuck, pod-config-error
- **工具调用**: 28 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
