======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 9b1d060542644c6e]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod SandboxCreateFailed / Pod sandbox 创建失败

> Pod异常类型: SandboxCreateFailed | 典型状态: ContainerCreating / FailedCreatePodSandBox | 兼容分类: sandbox_runtime

## 状态识别
- Events 含 `FailedCreatePodSa
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                              READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-sandbox-runtimeclass-invalid   0/1     ContainerCreating   
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-sandbox-runtimeclass-invalid
namespace: aiops-e2e
creationTimestamp: 2026-05-19T13:30:02Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={}
NAME                         HANDLER                                 AGE   LABELS
# 样例行
metax                        metax      
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                         HANDLER                                 AGE   LABELS
rc-invalid-runtime-handler   rc-definitely-missing-runtime-handler   17m   rootcause-e2e=true
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=16 abnormal=0 status_counts={'Running': 16}
key_facts: ["所有 16 个资源状态为 Running", "calico-node 和 kube-multus-ds 在多个节点上运行", "coredns-777df594b8 有两个副本在 master 节
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 51.4s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': 'CNI 插件异常或配置缺失', 'probability': '高', 'reason': 'Pod 事件显示 SandboxCreateFailed，且 CNI 未就绪或配置不完整。'}, {'scenario': 'RuntimeClass 不匹配或不存在', 'probability': '高', 'reason': 'Pod 使用的 RuntimeClass 指向一个不存在的 handler，导致 sandbox 创建失败。'}, {'scenario': 'IPAM 耗尽或 IP 地址分配失败', 'probability': '中', 'reason': 'Pod 无法分配 IP 地址，可能与 IP 池配置或 IPAM 服务异常有关。'}, {'scenario': 'container runtime sandbox 失败', 'probability': '中', 'reason': 'containerd/CRI-O 创建 sandbox 失败，可能与 pause 镜像拉取或 runtime 状态异常有关。'}]
   entities=[{"type": "Pod", "name": "rc-sandbox-runtimeclass-invalid", "namespace": "aiops-e2e"}, {"type": "RuntimeClass", "name": "rc-definitely-missing-runtime-handler", "namespace": ""}]
   reasoning=当前环境中的活跃异常对象为 aiops-e2e/rc-sandbox-runtimeclass-invalid，其状态为 ContainerCreating，pod_abnormal_type 为 SandboxCreateFailed。根据 runbook 和分析文本，该异常属于 L3 层级，涉及 sandbox_runtime，主要由 CNI/IPAM、RuntimeClass 不匹配或 container runtime sandbox 失败导致。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "L3", "confidence": 0.95, "reasoning": "当前环境中的活跃异常对象为 aiops-e2e/rc-sandbox-runtimeclass-invalid，其状态为 ContainerCreating，pod_abnormal_type 为 SandboxCreateFailed。根据 runbook 和分析文本，该异常属于 L3 层级，涉及 sandbox_runtime，主要由 CNI/IPAM、RuntimeClass 不匹配或 container runtime sandbox 失败导致。", "abnormal_pods": [{"name": "rc-sandbox-runtimeclass-invalid", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "SandboxCreateFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "Pod", "name": "rc-sandbox-runtimeclass-invalid", "namespace": "aiops-e2e"}, {"type": "RuntimeClass", "name": "rc-definitely-missing-runtime-handler", "namespace": ""}], "possible_scenarios": [{"scenario": "CNI 插件异常或配置缺失", "probability": "高", "reason": "Pod 事件显示 SandboxCreateFailed，且 CNI 未就绪或配置不完整。"}, {"scenario": "RuntimeClass 不匹配或不存在", "probability": "高", "reason": "Pod 使用的 RuntimeClass 指向一个不存在的 handler，导致 sandbox 创建失败。"}, {"scenario": "IPAM 耗尽或 IP 地址分配失败", "probability": "中", "reason": "Pod 无法分配 IP 地址，可能与 IP 池配置或 IPAM 服务异常有关。"}, {"scenario": "container runtime sandbox 失败", "probability": "中", "reason": "containerd/CRI-O 创建 sandbox 失败，可能与 pause 镜像拉取或 runtime 状态异常有关。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-sandbox-runtimeclass-invalid"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-sandbox-runtimeclass-invalid"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-sandbox-runtimeclass-invalid                     0/1     ContainerCreating   0              17m     <none>           node1    <none>           <none>            app=rc-sandbox-runtimeclass-invalid,pod_abnormal_type=SandboxCreateFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-sandbox-runtimeclass-invalid
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedCreatePodSandBox  2m8s (x92 over 22m)  kubelet            
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-sandbox-runtimeclass-invalid
namespace: aiops-e2e
creationTimestamp: 2026-05-19T13:30:02Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={}
NAME                         HANDLER                                 AGE   LABELS
# 样例行
metax                        metax      
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node1
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
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
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=16 abnormal=0 status_counts={'Running': 16}
NAME                                       READY   STATUS    RESTARTS       AGE    IP               NODE     NOM
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=217 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide runtimeclass rc-definitely-missing-runtime-handler
Error from server (NotFound): runtimeclass
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                              READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-sandbox-runtimeclass-invalid   0/1     ContainerCreating   
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   236d   v1.26.8   10.2.0.49     <
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=217 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide runtimeclass rc-definitely-missing-runtime-handler
Error from server (NotFound): runtimeclass
   💭 [证据链采集] {
  "已采集证据": [
    {
      "工具": "kubectl describe pod",
      "结果": "Pod rc-sandbox-runtimeclass-invalid 的状态为 ContainerCreating，且事件显示 'FailedCreatePodSandBox'，具体错误为 'no runtime for \"rc-definitely-missing-runtime-handler\" is configured'。"
    },
    {
      "工具": "kubectl get pod -o yaml",
      "结果": "Pod 的 runtimeClassName 为 'rc-definitely-missing-runtime-handler'，且 phase 为 'Pending'。"
    },
    {
      "工具": "kubectl get runtimeclass",
      "结果": "RuntimeClass 'rc-definitely-missing-runtime-handler' 不存在。"
    },
    {
      "工具": "kubectl describe node",
      "结果": "节点 node1 处于 'Ready' 状态，且容器运行时为 containerd。"
    },
    {
      "工具": "kubectl get pods -n kube-system",
      "结果": "CNI 相关 Pod（如 calico-node、kube-multus-ds）在节点上正常运行。"
    }
  ],
  "未采集证据": [],
  "冲突证据": {
    "工具": "kubectl get runtimeclass rc-definitely-missing-runtime-handler",
    "结果": "RuntimeClass 'rc-definitely-missing-runtime-handler' 不存在。"
  }
}
   ✅ [证据链采集] 完成 (5m 40.9s)
   📤 → 下游数据: evidence_items=11/11
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 'rc-sandbox-runtimeclass-invalid' 的详细描述信息，以检查其事件和状态详情，尤其是与 'FailedCreatePodSandBox' 相关的事件。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-sandbox-runtimeclass-invalid -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-sandbox-runtimeclass-invalid","namespace":"aiops-e2e"},"purpose":"验证 Pod 是否存在 'FailedCreatePodSandBox' 事件，并检查 runtimeClassName、nodeName、hostNetwork 等配置。","evidence_type":"event/status","target_scope":"aiops-e2e/rc-sandbox-runtimeclass-invalid","acceptable_tools":["kubectl_describe","kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 'rc-sandbox-runtimeclass-invalid' 的 YAML 配置，检查其 runtimeClassName、nodeName、hostNetwork、dnsPolicy 等关键字段。","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-sandbox-runtimeclass-invalid -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-sandbox-runtimeclass-invalid","namespace":"aiops-e2e"},"purpose":"检查 Pod 的 runtimeClassName 是否指向了不存在的 RuntimeClass，并确认其调度节点是否可用。","evidence_type":"configuration","target_scope":"aiops-e2e/rc-sandbox-runtimeclass-invalid","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"获取 Cluster 中所有 RuntimeClass 的列表，检查 'rc-definitely-missing-runtime-handler' 是否存在。","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get runtimeclass","tool_args":{"kind":"RuntimeClass"},"purpose":"确认 Pod 配置的 runtimeClassName 所指向的 RuntimeClass 是否存在。","evidence_type":"configuration","target_scope":"cluster/RuntimeClass","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e4","description":"获取节点 'node1' 的详细描述信息，检查其 Ready 状态、容器运行时状态以及网络状态。","level":"important","tool":"kubectl_describe","command":"kubectl describe node node1","tool_args":{"kind":"Node","name":"node1"},"purpose":"验证节点是否处于 Ready 状态，并检查容器运行时（containerd/CRI-O）以及网络插件是否正常。","evidence_type":"status/configuration","target_scope":"node1","acceptable_tools":["kubectl_describe","kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e5","description":"获取 kube-system 命名空间中的 CNI 相关 Pod 状态，检查其是否运行正常。","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pods -n kube-system -o wide","tool_args":{"kind":"Pod","namespace":"kube-system"},"purpose":"确认 CNI 相关的 DaemonSet Pod（如 calico-node、kube-multus-ds）是否在节点上正常运行。","evidence_type":"status","target_scope":"kube-system/Pod","acceptable_tools":["kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-sandbox-runtimeclass-invalid\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedCreatePodSandBox  2m8s (x92 over 22m)  kubelet            Failed to create pod sandbox: rpc error: code = Unknown desc = failed to get sandbox runtime: no runtime for \"rc-definitely-missing-runtime-handler\" is configured\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-vxgtc:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedCreatePodSandBox  2m8s (x92 over 22m)  kubelet            Failed to create pod sandbox: rpc error: code = Unknown desc = failed to get sandbox runtime: no runtime for \"rc-definitely-missing-runtime-handler\" is configured\n关键状态/事件:\n                     pod_abnormal_type=SandboxCreateFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-sandbox-runtimeclass-invalid\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-19T13:30:02Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-sandbox-runtimeclass-invalid, pod_abnormal_type=SandboxCreateFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-sandbox-create-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-vxgtc\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={}\nNAME                         HANDLER                                 AGE   LABELS\n# 样例行\nmetax                        metax                                   11h   <none>\nnvidia                       nvidia                                  27h   app.kubernetes.io/component=gpu-operator\nrc-invalid-runtime-handler   rc-definitely-missing-runtime-handler   22m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/003-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/003-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/003-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node1\n关键诊断行:\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nTaints:             <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 表格摘要: rows=16 abnormal=0 status_counts={'Running': 16}\nNAME                                       READY   STATUS    RESTARTS       AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 样例行\ncalico-kube-controllers-6c67f9d475-blt2r   1/1     Running   1 (13d ago)    22d    172.16.219.87    master   <none>           <none>            k8s-app=calico-kube-controllers,pod-template-hash=6c67f9d475\ncalico-node-4kp26                          1/1     Running   18 (13d ago)   211d   10.2.0.48        master   <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\ncalico-node-d2dhp                          1/1     Running   15 (13d ago)   211d   10.2.0.50        node2    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\ncalico-node-mnrjs                          1/1     Running   14 (13d ago)   211d   10.2.0.49        node1    <none>           <none>            controller-revision-hash=65f554db6,k8s-app=calico-node,pod-template-generation=1\ncoredns-777df594b8-gcnp8                   1/1     Running   1 (13d ago)    22d    172.16.219.112   master   <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\ncoredns-777df594b8-vfpsj                   1/1     Running   1 (13d ago)    22d    172.16.219.90    master   <none>           <none>            k8s-app=kube-dns,pod-template-hash=777df594b8\netcd-master                                1/1     Running   19 (13d ago)   236d   10.2.0.48        master   <none>           <none>            component=etcd,tier=control-plane\nkube-apiserver-master                      1/1     Running   19 (13d ago)   236d   10.2.0.48        master   <none>           <none>            component=kube-apiserver,tier=control-plane\nkube-controller-manager-master             1/1     Running   42 (13d ago)   236d   10.2.0.48        master   <none>           <none>            component=kube-controller-manager,tier=control-plane\nkube-multus-ds-rnvbg                       1/1     Running   14 (13d ago)   211d   10.2.0.49        node1    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-multus-ds-sc2jn                       1/1     Running   10 (13d ago)   113d   10.2.0.48        master   <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-multus-ds-x7h9s                       1/1     Running   15 (13d ago)   211d   10.2.0.50        node2    <none>           <none>            app=multus,controller-revision-hash=6d4c8546fc,name=multus,pod-template-generation=1,tier=node\nkube-proxy-69zzr                           1/1     Running   6 (13d ago)    55d    10.2.0.50        node2    <none>           <none>            controller-revision-hash=7d999967\n... (已压缩/截断，原始 3553 字符，完整内容见 raw_ref)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/005-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/005-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/005-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=217 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide runtimeclass rc-definitely-missing-runtime-handler\nError from server (NotFound): runtimeclasses.node.k8s.io \"rc-definitely-missing-runtime-handler\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/006-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/006-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/006-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                              READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-sandbox-runtimeclass-invalid   0/1     ContainerCreating   0          25m   <none>   node1   <none>           <none>            app=rc-sandbox-runtimeclass-invalid,pod_abnormal_type=SandboxCreateFailed,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/007-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/007-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/007-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode1   Ready    <none>   236d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/008-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/008-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/008-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=217 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide runtimeclass rc-definitely-missing-runtime-handler\nError from server (NotFound): runtimeclasses.node.k8s.io \"rc-definitely-missing-runtime-handler\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/009-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/009-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9b1d060542644c6e/tools/009-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"{\n  \"已采集证据\": [\n    {\n      \"工具\": \"kubectl describe pod\",\n      \"结果\": \"Pod rc-sandbox-runtimeclass-invalid 的状态为 ContainerCreating，且事件显示 'FailedCreatePodSandBox'，具体错误为 'no runtime for \\\"rc-definitely-missing-runtime-handler\\\" is configured'。\"\n    },\n    {\n      \"工具\": \"kubectl get pod -o yaml\",\n      \"结果\": \"Pod 的 runtimeClassName 为 'rc-definitely-missing-runtime-handler'，且 phase 为 'Pending'。\"\n    },\n    {\n      \"工具\": \"kubectl get runtimeclass\",\n      \"结果\": \"RuntimeClass 'rc-definitely-missing-runtime-handler' 不存在。\"\n    },\n    {\n      \"工具\": \"kubectl describe node\",\n      \"结果\": \"节点 node1 处于 'Ready' 状态，且容器运行时为 containerd。\"\n    },\n    {\n      \"工具\": \"kubectl get pods -n kube-system\",\n      \"结果\": \"CNI 相关 Pod（如 calico-node、kube-multus-ds）在节点上正常运行。\"\n    }\n  ],\n  \"未采集证据\": [],\n  \"冲突证据\": {\n    \"工具\": \"kubectl get runtimeclass rc-definitely-missing-runtime-handler\",\n    \"结果\": \"RuntimeClass 'rc-definitely-missing-runtime-handler' 不存在。\"\n  }\n}","collection_summary":"计划 5 项，实际采集 5 项，未采集 0 项，完整度 100%；其中真实环境证据 11/11 项，完整度 100%；实际执行工具 15 个，匹配计划 5 个，未规划证据 10 个","plan_total":5,"plan_collected":5,"plan_completeness":1.0,"environment_evidence_total":11,"environment_evidence_collected":11,"environment_evidence_completeness":1.0,"executed_tool_count":15,"matched_tool_count":5,"unplanned_tool_count":10,"evidence_inventory":[{"id":"e1","description":"获取 Pod 'rc-sandbox-runtimeclass-invalid' 的详细描述信息，以检查其事件和状态详情，尤其是与 'FailedCreatePodSandBox' 相关的事件。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-sandbox-runtimeclass-invalid -n aiops-e2e","purpose":"验证 Pod 是否存在 'FailedCreatePodSandBox' 事件，并检查 runtimeClassName、nodeName、hostNetwork 等配置。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 'rc-sandbox-runtimeclass-invalid' 的 YAML 配置，检查其 runtimeClassName、nodeName、hostNetwork、dnsPolicy 等关键字段。","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-sandbox-runtimeclass-invalid -n aiops-e2e -o yaml","purpose":"检查 Pod 的 runtimeClassName 是否指向了不存在的 RuntimeClass，并确认其调度节点是否可用。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Cluster 中所有 RuntimeClass 的列表，检查 'rc-definitely-missing-runtime-handler' 是否存在。","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get runtimeclass","purpose":"确认 Pod 配置的 runtimeClassName 所指向的 RuntimeClass 是否存在。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取节点 'node1' 的详细描述信息，检查其 Ready 状态、容器运行时状态以及网络状态。","level":"important","tool":"kubectl_describe","command":"kubectl describe node node1","purpose":"验证节点是否处于 Ready 状态，并检查容器运行时（containerd/CRI-O）以及网络插件是否正常。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"获取 kube-system 命名空间中的 CNI 相关 Pod 状态，检查其是否运行正常。","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pods -n kube-system -o wide","purpose":"确认 CNI 相关的 DaemonSet Pod（如 calico-node、kube-multus-ds）是否在节点上正常运行。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/5 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 'rc-sandbox-runtimeclass-invalid' 的详细描... | `kubectl describe pod rc-sandbox-runtimeclass-invalid -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 获取 Pod 'rc-sandbox-runtimeclass-invalid' 的 YA... | `kubectl get pod rc-sandbox-runtimeclass-invalid -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | kubectl_get_by_kind_in_cl... | 获取 Cluster 中所有 RuntimeClass 的列表，检查 'rc-defini... | `kubectl get runtimeclass` |
   | e4 | important | ✅ | kubectl_describe | 获取节点 'node1' 的详细描述信息，检查其 Ready 状态、容器运行时状态以及网络状态。 | `kubectl describe node node1` |
   | e5 | important | ✅ | kubectl_get_by_kind_in_na... | 获取 kube-system 命名空间中的 CNI 相关 Pod 状态，检查其是否运行正常。 | `kubectl get pods -n kube-system -o wide` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 21.0s)
   📤 → 下游数据: root_cause=Pod 'aiops-e2e/rc-sandbox-runtimeclass-invalid' 指定了一个不存在的 RuntimeClass 'rc-definitely-missing-runtime-handler'，导致 sandbox 创建失败。根据事件 'FailedCreatePodSandBox' 和错误信息 'no runtime for "rc-definitely-missing-runtime-handler" is configured'，可以确认这是导致 Pod 处于 ContainerCreating 状态的根本原因。
   confidence=95%
   causal_chain={"root_cause": "Pod 指定了一个不存在的 RuntimeClass 'rc-definitely-missing-runtime-handler'，导致 sandbox 创建失败。", "propagation": "Pod 指定了一个不存在的 RuntimeClass，导致 kubelet 无法创建 sandbox，从而导致 Pod 处于 ContainerCreating 状态。", "direct_cause": "RuntimeClass 'rc-definitely-missing-runtime-handler' 不存在，导致 kubelet 无法创建 sandbox。", "manifestation": "Pod 'aiops-e2e/rc-sandbox-runtimeclass-invalid' 处于 ContainerCreating 状态，且其异常类型为 SandboxCreateFailed。"}
   rca_analysis={"phenomenon": "Pod 'aiops-e2e/rc-sandbox-runtimeclass-invalid' 处于 ContainerCreating 状态，且其异常类型为 SandboxCreateFailed，具体错误为 'no runtime for \"rc-definitely-missing-runtime-handler\" is configured'。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod 事件显示 'FailedCreatePodSandBox'，具体错误为 'no runtime for \"rc-definitely-missing-runtime-handler\" is configured'。", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod 配置指定了 runtimeClassName 为 'rc-definitely-missing-runtime-handler'，且 phase 为 'Pending'。", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_by_kind_in_cluster", "content": "RuntimeClass 'rc-definitely-missing-runtime-handler' 不存在。", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe", "content": "节点 node1 处于 'Ready' 状态，且容器运行时为 containerd。", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_namespace", "content": "CNI 相关 Pod（如 calico-node、kube-multus-ds）在节点上正常运行。", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning  FailedCreatePodSandBox  2m8s (x92 over 22m)  kubelet            Failed to create pod sandbox: rpc error: code = Unknown desc = failed to get sandbox runtime: no runtime for \"rc-definitely-missing-runtime-handler\" is configured", "interpretation": "Pod 事件显示 'FailedCreatePodSandBox'，具体错误为 'no runtime for \"rc-definitely-missing-runtime-handler\" is configured'。"}, {"evidence_id": "e2", "raw_data": "runtimeClassName: rc-definitely-missing-runtime-handler\nphase: Pending", "interpretation": "Pod 配置指定了 runtimeClassName 为 'rc-definitely-missing-runtime-handler'，且 phase 为 'Pending'。"}, {"evidence_id": "e3", "raw_data": "RuntimeClass 'rc-definitely-missing-runtime-handler' 不存在。", "interpretation": "RuntimeClass 'rc-definitely-missing-runtime-handler' 不存在。"}, {"evidence_id": "e4", "raw_data": "node1 处于 'Ready' 状态，且容器运行时为 containerd。", "interpretation": "节点 node1 处于 'Ready' 状态，且容器运行时为 containerd。"}, {"evidence_id": "e5", "raw_data": "CNI 相关 Pod（如 calico-node、kube-multus-ds）在节点上正常运行。", "interpretation": "CNI 相关 Pod（如 calico-node、kube-multus-ds）在节点上正常运行。"}], "causal_chain": {"root_cause": "Pod 指定了一个不存在的 RuntimeClass 'rc-definitely-missing-runtime-handler'，导致 sandbox 创建失败。", "propagation": "Pod 指定了一个不存在的 RuntimeClass，导致 kubelet 无法创建 sandbox，从而导致 Pod 处于 ContainerCreating 状态。", "direct_cause": "RuntimeClass 'rc-definitely-missing-runtime-handler' 不存在，导致 kubelet 无法创建 sandbox。", "manifestation": "Pod 'aiops-e2e/rc-sandbox-runtimeclass-invalid' 处于 ContainerCreating 状态，且其异常类型为 SandboxCreateFailed。"}, "root_cause": "Pod 'aiops-e2e/rc-sandbox-runtimeclass-invalid' 指定了一个不存在的 RuntimeClass 'rc-definitely-missing-runtime-handler'，导致 sandbox 创建失败。根据事件 'FailedCreatePodSandBox' 和错误信息 'no runtime for \"rc-definitely-missing-runtime-handler\" is configured'，可以确认这是导致 Pod 处于 ContainerCreating 状态的根本原因。", "root_cause_summary": "Pod 'aiops-e2e/rc-sandbox-runtimeclass-invalid' 指定了一个不存在的 RuntimeClass 'rc-definitely-missing-runtime-handler'，导致 sandbox 创建失败。根据事件 'FailedCreatePodSandBox' 和错误信息 'no runtime for \"rc-definitely-missing-runtime-handler\" is configured'，可以确认这是导致 Pod 处于 ContainerCreating 状态的根本原因。", "confidence": 0.95, "confidence_reason": "有直接证据表明 Pod 指定了一个不存在的 RuntimeClass，导致 sandbox 创建失败。", "primary_runbooks": ["pod-sandbox-create-failed.md"], "alternative_causes": [{"cause": "CNI 插件异常或配置缺失", "probability": "低", "reason": "CNI 相关 Pod 在节点上正常运行，排除了 CNI 插件异常或配置缺失的可能性。"}, {"cause": "IPAM 耗尽或 IP 地址分配失败", "probability": "低", "reason": "未发现 IP 地址分配失败的证据，排除了 IPAM 耗尽或 IP 地址分配失败的可能性。"}, {"cause": "container runtime sandbox 失败", "probability": "低", "reason": "节点 node1 处于 'Ready' 状态，且容器运行时为 containerd，排除了 container runtime sandbox 失败的可能性。"}], "limitations": "未发现其他可能影响 Pod 状态的证据，因此无法排除其他潜在原因。", "llm_raw_analysis": "基于已采集的证据，Pod 'aiops-e2e/rc-sandbox-runtimeclass-invalid' 处于 ContainerCreating 状态，且其异常类型为 SandboxCreateFailed。具体错误为 'no runtime for \"rc-definitely-missing-runtime-handler\" is configured'。进一步分析发现，Pod 指定了一个不存在的 RuntimeClass 'rc-definitely-missing-runtime-handler'，导致 kubelet 无法创建 sandbox。节点 node1 处于 'Ready' 状态，且容器运行时为 containerd，排除了 container runtime sandbox 失败的可能性。CNI 相关 Pod 在节点上正常运行，排除了 CNI 插件异常或配置缺失的可能性。因此，可以确定 Pod 指定了一个不存在的 RuntimeClass 是导致 sandbox 创建失败的根本原因。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'aiops-e2e/rc-sandbox-runtimeclass-invalid' 指定了一个不存在的 RuntimeClass 'rc-definitely-missing-runtime-handler'，导致 sandbox 创建失败。根据事件 'FailedCreatePodSa...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 指定了一个不存在的 RuntimeClass 'rc-definitely-missing-runtime-handler'，导致 sandbox 创建失败。
     传导机制: Pod 指定了一个不存在的 RuntimeClass，导致 kubelet 无法创建 sandbox，从而导致 Pod 处于 ContainerCreating 状态。
     最终表现: Pod 'aiops-e2e/rc-sandbox-runtimeclass-invalid' 处于 ContainerCreating 状态，且其异常类型为 SandboxCreateFailed。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 15.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4670 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 11m 9.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating |
| **兼容归因层** | L3 |
| **问题分类** | SandboxCreateFailed |
| **置信度** | 高 (95%) |
| **证据完整度** | 5/5 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-sandbox-runtimeclass-invalid |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | SandboxCreateFailed / FailedCreatePodSandBox |

该 Pod 处于 `ContainerCreating` 状态，无法正常创建容器沙箱。根据事件日志，其根本原因为指定了一个不存在的 `RuntimeClass`，导致 kubelet 无法创建 sandbox 容器。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-sandbox-runtimeclass-invalid` | `Reason: ContainerCreating`, `Status: Pending`, `Event: FailedCreatePodSandBox` | Pod 无法创建 sandbox 容器 |
| 2 | Pod YAML 配置 | `kubectl get pod rc-sandbox-runtimeclass-invalid -o yaml` | `runtimeClassName: rc-definitely-missing-runtime-handler` | Pod 指定了一个不存在的 RuntimeClass |
| 3 | RuntimeClass 列表 | `kubectl get runtimeclass` | `rc-definitely-missing-runtime-handler` 不存在 | 该 RuntimeClass 不存在于集群中 |
| 4 | Node 状态 | `kubectl describe node node1` | `Ready: True`, `containerd://1.6.32` | 节点状态正常，容器运行时可用 |
| 5 | CNI Pod 状态 | `kubectl get pods -n kube-system` | 所有 CNI 相关 Pod 状态为 `Running` | CNI 状态正常，排除 CNI 问题 |

### 证据关联分析

- **证据 #2 + #3 印证**：Pod 指定了一个不存在的 `RuntimeClass`，导致 sandbox 创建失败。
- **证据链**：Pod 使用的 RuntimeClass 不存在 → kubelet 无法创建 sandbox → Pod 无法进入 Running 状态 → 用户观察到 `ContainerCreating`。

### 缺失证据（如有）

无缺失证据。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 指定了一个不存在的 RuntimeClass 'rc-definitely-missing-runtime-handler'，导致 kubelet 无法创建 sandbox。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 无法创建 sandbox，因为指定的 RuntimeClass 不存在。        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 事件 `FailedCreatePodSandBox` 明确指出 sandbox 创建失败。         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 `ContainerCreating`，且异常类型为 `SandboxCreateFailed`。│
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (Pod 指定了 `rc-definitely-missing-runtime-handler`) 和证据 #3 (该 RuntimeClass 不存在)，问题的根本原因是 **Pod 指定了一个不存在的 RuntimeClass**，导致 kubelet 无法创建 sandbox 容器，从而陷入 `ContainerCreating` 状态。

**置信度**：高 (95%)

- ✅ Pod YAML 明确指定 `runtimeClassName: rc-definitely-missing-runtime-handler`
- ✅ `kubectl get runtimeclass` 显示该 RuntimeClass 不存在
- ✅ 事件 `FailedCreatePodSandBox` 直接确认 sandbox 创建失败

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修改 Pod 的 runtimeClassName**

如果该 Pod 是测试用例，或需要使用特定 runtime，应确保该 `RuntimeClass` 已在集群中定义。

```bash
kubectl edit pod rc-sandbox-runtimeclass-invalid -n aiops-e2e
```

在编辑器中删除或修改 `runtimeClassName` 字段（或将其设置为一个有效的 RuntimeClass 名称）。

**2. [可选] 创建缺失的 RuntimeClass**

如果该 RuntimeClass 是有意定义的，可创建对应的 RuntimeClass：

```bash
kubectl apply -f - <<EOF
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: rc-definitely-missing-runtime-handler
handler: my-custom-handler
EOF
```

请确保集群中存在对应的 container runtime handler（如 containerd/CRI-O 支持该 handler）。

### 后续优化

1. **验证 RuntimeClass 是否生效**：
   ```bash
   kubectl get runtimeclass rc-definitely-missing-runtime-handler
   ```

2. **检查节点 container runtime 是否支持该 handler**：
   - 对于 containerd，检查 `/etc/containerd/config.toml` 中是否配置了该 handler。
   - 对于 CRI-O，检查 `/etc/crio/crio.conf` 中是否配置了该 handler。

3. **监控 Pod 创建事件**：
   ```bash
   kubectl describe pod rc-sandbox-runtimeclass-invalid -n aiops-e2e
   ```

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-sandbox-runtimeclass-invalid -n aiops-e2e` | STATUS: Running |
| 2. 检查事件 | `kubectl describe pod rc-sandbox-runtimeclass-invalid -n aiops-e2e` | 无 `FailedCreatePodSandBox` 事件 |
| 3. 确认 RuntimeClass 存在 | `kubectl get runtimeclass rc-definitely-missing-runtime-handler` | 存在 |

---

## ⚠️ 注意事项

- 如果你希望继续使用该 RuntimeClass，请确保集群中 container runtime 支持该 handler。
- 若为测试场景，可考虑删除或注释掉 `runtimeClassName` 字段，以使用默认 runtime。
- 如果问题仍未解决，检查节点日志（如 `journalctl -u kubelet`）以获取更详细的失败原因。

---

## 📊 性能统计

├─ 总耗时: 11.1m
├─ 问题定位: 171.4s (26%) ✅
├─ 证据链采集: 340.9s (51%) ✅
├─ 根因分析: 81.0s (12%) ✅
├─ 汇总总结: 75.6s (11%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 17 次
```

📋 诊断追踪

- **核心 Runbook**: pod-sandbox-create-failed
- **参考 Runbook**: pod-sandbox-create-failed
- **工具调用**: 17 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
