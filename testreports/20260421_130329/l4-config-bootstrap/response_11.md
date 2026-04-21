======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 0a9a0074075b48af]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来帮您诊断集群的问题。首先让我检查集群的整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     a
   💭 [问题定位] 我看到有一个 Pod 处于 CrashLoopBackOff 状态：`appconfigfail-7649c79dc5-pcxt8`。让我检查这个 Pod 的详细信息来诊断问题。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-pcxt8
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Tue, 21 Apr 2026 04:32:19
   💭 [问题定位] 现在让我检查节点状态，确保没有其他基础设施问题：
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   208d   v1.26.8  
   💭 [问题定位] 让我检查这个 Pod 的标签，看看是否有相关的 runbook 可以参考：
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS       AGE   IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-7649c79dc5-pcxt8   0/1     CrashLoopBac
   💭 [问题定位] 我看到这个 Pod 有标签 `l4-scenario=config-bootstrap-fail`，这看起来是一个 L4 应用层配置启动失败的场景。让我获取相关的 runbook：
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
   💭 [问题定位] 现在让我检查这个 Pod 的日志来确认问题：
   💭 [问题定位] 调用工具: run_bash_command
   💭 [问题定位] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: appl
   💭 [问题定位] 基于我的诊断，现在可以确定问题的层级。让我总结一下：

1. 用户意图是诊断集群问题，属于诊断模式
2. 发现一个 Pod 处于 CrashLoopBackOff 状态：`appconfigfail-7649c79dc5-pcxt8`
3. `kubectl describe` 显示：
   - Last State: Terminated, Reason: Error, Exit Code: 42
   - 不是 OOMKilled (Exit Code 137)
   - 不是 Evicted
   - 不是 ImagePullBackOff
4. Pod 日志显示明确的 L4 应用层错误：
   - "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config"
   - "FATAL: missing required APP_BOOT_MODE"
   - "FATAL: business config validation failed before server startup"
5. 所有节点状态为 Ready，没有基础设施问题
6. Pod 标签显示 `l4-scenario=config-bootstrap-fail`，与 runbook 匹配

```json
{
  "layer": "L4",
  "layers": ["L4"],
  "layer_name": "应用层",
  "confidence": 0.95,
  "reasoning": "Pod appconfigfail-7649c79dc5-pcxt8 处于 CrashLoopBackOff 状态，describe 显示 Exit Code 42（非 137），Last State: Terminated, Reason: Error。日志显示明确的 L4 应用层配置校验失败：'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'。无 OOMKilled、Evicted 或 ImagePullBackOff 迹象，符合 L4 应用启动配置校验失败场景。",
  "key_entities": [
    {"type": "Pod", "value": "appconfigfail-7649c79dc5-pcxt8"},
    {"type": "Namespace", "value": "aiops-e2e"},
    {"type": "ReplicaSet", "value": "appconfigfail-7649c79dc5"}
  ],
  "possible_scenarios": [
    {"scenario": "应用启动配置校验失败", "probability": "高", "reason": "日志显示缺少必填配置 APP_BOOT_MODE，应用在启动阶段主动退出"},
    {"scenario": "环境变量配置缺失", "probability": "高", "reason": "应用启动时缺少必要的业务配置参数"}
  ]
}
```
   ✅ [问题定位] 完成 (45.4s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '应用启动配置校验失败', 'probability': '高', 'reason': '日志显示缺少必填配置 APP_BOOT_MODE，应用在启动阶段主动退出'}, {'scenario': '环境变量配置缺失', 'probability': '高', 'reason': '应用启动时缺少必要的业务配置参数'}]
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-pcxt8"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "ReplicaSet", "value": "appconfigfail-7649c79dc5"}]
   reasoning=Pod appconfigfail-7649c79dc5-pcxt8 处于 CrashLoopBackOff 状态，describe 显示 Exit Code 42（非 137），Last State: Terminated, Reason: Error。日志显示明确的 L4 应用层配置校验失败：'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'。无 OOMKilled、Evicted 或 ImagePullBackOff 迹象，符合 L4 应用启动配置校验失败场景。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.95, "reasoning": "Pod appconfigfail-7649c79dc5-pcxt8 处于 CrashLoopBackOff 状态，describe 显示 Exit Code 42（非 137），Last State: Terminated, Reason: Error。日志显示明确的 L4 应用层配置校验失败：'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'。无 OOMKilled、Evicted 或 ImagePullBackOff 迹象，符合 L4 应用启动配置校验失败场景。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-pcxt8"}, {"type": "Namespace", "value": "aiops-e2e"}, {"type": "ReplicaSet", "value": "appconfigfail-7649c79dc5"}], "possible_scenarios": [{"scenario": "应用启动配置校验失败", "probability": "高", "reason": "日志显示缺少必填配置 APP_BOOT_MODE，应用在启动阶段主动退出"}, {"scenario": "环境变量配置缺失", "probability": "高", "reason": "应用启动时缺少必要的业务配置参数"}]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据您的问题，我需要先了解集群的整体状态。让我检查集群中的关键资源状态。
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     a
   💭 [证据链采集] 现在让我检查节点状态：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   208d   v1.26.8  
   💭 [证据链采集] 让我检查是否有其他异常资源：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                               READY   UP-TO-DATE   AVAILABLE   AGE    CONTAINERS                                                                      IMAGES                         
   💭 [证据链采集] 现在让我检查异常Pod的详细信息：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-pcxt8
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Tue, 21 Apr 2026 04:32:19
   💭 [证据链采集] 让我获取Pod的日志来确认问题：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: appl
   💭 [证据链采集] 现在让我检查相关的Deployment配置：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    deployment.kubernetes.io/revision: "1"
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"apps/v1","kind":"D
   💭 [证据链采集] 让我检查集群中是否有其他异常资源：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE   LAST SEEN   TYPE      REASON              OBJECT                                SUBOBJECT                                      SOURCE                                        MESSAGE        
   💭 [证据链采集] 现在让我检查集群资源使用情况，使用Prometheus查询：
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"instance":"10.2.0.49:9100"},"value":[1776748269.531,"9.445425934104613"]},{"metric":{"instance":"10.2.0.48:9100"},"value":[17767
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"container":"node-exporter","endpoint":"http-metrics","instance":"10.2.0.49:9100","job":"node-exporter","namespace":"xnet","pod":
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"container":"node-exporter","device":"/dev/mapper/ubuntu--vg-ubuntu--lv","endpoint":"http-metrics","fstype":"ext4","instance":"10
   💭 [证据链采集] 基于以上采集的证据，我现在可以分析集群的整体状态：

```json
{
  "layer": "L4",
  "evidence_plan": [
    {
      "id": "e1",
      "description": "检查集群中所有Pod的状态",
      "level": "critical",
      "tool": "kubectl_get_by_kind_in_cluster",
      "command": "kubectl get pods -A",
      "purpose": "确认集群中是否有异常Pod"
    },
    {
      "id": "e2",
      "description": "检查节点状态",
      "level": "critical",
      "tool": "kubectl_get_by_kind_in_cluster",
      "command": "kubectl get nodes",
      "purpose": "确认所有节点是否Ready"
    },
    {
      "id": "e3",
      "description": "检查异常Pod的详细信息",
      "level": "important",
      "tool": "kubectl_describe",
      "command": "kubectl describe pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e",
      "purpose": "分析Pod失败的具体原因"
    },
    {
      "id": "e4",
      "description": "获取异常Pod的日志",
      "level": "important",
      "tool": "run_bash_command",
      "command": "kubectl logs appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e",
      "purpose": "查看应用启动失败的具体错误信息"
    },
    {
      "id": "e5",
      "description": "检查Deployment配置",
      "level": "optional",
      "tool": "kubectl_get_yaml",
      "command": "kubectl get deployment appconfigfail -n aiops-e2e -o yaml",
      "purpose": "确认应用配置是否正确"
    },
    {
      "id": "e6",
      "description": "检查集群事件",
      "level": "optional",
      "tool": "kubectl_get_by_kind_in_cluster",
      "command": "kubectl get events -A",
      "purpose": "查看是否有其他异常事件"
    },
    {
      "id": "e7",
      "description": "检查集群资源使用情况",
      "level": "optional",
      "tool": "execute_prometheus_instant_query",
      "command": "查询CPU、内存、磁盘使用率",
      "purpose": "确认集群资源是否充足"
    }
  ],
  "collection_strategy": "先检查集群整体状态，然后聚焦于异常Pod，最后检查资源使用情况"
}
```

## 采集结果汇总

### ✅ 已采集的证据：

1. **集群Pod状态**：发现1个异常Pod `appconfigfail-7649c79dc5-pcxt8` 处于 `CrashLoopBackOff` 状态，重启12次。其他所有Pod（共47个）均正常运行。

2. **节点状态**：所有3个节点（master, node1, node2）状态均为 `Ready`，集群基础设施正常。

3. **异常Pod详细信息**：
   - Pod状态：`Running`（但容器状态为 `CrashLoopBackOff`）
   - 容器状态：`Waiting`，原因：`CrashLoopBackOff`
   - 上次终止状态：`Terminated`，原因：`Error`，退出码：`42`
   - 重启次数：12次
   - 容器命令：检查环境变量 `APP_BOOT_MODE`，如果缺失则退出

4. **Pod日志**：明确显示应用启动配置校验失败：
   ```
   L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config
   L4_LAYER_APPLICATION: true
   L4_SCENARIO: config-bootstrap-fail
   L4_ERROR_TYPE: application-config-validation
   FATAL: missing required APP_BOOT_MODE
   FATAL: business config validation failed before server startup
   ```

5. **Deployment配置**：确认Deployment配置中确实没有设置 `APP_BOOT_MODE` 环境变量，容器启动脚本会检查该变量。

6. **集群事件**：只有正常调度事件和Pod重启的BackOff警告，无其他异常。

7. **资源使用情况**：
   - CPU使用率：master 13.96%，node1 9.45%，node2 3.05%（正常范围）
   - 内存使用率：master 26.35%，node1 20.29%，node2 8.84%（正常范围）
   - 磁盘使用率：master 83.43%（较高），node1 52.97%，node2 54.89%

### ❌ 未采集的证据：无

## 集群问题分析

### 🔴 **主要问题**：

1. **L4应用层配置错误**：
   - Pod `appconfigfail-7649c79dc5-pcxt8` 因缺少必需的环境变量 `APP_BOOT_MODE` 而启动失败
   - 应用在启动阶段进行配置校验，发现配置缺失后主动退出（退出码42）
   - 符合典型的L4应用启动配置校验失败场景

### 🟡 **需要注意的问题**：

1. **master节点磁盘使用率较高**：83.43%，接近警戒线，需要关注磁盘空间。

### 🟢 **正常状态**：

1. **集群基础设施健康**：所有节点Ready，核心组件（etcd、kube-apiserver、kube-controller-manager、kube-scheduler、coredns、calico）正常运行
2. **资源使用正常**：CPU和内存使用率均在合理范围内
3. **其他应用正常**：除测试Pod外，所有业务应用（包括监控栈、AIOps系统等）均正常运行

## 建议的修复方案

### 针对L4应用配置错误：
1. **检查并添加缺失的环境变量**：
   ```bash
   # 查看当前Deployment配置
   kubectl get deployment appconfigfail -n aiops-e2e -o yaml
   
   # 更新Deployment添加环境变量
   kubectl patch deployment appconfigfail -n aiops-e2e -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","env":[{"name":"APP_BOOT_MODE","value":"production"}]}]}}}}'
   ```

2. **或者删除这个测试Deployment**（如果是测试用途）：
   ```bash
   kubectl delete deployment appconfigfail -n aiops-e2e
   ```

### 针对master节点磁盘使用率高：
1. **清理不必要的日志和临时文件**
2. **考虑扩容磁盘或迁移部分工作负载到其他节点**
3. **设置磁盘使用率监控告警**

## 结论
集群整体健康状况良好，主要问题是**一个测试应用因配置缺失而启动失败**（L4应用层问题）。这看起来像是一个故意的测试场景（标签 `l4-scenario=config-bootstrap-fail` 也表明了这一点）。集群基础设施、其他业务应用和资源使用均正常。
   ✅ [证据链采集] 完成 (1m 35.0s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan": [{"id": "e1", "description": "检查集群中所有Pod的状态", "level": "critical", "tool": "kubectl_get_by_kind_in_cluster", "command": "kubectl get pods -A", "purpose": "确认集群中是否有异常Pod"}, {"id": "e2", "description": "检查节点状态", "level": "critical", "tool": "kubectl_get_by_kind_in_cluster", "command": "kubectl get nodes", "purpose": "确认所有节点是否Ready"}, {"id": "e3", "description": "检查异常Pod的详细信息", "level": "important", "tool": "kubectl_describe", "command": "kubectl describe pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e", "purpose": "分析Pod失败的具体原因"}, {"id": "e4", "description": "获取异常Pod的日志", "level": "important", "tool": "run_bash_command", "command": "kubectl logs appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e", "purpose": "查看应用启动失败的具体错误信息"}, {"id": "e5", "description": "检查Deployment配置", "level": "optional", "tool": "kubectl_get_yaml", "command": "kubectl get deployment appconfigfail -n aiops-e2e -o yaml", "purpose": "确认应用配置是否正确"}, {"id": "e6", "description": "检查集群事件", "level": "optional", "tool": "kubectl_get_by_kind_in_cluster", "command": "kubectl get events -A", "purpose": "查看是否有其他异常事件"}, {"id": "e7", "description": "检查集群资源使用情况", "level": "optional", "tool": "execute_prometheus_instant_query", "command": "查询CPU、内存、磁盘使用率", "purpose": "确认集群资源是否充足"}], "tool_results": [], "tool_data": [{"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE     NAME                                                READY   STATUS             RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\naiops-e2e     appconfigfail-7649c79dc5-pcxt8                      0/1     CrashLoopBackOff   12 (107s ago)    38m    172.16.104.55    node2    <none>           <none>            app=appconfigfail,l4-scenario=config-bootstrap-fail,pod-template-hash=7649c79dc5\naiops         aiops-copilot-74c886ddb-lk8tb                       1/1     Running            0                49m    172.16.104.22    node2    <none>           <none>            app=aiops-copilot,pod-template-hash=74c886ddb\ndefault       dns-test-existing                                   1/1     Running            0                23h    172.16.166.148   node1    <none>           <none>            run=dns-test-existing\ndefault       exec-test                                           1/1     Running            0                25h    172.16.104.8     node2    <none>           <none>            run=exec-test\ndefault       network-test-from-running                           1/1     Running            0                23h    172.16.104.50    node2    <none>           <none>            run=network-test-from-running\ndefault       nfs-client-provisioner-6fcd4994c9-lczf6             1/1     Running            4 (3d22h ago)    84d    172.16.104.41    node2    <none>           <none>            app=nfs-client-provisioner,pod-template-hash=6fcd4994c9\nkube-system   calico-kube-controllers-6c67f9d475-2xcb7            1/1     Running            4 (3d22h ago)    26d    172.16.166.133   node1    <none>           <none>            k8s-app=calico-kube-controllers,pod-template-hash=6c67f9d475\nkube-system   calico-node-4kp26                                   1/1     Running            12 (3d22h ago)   182d   10.2.0.48        master   <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-d2dhp                                   1/1     Running            13 (3d22h ago)   182d   10.2.0.50        node2    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-mnrjs                                   1/1     Running            12 (3d22h ago)   182d   10.2.0.49        node1    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   coredns-777df594b8-j4857                            1/1     Running            4 (3d22h ago)    26d    172.16.166.129   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   coredns-777df594b8-s8r4n                            1/1     Running            4 (3d22h ago)    26d    172.16.166.185   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   etcd-master                                         1/1     Running            13 (3d22h ago)   208d   10.2.0.48        master   <none>           <none>            component=etcd,tier=control-plane\nkube-system   kube-apiserver-master                               1/1     Running            13 (3d22h ago)   208d   10.2.0.48        master   <none>           <none>            component=kube-apiserver,tier=control-plane\nkube-system   kube-controller-manager-master                      1/1     Running            36 (3d22h ago)   208d   10.2.0.48        master   <none>           <none>            component=kube-controller-manager,tier=control-plane\nkube-system   kube-multus-ds-rnvbg                                1/1     Running            12 (3d22h ago)   182d   10.2.0.49        node1    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-sc2jn                                1/1     Running            4 (3d22h ago)    84d    10.2.0.48        master   <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-x7h9s                                1/1     Running            13 (3d22h ago)   182d   10.2.0.50        node2    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-proxy-69zzr                                    1/1     Running            4 (3d22h ago)    26d    10.2.0.50        node2    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-bblvc                                    1/1     Running            4 (3d22h ago)    26d    10.2.0.49        node1    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-wbh4k                                    1/1     Running            4 (3d22h ago)    26d    10.2.0.48        master   <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-scheduler-master                               1/1     Running            38 (3d22h ago)   208d   10.2.0.48        master   <none>           <none>            component=kube-scheduler,tier=control-plane\nmcp           mcp-server-manager-8677f6896c-d4mr9                 1/1     Running            0                19h    172.16.104.59    node2    <none>           <none>            app=mcp-server-manager,pod-template-hash=8677f6896c\nxnet          alertmanager-observability-alertmanager-0           2/2     Running            8 (3d22h ago)    21d    172.16.166.161   node1    <none>           <none>            alertmanager=observability-alertmanager,app.kubernetes.io/instance=observability-alertmanager,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=alertmanager,app.kubernetes.io/version=0.28.1,controller-revision-hash=alertmanager-observability-alertmanager-6c9cfbf844,statefulset.kubernetes.io/pod-name=alertmanager-observability-alertmanager-0\nxnet          api-server-6bd6bf8d6f-27svp                         1/1     Running            4 (3d22h ago)    21d    172.16.219.106   master   <none>           <none>            app=api-server,pod-template-hash=6bd6bf8d6f\nxnet          deepflow-agent-pcknn                                1/1     Running            9 (3d22h ago)    21d    172.16.166.181   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-trc8k                                1/1     Running            7 (3d22h ago)    18d    172.16.104.7     node2    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-whn22                                1/1     Running            8 (3d22h ago)    21d    172.16.219.97    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          elasticsearch-master-0                              1/1     Running            4 (3d22h ago)    21d    172.16.219.109   master   <none>           <none>            app=elasticsearch-master,chart=observability,controller-revision-hash=elasticsearch-master-695ff9864f,release=observability,statefulset.kubernetes.io/pod-name=elasticsearch-master-0\nxnet          ham-p9dxv                                           1/1     Running            14 (3d22h ago)   176d   172.16.104.21    node2    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-qzjg5                                           1/1     Running            4 (3d22h ago)    84d    172.16.219.112   master   <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-wt9kh                                           1/1     Running            13 (3d22h ago)   176d   172.16.166.187   node1    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          lgtm-5dc5c67d5f-sc286                               1/1     Running            4 (3d22h ago)    21d    172.16.166.151   node1    <none>           <none>            app=lgtm,pod-template-hash=5dc5c67d5f\nxnet          observability-clickhouse-0                          1/1     Running            4 (3d22h ago)    21d    172.16.166.137   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=clickhouse,app=deepflow,component=clickhouse,controller-revision-hash=observability-clickhouse-75b8d58ccc,statefulset.kubernetes.io/pod-name=observability-clickhouse-0\nxnet          observability-deepflow-app-654fcfbfbf-q8st6         1/1     Running            4 (3d22h ago)    21d    172.16.166.160   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-app,pod-template-hash=654fcfbfbf\nxnet          observability-deepflow-server-774dd6c5b7-9c998      1/1     Running            14 (3d22h ago)   21d    172.16.166.135   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-server,pod-template-hash=774dd6c5b7\nxnet          observability-filebeat-ffwsp                        1/1     Running            4 (3d22h ago)    21d    172.16.219.80    master   <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-m58xw                        1/1     Running            5 (3d22h ago)    21d    172.16.166.134   node1    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-w6gtr                        1/1     Running            5 (3d22h ago)    18d    172.16.104.53    node2    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-grafana-58bf9cfd6f-ndsxr              4/4     Running            36 (3d22h ago)   21d    172.16.166.144   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=grafana,app.kubernetes.io/version=12.0.2,helm.sh/chart=grafana-9.2.7,pod-template-hash=58bf9cfd6f\nxnet          observability-kepler-2sgrr                          1/1     Running            6 (3d22h ago)    21d    10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-7scjm                          1/1     Running            7 (3d22h ago)    21d    10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-ggstf                          1/1     Running            8 (3d22h ago)    18d    10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kibana-65d7c45f6d-tm4vv               1/1     Running            4 (3d22h ago)    21d    172.16.166.191   node1    <none>           <none>            app=observability-kibana,pod-template-hash=65d7c45f6d,release=observability\nxnet          observability-kube-state-metrics-798986b8b7-6z2dq   1/1     Running            4 (3d22h ago)    21d    172.16.219.65    master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=kube-state-metrics,app.kubernetes.io/part-of=kube-state-metrics,app.kubernetes.io/version=2.15.0,helm.sh/chart=kube-state-metrics-5.37.0,pod-template-hash=798986b8b7,release=observability\nxnet          observability-mysql-764f9d5966-wh2bc                1/1     Running            4 (3d22h ago)    21d    172.16.219.98    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=mysql,app=deepflow,component=mysql,pod-template-hash=764f9d5966\nxnet          observability-operator-d4495dc86-69lgw              1/1     Running            4 (3d22h ago)    21d    172.16.166.182   node1    <none>           <none>            app.kubernetes.io/component=prometheus-operator,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=observability-prometheus-operator,app.kubernetes.io/part-of=observability,app.kubernetes.io/version=1.0.2,app=observability-operator,chart=observability-1.0.2,heritage=Helm,pod-template-hash=d4495dc86,release=observability\nxnet          observability-prometheus-node-exporter-lj75r        1/1     Running            4 (3d22h ago)    21d    10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-qp2qd        1/1     Running            4 (3d22h ago)    18d    10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-wnbb8        1/1     Running            4 (3d22h ago)    21d    10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-telegraf-79f45d86-4kzkm               1/1     Running            4 (3d22h ago)    21d    172.16.219.113   master   <none>           <none>            app.kubernetes.io/component=telegraf,app.kubernetes.io/instance=observability,app.kubernetes.io/name=observability,pod-template-hash=79f45d86\nxnet          prometheus-observability-prometheus-0               2/2     Running            16 (3d22h ago)   21d    172.16.166.142   node1    <none>           <none>            app.kubernetes.io/instance=observability-prometheus,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=prometheus,app.kubernetes.io/version=3.4.1,controller-revision-hash=prometheus-observability-prometheus-9467b46f7,operator.prometheus.io/name=observability-prometheus,operator.prometheus.io/shard=0,prometheus=observability-prometheus,statefulset.kubernetes.io/pod-name=prometheus-observability-prometheus-0\nxnet          xnet-agent-568f547566-jdsgp                         1/1     Running            4 (3d22h ago)    107d   172.16.104.40    node2    <none>           <none>            app=xnet-agent,pod-template-hash=568f547566", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   208d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          208d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          208d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE     NAME                               READY   UP-TO-DATE   AVAILABLE   AGE    CONTAINERS                                                                      IMAGES                                                                                                                                                                                                                                           SELECTOR                                                                                                             LABELS\naiops-e2e     appconfigfail                      0/1     1            0           38m    app                                                                             busybox:1.36                                                                                                                                                                                                                                     app=appconfigfail                                                                                                    l4-scenario=config-bootstrap-fail\naiops         aiops-copilot                      1/1     1            1           49m    aiops-copilot                                                                   xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.29                                                                                                                                                                                            app=aiops-copilot                                                                                                    <none>\ndefault       nfs-client-provisioner             1/1     1            1           207d   nfs-client-provisioner                                                          registry.cn-beijing.aliyuncs.com/xngczl/nfs-subdir-external-provisione:v4.0.0                                                                                                                                                                    app=nfs-client-provisioner                                                                                           app=nfs-client-provisioner\nkube-system   calico-kube-controllers            1/1     1            1           182d   calico-kube-controllers                                                         xnet.registry.io:8443/k8s/calico/kube-controllers:v3.26.1                                                                                                                                                                                        k8s-app=calico-kube-controllers                                                                                      k8s-app=calico-kube-controllers\nkube-system   coredns                            2/2     2            2           208d   coredns                                                                         xnet.registry.io:8443/k8s/registry.k8s.io/coredns:v1.9.3                                                                                                                                                                                         k8s-app=kube-dns                                                                                                     k8s-app=kube-dns\nmcp           mcp-server-manager                 1/1     1            1           19h    mcp-server-manager                                                              xnet.registry.io:8443/xnet-cloud/mcp-server-manager:7.0.6                                                                                                                                                                                        app=mcp-server-manager                                                                                               app=mcp-server-manager\nxnet          api-server                         1/1     1            1           21d    api-server                                                                      xnet.registry.io:8443/observability/apiserver:v1.0                                                                                                                                                                                               app=api-server                                                                                                       app.kubernetes.io/managed-by=Helm,app=api-server\nxnet          lgtm                               1/1     1            1           21d    lgtm                                                                            xnet.registry.io:8443/observability/grafana/otel-lgtm:latest                                                                                                                                                                                     app=lgtm                                                                                                             app.kubernetes.io/managed-by=Helm\nxnet          observability-deepflow-app         1/1     1            1           21d    deepflow-app                                                                    xnet.registry.io:8443/observability/deepflow-ce/deepflow-app:v7.0                                                                                                                                                                                app=deepflow,app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,component=deepflow-app         app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=deepflow,app.kubernetes.io/version=1.0.0,app=deepflow,component=deepflow-app,helm.sh/chart=deepflow-1.0.2\nxnet          observability-deepflow-server      1/1     1            1           21d    deepflow-server                                                                 xnet.registry.io:8443/observability/deepflow-ce/deepflow-server:v7.0                                                                                                                                                                             app=deepflow,app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,component=deepflow-server      app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=deepflow,app.kubernetes.io/version=1.0.0,app=deepflow,helm.sh/chart=deepflow-1.0.2\nxnet          observability-grafana              1/1     1            1           21d    grafana-sc-dashboard,grafana-sc-datasources,grafana,fix-grafana-db-dashboards   xnet.registry.io:8443/observability/kiwigrid/k8s-sidecar:1.30.0,xnet.registry.io:8443/observability/kiwigrid/k8s-sidecar:1.30.0,xnet.registry.io:8443/observability/grafana/grafana:12.0.2,xnet.registry.io:8443/observability/python:3-alpine   app.kubernetes.io/instance=observability,app.kubernetes.io/name=grafana                                              app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=grafana,app.kubernetes.io/version=12.0.2,helm.sh/chart=grafana-9.2.7\nxnet          observability-kibana               1/1     1            1           21d    kibana                                                                          xnet.registry.io:8443/observability/kibana/kibana:8.5.1                                                                                                                                                                                          app=observability-kibana,release=observability                                                                       app.kubernetes.io/managed-by=Helm,app=observability-kibana,heritage=Helm,release=observability\nxnet          observability-kube-state-metrics   1/1     1            1           21d    kube-state-metrics                                                              xnet.registry.io:8443/observability/kube-state-metrics/kube-state-metrics:v2.15.0                                                                                                                                                                app.kubernetes.io/instance=observability,app.kubernetes.io/name=kube-state-metrics                                   app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=kube-state-metrics,app.kubernetes.io/part-of=kube-state-metrics,app.kubernetes.io/version=2.15.0,helm.sh/chart=kube-state-metrics-5.37.0,release=observability\nxnet          observability-mysql                1/1     1            1           21d    mysql                                                                           xnet.registry.io:8443/observability/mysql:8.0.39                                                                                                                                                                                                 app=deepflow,app.kubernetes.io/instance=observability,app.kubernetes.io/name=mysql,component=mysql                   app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=mysql,app.kubernetes.io/version=8.0.39,app=deepflow,component=mysql,helm.sh/chart=mysql-0.1.000\nxnet          observability-operator             1/1     1            1           21d    observability                                                                   xnet.registry.io:8443/observability/prometheus-operator/prometheus-operator:v0.83.0                                                                                                                                                              app=observability-operator,release=observability                                                                     app.kubernetes.io/component=prometheus-operator,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=observability-prometheus-operator,app.kubernetes.io/part-of=observability,app.kubernetes.io/version=1.0.2,app=observability-operator,chart=observability-1.0.2,heritage=Helm,release=observability\nxnet          observability-telegraf             1/1     1            1           21d    telegraf                                                                        xnet.registry.io:8443/observability/telegraf:1.32-alpine                                                                                                                                                                                         app.kubernetes.io/component=telegraf,app.kubernetes.io/instance=observability,app.kubernetes.io/name=observability   app.kubernetes.io/component=telegraf,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=observability,app.kubernetes.io/version=1.0.0,helm.sh/chart=observability-1.0.2\nxnet          xnet-agent                         1/1     1            1           207d   xnet-agent                                                                      xnet.registry.io:8443/xnet-cloud/xnet-agent:v0.0.1                                                                                                                                                                                               app=xnet-agent                                                                                                       app.kubernetes.io/managed-by=Helm,app=xnet-agent", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             appconfigfail-7649c79dc5-pcxt8\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             node2/10.2.0.50\nStart Time:       Tue, 21 Apr 2026 04:32:19 +0000\nLabels:           app=appconfigfail\n                  l4-scenario=config-bootstrap-fail\n                  pod-template-hash=7649c79dc5\nAnnotations:      cni.projectcalico.org/containerID: 356ed4d59f01a2ae22b47f393fe17f068bfdbfa10c1f028c2fb7c21b0ee82e7d\n                  cni.projectcalico.org/podIP: 172.16.104.55/32\n                  cni.projectcalico.org/podIPs: 172.16.104.55/32\n                  k8s.v1.cni.cncf.io/network-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.55\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\n                  k8s.v1.cni.cncf.io/networks-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.55\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\nStatus:           Running\nIP:               172.16.104.55\nIPs:\n  IP:           172.16.104.55\nControlled By:  ReplicaSet/appconfigfail-7649c79dc5\nContainers:\n  app:\n    Container ID:  containerd://fd327dbddc1fa7820a1826fad2a0a8b17f2cbc9e1017ff9ea3e24c0fce250d18\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      sh\n      -c\n    Args:\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n      \n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n      Started:      Tue, 21 Apr 2026 05:08:52 +0000\n      Finished:     Tue, 21 Apr 2026 05:08:52 +0000\n    Ready:          False\n    Restart Count:  12\n    Environment:    <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-q5pfk (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             False \n  ContainersReady   False \n  PodScheduled      True \nVolumes:\n  kube-api-access-q5pfk:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              <none>\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason          Age                    From               Message\n  ----     ------          ----                   ----               -------\n  Normal   Scheduled       38m                    default-scheduler  Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-pcxt8 to node2\n  Normal   AddedInterface  38m                    multus             Add eth0 [172.16.104.55/32] from k8s-pod-network\n  Normal   Pulled          36m (x5 over 38m)      kubelet            Container image \"busybox:1.36\" already present on machine\n  Normal   Created         36m (x5 over 38m)      kubelet            Created container app\n  Normal   Started         36m (x5 over 38m)      kubelet            Started container app\n  Warning  BackOff         3m29s (x165 over 38m)  kubelet            Back-off restarting failed container app in pod appconfigfail-7649c79dc5-pcxt8_aiops-e2e(8334b6d7-f468-48a1-b133-70fec47e9e2e)", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\nL4_LAYER_APPLICATION: true\\nL4_SCENARIO: config-bootstrap-fail\\nL4_ERROR_TYPE: application-config-validation\\nFATAL: missing required APP_BOOT_MODE\\nFATAL: business config validation failed before server startup\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}, {"tool": "kubectl_get_yaml", "data": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  annotations:\n    deployment.kubernetes.io/revision: \"1\"\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":\"apps/v1\",\"kind\":\"Deployment\",\"metadata\":{\"annotations\":{},\"labels\":{\"l4-scenario\":\"config-bootstrap-fail\"},\"name\":\"appconfigfail\",\"namespace\":\"aiops-e2e\"},\"spec\":{\"replicas\":1,\"selector\":{\"matchLabels\":{\"app\":\"appconfigfail\"}},\"template\":{\"metadata\":{\"labels\":{\"app\":\"appconfigfail\",\"l4-scenario\":\"config-bootstrap-fail\"}},\"spec\":{\"containers\":[{\"args\":[\"echo \\\"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\\"\\necho \\\"L4_LAYER_APPLICATION: true\\\"\\necho \\\"L4_SCENARIO: config-bootstrap-fail\\\"\\necho \\\"L4_ERROR_TYPE: application-config-validation\\\"\\nif [ -z \\\"${APP_BOOT_MODE:-}\\\" ]; then\\n  echo \\\"FATAL: missing required APP_BOOT_MODE\\\"\\n  echo \\\"FATAL: business config validation failed before server startup\\\"\\n  exit 42\\nfi\\necho \\\"unexpected success\\\"\\nexit 1\\n\"],\"command\":[\"sh\",\"-c\"],\"image\":\"busybox:1.36\",\"imagePullPolicy\":\"Never\",\"name\":\"app\"}]}}}}\n  creationTimestamp: \"2026-04-21T04:32:19Z\"\n  generation: 1\n  labels:\n    l4-scenario: config-bootstrap-fail\n  name: appconfigfail\n  namespace: aiops-e2e\n  resourceVersion: \"46124428\"\n  uid: e73ef214-b779-4104-8bb3-4bd4c04d6ab7\nspec:\n  progressDeadlineSeconds: 600\n  replicas: 1\n  revisionHistoryLimit: 10\n  selector:\n    matchLabels:\n      app: appconfigfail\n  strategy:\n    rollingUpdate:\n      maxSurge: 25%\n      maxUnavailable: 25%\n    type: RollingUpdate\n  template:\n    metadata:\n      creationTimestamp: null\n      labels:\n        app: appconfigfail\n        l4-scenario: config-bootstrap-fail\n    spec:\n      containers:\n      - args:\n        - |\n          echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n          echo \"L4_LAYER_APPLICATION: true\"\n          echo \"L4_SCENARIO: config-bootstrap-fail\"\n          echo \"L4_ERROR_TYPE: application-config-validation\"\n          if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n            echo \"FATAL: missing required APP_BOOT_MODE\"\n            echo \"FATAL: business config validation failed before server startup\"\n            exit 42\n          fi\n          echo \"unexpected success\"\n          exit 1\n        command:\n        - sh\n        - -c\n        image: busybox:1.36\n        imagePullPolicy: Never\n        name: app\n        resources: {}\n        terminationMessagePath: /dev/termination-log\n        terminationMessagePolicy: File\n      dnsPolicy: ClusterFirst\n      restartPolicy: Always\n      schedulerName: default-scheduler\n      securityContext: {}\n      terminationGracePeriodSeconds: 30\nstatus:\n  conditions:\n  - lastTransitionTime: \"2026-04-21T04:32:19Z\"\n    lastUpdateTime: \"2026-04-21T04:35:21Z\"\n    message: ReplicaSet \"appconfigfail-7649c79dc5\" has successfully progressed.\n    reason: NewReplicaSetAvailable\n    status: \"True\"\n    type: Progressing\n  - lastTransitionTime: \"2026-04-21T04:35:22Z\"\n    lastUpdateTime: \"2026-04-21T04:35:22Z\"\n    message: Deployment does not have minimum availability.\n    reason: MinimumReplicasUnavailable\n    status: \"False\"\n    type: Available\n  observedGeneration: 1\n  replicas: 1\n  unavailableReplicas: 1\n  updatedReplicas: 1", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE   LAST SEEN   TYPE      REASON              OBJECT                                SUBOBJECT                                      SOURCE                                        MESSAGE                                                                                                                                                        FIRST SEEN   COUNT   NAME                                              LABELS\naiops-e2e   38m         Normal    Scheduled           pod/appconfigfail-7649c79dc5-pcxt8                                                   default-scheduler, default-scheduler-master   Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-pcxt8 to node2                                                                                        38m          1       appconfigfail-7649c79dc5-pcxt8.18a84504b3303cb7   <none>\naiops-e2e   38m         Normal    AddedInterface      pod/appconfigfail-7649c79dc5-pcxt8                                                   multus                                        Add eth0 [172.16.104.55/32] from k8s-pod-network                                                                                                               38m          1       appconfigfail-7649c79dc5-pcxt8.18a84504d22b6eab   <none>\naiops-e2e   37m         Normal    Pulled              pod/appconfigfail-7649c79dc5-pcxt8    spec.containers{app}                           kubelet, node2                                Container image \"busybox:1.36\" already present on machine                                                                                                      38m          5       appconfigfail-7649c79dc5-pcxt8.18a84504d6f30195   <none>\naiops-e2e   37m         Normal    Created             pod/appconfigfail-7649c79dc5-pcxt8    spec.containers{app}                           kubelet, node2                                Created container app                                                                                                                                          38m          5       appconfigfail-7649c79dc5-pcxt8.18a84504d7754992   <none>\naiops-e2e   37m         Normal    Started             pod/appconfigfail-7649c79dc5-pcxt8    spec.containers{app}                           kubelet, node2                                Started container app                                                                                                                                          38m          5       appconfigfail-7649c79dc5-pcxt8.18a84504d9cc7e8a   <none>\naiops-e2e   3m42s       Warning   BackOff             pod/appconfigfail-7649c79dc5-pcxt8    spec.containers{app}                           kubelet, node2                                Back-off restarting failed container app in pod appconfigfail-7649c79dc5-pcxt8_aiops-e2e(8334b6d7-f468-48a1-b133-70fec47e9e2e)                                 38m          165     appconfigfail-7649c79dc5-pcxt8.18a8450526d30606   <none>\naiops-e2e   38m         Normal    SuccessfulCreate    replicaset/appconfigfail-7649c79dc5                                                  replicaset-controller                         Created pod: appconfigfail-7649c79dc5-pcxt8                                                                                                                    38m          1       appconfigfail-7649c79dc5.18a84504b2f034ce         <none>\naiops-e2e   38m         Normal    ScalingReplicaSet   deployment/appconfigfail                                                             deployment-controller                         Scaled up replica set appconfigfail-7649c79dc5 to 1                                                                                                            38m          1       appconfigfail.18a84504b2961760                    <none>\naiops       49m         Normal    Scheduled           pod/aiops-copilot-74c886ddb-lk8tb                                                    default-scheduler, default-scheduler-master   Successfully assigned aiops/aiops-copilot-74c886ddb-lk8tb to node2                                                                                             49m          1       aiops-copilot-74c886ddb-lk8tb.18a84467de522e51    <none>\naiops       49m         Normal    AddedInterface      pod/aiops-copilot-74c886ddb-lk8tb                                                    multus                                        Add eth0 [172.16.104.22/32] from k8s-pod-network                                                                                                               49m          1       aiops-copilot-74c886ddb-lk8tb.18a84467fbefad5c    <none>\naiops       49m         Normal    Pulled              pod/aiops-copilot-74c886ddb-lk8tb     spec.initContainers{fix-reports-permissions}   kubelet, node2                                Container image \"busybox:1.36\" already present on machine                                                                                                      49m          1       aiops-copilot-74c886ddb-lk8tb.18a8446800d8a2fa    <none>\naiops       49m         Normal    Created             pod/aiops-copilot-74c886ddb-lk8tb     spec.initContainers{fix-reports-permissions}   kubelet, node2                                Created container fix-reports-permissions                                                                                                                      49m          1       aiops-copilot-74c886ddb-lk8tb.18a8446801fb14aa    <none>\naiops       49m         Normal    Started             pod/aiops-copilot-74c886ddb-lk8tb     spec.initContainers{fix-reports-permissions}   kubelet, node2                                Started container fix-reports-permissions                                                                                                                      49m          1       aiops-copilot-74c886ddb-lk8tb.18a8446804ea4ced    <none>\naiops       49m         Normal    Pulling             pod/aiops-copilot-74c886ddb-lk8tb     spec.containers{aiops-copilot}                 kubelet, node2                                Pulling image \"xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.29\"                                                                                          49m          1       aiops-copilot-74c886ddb-lk8tb.18a8446813fbb705    <none>\naiops       49m         Normal    Pulled              pod/aiops-copilot-74c886ddb-lk8tb     spec.containers{aiops-copilot}                 kubelet, node2                                Successfully pulled image \"xnet.registry.io:8443/xnet-cloud/aiops-copilot:6.0.29\" in 45.409704567s (45.409715715s including waiting)                           49m          1       aiops-copilot-74c886ddb-lk8tb.18a84472a69d57a7    <none>\naiops       49m         Normal    Created             pod/aiops-copilot-74c886ddb-lk8tb     spec.containers{aiops-copilot}                 kubelet, node2                                Created container aiops-copilot                                                                                                                                49m          1       aiops-copilot-74c886ddb-lk8tb.18a84472a7de54c2    <none>\naiops       49m         Normal    Started             pod/aiops-copilot-74c886ddb-lk8tb     spec.containers{aiops-copilot}                 kubelet, node2                                Started container aiops-copilot                                                                                                                                49m          1       aiops-copilot-74c886ddb-lk8tb.18a84472aa6869b3    <none>\naiops       50m         Warning   FailedCreate        replicaset/aiops-copilot-74c886ddb                                                   replicaset-controller                         Error creating: pods \"aiops-copilot-74c886ddb-\" is forbidden: error looking up service account aiops/aiops-copilot: serviceaccount \"aiops-copilot\" not found   50m          1       aiops-copilot-74c886ddb.18a84467dd111c26          <none>\naiops       50m         Normal    SuccessfulCreate    replicaset/aiops-copilot-74c886ddb                                                   replicaset-controller                         Created pod: aiops-copilot-74c886ddb-lk8tb                                                                                                                     50m          1       aiops-copilot-74c886ddb.18a84467ddd39377          <none>\naiops       50m         Normal    Killing             pod/aiops-copilot-7bbb65cc8d-4z697    spec.containers{aiops-copilot}                 kubelet, node2                                Stopping container aiops-copilot                                                                                                                               50m          1       aiops-copilot-7bbb65cc8d-4z697.18a84467066bc81a   <none>\naiops       50m         Normal    ScalingReplicaSet   deployment/aiops-copilot                                                             deployment-controller                         Scaled up replica set aiops-copilot-74c886ddb to 1                                                                                                             50m          1       aiops-copilot.18a84467dc9d7ddb                    <none>", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"instance\":\"10.2.0.49:9100\"},\"value\":[1776748269.531,\"9.445425934104613\"]},{\"metric\":{\"instance\":\"10.2.0.48:9100\"},\"value\":[1776748269.531,\"13.963888888894072\"]},{\"metric\":{\"instance\":\"10.2.0.50:9100\"},\"value\":[1776748269.531,\"3.0469943079220907\"]}]}}", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"container\":\"node-exporter\",\"endpoint\":\"http-metrics\",\"instance\":\"10.2.0.49:9100\",\"job\":\"node-exporter\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-wnbb8\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776748274.376,\"20.289498007149497\"]},{\"metric\":{\"container\":\"node-exporter\",\"endpoint\":\"http-metrics\",\"instance\":\"10.2.0.48:9100\",\"job\":\"node-exporter\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-lj75r\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776748274.376,\"26.35412507668786\"]},{\"metric\":{\"container\":\"node-exporter\",\"endpoint\":\"http-metrics\",\"instance\":\"10.2.0.50:9100\",\"job\":\"node-exporter\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-qp2qd\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776748274.376,\"8.844982319797845\"]}]}}", "duration_s": 0}, {"tool": "execute_prometheus_instant_query", "data": "{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"container\":\"node-exporter\",\"device\":\"/dev/mapper/ubuntu--vg-ubuntu--lv\",\"endpoint\":\"http-metrics\",\"fstype\":\"ext4\",\"instance\":\"10.2.0.49:9100\",\"job\":\"node-exporter\",\"mountpoint\":\"/\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-wnbb8\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776748278.404,\"52.96579076047643\"]},{\"metric\":{\"container\":\"node-exporter\",\"device\":\"/dev/mapper/ubuntu--vg-ubuntu--lv\",\"endpoint\":\"http-metrics\",\"fstype\":\"ext4\",\"instance\":\"10.2.0.48:9100\",\"job\":\"node-exporter\",\"mountpoint\":\"/\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-lj75r\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776748278.404,\"83.43355585538943\"]},{\"metric\":{\"container\":\"node-exporter\",\"device\":\"/dev/mapper/ubuntu--vg-ubuntu--lv\",\"endpoint\":\"http-metrics\",\"fstype\":\"ext4\",\"instance\":\"10.2.0.50:9100\",\"job\":\"node-exporter\",\"mountpoint\":\"/\",\"namespace\":\"xnet\",\"pod\":\"observability-prometheus-node-exporter-qp2qd\",\"service\":\"observability-prometheus-node-exporter\"},\"value\":[1776748278.404,\"54.890197156921694\"]}]}}", "duration_s": 0}], "llm_analysis": "基于以上采集的证据，我现在可以分析集群的整体状态：\n\n```json\n{\n  \"layer\": \"L4\",\n  \"evidence_plan\": [\n    {\n      \"id\": \"e1\",\n      \"description\": \"检查集群中所有Pod的状态\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_get_by_kind_in_cluster\",\n      \"command\": \"kubectl get pods -A\",\n      \"purpose\": \"确认集群中是否有异常Pod\"\n    },\n    {\n      \"id\": \"e2\",\n      \"description\": \"检查节点状态\",\n      \"level\": \"critical\",\n      \"tool\": \"kubectl_get_by_kind_in_cluster\",\n      \"command\": \"kubectl get nodes\",\n      \"purpose\": \"确认所有节点是否Ready\"\n    },\n    {\n      \"id\": \"e3\",\n      \"description\": \"检查异常Pod的详细信息\",\n      \"level\": \"important\",\n      \"tool\": \"kubectl_describe\",\n      \"command\": \"kubectl describe pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e\",\n      \"purpose\": \"分析Pod失败的具体原因\"\n    },\n    {\n      \"id\": \"e4\",\n      \"description\": \"获取异常Pod的日志\",\n      \"level\": \"important\",\n      \"tool\": \"run_bash_command\",\n      \"command\": \"kubectl logs appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e\",\n      \"purpose\": \"查看应用启动失败的具体错误信息\"\n    },\n    {\n      \"id\": \"e5\",\n      \"description\": \"检查Deployment配置\",\n      \"level\": \"optional\",\n      \"tool\": \"kubectl_get_yaml\",\n      \"command\": \"kubectl get deployment appconfigfail -n aiops-e2e -o yaml\",\n      \"purpose\": \"确认应用配置是否正确\"\n    },\n    {\n      \"id\": \"e6\",\n      \"description\": \"检查集群事件\",\n      \"level\": \"optional\",\n      \"tool\": \"kubectl_get_by_kind_in_cluster\",\n      \"command\": \"kubectl get events -A\",\n      \"purpose\": \"查看是否有其他异常事件\"\n    },\n    {\n      \"id\": \"e7\",\n      \"description\": \"检查集群资源使用情况\",\n      \"level\": \"optional\",\n      \"tool\": \"execute_prometheus_instant_query\",\n      \"command\": \"查询CPU、内存、磁盘使用率\",\n      \"purpose\": \"确认集群资源是否充足\"\n    }\n  ],\n  \"collection_strategy\": \"先检查集群整体状态，然后聚焦于异常Pod，最后检查资源使用情况\"\n}\n```\n\n## 采集结果汇总\n\n### ✅ 已采集的证据：\n\n1. **集群Pod状态**：发现1个异常Pod `appconfigfail-7649c79dc5-pcxt8` 处于 `CrashLoopBackOff` 状态，重启12次。其他所有Pod（共47个）均正常运行。\n\n2. **节点状态**：所有3个节点（master, node1, node2）状态均为 `Ready`，集群基础设施正常。\n\n3. **异常Pod详细信息**：\n   - Pod状态：`Running`（但容器状态为 `CrashLoopBackOff`）\n   - 容器状态：`Waiting`，原因：`CrashLoopBackOff`\n   - 上次终止状态：`Terminated`，原因：`Error`，退出码：`42`\n   - 重启次数：12次\n   - 容器命令：检查环境变量 `APP_BOOT_MODE`，如果缺失则退出\n\n4. **Pod日志**：明确显示应用启动配置校验失败：\n   ```\n   L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\n   L4_LAYER_APPLICATION: true\n   L4_SCENARIO: config-bootstrap-fail\n   L4_ERROR_TYPE: application-config-validation\n   FATAL: missing required APP_BOOT_MODE\n   FATAL: business config validation failed before server startup\n   ```\n\n5. **Deployment配置**：确认Deployment配置中确实没有设置 `APP_BOOT_MODE` 环境变量，容器启动脚本会检查该变量。\n\n6. **集群事件**：只有正常调度事件和Pod重启的BackOff警告，无其他异常。\n\n7. **资源使用情况**：\n   - CPU使用率：master 13.96%，node1 9.45%，node2 3.05%（正常范围）\n   - 内存使用率：master 26.35%，node1 20.29%，node2 8.84%（正常范围）\n   - 磁盘使用率：master 83.43%（较高），node1 52.97%，node2 54.89%\n\n### ❌ 未采集的证据：无\n\n## 集群问题分析\n\n### 🔴 **主要问题**：\n\n1. **L4应用层配置错误**：\n   - Pod `appconfigfail-7649c79dc5-pcxt8` 因缺少必需的环境变量 `APP_BOOT_MODE` 而启动失败\n   - 应用在启动阶段进行配置校验，发现配置缺失后主动退出（退出码42）\n   - 符合典型的L4应用启动配置校验失败场景\n\n### 🟡 **需要注意的", "collection_summary": "计划 10 项，实际采集 10 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "e1", "description": "检查集群中所有Pod的状态", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e2", "description": "检查节点状态", "level": "critical", "collected": true, "source": "thinking_match"}, {"id": "e3", "description": "检查异常Pod的详细信息", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e4", "description": "获取异常Pod的日志", "level": "important", "collected": true, "source": "thinking_match"}, {"id": "e5", "description": "检查Deployment配置", "level": "optional", "collected": true, "source": "thinking_match"}, {"id": "e6", "description": "检查集群事件", "level": "optional", "collected": true, "source": "thinking_match"}, {"id": "e7", "description": "检查集群资源使用情况", "level": "optional", "collected": true, "source": "thinking_match"}, {"id": "extra_4", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_8", "description": "工具采集: execute_prometheus_instant_query", "level": "important", "collected": true, "source": "thinking_extra"}, {"id": "extra_9", "description": "工具采集: execute_prometheus_instant_query", "level": "important", "collected": true, "source": "thinking_extra"}], "missing_reasons": [], "early_stop": {"triggered": true, "reason": "critical 和 important 级证据均已满足，提前停止后续采集", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 10/10 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (57.2s)
   📤 → 下游数据: root_cause=
   confidence=95%
   causal_chain={"root_cause": "Deployment 配置中未定义 APP_BOOT_MODE 环境变量", "propagation": "容器启动时执行配置校验脚本 → 检测到 APP_BOOT_MODE 环境变量缺失 → 应用层主动退出(Exit Code 42)", "direct_cause": "应用启动配置校验失败，业务逻辑要求必填参数缺失", "manifestation": "Pod 进入 CrashLoopBackOff 状态，容器反复崩溃重启"}
   rca_analysis={"phenomenon": "Pod appconfigfail-7649c79dc5-pcxt8 处于 CrashLoopBackOff 状态，重启12次，容器无法正常启动。", "evidence_inventory": [{"id": "e1", "content": "Pod appconfigfail-7649c79dc5-pcxt8 状态为 CrashLoopBackOff，重启12次，位于 node2", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e2", "content": "所有3个节点状态均为 Ready，集群基础设施正常", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e3", "content": "Pod describe 显示容器 Last State: Terminated, Reason: Error, Exit Code: 42，无 OOMKilled/Evicted", "source": "kubectl_describe", "reliability": "高"}, {"id": "e4", "content": "容器日志显示 'missing required APP_BOOT_MODE' 和 'business config validation failed before server startup'", "source": "run_bash_command", "reliability": "高"}, {"id": "e5", "content": "Deployment 配置显示容器启动脚本检查 APP_BOOT_MODE 环境变量，缺失则退出码 42", "source": "kubectl_get_yaml", "reliability": "高"}, {"id": "e6", "content": "集群事件显示 Pod 正常调度、创建、启动，但容器反复崩溃触发 BackOff", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e7", "content": "节点 CPU 使用率正常：master 13.96%，node1 9.45%，node2 3.05%", "source": "execute_prometheus_instant_query", "reliability": "高"}, {"id": "e8", "content": "节点内存使用率正常：node1 20.29%，master 数据不完整但无异常", "source": "execute_prometheus_instant_query", "reliability": "中"}, {"id": "e9", "content": "节点磁盘使用率正常：node1 根分区使用率 52.97%", "source": "execute_prometheus_instant_query", "reliability": "中"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "aiops-e2e/appconfigfail-7649c79dc5-pcxt8: READY 0/1, STATUS CrashLoopBackOff, RESTARTS 12 (107s ago), AGE 38m, NODE node2", "interpretation": "Pod 处于崩溃循环状态，容器反复启动失败，已重启12次"}, {"evidence_id": "e2", "raw_data": "master: Ready, node1: Ready, node2: Ready (所有节点状态正常)", "interpretation": "集群节点健康，无节点级故障"}, {"evidence_id": "e3", "raw_data": "Last State: Terminated, Reason: Error, Exit Code: 42, Started: 05:08:52, Finished: 05:08:52, Restart Count: 12", "interpretation": "容器以业务退出码42终止，非系统信号(如137/OOM)，表明应用层主动退出"}, {"evidence_id": "e4", "raw_data": "stdout: 'L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\nFATAL: missing required APP_BOOT_MODE\\nFATAL: business config validation failed before server startup'", "interpretation": "应用启动时校验配置失败，明确缺少必填环境变量 APP_BOOT_MODE"}, {"evidence_id": "e5", "raw_data": "容器启动脚本包含: if [ -z \"${APP_BOOT_MODE:-}\" ]; then echo \"FATAL: missing required APP_BOOT_MODE\"; exit 42; fi", "interpretation": "Deployment 配置中容器启动逻辑强制要求 APP_BOOT_MODE 环境变量，缺失则主动退出"}, {"evidence_id": "e6", "raw_data": "事件: Scheduled, AddedInterface, Pulled(x5), Created(x5), Started(x5), BackOff(x165)", "interpretation": "Pod 调度、网络、镜像拉取均正常，容器能启动但立即崩溃，触发 BackOff 机制"}, {"evidence_id": "e7", "raw_data": "CPU使用率: master 13.96%, node1 9.45%, node2 3.05% (均低于阈值)", "interpretation": "集群CPU资源充足，无资源竞争压力"}, {"evidence_id": "e8", "raw_data": "内存使用率: node1 20.29% (正常范围)", "interpretation": "内存资源充足，无内存压力"}, {"evidence_id": "e9", "raw_data": "磁盘使用率: node1 根分区 52.97% (正常范围)", "interpretation": "磁盘空间充足，无存储压力"}], "causal_chain": {"root_cause": "Deployment 配置中未定义 APP_BOOT_MODE 环境变量", "propagation": "容器启动时执行配置校验脚本 → 检测到 APP_BOOT_MODE 环境变量缺失 → 应用层主动退出(Exit Code 42)", "direct_cause": "应用启动配置校验失败，业务逻辑要求必填参数缺失", "manifestation": "Pod 进入 CrashLoopBackOff 状态，容器反复崩溃重启"}, "root_cause_summary": "根因为 L4 应用层配置错误：Pod appconfigfail-7649c79dc5-pcxt8 的容器启动脚本要求 APP_BOOT_MODE 环境变量（证据 e4/e5），但 Deployment 配置中未提供该环境变量（证据 e5）。容器每次启动时检测到变量缺失，输出 'missing required APP_BOOT_MODE' 后以退出码 42 主动终止（证据 e3/e4），导致 Pod 进入 CrashLoopBackOff 状态并重启12次（证据 e1）。集群基础设施正常（证据 e2/e7/e8/e9），无资源压力或底层故障。", "confidence": 0.95, "primary_runbooks": ["L4 应用启动配置校验失败 (Config Bootstrap Fail)"], "alternative_causes": [], "limitations": "证据充分，因果链清晰。未检查 ConfigMap/Secret 配置源，但 Deployment YAML 显示容器 spec 中无环境变量定义，已足够确定根因。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 95%
   🔗 因果链:
     根本原因: Deployment 配置中未定义 APP_BOOT_MODE 环境变量
     传导机制: 容器启动时执行配置校验脚本 → 检测到 APP_BOOT_MODE 环境变量缺失 → 应用层主动退出(Exit Code 42)
     最终表现: Pod 进入 CrashLoopBackOff 状态，容器反复崩溃重启


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 15.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5416 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 33.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **问题层级** | L4 - 应用层 |
| **问题分类** | 应用启动配置校验失败 |
| **置信度** | 高 (95%) |
| **证据完整度** | 10/10 (100%) |
---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**集群状态总结**：
您的集群基础设施（节点、网络、核心组件）运行正常，但存在一个**应用层配置错误**。具体表现为 Pod `appconfigfail-7649c79dc5-pcxt8` 因缺少必需的环境变量而持续崩溃重启。

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `appconfigfail-7649c79dc5-pcxt8` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| 错误信息 | `FATAL: missing required APP_BOOT_MODE` |
---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pods -A` | `aiops-e2e/appconfigfail-7649c79dc5-pcxt8: READY 0/1, STATUS CrashLoopBackOff, RESTARTS 12 (107s ago)` | Pod 处于崩溃循环，已重启12次 |
| 2 | 节点状态 | `kubectl get nodes` | `master: Ready, node1: Ready, node2: Ready` | 所有3个节点健康，基础设施正常 |
| 3 | Pod 详情 | `kubectl describe pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e` | `Last State: Terminated, Reason: Error, Exit Code: 42, Restart Count: 12` | 容器以业务退出码42终止，非系统OOM |
| 4 | 容器日志 | `kubectl logs appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e` | `L4_CONFIG_BOOTSTRAP_FAIL... FATAL: missing required APP_BOOT_MODE... business config validation failed` | 应用启动时明确报告缺少必填配置 `APP_BOOT_MODE` |
| 5 | Deployment配置 | `kubectl get deployment appconfigfail -n aiops-e2e -o yaml` | 容器启动脚本包含：`if [ -z "${APP_BOOT_MODE:-}" ]; then ... exit 42; fi` | Deployment 配置强制要求 `APP_BOOT_MODE` 环境变量，但未定义 |
| 6 | 集群事件 | `kubectl get events -A` | 事件：`Scheduled, AddedInterface, Pulled(x5), Created(x5), Started(x5), BackOff(x165)` | Pod 调度、网络、镜像拉取正常，容器启动后立即崩溃 |
| 7 | 节点CPU使用率 | Prometheus 查询 | `master: 13.96%, node1: 9.45%, node2: 3.05%` | CPU 资源充足，无竞争压力 |
| 8 | 节点内存使用率 | Prometheus 查询 | `node1: 20.29%, master: 26.35%, node2: 8.84%` | 内存资源充足 |
| 9 | 节点磁盘使用率 | Prometheus 查询 | `node1 根分区: 52.97%, master: 83.43%, node2: 54.89%` | 磁盘空间充足（master 使用率较高但未超限） |

### 证据关联分析
- **证据 #3 + #4 + #5 印证**：`Exit Code 42` + 日志 `missing required APP_BOOT_MODE` + Deployment脚本检查 `APP_BOOT_MODE` → **应用因配置缺失主动退出**
- **证据 #1 + #6 印证**：`CrashLoopBackOff` + 事件 `BackOff(x165)` → **容器反复崩溃触发重启退避机制**
- **证据 #2 + #7 + #8 + #9 排除**：所有节点 `Ready`，CPU/内存/磁盘使用率正常 → **排除底层资源或基础设施问题**

### 缺失证据（如有）
无。证据采集完整度 100%。
---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Deployment 配置中未定义 APP_BOOT_MODE 环境变量                   │
│ （证据 #5: Deployment YAML 显示容器 spec 中无环境变量定义）       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时执行配置校验脚本 → 检测到 APP_BOOT_MODE 环境变量缺失    │
│ （证据 #4: 日志显示校验失败；证据 #5: 脚本逻辑）                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 应用启动配置校验失败，业务逻辑要求必填参数缺失，主动退出(Exit 42) │
│ （证据 #3: Exit Code 42；证据 #4: FATAL 错误信息）              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 进入 CrashLoopBackOff 状态，容器反复崩溃重启                 │
│ （证据 #1: STATUS CrashLoopBackOff, RESTARTS 12）               │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #4（日志 `missing required APP_BOOT_MODE`）、证据 #5（Deployment 脚本检查 `APP_BOOT_MODE`）和证据 #3（`Exit Code: 42`），
问题的根本原因是 **L4 应用层配置错误**：Pod `appconfigfail-7649c79dc5-pcxt8` 的容器启动脚本要求 `APP_BOOT_MODE` 环境变量，但 Deployment 配置中未提供该变量，导致应用在启动阶段校验失败并主动退出。

**置信度**：高 (95%)
- ✅ 日志明确指向配置缺失（证据 #4）
- ✅ Deployment 配置证实变量未定义（证据 #5）
- ✅ 退出码 42 为业务逻辑退出，非系统错误（证据 #3）
- ✅ 集群基础设施及资源正常，排除底层问题（证据 #2, #7, #8, #9）
---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Deployment 添加缺失的环境变量**
```bash
kubectl set env deployment/appconfigfail -n aiops-e2e APP_BOOT_MODE=production
```
*依据*：证据 #4 和 #5 显示应用需要 `APP_BOOT_MODE` 环境变量才能启动。
*目的*：提供必需的配置，使应用能通过启动校验。

**2. [可选] 更新 Deployment 配置并重新部署**
如果环境变量值需要从 ConfigMap 或 Secret 注入，可编辑 Deployment：
```bash
kubectl edit deployment appconfigfail -n aiops-e2e
```
在容器 spec 中添加：
```yaml
env:
  - name: APP_BOOT_MODE
    value: "production" # 或 valueFrom: configMapKeyRef/secretKeyRef
```

### 后续优化
1.  **配置管理**：将应用配置（如 `APP_BOOT_MODE`）统一管理到 ConfigMap 或 Secret 中，与 Deployment 解耦。
2.  **健康检查**：为应用配置 `livenessProbe` 和 `readinessProbe`，更早发现启动失败。
3.  **资源监控**：虽然当前资源充足，建议持续监控 master 节点磁盘使用率（当前 83.43%），避免未来成为瓶颈。
---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e` | `STATUS: Running`，`READY: 1/1` |
| 2. 检查重启次数 | `kubectl get pod appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 数字不再增长（稳定在 12 或 13） |
| 3. 查看最新日志 | `kubectl logs appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e` | 不再出现 `FATAL: missing required APP_BOOT_MODE` 错误 |
| 4. 确认环境变量已设置 | `kubectl exec appconfigfail-7649c79dc5-pcxt8 -n aiops-e2e -- printenv APP_BOOT_MODE` | 输出 `production`（或您设置的值） |
---
## ⚠️ 注意事项
- 修复后，Pod 将自动重建（RollingUpdate 策略）。观察新 Pod 是否成功启动。
- 如果应用有其他配置依赖，请一并检查并补充。
- 此问题为特定应用配置错误，不影响集群其他服务。集群核心组件及监控体系运行正常。

---

## 📊 性能统计

├─ 总耗时: 4.6m
├─ 问题定位: 45.4s (17%) ✅
├─ 证据链采集: 95.0s (35%) ✅
├─ 根因分析: 57.2s (21%) ✅
├─ 汇总总结: 75.5s (28%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 16 次
```

📋 诊断追踪

- **核心 Runbook**: L4 应用启动配置校验失败 (Config Bootstrap Fail)
- **参考 Runbook**: L4 应用启动配置校验失败 (Config Bootstrap Fail)
- **工具调用**: 16 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
