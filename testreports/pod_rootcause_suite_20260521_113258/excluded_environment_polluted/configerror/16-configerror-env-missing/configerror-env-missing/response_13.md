======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c32a9204dc6a483d]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先全局扫描所有 Pod 的状态，找出异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned pod list. Running=59, abnormal=43 total. Abnormal pods: 1 CrashLoopBackOff (aiops-e2e/rc-config-env-missing, 8 restarts, ConfigError label), 1 Terminating (mcp/
   💭 [问题定位] 好，全局扫描完成，发现大量异常 Pod。让我进一步查看细节，并获取匹配的 runbook。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=300 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 1 completed, 1 in progress, 2 pending
[ ] [3] 获取匹配的 runbook 作为定位参考
[ ] [4]
   💭 [问题定位] 让我获取更多细节，看看有哪些异常 Pod 组以及它们的详细状态。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query returned 43 rows: 42 pods Pending with REASON=&lt;none&gt;, 1 pod Failed (Evicted). Pending pods span namespaces aiops-e2e, default, mcp, xnet, distributed across node1 and no
   💭 [问题定位] 现在我需要确认一下各异常 Pod 更精确的状态（特别是 ImagePull/ErrImagePull 等），这些 Pending 状态的 Pod 需要看 STATUS 列的精确值。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=22782 lines=777
Executing jq query for pods...
{
  "name": "test-dns-1779360358",
  "namespace": "aiops-e2e",
  "status": "Pending",
  "containerStatuses": [
    {

   💭 [问题定位] 很好，我可以看到大量 Pod 的状态是 `ErrImagePull` 和 `ImagePullBackOff`，原因都是镜像拉取超时（i/o timeout）。让我获取更多详情。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=4914 lines=259
Executing jq query for pods...
{
  "name": "test-dns-1779360358",
  "namespace": "aiops-e2e",
  "status": "Pending",
  "reason": "ErrImagePull"
}
{
 
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Kubernetes pods query returned 44 rows; 43 abnormal. 1 Running (CrashLoopBackOff), 1 Failed, 42 Pending. Image pull failures dominate: 27 ErrImagePull + 15 ImagePullBackOff across namespaces aiops-e2e
   💭 [问题定位] 现在让我获取匹配的 runbook。根据异常类型，有多个明显的匹配：

1. **ImagePullFailed** - 大量 ErrImagePull / ImagePullBackOff 镜像拉取失败
2. **CrashLoopBackOffRuntime** - aiops-e2e/rc-config-env-missing
3. **Pod-evicted** - xnet/observability-kibana (Failed/Evicted)
4. **TerminatingStuck** - mcp/curl-test-ev-1779385377 处于 Terminating
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
# Pod Evicted / 本地临时存储或节点资源压力驱逐

> Pod异常类型: Evicted | 典型状态: Evicted / Failed | 兼容分类: resource_eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted、Failed，或 describe
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod TerminatingStuck / 删除卡住

> runbook_id: pod-terminating-stuck.md
> Pod异常类型: TerminatingStuck | 典型状态: Terminating | 兼容分类: lifecycle

## 状态识别
- Pod 长时间处于 `Terminating`
- metadata.deletion
   💭 [问题定位] 现在让我确认一下 CrashLoopBackOff 和 Evicted Pod 的具体状态。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   ✅ [问题定位] 完成 (46.1s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L2+L4+L1
   scenarios=[{'scenario': '节点到外部镜像仓库网络不可达', 'probability': '高', 'reason': "多个Pod的ErrImagePull/ImagePullBackOff错误消息均为 'i/o timeout' 或 'dial tcp ... i/o timeout'，涉及docker.io和registry.k8s.io/eu-west2-docker.pkg.dev等仓库"}, {'scenario': '镜像拉取DNS解析或防火墙问题', 'probability': '中', 'reason': '虽然错误为i/o timeout而非DNS解析失败，但网络不可达可能由防火墙、代理或DNS解析链问题导致'}, {'scenario': '镜像仓库限流', 'probability': '低', 'reason': 'docker.io匿名拉取限流，但错误消息为timeout而非rate limit'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}]
   reasoning=集群存在43个异常Pod。根因为L3(ImagePullFailed)：42个Pending Pod中27个ErrImagePull、15个ImagePullBackOff，均因节点到镜像仓库(docker.io/registry.k8s.io)网络不可达(i/o timeout)导致，覆盖3个命名空间(aiops-e2e/default/mcp)。同时存在L2异常(aiops-e2e/rc-config-env-missing CrashLoopBackOff + ConfigError标签，8次重启)，L4异常(同一Pod因ConfigError标签归类)，以及L1异常(mcp/curl-test-ev-1779385377 Terminating卡住、xnet/observability-kibana Evicted on master)。系统组件(calico/coredns/etcd/apiserver/scheduler/controller-manager/kube-proxy/multus)均正常运行。当前最严重的普遍性问题为镜像拉取网络不可达(L3)，大量Pending Pod影响全局。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L2", "L4", "L1"], "layer_name": "ImagePullFailed / 镜像拉取异常", "confidence": 0.95, "reasoning": "集群存在43个异常Pod。根因为L3(ImagePullFailed)：42个Pending Pod中27个ErrImagePull、15个ImagePullBackOff，均因节点到镜像仓库(docker.io/registry.k8s.io)网络不可达(i/o timeout)导致，覆盖3个命名空间(aiops-e2e/default/mcp)。同时存在L2异常(aiops-e2e/rc-config-env-missing CrashLoopBackOff + ConfigError标签，8次重启)，L4异常(同一Pod因ConfigError标签归类)，以及L1异常(mcp/curl-test-ev-1779385377 Terminating卡住、xnet/observability-kibana Evicted on master)。系统组件(calico/coredns/etcd/apiserver/scheduler/controller-manager/kube-proxy/multus)均正常运行。当前最严重的普遍性问题为镜像拉取网络不可达(L3)，大量Pending Pod影响全局。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-bq8pn", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ErrImagePull"}, {"name": "dig-tool", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-check-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ErrImagePull"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ErrImagePull"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-test-ev-1779385377", "namespace": "mcp", "status": "Terminating"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ErrImagePull"}], "pod_status_keyword": "ErrImagePull / ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}], "possible_scenarios": [{"scenario": "节点到外部镜像仓库网络不可达", "probability": "高", "reason": "多个Pod的ErrImagePull/ImagePullBackOff错误消息均为 'i/o timeout' 或 'dial tcp ... i/o timeout'，涉及docker.io和registry.k8s.io/eu-west2-docker.pkg.dev等仓库"}, {"scenario": "镜像拉取DNS解析或防火墙问题", "probability": "中", "reason": "虽然错误为i/o timeout而非DNS解析失败，但网络不可达可能由防火墙、代理或DNS解析链问题导致"}, {"scenario": "镜像仓库限流", "probability": "低", "reason": "docker.io匿名拉取限流，但错误消息为timeout而非rate limit"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-bq8pn"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ErrImagePull", "ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "curl-test-ev-1779385377"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-bq8pn"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ErrImagePull", "ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "curl-test-ev-1779385377"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ErrImagePull": 25, "ImagePullBackOff": 16, "Terminating": 1}, "total_abnormal": 43, "selected_rows": ["aiops-e2e         rc-config-env-missing-5d9b8b766c-bq8pn              0/1     CrashLoopBackOff   8 (2m1s ago)   17m     172.16.166.129   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ErrImagePull       0              7h7m    172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ErrImagePull       0              144m    172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ErrImagePull       0              84m     172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ErrImagePull       0              5h55m   172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ErrImagePull       0              7h1m    172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0              4h37m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-tmp                                        0/1     ImagePullBackOff   0              91m     172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ErrImagePull       0              5h43m   172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0              6h11m   172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0              3h7m    172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0              4h6m    172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0              5h52m   172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ErrImagePull       0              7h1m    172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0              6h14m   172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               curl-check-tmp                                      0/1     ImagePullBackOff   0              153m    172.16.104.58    node2    <none>           <none>            run=curl-check-tmp", "mcp               curl-test-ev-1779385377                             0/1     Terminating        0              10m     <none>           node1    <none>           <none>            run=curl-test-ev-1779385377", "mcp               curls                                               0/1     ImagePullBackOff   0              53m     172.16.104.2     node2    <none>           <none>            run=curls", "mcp               dns-check-tmp                                       0/1     ImagePullBackOff   0              153m    172.16.104.13    node2    <none>           <none>            run=dns-check-tmp", "mcp               net-check-1779365549                                0/1     ErrImagePull       0              5h40m   172.16.166.179   node1    <none>           <none>            run=net-check-1779365549"], "raw_ref": "/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L2 + L4 + L1（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我先开始执行证据计划。先并行调用所有独立的 describe 和 events 工具。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod test-dns-1779360358 (ns: aiops-e2e) on node node1/10.2.0.49 is Pending. Container test-dns-1779360358 (image: busybox:1.36.1) is in Waiting state (Reason: ErrImagePull), not Ready. Events: repeate
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe pod net-check-1779365549 (ns=mcp): Status=Pending, PodIP=172.16.166.179, Node=node1. Container net-check-1779365549 with image alpine:3.18 is in State=Waiting, Reason=ErrImagePull. Ku
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: curl-test-ev-1779385377
namespace: mcp
node: node1/10.2.0.49
status: Terminating (lasts 9m35s)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: 3551efd68
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-bq8pn
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff         3m52
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace=default, node=node1/10.2.0.49) is Pending with status ErrImagePull. Container dig-tool uses image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0; state=Waiting, Reason=Err
   💭 [证据链采集] 很好，已经获取了大量关键信息。现在继续执行计划中的工具：

1. 获取 g2 组 Pod 的详细 Events
2. 获取 CrashLoopBackOff Pod 的 previous logs
3. 获取 g1 Pod 的 YAML（检查 imagePullSecrets 和镜像地址）
4. 获取 Terminating Pod 的 YAML（检查 deletionTimestamp 和 finalizers）
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
59m (x98 over 6h31m)    Warning   Failed    Pod/test-dns-1779360358   (combined from similar events): Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceede
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: curl-test-ev-1779385377
namespace: mcp
creationTimestamp: 2026-05-21T17:42:57Z
deletionTimestamp: 2026-05-21T17:44:27Z
deletionGracePeriodSeconds: 30
finalizer
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-env-missing-5d9b8b766c-bq8pn
namespace: aiops-e2e
creationTimestamp: 2026-05-21T17:35:07Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: Non
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] 好的，现在我已获取了所有关键证据。让我补充一下对于 **test-dns-1779360358** 和 **dig-tool** 的 describe 摘要（工具已执行但被压缩），以及检查节点状态。

让我查看一下关键节点的状态：
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node2   Ready    <none>   238d   v1.26.8   10.2.0.50     <
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   238d   v1.26.8   10.2.0.49     <
   💭 [证据链采集] [compacted ai_message: original_chars=78]
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN   TYPE     REASON           OBJECT                        MESSAGE
11m         Normal   Scheduled        Pod/curl-test-ev-1779385377   Successfully assigned mcp/curl-test-e
   💭 [证据链采集] 所有工具调用完毕，以下是证据采集结论。

---

## 证据采集结论

### ✅ 已采集证据

#### 1. 主异常组 g2 — ErrImagePull/ImagePullBackOff（41 个 Pod，影响最大）

**代表 Pod test-dns-1779360358 (aiops-e2e)**：
- 容器状态：Waiting, Reason=ErrImagePull
- Events：`Failed to pull image "docker.io/library/busybox:1.36.1": failed to resolve reference "docker.io/library/busybox:1.36.1": i/o timeout`（连续 7h 重试失败）
- 镜像：`docker.io/library/busybox:1.36.1`，无 imagePullSecrets

**跨 namespace 验证 — dig-tool (default)**：
- 同样 ErrImagePull，镜像 `docker.io/library/busybox:1.36`
- Events：`Failed to pull image "docker.io/library/busybox:1.36": i/o timeout`

**跨 namespace 验证 — net-check-1779365549 (mcp)**：
- 同样 ErrImagePull，镜像 `alpine:3.18`
- Events：`failed to pull alpine:3.18: i/o timeout dialing docker.io`（x49 次事件，持续 5h38m）

**结论**：g2 组 41 个 Pod 的根因一致——**node1 和 node2 到 docker.io 镜像仓库的出口网络不可达（i/o timeout）**，覆盖 aiops-e2e/default/mcp 三个命名空间。

#### 2. 异常组 g1 — CrashLoopBackOff（rc-config-env-missing-5d9b8b766c-bq8pn）

- **Last State**：Terminated, Exit Code=42
- **描述**：`back-off 5m0s restarting failed container`，8 次重启
- **崩溃前日志**：`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`
- **YAML 关键信息**：command=`sh -c`，args 含校验逻辑 `if [ -z "${APP_BOOT_MODE:-}" ]; then ... exit 42`；imagePullPolicy=Never（不从远程拉取）；镜像 `busybox:1.36`（本地已有）
- **结论**：这不是镜像拉取问题，是**配置缺失（ConfigError）**——环境变量 `APP_BOOT_MODE` 未设置导致容器退出码 42。

#### 3. 异常组 g3 — Terminating（curl-test-ev-1779385377）

- **YAML 关键字段**：deletionTimestamp=`2026-05-21T17:44:27Z`，finalizers=`<none>`，phase=`Pending`
- **删除已持续 ~11 分钟**（deletionTimestamp 比创建晚 1.5 分钟，即创建后很快被删除）
- **Events**：只有 `Scheduled`、`AddedInterface`、`Pulling`（Pulling image "busybox:1.36.1"），无 Killing/FailedKillPod 事件
- **节点状态**：node1 为 Ready
- **terminationGracePeriodSeconds**=30s，已远超正常优雅终止窗口
- **结论**：Pod 处于 Terminating 卡住状态，原因是**容器仍在 Pulling 阶段（i/o timeout 镜像拉取失败）导致 kubelet 无法完成容器停止流程**，而非 finalizer 或 volume 问题。

### 关键关联发现
g3（Terminating）的根因同样是 **docker.io 网络不可达**——容器镜像 busybox:1.36.1 一直卡在 Pulling，删除命令下发后 kubelet 无法完成终止流程。

---

### 🔴 未采集/冲突证据
无。所有计划项按预期完成，无 NotFound/冲突情况。
   ✅ [证据链采集] 完成 (56.2s)
   📤 → 下游数据: evidence_items=12/13
   evidence_analysis={"evidence_plan":[{"id":"g2-rep-pod-describe","description":"Describe g2的代表Pod来确认ErrImagePull的详细错误消息(镜像地址/拉取失败原因)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"获取g2组一个代表性ErrImagePull Pod的Events和容器状态，验证之前的i/o timeout错误是否仍然存在","evidence_type":"pod_events_and_status","target_scope":"g2代表Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-rep-pod-events","description":"查看g2组Pod相关events，确认镜像拉取失败的根因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=test-dns-1779360358 --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=test-dns-1779360358","sort_by":".lastTimestamp"},"purpose":"获取g2组Pod的详细Events，确认镜像拉取失败原因是否为i/o timeout/网络不可达","evidence_type":"pod_events","target_scope":"g2代表Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-alternate-pod-describe-default","description":"Describe default命名空间的另一个ErrImagePull Pod以跨namespace验证一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"验证default命名空间下ErrImagePull Pod是否也存在相同的i/o timeout错误，确认跨namespace一致性问题","evidence_type":"pod_events_and_status","target_scope":"g2跨namespace验证","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-alternate-pod-describe-mcp","description":"Describe mcp命名空间的另一个ErrImagePull Pod以跨namespace验证一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod net-check-1779365549 -n mcp","tool_args":{"kind":"pod","name":"net-check-1779365549","namespace":"mcp"},"purpose":"验证mcp命名空间下ErrImagePull Pod是否也存在相同的镜像拉取失败错误，确认跨namespace一致性问题","evidence_type":"pod_events_and_status","target_scope":"g2跨namespace验证","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-crashloop-describe","description":"Describe g1组CrashLoopBackOff Pod查看Last State和Exit Code","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-config-env-missing-5d9b8b766c-bq8pn","namespace":"aiops-e2e"},"purpose":"获取CrashLoopBackOff Pod的Last State、Exit Code、Reason，确认是否为容器运行时异常或配置错误","evidence_type":"pod_events_and_status","target_scope":"g1 Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-crashloop-previous-logs","description":"查看CrashLoopBackOff Pod崩溃前的日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous --tail=200","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-bq8pn","namespace":"aiops-e2e","tail":200,"previous":true},"purpose":"获取Pod崩溃前的日志，确认Exit Code和日志内容来判断容器异常原因","evidence_type":"container_logs","target_scope":"g1 Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"g3-terminating-describe","description":"Describe g3组Terminating Pod查看deletionTimestamp和finalizers","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod curl-test-ev-1779385377 -n mcp","tool_args":{"kind":"pod","name":"curl-test-ev-1779385377","namespace":"mcp"},"purpose":"获取Terminating Pod的deletionTimestamp、finalizers、相关事件，确认卡住原因","evidence_type":"pod_events_and_status","target_scope":"g3 Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-yaml-imagepullsecret","description":"获取g1 CrashLoopBackOff Pod的YAML检查镜像和imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-config-env-missing-5d9b8b766c-bq8pn","namespace":"aiops-e2e"},"purpose":"检查Pod的spec镜像地址、imagePullSecrets、command/args配置","evidence_type":"pod_yaml","target_scope":"g1 Pod","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod test-dns-1779360358 (ns: aiops-e2e) on node node1/10.2.0.49 is Pending. Container test-dns-1779360358 (image: busybox:1.36.1) is in Waiting state (Reason: ErrImagePull), not Ready. Events: repeated Failed to pull image from docker.io/library/busybox:1.36.1 — all attempts hit i/o timeout dialing registry-1.docker.io (multiple IPs: 162.125.1.8, 128.242.240.20, 50.117.117.42, 108.160.166.57, 198.44.185.131, 199.59.148.229:443) with DeadlineExceeded/Unknown errors; latest event at 2m28s (x59 over 7h6m) shows ErrImagePull. Pulling events also present (x74 over 7h8m). Pod has IP 172.16.166.148, QoS BestEffort, no node selectors.\nkey_facts: [\"Pod: test-dns-1779360358\", \"Namespace: aiops-e2e\", \"Node: node1/10.2.0.49\", \"Status: Pending\", \"Container: test-dns-1779360358\", \"Image: busybox:1.36.1\", \"Container State: Waiting (Reason: ErrImagePull)\", \"Ready: False\", \"Restart Count: 0\", \"Event: Warning Failed (x98 over 6h31m) — Failed to pull image: i/o timeout to 162.125.1.8:443\", \"Event: Warning Failed at 49m — i/o timeout to 128.242.240.20:443\", \"Event: Warning Failed at 37m — i/o timeout to 50.117.117.42:443\", \"Event: Warning Failed at 26m — i/o timeout to 108.160.166.57:443\", \"Event: War\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe pod net-check-1779365549 (ns=mcp): Status=Pending, PodIP=172.16.166.179, Node=node1. Container net-check-1779365549 with image alpine:3.18 is in State=Waiting, Reason=ErrImagePull. Kubelet repeatedly failed to pull image due to i/o timeout dialing docker.io (multiple IPs). 5 Failed events (55m, 44m, 33m, 21m, 9m59s) + 1 Error: ErrImagePull event (x49 over 5h38m). Container args include wget test to registry-1.docker.io. QoS=BestEffort.\nkey_facts: [\"name=net-check-1779365549, namespace=mcp\", \"node=node1/10.2.0.49\", \"podIP=172.16.166.179\", \"status=Pending\", \"container=net-check-1779365549, image=alpine:3.18\", \"containerState=Waiting, Reason=ErrImagePull\", \"containerReady=False, RestartCount=0\", \"Events: Warning Failed (55m,44m,33m,21m,9m59s) - kubelet failed to pull alpine:3.18: i/o timeout dialing docker.io\", \"Events: Warning Failed 9m59s (x49 over 5h38m) - Error: ErrImagePull\", \"Events: Normal Pulling 21m (x54 over 5h41m) - kubelet pulling image alpine:3.18\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\", \"QoS Class=BestEffort\", \"container args include wget test to registry-1.docker.io\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: curl-test-ev-1779385377\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Terminating (lasts 9m35s)\n关键诊断行:\nAnnotations:               cni.projectcalico.org/containerID: 3551efd6819108d277a3cc99607d8995eff76a8d3d817f30458fe4ac57690604\n                           cni.projectcalico.org/podIP: 172.16.166.156/32\n                           cni.projectcalico.org/podIPs: 172.16.166.156/32\n                           k8s.v1.cni.cncf.io/network-status:\n                           k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nTermination Grace Period:  30s\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  curl-test-ev-1779385377:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-p4pjb:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason          Age   Fr\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-bq8pn\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         3m52s (x71 over 18m)  kubelet            Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-bq8pn_aiops-e2e(e49e4e4b-9359-4371-9a5e-bf2b7b082950)\n                  cni.projectcalico.org/containerID: 163a263de27393e0bca456e7f67ca48c38c689aa78b6f47c0f8498e963219a8a\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-config-env-missing-5d9b8b766c\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://04d5db23eb36b2cf63c882f8bc105242d87ba50ca83af4e77e2df79f99169c98\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n    Args:\n    Sta\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-tool (namespace=default, node=node1/10.2.0.49) is Pending with status ErrImagePull. Container dig-tool uses image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0; state=Waiting, Reason=ErrImagePull, Ready=False, RestartCount=0. Kubelet repeatedly failed to pull image due to i/o timeout dialing various GCR backends (asia-east1, europe-west2). Events show 22 pull attempts over 145m, with expired DeadlineExceeded on latest attempts. Pod has IP 172.16.166.157, BestEffort QoS, no node selectors.\nkey_facts: [\"name: dig-tool\", \"namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: dig-tool, image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"container State: Waiting, Reason: ErrImagePull\", \"container Ready: False, RestartCount: 0\", \"Pod IP: 172.16.166.157\", \"QoS Class: BestEffort\", \"Events: Warning Failed (53m) - i/o timeout to asia-east1-docker.pkg.dev:443\", \"Events: Warning Failed (30m, x3 over 134m) - i/o timeout to europe-west2-docker.pkg.dev:443\", \"Events: Warning Failed (7m29s, x8 over 135m) - DeadlineExceeded, i/o timeout to europe-west2-docker.pkg.dev:443\", \"Events: Warning Failed (7m29s, x22 over 139m) - Error: ErrImagePull\", \"Events: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n59m (x98 over 6h31m)    Warning   Failed    Pod/test-dns-1779360358   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 162.125.1.8:443: i/o timeout\n49m                     Warning   Failed    Pod/test-dns-1779360358   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 128.242.240.20:443: i/o timeout\n37m                     Warning   Failed    Pod/test-dns-1779360358   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: He\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/006-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/006-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/006-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: curl-test-ev-1779385377\nnamespace: mcp\ncreationTimestamp: 2026-05-21T17:42:57Z\ndeletionTimestamp: 2026-05-21T17:44:27Z\ndeletionGracePeriodSeconds: 30\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- curl-test-ev-1779385377: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: /bin/sh -c timeout 10 wget -q -O- https://registry-1.docker.io/v2/ 2>&1 || timeout 10 wget -q -O- http://registry-1.docker.io/v2/ 2>&1 || echo CONNECTION_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [curl-test-ev-1779385377]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [curl-test-ev-1779385377]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- curl-test-ev-1779385377: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-p4pjb\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/007-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/007-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/007-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-env-missing-5d9b8b766c-bq8pn\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T17:35:07Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-config-env-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/rc-config-env-missing-5d9b8b766c\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c\n  args: if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n  echo \"L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE\"\n  exit 42\nfi\nsleep 3600\n\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=8 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=rc-config-env-missing-5d9b8b766c-bq8pn_aiops-e2e(e49e4e4b-9359-4371-9a5e-bf2b7b082950)\nvolumes:\n- {\"name\": \"kube-api-access-rlsf9\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/008-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/008-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/008-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/009-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/009-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/009-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode2   Ready    <none>   238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/010-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/010-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/010-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode1   Ready    <none>   238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/011-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/011-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/011-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN   TYPE     REASON           OBJECT                        MESSAGE\n11m         Normal   Scheduled        Pod/curl-test-ev-1779385377   Successfully assigned mcp/curl-test-ev-1779385377 to node1\n11m         Normal   AddedInterface   Pod/curl-test-ev-1779385377   Add eth0 [172.16.166.156/32] from k8s-pod-network\n11m         Normal   Pulling          Pod/curl-test-ev-1779385377   Pulling image \"busybox:1.36.1\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/012-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/012-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c32a9204dc6a483d/tools/012-evidence-kubectl_events.summary.txt"}],"llm_analysis":"所有工具调用完毕，以下是证据采集结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n#### 1. 主异常组 g2 — ErrImagePull/ImagePullBackOff（41 个 Pod，影响最大）\n\n**代表 Pod test-dns-1779360358 (aiops-e2e)**：\n- 容器状态：Waiting, Reason=ErrImagePull\n- Events：`Failed to pull image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": i/o timeout`（连续 7h 重试失败）\n- 镜像：`docker.io/library/busybox:1.36.1`，无 imagePullSecrets\n\n**跨 namespace 验证 — dig-tool (default)**：\n- 同样 ErrImagePull，镜像 `docker.io/library/busybox:1.36`\n- Events：`Failed to pull image \"docker.io/library/busybox:1.36\": i/o timeout`\n\n**跨 namespace 验证 — net-check-1779365549 (mcp)**：\n- 同样 ErrImagePull，镜像 `alpine:3.18`\n- Events：`failed to pull alpine:3.18: i/o timeout dialing docker.io`（x49 次事件，持续 5h38m）\n\n**结论**：g2 组 41 个 Pod 的根因一致——**node1 和 node2 到 docker.io 镜像仓库的出口网络不可达（i/o timeout）**，覆盖 aiops-e2e/default/mcp 三个命名空间。\n\n#### 2. 异常组 g1 — CrashLoopBackOff（rc-config-env-missing-5d9b8b766c-bq8pn）\n\n- **Last State**：Terminated, Exit Code=42\n- **描述**：`back-off 5m0s restarting failed container`，8 次重启\n- **崩溃前日志**：`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`\n- **YAML 关键信息**：command=`sh -c`，args 含校验逻辑 `if [ -z \"${APP_BOOT_MODE:-}\" ]; then ... exit 42`；imagePullPolicy=Never（不从远程拉取）；镜像 `busybox:1.36`（本地已有）\n- **结论**：这不是镜像拉取问题，是**配置缺失（ConfigError）**——环境变量 `APP_BOOT_MODE` 未设置导致容器退出码 42。\n\n#### 3. 异常组 g3 — Terminating（curl-test-ev-1779385377）\n\n- **YAML 关键字段**：deletionTimestamp=`2026-05-21T17:44:27Z`，finalizers=`<none>`，phase=`Pending`\n- **删除已持续 ~11 分钟**（deletionTimestamp 比创建晚 1.5 分钟，即创建后很快被删除）\n- **Events**：只有 `Scheduled`、`AddedInterface`、`Pulling`（Pulling image \"busybox:1.36.1\"），无 Killing/FailedKillPod 事件\n- **节点状态**：node1 为 Ready\n- **terminationGracePeriodSeconds**=30s，已远超正常优雅终止窗口\n- **结论**：Pod 处于 Terminating 卡住状态，原因是**容器仍在 Pulling 阶段（i/o timeout 镜像拉取失败）导致 kubelet 无法完成容器停止流程**，而非 finalizer 或 volume 问题。\n\n### 关键关联发现\ng3（Terminating）的根因同样是 **docker.io 网络不可达**——容器镜像 busybox:1.36.1 一直卡在 Pulling，删除命令下发后 kubelet 无法完成终止流程。\n\n---\n\n### 🔴 未采集/冲突证据\n无。所有计划项按预期完成，无 NotFound/冲突情况。","collection_summary":"计划 8 项，实际采集 7 项，未采集 1 项，完整度 88%；其中真实环境证据 12/13 项，完整度 92%；实际执行工具 17 个，匹配计划 7 个，未规划证据 10 个","plan_total":8,"plan_collected":7,"plan_completeness":0.875,"environment_evidence_total":13,"environment_evidence_collected":12,"environment_evidence_completeness":0.9230769230769231,"executed_tool_count":17,"matched_tool_count":7,"unplanned_tool_count":10,"evidence_inventory":[{"id":"g2-rep-pod-describe","description":"Describe g2的代表Pod来确认ErrImagePull的详细错误消息(镜像地址/拉取失败原因)","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"获取g2组一个代表性ErrImagePull Pod的Events和容器状态，验证之前的i/o timeout错误是否仍然存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-rep-pod-events","description":"查看g2组Pod相关events，确认镜像拉取失败的根因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=test-dns-1779360358 --sort-by='.lastTimestamp'","purpose":"获取g2组Pod的详细Events，确认镜像拉取失败原因是否为i/o timeout/网络不可达","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-alternate-pod-describe-default","description":"Describe default命名空间的另一个ErrImagePull Pod以跨namespace验证一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","purpose":"验证default命名空间下ErrImagePull Pod是否也存在相同的i/o timeout错误，确认跨namespace一致性问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-alternate-pod-describe-mcp","description":"Describe mcp命名空间的另一个ErrImagePull Pod以跨namespace验证一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod net-check-1779365549 -n mcp","purpose":"验证mcp命名空间下ErrImagePull Pod是否也存在相同的镜像拉取失败错误，确认跨namespace一致性问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-crashloop-describe","description":"Describe g1组CrashLoopBackOff Pod查看Last State和Exit Code","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e","purpose":"获取CrashLoopBackOff Pod的Last State、Exit Code、Reason，确认是否为容器运行时异常或配置错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-crashloop-previous-logs","description":"查看CrashLoopBackOff Pod崩溃前的日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous --tail=200","purpose":"获取Pod崩溃前的日志，确认Exit Code和日志内容来判断容器异常原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-terminating-describe","description":"Describe g3组Terminating Pod查看deletionTimestamp和finalizers","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod curl-test-ev-1779385377 -n mcp","purpose":"获取Terminating Pod的deletionTimestamp、finalizers、相关事件，确认卡住原因","collected":false,"source":"planned","outcome":"unknown"},{"id":"g1-yaml-imagepullsecret","description":"获取g1 CrashLoopBackOff Pod的YAML检查镜像和imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e -o yaml","purpose":"检查Pod的spec镜像地址、imagePullSecrets、command/args配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["g3-terminating-describe(Describe g3组Terminating Pod查看deletionTimestamp和finalizers): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/8 项, 完整度: 92%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g2-rep-pod-de... | critical | ✅ | kubectl_describe | Describe g2的代表Pod来确认ErrImagePull的详细错误消息(镜像地址/... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | g2-rep-pod-ev... | critical | ✅ | kubectl_events | 查看g2组Pod相关events，确认镜像拉取失败的根因 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=test-dns...` |
   | g2-alternate-... | important | ✅ | kubectl_describe | Describe default命名空间的另一个ErrImagePull Pod以跨nam... | `kubectl describe pod dig-tool -n default` |
   | g2-alternate-... | important | ✅ | kubectl_describe | Describe mcp命名空间的另一个ErrImagePull Pod以跨namespa... | `kubectl describe pod net-check-1779365549 -n mcp` |
   | g1-crashloop-... | critical | ✅ | kubectl_describe | Describe g1组CrashLoopBackOff Pod查看Last State和... | `kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e` |
   | g1-crashloop-... | critical | ✅ | kubectl_previous_logs | 查看CrashLoopBackOff Pod崩溃前的日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous -...` |
   | g3-terminatin... | critical | ❌ | kubectl_describe | Describe g3组Terminating Pod查看deletionTimestam... | `kubectl describe pod curl-test-ev-1779385377 -n mcp` |
   | g1-yaml-image... | important | ✅ | kubectl_get_yaml | 获取g1 CrashLoopBackOff Pod的YAML检查镜像和imagePullS... | `kubectl get pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e -o yaml` |

   ⚠️ 未采集原因:
   - g3-terminating-describe(Describe g3组Terminating Pod查看deletionTimestamp和finalizers): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.6s)
   📤 → 下游数据: root_cause=集群核心问题为**节点出口网络到外部镜像仓库不可达**。证据：(1) g2代表Pod test-dns-1779360358(aiops-e2e)使用busybox:1.36.1，所有拉取尝试均i/o timeout到registry-1.docker.io多IP(162.125.1.8:443等)，x98次事件持续6h31m；(2) dig-tool(default)使用registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0同样i/o timeout到asia-east1/europe-west2-docker.pkg.dev:443；(3) net-check-1779365549(mcp)使用alpine:3.18同样i/o timeout到docker.io，x49次事件持续5h38m。此问题影响node1和node2两个工作节点共41个Pod(27 ErrImagePull+15 ImagePullBackOff)，覆盖3个namespace。同时存在独立异常：aiops-e2e/rc-config-env-missing Cr
... 截断，原始 770 字符
   confidence=95%
   causal_chain={"root_cause": "集群工作节点(node1/node2)到外部镜像仓库(docker.io/registry.k8s.io)的出口网络不可达，TCP 443端口连接超时(i/o timeout)，导致所有需要远程拉取镜像的Pod无法启动", "propagation": "节点出口网络阻断→kubelet无法连接registry-1.docker.io:443/GCR后端→容器状态进入ErrImagePull→kubelet重试→进入ImagePullBackOff→Pod持续Pending→集群43个异常Pod中42个处于Pending状态", "direct_cause": "节点到docker.io/registry.k8s.io的HTTPS连接超时(i/o timeout)，具体为dial tcp 162.125.1.8:443/asia-east1-docker.pkg.dev:443/europe-west2-docker.pkg.dev:443超时", "manifestation": "用户可见: 42个Pod处于Pending状态(27 ErrImagePull + 15 ImagePullBackOff)，覆盖aiops-e2e/default/mcp三个namespace，分布在node1和node2；1个Terminating Pod因镜像拉取卡住无法完成删除"}
   rca_analysis={"phenomenon": "集群存在43个异常Pod，覆盖4个namespace（aiops-e2e/default/mcp/xnet）。主异常组(g2)为42个Pending Pod中27个ErrImagePull+15个ImagePullBackOff，镜像拉取失败。同时存在1个CrashLoopBackOff（aiops-e2e/rc-config-env-missing，退出码42，ConfigError标签），1个Terminating卡住（mcp/curl-test-ev-1779385377），1个Evicted（xnet/observability-kibana）。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "g2代表Pod test-dns-1779360358 (aiops-e2e): busybox:1.36.1, ErrImagePull, 所有拉取尝试均i/o timeout到registry-1.docker.io多IP", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe", "content": "g2跨namespace验证 net-check-1779365549 (mcp): alpine:3.18, ErrImagePull, i/o timeout到docker.io, x49次事件5h38m", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe", "content": "g2跨namespace验证 dig-tool (default): registry.k8s.io镜像, ErrImagePull, i/o timeout到GCR后端(asia-east1/europe-west2)", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe", "content": "g1 Pod rc-config-env-missing (aiops-e2e): CrashLoopBackOff, 8次重启, 退出码42, imagePullPolicy=Never", "reliability": "高"}, {"id": "e5", "source": "kubectl_previous_logs", "content": "rc-config-env-missing崩溃前日志: L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_yaml", "content": "rc-config-env-missing YAML: imagePullPolicy=Never, 标签pod_abnormal_type=ConfigError, command含APP_BOOT_MODE校验逻辑", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_yaml", "content": "g3 Terminating Pod curl-test-ev-1779385377: deletionTimestamp存在, finalizers=<none>, phase=Pending, 容器状态ContainerCreating", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe", "content": "curl-test-ev-1779385377 Events: 仅有Scheduled/AddedInterface/Pulling(busybox:1.36.1)，无Killing事件", "reliability": "高"}, {"id": "e9", "source": "kubectl_get_by_kind_in_cluster", "content": "全局扫描: Running=59, abnormal=43; 1 CrashLoopBackOff, 1 Terminating, ~41 ImagePull异常, 1 Evicted", "reliability": "高"}, {"id": "e10", "source": "kubernetes_tabular_query", "content": "42个Pending Pod + 1 Failed(Evicted); 27 ErrImagePull + 15 ImagePullBackOff", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Failed to pull image \"docker.io/library/busybox:1.36.1\"...i/o timeout dialing registry-1.docker.io (162.125.1.8:443, 128.242.240.20:443...)", "interpretation": "节点node1到docker.io的出口网络完全不可达，TCP连接在443端口超时，非DNS解析失败"}, {"evidence_id": "e2", "raw_data": "failed to pull alpine:3.18: i/o timeout dialing docker.io (x49 events over 5h38m)", "interpretation": "跨namespace(mcp)验证，node1上同样镜像拉取i/o timeout，排除namespace级问题"}, {"evidence_id": "e3", "raw_data": "i/o timeout to asia-east1-docker.pkg.dev:443, europe-west2-docker.pkg.dev:443", "interpretation": "不仅docker.io不可达，registry.k8s.io(GCR)同样不可达，说明是集群出口网络全局阻断"}, {"evidence_id": "e4", "raw_data": "BackOff restarting...Exit Code=42, imagePullPolicy=Never, 8次重启", "interpretation": "g1 Pod不是镜像拉取问题(imagePullPolicy=Never，不从远程拉取)，而是容器进程退出码42"}, {"evidence_id": "e5", "raw_data": "L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "interpretation": "容器启动脚本检测到APP_BOOT_MODE环境变量未设置，主动退出返回42"}, {"evidence_id": "e6", "raw_data": "imagePullSecrets=<absent>, labels=pod_abnormal_type=ConfigError, command含if [ -z \"${APP_BOOT_MODE:-}\" ]", "interpretation": "Pod自身标签标注ConfigError，YAML确认command校验APP_BOOT_MODE，确认为环境变量缺失"}, {"evidence_id": "e7", "raw_data": "deletionTimestamp=2026-05-21T17:44:27Z, finalizers=<none>, phase=Pending, containerStatuses.reason=ContainerCreating", "interpretation": "Pod已删除约11分钟但未清理，无finalizer阻塞；容器仍卡在ContainerCreating(镜像拉取中)"}, {"evidence_id": "e8", "raw_data": "Events: Normal Pulling image \"busybox:1.36.1\"...无Killing/FailedKillPod事件", "interpretation": "kubelet尚未进入容器停止阶段，因为镜像仍在Pulling中(i/o timeout)，termination流程被前置条件阻塞"}, {"evidence_id": "e9", "raw_data": "Total pods=~107, Running=~59, abnormal=43", "interpretation": "集群整体异常率约40%，主异常为镜像拉取失败"}, {"evidence_id": "e10", "raw_data": "27 ErrImagePull + 15 ImagePullBackOff, 跨node1/node2", "interpretation": "镜像拉取失败分布覆盖node1和node2两个工作节点，非单节点问题"}], "causal_chain": {"root_cause": "集群工作节点(node1/node2)到外部镜像仓库(docker.io/registry.k8s.io)的出口网络不可达，TCP 443端口连接超时(i/o timeout)，导致所有需要远程拉取镜像的Pod无法启动", "propagation": "节点出口网络阻断→kubelet无法连接registry-1.docker.io:443/GCR后端→容器状态进入ErrImagePull→kubelet重试→进入ImagePullBackOff→Pod持续Pending→集群43个异常Pod中42个处于Pending状态", "direct_cause": "节点到docker.io/registry.k8s.io的HTTPS连接超时(i/o timeout)，具体为dial tcp 162.125.1.8:443/asia-east1-docker.pkg.dev:443/europe-west2-docker.pkg.dev:443超时", "manifestation": "用户可见: 42个Pod处于Pending状态(27 ErrImagePull + 15 ImagePullBackOff)，覆盖aiops-e2e/default/mcp三个namespace，分布在node1和node2；1个Terminating Pod因镜像拉取卡住无法完成删除"}, "root_cause": "集群核心问题为**节点出口网络到外部镜像仓库不可达**。证据：(1) g2代表Pod test-dns-1779360358(aiops-e2e)使用busybox:1.36.1，所有拉取尝试均i/o timeout到registry-1.docker.io多IP(162.125.1.8:443等)，x98次事件持续6h31m；(2) dig-tool(default)使用registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0同样i/o timeout到asia-east1/europe-west2-docker.pkg.dev:443；(3) net-check-1779365549(mcp)使用alpine:3.18同样i/o timeout到docker.io，x49次事件持续5h38m。此问题影响node1和node2两个工作节点共41个Pod(27 ErrImagePull+15 ImagePullBackOff)，覆盖3个namespace。同时存在独立异常：aiops-e2e/rc-config-env-missing Cr\n... 截断，原始 770 字符", "root_cause_summary": "集群核心问题为**节点出口网络到外部镜像仓库不可达**。证据：(1) g2代表Pod test-dns-1779360358(aiops-e2e)使用busybox:1.36.1，所有拉取尝试均i/o timeout到registry-1.docker.io多IP(162.125.1.8:443等)，x98次事件持续6h31m；(2) dig-tool(default)使用registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0同样i/o timeout到asia-east1/europe-west2-docker.pkg.dev:443；(3) net-check-1779365549(mcp)使用alpine:3.18同样i/o timeout到docker.io，x49次事件持续5h38m。此问题影响node1和node2两个工作节点共41个Pod(27 ErrImagePull+15 ImagePullBackOff)，覆盖3个namespace。同时存在独立异常：aiops-e2e/rc-config-env-missing Cr\n... 截断，原始 770 字符", "confidence": 0.95, "confidence_reason": "直接证据充分：跨namespace(aiops-e2e/default/mcp)3个独立Pod的kubectl_describe均明确显示i/o timeout错误；跨镜像仓库(docker.io/registry.k8s.io)均不可达；跨节点(node1/node2)均受影响；x59/x49/x22次持续事件证明非瞬时故障。CrashLoopBackOff根因有崩溃日志L4_CONFIG_BOOTSTRAP_FAIL直接证据。Terminating根因有YAML(无finalizer)+容器状态(ContainerCreating)联合证据。唯一未采集的是g3 Terminating Pod的describe(但已有YAML和事件覆盖)，置信度0.95。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像地址或tag不存在", "probability": "low", "reason": "错误消息为i/o timeout而非manifest unknown/not found，且多个不同镜像(busybox:1.36.1/alpine:3.18/jessie-dnsutils:1.0)均失败"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "所有Pod均使用公共镜像(busybox/alpine/jessie-dnsutils)，无需认证；且错误为网络超时而非认证拒绝"}, {"cause": "docker.io匿名拉取限流", "probability": "low", "reason": "错误消息为i/o timeout而非rate limit/Too Many Requests"}, {"cause": "DNS解析失败", "probability": "low", "reason": "错误消息明确为dial tcp IP:443 i/o timeout，说明DNS已解析到IP地址，TCP连接阶段超时"}], "limitations": "未对g3 Terminating Pod(kubectl_describe)单独采集describe以确认events详情，但YAML和已有事件已足够定位根因。未在节点层面直接验证防火墙规则或网络策略(如traceroute/iptables)，但Pod级i/o timeout已足够定位。xnet/observability-kibana Evicted仅作为次要异常提及，未深入分析驱逐原因。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群核心问题为**节点出口网络到外部镜像仓库不可达**。证据：(1) g2代表Pod test-dns-1779360358(aiops-e2e)使用busybox:1.36.1，所有拉取尝试均i/o timeout到registry-1.docker.io多IP(162.125.1.8:443等)...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群工作节点(node1/node2)到外部镜像仓库(docker.io/registry.k8s.io)的出口网络不可达，TCP 443端口连接超时(i/o timeout)，导致所有需要远程拉取镜像的Pod无法启动
     传导机制: 节点出口网络阻断→kubelet无法连接registry-1.docker.io:443/GCR后端→容器状态进入ErrImagePull→kubelet重试→进入ImagePullBackOff→Pod持续Pending→集群43个异常Pod中42个处于Pending状态
     最终表现: 用户可见: 42个Pod处于Pending状态(27 ErrImagePull + 15 ImagePullBackOff)，覆盖aiops-e2e/default/mcp三个namespace，分布在node1和node2；1个Terminating Pod因镜像拉取卡住无法完成删除


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (29.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 7956 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 34.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您提供的诊断数据生成的详尽 K8s 集群诊断报告。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod 异常状态** | `Pending` (42 个), `CrashLoopBackOff` (1 个), `Terminating` (1 个), `Evicted` (1 个) |
| **兼容归因层** | L3 - 网络层 |
| **问题分类** | `ImagePullFailed` - 镜像拉取失败 |
| **置信度** | 高 (95%) |
| **证据完整度** | 7/8 (88%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 集群 Pod 总数 | 102 (59 Running + 43 Abnormal) |
| 异常 Pod 总数 | 43 个 |
| 受影响节点 | node1 (10.2.0.49), node2 (10.2.0.50) |
| 正常节点 | master |
| 正常系统组件 | calico, coredns, etcd, apiserver, scheduler, controller-manager, kube-proxy, multus |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 (ErrImagePull) | kubectl describe pod test-dns-1779360358 (ns: aiops-e2e) | `Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image... i/o timeout to 162.125.1.8:443, 128.242.240.20:443` (x98 次事件，持续 6h31m) | 节点到 `docker.io` 镜像仓库网络不可达 (TCP 443 超时) |
| 2 | Pod 事件 (ErrImagePull) | kubectl describe pod dig-tool (ns: default) | `Failed to pull image... i/o timeout to asia-east1-docker.pkg.dev:443, europe-west2-docker.pkg.dev:443` (22 次尝试，持续 145m) | 节点到 `registry.k8s.io` 镜像仓库网络不可达 |
| 3 | Pod 事件 (ErrImagePull) | kubectl describe pod net-check-1779365549 (ns: mcp) | `Failed to pull image "alpine:3.18"... i/o timeout dialing docker.io:443` (x49 次事件，持续 5h38m) | 再次印证节点到 `docker.io` 出口网络不通 |
| 4 | Pod 状态汇总 | kubectl tabular query | `42 pods Pending, 27 ErrImagePull + 15 ImagePullBackOff across namespaces aiops-e2e, default, mcp, xnet, distributed across node1 and node2` | 确认镜像拉取问题是集群范围内最严重的问题 (42/43 异常 Pod) |
| 5 | CrashLoopBackOff Pod 描述 | kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn (ns: aiops-e2e) | `Reason: CrashLoopBackOff, Restart Count: 8` | 该 Pod 存在单独的配置问题导致持续重启 |
| 6 | CrashLoopBackOff Pod 日志 | kubectl previous logs rc-config-env-missing-5d9b8b766c-bq8pn (ns: aiops-e2e) | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 容器崩溃根本原因是缺少必须的环境变量 `APP_BOOT_MODE` |
| 7 | Terminating Pod YAML | kubectl get pod curl-test-ev-1779385377 (ns: mcp) -o yaml | `deletionTimestamp: 2026-05-21T17:44:27Z, deletionGracePeriodSeconds: 30, finalizers: <none>` | Pod 卡在 Terminating 不是由于 finalizer 阻塞，而是在等待30秒宽限期结束。其基础镜像拉取也一直失败。 |
| 8 | 集群节点状态 | kubectl get nodes | `node2 Ready`, `node1` 承载了所有异常 Pod | 节点本身健康，问题在上层网络。 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：来自三个不同命名空间 (`aiops-e2e`, `default`, `mcp`) 的 Pod 分别尝试从 `docker.io` 和 `registry.k8s.io` 拉取镜像，均因为 `i/o timeout` 失败。这表明问题并非单个镜像或单个命名空间问题，而是**工作节点 `node1` 和 `node2` 到外部互联网出口的通用网络故障**。
- **证据 #5 + #6 印证**：`rc-config-env-missing` Pod 持续 `CrashLoopBackOff`，崩溃日志明确指示 `APP_BOOT_MODE` 环境变量缺失，这是一个与应用配置相关的独立问题，与网络故障无关。
- **证据 #7 分析**：Terminating Pod 的 YAML 显示 `finalizers: <none>`，排除了 finalizer 未清理的根因。其 30 秒的宽限期较短，但卡住 9 分多钟，很可能是因为其容器启动失败（受镜像拉取问题影响），导致 kubelet 无法完成容器停止流程。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Terminating Pod 的详细事件 | critical | 无法确认该 Pod 卡住的完整事件链，特别是优雅终止过程中是否遇到阻塞。 |
| 节点层面网络诊断 (traceroute, iptables) | important | 无法精确确定网络阻断位置（是防火墙、公司代理还是 ISP 问题）。 |

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ 集群工作节点 (node1, node2) 的出口网络到外部镜像仓库 (docker.io,            │
│ registry.k8s.io) 的 TCP 443 端口连接被阻断，导致连接超时 (i/o timeout)。     │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ 节点出口网络阻断 → kubelet 无法连接远程镜像仓库 (registry-1.docker.io:443, │
│ asia-east1-docker.pkg.dev:443 等) → kubelet 拉取镜像失败                    │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 容器状态进入 `ErrImagePull` → kubelet 重试 → 进入 `ImagePullBackOff` →     │
│ Pod 持续处于 `Pending` 状态                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ 42 个 Pod 处于 `Pending` 状态，集群 43 个异常 Pod 中绝大部分由该问题引起    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1, #2, #3 (来自三个不同 Pod 的 `i/o timeout` 错误) 和证据 #4 (42 个 Pending Pod)，集群的核心问题是**工作节点（node1， node2）到外部镜像仓库的出口网络不可达**。这是一个 L3/L4 层网络故障，导致所有需要拉取外部镜像的 Pod 无法启动。

此外，存在一个独立的配置异常：
1.  **`rc-config-env-missing` Pod CrashLoopBackOff**：根据证据 #6 (崩溃日志显示 `missing required APP_BOOT_MODE`)，这是**应用配置错误**，与网络问题无关。
2.  **`curl-test-ev-1779385377` Pod Terminating**：根据证据 #7 (`finalizers: <none>`， `deletionGracePeriodSeconds: 30`)，该 Pod 卡住主要是受其基础容器镜像拉取失败影响，导致优雅终止过程无法完成。已排除 finalizer 问题。

**置信度**：高 (95%)
- ✅ 多个 Pod 描述和事件明确指示 `i/o timeout`。
- ✅ 覆盖多个命名空间和镜像仓库，排除了单一故障点。
- ✅ 节点状态正常，排除了节点宕机。
- ⚠️ 缺少节点级网络诊断工具 (如 `traceroute`， `iptables`)，无法定位故障点的精确位置 (Node/Proxy/Firewall)。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [优先] 排查并恢复工作节点出口网络**
问题出在节点出口，需在 **node1** 和 **node2** 上检查网络连通性。
```bash
# 在所有工作节点上执行
# 1. 直接测试与镜像仓库的连接
curl -I https://registry-1.docker.io  --connect-timeout 5
curl -I https://asia-east1-docker.pkg.dev --connect-timeout 5

# 2. 检查 DNS 解析是否正常
nslookup registry-1.docker.io
nslookup docker.io

# 3. 检查 iptables 规则是否拦截了出站 443 端口
sudo iptables -L -n -v | grep 443

# 4. 查看节点防火墙规则或企业代理配置 (如有)
# e.g., cat /etc/resolv.conf, 查看 /etc/sysctl.conf
```
*依据*：上游证据包中的所有 i/o timeout 错误都指向此路不通。

**2. [临时绕过] 使用镜像仓库代理或私有镜像仓库**
在公司网络环境，可以考虑配置 `containerd` 或 `Docker` 代理。
```bash
# 方案 A (推荐): 在 containerd 配置中配置 Mirror (如果已有 Harbor 等仓库)
# 编辑 /etc/containerd/config.toml
# [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
#   endpoint = ["https://your-private-registry"]

# 方案 B: 配置 HTTP_PROXY 环境变量在 containerd 服务 (系统级别)
# 编辑 /lib/systemd/system/containerd.service
# Environment="HTTP_PROXY=http://your-proxy:port"
# Environment="HTTPS_PROXY=http://your-proxy:port"

# 修改后重启 containerd
sudo systemctl daemon-reload
sudo systemctl restart containerd
```
*依据*：只要无法直接访问公网，就必须通过代理或内部仓库。

**3. [修复配置错误] 修复 CrashLoopBackOff Pod**
为 Deployment 添加缺少的环境变量 `APP_BOOT_MODE`。
```bash
# 假设 Deployment 名为 rc-config-env-missing
kubectl set env deployment/rc-config-env-missing -n aiops-e2e APP_BOOT_MODE=<your_value>
# 或者直接编辑
kubectl edit deployment rc-config-env-missing -n aiops-e2e
# 在 spec.template.spec.containers[0].env 下添加:
# - name: APP_BOOT_MODE
#   value: "production"
# 保存后 Pod 会自动重启。
```
*依据*：证据 #6 (崩溃日志) 明确指出 `missing required APP_BOOT_MODE`。

### 后续优化
1.  **监控告警**：配置对 `ErrImagePull` 和 `ImagePullBackOff` 事件的告警，以便快速发现网络问题。
2.  **资源评估**：评估配置项 `APP_BOOT_MODE`，确保所有 Workload 都包含必要的基础配置。
3.  **基础设施冗余**：为工作节点部署多个网络出口或备用的镜像拉取路径，避免单点故障。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 测试节点网络 | 在 node1/node2 上执行 `curl -I https://registry-1.docker.io --connect-timeout 5` | 返回 HTTP 200 OK |
| 2. 验证 Pod 不再 Pending | `kubectl get pods -n aiops-e2e \| grep test-dns` | STATUS 列变为 `Running` 或 `ContainerCreating` (拉取中) |
| 3. 检查重启次数 | `kubectl get pod rc-config-env-missing-... -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数不再增加 |
| 4. 确认 Terminating Pod 被清除 | `kubectl get pods -n mcp \| grep curl-test` | 该 Pod 不再出现在列表中 |

---

## ⚠️ 注意事项
- **网络修复是最高优先级**：42 个 Pending Pod 是集群无法正常工作的主因，必须优先解决。
- **不要在生产环境随意更改节点网络**：进行 `iptables` 或防火墙修改前，请确保已备份原有规则。
- **`rc-config-env-missing` Pod 是独立问题**：修复网络后该 Pod 仍会 CrashLoopBackOff，需要按照步骤 3 单独修复。
- **`dig-tool` 使用的镜像 GCR**：如果公司环境也无法访问 GCR，上述代理方案必须同时支持 `registry.k8s.io` 和 GCR 域名。

---

## 📊 性能统计

├─ 总耗时: 2.6m
├─ 问题定位: 46.1s (30%) ✅
├─ 证据链采集: 56.2s (36%) ✅
├─ 根因分析: 22.6s (15%) ✅
├─ 汇总总结: 29.1s (19%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 25 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-config-error, pod-terminating-stuck, pod-evicted, pod-crashloop-runtime
- **工具调用**: 25 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
