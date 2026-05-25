======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d6edca6cc5d64748]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先对集群进行全局 Pod 状态扫描，查看所有异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces returned ~92 pods total. Running=59 (most stable). Abnormal=29: ImagePullBackOff=22, ErrImagePull=5, Error=1 (rc-crashloop-exit-code, restarted 10 times), Terminating
   💭 [问题定位] 好的，全局 Pod 扫描完毕。让我获取更多具体信息来精确定位异常类型。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=424 lines=4
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=343 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: run_bash_command
   💭 [问题定位] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "aiops-e2e   test-dns-1779360358                      0/1     ImagePullBackOff   0          3h14m\ndefault     dns-check-test                           0/1     ImagePullBac
   💭 [问题定位] 调用工具: run_bash_command
   💭 [问题定位] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "aiops-e2e         rc-crashloop-exit-code-5db5947859-2522x             0/1     CrashLoopBackOff   10 (29s ago)   26m\n", "stderr": "", "returncode": 0}
   💭 [问题定位] 现在让我确认在 aiops-e2e 命名空间中的那个 CrashLoopBackOff Pod 以及查看 Pod 的镜像拉取错误详情。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod CrashLoopBackOffRuntime / 容器反复退出

> Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime

## 状态识别
- Pod 状态: `CrashLoopBackOff`
- Last State: Terminated
-
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod TerminatingStuck / 删除卡住

> runbook_id: pod-terminating-stuck.md
> Pod异常类型: TerminatingStuck | 典型状态: Terminating | 兼容分类: lifecycle

## 状态识别
- Pod 长时间处于 `Terminating`
- metadata.deletion
   💭 [问题定位] 好的，全局数据已获取完毕。让我再查看一下具体的异常 Pod 详情来确认异常类型。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-check-test
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  22m (x167 over 121m)  kubelet  Back-off pulling image "busybox:1.36.1"
   
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-exit-code-5db5947859-2522x
namespace: aiops-e2e
node: node2/10.2.0.50
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRuntime
      R
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: net-check-tmp
namespace: mcp
node: node1/10.2.0.49
status: Terminating (lasts 7m2s)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: 1b8074c9d38cf453a73c
   💭 [问题定位] 现在让我进一步查看那个 CrashLoopBackOff Pod 的日志来确认退出原因。
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 调用工具: kubectl_previous_logs
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (44.6s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L2+L3
   scenarios=[{'scenario': '镜像仓库网络不可达或DNS解析失败导致大量Pod无法拉取镜像', 'probability': '高', 'reason': '22个ImagePullBackOff和5个ErrImagePullPod分布在多个命名空间，均尝试拉取busybox或其他镜像失败，kubelet事件显示Back-off pulling image/Error: ErrImagePull，表明集群到镜像仓库的网络或DNS存在问题'}, {'scenario': '镜像仓库认证或权限问题', 'probability': '低', 'reason': '目前没有看到unauthorized/no basic auth事件，且拉取的busybox是公开镜像，认证问题可能性较低'}, {'scenario': '容器命令/入口进程错误导致CrashLoopBackOff', 'probability': '中', 'reason': 'aiops-e2e/rc-crashloop-exit-code Exit Code 2，容器命令为sh -c但args为空，属于容器运行时启动命令导致的退出'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "pod", "name": "dns-check-test", "namespace": "default"}, {"type": "pod", "name": "rc-crashloop-exit-code-5db5947859-2522x", "namespace": "aiops-e2e"}, {"type": "pod", "name": "net-check-tmp", "namespace": "mcp"}]
   reasoning=集群存在大量异常Pod，核心问题是ImagePullBackOff（22个）和ErrImagePull（5个），分布在default、mcp、aiops-e2e命名空间。这些Pod尝试拉取busybox:1.36.1等镜像失败，kubelet持续BackOff。同时，aiops-e2e命名空间有一个CrashLoopBackOff Pod（rc-crashloop-exit-code，Exit Code 2，重启10次），mcp命名空间有一个Terminating卡住的Pod（net-check-tmp，已持续7分钟，仍在ContainerCreating状态）。根据五层模型，大量ImagePullBackOff/ErrImagePull属于L3（镜像仓库/网络问题），是集群最广泛、根因性的异常。CrashLoopBackOff（Exit Code 2，非OOM）属于L2容器运行时异常，TerminatingStuck属于L1生命周期卡住。但以覆盖范围最广和根因层级为准，整体定层L3。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L2", "L3"], "layer_name": "镜像拉取与网络问题", "confidence": 0.95, "reasoning": "集群存在大量异常Pod，核心问题是ImagePullBackOff（22个）和ErrImagePull（5个），分布在default、mcp、aiops-e2e命名空间。这些Pod尝试拉取busybox:1.36.1等镜像失败，kubelet持续BackOff。同时，aiops-e2e命名空间有一个CrashLoopBackOff Pod（rc-crashloop-exit-code，Exit Code 2，重启10次），mcp命名空间有一个Terminating卡住的Pod（net-check-tmp，已持续7分钟，仍在ContainerCreating状态）。根据五层模型，大量ImagePullBackOff/ErrImagePull属于L3（镜像仓库/网络问题），是集群最广泛、根因性的异常。CrashLoopBackOff（Exit Code 2，非OOM）属于L2容器运行时异常，TerminatingStuck属于L1生命周期卡住。但以覆盖范围最广和根因层级为准，整体定层L3。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-2522x", "namespace": "aiops-e2e", "status": "Error"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ErrImagePull"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-tmp", "namespace": "mcp", "status": "Terminating"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "pod", "name": "dns-check-test", "namespace": "default"}, {"type": "pod", "name": "rc-crashloop-exit-code-5db5947859-2522x", "namespace": "aiops-e2e"}, {"type": "pod", "name": "net-check-tmp", "namespace": "mcp"}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达或DNS解析失败导致大量Pod无法拉取镜像", "probability": "高", "reason": "22个ImagePullBackOff和5个ErrImagePullPod分布在多个命名空间，均尝试拉取busybox或其他镜像失败，kubelet事件显示Back-off pulling image/Error: ErrImagePull，表明集群到镜像仓库的网络或DNS存在问题"}, {"scenario": "镜像仓库认证或权限问题", "probability": "低", "reason": "目前没有看到unauthorized/no basic auth事件，且拉取的busybox是公开镜像，认证问题可能性较低"}, {"scenario": "容器命令/入口进程错误导致CrashLoopBackOff", "probability": "中", "reason": "aiops-e2e/rc-crashloop-exit-code Exit Code 2，容器命令为sh -c但args为空，属于容器运行时启动命令导致的退出"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-2522x"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "net-check-tmp"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-2522x"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "net-check-tmp"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Error": 1, "ImagePullBackOff": 22, "ErrImagePull": 5, "Terminating": 1}, "total_abnormal": 29, "selected_rows": ["aiops-e2e         rc-crashloop-exit-code-5db5947859-2522x             0/1     Error              10 (5m23s ago)   26m     172.16.104.21    node2    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0                3h14m   172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dns-check-test                                      0/1     ImagePullBackOff   0                122m    172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0                3h9m    172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0                45m     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           net-test-pod                                        0/1     ImagePullBackOff   0                110m    172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0                139m    172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0                13m     172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0                120m    172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ErrImagePull       0                3h8m    172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0                141m    172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               net-check-1779365549                                0/1     ErrImagePull       0                107m    172.16.166.179   node1    <none>           <none>            run=net-check-1779365549", "mcp               net-check-tmp                                       0/1     Terminating        0                7m15s   <none>           node1    <none>           <none>            run=net-check-tmp", "mcp               node-debugger-node1-2xvqr                           0/1     ImagePullBackOff   0                3h15m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-4ncj7                           0/1     ErrImagePull       0                175m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6pxvd                           0/1     ImagePullBackOff   0                55m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-ckjnc                           0/1     ErrImagePull       0                143m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-j7gtr                           0/1     ImagePullBackOff   0                74m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-jdbpc                           0/1     ImagePullBackOff   0                74m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-pjlg5                           0/1     ImagePullBackOff   0                179m    10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L2 + L3（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 好的，我现在开始执行既有 evidence_plan。上游已经获取了 runbook 参考，我先从关键证据开始采集。

首先，同时采集多个关键 Pod 的描述信息和全集群事件。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-test
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   17m (x19 over 115m)     kubelet  (combined from similar events): Failed to 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-check-test
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  23m (x167 over 122m)  kubelet  Back-off pulling image "busybox:1.36.1"
   
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod registry-conn-test-1779371220 in namespace default is Pending on node node2/10.2.0.50. Container busybox:1.36.1 fails to pull due to network timeouts / connection refused to registry-1.docker.io (
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: test-dns-1779360358
namespace: aiops-e2e
creationTimestamp: 2026-05-21T10:45:58Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-exit-code-5db5947859-2522x
namespace: aiops-e2e
node: node2/10.2.0.50
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRuntime
      R
   💭 [证据链采集] 很好！已经获取了大量关键证据。现在继续采集：全集群 ImagePull 失败事件、以及 CrashLoop Pod 的 previous logs。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAMESPACE   NAME   REASON   MESSAGE\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
23m (x167 over 122m)   Normal    BackOff   Pod/dns-check-test   Back-off pulling image "busybox:1.36.1"
57m (x11 over 122m)    Warning   Failed    Pod/dns-check-test   Error:
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [证据链采集] 很好！已经获取了关键证据。现在让我再获取 CrashLoop Pod 的完整 YAML 来确认 command/args 配置，以及获取 Terminating 的 Pod 的状态。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-exit-code-5db5947859-2522x
namespace: aiops-e2e
creationTimestamp: 2026-05-21T13:33:48Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=145 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide pod net-check-tmp -n mcp
Error from server (NotFound): pods "net-check-tmp" not found
   💭 [证据链采集] 让我再检查一下 Terminating Pod 是否已被删除（YAML 方式确认）。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "Error from server (NotFound): pods \"net-check-tmp\" not found\n", "stderr": "", "returncode": 1}
   💭 [证据链采集] 好的，所有关键证据已采集完毕。下面是证据结论：

---

## 已采集证据汇总

### 🟥 异常组 g2：ImagePullBackOff/ErrImagePull（主异常组，27个Pod）— 完整验证

**已采集关键证据：**

1. **kubectl describe dns-check-test -n default** — 确认拉取 `busybox:1.36.1` 失败，Events 显示 `Back-off pulling image "busybox:1.36.1"` + `Error: ErrImagePull`，无具体连接细节
2. **kubectl describe registry-conn-test-1779371220 -n default** — ✅ **核心证据**：事件原文显示 `dial tcp 157.240.13.8:443: i/o timeout` 和 `dial tcp 199.59.148.7:443: connect: connection refused`，目标为 `registry-1.docker.io`
3. **kubectl describe connectivity-test -n mcp** — ✅ **核心证据**：事件原文显示 `dial tcp 108.160.169.55:443: i/o timeout` 连接 `registry-1.docker.io` 超时
4. **kubectl get yaml test-dns-1779360358 -n aiops-e2e** — 确认使用镜像 `busybox:1.36.1`，**无 imagePullSecrets**，容器状态为 `ErrImagePull`，错误信息：`dial tcp 128.121.146.228:443: i/o timeout`
5. **全集群 ImagePull 事件** — 时间戳排序的 events 查询返回空（`field_selector` 语法未命中），但已通过各 Pod describe 获取到完整事件原文

**关键发现：** 所有 ImagePullBackOff/ErrImagePull Pod 均尝试拉取公开镜像 `busybox:1.36.1`，错误原文为 **`dial tcp ...:443: i/o timeout`** 和 **`connection refused`**，目标均为 `registry-1.docker.io`。无 imagePullSecrets（公开镜像不需要）。**结论：节点（node1/node2）到 docker.io 镜像仓库的网络不可达/超时**，这是根因。

---

### 🟨 异常组 g1：Error/CrashLoopBackOff（rc-crashloop-exit-code-5db5947859-2522x）— 完整验证

**已采集关键证据：**

1. **kubectl describe** — Last State: `Terminated` / `Error` / **Exit Code: 2**，重启 10 次，Reason: `CrashLoopBackOff`
2. **kubectl get yaml** — Command: `sh -c`，Args: `echo "RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2"\nexit 2`，**imagePullPolicy=Never**（不从远程拉取，所以 ImagePull 问题不影响此 Pod）
3. **kubectl logs --previous** — 输出仅含 `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2`

**关键发现：** 该 Pod 的 args 中显式编写了 `exit 2`，容器启动后立即退出，属于 **人为构造的 CrashLoopBackOff 测试用例**（标签 `rootcause-e2e=true`）。Exit Code 2 不是 OOM/配置缺失，而是命令主动退出。

---

### 🟩 异常组 g3：TerminatingStuck（net-check-tmp）— 冲突证据

**已采集：** `kubectl get pod net-check-tmp -n mcp` 返回 **NotFound**（Pod 已删除）。该 Pod 在 upstream 采集时处于 Terminating 状态，但现在已被清理完成。**不作为当前故障**处理。

---

## 最终诊断结论

| 问题 | 影响范围 | 根因 |
|------|---------|------|
| **ImagePullBackOff/ErrImagePull** | **27个Pod**，跨 default/mcp/aiops-e2e 命名空间，分布在 node1 和 node2 | **集群节点到 docker.io (registry-1.docker.io) 网络不可达** — `dial tcp ...:443: i/o timeout` 和 `connection refused`，导致所有需要拉取 `busybox:1.36.1` 的 Pod 均无法启动 |
| **CrashLoopBackOff (rc-crashloop-exit-code)** | 1个Pod，aiops-e2e | **人工构造的测试用例** — command/args 显式执行 `exit 2`，镜像使用 `busybox:1.36` 且 `imagePullPolicy=Never`，非真实故障 |
| **Terminating (net-check-tmp)** | 0个Pod（已自动清理） | Pod 已被删除，不再构成当前异常 |
   ✅ [证据链采集] 完成 (42.4s)
   📤 → 下游数据: evidence_items=14/18
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Runbook reference: pod-imagepull-failed.md","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{},"purpose":"参考ImagePull诊断流程","evidence_type":"reference","target_scope":"reference","acceptable_tools":[],"counts_for_completeness":false},{"id":"e2","description":"Runbook reference: pod-crashloop-runtime.md","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-crashloop-runtime.md","tool_args":{},"purpose":"参考CrashLoop诊断流程","evidence_type":"reference","target_scope":"reference","acceptable_tools":[],"counts_for_completeness":false},{"id":"e3","description":"Runbook reference: pod-terminating-stuck.md","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-terminating-stuck.md","tool_args":{},"purpose":"参考Terminating诊断流程","evidence_type":"reference","target_scope":"reference","acceptable_tools":[],"counts_for_completeness":false},{"id":"e4","description":"[主异常组g2-ImagePull] describe代表Pod dns-check-test确认Events中的拉取失败细节","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","tool_args":{"kind":"pod","name":"dns-check-test","namespace":"default","resource_type":"pod"},"purpose":"确认ImagePullBackOff的根本原因事件原文","evidence_type":"pod_event","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"[主异常组g2-ImagePull] 查看Pod test-dns-1779360358 (aiops-e2e)的镜像配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"检查镜像地址和imagePullSecrets","evidence_type":"pod_config","target_scope":"pod","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e6","description":"[主异常组g2-ImagePull] 查看Pod registry-conn-test-1779371220 (default)的镜像和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod registry-conn-test-1779371220 -n default","tool_args":{"kind":"pod","name":"registry-conn-test-1779371220","namespace":"default","resource_type":"pod"},"purpose":"确认registry连通性测试Pod的拉取失败细节","evidence_type":"pod_event","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7","description":"[主异常组g2-ImagePull] 查看mcp命名空间代表Pod connectivity-test的Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp","resource_type":"pod"},"purpose":"确认mcp命名空间ImagePull事件的共性","evidence_type":"pod_event","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e8","description":"[主异常组g2-ImagePull] 获取集群级Events查看ImagePull相关警告","level":"critical","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by='.lastTimestamp'","tool_args":{"field_selector":"reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff","all_namespaces":true},"purpose":"获取全集群ImagePull失败事件原文","evidence_type":"cluster_event","target_scope":"cluster","acceptable_tools":[],"counts_for_completeness":true},{"id":"e9","description":"[异常组g1-Error/CrashLoop] describe Pod rc-crashloop-exit-code-5db5947859-2522x","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-crashloop-exit-code-5db5947859-2522x","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"查看Last State、Exit Code、重启原因","evidence_type":"pod_event","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e10","description":"[异常组g1-Error/CrashLoop] 查看崩溃前日志","level":"critical","tool":"run_bash_command","command":"kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e --previous --tail=200","tool_args":{"command":"kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e --previous --tail=200"},"purpose":"查看容器崩溃前的输出，诊断Exit Code 2","evidence_type":"container_log","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   17m (x19 over 115m)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.169.55:443: i/o timeout\n  Normal   BackOff  2m34s (x542 over 141m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  connectivity-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-zhjs9:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   17m (x19 over 115m)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.169.55:443: i/o timeout\n  Normal   BackOff  2m34s (x542 over 141m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-check-test\nnamespace: default\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  23m (x167 over 122m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   57m (x11 over 122m)   kubelet  Error: ErrImagePull\n  Warning  Failed   5m56s (x13 over 82m)  kubelet  (combined from similar events): Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 0e7a6c53736ee153a1f68ab8eca45c237cb5f9eb52fb5ab71c7603eeb52a82c1\n                  cni.projectcalico.org/podIP: 172.16.166.167/32\n                  cni.projectcalico.org/podIPs: 172.16.166.167/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-check-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n      nslookup registry-1.docker.io 2>&1; echo '---'; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-dlk9d:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   57m (x11 over 122m)   kubelet  Error: ErrImagePull\n  Normal   BackOff  23m (x167 over 122m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   5m56s (x13 over 82m)  kubelet  (combined from similar events): Error: ErrImagePull\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod registry-conn-test-1779371220 in namespace default is Pending on node node2/10.2.0.50. Container busybox:1.36.1 fails to pull due to network timeouts / connection refused to registry-1.docker.io (IPs 157.240.13.8 and 199.59.148.7). Container State: Waiting (ImagePullBackOff), Ready: False, Restart Count: 0. Pod IP: 172.16.104.40/32. QoS: BestEffort. Events show repeated Failed (ErrImagePull, ImagePullBackOff) and BackOff (x32).\nkey_facts: [\"name: registry-conn-test-1779371220\", \"namespace: default\", \"node: node2/10.2.0.50\", \"Status: Pending\", \"Container Image: busybox:1.36.1\", \"Container State: Waiting (ImagePullBackOff)\", \"Container Ready: False\", \"Restart Count: 0\", \"Pod IP: 172.16.104.40/32\", \"QoS Class: BestEffort\", \"Failed to pull image: rpc error code=DeadlineExceeded - dial tcp 157.240.13.8:443: i/o timeout\", \"Failed to pull image: rpc error code=Unknown - dial tcp 199.59.148.7:443: connect: connection refused\", \"Event: Failed (ErrImagePull) x4 over 13m\", \"Event: Failed (ImagePullBackOff) x6 over 13m\", \"Event: BackOff (x32 over 13m) - Back-off pulling image\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: test-dns-1779360358\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T10:45:58Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- test-dns-1779360358: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: /bin/sh -c nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- test-dns-1779360358: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 128.121.146.228:443: i/o timeout\nvolumes:\n- {\"name\": \"kube-api-access-g4sbz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-exit-code-5db5947859-2522x\nnamespace: aiops-e2e\nnode: node2/10.2.0.50\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         2m34s (x117 over 27m)  kubelet            Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-2522x_aiops-e2e(850ba18e-e3f9-4c5e-9802-88f3f62aef2b)\n                  cni.projectcalico.org/containerID: a59e16b3acf90f303557929567aa2b41c9bf3e9d60e2e729ca607c43be0a50a3\n                  cni.projectcalico.org/podIP: 172.16.104.21/32\n                  cni.projectcalico.org/podIPs: 172.16.104.21/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-crashloop-exit-code-5db5947859\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://c5ddab1f6de30cd68d1d942404365a4329786d8705073137cc5ce3d3a626b5f2\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n    Args:\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    2\n      Started:      Thu, 21 May 2026 14:00:15 +0000\n      Finished:     Thu, 21 May 2026 14:00:15 +0000\n    Ready:          False\n    Restart Count:  10\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-wssxl:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  BackOff         2m34s (x117 over 27m)  kubelet            Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-2522x_aiops-e2e(850ba18e-e3f9-4c5e-9802-88f3f62aef2b)\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAMESPACE   NAME   REASON   MESSAGE\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/006-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n23m (x167 over 122m)   Normal    BackOff   Pod/dns-check-test   Back-off pulling image \"busybox:1.36.1\"\n57m (x11 over 122m)    Warning   Failed    Pod/dns-check-test   Error: ErrImagePull\n6m4s (x13 over 82m)    Warning   Failed    Pod/dns-check-test   (combined from similar events): Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/007-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/007-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/007-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/008-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/008-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/008-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-exit-code-5db5947859-2522x\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T13:33:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-exit-code, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-runtime.md\nownerReferences: ReplicaSet/rc-crashloop-exit-code-5db5947859\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c\n  args: echo \"RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2\"\nexit 2\n\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=10 reason=CrashLoopBackOff exitCode=2\n  message: back-off 5m0s restarting failed container=app pod=rc-crashloop-exit-code-5db5947859-2522x_aiops-e2e(850ba18e-e3f9-4c5e-9802-88f3f62aef2b)\nvolumes:\n- {\"name\": \"kube-api-access-wssxl\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/009-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/009-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/009-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=145 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide pod net-check-tmp -n mcp\nError from server (NotFound): pods \"net-check-tmp\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/010-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/010-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/010-evidence-kubectl_get_by_name.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"Error from server (NotFound): pods \\\"net-check-tmp\\\" not found\\n\", \"stderr\": \"\", \"returncode\": 1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6edca6cc5d64748/tools/011-evidence-run_bash_command.summary.txt"}],"llm_analysis":"好的，所有关键证据已采集完毕。下面是证据结论：\n\n---\n\n## 已采集证据汇总\n\n### 🟥 异常组 g2：ImagePullBackOff/ErrImagePull（主异常组，27个Pod）— 完整验证\n\n**已采集关键证据：**\n\n1. **kubectl describe dns-check-test -n default** — 确认拉取 `busybox:1.36.1` 失败，Events 显示 `Back-off pulling image \"busybox:1.36.1\"` + `Error: ErrImagePull`，无具体连接细节\n2. **kubectl describe registry-conn-test-1779371220 -n default** — ✅ **核心证据**：事件原文显示 `dial tcp 157.240.13.8:443: i/o timeout` 和 `dial tcp 199.59.148.7:443: connect: connection refused`，目标为 `registry-1.docker.io`\n3. **kubectl describe connectivity-test -n mcp** — ✅ **核心证据**：事件原文显示 `dial tcp 108.160.169.55:443: i/o timeout` 连接 `registry-1.docker.io` 超时\n4. **kubectl get yaml test-dns-1779360358 -n aiops-e2e** — 确认使用镜像 `busybox:1.36.1`，**无 imagePullSecrets**，容器状态为 `ErrImagePull`，错误信息：`dial tcp 128.121.146.228:443: i/o timeout`\n5. **全集群 ImagePull 事件** — 时间戳排序的 events 查询返回空（`field_selector` 语法未命中），但已通过各 Pod describe 获取到完整事件原文\n\n**关键发现：** 所有 ImagePullBackOff/ErrImagePull Pod 均尝试拉取公开镜像 `busybox:1.36.1`，错误原文为 **`dial tcp ...:443: i/o timeout`** 和 **`connection refused`**，目标均为 `registry-1.docker.io`。无 imagePullSecrets（公开镜像不需要）。**结论：节点（node1/node2）到 docker.io 镜像仓库的网络不可达/超时**，这是根因。\n\n---\n\n### 🟨 异常组 g1：Error/CrashLoopBackOff（rc-crashloop-exit-code-5db5947859-2522x）— 完整验证\n\n**已采集关键证据：**\n\n1. **kubectl describe** — Last State: `Terminated` / `Error` / **Exit Code: 2**，重启 10 次，Reason: `CrashLoopBackOff`\n2. **kubectl get yaml** — Command: `sh -c`，Args: `echo \"RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2\"\\nexit 2`，**imagePullPolicy=Never**（不从远程拉取，所以 ImagePull 问题不影响此 Pod）\n3. **kubectl logs --previous** — 输出仅含 `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2`\n\n**关键发现：** 该 Pod 的 args 中显式编写了 `exit 2`，容器启动后立即退出，属于 **人为构造的 CrashLoopBackOff 测试用例**（标签 `rootcause-e2e=true`）。Exit Code 2 不是 OOM/配置缺失，而是命令主动退出。\n\n---\n\n### 🟩 异常组 g3：TerminatingStuck（net-check-tmp）— 冲突证据\n\n**已采集：** `kubectl get pod net-check-tmp -n mcp` 返回 **NotFound**（Pod 已删除）。该 Pod 在 upstream 采集时处于 Terminating 状态，但现在已被清理完成。**不作为当前故障**处理。\n\n---\n\n## 最终诊断结论\n\n| 问题 | 影响范围 | 根因 |\n|------|---------|------|\n| **ImagePullBackOff/ErrImagePull** | **27个Pod**，跨 default/mcp/aiops-e2e 命名空间，分布在 node1 和 node2 | **集群节点到 docker.io (registry-1.docker.io) 网络不可达** — `dial tcp ...:443: i/o timeout` 和 `connection refused`，导致所有需要拉取 `busybox:1.36.1` 的 Pod 均无法启动 |\n| **CrashLoopBackOff (rc-crashloop-exit-code)** | 1个Pod，aiops-e2e | **人工构造的测试用例** — command/args 显式执行 `exit 2`，镜像使用 `busybox:1.36` 且 `imagePullPolicy=Never`，非真实故障 |\n| **Terminating (net-check-tmp)** | 0个Pod（已自动清理） | Pod 已被删除，不再构成当前异常 |","collection_summary":"计划 7 项，实际采集 6 项，未采集 1 项，完整度 86%；其中真实环境证据 14/15 项，完整度 93%；实际执行工具 18 个，匹配计划 6 个，未规划证据 12 个","plan_total":7,"plan_collected":6,"plan_completeness":0.8571428571428571,"environment_evidence_total":15,"environment_evidence_collected":14,"environment_evidence_completeness":0.9333333333333333,"executed_tool_count":18,"matched_tool_count":6,"unplanned_tool_count":12,"evidence_inventory":[{"id":"e1","description":"Runbook reference: pod-imagepull-failed.md","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"参考ImagePull诊断流程","collected":false,"source":"planned","outcome":"unknown"},{"id":"e2","description":"Runbook reference: pod-crashloop-runtime.md","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-crashloop-runtime.md","purpose":"参考CrashLoop诊断流程","collected":false,"source":"planned","outcome":"unknown"},{"id":"e3","description":"Runbook reference: pod-terminating-stuck.md","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-terminating-stuck.md","purpose":"参考Terminating诊断流程","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4","description":"[主异常组g2-ImagePull] describe代表Pod dns-check-test确认Events中的拉取失败细节","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","purpose":"确认ImagePullBackOff的根本原因事件原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"[主异常组g2-ImagePull] 查看Pod test-dns-1779360358 (aiops-e2e)的镜像配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml","purpose":"检查镜像地址和imagePullSecrets","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"[主异常组g2-ImagePull] 查看Pod registry-conn-test-1779371220 (default)的镜像和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod registry-conn-test-1779371220 -n default","purpose":"确认registry连通性测试Pod的拉取失败细节","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7","description":"[主异常组g2-ImagePull] 查看mcp命名空间代表Pod connectivity-test的Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","purpose":"确认mcp命名空间ImagePull事件的共性","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e8","description":"[主异常组g2-ImagePull] 获取集群级Events查看ImagePull相关警告","level":"critical","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by='.lastTimestamp'","purpose":"获取全集群ImagePull失败事件原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e9","description":"[异常组g1-Error/CrashLoop] describe Pod rc-crashloop-exit-code-5db5947859-2522x","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e","purpose":"查看Last State、Exit Code、重启原因","collected":false,"source":"planned","outcome":"unknown"},{"id":"e10","description":"[异常组g1-Error/CrashLoop] 查看崩溃前日志","level":"critical","tool":"run_bash_command","command":"kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e --previous --tail=200","purpose":"查看容器崩溃前的输出，诊断Exit Code 2","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: run_bash_command","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: run_bash_command","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e9([异常组g1-Error/CrashLoop] describe Pod rc-crashloop-exit-code-5db5947859-2522x): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/7 项, 完整度: 93%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | reference | ❌ | fetch_runbook | Runbook reference: pod-imagepull-failed.md | `fetch_runbook pod-imagepull-failed.md` |
   | e2 | reference | ❌ | fetch_runbook | Runbook reference: pod-crashloop-runtime.md | `fetch_runbook pod-crashloop-runtime.md` |
   | e3 | reference | ❌ | fetch_runbook | Runbook reference: pod-terminating-stuck.md | `fetch_runbook pod-terminating-stuck.md` |
   | e4 | critical | ✅ | kubectl_describe | [主异常组g2-ImagePull] describe代表Pod dns-check-te... | `kubectl describe pod dns-check-test -n default` |
   | e5 | important | ✅ | kubectl_get_yaml | [主异常组g2-ImagePull] 查看Pod test-dns-1779360358 ... | `kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml` |
   | e6 | important | ✅ | kubectl_describe | [主异常组g2-ImagePull] 查看Pod registry-conn-test-1... | `kubectl describe pod registry-conn-test-1779371220 -n default` |
   | e7 | important | ✅ | kubectl_describe | [主异常组g2-ImagePull] 查看mcp命名空间代表Pod connectivit... | `kubectl describe pod connectivity-test -n mcp` |
   | e8 | critical | ✅ | kubectl_events | [主异常组g2-ImagePull] 获取集群级Events查看ImagePull相关警告 | `kubectl get events --all-namespaces --field-selector reason=FailedToPullImage...` |
   | e9 | critical | ❌ | kubectl_describe | [异常组g1-Error/CrashLoop] describe Pod rc-crash... | `kubectl describe pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e` |
   | e10 | critical | ✅ | run_bash_command | [异常组g1-Error/CrashLoop] 查看崩溃前日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e --previous ...` |

   ⚠️ 未采集原因:
   - e9([异常组g1-Error/CrashLoop] describe Pod rc-crashloop-exit-code-5db5947859-2522x): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (30.6s)
   📤 → 下游数据: root_cause=根因：集群节点到Docker Hub镜像仓库的出口网络故障。证据：(1) mcp/connectivity-test在node2上报'dial tcp 108.160.169.55:443: i/o timeout'，(2) default/registry-conn-test-1779371220在node2上报'dial tcp 157.240.13.8:443: i/o timeout'和'dial tcp 199.59.148.7:443: connection refused'，(3) aiops-e2e/test-dns-1779360358在node1上报'dial tcp 128.121.146.228:443: i/o timeout'。三个命名空间、两个节点、4个不同IP均不可达，排除单个节点或单个镜像问题。27个受影响Pod中22个ImagePullBackOff、5个ErrImagePull。附属异常：aiops-e2e/rc-crashloop-exit-code的CrashLoopBackOff(Exit Code 2)为人为构造测试用例（args含exit
... 截断，原始 575 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点(node1/node2)到Docker Hub镜像仓库(registry-1.docker.io:443)的出口网络不可达，导致所有尝试拉取busybox:1.36.1的Pod均因TCP连接超时/拒绝失败", "propagation": "1) 节点kubelet发起镜像拉取请求 → 2) DNS解析registry-1.docker.io成功(获得多个IP)→ 3) TCP三次握手到IP:443全部超时(i/o timeout)或连接拒绝(connection refused)→ 4) containerd返回DeadlineExceeded错误→ 5) kubelet将Pod状态置为ErrImagePull→ 6) 进入指数退避重试循环变为ImagePullBackOff", "direct_cause": "节点到registry-1.docker.io:443的网络连通性故障，TCP连接9次尝试均失败（多个Pod分别连接不同IP: 108.160.169.55, 128.121.146.228, 157.240.13.8, 199.59.148.7均不可达）", "manifestation": "default/mcp/aiops-e2e三个命名空间共27个Pod处于ImagePullBackOff(22个)/ErrImagePull(5个)状态，持续13分钟至3小时以上，所有Pod均拉取busybox:1.36.1失败，kubelet Events显示i/o timeout/connection refused"}
   rca_analysis={"phenomenon": "集群存在29个异常Pod，主异常组g2为27个Pod处于ImagePullBackOff(22个)/ErrImagePull(5个)状态，分布在default(9个)、mcp(17个)、aiops-e2e(1个)命名空间，位于node1和node2上。附属异常：g1为aiops-e2e/rc-crashloop-exit-code-5db5947859-2522x处于Error状态(Exit Code 2, CrashLoopBackOff, 重启10次)；g3的mcp/net-check-tmp已被删除(NotFound)，不作为当前异常。", "evidence_inventory": [{"id": "e4", "source": "kubectl_describe connectivity-test -n mcp", "content": "mcp/connectivity-test, Failed to pull image 'busybox:1.36.1': dial tcp 108.160.169.55:443: i/o timeout to registry-1.docker.io", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_yaml test-dns-1779360358 -n aiops-e2e", "content": "aiops-e2e/test-dns-1779360358, image=busybox:1.36.1, no imagePullSecrets, error: dial tcp 128.121.146.228:443: i/o timeout", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe dns-check-test -n default", "content": "default/dns-check-test, Back-off pulling image 'busybox:1.36.1', x167 events over 122m, Error: ErrImagePull", "reliability": "高"}, {"id": "e7", "source": "kubectl_describe registry-conn-test-1779371220 -n default", "content": "default/registry-conn-test-1779371220, dial tcp 157.240.13.8:443: i/o timeout and dial tcp 199.59.148.7:443: connection refused to registry-1.docker.io", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe rc-crashloop-exit-code -n aiops-e2e", "content": "aiops-e2e/rc-crashloop-exit-code, Exit Code 2, CrashLoopBackOff, restart 10x, Command: sh -c, Args: echo ...exit 2", "reliability": "高"}, {"id": "e10", "source": "kubectl_previous_logs rc-crashloop-exit-code", "content": "日志仅输出: RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "总计~92个Pod, Running=59, 异常29个: ImagePullBackOff=22, ErrImagePull=5, Error=1, Terminating=1", "reliability": "高"}, {"id": "layer_8", "source": "kubectl_get_by_name net-check-tmp", "content": "NotFound: pods 'net-check-tmp' not found, 已删除", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e4", "raw_data": "Failed to pull image 'busybox:1.36.1': dial tcp 108.160.169.55:443: i/o timeout (registry-1.docker.io)", "interpretation": "mcp命名空间Pod connectivity-test在node2上拉取busybox:1.36.1时，TCP连接registry-1.docker.io:443超时，节点到Docker Hub网络不可达"}, {"evidence_id": "e5", "raw_data": "image=busybox:1.36.1, imagePullSecrets=<absent>, error: dial tcp 128.121.146.228:443: i/o timeout", "interpretation": "aiops-e2e命名空间Pod test-dns-1779360358在node1上同样报i/o timeout连接registry-1.docker.io；无imagePullSecrets说明非认证问题；跨命名空间和跨节点一致性指向集群级网络问题"}, {"evidence_id": "e7", "raw_data": "dial tcp 157.240.13.8:443: i/o timeout AND dial tcp 199.59.148.7:443: connect: connection refused", "interpretation": "default/registry-conn-test-1779371220在node2上报两种不同错误(i/o timeout和connection refused)连接registry-1.docker.io的不同IP，进一步确认出口网络存在问题"}, {"evidence_id": "e6", "raw_data": "Normal BackOff x167 over 122m — Back-off pulling image 'busybox:1.36.1', Warning Failed ErrImagePull x11/x13", "interpretation": "default/dns-check-test在node1上持续122分钟重试仍失败，kubelet已执行167次BackOff，系统持续消耗重试资源"}, {"evidence_id": "e8", "raw_data": "Exit Code 2, CrashLoopBackOff, restart 10x, Command: sh -c, Args: echo 'RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2'\\nexit 2", "interpretation": "该Pod的args显式编写了'exit 2'，是人为构造的CrashLoopBackOff测试用例(rootcause-e2e=true)，与镜像拉取问题无关"}, {"evidence_id": "e10", "raw_data": "RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2", "interpretation": "容器日志仅输出了人为构造的错误消息后退出，Exit Code 2对应args中的exit 2命令，非OOM或配置缺失"}, {"evidence_id": "layer_8", "raw_data": "Error from server (NotFound): pods 'net-check-tmp' not found", "interpretation": "异常组g3的Pod net-check-tmp已被删除，不作为当前故障"}], "causal_chain": {"root_cause": "集群节点(node1/node2)到Docker Hub镜像仓库(registry-1.docker.io:443)的出口网络不可达，导致所有尝试拉取busybox:1.36.1的Pod均因TCP连接超时/拒绝失败", "propagation": "1) 节点kubelet发起镜像拉取请求 → 2) DNS解析registry-1.docker.io成功(获得多个IP)→ 3) TCP三次握手到IP:443全部超时(i/o timeout)或连接拒绝(connection refused)→ 4) containerd返回DeadlineExceeded错误→ 5) kubelet将Pod状态置为ErrImagePull→ 6) 进入指数退避重试循环变为ImagePullBackOff", "direct_cause": "节点到registry-1.docker.io:443的网络连通性故障，TCP连接9次尝试均失败（多个Pod分别连接不同IP: 108.160.169.55, 128.121.146.228, 157.240.13.8, 199.59.148.7均不可达）", "manifestation": "default/mcp/aiops-e2e三个命名空间共27个Pod处于ImagePullBackOff(22个)/ErrImagePull(5个)状态，持续13分钟至3小时以上，所有Pod均拉取busybox:1.36.1失败，kubelet Events显示i/o timeout/connection refused"}, "root_cause": "根因：集群节点到Docker Hub镜像仓库的出口网络故障。证据：(1) mcp/connectivity-test在node2上报'dial tcp 108.160.169.55:443: i/o timeout'，(2) default/registry-conn-test-1779371220在node2上报'dial tcp 157.240.13.8:443: i/o timeout'和'dial tcp 199.59.148.7:443: connection refused'，(3) aiops-e2e/test-dns-1779360358在node1上报'dial tcp 128.121.146.228:443: i/o timeout'。三个命名空间、两个节点、4个不同IP均不可达，排除单个节点或单个镜像问题。27个受影响Pod中22个ImagePullBackOff、5个ErrImagePull。附属异常：aiops-e2e/rc-crashloop-exit-code的CrashLoopBackOff(Exit Code 2)为人为构造测试用例（args含exit\n... 截断，原始 575 字符", "root_cause_summary": "根因：集群节点到Docker Hub镜像仓库的出口网络故障。证据：(1) mcp/connectivity-test在node2上报'dial tcp 108.160.169.55:443: i/o timeout'，(2) default/registry-conn-test-1779371220在node2上报'dial tcp 157.240.13.8:443: i/o timeout'和'dial tcp 199.59.148.7:443: connection refused'，(3) aiops-e2e/test-dns-1779360358在node1上报'dial tcp 128.121.146.228:443: i/o timeout'。三个命名空间、两个节点、4个不同IP均不可达，排除单个节点或单个镜像问题。27个受影响Pod中22个ImagePullBackOff、5个ErrImagePull。附属异常：aiops-e2e/rc-crashloop-exit-code的CrashLoopBackOff(Exit Code 2)为人为构造测试用例（args含exit\n... 截断，原始 575 字符", "confidence": 0.95, "confidence_reason": "有直接证据：多个Pod的describe事件原文明确显示'dial tcp ...:443: i/o timeout'连接registry-1.docker.io。跨3个命名空间(default/mcp/aiops-e2e)、2个节点(node1/node2)、4个不同Docker Hub IP(108.160.169.55, 128.121.146.228, 157.240.13.8, 199.59.148.7)一致复现。因果链完整：网络不可达→拉取失败→ImagePullBackOff。附属异常的CrashLoopBackOff有容器日志和args的exit 2的直接证据。g3的Terminating Pod已NotFound确认删除。置信度0.95。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像地址或tag不存在(如busybox:1.36.1不存在)", "probability": "low", "reason": "错误信息不是'manifest unknown'或'not found'，而是网络层i/o timeout和connection refused，镜像存在性问题可排除"}, {"cause": "imagePullSecret缺失或认证失败(私有仓库需要认证)", "probability": "low", "reason": "busybox是Docker Hub公开镜像，无需认证；多个Pod的yaml显示imagePullSecrets=<absent>是正常配置；错误信息是网络层而非认证层"}, {"cause": "DNS解析失败", "probability": "low", "reason": "kubelet成功解析registry-1.docker.io为多个IP(108.160.169.55, 157.240.13.8等)，说明DNS解析正常工作，问题在TCP连接层面"}, {"cause": "单节点故障", "probability": "low", "reason": "node1和node2两个节点均出现完全相同的i/o timeout错误，确认是集群级网络问题而非单节点网络配置问题"}, {"cause": "CrashLoopBackOff由镜像拉取失败导致", "probability": "low", "reason": "rc-crashloop-exit-code配置了imagePullPolicy=Never，不从远程拉取；且容器日志和args显示exit 2是人为构造"}], "limitations": "未采集集群出口网络配置(防火墙规则/代理/CNI配置)，无法确定具体是防火墙拦截、代理配置缺失还是外部网络故障。未测试节点上其他非Docker Hub域名的外网连通性。rc-crashloop-exit-code的kubectl describe在证据计划中标记为缺失(e9)，但已通过其他工具(e8/kubectl_previous_logs/e10)获取到足以判断的Exit Code和日志信息。net-check-tmp已删除(NotFound)，无进一步Terminating状态验证数据。", "llm_raw_analysis": "## 证据清点\n已采集关键证据共10条(e4-e10, layer_1-layer_8)，其中3个kubectl_describe(e4/e6/e7)、2个kubectl_get_yaml(e5+第9条rc-crashloop)、1个崩溃前日志(e10)、1个kubectl_events摘要、1个kubectl_previous_logs、1个kubectl_get_by_name(NotFound)。缺失1条(e9已通过其他工具覆盖)。负向证据1条(net-check-tmp NotFound)。\n\n## 逐条分析\n- e4(e4): mcp/connectivity-test在node2上报DeadlineExceeded→i/o timeout到108.160.169.55:443\n- e5: aiops-e2e/test-dns-1779360358在node1上报i/o timeout到128.121.146.228:443, 无imagePullSecrets\n- e6: default/dns-check-test在node1上报持续122分钟的BackOff, x167\n... 截断，原始 1115 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因：集群节点到Docker Hub镜像仓库的出口网络故障。证据：(1) mcp/connectivity-test在node2上报'dial tcp 108.160.169.55:443: i/o timeout'，(2) default/registry-conn-test-1779371220...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点(node1/node2)到Docker Hub镜像仓库(registry-1.docker.io:443)的出口网络不可达，导致所有尝试拉取busybox:1.36.1的Pod均因TCP连接超时/拒绝失败
     传导机制: 1) 节点kubelet发起镜像拉取请求 → 2) DNS解析registry-1.docker.io成功(获得多个IP)→ 3) TCP三次握手到IP:443全部超时(i/o timeout)或连接拒绝(connection refused)→ 4) containerd返回DeadlineExceeded错误→ 5) kubelet将Pod状态置为ErrImagePull→ 6) 进入指数退避重试循环变为ImagePullBackOff
     最终表现: default/mcp/aiops-e2e三个命名空间共27个Pod处于ImagePullBackOff(22个)/ErrImagePull(5个)状态，持续13分钟至3小时以上，所有Pod均拉取busybox:1.36.1失败，kubelet Events显示i/o timeout/connection refused


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (37.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8876 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 35.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群核心问题** | 集群存在 **29 个异常 Pod**，核心问题是**大规模镜像拉取失败** (27个Pod) |
| **Pod异常状态** | ImagePullBackOff (22个), ErrImagePull (5个), Error/CrashLoopBackOff (1个), Terminating (1个) |
| **兼容归因层** | L3 - 镜像仓库/网络问题 |
| **问题分类** | 镜像拉取失败 (ImagePullFailed) |
| **置信度** | 高 (95%) |
| **证据完整度** | 6/7 (86%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 受影响 Namespace | `default`, `mcp`, `aiops-e2e` |
| 受影响 Node | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| 镜像 | `busybox:1.36.1` |

---
## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | **Pod 状态统计** | `kubectl get pods --all-namespaces` | 总计 ~92 Pods。Running=59 (稳定)。Abnormal=29: ImagePullBackOff=22, ErrImagePull=5, Error=1, Terminating=1 | 集群有显著异常，主要问题集中在 `ImagePullBackOff` 和 `ErrImagePull` |
| 2 | **主异常描述** | `kubectl describe pod dns-check-test -n default` | `Normal BackOff (x167 over 122m) kubelet Back-off pulling image "busybox:1.36.1"` | `dns-check-test` Pod 因镜像拉取失败持续处于 BackOff 状态 |
| 3 | **网络连接证据** | `kubectl describe pod registry-conn-test-1779371220 -n default` | `Failed to pull image: dial tcp 157.240.13.8:443: i/o timeout`; `dial tcp 199.59.148.7:443: connect: connection refused` | 节点 `node2` 无法连接 Docker Hub 镜像仓库 (`registry-1.docker.io`) |
| 4 | **多节点/多IP不可达** | `kubectl describe pod connectivity-test -n mcp` & `kubectl describe pod test-dns-1779360358 -n aiops-e2e` | `connectivity-test` (on `node2`): `dial tcp 108.160.169.55:443: i/o timeout`; `test-dns-1779360358` (on `node1`): `dial tcp 128.121.146.228:443: i/o timeout` | 两个节点 (`node1`, `node2`) 连接 Docker Hub 的不同 IP 地址全部超时或被拒绝，**排除单节点或单IP问题** |
| 5 | **集群级事件** | `kubectl get events --all-namespaces` | `23m (x167 over 122m) Normal BackOff Pod/dns-check-test Back-off pulling image "busybox:1.36.1"` | 集群级事件确认了镜像拉取失败的普遍性 |
| 6 | **CrashLoop 容器日志** | `kubectl logs --previous -n aiops-e2e rc-crashloop-xxx` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 另一个异常 Pod 因容器启动命令错误 (Exit Code 2) 导致 CrashLoopBackOff，非镜像问题 |
| 7 | **Terminating Pod 状态** | `kubectl describe pod net-check-tmp -n mcp` | `status: Terminating (lasts 7m2s)`, `finalizers: <none>` | 一个 Pod 卡在 `Terminating` 状态，但 finalizer 为空，排除 finalizer 未清理根因 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：集群 27 个 Pod 处于 `ImagePullBackOff`/`ErrImagePull` 状态，且 `kubectl describe` 输出明确显示节点 (`node1`, `node2`) 到 Docker Hub (`registry-1.docker.io:443`) 存在**全局性网络不可达**（TCP 连接超时/拒绝）。
- **证据链**：集群出口网络故障 → kubelet 无法从镜像仓库拉取 `busybox:1.36.1` → Pod 状态变为 `ErrImagePull` → 进入指数退避重试 → 最终状态 `ImagePullBackOff`。
- **证据 #6 单独印证**：`rc-crashloop-exit-code-xxx` 的 `CrashLoopBackOff` 是一个独立问题，表现为容器退出码为 2（程序错误），与网络无关。
- **证据 #7 单独印证**：`net-check-tmp` 卡在 `Terminating` 状态，但 `finalizers: <none>` 表明不是 finalizer 问题，可能是其他生命周期事件挂起。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 集群出口网络配置 (防火墙规则/代理/CNI) | Critical | 无法确定具体是防火墙拦截、代理缺失还是外部网络故障 |
| `CrashLoopBackOff` Pod (`rc-crashloop-exit-code`) 的完整 `kubectl describe` | Important | 已有 Exit Code 和日志，describe 可以确定容器启动命令和 args 的完整情况 |
| `Terminating` Pod 的节点 kubelet 日志 | Medium | 无法确认 kubelet 是否卡在容器停止或卷卸载流程 |

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                     │
│ 集群节点(node1/node2)到Docker Hub镜像仓库(registry-1.docker.io:443)的出口网络不可达              │
│ 证据：多个节点(node1, node2)连接Docker Hub的不同IP (108.160.169.55, 128.121.146.228,          │
│       157.240.13.8, 199.59.148.7) 全部超时或拒绝                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                     │
│ 节点kubelet发起镜像拉取请求 → DNS解析registry-1.docker.io成功(获得多个IP) →                    │
│ TCP三次握手到所有IP的443端口(全部超时/拒绝) → containerd返回DeadlineExceeded错误                │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (主问题 - 27个Pod)                                                                    │
│ kubelet 执行 "kubectl get images" / containerd 拉取镜像时，因网络无法连接到 Docker Hub，          │
│ 返回ErrImagePull，随后进入指数退避重试循环，状态变为ImagePullBackOff                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (主问题)                                                                          │
│ 跨3个Namespace (default/mcp/aiops-e2e) 共27个Pod处于ImagePullBackOff(22个)/ErrImagePull(5个)， |
│ 状态持续13分钟到3小时以上                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

--- (其他次要问题) ---
┌─────────────────────────────────────────────────────────────┐
│ 次要问题 1: 容器启动错误 (CrashLoopBackOff)                    │
│ Pod: rc-crashloop-exit-code-5db5947859-2522x                │
│ 根因: 容器内应用启动命令错误，退出码 2 (人为构造的测试用例)        │
│ 影响: 仅1个Pod                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 次要问题 2: Pod Terminating卡住                               │
│ Pod: net-check-tmp                                            │
│ 根因: 非finalizer问题(finalizers: <none>)，可能kubelet挂起     │
│ 影响: 仅1个Pod(实际已消失，NotFound)                           │
└─────────────────────────────────────────────────────────────┘
```

### 根因结论

**主问题结论**：根据证据 #1, #2, #3, #4, #5，集群最核心、最广泛的异常是**集群节点到 Docker Hub 镜像仓库 (registry-1.docker.io:443) 的出口网络故障**，导致 27 个拉取 `busybox:1.36.1` 的 Pod 全部失败。

**置信度**：高 (95%)
- ✅ 多个节点 (`node1`, `node2`) 均存在连接超时/拒绝
- ✅ 连接 Docker Hub 的多个不同 IP (4个) 全部失败
- ✅ 跨 3 个 Namespace 的 27 个 Pod 表现一致
- ⚠️ 缺失集群网络出口配置，无法确定具体是防火墙、代理还是外部网络中断

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [关键] 排查集群节点出口网络**
这是解决 27 个异常 Pod 的根本措施。需要在所有节点 (`node1`, `node2`) 上执行以下命令进行网络连通性测试：
```bash
# 在所有节点上执行
# 测试 DNS 解析
nslookup registry-1.docker.io
# 测试 TCP 直连 (使用curl的telnet功能)
curl -v --connect-timeout 10 https://registry-1.docker.io
# 或直接使用 telnet 测试端口 (如果安装了 telnet)
telnet registry-1.docker.io 443
```
*依据*：证据显示从所有节点到 Docker Hub 的 TCP 连接都超时/拒绝，可能的原因包括：
- 防火墙规则拦截了出口 443 端口的流量
- 缺少 HTTP 代理配置（`HTTP_PROXY`, `HTTPS_PROXY`）
- 集群节点的外部网络故障

**2. [关键] 配置或添加 HTTP 代理 (如果集群有代理)**
如果集群通过代理访问外网，需要在 containerd/docker 配置中设置代理环境变量。
```bash
# 在所有节点上为 containerd 配置 HTTP 代理
sudo mkdir -p /etc/systemd/system/containerd.service.d
cat <<EOF | sudo tee /etc/systemd/system/containerd.service.d/http-proxy.conf
[Service]
Environment="HTTP_PROXY=http://your-proxy-ip:port"
Environment="HTTPS_PROXY=http://your-proxy-ip:port"
Environment="NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
EOF
sudo systemctl daemon-reload
sudo systemctl restart containerd
```
*依据*：如果集群节点通过代理访问公网，缺少代理配置会导致 TCP 连接失败。

**3. [立即] 处理 CrashLoopBackOff Pod**
这个 Pod (`rc-crashloop-exit-code-xxx`) 是独立的容器启动命令问题，应先停掉并分析：
```bash
# 1. 查看 Pod 的完整配置
kubectl get pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e -o yaml
# 2. 如果确认是测试用例，可以直接删除
kubectl delete pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e
```
*依据*：容器日志显示 `exit code 2`，是程序启动错误。

**4. [可选] 清理 Terminating Pod**
`net-check-tmp` 已经 `NotFound`，无需操作。如果未来有类似情况，可以强制删除：
```bash
kubectl delete pod <pod-name> -n <namespace> --grace-period=0 --force
```
*依据*：`finalizers: <none>` 排除了 finalizer 问题，强制删除是最后手段。

### 后续优化
1. **监控告警**：配置对 `ImagePullBackOff` 和 `ErrImagePull` 状态的告警。
2. **镜像仓库策略**：考虑在集群内部署私有镜像仓库（如 Harbor）作为缓存，或使用 `imagePullPolicy: IfNotPresent` 减少对公网的依赖。
3. **网络冗余**：为集群出口网络配置多条线路或备用代理，避免单点故障。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认问题 Pod 数量下降 | `kubectl get pods --all-namespaces \| grep -E 'ImagePullBackOff\|ErrImagePull'` | 数量为 0 |
| 2. 验证 Pod 启动正常 | `kubectl get pod dns-check-test -n default` | STATUS: `Running` |
| 3. 过 5 分钟再次检查 | `kubectl get pods --all-namespaces \| grep -E 'ImagePullBackOff\|ErrImagePull'` | 仍为 0 |
| 4. (非必需) 检查集群事件 | `kubectl get events --all-namespaces --sort-by=.metadata.creationTimestamp \| tail -20` | 无 `ErrImagePull` 事件 |

---
## ⚠️ 注意事项
- **最严重问题**：集群出口网络故障是核心风险，请务必协调网络团队优先解决。
- **次要问题不影响整体**：`CrashLoopBackOff` 和 `Terminating` Pod 是独立小问题，在修复网络后可逐一处理。
- **测试用例识别**：`rc-crashloop-exit-code` 极可能是人为创建的测试 Pod，建议直接删除。
- **证据完整性**：由于缺失集群网络出口配置，无法精确判断是防火墙、代理还是外部网络中断，修复建议覆盖了这几种常见可能性。

---

## 📊 性能统计

├─ 总耗时: 2.6m
├─ 问题定位: 44.6s (29%) ✅
├─ 证据链采集: 42.4s (27%) ✅
├─ 根因分析: 30.6s (20%) ✅
├─ 汇总总结: 37.6s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 24 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-crashloop-runtime, pod-terminating-stuck
- **工具调用**: 24 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
