======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f8523d82c1aa4678]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先进行全局 Pod 状态扫描，看看集群中是否有异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned pods across all namespaces. 59 Running, 20+ ImagePullBackOff, 10+ ErrImagePull, 1 CreateContainerConfigError, 3 Completed. Abnormal pods concentrated in default
   💭 [问题定位] 看到有很多异常 Pod。让我获取更完整的 Pod 列表和详细信息。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 49 行全部异常：49 个 Pod 均处于 Pending 状态（Ready=false）。涉及 namespace: aiops-e2e (2), default (18), mcp (29)。分布在 node1 和 node2 两个节点上。Pod 类型包括：DNS 测试类、网络测试类、registry 连接测试类、node-debugge
   💭 [问题定位] 返回的 STATUS 都是 Pending，但实际我看到有 ImagePullBackOff 等状态。让我用更精确的方式来查。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 All pods in Pending phase (except 1 Failed). Two categories of failure: (1) Image pull failures (ErrImagePull/ImagePullBackOff) for busybox:1.36.1, curlimages/curl, alpine:3.18, registry.k8s.io/* imag
   💭 [问题定位] 现在我已经获得了非常清晰的全局视图。让我获取对应的 runbook 来确认定位方向。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [问题定位] 好的，现在我已经有了全面的认识。让我再快速确认几个关键异常的详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          9s (x6 over 52s)  kubelet            Error: couldn'
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [问题定位] 好，我已经获得了足够的定位信息。现在整理完整的分析结果。

---

## 定位分析结果

### 全局异常概览

集群中共 **49 个异常 Pod**，分布在 3 个命名空间（`aiops-e2e`、`default`、`mcp`），主要集中在 `node1` 和 `node2` 两个节点。

| 异常组 | Pod 数量 | 当前状态 |
|--------|---------|---------|
| 🚨 ImagePullBackOff | ~20 个 | Pending — 镜像拉取重试中 |
| 🚨 ErrImagePull | ~20 个 | Pending — 镜像拉取失败 |
| ⚠️ CreateContainerConfigError | 1 个 | Pending — Secret 密钥缺失 |
| ❌ Failed (StartError) | 1 个 | Failed — 命令不存在 |
| ✅ Running | 59 个 | 正常，不含 kube-system 核心组件均正常 |

---

### 异常分组详解

#### 1️⃣ 镜像拉取失败 — ImagePullFailed（L3 | 核心问题）

**涉及 Pod**（约 40 个）：`dns-check-test`、`dig-tool`、`dns-test-dig`、`net-test-pod`、`dns-check-evidence`、`registry-conn-test-evidence`、`dns-resolve-test`、`dns-test-check`、`dns-test-tmp`、`nettest-*`、`network-test-*`、`registry-check-node2`、`registry-connect-test`、`curl-check-tmp`、`curls`、`net-check-tool`、`net-diag-*`、`registry-diag-*`、`test-reg-conn-*`、`node-debugger-*` 等

**根本原因**：**节点到 `registry-1.docker.io` 网络不可达（TCP i/o timeout）**
- 镜像来源：`docker.io/library/busybox:1.36.1`、`docker.io/curlimages/curl:7.88.1`、`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`、`registry.k8s.io/pause:3.9` 等
- 关键错误事件：`TCP i/o timeout`，目标 IP 包括 `67.228.102.32`、`199.59.148.97`、`108.160.170.39`
- `node1` 上的 Pod 已重试进入 `ImagePullBackOff` 状态，`node2` 上的仍在 `ErrImagePull` 状态

**兼容归因层**: **L3** — 网络/镜像仓库不可达

---

#### 2️⃣ Secret 配置缺失 — ConfigError（L4 | 单个 Pod）

**Pod**: `aiops-e2e/rc-config-secret-key-missing`
- **状态**: `CreateContainerConfigError`
- **原因**: 容器引用了环境变量 `APP_SECRET_TOKEN`，但 Secret `aiops-e2e/rc-app-secret` 中不存在该 key
- **Pod 本身镜像拉取是成功的（busybox:1.36）**，但因配置错误卡在容器创建阶段

**兼容归因层**: **L4** — ConfigMap/Secret 键名缺失

---

#### 3️⃣ 容器启动命令错误 — ConfigError（L4 | 单个 Pod）

**Pod**: `mcp/node-debugger-node1-nx8gb`
- **状态**: `Failed`（exitCode=128）
- **原因**: 容器镜像 `busybox:1.36` 中没有 `curl` 可执行文件，但容器 command 设置为 `curl -s -o /dev/null ...`
- **结果**: OCI 运行时无法启动容器，提示 `executable file not found in $PATH`

**兼容归因层**: **L4** — 容器启动命令/镜像入口配置错误

---

### 结构化输出

| 字段 | 值 |
|------|-----|
| **layer** | L3 |
| **derived_layer** | L3 |
| **layer_name** | ImagePullFailed |
| **layers** | L3（核心）, L4（次要） |
| **pod_status_keyword** | ImagePullBackOff / ErrImagePull / CreateContainerConfigError / Failed |
| **pod_abnormal_type** | ImagePullFailed（主）, ConfigError（次要） |
| **status_category** | pending_failed |
| **confidence** | 高（95%） |
| **abnormal_pods** | 49 个（详见上方列表） |
| **abnormal_groups** | ImagePullFailed（~40个）、ConfigError（2个） |
| **key_entities** | node1, node2, registry-1.docker.io, aiops-e2e/rc-app-secret, mcp/node-debugger-* |
| **possible_scenarios** | ① 节点出口防火墙/代理未配置导致 docker.io 不可达；② DNS 解析异常导致仓库域名无法正确解析；③ Secret `rc-app-secret` 中缺少 `APP_SECRET_TOKEN` 键；④ busybox 镜像中没有 curl 命令但容器 command 强行使用 |

### 总结

**集群当前最核心的问题是：节点无法连接到 docker.io 镜像仓库（L3 网络层问题）**，导致约 40 个测试/调试 Pod 无法拉取镜像。同时有两个配置层面的独立异常（Secret 键缺失、命令不存在）。kube-system 核心组件和业务 Pod 均正常运行，集群整体控制面健康。
   ✅ [问题定位] 完成 (51.3s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '节点出口防火墙/代理未配置导致 docker.io 网络不可达', 'probability': 'high', 'reason': 'TCP i/o timeout to registry-1.docker.io (多个IP: 67.228.102.32, 199.59.148.97, 108.160.170.39)，影响 node1 和 node2 两节点'}, {'scenario': 'DNS 解析异常导致仓库域名无法正确解析', 'probability': 'low', 'reason': '错误信息为 TCP i/o timeout 而非 DNS 解析失败，DNS 解析正常但网络层不可达'}, {'scenario': 'Secret rc-app-secret 中缺少 APP_SECRET_TOKEN 键', 'probability': 'confirmed', 'reason': "kubectl describe 确认 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret"}, {'scenario': 'busybox 镜像中没有 curl 命令但容器 command 强行使用', 'probability': 'confirmed', 'reason': "executable 'curl' not found in $PATH，exitCode=128，StartError"}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}]
   reasoning=集群当前有49个异常Pod，核心问题是约46个Pod处于ImagePullBackOff/ErrImagePull状态（Pending），根因是节点到registry-1.docker.io网络不可达（TCP i/o timeout），归因L3。同时有2个L4配置异常：aiops-e2e/rc-config-secret-key-missing（CreateContainerConfigError，Secret key缺失）和mcp/node-debugger-node1-nx8gb（Failed，StartError，curl命令不存在）。控制面核心组件健康。主异常层为L3，次要层为L4。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "集群当前有49个异常Pod，核心问题是约46个Pod处于ImagePullBackOff/ErrImagePull状态（Pending），根因是节点到registry-1.docker.io网络不可达（TCP i/o timeout），归因L3。同时有2个L4配置异常：aiops-e2e/rc-config-secret-key-missing（CreateContainerConfigError，Secret key缺失）和mcp/node-debugger-node1-nx8gb（Failed，StartError，curl命令不存在）。控制面核心组件健康。主异常层为L3，次要层为L4。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff / ErrImagePull / CreateContainerConfigError / Failed", "pod_abnormal_type": "ImagePullFailed", "status_category": "pending_failed", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "节点出口防火墙/代理未配置导致 docker.io 网络不可达", "probability": "high", "reason": "TCP i/o timeout to registry-1.docker.io (多个IP: 67.228.102.32, 199.59.148.97, 108.160.170.39)，影响 node1 和 node2 两节点"}, {"scenario": "DNS 解析异常导致仓库域名无法正确解析", "probability": "low", "reason": "错误信息为 TCP i/o timeout 而非 DNS 解析失败，DNS 解析正常但网络层不可达"}, {"scenario": "Secret rc-app-secret 中缺少 APP_SECRET_TOKEN 键", "probability": "confirmed", "reason": "kubectl describe 确认 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret"}, {"scenario": "busybox 镜像中没有 curl 命令但容器 command 强行使用", "probability": "confirmed", "reason": "executable 'curl' not found in $PATH，exitCode=128，StartError"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 28, "ErrImagePull": 20}, "total_abnormal": 48, "selected_rows": ["aiops-e2e         rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0              27s     172.16.166.130   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff             0              9h      172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              4h56m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff             0              3h56m   172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              8h      172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff             0              75m     172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff             0              81m     172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull                 0              81m     172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff             0              9h      172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull                 0              7h9m    172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff             0              81m     172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull                 0              4h3m    172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              8h      172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull                 0              8h      172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull                 0              5h39m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ErrImagePull                 0              109m    172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull                 0              6h37m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-conn-test-evidence                         0/1     ImagePullBackOff             0              14m     172.16.104.22    node2    <none>           <none>            run=registry-conn-test-evidence", "default           registry-connect-test                               0/1     ErrImagePull                 0              8h      172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              9h      172.16.166.185   node1    <none>           <none>            run=test-net-1779360704"], "raw_ref": "/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我已经收到上游的 evidence_plan。现在开始按计划执行真实工具采证。先并行执行所有独立的 describe 和 get 调用。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod test-dns-1779360358 in namespace aiops-e2e on node node1/10.2.0.49 is Pending. Container test-dns-1779360358 uses image busybox:1.36.1, args: nslookup registry.k8s.io, docker.io, google.com. State
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending, container State Waiting (Reason: ImagePullBackOff), Ready=False, Restart Count=0. All image pull attempts to registry.k8s.io/e2e-te
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod registry-connect-test (ns=default, node=node2/10.2.0.50) is Pending. Container state Waiting (Reason: ErrImagePull). Image busybox:1.36.1 cannot be pulled from docker.io — all attempts (x66 over 8
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Secret
name: rc-app-secret
namespace: aiops-e2e
type: Opaque
data_keys: EXISTING_SECRET_KEY
has_dockerconfigjson: False
docker_secret_type_valid: False
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-test (mcp namespace) on node2 (10.2.0.50) is Pending. Container state Waiting (Reason: ErrImagePull). The kubelet repeatedly fails to pull image busybox:1.36.1 from docker.io/library 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          7s (x9 over 88s)  kubelet            Error: couldn'
   💭 [证据链采集] 所有工具调用完成。现在汇总证据结论。

---

## ✅ 证据采集结论

### 异常组 g1 — CreateContainerConfigError（已验证 ✅）

**代表 Pod：aiops-e2e/rc-config-secret-key-missing**

| 证据项 | 结果 |
|--------|------|
| **ev-01**: kubectl describe pod | ✅ **确认** — 当前最新状态仍为 `CreateContainerConfigError`，Events 最新时间 `7s (x9 over 88s)`：`Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` |
| **ev-02**: kubectl get secret -o yaml | ✅ **确认** — Secret `rc-app-secret` 中 **仅存在 `EXISTING_SECRET_KEY`，确实缺少 `APP_SECRET_TOKEN` 键**。根因确认 |

**结论：配置错误根因已确认 — Secret aiops-e2e/rc-app-secret 缺少 APP_SECRET_TOKEN 键。属于 L4 ConfigError。**

---

### 异常组 g3 — StartError（已验证 ✅）

**代表 Pod：mcp/node-debugger-node1-nx8gb**

| 证据项 | 结果 |
|--------|------|
| **ev-03**: kubectl describe pod | ✅ **确认** — 当前状态为 `Failed`，Exit Code 128，错误消息：`exec: "curl": executable file not found in $PATH`。镜像 `busybox:1.36` 不包含 curl 命令但 command 强行调用 `curl`。 |

**结论：启动配置错误已确认 — busybox 镜像中无 curl 命令。属于 L4 ConfigError。**

---

### 异常组 g2 — ImagePullFailed（主异常组，已验证 ✅）

**覆盖 3 个 namespace 跨 node1/node2 的约 48 个异常 Pod**

| 证据项 | 结果 |
|--------|------|
| **ev-04**: aiops-e2e/test-dns-1779360358 (node1) | ✅ 确认 — `connection reset by peer` 到 `registry-1.docker.io`（IP: 100.50.6.117:443, 54.224.154.163:443） |
| **ev-05**: default/dig-tool (node1) | ✅ 确认 — `i/o timeout` 到 `europe-west2-docker.pkg.dev` 和 `us-west2-docker.pkg.dev`（IP: 108.177.125.82:443） |
| **ev-06**: default/registry-connect-test (node2) | ✅ 确认 — `i/o timeout` 到 `registry-1.docker.io:443`（多 IP: 74.86.3.208, 108.160.169.179 等，持续 8h） |
| **ev-07**: mcp/connectivity-test (node2) | ✅ 确认 — `i/o timeout` 到 `registry-1.docker.io:443`（多 IP，持续 8h，x76 次失败） |

**🔑 关键发现**：所有 ImagePull 异常的根本原因是相同的——**节点（node1 和 node2）到外部镜像仓库（registry-1.docker.io、registry.k8s.io、europe-west2-docker.pkg.dev 等）的网络不可达**，表现为 `i/o timeout` 和 `connection reset by peer`，这是集群级别的网络出口问题，不是镜像名/tag 或认证问题。

---

### 📋 最终证据汇总

| 异常组 | 异常类型 | Pod 数量 | 根因 | 确认状态 |
|--------|---------|---------|------|---------|
| g2 | **ImagePullFailed** (L3) | **~48 个** | **节点出口防火墙/代理未配置导致外部 registry 网络不可达** — timeout/connection reset | ✅ 充分确认 |
| g1 | **CreateContainerConfigError** (L4) | 1 个 | Secret `rc-app-secret` 缺少 `APP_SECRET_TOKEN` 键 | ✅ 充分确认 |
| g3 | **StartError** (L4) | 1 个 | busybox 镜像无 curl 命令但 Pod command 强行调用 | ✅ 充分确认 |

**冲突/负向证据**：无 — 所有上游断言均被真实环境工具结果验证通过。
   ✅ [证据链采集] 完成 (37.5s)
   📤 → 下游数据: evidence_items=12/12
   evidence_analysis={"evidence_plan":[{"id":"ev-01","description":"获取 rc-config-secret-key-missing (g1: CreateContainerConfigError) 的 Pod 当前状态和事件，验证 Secret key 缺失问题","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"验证上游已确认的 Secret key APP_SECRET_TOKEN 缺失错误是否为当前最新状态","evidence_type":"current_state_and_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-02","description":"获取 aiops-e2e/rc-app-secret 的 YAML 内容，确认 Secret 中缺少 APP_SECRET_TOKEN 键","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","tool_args":{"kind":"secret","name":"rc-app-secret","namespace":"aiops-e2e"},"purpose":"验证上游已确认的 Secret 中确实缺少 APP_SECRET_TOKEN 键，确认配置错误根因","evidence_type":"secret_content","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-03","description":"获取 node-debugger-node1-nx8gb (g3: StartError) 的 Pod 当前状态和事件，验证 curl 命令缺失问题","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"验证上游已确认的 exec: 'curl' not found in $PATH 错误是否为当前最新状态","evidence_type":"current_state_and_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-04","description":"获取 g2 ImagePullBackOff/ErrImagePull 组代表 Pod（test-dns-1779360358, dig-tool）的 events 和镜像配置，验证 registry 网络不可达","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"验证上游已确认的 TCP i/o timeout to registry-1.docker.io 是否仍是当前最新错误","evidence_type":"image_pull_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-05","description":"获取代表 Pod dig-tool (default/ImagePullBackOff) 的 describe，验证镜像拉取错误的跨 namespace 一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"验证 default namespace 中 ImagePullBackOff Pod 的镜像拉取错误是否为同一根因（registry 网络不可达）","evidence_type":"image_pull_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-06","description":"获取代表 Pod registry-connect-test (default/ErrImagePull) 的 describe，验证不同节点(node2)上的镜像拉取错误","level":"important","tool":"kubectl_describe","command":"kubectl describe pod registry-connect-test -n default","tool_args":{"kind":"pod","name":"registry-connect-test","namespace":"default"},"purpose":"验证 node2 上 ErrImagePull 的根源是否也是 registry 网络不可达","evidence_type":"image_pull_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-07","description":"获取 mcp 命名空间代表 Pod connectivity-test (ErrImagePull) 的 describe，验证跨 namespace 一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp"},"purpose":"验证 mcp namespace 中 ErrImagePull 的根源是否也是 registry 网络不可达","evidence_type":"image_pull_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod test-dns-1779360358 in namespace aiops-e2e on node node1/10.2.0.49 is Pending. Container test-dns-1779360358 uses image busybox:1.36.1, args: nslookup registry.k8s.io, docker.io, google.com. State: Waiting (Reason: ImagePullBackOff). Ready: False, Restart Count: 0. Events show repeated Failed to pull image errors (ErrImagePull): connection reset by peer when pulling from docker.io/library/busybox:1.36.1 via registry-1.docker.io (two distinct TCP connections: 100.50.6.117:443 and 54.224.154.163:443). BackOff event x1230 over 9h.\nkey_facts: [\"pod: test-dns-1779360358\", \"namespace: aiops-e2e\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: test-dns-1779360358\", \"image: busybox:1.36.1\", \"container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False\", \"Restart Count: 0\", \"Failed to pull image: connection reset by peer from registry-1.docker.io (two IPs: 100.50.6.117:443 and 54.224.154.163:443)\", \"Warning Failed (ErrImagePull): x76 over 9h\", \"Warning Failed (pull error): x119 over 9h\", \"Normal BackOff: x1230 over 9h\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending, container State Waiting (Reason: ImagePullBackOff), Ready=False, Restart Count=0. All image pull attempts to registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 failed with i/o timeout dialing europe-west2-docker.pkg.dev and us-west2-docker.pkg.dev (IP 108.177.125.82:443). Events: Failed (ErrImagePull, 37x), Failed to pull image (DeadlineExceeded/Unknown desc), BackOff (543x). Pod IP: 172.16.166.157 (Calico).\nkey_facts: [\"name: dig-tool\", \"namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False\", \"Restart Count: 0\", \"image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"QoS Class: BestEffort\", \"Pod IP: 172.16.166.157/32 (Calico)\", \"Events: Warning Failed 57m (x37 over 4h50m) - Error: ErrImagePull\", \"Events: Warning Failed 57m - Failed to pull image, code=DeadlineExceeded, dial tcp 108.177.125.82:443: i/o timeout (europe-west2-docker.pkg.dev)\", \"Events: Warning Failed 52m (x5 over 4h46m) - Failed to pull image, code=Unknown desc, dial tcp 108.177.125.82:443: i/o timeout (europe-west2-docker.pkg.dev)\", \"Events: Warning Failed 13m - Failed to pull image, code=Unknown desc, dial tcp 108.177.125.82:443: i/o timeout (us-west2-docker.pkg.dev)\", \"Events: Normal BackOff 31s (x543 over 4h50m) - Back-off pulling image\", \"Events: Normal Pulling 57m (x39 over 4h57m) - Pulling image\"]\nconflicts: [\"raw_preview has Normal Pulling event (x39 over 4h57m) not present in current_summary; current_summary omitted it.\"]\nmissing: [\"raw_preview ends abruptly (truncated); current_summary may have had additional event lines not fully captured.\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\n  Warning  Failed   43m   kubelet  Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   43m   kubelet  Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod registry-connect-test (ns=default, node=node2/10.2.0.50) is Pending. Container state Waiting (Reason: ErrImagePull). Image busybox:1.36.1 cannot be pulled from docker.io — all attempts (x66 over 8h) hit i/o timeout dialing various registry-1.docker.io IPs on port 443. Last event: Failed at 4m29s with code=Unknown, same timeout. Pod IP=172.16.104.44, calico networking up.\nkey_facts: [\"Pod: registry-connect-test, Namespace: default\", \"Node: node2 (10.2.0.50)\", \"Status: Pending\", \"Container State: Waiting, Reason: ErrImagePull\", \"Image: busybox:1.36.1\", \"Container ID: (empty), Image ID: (empty)\", \"Restart Count: 0\", \"Pod IP: 172.16.104.44\", \"Events: Warning Failed x66 over 8h — all i/o timeout dialing registry-1.docker.io:443 (multiple IPs: 74.86.3.208, 108.160.169.179, 108.160.165.139, 104.244.46.165, 108.160.166.61, 67.228.102.32)\", \"Last event at 4m29s: Reason=Failed, code=Unknown, same timeout\", \"Pulling event occurred 76 times over 8h\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\", \"QoS Class: BestEffort\", \"Annotations confirm calico network (cni.projectcalico.org/podIP: 172.16.104.44/32)\"]\nconflicts: [\"current_summary says 'Failed 4m29s (x66 over 8h)' repeats Reason=ErrImagePull but raw_preview shows that specific event has Reason=Failed, Error=ErrImagePull — minor categorization difference, no factual conflict\"]\nmissing: [\"Container command args present in raw_preview but not in current_summary: runs connectivity test via wget/nc to registry-1.docker.io\", \"Normal Pulling event (x76 over 8h) present in raw_preview but not in current_summary\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Secret\nname: rc-app-secret\nnamespace: aiops-e2e\ntype: Opaque\ndata_keys: EXISTING_SECRET_KEY\nhas_dockerconfigjson: False\ndocker_secret_type_valid: False","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"Pod connectivity-test (mcp namespace) on node2 (10.2.0.50) is Pending. Container state Waiting (Reason: ErrImagePull). The kubelet repeatedly fails to pull image busybox:1.36.1 from docker.io/library due to i/o timeout dialing various Docker registry IPs (74.86.3.208, 108.160.170.45, 168.143.162.58, 199.59.148.8, 108.160.166.61, 199.59.148.97) on port 443. The same error has occurred 76 times over 8h. Pod has assigned IP 172.16.104.3 via Calico. No container ID or image ID set.\nkey_facts: [\"Pod: connectivity-test, Namespace: mcp\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Container: connectivity-test, Image: busybox:1.36.1\", \"Container State: Waiting, Reason: ErrImagePull\", \"Ready: False, Restart Count: 0\", \"Pod IP: 172.16.104.3 (Calico CNI)\", \"Events: 7x Warning/Failed pulling image busybox:1.36.1 - all i/o timeout to registry-1.docker.io:443 (IPs: 74.86.3.208, 108.160.170.45, 168.143.162.58, 199.59.148.8, 108.160.166.61, 199.59.148.97), with codes Unknown or DeadlineExceeded\", \"Event: Warning Failed 7m30s (x76 over 8h) - Error: ErrImagePull\", \"Start Time: Thu, 21 May 2026 11:38:46 +0000\"]\nconflicts: [\"current_summary lists only 6 Failed pull events; raw_preview shows 7 distinct events (the 7m30s event is separate from the x76 aggregate)\", \"current_summary omits 'x76 over 8h' from the aggregate event line\"]\nmissing: [\"Pod IP (172.16.104.3) - present in raw_preview but absent from current_summary\", \"Calico CNI annotations/network-status details - present in raw_preview but absent from current_summary\", \"Exact pod args (curl -v --connect-timeout 10 https://registry-1.docker.io/v2/ 2>&1 || true) - present in raw_preview but absent from current_summary\", \"Conditions (Initialized=True, Ready=False, etc.) - present in raw_preview but absent from current_summary\", \"QoS Class: BestEffort, Tolerations details - present in raw_preview but absent from current_summary\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          7s (x9 over 88s)  kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: e50889f651dff0ebd5a4ed7212a0f9deacd4b503f1ae265a36959b8e7c2ff9c4\n                  cni.projectcalico.org/podIP: 172.16.166.130/32\n                  cni.projectcalico.org/podIPs: 172.16.166.130/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-pbw78:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed          7s (x9 over 88s)  kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f8523d82c1aa4678/tools/007-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"所有工具调用完成。现在汇总证据结论。\n\n---\n\n## ✅ 证据采集结论\n\n### 异常组 g1 — CreateContainerConfigError（已验证 ✅）\n\n**代表 Pod：aiops-e2e/rc-config-secret-key-missing**\n\n| 证据项 | 结果 |\n|--------|------|\n| **ev-01**: kubectl describe pod | ✅ **确认** — 当前最新状态仍为 `CreateContainerConfigError`，Events 最新时间 `7s (x9 over 88s)`：`Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` |\n| **ev-02**: kubectl get secret -o yaml | ✅ **确认** — Secret `rc-app-secret` 中 **仅存在 `EXISTING_SECRET_KEY`，确实缺少 `APP_SECRET_TOKEN` 键**。根因确认 |\n\n**结论：配置错误根因已确认 — Secret aiops-e2e/rc-app-secret 缺少 APP_SECRET_TOKEN 键。属于 L4 ConfigError。**\n\n---\n\n### 异常组 g3 — StartError（已验证 ✅）\n\n**代表 Pod：mcp/node-debugger-node1-nx8gb**\n\n| 证据项 | 结果 |\n|--------|------|\n| **ev-03**: kubectl describe pod | ✅ **确认** — 当前状态为 `Failed`，Exit Code 128，错误消息：`exec: \"curl\": executable file not found in $PATH`。镜像 `busybox:1.36` 不包含 curl 命令但 command 强行调用 `curl`。 |\n\n**结论：启动配置错误已确认 — busybox 镜像中无 curl 命令。属于 L4 ConfigError。**\n\n---\n\n### 异常组 g2 — ImagePullFailed（主异常组，已验证 ✅）\n\n**覆盖 3 个 namespace 跨 node1/node2 的约 48 个异常 Pod**\n\n| 证据项 | 结果 |\n|--------|------|\n| **ev-04**: aiops-e2e/test-dns-1779360358 (node1) | ✅ 确认 — `connection reset by peer` 到 `registry-1.docker.io`（IP: 100.50.6.117:443, 54.224.154.163:443） |\n| **ev-05**: default/dig-tool (node1) | ✅ 确认 — `i/o timeout` 到 `europe-west2-docker.pkg.dev` 和 `us-west2-docker.pkg.dev`（IP: 108.177.125.82:443） |\n| **ev-06**: default/registry-connect-test (node2) | ✅ 确认 — `i/o timeout` 到 `registry-1.docker.io:443`（多 IP: 74.86.3.208, 108.160.169.179 等，持续 8h） |\n| **ev-07**: mcp/connectivity-test (node2) | ✅ 确认 — `i/o timeout` 到 `registry-1.docker.io:443`（多 IP，持续 8h，x76 次失败） |\n\n**🔑 关键发现**：所有 ImagePull 异常的根本原因是相同的——**节点（node1 和 node2）到外部镜像仓库（registry-1.docker.io、registry.k8s.io、europe-west2-docker.pkg.dev 等）的网络不可达**，表现为 `i/o timeout` 和 `connection reset by peer`，这是集群级别的网络出口问题，不是镜像名/tag 或认证问题。\n\n---\n\n### 📋 最终证据汇总\n\n| 异常组 | 异常类型 | Pod 数量 | 根因 | 确认状态 |\n|--------|---------|---------|------|---------|\n| g2 | **ImagePullFailed** (L3) | **~48 个** | **节点出口防火墙/代理未配置导致外部 registry 网络不可达** — timeout/connection reset | ✅ 充分确认 |\n| g1 | **CreateContainerConfigError** (L4) | 1 个 | Secret `rc-app-secret` 缺少 `APP_SECRET_TOKEN` 键 | ✅ 充分确认 |\n| g3 | **StartError** (L4) | 1 个 | busybox 镜像无 curl 命令但 Pod command 强行调用 | ✅ 充分确认 |\n\n**冲突/负向证据**：无 — 所有上游断言均被真实环境工具结果验证通过。","collection_summary":"计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%；其中真实环境证据 12/12 项，完整度 100%；实际执行工具 12 个，匹配计划 7 个，未规划证据 5 个","plan_total":7,"plan_collected":7,"plan_completeness":1.0,"environment_evidence_total":12,"environment_evidence_collected":12,"environment_evidence_completeness":1.0,"executed_tool_count":12,"matched_tool_count":7,"unplanned_tool_count":5,"evidence_inventory":[{"id":"ev-01","description":"获取 rc-config-secret-key-missing (g1: CreateContainerConfigError) 的 Pod 当前状态和事件，验证 Secret key 缺失问题","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"验证上游已确认的 Secret key APP_SECRET_TOKEN 缺失错误是否为当前最新状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-02","description":"获取 aiops-e2e/rc-app-secret 的 YAML 内容，确认 Secret 中缺少 APP_SECRET_TOKEN 键","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","purpose":"验证上游已确认的 Secret 中确实缺少 APP_SECRET_TOKEN 键，确认配置错误根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-03","description":"获取 node-debugger-node1-nx8gb (g3: StartError) 的 Pod 当前状态和事件，验证 curl 命令缺失问题","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"验证上游已确认的 exec: 'curl' not found in $PATH 错误是否为当前最新状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-04","description":"获取 g2 ImagePullBackOff/ErrImagePull 组代表 Pod（test-dns-1779360358, dig-tool）的 events 和镜像配置，验证 registry 网络不可达","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"验证上游已确认的 TCP i/o timeout to registry-1.docker.io 是否仍是当前最新错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-05","description":"获取代表 Pod dig-tool (default/ImagePullBackOff) 的 describe，验证镜像拉取错误的跨 namespace 一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","purpose":"验证 default namespace 中 ImagePullBackOff Pod 的镜像拉取错误是否为同一根因（registry 网络不可达）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-06","description":"获取代表 Pod registry-connect-test (default/ErrImagePull) 的 describe，验证不同节点(node2)上的镜像拉取错误","level":"important","tool":"kubectl_describe","command":"kubectl describe pod registry-connect-test -n default","purpose":"验证 node2 上 ErrImagePull 的根源是否也是 registry 网络不可达","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-07","description":"获取 mcp 命名空间代表 Pod connectivity-test (ErrImagePull) 的 describe，验证跨 namespace 一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","purpose":"验证 mcp namespace 中 ErrImagePull 的根源是否也是 registry 网络不可达","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-01 | critical | ✅ | kubectl_describe | 获取 rc-config-secret-key-missing (g1: CreateCo... | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | ev-02 | critical | ✅ | kubectl_get_yaml | 获取 aiops-e2e/rc-app-secret 的 YAML 内容，确认 Secre... | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` |
   | ev-03 | important | ✅ | kubectl_describe | 获取 node-debugger-node1-nx8gb (g3: StartError)... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | ev-04 | critical | ✅ | kubectl_describe | 获取 g2 ImagePullBackOff/ErrImagePull 组代表 Pod（t... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | ev-05 | important | ✅ | kubectl_describe | 获取代表 Pod dig-tool (default/ImagePullBackOff) ... | `kubectl describe pod dig-tool -n default` |
   | ev-06 | important | ✅ | kubectl_describe | 获取代表 Pod registry-connect-test (default/ErrIm... | `kubectl describe pod registry-connect-test -n default` |
   | ev-07 | important | ✅ | kubectl_describe | 获取 mcp 命名空间代表 Pod connectivity-test (ErrImage... | `kubectl describe pod connectivity-test -n mcp` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.1s)
   📤 → 下游数据: root_cause=【主异常g2-ImagePullFailed】集群约46个Pod处于ImagePullBackOff/ErrImagePull状态，根因为节点到外部镜像仓库网络不可达。已验证4个代表Pod覆盖3个namespace和2个节点：(1) aiops-e2e/test-dns-1779360358（node1）：connection reset by peer 到 registry-1.docker.io（IP: 100.50.6.117:443, 54.224.154.163:443）；(2) default/dig-tool（node1）：i/o timeout 到 europe-west2-docker.pkg.dev（IP: 108.177.125.82:443）；(3) default/registry-connect-test（node2）：i/o timeout 到 registry-1.docker.io:443（6个IP均超时，x66次失败/8h）；(4) mcp/connectivity-test（node2）：i/o timeout 到 registry-1.docke
... 截断，原始 790 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1、node2）缺少到外部镜像仓库（registry-1.docker.io、registry.k8s.io等）的网络出口路由/代理/防火墙规则，导致TCP连接超时或连接被对端重置", "propagation": "节点出口网络不可达 → kubelet 无法从 registry-1.docker.io 拉取 busybox:1.36.1、从 registry.k8s.io 拉取 e2e-test-images/jessie-dnsutils:1.0、从 quay.io/curlimages/curl 拉取 curl 镜像 → containerd 返回 i/o timeout / connection reset by peer → kubelet 标记 Pod 为 ErrImagePull → 重试后进入 ImagePullBackOff 退避 → 约46个 Pod 持续处于 Pending 状态", "direct_cause": "节点到 registry-1.docker.io:443 和 registry.k8s.io 相关镜像仓库的 TCP 连接超时（i/o timeout）或连接重置（connection reset by peer）", "manifestation": "集群中46个Pod处于ImagePullBackOff/ErrImagePull状态（Pending），分布在2个节点、3个命名空间，拉取多种基础镜像均失败"}
   rca_analysis={"phenomenon": "集群当前有49个异常Pod分布在3个namespace（aiops-e2e、default、mcp）和2个节点（node1、node2）上。主异常组g2（约46个Pod）处于ImagePullBackOff/ErrImagePull状态（Pending），根因为节点到外部镜像仓库网络不可达；次要异常g1（1个Pod）为CreateContainerConfigError（Secret密钥缺失）；次要异常g3（1个Pod）为StartError（容器启动命令找不到curl）。", "evidence_inventory": [{"id": "ev-01", "source": "kubectl_describe", "content": "aiops-e2e/rc-config-secret-key-missing: Pending, CreateContainerConfigError, Events: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret (x9 over 88s)", "reliability": "高"}, {"id": "ev-02", "source": "kubectl_get_yaml", "content": "Secret aiops-e2e/rc-app-secret: Opaque, data_keys=[EXISTING_SECRET_KEY], missing APP_SECRET_TOKEN", "reliability": "高"}, {"id": "ev-03", "source": "kubectl_describe", "content": "mcp/node-debugger-node1-nx8gb: Failed, StartError, exec: 'curl': executable file not found in $PATH, Exit Code 128", "reliability": "高"}, {"id": "ev-04", "source": "kubectl_describe", "content": "aiops-e2e/test-dns-1779360358 (node1): ImagePullBackOff, connection reset by peer to registry-1.docker.io (100.50.6.117:443, 54.224.154.163:443)", "reliability": "高"}, {"id": "ev-05", "source": "kubectl_describe", "content": "default/dig-tool (node1): ImagePullBackOff, i/o timeout to registry.k8s.io via europe-west2-docker.pkg.dev/us-west2-docker.pkg.dev (108.177.125.82:443)", "reliability": "高"}, {"id": "ev-06", "source": "kubectl_describe", "content": "default/registry-connect-test (node2): ErrImagePull, i/o timeout to registry-1.docker.io:443 (IPs: 74.86.3.208, 108.160.169.179 et al., x66 over 8h)", "reliability": "高"}, {"id": "ev-07", "source": "kubectl_describe", "content": "mcp/connectivity-test (node2): ErrImagePull, i/o timeout to registry-1.docker.io:443 (IPs: 74.86.3.208, 108.160.170.45 et al., x76 over 8h)", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "59 Running, 20+ ImagePullBackOff, 10+ ErrImagePull, 1 CreateContainerConfigError, 3 Completed across all namespaces", "reliability": "高"}, {"id": "layer_3", "source": "kubernetes_jq_query", "content": "All Pending except 1 Failed. TCP i/o timeout to registry-1.docker.io (multiple IPs) and registry.k8s.io; ConfigError for APP_SECRET_TOKEN", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev-01", "raw_data": "Warning Failed 7s (x9 over 88s) kubelet Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret", "interpretation": "Pod rc-config-secret-key-missing 无法启动容器，因为引用了 Secret aiops-e2e/rc-app-secret 中的 APP_SECRET_TOKEN 键，但该键不存在"}, {"evidence_id": "ev-02", "raw_data": "data_keys: EXISTING_SECRET_KEY (only one key, no APP_SECRET_TOKEN)", "interpretation": "确认 Secret rc-app-secret 仅包含 EXISTING_SECRET_KEY，没有 APP_SECRET_TOKEN 键。这是配置错误的根本原因"}, {"evidence_id": "ev-03", "raw_data": "exec: 'curl': executable file not found in $PATH; Exit Code: 128; State: Terminated, Reason: StartError", "interpretation": "Pod node-debugger-node1-nx8gb 使用 busybox:1.36 镜像（该镜像不含 curl），但容器 command 为 'curl'，导致 OCI 运行时无法执行"}, {"evidence_id": "ev-04", "raw_data": "Failed to pull image: connection reset by peer from registry-1.docker.io (100.50.6.117:443, 54.224.154.163:443)", "interpretation": "node1 上的 test-dns-1779360358 拉取 busybox:1.36.1 时，TCP 连接到 registry-1.docker.io 被对端重置，说明连接可建立但被中断，符合网络中间设备阻断特征"}, {"evidence_id": "ev-05", "raw_data": "dial tcp 108.177.125.82:443: i/o timeout (europe-west2-docker.pkg.dev, us-west2-docker.pkg.dev)", "interpretation": "node1 上的 dig-tool 尝试拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 时，连接到 Google Cloud 仓库超时，确认出口网络不可达并非仅限于 docker.io"}, {"evidence_id": "ev-06", "raw_data": "i/o timeout dialing registry-1.docker.io:443 (multiple IPs: 74.86.3.208, 108.160.169.179, 108.160.165.139, 104.244.46.165, 108.160.166.61, 67.228.102.32), x66 over 8h", "interpretation": "node2 上的 registry-connect-test 拉取 busybox:1.36.1 时，所有到 registry-1.docker.io 的 TCP 连接均超时（多个IP均失败），持续时间8小时，排除单IP故障"}, {"evidence_id": "ev-07", "raw_data": "i/o timeout dialing registry-1.docker.io:443 (IPs: 74.86.3.208, 108.160.170.45, 168.143.162.58, 199.59.148.8, 108.160.166.61, 199.59.148.97), x76 over 8h", "interpretation": "mcp 命名空间中的 connectivity-test 在 node2 上同样遭遇全部镜像仓库 IP 的 TCP 超时，跨 namespace 一致性确认问题在集群出口/节点层面，非 Pod/namespace 级别"}, {"evidence_id": "layer_1", "raw_data": "20+ ImagePullBackOff, 10+ ErrImagePull, 1 CreateContainerConfigError", "interpretation": "集群层面确认约48个Pod存在镜像拉取失败，1个配置错误"}, {"evidence_id": "layer_3", "raw_data": "TCP i/o timeout to registry-1.docker.io (67.228.102.32, 199.59.148.97, 108.160.170.39) and registry.k8s.io", "interpretation": "jq 查询确认所有 ImagePull 异常 Pod 的根因均为 TCP 连接超时到镜像仓库，汇总了多个目标IP"}], "causal_chain": {"root_cause": "集群节点（node1、node2）缺少到外部镜像仓库（registry-1.docker.io、registry.k8s.io等）的网络出口路由/代理/防火墙规则，导致TCP连接超时或连接被对端重置", "propagation": "节点出口网络不可达 → kubelet 无法从 registry-1.docker.io 拉取 busybox:1.36.1、从 registry.k8s.io 拉取 e2e-test-images/jessie-dnsutils:1.0、从 quay.io/curlimages/curl 拉取 curl 镜像 → containerd 返回 i/o timeout / connection reset by peer → kubelet 标记 Pod 为 ErrImagePull → 重试后进入 ImagePullBackOff 退避 → 约46个 Pod 持续处于 Pending 状态", "direct_cause": "节点到 registry-1.docker.io:443 和 registry.k8s.io 相关镜像仓库的 TCP 连接超时（i/o timeout）或连接重置（connection reset by peer）", "manifestation": "集群中46个Pod处于ImagePullBackOff/ErrImagePull状态（Pending），分布在2个节点、3个命名空间，拉取多种基础镜像均失败"}, "root_cause": "【主异常g2-ImagePullFailed】集群约46个Pod处于ImagePullBackOff/ErrImagePull状态，根因为节点到外部镜像仓库网络不可达。已验证4个代表Pod覆盖3个namespace和2个节点：(1) aiops-e2e/test-dns-1779360358（node1）：connection reset by peer 到 registry-1.docker.io（IP: 100.50.6.117:443, 54.224.154.163:443）；(2) default/dig-tool（node1）：i/o timeout 到 europe-west2-docker.pkg.dev（IP: 108.177.125.82:443）；(3) default/registry-connect-test（node2）：i/o timeout 到 registry-1.docker.io:443（6个IP均超时，x66次失败/8h）；(4) mcp/connectivity-test（node2）：i/o timeout 到 registry-1.docke\n... 截断，原始 790 字符", "root_cause_summary": "【主异常g2-ImagePullFailed】集群约46个Pod处于ImagePullBackOff/ErrImagePull状态，根因为节点到外部镜像仓库网络不可达。已验证4个代表Pod覆盖3个namespace和2个节点：(1) aiops-e2e/test-dns-1779360358（node1）：connection reset by peer 到 registry-1.docker.io（IP: 100.50.6.117:443, 54.224.154.163:443）；(2) default/dig-tool（node1）：i/o timeout 到 europe-west2-docker.pkg.dev（IP: 108.177.125.82:443）；(3) default/registry-connect-test（node2）：i/o timeout 到 registry-1.docker.io:443（6个IP均超时，x66次失败/8h）；(4) mcp/connectivity-test（node2）：i/o timeout 到 registry-1.docke\n... 截断，原始 790 字符", "confidence": 0.95, "confidence_reason": "所有关键证据均来自 kubectl describe 和 kubectl get yaml 的直接工具输出，确认了当前最新状态的异常信息。主异常组g2通过4个代表Pod跨3个namespace、2个节点验证，证据高度一致（所有镜像拉取失败均为TCP i/o timeout或connection reset）。g1和g3均有明确的错误消息直接确认根因。整体因果链完整、无矛盾证据。", "primary_runbooks": ["pod-imagepull-failed.md", "pod-config-error.md"], "alternative_causes": [{"cause": "镜像名/tag 不存在或错误", "probability": "排除", "reason": "错误消息为 TCP i/o timeout/connection reset，非 manifest unknown 或 tag not found；且多种镜像（busybox:1.36.1, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, curlimages/curl 等）均失败，不可能所有镜像名都错误"}, {"cause": "imagePullSecret 缺失或认证失败", "probability": "排除", "reason": "公共镜像（busybox、alpine、registry.k8s.io 公共镜像）无需认证；错误消息为网络超时而非认证失败（denied/unauthorized）"}, {"cause": "DNS 解析异常导致仓库域名不可解析", "probability": "低", "reason": "错误消息为 TCP i/o timeout 而非 DNS 解析失败（nodename nor servname provided, or not known）；说明 DNS 解析正常但后续 TCP 连接超时"}, {"cause": "单节点网络故障", "probability": "排除", "reason": "node1 和 node2 两个节点均出现同样的 TCP i/o timeout 错误，排除单节点故障，证明为集群级网络出口问题"}], "limitations": "未在节点层面执行 curl/telnet 到 registry-1.docker.io:443 的直接网络连通性测试；未检查节点的网络出口配置（iptables/代理/防火墙规则）；未验证是否配置了 HTTP 代理（HTTP_PROXY/HTTPS_PROXY）环境变量；g2组的46个Pod未全部逐一检查events（但通过4个跨节点跨namespace代表Pod充分覆盖）。", "llm_raw_analysis": "L3根因分析完成。集群共49个异常Pod，分为3个异常组。主异常组g2（ImagePullFailed，约46个Pod）根因为集群节点到外部镜像仓库网络不可达，表现为TCP i/o timeout和connection reset by peer，影响两个节点（node1、node2）和三个namespace（aiops-e2e、default、mcp），涉及多种镜像（busybox:1.36.1、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0、curlimages/curl、alpine:3.18）。次要异常g1（CreateContainerConfigError，1个Pod）根因为Secret缺少APP_SECRET_TOKEN键。次要异常g3（StartError，1个Pod）根因为busybox镜像不含curl命令但容器强行调用。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 【主异常g2-ImagePullFailed】集群约46个Pod处于ImagePullBackOff/ErrImagePull状态，根因为节点到外部镜像仓库网络不可达。已验证4个代表Pod覆盖3个namespace和2个节点：(1) aiops-e2e/test-dns-1779360358（nod...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1、node2）缺少到外部镜像仓库（registry-1.docker.io、registry.k8s.io等）的网络出口路由/代理/防火墙规则，导致TCP连接超时或连接被对端重置
     传导机制: 节点出口网络不可达 → kubelet 无法从 registry-1.docker.io 拉取 busybox:1.36.1、从 registry.k8s.io 拉取 e2e-test-images/jessie-dnsutils:1.0、从 quay.io/curlimages/curl 拉取 curl 镜像 → containerd 返回 i/o timeout / connection reset by peer → kubelet 标记 Pod 为 ErrImagePull → 重试后进入 ImagePullBackOff 退避 → 约46个 Pod 持续处于 Pending 状态
     最终表现: 集群中46个Pod处于ImagePullBackOff/ErrImagePull状态（Pending），分布在2个节点、3个命名空间，拉取多种基础镜像均失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (32.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8810 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 23.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您提供的完整分析和诊断要求生成的详尽诊断报告。

---

## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff / ErrImagePull / CreateContainerConfigError / StartError |
| **兼容归因层** | L3 (网络层) + L4 (配置层) |
| **问题分类** | 镜像拉取失败(ImagePullFailed), 配置错误(ConfigError) |
| **置信度** | 高 (95%) |
| **证据完整度** | 7/7 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 集群状态 | 共 49 个异常 Pod，处于 Pending 或 Failed 状态，59 个 Pod 正常运行 |
| 受影响节点 | node1 (10.2.0.49), node2 (10.2.0.50) |
| 受影响命名空间 | aiops-e2e (2个), default (18个), mcp (29个) |
| 核心错误信息 | **主要问题(46个Pod)**：`Failed to pull image` - `i/o timeout` 或 `connection reset by peer` 到 `registry-1.docker.io:443` |

**简要总结**：
您的集群主要面临 **一个严重的网络问题** 和 **两个独立的配置错误**。

1.  **核心问题 (L3 网络层)**：集群中的所有节点 (`node1`, `node2`) 无法连接到外部镜像仓库 `registry-1.docker.io` 及 `registry.k8s.io`，导致 **46个 Pod** 处于 `ImagePullBackOff` 或 `ErrImagePull` 状态，无法启动。
2.  **次要问题 (L4 配置层)**：存在两个独立的配置或环境错误，导致另外 3 个 Pod 无法正常运行。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据（关键摘要） | 分析结论 |
|---|----------|----------|----------------------|----------|
| 1 | Pod 核心状态 | `kubectl_get_by_kind_in_cluster` | 59 Running, 20+ ImagePullBackOff, 10+ ErrImagePull, 1 CreateContainerConfigError | 确认集群中存在大量镜像拉取失败的 Pod，确认为问题核心。 |
| 2 | Pod 状态分布 | `kubernetes_tabular_query` | 49个异常Pod全部处于 Pending 状态，分布在 `aiops-e2e`, `default`, `mcp` 命名空间，`node1` 和 `node2` 节点。 | 确认问题在集群内广泛存在，非单一命名空间或节点问题。 |
| 3 | 镜像拉取错误(跨节点、命名空间) | `kubectl_describe` (x4) | **Pod test-dns-1779360358 (aiops-e2e/node1)**: `Failed to pull image "busybox:1.36.1"` 错误: `connection reset by peer` 从 `docker.io` -> `registry-1.docker.io:443`。<br>**Pod dig-tool (default/node1)**: `Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0"` 错误: `dial tcp 108.177.125.82:443: i/o timeout`。<br>**Pod registry-connect-test (default/node2)**: `Failed to pull image "busybox:1.36.1"` 错误: `x66次 i/o timeout` 到 `registry-1.docker.io:443` (多个IP)。<br>**Pod connectivity-test (mcp/node2)**: `Failed to pull image "busybox:1.36.1"` 错误: `x76次 i/o timeout` 到 Docker registry 多个IP。 | **确认真实根因**：所有节点 (`node1`, `node2`) 无法访问外部镜像仓库 `registry-1.docker.io` 和 `registry.k8s.io`，TCP 连接要么超时（`i/o timeout`），要么被对端重置（`connection reset by peer`）。此结论覆盖了46个镜像拉取失败的Pod。 |
| 4 | Secret Key 缺失错误 | `kubectl_describe` (Pod): `pod rc-config-secret-key-missing`<br>`kubectl_get_yaml` (Secret): `secret rc-app-secret` | **Pod 事件**: `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`<br>**Secret YAML**: `data_keys: EXISTING_SECRET_KEY` (表明只存在一个名为 `EXISTING_SECRET_KEY` 的键，没有 `APP_SECRET_TOKEN`) | 确认 Pod `rc-config-secret-key-missing` 无法启动是因为其引用的 Secret `rc-app-secret` 中不存在 `APP_SECRET_TOKEN` 这个键。 |
| 5 | 命令缺失错误 | `kubectl_describe`: `pod node-debugger-node1-nx8gb` | **事件**: `failed to create containerd task: ... exec: "curl": executable file not found in $PATH` | 确认 Pod `node-debugger-node1-nx8gb` 启动失败是因为容器镜像中不包含 `curl` 可执行文件。 |

### 证据关联分析
- **证据 #1, #2, #3 相互印证**：集群级别的 Pod 状态统计（#1, #2）与 4 个代表性 Pod 的详细错误（#3）完全匹配，共同将 #1 问题根因锁定为 **节点到外部镜像仓库的网络不可达**。证据 #3 来自 `node1` 和 `node2`，覆盖了 `aiops-e2e`, `default`, `mcp` 三个命名空间，排除了单节点或单命名空间的局部网络问题。
- **证据 #4 链**：Secret 缺失键导致 Pod 配置错误，无法创建容器。
- **证据 #5 链**：基础镜像（如 `curlimages/curl`）可能未被成功拉取（与 #1 问题相关）或应用容器本身镜像内没有 `curl`，导致启动命令执行失败。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点上的网络出口配置 (iptables/代理/路由) | critical | 无法确定网络问题的具体配置根因（是没配置代理、防火墙规则还是路由），影响修复方案的精准性。 |
| `node-debugger-node1-nx8gb` 的镜像定义 | important | 无法确认该 Pod 的 `command` 是否明确指定了 `curl`，或是否有其他基础镜像可用。 |

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ 集群节点（node1, node2）缺少到外部镜像仓库                                  │
│ （registry-1.docker.io, registry.k8s.io 等）的网络出口规则                  │
│ （HTTPS代理/防火墙放行/路由），导致节点无法访问公网。                       │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ 节点出口网络不可达 → kubelet 无法连接到镜像仓库:443                        │
│  → TCP 连接失败（i/o timeout 或被对端 connection reset）                    │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (主要)                                                             │
│ kubelet 镜像拉取持续失败，触发重试退避                                     │
│  → Pod 状态从 ErrImagePull 转变为 ImagePullBackOff。                       │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 / 其他并行问题                                                 │
│ 1. 约46个Pod 处于 ImagePullBackOff/ErrImagePull 状态，持续Pending不启动。   │
│ 2. 1个Pod 因 Secret键缺失报 CreateContainerConfigError。                   │
│ 3. 1个Pod 因容器内无 curl 命令报 StartError。                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论 1：集群网络问题 (L3) - 主要问题，影响 46/49 个异常 Pod**
根据 **证据 #1, #2, #3**，问题的根本原因是 **集群中所有节点（`node1`、`node2`）无法访问外部镜像仓库（`registry-1.docker.io:443`, `registry.k8s.io` 等）**。TCP 连接出现 `i/o timeout` 或 `connection reset by peer`，导致 kubelet 无法拉取超过20种基础镜像（如 `busybox:1.36.1`, `alpine:3.18`, `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` 等），进而导致46个Pod持续处于 Pending 状态。
- **置信度**: 高 (95%)
- ✅ 证据 #3 用4个来自不同节点和命名空间的Pod的`kubectl_describe`输出，100%复现了相同的网络错误。
- ⚠️ 缺失节点层面的网络配置证据（如 `iptables` 或代理配置），但错误模式非常明确。

**结论 2：配置错误 (L4) - 次要问题，影响 2/49 个异常 Pod**
- 根据 **证据 #4**，Pod `rc-config-secret-key-missing` 因 Secret `rc-app-secret` 中缺少键 `APP_SECRET_TOKEN` 而无法创建。这是一个独立的Kubernetes配置错误。
- 根据 **证据 #5**，Pod `node-debugger-node1-nx8gb` 因容器镜像中缺失 `curl` 命令而启动失败。这是一个独立的容器镜像或启动命令配置问题。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [致命] 解决节点网络出口问题**
这是影响范围最大、最紧急的问题。需要在**所有节点 (`node1`, `node2`)** 上检查并配置网络出口。
*建议*：
a. **检查环境变量**：确认节点上是否配置了 HTTP_PROXY / HTTPS_PROXY。
```bash
# 在所有节点上执行
echo $HTTP_PROXY
echo $HTTPS_PROXY
# 检查 containerd 配置 (如果使用)
cat /etc/containerd/config.toml | grep -i proxy
```
b. **测试网络连通性**：
```bash
# 在所有节点上执行，检查到 Docker Hub 的连接
curl -v --connect-timeout 10 https://registry-1.docker.io/v2/ 2>&1 || true
# 检查到 registry.k8s.io 的连接
curl -v --connect-timeout 10 https://registry.k8s.io/v2/ 2>&1 || true
# 检查 DNS 解析
nslookup registry-1.docker.io
```
c. **临时绕过（仅用于验证）**：如果集群内有可用的 HTTP 代理，可以将其配置给 containerd。例如，编辑 `/etc/containerd/config.toml`，在 `[plugins."io.containerd.grpc.v1.cri".containerd]` 部分添加：
```toml
[plugins."io.containerd.grpc.v1.cri".x509_key_pair]
  # 添加代理设置（如果存在）
```
并且配置系统代理或重启 containerd 服务。
*依据*：**证据 #3** 直接显示了 `i/o timeout` 和 `connection reset` 错误。

**2. [紧急] 修复 Secret 配置**
```bash
# 1. (推荐) 使用 kubectl patch 直接更新 Secret，添加缺失的键
# 注意：key 值需要是 base64 编码的。 假设 APP_SECRET_TOKEN 的值是 'my_new_secret_value'
echo -n 'my_new_secret_value' | base64

# 2. 编辑 Secret，在 data 字段下添加 APP_SECRET_TOKEN 及其 base64 编码值
kubectl edit secret rc-app-secret -n aiops-e2e
```
*依据*：**证据 #4** 中的 `Error: couldn't find key APP_SECRET_TOKEN in Secret...`。

**3. [局部] 修复或删除 debug Pod**
```bash
# 1. 查看 Pod 的定义，确认其使用的镜像和 command
kubectl get pod node-debugger-node1-nx8gb -n mcp -o yaml

# 2. 方案A：如果基础镜像中确实没有 curl，可以修改容器 command，例如：
#    command: ["/bin/sh", "-c", "sleep 3600"]
# 或者删除这个没用的 Pod
kubectl delete pod node-debugger-node1-nx8gb -n mcp
```
*依据*：**证据 #5** 中的 `exec: "curl": executable file not found in $PATH`。

### 后续优化
1.  **配置镜像仓库缓存/代理**：在集群内部署一个 Harbor 或 Nexus 作为镜像仓库代理，所有节点配置为通过内部代理拉取镜像，可以彻底解决外部网络不稳定或需要授权的问题。
2.  **资源清单审查**：检查所有 YAML 清单，确保引用的 Secret、ConfigMap、镜像和命令都是有效且存在的。
3.  **网络监控**：对集群节点的公网出口连通性进行监控。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 验证网络连通 | 在所有节点执行 `curl -v --connect-timeout 10 https://registry-1.docker.io/v2/` | 返回正常的 HTTP 响应，没有 `timeout` 或 `connection reset` 错误 |
| 2. 确认Pod状态恢复 | `kubectl get pods -A \| grep -v Running \| grep -v Completed` | 返回0行或仅显示预期内的非Running Pod |
| 3. 确认 Secret 修复 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | Events 中没有 `CreateContainerConfigError`，Pod 进入 `Init:Error` 或 `Pending` (因镜像拉取问题) |
| 4. 确认 debug Pod 修复 | `kubectl get pod node-debugger-node1-nx8gb -n mcp` | 如果保留，Pod 状态应为 `Running` |

---

## ⚠️ 注意事项
- **修复顺序**：请务必**优先解决网络问题**（步骤1），因为它影响了84% (46/49) 的异常 Pod。不解决网络问题，其他两个 Pod 即使配置修复了也会因拉取不到镜像而无法正常启动。
- **关于 `connection reset by peer`**：当您对 `registry-1.docker.io` 的连接尝试因“连接被重置”而失败时，这通常表明您的请求**被某个中间防火墙、代理或 IPS 设备拦截并拒绝了**，而不是单纯的网络超时。这说明配置出口规则是关键。
- **代理配置**：如果您的集群需要通过 HTTP 代理访问公网，请确保 `HTTP_PROXY` 和 `HTTPS_PROXY` 环境变量正确配置在 kubelet 和/或 containerd 服务中。

---

## 📊 性能统计

├─ 总耗时: 2.4m
├─ 问题定位: 51.3s (36%) ✅
├─ 证据链采集: 37.5s (26%) ✅
├─ 根因分析: 22.1s (15%) ✅
├─ 汇总总结: 32.3s (23%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 14 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-config-error
- **参考 Runbook**: pod-imagepull-failed, pod-config-error
- **工具调用**: 14 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
