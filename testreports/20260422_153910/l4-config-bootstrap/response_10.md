======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 257494e5a270421f]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先做一次轻量状态检查，看看集群当前的整体健康状况。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 5 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 0 completed, 1 in progress, 4 pending

[ ] [2] 检查异常 Pod
[ ] [3] 检查 Service/Endpoints
[ ] [4] 获取通用健康参考 runbook

   💭 [问题定位] 先获取通用健康参考 runbook，同时检查 Node 和 Pod 状态。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS       AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     ap
   💭 [问题定位] 好，节点全部 Ready，没有异常节点。让我看看那个异常 Pod 的情况。

发现一个异常 Pod：`aiops-e2e/appconfigfail-7649c79dc5-q4zjz` 处于 `CrashLoopBackOff` 状态。让我查看详情。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 5 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 2 completed, 1 in progress, 2 pending

[ ] [3] 检查 Service/Endpoints
[ ] [5] 综合分析并定层
[~] [2] 检查异常 Pod
[✓] [1] 检
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [问题定位] 这个 Pod 的情况很明确了。让我再看看 Service/Endpoints 状态，确保没有其他问题。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 5 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 3 completed, 1 in progress, 1 pending

[ ] [5] 综合分析并定层
[~] [3] 检查 Service/Endpoints
[✓] [1] 检查 Node 状态
[✓] [2]
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                     ENDPOINTS                                                                    AGE    LABELS
aaa           test1-redis-headless                    
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                     TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                                                                                               
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                               READY   UP-TO-DATE   AVAILABLE   AGE     CONTAINERS                                                                      IMAGES                        
   💭 [问题定位] 这个 Pod 的场景非常明确——它的 label 是 `l4-scenario=config-bootstrap-fail`，描述信息里也打印了 `FATAL: missing required APP_BOOT_MODE` 和 `exit 42`，这是典型的应用层启动配置校验失败。让我查看一下相关的 runbook。
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
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 情况已经非常清楚了。让我看看那三个没有 Endpoints 的 Service 是否属于当前活跃问题。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:              test2-redis-master
Namespace:         xnet
Labels:            app=redis
                   app.kubernetes.io/managed-by=Helm
                   chart=redis-10.5.7
                  
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:              test1-redis-master
Namespace:         aaa
Labels:            app=redis
                   app.kubernetes.io/managed-by=Helm
                   chart=redis-10.5.7
                   
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Command failed (exit 1):
kubectl describe service nfs-client -n default
Error from server (NotFound): services "nfs-client" not found

   💭 [问题定位] 好的，让我查一下是否有对应的 Redis Pod 存在。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_find_resource
   💭 [问题定位] 调用工具: kubectl_find_resource
   💭 [问题定位] 工具结果: kubectl_find_resource (success)
      📄 Command failed (exit 1):
kubectl get -A --show-labels -o wide pods | grep -i 'test1-redis'

   💭 [问题定位] 工具结果: kubectl_find_resource (success)
      📄 Command failed (exit 1):
kubectl get -A --show-labels -o wide pods | grep -i 'test2-redis'

   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 No resources found in aaa namespace.
   💭 [问题定位] 这些 Redis 的 Service 没有对应的 Pod，但是这些是 Helm 安装的遗留资源（test1/test2 看起来是测试用途），Pod 不存在所以 Endpoints 为空是正常的——这不是当前活跃的故障。

现在让我查看日志确认一下那个异常 Pod 的情况。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS        AGE     IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-7649c79dc5-q4zjz   0/1     CrashLoop
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 Investigation plan updated with 5 tasks.

# CURRENT INVESTIGATION TASKS

**Task Status**: 5 completed, 0 in progress, 0 pending

[✓] [1] 检查 Node 状态
[✓] [2] 检查异常 Pod
[✓] [3] 检查 Service/Endpoints
[✓] [4
   💭 [问题定位] ## 集群健康分析结果

### 检查概要

| 检查面 | 状态 |
|--------|------|
| **节点 (3个)** | ✅ 全部 Ready |
| **控制面组件** | ✅ etcd / apiserver / scheduler / controller-manager 正常 |
| **CoreDNS** | ✅ 2个 Pod Running，有 Endpoints |
| **Calico** | ✅ 3个 calico-node Running |
| **kube-proxy** | ✅ 正常 |
| **NFS Provisioner** | ✅ Running |
| **PVC/PV** | 未发现挂载相关异常 |
| **主要业务 Deployment** | ✅ 均正常 |

### 发现的异常

**1 个异常 Pod（L4 - 应用层）**

| 项目 | 内容 |
|------|------|
| **Pod** | `aiops-e2e/appconfigfail-7649c79dc5-q4zjz` |
| **状态** | `CrashLoopBackOff`（已重启 5 次） |
| **Exit Code** | 42（业务退出码，非 OOM） |
| **根因** | 启动配置校验失败：**缺少必填环境变量 `APP_BOOT_MODE`** |
| **日志关键信息** | `FATAL: missing required APP_BOOT_MODE` / `FATAL: business config validation failed before server startup` |
| **场景** | 应用在 bootstrap 阶段检测到配置缺失后主动退出，属于典型的 **L4 应用层配置错误** |

### 非异常说明

- `aaa/test1-redis-*` 和 `xnet/test2-redis-*` Service 无 Endpoints → 对应 Pod 不存在，属于已废弃的测试 Helm release，非当前活跃故障
- `default/nfs-client` Service 不存在 → 仅 `nfs-client-provisioner` 存在，属于正常

### 最终结论

```json
{
  "layer": "L4",
  "layers": ["L4"],
  "layer_name": "应用层",
  "confidence": 0.95,
  "reasoning": "集群节点全部 Ready，控制面、网络插件、DNS 均正常。唯一活跃异常是 aiops-e2e 命名空间下 Pod CrashLoopBackOff，Exit Code 42，日志明确显示因缺少必填环境变量 APP_BOOT_MODE 导致业务配置校验失败后主动退出。属于应用层启动配置错误（L4）。",
  "key_entities": [
    {"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "Deployment", "value": "appconfigfail"}
  ],
  "possible_scenarios": ["L4 应用启动配置校验失败"]
}
```
   ✅ [问题定位] 完成 (1m 31.8s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=['L4 应用启动配置校验失败']
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Deployment", "value": "appconfigfail"}]
   reasoning=集群节点全部 Ready，控制面、网络插件、DNS 均正常。唯一活跃异常是 aiops-e2e 命名空间下 Pod CrashLoopBackOff，Exit Code 42，日志明确显示因缺少必填环境变量 APP_BOOT_MODE 导致业务配置校验失败后主动退出。属于应用层启动配置错误（L4）。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.95, "reasoning": "集群节点全部 Ready，控制面、网络插件、DNS 均正常。唯一活跃异常是 aiops-e2e 命名空间下 Pod CrashLoopBackOff，Exit Code 42，日志明确显示因缺少必填环境变量 APP_BOOT_MODE 导致业务配置校验失败后主动退出。属于应用层启动配置错误（L4）。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "Deployment", "value": "appconfigfail"}], "possible_scenarios": ["L4 应用启动配置校验失败"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 让我先检查集群的整体状况，然后聚焦于上游已定位的具体问题。

## 第一步：输出 JSON 证据采集计划

根据上游定位结果，问题已明确为 **L4 应用启动配置校验失败**。我来制定证据采集计划，深入验证根因。

```json
{
  "layer": "L4",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "获取异常 Pod 的详细描述信息",
      "level": "critical",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e",
      "purpose": "确认 Pod 状态、Exit Code、重启次数、Events"
    },
    {
      "id": "e2",
      "description": "查看 Pod 最近一次退出的容器日志",
      "level": "critical",
      "tool": "kubectl logs (with --previous)",
      "command": "kubectl logs appconfigfail-7649c79dc5-q4zjz -n aiops-e2e --previous",
      "purpose": "获取应用启动时输出的 FATAL 错误日志"
    },
    {
      "id": "e3",
      "description": "获取 Deployment YAML 配置",
      "level": "critical",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get deployment appconfigfail -n aiops-e2e -o yaml",
      "purpose": "检查 Deployment 中是否缺失 APP_BOOT_MODE 环境变量"
    },
    {
      "id": "e4",
      "description": "获取 Pod 的 YAML 配置（当前状态）",
      "level": "important",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e -o yaml",
      "purpose": "查看容器定义中的 env 和 containerStatuses 状态"
    },
    {
      "id": "e5",
      "description": "检查命名空间中是否存在 ConfigMap 或 Secret 可能提供该变量",
      "level": "important",
      "tool": "kubectl_get_by_kind_in_namespace",
      "command": "kubectl get cm,secret -n aiops-e2e",
      "purpose": "确认是否已有相关配置资源"
    },
    {
      "id": "e6",
      "description": "查看 Pod 相关 Events",
      "level": "important",
      "tool": "kubectl_events",
      "command": "kubectl events --for pod/appconfigfail-7649c79dc5-q4zjz -n aiops-e2e",
      "purpose": "获取 CrashLoopBackOff 相关事件时间线"
    }
  ],
  "collection_strategy": "先采集 critical 级证据确认根因，再采集 important 级补充上下文"
}
```

## 第二步：逐项采集证据
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    deployment.kubernetes.io/revision: "1"
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"apps/v1","kind":"D
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 NAME                         DATA   AGE   LABELS
configmap/kube-root-ca.crt   1      88d   <none>
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [证据链采集] 现在让我查看当前 Pod 的日志（最新一次退出）和之前一次的日志：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: v1
kind: Pod
metadata:
  annotations:
    cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f
    cni.projectcalico.org/podIP: 172.16.104.57
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: appl
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: appl
   💭 [证据链采集] 所有证据已采集完毕。以下是完整的诊断报告。

---

## 第三步：证据采集结果汇总

| 证据 ID | 工具 | 结果 | 状态 |
|---------|------|------|------|
| **e1** | kubectl describe pod | ✅ Pod Status: `CrashLoopBackOff`, Exit Code: 42, 已重启 6 次 | ✅ 已采集 |
| **e2** | kubectl logs --previous | ✅ 日志明确输出 `FATAL: missing required APP_BOOT_MODE` | ✅ 已采集 |
| **e3** | kubectl get deployment -o yaml | ✅ Deployment 中 `env:` 字段为 **`<none>`**，未定义任何环境变量 | ✅ 已采集 |
| **e4** | kubectl get pod -o yaml | ✅ Pod 的 container spec 中 `env:` 为空 | ✅ 已采集 |
| **e5** | kubectl get cm,secret -n aiops-e2e | ✅ 仅有 `kube-root-ca.crt` ConfigMap，无业务配置 | ✅ 已采集 |
| **e6** | kubectl events (含于 describe) | ✅ Events 显示 BackOff 反复重启，无其他异常事件 | ✅ 已采集 |

---

## 📋 诊断结论

### 问题确认
**L4 应用启动配置校验失败 — 根因已确认**

| 项目 | 内容 |
|------|------|
| **异常 Pod** | `appconfigfail-7649c79dc5-q4zjz` (aiops-e2e) |
| **状态** | `CrashLoopBackOff`，已重启 6 次 |
| **退出码** | **42**（业务主动退出，非系统级错误） |
| **容器镜像** | `busybox:1.36`（已存在本地，无需拉取） |
| **节点** | node2 (10.2.0.50) |

### 根因分析

**Pod 启动脚本在 bootstrap 阶段检查环境变量 `APP_BOOT_MODE`，发现该变量为空，主动输出 FATAL 日志并以 Exit Code 42 退出。**

关键证据链：
1. **日志证据** — 容器日志（当前 & 上一次）一致输出：
   ```
   L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
   L4_LAYER_APPLICATION: true
   L4_SCENARIO: config-bootstrap-fail
   L4_ERROR_TYPE: application-config-validation
   FATAL: missing required APP_BOOT_MODE
   FATAL: business config validation failed before server startup
   ```
2. **配置证据** — Deployment `appconfigfail` 的容器 `app` **没有定义任何环境变量**（`env: <none>`），`APP_BOOT_MODE` 完全缺失
3. **行为证据** — Exit Code 42 是脚本中 `exit 42` 主动退出，不是 OOMKilled（137）或系统信号终止

### 影响范围
- **仅限** `aiops-e2e` 命名空间的 `appconfigfail` Deployment
- 不影响集群中其他 Pod、节点、网络或存储组件

### ✅ 修复建议

> ⚠️ **注意**：以下为建议方案，请由有权限的人员执行

为 Deployment `appconfigfail` 添加环境变量 `APP_BOOT_MODE`：

```bash
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production
```

或编辑 Deployment 手动添加：
```yaml
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: APP_BOOT_MODE
          value: "production"
```

添加后 Pod 将自动滚动更新，应用启动配置校验通过，Pod 应能正常运行。
   ✅ [证据链采集] 完成 (37.0s)
   📤 → 下游数据: evidence_items=6/8
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "获取异常 Pod 的详细描述信息", "level": "critical", "tool": "kubectl_describe", "command": "kubectl describe pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e", "purpose": "确认 Pod 状态、Exit Code、重启次数、Events"}, {"id": "e2", "description": "查看 Pod 最近一次退出的容器日志", "level": "critical", "tool": "kubectl logs (with --previous)", "command": "kubectl logs appconfigfail-7649c79dc5-q4zjz -n aiops-e2e --previous", "purpose": "获取应用启动时输出的 FATAL 错误日志"}, {"id": "e3", "description": "获取 Deployment YAML 配置", "level": "critical", "tool": "kubectl_get_yaml", "command": "kubectl get deployment appconfigfail -n aiops-e2e -o yaml", "purpose": "检查 Deployment 中是否缺失 APP_BOOT_MODE 环境变量"}, {"id": "e4", "description": "获取 Pod 的 YAML 配置（当前状态）", "level": "important", "tool": "kubectl_get_yaml", "command": "kubectl get pod appconfigfail-7649c79dc5-q4zjz -n aiops-e2e -o yaml", "purpose": "查看容器定义中的 env 和 containerStatuses 状态"}, {"id": "e5", "description": "检查命名空间中是否存在 ConfigMap 或 Secret 可能提供该变量", "level": "important", "tool": "kubectl_get_by_kind_in_namespace", "command": "kubectl get cm,secret -n aiops-e2e", "purpose": "确认是否已有相关配置资源"}, {"id": "e6", "description": "查看 Pod 相关 Events", "level": "important", "tool": "kubectl_events", "command": "kubectl events --for pod/appconfigfail-7649c79dc5-q4zjz -n aiops-e2e", "purpose": "获取 CrashLoopBackOff 相关事件时间线"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_yaml", "data": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  annotations:\n    deployment.kubernetes.io/revision: \"1\"\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":\"apps/v1\",\"kind\":\"Deployment\",\"metadata\":{\"annotations\":{},\"labels\":{\"l4-scenario\":\"config-bootstrap-fail\"},\"name\":\"appconfigfail\",\"namespace\":\"aiops-e2e\"},\"spec\":{\"replicas\":1,\"selector\":{\"matchLabels\":{\"app\":\"appconfigfail\"}},\"template\":{\"metadata\":{\"labels\":{\"app\":\"appconfigfail\",\"l4-scenario\":\"config-bootstrap-fail\"}},\"spec\":{\"containers\":[{\"args\":[\"echo \\\"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\\"\\necho \\\"L4_LAYER_APPLICATION: true\\\"\\necho \\\"L4_SCENARIO: config-bootstrap-fail\\\"\\necho \\\"L4_ERROR_TYPE: application-config-validation\\\"\\nif [ -z \\\"${APP_BOOT_MODE:-}\\\" ]; then\\n  echo \\\"FATAL: missing required APP_BOOT_MODE\\\"\\n  echo \\\"FATAL: business config validation failed before server startup\\\"\\n  exit 42\\nfi\\necho \\\"unexpected success\\\"\\nexit 1\\n\"],\"command\":[\"sh\",\"-c\"],\"image\":\"busybox:1.36\",\"imagePullPolicy\":\"Never\",\"name\":\"app\"}]}}}}\n  creationTimestamp: \"2026-04-22T07:38:39Z\"\n  generation: 1\n  labels:\n    l4-scenario: config-bootstrap-fail\n  name: appconfigfail\n  namespace: aiops-e2e\n  resourceVersion: \"46413881\"\n  uid: 99cdabf8-f7bb-4fde-be0d-23711032bd1e\nspec:\n  progressDeadlineSeconds: 600\n  replicas: 1\n  revisionHistoryLimit: 10\n  selector:\n    matchLabels:\n      app: appconfigfail\n  strategy:\n    rollingUpdate:\n      maxSurge: 25%\n      maxUnavailable: 25%\n    type: RollingUpdate\n  template:\n    metadata:\n      creationTimestamp: null\n      labels:\n        app: appconfigfail\n        l4-scenario: config-bootstrap-fail\n    spec:\n      containers:\n      - args:\n        - |\n          echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n          echo \"L4_LAYER_APPLICATION: true\"\n          echo \"L4_SCENARIO: config-bootstrap-fail\"\n          echo \"L4_ERROR_TYPE: application-config-validation\"\n          if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n            echo \"FATAL: missing required APP_BOOT_MODE\"\n            echo \"FATAL: business config validation failed before server startup\"\n            exit 42\n          fi\n          echo \"unexpected success\"\n          exit 1\n        command:\n        - sh\n        - -c\n        image: busybox:1.36\n        imagePullPolicy: Never\n        name: app\n        resources: {}\n        terminationMessagePath: /dev/termination-log\n        terminationMessagePolicy: File\n      dnsPolicy: ClusterFirst\n      restartPolicy: Always\n      schedulerName: default-scheduler\n      securityContext: {}\n      terminationGracePeriodSeconds: 30\nstatus:\n  conditions:\n  - lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    lastUpdateTime: \"2026-04-22T07:38:39Z\"\n    message: Deployment does not have minimum availability.\n    reason: MinimumReplicasUnavailable\n    status: \"False\"\n    type: Available\n  - lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    lastUpdateTime: \"2026-04-22T07:38:39Z\"\n    message: ReplicaSet \"appconfigfail-7649c79dc5\" is progressing.\n    reason: ReplicaSetUpdated\n    status: \"True\"\n    type: Progressing\n  observedGeneration: 1\n  replicas: 1\n  unavailableReplicas: 1\n  updatedReplicas: 1", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_namespace", "data": "NAME                         DATA   AGE   LABELS\nconfigmap/kube-root-ca.crt   1      88d   <none>", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             appconfigfail-7649c79dc5-q4zjz\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             node2/10.2.0.50\nStart Time:       Wed, 22 Apr 2026 07:38:39 +0000\nLabels:           app=appconfigfail\n                  l4-scenario=config-bootstrap-fail\n                  pod-template-hash=7649c79dc5\nAnnotations:      cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f\n                  cni.projectcalico.org/podIP: 172.16.104.57/32\n                  cni.projectcalico.org/podIPs: 172.16.104.57/32\n                  k8s.v1.cni.cncf.io/network-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\n                  k8s.v1.cni.cncf.io/networks-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\nStatus:           Running\nIP:               172.16.104.57\nIPs:\n  IP:           172.16.104.57\nControlled By:  ReplicaSet/appconfigfail-7649c79dc5\nContainers:\n  app:\n    Container ID:  containerd://85acccef8f77944b76229da211c445d9ddff897d1ac39a4a21f747951ce1f2f0\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      sh\n      -c\n    Args:\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n      \n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n      Started:      Wed, 22 Apr 2026 07:44:18 +0000\n      Finished:     Wed, 22 Apr 2026 07:44:18 +0000\n    Ready:          False\n    Restart Count:  6\n    Environment:    <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-zndsj (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             False \n  ContainersReady   False \n  PodScheduled      True \nVolumes:\n  kube-api-access-zndsj:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              <none>\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason          Age                   From               Message\n  ----     ------          ----                  ----               -------\n  Normal   Scheduled       6m9s                  default-scheduler  Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n  Normal   AddedInterface  6m9s                  multus             Add eth0 [172.16.104.57/32] from k8s-pod-network\n  Normal   Pulled          4m43s (x5 over 6m9s)  kubelet            Container image \"busybox:1.36\" already present on machine\n  Normal   Created         4m43s (x5 over 6m9s)  kubelet            Created container app\n  Normal   Started         4m43s (x5 over 6m9s)  kubelet            Started container app\n  Warning  BackOff         68s (x24 over 6m7s)   kubelet            Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f\n    cni.projectcalico.org/podIP: 172.16.104.57/32\n    cni.projectcalico.org/podIPs: 172.16.104.57/32\n    k8s.v1.cni.cncf.io/network-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.104.57\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n    k8s.v1.cni.cncf.io/networks-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.104.57\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n  creationTimestamp: \"2026-04-22T07:38:39Z\"\n  generateName: appconfigfail-7649c79dc5-\n  labels:\n    app: appconfigfail\n    l4-scenario: config-bootstrap-fail\n    pod-template-hash: 7649c79dc5\n  name: appconfigfail-7649c79dc5-q4zjz\n  namespace: aiops-e2e\n  ownerReferences:\n  - apiVersion: apps/v1\n    blockOwnerDeletion: true\n    controller: true\n    kind: ReplicaSet\n    name: appconfigfail-7649c79dc5\n    uid: 7b8b69a7-397c-4d54-b9c7-818ef9ad399f\n  resourceVersion: \"46414957\"\n  uid: 77ea5d65-2a07-47e0-b606-3f03812dcc6a\nspec:\n  containers:\n  - args:\n    - |\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n    command:\n    - sh\n    - -c\n    image: busybox:1.36\n    imagePullPolicy: Never\n    name: app\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-zndsj\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  nodeName: node2\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0\n  restartPolicy: Always\n  schedulerName: default-scheduler\n  securityContext: {}\n  serviceAccount: default\n  serviceAccountName: default\n  terminationGracePeriodSeconds: 30\n  tolerations:\n  - effect: NoExecute\n    key: node.kubernetes.io/not-ready\n    operator: Exists\n    tolerationSeconds: 300\n  - effect: NoExecute\n    key: node.kubernetes.io/unreachable\n    operator: Exists\n    tolerationSeconds: 300\n  volumes:\n  - name: kube-api-access-zndsj\n    projected:\n      defaultMode: 420\n      sources:\n      - serviceAccountToken:\n          expirationSeconds: 3607\n          path: token\n      - configMap:\n          items:\n          - key: ca.crt\n            path: ca.crt\n          name: kube-root-ca.crt\n      - downwardAPI:\n          items:\n          - fieldRef:\n              apiVersion: v1\n              fieldPath: metadata.namespace\n            path: namespace\nstatus:\n  conditions:\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    status: \"True\"\n    type: Initialized\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    message: 'containers with unready status: [app]'\n    reason: ContainersNotReady\n    status: \"False\"\n    type: Ready\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    message: 'containers with unready status: [app]'\n    reason: ContainersNotReady\n    status: \"False\"\n    type: ContainersReady\n  - lastProbeTime: null\n    lastTransitionTime: \"2026-04-22T07:38:39Z\"\n    status: \"True\"\n    type: PodScheduled\n  containerStatuses:\n  - containerID: containerd://85acccef8f77944b76229da211c445d9ddff897d1ac39a4a21f747951ce1f2f0\n    image: docker.io/library/busybox:1.36\n    imageID: sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    lastState:\n      terminated:\n        containerID: containerd://85acccef8f77944b76229da211c445d9ddff897d1ac39a4a21f747951ce1f2f0\n        exitCode: 42\n        finishedAt: \"2026-04-22T07:44:18Z\"\n        reason: Error\n        startedAt: \"2026-04-22T07:44:18Z\"\n    name: app\n    ready: false\n    restartCount: 6\n    started: false\n    state:\n      waiting:\n        message: back-off 5m0s restarting failed container=app pod=appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)\n        reason: CrashLoopBackOff\n  hostIP: 10.2.0.50\n  phase: Running\n  podIP: 172.16.104.57\n  podIPs:\n  - ip: 172.16.104.57\n  qosClass: BestEffort\n  startTime: \"2026-04-22T07:38:39Z\"", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\nL4_LAYER_APPLICATION: true\\nL4_SCENARIO: config-bootstrap-fail\\nL4_ERROR_TYPE: application-config-validation\\nFATAL: missing required APP_BOOT_MODE\\nFATAL: business config validation failed before server startup\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\nL4_LAYER_APPLICATION: true\\nL4_SCENARIO: config-bootstrap-fail\\nL4_ERROR_TYPE: application-config-validation\\nFATAL: missing required APP_BOOT_MODE\\nFATAL: business config validation failed before server startup\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}], "llm_analysis": "所有证据已采集完毕。以下是完整的诊断报告。\n\n---\n\n## 第三步：证据采集结果汇总\n\n| 证据 ID | 工具 | 结果 | 状态 |\n|---------|------|------|------|\n| **e1** | kubectl describe pod | ✅ Pod Status: `CrashLoopBackOff`, Exit Code: 42, 已重启 6 次 | ✅ 已采集 |\n| **e2** | kubectl logs --previous | ✅ 日志明确输出 `FATAL: missing required APP_BOOT_MODE` | ✅ 已采集 |\n| **e3** | kubectl get deployment -o yaml | ✅ Deployment 中 `env:` 字段为 **`<none>`**，未定义任何环境变量 | ✅ 已采集 |\n| **e4** | kubectl get pod -o yaml | ✅ Pod 的 container spec 中 `env:` 为空 | ✅ 已采集 |\n| **e5** | kubectl get cm,secret -n aiops-e2e | ✅ 仅有 `kube-root-ca.crt` ConfigMap，无业务配置 | ✅ 已采集 |\n| **e6** | kubectl events (含于 describe) | ✅ Events 显示 BackOff 反复重启，无其他异常事件 | ✅ 已采集 |\n\n---\n\n## 📋 诊断结论\n\n### 问题确认\n**L4 应用启动配置校验失败 — 根因已确认**\n\n| 项目 | 内容 |\n|------|------|\n| **异常 Pod** | `appconfigfail-7649c79dc5-q4zjz` (aiops-e2e) |\n| **状态** | `CrashLoopBackOff`，已重启 6 次 |\n| **退出码** | **42**（业务主动退出，非系统级错误） |\n| **容器镜像** | `busybox:1.36`（已存在本地，无需拉取） |\n| **节点** | node2 (10.2.0.50) |\n\n### 根因分析\n\n**Pod 启动脚本在 bootstrap 阶段检查环境变量 `APP_BOOT_MODE`，发现该变量为空，主动输出 FATAL 日志并以 Exit Code 42 退出。**\n\n关键证据链：\n1. **日志证据** — 容器日志（当前 & 上一次）一致输出：\n   ```\n   L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\n   L4_LAYER_APPLICATION: true\n   L4_SCENARIO: config-bootstrap-fail\n   L4_ERROR_TYPE: application-config-validation\n   FATAL: missing required APP_BOOT_MODE\n   FATAL: business config validation failed before server startup\n   ```\n2. **配置证据** — Deployment `appconfigfail` 的容器 `app` **没有定义任何环境变量**（`env: <none>`），`APP_BOOT_MODE` 完全缺失\n3. **行为证据** — Exit Code 42 是脚本中 `exit 42` 主动退出，不是 OOMKilled（137）或系统信号终止\n\n### 影响范围\n- **仅限** `aiops-e2e` 命名空间的 `appconfigfail` Deployment\n- 不影响集群中其他 Pod、节点、网络或存储组件\n\n### ✅ 修复建议\n\n> ⚠️ **注意**：以下为建议方案，请由有权限的人员执行\n\n为 Deployment `appconfigfail` 添加环境变量 `APP_BOOT_MODE`：\n\n```bash\nkubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production\n```\n\n或编辑 Deployment 手动添加：\n```yaml\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        env:\n        - name: APP_BOOT_MODE\n          value: \"production\"\n```\n\n添加后 Pod 将自动滚动更新，应用启动配置校验通过，Pod 应能正常运行。", "collection_summary": "计划 8 项，实际采集 6 项，未采集 2 项，完整度 75%", "evidence_inventory": [{"id": "e1", "description": "获取异常 Pod 的详细描述信息", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "查看 Pod 最近一次退出的容器日志", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "获取 Deployment YAML 配置", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "获取 Pod 的 YAML 配置（当前状态）", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "检查命名空间中是否存在 ConfigMap 或 Secret 可能提供该变量", "level": "important", "collected": false, "source": "planned"}, {"id": "e6", "description": "查看 Pod 相关 Events", "level": "important", "collected": false, "source": "planned"}, {"id": "extra_4", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_5", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": ["e5(检查命名空间中是否存在 ConfigMap 或 Secret 可能提供该变量): 已规划但工具执行失败或无匹配结果", "e6(查看 Pod 相关 Events): 已规划但工具执行失败或无匹配结果"], "early_stop": {"triggered": false, "reason": "", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/8 项, 完整度: 75%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (10m 13.6s)
   📤 → 下游数据: root_cause=详见 LLM 原始分析
   confidence=60%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_analysis": [], "causal_chain": {}, "root_cause": "详见 LLM 原始分析", "llm_raw_analysis": "```json\n{\n  \"phenomenon\": \"Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，Deployment appconfigfail 0/1 Available，集群其余组件均健康\",\n  \"evidence_inventory\": [\n    {\n      \"id\": \"e1\",\n      \"content\": \"Pod 状态为 CrashLoopBackOff，Exit Code 42，重启 6 次\",\n      \"source\": \"kubectl describe pod\",\n      \"reliability\": \"高\"\n    },\n    {\n      \"id\": \"e2\",\n      \"content\": \"容器日志输出：FATAL: missing required APP_BOOT_MODE\",\n      \"source\": \"kubectl logs --previous\",\n      \"reliability\": \"高\"\n    },\n    {\n      \"id\": \"e3\",\n      \"content\": \"Deployment YAML 中 env 字段为 <none>，未定义任何环境变量\",\n      \"source\": \"kubectl get deployment -o yaml\",\n      \"reliability\": \"高\"\n    },\n    {\n      \"id\": \"e4\",\n      \"content\": \"Pod YAML 中 container spec 的 env 字段为空\",\n      \"source\": \"kubectl get pod -o yaml\",\n      \"reliability\": \"高\"\n    },\n    {\n      \"id\": \"e5\",\n      \"content\": \"命名空间 aiops-e2e 仅有 kube-root-ca.crt ConfigMap，无业务配置 ConfigMap 或 Secret\",\n      \"source\": \"kubectl get cm,secret -n aiops-e2e\",\n      \"reliability\": \"高\"\n    },\n    {\n      \"id\": \"e6\",\n      \"content\": \"Events 显示 Back-off restarting failed container，无其他异常事件\",\n      \"source\": \"kubectl describe pod events\",\n      \"reliability\": \"高\"\n    },\n    {\n      \"id\": \"e7\",\n      \"content\": \"启动脚本输出：L4_CONFIG_BOOTSTRAP_FAIL, L4_LAYER_APPLICATION, L4_SCENARIO: config-bootstrap-fail, L4_ERROR_TYPE: application-config-validation\",\n      \"source\": \"run_bash_command 工具采集\",\n      \"reliability\": \"高\"\n    }\n  ],\n  \"evidence_analysis\": [\n    {\n      \"evidence_id\": \"e1\",\n      \"raw_data\": \"Exit Code: 42, Restart Count: 6, State: Waiting (CrashLoopBackOff), Last State: Terminated (Error)\",\n      \"interpretation\": \"Pod 主动以退出码 42 终止，该退出码非系统信号（如 137 OOM），表明是业务逻辑主动退出。重启 6 次后进入 CrashLoopBackOff，说明问题持续存在未解决。\"\n    },\n    {\n      \"evidence_id\": \"e2\",\n      \"raw_data\": \"日志内容：\\\"FATAL: missing required APP_BOOT_MODE\\\", \\\"FATAL: business config validation failed before server startup\\\"\",\n      \"interpretation\": \"容器启动脚本在执行 bootstrap 配置校验时，检测到 APP_BOOT_MODE 环境变量为空，判定为致命错误并主动终止。\"\n    },\n    {\n      \"evidence_id\": \"e3\",\n      \"raw_data\": \"Deployment spec.template.s", "confidence": 0.6, "confidence_reason": "LLM 未输出结构化 JSON，使用原始分析文本", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 详见 LLM 原始分析
   置信度: 60%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (37.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6060 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 13m 0.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群整体状态** | **基本健康** — 3 节点全部 Ready，控制面组件运行正常 |
| **发现的问题** | **1 个应用层异常** — Pod `appconfigfail-7649c79dc5-q4zjz` 处于 `CrashLoopBackOff` |
| **问题层级** | L4 - 应用层 |
| **问题分类** | 应用启动配置校验失败 (Config Bootstrap Fail) |
| **影响范围** | 仅限于 `aiops-e2e` 命名空间的 `appconfigfail` Deployment，**不影响集群其他组件** |
| **置信度** | 高 (95%) |
| **证据完整度** | 6/8 (75%) |

**快速结论**：您的集群基础设施（节点、网络、存储、控制面）一切正常。唯一的异常是 `aiops-e2e` 命名空间中的一个测试 Pod `appconfigfail`，其启动脚本因缺少必需的 `APP_BOOT_MODE` 环境变量而主动退出。这是一个**业务配置问题**，而非集群故障。

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | `appconfigfail-7649c79dc5-q4zjz` |
| Namespace | `aiops-e2e` |
| Node | `node2` (10.2.0.50) |
| Deployment | `appconfigfail` — **0/1 Available** |
| 容器镜像 | `busybox:1.36` |
| 退出码 | **42**（业务主动退出，非系统级错误） |
| 重启次数 | **6 次**（持续增长中） |
| Pod 状态 | `CrashLoopBackOff` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod` | `State: Waiting (CrashLoopBackOff)`, `Last State: Terminated (Error)`, `Exit Code: 42`, `Restart Count: 6` | Pod 主动以退出码 42 终止，业务逻辑主动退出 |
| 2 | 容器日志 | `kubectl logs --previous` | `FATAL: missing required APP_BOOT_MODE`<br>`FATAL: business config validation failed before server startup` | 启动脚本明确报告缺少必需的环境变量 |
| 3 | Deployment 配置 | `kubectl get deployment -o yaml` | `containers[0].env: <none>` — 未定义任何环境变量 | Deployment 中完全缺失 `APP_BOOT_MODE` 环境变量 |
| 4 | Pod 配置 | `kubectl get pod -o yaml` | `containers[0].env:` 字段为空 | Pod 运行时未注入任何环境变量 |
| 5 | 命名空间 ConfigMap/Secret | `kubectl get cm,secret -n aiops-e2e` | 仅有 `configmap/kube-root-ca.crt`，无业务配置 | 不存在可注入 `APP_BOOT_MODE` 的 ConfigMap 或 Secret |
| 6 | Pod Events | `kubectl describe pod` 中的 Events | `Back-off restarting failed container` (x24) | Kubelet 反复重启失败容器，无其他异常事件 |

### 证据关联分析

- **证据 #2 + #3 印证**：容器日志输出 `FATAL: missing required APP_BOOT_MODE`，Deployment 的 `env` 字段为 `<none>` → 直接确认根因是环境变量缺失
- **证据 #1 + #6 印证**：Exit Code 42 + BackOff 重启 → 问题持续未解决，且每次启动都因相同原因失败
- **证据链**：Deployment 未配置 `APP_BOOT_MODE` → 容器启动脚本 `if [ -z "${APP_BOOT_MODE:-}" ]` 检测为空 → 输出 FATAL 日志 → `exit 42` 主动终止 → Pod 进入 CrashLoopBackOff

### 启动脚本关键代码（来自 Deployment YAML）

```bash
if [ -z "${APP_BOOT_MODE:-}" ]; then
  echo "FATAL: missing required APP_BOOT_MODE"
  echo "FATAL: business config validation failed before server startup"
  exit 42
fi
```

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| 未单独查询 ConfigMap/Secret | important | 不影响根因判断（已通过 Deployment 和 Pod YAML 确认无 env 注入） |
| 未单独查询 Pod Events | important | 不影响根因判断（Events 已包含在 describe 输出中） |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Deployment appconfigfail 的容器定义中未配置 APP_BOOT_MODE        │
│ 环境变量（env: <none>）                                         │
│ 证据 #3: kubectl get deployment -o yaml                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动脚本执行 if [ -z "${APP_BOOT_MODE:-}" ] 检查             │
│ → 环境变量为空/未设置 → 判定为致命业务配置错误                  │
│ 证据 #2: 日志输出 "FATAL: missing required APP_BOOT_MODE"       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 脚本主动执行 exit 42 终止进程                                   │
│ 证据 #1: Exit Code 42, Reason: Error                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，Deployment 0/1 Available             │
│ 证据 #6: Events 显示 Back-off restarting failed container       │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（日志明确输出 `FATAL: missing required APP_BOOT_MODE`）和证据 #3（Deployment 中 `env` 字段为空），问题的根本原因是 **Deployment `appconfigfail` 未配置必需的 `APP_BOOT_MODE` 环境变量**，导致容器启动脚本在业务配置校验阶段主动退出（Exit Code 42）。

这是一个**L4 应用层配置问题**，而非集群基础设施故障。

**置信度**：高 (95%)
- ✅ 日志直接输出缺失变量名称
- ✅ Deployment YAML 确认 `env` 为空
- ✅ 命名空间内无相关 ConfigMap/Secret
- ✅ Exit Code 42 与脚本中 `exit 42` 完全匹配

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [推荐] 使用 kubectl set env 添加环境变量**
```bash
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production
```
*依据*：添加缺失的环境变量，触发 Pod 滚动更新

**2. [备选] 编辑 Deployment 手动添加**
```bash
kubectl edit deployment appconfigfail -n aiops-e2e
```
在 `spec.template.spec.containers[0].env` 中添加：
```yaml
        env:
        - name: APP_BOOT_MODE
          value: "production"
```

**3. 验证修复**
```bash
# 查看 Pod 是否启动成功
kubectl get pod -n aiops-e2e -l app=appconfigfail

# 查看最新 Pod 日志
kubectl logs -n aiops-e2e -l app=appconfigfail
```

### 后续优化
1. **配置标准化**：将 `APP_BOOT_MODE` 等通用配置纳入 ConfigMap，统一管理
2. **启动脚本优化**：在启动脚本中提供更清晰的错误提示，指出缺失变量名称和预期值范围
3. **健康检查**：为 Deployment 配置 Readiness Probe，避免类似问题影响服务可用性感知

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 添加环境变量 | `kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production` | `deployment.apps/appconfigfail env updated` |
| 2. 等待 Pod 重建 | `kubectl get pod -n aiops-e2e -w -l app=appconfigfail` | 旧 Pod 终止 → 新 Pod 进入 `Running` 状态 |
| 3. 确认 Pod 状态 | `kubectl get pod -n aiops-e2e -l app=appconfigfail` | `STATUS: Running`, `READY: 1/1` |
| 4. 确认 Deployment | `kubectl get deployment appconfigfail -n aiops-e2e` | `AVAILABLE: 1` |
| 5. 查看容器日志 | `kubectl logs -n aiops-e2e -l app=appconfigfail` | 不再有 FATAL 日志，启动正常完成 |

---

## ⚠️ 注意事项

- 当前 `APP_BOOT_MODE` 的值设为 `production`，请根据应用实际要求调整（如 `staging`、`development` 等）
- 本问题为测试场景（标签 `l4-scenario=config-bootstrap-fail`），不影响集群中其他服务
- 如果集群中有其他 Pod 依赖类似环境变量，建议统一检查其配置

---

## 📊 性能统计

├─ 总耗时: 13.0m
├─ 问题定位: 91.8s (12%) ✅
├─ 证据链采集: 37.0s (5%) ✅
├─ 根因分析: 613.6s (79%) ✅
├─ 汇总总结: 37.9s (5%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 25 次
```

📋 诊断追踪

- **参考 Runbook**: private-k8s-health-reference, l4-config-bootstrap-fail
- **工具调用**: 25 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
