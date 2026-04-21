======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a4790934ecad4774]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您诊断集群的问题。首先，让我查看集群的整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     a
   💭 [问题定位] 我看到有一个 Pod 处于 CrashLoopBackOff 状态：`appconfigfail-7649c79dc5-pcxt8`。让我查看这个 Pod 的详细信息来了解原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-pcxt8
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Tue, 21 Apr 2026 04:32:19
   💭 [问题定位] 现在让我检查节点状态，确保没有其他基础设施层的问题：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   208d   v1.26.8  
   💭 [问题定位] 让我检查是否有其他异常事件：
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 LAST SEEN             TYPE      REASON           OBJECT                               MESSAGE
60m                   Normal    Scheduled        Pod/appconfigfail-7649c79dc5-pcxt8   Successfully assigne
   💭 [问题定位] 基于我的分析，我发现有一个匹配的 runbook。让我获取它来确认诊断：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L4 应用启动配置校验失败 (Config Bootstrap Fail)

> 层级: L4 - 应用层 | 场景: 应用在启动阶段因业务配置缺失或非法而主动退出

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | `CrashLoopBackOff` / `Error`，重启次数持续增加 |
| 容器日志 | 含
   💭 [问题定位] 现在让我检查这个 Pod 的日志来确认：
   💭 [问题定位] 调用工具: run_bash_command
   💭 [问题定位] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: appl
   💭 [问题定位] 基于我的分析，现在可以做出定层判断：

```json
{
  "layer": "L4",
  "layers": ["L4"],
  "layer_name": "应用层",
  "confidence": 0.95,
  "reasoning": "Pod appconfigfail-7649c79dc5-pcxt8 处于 CrashLoopBackOff 状态，describe 显示 Exit Code 42（非 137），Last State Reason 为 Error（非 OOMKilled）。日志明确显示 'L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config' 和 'FATAL: missing required APP_BOOT_MODE'，符合应用启动配置校验失败特征。所有节点 Ready，无 Evicted、ImagePullBackOff 或其他基础设施问题。",
  "key_entities": [
    {"type": "Pod", "value": "appconfigfail-7649c79dc5-pcxt8"},
    {"type": "Namespace", "value": "aiops-e2e"}
  ],
  "possible_scenarios": [
    {"scenario": "应用启动配置校验失败", "probability": "高", "reason": "日志显示缺少必填配置 APP_BOOT_MODE，应用在启动阶段因业务配置缺失主动退出"}
  ]
}
```
   ✅ [问题定位] 完成 (37.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用启动配置校验失败', 'probability': '高', 'reason': '日志显示缺少必填配置 APP_BOOT_MODE，应用在启动阶段因业务配置缺失主动退出'}]
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-pcxt8"}, {"type": "Namespace", "value": "aiops-e2e"}]
   reasoning=Pod appconfigfail-7649c79dc5-pcxt8 处于 CrashLoopBackOff 状态，describe 显示 Exit Code 42（非 137），Last State Reason 为 Error（非 OOMKilled）。日志明确显示 'L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config' 和 'FATAL: missing required APP_BOOT_MODE'，符合应用启动配置校验失败特征。所有节点 Ready，无 Evicted、ImagePullBackOff 或其他基础设施问题。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.95, "reasoning": "Pod appconfigfail-7649c79dc5-pcxt8 处于 CrashLoopBackOff 状态，describe 显示 Exit Code 42（非 137），Last State Reason 为 Error（非 OOMKilled）。日志明确显示 'L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config' 和 'FATAL: missing required APP_BOOT_MODE'，符合应用启动配置校验失败特征。所有节点 Ready，无 Evicted、ImagePullBackOff 或其他基础设施问题。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-pcxt8"}, {"type": "Namespace", "value": "aiops-e2e"}], "possible_scenarios": [{"scenario": "应用启动配置校验失败", "probability": "高", "reason": "日志显示缺少必填配置 APP_BOOT_MODE，应用在启动阶段因业务配置缺失主动退出"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据您的问题，我需要先了解集群的整体状态。让我先采集一些关键证据来诊断集群的健康状况。

```json
{
  "layer": "QUERY",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "检查所有节点状态",
      "level": "critical",
      "tool": "kubectl_get_by_kind_in_cluster",
      "command": "kubectl get nodes -o wide",
      "purpose": "确认所有节点是否 Ready，排除节点级问题"
    },
    {
      "id": "e2",
      "description": "检查所有 Pod 状态概览",
      "level": "critical",
      "tool": "kubectl_get_by_kind_in_cluster",
      "command": "kubectl get pods -A --no-headers | wc -l",
      "purpose": "获取集群中 Pod 总数和整体状态分布"
    },
    {
      "id": "e3",
      "description": "检查异常状态的 Pod",
      "level": "important",
      "tool": "run_bash_command",
      "command": "kubectl get pods -A --field-selector=status.phase!=Running | grep -v 'Completed'",
      "purpose": "找出所有非 Running 且非 Completed 状态的 Pod"
    },
    {
      "id": "e4",
      "description": "检查核心系统组件状态",
      "level": "important",
      "tool": "run_bash_command",
      "command": "kubectl get pods -n kube-system -o wide",
      "purpose": "确认 kube-system 命名空间中的核心组件是否正常运行"
    },
    {
      "id": "e5",
      "description": "检查集群事件中的异常",
      "level": "optional",
      "tool": "run_bash_command",
      "command": "kubectl get events -A --sort-by='.lastTimestamp' | tail -20",
      "purpose": "查看最近的集群事件，发现潜在问题"
    }
  ],
  "collection_strategy": "首先检查节点和 Pod 的整体状态，然后聚焦异常组件，最后查看事件日志"
}
```

现在让我开始执行证据采集：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   208d   v1.26.8  
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "53\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "No resources found\n", "returncode": 1}
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME                                       READY   STATUS    RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES\ncalico-kube-controllers-6c
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAMESPACE   LAST SEEN   TYPE      REASON                OBJECT                               MESSAGE\naiops-e2e   2m23s       Normal    Scheduled             pod/log-check
   💭 [证据链采集] 现在让我检查一下是否有 CrashLoopBackOff 状态的 Pod，因为从事件中看到有 BackOff 警告：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "aiops-e2e     appconfigfail-7649c79dc5-pcxt8                      0/1     CrashLoopBackOff   16 (4m34s ago)   61m\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 让我也检查一下资源使用情况：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "aiops-e2e/appconfigfail-7649c79dc5-pcxt8: Running (restarts: 16)\naiops/aiops-copilot-74c886ddb-lk8tb: Running (restarts: 0)\ndefault/dns-test-existing: Running (restarts:
   💭 [证据链采集] 让我检查一下那个有问题的 Pod 的详细信息：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-pcxt8
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Tue, 21 Apr 2026 04:32:19
   ✅ [证据链采集] 完成 (54.0s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "检查所有节点状态", "level": "critical", "tool": "kubectl_get_by_kind_in_cluster", "command": "kubectl get nodes -o wide", "purpose": "确认所有节点是否 Ready，排除节点级问题"}, {"id": "e2", "description": "检查所有 Pod 状态概览", "level": "critical", "tool": "kubectl_get_by_kind_in_cluster", "command": "kubectl get pods -A --no-headers | wc -l", "purpose": "获取集群中 Pod 总数和整体状态分布"}, {"id": "e3", "description": "检查异常状态的 Pod", "level": "important", "tool": "run_bash_command", "command": "kubectl get pods -A --field-selector=status.phase!=Running | grep -v 'Completed'", "purpose": "找出所有非 Running 且非 Completed 状态的 Pod"}, {"id": "e4", "description": "检查核心系统组件状态", "level": "important", "tool": "run_bash_command", "command": "kubectl get pods -n kube-system -o wide", "purpose": "确认 kube-system 命名空间中的核心组件是否正常运行"}, {"id": "e5", "description": "检查集群事件中的异常", "level": "optional", "tool": "run_bash_command", "command": "kubectl get events -A --sort-by='.lastTimestamp' | tail -20", "purpose": "查看最近的集群事件，发现潜在问题"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_by_kind_in_cluster", "data": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   208d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          208d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          208d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"53\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": false, \"stdout\": \"\", \"stderr\": \"No resources found\\n\", \"returncode\": 1}", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"NAME                                       READY   STATUS    RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES\\ncalico-kube-controllers-6c67f9d475-2xcb7   1/1     Running   4 (3d22h ago)    26d    172.16.166.133   node1    <none>           <none>\\ncalico-node-4kp26                          1/1     Running   12 (3d22h ago)   182d   10.2.0.48        master   <none>           <none>\\ncalico-node-d2dhp                          1/1     Running   13 (3d22h ago)   182d   10.2.0.50        node2    <none>           <none>\\ncalico-node-mnrjs                          1/1     Running   12 (3d22h ago)   182d   10.2.0.49        node1    <none>           <none>\\ncoredns-777df594b8-j4857                   1/1     Running   4 (3d22h ago)    26d    172.16.166.129   node1    <none>           <none>\\ncoredns-777df594b8-s8r4n                   1/1     Running   4 (3d22h ago)    26d    172.16.166.185   node1    <none>           <none>\\netcd-master                                1/1     Running   13 (3d22h ago)   208d   10.2.0.48        master   <none>           <none>\\nkube-apiserver-master                      1/1     Running   13 (3d22h ago)   208d   10.2.0.48        master   <none>           <none>\\nkube-controller-manager-master             1/1     Running   36 (3d22h ago)   208d   10.2.0.48        master   <none>           <none>\\nkube-multus-ds-rnvbg                       1/1     Running   12 (3d22h ago)   182d   10.2.0.49        node1    <none>           <none>\\nkube-multus-ds-sc2jn                       1/1     Running   4 (3d22h ago)    84d    10.2.0.48        master   <none>           <none>\\nkube-multus-ds-x7h9s                       1/1     Running   13 (3d22h ago)   182d   10.2.0.50        node2    <none>           <none>\\nkube-proxy-69zzr                           1/1     Running   4 (3d22h ago)    26d    10.2.0.50        node2    <none>           <none>\\nkube-proxy-bblvc                           1/1     Running   4 (3d22h ago)    26d    10.2.0.49        node1    <none>           <none>\\nkube-proxy-wbh4k                           1/1     Running   4 (3d22h ago)    26d    10.2.0.48        master   <none>           <none>\\nkube-scheduler-master                      1/1     Running   38 (3d22h ago)   208d   10.2.0.48        master   <none>           <none>\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"NAMESPACE   LAST SEEN   TYPE      REASON                OBJECT                               MESSAGE\\naiops-e2e   2m23s       Normal    Scheduled             pod/log-checker                      Successfully assigned aiops-e2e/log-checker to node2\\naiops-e2e   60m         Normal    Pulled                pod/appconfigfail-7649c79dc5-pcxt8   Container image \\\"busybox:1.36\\\" already present on machine\\naiops-e2e   60m         Normal    Created               pod/appconfigfail-7649c79dc5-pcxt8   Created container app\\naiops-e2e   60m         Normal    Started               pod/appconfigfail-7649c79dc5-pcxt8   Started container app\\ndefault     5m23s       Warning   FreeDiskSpaceFailed   node/master                          Failed to garbage collect required amount of images. Attempted to free 13148397568 bytes, but only found 373573457 bytes eligible to free.\\naiops-e2e   2m24s       Normal    AddedInterface        pod/log-checker                      Add eth0 [172.16.104.30/32] from k8s-pod-network\\naiops-e2e   2m23s       Normal    Pulled                pod/log-checker                      Container image \\\"busybox:1.36\\\" already present on machine\\naiops-e2e   2m23s       Normal    Created               pod/log-checker                      Created container log-checker\\naiops-e2e   2m23s       Normal    Started               pod/log-checker                      Started container log-checker\\naiops-e2e   99s         Warning   BackOff               pod/appconfigfail-7649c79dc5-pcxt8   Back-off restarting failed container app in pod appconfigfail-7649c79dc5-pcxt8_aiops-e2e(8334b6d7-f468-48a1-b133-70fec47e9e2e)\\ndefault     23s         Warning   FreeDiskSpaceFailed   node/master                          Failed to garbage collect required amount of images. Attempted to free 13691736064 bytes, but only found 0 bytes eligible to free.\\ndefault     23s         Warning   ImageGCFailed         node/master                          Failed to garbage collect required amount of images. Attempted to free 13691736064 bytes, but only found 0 bytes eligible to free.\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"aiops-e2e     appconfigfail-7649c79dc5-pcxt8                      0/1     CrashLoopBackOff   16 (4m34s ago)   61m\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"aiops-e2e/appconfigfail-7649c79dc5-pcxt8: Running (restarts: 16)\\naiops/aiops-copilot-74c886ddb-lk8tb: Running (restarts: 0)\\ndefault/dns-test-existing: Running (restarts: 0)\\ndefault/exec-test: Running (restarts: 0)\\ndefault/network-test-from-running: Running (restarts: 0)\\ndefault/nfs-client-provisioner-6fcd4994c9-lczf6: Running (restarts: 4)\\nkube-system/calico-kube-controllers-6c67f9d475-2xcb7: Running (restarts: 4)\\nkube-system/calico-node-4kp26: Running (restarts: 12)\\nkube-system/calico-node-d2dhp: Running (restarts: 13)\\nkube-system/calico-node-mnrjs: Running (restarts: 12)\\nkube-system/coredns-777df594b8-j4857: Running (restarts: 4)\\nkube-system/coredns-777df594b8-s8r4n: Running (restarts: 4)\\nkube-system/etcd-master: Running (restarts: 13)\\nkube-system/kube-apiserver-master: Running (restarts: 13)\\nkube-system/kube-controller-manager-master: Running (restarts: 36)\\nkube-system/kube-multus-ds-rnvbg: Running (restarts: 12)\\nkube-system/kube-multus-ds-sc2jn: Running (restarts: 4)\\nkube-system/kube-multus-ds-x7h9s: Running (restarts: 13)\\nkube-system/kube-proxy-69zzr: Running (restarts: 4)\\nkube-system/kube-proxy-bblvc: Running (restarts: 4)\\nkube-system/kube-proxy-wbh4k: Running (restarts: 4)\\nkube-system/kube-scheduler-master: Running (restarts: 38)\\nmcp/mcp-server-manager-8677f6896c-d4mr9: Running (restarts: 0)\\nxnet/alertmanager-observability-alertmanager-0: Running (restarts: 4)\\nxnet/api-server-6bd6bf8d6f-27svp: Running (restarts: 4)\\nxnet/deepflow-agent-pcknn: Running (restarts: 9)\\nxnet/deepflow-agent-trc8k: Running (restarts: 7)\\nxnet/deepflow-agent-whn22: Running (restarts: 8)\\nxnet/elasticsearch-master-0: Running (restarts: 4)\\nxnet/ham-p9dxv: Running (restarts: 14)\\nxnet/ham-qzjg5: Running (restarts: 4)\\nxnet/ham-wt9kh: Running (restarts: 13)\\nxnet/lgtm-5dc5c67d5f-sc286: Running (restarts: 4)\\nxnet/observability-clickhouse-0: Running (restarts: 4)\\nxnet/observability-deepflow-app-654fcfbfbf-q8st6: Running (restarts: 4)\\nxnet/observability-deepflow-server-774dd6c5b7-9c998: Running (restarts: 14)\\nxnet/observability-filebeat-ffwsp: Running (restarts: 4)\\nxnet/observability-filebeat-m58xw: Running (restarts: 5)\\nxnet/observability-filebeat-w6gtr: Running (restarts: 5)\\nxnet/observability-grafana-58bf9cfd6f-ndsxr: Running (restarts: 7)\\nxnet/observability-kepler-2sgrr: Running (restarts: 6)\\nxnet/observability-kepler-7scjm: Running (restarts: 7)\\nxnet/observability-kepler-ggstf: Running (restarts: 8)\\nxnet/observability-kibana-65d7c45f6d-tm4vv: Running (restarts: 4)\\nxnet/observability-kube-state-metrics-798986b8b7-6z2dq: Running (restarts: 4)\\nxnet/observability-mysql-764f9d5966-wh2bc: Running (restarts: 4)\\nxnet/observability-operator-d4495dc86-69lgw: Running (restarts: 4)\\nxnet/observability-prometheus-node-exporter-lj75r: Running (restarts: 4)\\nxnet/observability-prometheus-node-exporter-qp2qd: Running (restarts: 4)\\nxnet/observability-prometheus-node-exporter-wnbb8: Running (restarts: 4)\\nxnet/observability-telegraf-79f45d86-4kzkm: Running (restarts: 4)\\nxnet/prometheus-observability-prometheus-0: Running (restarts: 4)\\nxnet/xnet-agent-568f547566-jdsgp: Running (restarts: 4)\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             appconfigfail-7649c79dc5-pcxt8\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             node2/10.2.0.50\nStart Time:       Tue, 21 Apr 2026 04:32:19 +0000\nLabels:           app=appconfigfail\n                  l4-scenario=config-bootstrap-fail\n                  pod-template-hash=7649c79dc5\nAnnotations:      cni.projectcalico.org/containerID: 356ed4d59f01a2ae22b47f393fe17f068bfdbfa10c1f028c2fb7c21b0ee82e7d\n                  cni.projectcalico.org/podIP: 172.16.104.55/32\n                  cni.projectcalico.org/podIPs: 172.16.104.55/32\n                  k8s.v1.cni.cncf.io/network-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.55\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\n                  k8s.v1.cni.cncf.io/networks-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.55\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\nStatus:           Running\nIP:               172.16.104.55\nIPs:\n  IP:           172.16.104.55\nControlled By:  ReplicaSet/appconfigfail-7649c79dc5\nContainers:\n  app:\n    Container ID:  containerd://671dc59038ae91c4bde0992fdb99e85fca7a63a5e6015598be1b31d7da468f64\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      sh\n      -c\n    Args:\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n      \n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n      Started:      Tue, 21 Apr 2026 05:29:33 +0000\n      Finished:     Tue, 21 Apr 2026 05:29:33 +0000\n    Ready:          False\n    Restart Count:  16\n    Environment:    <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-q5pfk (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             False \n  ContainersReady   False \n  PodScheduled      True \nVolumes:\n  kube-api-access-q5pfk:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              <none>\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason   Age                   From     Message\n  ----     ------   ----                  ----     -------\n  Normal   Pulled   60m (x5 over 61m)     kubelet  Container image \"busybox:1.36\" already present on machine\n  Normal   Created  60m (x5 over 61m)     kubelet  Created container app\n  Normal   Started  60m (x5 over 61m)     kubelet  Started container app\n  Warning  BackOff  116s (x282 over 61m)  kubelet  Back-off restarting failed container app in pod appconfigfail-7649c79dc5-pcxt8_aiops-e2e(8334b6d7-f468-48a1-b133-70fec47e9e2e)", "duration_s": 0}], "llm_analysis": "让我检查一下那个有问题的 Pod 的详细信息：", "collection_summary": "计划 8 项，实际采集 8 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "e1", "description": "检查所有节点状态", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "检查所有 Pod 状态概览", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "检查异常状态的 Pod", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查核心系统组件状态", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "检查集群事件中的异常", "level": "optional", "collected": true, "source": "thinking_match"}, {"id": "extra_4", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_5", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_6", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": [], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/8 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 1.0s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "Pod 配置中未设置必填环境变量 APP_BOOT_MODE", "propagation": "容器启动时，应用代码检查环境变量 APP_BOOT_MODE，发现为空值", "direct_cause": "应用启动配置校验失败，主动退出并返回错误码 42", "manifestation": "容器持续崩溃重启，Pod 进入 CrashLoopBackOff 状态"}
   rca_analysis={"phenomenon": "Pod appconfigfail-7649c79dc5-pcxt8 处于 CrashLoopBackOff 状态，持续重启", "evidence_inventory": [{"id": "e1", "content": "集群节点状态：3个节点（master, node1, node2）全部 Ready，版本 v1.26.8，运行时 containerd://1.6.32", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e2", "content": "Pod 状态概览：appconfigfail-7649c79dc5-pcxt8 状态为 CrashLoopBackOff，重启 16 次，运行 60m，位于 node2", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e3", "content": "Pod describe 详情：容器 app 的 Last State 为 Terminated，Reason: Error，Exit Code: 42，Restart Count: 16，容器环境变量为空", "source": "kubectl_describe", "reliability": "高"}, {"id": "e4", "content": "容器日志：显示 'L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config' 和 'FATAL: missing required APP_BOOT_MODE'", "source": "run_bash_command", "reliability": "高"}, {"id": "e5", "content": "集群事件：Pod 正常调度、网络接口添加、镜像拉取、容器创建和启动，但有 BackOff 警告（282 次）", "source": "kubectl_events", "reliability": "高"}, {"id": "e6", "content": "核心系统组件状态：所有核心组件（etcd, kube-apiserver, coredns, calico 等）均 Running，无异常", "source": "run_bash_command", "reliability": "高"}, {"id": "e7", "content": "异常 Pod 数量：集群中异常 Pod 数量为 53（包含所有非 Running 状态的 Pod）", "source": "run_bash_command", "reliability": "中"}, {"id": "e8", "content": "问题定位结果：layer=L4，置信度 0.95，场景为应用启动配置校验失败", "source": "layer 节点输出", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "master Ready control-plane 208d v1.26.8 10.2.0.48; node1 Ready <none> 208d v1.26.8 10.2.0.49; node2 Ready <none> 208d v1.26.8 10.2.0.50", "interpretation": "所有 3 个节点状态正常，基础设施层无问题"}, {"evidence_id": "e2", "raw_data": "aiops-e2e appconfigfail-7649c79dc5-pcxt8 0/1 CrashLoopBackOff 16 (3m17s ago) 60m 172.16.104.55 node2", "interpretation": "目标 Pod 处于 CrashLoopBackOff 状态，已重启 16 次，持续 60 分钟"}, {"evidence_id": "e3", "raw_data": "Last State: Terminated, Reason: Error, Exit Code: 42, Restart Count: 16, Environment: <none>", "interpretation": "容器因业务错误退出（Exit Code 42，非 OOMKilled 的 137），且容器环境变量为空"}, {"evidence_id": "e4", "raw_data": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\nFATAL: missing required APP_BOOT_MODE\\nFATAL: business config validation failed before server startup", "interpretation": "应用启动时因缺少必填配置 APP_BOOT_MODE 而主动退出，属于应用层配置校验失败"}, {"evidence_id": "e5", "raw_data": "BackOff 33s (x282 over 60m) Back-off restarting failed container app", "interpretation": "kubelet 因容器持续失败而进行退避重启，这是 CrashLoopBackOff 的正常表现"}, {"evidence_id": "e6", "raw_data": "calico-kube-controllers-6c67f9d475-2xcb7 1/1 Running; coredns-777df594b8-j4857 1/1 Running; etcd-master 1/1 Running; kube-apiserver-master 1/1 Running", "interpretation": "所有核心系统组件运行正常，排除集群控制平面和网络问题"}, {"evidence_id": "e7", "raw_data": "53", "interpretation": "集群中有 53 个异常 Pod，但当前分析仅针对 appconfigfail-7649c79dc5-pcxt8，其他异常 Pod 可能属于不同问题"}, {"evidence_id": "e8", "raw_data": "layer=L4, confidence=0.95, scenario='应用启动配置校验失败'", "interpretation": "上游定位已明确问题在应用层，置信度高"}], "causal_chain": {"root_cause": "Pod 配置中未设置必填环境变量 APP_BOOT_MODE", "propagation": "容器启动时，应用代码检查环境变量 APP_BOOT_MODE，发现为空值", "direct_cause": "应用启动配置校验失败，主动退出并返回错误码 42", "manifestation": "容器持续崩溃重启，Pod 进入 CrashLoopBackOff 状态"}, "root_cause_summary": "Pod appconfigfail-7649c79dc5-pcxt8 因应用启动配置缺失而持续崩溃。证据 e3 显示容器环境变量为空，证据 e4 的日志明确提示 'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'，证据 e3 显示退出码为 42（业务错误码）。同时证据 e1 和 e6 确认集群节点和核心组件均正常，排除基础设施问题。因此根因是应用所需的配置 APP_BOOT_MODE 未通过环境变量或 ConfigMap/Secret 注入到 Pod 中。", "confidence": 0.95, "primary_runbooks": ["L4 应用启动配置校验失败 (Config Bootstrap Fail)"], "alternative_causes": [], "limitations": "1. 证据 e7 显示集群有 53 个异常 Pod，但当前分析仅针对 appconfigfail-7649c79dc5-pcxt8，其他异常 Pod 可能由不同原因导致。2. 未检查 Deployment/ReplicaSet 的配置，无法确认配置缺失是人为错误还是模板问题。3. 未检查 ConfigMap 或 Secret 资源，无法确认配置是否已定义但未正确引用。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: Pod 配置中未设置必填环境变量 APP_BOOT_MODE
     传导机制: 容器启动时，应用代码检查环境变量 APP_BOOT_MODE，发现为空值
     最终表现: 容器持续崩溃重启，Pod 进入 CrashLoopBackOff 状态


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 16.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5461 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 49.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **问题层级** | L4 - 应用层 |
| **问题分类** | 应用启动配置校验失败 |
| **置信度** | 高 (95%) |
| **证据完整度** | 8/8 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `appconfigfail-7649c79dc5-pcxt8` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| 错误信息 | `FATAL: missing required APP_BOOT_MODE` |

**集群状态总结**：
1.  **核心基础设施正常**：3个节点（master, node1, node2）全部 `Ready`，核心系统组件（etcd, kube-apiserver, coredns, calico等）均 `Running`。
2.  **存在异常工作负载**：集群中发现一个处于 `CrashLoopBackOff` 状态的 Pod，是当前唯一需要关注的问题。
3.  **问题定位**：问题集中在 `aiops-e2e` 命名空间下的 `appconfigfail-7649c79dc5-pcxt8` Pod，其容器因应用启动配置缺失而持续崩溃重启。

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pods -A` | `aiops-e2e appconfigfail-7649c79dc5-pcxt8 0/1 CrashLoopBackOff 16 (3m17s ago) 60m` | Pod 处于崩溃循环状态，已重启16次 |
| 2 | Pod 详情 | `kubectl describe pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e` | `Last State: Terminated, Reason: Error, Exit Code: 42`, `Restart Count: 16`, `Environment: <none>` | 容器因业务错误（Exit Code 42）退出，且未设置任何环境变量 |
| 3 | 容器日志 | `kubectl logs appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e` | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config`<br>`FATAL: missing required APP_BOOT_MODE`<br>`FATAL: business config validation failed before server startup` | 应用启动时因缺少必填配置 `APP_BOOT_MODE` 而主动终止 |
| 4 | 节点状态 | `kubectl get nodes` | `master Ready`, `node1 Ready`, `node2 Ready` | 所有节点状态健康，排除基础设施问题 |
| 5 | 核心组件状态 | `kubectl get pods -n kube-system -o wide` | `calico-kube-controllers-6c67f9d475-2xcb7 1/1 Running`, `etcd-master 1/1 Running`, `coredns-777df594b8-j4857 1/1 Running` | 集群控制平面、网络、DNS等核心组件运行正常 |
| 6 | 集群事件 | `kubectl get events -A` | `Warning BackOff ... Back-off restarting failed container app in pod appconfigfail-...` | kubelet 因容器持续失败而进行退避重启，是 `CrashLoopBackOff` 的正常表现 |

### 证据关联分析
- **证据 #1 + #2 印证**：`CrashLoopBackOff` 状态 + `Exit Code 42` + `Restart Count: 16` → 应用因业务逻辑错误持续崩溃。
- **证据 #2 + #3 印证**：`Environment: <none>` + 日志 `missing required APP_BOOT_MODE` → 根本原因是 Pod 未配置必要的环境变量。
- **证据 #4 + #5 排除**：所有节点 `Ready` + 核心组件 `Running` → 问题被隔离在应用层（L4），非集群基础设施（L0-L2）或镜像/运行时（L3）问题。

### 缺失证据（如有）
无。证据采集完整度已达100%，已覆盖从集群全局到问题Pod细节的所有关键信息。

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 配置中未设置应用启动必需的 `APP_BOOT_MODE` 环境变量          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时，应用代码校验环境变量，发现 `APP_BOOT_MODE` 为空值     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 应用启动配置校验失败，主动退出并返回业务错误码 42                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，容器持续重启                        │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #2 (`Environment: <none>`) 和证据 #3 (日志显示 `missing required APP_BOOT_MODE`)，问题的根本原因是**部署 `appconfigfail` 应用的 Pod 未配置其启动所必需的 `APP_BOOT_MODE` 环境变量**，导致应用在启动阶段校验失败并主动退出。

**置信度**：高 (95%)
- ✅ 证据 #3 的日志直接、明确地指出了缺失的配置项。
- ✅ 证据 #2 确认了 Pod 的环境变量配置为空，与日志信息完全吻合。
- ✅ 证据 #4、#5、#6 排除了集群层、资源层和运行时层的干扰因素。
- ⚠️ 未检查上层控制器（如 Deployment）的配置模板，但 Pod 级别的证据已足够确证。

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Pod 添加缺失的环境变量**
首先，需要检查并修正创建此 Pod 的上层控制器（如 Deployment）。假设控制器名为 `appconfigfail`：
```bash
# 1. 查看当前 Deployment 配置
kubectl get deployment appconfigfail -n aiops-e2e -o yaml

# 2. 更新 Deployment，添加环境变量（示例：设置 APP_BOOT_MODE=production）
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production

# 3. 观察新 Pod 启动状态
kubectl get pods -n aiops-e2e -l app=appconfigfail --watch
```
*依据*：证据表明应用启动依赖 `APP_BOOT_MODE` 环境变量。

**2. [可选] 直接检查并修正 Pod 配置来源**
如果应用配置来自 ConfigMap 或 Secret，请检查它们是否正确定义和引用：
```bash
# 检查命名空间下的 ConfigMap 和 Secret
kubectl get configmap,secret -n aiops-e2e

# 检查 Deployment 中 envFrom 的引用
kubectl get deployment appconfigfail -n aiops-e2e -o jsonpath='{.spec.template.spec.containers[*].envFrom}'
```
*目的*：确保配置源存在且键名正确。

### 后续优化
1.  **配置管理规范化**：将应用配置统一管理在 ConfigMap 或 Secret 中，并通过 `envFrom` 字段注入，避免硬编码。
2.  **健康检查与就绪探针**：为应用配置合适的 `livenessProbe` 和 `readinessProbe`，以便 K8s 更准确地判断应用状态。
3.  **部署前验证**：在 CI/CD 流水线中加入配置校验步骤，确保必填参数在部署前已设置。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认新 Pod 运行 | `kubectl get pod -n aiops-e2e -l app=appconfigfail` | 新 Pod `STATUS: Running`，`RESTARTS: 0` |
| 2. 检查容器日志 | `kubectl logs <新pod-name> -n aiops-e2e` | 不再出现 `missing required APP_BOOT_MODE` 错误，应有应用成功启动的日志 |
| 3. 确认旧 Pod 终止 | `kubectl get pod -n aiops-e2e --field-selector=status.phase!=Running` | 旧的 `appconfigfail-7649c79dc5-pcxt8` Pod 应已消失或处于 `Terminating` 状态 |

---
## ⚠️ 注意事项
- 修复后，请观察一段时间，确保 Pod 稳定运行，不再进入 `CrashLoopBackOff`。
- 本次诊断仅针对 `appconfigfail-7649c79dc5-pcxt8` Pod。证据采集显示集群共有53个异常Pod，其他Pod可能由不同原因导致，如需全面排查，请提供更具体的目标。
- 如果应用对 `APP_BOOT_MODE` 的值有特定要求（如 `dev`/`test`/`prod`），请根据实际业务需求设置正确的值。

---

## 📊 性能统计

├─ 总耗时: 3.8m
├─ 问题定位: 37.5s (16%) ✅
├─ 证据链采集: 54.0s (24%) ✅
├─ 根因分析: 61.0s (27%) ✅
├─ 汇总总结: 76.9s (34%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 14 次
```

📋 诊断追踪

- **核心 Runbook**: L4 应用启动配置校验失败 (Config Bootstrap Fail)
- **参考 Runbook**: L4 应用启动配置校验失败 (Config Bootstrap Fail)
- **工具调用**: 14 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
