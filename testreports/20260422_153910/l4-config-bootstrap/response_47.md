======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: bd82675cf78842bc]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先做轻量状态确认，快速查看集群的整体健康状况。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 3 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 0 completed, 1 in progress, 2 pending

[ ] [2] 获取通用健康检查runbook作为基线参考
[ ] [3] 分析异常对象并定层
[~] [1] 查看集群整体状态（Nodes、
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 很好！集群整体状态不错：

- **3 个节点全部 Ready**（master、node1、node2）
- **系统组件全部 Running**（etcd、apiserver、controller-manager、scheduler、coredns、calico、kube-proxy 等）
- **发现一个异常 Pod**：`aiops-e2e/appconfigfail-7649c79dc5-q4zjz` 处于 **CrashLoopBackOff** 状态

让我进一步查看这个异常 Pod 的详情。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 3 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 1 completed, 1 in progress, 1 pending

[ ] [3] 分析异常对象并定层
[~] [2] 获取通用健康检查runbook作为基线参考
[✓] [1] 查看集群整体状态（Nodes、
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [问题定位] 情况很清晰了。让我查看这个 Pod 的标签，它有明确指示。现在获取通用健康检查 runbook 作为基线参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 3 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 2 completed, 1 in progress, 0 pending

[~] [3] 分析异常对象并定层
[✓] [1] 查看集群整体状态（Nodes、关键系统Pod）
[✓] [2] 获取通用健康检查runbo
   💭 [问题定位] 现在分析完毕，这个 Pod 的标签 `l4-scenario=config-bootstrap-fail` 和日志信息非常明确，让我也获取对应的 L4 runbook 确认。
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
   💭 [问题定位] 完美，证据已经完全确认。现在我来做最终定层分析。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 3 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 3 completed, 0 in progress, 0 pending

[✓] [1] 查看集群整体状态（Nodes、关键系统Pod）
[✓] [2] 获取通用健康检查runbook作为基线参考
[✓] [3] 分
   💭 [问题定位] ```json
{
  "layer": "L4",
  "layers": ["L4"],
  "layer_name": "应用层",
  "confidence": 0.98,
  "reasoning": "集群3个节点全部Ready，所有系统组件（etcd/apiserver/coredns/calico/kube-proxy等）均正常Running。唯一异常Pod为aiops-e2e命名空间下的appconfigfail-7649c79dc5-q4zjz，处于CrashLoopBackOff状态。Describe显示Exit Code=42，容器日志明确输出'L4_CONFIG_BOOTSTRAP_FAIL'和'FATAL: missing required APP_BOOT_MODE'，Pod标签也标注了l4-scenario=config-bootstrap-fail。无OOMKilled(非L2)、无ImagePullBackOff(非L3)、无Evicted(非L0)，属于应用层配置校验失败导致的主动退出。",
  "key_entities": [
    {"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Node", "value": "node2"}
  ],
  "possible_scenarios": [
    "应用启动配置校验失败（Config Bootstrap Fail）— 容器启动脚本检测到环境变量 APP_BOOT_MODE 缺失，主动退出并返回 Exit Code 42"
  ]
}
```
   ✅ [问题定位] 完成 (29.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=['应用启动配置校验失败（Config Bootstrap Fail）— 容器启动脚本检测到环境变量 APP_BOOT_MODE 缺失，主动退出并返回 Exit Code 42']
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}]
   reasoning=集群3个节点全部Ready，所有系统组件（etcd/apiserver/coredns/calico/kube-proxy等）均正常Running。唯一异常Pod为aiops-e2e命名空间下的appconfigfail-7649c79dc5-q4zjz，处于CrashLoopBackOff状态。Describe显示Exit Code=42，容器日志明确输出'L4_CONFIG_BOOTSTRAP_FAIL'和'FATAL: missing required APP_BOOT_MODE'，Pod标签也标注了l4-scenario=config-bootstrap-fail。无OOMKilled(非L2)、无ImagePullBackOff(非L3)、无Evicted(非L0)，属于应用层配置校验失败导致的主动退出。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.98, "reasoning": "集群3个节点全部Ready，所有系统组件（etcd/apiserver/coredns/calico/kube-proxy等）均正常Running。唯一异常Pod为aiops-e2e命名空间下的appconfigfail-7649c79dc5-q4zjz，处于CrashLoopBackOff状态。Describe显示Exit Code=42，容器日志明确输出'L4_CONFIG_BOOTSTRAP_FAIL'和'FATAL: missing required APP_BOOT_MODE'，Pod标签也标注了l4-scenario=config-bootstrap-fail。无OOMKilled(非L2)、无ImagePullBackOff(非L3)、无Evicted(非L0)，属于应用层配置校验失败导致的主动退出。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Node", "value": "node2"}], "possible_scenarios": ["应用启动配置校验失败（Config Bootstrap Fail）— 容器启动脚本检测到环境变量 APP_BOOT_MODE 缺失，主动退出并返回 Exit Code 42"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，已经明确发现了一个异常 Pod。让我先制定证据采集计划，然后执行工具采集数据。

## 第一步：输出 JSON 证据采集计划

```json
{
  "layer": "L4",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "查看异常 Pod 当前状态和退出历史",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e",
      "purpose": "确认退出码、容器命令、重启次数等关键信息"
    },
    {
      "id": "e2",
      "description": "查看异常 Pod 的容器日志",
      "level": "critical",
      "tool": "run_bash_command",
      "command": "kubectl logs appconfigfail-7649c79dc5-q4zjz -n aiops-e2e --tail=50",
      "purpose": "获取应用启动阶段的错误日志输出"
    },
    {
      "id": "e3",
      "description": "查看关联 Deployment 的配置",
      "level": "important",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get deployment appconfigfail -n aiops-e2e -o yaml",
      "purpose": "检查 Deployment 的 Pod template 是否缺少环境变量 APP_BOOT_MODE"
    },
    {
      "id": "e4",
      "description": "查看 Pod 关联的 Events",
      "level": "critical",
      "tool": "kubectl_events",
      "command": "kubectl events --for pod/appconfigfail-7649c79dc5-q4zjz -n aiops-e2e",
      "purpose": "确认 CrashLoopBackOff 事件的详细时间线和原因"
    },
    {
      "id": "e5",
      "description": "查看 Pod 完整 YAML 定义",
      "level": "important",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e -o yaml",
      "purpose": "确认容器规格、环境变量、卷挂载等完整配置"
    },
    {
      "id": "e6",
      "description": "查看 node2 节点状态确认无节点级问题",
      "level": "important",
      "tool": "kubectl_get_by_name",
      "command": "kubectl get node node2 -o wide --show-labels",
      "purpose": "排除节点层面的干扰因素"
    }
  ],
  "collection_strategy": "先采集 Pod 级别的关键证据（describe + logs + events + yaml），确认 L4 配置校验失败的根因；再补充节点状态确认无干扰因素。"
}
```

## 第二步：逐项执行工具采集证据
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: appl
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 LAST SEEN              TYPE      REASON           OBJECT                               MESSAGE
41m                    Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully assig
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [证据链采集] 关键证据已全部采集。让我继续补充 Deployment YAML、Pod YAML 和节点状态。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  annotations:
    cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f
    cni.projectcalico.org/podIP: 172.16.104.57
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    deployment.kubernetes.io/revision: "1"
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"apps/v1","kind":"D
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node2   Ready    <none>   209d   v1.26.8   10.2.0.50     <
   ✅ [证据链采集] 完成 (15.5s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "查看异常 Pod 当前状态和退出历史", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e", "purpose": "确认退出码、容器命令、重启次数等关键信息"}, {"id": "e2", "description": "查看异常 Pod 的容器日志", "level": "critical", "tool": "run_bash_command", "command": "kubectl logs appconfigfail-7649c79dc5-q4zjz -n aiops-e2e --tail=50", "purpose": "获取应用启动阶段的错误日志输出"}, {"id": "e3", "description": "查看关联 Deployment 的配置", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get deployment appconfigfail -n aiops-e2e -o yaml", "purpose": "检查 Deployment 的 Pod template 是否缺少环境变量 APP_BOOT_MODE"}, {"id": "e4", "description": "查看 Pod 关联的 Events", "level": "critical", "tool": "kubectl_events", "command": "kubectl events --for pod/appconfigfail-7649c79dc5-q4zjz -n aiops-e2e", "purpose": "确认 CrashLoopBackOff 事件的详细时间线和原因"}, {"id": "e5", "description": "查看 Pod 完整 YAML 定义", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e -o yaml", "purpose": "确认容器规格、环境变量、卷挂载等完整配置"}, {"id": "e6", "description": "查看 node2 节点状态确认无节点级问题", "level": "important", "tool": "kubectl_get_by_name", "command": "kubectl get node node2 -o wide --show-labels", "purpose": "排除节点层面的干扰因素"}], "tool_results": [], "tool_data": [{"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\nL4_LAYER_APPLICATION: true\\nL4_SCENARIO: config-bootstrap-fail\\nL4_ERROR_TYPE: application-config-validation\\nFATAL: missing required APP_BOOT_MODE\\nFATAL: business config validation failed before server startup\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "kubectl_events", "data": "LAST SEEN              TYPE      REASON           OBJECT                               MESSAGE\n41m                    Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n41m                    Normal    AddedInterface   Pod/appconfigfail-7649c79dc5-q4zjz   Add eth0 [172.16.104.57/32] from k8s-pod-network\n40m (x5 over 41m)      Normal    Pulled           Pod/appconfigfail-7649c79dc5-q4zjz   Container image \"busybox:1.36\" already present on machine\n40m (x5 over 41m)      Normal    Created          Pod/appconfigfail-7649c79dc5-q4zjz   Created container app\n40m (x5 over 41m)      Normal    Started          Pod/appconfigfail-7649c79dc5-q4zjz   Started container app\n103s (x184 over 41m)   Warning   BackOff          Pod/appconfigfail-7649c79dc5-q4zjz   Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             appconfigfail-7649c79dc5-q4zjz\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             node2/10.2.0.50\nStart Time:       Wed, 22 Apr 2026 07:38:39 +0000\nLabels:           app=appconfigfail\n                  l4-scenario=config-bootstrap-fail\n                  pod-template-hash=7649c79dc5\nAnnotations:      cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f\n                  cni.projectcalico.org/podIP: 172.16.104.57/32\n                  cni.projectcalico.org/podIPs: 172.16.104.57/32\n                  k8s.v1.cni.cncf.io/network-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\n                  k8s.v1.cni.cncf.io/networks-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\nStatus:           Running\nIP:               172.16.104.57\nIPs:\n  IP:           172.16.104.57\nControlled By:  ReplicaSet/appconfigfail-7649c79dc5\nContainers:\n  app:\n    Container ID:  containerd://13fd13d7904fdfa5bf4756b8e1eac8f6ab98ff713f4098c8a987578461edc8aa\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      sh\n      -c\n    Args:\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n      \n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n      Started:      Wed, 22 Apr 2026 08:15:16 +0000\n      Finished:     Wed, 22 Apr 2026 08:15:16 +0000\n    Ready:          False\n    Restart Count:  12\n    Environment:    <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-zndsj (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             False \n  ContainersReady   False \n  PodScheduled      True \nVolumes:\n  kube-api-access-zndsj:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              <none>\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason          Age                   From               Message\n  ----     ------          ----                  ----               -------\n  Normal   Scheduled       41m                   default-scheduler  Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n  Normal   AddedInterface  41m                   multus             Add eth0 [172.16.104.57/32] from k8s-pod-network\n  Normal   Pulled          40m (x5 over 41m)     kubelet            Container image \"busybox:1.36\" already present on machine\n  Normal   Created         40m (x5 over 41m)     kubelet            Created container app\n  Normal   Started         40m (x5 over 41m)     kubelet            Started container app\n  Warning  BackOff         104s (x184 over 41m)  kubelet            Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f\n    cni.projectcalico.org/podIP: 172.16.104.57/32\n    cni.projectcalico.org/podIPs: 172.16.104.57/32\n    k8s.v1.cni.cncf.io/network-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.104.57\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n    k8s.v1.cni.cncf.io/networks-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.104.57\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n  creationTimestamp: \"2026-04-22T07:38:39Z\"\n  generateName: appconfigfail-7649c79dc5-\n  labels:\n    app: appconfigfail\n    l4-scenario: config-bootstrap-fail\n    pod-template-hash: 7649c79dc5\n  name: appconfigfail-7649c79dc5-q4zjz\n  namespace: aiops-e2e\n  ownerReferences:\n  - apiVersion: apps/v1\n    blockOwnerDeletion: true\n    controller: true\n    kind: ReplicaSet\n    name: appconfigfail-7649c79dc5\n    uid: 7b8b69a7-397c-4d54-b9c7-818ef9ad399f\n  resourceVersion: \"46421241\"\n  uid: 77ea5d65-2a07-47e0-b606-3f03812dcc6a\nspec:\n  containers:\n  - args:\n    - |\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n    command:\n    - sh\n    - -c\n    image: busybox:1.36\n    imagePullPolicy: Never\n    name: app\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-zndsj\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  nodeName: node2\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0\n  restartPolicy: Always\n  schedulerName: default-scheduler\n  securityContext: {}\n  serviceAccount: default\n  serviceAccountName: default\n  terminationGracePeriodSeconds: 30\n  tolerations:\n  - effect: NoExecute\n    key: node.kubernetes.io/not-ready\n    operator: Exists\n    tolerationSeconds: 300\n  - effect: NoExecute\n    key: node.kubernetes.io/unreachable\n    operator: Exists\n    tolerationSeconds: 300\n  volumes:\n  - name: kube-api-access-zndsj\n    projected:\n      defaultMode: 420\n      sources:\n      - serviceAccountToken:\n          expirationSeconds: 3607\n          path: token\n      - configMap:\n          items:\n          - key: ca.crt\n            path: ca.crt\n          name: kube-root-ca.crt\n      - downwardAPI:\n          items:\n          - fieldRef:\n              apiVersion: v1\n              fieldPath: metadata.namespace\n            path: namespace\nstatus:\n  conditions:\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    status: \"True\"\n    type: Initialized\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    message: 'containers with unready status: [app]'\n    reason: ContainersNotReady\n    status: \"False\"\n    type: Ready\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    message: 'containers with unready status: [app]'\n    reason: ContainersNotReady\n    status: \"False\"\n    type: ContainersReady\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    status: \"True\"\n    type: PodScheduled\n  containerStatuses:\n  - containerID: containerd://33dba510980e2d63aa8be62b5854b61a5c342fc43765a8d44fc8376655845e39\n    image: docker.io/library/busybox:1.36\n    imageID: sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    lastState:\n      terminated:\n        containerID: containerd://13fd13d7904fdfa5bf4756b8e1eac8f6ab98ff713f4098c8a987578461edc8aa\n        exitCode: 42\n        finishedAt: \"2026-04-22T08:15:16Z\"\n        reason: Error\n        startedAt: \"2026-04-22T08:15:16Z\"\n    name: app\n    ready: false\n    restartCount: 13\n    started: false\n    state:\n      terminated:\n        containerID: containerd://33dba510980e2d63aa8be62b5854b61a5c342fc43765a8d44fc8376655845e39\n        exitCode: 42\n        finishedAt: \"2026-04-22T08:20:26Z\"\n        reason: Error\n        startedAt: \"2026-04-22T08:20:26Z\"\n  hostIP: 10.2.0.50\n  phase: Running\n  podIP: 172.16.104.57\n  podIPs:\n  - ip: 172.16.104.57\n  qosClass: BestEffort\n  startTime: \"2026-04-22T07:38:39Z\"", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  annotations:\n    deployment.kubernetes.io/revision: \"1\"\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":\"apps/v1\",\"kind\":\"Deployment\",\"metadata\":{\"annotations\":{},\"labels\":{\"l4-scenario\":\"config-bootstrap-fail\"},\"name\":\"appconfigfail\",\"namespace\":\"aiops-e2e\"},\"spec\":{\"replicas\":1,\"selector\":{\"matchLabels\":{\"app\":\"appconfigfail\"}},\"template\":{\"metadata\":{\"labels\":{\"app\":\"appconfigfail\",\"l4-scenario\":\"config-bootstrap-fail\"}},\"spec\":{\"containers\":[{\"args\":[\"echo \\\"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\\"\\necho \\\"L4_LAYER_APPLICATION: true\\\"\\necho \\\"L4_SCENARIO: config-bootstrap-fail\\\"\\necho \\\"L4_ERROR_TYPE: application-config-validation\\\"\\nif [ -z \\\"${APP_BOOT_MODE:-}\\\" ]; then\\n  echo \\\"FATAL: missing required APP_BOOT_MODE\\\"\\n  echo \\\"FATAL: business config validation failed before server startup\\\"\\n  exit 42\\nfi\\necho \\\"unexpected success\\\"\\nexit 1\\n\"],\"command\":[\"sh\",\"-c\"],\"image\":\"busybox:1.36\",\"imagePullPolicy\":\"Never\",\"name\":\"app\"}]}}}}\n  creationTimestamp: \"2026-04-22T07:38:39Z\"\n  generation: 1\n  labels:\n    l4-scenario: config-bootstrap-fail\n  name: appconfigfail\n  namespace: aiops-e2e\n  resourceVersion: \"46415682\"\n  uid: 99cdabf8-f7bb-4fde-be0d-23711032bd1e\nspec:\n  progressDeadlineSeconds: 600\n  replicas: 1\n  revisionHistoryLimit: 10\n  selector:\n    matchLabels:\n      app: appconfigfail\n  strategy:\n    rollingUpdate:\n      maxSurge: 25%\n      maxUnavailable: 25%\n    type: RollingUpdate\n  template:\n    metadata:\n      creationTimestamp: null\n      labels:\n        app: appconfigfail\n        l4-scenario: config-bootstrap-fail\n    spec:\n      containers:\n      - args:\n        - |\n          echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n          echo \"L4_LAYER_APPLICATION: true\"\n          echo \"L4_SCENARIO: config-bootstrap-fail\"\n          echo \"L4_ERROR_TYPE: application-config-validation\"\n          if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n            echo \"FATAL: missing required APP_BOOT_MODE\"\n            echo \"FATAL: business config validation failed before server startup\"\n            exit 42\n          fi\n          echo \"unexpected success\"\n          exit 1\n        command:\n        - sh\n        - -c\n        image: busybox:1.36\n        imagePullPolicy: Never\n        name: app\n        resources: {}\n        terminationMessagePath: /dev/termination-log\n        terminationMessagePolicy: File\n      dnsPolicy: ClusterFirst\n      restartPolicy: Always\n      schedulerName: default-scheduler\n      securityContext: {}\n      terminationGracePeriodSeconds: 30\nstatus:\n  conditions:\n  - lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    lastUpdateTime: \"2026-04-22T07:38:39Z\"\n    message: Deployment does not have minimum availability.\n    reason: MinimumReplicasUnavailable\n    status: \"False\"\n    type: Available\n  - lastTransitionTime: \"2026-04-22T07:48:40Z\"\n    lastUpdateTime: \"2026-04-22T07:48:40Z\"\n    message: ReplicaSet \"appconfigfail-7649c79dc5\" has timed out progressing.\n    reason: ProgressDeadlineExceeded\n    status: \"False\"\n    type: Progressing\n  observedGeneration: 1\n  replicas: 1\n  unavailableReplicas: 1\n  updatedReplicas: 1", "duration_s": 0}, {"tool": "kubectl_get_by_name", "data": "NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode2   Ready    <none>   209d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}], "llm_analysis": "关键证据已全部采集。让我继续补充 Deployment YAML、Pod YAML 和节点状态。", "collection_summary": "计划 6 项，实际采集 6 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "e1", "description": "查看异常 Pod 当前状态和退出历史", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "查看异常 Pod 的容器日志", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "查看关联 Deployment 的配置", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "查看 Pod 关联的 Events", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "查看 Pod 完整 YAML 定义", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "查看 node2 节点状态确认无节点级问题", "level": "important", "collected": true, "source": "thinking_match"}], "missing_reasons": [], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/6 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (20.3s)
   📤 → 下游数据: root_cause=
   confidence=100%
   causal_chain={"root_cause": "Deployment appconfigfail 的容器定义中未配置环境变量 APP_BOOT_MODE", "propagation": "Pod 启动时，容器启动脚本执行 if [ -z \"${APP_BOOT_MODE:-}\" ] 检查 → 环境变量为空 → 脚本主动执行 exit 42 → 容器以 Error 终止 → kubelet 检测到退出码 42 并重启容器 → 反复失败触发 CrashLoopBackOff", "direct_cause": "容器启动脚本的配置校验逻辑检测到必需的 APP_BOOT_MODE 环境变量缺失", "manifestation": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态（重启 13 次），Deployment appconfigfail 不可用（ProgressDeadlineExceeded）"}
   rca_analysis={"phenomenon": "命名空间 aiops-e2e 中 Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态（已重启 13 次，退出码 42），导致 Deployment appconfigfail 不可用", "evidence_inventory": [{"id": "e1", "content": "Pod 事件：BackOff 重启警告，已重启 13 次", "source": "kubectl describe pod / events", "reliability": "高"}, {"id": "e2", "content": "容器日志：明确输出 L4_CONFIG_BOOTSTRAP_FAIL，FATAL: missing required APP_BOOT_MODE", "source": "容器日志 (run_bash_command)", "reliability": "高"}, {"id": "e3", "content": "Pod 规格：容器命令中包含 if [ -z \"${APP_BOOT_MODE:-}\" ]; then exit 42; fi，且 Environment: <none>", "source": "kubectl describe pod", "reliability": "高"}, {"id": "e4", "content": "Pod YAML：确认容器 args 中包含环境变量检查逻辑，无 env 字段", "source": "kubectl get pod -o yaml", "reliability": "高"}, {"id": "e5", "content": "Deployment YAML：容器定义中未配置任何环境变量，无 ConfigMap/Secret 引用", "source": "kubectl get deployment -o yaml", "reliability": "高"}, {"id": "e6", "content": "node2 节点状态：Ready，运行 209 天，Kubernetes v1.26.8，containerd 1.6.32", "source": "kubectl get node node2", "reliability": "高"}, {"id": "e7", "content": "集群整体：3/3 节点 Ready，所有系统组件正常", "source": "问题定位摘要", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "容器重启计数：13 次；退出码：42；最后退出时间：2026-04-22T08:20:26Z；BackOff 警告出现 184 次", "interpretation": "容器持续快速重启，退出码固定为 42，表明是应用主动退出而非系统级错误"}, {"evidence_id": "e2", "raw_data": "stdout: \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\n...FATAL: missing required APP_BOOT_MODE\\nFATAL: business config validation failed before server startup\\n\"", "interpretation": "应用启动脚本检测到 APP_BOOT_MODE 环境变量未设置，主动报告配置校验失败并退出"}, {"evidence_id": "e3", "raw_data": "容器命令: sh -c \"...if [ -z \\\"${APP_BOOT_MODE:-}\\\" ]; then echo FATAL; exit 42; fi\"; Environment: <none>", "interpretation": "容器启动脚本显式检查 APP_BOOT_MODE 变量，变量为空时触发 exit 42，与日志和退出码完全吻合"}, {"evidence_id": "e4", "raw_data": "spec.containers[0].env: null (未定义)", "interpretation": "Pod 规格中未定义任何环境变量，确认 APP_BOOT_MODE 确实未被注入"}, {"evidence_id": "e5", "raw_data": "Deployment spec.template.spec.containers[0]: 仅定义了 command/args/image，无 env、envFrom、ConfigMapRef 或 SecretRef", "interpretation": "Deployment 模板中缺少环境变量定义，所有 Pod 副本都会因同样原因失败"}, {"evidence_id": "e6", "raw_data": "节点 node2: STATUS=Ready, AGE=209d, OS=Ubuntu 22.04.4 LTS, KERNEL=5.15.0-174-generic, CONTAINER-RUNTIME=containerd://1.6.32", "interpretation": "节点状态正常，排除了节点级故障（资源不足、kubelet 异常等）"}, {"evidence_id": "e7", "raw_data": "集群 3/3 节点 Ready；系统组件 etcd, apiserver, coredns, calico, kube-proxy, multus 均 Running", "interpretation": "集群控制面和基础设施正常，问题局限在特定应用 Pod"}], "causal_chain": {"root_cause": "Deployment appconfigfail 的容器定义中未配置环境变量 APP_BOOT_MODE", "propagation": "Pod 启动时，容器启动脚本执行 if [ -z \"${APP_BOOT_MODE:-}\" ] 检查 → 环境变量为空 → 脚本主动执行 exit 42 → 容器以 Error 终止 → kubelet 检测到退出码 42 并重启容器 → 反复失败触发 CrashLoopBackOff", "direct_cause": "容器启动脚本的配置校验逻辑检测到必需的 APP_BOOT_MODE 环境变量缺失", "manifestation": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态（重启 13 次），Deployment appconfigfail 不可用（ProgressDeadlineExceeded）"}, "root_cause_summary": "根因是 Deployment appconfigfail 的容器定义中缺少环境变量 APP_BOOT_MODE。容器启动脚本（见 e3）显式检查该变量（if [ -z \"${APP_BOOT_MODE:-}\" ]），由于环境变量为空（Environment: <none>），脚本输出 'FATAL: missing required APP_BOOT_MODE'（见 e2）并执行 exit 42，导致容器以退出码 42 反复终止（见 e1）。Deployment YAML 确认未定义任何 env、envFrom、ConfigMap 或 Secret 引用（见 e5）。集群和节点状态均正常（e6, e7），排除基础设施故障。", "confidence": 1.0, "primary_runbooks": ["L4 应用启动配置校验失败 (Config Bootstrap Fail)"], "alternative_causes": [], "limitations": "证据充分，因果链完整清晰，无局限性"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 100%
   🔗 因果链:
     根本原因: Deployment appconfigfail 的容器定义中未配置环境变量 APP_BOOT_MODE
     传导机制: Pod 启动时，容器启动脚本执行 if [ -z "${APP_BOOT_MODE:-}" ] 检查 → 环境变量为空 → 脚本主动执行 exit 42 → 容器以 Error 终止 → kubelet 检测到退出码 42 并重启容器 → 反复失败触发 CrashLoopBackOff
     最终表现: Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态（重启 13 次），Deployment appconfigfail 不可用（ProgressDeadlineExceeded）


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (26.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5239 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 30.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您分析集群当前的状态和问题。

---
## 📊 诊断概览

**核心问题回答：您的集群整体运行正常，但有一个应用层 Pod 因缺少配置环境变量而处于持续重启状态。**

| 项目 | 内容 |
|------|------|
| **集群整体状态** | ✅ **健康**。3/3 节点 (master, node1, node2) 状态 Ready，所有系统组件 (etcd, apiserver, coredns, calico, kube-proxy 等) 运行正常。 |
| **问题层级** | **L4 - 应用层** |
| **问题分类** | **应用启动配置校验失败 (Config Bootstrap Fail)** |
| **影响范围** | **局部**。仅影响命名空间 `aiops-e2e` 下的 Deployment `appconfigfail` 及其 Pod。 |
| **置信度** | **高 (100%)** |
| **证据完整度** | 6/6 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|------|
| Pod | `appconfigfail-7649c79dc5-q4zjz` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| Deployment | `appconfigfail` |
| 错误状态 | `CrashLoopBackOff` |
| 退出码 | `42` |
| 错误日志 | `FATAL: missing required APP_BOOT_MODE` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与退出码 | `kubectl describe pod` | `State: Waiting (CrashLoopBackOff)`, `Last State: Terminated (Error)`, `Exit Code: 42`, `Restart Count: 13` | 容器因应用主动返回错误码 42 而反复退出重启。 |
| 2 | 容器日志 | `kubectl logs` | `L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config` ... `FATAL: missing required APP_BOOT_MODE` | 应用启动脚本明确报告因缺少 `APP_BOOT_MODE` 环境变量而校验失败。 |
| 3 | 容器启动命令 | `kubectl describe pod` | `Command: sh -c`, `Args: ... if [ -z "${APP_BOOT_MODE:-}" ]; then echo "FATAL..."; exit 42; fi` | 启动脚本逻辑与日志和退出码完全吻合：检查环境变量，为空则退出。 |
| 4 | Pod 环境变量 | `kubectl describe pod` | `Environment: <none>` | Pod 规格中未定义任何环境变量，确认 `APP_BOOT_MODE` 未被注入。 |
| 5 | Deployment 配置 | `kubectl get deployment -o yaml` | `spec.template.spec.containers[0]` 中 `env` 字段缺失，无 ConfigMap/Secret 引用。 | Deployment 模板未配置任何环境变量，所有新创建的 Pod 副本都会因此失败。 |
| 6 | 节点状态 | `kubectl get node node2` | `STATUS: Ready`, `AGE: 209d` | 节点运行正常，排除了节点级别的资源不足或故障。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：容器日志输出 `FATAL: missing required APP_BOOT_MODE`，启动脚本 `if [ -z "${APP_BOOT_MODE:-}" ]` 直接检查该变量，变量为空则执行 `exit 42`，导致 Pod 进入 `CrashLoopBackOff`。三者构成完整证据闭环。
- **证据 #4 + #5 印证**：Pod 和 Deployment 的配置均显示未定义任何环境变量，这直接解释了为何 `APP_BOOT_MODE` 为空。
- **证据 #6 + 集群概况**：节点及集群系统组件均正常，证明问题仅限于应用配置层。

### 缺失证据（如有）
无。所有关键和重要的证据均已完整采集。

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                        │
│ Deployment `appconfigfail` 的 Pod 模板中，容器定义未配置必需的环境变量 `APP_BOOT_MODE`。 │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                        │
│ Pod 启动 → 容器运行启动脚本 → 脚本检查 `${APP_BOOT_MODE:-}` 是否为空              │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                        │
│ 环境变量 `APP_BOOT_MODE` 为空，脚本执行 `exit 42`，容器主动终止。                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                    │
│ Pod 状态变为 `CrashLoopBackOff`（已重启 13 次），Deployment 不可用。               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (退出码 42)、证据 #2 (日志报错 `missing required APP_BOOT_MODE`)、证据 #3 (启动脚本逻辑) 及证据 #4/#5 (环境变量缺失) 的完整链条，问题的根本原因是 **Deployment `appconfigfail` 的容器配置中缺少名为 `APP_BOOT_MODE` 的环境变量**，导致应用启动时主动校验失败并退出。

**置信度**：高 (100%)
- ✅ 退出码、日志、启动脚本逻辑完全吻合。
- ✅ Pod 和 Deployment 配置确认了环境变量确实不存在。
- ✅ 已排除集群和节点级别故障。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为 Deployment 添加环境变量**
为 Deployment `appconfigfail` 添加缺失的 `APP_BOOT_MODE` 环境变量。`<your-value>` 请替换为实际所需的值（如 `production`, `development`, `staging` 等）。

```bash
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=<your-value>
```

*示例：*
```bash
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production
```

*依据*：该操作会直接修改 Deployment 模板，触发 RollingUpdate，创建新的、配置正确的 Pod，自动解决当前问题。

**2. [确认] 验证新 Pod 状态**
执行命令后，检查新 Pod 是否创建成功并正常运行。
```bash
kubectl get pods -n aiops-e2e -l app=appconfigfail -w
```
*预期结果*：旧 Pod 被终止，新 Pod 启动并进入 `Running` 状态，重启次数为 0。

### 后续优化
1.  **配置管理**：建议将 `APP_BOOT_MODE` 这类与环境相关的通用配置统一管理，可以通过 **ConfigMap** 或 **Secret** 注入，以便于不同环境（开发、测试、生产）的部署切换。
2.  **应用文档**：建议在应用部署文档或 Helm Chart 中明确声明所有必需的启动环境变量，避免类似问题再次发生。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod -n aiops-e2e -l app=appconfigfail` | `STATUS: Running`，`RESTARTS: 0` |
| 2. 检查 Deployment 状态 | `kubectl rollout status deployment/appconfigfail -n aiops-e2e` | `deployment "appconfigfail" successfully rolled out` |
| 3. 查看新 Pod 日志 | `kubectl logs deployment/appconfigfail -n aiops-e2e --tail=20` | 不再包含 `FATAL: missing required APP_BOOT_MODE` 错误。 |

---
## ⚠️ 注意事项
- 请确保为 `APP_BOOT_MODE` 设置的值是正确的、符合应用预期的值。
- 如果应用需要多个环境变量才能正常启动，请一次性完成所有配置，避免 Pod 再次重启。

---

## 📊 性能统计

├─ 总耗时: 1.5m
├─ 问题定位: 29.0s (32%) ✅
├─ 证据链采集: 15.5s (17%) ✅
├─ 根因分析: 20.3s (22%) ✅
├─ 汇总总结: 26.0s (29%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 15 次
```

📋 诊断追踪

- **核心 Runbook**: l4-config-bootstrap-fail
- **参考 Runbook**: l4-config-bootstrap-fail, private-k8s-health-reference
- **工具调用**: 15 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
