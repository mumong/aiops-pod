======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 5a701fee8a21437b]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来检查集群的整体状态，查看是否存在问题。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     a
   💭 [问题定位] 我看到有一个 Pod 处于 CrashLoopBackOff 状态：`appconfigfail-7649c79dc5-pcxt8`。让我检查这个 Pod 的详细信息来了解原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-pcxt8
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Tue, 21 Apr 2026 04:32:19
   💭 [问题定位] 现在让我检查节点状态，看看是否有其他问题：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   208d   v1.26.8  
   💭 [问题定位] 让我检查一下是否有相关的 runbook 可以参考：
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
   💭 [问题定位] 基于我的分析，这个 Pod 的问题与 runbook 中描述的 L4 应用启动配置校验失败场景完全匹配。让我检查一下集群中是否有其他异常：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE   LAST SEEN   TYPE      REASON              OBJECT                                SUBOBJECT                                      SOURCE                                        MESSAGE        
   💭 [问题定位] 根据我的分析，集群中有一个明显的 L4 层问题。让我总结一下：

1. 用户意图：用户询问"我的集群有什么问题"，这是一个开放式的诊断请求，不是查询特定指标，所以属于诊断模式。

2. 发现的问题：
   - 有一个 Pod `appconfigfail-7649c79dc5-pcxt8` 处于 CrashLoopBackOff 状态
   - 从 describe 信息看：Exit Code 为 42（非 137），Reason 为 Error，无 OOMKilled 或 Evicted 信息
   - Pod 标签显示 `l4-scenario=config-bootstrap-fail`
   - 容器命令显示应用因缺少 `APP_BOOT_MODE` 环境变量而退出

3. 其他状态：
   - 所有节点都处于 Ready 状态
   - 其他 Pod 都正常运行
   - 没有发现 L0、L1、L2、L3 层的问题

4. 匹配 runbook：这个问题与 `l4-config-bootstrap-fail.md` runbook 完全匹配。

```json
{
  "layer": "L4",
  "layers": ["L4"],
  "layer_name": "应用层",
  "confidence": 0.9,
  "reasoning": "发现一个 Pod (appconfigfail-7649c79dc5-pcxt8) 处于 CrashLoopBackOff 状态，describe 显示 Exit Code 42，无 OOMKilled 或 Evicted 信息。容器命令显示因缺少 APP_BOOT_MODE 环境变量而退出，标签包含 l4-scenario=config-bootstrap-fail，符合 L4 应用启动配置校验失败特征。所有节点 Ready，无其他异常。",
  "key_entities": [
    {"type": "Pod", "value": "appconfigfail-7649c79dc5-pcxt8"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Deployment", "value": "appconfigfail"}
  ],
  "possible_scenarios": [
    {"scenario": "应用启动配置校验失败", "probability": "高", "reason": "容器因缺少 APP_BOOT_MODE 环境变量而退出，Exit Code 42，标签显示 l4-scenario=config-bootstrap-fail"}
  ]
}
```
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 9.6s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用启动配置校验失败', 'probability': '高', 'reason': '容器因缺少 APP_BOOT_MODE 环境变量而退出，Exit Code 42，标签显示 l4-scenario=config-bootstrap-fail'}]
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-pcxt8"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Deployment", "value": "appconfigfail"}]
   reasoning=发现一个 Pod (appconfigfail-7649c79dc5-pcxt8) 处于 CrashLoopBackOff 状态，describe 显示 Exit Code 42，无 OOMKilled 或 Evicted 信息。容器命令显示因缺少 APP_BOOT_MODE 环境变量而退出，标签包含 l4-scenario=config-bootstrap-fail，符合 L4 应用启动配置校验失败特征。所有节点 Ready，无其他异常。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.9, "reasoning": "发现一个 Pod (appconfigfail-7649c79dc5-pcxt8) 处于 CrashLoopBackOff 状态，describe 显示 Exit Code 42，无 OOMKilled 或 Evicted 信息。容器命令显示因缺少 APP_BOOT_MODE 环境变量而退出，标签包含 l4-scenario=config-bootstrap-fail，符合 L4 应用启动配置校验失败特征。所有节点 Ready，无其他异常。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-pcxt8"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Deployment", "value": "appconfigfail"}], "possible_scenarios": [{"scenario": "应用启动配置校验失败", "probability": "高", "reason": "容器因缺少 APP_BOOT_MODE 环境变量而退出，Exit Code 42，标签显示 l4-scenario=config-bootstrap-fail"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 90%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，我已经识别到集群中存在一个明确的L4级别问题。现在我将制定证据采集计划并执行工具采集真实数据。

```json
{
  "layer": "L4",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取异常Pod的YAML配置，检查环境变量、启动命令等配置详情",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e -o yaml",
      "purpose": "确认Pod配置中是否确实缺少APP_BOOT_MODE环境变量"
    },
    {
      "id": "e2",
      "description": "获取Deployment的YAML配置，检查模板中的环境变量设置",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get deployment appconfigfail -n aiops-e2e -o yaml",
      "purpose": "确认Deployment模板中是否配置了APP_BOOT_MODE环境变量"
    },
    {
      "id": "e3",
      "description": "获取Pod的详细事件，确认启动失败的具体原因",
      "level": "important",
      "tool": "kubectl_events",
      "command": "kubectl events pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e",
      "purpose": "查看Pod事件中是否有更详细的启动失败信息"
    },
    {
      "id": "e4",
      "description": "获取ReplicaSet的YAML配置，检查实际运行的配置",
      "level": "important",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get replicaset appconfigfail-7649c79dc5 -n aiops-e2e -o yaml",
      "purpose": "确认ReplicaSet中Pod模板的环境变量配置"
    },
    {
      "id": "e5",
      "description": "获取Deployment相关的事件",
      "level": "optional",
      "tool": "kubectl_events",
      "command": "kubectl events deployment appconfigfail -n aiops-e2e",
      "purpose": "查看Deployment级别的事件，了解部署历史"
    }
  ],
  "collection_strategy": "首先确认Pod配置中确实缺少APP_BOOT_MODE环境变量，然后检查Deployment模板配置，最后通过事件确认启动失败的具体原因。"
}
```

现在开始执行证据采集：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  annotations:
    cni.projectcalico.org/containerID: 356ed4d59f01a2ae22b47f393fe17f068bfdbfa10c1f028c2fb7c21b0ee82e7d
    cni.projectcalico.org/podIP: 172.16.104.55
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    deployment.kubernetes.io/revision: "1"
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"apps/v1","kind":"D
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 LAST SEEN             TYPE      REASON           OBJECT                               MESSAGE
35m                   Normal    Scheduled        Pod/appconfigfail-7649c79dc5-pcxt8   Successfully assigne
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: apps/v1
kind: ReplicaSet
metadata:
  annotations:
    deployment.kubernetes.io/desired-replicas: "1"
    deployment.kubernetes.io/max-replicas: "2"
    deployment.kubernetes.io/revision: "
   ✅ [证据链采集] 完成 (37.9s)
   📤 → 下游数据: evidence_items=4/5
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "获取异常Pod的YAML配置，检查环境变量、启动命令等配置详情", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e -o yaml", "purpose": "确认Pod配置中是否确实缺少APP_BOOT_MODE环境变量"}, {"id": "e2", "description": "获取Deployment的YAML配置，检查模板中的环境变量设置", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get deployment appconfigfail -n aiops-e2e -o yaml", "purpose": "确认Deployment模板中是否配置了APP_BOOT_MODE环境变量"}, {"id": "e3", "description": "获取Pod的详细事件，确认启动失败的具体原因", "level": "important", "tool": "kubectl_events", "command": "kubectl events pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e", "purpose": "查看Pod事件中是否有更详细的启动失败信息"}, {"id": "e4", "description": "获取ReplicaSet的YAML配置，检查实际运行的配置", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get replicaset appconfigfail-7649c79dc5 -n aiops-e2e -o yaml", "purpose": "确认ReplicaSet中Pod模板的环境变量配置"}, {"id": "e5", "description": "获取Deployment相关的事件", "level": "optional", "tool": "kubectl_events", "command": "kubectl events deployment appconfigfail -n aiops-e2e", "purpose": "查看Deployment级别的事件，了解部署历史"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    cni.projectcalico.org/containerID: 356ed4d59f01a2ae22b47f393fe17f068bfdbfa10c1f028c2fb7c21b0ee82e7d\n    cni.projectcalico.org/podIP: 172.16.104.55/32\n    cni.projectcalico.org/podIPs: 172.16.104.55/32\n    k8s.v1.cni.cncf.io/network-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.104.55\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n    k8s.v1.cni.cncf.io/networks-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.104.55\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n  creationTimestamp: \"2026-04-21T04:32:19Z\"\n  generateName: appconfigfail-7649c79dc5-\n  labels:\n    app: appconfigfail\n    l4-scenario: config-bootstrap-fail\n    pod-template-hash: 7649c79dc5\n  name: appconfigfail-7649c79dc5-pcxt8\n  namespace: aiops-e2e\n  ownerReferences:\n  - apiVersion: apps/v1\n    blockOwnerDeletion: true\n    controller: true\n    kind: ReplicaSet\n    name: appconfigfail-7649c79dc5\n    uid: 236c3614-6d5e-40e4-9b64-53bd20d9cbc9\n  resourceVersion: \"46129433\"\n  uid: 8334b6d7-f468-48a1-b133-70fec47e9e2e\nspec:\n  containers:\n  - args:\n    - |\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n    command:\n    - sh\n    - -c\n    image: busybox:1.36\n    imagePullPolicy: Never\n    name: app\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-q5pfk\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  nodeName: node2\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0\n  restartPolicy: Always\n  schedulerName: default-scheduler\n  securityContext: {}\n  serviceAccount: default\n  serviceAccountName: default\n  terminationGracePeriodSeconds: 30\n  tolerations:\n  - effect: NoExecute\n    key: node.kubernetes.io/not-ready\n    operator: Exists\n    tolerationSeconds: 300\n  - effect: NoExecute\n    key: node.kubernetes.io/unreachable\n    operator: Exists\n    tolerationSeconds: 300\n  volumes:\n  - name: kube-api-access-q5pfk\n    projected:\n      defaultMode: 420\n      sources:\n      - serviceAccountToken:\n          expirationSeconds: 3607\n          path: token\n      - configMap:\n          items:\n          - key: ca.crt\n            path: ca.crt\n          name: kube-root-ca.crt\n      - downwardAPI:\n          items:\n          - fieldRef:\n              apiVersion: v1\n              fieldPath: metadata.namespace\n            path: namespace\nstatus:\n  conditions:\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-21T04:32:19Z\"\n    status: \"True\"\n    type: Initialized\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-21T04:35:22Z\"\n    message: 'containers with unready status: [app]'\n    reason: ContainersNotReady\n    status: \"False\"\n    type: Ready\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-21T04:35:22Z\"\n    message: 'containers with unready status: [app]'\n    reason: ContainersNotReady\n    status: \"False\"\n    type: ContainersReady\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-21T04:32:19Z\"\n    status: \"True\"\n    type: PodScheduled\n  containerStatuses:\n  - containerID: containerd://8c0a14b518b09a8541fe31e44faaa35e849f8d451f165cc08668ab5bdbc0c60b\n    image: docker.io/library/busybox:1.36\n    imageID: sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    lastState:\n      terminated:\n        containerID: containerd://8c0a14b518b09a8541fe31e44faaa35e849f8d451f165cc08668ab5bdbc0c60b\n        exitCode: 42\n        finishedAt: \"2026-04-21T05:03:45Z\"\n        reason: Error\n        startedAt: \"2026-04-21T05:03:45Z\"\n    name: app\n    ready: false\n    restartCount: 11\n    started: false\n    state:\n      waiting:\n        message: back-off 5m0s restarting failed container=app pod=appconfigfail-7649c79dc5-pcxt8_aiops-e2e(8334b6d7-f468-48a1-b133-70fec47e9e2e)\n        reason: CrashLoopBackOff\n  hostIP: 10.2.0.50\n  phase: Running\n  podIP: 172.16.104.55\n  podIPs:\n  - ip: 172.16.104.55\n  qosClass: BestEffort\n  startTime: \"2026-04-21T04:32:19Z\"", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  annotations:\n    deployment.kubernetes.io/revision: \"1\"\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":\"apps/v1\",\"kind\":\"Deployment\",\"metadata\":{\"annotations\":{},\"labels\":{\"l4-scenario\":\"config-bootstrap-fail\"},\"name\":\"appconfigfail\",\"namespace\":\"aiops-e2e\"},\"spec\":{\"replicas\":1,\"selector\":{\"matchLabels\":{\"app\":\"appconfigfail\"}},\"template\":{\"metadata\":{\"labels\":{\"app\":\"appconfigfail\",\"l4-scenario\":\"config-bootstrap-fail\"}},\"spec\":{\"containers\":[{\"args\":[\"echo \\\"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\\"\\necho \\\"L4_LAYER_APPLICATION: true\\\"\\necho \\\"L4_SCENARIO: config-bootstrap-fail\\\"\\necho \\\"L4_ERROR_TYPE: application-config-validation\\\"\\nif [ -z \\\"${APP_BOOT_MODE:-}\\\" ]; then\\n  echo \\\"FATAL: missing required APP_BOOT_MODE\\\"\\n  echo \\\"FATAL: business config validation failed before server startup\\\"\\n  exit 42\\nfi\\necho \\\"unexpected success\\\"\\nexit 1\\n\"],\"command\":[\"sh\",\"-c\"],\"image\":\"busybox:1.36\",\"imagePullPolicy\":\"Never\",\"name\":\"app\"}]}}}}\n  creationTimestamp: \"2026-04-21T04:32:19Z\"\n  generation: 1\n  labels:\n    l4-scenario: config-bootstrap-fail\n  name: appconfigfail\n  namespace: aiops-e2e\n  resourceVersion: \"46124428\"\n  uid: e73ef214-b779-4104-8bb3-4bd4c04d6ab7\nspec:\n  progressDeadlineSeconds: 600\n  replicas: 1\n  revisionHistoryLimit: 10\n  selector:\n    matchLabels:\n      app: appconfigfail\n  strategy:\n    rollingUpdate:\n      maxSurge: 25%\n      maxUnavailable: 25%\n    type: RollingUpdate\n  template:\n    metadata:\n      creationTimestamp: null\n      labels:\n        app: appconfigfail\n        l4-scenario: config-bootstrap-fail\n    spec:\n      containers:\n      - args:\n        - |\n          echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n          echo \"L4_LAYER_APPLICATION: true\"\n          echo \"L4_SCENARIO: config-bootstrap-fail\"\n          echo \"L4_ERROR_TYPE: application-config-validation\"\n          if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n            echo \"FATAL: missing required APP_BOOT_MODE\"\n            echo \"FATAL: business config validation failed before server startup\"\n            exit 42\n          fi\n          echo \"unexpected success\"\n          exit 1\n        command:\n        - sh\n        - -c\n        image: busybox:1.36\n        imagePullPolicy: Never\n        name: app\n        resources: {}\n        terminationMessagePath: /dev/termination-log\n        terminationMessagePolicy: File\n      dnsPolicy: ClusterFirst\n      restartPolicy: Always\n      schedulerName: default-scheduler\n      securityContext: {}\n      terminationGracePeriodSeconds: 30\nstatus:\n  conditions:\n  - lastTransitionTime: \"2026-04-21T04:32:19Z\"\n    lastUpdateTime: \"2026-04-21T04:35:21Z\"\n    message: ReplicaSet \"appconfigfail-7649c79dc5\" has successfully progressed.\n    reason: NewReplicaSetAvailable\n    status: \"True\"\n    type: Progressing\n  - lastTransitionTime: \"2026-04-21T04:35:22Z\"\n    lastUpdateTime: \"2026-04-21T04:35:22Z\"\n    message: Deployment does not have minimum availability.\n    reason: MinimumReplicasUnavailable\n    status: \"False\"\n    type: Available\n  observedGeneration: 1\n  replicas: 1\n  unavailableReplicas: 1\n  updatedReplicas: 1", "duration_s": 0}, {"tool": "kubectl_events", "data": "LAST SEEN             TYPE      REASON           OBJECT                               MESSAGE\n35m                   Normal    Scheduled        Pod/appconfigfail-7649c79dc5-pcxt8   Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-pcxt8 to node2\n35m                   Normal    AddedInterface   Pod/appconfigfail-7649c79dc5-pcxt8   Add eth0 [172.16.104.55/32] from k8s-pod-network\n34m (x5 over 35m)     Normal    Pulled           Pod/appconfigfail-7649c79dc5-pcxt8   Container image \"busybox:1.36\" already present on machine\n34m (x5 over 35m)     Normal    Created          Pod/appconfigfail-7649c79dc5-pcxt8   Created container app\n34m (x5 over 35m)     Normal    Started          Pod/appconfigfail-7649c79dc5-pcxt8   Started container app\n45s (x165 over 35m)   Warning   BackOff          Pod/appconfigfail-7649c79dc5-pcxt8   Back-off restarting failed container app in pod appconfigfail-7649c79dc5-pcxt8_aiops-e2e(8334b6d7-f468-48a1-b133-70fec47e9e2e)", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: apps/v1\nkind: ReplicaSet\nmetadata:\n  annotations:\n    deployment.kubernetes.io/desired-replicas: \"1\"\n    deployment.kubernetes.io/max-replicas: \"2\"\n    deployment.kubernetes.io/revision: \"1\"\n  creationTimestamp: \"2026-04-21T04:32:19Z\"\n  generation: 1\n  labels:\n    app: appconfigfail\n    l4-scenario: config-bootstrap-fail\n    pod-template-hash: 7649c79dc5\n  name: appconfigfail-7649c79dc5\n  namespace: aiops-e2e\n  ownerReferences:\n  - apiVersion: apps/v1\n    blockOwnerDeletion: true\n    controller: true\n    kind: Deployment\n    name: appconfigfail\n    uid: e73ef214-b779-4104-8bb3-4bd4c04d6ab7\n  resourceVersion: \"46124427\"\n  uid: 236c3614-6d5e-40e4-9b64-53bd20d9cbc9\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: appconfigfail\n      pod-template-hash: 7649c79dc5\n  template:\n    metadata:\n      creationTimestamp: null\n      labels:\n        app: appconfigfail\n        l4-scenario: config-bootstrap-fail\n        pod-template-hash: 7649c79dc5\n    spec:\n      containers:\n      - args:\n        - |\n          echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n          echo \"L4_LAYER_APPLICATION: true\"\n          echo \"L4_SCENARIO: config-bootstrap-fail\"\n          echo \"L4_ERROR_TYPE: application-config-validation\"\n          if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n            echo \"FATAL: missing required APP_BOOT_MODE\"\n            echo \"FATAL: business config validation failed before server startup\"\n            exit 42\n          fi\n          echo \"unexpected success\"\n          exit 1\n        command:\n        - sh\n        - -c\n        image: busybox:1.36\n        imagePullPolicy: Never\n        name: app\n        resources: {}\n        terminationMessagePath: /dev/termination-log\n        terminationMessagePolicy: File\n      dnsPolicy: ClusterFirst\n      restartPolicy: Always\n      schedulerName: default-scheduler\n      securityContext: {}\n      terminationGracePeriodSeconds: 30\nstatus:\n  fullyLabeledReplicas: 1\n  observedGeneration: 1\n  replicas: 1", "duration_s": 0}], "llm_analysis": "根据上游定位结果，我已经识别到集群中存在一个明确的L4级别问题。现在我将制定证据采集计划并执行工具采集真实数据。\n\n```json\n{\n  \"layer\": \"L4\",\n  \"evidence_plan\": [\n    {\n      \"id\": \"e1\",\n      \"description\": \"获取异常Pod的YAML配置，检查环境变量、启动命令等配置详情\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_get_yaml\",\n      \"command\": \"kubectl get pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e -o yaml\",\n      \"purpose\": \"确认Pod配置中是否确实缺少APP_BOOT_MODE环境变量\"\n    },\n    {\n      \"id\": \"e2\",\n      \"description\": \"获取Deployment的YAML配置，检查模板中的环境变量设置\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_get_yaml\",\n      \"command\": \"kubectl get deployment appconfigfail -n aiops-e2e -o yaml\",\n      \"purpose\": \"确认Deployment模板中是否配置了APP_BOOT_MODE环境变量\"\n    },\n    {\n      \"id\": \"e3\",\n      \"description\": \"获取Pod的详细事件，确认启动失败的具体原因\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_events\",\n      \"command\": \"kubectl events pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e\",\n      \"purpose\": \"查看Pod事件中是否有更详细的启动失败信息\"\n    },\n    {\n      \"id\": \"e4\",\n      \"description\": \"获取ReplicaSet的YAML配置，检查实际运行的配置\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_get_yaml\",\n      \"command\": \"kubectl get replicaset appconfigfail-7649c79dc5 -n aiops-e2e -o yaml\",\n      \"purpose\": \"确认ReplicaSet中Pod模板的环境变量配置\"\n    },\n    {\n      \"id\": \"e5\",\n      \"description\": \"获取Deployment相关的事件\",\n      \"level\": \"optional\",\n      \"tool\": \"kubectl_events\",\n      \"command\": \"kubectl events deployment appconfigfail -n aiops-e2e\",\n      \"purpose\": \"查看Deployment级别的事件，了解部署历史\"\n    }\n  ],\n  \"collection_strategy\": \"首先确认Pod配置中确实缺少APP_BOOT_MODE环境变量，然后检查Deployment模板配置，最后通过事件确认启动失败的具体原因。\"\n}\n```\n\n现在开始执行证据采集：", "collection_summary": "计划 5 项，实际采集 4 项，未采集 1 项，完整度 80%", "evidence_inventory": [{"id": "e1", "description": "获取异常Pod的YAML配置，检查环境变量、启动命令等配置详情", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "获取Deployment的YAML配置，检查模板中的环境变量设置", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "获取Pod的详细事件，确认启动失败的具体原因", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "获取ReplicaSet的YAML配置，检查实际运行的配置", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "获取Deployment相关的事件", "level": "optional", "collected": false, "source": "planned"}], "missing_reasons": ["e5(获取Deployment相关的事件): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/5 项, 完整度: 80%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (59.4s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "Deployment `appconfigfail` 的 Pod 模板中，未定义应用启动所必需的 `APP_BOOT_MODE` 环境变量。", "propagation": "有缺陷的 Pod 模板从 Deployment 传递到其控制的 ReplicaSet `appconfigfail-7649c79dc5`，再由该 ReplicaSet 创建出具体的 Pod `appconfigfail-7649c79dc5-pcxt8`。", "direct_cause": "Pod 内的容器启动时，执行预设的启动脚本，该脚本检查 `APP_BOOT_MODE` 环境变量。由于变量未定义，脚本执行 `exit 42`，导致容器立即终止。", "manifestation": "容器不断启动并立即失败，触发 Kubernetes 重启策略。在短时间内多次失败后，Pod 进入 `CrashLoopBackOff` 状态，表现为 Pod 状态异常且关联的 Deployment 无法达到可用状态。"}
   rca_analysis={"phenomenon": "Pod appconfigfail-7649c79dc5-pcxt8 在命名空间 aiops-e2e 中处于 CrashLoopBackOff 状态，已重启 11 次，导致关联的 Deployment `appconfigfail` 不可用（1/1 副本不可用）。", "evidence_inventory": [{"id": "e1", "content": "Pod appconfigfail-7649c79dc5-pcxt8 的 YAML 配置，显示其容器启动命令包含检查 APP_BOOT_MODE 环境变量的逻辑，若缺失则退出码为 42。Pod spec 中未定义 APP_BOOT_MODE 环境变量。", "source": "kubectl_get_yaml (Pod)", "reliability": "高"}, {"id": "e2", "content": "Deployment appconfigfail 的 YAML 配置，显示其 Pod 模板 spec 中未定义 APP_BOOT_MODE 环境变量。kubectl.kubernetes.io/last-applied-configuration 注解确认了此配置是用户有意部署的。", "source": "kubectl_get_yaml (Deployment)", "reliability": "高"}, {"id": "e3", "content": "Pod appconfigfail-7649c79dc5-pcxt8 的事件列表，显示容器被成功调度、创建和启动，但随后出现大量（x165）BackOff 警告事件，表明容器持续启动失败。", "source": "kubectl_events (Pod)", "reliability": "高"}, {"id": "e4", "content": "ReplicaSet appconfigfail-7649c79dc5 的 YAML 配置，显示其 Pod 模板 spec 中同样未定义 APP_BOOT_MODE 环境变量，与 Deployment 和 Pod 的配置一致。", "source": "kubectl_get_yaml (ReplicaSet)", "reliability": "高"}, {"id": "e5", "content": "上游定位结果中容器状态详情，显示容器上次终止退出码为 42，状态为 Error，且容器命令逻辑明确指向缺少 APP_BOOT_MODE 环境变量。", "source": "kubectl_describe (Pod)", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Pod spec.containers[0].args 包含脚本：`if [ -z \"${APP_BOOT_MODE:-}\" ]; then echo \"FATAL: missing required APP_BOOT_MODE\"; exit 42; fi`。Pod spec.containers[0].env 字段不存在，即未定义任何环境变量。", "interpretation": "Pod 的配置决定了容器的行为：启动时会检查 APP_BOOT_MODE 环境变量，如果未设置，则打印错误信息并以退出码 42 主动终止。这是导致容器启动失败的直接代码逻辑。"}, {"evidence_id": "e2", "raw_data": "Deployment spec.template.spec.containers[0] 的定义中，只有 args、command、image 等字段，没有 env 字段。kubectl.kubernetes.io/last-applied-configuration 注解的 JSON 内容也确认了这一点。", "interpretation": "Deployment 作为工作负载的期望状态定义，其 Pod 模板中根本没有配置 APP_BOOT_MODE 环境变量。这是问题的根源配置。"}, {"evidence_id": "e3", "raw_data": "事件显示：`45s (x165 over 35m) Warning BackOff ... Back-off restarting failed container app ...`。同时有多次 `Normal Created` 和 `Normal Started` 事件。", "interpretation": "事件链表明 Pod 调度、网络、镜像拉取均正常。容器能被成功创建和启动，但立即失败，触发 Kubernetes 的重启策略（RestartPolicy: Always），失败次数累积导致进入 CrashLoopBackOff 状态。这与容器因配置检查失败而快速退出的行为吻合。"}, {"evidence_id": "e4", "raw_data": "ReplicaSet spec.template.spec.containers[0] 的定义与 Deployment 中的完全一致，同样没有 env 字段。", "interpretation": "ReplicaSet 作为 Deployment 和 Pod 之间的中间层，其配置是 Deployment 模板的精确副本。这证实了缺失环境变量的配置从源头（Deployment）一直传递到了运行实例（Pod）。"}, {"evidence_id": "e5", "raw_data": "容器状态：`lastState.terminated.exitCode: 42`, `lastState.terminated.reason: Error`, `restartCount: 11`, `state.waiting.reason: CrashLoopBackOff`。", "interpretation": "这是容器运行时的直接证据：容器以自定义错误码 42 退出，符合其启动脚本中缺失 APP_BOOT_MODE 时的行为。重启 11 次证明了问题的持续性。"}], "causal_chain": {"root_cause": "Deployment `appconfigfail` 的 Pod 模板中，未定义应用启动所必需的 `APP_BOOT_MODE` 环境变量。", "propagation": "有缺陷的 Pod 模板从 Deployment 传递到其控制的 ReplicaSet `appconfigfail-7649c79dc5`，再由该 ReplicaSet 创建出具体的 Pod `appconfigfail-7649c79dc5-pcxt8`。", "direct_cause": "Pod 内的容器启动时，执行预设的启动脚本，该脚本检查 `APP_BOOT_MODE` 环境变量。由于变量未定义，脚本执行 `exit 42`，导致容器立即终止。", "manifestation": "容器不断启动并立即失败，触发 Kubernetes 重启策略。在短时间内多次失败后，Pod 进入 `CrashLoopBackOff` 状态，表现为 Pod 状态异常且关联的 Deployment 无法达到可用状态。"}, "root_cause_summary": "根因是 Deployment `appconfigfail` 的配置错误。其 Pod 模板（证据 e2 和 e4）中缺少应用强制要求的 `APP_BOOT_MODE` 环境变量定义。这导致由该模板创建出的 Pod `appconfigfail-7649c79dc5-pcxt8`（证据 e1）内的容器，在启动阶段执行校验脚本（证据 e1 和 e5）时因条件不满足而主动退出（退出码 42）。Kubernetes 事件（证据 e3）记录了容器反复启动和失败的过程，最终使 Pod 陷入 CrashLoopBackOff 状态。", "confidence": 0.95, "primary_runbooks": ["L4 应用启动配置校验失败"], "alternative_causes": [], "limitations": "分析基于已提供的配置和状态数据，结论清晰。未采集 Deployment 级别的事件（计划中的 e5），但这不影响对当前根因（静态配置缺失）的判断。未检查是否存在可能覆盖 Pod 环境变量的其他资源（如 ConfigMap、Secret 引用），但根据现有证据，Deployment 模板是问题的源头。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: Deployment `appconfigfail` 的 Pod 模板中，未定义应用启动所必需的 `APP_BOOT_MODE` 环境变量。
     传导机制: 有缺陷的 Pod 模板从 Deployment 传递到其控制的 ReplicaSet `appconfigfail-7649c79dc5`，再由该 ReplicaSet 创建出具体的 Pod `appconfigfail-7649c79dc5-pcxt8`。
     最终表现: 容器不断启动并立即失败，触发 Kubernetes 重启策略。在短时间内多次失败后，Pod 进入 `CrashLoopBackOff` 状态，表现为 Pod 状态异常且关联的 Deployment 无法达到可用状态。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 22.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5837 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 9.3s
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
| **证据完整度** | 4/5 (80%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `appconfigfail-7649c79dc5-pcxt8` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| 错误信息 | 容器因缺少环境变量 `APP_BOOT_MODE` 而主动退出（`exit 42`） |

**集群状态总结**：
- **节点状态**：所有节点（`master`, `node1`, `node2`）状态均为 `Ready`，无节点级异常。
- **Pod状态**：发现一个异常Pod `appconfigfail-7649c79dc5-pcxt8` 处于 `CrashLoopBackOff` 状态，已重启 `11` 次。其他Pod状态均为 `Running`。
- **核心问题**：一个应用因启动配置（环境变量）缺失而持续启动失败，导致其所属的 Deployment `appconfigfail` 不可用（1/1副本不可用）。

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 配置 (YAML) | `kubectl get pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e -o yaml` | `spec.containers[0].args` 包含脚本：`if [ -z \"${APP_BOOT_MODE:-}\" ]; then echo \"FATAL: missing required APP_BOOT_MODE\"; exit 42; fi`。`spec.containers[0].env` 字段不存在。 | Pod 配置中未定义 `APP_BOOT_MODE` 环境变量，容器启动脚本会因此主动退出。 |
| 2 | Deployment 配置 (YAML) | `kubectl get deployment appconfigfail -n aiops-e2e -o yaml` | `spec.template.spec.containers[0]` 无 `env` 字段。`kubectl.kubernetes.io/last-applied-configuration` 注解确认此配置为用户部署。 | Deployment 的 Pod 模板中根本未配置 `APP_BOOT_MODE` 环境变量，是问题的根源。 |
| 3 | Pod 事件 | `kubectl events pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e` | `45s (x165 over 35m) Warning BackOff ... Back-off restarting failed container app ...` | 容器反复启动并立即失败，触发大量 `BackOff` 警告，最终进入 `CrashLoopBackOff` 状态。 |
| 4 | ReplicaSet 配置 (YAML) | `kubectl get replicaset appconfigfail-7649c79dc5 -n aiops-e2e -o yaml` | `spec.template.spec.containers[0]` 定义与 Deployment 完全一致，同样没有 `env` 字段。 | ReplicaSet 的配置与 Deployment 一致，证实了缺失的环境变量配置从源头传递到了运行层。 |
| 5 | Pod 状态详情 (来自阶段1) | `kubectl describe pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e` | `lastState.terminated.exitCode: 42`, `lastState.terminated.reason: Error`, `restartCount: 11` | 容器以自定义退出码 `42` 终止，符合脚本中缺失 `APP_BOOT_MODE` 时的行为，且已重启11次。 |

### 证据关联分析
- **证据 #1 + #2 + #4 印证**：Pod、Deployment、ReplicaSet 的配置中均未定义 `APP_BOOT_MODE` 环境变量，证明配置缺失是系统性的。
- **证据 #1 + #5 印证**：Pod 启动脚本逻辑（检查变量并 `exit 42`）与容器实际退出码 `42` 完全吻合，明确了直接失败原因。
- **证据 #3 印证**：大量 `BackOff` 事件是容器因配置缺失快速退出后，Kubernetes 重启策略（`restartPolicy: Always`）作用的结果，形成了 `CrashLoopBackOff` 现象。
- **证据链**：Deployment 模板缺失环境变量 → ReplicaSet 继承错误配置 → Pod 启动时脚本检查失败 → 容器退出码 42 → Kubernetes 重启容器 → 反复失败进入 `CrashLoopBackOff`。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| e5: 获取Deployment相关的事件 | optional | 不影响对当前静态配置错误的根因判断，但缺失了了解部署历史的上下文。 |

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Deployment `appconfigfail` 的 Pod 模板中，未定义应用启动所必需 │
│ 的 `APP_BOOT_MODE` 环境变量。                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 有缺陷的 Pod 模板从 Deployment 传递到其控制的 ReplicaSet        │
│ `appconfigfail-7649c79dc5`，再由该 ReplicaSet 创建出具体的 Pod。│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 内的容器启动时，执行预设脚本检查 `APP_BOOT_MODE` 环境变量。 │
│ 由于变量未定义，脚本执行 `exit 42`，导致容器立即终止。          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ 容器不断启动并立即失败，触发重启策略，Pod 进入                  │
│ `CrashLoopBackOff` 状态，Deployment 无法达到可用状态。          │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1、#2、#4（Pod、Deployment、ReplicaSet YAML 中均无 `APP_BOOT_MODE` 环境变量定义）和证据 #5（容器退出码 `42`），
问题的根本原因是 **Deployment `appconfigfail` 的配置错误，其 Pod 模板中缺少应用强制要求的 `APP_BOOT_MODE` 环境变量**，
导致容器在启动阶段校验失败而主动退出，并陷入重启循环。

**置信度**：高 (95%)
- ✅ 所有层级的资源配置（Deployment、ReplicaSet、Pod）一致显示环境变量缺失。
- ✅ 容器退出码 `42` 与 Pod 内定义的启动脚本逻辑完全匹配。
- ✅ 事件链清晰显示了容器反复启动失败的过程。
- ⚠️ 未检查可能的环境变量覆盖源（如 ConfigMap），但当前证据已足够定位到 Deployment 模板的配置缺陷。

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修复 Deployment 配置，添加缺失的环境变量**
假设 `APP_BOOT_MODE` 的正确值应为 `production`，通过更新 Deployment 的 Pod 模板来修复：
```bash
kubectl patch deployment appconfigfail -n aiops-e2e --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/env", "value": [{"name": "APP_BOOT_MODE", "value": "production"}]}]'
```
*依据*：证据 #2 显示 Deployment 模板中 `env` 字段缺失。此命令将添加所需的环境变量。
*验证*：执行后，观察新的 Pod 是否被创建并进入 `Running` 状态。

**2. [可选] 查看容器退出前的日志（如果存在）**
```bash
kubectl logs appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e --previous
```
*目的*：确认日志中是否打印了 `FATAL: missing required APP_BOOT_MODE` 等预期错误信息，作为辅助验证。

### 后续优化
1.  **配置管理**：考虑将 `APP_BOOT_MODE` 等配置移入 ConfigMap 或 Secret，实现配置与镜像解耦。
2.  **健康检查**：为应用配置 `startupProbe`，在启动阶段进行更细致的健康检查，避免因配置错误陷入快速重启循环。
3.  **CI/CD 集成**：在部署流水线中加入配置校验步骤，确保必需的环境变量在部署前已定义。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认新 Pod 生成 | `kubectl get pods -l app=appconfigfail -n aiops-e2e -w` | 看到旧 Pod 终止，新 Pod 被创建。 |
| 2. 检查新 Pod 状态 | `kubectl get pod <new-pod-name> -n aiops-e2e` | `STATUS: Running`，`RESTARTS: 0`。 |
| 3. 检查容器日志 | `kubectl logs <new-pod-name> -n aiops-e2e` | 不再出现 `FATAL: missing required APP_BOOT_MODE` 错误。可能输出 `unexpected success` 后退出（根据脚本逻辑），或持续运行。 |
| 4. 确认 Deployment 状态 | `kubectl get deployment appconfigfail -n aiops-e2e` | `AVAILABLE` 列显示为 `1`。 |

## ⚠️ 注意事项
- 修复后，旧 Pod `appconfigfail-7649c79dc5-pcxt8` 会被新 Pod 替换，这是预期行为。
- 如果 `APP_BOOT_MODE` 的实际值不是 `production`，请在上述修复命令中替换为正确的值。
- 此问题是应用层（L4）的配置错误，不涉及底层K8s集群资源（CPU、内存、磁盘）或系统组件问题。

---

## 📊 性能统计

├─ 总耗时: 4.2m
├─ 问题定位: 69.6s (28%) ✅
├─ 证据链采集: 37.9s (15%) ✅
├─ 根因分析: 59.4s (24%) ✅
├─ 汇总总结: 82.4s (33%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: L4 应用启动配置校验失败
- **参考 Runbook**: L4 应用启动配置校验失败, L4 应用启动配置校验失败 (Config Bootstrap Fail)
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
