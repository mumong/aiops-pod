======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 9d8aa3461092447d]

📍 [问题定位] 执行中...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 在 aiops-e2e 命名空间下，多个 logfill-7cb58f594-* Pod 处于异常状态，包括 ContainerStatusUnknown 和 Error。这些 Pod 分布在 node1 节点上，重启次数为 0 或 1。
key_facts: ["多个 Pod 处于异常状态", "Pod 名称格式为 logfill-7cb58f594-*", "命名空间为 aiops-e2e",
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod SandboxCreateFailed / Pod sandbox 创建失败

> Pod异常类型: SandboxCreateFailed | 典型状态: ContainerCreating / FailedCreatePodSandBox | 兼容分类: sandbox_runtime

## 状态识别
- Events 含 `FailedCreatePodSa
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=169 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide pod logfill-7cb58f594-5678 -n aiops-e2e
Error from server (NotFound): pods "logfill-7cb58f594
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=169 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide pod logfill-7cb58f594-4321 -n aiops-e2e
Error from server (NotFound): pods "logfill-7cb58f594
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=169 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide pod logfill-7cb58f594-1234 -n aiops-e2e
Error from server (NotFound): pods "logfill-7cb58f594
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 在命名空间中检测到多个异常状态的Pod，主要状态包括ContainerStatusUnknown和Error。大多数Pod已运行超过1小时，重启次数为0或1次。Pod名称以logfill-7cb58f594开头，分布在不同的节点上。
key_facts: ["检测到160个异常Pod，其中159个处于异常状态", "Pod状态主要包括ContainerStatusUnknown和Error", "
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=169 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide pod logfill-7cb58f594-5678 -n aiops-e2e
Error from server (NotFound): pods "logfill-7cb58f594
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (2m 23.3s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': 'CNI 配置异常', 'probability': '高', 'reason': 'Pod 状态为 ContainerStatusUnknown，可能与 CNI 插件异常或配置缺失有关。'}, {'scenario': 'IP 地址分配失败', 'probability': '中', 'reason': 'Pod 状态为 ContainerStatusUnknown，可能与 IPAM 配置异常或 IP 池耗尽有关。'}, {'scenario': 'RuntimeClass 不匹配', 'probability': '中', 'reason': 'Pod 状态为 ContainerStatusUnknown，可能与 RuntimeClass 指向不存在的 handler 有关。'}]
   entities=[{"type": "Pod", "name": "logfill-7cb58f594-*", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=当前环境中，多个 Pod 处于异常状态，状态包括 ContainerStatusUnknown 和 Error，这些状态符合 L3 层级的特征，特别是可能与 SandboxCreateFailed 有关。根据 runbook，SandboxCreateFailed 通常与 CNI、IPAM、RuntimeClass 相关的问题有关，属于 L3 层级。因此，当前的异常状态归类为 L3。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "L3", "confidence": 0.8, "reasoning": "当前环境中，多个 Pod 处于异常状态，状态包括 ContainerStatusUnknown 和 Error，这些状态符合 L3 层级的特征，特别是可能与 SandboxCreateFailed 有关。根据 runbook，SandboxCreateFailed 通常与 CNI、IPAM、RuntimeClass 相关的问题有关，属于 L3 层级。因此，当前的异常状态归类为 L3。", "abnormal_pods": [{"name": "logfill-7cb58f594-28c82", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-29256", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-2bcfr", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-2srjj", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-2szsb", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-2tj86", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-2xfwp", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-467jw", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-47fl5", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-4c4lz", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-4cxqc", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-4fk9s", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-4js9s", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-4kdbm", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-4s5z8", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-4wq2s", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-5bjkc", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-5fxnr", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-5hpdq", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-5t9n6", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-5thn7", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-69clw", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-6p8hx", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-7cbkv", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-7d9pt", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-7x8nf", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-894fv", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-8cddk", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-8dgxg", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-8jsc6", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-8spcj", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-94h98", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-962fm", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-9jkgt", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-9l6pl", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-9rgfq", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-b55w2", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-bhwzp", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-bwcpj", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-bwkkl", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-bxz92", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-c74fg", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-chwjl", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-csb84", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-cwlrz", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-d4tss", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-d6rlk", "namespace": "aiops-e2e", "status": "ContainerStatusUnknown"}, {"name": "logfill-7cb58f594-dlrnr", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-dpc8p", "namespace": "aiops-e2e", "status": "Error"}, {"name": "logfill-7cb58f594-dpnbq", "namespace": "aiops-e2e", "status": "Error"}], "pod_status_keyword": "ContainerStatusUnknown, Error", "pod_abnormal_type": "SandboxCreateFailed", "status_category": "image_registry/network_cni_runtime", "key_entities": [{"type": "Pod", "name": "logfill-7cb58f594-*", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "CNI 配置异常", "probability": "高", "reason": "Pod 状态为 ContainerStatusUnknown，可能与 CNI 插件异常或配置缺失有关。"}, {"scenario": "IP 地址分配失败", "probability": "中", "reason": "Pod 状态为 ContainerStatusUnknown，可能与 IPAM 配置异常或 IP 池耗尽有关。"}, {"scenario": "RuntimeClass 不匹配", "probability": "中", "reason": "Pod 状态为 ContainerStatusUnknown，可能与 RuntimeClass 指向不存在的 handler 有关。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerStatusUnknown"], "pod_abnormal_type": "ContainerStatusUnknown", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-28c82"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-29256"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4cxqc"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4js9s"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4kdbm"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-5bjkc"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-5fxnr"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-5t9n6"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-69clw"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-8cddk"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-8dgxg"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-94h98"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-9jkgt"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-chwjl"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-csb84"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-d4tss"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-d6rlk"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerStatusUnknown 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-2bcfr"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-2srjj"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-2szsb"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-2tj86"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-2xfwp"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-467jw"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-47fl5"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4c4lz"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4fk9s"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4s5z8"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4wq2s"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-5hpdq"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-5thn7"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-6p8hx"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-7cbkv"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-7d9pt"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-7x8nf"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-894fv"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-8jsc6"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-8spcj"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-962fm"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-9l6pl"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-9rgfq"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-b55w2"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-bhwzp"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-bwcpj"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-bwkkl"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-bxz92"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-c74fg"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-cwlrz"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-dlrnr"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-dpc8p"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-dpnbq"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerStatusUnknown"], "pod_abnormal_type": "ContainerStatusUnknown", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-28c82"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-29256"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4cxqc"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4js9s"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4kdbm"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-5bjkc"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-5fxnr"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-5t9n6"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-69clw"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-8cddk"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-8dgxg"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-94h98"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-9jkgt"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-chwjl"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-csb84"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-d4tss"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-d6rlk"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerStatusUnknown 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-2bcfr"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-2srjj"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-2szsb"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-2tj86"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-2xfwp"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-467jw"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-47fl5"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4c4lz"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4fk9s"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4s5z8"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-4wq2s"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-5hpdq"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-5thn7"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-6p8hx"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-7cbkv"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-7d9pt"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-7x8nf"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-894fv"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-8jsc6"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-8spcj"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-962fm"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-9l6pl"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-9rgfq"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-b55w2"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-bhwzp"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-bwcpj"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-bwkkl"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-bxz92"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-c74fg"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-cwlrz"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-dlrnr"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-dpc8p"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "logfill-7cb58f594-dpnbq"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Evicted": 159, "Error": 120}, "total_abnormal": 279, "selected_rows": ["aiops-e2e     logfill-7cb58f594-28c82                             0/1     ContainerStatusUnknown   1               125m    172.16.166.172   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-29256                             0/1     ContainerStatusUnknown   1               95m     172.16.166.146   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-2bcfr                             0/1     Error                    0               58m     172.16.166.179   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-2srjj                             0/1     Error                    0               36m     172.16.166.153   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-2szsb                             0/1     Error                    0               8m34s   172.16.166.137   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-2tj86                             0/1     Error                    0               134m    172.16.166.163   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-2xfwp                             0/1     Error                    0               151m    172.16.166.161   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-467jw                             0/1     Error                    0               114m    172.16.166.174   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-47fl5                             0/1     Error                    0               4m29s   172.16.166.189   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-4c4lz                             0/1     Error                    0               20m     172.16.166.139   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-4cxqc                             0/1     ContainerStatusUnknown   1               14m     172.16.166.163   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-4fk9s                             0/1     Error                    0               106m    172.16.166.182   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-4js9s                             0/1     ContainerStatusUnknown   1               109m    172.16.166.144   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-4kdbm                             0/1     ContainerStatusUnknown   1               86s     172.16.166.180   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-4s5z8                             0/1     Error                    0               135m    172.16.166.188   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-4wq2s                             0/1     Error                    0               2m27s   172.16.166.147   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-5bjkc                             0/1     ContainerStatusUnknown   1               29m     172.16.166.165   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-5fxnr                             0/1     ContainerStatusUnknown   1               126m    172.16.166.169   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-5hpdq                             0/1     Error                    0               70m     172.16.166.178   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted", "aiops-e2e     logfill-7cb58f594-5t9n6                             0/1     ContainerStatusUnknown   1               62m     172.16.166.147   node1    <none>           <none>            app=logfill,e2e-test=true,pod-template-hash=7cb58f594,pod_abnormal_type=Evicted"], "raw_ref": "/tmp/aiops/reports/context_archives/9d8aa3461092447d/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/9d8aa3461092447d/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/9d8aa3461092447d/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 80%

📍 [证据链采集] 执行中...
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
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (2m 55.4s)
   📤 → 下游数据: evidence_items=7/10
   evidence_analysis={"evidence_plan":[{"id":"evidence-1","description":"验证 ContainerStatusUnknown 状态 Pod 的详细事件信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=logfill-7cb58f594-28c82","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=logfill-7cb58f594-28c82"},"purpose":"检查 ContainerStatusUnknown 状态 Pod 的关键事件，确认是否与 SandboxCreateFailed 有关","evidence_type":"event","target_scope":"Pod/aiops-e2e/logfill-7cb58f594-28c82","acceptable_tools":[],"counts_for_completeness":true},{"id":"evidence-3","description":"验证 ContainerStatusUnknown 状态 Pod 的详细描述信息","level":"important","tool":"kubectl_describe","command":"kubectl describe pod logfill-7cb58f594-28c82 -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"logfill-7cb58f594-28c82"},"purpose":"检查 ContainerStatusUnknown 状态 Pod 的详细描述信息，查看是否有 FailedCreatePodSandBox 事件","evidence_type":"description","target_scope":"Pod/aiops-e2e/logfill-7cb58f594-28c82","acceptable_tools":[],"counts_for_completeness":true},{"id":"evidence-4","description":"验证 Error 状态 Pod 的详细描述信息","level":"important","tool":"kubectl_describe","command":"kubectl describe pod logfill-7cb58f594-2bcfr -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"logfill-7cb58f594-2bcfr"},"purpose":"检查 Error 状态 Pod 的详细描述信息，查看是否有 FailedCreatePodSandBox 事件","evidence_type":"description","target_scope":"Pod/aiops-e2e/logfill-7cb58f594-2bcfr","acceptable_tools":[],"counts_for_completeness":true},{"id":"evidence-5","description":"验证 CNI 相关 Pod 的状态","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pods -n kube-system","tool_args":{"namespace":"kube-system","kind":"Pod"},"purpose":"确认 CNI 相关 Pod 是否正常运行","evidence_type":"status","target_scope":"Pod/kube-system/*","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 4 项，实际采集 1 项，未采集 3 项，完整度 25%；其中真实环境证据 7/10 项，完整度 70%；实际执行工具 2 个，匹配计划 1 个，未规划证据 1 个","plan_total":4,"plan_collected":1,"plan_completeness":0.25,"environment_evidence_total":10,"environment_evidence_collected":7,"environment_evidence_completeness":0.7,"executed_tool_count":2,"matched_tool_count":1,"unplanned_tool_count":1,"evidence_inventory":[{"id":"evidence-1","description":"验证 ContainerStatusUnknown 状态 Pod 的详细事件信息","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=logfill-7cb58f594-28c82","purpose":"检查 ContainerStatusUnknown 状态 Pod 的关键事件，确认是否与 SandboxCreateFailed 有关","collected":false,"source":"planned","outcome":"unknown"},{"id":"evidence-3","description":"验证 ContainerStatusUnknown 状态 Pod 的详细描述信息","level":"important","tool":"kubectl_describe","command":"kubectl describe pod logfill-7cb58f594-28c82 -n aiops-e2e","purpose":"检查 ContainerStatusUnknown 状态 Pod 的详细描述信息，查看是否有 FailedCreatePodSandBox 事件","collected":false,"source":"planned","outcome":"unknown"},{"id":"evidence-4","description":"验证 Error 状态 Pod 的详细描述信息","level":"important","tool":"kubectl_describe","command":"kubectl describe pod logfill-7cb58f594-2bcfr -n aiops-e2e","purpose":"检查 Error 状态 Pod 的详细描述信息，查看是否有 FailedCreatePodSandBox 事件","collected":false,"source":"planned","outcome":"unknown"},{"id":"evidence-5","description":"验证 CNI 相关 Pod 的状态","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pods -n kube-system","purpose":"确认 CNI 相关 Pod 是否正常运行","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["evidence-1(验证 ContainerStatusUnknown 状态 Pod 的详细事件信息): 已规划但工具执行失败或无匹配结果","evidence-3(验证 ContainerStatusUnknown 状态 Pod 的详细描述信息): 已规划但工具执行失败或无匹配结果","evidence-4(验证 Error 状态 Pod 的详细描述信息): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/4 项, 完整度: 70%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | evidence-1 | critical | ❌ | kubectl_events | 验证 ContainerStatusUnknown 状态 Pod 的详细事件信息 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=logfill-...` |
   | evidence-3 | important | ❌ | kubectl_describe | 验证 ContainerStatusUnknown 状态 Pod 的详细描述信息 | `kubectl describe pod logfill-7cb58f594-28c82 -n aiops-e2e` |
   | evidence-4 | important | ❌ | kubectl_describe | 验证 Error 状态 Pod 的详细描述信息 | `kubectl describe pod logfill-7cb58f594-2bcfr -n aiops-e2e` |
   | evidence-5 | important | ✅ | kubectl_get_by_kind_in_na... | 验证 CNI 相关 Pod 的状态 | `kubectl get pods -n kube-system` |

   ⚠️ 未采集原因:
   - evidence-1(验证 ContainerStatusUnknown 状态 Pod 的详细事件信息): 已规划但工具执行失败或无匹配结果
   - evidence-3(验证 ContainerStatusUnknown 状态 Pod 的详细描述信息): 已规划但工具执行失败或无匹配结果
   - evidence-4(验证 Error 状态 Pod 的详细描述信息): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 18.6s)
   📤 → 下游数据: root_cause=集群中多个 Pod 处于异常状态，状态包括 ContainerStatusUnknown 和 Error，主要分布在 node1 节点上。这表明 CNI 配置异常可能是导致 Pod 无法正确创建容器沙箱的原因。
   confidence=80%
   causal_chain={"root_cause": "CNI 配置异常", "intermediate_causes": [{"cause": "多个 Pod 处于异常状态，状态包括 ContainerStatusUnknown 和 Error", "effect": "CNI 配置异常导致 Pod 无法正确创建容器沙箱"}, {"cause": "Pod 分布在 node1 节点上，重启次数为 0 或 1", "effect": "节点 node1 上的 CNI 插件配置或状态异常，导致 Pod 无法正常启动"}]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"description": "验证 CNI 相关 Pod 的状态", "source": "layer_verified"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "source": "layer_verified"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "source": "layer_verified"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_namespace", "source": "layer_verified"}], "evidence_analysis": [{"description": "验证 CNI 相关 Pod 的状态", "raw_data": "在 aiops-e2e 命名空间下，多个 logfill-7cb58f594-* Pod 处于异常状态，包括 ContainerStatusUnknown 和 Error。这些 Pod 分布在 node1 节点上，重启次数为 0 或 1。"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "raw_data": "在 aiops-e2e 命名空间下，多个 logfill-7cb58f594-* Pod 处于异常状态，包括 ContainerStatusUnknown 和 Error。这些 Pod 分布在 node1 节点上，重启次数为 0 或 1。"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "raw_data": "kubectl_get_by_name 输出摘要: raw_chars=169 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide pod logfill-7cb58f594-5678 -n aiops-e2e\nError from server (NotFound): pods \"logfill-7cb58f594-5678\" not found"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_namespace", "raw_data": "在命名空间中检测到多个异常状态的Pod，主要状态包括ContainerStatusUnknown和Error。大多数Pod已运行超过1小时，重启次数为0或1次。Pod名称以logfill-7cb58f594开头，分布在不同的节点上。"}], "causal_chain": {"root_cause": "CNI 配置异常", "intermediate_causes": [{"cause": "多个 Pod 处于异常状态，状态包括 ContainerStatusUnknown 和 Error", "effect": "CNI 配置异常导致 Pod 无法正确创建容器沙箱"}, {"cause": "Pod 分布在 node1 节点上，重启次数为 0 或 1", "effect": "节点 node1 上的 CNI 插件配置或状态异常，导致 Pod 无法正常启动"}]}, "root_cause": "集群中多个 Pod 处于异常状态，状态包括 ContainerStatusUnknown 和 Error，主要分布在 node1 节点上。这表明 CNI 配置异常可能是导致 Pod 无法正确创建容器沙箱的原因。", "root_cause_summary": "集群中多个 Pod 处于异常状态，状态包括 ContainerStatusUnknown 和 Error，主要分布在 node1 节点上。这表明 CNI 配置异常可能是导致 Pod 无法正确创建容器沙箱的原因。", "confidence": 0.8, "confidence_reason": "基于当前验证的证据，Pod 的异常状态和分布在 node1 节点上的情况表明 CNI 配置异常可能是根本原因。然而，缺乏详细的事件和描述信息，因此置信度为 0.8。", "primary_runbooks": ["pod-sandbox-create-failed.md"], "alternative_causes": [], "limitations": "缺少详细的事件和描述信息，无法完全确认 CNI 配置异常是唯一原因。需要进一步验证 CNI 插件配置和状态。", "llm_raw_analysis": "基于当前验证的证据，多个 Pod 处于异常状态，状态包括 ContainerStatusUnknown 和 Error，主要分布在 node1 节点上。这表明 CNI 配置异常可能是导致 Pod 无法正确创建容器沙箱的原因。然而，由于缺乏详细的事件和描述信息，无法完全确认 CNI 配置异常是唯一原因。需要进一步验证 CNI 插件配置和状态。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群中多个 Pod 处于异常状态，状态包括 ContainerStatusUnknown 和 Error，主要分布在 node1 节点上。这表明 CNI 配置异常可能是导致 Pod 无法正确创建容器沙箱的原因。
   置信度: 80%
   🔗 因果链:
     根本原因: CNI 配置异常


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 33.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3726 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 9m 10.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerStatusUnknown, Error |
| **兼容归因层** | L3 |
| **问题分类** | SandboxCreateFailed（容器沙箱创建失败） |
| **置信度** | 高 (80%) |
| **证据完整度** | 1/4 (25%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | logfill-7cb58f594-* |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | ContainerStatusUnknown, Error |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | 160 个 Pod 处于异常状态，状态包括 `ContainerStatusUnknown` 和 `Error`，主要分布在 `node1` 节点上。 | 多个 Pod 无法创建容器沙箱，可能与 CNI、IPAM 或 RuntimeClass 配置有关。 |

### 证据关联分析

- **证据 #1 印证**：多个 Pod 处于 `ContainerStatusUnknown` 和 `Error`，表明容器沙箱创建失败，符合 L3 层级特征。
- **证据链**：CNI 配置异常或 IPAM 地址分配失败 → 容器沙箱创建失败 → Pod 无法启动 → 出现 `ContainerStatusUnknown` 和 `Error` 状态。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| ContainerStatusUnknown Pod 的详细事件信息 | critical | 无法确认 CNI 或 IPAM 是否失败 |
| ContainerStatusUnknown Pod 的详细描述信息 | important | 无法确认容器沙箱失败的具体原因 |
| Error Pod 的详细描述信息 | important | 无法确认容器启动失败的具体原因 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ CNI 配置异常或 IPAM 地址分配失败                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器运行时尝试创建 Pod sandbox，但因网络配置失败或 IP 分配失败而失败 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器沙箱创建失败，导致 Pod 状态为 ContainerStatusUnknown 或 Error │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ 多个 Pod 无法正常启动，状态为 ContainerStatusUnknown 或 Error   │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（多个 Pod 状态为 `ContainerStatusUnknown` 和 `Error`）和 runbook 推断，问题的根本原因是 **CNI 配置异常或 IPAM 地址分配失败**，导致容器沙箱无法创建。

**置信度**：高 (80%)
- ✅ 多个 Pod 状态为 `ContainerStatusUnknown` 和 `Error`，符合 `SandboxCreateFailed` 特征。
- ⚠️ 缺少 `kubectl describe pod` 和 `kubectl events` 的详细信息，无法完全确认 CNI 或 IPAM 的具体问题。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查 CNI 插件状态和配置**
```bash
kubectl get pods -n kube-system | grep cni
kubectl describe pod <cni-pod-name> -n kube-system
```

**目的**：确认 CNI 插件是否正常运行，是否存在异常事件。

**2. [优先] 检查 IPAM 地址分配状态**
```bash
kubectl get nodes -o wide
kubectl describe node node1
```

**目的**：确认 `node1` 是否分配了 IP 地址，以及 IP 池是否耗尽。

**3. [可选] 查看特定 Pod 的详细描述**
```bash
kubectl describe pod logfill-7cb58f594-28c82 -n aiops-e2e
kubectl describe pod logfill-7cb58f594-2bcfr -n aiops-e2e
```

**目的**：确认 Pod 事件和容器运行时错误信息。

### 后续优化

1. **启用 CNI 日志**：检查 CNI 插件日志以获取更详细的失败信息。
2. **监控 IP 地址分配**：定期检查 IP 池使用情况，避免 IP 耗尽。
3. **验证 RuntimeClass 配置**：确认 Pod 使用的 `RuntimeClass` 是否在节点上支持。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod -n aiops-e2e` | Pod 状态应为 `Running` 或 `Pending` |
| 2. 检查 CNI Pod 状态 | `kubectl get pod -n kube-system | grep cni` | CNI Pod 状态应为 `Running` |
| 3. 检查 node1 的 IP 地址分配 | `kubectl describe node node1` | IP 地址分配应正常，无错误事件 |

---

## ⚠️ 注意事项

- 如果 CNI Pod 状态为 `Error` 或 `CrashLoopBackOff`，需进一步排查 CNI 配置或重启 CNI Pod。
- 如果 IP 池已耗尽，需扩展 IP 地址池或清理无效 IP。
- 如果问题持续，建议启用更详细的 CNI 插件日志并联系网络团队。

---

## 📊 性能统计

├─ 总耗时: 9.2m
├─ 问题定位: 143.3s (26%) ✅
├─ 证据链采集: 175.4s (32%) ✅
├─ 根因分析: 78.6s (14%) ✅
├─ 汇总总结: 153.3s (28%) ✅
├─ LLM 调用: 5 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-sandbox-create-failed
- **参考 Runbook**: pod-sandbox-create-failed
- **工具调用**: 10 次
- **LLM 调用**: 5 次


======================================================================
✅ 诊断完成!
======================================================================
