======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c240bebbae104797]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来做一次轻量集群健康检查。先获取集群的整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS    RESTARTS      AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     appconfigfai
   💭 [问题定位] 3个节点都是 Ready 状态。我发现有一个异常 Pod：

- **aiops-e2e/appconfigfail-7649c79dc5-q4zjz** — STATUS: **Error**, 5次重启，刚发生（88s ago）

让我进一步查看这个 Pod 的详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [问题定位] 现在我很清楚这个 Pod 的情况了。让我获取通用 runbook 作为基线参考，同时也看看这个场景对应的 runbook。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# 私有化 Kubernetes 环境健康与高效排查参考手册

> 类型: reference | 适用: 私有化 Kubernetes 环境 | 环境特征: Calico + NFS + containerd

## 目的

本手册不是某个具体故障的处理步骤，而是一个**额外知识参考**：
- 帮助理解在私有化 Kubernetes 环境中，健康检查应重点关注哪些资源与信号

   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# L4 应用启动配置校验失败 (Config Bootstrap Fail)

> 层级: L4 - 应用层 | 场景: 应用在启动阶段因业务配置缺失或非法而主动退出

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | `CrashLoopBackOff` / `Error`，重启次数持续增加 |
| 容器日志 | 含
   💭 [问题定位] 现在我已有足够的证据。让我看一下这个 Pod 的日志来进一步确认。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS             RESTARTS      AGE    IP              NODE    NOMINATED NODE   READINESS GATES   LABELS
appconfigfail-7649c79dc5-q4zjz   0/1     CrashLoopBac
   💭 [问题定位] 现在状态已变为 CrashLoopBackOff。证据非常充分，可以输出了。

```json
{
  "layer": "L4",
  "layers": ["L4"],
  "layer_name": "应用层",
  "confidence": 0.95,
  "reasoning": "集群整体状态健康：3节点 Ready，绝大多数 Pod 正常运行。唯一异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，处于 CrashLoopBackOff。describe 显示容器 Exit Code=42，Last State=Error（非 OOMKilled/137），日志包含 'missing required APP_BOOT_MODE'、'FATAL: business config validation failed before server startup'，Pod 标签含 'l4-scenario=config-bootstrap-fail'。完全匹配 L4 应用启动配置校验失败场景。无 L0/L1/L2/L3 特征。",
  "key_entities": [
    {"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"},
    {"type": "Namespace", "value": "aiops-e2e"}
  ],
  "possible_scenarios": ["应用启动配置校验失败 (Config Bootstrap Fail)"]
}
```
   ✅ [问题定位] 完成 (25.3s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=['应用启动配置校验失败 (Config Bootstrap Fail)']
   entities=[{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}]
   reasoning=集群整体状态健康：3节点 Ready，绝大多数 Pod 正常运行。唯一异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，处于 CrashLoopBackOff。describe 显示容器 Exit Code=42，Last State=Error（非 OOMKilled/137），日志包含 'missing required APP_BOOT_MODE'、'FATAL: business config validation failed before server startup'，Pod 标签含 'l4-scenario=config-bootstrap-fail'。完全匹配 L4 应用启动配置校验失败场景。无 L0/L1/L2/L3 特征。
   layer_analysis={"layer": "L4", "layers": ["L4"], "layer_name": "应用层", "confidence": 0.95, "reasoning": "集群整体状态健康：3节点 Ready，绝大多数 Pod 正常运行。唯一异常 Pod 为 aiops-e2e/appconfigfail-7649c79dc5-q4zjz，处于 CrashLoopBackOff。describe 显示容器 Exit Code=42，Last State=Error（非 OOMKilled/137），日志包含 'missing required APP_BOOT_MODE'、'FATAL: business config validation failed before server startup'，Pod 标签含 'l4-scenario=config-bootstrap-fail'。完全匹配 L4 应用启动配置校验失败场景。无 L0/L1/L2/L3 特征。", "key_entities": [{"type": "Pod", "value": "appconfigfail-7649c79dc5-q4zjz"}, {"type": "Namespace", "value": "aiops-e2e"}], "possible_scenarios": ["应用启动配置校验失败 (Config Bootstrap Fail)"]}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 让我先查看集群的整体状态。
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAMESPACE     NAME                                                READY   STATUS             RESTARTS      AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS
aiops-e2e     app
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   209d   v1.26.8  
   💭 [证据链采集] 集群整体是健康的——3个节点都是 `Ready` 状态。不过我注意到有一个异常的 Pod：

**`aiops-e2e` 命名空间下**的 `appconfigfail-7649c79dc5-q4zjz` 处于 `CrashLoopBackOff` 状态，已重启了 5 次。让我进一步查看详情。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Name:             appconfigfail-7649c79dc5-q4zjz
Namespace:        aiops-e2e
Priority:         0
Service Account:  default
Node:             node2/10.2.0.50
Start Time:       Wed, 22 Apr 2026 07:38:39
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 LAST SEEN              TYPE      REASON           OBJECT                               MESSAGE
3m25s                  Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully assig
   💭 [证据链采集] 现在让我看一下这个 Pod 的完整日志。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\nL4_LAYER_APPLICATION: true\nL4_SCENARIO: config-bootstrap-fail\nL4_ERROR_TYPE: appl
   💭 [证据链采集] 好的，我已经完成了对集群的诊断。下面给你总结一下：

---

## 集群状态总览

**整体健康度：✅ 集群基本健康**

- **3 个节点**：`master`、`node1`、`node2` 全部 `Ready`
- **系统组件**：CoreDNS、Calico、kube-proxy 等全部正常运行
- **Prometheus/Grafana/Alertmanager** 等监控组件正常

---

## ⚠️ 唯一异常：`appconfigfail` Pod CrashLoopBackOff

| 项目 | 详情 |
|------|------|
| **Pod** | `appconfigfail-7649c79dc5-q4zjz`（命名空间：`aiops-e2e`） |
| **状态** | `CrashLoopBackOff`，已重启 **5 次** |
| **节点** | `node2` |
| **退出码** | **42**（业务自定义退出码，非 OOM） |

### 根因：**应用启动配置校验失败（L4 层问题）**

从日志中可以看到明确的失败链：

```
FATAL: missing required APP_BOOT_MODE
FATAL: business config validation failed before server startup
```

Pod 的启动脚本会检查环境变量 `APP_BOOT_MODE` 是否设置，发现为空后直接退出（exit 42），属于**应用层配置校验失败**。

### 修复建议

为 Pod 设置环境变量 `APP_BOOT_MODE`。例如在 Deployment 中补充：

```yaml
env:
  - name: APP_BOOT_MODE
    value: "production"  # 或其他合适的值
```

---

**总结：集群本身是健康的，只有这一个测试用的 Pod 因缺少配置环境变量而不断重启，这是 L4 应用层问题，不影响集群整体运行。**
   ✅ [证据链采集] 完成 (19.3s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan": [], "tool_results": [], "tool_data": [{"tool": "kubectl_get_by_kind_in_cluster", "data": "NAMESPACE     NAME                                                READY   STATUS             RESTARTS      AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\naiops-e2e     appconfigfail-7649c79dc5-q4zjz                      0/1     CrashLoopBackOff   5 (31s ago)   3m20s   172.16.104.57    node2    <none>           <none>            app=appconfigfail,l4-scenario=config-bootstrap-fail,pod-template-hash=7649c79dc5\naiops         aiops-copilot-76779bb6df-4bcrf                      1/1     Running            0             6h4m    172.16.104.29    node2    <none>           <none>            app=aiops-copilot,pod-template-hash=76779bb6df\ndefault       dns-test-existing                                   1/1     Running            0             2d2h    172.16.166.148   node1    <none>           <none>            run=dns-test-existing\ndefault       exec-test                                           1/1     Running            0             2d4h    172.16.104.8     node2    <none>           <none>            run=exec-test\ndefault       network-test-from-running                           1/1     Running            0             2d2h    172.16.104.50    node2    <none>           <none>            run=network-test-from-running\ndefault       nfs-client-provisioner-6fcd4994c9-lczf6             1/1     Running            4 (5d ago)    85d     172.16.104.41    node2    <none>           <none>            app=nfs-client-provisioner,pod-template-hash=6fcd4994c9\nkube-system   calico-kube-controllers-6c67f9d475-2xcb7            1/1     Running            4 (5d ago)    28d     172.16.166.133   node1    <none>           <none>            k8s-app=calico-kube-controllers,pod-template-hash=6c67f9d475\nkube-system   calico-node-4kp26                                   1/1     Running            12 (5d ago)   183d    10.2.0.48        master   <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-d2dhp                                   1/1     Running            13 (5d ago)   183d    10.2.0.50        node2    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   calico-node-mnrjs                                   1/1     Running            12 (5d ago)   183d    10.2.0.49        node1    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\nkube-system   coredns-777df594b8-j4857                            1/1     Running            4 (5d ago)    28d     172.16.166.129   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   coredns-777df594b8-s8r4n                            1/1     Running            4 (5d ago)    28d     172.16.166.185   node1    <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\nkube-system   etcd-master                                         1/1     Running            13 (5d ago)   209d    10.2.0.48        master   <none>           <none>            component=etcd,tier=control-plane\nkube-system   kube-apiserver-master                               1/1     Running            13 (5d ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-apiserver,tier=control-plane\nkube-system   kube-controller-manager-master                      1/1     Running            36 (5d ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-controller-manager,tier=control-plane\nkube-system   kube-multus-ds-rnvbg                                1/1     Running            12 (5d ago)   183d    10.2.0.49        node1    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-sc2jn                                1/1     Running            4 (5d ago)    85d     10.2.0.48        master   <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-multus-ds-x7h9s                                1/1     Running            13 (5d ago)   183d    10.2.0.50        node2    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-system   kube-proxy-69zzr                                    1/1     Running            4 (5d ago)    28d     10.2.0.50        node2    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-bblvc                                    1/1     Running            4 (5d ago)    28d     10.2.0.49        node1    <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-proxy-wbh4k                                    1/1     Running            4 (5d ago)    27d     10.2.0.48        master   <none>           <none>            controller-revision-hash=7d99996759,k8s-app=kube-proxy,pod-template-generation=1\nkube-system   kube-scheduler-master                               1/1     Running            38 (5d ago)   209d    10.2.0.48        master   <none>           <none>            component=kube-scheduler,tier=control-plane\nmcp           mcp-server-manager-8677f6896c-d4mr9                 1/1     Running            0             45h     172.16.104.59    node2    <none>           <none>            app=mcp-server-manager,pod-template-hash=8677f6896c\nxnet          alertmanager-observability-alertmanager-0           2/2     Running            8 (5d ago)    23d     172.16.166.161   node1    <none>           <none>            alertmanager=observability-alertmanager,app.kubernetes.io/instance=observability-alertmanager,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=alertmanager,app.kubernetes.io/version=0.28.1,controller-revision-hash=alertmanager-observability-alertmanager-6c9cfbf844,statefulset.kubernetes.io/pod-name=alertmanager-observability-alertmanager-0\nxnet          api-server-6bd6bf8d6f-27svp                         1/1     Running            4 (5d ago)    23d     172.16.219.106   master   <none>           <none>            app=api-server,pod-template-hash=6bd6bf8d6f\nxnet          deepflow-agent-pcknn                                1/1     Running            9 (5d ago)    23d     172.16.166.181   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-trc8k                                1/1     Running            7 (5d ago)    19d     172.16.104.7     node2    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          deepflow-agent-whn22                                1/1     Running            8 (5d ago)    23d     172.16.219.97    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow-agent,app=deepflow,component=deepflow-agent,controller-revision-hash=54856d959b,pod-template-generation=1\nxnet          elasticsearch-master-0                              1/1     Running            4 (5d ago)    23d     172.16.219.109   master   <none>           <none>            app=elasticsearch-master,chart=observability,controller-revision-hash=elasticsearch-master-695ff9864f,release=observability,statefulset.kubernetes.io/pod-name=elasticsearch-master-0\nxnet          ham-p9dxv                                           1/1     Running            14 (5d ago)   177d    172.16.104.21    node2    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-qzjg5                                           1/1     Running            4 (5d ago)    85d     172.16.219.112   master   <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          ham-wt9kh                                           1/1     Running            13 (5d ago)   177d    172.16.166.187   node1    <none>           <none>            app=ham,controller-revision-hash=f65f887d,pod-template-generation=1\nxnet          lgtm-5dc5c67d5f-sc286                               1/1     Running            4 (5d ago)    23d     172.16.166.151   node1    <none>           <none>            app=lgtm,pod-template-hash=5dc5c67d5f\nxnet          observability-clickhouse-0                          1/1     Running            4 (5d ago)    23d     172.16.166.137   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=clickhouse,app=deepflow,component=clickhouse,controller-revision-hash=observability-clickhouse-75b8d58ccc,statefulset.kubernetes.io/pod-name=observability-clickhouse-0\nxnet          observability-deepflow-app-654fcfbfbf-q8st6         1/1     Running            4 (5d ago)    23d     172.16.166.160   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-app,pod-template-hash=654fcfbfbf\nxnet          observability-deepflow-server-774dd6c5b7-9c998      1/1     Running            14 (5d ago)   23d     172.16.166.135   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=deepflow,app=deepflow,component=deepflow-server,pod-template-hash=774dd6c5b7\nxnet          observability-filebeat-ffwsp                        1/1     Running            4 (5d ago)    23d     172.16.219.80    master   <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-m58xw                        1/1     Running            5 (5d ago)    23d     172.16.166.134   node1    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-filebeat-w6gtr                        1/1     Running            5 (5d ago)    19d     172.16.104.53    node2    <none>           <none>            app=observability-filebeat,chart=observability-1.0.2,controller-revision-hash=57fb88b7c5,heritage=Helm,pod-template-generation=1,release=observability\nxnet          observability-grafana-58bf9cfd6f-ndsxr              4/4     Running            36 (5d ago)   23d     172.16.166.144   node1    <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=grafana,app.kubernetes.io/version=12.0.2,helm.sh/chart=grafana-9.2.7,pod-template-hash=58bf9cfd6f\nxnet          observability-kepler-2sgrr                          1/1     Running            6 (5d ago)    23d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-7scjm                          1/1     Running            7 (5d ago)    23d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kepler-ggstf                          1/1     Running            8 (5d ago)    19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=exporter,app.kubernetes.io/name=kepler-kepler,controller-revision-hash=7c6c5f9bd6,pod-template-generation=1\nxnet          observability-kibana-65d7c45f6d-tm4vv               1/1     Running            4 (5d ago)    23d     172.16.166.191   node1    <none>           <none>            app=observability-kibana,pod-template-hash=65d7c45f6d,release=observability\nxnet          observability-kube-state-metrics-798986b8b7-6z2dq   1/1     Running            4 (5d ago)    23d     172.16.219.65    master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=kube-state-metrics,app.kubernetes.io/part-of=kube-state-metrics,app.kubernetes.io/version=2.15.0,helm.sh/chart=kube-state-metrics-5.37.0,pod-template-hash=798986b8b7,release=observability\nxnet          observability-mysql-764f9d5966-wh2bc                1/1     Running            4 (5d ago)    23d     172.16.219.98    master   <none>           <none>            app.kubernetes.io/instance=observability,app.kubernetes.io/name=mysql,app=deepflow,component=mysql,pod-template-hash=764f9d5966\nxnet          observability-operator-d4495dc86-69lgw              1/1     Running            4 (5d ago)    23d     172.16.166.182   node1    <none>           <none>            app.kubernetes.io/component=prometheus-operator,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=observability-prometheus-operator,app.kubernetes.io/part-of=observability,app.kubernetes.io/version=1.0.2,app=observability-operator,chart=observability-1.0.2,heritage=Helm,pod-template-hash=d4495dc86,release=observability\nxnet          observability-prometheus-node-exporter-lj75r        1/1     Running            4 (5d ago)    23d     10.2.0.48        master   <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-qp2qd        1/1     Running            4 (5d ago)    19d     10.2.0.50        node2    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-prometheus-node-exporter-wnbb8        1/1     Running            4 (5d ago)    23d     10.2.0.49        node1    <none>           <none>            app.kubernetes.io/component=metrics,app.kubernetes.io/instance=observability,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=prometheus-node-exporter,app.kubernetes.io/part-of=prometheus-node-exporter,app.kubernetes.io/version=1.9.1,controller-revision-hash=74f4f4b87d,helm.sh/chart=prometheus-node-exporter-4.47.0,jobLabel=node-exporter,pod-template-generation=1,release=observability\nxnet          observability-telegraf-79f45d86-4kzkm               1/1     Running            4 (5d ago)    23d     172.16.219.113   master   <none>           <none>            app.kubernetes.io/component=telegraf,app.kubernetes.io/instance=observability,app.kubernetes.io/name=observability,pod-template-hash=79f45d86\nxnet          prometheus-observability-prometheus-0               2/2     Running            16 (5d ago)   23d     172.16.166.142   node1    <none>           <none>            app.kubernetes.io/instance=observability-prometheus,app.kubernetes.io/managed-by=prometheus-operator,app.kubernetes.io/name=prometheus,app.kubernetes.io/version=3.4.1,controller-revision-hash=prometheus-observability-prometheus-9467b46f7,operator.prometheus.io/name=observability-prometheus,operator.prometheus.io/shard=0,prometheus=observability-prometheus,statefulset.kubernetes.io/pod-name=prometheus-observability-prometheus-0\nxnet          xnet-agent-568f547566-jdsgp                         1/1     Running            4 (5d ago)    108d    172.16.104.40    node2    <none>           <none>            app=xnet-agent,pod-template-hash=568f547566", "duration_s": 0}, {"tool": "kubectl_get_by_kind_in_cluster", "data": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   209d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          209d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          209d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-174-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux", "duration_s": 0}, {"tool": "kubectl_describe", "data": "Name:             appconfigfail-7649c79dc5-q4zjz\nNamespace:        aiops-e2e\nPriority:         0\nService Account:  default\nNode:             node2/10.2.0.50\nStart Time:       Wed, 22 Apr 2026 07:38:39 +0000\nLabels:           app=appconfigfail\n                  l4-scenario=config-bootstrap-fail\n                  pod-template-hash=7649c79dc5\nAnnotations:      cni.projectcalico.org/containerID: c6399f913454284036a261148882084711e3bf6f9788cf1df749c56fbda41b6f\n                  cni.projectcalico.org/podIP: 172.16.104.57/32\n                  cni.projectcalico.org/podIPs: 172.16.104.57/32\n                  k8s.v1.cni.cncf.io/network-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\n                  k8s.v1.cni.cncf.io/networks-status:\n                    [{\n                        \"name\": \"k8s-pod-network\",\n                        \"ips\": [\n                            \"172.16.104.57\"\n                        ],\n                        \"default\": true,\n                        \"dns\": {}\n                    }]\nStatus:           Running\nIP:               172.16.104.57\nIPs:\n  IP:           172.16.104.57\nControlled By:  ReplicaSet/appconfigfail-7649c79dc5\nContainers:\n  app:\n    Container ID:  containerd://2851411f339b74d06683c98492b87fc65f8212a1558e70605591e4722939b0a9\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Port:          <none>\n    Host Port:     <none>\n    Command:\n      sh\n      -c\n    Args:\n      echo \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\"\n      echo \"L4_LAYER_APPLICATION: true\"\n      echo \"L4_SCENARIO: config-bootstrap-fail\"\n      echo \"L4_ERROR_TYPE: application-config-validation\"\n      if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n        echo \"FATAL: missing required APP_BOOT_MODE\"\n        echo \"FATAL: business config validation failed before server startup\"\n        exit 42\n      fi\n      echo \"unexpected success\"\n      exit 1\n      \n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n      Started:      Wed, 22 Apr 2026 07:41:28 +0000\n      Finished:     Wed, 22 Apr 2026 07:41:28 +0000\n    Ready:          False\n    Restart Count:  5\n    Environment:    <none>\n    Mounts:\n      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-zndsj (ro)\nConditions:\n  Type              Status\n  Initialized       True \n  Ready             False \n  ContainersReady   False \n  PodScheduled      True \nVolumes:\n  kube-api-access-zndsj:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    TokenExpirationSeconds:  3607\n    ConfigMapName:           kube-root-ca.crt\n    ConfigMapOptional:       <nil>\n    DownwardAPI:             true\nQoS Class:                   BestEffort\nNode-Selectors:              <none>\nTolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\n                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s\nEvents:\n  Type     Reason          Age                   From               Message\n  ----     ------          ----                  ----               -------\n  Normal   Scheduled       3m25s                 default-scheduler  Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n  Normal   AddedInterface  3m25s                 multus             Add eth0 [172.16.104.57/32] from k8s-pod-network\n  Normal   Pulled          119s (x5 over 3m25s)  kubelet            Container image \"busybox:1.36\" already present on machine\n  Normal   Created         119s (x5 over 3m25s)  kubelet            Created container app\n  Normal   Started         119s (x5 over 3m25s)  kubelet            Started container app\n  Warning  BackOff         93s (x10 over 3m23s)  kubelet            Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "kubectl_events", "data": "LAST SEEN              TYPE      REASON           OBJECT                               MESSAGE\n3m25s                  Normal    Scheduled        Pod/appconfigfail-7649c79dc5-q4zjz   Successfully assigned aiops-e2e/appconfigfail-7649c79dc5-q4zjz to node2\n3m25s                  Normal    AddedInterface   Pod/appconfigfail-7649c79dc5-q4zjz   Add eth0 [172.16.104.57/32] from k8s-pod-network\n119s (x5 over 3m25s)   Normal    Pulled           Pod/appconfigfail-7649c79dc5-q4zjz   Container image \"busybox:1.36\" already present on machine\n119s (x5 over 3m25s)   Normal    Created          Pod/appconfigfail-7649c79dc5-q4zjz   Created container app\n119s (x5 over 3m25s)   Normal    Started          Pod/appconfigfail-7649c79dc5-q4zjz   Started container app\n93s (x10 over 3m23s)   Warning   BackOff          Pod/appconfigfail-7649c79dc5-q4zjz   Back-off restarting failed container app in pod appconfigfail-7649c79dc5-q4zjz_aiops-e2e(77ea5d65-2a07-47e0-b606-3f03812dcc6a)", "duration_s": 0}, {"tool": "run_bash_command", "data": "{\"success\": true, \"stdout\": \"L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config\\nL4_LAYER_APPLICATION: true\\nL4_SCENARIO: config-bootstrap-fail\\nL4_ERROR_TYPE: application-config-validation\\nFATAL: missing required APP_BOOT_MODE\\nFATAL: business config validation failed before server startup\\n\", \"stderr\": \"\", \"returncode\": 0}", "duration_s": 0}], "llm_analysis": "好的，我已经完成了对集群的诊断。下面给你总结一下：\n\n---\n\n## 集群状态总览\n\n**整体健康度：✅ 集群基本健康**\n\n- **3 个节点**：`master`、`node1`、`node2` 全部 `Ready`\n- **系统组件**：CoreDNS、Calico、kube-proxy 等全部正常运行\n- **Prometheus/Grafana/Alertmanager** 等监控组件正常\n\n---\n\n## ⚠️ 唯一异常：`appconfigfail` Pod CrashLoopBackOff\n\n| 项目 | 详情 |\n|------|------|\n| **Pod** | `appconfigfail-7649c79dc5-q4zjz`（命名空间：`aiops-e2e`） |\n| **状态** | `CrashLoopBackOff`，已重启 **5 次** |\n| **节点** | `node2` |\n| **退出码** | **42**（业务自定义退出码，非 OOM） |\n\n### 根因：**应用启动配置校验失败（L4 层问题）**\n\n从日志中可以看到明确的失败链：\n\n```\nFATAL: missing required APP_BOOT_MODE\nFATAL: business config validation failed before server startup\n```\n\nPod 的启动脚本会检查环境变量 `APP_BOOT_MODE` 是否设置，发现为空后直接退出（exit 42），属于**应用层配置校验失败**。\n\n### 修复建议\n\n为 Pod 设置环境变量 `APP_BOOT_MODE`。例如在 Deployment 中补充：\n\n```yaml\nenv:\n  - name: APP_BOOT_MODE\n    value: \"production\"  # 或其他合适的值\n```\n\n---\n\n**总结：集群本身是健康的，只有这一个测试用的 Pod 因缺少配置环境变量而不断重启，这是 L4 应用层问题，不影响集群整体运行。**", "collection_summary": "计划 5 项，实际采集 5 项，未采集 0 项，完整度 100%", "evidence_inventory": [{"id": "auto_0", "description": "工具采集: kubectl_get_by_kind_in_cluster", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_1", "description": "工具采集: kubectl_get_by_kind_in_cluster", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_2", "description": "工具采集: kubectl_describe", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_3", "description": "工具采集: kubectl_events", "level": "important", "collected": true, "source": "thinking_auto"}, {"id": "auto_4", "description": "工具采集: run_bash_command", "level": "important", "collected": true, "source": "thinking_auto"}], "missing_reasons": [], "early_stop": {"triggered": false, "reason": "", "required_levels": ["critical", "important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/5 项, 完整度: 100%

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.7s)
   📤 → 下游数据: root_cause=
   confidence=98%
   causal_chain={"root_cause": "应用 Deployment 未配置必需的环境变量 APP_BOOT_MODE", "propagation": "应用启动时进行配置校验 -> 检查 APP_BOOT_MODE 环境变量 -> 发现变量未设置 -> 触发启动脚本中的 FATAL 错误逻辑 -> 调用 exit(42) 退出进程", "direct_cause": "应用启动脚本因缺少 APP_BOOT_MODE 环境变量而执行配置校验失败并终止", "manifestation": "Pod 进程以退出码 42 退出 -> Kubernetes 检测到容器退出（非 0 退出码）-> 自动重启容器 -> 重启后再次因相同原因退出 -> 反复循环，Pod 进入 CrashLoopBackOff 状态"}
   rca_analysis={"phenomenon": "Pod appconfigfail-7649c79dc5-q4zjz 处于 CrashLoopBackOff 状态，已重启 5 次，退出码为 42", "evidence_inventory": [{"id": "e1", "content": "Pod appconfigfail-7649c79dc5-q4zjz 状态为 CrashLoopBackOff，已重启 5 次", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e2", "content": "集群 3 个节点 (master, node1, node2) 全部 Ready", "source": "kubectl_get_by_kind_in_cluster", "reliability": "高"}, {"id": "e3", "content": "Pod 退出码为 42，容器状态为 Terminated/Error，事件显示 BackOff", "source": "kubectl_describe", "reliability": "高"}, {"id": "e4", "content": "Pod 被成功调度到 node2，网络已配置（IP 172.16.104.57）", "source": "kubectl_events", "reliability": "高"}, {"id": "e5", "content": "日志包含：'missing required APP_BOOT_MODE'、'FATAL: business config validation failed before server startup'、'L4_CONFIG_BOOTSTRAP_FAIL'", "source": "run_bash_command (kubectl logs --previous)", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Pod appconfigfail-7649c79dc5-q4zjz: READY=0/1, STATUS=CrashLoopBackOff, RESTARTS=5, AGE=3m20s, NODE=node2, IP=172.16.104.57", "interpretation": "Pod 无法正常运行，持续崩溃并自动重启，已重试 5 次，表明存在持续性故障"}, {"evidence_id": "e2", "raw_data": "3 节点: master (Ready), node1 (Ready), node2 (Ready)", "interpretation": "集群基础设施正常，排除节点级故障（L0/L1/L2）"}, {"evidence_id": "e3", "raw_data": "Exit Code=42 (非 137 OOMKilled), State: Terminated, Reason: Error, 事件: Warning BackOff", "interpretation": "退出码 42 为业务自定义错误码，非系统 OOM 或信号终止，指向应用自身逻辑异常"}, {"evidence_id": "e4", "raw_data": "事件: Scheduled (成功分配到 node2, 10.2.0.50), AddedInterface (添加 eth0, IP 172.16.104.57/32)", "interpretation": "Pod 调度和网络配置均正常，排除调度或网络问题"}, {"evidence_id": "e5", "raw_data": "日志内容: 'FATAL: missing required APP_BOOT_MODE', 'FATAL: business config validation failed before server startup', 'L4_CONFIG_BOOTSTRAP_FAIL: application bootstrap aborted due to invalid business config'", "interpretation": "应用启动时进行配置校验，发现必需的环境变量 APP_BOOT_MODE 缺失，主动终止启动，并打印明确的 FATAL 错误"}], "causal_chain": {"root_cause": "应用 Deployment 未配置必需的环境变量 APP_BOOT_MODE", "propagation": "应用启动时进行配置校验 -> 检查 APP_BOOT_MODE 环境变量 -> 发现变量未设置 -> 触发启动脚本中的 FATAL 错误逻辑 -> 调用 exit(42) 退出进程", "direct_cause": "应用启动脚本因缺少 APP_BOOT_MODE 环境变量而执行配置校验失败并终止", "manifestation": "Pod 进程以退出码 42 退出 -> Kubernetes 检测到容器退出（非 0 退出码）-> 自动重启容器 -> 重启后再次因相同原因退出 -> 反复循环，Pod 进入 CrashLoopBackOff 状态"}, "root_cause_summary": "Pod appconfigfail-7649c79dc5-q4zjz（命名空间 aiops-e2e，节点 node2，IP 172.16.104.57）持续 CrashLoopBackOff（5 次重启，退出码 42）的根因是应用启动配置校验失败：应用启动时检查环境变量 APP_BOOT_MODE 是否设置，发现缺失后直接终止启动，日志明确输出 'FATAL: missing required APP_BOOT_MODE' 和 'FATAL: business config validation failed before server startup'。集群 3 个节点均 Ready，其余 Pod 运行正常，已排除 L0/L1/L2/L3 问题，确认为 L4 应用层配置问题。", "confidence": 0.98, "primary_runbooks": [], "alternative_causes": [], "limitations": "证据充分，无显著局限性。日志中 'busybo' 可能为 busybox 镜像名截断，但不影响根因判断。未采集 Pod YAML 确认 Deployment 定义，但日志已直接定位问题。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   置信度: 98%
   🔗 因果链:
     根本原因: 应用 Deployment 未配置必需的环境变量 APP_BOOT_MODE
     传导机制: 应用启动时进行配置校验 -> 检查 APP_BOOT_MODE 环境变量 -> 发现变量未设置 -> 触发启动脚本中的 FATAL 错误逻辑 -> 调用 exit(42) 退出进程
     最终表现: Pod 进程以退出码 42 退出 -> Kubernetes 检测到容器退出（非 0 退出码）-> 自动重启容器 -> 重启后再次因相同原因退出 -> 反复循环，Pod 进入 CrashLoopBackOff 状态


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (40.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5251 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 50.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的分析结果，为您生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **问题层级** | L4 - 应用层 |
| **问题分类** | 应用启动配置校验失败 (Config Bootstrap Fail) |
| **置信度** | 高 (98%) |
| **证据完整度** | 5/5 (100%) |

## 核心问题总结

**您的集群本身是健康的。** 根据采集到的数据，所有 3 个节点（`master`, `node1`, `node2`）均处于 `Ready` 状态，系统组件（如 CoreDNS, Calico）和绝大多数业务 Pod 都运行正常。

**集群中唯一发现的问题**是一个用于模拟故障的测试 Pod：`appconfigfail-7649c79dc5-q4zjz`。该 Pod 处于 `CrashLoopBackOff` 状态，根本原因是**其启动脚本因缺少必需的环境变量 `APP_BOOT_MODE` 而主动退出**，这是一个典型的 L4 应用层配置问题，不影响集群整体运行。

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `appconfigfail-7649c79dc5-q4zjz` |
| Namespace | `aiops-e2e` |
| Node | `node2` |
| 错误信息 | `FATAL: missing required APP_BOOT_MODE` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl_get_by_kind_in_cluster` | `READY: 0/1, STATUS: CrashLoopBackOff, RESTARTS: 5` | Pod 无法正常运行，持续崩溃重启 |
| 2 | 节点状态 | `kubectl_get_by_kind_in_cluster` | `master (Ready), node1 (Ready), node2 (Ready)` | 集群节点基础设施正常，排除 L0/L1/L2 问题 |
| 3 | Pod 描述 | `kubectl_describe` | `Exit Code: 42, State: Terminated, Reason: Error` | 退出码 42 是业务自定义错误码，非系统 OOM (137) |
| 4 | 事件信息 | `kubectl_events` | `Warning BackOff: Back-off restarting failed container` | Kubernetes 检测到容器持续异常退出并执行退避重启 |
| 5 | 容器日志 | `run_bash_command (kubectl logs --previous)` | `FATAL: missing required APP_BOOT_MODE`, `FATAL: business config validation failed before server startup` | 应用启动时检查环境变量 `APP_BOOT_MODE`，发现缺失后主动终止 |

### 证据关联分析
- **证据 #1 + #3 印证**：`CrashLoopBackOff` 状态与 `Exit Code: 42` 直接关联，表明 Pod 崩溃是由应用程序以特定错误码退出导致。
- **证据 #3 + #5 印证**：`Exit Code: 42` 是启动脚本中 `exit 42` 命令的执行结果，日志明确记录了导致退出的原因（`missing required APP_BOOT_MODE`），构成完整证据链。
- **证据 #1 + #2 排除**：集群和节点健康，说明问题与应用自身相关，而非基础设施故障。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 证据完整，无缺失项 |

---
## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                         │
│ Pod 对应的 Deployment 未配置必需的环境变量 APP_BOOT_MODE                           │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                         │
│ Pod 启动 -> 执行启动脚本 -> 脚本校验环境变量 APP_BOOT_MODE -> 发现变量为空/未设置    │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                         │
│ 应用启动脚本因配置校验失败，主动调用 `exit(42)` 终止进程                           │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                     │
│ Pod 进程退出 -> Kubelet 检测到非零退出码 -> 自动重启容器 -> 再次失败 -> 循环      │
│ 最终状态: CrashLoopBackOff，持续重启                                              │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #3 (Exit Code 42, Reason: Error) 和证据 #5 (日志 `FATAL: missing required APP_BOOT_MODE`)，问题的根本原因是 **Pod 的启动脚本依赖环境变量 `APP_BOOT_MODE`，但该变量未被定义**，导致应用在启动阶段的配置校验环节失败并主动退出，最终陷入 `CrashLoopBackOff` 状态。

**置信度**：高 (98%)
- ✅ 日志明确指出了缺失的变量名 (`APP_BOOT_MODE`)。
- ✅ 退出码 42 与日志中的主动退出逻辑完全吻合。
- ✅ 排除了所有 L0/L1/L2/L3 的基础设施问题。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [优先] 为 Pod 设置环境变量 APP_BOOT_MODE**
您需要修改管理该 Pod 的 Deployment（通常名为 `appconfigfail`）的 YAML 配置，在容器定义中添加环境变量。

```bash
# 查看当前 Deployment 配置
kubectl edit deployment appconfigfail -n aiops-e2e
```
在打开的 YAML 文件中，找到 `spec.template.spec.containers[0].env` 字段，如果没有则创建它，并添加如下内容：
```yaml
env:
  - name: APP_BOOT_MODE
    value: "production"  # 根据您的实际需求设置，例如 "production", "development", "staging"
```
保存并退出编辑器后，Kubernetes 会自动触发滚动更新，重新创建 Pod。

*依据*：当前 `APP_BOOT_MODE` 环境变量缺失是唯一根因，设置后应用即可正常启动。

**2. [可选] 验证修复**
```bash
# 查看新 Pod 的状态
kubectl get pods -n aiops-e2e -l app=appconfigfail

# 查看 Pod 日志，确认不再有 FATAL 错误
kubectl logs -n aiops-e2e -l app=appconfigfail --tail=10
```

### 后续优化
1. **应用配置清单化**：将所有应用必需的环境变量和配置项记录在 ConfigMap 或 Helm values 文件中，方便统一管理和审查。
2. **启动健康检查**：为应用配置合适的 Startup Probe，在启动脚本中添加更详细的错误提示，避免仅通过 `exit 42` 这样不明确的退出码进行诊断。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认新 Pod 运行 | `kubectl get pods -n aiops-e2e -l app=appconfigfail` | `STATUS: Running`, `READY: 1/1` |
| 2. 检查重启次数 | `kubectl get pods -n aiops-e2e -l app=appconfigfail -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}'` | `0` (或不再增加) |
| 3. 检查应用日志 | `kubectl logs -n aiops-e2e -l app=appconfigfail --tail=5` | 日志输出 `unexpected success` (如启动脚本所述) 或其他正常启动日志，无 `FATAL` 错误 |

---
## ⚠️ 注意事项
- 此问题是一个典型的**模拟故障场景**，其 Pod 标签 `l4-scenario=config-bootstrap-fail` 也印证了这一点。它主要用于测试和验证集群的故障诊断能力，**不会影响集群上运行的其他关键业务**。
- 如果这是一个生产应用，请确保将 `APP_BOOT_MODE` 的值（如 `production`）正确配置在 Deployment 或 Helm values 中，避免在多个环境中因配置不一致导致启动失败。

---

## 📊 性能统计

├─ 总耗时: 1.8m
├─ 问题定位: 25.3s (23%) ✅
├─ 证据链采集: 19.3s (18%) ✅
├─ 根因分析: 24.7s (22%) ✅
├─ 汇总总结: 40.9s (37%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **参考 Runbook**: private-k8s-health-reference, l4-config-bootstrap-fail
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
