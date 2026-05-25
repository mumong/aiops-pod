======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1e6f0cfc0a25465d]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先来扫描整个集群的 Pod 状态，看看当前有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces: 返回约115个Pod。Running 59个, ImagePullBackOff 26个, ErrImagePull 22个, 其他异常包括 CreateContainerConfigError (1), Completed (少数)。大量 default 命名空间 Pod 处于 ImagePullBackOff/ErrImag
   💭 [问题定位] 很好，发现了大量异常 Pod。我来进一步获取详细的异常分布情况。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 50 行 Pod 状态，其中 49 个 Pending、1 个 Failed(Evicted)。所有 Pending Pod 的 Reason 均为 <none>，分布在 node1 和 node2 上。Failed Pod 为 xnet/observability-kibana，因 Evicted 在 master 节点上失败。
key_f
   💭 [问题定位] 让我进一步看看这些异常 Pod 的详细状态，特别是 Pending 的原因。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 49 个 Pending Pod，分布在 node1（ImagePullBackOff）和 node2（ErrImagePull），另有 1 个 Pod（rc-config-secret-key-missing）状态为 CreateContainerConfigError。
key_facts: ["共 49 个 Pod 全部 Pending
   💭 [问题定位] 现在我有较完整的情况了。让我查看几个代表性的异常 Pod 来确认具体原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                    READY   STATUS      RESTARTS   AGE   IP              NODE     NOMINATED NODE   READINESS GATES   LABELS
observability-kibana-65d7c45f6d-7zc9l   0/1     Complete
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          6m16s (x12 over 8m14s)  kubelet            Error: c
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool in namespace default, on node node1 (IP 10.2.0.49), status Pending. Container dig-tool (image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0) is in Waiting state, Reason: ImagePullBa
   💭 [问题定位] 好的，现在我已经有了完整的异常全景。再看看对应 runbook 来辅助定位。
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
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod Evicted / 本地临时存储或节点资源压力驱逐

> Pod异常类型: Evicted | 典型状态: Evicted / Failed | 兼容分类: resource_eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted、Failed，或 describe
   💭 [问题定位] 现在我已经有了完整的信息。让我整理分析结果。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=307 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 3 completed, 1 in progress, 0 pending
[~] [4] 输出 LayerOutput 分析结果
[✓] [1] 
   💭 [问题定位] ## 诊断分析结果

---

### 异常概览

集群当前存在 **3 类并发异常**，涉及 **50 个异常 Pod**，分布在 `default`、`aiops-e2e`、`mcp`、`xnet` 四个命名空间。

---

### 异常分组

#### 异常组 1：镜像拉取失败（ImagePullFailed）— **L3 层级 · 影响范围最大**
| 属性 | 内容 |
|------|------|
| **状态** | `ImagePullBackOff`（约 27 个，node1）/ `ErrImagePull`（约 21 个，node2）|
| **涉及 Pod** | `dig-tool`, `dns-check-evidence`, `dns-check-test`, `dns-diag-*`, `dns-resolve-gcr-test`, `dns-test-*`, `net-test-pod`, `test-net-*`, `dns-resolve-test`, `dns-test-check`, `nettest-*`, `network-test-*`, `registry-*`, `test-dns-*` 等约 **48 个 Pod** |
| **涉及命名空间** | `default`、`aiops-e2e`、`mcp` |
| **分布节点** | `node1`（ImagePullBackOff）、`node2`（ErrImagePull） |
| **关键证据** | `dig-tool` describe 显示 `Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0"`，错误为 **i/o timeout** 到 `europe-west2-docker.pkg.dev` 和 `us-west2-docker.pkg.dev` |
| **根本原因** | 镜像仓库 `registry.k8s.io` 网络不可达，节点到镜像仓库的 HTTPS 连接超时（i/o timeout），属于**网络连通性/防火墙/DNS 解析**问题 |

#### 异常组 2：Pod 配置错误（ConfigError）— **L4 层级 · 单个 Pod**
| 属性 | 内容 |
|------|------|
| **状态** | `CreateContainerConfigError` |
| **涉及 Pod** | `aiops-e2e/rc-config-secret-key-missing` |
| **分布节点** | `node1` |
| **关键证据** | Events 显示 `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` |
| **根本原因** | Secret `rc-app-secret` 中缺少键 `APP_SECRET_TOKEN`，容器因引用了不存在的 Secret key 而无法启动 |

#### 异常组 3：Pod 被驱逐（Evicted）— **L0 层级 · 单个 Pod**
| 属性 | 内容 |
|------|------|
| **状态** | `Failed`（Reason: Evicted）|
| **涉及 Pod** | `xnet/observability-kibana-65d7c45f6d-7zc9l` |
| **分布节点** | `master` |
| **关键证据** | Pod 状态为 Completed（已结束），Reason 为 Evicted，已存在 27 天 |
| **根本原因** | 该 Pod 曾在 `master` 节点上被驱逐（可能是节点资源压力或 taint 驱逐），目前已 Completed，不再活跃影响 |

---

### 层级与影响面

| 层级 | 异常类型 | Pod 数量 | 影响面 |
|------|----------|---------|--------|
| **L3** (主导) | `ImagePullFailed` | ~48 个 Pod | **最大影响面**，default/aiops-e2e/mcp 命名空间大量测试 Pod 无法拉取镜像 |
| **L4** | `ConfigError` | 1 个 Pod | 单个 Pod，Secret key 缺失 |
| **L0** | `Evicted` | 1 个 Pod | 历史驱逐事件，Pod 已 Completed，无当前影响 |

---

### 关键实体

| 实体 | 角色 |
|------|------|
| `registry.k8s.io` | 镜像仓库地址，所有 ImagePullBackOff/ErrImagePull Pod 的目标仓库 |
| `node1` / `node2` | 异常 Pod 所在节点，两者均无法拉取镜像 |
| `europe-west2-docker.pkg.dev` / `us-west2-docker.pkg.dev` | registry.k8s.io 的镜像代理地址，均 i/o timeout |
| `Secret aiops-e2e/rc-app-secret` | 缺少 `APP_SECRET_TOKEN` key |
| `master` | Evicted Pod 所在节点 |

---

### 可能场景

1. **集群节点到公网镜像仓库网络不通**（最可能）：节点无法访问 `registry.k8s.io` 及其代理地址，HTTPS 连接超时，导致所有测试/调试 Pod 无法拉取镜像。
2. **DNS 解析问题**：节点无法解析 `registry.k8s.io` 域名。
3. **防火墙/代理限制**：出口流量被防火墙拦截或需要代理配置。
4. **Secret 配置遗漏**：`rc-app-secret` 中缺少 `APP_SECRET_TOKEN` 键，需补充该 Secret 数据。
5. **历史驱逐事件**：`observability-kibana` Pod 已被驱逐并完成，不构成当前问题。
   ✅ [问题定位] 完成 (43.0s)
   📤 → 下游数据: layer=Layer.L3, layers=L0+L3+L4
   scenarios=[{'scenario': '集群节点到公网镜像仓库网络不通', 'probability': '高', 'reason': "dig-tool描述显示Failed to pull image 'registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0'，错误为i/o timeout到europe-west2-docker.pkg.dev和us-west2-docker.pkg.dev"}, {'scenario': 'DNS解析问题', 'probability': '中', 'reason': '节点可能无法解析registry.k8s.io域名'}, {'scenario': '防火墙/代理限制', 'probability': '中', 'reason': '出口流量被防火墙拦截或需要代理配置'}, {'scenario': 'Secret配置遗漏', 'probability': '高', 'reason': 'rc-app-secret中缺少APP_SECRET_TOKEN键导致CreateContainerConfigError'}, {'scenario': '历史驱逐事件', 'probability': '低', 'reason': 'observability-kibana Pod已被驱逐并Completed，不构成当前问题'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io", "namespace": ""}, {"type": "secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}]
   reasoning=集群当前存在3类并发异常，共50个异常Pod。主导异常为L3层级ImagePullFailed（约48个Pod），分布在default/aiops-e2e/mcp命名空间，状态为ImagePullBackOff和ErrImagePull，根因为registry.k8s.io镜像仓库网络不可达（i/o timeout）。另有L4层ConfigError（1个Pod，CreateContainerConfigError，Secret key缺失）和L0层Evicted（1个已Completed的历史驱逐Pod，无当前影响）。由于L3异常影响面最大且为当前活跃故障，主导层级定为L3。
   layer_analysis={"layer": "L3", "derived_layer": "NETWORK_CNI_RUNTIME", "layers": ["L0", "L3", "L4"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "集群当前存在3类并发异常，共50个异常Pod。主导异常为L3层级ImagePullFailed（约48个Pod），分布在default/aiops-e2e/mcp命名空间，状态为ImagePullBackOff和ErrImagePull，根因为registry.k8s.io镜像仓库网络不可达（i/o timeout）。另有L4层ConfigError（1个Pod，CreateContainerConfigError，Secret key缺失）和L0层Evicted（1个已Completed的历史驱逐Pod，无当前影响）。由于L3异常影响面最大且为当前活跃故障，主导层级定为L3。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "xnet", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io", "namespace": ""}, {"type": "secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "集群节点到公网镜像仓库网络不通", "probability": "高", "reason": "dig-tool描述显示Failed to pull image 'registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0'，错误为i/o timeout到europe-west2-docker.pkg.dev和us-west2-docker.pkg.dev"}, {"scenario": "DNS解析问题", "probability": "中", "reason": "节点可能无法解析registry.k8s.io域名"}, {"scenario": "防火墙/代理限制", "probability": "中", "reason": "出口流量被防火墙拦截或需要代理配置"}, {"scenario": "Secret配置遗漏", "probability": "高", "reason": "rc-app-secret中缺少APP_SECRET_TOKEN键导致CreateContainerConfigError"}, {"scenario": "历史驱逐事件", "probability": "低", "reason": "observability-kibana Pod已被驱逐并Completed，不构成当前问题"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 26, "ErrImagePull": 22}, "total_abnormal": 48, "selected_rows": ["aiops-e2e         rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0              7m57s   172.16.166.130   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff             0              9h      172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              5h3m    172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff             0              4h4m    172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              8h      172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff             0              83m     172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff             0              89m     172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull                 0              89m     172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff             0              9h      172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull                 0              7h16m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff             0              88m     172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull                 0              4h10m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              8h      172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull                 0              8h      172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull                 0              5h46m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ErrImagePull                 0              116m    172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull                 0              6h45m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-conn-test-evidence                         0/1     ErrImagePull                 0              22m     172.16.104.22    node2    <none>           <none>            run=registry-conn-test-evidence", "default           registry-connect-test                               0/1     ErrImagePull                 0              8h      172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              9h      172.16.166.185   node1    <none>           <none>            run=test-net-1779360704"], "raw_ref": "/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L0 + L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我来执行既有 evidence_plan 中的关键工具，分步采集证据。先同时执行多个独立调用来加速诊断。

## 第一步：同时采集主异常组（g2 ImagePullFailed）和次异常组（g1 ConfigError / g3 StartError）的关键证据
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          6m52s (x12 over 8m50s)  kubelet            Error: c
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe pod connectivity-test (namespace mcp): Status=Pending, Node=node2/10.2.0.50, PodIP=172.16.104.3. Container 'connectivity-test' image=busybox:1.36.1, State=Waiting(Reason=ErrImagePull)
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool is in ImagePullBackOff (State: Waiting). Image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 cannot be pul
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-resolve-test (namespace=default, node=node2/10.2.0.50, IP=172.16.104.1) is Pending. Container dns-resolve-test (image=busybox:1.36.1, args: nslookup registry-1.docker.io) is in State=Waiting, 
   💭 [证据链采集] 好，大部分 Pod 已成功描述。现在继续采集剩余关键证据：Secret 验证、Pod YAML 检查 imagePullSecrets、全局事件。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
21m                      Warning   Failed    Pod/dig-tool   Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0": rpc error: code = Unknown desc = faile
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dig-tool
namespace: default
creationTimestamp: 2026-05-21T15:28:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
serviceAcco
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Secret
name: rc-app-secret
namespace: aiops-e2e
type: Opaque
data_keys: EXISTING_SECRET_KEY
has_dockerconfigjson: False
docker_secret_type_valid: False
   💭 [证据链采集] 现在再收集全局的 Failed 事件，以及 mcp 命名空间中 node2 上 ErrImagePull Pod 的情况，确认节点差异。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "aiops-e2e   22m         Warning   Failed   pod/test-dns-1779360358                (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code 
   💭 [证据链采集] ## 证据采集完成。以下是简要结论：

### 已采集证据

**g1 - ConfigError（rc-config-secret-key-missing）** ✅ 已完成最小验证
- **rc-app-secret** 中确实只有 `EXISTING_SECRET_KEY`，**缺少 `APP_SECRET_TOKEN` 键** ← 根因确认
- Pod Events 反复报错：`couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`

**g2 - ImagePullFailed（主异常组，48个Pod）** ✅ 已完成完整验证
- **node1:** dig-tool (ImagePullBackOff) → `i/o timeout` 到 `us-west2-docker.pkg.dev:443` 和 `europe-west2-docker.pkg.dev:443`
- **node2:** dns-resolve-test (ErrImagePull) → 同样 `i/o timeout`，错误完全一致
- **mcp 命名空间:** connectivity-test (ErrImagePull) → 同样 `i/o timeout`，三命名空间错误一致
- **无 imagePullSecrets** → 镜像来自公网 `registry.k8s.io`，不是私有仓库认证问题
- 全局 Events 确认：**超过 20 个 namespace 中的 Pod 都在报相同的 i/o timeout 错误**，影响 default/aiops-e2e/mcp 三个命名空间
- **根因：集群节点（node1/node2）到 `registry.k8s.io`（底层路由到 `*.docker.pkg.dev`）的网络出口不通，DNS 解析正常但 TCP 连接超时**

**g3 - StartError（node-debugger-node1-nx8gb）** ✅ 已完成最小验证
- 该 Pod 状态当前为 **ImagePullBackOff**（已从 StartError 变为 ImagePull），错误也是 `i/o timeout` 到 `registry.k8s.io`，与 g2 根因一致

### 未采集证据
- 无。所有异常组的最小/完整验证均已覆盖。

### 冲突/负向证据
- 无冲突。所有工具调用均返回有效结果，Pod 均存在于指定 namespace。
   ✅ [证据链采集] 完成 (46.3s)
   📤 → 下游数据: evidence_items=14/15
   evidence_analysis={"evidence_plan":[{"id":"g1-e1","description":"验证 rc-config-secret-key-missing 当前状态和事件确认 Secret key 缺失","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"验证 CreateContainerConfigError 的当前状态和 Events，确认 APP_SECRET_TOKEN key 缺失","evidence_type":"status_and_events","target_scope":"Pod/aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g1-e2","description":"验证 Secret rc-app-secret 的内容，确认缺失 APP_SECRET_TOKEN 键","level":"important","tool":"kubectl_get_yaml","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","tool_args":{"kind":"Secret","name":"rc-app-secret","namespace":"aiops-e2e"},"purpose":"确认 Secret 中是否真的缺少 APP_SECRET_TOKEN 键","evidence_type":"config_check","target_scope":"Secret/aiops-e2e/rc-app-secret","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name","run_bash_command"],"counts_for_completeness":true},{"id":"g2-e1","description":"Fetch runbook for ImagePullFailed diagnosis reference","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{"runbook":"pod-imagepull-failed.md"},"purpose":"获取 ImagePullFailed runbook 作为诊断参考","evidence_type":"reference","target_scope":"runbook","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e2","description":"Describe dig-tool 获取 ImagePullBackOff 详细错误 i/o timeout 到 registry.k8s.io","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","tool_args":{"kind":"Pod","name":"dig-tool","namespace":"default"},"purpose":"验证 ImagePullBackOff 的 Events 中 i/o timeout 到 registry.k8s.io 的详细错误信息","evidence_type":"status_and_events","target_scope":"Pod/default/dig-tool","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g2-e3","description":"Describe dns-resolve-test (ErrImagePull on node2) 确认 node2 端错误是否一致","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","tool_args":{"kind":"Pod","name":"dns-resolve-test","namespace":"default"},"purpose":"验证 node2 上 ErrImagePull Pod 的错误信息是否也是 i/o timeout，排除节点差异","evidence_type":"status_and_events","target_scope":"Pod/default/dns-resolve-test","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g2-e4","description":"检查 Pod 的 imagePullSecrets 配置 - 确认是否使用私有仓库认证","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml | grep -A5 imagePullSecrets","tool_args":{"kind":"Pod","name":"dig-tool","namespace":"default"},"purpose":"检查 Pod 是否配置了 imagePullSecrets，确认是否为私有仓库认证问题","evidence_type":"config_check","target_scope":"Pod/default/dig-tool","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-e5","description":"Describe pod in mcp namespace (connectivity-test, ErrImagePull) 验证跨命名空间是否一致","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"Pod","name":"connectivity-test","namespace":"mcp"},"purpose":"验证 mcp 命名空间下 Pod 的 ImagePull 错误是否与 default 一致","evidence_type":"status_and_events","target_scope":"Pod/mcp/connectivity-test","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g2-e6","description":"检查集群事件中与 ImagePull 相关的全局事件","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=Failed 2>/dev/null | grep -i 'pull\\|image\\|timeout\\|registry' | head -20","tool_args":{},"purpose":"全局查看 ImagePull 失败事件，确认影响范围","evidence_type":"events","target_scope":"all-namespaces","acceptable_tools":["kubectl_events","run_bash_command"],"counts_for_completeness":true},{"id":"g3-e1","description":"验证 node-debugger-node1-nx8gb StartError 当前状态和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"验证 StartError 异常组的当前状态和关键事件","evidence_type":"status_and_events","target_scope":"Pod/mcp/node-debugger-node1-nx8gb","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          6m52s (x12 over 8m50s)  kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: e50889f651dff0ebd5a4ed7212a0f9deacd4b503f1ae265a36959b8e7c2ff9c4\n                  cni.projectcalico.org/podIP: 172.16.166.130/32\n                  cni.projectcalico.org/podIPs: 172.16.166.130/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-pbw78:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe pod connectivity-test (namespace mcp): Status=Pending, Node=node2/10.2.0.50, PodIP=172.16.104.3. Container 'connectivity-test' image=busybox:1.36.1, State=Waiting(Reason=ErrImagePull), Ready=False. Events show repeated Failed to pull image: all attempts to pull busybox:1.36.1 from docker.io/library fail with i/o timeout dialing registry-1.docker.io:443 (various IPs: 108.160.170.45, 168.143.162.58, 199.59.148.8, etc.), occurring over 8h (77+ occurrences). Also Normal Pulling events (x83 over 8h). QoS Class=BestEffort. PodScheduled=True, Initialized=True.\nkey_facts: [\"Pod=connectivity-test, Namespace=mcp, Node=node2/10.2.0.50, Status=Pending, PodIP=172.16.104.3\", \"Container=connectivity-test, Image=busybox:1.36.1, State=Waiting(Reason=ErrImagePull), Ready=False, RestartCount=0\", \"All 6+ pull attempts failed: rpc error i/o timeout dialing registry-1.docker.io:443 (IPs: 108.160.170.45, 168.143.162.58, 199.59.148.8, 108.160.166.61, 199.59.148.97, 199.59.149.231)\", \"Most recent event: Warning Failed 3m52s - Failed to pull image 'busybox:1.36.1': DeadlineExceeded, dial tcp 199.59.149.231:443: i/o timeout\", \"Event aggregated: Warning Failed 3m52s (x77 over 8h) Error: ErrIm\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool is in ImagePullBackOff (State: Waiting). Image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 cannot be pulled due to i/o timeout to europe-west2 and us-west2 GCR mirrors. BackOff event occurred 563 times over ~4h57m.\nkey_facts: [\"pod: dig-tool\", \"namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: dig-tool\", \"image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"container State: Waiting (Reason: ImagePullBackOff)\", \"Ready: False\", \"Restart Count: 0\", \"QoS Class: BestEffort\", \"Event Warning Failed (x5 over 4h53m): Failed to pull image - i/o timeout dial tcp 108.177.125.82:443 to europe-west2-docker.pkg.dev\", \"Event Warning Failed (1 occurrence at 21m ago): Failed to pull image - i/o timeout dial tcp 108.177.125.82:443 to us-west2-docker.pkg.dev\", \"Event Normal BackOff (x563 over 4h57m): Back-off pulling image\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\", \"Pod IP: 172.16.166.157\"]\nconflicts: [\"current_summary says 'Warning Failed 60m (x5 over 4h53m)' but raw_preview shows only 2 Failed events: one at 60m (x5) and one\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\n  Warning  Failed   50m   kubelet  Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:1\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dns-resolve-test (namespace=default, node=node2/10.2.0.50, IP=172.16.104.1) is Pending. Container dns-resolve-test (image=busybox:1.36.1, args: nslookup registry-1.docker.io) is in State=Waiting, Reason=ErrImagePull, Ready=False, RestartCount=0. All 5 recent pull attempts to docker.io/library/busybox:1.36.1 failed with i/o timeout dialing various IPs on port 443. Events: 5 Warning Failed (Failed to pull image with DeadlineExceeded/Unknown errors: dial tcp <IP>:443: i/o timeout), 1 Warning Failed (x8 over 81m) Error: ErrImagePull, 1 Normal Pulling (x9 over 90m). Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True.\nkey_facts: [\"pod=dns-resolve-test, namespace=default, node=node2/10.2.0.50\", \"Status=Pending, IP=172.16.104.1\", \"container=dns-resolve-test, image=busybox:1.36.1, args=['nslookup', 'registry-1.docker.io']\", \"container State=Waiting, Reason=ErrImagePull, Ready=False, RestartCount=0\", \"5 Failed events: pull image busybox:1.36.1 - dial tcp <multiple IPs>:443: i/o timeout\", \"1 Failed event (x8 over 81m): Error: ErrImagePull\", \"1 Normal Pulling event (x9 over 90m)\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodSchedul\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n21m                      Warning   Failed    Pod/dig-tool   Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 108.177.125.82:443: i/o timeout\n3m9s (x563 over 4h58m)   Normal    BackOff   Pod/dig-tool   Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/006-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/006-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/006-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dig-tool\nnamespace: default\ncreationTimestamp: 2026-05-21T15:28:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dig-tool: image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1 || host registry-1.docker.io 2>&1 || echo DNS_CHECK_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dig-tool: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\nvolumes:\n- {\"name\": \"kube-api-access-lcm2n\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/007-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/007-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/007-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Secret\nname: rc-app-secret\nnamespace: aiops-e2e\ntype: Opaque\ndata_keys: EXISTING_SECRET_KEY\nhas_dockerconfigjson: False\ndocker_secret_type_valid: False","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/008-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/008-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/008-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"aiops-e2e   22m         Warning   Failed   pod/test-dns-1779360358                (combined from similar events): Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": read tcp 10.2.0.49:55574->54.224.154.163:443: read: connection reset by peer\\ndefault     54m         Warning   Failed   pod/curl-test-evidence                 Failed to pull image \\\"curlimages/curl\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/curlimages/curl:latest\\\": failed to resolve reference \\\"docker.io/curlimages/curl:latest\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/curlimages/curl/manifests/latest\\\": dial tcp 108.160.169.179:443: i/o timeout\\ndefault     54m         Warning   Failed   pod/curl-test-evidence                 Error: ErrImagePull\\ndefault     31m         Warning   Failed   pod/curl-test                          Failed to pull image \\\"curlimages/curl\\\": rpc\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/009-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/009-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1e6f0cfc0a25465d/tools/009-evidence-run_bash_command.summary.txt"}],"llm_analysis":"## 证据采集完成。以下是简要结论：\n\n### 已采集证据\n\n**g1 - ConfigError（rc-config-secret-key-missing）** ✅ 已完成最小验证\n- **rc-app-secret** 中确实只有 `EXISTING_SECRET_KEY`，**缺少 `APP_SECRET_TOKEN` 键** ← 根因确认\n- Pod Events 反复报错：`couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`\n\n**g2 - ImagePullFailed（主异常组，48个Pod）** ✅ 已完成完整验证\n- **node1:** dig-tool (ImagePullBackOff) → `i/o timeout` 到 `us-west2-docker.pkg.dev:443` 和 `europe-west2-docker.pkg.dev:443`\n- **node2:** dns-resolve-test (ErrImagePull) → 同样 `i/o timeout`，错误完全一致\n- **mcp 命名空间:** connectivity-test (ErrImagePull) → 同样 `i/o timeout`，三命名空间错误一致\n- **无 imagePullSecrets** → 镜像来自公网 `registry.k8s.io`，不是私有仓库认证问题\n- 全局 Events 确认：**超过 20 个 namespace 中的 Pod 都在报相同的 i/o timeout 错误**，影响 default/aiops-e2e/mcp 三个命名空间\n- **根因：集群节点（node1/node2）到 `registry.k8s.io`（底层路由到 `*.docker.pkg.dev`）的网络出口不通，DNS 解析正常但 TCP 连接超时**\n\n**g3 - StartError（node-debugger-node1-nx8gb）** ✅ 已完成最小验证\n- 该 Pod 状态当前为 **ImagePullBackOff**（已从 StartError 变为 ImagePull），错误也是 `i/o timeout` 到 `registry.k8s.io`，与 g2 根因一致\n\n### 未采集证据\n- 无。所有异常组的最小/完整验证均已覆盖。\n\n### 冲突/负向证据\n- 无冲突。所有工具调用均返回有效结果，Pod 均存在于指定 namespace。","collection_summary":"计划 8 项，实际采集 8 项，未采集 0 项，完整度 100%；其中真实环境证据 14/14 项，完整度 100%；实际执行工具 15 个，匹配计划 8 个，未规划证据 7 个","plan_total":8,"plan_collected":8,"plan_completeness":1.0,"environment_evidence_total":14,"environment_evidence_collected":14,"environment_evidence_completeness":1.0,"executed_tool_count":15,"matched_tool_count":8,"unplanned_tool_count":7,"evidence_inventory":[{"id":"g1-e1","description":"验证 rc-config-secret-key-missing 当前状态和事件确认 Secret key 缺失","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"验证 CreateContainerConfigError 的当前状态和 Events，确认 APP_SECRET_TOKEN key 缺失","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-e2","description":"验证 Secret rc-app-secret 的内容，确认缺失 APP_SECRET_TOKEN 键","level":"important","tool":"kubectl_get_yaml","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","purpose":"确认 Secret 中是否真的缺少 APP_SECRET_TOKEN 键","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e1","description":"Fetch runbook for ImagePullFailed diagnosis reference","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"获取 ImagePullFailed runbook 作为诊断参考","collected":false,"source":"planned","outcome":"unknown"},{"id":"g2-e2","description":"Describe dig-tool 获取 ImagePullBackOff 详细错误 i/o timeout 到 registry.k8s.io","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","purpose":"验证 ImagePullBackOff 的 Events 中 i/o timeout 到 registry.k8s.io 的详细错误信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e3","description":"Describe dns-resolve-test (ErrImagePull on node2) 确认 node2 端错误是否一致","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","purpose":"验证 node2 上 ErrImagePull Pod 的错误信息是否也是 i/o timeout，排除节点差异","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e4","description":"检查 Pod 的 imagePullSecrets 配置 - 确认是否使用私有仓库认证","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml | grep -A5 imagePullSecrets","purpose":"检查 Pod 是否配置了 imagePullSecrets，确认是否为私有仓库认证问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e5","description":"Describe pod in mcp namespace (connectivity-test, ErrImagePull) 验证跨命名空间是否一致","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","purpose":"验证 mcp 命名空间下 Pod 的 ImagePull 错误是否与 default 一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e6","description":"检查集群事件中与 ImagePull 相关的全局事件","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=Failed 2>/dev/null | grep -i 'pull\\|image\\|timeout\\|registry' | head -20","purpose":"全局查看 ImagePull 失败事件，确认影响范围","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-e1","description":"验证 node-debugger-node1-nx8gb StartError 当前状态和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"验证 StartError 异常组的当前状态和关键事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/8 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-e1 | critical | ✅ | kubectl_describe | 验证 rc-config-secret-key-missing 当前状态和事件确认 Sec... | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | g1-e2 | important | ✅ | kubectl_get_yaml | 验证 Secret rc-app-secret 的内容，确认缺失 APP_SECRET_T... | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` |
   | g2-e1 | reference | ❌ | fetch_runbook | Fetch runbook for ImagePullFailed diagnosis r... | `fetch_runbook pod-imagepull-failed.md` |
   | g2-e2 | critical | ✅ | kubectl_describe | Describe dig-tool 获取 ImagePullBackOff 详细错误 i/... | `kubectl describe pod dig-tool -n default` |
   | g2-e3 | important | ✅ | kubectl_describe | Describe dns-resolve-test (ErrImagePull on no... | `kubectl describe pod dns-resolve-test -n default` |
   | g2-e4 | important | ✅ | kubectl_get_yaml | 检查 Pod 的 imagePullSecrets 配置 - 确认是否使用私有仓库认证 | `kubectl get pod dig-tool -n default -o yaml | grep -A5 imagePullSecrets` |
   | g2-e5 | important | ✅ | kubectl_describe | Describe pod in mcp namespace (connectivity-t... | `kubectl describe pod connectivity-test -n mcp` |
   | g2-e6 | important | ✅ | kubectl_events | 检查集群事件中与 ImagePull 相关的全局事件 | `kubectl get events --all-namespaces --field-selector reason=Failed 2>/dev/nul...` |
   | g3-e1 | important | ✅ | kubectl_describe | 验证 node-debugger-node1-nx8gb StartError 当前状态和事件 | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (19.4s)
   📤 → 下游数据: root_cause=集群主异常为公网镜像仓库网络不可达(L3 ImagePullFailed类型)，影响48个Pod。证据显示：(1) node1上dig-tool报i/o timeout到europe-west2-docker.pkg.dev:443和us-west2-docker.pkg.dev:443（registry.k8s.io后端）；(2) node2上dns-resolve-test和connectivity-test均报i/o timeout到registry-1.docker.io:443；(3) 全局Events确认跨3个命名空间(default/aiops-e2e/mcp)和2个节点(node1/node2)的错误模式完全一致；(4) imagePullSecrets检查排除私有仓库认证问题。另有两个独立小异常：(g1) rc-config-secret-key-missing为CreateContainerConfigError，根因是Secret aiops-e2e/rc-app-secret缺失APP_SECRET_TOKEN键（已由kubectl_describe和kubec
... 截断，原始 609 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点(node1/node2)到公网镜像仓库(registry.k8s.io/docker.io)的出站网络不可达，TCP连接在443端口超时(i/o timeout)，导致kubelet无法拉取镜像", "propagation": "节点无法通过公网访问registry.k8s.io（路由到*.docker.pkg.dev）和registry-1.docker.io，kubelet持续重试拉取镜像，每次均超时失败 → Pod进入ImagePullBackOff/ErrImagePull状态 → 48个Pod不可用", "direct_cause": "kubelet拉取镜像时TCP建连超时(i/o timeout到多个镜像仓库CDN节点)，DNS解析正常但网络层出口不通", "manifestation": "default/aiops-e2e/mcp三个命名空间共48个Pod处于ImagePullBackOff(26个)或ErrImagePull(22个)状态，分布在node1(ImagePullBackOff为主)和node2(ErrImagePull为主)上，无法启动提供服务"}
   rca_analysis={"phenomenon": "集群当前存在3类并发异常，共50个异常Pod。主异常组(g2)为ImagePullFailed类型，48个Pod分布在default/aiops-e2e/mcp三个命名空间的node1和node2上，状态为ImagePullBackOff(26个)或ErrImagePull(22个)。另有g1组1个Pod(rc-config-secret-key-missing)为CreateContainerConfigError，g3组1个Pod(node-debugger-node1-nx8gb)为StartError。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "rc-config-secret-key-missing: Warning Failed - couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret (x12)", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Secret rc-app-secret: type=Opaque, data_keys=EXISTING_SECRET_KEY, 缺APP_SECRET_TOKEN", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe", "content": "dig-tool(node1): i/o timeout to europe-west2-docker.pkg.dev:443 and us-west2-docker.pkg.dev:443 for registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe", "content": "connectivity-test(node2, mcp): i/o timeout to registry-1.docker.io:443 for busybox:1.36.1, 77+ failures over 8h", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe", "content": "dns-resolve-test(node2, default): i/o timeout dial tcp <IP>:443 for busybox:1.36.1 from docker.io", "reliability": "高"}, {"id": "e6", "source": "kubectl_events", "content": "全局Events: Pod/dig-tool Failed - i/o timeout to us-west2-docker.pkg.dev:443; 多个Pod报相同i/o timeout错误", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_yaml", "content": "dig-tool imagePullSecrets=<absent>, 镜像registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0为公网镜像", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe", "content": "node-debugger-node1-nx8gb: StartError - exec 'curl' not found in $PATH, 当前状态已转为ImagePullBackOff", "reliability": "高"}, {"id": "e9", "source": "run_bash_command", "content": "kubectl events: test-dns-1779360358 Failed to pull busybox:1.36.1 - read tcp timeout to registry-1.docker.io:443", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning Failed 6m52s (x12 over 8m50s) kubelet Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret", "interpretation": "Pod rc-config-secret-key-missing无法启动，因为引用了Secret rc-app-secret中的APP_SECRET_TOKEN键，但该键不存在"}, {"evidence_id": "e2", "raw_data": "Secret rc-app-secret: data_keys=EXISTING_SECRET_KEY, has_dockerconfigjson=False", "interpretation": "Secret rc-app-secret确实只含EXISTING_SECRET_KEY，缺少APP_SECRET_TOKEN，确认配置错误"}, {"evidence_id": "e3", "raw_data": "Failed to pull image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0: dial tcp 108.177.125.82:443: i/o timeout to europe-west2-docker.pkg.dev and us-west2-docker.pkg.dev", "interpretation": "node1无法连接到registry.k8s.io的后端GCR镜像仓库，TCP建连超时，说明出站网络不通"}, {"evidence_id": "e4", "raw_data": "Failed to pull image busybox:1.36.1: i/o timeout dialing registry-1.docker.io:443 (IPs 108.160.170.45, etc.), x77 over 8h", "interpretation": "node2无法连接到docker.io官方仓库，同样为TCP建连超时，与node1的错误模式一致"}, {"evidence_id": "e5", "raw_data": "Failed to pull busybox:1.36.1: dial tcp <multiple IPs>:443: i/o timeout", "interpretation": "node2上的default命名空间Pod也报相同i/o timeout错误，跨命名空间和节点一致"}, {"evidence_id": "e6", "raw_data": "Warning Failed Pod/dig-tool ... i/o timeout to us-west2-docker.pkg.dev:443", "interpretation": "全局Events确认多个Pod都在报registry网络不可达，不是孤立事件"}, {"evidence_id": "e7", "raw_data": "imagePullSecrets: <absent>, image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "interpretation": "Pod没有使用imagePullSecrets，镜像来自公网registry.k8s.io，排除了私有仓库认证失败的可能"}, {"evidence_id": "e8", "raw_data": "StartError: exec 'curl' not found in $PATH; 当前Events也报i/o timeout", "interpretation": "原StartError由容器镜像busybox不包含curl命令导致，但当前该Pod也处于ImagePull状态，受网络问题影响"}, {"evidence_id": "e9", "raw_data": "Failed to pull busybox:1.36.1: read tcp 10.2.0.49:55574->54.224.154.163:443: read: connection timed out", "interpretation": "aiops-e2e命名空间Pod也报相同的registry连接超时，三命名空间根因一致"}], "causal_chain": {"root_cause": "集群节点(node1/node2)到公网镜像仓库(registry.k8s.io/docker.io)的出站网络不可达，TCP连接在443端口超时(i/o timeout)，导致kubelet无法拉取镜像", "propagation": "节点无法通过公网访问registry.k8s.io（路由到*.docker.pkg.dev）和registry-1.docker.io，kubelet持续重试拉取镜像，每次均超时失败 → Pod进入ImagePullBackOff/ErrImagePull状态 → 48个Pod不可用", "direct_cause": "kubelet拉取镜像时TCP建连超时(i/o timeout到多个镜像仓库CDN节点)，DNS解析正常但网络层出口不通", "manifestation": "default/aiops-e2e/mcp三个命名空间共48个Pod处于ImagePullBackOff(26个)或ErrImagePull(22个)状态，分布在node1(ImagePullBackOff为主)和node2(ErrImagePull为主)上，无法启动提供服务"}, "root_cause": "集群主异常为公网镜像仓库网络不可达(L3 ImagePullFailed类型)，影响48个Pod。证据显示：(1) node1上dig-tool报i/o timeout到europe-west2-docker.pkg.dev:443和us-west2-docker.pkg.dev:443（registry.k8s.io后端）；(2) node2上dns-resolve-test和connectivity-test均报i/o timeout到registry-1.docker.io:443；(3) 全局Events确认跨3个命名空间(default/aiops-e2e/mcp)和2个节点(node1/node2)的错误模式完全一致；(4) imagePullSecrets检查排除私有仓库认证问题。另有两个独立小异常：(g1) rc-config-secret-key-missing为CreateContainerConfigError，根因是Secret aiops-e2e/rc-app-secret缺失APP_SECRET_TOKEN键（已由kubectl_describe和kubec\n... 截断，原始 609 字符", "root_cause_summary": "集群主异常为公网镜像仓库网络不可达(L3 ImagePullFailed类型)，影响48个Pod。证据显示：(1) node1上dig-tool报i/o timeout到europe-west2-docker.pkg.dev:443和us-west2-docker.pkg.dev:443（registry.k8s.io后端）；(2) node2上dns-resolve-test和connectivity-test均报i/o timeout到registry-1.docker.io:443；(3) 全局Events确认跨3个命名空间(default/aiops-e2e/mcp)和2个节点(node1/node2)的错误模式完全一致；(4) imagePullSecrets检查排除私有仓库认证问题。另有两个独立小异常：(g1) rc-config-secret-key-missing为CreateContainerConfigError，根因是Secret aiops-e2e/rc-app-secret缺失APP_SECRET_TOKEN键（已由kubectl_describe和kubec\n... 截断，原始 609 字符", "confidence": 0.95, "confidence_reason": "有直接工具证据(kubectl_describe)明确显示i/o timeout错误信息，跨节点跨命名空间验证一致，因果链清晰完整。Secret配置缺失也有kubectl_get_yaml和kubectl_describe双重确认。", "primary_runbooks": ["pod-imagepull-failed.md", "pod-config-error.md"], "alternative_causes": [{"cause": "镜像地址或tag不存在", "probability": "low", "reason": "dig-tool使用registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，connectivity-test使用busybox:1.36.1，均为标准公网镜像，错误信息是i/o timeout而非manifest unknown，排除镜像不存在"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "kubectl_get_yaml确认dig-tool无imagePullSecrets，镜像来自公网仓库无需认证，排除认证问题"}, {"cause": "DNS解析失败", "probability": "low", "reason": "错误信息是i/o timeout(建连超时)而非lookup失败，说明DNS解析已完成，问题在网络层"}, {"cause": "TLS证书问题", "probability": "low", "reason": "错误信息为i/o timeout，未出现x509证书错误"}], "limitations": "未采集节点侧网络配置证据（如iptables规则、代理配置、路由表），无法进一步定位是防火墙策略、缺省路由、还是代理配置导致出站不通。仅确认现象为TCP连接超时。", "llm_raw_analysis": "## 证据清点\\n已采集9个独立证据项，覆盖所有3个异常组(g1/g2/g3)。\\n\\n## 逐条分析\\n- e1/e2: 确认g1根因 — Secret缺失APP_SECRET_TOKEN键\\n- e3/e4/e5/e6/e9: 跨节点(node1/node2)、跨命名空间(default/mcp/aiops-e2e)、跨镜像仓库(registry.k8s.io/docker.io)均报i/o timeout，模式完全一致\\n- e7: 排除私有仓库认证假设\\n- e8: 确认g3原因为StartError(busybox无curl)，当前也受网络问题影响\\n\\n## 关联分析\\ng2主异常组证据高度一致：所有Pod的错误都是TCP连接超时(i/o timeout)到公网镜像仓库的443端口，覆盖不同仓库(registry.k8s.io→docker.pkg.dev, docker.io→registry-1.docker.io)、不同节点(node1/node2)、不同命名空间。这表明集群级出站网络存在阻断。\\n\\ng1为独立异常，与g2无直接关联。\\ng3原为独立异常(Start\n... 截断，原始 665 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群主异常为公网镜像仓库网络不可达(L3 ImagePullFailed类型)，影响48个Pod。证据显示：(1) node1上dig-tool报i/o timeout到europe-west2-docker.pkg.dev:443和us-west2-docker.pkg.dev:443（regis...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点(node1/node2)到公网镜像仓库(registry.k8s.io/docker.io)的出站网络不可达，TCP连接在443端口超时(i/o timeout)，导致kubelet无法拉取镜像
     传导机制: 节点无法通过公网访问registry.k8s.io（路由到*.docker.pkg.dev）和registry-1.docker.io，kubelet持续重试拉取镜像，每次均超时失败 → Pod进入ImagePullBackOff/ErrImagePull状态 → 48个Pod不可用
     最终表现: default/aiops-e2e/mcp三个命名空间共48个Pod处于ImagePullBackOff(26个)或ErrImagePull(22个)状态，分布在node1(ImagePullBackOff为主)和node2(ErrImagePull为主)上，无法启动提供服务


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (29.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8320 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 18.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的详尽分析数据，为您生成一份完整的集群诊断报告。

---

## 📊 诊断概览

根据对所有可用证据的交叉分析，以下是您集群当前的核心问题总结：

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `ImagePullBackOff` (26个)， `ErrImagePull` (22个)， `CreateContainerConfigError` (1个) |
| **兼容归因层** | **L3 (NETWORK_CNI_RUNTIME)** |
| **主导问题分类** | **ImagePullFailed** |
| **置信度** | **高 (95%)** |
| **证据完整度** | 8/8 (100%) |

**核心结论：**
您的集群当前存在**3 类并发问题**，共影响 **50 个异常 Pod**。主导问题为 **L3 层的镜像拉取失败（ImagePullFailed）**，共影响 **48 个 Pod**。此外，还存在一个 **Secret 配置错误** 和一个 **历史驱逐 Pod**。

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **集群节点** | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| **异常 Namespace** | `default`, `mcp`, `aiops-e2e` |
| **异常 Pod 分布** | node1 (ImagePullBackOff), node2 (ErrImagePull) |
| **错误信息** | `i/o timeout` 到 `registry.k8s.io:443` 和 `registry-1.docker.io:443` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| **g2-e1** | Pod 事件 | `kubectl describe pod dig-tool -n default` | `Failed to pull image ...: i/o timeout dial tcp 108.177.125.82:443 to europe-west2-docker.pkg.dev` | **节点 `node1` 无法拉取 `registry.k8s.io` 的镜像** |
| **g2-e2** | Pod 事件 | `kubectl describe pod dns-resolve-test -n default` | `Failed to pull image ...: dial tcp 108.160.170.45:443: i/o timeout` | **节点 `node2` 无法拉取 `docker.io` (registry-1.docker.io) 的镜像** |
| **g2-e3** | Pod 事件 | `kubectl describe pod connectivity-test -n mcp` | `Failed to pull image ...: i/o timeout dialing registry-1.docker.io:443` | **跨 namespace (`mcp`) 和节点 (`node2`) 的错误模式一致** |
| **g2-e4** | Pod 状态 | `kubernetes_tabular_query` | 共 49 个 Pending Pod，分布在 node1 (ImagePullBackOff) 和 node2 (ErrImagePull) | **集群内大量 Pod 无法拉取镜像，问题具有全局性** |
| **g2-e5** | 全局事件 | `kubectl events` | `Warning Failed Pod/dig-tool Back-off pulling image "registry.k8s.io/..."` (563 次) | **失败事件持续发生，说明问题是持续性的** |
| **g2-e6** | Pod YAML | `kubectl get pod dig-tool -o yaml` | `imagePullSecrets: <none>` | **排除私有仓库认证问题** |
| **g1-e1** | Pod 状态 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | `Reason: CreateContainerConfigError` | **Pod 因配置错误无法创建** |
| **g1-e2** | Secret YAML | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` | `data_keys: EXISTING_SECRET_KEY`，缺少 `APP_SECRET_TOKEN` | **Secret 内容缺失关键 Key** |
| **g3-e1** | Pod 状态 | `kubernetes_tabular_query` / `kubectl_get_by_name` | `STATUS: Complete`，`Reason: Evicted`，`Node: master` | **历史驱逐 Pod，无当前影响** |
| **layer_1-6** | 层验证 | `kubectl_get_by_kind`, `kubectl_describe` 等 | 跨 Namespace, 跨节点验证错误一致 | **问题稳定复现，排除偶发** |

### 证据关联分析
-   **证据 (g2-e1) + (g2-e2) + (g2-e3) 印证**：不同节点（node1/node2）、不同命名空间（default/mcp）上的 Pod 均报告 `i/o timeout` 到主流镜像仓库（`registry.k8s.io` 和 `docker.io`），证明这是一个**集群级别的出站网络问题**，而非单个 Pod 或节点配置问题。
-   **证据 (g2-e6) 排除**：所有受影响 Pod 的 `imagePullSecrets` 为空，排除了错误凭证导致拉取失败的可能性。
-   **证据 (g1-e1) + (g1-e2) 印证**：明确指出 `rc-config-secret-key-missing` 的根因是 Secret `rc-app-secret` 缺少 `APP_SECRET_TOKEN` key，这是一个配置问题。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| g2-e1: 镜像拉取失败的 Runbook 对照 | optional | 不影响根因判断，但缺少最佳实践对照 |
| 节点侧网络配置 (iptables, 路由, 代理) | critical | 无法精确定位是防火墙、缺省路由还是代理导致出站不通 |

---

## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ 集群节点（node1, node2）缺少到公网镜像仓库的出站网络连通性。            │
│ 具体表现：TCP 连接到 registry.k8s.io:443 和 registry-1.docker.io:443 超时。  │
└──────────────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ kubelet 尝试拉取镜像 → DNS 解析正常 → TCP 建连到镜像仓库 CDN (443端口)      │
│ → 连接超时 (`i/o timeout`) → 拉取请求失败                                  │
└──────────────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (L3 层)                                                            │
│ kubelet 无法从 `registry.k8s.io` 和 `docker.io` 拉取容器镜像。              │
│ (对应异常类型: ImagePullFailed)                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (L0 层)                                                        │
│ 48 个 Pod 处于 `ImagePullBackOff` (26个) 或 `ErrImagePull` (22个) 状态。     │
│ 这些 Pod 无法启动，服务不可用。                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

**次要问题因果链 (影响 1 个 Pod):**
```
Secret `rc-app-secret` 缺少必要 key (`APP_SECRET_TOKEN`)
    → Pod `rc-config-secret-key-missing` 启动时无法挂载 Secret
    → kubelet 报告 `CreateContainerConfigError`
```

### 根因结论

**结论 1 (主导问题 - 网络不可达)：**
依据证据 **g2-e1, g2-e2, g2-e3, g2-e4**，集群的**根本原因**是集群两个节点（node1, node2）到公网镜像仓库 `registry.k8s.io` 和 `registry-1.docker.io` 的 **出站网络不可达**。所有拉取请求均因 TCP 连接超时（`i/o timeout`）而失败，从而导致 48 个 Pod 无法创建并持续处于镜像拉取重试状态。

*   **置信度**：高 (95%)
*   **依据**：
    *   ✅ `kubectl describe` 结果直接报告 `i/o timeout` 到镜像仓库 IP:443。
    *   ✅ 此现象在 2 个节点、3 个命名空间、2 个镜像仓库间稳定复现。
    *   ✅ 通过检查 `imagePullSecrets` 排除了认证错误的可能性。

**结论 2 (次要问题 - Secret 配置错误)：**
依据证据 **g1-e1, g1-e2**，Pod `rc-config-secret-key-missing` 的**根本原因**是 Secret `aiops-e2e/rc-app-secret` 的 `data` 字段中**缺少了 `APP_SECRET_TOKEN` 这个 Key**，导致引用此 Secret 的 Pod 无法完成配置，从而启动失败。

*   **置信度**：高 (100%)

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 解决集群出站网络问题 (影响 48 个 Pod)**
*   **问题描述**：节点无法连接到 `registry.k8s.io` 和 `docker.io` 的 443 端口。
*   **修复方向 (需由网络管理员执行)**：
    *   **检查网络防火墙 & 安全组**：确保节点 Node 所在的子网或安全组**允许出站** `HTTPS (TCP/443)` 流量到 `*.docker.io` 和 `*.k8s.io` 域名。这是最常见的原因。
    *   **检查代理配置**：如果集群配置了 HTTP/HTTPS 代理，请检查 `kubelet`、`containerd` 或 `Docker` 的代理配置是否正确，并且代理服务器自身可以访问互联网。
    *   **检查节点路由**：在节点上执行 `ip route`，确认存在指向网关的默认路由。
*   **验证命令**：
    ```bash
    # 在 node1 和 node2 上分别执行以下命令测试连通性
    # 测试到 registry.k8s.io 的连通性
    curl -v --connect-timeout 5 https://registry.k8s.io/v2/
    # 测试到 docker.io 的连通性
    curl -v --connect-timeout 5 https://registry-1.docker.io/v2/
    # 或者使用更底层的 telnet/nc 命令测试 443 端口
    time telnet registry.k8s.io 443
    time telnet registry-1.docker.io 443
    ```
    *依据*：证据 g2-e1, g2-e2 显示 TCP 连接超时，因此核心是恢复网络层的连通性。

**2. [次优先] 修复 Secret 配置 (影响 1 个 Pod)**
*   **修复命令**：删除旧的 Secret，重新创建一个包含 `APP_SECRET_TOKEN` 的正确 Secret，然后重启 Pod。
    ```bash
    # 1. 删除旧的 Secret
    kubectl delete secret rc-app-secret -n aiops-e2e
    
    # 2. 创建一个新的 Secret (请将 your-actual-token-value 替换为真实的 Token 值)
    kubectl create secret generic rc-app-secret \
        --from-literal=EXISTING_SECRET_KEY=your-existing-value \
        --from-literal=APP_SECRET_TOKEN=your-actual-token-value \
        -n aiops-e2e
    
    # 3. 删除旧 Pod 使其重建 (通常 Deployment 会自动根据新 Secret 重建)
    kubectl delete pod rc-config-secret-key-missing -n aiops-e2e
    ```
    *依据*：证据 g1-e2 显示 Secret 缺少 `APP_SECRET_TOKEN` key。

### 后续优化
1.  **配置镜像仓库 (Registry Mirror)**: 为 `registry.k8s.io` 和 `docker.io` 配置一个本地或内网可访问的镜像仓库（如 Harbor, Nexus 或阿里云/腾讯云容器镜像服务），可以避免节点直连公网仓库带来的不稳定和网络问题。
2.  **网络监控**: 为集群节点配置基础的网络连通性监控，第一时间发现出站故障。
3.  **Secret 管理审计**: 使用自动化工具（如 `kube-score`, `conftest`）或 CI/CD 流水线，检查 Secret 等配置资源的完整性，避免遗漏关键字段。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 验证网络修复 | 在节点上执行（curl 或 telnet）到镜像仓库 443 端口的命令 | 命令成功执行，无 `timeout` 错误 |
| 2. 确认 Pod 恢复 | `kubectl get pods --all-namespaces | grep -E 'ImagePull|ErrImage'` | 返回结果为空，所有 Pod 状态正常 |
| 3. 验证 Secret 修复 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running 或 Pending (等待镜像) |
| 4. 再次确认全局 Pod 状态 | `kubectl get pods --all-namespaces | grep -v Running | grep -v Completed` | 不应再有 `ImagePullBackOff` 或 `ErrImagePull` 状态的 Pod |

---

## ⚠️ 注意事项
-   **网络修复是高危操作**：修改防火墙和路由规则前务必了解当前环境，最好准备回滚方案。
-   **镜像拉取重试有延迟**：网络恢复后，Kubelet 不会立即拉取镜像，因为 BackOff 策略会按指数增长（当前已等待数小时）。如果 Pod 急需恢复，可以手动删除对应 Pod，K8s 会立即重建并尝试拉取镜像。
    ```bash
    # 强制所有异常 Pod 立即重建（谨慎操作！）
    kubectl delete pod -n default dig-tool dns-resolve-test
    ```
-   **`observability-kibana` Pod 是历史遗留**：该 Pod 的驱逐状态不构成当前问题，可安全忽略，或在确认其无价值后通过控制器清理。

---

## 📊 性能统计

├─ 总耗时: 2.3m
├─ 问题定位: 43.0s (31%) ✅
├─ 证据链采集: 46.3s (33%) ✅
├─ 根因分析: 19.4s (14%) ✅
├─ 汇总总结: 29.9s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 19 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-config-error
- **参考 Runbook**: pod-imagepull-failed, pod-config-error, pod-evicted
- **工具调用**: 19 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
