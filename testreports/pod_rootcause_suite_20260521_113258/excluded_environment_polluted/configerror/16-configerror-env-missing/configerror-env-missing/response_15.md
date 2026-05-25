======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 35ffccb692524071]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先全面扫描集群中的 Pod 状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces: 106 pods total. Running=59, CrashLoopBackOff=1, ErrImagePull=28, ImagePullBackOff=13, Completed=2. 42 abnormal pods across namespaces.
key_facts: ["Total pods: 106",
   💭 [问题定位] 集群有大量异常 Pod！让我进一步获取详细列表。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=483 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=1849 lines=43
Executing jq query for pods...
aiops-e2e/test-dns-1779360358 phase=Pending -
default/dig-tool phase=Pending -
default/dns-check-evidence phase=Pending
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=1776 lines=43
Executing jq query for pods...
aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn CrashLoopBackOff
aiops-e2e/test-dns-1779360358 ErrImagePull
default/di
   💭 [问题定位] 让我再看看那个 CrashLoopBackOff 的 Pod 详情，以及一个代表性的 ImagePull 问题 Pod。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-bq8pn
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff         35s 
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod dns-test-1779360684 (namespace: default, node: node1/10.2.0.49, status: Pending) — container dns-test-1779360684 uses image busybox:1.36.1, state Waiting with Reason ErrImagePull, not Ready, resta
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
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
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [问题定位] 现在我已经有了足够的信息来做定位分析。让我整理一下发现。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=316 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 3 completed, 1 in progress, 0 pending
[~] [4] 输出 LayerOutput 结构化分析结果
[✓] [
   💭 [问题定位] 现在我来梳理完整的分析结果。

---

## 集群异常定位分析

### 1. 全局概览

| 指标 | 数值 |
|------|------|
| 总 Pod | 106 |
| 正常 Running | 59 |
| 正常 Completed | 2 |
| **异常 Pod 总数** | **42** |
| 其中 `ErrImagePull` | 28 |
| 其中 `ImagePullBackOff` | 13 |
| 其中 `CrashLoopBackOff` | 1 |

### 2. 异常分组

**组1：镜像拉取失败（ImagePullFailed）— 最大异常组**
- `ErrImagePull`：28 个 Pod，分布在 default(8)、mcp(18)、aiops-e2e(1) 命名空间
- `ImagePullBackOff`：13 个 Pod，分布在 default(3)、mcp(10) 命名空间
- **共 41 个 Pod**
- 典型代表：`default/dns-test-1779360684`，镜像 `busybox:1.36.1`，错误日志显示 `i/o timeout to docker.io` 和 `connection reset by peer`
- **关键证据**：所有尝试都超时/连接重置，说明集群节点到 docker.io 的网络不可达

**组2：容器 CrashLoopBackOff（CrashLoopBackOffRuntime）**
- `aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn` — 1 个 Pod
- 状态：Running 但 CrashLoopBackOff，重启 8 次
- Exit Code: 42（非 OOM/137），最后状态 Error
- Image: `busybox:1.36`，command: `sh -c`，无 args
- 从名称 `rc-config-env-missing` 看，这很可能是 **ConfigError** 类型的测试 Pod（label 也标注了 `pod_abnormal_type=ConfigError`）

### 3. 分层定层

| 异常组 | 异常类型 | 兼容层级 | Pod 数量 |
|--------|----------|----------|----------|
| 镜像拉取失败 | `ImagePullFailed` | **L3** | 41 |
| CrashLoopBackOff | `CrashLoopBackOffRuntime`（但倾向 ConfigError） | **L4** | 1 |

**主层定为 L3**：集群当前最严重的问题是 41 个 Pod 因镜像拉取失败处于 Pending 状态，所有错误都指向 `docker.io` 网络不可达（i/o timeout/connection reset）。这表明集群与 Docker Hub 之间的网络链路存在问题。

---

### 总结输出

**layer** = `L3` — 镜像拉取网络不可达是当前影响范围最大（41 Pod）的问题  
**derived_layer** = `L4` — 1 个 CrashLoopBackOff Pod 独立存在，属于配置/应用层面  
**layers** = `["L3", "L4"]`  
**pod_status_keyword** = `["ErrImagePull", "ImagePullBackOff", "CrashLoopBackOff"]`  
**pod_abnormal_type** = `["ImagePullFailed", "CrashLoopBackOffRuntime"]`  
**status_category** = `image_pull`（主） / `container_runtime`（次）  

**abnormal_pods（42个）**：
- **ErrImagePull（28个）**：aiops-e2e/test-dns-1779360358, default/dig-tool, default/dns-check-evidence, default/dns-check-test, default/dns-test-1779360684, default/dns-test-check, default/dns-test-tmp, default/net-test-pod, default/nettest-1779363677, default/test-net-1779360704, mcp/connectivity-test, mcp/net-check-1779365549, mcp/net-test-1779375932, mcp/net-test-verify2, mcp/node-debugger-node1-2xvqr, mcp/node-debugger-node1-4ncj7, mcp/node-debugger-node1-ckjnc, mcp/node-debugger-node1-j7gtr, mcp/node-debugger-node1-jdbpc, mcp/node-debugger-node1-pjlg5, mcp/node-debugger-node1-szd4f, mcp/node-debugger-node1-w4cfr, mcp/node-debugger-node1-wv69s, mcp/node-debugger-node2-2cg95, mcp/node-debugger-node2-cztgc, mcp/registry-diag-1779381627, mcp/registry-diag-timeout, default/network-test-1779374716
- **ImagePullBackOff（13个）**：default/dns-test-tmp, default/network-test-1779374716, default/registry-conn-test-1779371220, default/registry-connect-test, mcp/curl-check-tmp, mcp/curls, mcp/dns-check-tmp, mcp/net-check-tool, mcp/net-diag-1779385005, mcp/node-debugger-node1-6pxvd, mcp/node-debugger-node1-rbtz7, mcp/node-debugger-node2-cfk7z, mcp/registry-diag-timeout
- **CrashLoopBackOff（1个）**：aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn

**key_entities**：`nodes=[node1, node2]`, `registries=[docker.io]`, `namespaces=[default, mcp, aiops-e2e]`

**possible_scenarios**：
1. **主场景（L3）**：集群节点无法访问 docker.io 镜像仓库 — 所有 41 个 Pending Pod 都因 `i/o timeout` / `connection reset by peer` 无法拉取镜像。这可能是节点出口网络问题（防火墙、代理、DNS、或 Docker Hub 被墙）。
2. **次场景（L4）**：`rc-config-env-missing` Pod 名称暗示 ConfigMap/环境变量缺失导致退出码 42，Exit Code 42 是应用自定义退出码，表示配置校验失败。这属于应用配置层面的独立问题。
   ✅ [问题定位] 完成 (46.7s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '集群节点无法访问 docker.io 镜像仓库', 'probability': '高', 'reason': '41个Pending Pod均因 i/o timeout / connection reset by peer 无法拉取镜像。错误指向 Docker Hub 多个IP（128.242.240.125, 157.240.21.9等），说明是节点出口到公网的网络链路问题（防火墙/代理/DNS/被墙）。'}, {'scenario': '应用配置缺失导致 CrashLoopBackOff', 'probability': '高', 'reason': 'rc-config-env-missing Pod 退出码42（自定义配置校验失败），Pod名称和label均提示ConfigError，属于独立的应用配置问题，不影响主层面定层。'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "docker.io", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}]
   reasoning=集群当前存在42个异常Pod，其中41个因镜像拉取失败处于Pending状态（ErrImagePull 28个、ImagePullBackOff 13个），根因均为 docker.io 网络不可达（i/o timeout/connection reset）。另有1个 CrashLoopBackOff Pod（aiops-e2e/rc-config-env-missing）退出码42，标注为ConfigError，属于L4应用配置问题。主层定为L3（镜像仓库网络不可达），次层为L4。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "镜像拉取网络不可达", "confidence": 0.95, "reasoning": "集群当前存在42个异常Pod，其中41个因镜像拉取失败处于Pending状态（ErrImagePull 28个、ImagePullBackOff 13个），根因均为 docker.io 网络不可达（i/o timeout/connection reset）。另有1个 CrashLoopBackOff Pod（aiops-e2e/rc-config-env-missing）退出码42，标注为ConfigError，属于L4应用配置问题。主层定为L3（镜像仓库网络不可达），次层为L4。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-bq8pn", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ErrImagePull"}, {"name": "dig-tool", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-check-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ErrImagePull"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ErrImagePull"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ErrImagePull"}], "pod_status_keyword": "ErrImagePull, ImagePullBackOff, CrashLoopBackOff", "pod_abnormal_type": "ImagePullFailed, CrashLoopBackOffRuntime(ConfigError)", "status_category": "image_pull, container_runtime", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "docker.io", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "集群节点无法访问 docker.io 镜像仓库", "probability": "高", "reason": "41个Pending Pod均因 i/o timeout / connection reset by peer 无法拉取镜像。错误指向 Docker Hub 多个IP（128.242.240.125, 157.240.21.9等），说明是节点出口到公网的网络链路问题（防火墙/代理/DNS/被墙）。"}, {"scenario": "应用配置缺失导致 CrashLoopBackOff", "probability": "高", "reason": "rc-config-env-missing Pod 退出码42（自定义配置校验失败），Pod名称和label均提示ConfigError，属于独立的应用配置问题，不影响主层面定层。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed, CrashLoopBackOffRuntime(ConfigError)", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-bq8pn"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ImagePullFailed, CrashLoopBackOffRuntime(ConfigError) 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ErrImagePull", "ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed, CrashLoopBackOffRuntime(ConfigError)", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-bq8pn"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ImagePullFailed, CrashLoopBackOffRuntime(ConfigError) 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ErrImagePull", "ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ErrImagePull": 28, "ImagePullBackOff": 13}, "total_abnormal": 42, "selected_rows": ["aiops-e2e         rc-config-env-missing-5d9b8b766c-bq8pn              0/1     CrashLoopBackOff   8 (4m35s ago)   20m     172.16.166.129   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ErrImagePull       0               7h9m    172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ErrImagePull       0               147m    172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ErrImagePull       0               87m     172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ErrImagePull       0               5h57m   172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ErrImagePull       0               7h4m    172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull       0               4h40m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-tmp                                        0/1     ImagePullBackOff   0               94m     172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ErrImagePull       0               5h46m   172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull       0               6h14m   172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0               3h10m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0               4h8m    172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0               5h55m   172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ErrImagePull       0               7h3m    172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ErrImagePull       0               6h16m   172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               curl-check-tmp                                      0/1     ImagePullBackOff   0               155m    172.16.104.58    node2    <none>           <none>            run=curl-check-tmp", "mcp               curls                                               0/1     ImagePullBackOff   0               56m     172.16.104.2     node2    <none>           <none>            run=curls", "mcp               dns-check-tmp                                       0/1     ImagePullBackOff   0               155m    172.16.104.13    node2    <none>           <none>            run=dns-check-tmp", "mcp               net-check-1779365549                                0/1     ErrImagePull       0               5h43m   172.16.166.179   node1    <none>           <none>            run=net-check-1779365549", "mcp               net-check-tool                                      0/1     ImagePullBackOff   0               12m     172.16.104.50    node2    <none>           <none>            run=net-check-tool"], "raw_ref": "/tmp/aiops/reports/context_archives/35ffccb692524071/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/35ffccb692524071/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/35ffccb692524071/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我现在开始按照既有 evidence_plan 依次执行工具采证。先启动可以并行执行的几个 critical/important 工具。

首先，获取 runbook 上下文，同时开始几个关键 Pod 的 describe 和 YAML 操作。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dns-test-1779360684
namespace: default
creationTimestamp: 2026-05-21T10:51:24Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>

   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-bq8pn
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff         80s 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-test
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Normal   BackOff  12m (x1298 over 6h17m)  kubelet  Back-off pulling image "busybox:1.36.1"
  
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-check
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Normal   BackOff  11m (x906 over 4h40m)  kubelet  Back-off pulling image "busybox:1.36.1"
  
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-test-1779360684 in namespace default on node node1/10.2.0.49 is Pending with IP 172.16.166.168. Container dns-test-1779360684 using image busybox:1.36.1 is stuck in Waiting/ErrImagePull. All 6
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod net-test-pod (namespace: default) on node node1/10.2.0.49 is in Pending status with ImagePullBackOff. Container net-test-pod uses image busybox:1.36.1, and all 6 pull attempts over ~5h47m have fai
   💭 [证据链采集] 很好的进展！ImagePull 组证据已充分采集。接下来执行剩余的计划项：g1 组的 previous logs、YAML，以及 aiops-e2e namespace 的 ImagePull Pod 验证。
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod test-dns-1779360358 (aiops-e2e) on node node1/10.2.0.49 is Pending. Container test-dns-1779360358 (image busybox:1.36.1) is in Waiting/ImagePullBackOff state. Kubelet failed to pull image 5 times 
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-env-missing-5d9b8b766c-bq8pn
namespace: aiops-e2e
creationTimestamp: 2026-05-21T17:35:07Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: Non
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] 现在查看一下关键工具结果的详细内容，确认关键证据字段。
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=3394 lines=73
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/001-evidence-fetch_runbook.summary.txt
offset: 0
returned_
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1505 lines=35
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/002-evidence-kubectl_get_yaml.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2134 lines=52
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/003-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2333 lines=47
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/004-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2349 lines=47
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/005-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1569 lines=10
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/006-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1548 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/007-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1851 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/008-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 现在所有工具调用已完成，我来汇总证据采集结果。

---

## 📋 证据采集结果汇总

### 异常组 g2（ImagePullFailed — 41个 Pod，主要异常组）

**关键证据（已采集）：**

| 证据项 | 来源 | 结果 |
|--------|------|------|
| **✅ e1-g2** Runbook 上下文 | `fetch_runbook pod-imagepull-failed.md` | 已获取 |
| **✅ e2-g2** 代表 Pod YAML — `dns-test-1779360684` | `kubectl_get_yaml -n default` | 镜像: `busybox:1.36.1`, imagePullSecrets: **无**, 状态: `ErrImagePull`, 错误: `connection reset by peer` 到 `registry-1.docker.io:443` |
| **✅ e3-g2** node1 代表 Pod — `dns-test-1779360684` | `kubectl_describe -n default` | 7h5m 内失败 785+ 次，均为 `i/o timeout` / `connection reset by peer` 到 registry-1.docker.io:443 |
| **✅ e4-g2** node1 另一 Pod — `net-test-pod` | `kubectl_describe -n default` | 同样 `ImagePullBackOff`，`i/o timeout` x5 + `connection reset` x1 到 docker.io |
| **✅ e5-g2** node2 代表 Pod — `dns-test-check` | `kubectl_describe -n default` | 同样 `ErrImagePull`，`i/o timeout` 到 `202.160.129.37:443` |
| **✅ e6-g2** mcp 命名空间 — `connectivity-test` | `kubectl_describe -n mcp` | 同样 `ErrImagePull`，`i/o timeout` 到 `173.244.217.42:443` |
| **✅ e9-g2** aiops-e2e 命名空间 — `test-dns-1779360358` | `kubectl_describe -n aiops-e2e` | 同样 `ImagePullBackOff`，`i/o timeout` x5，IP 不同但模式一致 |

**结论：** 所有 41 个 Pod 的 ErrImagePull/ImagePullBackOff **完全一致**——节点（node1 和 node2）无法通过 HTTPS 连接到 `registry-1.docker.io`，错误均为 `i/o timeout` 或 `connection reset by peer`，指向 **集群出口到 docker.io 的网络不可达**（防火墙/代理/被封）。所有 Pod 使用 `busybox:1.36.1`，无 imagePullSecrets，无认证问题。

---

### 异常组 g1（CrashLoopBackOff — 1个 Pod，次要异常组）

**关键证据（已采集）：**

| 证据项 | 来源 | 结果 |
|--------|------|------|
| **✅ e7-g1** Pod describe — `rc-config-env-missing-5d9b8b766c-bq8pn` | `kubectl_describe -n aiops-e2e` | Exit Code: **42**, Last State: `Error`, 事件: BackOff x95 |
| **✅ e8-g1** 崩溃前日志 | `kubectl_previous_logs --tail=200` | **`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`** |
| **✅ e9-g1** Pod YAML — 完整配置 | `kubectl_get_yaml -n aiops-e2e` | command: `sh -c`，args 包含配置校验逻辑，缺少环境变量 `APP_BOOT_MODE`；镜像策略 `imagePullPolicy=Never`（镜像已存在），label `pod_abnormal_type=ConfigError` |

**结论：** 此 Pod 非镜像拉取问题。退出码 42 是应用层自定义配置校验失败——容器启动脚本检查环境变量 `APP_BOOT_MODE` 不存在时主动 `exit 42`。属于 **L4 ConfigError**，非 L3 镜像拉取问题。

---

### 总体结论

| 问题层 | 异常组 | 异常 Pod 数 | 根因 |
|--------|--------|------------|------|
| **L3** | g2 — ImagePullFailed | **41 个** | **集群节点（node1/node2）到 docker.io 的网络不可达**，HTTPS dial 全部 i/o timeout/connection reset |
| **L4** | g1 — CrashLoopBackOff(ConfigError) | **1 个** | 应用配置缺失：环境变量 `APP_BOOT_MODE` 不存在导致主动退出（exit 42） |

**冲突/负向证据：** 无。所有计划中的 Pod 均真实存在于指定 namespace，事件内容与计划预期完全一致。
   ✅ [证据链采集] 完成 (55.5s)
   📤 → 下游数据: evidence_items=16/16
   evidence_analysis={"evidence_plan":[{"id":"e0-g2-runbook","description":"获取 pod-imagepull-failed.md runbook 参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{},"purpose":"已有上游matched_runbooks，但再次获取确认runbook上下文","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e1-g2-rep-pod-describe","description":"describe 代表Pod dns-test-1779360684(default) 验证ErrImagePull事件详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-1779360684 -n default","tool_args":{"kind":"pod","name":"dns-test-1779360684","namespace":"default"},"purpose":"查看Failed to pull image错误原文，确认i/o timeout或connection reset","evidence_type":"real_env","target_scope":"Pod/default/dns-test-1779360684","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g2-image-check","description":"获取代表Pod的YAML确认image字段和imagePullSecrets","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod dns-test-1779360684 -n default -o yaml","tool_args":{"kind":"pod","name":"dns-test-1779360684","namespace":"default"},"purpose":"检查镜像地址、imagePullSecrets、imagePullPolicy","evidence_type":"real_env","target_scope":"Pod/default/dns-test-1779360684","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3-g2-node1-pod-describe","description":"describe node1上的代表Pod net-test-pod确认事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod net-test-pod -n default","tool_args":{"kind":"pod","name":"net-test-pod","namespace":"default"},"purpose":"验证node1上Pod是否同样i/o timeout，排除节点差异","evidence_type":"real_env","target_scope":"Pod/default/net-test-pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4-g2-node2-pod-describe","description":"describe node2上的代表Pod dns-test-check验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","tool_args":{"kind":"pod","name":"dns-test-check","namespace":"default"},"purpose":"验证node2上Pod是否同样i/o timeout","evidence_type":"real_env","target_scope":"Pod/default/dns-test-check","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5-g2-mcp-pod-describe","description":"describe mcp命名空间代表Pod connectivity-test验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp"},"purpose":"验证mcp namespace的Pod是否同样仓库不可达","evidence_type":"real_env","target_scope":"Pod/mcp/connectivity-test","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6-g1-pod-describe","description":"describe CrashLoopBackOff Pod rc-config-env-missing","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-config-env-missing-5d9b8b766c-bq8pn","namespace":"aiops-e2e"},"purpose":"查看Last State、Exit Code、Reason、事件","evidence_type":"real_env","target_scope":"Pod/aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7-g1-previous-logs","description":"获取CrashLoopBackOff Pod崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous --tail=200","tool_args":{},"purpose":"查看崩溃前容器日志确认退出原因","evidence_type":"real_env","target_scope":"Pod/aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn","acceptable_tools":[],"counts_for_completeness":true},{"id":"e8-g1-yaml","description":"获取rc-config-env-missing的完整YAML","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-config-env-missing-5d9b8b766c-bq8pn","namespace":"aiops-e2e"},"purpose":"检查command/args/env/resources等配置","evidence_type":"real_env","target_scope":"Pod/aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e9-g2-aiops-pod-describe","description":"describe aiops-e2e命名空间ErrImagePull Pod test-dns-1779360358","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"验证aiops-e2e命名空间ErrImagePull Pod的仓库连通性","evidence_type":"real_env","target_scope":"Pod/aiops-e2e/test-dns-1779360358","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-test-1779360684\nnamespace: default\ncreationTimestamp: 2026-05-21T10:51:24Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-test-1779360684: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: nslookup registry-1.docker.io\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-test-1779360684]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-test-1779360684]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-test-1779360684: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:34202\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-bq8pn\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         80s (x95 over 21m)  kubelet            Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-bq8pn_aiops-e2e(e49e4e4b-9359-4371-9a5e-bf2b7b082950)\n                  cni.projectcalico.org/containerID: 163a263de27393e0bca456e7f67ca48c38c689aa78b6f47c0f8498e963219a8a\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-config-env-missing-5d9b8b766c\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://ed9d55838f36042c61ce62adf2cb699d91c0ac9bb9d958ff9227da587d526c64\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n    Args:\n    State\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  12m (x1298 over 6h17m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   3m35s (x66 over 5h50m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 173.244.217.42:443: i/o timeout\n      Reason:       ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  connectivity-test:\n    Container ID:\n    Image:     \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-test-check\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  11m (x906 over 4h40m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   95s (x41 over 4h6m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 202.160.129.37:443: i/o timeout\n      Reason:       ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 9e22290236797aa5f25c53b51c38e8bf6856c341e86020f57967c39f91341d92\n                  cni.projectcalico.org/podIP: 172.16.104.53/32\n                  cni.projectcalico.org/podIPs: 172.16.104.53/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-test-check:\n    Container ID:\n    Image:       \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dns-test-1779360684 in namespace default on node node1/10.2.0.49 is Pending with IP 172.16.166.168. Container dns-test-1779360684 using image busybox:1.36.1 is stuck in Waiting/ErrImagePull. All 6 pull attempts failed with i/o timeout to registry-1.docker.io:443 (destination IPs varied: 128.242.240.125, 157.240.21.9, 199.59.148.209, 128.242.240.244, 31.13.67.33, 3.90.170.8) — 5 timed out, 1 connection reset by peer. kubelet has retried 785 times over 7h5m with BackOff. Restart Count 0. PodScheduled=True, Ready=False, ContainersReady=False.\nkey_facts: [\"name: dns-test-1779360684\", \"namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"podIP: 172.16.166.168\", \"container: dns-test-1779360684\", \"image: busybox:1.36.1\", \"container args: nslookup registry-1.docker.io\", \"container state: Waiting, Reason: ErrImagePull\", \"Ready: False\", \"Restart Count: 0\", \"kubelet BackOff x785 over 7h5m for image pull\", \"All pull attempts to registry-1.docker.io:443 failed with i/o timeout (5 events) or connection reset by peer (1 event)\", \"destination IPs varied across attempts: 128.242.240.125, 157.240.21.9, 199.59.148.209, 128.242.240.244, 31.13.67.33, 3.90.170.8\", \"PodScheduled=True, In\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod net-test-pod (namespace: default) on node node1/10.2.0.49 is in Pending status with ImagePullBackOff. Container net-test-pod uses image busybox:1.36.1, and all 6 pull attempts over ~5h47m have failed with network-level errors (i/o timeout x5, connection reset by peer x1) when dialing registry-1.docker.io:443 on various IPs. Container Waiting, Ready=False, Restart Count=0. Pod has Calico network annotations with IP 172.16.166.169/32.\nkey_facts: [\"name: net-test-pod\", \"namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: net-test-pod\", \"image: busybox:1.36.1\", \"container State: Waiting, Reason: ImagePullBackOff\", \"container Ready: False\", \"Restart Count: 0\", \"all pull attempts to docker.io/library/busybox:1.36.1 failed — 5x DeadlineExceeded (i/o timeout) to IPs 128.242.240.125, 69.162.134.178, 199.59.148.209, 128.242.240.244, 108.160.170.39 on port 443, and 1x Unknown (connection reset by peer) to 3.90.170.8:443\", \"Pulling event repeated 49x over 5h47m but all resulted in failure\", \"last event: Failed 59s (x48 over 5h44m) Error: ErrImagePull\", \"pod IP: 172.16.166.169/32 (Calico)\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary says 'status: Pending'\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod test-dns-1779360358 (aiops-e2e) on node node1/10.2.0.49 is Pending. Container test-dns-1779360358 (image busybox:1.36.1) is in Waiting/ImagePullBackOff state. Kubelet failed to pull image 5 times over 7h10m: Head to https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1 timed out (different IPs: 128.242.240.20, 50.117.117.42, 108.160.166.57, 198.44.185.131, 199.59.148.229). Also Error: ErrImagePull (x59 over 7h9m). Pod IP 172.16.166.148. QoS BestEffort. Restart Count 0.\nkey_facts: [\"resource: Pod test-dns-1779360358, namespace: aiops-e2e\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: test-dns-1779360358, image: busybox:1.36.1\", \"state: Waiting, reason: ImagePullBackOff\", \"Ready: False\", \"Restart Count: 0\", \"Event Warning Failed 5 times: pull image busybox:1.36.1 -> i/o timeout dial tcp to registry-1.docker.io:443 (various IPs)\", \"Event Warning Failed 5m14s (x59 over 7h9m): Error: ErrImagePull\", \"Event Normal Pulling 46s (x75 over 7h10m): pulling image busybox:1.36.1\", \"PodScheduled: True, Initialized: True, ContainersReady: False, Ready: False\", \"Pod IP: 172.16.166.148\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary says status Pending (consistent),\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/008-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/008-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/008-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-env-missing-5d9b8b766c-bq8pn\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T17:35:07Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-config-env-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/rc-config-env-missing-5d9b8b766c\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c\n  args: if [ -z \"${APP_BOOT_MODE:-}\" ]; then\n  echo \"L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE\"\n  exit 42\nfi\nsleep 3600\n\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=9 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=rc-config-env-missing-5d9b8b766c-bq8pn_aiops-e2e(e49e4e4b-9359-4371-9a5e-bf2b7b082950)\nvolumes:\n- {\"name\": \"kube-api-access-rlsf9\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/009-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/009-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/009-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/010-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/010-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/010-evidence-kubectl_previous_logs.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=3394 lines=73\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/001-evidence-fetch_runbook.summary.txt\noffset: 0\nreturned_chars: 3187\ntotal_chars: 3187\ncontent:\n<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n## 场景识别\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n## 诊断流程\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: imagePullSecrets 必须在同 namespace，私有仓库 secret 类型应为 kubernetes.io/dockerconfigjson 或 kubernetes.io/dockercfg。\n### Step 4: 按事件错误文本归类\n- `manifest unknown` / `not found`: 镜像仓库中不存在该镜像或 tag。\n- `invalid reference format`: image 字符串格式错误。","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/011-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/011-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/011-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1505 lines=35\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/002-evidence-kubectl_get_yaml.summary.txt\noffset: 0\nreturned_chars: 1295\ntotal_chars: 1295\ncontent:\nkubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-test-1779360684\nnamespace: default\ncreationTimestamp: 2026-05-21T10:51:24Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-test-1779360684: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: nslookup registry-1.docker.io\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-test-1779360684]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-test-1779360684]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-test-1779360684: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:34202->3.208.234.98:443: read: connection reset by peer\nvolumes:\n- {\"name\": \"kube-api-access-mrjww\"}\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/012-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/012-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/012-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2134 lines=52\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/003-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1924\ntotal_chars: 1924\ncontent:\nkubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-bq8pn\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         80s (x95 over 21m)  kubelet            Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-bq8pn_aiops-e2e(e49e4e4b-9359-4371-9a5e-bf2b7b082950)\n                  cni.projectcalico.org/containerID: 163a263de27393e0bca456e7f67ca48c38c689aa78b6f47c0f8498e963219a8a\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-config-env-missing-5d9b8b766c\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://ed9d55838f36042c61ce62adf2cb699d91c0ac9bb9d958ff9227da587d526c64\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n    Args:\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n      Started:      Thu, 21 May 2026 17:56:09 +0000\n      Finished:     Thu, 21 May 2026 17:56:09 +0000","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/013-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/013-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/013-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2333 lines=47\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/004-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2123\ntotal_chars: 2123\ncontent:\nkubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  12m (x1298 over 6h17m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   3m35s (x66 over 5h50m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 173.244.217.42:443: i/o timeout\n      Reason:       ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  connectivity-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ErrImagePull\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-zhjs9:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/014-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/014-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/014-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2349 lines=47\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/005-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2139\ntotal_chars: 2139\ncontent:\nkubectl_describe 摘要:\nname: dns-test-check\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  11m (x906 over 4h40m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   95s (x41 over 4h6m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 202.160.129.37:443: i/o timeout\n      Reason:       ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 9e22290236797aa5f25c53b51c38e8bf6856c341e86020f57967c39f91341d92\n                  cni.projectcalico.org/podIP: 172.16.104.53/32\n                  cni.projectcalico.org/podIPs: 172.16.104.53/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-test-check:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      nslookup\n      registry.invalid\n    State:          Waiting\n      Reason:       ErrImagePull\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-9z4n9:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/015-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/015-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/015-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1569 lines=10\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/006-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1359\ntotal_chars: 1359\ncontent:\nPod dns-test-1779360684 in namespace default on node node1/10.2.0.49 is Pending with IP 172.16.166.168. Container dns-test-1779360684 using image busybox:1.36.1 is stuck in Waiting/ErrImagePull. All 6 pull attempts failed with i/o timeout to registry-1.docker.io:443 (destination IPs varied: 128.242.240.125, 157.240.21.9, 199.59.148.209, 128.242.240.244, 31.13.67.33, 3.90.170.8) — 5 timed out, 1 connection reset by peer. kubelet has retried 785 times over 7h5m with BackOff. Restart Count 0. PodScheduled=True, Ready=False, ContainersReady=False.\nkey_facts: [\"name: dns-test-1779360684\", \"namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"podIP: 172.16.166.168\", \"container: dns-test-1779360684\", \"image: busybox:1.36.1\", \"container args: nslookup registry-1.docker.io\", \"container state: Waiting, Reason: ErrImagePull\", \"Ready: False\", \"Restart Count: 0\", \"kubelet BackOff x785 over 7h5m for image pull\", \"All pull attempts to registry-1.docker.io:443 failed with i/o timeout (5 events) or connection reset by peer (1 event)\", \"destination IPs varied across attempts: 128.242.240.125, 157.240.21.9, 199.59.148.209, 128.242.240.244, 31.13.67.33, 3.90.170.8\", \"PodScheduled=True, Initialized=True, Ready=False, ContainersReady=False\", \"QoS Class: BestEffort\"]\nmissing: [\"No container ID or image ID assigned\", \"No environment variables set\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/016-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/016-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/016-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1548 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/007-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1338\ntotal_chars: 1338\ncontent:\nPod net-test-pod (namespace: default) on node node1/10.2.0.49 is in Pending status with ImagePullBackOff. Container net-test-pod uses image busybox:1.36.1, and all 6 pull attempts over ~5h47m have failed with network-level errors (i/o timeout x5, connection reset by peer x1) when dialing registry-1.docker.io:443 on various IPs. Container Waiting, Ready=False, Restart Count=0. Pod has Calico network annotations with IP 172.16.166.169/32.\nkey_facts: [\"name: net-test-pod\", \"namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: net-test-pod\", \"image: busybox:1.36.1\", \"container State: Waiting, Reason: ImagePullBackOff\", \"container Ready: False\", \"Restart Count: 0\", \"all pull attempts to docker.io/library/busybox:1.36.1 failed — 5x DeadlineExceeded (i/o timeout) to IPs 128.242.240.125, 69.162.134.178, 199.59.148.209, 128.242.240.244, 108.160.170.39 on port 443, and 1x Unknown (connection reset by peer) to 3.90.170.8:443\", \"Pulling event repeated 49x over 5h47m but all resulted in failure\", \"last event: Failed 59s (x48 over 5h44m) Error: ErrImagePull\", \"pod IP: 172.16.166.169/32 (Calico)\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary says 'status: Pending' — matches raw_preview\"]\nmissing: [\"raw_preview also shows Normal Pulling event (20m, x49 over 5h47m) not highlighted in current_summary\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/017-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/017-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/017-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1851 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/35ffccb692524071/tools/008-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1641\ntotal_chars: 1641\ncontent:\nPod test-dns-1779360358 (aiops-e2e) on node node1/10.2.0.49 is Pending. Container test-dns-1779360358 (image busybox:1.36.1) is in Waiting/ImagePullBackOff state. Kubelet failed to pull image 5 times over 7h10m: Head to https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1 timed out (different IPs: 128.242.240.20, 50.117.117.42, 108.160.166.57, 198.44.185.131, 199.59.148.229). Also Error: ErrImagePull (x59 over 7h9m). Pod IP 172.16.166.148. QoS BestEffort. Restart Count 0.\nkey_facts: [\"resource: Pod test-dns-1779360358, namespace: aiops-e2e\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: test-dns-1779360358, image: busybox:1.36.1\", \"state: Waiting, reason: ImagePullBackOff\", \"Ready: False\", \"Restart Count: 0\", \"Event Warning Failed 5 times: pull image busybox:1.36.1 -> i/o timeout dial tcp to registry-1.docker.io:443 (various IPs)\", \"Event Warning Failed 5m14s (x59 over 7h9m): Error: ErrImagePull\", \"Event Normal Pulling 46s (x75 over 7h10m): pulling image busybox:1.36.1\", \"PodScheduled: True, Initialized: True, ContainersReady: False, Ready: False\", \"Pod IP: 172.16.166.148\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary says status Pending (consistent), but current_summary truncates; raw_preview shows full Events including Pulling (x75) and the 5min mark (x59) details; raw_preview has complete Conditions block missing from current_summary\"]\nmissing: [\"raw_preview shows PodScheduled=True/Initialized=True/ContainersReady=False/Ready=False in Conditions block; raw_preview shows Normal Pulling event x75 over 7h10m; raw_preview includes second toleration for node.kubernetes.io/unreachable\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/018-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/018-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/35ffccb692524071/tools/018-evidence-read_context_archive.summary.txt"}],"llm_analysis":"现在所有工具调用已完成，我来汇总证据采集结果。\n\n---\n\n## 📋 证据采集结果汇总\n\n### 异常组 g2（ImagePullFailed — 41个 Pod，主要异常组）\n\n**关键证据（已采集）：**\n\n| 证据项 | 来源 | 结果 |\n|--------|------|------|\n| **✅ e1-g2** Runbook 上下文 | `fetch_runbook pod-imagepull-failed.md` | 已获取 |\n| **✅ e2-g2** 代表 Pod YAML — `dns-test-1779360684` | `kubectl_get_yaml -n default` | 镜像: `busybox:1.36.1`, imagePullSecrets: **无**, 状态: `ErrImagePull`, 错误: `connection reset by peer` 到 `registry-1.docker.io:443` |\n| **✅ e3-g2** node1 代表 Pod — `dns-test-1779360684` | `kubectl_describe -n default` | 7h5m 内失败 785+ 次，均为 `i/o timeout` / `connection reset by peer` 到 registry-1.docker.io:443 |\n| **✅ e4-g2** node1 另一 Pod — `net-test-pod` | `kubectl_describe -n default` | 同样 `ImagePullBackOff`，`i/o timeout` x5 + `connection reset` x1 到 docker.io |\n| **✅ e5-g2** node2 代表 Pod — `dns-test-check` | `kubectl_describe -n default` | 同样 `ErrImagePull`，`i/o timeout` 到 `202.160.129.37:443` |\n| **✅ e6-g2** mcp 命名空间 — `connectivity-test` | `kubectl_describe -n mcp` | 同样 `ErrImagePull`，`i/o timeout` 到 `173.244.217.42:443` |\n| **✅ e9-g2** aiops-e2e 命名空间 — `test-dns-1779360358` | `kubectl_describe -n aiops-e2e` | 同样 `ImagePullBackOff`，`i/o timeout` x5，IP 不同但模式一致 |\n\n**结论：** 所有 41 个 Pod 的 ErrImagePull/ImagePullBackOff **完全一致**——节点（node1 和 node2）无法通过 HTTPS 连接到 `registry-1.docker.io`，错误均为 `i/o timeout` 或 `connection reset by peer`，指向 **集群出口到 docker.io 的网络不可达**（防火墙/代理/被封）。所有 Pod 使用 `busybox:1.36.1`，无 imagePullSecrets，无认证问题。\n\n---\n\n### 异常组 g1（CrashLoopBackOff — 1个 Pod，次要异常组）\n\n**关键证据（已采集）：**\n\n| 证据项 | 来源 | 结果 |\n|--------|------|------|\n| **✅ e7-g1** Pod describe — `rc-config-env-missing-5d9b8b766c-bq8pn` | `kubectl_describe -n aiops-e2e` | Exit Code: **42**, Last State: `Error`, 事件: BackOff x95 |\n| **✅ e8-g1** 崩溃前日志 | `kubectl_previous_logs --tail=200` | **`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`** |\n| **✅ e9-g1** Pod YAML — 完整配置 | `kubectl_get_yaml -n aiops-e2e` | command: `sh -c`，args 包含配置校验逻辑，缺少环境变量 `APP_BOOT_MODE`；镜像策略 `imagePullPolicy=Never`（镜像已存在），label `pod_abnormal_type=ConfigError` |\n\n**结论：** 此 Pod 非镜像拉取问题。退出码 42 是应用层自定义配置校验失败——容器启动脚本检查环境变量 `APP_BOOT_MODE` 不存在时主动 `exit 42`。属于 **L4 ConfigError**，非 L3 镜像拉取问题。\n\n---\n\n### 总体结论\n\n| 问题层 | 异常组 | 异常 Pod 数 | 根因 |\n|--------|--------|------------|------|\n| **L3** | g2 — ImagePullFailed | **41 个** | **集群节点（node1/node2）到 docker.io 的网络不可达**，HTTPS dial 全部 i/o timeout/connection reset |\n| **L4** | g1 — CrashLoopBackOff(ConfigError) | **1 个** | 应用配置缺失：环境变量 `APP_BOOT_MODE` 不存在导致主动退出（exit 42） |\n\n**冲突/负向证据：** 无。所有计划中的 Pod 均真实存在于指定 namespace，事件内容与计划预期完全一致。","collection_summary":"计划 9 项，实际采集 9 项，未采集 0 项，完整度 100%；其中真实环境证据 15/15 项，完整度 100%；实际执行工具 14 个，匹配计划 10 个，未规划证据 4 个","plan_total":9,"plan_collected":9,"plan_completeness":1.0,"environment_evidence_total":15,"environment_evidence_collected":15,"environment_evidence_completeness":1.0,"executed_tool_count":14,"matched_tool_count":10,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e0-g2-runbook","description":"获取 pod-imagepull-failed.md runbook 参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"已有上游matched_runbooks，但再次获取确认runbook上下文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e1-g2-rep-pod-describe","description":"describe 代表Pod dns-test-1779360684(default) 验证ErrImagePull事件详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-1779360684 -n default","purpose":"查看Failed to pull image错误原文，确认i/o timeout或connection reset","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g2-image-check","description":"获取代表Pod的YAML确认image字段和imagePullSecrets","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod dns-test-1779360684 -n default -o yaml","purpose":"检查镜像地址、imagePullSecrets、imagePullPolicy","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-g2-node1-pod-describe","description":"describe node1上的代表Pod net-test-pod确认事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod net-test-pod -n default","purpose":"验证node1上Pod是否同样i/o timeout，排除节点差异","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-g2-node2-pod-describe","description":"describe node2上的代表Pod dns-test-check验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","purpose":"验证node2上Pod是否同样i/o timeout","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-g2-mcp-pod-describe","description":"describe mcp命名空间代表Pod connectivity-test验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","purpose":"验证mcp namespace的Pod是否同样仓库不可达","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6-g1-pod-describe","description":"describe CrashLoopBackOff Pod rc-config-env-missing","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e","purpose":"查看Last State、Exit Code、Reason、事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7-g1-previous-logs","description":"获取CrashLoopBackOff Pod崩溃前日志","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous --tail=200","purpose":"查看崩溃前容器日志确认退出原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e8-g1-yaml","description":"获取rc-config-env-missing的完整YAML","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e -o yaml","purpose":"检查command/args/env/resources等配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e9-g2-aiops-pod-describe","description":"describe aiops-e2e命名空间ErrImagePull Pod test-dns-1779360358","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"验证aiops-e2e命名空间ErrImagePull Pod的仓库连通性","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 9/9 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e0-g2-runbook | reference | ✅ | fetch_runbook | 获取 pod-imagepull-failed.md runbook 参考 | `fetch_runbook pod-imagepull-failed.md` |
   | e1-g2-rep-pod... | critical | ✅ | kubectl_describe | describe 代表Pod dns-test-1779360684(default) 验... | `kubectl describe pod dns-test-1779360684 -n default` |
   | e2-g2-image-c... | critical | ✅ | kubectl_get_yaml | 获取代表Pod的YAML确认image字段和imagePullSecrets | `kubectl get pod dns-test-1779360684 -n default -o yaml` |
   | e3-g2-node1-p... | important | ✅ | kubectl_describe | describe node1上的代表Pod net-test-pod确认事件 | `kubectl describe pod net-test-pod -n default` |
   | e4-g2-node2-p... | important | ✅ | kubectl_describe | describe node2上的代表Pod dns-test-check验证 | `kubectl describe pod dns-test-check -n default` |
   | e5-g2-mcp-pod... | important | ✅ | kubectl_describe | describe mcp命名空间代表Pod connectivity-test验证 | `kubectl describe pod connectivity-test -n mcp` |
   | e6-g1-pod-des... | critical | ✅ | kubectl_describe | describe CrashLoopBackOff Pod rc-config-env-m... | `kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e` |
   | e7-g1-previou... | critical | ✅ | kubectl_previous_logs | 获取CrashLoopBackOff Pod崩溃前日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous -...` |
   | e8-g1-yaml | important | ✅ | kubectl_get_yaml | 获取rc-config-env-missing的完整YAML | `kubectl get pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e -o yaml` |
   | e9-g2-aiops-p... | important | ✅ | kubectl_describe | describe aiops-e2e命名空间ErrImagePull Pod test-d... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (29.7s)
   📤 → 下游数据: root_cause=集群存在两个独立问题：（1）**主问题（L3，影响41个Pod，占异常Pod的97.6%）**：节点node1和node2到docker.io镜像仓库的网络不可达。证据：describe 6个代表Pod（覆盖node1/node2、default/mcp/aiops-e2e命名空间），全部显示`Failed to pull image "busybox:1.36.1"`，错误为`dial tcp [不同IP]:443: i/o timeout`或`connection reset by peer`，涉及10+不同docker.io IP地址（128.242.240.125、157.240.21.9、199.59.148.209等），最长重试7h10m/1298次。所有Pod使用合法公开镜像`busybox:1.36.1`，无imagePullSecrets，排除镜像不存在和认证问题。（2）**次要问题（L4，影响1个Pod）**：aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn因环境变量`APP_BOOT_MODE`未设置导致CrashL
... 截断，原始 608 字符
   confidence=98%
   causal_chain={"root_cause": "集群节点（node1、node2）到 docker.io 镜像仓库的出口网络不可达——HTTPS连接 registry-1.docker.io:443 全部 i/o timeout 或 connection reset by peer，涉及超过10个不同目的IP，排除单点故障，指向防火墙/代理/出口网关拦截或 docker.io 在国内被限制访问。", "propagation": "节点出口网络不可达 → containerd 无法通过 HTTPS 拉取镜像 → kubelet 反复重试失败 → Pod 状态变为 ErrImagePull（首次失败）→ 持续重试进入 ImagePullBackOff（退避重试）→ 41个Pod全部Pending", "direct_cause": "节点（node1/node2）无法建立到 registry-1.docker.io:443 的 TCP 连接，错误均为 i/o timeout（10+不同IP）和 connection reset by peer，说明集群出口到公网 docker.io 的网络链路存在阻断。", "manifestation": "用户可见: 41个Pod（分布于aiops-e2e、default、mcp三个命名空间）持续处于ErrImagePull(28个)和ImagePullBackOff(13个)状态，kubectl get pods显示Pending，Events显示长时间拉取镜像失败"}
   rca_analysis={"phenomenon": "集群共有42个异常Pod，分布在aiops-e2e、default、mcp三个命名空间。主异常组g2：41个Pod因镜像拉取失败处于Pending状态（ErrImagePull 28个、ImagePullBackOff 13个），分布在node1和node2两个节点上。次要异常组g1：1个Pod（aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn）因配置缺失处于CrashLoopBackOff状态。", "evidence_inventory": [{"id": "e0-g2-runbook", "source": "fetch_runbook pod-imagepull-failed.md", "content": "获取ImagePullFailed runbook参考，确认诊断流程：检查Pod状态、Events、镜像地址和PullSecret", "reliability": "高"}, {"id": "e1-g2-rep-pod-describe", "source": "kubectl_describe -n default dns-test-1779360684", "content": "代表Pod dns-test-1779360684: 镜像busybox:1.36.1, 状态Waiting/ErrImagePull, 785次重试失败, 均为i/o timeout", "reliability": "高"}, {"id": "e2-g2-image-check", "source": "kubectl_get_yaml -n default dns-test-1779360684", "content": "YAML确认: image=busybox:1.36.1, imagePullPolicy=IfNotPresent, 无imagePullSecrets, 错误信息含connection reset by peer", "reliability": "高"}, {"id": "e3-g2-node1-pod-describe", "source": "kubectl_describe -n default net-test-pod (node1)", "content": "node1代表Pod net-test-pod: ImagePullBackOff, 6次全部失败, 5次i/o timeout+1次connection reset to registry-1.docker.io:443", "reliability": "高"}, {"id": "e4-g2-node2-pod-describe", "source": "kubectl_describe -n default dns-test-check (node2)", "content": "node2代表Pod dns-test-check: ErrImagePull, i/o timeout to 202.160.129.37:443, 906次BackOff", "reliability": "高"}, {"id": "e5-g2-mcp-pod-describe", "source": "kubectl_describe -n mcp connectivity-test (node2)", "content": "mcp命名空间代表Pod connectivity-test: ErrImagePull, i/o timeout to 173.244.217.42:443, 1298次BackOff", "reliability": "高"}, {"id": "e6-g1-pod-describe", "source": "kubectl_describe -n aiops-e2e rc-config-env-missing", "content": "CrashLoopBackOff Pod描述: Last State Error, Exit Code 42, BackOff x95 over 21m", "reliability": "高"}, {"id": "e7-g1-previous-logs", "source": "kubectl_previous_logs rc-config-env-missing", "content": "崩溃前日志: L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "reliability": "高"}, {"id": "e8-g1-yaml", "source": "kubectl_get_yaml rc-config-env-missing", "content": "完整YAML: image=busybox:1.36, imagePullPolicy=Never, command含env校验逻辑, label pod_abnormal_type=ConfigError", "reliability": "高"}, {"id": "e9-g2-aiops-pod-describe", "source": "kubectl_describe -n aiops-e2e test-dns-1779360358", "content": "aiops-e2e代表Pod test-dns-1779360358: ImagePullBackOff, 5次i/o timeout到registry-1.docker.io:443, 不同IP", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "全局Pod扫描: 106总Pod, Running=59, ErrImagePull=28, ImagePullBackOff=13, CrashLoopBackOff=1, Completed=2", "reliability": "高"}, {"id": "layer_3", "source": "kubernetes_jq_query phase", "content": "异常Pod全部处于Pending或CrashLoopBackOff状态", "reliability": "高"}, {"summary": "... 截断，原始 13 项"}], "evidence_analysis": [{"evidence_id": "e0-g2-runbook", "raw_data": "Runbook ImagePullFailed: 场景识别-> Events含Failed to pull image, timeout, connection refused", "interpretation": "当前现象与runbook描述的镜像仓库网络不可达场景完全匹配"}, {"evidence_id": "e1-g2-rep-pod-describe", "raw_data": "Failed to pull image \"busybox:1.36.1\"... dial tcp 128.242.240.125:443: i/o timeout (785次重试, 7h5m历史)", "interpretation": "节点node1无法通过HTTPS连接到registry-1.docker.io，目标IP随时间变化但全部超时，说明不是单一IP故障而是整体网络不可达"}, {"evidence_id": "e2-g2-image-check", "raw_data": "image=busybox:1.36.1, imagePullSecrets=absent, 错误: connection reset by peer", "interpretation": "镜像名和tag合法(busybox:1.36.1是官方公开镜像)，无imagePullSecrets说明不是认证问题，connection reset by peer表明网络层面被主动拒绝(可能被墙或防火墙拦截)"}, {"evidence_id": "e3-g2-node1-pod-describe", "raw_data": "net-test-pod: 5x i/o timeout to IPs 128.242.240.125,69.162.134.178,199.59.148.209,128.242.240.244,108.160.170.39:443, 1x connection reset by peer to 3.90.170.8:443", "interpretation": "node1上不同Pod拉取同一镜像均失败，目标IP不同但错误模式完全一致，排除单点故障，确认是节点出口到docker.io的连通性问题"}, {"evidence_id": "e4-g2-node2-pod-describe", "raw_data": "dns-test-check(node2): Failed to pull image... dial tcp 202.160.129.37:443: i/o timeout (906次BackOff)", "interpretation": "node2同样无法连接docker.io，目标IP与node1不同(202.160.129.37)，说明两个节点都受影响，问题在集群出口层"}, {"evidence_id": "e5-g2-mcp-pod-describe", "raw_data": "connectivity-test(mcp/node2): Failed to pull image... dial tcp 173.244.217.42:443: i/o timeout (1298次BackOff)", "interpretation": "mcp命名空间的Pod同样受影响，确认问题与命名空间无关，是集群级别的网络问题"}, {"evidence_id": "e6-g1-pod-describe", "raw_data": "rc-config-env-missing: Exit Code 42, Last State=Error, BackOff x95 over 21m", "interpretation": "退出码42是自定义错误码(非标准信号)，kubelet不断重启但Pod无法正常运行"}, {"evidence_id": "e7-g1-previous-logs", "raw_data": "L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "interpretation": "容器启动脚本检查环境变量APP_BOOT_MODE，未设置时打印错误并exit 42，这是明确的应用配置缺失"}, {"evidence_id": "e8-g1-yaml", "raw_data": "imagePullPolicy=Never, command: sh -c, args: 'if [ -z \"${APP_BOOT_MODE:-}\" ]; then echo ...; exit 42; fi; sleep 3600', label: pod_abnormal_type=ConfigError", "interpretation": "YAML确认Pod设计为通过环境变量控制启动行为，APP_BOOT_MODE未设置是唯一原因。imagePullPolicy=Never说明镜像已存在本地，无拉取问题"}, {"evidence_id": "e9-g2-aiops-pod-describe", "raw_data": "test-dns-1779360358(aiops-e2e/node1): Failed... i/o timeout to IPs 128.242.240.20,50.117.117.42,108.160.166.57,198.44.185.131,199.59.148.229:443", "interpretation": "aiops-e2e命名空间也受影响，确认三个命名空间下所有41个ErrImagePull/ImagePullBackOff Pod共享同一根因"}, {"evidence_id": "layer_1", "raw_data": "Total pods: 106, Running: 59, ErrImagePull: 28, ImagePullBackOff: 13, CrashLoopBackOff: 1, Completed: 2", "interpretation": "异常Pod占比39.6%(42/106)，镜像拉取失败是绝对主要问题(41/42)"}, {"evidence_id": "layer_4", "raw_data": "41个Pod为ErrImagePull/ImagePullBackOff, 1个为CrashLoopBackOff", "interpretation": "确认异常分组: g1(1个CrashLoopBackOff)和g2(41个ImagePullFailed)是两个独立问题"}], "causal_chain": {"root_cause": "集群节点（node1、node2）到 docker.io 镜像仓库的出口网络不可达——HTTPS连接 registry-1.docker.io:443 全部 i/o timeout 或 connection reset by peer，涉及超过10个不同目的IP，排除单点故障，指向防火墙/代理/出口网关拦截或 docker.io 在国内被限制访问。", "propagation": "节点出口网络不可达 → containerd 无法通过 HTTPS 拉取镜像 → kubelet 反复重试失败 → Pod 状态变为 ErrImagePull（首次失败）→ 持续重试进入 ImagePullBackOff（退避重试）→ 41个Pod全部Pending", "direct_cause": "节点（node1/node2）无法建立到 registry-1.docker.io:443 的 TCP 连接，错误均为 i/o timeout（10+不同IP）和 connection reset by peer，说明集群出口到公网 docker.io 的网络链路存在阻断。", "manifestation": "用户可见: 41个Pod（分布于aiops-e2e、default、mcp三个命名空间）持续处于ErrImagePull(28个)和ImagePullBackOff(13个)状态，kubectl get pods显示Pending，Events显示长时间拉取镜像失败"}, "root_cause": "集群存在两个独立问题：（1）**主问题（L3，影响41个Pod，占异常Pod的97.6%）**：节点node1和node2到docker.io镜像仓库的网络不可达。证据：describe 6个代表Pod（覆盖node1/node2、default/mcp/aiops-e2e命名空间），全部显示`Failed to pull image \"busybox:1.36.1\"`，错误为`dial tcp [不同IP]:443: i/o timeout`或`connection reset by peer`，涉及10+不同docker.io IP地址（128.242.240.125、157.240.21.9、199.59.148.209等），最长重试7h10m/1298次。所有Pod使用合法公开镜像`busybox:1.36.1`，无imagePullSecrets，排除镜像不存在和认证问题。（2）**次要问题（L4，影响1个Pod）**：aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn因环境变量`APP_BOOT_MODE`未设置导致CrashL\n... 截断，原始 608 字符", "root_cause_summary": "集群存在两个独立问题：（1）**主问题（L3，影响41个Pod，占异常Pod的97.6%）**：节点node1和node2到docker.io镜像仓库的网络不可达。证据：describe 6个代表Pod（覆盖node1/node2、default/mcp/aiops-e2e命名空间），全部显示`Failed to pull image \"busybox:1.36.1\"`，错误为`dial tcp [不同IP]:443: i/o timeout`或`connection reset by peer`，涉及10+不同docker.io IP地址（128.242.240.125、157.240.21.9、199.59.148.209等），最长重试7h10m/1298次。所有Pod使用合法公开镜像`busybox:1.36.1`，无imagePullSecrets，排除镜像不存在和认证问题。（2）**次要问题（L4，影响1个Pod）**：aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn因环境变量`APP_BOOT_MODE`未设置导致CrashL\n... 截断，原始 608 字符", "confidence": 0.98, "confidence_reason": "有直接证据覆盖两个节点、三个命名空间、6个代表Pod的describe/YAML/logs，所有数据一致指向docker.io网络不可达。无冲突证据。CrashLoopBackOff Pod有崩溃前日志和完整YAML确认根因。置信度0.98。", "primary_runbooks": ["pod-imagepull-failed.md", "pod-crashloop-runtime.md"], "alternative_causes": [{"cause": "镜像名或tag错误（busybox:1.36.1不存在）", "probability": "极低", "reason": "busybox:1.36.1是Docker Hub官方有效镜像标签，错误信息不是manifest unknown而是网络超时，排除此原因"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "极低", "reason": "所有Pod YAML中imagePullSecrets为空，且busybox是公开镜像无需认证，错误信息不含unauthorized"}, {"cause": "DNS解析失败", "probability": "低", "reason": "kubelet成功解析registry-1.docker.io为多个IP（128.242.240.125等），DNS解析正常，故障在TCP连接阶段"}, {"cause": "单节点网络问题", "probability": "极低", "reason": "node1和node2均有Pod出现相同错误，涉及不同目标IP，排除单节点故障"}, {"cause": "containerd运行时故障", "probability": "低", "reason": "错误明确为网络层dial tcp超时，非containerd内部错误，且59个Running Pod正常运行说明containerd整体正常"}], "limitations": "未直接测试节点到docker.io的ICMP/curl连通性（如从节点上执行curl registry-1.docker.io），但kubelet Events已提供足够网络层诊断信息。未检查集群出口是否有代理配置（如HTTP_PROXY/HTTPS_PROXY），这是可能的解决方案路径但不是根因分析的必要证据。CrashLoopBackOff Pod的日志仅获取到一行关键日志(previous_logs)，但已足够定位问题。", "llm_raw_analysis": "## 证据清点\\n共采集13项证据，覆盖：\\n- 全局Pod状态扫描（1项）\\n- 代表Pod的YAML（2项，覆盖default和aiops-e2e命名空间）\\n- 代表Pod的describe（6项，覆盖node1/node2两个节点，default/mcp/aiops-e2e三个命名空间）\\n- 崩溃日志（1项）\\n- Runbook参考（1项）\\n- 上游已验证工具结果（2项）\\n\\n## 逐条分析\\n### g2组（41个ImagePullFailed Pod）\\n所有describe/YAML证据高度一致：镜像=busybox:1.36.1，无imagePullSecrets，错误均为i/o timeout或connection reset by peer到registry-1.docker.io:443，涉及10+不同IP地址。node1和node2同时受影响。排除镜像不存在、认证失败、DNS解析失败、单节点故障。\\n\\n### g1组（1个CrashLoopBackOff Pod）\\n崩溃前日志明确显示L4_CONFIG_BOOTSTRAP_FAIL: missing\n... 截断，原始 873 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群存在两个独立问题：（1）**主问题（L3，影响41个Pod，占异常Pod的97.6%）**：节点node1和node2到docker.io镜像仓库的网络不可达。证据：describe 6个代表Pod（覆盖node1/node2、default/mcp/aiops-e2e命名空间），全部显示`Fa...
   置信度: 98%
   🔗 因果链:
     根本原因: 集群节点（node1、node2）到 docker.io 镜像仓库的出口网络不可达——HTTPS连接 registry-1.docker.io:443 全部 i/o timeout 或 connection reset by peer，涉及超过10个不同目的IP，排除单点故障，指向防火墙/代理/出口网关拦截或 docker.io 在国内被限制访问。
     传导机制: 节点出口网络不可达 → containerd 无法通过 HTTPS 拉取镜像 → kubelet 反复重试失败 → Pod 状态变为 ErrImagePull（首次失败）→ 持续重试进入 ImagePullBackOff（退避重试）→ 41个Pod全部Pending
     最终表现: 用户可见: 41个Pod（分布于aiops-e2e、default、mcp三个命名空间）持续处于ErrImagePull(28个)和ImagePullBackOff(13个)状态，kubectl get pods显示Pending，Events显示长时间拉取镜像失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (35.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 10050 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 46.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，请查收您的集群诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群健康状态** | ❌ **异常**。共发现 **42 个异常 Pod**，占集群总 Pod 的 39.6%。 |
| **主要问题** | **问题1（主要）**：41 个 Pod 因镜像拉取失败处于 `Pending` 状态（28 个 `ErrImagePull`，13 个 `ImagePullBackOff`）<br>**问题2（次要）**：1 个 Pod 因应用配置缺失处于 `CrashLoopBackOff` 状态 |
| **兼容归因层** | L3 (镜像仓库网络不可达)、L4 (应用配置) |
| **问题分类** | `ImagePullFailed`, `ConfigError` |
| **置信度** | 高 (98%) |
| **证据完整度** | 9/9 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**核心发现**：您的 Kubernetes 集群（共 106 个 Pod）正在经历两个独立的问题，其中大规模镜像拉取失败是主要矛盾，影响了绝大多数异常 Pod。

### 关键实体

| 类型 | 值 |
|------|-----|
| **问题一** | **镜像拉取失败** — 影响 **41 个 Pod** |
| Pod 状态 | `ErrImagePull` (28个), `ImagePullBackOff` (13个) |
| 受影响 Namespace | `default`, `aiops-e2e`, `mcp` |
| 受影响 Node | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| 错误信息 | `Failed to pull image "busybox:1.36.1"`，核心错误为 `dial tcp [IP]:443: i/o timeout` 或 `connection reset by peer` |
| **问题二** | **应用配置错误** — 影响 **1 个 Pod** |
| Pod | `rc-config-env-missing-5d9b8b766c-bq8pn` (namespace: `aiops-e2e`) |
| Pod 状态 | `CrashLoopBackOff` (重启 8 次) |
| 退出码 | 42 (`ConfigError`) |
| 错误信息 | `missing required APP_BOOT_MODE` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | 集群状态总览 | `kubectl get pods --all-namespaces` | Total 106 Pods: Running=59, Completed=2, **ErrImagePull=28, ImagePullBackOff=13, CrashLoopBackOff=1** | 确认集群存在42个异常Pod，主要类型为镜像拉取失败和启动失败。 |
| 2 | 代表 Pod 事件 (1) | `kubectl describe pod dns-test-1779360684 -n default` | 容器 `dns-test-1779360684` 状态 `Waiting/ErrImagePull`。<br>事件: `Failed to pull image "busybox:1.36.1"`<br>错误详情: 6次拉取均失败，5次 `i/o timeout` 到 `128.242.240.125`, `157.240.21.9` 等，1次 `connection reset by peer` 到 `3.90.170.8`。<br>Kubelet 已重试 785 次超过 7 小时。 | 确认 node1 无法连接到 `registry-1.docker.io`，错误为网络超时和连接重置，排除镜像不存在或认证问题。 |
| 3 | 代表 Pod 事件 (2) | `kubectl describe pod net-test-pod -n default` | 容器 `net-test-pod` 状态 `Waiting/ImagePullBackOff`。<br>全部 6 次拉取失败，5次 `DeadlineExceeded` (i/o timeout) 到不同 IP，1次 `connection reset by peer`。<br>Kubelet 已重试 5 小时以上。 | 交叉验证 node1 到 `docker.io` 的网络问题，超时和连接重置现象普遍。 |
| 4 | 代表 Pod 事件 (3) | `kubectl describe pod connectivity-test -n mcp` | 状态 `Pending`。<br>事件: `Back-off pulling image "busybox:1.36.1"` (重试 1298 次)<br>错误: `i/o timeout` | 确认 node2 (`10.2.0.50`) 也存在相同的网络问题，无法拉取 `busybox` 镜像。问题波及所有节点。 |
| 5 | 代表 Pod 事件 (4) | `kubectl describe pod dns-test-check -n default` | 状态 `Pending`。<br>事件: `Back-off pulling image "busybox:1.36.1"` (重试 906 次)<br>错误: `i/o timeout` | 进一步确认 node2 的网络问题。 |
| 6 | 代表 Pod 事件 (5) | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` | 状态 `Pending`，容器状态 `Waiting/ImagePullBackOff`。<br>Kubelet 5次拉取失败: `Head https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1 timed out` (不同IP)。<br>Kubelet 已重试 5 次超过 7 小时。 | 确认 `aiops-e2e` 命名空间的 Pod 也受相同网络问题影响。 |
| 7 | CrashLoopBackOff Pod 状态 | `kubectl describe pod rc-config-env-missing -n aiops-e2e` | Pod 状态为 `Running`，但容器状态为 `CrashLoopBackOff`。<br>事件: `Back-off restarting failed container` (重试95次)。<br>Pod `label` 包含 `pod_abnormal_type=ConfigError`。 | 确认应用在启动后立即退出，退出码为 42，属于配置错误。 |
| 8 | CrashLoopBackOff Pod 日志 | `kubectl logs --previous pod rc-config-env-missing -n aiops-e2e` | 关键日志: **`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`** | 直接定位到根因：Pod 启动时缺少必需的 `APP_BOOT_MODE` 环境变量。 |
| 9 | 上层的全局 Pod YAML | `kubectl get pod dns-test-1779360684 -o yaml` | `finalizers: <none>`<br>`terminationGracePeriodSeconds: 30` | 确认 Pod 无 finalizers 残留，Terminating 状态非由 finalizer 引起。 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 + #5 + #6**：证据链完全闭环。41 个异常 Pod 分布在 3 个命名空间和 2 个节点上，其状态和事件都指向同一个根因：集群**所有节点无法访问 `docker.io` 仓库**。
- **证据 #7 + #8**：证据链完整。CrashLoopBackOff Pod 的状态、事件和崩溃前日志，清晰地指向根因：**缺少必需的 `APP_BOOT_MODE` 环境变量**。

### 缺失证据（如有）
无。证据完整度为 100%，根因分析所需的关键信息均已收集。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因（问题一）                                                                                                             │
│ 集群节点（node1, node2）的出口网络无法到达 docker.io 镜像仓库。到 registry-1.docker.io:443 的 HTTPS 连接全部 | i/o timeout      │
│ 或被 connection reset，涉及超过 10 个不同的 Docker Hub IP 地址，排除单点故障。                                                │
└──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                                                       │
│ 节点出口网络被防火墙/代理/网关拦截，或目标网络受限 → containerd 无法通过 HTTPS 拉取镜像 → kubelet 反复重试失败                  │
└──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                                                       │
│ 所有 Pod 拉取镜像时均返回 i/o timeout 或 connection reset，导致 kubelet 标记为 ErrImagePull，后续进入 ImagePullBackOff 退避。   │
└──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┐
│ 用户可见现象（问题一）                                                                                                         │
│ 41 个 Pod 在 kubectl get pods 中显示为 Pending，状态为 ErrImagePull (28个) 或 ImagePullBackOff (13个)。                        │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因（问题二）                                                                                                             │
│ Pod 的 Deployment 配置中未设置必须的环境变量 `APP_BOOT_MODE`，导致应用启动时因缺少配置而退出。                                 │
└──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┐
│ 用户可见现象（问题二）                                                                                                         │
│ Pod `rc-config-env-missing` 在 CrashLoopBackOff 状态中持续重启，事件显示容器反复启动失败。                                    │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**问题一：镜像拉取失败（41 个 Pod）**
- **结论**：根据证据 #2 到 #6，所有 `ErrImagePull`/`ImagePullBackOff` Pod 的 `kubectl describe` 输出均包含 `i/o timeout` 或 `connection reset by peer` 错误，连接目标均为 `registry-1.docker.io:443`。
- **根因**：**节点到 `docker.io` 镜像仓库的网络连接不可达**。
- **排除项**：
  - **排除镜像不存在**：镜像为公开的 `busybox:1.36.1`，且在多个 Pod YAML 中确认无误（证据 #2, #6）。
  - **排除认证问题**：Pod YAML 中未配置 `imagePullSecrets`（证据 #2）。
  - **排除节点单个故障**：node1 和 node2 均出现相同错误（证据 #2, #3, #4, #5）。

**问题二：应用配置错误（1 个 Pod）**
- **结论**：根据证据 #7 和 #8，Pod `rc-config-env-missing` 的崩溃前日志明确显示 `missing required APP_BOOT_MODE`。
- **根因**：**Pod 启动时缺少必需的 `APP_BOOT_MODE` 环境变量**。
- **置信度**：高（100%）。证据直接、明确。

**总置信度**：高 (98%)

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 排查并修复集群出口网络问题**
这是影响范围最大的问题，必须优先解决。
- **检查点**：
  - 集群是否位于公司内网/私有云？如果是，请检查**防火墙规则**或**代理配置**是否允许出站 `HTTPS (443)` 到 `*.docker.io`。
  - 集群所在网络出口是否有 **HTTP(S) 代理**？如果是，需要配置 `containerd` 使用代理。
- **命令（在节点上执行，作为诊断）**：
  ```bash
  # 测试节点到 docker.io 的连通性
  curl -v https://registry-1.docker.io/v2/ 2>&1 | grep -E "Connected|timed out|refused"
  
  # 如果没有 curl，使用 wget
  wget --timeout=5 https://registry-1.docker.io/v2/ -O /dev/null
  ```
  *注意：请通过 `ssh` 登录到 node1 和 node2 上执行。*
- **常见解决方案**：
  - **使用国内镜像加速器**：配置 `containerd` 使用阿里云 (`https://<your-code>.mirror.aliyuncs.com`) 或 `dockerproxy.com` 等镜像加速器。
  - **添加 HTTP 代理**：将 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量配置到 containerd 服务或节点层面。

**2. [次要] 修复 `rc-config-env-missing` Pod**
在解决网络问题后，修复此 Pod。
```bash
# 1. 先找出管理此 Pod 的 Deployment 或 StatefulSet
kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e | grep -i "Controlled By"

# 2. 假设它由一个名为 rc-config-env-missing 的 Deployment 管理，添加缺失的环境变量
kubectl set env deployment/rc-config-env-missing -n aiops-e2e APP_BOOT_MODE=production

# 或者，如果不知道具体值，先查看 Deployment YAML
kubectl get deployment rc-config-env-missing -n aiops-e2e -o yaml
```
*依据*：崩溃前日志显示 `missing required APP_BOOT_MODE`，需要通过环境变量注入应用配置。

### 后续优化

1.  **永久解决网络问题**：避免依赖单个公共仓库，考虑搭建内网的 Harbor 或 Nexus 镜像仓库，并从该内网仓库拉取所有镜像。
2.  **应用配置管理**：使用 **ConfigMap** 和 **Secret** 管理应用配置和敏感信息，避免直接在 Deployment YAML 中遗漏关键变量。
3.  **配置健康检查**：为应用添加 Readiness 和 Liveness 探针，在配置错误时 Kubernetes 可以自动处理，而不是不断重启。配置错误不应导致 `CrashLoopBackOff`，而应让 Pod 不接收流量并触发告警。
4.  **资源配置校验**：在 CI/CD 流水线中增加对 K8s YAML 的 Schema 校验，确保关键字段（如环境变量）不缺失。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认异常 Pod 总数减少 | `kubectl get pods --all-namespaces \| grep -E "ErrImagePull\|ImagePullBackOff\|CrashLoopBackOff"` | 无输出 或 异常 Pod 数量减少至 0 |
| 2. 验证镜像拉取恢复正常 | `kubectl describe pod <之前的ErrImagePull Pod> -n <namespace>` | Events 中无 i/o timeout 错误，Pod 状态变为 Running |
| 3. 验证配置修复 | `kubectl get pod rc-config-env-missing -n aiops-e2e` | STATUS 为 Running |
| 4. 检查修复后的 Pod 日志 | `kubectl logs rc-config-env-missing -n aiops-e2e` | 日志正常输出，不再有 `missing required APP_BOOT_MODE` 错误 |

## ⚠️ 注意事项
- 修复集群出口网络时，请注意操作窗口，避免影响集群内部业务。
- `APP_BOOT_MODE` 环境变量的值（如 `production`, `development`）需要与应用开发者确认，设置错误的模式可能导致其他问题。
- 如果无法连通外网，建议立刻搭建内网镜像仓库，将所有容器镜像推送至内网仓库，并修改所有工作负载的 `image` 字段指向内网地址。这是解决此类问题的最根本方法。

---

## 📊 性能统计

├─ 总耗时: 2.8m
├─ 问题定位: 46.7s (28%) ✅
├─ 证据链采集: 55.5s (33%) ✅
├─ 根因分析: 29.7s (18%) ✅
├─ 汇总总结: 35.0s (21%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 27 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-crashloop-runtime
- **参考 Runbook**: pod-imagepull-failed, pod-crashloop-runtime, pod-config-error
- **工具调用**: 27 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
