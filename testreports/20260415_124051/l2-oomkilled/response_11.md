======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f9774aaaffcd48c5]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您检查集群的健康状况。首先让我查看所有 Pod 的状态，这是诊断问题的第一步。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS      RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     memhog-5
   💭 [问题定位] 我发现了问题！有一个 Pod 状态异常：

**问题 Pod：**
- `memhog-578d9b5ffd-56mqz` (namespace: `aiops-e2e`) - **STATUS: OOMKilled**, RESTARTS: 18次

根据五层模型，OOMKilled 属于 **L2（工作负载层）** 问题。让我查看这个 Pod 的详细信息来确认根因：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             memhog-578d9b5ffd-56mqz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 15 Apr 2026 03:42:51 +0000

   💭 [问题定位] 现在让我查看这个 Pod 的日志来了解更多信息：
   💭 [问题定位] 调用工具: run_bash_command
   💭 [问题定位] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [问题定位] 让我检查一下是否有相关的 runbook 可以参考：
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
   💭 [问题定位] 现在让我检查节点状态，确保没有其他问题：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   202d   v1.26.8  
   💭 [问题定位] 让我查看集群事件，看看是否有其他警告：
   💭 [问题定位] 调用工具: run_bash_command
   💭 [问题定位] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "xnet        59m         Warning   Unhealthy   pod/prometheus-observability-prometheus-0   Readiness probe failed: Get \"http://172.16.166.142:9090/-/ready\": context deadl
   💭 [问题定位] 让我检查一下 prometheus 的状态：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             prometheus-observability-prometheus-0
Namespace:        xnet
Priority:         0
Service Account:  observability-prometheus
Node:             node1/10.2.0.49
Start Time:       Mon, 3
   💭 [问题定位] 现在让我查看一下 prometheus 的日志：
   💭 [问题定位] 调用工具: run_bash_command
   💭 [问题定位] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "time=2026-04-15T03:34:12.763Z level=INFO source=repair.go:54 msg=\"Found healthy block\" component=tsdb mint=1775649600172 maxt=1775714400000 ulid=01KNRYHG03MGZWKYHA6WS8VK
   💭 [问题定位] 让我使用 Prometheus 查询来检查内存使用情况：
   💭 [问题定位] 调用工具: execute_prometheus_instant_query
   💭 [问题定位] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"__name__":"container_memory_working_set_bytes","endpoint":"https-metrics","id":"/kubepods.slice/kubepods-burstable.slice/kubepod
   💭 [问题定位] 现在让我检查一下 prometheus 的内存使用情况：
   💭 [问题定位] 调用工具: execute_prometheus_instant_query
   💭 [问题定位] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"__name__":"container_memory_working_set_bytes","container":"prometheus","endpoint":"https-metrics","id":"/kubepods.slice/kubepod
   💭 [问题定位] 让我检查 prometheus 的内存限制：
   💭 [问题定位] 调用工具: execute_prometheus_instant_query
   💭 [问题定位] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"__name__":"kube_pod_container_resource_limits","container":"prometheus","endpoint":"http","instance":"172.16.219.89:8080","job":
   💭 [问题定位] 现在让我创建一个任务列表来跟踪调查进度：
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 4 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 4 completed, 0 in progress, 0 pending

[✓] [1] 检查 memhog Pod 的 OOMKilled 问题 - 确认是 L2 工作负载层问题
[✓] [2] 检查 promet
   💭 [问题定位] ## 集群问题诊断报告

### 🔍 **发现的问题**

1. **主要问题（L2 工作负载层）：**
   - **Pod**: `memhog-578d9b5ffd-56mqz` (namespace: `aiops-e2e`)
   - **状态**: CrashLoopBackOff, **OOMKilled**
   - **重启次数**: 18次
   - **根因**: 容器内存超过限制被 OOM Killer 终止
   - **证据**: 
     - `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`
     - 内存限制: 40Mi
     - 容器执行内存泄漏脚本：`while True: a.append("x"*1024*1024)`

2. **次要问题（L2 工作负载层）：**
   - **Pod**: `prometheus-observability-prometheus-0` (namespace: `xnet`)
   - **状态**: Running，但有健康检查失败警告
   - **重启次数**: 8次（最近一次重启原因为 OOMKilled）
   - **证据**:
     - 最近一次重启：`Last State: Terminated, Reason: OOMKilled, Exit Code: 137`
     - 当前内存使用：~508MB
     - 内存限制：512MB（接近限制）
     - 健康检查失败：`Readiness probe failed: context deadline exceeded`

### 📊 **详细分析**

#### 1. memhog Pod 问题分析
- **层级**: **L2（工作负载层）**
- **根因**: 容器内存超限
- **资源配置**: 
  - 内存限制: 40Mi
  - 内存请求: 20Mi
- **应用行为**: 执行 Python 脚本持续分配内存（1MB/次），导致内存泄漏
- **当前状态**: 处于 CrashLoopBackOff 循环，每次启动后很快 OOMKilled

#### 2. prometheus Pod 问题分析
- **层级**: **L2（工作负载层）**
- **根因**: 内存使用接近限制，可能导致性能问题
- **资源配置**:
  - 内存限制: 512Mi
  - 内存请求: 256Mi
  - 当前使用: ~508Mi（接近 99% 使用率）
- **影响**: 内存压力可能导致查询超时，健康检查失败
- **日志显示**: TSDB 数据加载和 WAL 重放需要大量内存

### ✅ **集群整体健康状况**
- **所有节点**: Ready ✅ (master, node1, node2)
- **其他 Pod**: 全部 Running ✅
- **无 L0/L1 问题**: 无磁盘压力、节点故障、调度问题

### 🎯 **问题分层定位**

| 问题 | 表象 | 根因层级 | 根因描述 |
|------|------|----------|----------|
| memhog Pod | CrashLoopBackOff, OOMKilled | **L2** | 容器内存超限（内存泄漏脚本） |
| prometheus Pod | 健康检查失败，历史 OOMKilled | **L2** | 内存使用接近限制，查询超时 |

### 💡 **建议修复方案**

#### 对于 memhog Pod:
1. **调整资源配置**:
   ```yaml
   resources:
     limits:
       memory: "200Mi"  # 增加内存限制
     requests:
       memory: "100Mi"
   ```

2. **修复应用代码**:
   - 修复内存泄漏的 Python 脚本
   - 添加内存使用监控和限制逻辑

#### 对于 prometheus Pod:
1. **增加内存资源**:
   ```yaml
   resources:
     limits:
       memory: "1Gi"  # 从 512Mi 增加到 1Gi
     requests:
       memory: "512Mi"
   ```

2. **优化 Prometheus 配置**:
   - 减少数据保留时间
   - 优化查询规则复杂度
   - 调整 scrape 间隔

3. **调整健康检查**:
   - 增加 readiness probe 的超时时间
   - 考虑使用更轻量的健康检查端点

### ⚠️ **注意**
- memhog Pod 看起来是测试用途（`e2e-test=true`标签），可能是故意设计的压力测试
- prometheus 的内存压力可能是由于数据量增长导致的，需要长期监控

**总结**: 集群主要问题是 **L2 工作负载层**的内存资源不足，没有发现 L0/L1 基础设施问题。建议优先解决 prometheus 的内存限制问题，因为它影响监控系统的稳定性。
   ✅ [问题定位] 完成 (2m 38.6s)
   📤 → 下游数据: layer=Layer.L2, layers=L2
   scenarios=[{'scenario': '容器内存超限被OOM Killer终止', 'probability': '高', 'reason': 'memhog Pod明确因内存泄漏脚本超过40Mi限制被OOMKilled；prometheus Pod内存使用接近512Mi限制，历史有OOMKilled记录'}, {'scenario': '资源配置不足', 'probability': '高', 'reason': 'memhog内存限制设置过低（40Mi）无法满足应用需求；prometheus内存限制（512Mi）不足以处理当前数据量'}, {'scenario': '应用内存泄漏', 'probability': '中', 'reason': 'memhog Pod执行无限内存分配脚本导致内存泄漏'}]
   entities=[{"type": "Pod", "value": "memhog-578d9b5ffd-56mqz"}, {"type": "Pod", "value": "prometheus-observability-prometheus-0"}]
   reasoning=分析文本明确识别出两个Pod存在OOMKilled问题：1) memhog-578d9b5ffd-56mqz状态为CrashLoopBackOff，Last State: Terminated, Reason: OOMKilled, Exit Code: 137，内存限制40Mi，容器执行内存泄漏脚本；2) prometheus-observability-prometheus-0最近一次重启原因为OOMKilled，当前内存使用~508MB接近512MB限制，导致健康检查失败。所有节点Ready，无L0/L1问题。
   layer_analysis={"layer": "L2", "layers": ["L2"], "layer_name": "工作负载层", "confidence": 0.95, "reasoning": "分析文本明确识别出两个Pod存在OOMKilled问题：1) memhog-578d9b5ffd-56mqz状态为CrashLoopBackOff，Last State: Terminated, Reason: OOMKilled, Exit Code: 137，内存限制40Mi，容器执行内存泄漏脚本；2) prometheus-observability-prometheus-0最近一次重启原因为OOMKilled，当前内存使用~508MB接近512MB限制，导致健康检查失败。所有节点Ready，无L0/L1问题。", "key_entities": [{"type": "Pod", "value": "memhog-578d9b5ffd-56mqz"}, {"type": "Pod", "value": "prometheus-observability-prometheus-0"}], "possible_scenarios": [{"scenario": "容器内存超限被OOM Killer终止", "probability": "高", "reason": "memhog Pod明确因内存泄漏脚本超过40Mi限制被OOMKilled；prometheus Pod内存使用接近512Mi限制，历史有OOMKilled记录"}, {"scenario": "资源配置不足", "probability": "高", "reason": "memhog内存限制设置过低（40Mi）无法满足应用需求；prometheus内存限制（512Mi）不足以处理当前数据量"}, {"scenario": "应用内存泄漏", "probability": "中", "reason": "memhog Pod执行无限内存分配脚本导致内存泄漏"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L2
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 基于上游的问题定位结果，我已经确认了集群中的两个关键问题。现在我将制定一个精炼的证据采集计划来进一步验证和量化这些问题。

```json
{
  "layer": "L2",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "验证 memhog Pod 的 OOMKilled 详细状态和重启历史",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml pod memhog-578d9b5ffd-56mqz -n aiops-e2e",
      "purpose": "获取完整的 Pod YAML 配置，包括详细的容器状态、重启计数、资源限制和状态历史"
    },
    {
      "id": "e2",
      "description": "验证 prometheus Pod 的详细配置和状态",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get -o yaml pod prometheus-observability-prometheus-0 -n xnet",
      "purpose": "获取 Prometheus Pod 的完整配置，包括资源限制、探针配置和详细状态信息"
    },
    {
      "id": "e3",
      "description": "查询 memhog Pod 的内存使用趋势",
      "level": "important",
      "tool": "execute_prometheus_range_query",
      "command": "container_memory_working_set_bytes{pod=\"memhog-578d9b5ffd-56mqz\", namespace=\"aiops-e2e\"}",
      "purpose": "查看 memhog Pod 内存使用随时间的变化趋势，确认内存泄漏模式"
    },
    {
      "id": "e4",
      "description": "查询 prometheus Pod 的内存使用趋势",
      "level": "important",
      "tool": "execute_prometheus_range_query",
      "command": "container_memory_working_set_bytes{pod=\"prometheus-observability-prometheus-0\", namespace=\"xnet\"}",
      "purpose": "查看 Prometheus Pod 内存使用随时间的变化趋势，确认是否持续接近限制"
    },
    {
      "id": "e5",
      "description": "查询节点内存使用情况",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
      "purpose": "确认节点整体内存压力，排除节点级内存不足导致的问题"
    },
    {
      "id": "e6",
      "description": "获取 prometheus 相关 Helm release 信息",
      "level": "optional",
      "tool": "helm_list",
      "command": "",
      "purpose": "确认 Prometheus 是否通过 Helm 部署，获取部署配置信息"
    }
  ],
  "collection_strategy": "首先获取两个异常 Pod 的完整配置信息，然后通过 Prometheus 查询内存使用趋势来确认问题模式，最后检查节点级资源状态以排除基础设施问题。"
}
```

现在让我执行这些证据采集计划：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  annotations:
    cni.projectcalico.org/containerID: 53810639977cdc3a6b08b95f886b0cfe2b73866445644fd675e344d1dec8d95d
    cni.projectcalico.org/podIP: 172.16.104.19
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  annotations:
    cni.projectcalico.org/containerID: 538e5c9125d7e10d293b91dc69b99fd57b98ee94aca82d6ae34c8760d1b433e1
    cni.projectcalico.org/podIP: 172.16.166.14
   💭 [证据链采集] 现在让我查询内存使用趋势：
   💭 [证据链采集] 调用工具: execute_prometheus_range_query
   💭 [证据链采集] 工具结果: execute_prometheus_range_query (success)
      📄 {"status":"success","data":{"resultType":"matrix","result":[{"metric":{"__name__":"container_memory_working_set_bytes","container":"memhog","endpoint":"https-metrics","id":"/kubepods.slice/kubepods-bu
   💭 [证据链采集] 调用工具: execute_prometheus_range_query
   💭 [证据链采集] 工具结果: execute_prometheus_range_query (success)
      📄 {"status":"success","data":{"resultType":"matrix","result":[{"metric":{"__name__":"container_memory_working_set_bytes","container":"config-reloader","endpoint":"https-metrics","id":"/kubepods.slice/ku
   💭 [证据链采集] 现在让我查询节点内存使用情况：
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"container":"node-exporter","endpoint":"http-metrics","instance":"10.2.0.49:9100","job":"node-exporter","namespace":"xnet","pod":
   💭 [证据链采集] 最后让我获取 Helm release 信息：
   💭 [证据链采集] 调用工具: helm_list
   💭 [证据链采集] 工具结果: helm_list (success)
      📄 NAME         	NAMESPACE	REVISION	UPDATED                                  	STATUS  	CHART              	APP VERSION
observability	xnet     	1       	2026-03-30 15:18:36.057713534 +0800 +0800	deployed	
   💭 [证据链采集] ## 证据采集结果总结

基于我的证据采集计划，我已经成功收集了以下关键证据：

### 1. **memhog Pod 详细配置和状态** ✅
- **Pod 状态**: `CrashLoopBackOff`，重启 18 次
- **容器状态**: `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`
- **资源配置**: 内存限制 `40Mi`，请求 `20Mi`
- **应用行为**: 容器执行内存泄漏脚本 `while True: a.append("x"*1024*1024)`
- **内存使用趋势**: 内存使用量在 300KB-400KB 范围内波动，但受限于 40Mi 限制

### 2. **prometheus Pod 详细配置和状态** ✅
- **Pod 状态**: `Running`，但重启 8 次
- **容器状态**: `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`
- **资源配置**: 内存限制 `512Mi`，请求 `256Mi`
- **探针配置**: 就绪探针超时时间 3 秒
- **内存使用趋势**: 内存使用量在 450MB-530MB 范围内波动，持续接近 512MB 限制
- **OOM 日志**: 显示查询超时错误 `"query timed out in expression evaluation"`

### 3. **内存使用趋势分析** ✅
- **memhog Pod**: 内存使用稳定在 300-400KB，远低于 40Mi 限制，但脚本持续分配内存导致 OOM
- **prometheus Pod**: 内存使用持续在 450-530MB 范围内，使用率 88-99%，多次接近或达到 512MB 限制

### 4. **节点内存使用情况** ✅
- **node1** (10.2.0.49): 内存使用率 21.57% (Prometheus 所在节点)
- **node2** (10.2.0.50): 内存使用率 10.91% (memhog 所在节点)  
- **master** (10.2.0.48): 内存使用率 33.73%
- **结论**: 节点级内存充足，问题在于 Pod 级别的资源限制

### 5. **Helm release 信息** ✅
- **observability**: 在 `xnet` 命名空间中部署，包含 Prometheus

## 问题根因确认

### 问题 1: memhog Pod OOMKilled
- **根因**: 应用内存泄漏脚本持续分配内存，超过 40Mi 限制
- **证据**: `Exit Code: 137`, `Reason: OOMKilled`, 重启 18 次，脚本明确分配 1MB 内存块

### 问题 2: prometheus Pod 内存压力
- **根因**: Prometheus 内存使用持续接近 512MB 限制，导致性能问题和历史 OOM
- **证据**: 
  - 内存使用率 88-99%，多次接近 512MB 限制
  - 重启 8 次，最近一次 OOMKilled
  - 就绪探针超时，查询执行超时
  - 节点内存充足 (21.57%)

## 建议修复方案

1. **memhog Pod**:
   - 增加内存限制至 200Mi 或更高
   - 修复应用脚本（如果是测试负载，可调整分配策略）

2. **prometheus Pod**:
   - 增加内存限制至 1Gi 或更高
   - 优化 Prometheus 配置（减少保留时间、简化查询规则）
   - 调整就绪探针超时时间至 10-15 秒

3. **监控建议**:
   - 为关键应用设置内存使用率告警（如 >80%）
   - 定期审查资源限制与实际使用情况

**集群整体状态**: 基础设施层健康，所有节点就绪，问题集中在工作负载层的资源配置不足。
📍 [根因分析] 执行中...
   ✅ [证据链采集] 完成 (2m 28.6s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "验证 memhog Pod 的 OOMKilled 详细状态和重启历史", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod memhog-578d9b5ffd-56mqz -n aiops-e2e", "purpose": "获取完整的 Pod YAML 配置，包括详细的容器状态、重启计数、资源限制和状态历史"}, {"id": "e2", "description": "验证 prometheus Pod 的详细配置和状态", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get -o yaml pod prometheus-observability-prometheus-0 -n xnet", "purpose": "获取 Prometheus Pod 的完整配置，包括资源限制、探针配置和详细状态信息"}, {"id": "e3", "description": "查询 memhog Pod 的内存使用趋势", "level": "important", "tool": "execute_prometheus_range_query", "command": "container_memory_working_set_bytes{pod=\"memhog-578d9b5ffd-56mqz\", namespace=\"aiops-e2e\"}", "purpose": "查看 memhog Pod 内存使用随时间的变化趋势，确认内存泄漏模式"}, {"id": "e4", "description": "查询 prometheus Pod 的内存使用趋势", "level": "important", "tool": "execute_prometheus_range_query", "command": "container_memory_working_set_bytes{pod=\"prometheus-observability-prometheus-0\", namespace=\"xnet\"}", "purpose": "查看 Prometheus Pod 内存使用随时间的变化趋势，确认是否持续接近限制"}, {"id": "e5", "description": "查询节点内存使用情况", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100", "purpose": "确认节点整体内存压力，排除节点级内存不足导致的问题"}, {"id": "e6", "description": "获取 prometheus 相关 Helm release 信息", "level": "optional", "tool": "helm_list", "command": "", "purpose": "确认 Prometheus 是否通过 Helm 部署，获取部署配置信息"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    cni.projectcalico.org/containerID: 53810639977cdc3a6b08b95f886b0cfe2b73866445644fd675e344d1dec8d95d\n    cni.projectcalico.org/podIP: 172.16.104.19", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    cni.projectcalico.org/containerID: 538e5c9125d7e10d293b91dc69b99fd57b98ee94aca82d6ae34c8760d1b433e1\n    cni.projectcalico.org/podIP: 172.16.166.14", "duration_s": 0}, {"tool": "execute_prometheus_range_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"matrix\",\"result\":[{\"metric\":{\"__name__\":\"container_memory_working_set_bytes\",\"container\":\"memhog\",\"endpoint\":\"https-metrics\",\"id\":\"/kubepods.slice/kubepods-bu", "duration_s": 0}, {"tool": "execute_prometheus_range_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"matrix\",\"result\":[{\"metric\":{\"__name__\":\"container_memory_working_set_bytes\",\"container\":\"config-reloader\",\"endpoint\":\"https-metrics\",\"id\":\"/kubepods.slice/ku", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"container\":\"node-exporter\",\"endpoint\":\"http-metrics\",\"instance\":\"10.2.0.49:9100\",\"job\":\"node-exporter\",\"namespace\":\"xnet\",\"pod\":", "duration_s": 0}, {"tool": "helm_list", "data": "NAME         \tNAMESPACE\tREVISION\tUPDATED                                  \tSTATUS  \tCHART              \tAPP VERSION\nobservability\txnet     \t1       \t2026-03-30 15:18:36.057713534 +0800 +0800\tdeployed\t", "duration_s": 0}], "llm_analysis": "## 证据采集结果总结\n\n基于我的证据采集计划，我已经成功收集了以下关键证据：\n\n### 1. **memhog Pod 详细配置和状态** ✅\n- **Pod 状态**: `CrashLoopBackOff`，重启 18 次\n- **容器状态**: `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`\n- **资源配置**: 内存限制 `40Mi`，请求 `20Mi`\n- **应用行为**: 容器执行内存泄漏脚本 `while True: a.append(\"x\"*1024*1024)`\n- **内存使用趋势**: 内存使用量在 300KB-400KB 范围内波动，但受限于 40Mi 限制\n\n### 2. **prometheus Pod 详细配置和状态** ✅\n- **Pod 状态**: `Running`，但重启 8 次\n- **容器状态**: `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`\n- **资源配置**: 内存限制 `512Mi`，请求 `256Mi`\n- **探针配置**: 就绪探针超时时间 3 秒\n- **内存使用趋势**: 内存使用量在 450MB-530MB 范围内波动，持续接近 512MB 限制\n- **OOM 日志**: 显示查询超时错误 `\"query timed out in expression evaluation\"`\n\n### 3. **内存使用趋势分析** ✅\n- **memhog Pod**: 内存使用稳定在 300-400KB，远低于 40Mi 限制，但脚本持续分配内存导致 OOM\n- **prometheus Pod**: 内存使用持续在 450-530MB 范围内，使用率 88-99%，多次接近或达到 512MB 限制\n\n### 4. **节点内存使用情况** ✅\n- **node1** (10.2.0.49): 内存使用率 21.57% (Prometheus 所在节点)\n- **node2** (10.2.0.50): 内存使用率 10.91% (memhog 所在节点)  \n- **master** (10.2.0.48): 内存使用率 33.73%\n- **结论**: 节点级内存充足，问题在于 Pod 级别的资源限制\n\n### 5. **Helm release 信息** ✅\n- **observability**: 在 `xnet` 命名空间中部署，包含 Prometheus\n\n## 问题根因确认\n\n### 问题 1: memhog Pod OOMKilled\n- **根因**: 应用内存泄漏脚本持续分配内存，超过 40Mi 限制\n- **证据**: `Exit Code: 137`, `Reason: OOMKilled`, 重启 18 次，脚本明确分配 1MB 内存块\n\n### 问题 2: prometheus Pod 内存压力\n- **根因**: Prometheus 内存使用持续接近 512MB 限制，导致性能问题和历史 OOM\n- **证据**: \n  - 内存使用率 88-99%，多次接近 512MB 限制\n  - 重启 8 次，最近一次 OOMKilled\n  - 就绪探针超时，查询执行超时\n  - 节点内存充足 (21.57%)\n\n## 建议修复方案\n\n1. **memhog Pod**:\n   - 增加内存限制至 200Mi 或更高\n   - 修复应用脚本（如果是测试负载，可调整分配策略）\n\n2. **prometheus Pod**:\n   - 增加内存限制至 1Gi 或更高\n   - 优化 Prometheus 配置（减少保留时间、简化查询规则）\n   - 调整就绪探针超时时间至 10-15 秒\n\n3. **监控建议**:\n   - 为关键应用设置内存使用率告警（如 >80%）\n   - 定期审查资源限制与实际使用情况\n\n**集群整体状态**: 基础设施层健康，所有节点就绪，问题集中在工作负载层的资源配置不足。", "collection_summary": "计划 6 项，实际采集 6 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "e1", "description": "验证 memhog Pod 的 OOMKilled 详细状态和重启历史", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "验证 prometheus Pod 的详细配置和状态", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "查询 memhog Pod 的内存使用趋势", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "查询 prometheus Pod 的内存使用趋势", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "查询节点内存使用情况", "level": "optional", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "获取 prometheus 相关 Helm release 信息", "level": "optional", "collected": true, "source": "thinking_match"}], "missing_reasons": []}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/6 项, 完整度: 100%

📍 [汇总总结] 执行中...
   ✅ [根因分析] 完成 (1m 22.0s)
   📤 → 下游数据: root_cause=详见 LLM 原始分析
   confidence=60%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_analysis": [], "causal_chain": {}, "root_cause": "详见 LLM 原始分析", "llm_raw_analysis": "```json\n{\n  \"phenomenon\": \"集群中存在两个Pod出现异常：1) memhog-578d9b5ffd-56mqz 处于CrashLoopBackOff状态，重启18次；2) prometheus-observability-prometheus-0 运行中但就绪探针失败，重启8次。\",\n  \"evidence_inventory\": [\n    {\n      \"id\": \"e1\",\n      \"content\": \"memhog Pod详细状态：状态CrashLoopBackOff，容器上次终止原因为OOMKilled (Exit Code 137)，重启18次，内存限制40Mi，请求20Mi，容器执行内存泄漏脚本while True: a.append('x'*1024*1024)\",\n      \"source\": \"kubectl_get_yaml (证据1)\",\n      \"reliability\": \"高\"\n    },\n    {\n      \"id\": \"e2\",\n      \"content\": \"prometheus Pod详细状态：状态Running，prometheus容器上次终止原因为OOMKilled (Exit Code 137)，重启8次，内存限制512Mi，请求256Mi，就绪探针超时失败\",\n      \"source\": \"kubectl_get_yaml (证据2)\",\n      \"reliability\": \"高\"\n    },\n    {\n      \"id\": \"e3\",\n      \"content\": \"memhog Pod内存使用趋势：内存工作集在300-400KB范围内波动，最近值为319488字节（约0.3MB）\",\n      \"source\": \"execute_prometheus_range_query (证据3)\",\n      \"reliability\": \"高\"\n    },\n    {\n      \"id\": \"e4\",\n      \"content\": \"prometheus Pod内存使用趋势：prometheus容器内存工作集在450-530MB范围内波动，最近值为508645376字节（约508MB），多次接近512MB限制\",\n      \"source\": \"execute_prometheus_range_query (证据4)\",\n      \"reliability\": \"高\"\n    },\n    {\n      \"id\": \"e5\",\n      \"content\": \"节点内存使用率：node1（Prometheus所在节点）21.57%，node2（memhog所在节点）10.91%，master 33.73%\",\n      \"source\": \"execute_prometheus_instant_query (证据5)\",\n      \"reliability\": \"高\"\n    },\n    {\n      \"id\": \"e6\",\n      \"content\": \"Helm release信息：observability release在xnet命名空间部署，包含Prometheus\",\n      \"source\": \"helm_list (证据6)\",\n      \"reliability\": \"高\"\n    }\n  ],\n  \"evidence_analysis\": [\n    {\n      \"evidence_id\": \"e1\",\n      \"raw_data\": \"containerStatuses: [{\\\"lastState\\\": {\\\"terminated\\\": {\\\"exitCode\\\": 137, \\\"reason\\\": \\\"OOMKilled\\\"}}, \\\"restartCount\\\": 18}], spec.containers[0].resources.limits.memory: \\\"40Mi\\\", spec.containers[0].args: [\\\"import time\\\\na=[]\\\\nwhile True:\\\\n  a.append(\\\\\\\"x\\\\\\\"*1024*1024)\\\\n  time.sleep(0.02)\\\"]\",\n      \"interpretation\": \"memhog容器因内存超限被OOM Killer终止，容器执行的内存泄漏脚本会持续分配1MB内存块，超过40Mi限制导致反复OOM\"\n    },\n    {\n      \"evidence_id\": \"e2\",\n      \"raw_data\": \"containerStatuses: [{\\\"name\\\": \\\"prometheus\\\", \\\"lastState\\\": {\\\"terminated\\\": {\\\"exitCode\\\": 137, \\\"reason\\\": \\\"OOMKilled\\\"}}, \\\"restartCount\\\": 8}], spec.containers[0].resources.limits.memory: \\\"512Mi\\\", spec.containers[0].readinessProbe.timeoutSeconds: 3\",\n      \"interpretation\": \"prometheus容器历史上有OOMKilled记录，当前内存限制为512Mi，就绪探针超时时间仅3秒，在内存压力下容易失败\"\n    },\n    {\n      \"evidence_id\": \"e3\",\n      \"raw_data\": \"values: [[1776228660,\\\"319488\\\"], [1776228690,\\\"319488\\\"], [1776228720,\\\"319488\\\"], [1776228750,\\\"319488\\\"], [1776228780,\\\"319488\\\"], [1776228810,\\\"319488\\\"], [1776228840,\\\"319488\\\"], [1776228870,\\\"319488\\\"], [1776228900,\\\"319488\\\"]]\",\n      \"interpretation\": \"memhog容器内存使用稳定在约0.3MB，远低于40Mi限制，但脚本持续分配内存最终会导致OOM\"\n    },\n    {\n      \"evidence_id\": \"e4\",\n      \"raw_data\": \"values: [[1776228690,\\\"508645376\\\"], [1776228720,\\\"501149696\\\"], [1776228750,\\\"509648896\\\"], [1776228780,\\\"501415936\\\"], [1776228810,\\\"502546432\\\"], [1776228840,\\\"510222336\\\"], [1776228870,\\\"510222336\\\"], [1776228900,\\\"510222336\\\"]]\",\n      \"interpretation\": \"prometheus容器内存使用在501-510MB范围内，持续接近512MB限制，使用率约98-99.6%，导致性能问题和历史OOM\"\n    },\n    {\n      \"evidence_id\": \"e5\",\n      \"raw_data\": \"result: [{\\\"value\\\": [1776228850.762,\\\"21.571036924345133\\\"]}, {\\\"value\\\": [1776228850.762,\\\"33.72573971199214\\\"]}, {\\\"value\\\": [1776228850.762,\\\"10.908916286595305\\\"]}]\",\n      \"interpretation\": \"所有节点内存使用率正常（node1: 21.57%, node2: 10.91%, master: 33.73%），表明问题在于Pod级别资源限制，而非节点资源不足\"\n    },\n    {\n      \"evidence_id\": \"e6\",\n      \"raw_data\": \"NAME         \tNAMESPACE\tREVISION\tUPDATED                                  \tSTATUS  \tCHART              \tAPP VERSION\\nobservability\txnet     \t1       \t2026-03-30 15:18:36.057713534 +0800 +0800\tdeployed\tobservability-1.0.2\t1.0.0\",\n      \"interpretation\": \"Prometheus通过observability Helm chart部署，配置可能通过Helm values控制，需要检查资源限制配置\"\n    }\n  ],\n  \"causal_chain\": {\n    \"root_cause\": \"工作负载层（L2）资源配置不足：1) memhog应用内存泄漏脚本超过40Mi限制；2) Prometheus内存使用接近512Mi限制\",\n    \"propagation\": \"内存超限 → 容器被OOM Killer终止 → 容器重启 → 健康检查失败/持续崩溃\",\n    \"direct_cause\": \"1) memhog容器执行while True: a.append('x'*1024*1024)脚本，持续分配内存超过40Mi限制；2) Prometheus容器内存使用达508MB（99%使用率），导致性能下降和就绪探针超时\",\n    \"manifestation\": \"1) memhog Pod处于CrashLoopBackOff状态，重启18次；2) prometheus Pod就绪探针失败，重启8次（含OOMKilled记录）\"\n  },\n  \"root_cause_summary\": \"集群存在两个独立的工作负载层内存问题：1) memhog-578d9b5ffd-56mqz (aiops-e2e) 因执行内存泄漏脚本超过40Mi限制而被OOMKilled，证据：Exit Code 137，重启18次，脚本while True: a.append('x'*1024*1024)；2) prometheus-observability-prometheus-0 (xnet) 内存使用达508MB（证据：最近值508645376字节），接近512Mi限制（99%使用率），导致历史OOM（Exit Code 137，重启8次）和当前就绪探针超时失败。节点内存充足（node1: 21.57%, node2: 10.91%），问题仅限于Pod资源配置。\",\n  \"confidence\": 0.95,\n  \"primary_runbooks\": [\"L2 OOMKilled（Exit Code 137）\"],\n  \"alternative_causes\": [],\n  \"limitations\": \"分析基于当前时刻的快照数据，未检查Pod的长期历史日志或应用内部错误。memhog可能是故意设置的测试负载，Prometheus的精确内存需求需要更长时间观察。\"\n}\n```", "confidence": 0.6, "confidence_reason": "LLM 未输出结构化 JSON，使用原始分析文本", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 详见 LLM 原始分析
   置信度: 60%

   ✅ [汇总总结] 完成 (5ms)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 7168 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 30.6s
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
| **问题分类** | 内存超限 (OOMKilled) |
| **置信度** | 高 (95%) |
| **证据完整度** | 6/6 (100%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键发现**：
您的集群整体基础设施（节点）健康，但存在两个独立的工作负载层内存问题：
1.  **Pod `memhog-578d9b5ffd-56mqz`** 处于 `CrashLoopBackOff` 状态，已重启 **18 次**。
2.  **Pod `prometheus-observability-prometheus-0`** 处于 `Running` 状态，但就绪探针持续失败，已重启 **8 次**，且历史上有因内存超限被终止的记录。

**关键实体**：
| 类型 | 值 |
|------|-----|
| 异常 Pod 1 | `memhog-578d9b5ffd-56mqz` |
| 命名空间 1 | `aiops-e2e` |
| 节点 1 | `node2` |
| 异常 Pod 2 | `prometheus-observability-prometheus-0` |
| 命名空间 2 | `xnet` |
| 节点 2 | `node1` |
| 共同错误信息 | `Reason: OOMKilled, Exit Code: 137` |

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与配置 | `kubectl get -o yaml pod memhog-...` | `lastState: {terminated: {exitCode: 137, reason: "OOMKilled"}}`, `restartCount: 18`, `limits.memory: "40Mi"`, `args: ["import time\na=[]\nwhile True:\n a.append(\"x\"*1024*1024)\n time.sleep(0.02)"]` | 容器因内存超限被终止，内存限制为40Mi，容器执行内存泄漏脚本。 |
| 2 | Pod 状态与配置 | `kubectl get -o yaml pod prometheus-...` | `lastState: {terminated: {exitCode: 137, reason: "OOMKilled"}}`, `restartCount: 8`, `limits.memory: "512Mi"`, `readinessProbe.timeoutSeconds: 3` | 容器历史上有OOM记录，内存限制为512Mi，就绪探针超时时间短（3秒）。 |
| 3 | 内存使用趋势 | `container_memory_working_set_bytes{pod="memhog-..."}` | `values: [[...,"319488"], [...,"319488"], ...]` (约 0.3MB) | 容器内存使用稳定在约0.3MB，但脚本持续分配内存最终会触发OOM。 |
| 4 | 内存使用趋势 | `container_memory_working_set_bytes{pod="prometheus-..."}` | `values: [[...,"508645376"], [...,"501149696"], ...]` (约 508MB - 501MB) | Prometheus容器内存使用持续在501-510MB高位，接近512MB限制，使用率高达98%-99.6%。 |
| 5 | 节点内存压力 | `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100` | `node1: 21.57%`, `node2: 10.91%`, `master: 33.73%` | 所有节点内存充足，问题在于Pod级别的资源限制，而非节点资源不足。 |
| 6 | 部署信息 | `helm list` | `observability` release 在 `xnet` 命名空间 | Prometheus 通过 Helm Chart 部署，资源配置可通过 Helm values 调整。 |

### 证据关联分析
- **证据 #1 + #3 印证**：`Exit Code 137 (OOMKilled)` + `内存泄漏脚本` + `内存限制 40Mi` → **memhog Pod 因应用脚本持续消耗内存超过限制而被反复终止**。
- **证据 #2 + #4 印证**：`历史 Exit Code 137 (OOMKilled)` + `当前内存使用 ~508MB` + `内存限制 512Mi` → **Prometheus Pod 内存使用持续接近上限，导致历史OOM及当前性能问题**。
- **证据 #4 + #2 印证**：`内存使用率 99%` + `就绪探针超时 3秒` → **高内存压力导致 Prometheus 响应变慢，就绪探针因超时而失败**。
- **证据 #5 支撑**：节点内存使用率低 → **排除节点级内存压力，将问题定位在 Pod 资源配置**。

### 缺失证据（如有）
*无缺失证据。*

## 🎯 根因分析
### 因果链
#### 问题一：memhog Pod CrashLoopBackOff
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用容器执行内存泄漏脚本，持续分配内存                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 内存消耗超过 Pod 设置的 40Mi 限制                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 触发 cgroup OOM Killer，容器被终止 (Exit Code 137)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，重启次数达 18 次                   │
└─────────────────────────────────────────────────────────────────┘
```

#### 问题二：Prometheus Pod 就绪探针失败
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Prometheus 工作内存需求持续接近或达到 512Mi 的限制               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┘
│ 传导机制                                                        │
│ 1. 内存压力导致性能下降，查询超时；2. 历史上曾触发 OOM          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 1. 就绪探针（3秒超时）因服务响应慢而失败；2. 容器曾因OOM被终止  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod Running 但就绪探针失败，重启次数达 8 次                     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据链，集群中存在两个独立的 **L2 工作负载层内存资源配置不足** 问题：
1.  **memhog Pod**：根本原因是**应用内存泄漏脚本 (`while True: a.append("x"*1024*1024)`) 的内存消耗超过了容器设置的 40Mi 限制**（证据 #1），导致容器被 OOM Killer 反复终止。
2.  **Prometheus Pod**：根本原因是**Prometheus 实例的实际内存工作集（~508MB，证据 #4）持续接近其配置的内存限制（512Mi，证据 #2）**，导致服务性能下降、就绪探针超时，并曾触发 OOM 导致重启。

**置信度**：高 (95%)
- ✅ 两个 Pod 均有明确的 `OOMKilled (Exit Code 137)` 记录。
- ✅ 内存使用监控数据与限制值直接关联。
- ✅ 节点级资源充足，排除底层干扰。
- ⚠️ memhog 可能是测试负载，Prometheus 的长期内存需求需进一步观察。

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 调整 memhog Pod 的内存限制**
```bash
# 假设 memhog 由 Deployment 管理
kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=200Mi --requests=memory=100Mi
```
*依据*：当前 40Mi 限制明显不足，建议提高至 200Mi 以满足脚本运行需求。如果是测试负载，应考虑优化或停止该脚本。

**2. [优先] 调整 Prometheus Pod 的内存限制**
```bash
# 通过 Helm 升级 observability release，修改 values 中的资源限制
# 首先，获取当前的 values 文件
helm get values observability -n xnet > prometheus-values.yaml
# 编辑 prometheus-values.yaml，增加 prometheus 容器的内存限制，例如：
# prometheus:
#   resources:
#     limits:
#       memory: 2Gi
#     requests:
#       memory: 1Gi
# 然后执行升级
helm upgrade observability -n xnet -f prometheus-values.yaml
```
*依据*：当前 512Mi 限制已被持续占用 99%，是性能瓶颈和 OOM 根源，建议至少提升至 1Gi 或 2Gi。

**3. [可选] 临时调整 Prometheus 就绪探针超时时间**
```bash
# 此命令通常需要修改 PodTemplate (如 StatefulSet)，建议通过上述 Helm 升级一并修改。
# 在 values.yaml 中调整：
# prometheus:
#   readinessProbe:
#     timeoutSeconds: 15
```
*目的*：在内存压力未彻底解决前，避免因短暂的性能波动导致就绪探针失败。

### 后续优化
1.  **应用优化**：审查 `memhog` 应用的真实用途，若非必要，应修复其内存泄漏代码。
2.  **Prometheus 配置优化**：审查 Prometheus 配置（`retention`、`scrape_interval`、`rules`），降低其内存占用。
3.  **监控与告警**：为关键 Pod 设置内存使用率告警（例如 >85%），以便提前干预。
4.  **资源规划**：定期使用 `kubectl describe pod` 和 Prometheus 监控，对比资源 `requests/limits` 与实际使用量，进行合理调整。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 memhog Pod 状态 | `kubectl get pod memhog-578d9b5ffd-56mqz -n aiops-e2e` | STATUS: `Running`，RESTARTS 不再增加 |
| 2. 确认 Prometheus Pod 状态 | `kubectl get pod prometheus-observability-prometheus-0 -n xnet` | READY: `1/1`，RESTARTS 不再增加 |
| 3. 检查 Prometheus 内存使用 | Prometheus 查询：`container_memory_working_set_bytes{pod="prometheus-observability-prometheus-0", namespace="xnet"}` / 1024 / 1024 | 数值稳定在新的限制值（如 2Gi）的 80% 以下 |
| 4. 检查节点内存 | `kubectl describe node node1 node2` | `Allocated resources` 部分显示内存压力正常 |

## ⚠️ 注意事项
- 调整 `memhog` 资源限制后，若其脚本持续泄漏内存，最终仍可能耗尽新限制，需从根本上解决应用问题。
- Prometheus 内存需求会随监控数据量增长而增加，扩容后仍需持续关注。
- 所有修复操作（特别是 Helm 升级）建议在维护窗口进行，并确保有回滚方案。

---

## 📊 性能统计

├─ 总耗时: 6.5m
├─ 问题定位: 158.6s (41%) ✅
├─ 证据链采集: 148.6s (38%) ✅
├─ 根因分析: 82.0s (21%) ✅
├─ 汇总总结: 0.0s (0%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 18 次
```

📋 诊断追踪

- **参考 Runbook**: L2 Pod OOMKilled (Exit Code 137)
- **工具调用**: 18 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
