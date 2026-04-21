======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 39cd101bbbfc4d6c]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您检查集群的整体健康状况。首先，让我查看所有Pod的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS        AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     apphealth-
   💭 [问题定位] 现在让我检查节点状态，看看是否有节点层面的问题：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   207d   v1.26.8  
   💭 [问题定位] 现在让我检查是否有异常状态的Pod。从Pod列表看，所有Pod都是Running状态，但让我检查是否有任何Pod有重启次数异常的情况。我注意到有一个Pod的标签显示`l4-scenario=app-health-fail`，这看起来是一个应用健康检查失败的场景。让我检查这个Pod的详细信息：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             apphealth-64f87849cb-lnx59
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Mon, 20 Apr 2026 09:27:11 +00
   💭 [问题定位] 这个Pod看起来是专门为测试L4应用层健康检查失败场景而设置的。让我获取相关的runbook来了解更多信息：
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L4 应用健康检查失败 (Readiness/Liveness Probe Failure)

> 层级: L4 - 应用层 | 场景: 应用 Probe 失败导致 Pod NotReady 或频繁重启

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Running 但 READY=0/1，或频繁重启 |
| E
   💭 [问题定位] 现在让我检查是否有其他异常Pod。从Pod列表看，所有Pod都是Running状态，但让我检查是否有任何Pod有重启次数异常的情况。我注意到nfs-client-provisioner有4次重启，但最近一次是3天前。让我检查一下这个Pod：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             nfs-client-provisioner-6fcd4994c9-lczf6
Namespace:        default
Priority:         0
Service Account:  nfs-client-provisioner
Node:             node2/10.2.0.50
Start Time:       Mon
   ✅ [问题定位] 完成 (42.2s)
   📤 → 下游数据: layer=Layer.QUERY, layers=QUERY
   scenarios=[]
   entities=[{"type": "Pod", "value": "nfs-client-provisioner-6fcd4994c9-lczf6"}, {"type": "Pod", "value": "apphealth-64f87849cb-lnx59"}]
   reasoning=用户意图是检查集群中是否有其他异常Pod，特别是关注重启次数异常的情况。分析文本显示用户正在主动查询Pod列表和状态，属于数据查询行为，而非请求故障诊断。集群中所有Pod状态为Running，节点状态为Ready，虽有部分Pod存在历史重启记录，但用户并未询问根因或请求排查。
   layer_analysis={"layer": "QUERY", "layers": [], "layer_name": "查询模式", "confidence": 0.95, "reasoning": "用户意图是检查集群中是否有其他异常Pod，特别是关注重启次数异常的情况。分析文本显示用户正在主动查询Pod列表和状态，属于数据查询行为，而非请求故障诊断。集群中所有Pod状态为Running，节点状态为Ready，虽有部分Pod存在历史重启记录，但用户并未询问根因或请求排查。", "key_entities": [{"type": "Pod", "value": "nfs-client-provisioner-6fcd4994c9-lczf6"}, {"type": "Pod", "value": "apphealth-64f87849cb-lnx59"}], "possible_scenarios": []}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.QUERY
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 基于我看到的集群状态，我将制定一个全面的证据采集计划来诊断集群可能存在的问题。

```json
{
  "layer": "QUERY",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "检查所有节点的状态和资源使用情况",
      "level": "critical",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance)) * 100",
      "purpose": "确认各节点CPU使用率是否正常"
    },
    {
      "id": "e2",
      "description": "检查节点内存使用情况",
      "level": "critical",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
      "purpose": "确认各节点内存使用率是否正常"
    },
    {
      "id": "e3",
      "description": "检查节点磁盘使用情况",
      "level": "critical",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"}) * 100",
      "purpose": "确认根目录磁盘使用率是否正常"
    },
    {
      "id": "e4",
      "description": "检查重启次数异常的Pod详细信息",
      "level": "important",
      "tool": "kubectl_describe",
      "command": "pod nfs-client-provisioner-6fcd4994c9-lczf6 -n default",
      "purpose": "分析nfs-client-provisioner频繁重启的原因"
    },
    {
      "id": "e5",
      "description": "检查最近的事件和告警",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_cluster",
      "command": "events",
      "purpose": "查看集群中是否有异常事件"
    },
    {
      "id": "e6",
      "description": "检查测试应用apphealth的状态",
      "level": "optional",
      "tool": "kubectl_describe",
      "command": "pod apphealth-64f87849cb-lnx59 -n aiops-e2e",
      "purpose": "确认测试应用的运行状态"
    }
  ],
  "collection_strategy": "首先检查集群整体健康状态（节点资源），然后分析异常Pod，最后查看集群事件。重点关注nfs-client-provisioner的频繁重启问题。"
}
```

现在我将逐项执行证据采集：
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"instance":"10.2.0.49:9100"},"value":[1776683067.803,"9.781597222221938"]},{"metric":{"instance":"10.2.0.48:9100"},"value":[17766
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"container":"node-exporter","endpoint":"http-metrics","instance":"10.2.0.49:9100","job":"node-exporter","namespace":"xnet","pod":
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"container":"node-exporter","device":"/dev/mapper/ubuntu--vg-ubuntu--lv","endpoint":"http-metrics","fstype":"ext4","instance":"10
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             nfs-client-provisioner-6fcd4994c9-lczf6
Namespace:        default
Priority:         0
Service Account:  nfs-client-provisioner
Node:             node2/10.2.0.50
Start Time:       Mon
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE   LAST SEEN   TYPE      REASON              OBJECT                                SUBOBJECT                                      SOURCE                                        MESSAGE        
   ✅ [证据链采集] 完成 (54.8s)
   📤 → 下游数据: evidence_items=5/6
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "检查所有节点的状态和资源使用情况", "level": "critical", "tool": "execute_prometheus_instant_query", "command": "(1 - avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance)) * 100", "purpose": "确认各节点CPU使用率是否正常"}, {"id": "e2", "description": "检查节点内存使用情况", "level": "critical", "tool": "execute_prometheus_instant_query", "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100", "purpose": "确认各节点内存使用率是否正常"}, {"id": "e3", "description": "检查节点磁盘使用情况", "level": "critical", "tool": "execute_prometheus_instant_query", "command": "(1 - node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"}) * 100", "purpose": "确认根目录磁盘使用率是否正常"}, {"id": "e4", "description": "检查重启次数异常的Pod详细信息", "level": "important", "tool": "kubectl_describe", "command": "pod nfs-client-provisioner-6fcd4994c9-lczf6 -n default", "purpose": "分析nfs-client-provisioner频繁重启的原因"}, {"id": "e5", "description": "检查最近的事件和告警", "level": "important", "tool": "kubectl_get_by_kind_in_cluster", "command": "events", "purpose": "查看集群中是否有异常事件"}, {"id": "e6", "description": "检查测试应用apphealth的状态", "level": "optional", "tool": "kubectl_describe", "command": "pod apphealth-64f87849cb-lnx59 -n aiops-e2e", "purpose": "确认测试应用的运行状态"}], "tool_results": [], "tool_data": [{"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"instance\":\"10.2.0.49:9100\"},\"value\":[1776683067.803,\"9.781597222221938\"]},{\"metric\":{\"instance\":\"10.2.0.48:9100\"},\"value\":[17766", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"container\":\"node-exporter\",\"endpoint\":\"http-metrics\",\"instance\":\"10.2.0.49:9100\",\"job\":\"node-exporter\",\"namespace\":\"xnet\",\"pod\":", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"container\":\"node-exporter\",\"device\":\"/dev/mapper/ubuntu--vg-ubuntu--lv\",\"endpoint\":\"http-metrics\",\"fstype\":\"ext4\",\"instance\":\"10", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             nfs-client-provisioner-6fcd4994c9-lczf6\nNamespace:        default\nPriority:         0\nService Account:  nfs-client-provisioner\nNode:             node2/10.2.0.50\nStart Time:       Mon", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE   LAST SEEN   TYPE      REASON              OBJECT                                SUBOBJECT                                      SOURCE                                        MESSAGE        ", "duration_s": 0}], "llm_analysis": "基于我看到的集群状态，我将制定一个全面的证据采集计划来诊断集群可能存在的问题。\n\n```json\n{\n  \"layer\": \"QUERY\",\n  \"evidence_plan\": [\n    {\n      \"id\": \"e1\",\n      \"description\": \"检查所有节点的状态和资源使用情况\",\n      \"level\": \"critical\",\n      \"tool\": \"execute_prometheus_instant_query\",\n      \"command\": \"(1 - avg(rate(node_cpu_seconds_total{mode=\\\"idle\\\"}[5m])) by (instance)) * 100\",\n      \"purpose\": \"确认各节点CPU使用率是否正常\"\n    },\n    {\n      \"id\": \"e2\",\n      \"description\": \"检查节点内存使用情况\",\n      \"level\": \"critical\",\n      \"tool\": \"execute_prometheus_instant_query\",\n      \"command\": \"(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100\",\n      \"purpose\": \"确认各节点内存使用率是否正常\"\n    },\n    {\n      \"id\": \"e3\",\n      \"description\": \"检查节点磁盘使用情况\",\n      \"level\": \"critical\",\n      \"tool\": \"execute_prometheus_instant_query\",\n      \"command\": \"(1 - node_filesystem_avail_bytes{mountpoint=\\\"/\\\"} / node_filesystem_size_bytes{mountpoint=\\\"/\\\"}) * 100\",\n      \"purpose\": \"确认根目录磁盘使用率是否正常\"\n    },\n    {\n      \"id\": \"e4\",\n      \"description\": \"检查重启次数异常的Pod详细信息\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_describe\",\n      \"command\": \"pod nfs-client-provisioner-6fcd4994c9-lczf6 -n default\",\n      \"purpose\": \"分析nfs-client-provisioner频繁重启的原因\"\n    },\n    {\n      \"id\": \"e5\",\n      \"description\": \"检查最近的事件和告警\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_get_by_kind_in_cluster\",\n      \"command\": \"events\",\n      \"purpose\": \"查看集群中是否有异常事件\"\n    },\n    {\n      \"id\": \"e6\",\n      \"description\": \"检查测试应用apphealth的状态\",\n      \"level\": \"optional\",\n      \"tool\": \"kubectl_describe\",\n      \"command\": \"pod apphealth-64f87849cb-lnx59 -n aiops-e2e\",\n      \"purpose\": \"确认测试应用的运行状态\"\n    }\n  ],\n  \"collection_strategy\": \"首先检查集群整体健康状态（节点资源），然后分析异常Pod，最后查看集群事件。重点关注nfs-client-provisioner的频繁重启问题。\"\n}\n```\n\n现在我将逐项执行证据采集：", "collection_summary": "计划 6 项，实际采集 5 项，未采集 1 项，完整度 83%", "evidence_inventory": [{"id": "e1", "description": "检查所有节点的状态和资源使用情况", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "检查节点内存使用情况", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "检查节点磁盘使用情况", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "检查重启次数异常的Pod详细信息", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "检查最近的事件和告警", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "检查测试应用apphealth的状态", "level": "optional", "collected": false, "source": "planned"}], "missing_reasons": ["e6(检查测试应用apphealth的状态): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/6 项, 完整度: 83%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (57.5s)
   📤 → 下游数据: root_cause=
   confidence=85%
   causal_chain={"root_cause": "1) master节点磁盘空间使用率较高(83.19%)；2) nfs-client-provisioner历史重启原因未知", "propagation": "磁盘空间不足可能导致Pod调度失败、镜像拉取失败、日志写入失败等问题；nfs-client-provisioner重启可能影响存储卷的动态供应", "direct_cause": "1) master节点/分区使用率接近警戒线；2) nfs-client-provisioner容器异常退出(Exit Code 255)", "manifestation": "1) 监控显示master磁盘使用率83.19%；2) nfs-client-provisioner有4次重启记录"}
   rca_analysis={"phenomenon": "集群整体运行正常，但存在两个潜在问题：1) nfs-client-provisioner Pod 有历史重启记录；2) master 节点磁盘使用率较高。", "evidence_inventory": [{"id": "e1", "content": "节点CPU使用率：node1=9.78%，master=13.63%，node2=2.84%", "source": "execute_prometheus_instant_query", "reliability": "高"}, {"id": "e2", "content": "节点内存使用率：node1=19.46%，master=27.14%，node2=8.83%", "source": "execute_prometheus_instant_query", "reliability": "高"}, {"id": "e3", "content": "节点磁盘使用率：node1=52.92%，master=83.19%，node2=54.90%", "source": "execute_prometheus_instant_query", "reliability": "高"}, {"id": "e4", "content": "nfs-client-provisioner Pod 详细信息：重启4次，最近一次重启3天前，Exit Code=255，Reason=Unknown", "source": "kubectl_describe", "reliability": "高"}, {"id": "e5", "content": "集群事件：主要为 aiops-copilot 部署的正常滚动更新事件，无异常告警", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e6", "content": "apphealth Pod 详细信息：为测试应用，正常运行，无重启", "source": "kubectl_describe", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "node1: 9.781597222221938%, master: 13.631597222221092%, node2: 2.8385416666666607%", "interpretation": "所有节点CPU使用率正常，均低于15%，无CPU压力"}, {"evidence_id": "e2", "raw_data": "node1: 19.459308978800916%, master: 27.139810495768778%, node2: 8.831981902640262%", "interpretation": "所有节点内存使用率正常，均低于30%，无内存压力"}, {"evidence_id": "e3", "raw_data": "node1: 52.92422246419357%, master: 83.19139380912786%, node2: 54.90043415470763%", "interpretation": "master节点磁盘使用率83.19%较高，接近警戒线；node1和node2磁盘使用率正常"}, {"evidence_id": "e4", "raw_data": "Restart Count: 4, Last State: Terminated, Reason: Unknown, Exit Code: 255, Last restart: 3 days ago", "interpretation": "nfs-client-provisioner有4次重启历史，最近一次重启发生在3天前，退出码255表示未知错误，但当前Pod运行正常"}, {"evidence_id": "e5", "raw_data": "54个事件记录，主要为Normal类型，涉及aiops-copilot部署的滚动更新、Pod调度、镜像拉取等正常操作", "interpretation": "集群事件正常，无异常告警或错误事件"}, {"evidence_id": "e6", "raw_data": "Pod状态：Running, Ready: True, Restart Count: 0, 容器命令为循环输出测试信息", "interpretation": "apphealth为测试应用，标签显示l4-scenario=app-health-fail，但实际运行正常，无重启"}], "causal_chain": {"root_cause": "1) master节点磁盘空间使用率较高(83.19%)；2) nfs-client-provisioner历史重启原因未知", "propagation": "磁盘空间不足可能导致Pod调度失败、镜像拉取失败、日志写入失败等问题；nfs-client-provisioner重启可能影响存储卷的动态供应", "direct_cause": "1) master节点/分区使用率接近警戒线；2) nfs-client-provisioner容器异常退出(Exit Code 255)", "manifestation": "1) 监控显示master磁盘使用率83.19%；2) nfs-client-provisioner有4次重启记录"}, "root_cause_summary": "基于证据分析：1) master节点磁盘使用率83.19%（证据e3），虽未达到紧急阈值但需关注；2) nfs-client-provisioner Pod有4次重启历史，最近一次在3天前，退出码255表示未知错误（证据e4），但当前运行正常。其他节点资源（CPU、内存）均正常，集群事件无异常告警。", "confidence": 0.85, "primary_runbooks": ["L4 应用健康检查失败 (Readiness/Liveness Probe Failure)"], "alternative_causes": ["nfs-client-provisioner重启可能由于NFS服务器连接问题", "master节点磁盘使用率高可能由于日志文件积累或监控数据存储"], "limitations": "1) 未采集nfs-client-provisioner的日志，无法确定具体重启原因；2) 未检查master节点磁盘的具体使用情况（哪些目录占用高）；3) 未检查NFS服务器状态；4) 证据e6显示apphealth为测试应用，但上游节点参考了L4 runbook，可能存在误判"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 85%
   🔗 因果链:
     根本原因: 1) master节点磁盘空间使用率较高(83.19%)；2) nfs-client-provisioner历史重启原因未知
     传导机制: 磁盘空间不足可能导致Pod调度失败、镜像拉取失败、日志写入失败等问题；nfs-client-provisioner重启可能影响存储卷的动态供应
     最终表现: 1) 监控显示master磁盘使用率83.19%；2) nfs-client-provisioner有4次重启记录


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (39.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 1743 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 14.1s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 查询结果

- **查询目标**: 检查集群整体是否存在问题
- **模式**: QUERY 结构化回复
- **采集情况**: 计划 6 项，实际采集 5 项，未采集 1 项，完整度 83%

## 📈 数据摘要
| 对象 | 指标 | 数值 | 状态 | 数据来源 |
|------|------|------|------|----------|
| **节点资源** | | | | |
| node1 (10.2.0.49) | CPU 使用率 | 9.78% | 正常 | Prometheus: `(1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)) * 100` |
| master (10.2.0.48) | CPU 使用率 | 13.63% | 正常 | 同上 |
| node2 (10.2.0.50) | CPU 使用率 | 2.84% | 正常 | 同上 |
| node1 (10.2.0.49) | 内存使用率 | 19.46% | 正常 | Prometheus: `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100` |
| master (10.2.0.48) | 内存使用率 | 27.14% | 正常 | 同上 |
| node2 (10.2.0.50) | 内存使用率 | 8.83% | 正常 | 同上 |
| node1 (10.2.0.49) | 根分区磁盘使用率 | 52.92% | 正常 | Prometheus: `(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100` |
| **master (10.2.0.48)** | **根分区磁盘使用率** | **83.19%** | **偏高** | 同上 |
| node2 (10.2.0.50) | 根分区磁盘使用率 | 54.90% | 正常 | 同上 |
| **异常 Pod** | | | | |
| nfs-client-provisioner-6fcd4994c9-lczf6 (default) | 重启次数 | 4 次 | 历史异常 | `kubectl describe pod nfs-client-provisioner-6fcd4994c9-lczf6 -n default` |
| | 最近重启时间 | 3 天前 | 已稳定 | 同上 |
| | 上次退出原因 | Unknown (Exit Code: 255) | 未知错误 | 同上 |
| **集群事件** | | | | |
| 集群 | 最近事件数量 | 54 条 | 正常 | `kubectl get events` |
| | 事件类型 | 主要为 Normal (滚动更新、调度等) | 正常 | 同上 |

## 🔎 补充说明
1.  **主要发现**：
    *   **master 节点磁盘使用率偏高**：根分区使用率达到 83.19%，虽未触发紧急告警，但已接近常见警戒线（如85%），需关注。
    *   **nfs-client-provisioner Pod 有历史重启**：该 Pod 曾重启 4 次，最近一次发生在 3 天前，退出原因为 `Unknown` (退出码 255)。目前 Pod 状态为 `Running`，已稳定运行。
2.  **其他状态**：集群所有节点 CPU 和内存使用率均处于低位，节点状态均为 `Ready`，近期集群事件无异常告警。
3.  **未获取到的信息**：计划中的“检查测试应用 apphealth 的状态”项未采集成功，但根据已有 Pod 列表，该 Pod (`apphealth-64f87849cb-lnx59`) 状态为 `Running`，重启次数为 0。

---

## 📊 性能统计

├─ 总耗时: 3.2m
├─ 问题定位: 42.2s (22%) ✅
├─ 证据链采集: 54.8s (28%) ✅
├─ 根因分析: 57.5s (30%) ✅
├─ 汇总总结: 39.5s (20%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: L4 应用健康检查失败 (Readiness/Liveness Probe Failure)
- **参考 Runbook**: L4 应用健康检查失败 (Readiness/Liveness Probe Failure)
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
