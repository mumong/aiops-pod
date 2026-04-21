======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d8a0e741bac54978]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来检查一下集群的整体状态，看看是否存在什么问题。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     apphealth-
   💭 [问题定位] 现在让我检查一下是否有异常状态的Pod。从输出中我看到所有Pod都是Running状态，但让我检查一下是否有节点状态异常：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   207d   v1.26.8  
   💭 [问题定位] 所有节点都是Ready状态。让我检查一下是否有其他异常资源，比如查看事件：
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 Command failed (exit 1):
kubectl get events --all-namespaces -o custom-columns='NAMESPACE,LAST SEEN,TYPE,REASON,OBJECT,MESSAGE' | (head -n 1; tail -n +2 | grep -E 'Warning\|Error\|Failed\|BackOff\|Evi
   💭 [问题定位] 让我用正确的方式检查事件：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE   LAST SEEN   TYPE      REASON              OBJECT                                     SUBOBJECT                                      SOURCE                                        MESSAGE   
   💭 [问题定位] 我看到有一些事件，但主要是正常的调度和创建事件。让我检查一下是否有更近期的警告事件：
   💭 [问题定位] 调用工具: run_bash_command
   💭 [问题定位] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAMESPACE   LAST SEEN   TYPE      REASON         OBJECT                                MESSAGE\naiops       36m         Warning   FailedCreate   replicaset/aiops-copilot-5
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 7.7s)
   📤 → 下游数据: layer=Layer.QUERY, layers=QUERY
   scenarios=[]
   entities=[]
   reasoning=用户意图是检查集群事件，特别是警告事件，属于数据查询而非故障诊断。虽然发现一个历史警告事件（FailedCreate replicaset），但用户当前主要任务是查询和检查事件状态，所有Pod当前状态为Running，所有节点状态为Ready。
   layer_analysis={"layer": "QUERY", "layers": [], "layer_name": "查询模式", "confidence": 0.9, "reasoning": "用户意图是检查集群事件，特别是警告事件，属于数据查询而非故障诊断。虽然发现一个历史警告事件（FailedCreate replicaset），但用户当前主要任务是查询和检查事件状态，所有Pod当前状态为Running，所有节点状态为Ready。", "key_entities": [], "possible_scenarios": []}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.QUERY
   置信度: 90%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据上游定位结果，我发现集群整体状态健康，但有一个历史异常需要深入调查。让我制定证据采集计划来全面了解集群状态。

```json
{
  "layer": "QUERY",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "检查异常ReplicaSet的详细状态和关联Pod",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe replicaset aiops-copilot-54dd898d8b -n aiops",
      "purpose": "确认ReplicaSet状态、事件和关联的Pod创建失败详情"
    },
    {
      "id": "e2",
      "description": "检查当前aiops-copilot相关Pod状态",
      "level": "critical",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get pods -n aiops | grep aiops-copilot",
      "purpose": "确认当前aiops-copilot工作负载的实际运行状态"
    },
    {
      "id": "e3",
      "description": "检查缺失的服务账户是否存在",
      "level": "critical",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get serviceaccounts -n aiops | grep aiops-copilot",
      "purpose": "确认服务账户aiops-copilot当前是否存在"
    },
    {
      "id": "e4",
      "description": "检查aiops命名空间所有资源状态",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get all -n aiops",
      "purpose": "全面了解aiops命名空间资源状态，确认是否有其他异常"
    },
    {
      "id": "e5",
      "description": "检查集群所有命名空间的资源使用情况",
      "level": "important",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance)) * 100",
      "purpose": "检查各节点CPU使用率，确认资源压力"
    },
    {
      "id": "e6",
      "description": "检查集群内存使用情况",
      "level": "important",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
      "purpose": "检查各节点内存使用率，确认是否有内存压力"
    }
  ],
  "collection_strategy": "先聚焦于历史异常（服务账户缺失导致Pod创建失败），确认当前状态是否已恢复；然后检查集群整体资源使用情况，确保没有潜在问题"
}
```

现在开始逐项执行工具采集证据：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Command failed (exit 1):
kubectl describe replicaset aiops-copilot-54dd898d8b -n aiops
Error from server (NotFound): replicasets.apps "aiops-copilot-54dd898d8b" not found

   💭 [证据链采集] ReplicaSet不存在，让我检查当前相关的Pod：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                             READY   STATUS    RESTARTS   AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
aiops-copilot-6455dff479-bw4q8   1/1     Running   0          31m 
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME            SECRETS   AGE   LABELS
aiops-copilot   0         31m   app=aiops-copilot
default         0         90d   <none>
   💭 [证据链采集] 很好！服务账户现在存在了。让我检查aiops命名空间的所有资源：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                                 READY   STATUS    RESTARTS   AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
pod/aiops-copilot-6455dff479-bw4q8   1/1     Running   0      
   💭 [证据链采集] 现在检查集群资源使用情况：
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"instance":"10.2.0.49:9100"},"value":[1776682074.062,"9.762152777777578"]},{"metric":{"instance":"10.2.0.48:9100"},"value":[17766
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"container":"node-exporter","endpoint":"http-metrics","instance":"10.2.0.49:9100","job":"node-exporter","namespace":"xnet","pod":
   ✅ [证据链采集] 完成 (54.5s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "检查异常ReplicaSet的详细状态和关联Pod", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe replicaset aiops-copilot-54dd898d8b -n aiops", "purpose": "确认ReplicaSet状态、事件和关联的Pod创建失败详情"}, {"id": "e2", "description": "检查当前aiops-copilot相关Pod状态", "level": "critical", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get pods -n aiops | grep aiops-copilot", "purpose": "确认当前aiops-copilot工作负载的实际运行状态"}, {"id": "e3", "description": "检查缺失的服务账户是否存在", "level": "critical", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get serviceaccounts -n aiops | grep aiops-copilot", "purpose": "确认服务账户aiops-copilot当前是否存在"}, {"id": "e4", "description": "检查aiops命名空间所有资源状态", "level": "important", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get all -n aiops", "purpose": "全面了解aiops命名空间资源状态，确认是否有其他异常"}, {"id": "e5", "description": "检查集群所有命名空间的资源使用情况", "level": "important", "tool": "execute_prometheus_instant_query", "command": "(1 - avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance)) * 100", "purpose": "检查各节点CPU使用率，确认资源压力"}, {"id": "e6", "description": "检查集群内存使用情况", "level": "important", "tool": "execute_prometheus_instant_query", "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100", "purpose": "检查各节点内存使用率，确认是否有内存压力"}], "tool_results": [], "tool_data": [{"tool": "kubectl_describe", "data": "Command failed (exit 1):\nkubectl describe replicaset aiops-copilot-54dd898d8b -n aiops\nError from server (NotFound): replicasets.apps \"aiops-copilot-54dd898d8b\" not found\n", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME                             READY   STATUS    RESTARTS   AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS\naiops-copilot-6455dff479-bw4q8   1/1     Running   0          31m ", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME            SECRETS   AGE   LABELS\naiops-copilot   0         31m   app=aiops-copilot\ndefault         0         90d   <none>", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME                                 READY   STATUS    RESTARTS   AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS\npod/aiops-copilot-6455dff479-bw4q8   1/1     Running   0      ", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"instance\":\"10.2.0.49:9100\"},\"value\":[1776682074.062,\"9.762152777777578\"]},{\"metric\":{\"instance\":\"10.2.0.48:9100\"},\"value\":[17766", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"container\":\"node-exporter\",\"endpoint\":\"http-metrics\",\"instance\":\"10.2.0.49:9100\",\"job\":\"node-exporter\",\"namespace\":\"xnet\",\"pod\":", "duration_s": 0}], "llm_analysis": "现在检查集群资源使用情况：", "collection_summary": "计划 6 项，实际采集 6 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "e1", "description": "检查异常ReplicaSet的详细状态和关联Pod", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "检查当前aiops-copilot相关Pod状态", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "检查缺失的服务账户是否存在", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查aiops命名空间所有资源状态", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "检查集群所有命名空间的资源使用情况", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "检查集群内存使用情况", "level": "important", "collected": true, "source": "thinking_match"}], "missing_reasons": [], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/6 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 15.3s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "在部署或更新 `aiops-copilot` 应用时，其Kubernetes清单文件（如Deployment YAML）中指定的服务账户 `aiops-copilot` 在 `aiops` 命名空间中不存在。", "propagation": "1. 用户或CI/CD系统尝试创建或更新 `aiops-copilot` 的Deployment。\n2. Deployment控制器创建了ReplicaSet `aiops-copilot-54dd898d8b`。\n3. 该ReplicaSet尝试创建Pod时，Kubernetes API Server进行权限校验，发现Pod规约中引用的服务账户 `aiops/aiops-copilot` 不存在。\n4. API Server拒绝创建Pod，并生成 `FailedCreate` 警告事件。", "direct_cause": "Pod创建请求因 `is forbidden: serviceaccount \"aiops-copilot\" not found` 错误被API Server拒绝。", "manifestation": "Kubernetes事件系统中记录了一条Warning类型事件，报告 `replicaset/aiops-copilot-54dd898d8b` 的 `FailedCreate` 错误。"}
   rca_analysis={"phenomenon": "集群整体运行正常，但存在一个已恢复的历史异常：36分钟前 aiops 命名空间下的 aiops-copilot 工作负载因服务账户缺失导致 Pod 创建失败。", "evidence_inventory": [{"id": "e1", "content": "集群事件列表显示一个警告事件：replicaset/aiops-copilot-54dd898d8b 创建Pod失败，原因是服务账户 aiops/aiops-copilot 不存在。", "source": "kubectl_get_by_kind_in_cluster (事件列表)", "reliability": "高"}, {"id": "e2", "content": "查询旧ReplicaSet (aiops-copilot-54dd898d8b) 状态失败，提示资源不存在。", "source": "kubectl_describe", "reliability": "高"}, {"id": "e3", "content": "当前 aiops 命名空间中存在一个运行正常的Pod (aiops-copilot-6455dff479-bw4q8)，年龄31分钟，无重启。", "source": "kubectl_get_by_kind_in_namespace (Pod状态)", "reliability": "高"}, {"id": "e4", "content": "服务账户 aiops-copilot 当前已存在，年龄31分钟。", "source": "kubectl_get_by_kind_in_namespace (ServiceAccount)", "reliability": "高"}, {"id": "e5", "content": "aiops 命名空间资源概览显示 Deployment aiops-copilot 及其新ReplicaSet (aiops-copilot-6455dff479) 运行正常。", "source": "kubectl_get_by_kind_in_namespace (所有资源)", "reliability": "高"}, {"id": "e6", "content": "集群CPU使用率：master节点14.33%，node1节点9.76%，node2节点2.80%。", "source": "execute_prometheus_instant_query (CPU)", "reliability": "中"}, {"id": "e7", "content": "集群内存使用率：master节点26.98%，node1节点19.55%，node2节点8.71%。", "source": "execute_prometheus_instant_query (内存)", "reliability": "中"}, {"id": "e8", "content": "集群所有节点状态为Ready，所有Pod当前状态为Running。", "source": "问题定位结果摘要 (Node/Pod列表)", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning事件：对象 `replicaset/aiops-copilot-54dd898d8b`，原因 `FailedCreate`，错误信息 `Error creating: pods \"aiops-copilot-54dd898d8b-\" is forbidden: error looking up service account aiops/aiops-copilot: serviceaccount \"aiops-copilot\" not found`", "interpretation": "这是问题的直接现象。一个ReplicaSet在创建Pod时，因无法找到其指定的服务账户而失败。"}, {"evidence_id": "e2", "raw_data": "Command failed (exit 1): Error from server (NotFound): replicasets.apps \"aiops-copilot-54dd898d8b\" not found", "interpretation": "引发警告事件的旧ReplicaSet已不存在，表明该工作负载已被更新或清理。"}, {"evidence_id": "e3", "raw_data": "Pod `aiops-copilot-6455dff479-bw4q8` 状态: READY 1/1, STATUS Running, RESTARTS 0, AGE 31m", "interpretation": "当前存在一个同名应用的新版本Pod，运行完全正常，且年龄(31m)与警告事件时间(36m前)接近。"}, {"evidence_id": "e4", "raw_data": "ServiceAccount `aiops-copilot` 状态: SECRETS 0, AGE 31m", "interpretation": "之前缺失的服务账户现在已存在，且创建时间(31m)与当前正常Pod的年龄一致。"}, {"evidence_id": "e5", "raw_data": "Deployment `aiops-copilot` READY 1/1, UP-TO-DATE 1, AVAILABLE 1, AGE 31m。关联的ReplicaSet为 `aiops-copilot-6455dff479`。", "interpretation": "工作负载已成功更新至新版本(哈希后缀变更)，当前部署及其管理的副本集状态健康。"}, {"evidence_id": "e6", "raw_data": "CPU使用率百分比: master(10.2.0.48): 14.33, node1(10.2.0.49): 9.76, node2(10.2.0.50): 2.80", "interpretation": "所有节点CPU使用率处于极低水平，无资源瓶颈。"}, {"evidence_id": "e7", "raw_data": "内存使用率百分比: master: 26.98, node1: 19.55, node2: 8.71", "interpretation": "所有节点内存使用率处于健康水平，无内存压力。"}, {"evidence_id": "e8", "raw_data": "节点状态: Ready。Pod状态: Running (虽有历史重启记录，但均为3天前)。", "interpretation": "集群基础设施和所有工作负载当前运行状态完全正常。"}], "causal_chain": {"root_cause": "在部署或更新 `aiops-copilot` 应用时，其Kubernetes清单文件（如Deployment YAML）中指定的服务账户 `aiops-copilot` 在 `aiops` 命名空间中不存在。", "propagation": "1. 用户或CI/CD系统尝试创建或更新 `aiops-copilot` 的Deployment。\n2. Deployment控制器创建了ReplicaSet `aiops-copilot-54dd898d8b`。\n3. 该ReplicaSet尝试创建Pod时，Kubernetes API Server进行权限校验，发现Pod规约中引用的服务账户 `aiops/aiops-copilot` 不存在。\n4. API Server拒绝创建Pod，并生成 `FailedCreate` 警告事件。", "direct_cause": "Pod创建请求因 `is forbidden: serviceaccount \"aiops-copilot\" not found` 错误被API Server拒绝。", "manifestation": "Kubernetes事件系统中记录了一条Warning类型事件，报告 `replicaset/aiops-copilot-54dd898d8b` 的 `FailedCreate` 错误。"}, "root_cause_summary": "根因是配置顺序问题：在部署 `aiops-copilot` 应用的Deployment（或其相关清单）时，其所依赖的服务账户 `aiops-copilot` 尚未在 `aiops` 命名空间中创建。证据e1直接显示了该错误。此问题已被修复，证据e3、e4、e5表明，服务账户（年龄31m）和新的、运行正常的Pod及ReplicaSet（年龄31m）已成功创建，集群当前无此问题。", "confidence": 0.95, "primary_runbooks": [], "alternative_causes": [], "limitations": "1. 分析基于历史事件，问题已自动或手动修复，无法获取问题发生时的实时配置和操作日志。\n2. 未采集到 `aiops-copilot` Deployment的详细YAML配置，无法确认服务账户引用是显式指定还是使用默认值。\n3. Prometheus查询结果未提供指标的单位说明（CPU使用率百分比，内存使用率百分比），但通过数值范围可判断正常。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: 在部署或更新 `aiops-copilot` 应用时，其Kubernetes清单文件（如Deployment YAML）中指定的服务账户 `aiops-copilot` 在 `aiops` 命名空间中不存在。
     传导机制: 1. 用户或CI/CD系统尝试创建或更新 `aiops-copilot` 的Deployment。
2. Deployment控制器创建了ReplicaSet `aiops-copilot-54dd898d8b`。
3. 该ReplicaSet尝试创建Pod时，Kubernetes API Server进行权限校验，发现Pod规约中引用的服务账户 `aiops/aiops-copilot` 不存在。
4. API Server拒绝创建Pod，并生成 `FailedCreate` 警告事件。
     最终表现: Kubernetes事件系统中记录了一条Warning类型事件，报告 `replicaset/aiops-copilot-54dd898d8b` 的 `FailedCreate` 错误。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (29.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 1404 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 47.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 查询结果

- **查询目标**: 检查集群当前整体状态及是否存在问题
- **模式**: QUERY 结构化回复
- **采集情况**: 计划 6 项，实际采集 6 项，未采集 0 项，完整度 100%

## 📈 数据摘要
| 对象 | 指标 | 数值 | 状态 | 数据来源 |
|------|------|------|------|----------|
| 集群 | 节点状态 | 3/3 Ready | 正常 | `kubectl get nodes` |
| 集群 | Pod 整体状态 | 所有 Pod 为 Running | 正常 | `kubectl get pods --all-namespaces` |
| aiops 命名空间 | aiops-copilot Pod 状态 | 1/1 Running (aiops-copilot-6455dff479-bw4q8) | 正常 | `kubectl get pods -n aiops \| grep aiops-copilot` |
| aiops 命名空间 | aiops-copilot 服务账户状态 | 已存在 (年龄: 31m) | 正常 | `kubectl get serviceaccounts -n aiops \| grep aiops-copilot` |
| 节点 master (10.2.0.48) | CPU 使用率 | 14.33% | 正常 | PromQL: `(1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)) * 100` |
| 节点 node1 (10.2.0.49) | CPU 使用率 | 9.76% | 正常 | 同上 |
| 节点 node2 (10.2.0.50) | CPU 使用率 | 2.80% | 正常 | 同上 |
| 节点 master (10.2.0.48) | 内存使用率 | 26.98% | 正常 | PromQL: `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100` |
| 节点 node1 (10.2.0.49) | 内存使用率 | 19.55% | 正常 | 同上 |
| 节点 node2 (10.2.0.50) | 内存使用率 | 8.71% | 正常 | 同上 |

## 🔎 补充说明
- **历史异常（已恢复）**：约36分钟前，`aiops` 命名空间下 `aiops-copilot` 应用的 ReplicaSet 曾因服务账户 `aiops-copilot` 缺失而创建 Pod 失败。目前该服务账户（年龄31m）和新的 Pod（年龄31m）均已成功创建，应用运行正常。
- **Pod 重启历史**：部分 Pod（如 `kube-controller-manager-master`）有历史重启记录（最高达36次），但最近一次重启均在3天前，表明集群近期运行稳定。
- **关于旧 ReplicaSet**：引发历史警告的 `replicaset/aiops-copilot-54dd898d8b` 已不存在，表明工作负载已更新。

---

## 📊 性能统计

├─ 总耗时: 3.8m
├─ 问题定位: 67.7s (30%) ✅
├─ 证据链采集: 54.5s (24%) ✅
├─ 根因分析: 75.3s (33%) ✅
├─ 汇总总结: 29.5s (13%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **参考 Runbook**: 无
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
