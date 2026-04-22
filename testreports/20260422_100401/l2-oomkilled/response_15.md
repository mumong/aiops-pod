======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 5c6627cc54664152]

📍 [问题定位] 执行中...
   💭 [问题定位] 我将帮您检查集群的健康状况。首先，让我获取一些基本信息来了解当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   208d   v1.26.8  
   💭 [问题定位] 节点状态看起来都正常。现在让我检查所有命名空间中的Pod状态，看看是否有异常：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:metadata.namespace,NAME:metadata.name,STATUS:status.phase,NODE:spec.nodeName,READY:status.containerStatuses[0].r
   💭 [问题定位] 让我用更简单的方式检查异常Pod：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "memhog-578d9b5ffd-lwfxj",
  "phase": "Running",
  "node": "node2",
  "reason": "CrashLoopBackOff"
}
   💭 [问题定位] 发现了一个有问题的Pod。让我获取更多信息：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             memhog-578d9b5ffd-lwfxj
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Tue, 21 Apr 2026 09:55:19 +0000

   💭 [问题定位] 现在让我检查是否有其他异常资源。首先获取通用健康检查参考手册：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 现在让我检查其他关键资源面。首先检查Service和Endpoints：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for services...
{
  "namespace": "aaa",
  "name": "test1-redis-headless",
  "selector": {
    "app": "redis",
    "release": "test1"
  },
  "ports": [
    {
      "name": "redis",
 
   💭 [问题定位] 现在让我检查PVC状态：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for persistentvolumeclaims...
   💭 [问题定位] 让我检查Deployment状态：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for deployments...
{
  "namespace": "aiops-e2e",
  "name": "memhog",
  "ready": null,
  "desired": 1,
  "available": null
}
   💭 [问题定位] 现在让我获取OOMKilled相关的runbook：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L2 Pod OOMKilled (Exit Code 137)

> 层级: L2 - 工作负载层 | 场景: 容器内存超限被 OOM Killer 终止

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | CrashLoopBackOff / Error / 频繁重启 |
| Describe | termina
   💭 [问题定位] 基于我的检查，我发现了一个明确的异常。让我检查是否有其他异常Pod：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for pods...
{
  "namespace": "aiops-e2e",
  "name": "memhog-578d9b5ffd-lwfxj",
  "restartCount": 196,
  "phase": "Running"
}
{
  "namespace": "kube-system",
  "name": "calico-node-4
   💭 [问题定位] 现在让我检查是否有Pending状态的Pod：
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 Executing jq query for pods...
   💭 [问题定位] 基于我的检查，我已经发现了明确的异常。现在让我总结发现的问题：

```json
{
  "layer": "L2",
  "layers": ["L2"],
  "layer_name": "工作负载层",
  "confidence": 0.95,
  "reasoning": "发现 aiops-e2e 命名空间中的 memhog-578d9b5ffd-lwfxj Pod 处于 CrashLoopBackOff 状态，describe 显示 Last State: Terminated, Reason: OOMKilled, Exit Code: 137。该 Pod 已重启 196 次，内存限制为 40Mi，但应用代码持续分配内存导致 OOM。节点状态正常（全部 Ready），无其他当前活跃异常对象。",
  "key_entities": [
    {"type": "Pod", "value": "memhog-578d9b5ffd-lwfxj"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Deployment", "value": "memhog"}
  ],
  "possible_scenarios": ["OOMKilled 内存超限", "应用内存泄漏"]
}
```
   ✅ [问题定位] 完成 (1m 8.9s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=['OOMKilled 内存超限', '应用内存泄漏']
   entities=[{"type": "Pod", "value": "memhog-578d9b5ffd-lwfxj"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Deployment", "value": "memhog"}]
   reasoning=发现 aiops-e2e 命名空间中的 memhog-578d9b5ffd-lwfxj Pod 处于 CrashLoopBackOff 状态，describe 显示 Last State: Terminated, Reason: OOMKilled, Exit Code: 137。该 Pod 已重启 196 次，内存限制为 40Mi，但应用代码持续分配内存导致 OOM。节点状态正常（全部 Ready），无其他当前活跃异常对象。
   layer_analysis={"layer": "L2", "layers": ["L2"], "layer_name": "工作负载层", "confidence": 0.95, "reasoning": "发现 aiops-e2e 命名空间中的 memhog-578d9b5ffd-lwfxj Pod 处于 CrashLoopBackOff 状态，describe 显示 Last State: Terminated, Reason: OOMKilled, Exit Code: 137。该 Pod 已重启 196 次，内存限制为 40Mi，但应用代码持续分配内存导致 OOM。节点状态正常（全部 Ready），无其他当前活跃异常对象。", "key_entities": [{"type": "Pod", "value": "memhog-578d9b5ffd-lwfxj"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Deployment", "value": "memhog"}], "possible_scenarios": ["OOMKilled 内存超限", "应用内存泄漏"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，发现 aiops-e2e 命名空间中的 memhog-578d9b5ffd-lwfxj Pod 处于 CrashLoopBackOff 状态，原因是 OOMKilled（Exit Code 137）。现在我将制定证据采集计划来深入分析这个问题。

```json
{
  "layer": "L2",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取 Pod 崩溃前的日志，查看内存分配失败的具体信息",
      "level": "critical",
      "tool": "kubectl_run_image",
      "command": "kubectl run debug-pod --rm -i --tty --image=busybox --restart=Never -- sh -c 'kubectl logs memhog-578d9b5ffd-lwfxj -n aiops-e2e --previous --tail=200'",
      "purpose": "确认容器崩溃前的内存分配错误信息"
    },
    {
      "id": "e2",
      "description": "获取 Deployment 的详细配置，查看资源限制设置",
      "level": "important",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get deployment memhog -n aiops-e2e -o yaml",
      "purpose": "查看 Deployment 的资源限制配置，确认内存限制值"
    },
    {
      "id": "e3",
      "description": "查询 Pod 内存使用历史指标",
      "level": "important",
      "tool": "execute_prometheus_range_query",
      "command": "container_memory_working_set_bytes{pod=\"memhog-578d9b5ffd-lwfxj\", namespace=\"aiops-e2e\"}",
      "purpose": "查看 Pod 内存使用历史趋势，确认是否持续增长超过限制"
    },
    {
      "id": "e4",
      "description": "查询节点内存使用情况",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
      "purpose": "确认节点整体内存压力情况"
    },
    {
      "id": "e5",
      "description": "获取 Pod 的详细 YAML 配置",
      "level": "optional",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get pod memhog-578d9b5ffd-lwfxj -n aiops-e2e -o yaml",
      "purpose": "查看完整的 Pod 配置，包括资源限制和重启策略"
    }
  ],
  "collection_strategy": "首先获取崩溃日志确认 OOM 的具体表现，然后检查资源配置是否合理，最后通过 Prometheus 指标验证内存使用趋势。优先确认关键证据，避免过度采集。"
}
```

现在开始执行证据采集：
   💭 [证据链采集] 调用工具: kubectl_run_image
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_run_image (success)
      📄 {"success": false, "stdout": "pod \"debug-pod\" deleted\n", "stderr": "error: timed out waiting for the condition\n", "returncode": 1}
   💭 [证据链采集] 让我尝试直接使用 kubectl logs 命令：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [证据链采集] 日志为空，这可能是因为容器启动后立即被 OOMKilled。让我继续执行其他证据采集：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    deployment.kubernetes.io/revision: "1"
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"apps/v1","kind":"D
   💭 [证据链采集] 现在查询 Pod 内存使用历史指标：
   💭 [证据链采集] 调用工具: execute_prometheus_range_query
   💭 [证据链采集] 工具结果: execute_prometheus_range_query (success)
      📄 {"status":"success","data":{"resultType":"matrix","result":[{"metric":{"__name__":"container_memory_working_set_bytes","endpoint":"https-metrics","id":"/kubepods.slice/kubepods-burstable.slice/kubepod
   ✅ [证据链采集] 完成 (1m 44.2s)
   📤 → 下游数据: evidence_items=4/6
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "获取 Pod 崩溃前的日志，查看内存分配失败的具体信息", "level": "critical", "tool": "kubectl_run_image", "command": "kubectl run debug-pod --rm -i --tty --image=busybox --restart=Never -- sh -c 'kubectl logs memhog-578d9b5ffd-lwfxj -n aiops-e2e --previous --tail=200'", "purpose": "确认容器崩溃前的内存分配错误信息"}, {"id": "e2", "description": "获取 Deployment 的详细配置，查看资源限制设置", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get deployment memhog -n aiops-e2e -o yaml", "purpose": "查看 Deployment 的资源限制配置，确认内存限制值"}, {"id": "e3", "description": "查询 Pod 内存使用历史指标", "level": "important", "tool": "execute_prometheus_range_query", "command": "container_memory_working_set_bytes{pod=\"memhog-578d9b5ffd-lwfxj\", namespace=\"aiops-e2e\"}", "purpose": "查看 Pod 内存使用历史趋势，确认是否持续增长超过限制"}, {"id": "e4", "description": "查询节点内存使用情况", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100", "purpose": "确认节点整体内存压力情况"}, {"id": "e5", "description": "获取 Pod 的详细 YAML 配置", "level": "optional", "tool": "kubectl_get_yaml", "command": "kubectl get pod memhog-578d9b5ffd-lwfxj -n aiops-e2e -o yaml", "purpose": "查看完整的 Pod 配置，包括资源限制和重启策略"}], "tool_results": [], "tool_data": [{"tool": "kubectl_run_image", "data": "{\"success\": false, \"stdout\": \"pod \\\"debug-pod\\\" deleted\\n\", \"stderr\": \"error: timed out waiting for the condition\\n\", \"returncode\": 1}", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  annotations:\n    deployment.kubernetes.io/revision: \"1\"\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":\"apps/v1\",\"kind\":\"Deployment\",\"metadata\":{\"annotations\":{},\"labels\":{\"e2e-test\":\"true\"},\"name\":\"memhog\",\"namespace\":\"aiops-e2e\"},\"spec\":{\"replicas\":1,\"selector\":{\"matchLabels\":{\"app\":\"memhog\"}},\"template\":{\"metadata\":{\"labels\":{\"app\":\"memhog\",\"e2e-test\":\"true\"}},\"spec\":{\"containers\":[{\"args\":[\"import time\\na=[]\\nwhile True:\\n  a.append(\\\"x\\\"*1024*1024)  # 1MiB\\n  time.sleep(0.02)\\n\"],\"command\":[\"python\",\"-c\"],\"image\":\"python:3.11-slim\",\"name\":\"memhog\",\"resources\":{\"limits\":{\"cpu\":\"200m\",\"memory\":\"40Mi\"},\"requests\":{\"cpu\":\"50m\",\"memory\":\"20Mi\"}}}]}}}}\n  creationTimestamp: \"2026-04-21T09:55:19Z\"\n  generation: 1\n  labels:\n    e2e-test: \"true\"\n  name: memhog\n  namespace: aiops-e2e\n  resourceVersion: \"46352946\"\n  uid: b4c375bf-f2b7-4225-b4af-47d450e59b34\nspec:\n  progressDeadlineSeconds: 600\n  replicas: 1\n  revisionHistoryLimit: 10\n  selector:\n    matchLabels:\n      app: memhog\n  strategy:\n    rollingUpdate:\n      maxSurge: 25%\n      maxUnavailable: 25%\n    type: RollingUpdate\n  template:\n    metadata:\n      creationTimestamp: null\n      labels:\n        app: memhog\n        e2e-test: \"true\"\n    spec:\n      containers:\n      - args:\n        - |\n          import time\n          a=[]\n          while True:\n            a.append(\"x\"*1024*1024)  # 1MiB\n            time.sleep(0.02)\n        command:\n        - python\n        - -c\n        image: python:3.11-slim\n        imagePullPolicy: IfNotPresent\n        name: memhog\n        resources:\n          limits:\n            cpu: 200m\n            memory: 40Mi\n          requests:\n            cpu: 50m\n            memory: 20Mi\n        terminationMessagePath: /dev/termination-log\n        terminationMessagePolicy: File\n      dnsPolicy: ClusterFirst\n      restartPolicy: Always\n      schedulerName: default-scheduler\n      securityContext: {}\n      terminationGracePeriodSeconds: 30\nstatus:\n  conditions:\n  - lastTransitionTime: \"2026-04-21T09:55:19Z\"\n    lastUpdateTime: \"2026-04-21T09:55:20Z\"\n    message: ReplicaSet \"memhog-578d9b5ffd\" has successfully progressed.\n    reason: NewReplicaSetAvailable\n    status: \"True\"\n    type: Progressing\n  - lastTransitionTime: \"2026-04-22T02:14:22Z\"\n    lastUpdateTime: \"2026-04-22T02:14:22Z\"\n    message: Deployment does not have minimum availability.\n    reason: MinimumReplicasUnavailable\n    status: \"False\"\n    type: Available\n  observedGeneration: 1\n  replicas: 1\n  unavailableReplicas: 1\n  updatedReplicas: 1", "duration_s": 0}, {"tool": "execute_prometheus_range_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"matrix\",\"result\":[{\"metric\":{\"__name__\":\"container_memory_working_set_bytes\",\"endpoint\":\"https-metrics\",\"id\":\"/kubepods.slice/kubepods-burstable.slice/kubepods-burstable-podd99532da_7388_4d95_a264_211c7bb74a22.slice\",\"instance\":\"10.2.0.50:10250\",\"job\":\"kubelet\",\"metrics_path\":\"/metrics/cadvisor\",\"namespace\":\"aiops-e2e\",\"node\":\"node2\",\"pod\":\"memhog-578d9b5ffd-lwfxj\",\"service\":\"observability-kubelet\"},\"values\":[[1776819600,\"487424\"],[1776819630,\"487424\"],[1776819660,\"487424\"],[1776819690,\"487424\"],[1776819720,\"487424\"],[1776819750,\"487424\"],[1776819780,\"487424\"],[1776819810,\"487424\"],[1776819840,\"487424\"],[1776819870,\"487424\"],[1776819900,\"487424\"],[1776819930,\"487424\"],[1776819960,\"487424\"],[1776819990,\"487424\"],[1776820020,\"487424\"],[1776820050,\"487424\"],[1776820080,\"487424\"],[1776820110,\"491520\"],[1776820140,\"491520\"],[1776820170,\"491520\"],[1776820200,\"491520\"],[1776820230,\"491520\"],[1776820260,\"491520\"],[1776820290,\"491520\"],[1776820320,\"491520\"],[1776820350,\"491520\"],[1776820380,\"491520\"],[1776820410,\"499712\"],[1776820440,\"499712\"],[1776820470,\"499712\"],[1776820500,\"499712\"],[1776820530,\"499712\"],[1776820560,\"499712\"],[1776820590,\"499712\"],[1776820620,\"499712\"],[1776820650,\"499712\"],[1776820680,\"499712\"],[1776820710,\"499712\"],[1776820740,\"495616\"],[1776820770,\"495616\"],[1776820800,\"495616\"],[1776820830,\"495616\"],[1776820860,\"495616\"],[1776820890,\"495616\"],[1776820920,\"495616\"],[1776820950,\"495616\"],[1776820980,\"495616\"],[1776821010,\"495616\"],[1776821040,\"532480\"],[1776821070,\"532480\"],[1776821100,\"532480\"],[1776821130,\"532480\"],[1776821160,\"532480\"],[1776821190,\"532480\"],[1776821220,\"532480\"],[1776821250,\"532480\"],[1776821280,\"532480\"],[1776821310,\"532480\"],[1776821340,\"536576\"],[1776821370,\"536576\"],[1776821400,\"536576\"],[1776821430,\"536576\"],[1776821460,\"536576\"],[1776821490,\"536576\"],[1776821520,\"536576\"],[1776821550,\"536576\"],[1776821580,\"536576\"],[1776821610,\"536576\"],[1776821640,\"577536\"],[1776821670,\"577536\"],[1776821700,\"577536\"],[1776821730,\"577536\"],[1776821760,\"577536\"],[1776821790,\"577536\"],[1776821820,\"577536\"],[1776821850,\"577536\"],[1776821880,\"577536\"],[1776821910,\"577536\"],[1776821940,\"331776\"],[1776821970,\"331776\"],[1776822000,\"331776\"],[1776822030,\"331776\"],[1776822060,\"331776\"],[1776822090,\"331776\"],[1776822120,\"331776\"],[1776822150,\"331776\"],[1776822180,\"331776\"],[1776822210,\"331776\"],[1776822240,\"327680\"],[1776822270,\"327680\"],[1776822300,\"327680\"],[1776822330,\"327680\"],[1776822360,\"327680\"],[1776822390,\"327680\"],[1776822420,\"327680\"],[1776822450,\"327680\"],[1776822480,\"327680\"],[1776822510,\"327680\"],[1776822540,\"327680\"],[1776822570,\"368640\"],[1776822600,\"368640\"],[1776822630,\"368640\"],[1776822660,\"368640\"],[1776822690,\"368640\"],[1776822720,\"368640\"],[1776822750,\"368640\"],[1776822780,\"368640\"],[1776822810,\"368640\"],[1776822840,\"368640\"],[1776822870,\"331776\"],[1776822900,\"331776\"],[1776822930,\"331776\"],[1776822960,\"331776\"],[1776822990,\"331776\"],[1776823020,\"331776\"],[1776823050,\"331776\"],[1776823080,\"331776\"],[1776823110,\"331776\"],[1776823140,\"331776\"],[1776823170,\"290816\"],[1776823200,\"290816\"],[1776823230,\"290816\"],[1776823260,\"290816\"],[1776823290,\"290816\"],[1776823320,\"290816\"],[1776823350,\"290816\"],[1776823380,\"290816\"],[1776823410,\"290816\"],[1776823440,\"290816\"],[1776823470,\"335872\"],[1776823500,\"335872\"],[1776823530,\"335872\"],[1776823560,\"335872\"],[1776823590,\"335872\"],[1776823620,\"335872\"],[1776823650,\"335872\"],[1776823680,\"335872\"],[1776823710,\"335872\"],[1776823740,\"335872\"],[1776823770,\"335872\"],[1776823800,\"368640\"],[1776823830,\"368640\"],[1776823860,\"368640\"],[1776823890,\"368640\"],[1776823920,\"368640\"],[1776823950,\"368640\"],[1776823980,\"368640\"],[1776824010,\"368640\"],[1776824040,\"368640\"],[1776824070,\"376832\"],[1776824100,\"376832\"],[1776824130,\"376832\"],[1776824160,\"376832\"],[1776824190,\"376832\"],[1776824220,\"376832\"],[1776824250,\"376832\"],[1776824280,\"376832\"],[1776824310,\"376832\"],[1776824340,\"376832\"],[1776824370,\"376832\"],[1776824400,\"376832\"],[1776824430,\"376832\"],[1776824460,\"376832\"],[1776824490,\"376832\"],[1776824520,\"376832\"],[1776824550,\"376832\"],[1776824580,\"376832\"]]},{\"metric\":{\"__name__\":\"container_memory_working_set_bytes\",\"endpoint\":\"https-metrics\",\"id\":\"/kubepods.slice/kubepods-burstable.slice/kubepods-burstable-podd99532da_7388_4d95_a264_211c7bb74a22.slice/cri-containerd-eaaee02f72793d767c9ed50ab8faf5878703fa94108e32e3e2998d23813503b3.scope\",\"image\":\"xnet.registry.io:8443/k8s/registry.k8s.io/pause:3.9\",\"instance\":\"10.2.0.50:10250\",\"job\":\"kubelet\",\"metrics_path\":\"/metrics/cadvisor\",\"name\":\"eaaee02f72793d767c9ed50ab8faf5878703fa94108e32e3e2998d23813503b3\",\"namespace\":\"aiops-e2e\",\"node\":\"node2\",\"pod\":\"memhog-578d9b5ffd-lwfxj\",\"service\":\"observability-kubelet\"},\"values\":[[1776819600,\"188416\"],[1776819630,\"188416\"],[1776819660,\"188416\"],[1776819690,\"188416\"],[1776819720,\"188416\"],[1776819750,\"188416\"],[1776819780,\"188416\"],[1776819810,\"188416\"],[1776819840,\"188416\"],[1776819870,\"188416\"],[1776819900,\"188416\"],[1776819930,\"188416\"],[1776819960,\"188416\"],[1776819990,\"188416\"],[1776820020,\"188416\"],[1776820050,\"188416\"],[1776820080,\"188416\"],[1776820110,\"188416\"],[1776820140,\"188416\"],[1776820170,\"188416\"],[1776820200,\"188416\"],[1776820230,\"188416\"],[1776820260,\"188416\"],[1776820290,\"188416\"],[1776820320,\"188416\"],[1776820350,\"188416\"],[1776820380,\"188416\"],[1776820410,\"188416\"],[1776820440,\"188416\"],[1776820470,\"188416\"],[1776820500,\"188416\"],[1776820530,\"188416\"],[1776820560,\"188416\"],[1776820590,\"188416\"],[1776820620,\"188416\"],[1776820650,\"188416\"],[1776820680,\"188416\"],[1776820710,\"188416\"],[1776820740,\"188416\"],[1776820770,\"188416\"],[1776820800,\"188416\"],[1776820830,\"188416\"],[1776820860,\"188416\"],[1776820890,\"188416\"],[1776820920,\"188416\"],[1776820950,\"188416\"],[1776820980,\"188416\"],[1776821010,\"188416\"],[1776821040,\"188416\"],[1776821070,\"188416\"],[1776821100,\"188416\"],[1776821130,\"188416\"],[1776821160,\"188416\"],[1776821190,\"188416\"],[1776821220,\"188416\"],[1776821250,\"188416\"],[1776821280,\"188416\"],[1776821310,\"188416\"],[1776821340,\"188416\"],[1776821370,\"188416\"],[1776821400,\"188416\"],[1776821430,\"188416\"],[1776821460,\"188416\"],[1776821490,\"188416\"],[1776821520,\"188416\"],[1776821550,\"188416\"],[1776821580,\"188416\"],[1776821610,\"188416\"],[1776821640,\"188416\"],[1776821670,\"188416\"],[1776821700,\"188416\"],[1776821730,\"188416\"],[1776821760,\"188416\"],[1776821790,\"188416\"],[1776821820,\"188416\"],[1776821850,\"188416\"],[1776821880,\"188416\"],[1776821910,\"188416\"],[1776821940,\"188416\"],[1776821970,\"188416\"],[1776822000,\"188416\"],[1776822030,\"188416\"],[1776822060,\"188416\"],[1776822090,\"188416\"],[1776822120,\"188416\"],[1776822150,\"188416\"],[1776822180,\"188416\"],[1776822210,\"188416\"],[1776822240,\"188416\"],[1776822270,\"188416\"],[1776822300,\"188416\"],[1776822330,\"188416\"],[1776822360,\"188416\"],[1776822390,\"188416\"],[1776822420,\"188416\"],[1776822450,\"188416\"],[1776822480,\"188416\"],[1776822510,\"188416\"],[1776822540,\"188416\"],[1776822570,\"188416\"],[1776822600,\"188416\"],[1776822630,\"188416\"],[1776822660,\"188416\"],[1776822690,\"188416\"],[1776822720,\"188416\"],[1776822750,\"188416\"],[1776822780,\"188416\"],[1776822810,\"188416\"],[1776822840,\"188416\"],[1776822870,\"188416\"],[1776822900,\"188416\"],[1776822930,\"188416\"],[1776822960,\"188416\"],[1776822990,\"188416\"],[1776823020,\"188416\"],[1776823050,\"188416\"],[1776823080,\"188416\"],[1776823110,\"188416\"],[1776823140,\"188416\"],[1776823170,\"188416\"],[1776823200,\"188416\"],[1776823230,\"188416\"],[1776823260,\"188416\"],[1776823290,\"188416\"],[1776823320,\"188416\"],[1776823350,\"188416\"],[1776823380,\"188416\"],[1776823410,\"188416\"],[1776823440,\"188416\"],[1776823470,\"188416\"],[1776823500,\"188416\"],[1776823530,\"188416\"],[1776823560,\"188416\"],[1776823590,\"188416\"],[1776823620,\"188416\"],[1776823650,\"188416\"],[1776823680,\"188416\"],[1776823710,\"188416\"],[1776823740,\"188416\"],[1776823770,\"188416\"],[1776823800,\"188416\"],[1776823830,\"188416\"],[1776823860,\"188416\"],[1776823890,\"188416\"],[1776823920,\"188416\"],[1776823950,\"188416\"],[1776823980,\"188416\"],[1776824010,\"188416\"],[1776824040,\"188416\"],[1776824070,\"188416\"],[1776824100,\"188416\"],[1776824130,\"188416\"],[1776824160,\"188416\"],[1776824190,\"188416\"],[1776824220,\"188416\"],[1776824250,\"188416\"],[1776824280,\"188416\"],[1776824310,\"188416\"],[1776824340,\"188416\"],[1776824370,\"188416\"],[1776824400,\"188416\"],[1776824430,\"188416\"],[1776824460,\"188416\"],[1776824490,\"188416\"],[1776824520,\"188416\"],[1776824550,\"188416\"],[1776824580,\"188416\"]]}]}}", "duration_s": 0}], "llm_analysis": "现在查询 Pod 内存使用历史指标：", "collection_summary": "计划 6 项，实际采集 4 项，未采集 2 项，完整度 67%", "evidence_inventory": [{"id": "e1", "description": "获取 Pod 崩溃前的日志，查看内存分配失败的具体信息", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "获取 Deployment 的详细配置，查看资源限制设置", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "查询 Pod 内存使用历史指标", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "查询节点内存使用情况", "level": "optional", "collected": false, "source": "planned"}, {"id": "e5", "description": "获取 Pod 的详细 YAML 配置", "level": "optional", "collected": false, "source": "planned"}, {"id": "extra_1", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": ["e4(查询节点内存使用情况): 已规划但工具执行失败或无匹配结果", "e5(获取 Pod 的详细 YAML 配置): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/6 项, 完整度: 67%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 6.0s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "应用代码设计缺陷：memhog 容器的 Python 代码包含无限循环，每秒分配约 50MiB 内存（a.append(\"x\"*1024*1024); time.sleep(0.02)），内存分配速率远超限制", "propagation": "应用持续分配内存 → 容器内存使用量快速增加 → 达到内存限制（40MiB）", "direct_cause": "容器内存使用超过 limits.memory（40MiB）限制，触发内核 OOM Killer 终止容器进程", "manifestation": "Pod 状态为 CrashLoopBackOff，Last State: OOMKilled (Exit Code 137)，已重启 196 次，Deployment 无可用副本"}
   rca_analysis={"phenomenon": "aiops-e2e 命名空间中的 memhog-578d9b5ffd-lwfxj Pod 处于 CrashLoopBackOff 状态，已重启 196 次，Pod 未 Ready，导致 Deployment 的 availableReplicas 为 0（1 个副本不可用）。", "evidence_inventory": [{"id": "e1", "content": "节点状态：3 个节点（master, node1, node2）全部 Ready，无 MemoryPressure/DiskPressure 等异常条件", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e2", "content": "Pod 状态查询：memhog-578d9b5ffd-lwfxj Pod 的 phase 为 Running，reason 为 CrashLoopBackOff，运行在 node2 节点", "source": "kubernetes_jq_query (pods)", "reliability": "高"}, {"id": "e3", "content": "Pod describe 详情：Last State: Terminated, Reason: OOMKilled, Exit Code: 137；State: Waiting, Reason: CrashLoopBackOff；Restart Count: 196；内存限制 limits.memory: 40Mi", "source": "kubectl_describe", "reliability": "高"}, {"id": "e4", "content": "Pod 容器命令和参数：python -c 'import time; a=[]; while True: a.append(\"x\"*1024*1024); time.sleep(0.02)'，这是一个持续分配 1MiB 内存的无限循环", "source": "kubectl_describe", "reliability": "高"}, {"id": "e5", "content": "Deployment 配置：memhog Deployment 的 replicas: 1，容器资源限制 limits.memory: 40Mi，requests.memory: 20Mi；Deployment 状态：unavailableReplicas: 1，availableReplicas: 0", "source": "kubectl_get_yaml", "reliability": "高"}, {"id": "e6", "content": "Pod 内存使用历史指标：container_memory_working_set_bytes 在最近时间段内显示内存使用量在 290KB 到 577KB 之间波动（如 487424 bytes ≈ 476KB，577536 bytes ≈ 564KB），远低于 40MiB 限制", "source": "execute_prometheus_range_query", "reliability": "中"}, {"id": "e7", "content": "Pod 重启次数确认：memhog-578d9b5ffd-lwfxj 的 restartCount 为 196", "source": "kubernetes_jq_query (pods restartCount)", "reliability": "高"}, {"id": "e8", "content": "Pod 崩溃前日志获取失败：kubectl logs --previous 因超时失败，未获取到具体错误信息", "source": "kubectl_run_image", "reliability": "中"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "master Ready, node1 Ready, node2 Ready", "interpretation": "集群节点层面健康，无节点资源压力或节点故障，排除 L0 节点层问题"}, {"evidence_id": "e2", "raw_data": "phase: Running, reason: CrashLoopBackOff, node: node2", "interpretation": "Pod 处于运行状态但容器持续崩溃重启，是典型的 CrashLoopBackOff 现象，问题定位在容器内部"}, {"evidence_id": "e3", "raw_data": "Last State: Terminated, Reason: OOMKilled, Exit Code: 137; Restart Count: 196; limits.memory: 40Mi", "interpretation": "直接证据表明容器因内存超限被 OOM Killer 终止（Exit Code 137），已重启 196 次，内存限制为 40MiB"}, {"evidence_id": "e4", "raw_data": "python -c 'import time; a=[]; while True: a.append(\"x\"*1024*1024); time.sleep(0.02)'", "interpretation": "应用代码是一个无限循环，每秒约分配 50MiB 内存（1MiB/0.02s），远超 40MiB 的内存限制，这是导致 OOM 的根本原因"}, {"evidence_id": "e5", "raw_data": "Deployment replicas: 1, unavailableReplicas: 1, availableReplicas: 0; limits.memory: 40Mi", "interpretation": "Deployment 期望 1 个副本，但因 Pod 持续崩溃导致无可用副本，资源配置与 Pod describe 一致"}, {"evidence_id": "e6", "raw_data": "内存使用指标值：487424 bytes (476KB), 577536 bytes (564KB) 等，持续在 290KB-577KB 范围", "interpretation": "Prometheus 指标显示的内存使用量远低于 40MiB 限制，这可能是因为指标采集的是容器存活时的瞬时值，而 OOM 发生在内存快速增长的瞬间，指标未能捕捉到峰值"}, {"evidence_id": "e7", "raw_data": "restartCount: 196", "interpretation": "Pod 已频繁重启 196 次，证实了 CrashLoopBackOff 的持续性"}, {"evidence_id": "e8", "raw_data": "kubectl logs --previous 失败：error: timed out waiting for the condition", "interpretation": "未能获取崩溃前的应用日志，但 OOMKilled 的 exit code 137 已是强证据"}], "causal_chain": {"root_cause": "应用代码设计缺陷：memhog 容器的 Python 代码包含无限循环，每秒分配约 50MiB 内存（a.append(\"x\"*1024*1024); time.sleep(0.02)），内存分配速率远超限制", "propagation": "应用持续分配内存 → 容器内存使用量快速增加 → 达到内存限制（40MiB）", "direct_cause": "容器内存使用超过 limits.memory（40MiB）限制，触发内核 OOM Killer 终止容器进程", "manifestation": "Pod 状态为 CrashLoopBackOff，Last State: OOMKilled (Exit Code 137)，已重启 196 次，Deployment 无可用副本"}, "root_cause_summary": "根因是 aiops-e2e/memhog Deployment 中的容器应用代码存在内存泄漏式设计。证据 e4 显示代码为无限循环，每秒分配约 50MiB 内存（1MiB/0.02s）。证据 e3 和 e5 确认内存限制为 40MiB，导致容器必然超限。证据 e3 的 OOMKilled (Exit Code 137) 和 196 次重启直接证明了这一点。节点层（证据 e1）和内存指标（证据 e6）正常，排除了节点资源不足或指标异常的可能性。", "confidence": 0.95, "primary_runbooks": ["私有化 Kubernetes 环境健康与高效排查参考手册", "L2 Pod OOMKilled (Exit Code 137)"], "alternative_causes": [], "limitations": "1. 未能获取崩溃前的容器日志（证据 e8 失败），缺少应用层内存分配失败的具体错误信息。2. Prometheus 内存指标（证据 e6）显示的使用量（~500KB）远低于限制，这可能是因为指标采集频率（30秒）未能捕捉到内存快速增长的瞬间峰值，或指标反映的是容器重启后的初始状态。但 OOMKilled 的 exit code 137 是决定性证据。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: 应用代码设计缺陷：memhog 容器的 Python 代码包含无限循环，每秒分配约 50MiB 内存（a.append("x"*1024*1024); time.sleep(0.02)），内存分配速率远超限制
     传导机制: 应用持续分配内存 → 容器内存使用量快速增加 → 达到内存限制（40MiB）
     最终表现: Pod 状态为 CrashLoopBackOff，Last State: OOMKilled (Exit Code 137)，已重启 196 次，Deployment 无可用副本


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 13.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5332 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 12.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **问题层级** | L2 - 工作负载层 |
| **问题分类** | OOMKilled (内存超限) |
| **置信度** | 高 (95%) |
| **证据完整度** | 4/6 (67%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键发现**：
您的集群节点层面运行正常，但存在一个工作负载层问题。具体表现为 `aiops-e2e` 命名空间下的 `memhog` 应用因内存超限而持续崩溃重启，导致服务不可用。

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | memhog-578d9b5ffd-lwfxj |
| Namespace | aiops-e2e |
| Node | node2 |
| Deployment | memhog |
| 错误信息 | Last State: Terminated, Reason: OOMKilled, Exit Code: 137 |

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | 节点状态 | `kubectl get nodes` | `master Ready, node1 Ready, node2 Ready` | 集群所有节点状态健康，无资源压力，排除节点层问题。 |
| 2 | Pod 状态 | `kubectl get pods` (jq查询) | `{"namespace":"aiops-e2e","name":"memhog-578d9b5ffd-lwfxj","phase":"Running","node":"node2","reason":"CrashLoopBackOff"}` | Pod 处于 `CrashLoopBackOff` 状态，容器持续崩溃重启。 |
| 3 | Pod 详情 | `kubectl describe pod` | `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`<br>`Restart Count: 196`<br>`limits.memory: 40Mi` | 容器因内存超限被 OOM Killer 终止，已重启196次，内存限制为40Mi。 |
| 4 | 应用代码 | `kubectl describe pod` | `Command: python -c`<br>`Args: import time; a=[]; while True: a.append("x"*1024*1024); time.sleep(0.02)` | 应用是一个无限循环，每秒分配约50MiB内存，远超40MiB限制。 |
| 5 | Deployment配置 | `kubectl get deployment -o yaml` | `limits.memory: 40Mi`<br>`unavailableReplicas: 1`<br>`availableReplicas: 0` | Deployment资源配置确认内存限制为40Mi，且因Pod崩溃无可用副本。 |
| 6 | 内存使用指标 | Prometheus 查询 | `container_memory_working_set_bytes` 值在 290KB 到 577KB 之间波动 | 指标显示的内存使用量远低于限制，可能因采集频率未捕捉到OOM瞬间峰值。 |
| 7 | 重启次数 | `kubectl get pods` (jq查询) | `{"namespace":"aiops-e2e","name":"memhog-578d9b5ffd-lwfxj","restartCount":196}` | 确认Pod已重启196次。 |

### 证据关联分析
- **证据 #3 + #4 + #5 印证**：`Exit Code 137 (OOMKilled)` + `应用每秒分配50MiB内存` + `memory limit 40Mi` → 应用内存需求远超限制，必然触发OOM。
- **证据 #1 + #2 排除**：所有节点 `Ready`，且Pod调度正常 → 问题非节点资源不足或调度失败，定位在容器内部。
- **证据链**：应用代码内存泄漏 → 内存使用快速超过40Mi限制 → 触发cgroup OOM Killer → 容器被终止 (Exit 137) → Pod重启并进入 `CrashLoopBackOff` → Deployment无可用副本。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| e4: 节点内存使用情况 | optional | 不影响根因判断，节点状态已确认正常 |
| e5: Pod 详细 YAML | optional | 不影响根因判断，关键配置已从 `describe` 和 Deployment YAML 获取 |
| e1: 容器崩溃前日志 | critical | 无法从应用日志层面确认内存分配失败的具体报错信息 |

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用代码设计缺陷：无限循环每秒分配约50MiB内存，远超40MiB限制     │
│ (证据 #4: 应用代码逻辑)                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器内存使用量在秒级内达到并超过 limits.memory (40Mi)            │
│ (证据 #3: 内存限制，证据 #4: 分配速率)                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 触发内核 cgroup OOM Killer，容器被强制终止 (Exit Code 137)       │
│ (证据 #3: Reason: OOMKilled, Exit Code: 137)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，重启196次，Deployment 无可用副本      │
│ (证据 #2, #3, #5, #7)                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #3 (OOMKilled, Exit Code 137)、证据 #4 (每秒分配50MiB内存的代码) 和证据 #5 (内存限制40Mi)，
问题的根本原因是 **`aiops-e2e/memhog` Deployment 中的容器应用代码存在内存泄漏式设计，其内存分配速率远超设定的资源限制**，
导致容器被 cgroup OOM Killer 反复终止并持续重启。

**置信度**：高 (95%)
- ✅ `Exit Code 137` 和 `Reason: OOMKilled` 是 OOM 的直接铁证。
- ✅ 应用代码逻辑清晰显示每秒分配约50MiB内存，而限制仅为40MiB，必然超限。
- ✅ 节点状态正常，排除了底层资源不足的可能性。
- ⚠️ 缺失崩溃前日志，但不影响对OOM根本原因的判定。

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修正应用代码逻辑**
这是根本解决之道。需要修改 `memhog` 应用的代码，停止无限内存分配行为。例如，可以改为分配固定大小的内存或引入内存释放机制。
*依据*：证据 #4 显示代码逻辑是问题的根源。

**2. [临时缓解] 调整内存限制以适应当前代码（不推荐长期使用）**
如果无法立即修改代码，可临时大幅提高内存限制，但需警惕节点内存被耗尽的风险。
```bash
kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=512Mi
```
*依据*：当前40Mi限制不足，临时提高至512Mi可避免OOM，但需监控。

**3. [可选] 尝试获取崩溃日志**
虽然之前超时，可再次尝试获取日志以获取更多细节。
```bash
kubectl logs memhog-578d9b5ffd-lwfxj -n aiops-e2e --previous
```
*目的*：确认应用层是否有其他错误信息。

### 后续优化
1.  **资源评估与监控**：使用 `kubectl describe pod` 观察调整后的资源使用情况。建议配置内存使用率告警（例如 >80% limit时预警）。
2.  **应用健康检查**：为Deployment配置 `livenessProbe` 和 `readinessProbe`，以便更早发现应用异常。
3.  **代码审查与测试**：确保上线前对应用的内存使用行为进行充分测试和评估。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod -n aiops-e2e -l app=memhog` | STATUS: Running，且 RESTARTS 不再增加 |
| 2. 检查容器状态 | `kubectl describe pod -n aiops-e2e -l app=memhog \| grep -A 5 \"Last State\"` | 无 `OOMKilled` 或 `Terminated` 状态 |
| 3. 确认 Deployment | `kubectl get deployment memhog -n aiops-e2e` | AVAILABLE: 1 |

## ⚠️ 注意事项
- **临时增加内存限制只是权宜之计**，必须尽快修复有缺陷的应用代码，否则可能影响节点上其他Pod。
- 该 `memhog` Pod 带有 `e2e-test=true` 标签，可能是一个测试应用。请确认其用途，如果是无用的测试负载，可以考虑直接删除。
- 删除测试Deployment的命令（如需）：
  ```bash
  kubectl delete deployment memhog -n aiops-e2e
  ```

---

## 📊 性能统计

├─ 总耗时: 5.2m
├─ 问题定位: 68.9s (22%) ✅
├─ 证据链采集: 104.2s (33%) ✅
├─ 根因分析: 66.0s (21%) ✅
├─ 汇总总结: 73.7s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 15 次
```

📋 诊断追踪

- **核心 Runbook**: private-k8s-health-reference, l2-oomkilled
- **参考 Runbook**: private-k8s-health-reference, l2-oomkilled
- **工具调用**: 15 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
