======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 21b3e797fc41436e]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先来进行全局 Pod 状态扫描，获取所有 Pod 的当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 返回 pods 列表，共约 50+ pods。正常运行 pods 约 32 个（Running），涉及 admin/aiops/aiops-e2e/default/kube-system/mcp 等 namespace。异常 pods 约 15 个：ImagePullBackOff 状态 13 个，CreateContainerConf
   💭 [问题定位] 让我更详细地查看异常 Pod 的状态。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 表格摘要: rows=8 abnormal=8 status_counts={'Pending': 8}
NAMESPACE         NAME                                                STATUS      READY   AGE                    NODE
# 异常
   💭 [问题定位] 看起来有一些 Pending 的 Pod 没有完全显示。让我获取更完整的信息。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 109 个 Pod，统计：Running=59, Succeeded=5, Pending=44, Failed=1。45 个异常行。大量 Pending Pod 集中在 mcp（node-debugger* 系列、connectivity-test、net-*、registry-diag* 等）和 default（dns-*、net-*、r
   💭 [问题定位] 好的，现在我对全局 Pod 状态有了清晰了解。让我进一步查看几个关键异常 Pod 的详情，以及获取 runbook 参考。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default) on node node1/10.2.0.49 is in Pending status with ImagePullBackOff. Container state: Waiting (Reason: ImagePullBackOff), Ready: False, Restart Count: 0. Pod IP: 172.1
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
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          10s (x6 over 47s)  kubelet            Error: cou
   💭 [问题定位] 现在让我看看那些大量 Pending Pod 的具体状态，以及获取相关 runbook。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: registry-conn-test-1779371220
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   5m12s (x54 over 4h42m)   kubelet  (combined from similar ev
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-hzpmz
namespace: mcp
node: node1/10.2.0.49
status: Succeeded
Pod 关键区块:
QoS Class: BestEffort
Node-Selectors: <none>
Tolerations: op=Exists
Containers:
  
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-test
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Normal   BackOff  6m29s (x1445 over 7h20m)  kubelet  Back-off pulling image "busybox:1.36.1"

   💭 [问题定位] 现在让我获取相关的 runbook 参考。
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
# Pod Evicted / 本地临时存储或节点资源压力驱逐

> Pod异常类型: Evicted | 典型状态: Evicted / Failed | 兼容分类: resource_eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted、Failed，或 describe
   💭 [问题定位] 让我再看看节点的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 好的，现在我有了完整的全局视图。让我整理诊断结果。
   💭 [问题定位] 调用工具: TodoWrite
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (53.0s)
   📤 → 下游数据: layer=Layer.L3, layers=L0+L3
   scenarios=[{'scenario': '镜像仓库（docker.io, registry.k8s.io）网络不可达', 'probability': '非常高', 'reason': '多个 namespace 的 Pod 均出现 ImagePullBackOff，describe 显示 dial tcp i/o timeout 到 docker.io:443 和 registry.k8s.io，网络层故障'}, {'scenario': '节点磁盘/临时存储压力导致 Pod 被驱逐', 'probability': '高', 'reason': 'xnet/observability-kibana 被 Evicted，Message 明确为 ephemeral-storage 不足，root cause 为 L0 存储驱逐'}, {'scenario': 'ConfigMap key 缺失导致 Pod 启动配置错误', 'probability': '高', 'reason': 'aiops-e2e/rc-config-configmap-key-missing 状态 CreateContainerConfigError，kubelet 报错找不到 key APP_BOOT_MODE'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}, {"type": "pod", "name": "dig-tool", "namespace": "default"}, {"type": "pod", "name": "connectivity-test", "namespace": "mcp"}, {"type": "pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "node", "name": "master", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}]
   reasoning=当前集群存在三类活跃异常：(1) 大量 ImagePullBackOff Pod（约13+个Pods，分布在default/mcp/aiops-e2e），describe 显示 dial tcp i/o timeout 到 docker.io 和 registry.k8s.io，根因为镜像仓库网络不可达，归因 L3；(2) 8个 Pending Pod（mcp namespace）虽状态 Pending，但均为 node-debugger/registry-diag/test-reg-conn 等测试类 Pod，未提供具体 Pending Reason，暂不明确根因；(3) 1个 Evicted Pod (xnet/observability-kibana-65d7c45f6d-7zc9l)，原因：节点 master 上 ephemeral-storage 不足触发驱逐，归因 L0。CreateContainerConfigError Pod (aiops-e2e/rc-config-configmap-key-missing) 因 ConfigMap 缺少 key APP_BOOT_MODE 导致，归因 L4。当前最影响集群的活跃异常是大量 ImagePullBackOff（镜像仓库访问故障），故主导层级为 L3。同时存在 L0（Evicted）和 L4（ConfigMap 配置错误）异常。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L0", "L3"], "layer_name": "ImagePullBackOff + 镜像仓库网络不可达 & Evicted (存储驱逐)", "confidence": 0.95, "reasoning": "当前集群存在三类活跃异常：(1) 大量 ImagePullBackOff Pod（约13+个Pods，分布在default/mcp/aiops-e2e），describe 显示 dial tcp i/o timeout 到 docker.io 和 registry.k8s.io，根因为镜像仓库网络不可达，归因 L3；(2) 8个 Pending Pod（mcp namespace）虽状态 Pending，但均为 node-debugger/registry-diag/test-reg-conn 等测试类 Pod，未提供具体 Pending Reason，暂不明确根因；(3) 1个 Evicted Pod (xnet/observability-kibana-65d7c45f6d-7zc9l)，原因：节点 master 上 ephemeral-storage 不足触发驱逐，归因 L0。CreateContainerConfigError Pod (aiops-e2e/rc-config-configmap-key-missing) 因 ConfigMap 缺少 key APP_BOOT_MODE 导致，归因 L4。当前最影响集群的活跃异常是大量 ImagePullBackOff（镜像仓库访问故障），故主导层级为 L3。同时存在 L0（Evicted）和 L4（ConfigMap 配置错误）异常。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-check-node2", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}, {"type": "pod", "name": "dig-tool", "namespace": "default"}, {"type": "pod", "name": "connectivity-test", "namespace": "mcp"}, {"type": "pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "pod", "name": "observability-kibana-65d7c45f6d-7zc9l", "namespace": "xnet"}, {"type": "node", "name": "master", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "镜像仓库（docker.io, registry.k8s.io）网络不可达", "probability": "非常高", "reason": "多个 namespace 的 Pod 均出现 ImagePullBackOff，describe 显示 dial tcp i/o timeout 到 docker.io:443 和 registry.k8s.io，网络层故障"}, {"scenario": "节点磁盘/临时存储压力导致 Pod 被驱逐", "probability": "高", "reason": "xnet/observability-kibana 被 Evicted，Message 明确为 ephemeral-storage 不足，root cause 为 L0 存储驱逐"}, {"scenario": "ConfigMap key 缺失导致 Pod 启动配置错误", "probability": "高", "reason": "aiops-e2e/rc-config-configmap-key-missing 状态 CreateContainerConfigError，kubelet 报错找不到 key APP_BOOT_MODE"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 41, "ErrImagePull": 2}, "total_abnormal": 43, "selected_rows": ["aiops-e2e         rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0              27s     172.16.166.142   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff             0              8h      172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              3h31m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff             0              151m    172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              7h2m    172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff             0              8h      172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff             0              5h44m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-tmp                                        0/1     ImagePullBackOff             0              158m    172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              6h50m   172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff             0              7h18m   172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff             0              4h14m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ImagePullBackOff             0              24m     172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff             0              5h12m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff             0              6h59m   172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              8h      172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff             0              7h21m   172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               curl-check-tmp                                      0/1     ImagePullBackOff             0              3h40m   172.16.104.58    node2    <none>           <none>            run=curl-check-tmp", "mcp               curls                                               0/1     ImagePullBackOff             0              120m    172.16.104.2     node2    <none>           <none>            run=curls", "mcp               dns-check-tmp                                       0/1     ImagePullBackOff             0              3h40m   172.16.104.13    node2    <none>           <none>            run=dns-check-tmp", "mcp               net-check-1779365549                                0/1     ImagePullBackOff             0              6h47m   172.16.166.179   node1    <none>           <none>            run=net-check-1779365549"], "raw_ref": "/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L0 + L3（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我来按照既有 evidence_plan 执行真实工具调用。先执行多个可以并行调用的工具。

## 开始执行既有 evidence_plan

首先并行执行所有独立工具调用：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default) is Pending on node node1/10.2.0.49. Container dig-tool is in ImagePullBackOff (Waiting state, Reason: ImagePullBackOff). Failed to pull image registry.k8s.io/e2e-test
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: registry-conn-test-1779371220
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   5m49s (x54 over 4h43m)   kubelet  (combined from similar ev
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
7m5s (x1445 over 7h21m)   Normal    BackOff   Pod/connectivity-test   Back-off pulling image "busybox:1.36.1"
49s (x81 over 6h55m)      Warning   Failed    Pod/connectivity-t
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-test
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Normal   BackOff  7m5s (x1445 over 7h21m)  kubelet  Back-off pulling image "busybox:1.36.1"
 
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
48m (x4 over 3h16m)       Warning   Failed    Pod/dig-tool   Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0": rpc error: code = DeadlineExceeded de
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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          4s (x10 over 92s)  kubelet            Error: cou
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-app-config
namespace: aiops-e2e
   💭 [证据链采集] 现在让我查看关键工具的详细输出，特别是 ConfigMap 内容和 dig-tool 的详细 events。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
48m (x4 over 3h16m)       Warning   Failed    Pod/dig-tool   Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0": rpc error: code = DeadlineExceeded de
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-app-config
namespace: aiops-e2e
   💭 [证据链采集] ConfigMap 的 YAML 被压缩了，让我用完整方式获取其内容来确认 key 是否缺失：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "apiVersion: v1\ndata:\n  EXISTING_KEY: present\nkind: ConfigMap\nmetadata:\n  annotations:\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":
   💭 [证据链采集] 现在我已获取到所有关键证据。让我读取之前被压缩的工具结果中遗漏的关键信息。
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1574 lines=10
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/001-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] [compacted ai_message: original_chars=48]
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2411 lines=48
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/002-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] [compacted ai_message: original_chars=43]
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2503 lines=49
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/004-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 好的，所有关键工具都已执行完毕。现在我来整理最终证据结论。

---

## 证据采集结论

### ✅ 已采集证据

**异常组 g1 — CreateContainerConfigError（aiops-e2e/rc-config-configmap-key-missing）**
| 证据项 | 结果 |
|--------|------|
| `kubectl describe pod rc-config-configmap-key-missing` | **确认**：`Waiting Reason=CreateContainerConfigError`，Events 明确报错 `couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config`（x10 over 92s） |
| `kubectl get configmap rc-app-config -o yaml` | **确认**：ConfigMap `rc-app-config` 中**仅包含** `EXISTING_KEY: present`，**没有** `APP_BOOT_MODE` 这个 key。根因明确：Pod env 引用了一个不存在的 ConfigMap key |

**异常组 g2 — ImagePullBackOff/ErrImagePull（主异常组，覆盖 43 个 Pod）**
| 证据项 | 结果 |
|--------|------|
| `kubectl describe pod dig-tool` (default, node1) | **确认**：Image `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，dial tcp i/o timeout 到 `asia-east1-docker.pkg.dev:443` 和 `us-west2-docker.pkg.dev:443`，x293 BackOff |
| `kubectl describe pod registry-conn-test-1779371220` (default, node2) | **确认**：Image `busybox:1.36.1`，dial tcp i/o timeout 到 `registry-1.docker.io:443`（128.121.243.107），x944 BackOff |
| `kubectl describe pod connectivity-test` (mcp, node2) | **确认**：Image `busybox:1.36.1`，dial tcp i/o timeout 到 `registry-1.docker.io:443`（108.160.161.83），x1445 BackOff |
| `kubectl get pod dig-tool -o yaml` | **确认**：`imagePullSecrets: <absent>`，Pod spec 中无私有仓库认证配置；镜像为公开镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` |
| Events - default namespace | **确认**：所有 ImagePullBackOff 事件模式一致——`Failed to pull image ... dial tcp ... :443: i/o timeout`，涉及 registry.k8s.io 和 docker.io |
| Events - mcp namespace | **确认**：connectivity-test 同样 `dial tcp registry-1.docker.io:443: i/o timeout` |

### 📋 核心证据总结

| 问题 | 影响范围 | 根因 |
|------|----------|------|
| **⚠️ 镜像仓库网络不可达** | **43 个 Pod**（41 ImagePullBackOff + 2 ErrImagePull），分布在 default、mcp、aiops-e2e 三个 namespace，node1 和 node2 均受影响 | ✅ **已确认**：节点到 `registry-1.docker.io:443`（busybox）和 `registry.k8s.io` 的镜像仓库 endpoint（`asia-east1-docker.pkg.dev:443`、`us-west2-docker.pkg.dev:443`）TCP 连接 i/o timeout，容器运行时无法拉取镜像 |
| **⚠️ ConfigMap key 缺失** | **1 个 Pod**（aiops-e2e/rc-config-configmap-key-missing） | ✅ **已确认**：Pod 引用了 ConfigMap `rc-app-config` 中的 key `APP_BOOT_MODE`，但该 ConfigMap 中仅有 `EXISTING_KEY`，缺少目标 key |

### ❌ 未发现冲突/负向证据
- 所有 `kubectl describe` 和 `kubectl get` 均返回正常结果，Pod 仍存在于指定 namespace，状态与交接一致。
- 无 NotFound、namespace 不匹配、空事件等情况。
   ✅ [证据链采集] 完成 (50.9s)
   📤 → 下游数据: evidence_items=18/20
   evidence_analysis={"evidence_plan":[{"id":"g1-state","description":"CreateContainerConfigError 异常组 g1: Pod aiops-e2e/rc-config-configmap-key-missing 当前状态和事件验证","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-config-configmap-key-missing","tool_args":{"kind":"pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e","pod":"rc-config-configmap-key-missing"},"purpose":"验证 CreateContainerConfigError 原因和 kubelet 错误原文","evidence_type":"current_state","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-configmap","description":"验证 ConfigMap aiops-e2e/rc-app-config 是否存在 key APP_BOOT_MODE","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap -n aiops-e2e rc-app-config -o yaml","tool_args":{"kind":"configmap","name":"rc-app-config","namespace":"aiops-e2e","resource":"configmap"},"purpose":"验证 ConfigMap 中是否存在 key APP_BOOT_MODE","evidence_type":"dependency_config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-dig-tool-describe","description":"ImagePullFailed 主异常组 g2: Pod default/dig-tool describe 查看错误原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dig-tool","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default","pod":"dig-tool"},"purpose":"验证 ImagePullBackOff 的详细错误信息","evidence_type":"current_state","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-registry-conn-describe","description":"ImagePullFailed 主异常组 g2: Pod default/registry-conn-test-1779371220 describe 验证 docker.io 镜像拉取失败","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default registry-conn-test-1779371220","tool_args":{"kind":"pod","name":"registry-conn-test-1779371220","namespace":"default","pod":"registry-conn-test-1779371220"},"purpose":"验证 docker.io 仓库不可达的 dial tcp timeout 错误","evidence_type":"current_state","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-connectivity-describe","description":"ImagePullFailed 主异常组 g2: Pod mcp/connectivity-test describe 验证 mcp namespace 拉取失败","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp connectivity-test","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp","pod":"connectivity-test"},"purpose":"验证 mcp namespace 下 busybox 镜像拉取失败也因 docker.io 不可达","evidence_type":"current_state","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-imagepullsecrets","description":"检查 Pod 是否配置了 imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n default dig-tool -o yaml","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default","pod":"dig-tool"},"purpose":"检查 Pod spec 中 imagePullSecrets、image 配置","evidence_type":"spec_config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-events-cluster","description":"采集 namespace default 的集群级 Events，查看 ImagePullBackOff 相关事件","level":"critical","tool":"kubectl_events","command":"kubectl get events -n default --sort-by='.lastTimestamp' | tail -30","tool_args":{"namespace":"default"},"purpose":"验证大量 ImagePullBackOff Pod 的 kubelet 拉取事件","evidence_type":"cluster_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-mcp-events","description":"采集 namespace mcp 的集群级 Events，查看 ImagePullBackOff 相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --sort-by='.lastTimestamp' | tail -30","tool_args":{"namespace":"mcp"},"purpose":"验证 mcp namespace 下 ImagePullBackOff 事件","evidence_type":"cluster_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ref-runbook-imagepull","description":"引用 pod-imagepull-failed.md runbook 确认诊断流程","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{"runbook":"pod-imagepull-failed.md"},"purpose":"参考 runbook 确认诊断分支","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ref-runbook-config","description":"引用 pod-config-error.md runbook 确认 CreateContainerConfigError 诊断","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-config-error.md","tool_args":{"runbook":"pod-config-error.md"},"purpose":"参考 runbook 确认 ConfigError 诊断分支","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod dig-tool (namespace: default) is Pending on node node1/10.2.0.49. Container dig-tool is in ImagePullBackOff (Waiting state, Reason: ImagePullBackOff). Failed to pull image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 from multiple registry endpoints (asia-east1, us-west2) with DeadlineExceeded / dial tcp i/o timeout errors. Events show repeated Failed (ErrImagePull) and BackOff over 3h25m.\nkey_facts: [\"namespace: default\", \"name: dig-tool\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: dig-tool\", \"image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"container State: Waiting (Reason: ImagePullBackOff)\", \"container Ready: False\", \"container Restart Count: 0\", \"QoS Class: BestEffort\", \"pod IP: 172.16.166.157\", \"Event Warning: Failed - Error: ErrImagePull (x27 over 3h25m)\", \"Event Warning: Failed to pull image - DeadlineExceeded dial tcp i/o timeout to asia-east1-docker.pkg.dev (142.250.157.82:443) (x4 over 3h16m)\", \"Event Warning: Failed to pull image - DeadlineExceeded dial tcp i/o timeout to us-west2-docker.pkg.dev (108.177.125.82:443) (x6 over 3h25m)\", \"Event Warning: Failed to pull image - DeadlineExceeded dial tcp i/o timeout to us-west2-docker.pkg.d\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: registry-conn-test-1779371220\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   5m49s (x54 over 4h43m)   kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 128.121.243.107:443: i/o timeout\n  Normal   BackOff  3m54s (x944 over 5h12m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: b528ad209888aece1130b096427e99e758d9f26e8dbb29d3130fe31eb1109f26\n                  cni.projectcalico.org/podIP: 172.16.104.40/32\n                  cni.projectcalico.org/podIPs: 172.16.104.40/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  registry-conn-test\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n7m5s (x1445 over 7h21m)   Normal    BackOff   Pod/connectivity-test   Back-off pulling image \"busybox:1.36.1\"\n49s (x81 over 6h55m)      Warning   Failed    Pod/connectivity-test   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.161.83:443: i/o timeout\n46m (x63 over 7h21m)      Warning   Failed    Pod/connectivity-test   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/003-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  7m5s (x1445 over 7h21m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   49s (x81 over 6h55m)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.161.83:443: i/o timeout\n      Reason:       ErrImagePull\n  Warning  Failed   46m (x63 over 7h21m)     kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n48m (x4 over 3h16m)       Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://asia-east1-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 142.250.157.82:443: i/o timeout\n35m (x6 over 3h25m)       Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 108.177.125.82:443: i/o timeout\n18m (x5 over 178m)        Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jes\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/005-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/005-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/005-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dig-tool\nnamespace: default\ncreationTimestamp: 2026-05-21T15:28:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dig-tool: image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1 || host registry-1.docker.io 2>&1 || echo DNS_CHECK_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dig-tool: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\nvolumes:\n- {\"name\": \"kube-api-access-lcm2n\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/006-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/006-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/006-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          4s (x10 over 92s)  kubelet            Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config\n                  cni.projectcalico.org/containerID: c3f68f3c291432ef6dcdea4afa9ea904811c43850537021eafd2f80e4b705cd1\n                  cni.projectcalico.org/podIP: 172.16.166.142/32\n                  cni.projectcalico.org/podIPs: 172.16.166.142/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-vr7b6:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed          4s (x10 over 92s)  kubelet            Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-app-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/008-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/008-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/008-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n48m (x4 over 3h16m)       Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://asia-east1-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 142.250.157.82:443: i/o timeout\n35m (x6 over 3h26m)       Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 108.177.125.82:443: i/o timeout\n18m (x5 over 178m)        Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 142.250.157.82:443: i/o timeout\n6m16s (x293 over 3h26m)   Normal    BackOff   Pod/dig-tool   Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\n48m (x27 over 3h26m)      Warning   Failed    Pod/dig-tool   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/009-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/009-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/009-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-app-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/010-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/010-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/010-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"apiVersion: v1\\ndata:\\n  EXISTING_KEY: present\\nkind: ConfigMap\\nmetadata:\\n  annotations:\\n    kubectl.kubernetes.io/last-applied-configuration: |\\n      {\\\"apiVersion\\\":\\\"v1\\\",\\\"data\\\":{\\\"EXISTING_KEY\\\":\\\"present\\\"},\\\"kind\\\":\\\"ConfigMap\\\",\\\"metadata\\\":{\\\"annotations\\\":{},\\\"labels\\\":{\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-app-config\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"}}\\n  creationTimestamp: \\\"2026-05-21T18:59:23Z\\\"\\n  labels:\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-app-config\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52787325\\\"\\n  uid: 84b902b0-288b-4ffb-ae96-6c3f62a72d12\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/011-evidence-run_bash_command.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1574 lines=10\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/001-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1364\ntotal_chars: 1364\ncontent:\nPod dig-tool (namespace: default) is Pending on node node1/10.2.0.49. Container dig-tool is in ImagePullBackOff (Waiting state, Reason: ImagePullBackOff). Failed to pull image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 from multiple registry endpoints (asia-east1, us-west2) with DeadlineExceeded / dial tcp i/o timeout errors. Events show repeated Failed (ErrImagePull) and BackOff over 3h25m.\nkey_facts: [\"namespace: default\", \"name: dig-tool\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: dig-tool\", \"image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"container State: Waiting (Reason: ImagePullBackOff)\", \"container Ready: False\", \"container Restart Count: 0\", \"QoS Class: BestEffort\", \"pod IP: 172.16.166.157\", \"Event Warning: Failed - Error: ErrImagePull (x27 over 3h25m)\", \"Event Warning: Failed to pull image - DeadlineExceeded dial tcp i/o timeout to asia-east1-docker.pkg.dev (142.250.157.82:443) (x4 over 3h16m)\", \"Event Warning: Failed to pull image - DeadlineExceeded dial tcp i/o timeout to us-west2-docker.pkg.dev (108.177.125.82:443) (x6 over 3h25m)\", \"Event Warning: Failed to pull image - DeadlineExceeded dial tcp i/o timeout to us-west2-docker.pkg.dev (142.250.157.82:443) (x5 over 178m)\", \"Event Normal: BackOff - Back-off pulling image (x293 over 3h25m)\"]\nmissing: [\"container ID is empty\", \"image ID is empty\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/012-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/012-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/012-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2411 lines=48\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/002-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2201\ntotal_chars: 2201\ncontent:\nkubectl_describe 摘要:\nname: registry-conn-test-1779371220\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   5m49s (x54 over 4h43m)   kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 128.121.243.107:443: i/o timeout\n  Normal   BackOff  3m54s (x944 over 5h12m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: b528ad209888aece1130b096427e99e758d9f26e8dbb29d3130fe31eb1109f26\n                  cni.projectcalico.org/podIP: 172.16.104.40/32\n                  cni.projectcalico.org/podIPs: 172.16.104.40/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  registry-conn-test-1779371220:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n      echo test\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/013-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/013-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/013-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2503 lines=49\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/004-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2293\ntotal_chars: 2293\ncontent:\nkubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  7m5s (x1445 over 7h21m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   49s (x81 over 6h55m)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.161.83:443: i/o timeout\n      Reason:       ErrImagePull\n  Warning  Failed   46m (x63 over 7h21m)     kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  connectivity-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ErrImagePull\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/014-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/014-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/21b3e797fc41436e/tools/014-evidence-read_context_archive.summary.txt"}],"llm_analysis":"好的，所有关键工具都已执行完毕。现在我来整理最终证据结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n**异常组 g1 — CreateContainerConfigError（aiops-e2e/rc-config-configmap-key-missing）**\n| 证据项 | 结果 |\n|--------|------|\n| `kubectl describe pod rc-config-configmap-key-missing` | **确认**：`Waiting Reason=CreateContainerConfigError`，Events 明确报错 `couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config`（x10 over 92s） |\n| `kubectl get configmap rc-app-config -o yaml` | **确认**：ConfigMap `rc-app-config` 中**仅包含** `EXISTING_KEY: present`，**没有** `APP_BOOT_MODE` 这个 key。根因明确：Pod env 引用了一个不存在的 ConfigMap key |\n\n**异常组 g2 — ImagePullBackOff/ErrImagePull（主异常组，覆盖 43 个 Pod）**\n| 证据项 | 结果 |\n|--------|------|\n| `kubectl describe pod dig-tool` (default, node1) | **确认**：Image `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，dial tcp i/o timeout 到 `asia-east1-docker.pkg.dev:443` 和 `us-west2-docker.pkg.dev:443`，x293 BackOff |\n| `kubectl describe pod registry-conn-test-1779371220` (default, node2) | **确认**：Image `busybox:1.36.1`，dial tcp i/o timeout 到 `registry-1.docker.io:443`（128.121.243.107），x944 BackOff |\n| `kubectl describe pod connectivity-test` (mcp, node2) | **确认**：Image `busybox:1.36.1`，dial tcp i/o timeout 到 `registry-1.docker.io:443`（108.160.161.83），x1445 BackOff |\n| `kubectl get pod dig-tool -o yaml` | **确认**：`imagePullSecrets: <absent>`，Pod spec 中无私有仓库认证配置；镜像为公开镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` |\n| Events - default namespace | **确认**：所有 ImagePullBackOff 事件模式一致——`Failed to pull image ... dial tcp ... :443: i/o timeout`，涉及 registry.k8s.io 和 docker.io |\n| Events - mcp namespace | **确认**：connectivity-test 同样 `dial tcp registry-1.docker.io:443: i/o timeout` |\n\n### 📋 核心证据总结\n\n| 问题 | 影响范围 | 根因 |\n|------|----------|------|\n| **⚠️ 镜像仓库网络不可达** | **43 个 Pod**（41 ImagePullBackOff + 2 ErrImagePull），分布在 default、mcp、aiops-e2e 三个 namespace，node1 和 node2 均受影响 | ✅ **已确认**：节点到 `registry-1.docker.io:443`（busybox）和 `registry.k8s.io` 的镜像仓库 endpoint（`asia-east1-docker.pkg.dev:443`、`us-west2-docker.pkg.dev:443`）TCP 连接 i/o timeout，容器运行时无法拉取镜像 |\n| **⚠️ ConfigMap key 缺失** | **1 个 Pod**（aiops-e2e/rc-config-configmap-key-missing） | ✅ **已确认**：Pod 引用了 ConfigMap `rc-app-config` 中的 key `APP_BOOT_MODE`，但该 ConfigMap 中仅有 `EXISTING_KEY`，缺少目标 key |\n\n### ❌ 未发现冲突/负向证据\n- 所有 `kubectl describe` 和 `kubectl get` 均返回正常结果，Pod 仍存在于指定 namespace，状态与交接一致。\n- 无 NotFound、namespace 不匹配、空事件等情况。","collection_summary":"计划 8 项，实际采集 8 项，未采集 0 项，完整度 100%；其中真实环境证据 18/18 项，完整度 100%；实际执行工具 21 个，匹配计划 8 个，未规划证据 13 个","plan_total":8,"plan_collected":8,"plan_completeness":1.0,"environment_evidence_total":18,"environment_evidence_collected":18,"environment_evidence_completeness":1.0,"executed_tool_count":21,"matched_tool_count":8,"unplanned_tool_count":13,"evidence_inventory":[{"id":"g1-state","description":"CreateContainerConfigError 异常组 g1: Pod aiops-e2e/rc-config-configmap-key-missing 当前状态和事件验证","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-config-configmap-key-missing","purpose":"验证 CreateContainerConfigError 原因和 kubelet 错误原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-configmap","description":"验证 ConfigMap aiops-e2e/rc-app-config 是否存在 key APP_BOOT_MODE","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap -n aiops-e2e rc-app-config -o yaml","purpose":"验证 ConfigMap 中是否存在 key APP_BOOT_MODE","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-dig-tool-describe","description":"ImagePullFailed 主异常组 g2: Pod default/dig-tool describe 查看错误原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dig-tool","purpose":"验证 ImagePullBackOff 的详细错误信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-registry-conn-describe","description":"ImagePullFailed 主异常组 g2: Pod default/registry-conn-test-1779371220 describe 验证 docker.io 镜像拉取失败","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default registry-conn-test-1779371220","purpose":"验证 docker.io 仓库不可达的 dial tcp timeout 错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-connectivity-describe","description":"ImagePullFailed 主异常组 g2: Pod mcp/connectivity-test describe 验证 mcp namespace 拉取失败","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp connectivity-test","purpose":"验证 mcp namespace 下 busybox 镜像拉取失败也因 docker.io 不可达","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-imagepullsecrets","description":"检查 Pod 是否配置了 imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n default dig-tool -o yaml","purpose":"检查 Pod spec 中 imagePullSecrets、image 配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-events-cluster","description":"采集 namespace default 的集群级 Events，查看 ImagePullBackOff 相关事件","level":"critical","tool":"kubectl_events","command":"kubectl get events -n default --sort-by='.lastTimestamp' | tail -30","purpose":"验证大量 ImagePullBackOff Pod 的 kubelet 拉取事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-mcp-events","description":"采集 namespace mcp 的集群级 Events，查看 ImagePullBackOff 相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --sort-by='.lastTimestamp' | tail -30","purpose":"验证 mcp namespace 下 ImagePullBackOff 事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ref-runbook-imagepull","description":"引用 pod-imagepull-failed.md runbook 确认诊断流程","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"参考 runbook 确认诊断分支","collected":false,"source":"planned","outcome":"unknown"},{"id":"ref-runbook-config","description":"引用 pod-config-error.md runbook 确认 CreateContainerConfigError 诊断","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-config-error.md","purpose":"参考 runbook 确认 ConfigError 诊断分支","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_10","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/8 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-state | critical | ✅ | kubectl_describe | CreateContainerConfigError 异常组 g1: Pod aiops-... | `kubectl describe pod -n aiops-e2e rc-config-configmap-key-missing` |
   | g1-configmap | critical | ✅ | kubectl_get_yaml | 验证 ConfigMap aiops-e2e/rc-app-config 是否存在 key... | `kubectl get configmap -n aiops-e2e rc-app-config -o yaml` |
   | g2-dig-tool-d... | critical | ✅ | kubectl_describe | ImagePullFailed 主异常组 g2: Pod default/dig-tool... | `kubectl describe pod -n default dig-tool` |
   | g2-registry-c... | critical | ✅ | kubectl_describe | ImagePullFailed 主异常组 g2: Pod default/registry... | `kubectl describe pod -n default registry-conn-test-1779371220` |
   | g2-connectivi... | important | ✅ | kubectl_describe | ImagePullFailed 主异常组 g2: Pod mcp/connectivity... | `kubectl describe pod -n mcp connectivity-test` |
   | g2-imagepulls... | important | ✅ | kubectl_get_yaml | 检查 Pod 是否配置了 imagePullSecrets | `kubectl get pod -n default dig-tool -o yaml` |
   | g2-events-clu... | critical | ✅ | kubectl_events | 采集 namespace default 的集群级 Events，查看 ImagePull... | `kubectl get events -n default --sort-by='.lastTimestamp' | tail -30` |
   | g2-mcp-events | important | ✅ | kubectl_events | 采集 namespace mcp 的集群级 Events，查看 ImagePullBack... | `kubectl get events -n mcp --sort-by='.lastTimestamp' | tail -30` |
   | ref-runbook-i... | reference | ❌ | fetch_runbook | 引用 pod-imagepull-failed.md runbook 确认诊断流程 | `fetch_runbook pod-imagepull-failed.md` |
   | ref-runbook-c... | reference | ❌ | fetch_runbook | 引用 pod-config-error.md runbook 确认 CreateConta... | `fetch_runbook pod-config-error.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (33.4s)
   📤 → 下游数据: root_cause=集群存在三类独立异常，按影响范围和严重程度排序如下：\n\n**1. [主异常] 镜像仓库网络不可达 — 影响 43 个 Pod（关键）**\n- 涉及 Pod：41 ImagePullBackOff + 2 ErrImagePull，分布在 default（dig-tool、dns-check-evidence、registry-conn-test 等约 14 个）、mcp（connectivity-test、node-debugger-* 系列、net-* 系列等约 27 个）、aiops-e2e（test-dns-1779360358）共 3 个 namespace\n- 涉及节点：node1 和 node2 均受影响（3 节点均 Ready，非节点本身故障，证据 e10）\n- 涉及镜像：公开镜像 busybox:1.36.1 和 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\n- 错误特征：所有 Pod Events 一致报告 `dial tcp ... :443: i/o timeout`（证据 e1/e2/e3/e
... 截断，原始 1095 字符
   confidence=97%
   causal_chain={"root_cause": "集群节点（node1、node2）到公共镜像仓库 registry-1.docker.io:443 和 registry.k8s.io 后端端点（asia-east1-docker.pkg.dev:443、us-west2-docker.pkg.dev:443）的网络出口不可达，TCP 连接建立均超时（dial tcp i/o timeout）", "propagation": "节点尝试拉取镜像时，kubelet 通过 containerd 向镜像仓库发起 HTTPS 请求，TCP 三次握手在 connect() 阶段超时（i/o timeout）→ containerd 返回 DeadlineExceeded 错误 → kubelet 将 Pod 容器状态标记为 ErrImagePull → 重试策略触发 BackOff → Pod 最终稳定在 ImagePullBackOff 状态，不再重试直到退避周期结束", "direct_cause": "集群出口防火墙/代理/NAT 阻止了节点到互联网镜像仓库（docker.io 和 registry.k8s.io）的出向 TCP 443 连接", "manifestation": "约 43 个 Pod（分布在 default、mcp、aiops-e2e namespace，node1 和 node2 上）持续处于 ImagePullBackOff/ErrImagePull 状态，Events 报告 dial tcp i/o timeout，所有公开镜像（busybox:1.36.1、jessie-dnsutils:1.0）均无法拉取"}
   rca_analysis={"phenomenon": "当前集群存在三类活跃异常：(1) 主异常组 ImagePullFailed — 约43个Pod（41 ImagePullBackOff + 2 ErrImagePull），分布在 default、mcp、aiops-e2e 三个 namespace，节点 node1 和 node2 均受影响，Pod 无法拉取公共镜像；(2) CreateContainerConfigError — aiops-e2e/rc-config-configmap-key-missing 因 ConfigMap key 缺失无法启动；(3) 已驱逐 Pod — xnet/observability-kibana-65d7c45f6d-7zc9l 因节点 master ephemeral-storage 不足被 Evicted。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe (dig-tool, default)", "content": "Pod dig-tool Pending, ImagePullBackOff, dial tcp i/o timeout to asia-east1-docker.pkg.dev:443 和 us-west2-docker.pkg.dev:443, x293 BackOff 超 3h25m", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe (registry-conn-test-1779371220, default)", "content": "Pod registry-conn-test Pending, ImagePullBackOff, dial tcp i/o timeout to registry-1.docker.io:443 (128.121.243.107), x944 BackOff", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe (connectivity-test, mcp)", "content": "Pod connectivity-test Pending, ErrImagePull/ImagePullBackOff, dial tcp i/o timeout to registry-1.docker.io:443 (108.160.161.83), x1445 BackOff", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_yaml (dig-tool, default)", "content": "Pod dig-tool: imagePullSecrets=<absent>, image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0（公开镜像）", "reliability": "高"}, {"id": "e5", "source": "kubectl_events (default namespace)", "content": "所有 ImagePullBackOff Pod 事件一致：Failed to pull image ... dial tcp ... :443: i/o timeout", "reliability": "高"}, {"id": "e6", "source": "kubectl_events (mcp namespace)", "content": "connectivity-test 同样 dial tcp registry-1.docker.io:443: i/o timeout", "reliability": "高"}, {"id": "e7", "source": "kubectl_describe (rc-config-configmap-key-missing, aiops-e2e)", "content": "Pod Pending, CreateContainerConfigError, Events: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config (x10 over 92s)", "reliability": "高"}, {"id": "e8", "source": "kubectl_get_yaml (ConfigMap rc-app-config)", "content": "ConfigMap rc-app-config 仅包含 EXISTING_KEY: present，缺少 APP_BOOT_MODE key", "reliability": "高"}, {"id": "e9", "source": "kubectl_describe (observability-kibana, xnet)", "content": "Pod Evicted, reason: ephemeral-storage 不足, Threshold: 46993491787, available: 45494108Ki", "reliability": "高"}, {"id": "e10", "source": "kubectl_get_by_kind_in_cluster (nodes)", "content": "3 节点均 Ready (master/node1/node2)，无节点级异常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "dial tcp 142.250.157.82:443: i/o timeout (asia-east1-docker.pkg.dev)", "interpretation": "Pod dig-tool 在 node1 上拉取 registry.k8s.io 的 jessie-dnsutils 镜像时，到 asia-east1-docker.pkg.dev:443 和 us-west2-docker.pkg.dev:443 均 TCP 超时。这不是镜像不存在或认证问题，而是网络层无法到达仓库端点。"}, {"evidence_id": "e2", "raw_data": "dial tcp 128.121.243.107:443: i/o timeout (registry-1.docker.io)", "interpretation": "Pod registry-conn-test 在 node2 上拉取 busybox:1.36.1 时到 registry-1.docker.io:443 TCP 超时。与 e1 不同的仓库地址、不同的目标 IP，但错误的模式完全一致——TCP 连接建立阶段超时。"}, {"evidence_id": "e3", "raw_data": "dial tcp 108.160.161.83:443: i/o timeout (registry-1.docker.io)", "interpretation": "Pod connectivity-test（mcp namespace）在 node2 上同样拉取 busybox:1.36.1 触发 registry-1.docker.io TCP 超时。x1445 次 BackOff 表明问题持续 7h+ 无缓解。不同 Pod、不同 namespace、不同仓库地址均超时，排除了单一 Pod 或单一镜像的配置问题。"}, {"evidence_id": "e4", "raw_data": "imagePullSecrets: <absent>", "interpretation": "Pod dig-tool 没有配置 imagePullSecrets，镜像 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 为公开镜像，不存在认证失败场景。排除 imagePullSecret 缺失/认证失败的可能性。"}, {"evidence_id": "e5", "raw_data": "Failed to pull image ... dial tcp ... :443: i/o timeout", "interpretation": "default namespace 的所有 ImagePullBackOff Pod Events 错误模式完全一致，均为 TCP 连接超时（i/o timeout），而非 404/401/refused。这强有力地指向集群出口网络或 DNS 解析到仓库 IP 后无法建立 TCP 连接。"}, {"evidence_id": "e6", "raw_data": "Back-off pulling image busybox:1.36.1, dial tcp registry-1.docker.io:443: i/o timeout", "interpretation": "mcp namespace 的 Pod 同样遭遇 registry-1.docker.io TCP 超时。两个 namespace、两个节点(node1/node2)、两个不同仓库(docker.io/registry.k8s.io)均超时，确认是集群级别的对外镜像仓库网络不可达问题。"}, {"evidence_id": "e7", "raw_data": "Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config", "interpretation": "Pod rc-config-configmap-key-missing 的 CreateContainerConfigError 根因明确：Pod env 引用了 ConfigMap rc-app-config 中的 key APP_BOOT_MODE，但该 key 在 ConfigMap 中不存在。这是应用配置错误，与网络问题无关。"}, {"evidence_id": "e8", "raw_data": "ConfigMap rc-app-config: only has EXISTING_KEY: present", "interpretation": "ConfigMap rc-app-config 确实存在但只包含 EXISTING_KEY，缺少 APP_BOOT_MODE key。直接证实了 e7 的事件描述，属于 L4 配置层问题。"}, {"evidence_id": "e9", "raw_data": "ephemeral-storage threshold: 46993491787, available: 45494108Ki", "interpretation": "节点 master 的临时存储容量不足触发驱逐，threshold 约 43.8Gi，available 约 43.4Gi（45494108Ki），接近阈值。容器 kibana 仅使用 108Ki，但节点整体存储压力大。这是独立的 L0 资源驱逐问题。"}, {"evidence_id": "e10", "raw_data": "3 nodes Ready, no abnormal conditions", "interpretation": "节点层面均健康，排除了节点不可用或 CNI 故障导致的网络问题。镜像拉取超时不是由于节点异常引起，而是节点到外网（docker.io, registry.k8s.io）的出口网络问题。"}], "causal_chain": {"root_cause": "集群节点（node1、node2）到公共镜像仓库 registry-1.docker.io:443 和 registry.k8s.io 后端端点（asia-east1-docker.pkg.dev:443、us-west2-docker.pkg.dev:443）的网络出口不可达，TCP 连接建立均超时（dial tcp i/o timeout）", "propagation": "节点尝试拉取镜像时，kubelet 通过 containerd 向镜像仓库发起 HTTPS 请求，TCP 三次握手在 connect() 阶段超时（i/o timeout）→ containerd 返回 DeadlineExceeded 错误 → kubelet 将 Pod 容器状态标记为 ErrImagePull → 重试策略触发 BackOff → Pod 最终稳定在 ImagePullBackOff 状态，不再重试直到退避周期结束", "direct_cause": "集群出口防火墙/代理/NAT 阻止了节点到互联网镜像仓库（docker.io 和 registry.k8s.io）的出向 TCP 443 连接", "manifestation": "约 43 个 Pod（分布在 default、mcp、aiops-e2e namespace，node1 和 node2 上）持续处于 ImagePullBackOff/ErrImagePull 状态，Events 报告 dial tcp i/o timeout，所有公开镜像（busybox:1.36.1、jessie-dnsutils:1.0）均无法拉取"}, "root_cause": "集群存在三类独立异常，按影响范围和严重程度排序如下：\\n\\n**1. [主异常] 镜像仓库网络不可达 — 影响 43 个 Pod（关键）**\\n- 涉及 Pod：41 ImagePullBackOff + 2 ErrImagePull，分布在 default（dig-tool、dns-check-evidence、registry-conn-test 等约 14 个）、mcp（connectivity-test、node-debugger-* 系列、net-* 系列等约 27 个）、aiops-e2e（test-dns-1779360358）共 3 个 namespace\\n- 涉及节点：node1 和 node2 均受影响（3 节点均 Ready，非节点本身故障，证据 e10）\\n- 涉及镜像：公开镜像 busybox:1.36.1 和 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\\n- 错误特征：所有 Pod Events 一致报告 `dial tcp ... :443: i/o timeout`（证据 e1/e2/e3/e\n... 截断，原始 1095 字符", "root_cause_summary": "集群存在三类独立异常，按影响范围和严重程度排序如下：\\n\\n**1. [主异常] 镜像仓库网络不可达 — 影响 43 个 Pod（关键）**\\n- 涉及 Pod：41 ImagePullBackOff + 2 ErrImagePull，分布在 default（dig-tool、dns-check-evidence、registry-conn-test 等约 14 个）、mcp（connectivity-test、node-debugger-* 系列、net-* 系列等约 27 个）、aiops-e2e（test-dns-1779360358）共 3 个 namespace\\n- 涉及节点：node1 和 node2 均受影响（3 节点均 Ready，非节点本身故障，证据 e10）\\n- 涉及镜像：公开镜像 busybox:1.36.1 和 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\\n- 错误特征：所有 Pod Events 一致报告 `dial tcp ... :443: i/o timeout`（证据 e1/e2/e3/e\n... 截断，原始 1095 字符", "confidence": 0.97, "confidence_reason": "（1）主异常组 g2（ImagePullFailed）：三个 Pod 跨 namespace（default/mcp）、跨节点（node1/node2）、跨仓库（docker.io/registry.k8s.io）的 kubectl_describe 和 kubectl_events 均一致报告 dial tcp i/o timeout，证据交叉验证充分。排除 imagePullSecrets（YAML 确认无配置）、镜像名不存在（公开镜像正确）。因果链闭环：出口网络不可达 → TCP 超时 → 拉取失败 → ImagePullBackOff。置信度 0.97。\\n（2）异常组 g1（CreateContainerConfigError）：describe 事件和 ConfigMap YAML 双重确认 key 缺失，证据直接且充分，置信度 1.0。\\n（3）Evicted 异常：describe 明确 Message 含 ephemeral-storage 不足，置信度 1.0。", "primary_runbooks": ["pod-imagepull-failed.md", "pod-config-error.md", "pod-evicted.md"], "alternative_causes": [{"cause": "镜像地址或 tag 不存在", "probability": "low", "reason": "已排除。busybox:1.36.1 和 jessie-dnsutils:1.0 均为合法公开镜像 tag，Events 报错为 TCP 超时而非 manifest unknown/not found"}, {"cause": "imagePullSecret 缺失或认证失败", "probability": "low", "reason": "已排除。Pod dig-tool YAML 显示 imagePullSecrets=<absent>，但镜像为公开镜像无需认证；且错误信息为 TCP 超时而非 401/denied"}, {"cause": "节点 CNI 或网络插件故障", "probability": "low", "reason": "已排除。3 节点均 Ready，Pod 已分配到 IP（172.16.x.x），节点间内部通信正常（部分 Succeeded Pod 已完成执行），且 3 个不同仓库地址（不同目标 IP）同时超时不符合 CNI 故障特征"}, {"cause": "DNS 解析失败", "probability": "low", "reason": "已排除。Events 显示已解析到目标 IP（如 registry-1.docker.io→128.121.243.107），在 TCP 连接阶段超时而非 DNS 查询失败"}], "limitations": "（1）缺少直接的节点出口网络探测（如节点上执行 curl/wget 到 registry-1.docker.io），无法精确判断是防火墙规则、代理配置还是 NAT 问题导致网络不可达；（2）未采集 Pod 使用的精确镜像列表确认所有 43 个 Pod 的镜像是否均为公开镜像且可拉取；（3）未验证集群是否存在镜像缓存/私有 registry mirror 配置；（4）关于 Pending Pod（8 个 mcp namespace 的 node-debugger/registry-diag/test-reg-conn 等）未提供具体 Pending Reason，它们可能因 ImagePullBackOff 间接 Pending（与 g2 重叠），也可能有其他调度原因——但已从异常组列表中排除，因它们大部分被 g2 覆盖或为测试类 Pod", "llm_raw_analysis": "按照故障诊断 L3 分析流程执行：\\n\\n1. 证据清点：共采集 10 项关键证据（e1-e10），覆盖 kubectl_describe（5个Pod）、kubectl_get_yaml（2个）、kubectl_events（2个namespace）、kubectl_get_by_kind_in_cluster（节点）。\\n\\n2. 逐条分析：\\n   - e1/e2/e3：三个跨 namespace/跨节点/跨仓库的 Pod describe 均显示相同的 dial tcp i/o timeout 错误模式，排除了单点故障可能\\n   - e4：Pod YAML 确认无 imagePullSecrets，但因镜像为公开镜像，这不构成问题——反而排除了认证失败场景\\n   - e5/e6：两个 namespace 的 Events 汇总确认所有 ImagePullBackOff Pod 错误一致，均为 TCP 超时\\n   - e7/e8：CreateContainerConfigError 根因独立确认——ConfigMap key 缺失\\n   - e9：Evicted 根因独立确\n... 截断，原始 780 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群存在三类独立异常，按影响范围和严重程度排序如下：\n\n**1. [主异常] 镜像仓库网络不可达 — 影响 43 个 Pod（关键）**\n- 涉及 Pod：41 ImagePullBackOff + 2 ErrImagePull，分布在 default（dig-tool、dns-check-e...
   置信度: 97%
   🔗 因果链:
     根本原因: 集群节点（node1、node2）到公共镜像仓库 registry-1.docker.io:443 和 registry.k8s.io 后端端点（asia-east1-docker.pkg.dev:443、us-west2-docker.pkg.dev:443）的网络出口不可达，TCP 连接建立均超时（dial tcp i/o timeout）
     传导机制: 节点尝试拉取镜像时，kubelet 通过 containerd 向镜像仓库发起 HTTPS 请求，TCP 三次握手在 connect() 阶段超时（i/o timeout）→ containerd 返回 DeadlineExceeded 错误 → kubelet 将 Pod 容器状态标记为 ErrImagePull → 重试策略触发 BackOff → Pod 最终稳定在 ImagePullBackOff 状态，不再重试直到退避周期结束
     最终表现: 约 43 个 Pod（分布在 default、mcp、aiops-e2e namespace，node1 和 node2 上）持续处于 ImagePullBackOff/ErrImagePull 状态，Events 报告 dial tcp i/o timeout，所有公开镜像（busybox:1.36.1、jessie-dnsutils:1.0）均无法拉取


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (37.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 9573 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 54.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您提供的三阶段分析结果生成的详尽诊断报告。

---
## 📊 诊断概览

您的集群当前存在 **3 类独立异常问题**，按影响范围和严重程度排序如下：

| 优先级 | 项目 | 内容 |
|:--- |:--- |:--- |
| **⛔️ 高** | **Pod异常状态** | `ImagePullBackOff` (41个), `ErrImagePull` (2个) |
| | **兼容归因层** | L3 - 基础设施层 |
| | **问题分类** | 镜像仓库网络不可达 |
| | **置信度** | 高 (97%) |
| | **影响范围** | `default`, `mcp`, `aiops-e2e` 命名空间，共 43 个 Pod |
| ---- | ---- | ---- |
| **⚠️ 中** | **Pod异常状态** | `Evicted` (1个) |
| | **兼容归因层** | L0 - 节点层 |
| | **问题分类** | 节点临时存储压力驱逐 |
| | **置信度** | 高 (95%) |
| | **影响范围** | `xnet` 命名空间，`master` 节点 |
| ---- | ---- | ---- |
| **⚠️ 低** | **Pod异常状态** | `CreateContainerConfigError` (1个) |
| | **兼容归因层** | L4 - 应用配置层 |
| | **问题分类** | ConfigMap 配置错误 |
| | **置信度** | 高 (99%) |
| | **影响范围** | `aiops-e2e` 命名空间 |

**证据完整度**: 8/8 (100%)

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体汇总**：
| 类型 | 值 |
|------|-----|
| **核心问题** | 集群内大量 Pod (43个) 因无法连接互联网镜像仓库而持续处于 `ImagePullBackOff` 状态。此外，存在 1 个因节点磁盘压力被驱逐的 Pod 和 1 个因配置缺失无法启动的 Pod。 |
| **问题 Pod 示例** | `default/dig-tool`, `default/registry-conn-test-1779371220`, `mcp/connectivity-test`, `xnet/observability-kibana-65d7c45f6d-7zc9l`, `aiops-e2e/rc-config-configmap-key-missing` |
| **受影响命名空间** | `default`, `mcp`, `aiops-e2e`, `xnet` |
| **涉及节点** | `node1`, `node2` (`ImagePullBackOff`), `master` (驱逐) |
| **错误信息样本** | `Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0" ... dial tcp ...:443: i/o timeout` |

---
## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| **主异常组 (g2): ImagePullFailed** |
| 1 | Pod 状态与事件 | `kubectl describe pod dig-tool -n default` | `Reason: ImagePullBackOff`<br>`Events: Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0" ... dial tcp ...:443: i/o timeout` (x293 BackOff over 3h25m) | `registry.k8s.io` 镜像仓库网络不可达，TCP 连接超时。 |
| 2 | Pod 状态与事件 | `kubectl describe pod registry-conn-test-1779371220 -n default` | `Back-off pulling image "busybox:1.36.1"`<br>`Events: Failed to pull image "busybox:1.36.1" ... dial tcp registry-1.docker.io:443: i/o timeout` (x944 BackOff over 5h12m) | `docker.io` 镜像仓库同样网络不可达。 |
| 3 | Pod 状态与事件 | `kubectl describe pod connectivity-test -n mcp` | `Back-off pulling image "busybox:1.36.1"`<br>`Events: Error: ErrImagePull` (x1445 BackOff over 7h21m) | `mcp` 命名空间内的 Pod 也遭遇相同的`docker.io` 拉取超时。 |
| 4 | Pod YAML 配置 | `kubectl get pod dig-tool -o yaml` | `imagePullSecrets: <none>` | Pod 未配置私有仓库认证信息，尝试拉取公开镜像失败，排除私有仓库认证问题。 |
| 5 | 集群事件 | `kubectl get events -n default` | `Warning Failed Pod/registry-conn-test-1779371220`<br>`Warning Failed Pod/dig-tool` | 收集了所有 `default` 命名空间下 Pod 的失败事件，与上述时序保持一致。 |
| 6 | 集群事件 | `kubectl get events -n mcp` | `Normal BackOff Pod/connectivity-test` (x1445 over 7h21m) | `mcp` 命名空间下大量 BackOff 事件，证实该问题是集群范围的。 |
| 7 | 节点状态 | `kubectl get nodes` | `NAME     STATUS   ROLES           AGE    VERSION`<br>`master   Ready    control-plane   ...`<br>`node1    Ready    <none>          ...`<br>`node2    Ready    <none>          ...` | 所有 3 个节点均处于 `Ready` 状态，**排除节点自身故障或 kubelet 未响应**。 |
| **异常组 (g3): Pod Evicted** |
| 8 | Pod 状态 | `kubectl describe pod observability-kibana-65d7c45f6d-7zc9l -n xnet` | `Status: Failed`<br>`Reason: Evicted`<br>`Message: The node was low on resource: ephemeral-storage.` | Pod 因节点 `master` 临时存储空间不足被驱逐。 |
| **异常组 (g1): CreateContainerConfigError** |
| 9 | Pod 状态 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | `Reason: CreateContainerConfigError`<br>`Events: Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config` | Pod 启动时无法从引用的 ConfigMap 中找到必要字段。 |
| 10 | ConfigMap 数据 | `kubectl get configmap rc-app-config -n aiops-e2e -o yaml` | `data:`<br> `  EXISTING_KEY: present`<br> `  # APP_BOOT_MODE is MISSING` | ConfigMap `rc-app-config` 存在，但确实缺少键 `APP_BOOT_MODE`。 |

### 证据关联分析

-   **证据 #1, #2, #3, #7 印证**：集群节点（`node1`, `node2`）均健康，且在拉取两个不同公共镜像仓库（`registry.k8s.io` 和 `docker.io`）的公开镜像时，都报告 `dial tcp i/o timeout`。这强烈指向 **集群层面到互联网的出口网络存在问题** (如防火墙、代理、NAT)。
-   **证据 #4**：排除了私有仓库凭据问题，问题聚焦于公共网络连通性。
-   **证据 #8**：是独立的节点资源问题。
-   **证据 #9, #10 印证**：Pod 配置与 ConfigMap 内容不一致，导致 Pod 无法启动。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 节点上直接测试网络连通性的命令（如 `curl` / `wget` / `ping` 到 `docker.io`） | **Critical** | 无法精确判断网络问题是出在防火墙、代理服务器、还是 NAT 配置上。 |
| 集群是否有配置镜像缓存 (mirror) 或私有 Registry | Important | 若存在，应优先排查 mirror/私有 Registry 的可用性。 |

---
## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (主异常)                                                                   │
│ 集群节点(node1, node2)到公共镜像仓库(registry-1.docker.io, registry.k8s.io)        │
│ 的出向网络(TCP 443)不可达，导致 TCP 连接超时(dial tcp i/o timeout)。              │
└─────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                           │
│ 1. kubelet 通过 containerd 向镜像仓库发起 HTTPS 请求                    │
│ 2. TCP 三次握手在 connect() 阶段因网络不可达而超时 (i/o timeout)                    │
│ 3. containerd 返回 DeadlineExceeded 错误                                            │
│ 4. kubelet 将 Pod 容器状态标记为 ErrImagePull                                       │
│ 5. 重试策略触发 BackOff，Pod 最终进入并稳定在 ImagePullBackOff 状态                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                           │
│ 容器镜像拉取失败 (ErrImagePull / ImagePullBackOff)                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                       │
│ 约 43 个 Pod 在 default, mcp, aiops-e2e 命名空间下持续处于                        │
│ ImagePullBackOff / ErrImagePull 状态，部分服务不可用。                              │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论 1 (主要根因)**：根据证据 #1, #2, #3 (多个 Pod，不同镜像仓库，一致的 `i/o timeout` 错误) 和证据 #7 (节点均健康 `Ready`)，当前集群存在 **“镜像仓库网络不可达”** 问题。根本原因是 **集群底层网络出口（如防火墙、代理、NAT网关）阻止了节点到 `docker.io` 和 `registry.k8s.io` 的出向 TCP 443 连接**。

- **置信度**：高 (97%)
- ✅ 证据 #1, #2, #3: 3 个 Pod，两种不同公共镜像，均报告 `dial tcp i/o timeout`。
- ✅ 证据 #7: 排除节点自身故障，进一步确认是网络出口问题。
- ⚠️ 缺少节点上的直接网络探测命令结果，无法精确锁定是防火墙规则还是代理配置问题。

**结论 2 (次要根因)**：根据证据 #8，`xnet` 命名空间下的 `observability-kibana` Pod 因节点 `master` 临时存储不足而被 **驱逐 (Evicted)**。

- **置信度**：高 (95%)

**结论 3 (次要根因)**：根据证据 #9 和 #10，`aiops-e2e` 命名空间下的 `rc-config-configmap-key-missing` Pod 因为 **ConfigMap 配置错误** (`APP_BOOT_MODE` 键缺失) 而无法启动。

- **置信度**：高 (99%)

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**优先级 1：解决网络不可达核心问题 (影响 43 个 Pod)**

```bash
# 1. 手动在任意被影响的节点上测试网络连通性，以定位问题
#    例如：登录 node1，执行以下命令
#    curl -v https://registry-1.docker.io/v2/ 2>&1 | head -20
#    curl -v https://registry.k8s.io/v2/ 2>&1 | head -20
#    如果命令执行成功，需检查是否可访问具体的镜像仓库端点。

# 2. 定位问题后，调整防火墙、代理或 NAT 规则，允许节点出站到以下域名及 IP 的 TCP 443 端口：
#    - *.docker.io
#    - *.registry.k8s.io
#    - 以及它们相关的 CDN 域名

# 3. 配置私有镜像仓库代理 (推荐方案，避免依赖外部网络)
#   在集群内或局域网内部署一个 Harbor 或 Sonatype Nexus，并配置 containerd 的 mirrors
#   例如：在 /etc/containerd/config.toml 中配置
#   [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
#     endpoint = ["http://<your_proxy_address>:5000"]
```

**优先级 2：清理被驱逐的 Pod (影响 1 个 Pod)**

```bash
# 清理被驱逐的 Pod，释放资源
kubectl delete pod <pod-name> -n xnet
# 或根据部署重新创建
```

**优先级 3：修复 ConfigMap 配置 (影响 1 个 Pod)**

```bash
# 1. 方法一：编辑 ConfigMap，添加缺失的键
kubectl edit configmap rc-app-config -n aiops-e2e

# 在 data: 部分添加如下内容：
#   APP_BOOT_MODE: "<your_desired_mode>"   # 例如 "production", "development"

# 2. 方法二：直接更新 ConfigMap (推荐)
kubectl create configmap rc-app-config -n aiops-e2e --from-literal=EXISTING_KEY=present --from-literal=APP_BOOT_MODE=production -o yaml --dry-run=client | kubectl apply -f -

# 3. 删除并重新创建引用了该 ConfigMap 的 Pod，或滚动更新其控制器
kubectl delete pod rc-config-configmap-key-missing -n aiops-e2e
```

### 后续优化

1.  **监控告警**：配置对 `ImagePullBackOff`, `Evicted`, `CreateContainerError` 等状态的 Pod 告警。
2.  **基础设施**：将私有镜像仓库 (mirror) 作为常备基础设施，降低对公共互联网的依赖，提高集群的稳定性和部署速度。
3.  **CI/CD 规范**：将 ConfigMap 和 Deployment 配置作为代码的一部分进行管理（如使用 Helm, Kustomize），并在 CI 流程中进行校验，防止配置缺失问题流入生产环境。
4.  **资源管理**：为节点关键 Pod 设置 `requests` 和 `limits` 资源限制，并关注节点磁盘使用率（可使用 `df -h` 在 master 节点上手动检查）。

---
## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 验证网络可达 | 在问题节点上执行 `curl -v https://registry-1.docker.io/v2/ 2>&1 \| grep "HTTP/"` | 返回 `HTTP/2 200` 或类似成功状态码 |
| 2. 确认 Pod 自动恢复 | `kubectl get pods -A \| grep -E 'ImagePullBackOff\|ErrImagePull'` | 返回为空，或状态变为 `Running`/`Completed` |
| 3. 确认已修复 Pod 启动 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e` | STATUS: `Running` 或 `Completed` |
| 4. 确认驱逐记录清理 | `kubectl get pod observability-kibana-* -n xnet` | 已无 `Evicted` 状态的 Pod |
| 5. 查看节点资源 | `kubectl describe node master \| grep -A 5 "ephemeral-storage"` | 显示有可用资源，无 Pressure 状态 |

---
## ⚠️ 注意事项
- **网络修复操作（如修改防火墙）应由集群基础设施管理员执行**，可能影响其他公共服务。
- 在解决网络问题后，被驱逐的 Pod 需要手动清理 (`kubectl delete pod <pod_name> -n xnet`)。
- 对于 ConfigMap 的修改，需要重新创建 Pod 才能生效。如果该 Pod 由 `Deployment` 管理，修改 ConfigMap 后仅对新 Pod 生效。如果您需要重启旧 Pod，请执行 `kubectl rollout restart deployment <deployment_name> -n <namespace>` 或直接删除该 Pod。

---

## 📊 性能统计

├─ 总耗时: 2.9m
├─ 问题定位: 53.0s (30%) ✅
├─ 证据链采集: 50.9s (29%) ✅
├─ 根因分析: 33.4s (19%) ✅
├─ 汇总总结: 37.5s (21%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 28 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-config-error, pod-evicted
- **参考 Runbook**: pod-imagepull-failed, pod-config-error, pod-evicted
- **工具调用**: 28 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
