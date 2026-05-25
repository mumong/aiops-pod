======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c68cdf2dcdcf4063]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先全局扫描一下集群中的所有 Pod，查看当前异常状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces: 总行数约108, 状态分布: Running ~59, ImagePullBackOff ~41, Completed 3, CrashLoopBackOff 1, ErrImagePull 1。大量ImagePullBackOff pods集中分布在default和mcp命名空间, 另有CrashLoopBackOff 1个在
   💭 [问题定位] 让我获取更详细的 Pod 列表信息。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=528 lines=3
Command failed (exit 2):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 22 pods in namespaces aiops-e2e, default, mcp, xnet — all Pending with ImagePullBackOff or ErrImagePull, except xnet/observability-kibana-65d7c45f6d-7zc9l which is Completed (exitCode=0). 39 out of 40
   💭 [问题定位] 很好，我已经掌握了全局异常情况。让我再看看那个 CrashLoopBackOff 的 Pod 详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-bq8pn   0
   💭 [问题定位] 现在让我获取对应的 runbook 来帮助定位。
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
   💭 [问题定位] 现在让我看一下那个具体的 ErrImagePull Pod 的详细信息来确认根因。
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
  Warning  BackOff  78s (x321 o
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod net-diag-1779385005 in namespace mcp on node node1/10.2.0.49 is Pending with pod IP 172.16.166.161. Container net-diag-1779385005 (image busybox:1.36.1) is in state Waiting (Reason: ImagePullBackO
   💭 [问题定位] 让我也看一下这个 CrashLoopBackOff 的 Pod 的上一次日志。
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [问题定位] 现在我已经掌握了所有信息。下面给出完整的定位分析结果。

---

## 🧠 定位分析结果

### 核心发现：集群存在两类异常

---

### 📊 异常组 1：ImagePullFailed（大规模影响）
| 维度 | 内容 |
|------|------|
| **异常类型** | `ImagePullFailed` |
| **兼容层级** | `L3` |
| **影响范围** | **39 个 Pod** 分布在 3 个命名空间 |
| **异常 Pod 分布** | `default` 命名空间约 13 个，`mcp` 命名空间约 25 个，`aiops-e2e` 命名空间 1 个 |
| **异常状态** | `Pending` → `ImagePullBackOff` / `ErrImagePull` |
| **Pod 状态关键词** | `ImagePullBackOff`, `ErrImagePull` |

**关键证据**（来自 `mcp/net-diag-1779385005` 的详细 Events）：
- 镜像 `busybox:1.36.1`（docker.io）拉取失败
- 错误信息：**`i/o timeout`** 和 **`connection reset by peer`**，从节点 `node1 (10.2.0.49)` 到 `registry-1.docker.io:443`（多个 IP，如 44.218.41.59、31.13.67.33 等）
- 72 次 Back-off 重试均失败，持续 57 分钟
- 受影响镜像包括：`busybox:1.36.1`（占绝大多数）、`alpine:3.18`、`curlimages/curl:8.12.1/7.88.1`、`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`、`registry.k8s.io/pause:3.9`

**根因判断**：**集群节点无法连通外部镜像仓库（docker.io 等）**，表现为 TCP 连接超时和被对端重置，可能是网络出口防火墙/代理限制、DNS 解析问题或镜像仓库出口带宽受限。

---

### 📊 异常组 2：ConfigError（单个 Pod 业务配置错误）
| 维度 | 内容 |
|------|------|
| **异常类型** | `ConfigError` |
| **兼容层级** | `L4` |
| **影响范围** | 1 个 Pod |
| **异常 Pod** | `aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn` |
| **异常状态** | `CrashLoopBackOff`（已重启 18 次） |
| **Pod 状态关键词** | `CrashLoopBackOff` |

**关键证据**：
- `Last State: Terminated, Reason: Error, Exit Code: 42` — 非 OOM（非 137）
- 上一次崩溃日志：**`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`**
- 容器镜像 `busybox:1.36` 已正常拉取到本地（Image ID 存在），说明不是镜像拉取问题
- 环境变量（`Environment: <none>`）未设置任何值

**根因判断**：应用启动时缺少必填环境变量 `APP_BOOT_MODE`，导致启动配置校验失败退出。该 Pod 由 `ReplicaSet/rc-config-env-missing` 管理（名称也暗示了 env 缺失），属于测试/e2e 场景。

---

### 综合分析

| 字段 | 值 |
|------|-----|
| **主异常层 (layer)** | `L3` — 镜像拉取失败影响范围最大（39 Pods） |
| **衍生层 (derived_layer)** | `L4` — ConfigError 单独存在 |
| **所有兼容层 (layers)** | `[L3, L4]` |
| **层名称 (layer_name)** | `ImagePullFailed` |
| **置信度 (confidence)** | `高` |
| **状态分类 (status_category)** | `ImagePullBackOff / CrashLoopBackOff` |

**关键实体 (key_entities)**：
- Pod 组：`default/*`（13 个 ImagePullBackOff）、`mcp/*`（25 个 ImagePullBackOff/ErrImagePull）、`aiops-e2e/test-dns-*`（1 个 ImagePullBackOff）
- 节点：`node1`（10.2.0.49）— 确认到 docker.io 超时/重置
- 镜像仓库：`registry-1.docker.io:443` — 无法连通
- 业务 Pod：`aiops-e2e/rc-config-env-missing-*` — 缺少 `APP_BOOT_MODE` 环境变量

**可能场景 (possible_scenarios)**：
1. **L3 主场景**：集群节点出口网络无法访问外部镜像仓库（docker.io/quay.io 等），TCP 连接超时或被防火墙重置
2. **L4 独立场景**：e2e 测试 Pod 缺少必要的环境变量配置，业务启动配置校验失败
   ✅ [问题定位] 完成 (53.2s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '集群节点出口网络无法访问外部镜像仓库 docker.io', 'probability': '高', 'reason': '多个 Pod 镜像拉取失败，错误均为 i/o timeout 和 connection reset by peer，节点 node1 到 registry-1.docker.io:443 的 TCP 连接被重置/超时'}, {'scenario': 'e2e 测试 Pod 缺少 APP_BOOT_MODE 环境变量导致业务启动失败', 'probability': '高', 'reason': 'Pod rc-config-env-missing 日志明确输出 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，退出码 42'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "node", "name": "node1 (10.2.0.49)", "namespace": ""}, {"type": "pod", "name": "net-diag-1779385005", "namespace": "mcp"}, {"type": "pod", "name": "rc-config-env-missing-5d9b8b766c-bq8pn", "namespace": "aiops-e2e"}, {"type": "image_registry", "name": "registry-1.docker.io:443", "namespace": ""}]
   reasoning=集群当前存在两类异常：(1) L3 主异常：39 个 Pod 处于 ImagePullBackOff/ErrImagePull 状态，分布在 aiops-e2e, default, mcp 命名空间，根因为节点无法连通外部镜像仓库（docker.io），TCP 连接超时/重置；(2) L4 独立异常：aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn 处于 CrashLoopBackOff（退出码 42），日志显示缺少 APP_BOOT_MODE 环境变量。由于 L3 影响范围最大（39 Pods），定层为 L3，衍生层为 L3/L4 共存。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "集群当前存在两类异常：(1) L3 主异常：39 个 Pod 处于 ImagePullBackOff/ErrImagePull 状态，分布在 aiops-e2e, default, mcp 命名空间，根因为节点无法连通外部镜像仓库（docker.io），TCP 连接超时/重置；(2) L4 独立异常：aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn 处于 CrashLoopBackOff（退出码 42），日志显示缺少 APP_BOOT_MODE 环境变量。由于 L3 影响范围最大（39 Pods），定层为 L3，衍生层为 L3/L4 共存。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-bq8pn", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-check-node2", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "node", "name": "node1 (10.2.0.49)", "namespace": ""}, {"type": "pod", "name": "net-diag-1779385005", "namespace": "mcp"}, {"type": "pod", "name": "rc-config-env-missing-5d9b8b766c-bq8pn", "namespace": "aiops-e2e"}, {"type": "image_registry", "name": "registry-1.docker.io:443", "namespace": ""}], "possible_scenarios": [{"scenario": "集群节点出口网络无法访问外部镜像仓库 docker.io", "probability": "高", "reason": "多个 Pod 镜像拉取失败，错误均为 i/o timeout 和 connection reset by peer，节点 node1 到 registry-1.docker.io:443 的 TCP 连接被重置/超时"}, {"scenario": "e2e 测试 Pod 缺少 APP_BOOT_MODE 环境变量导致业务启动失败", "probability": "高", "reason": "Pod rc-config-env-missing 日志明确输出 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，退出码 42"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-bq8pn"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-bq8pn"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 41, "ErrImagePull": 1}, "total_abnormal": 43, "selected_rows": ["aiops-e2e         rc-config-env-missing-5d9b8b766c-bq8pn              0/1     CrashLoopBackOff   18 (3m31s ago)   70m     172.16.166.129   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0                8h      172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff   0                3h17m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff   0                137m    172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff   0                6h48m   172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0                7h54m   172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0                5h30m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-tmp                                        0/1     ImagePullBackOff   0                144m    172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff   0                6h36m   172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0                7h4m    172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0                4h      172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ImagePullBackOff   0                10m     172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0                4h59m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0                6h45m   172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff   0                7h54m   172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0                7h7m    172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               curl-check-tmp                                      0/1     ImagePullBackOff   0                3h26m   172.16.104.58    node2    <none>           <none>            run=curl-check-tmp", "mcp               curls                                               0/1     ImagePullBackOff   0                106m    172.16.104.2     node2    <none>           <none>            run=curls", "mcp               dns-check-tmp                                       0/1     ImagePullBackOff   0                3h26m   172.16.104.13    node2    <none>           <none>            run=dns-check-tmp", "mcp               net-check-1779365549                                0/1     ImagePullBackOff   0                6h33m   172.16.166.179   node1    <none>           <none>            run=net-check-1779365549"], "raw_ref": "/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我已收到既有 evidence_plan，现在按计划调用所有 critical 和 important 级别的工具来采集证据。先从关键 Pod 的 describe 开始同步执行。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace default, node node1/10.2.0.49) is Pending. Container dig-tool (image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0) is in Waiting state (Reason: ImagePullBackOff). Ready
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-bq8pn
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff  118s (x321 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod test-dns-1779360358 (ns: aiops-e2e) on node node1/10.2.0.49 is Pending. Container image busybox:1.36.1 cannot be pulled: all attempts hit network errors (i/o timeout, connection reset by peer, Dea
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe pod net-diag-1779385005 (ns=mcp) on node node1/10.2.0.49: Status=Pending, State=Waiting(Reason=ImagePullBackOff). Container net-diag-1779385005 uses image busybox:1.36.1. All pull att
   💭 [证据链采集] 非常好，前 5 个 critical 工具已采集完成。接下来执行剩余两个 important 工具：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod node-debugger-node1-ckjnc (namespace mcp, node node1/10.2.0.49) is in Pending status. Container "debugger" uses image "busybox", command: nslookup registry.k8s.io. Container state: Waiting (Reason
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-check
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   4m48s (x49 over 4h57m)   kubelet  (combined from similar events): Failed t
   💭 [证据链采集] 所有证据已采集完毕，下面汇总结论。

---

## 证据采集结论

### ✅ 已采集证据（全部 7 项计划已完成）

#### G2 组 — ImagePullBackOff/ErrImagePull（主异常组，39+ Pods）— 完整验证

| 计划 | 命名空间 | Pod | 节点 | 镜像 | 关键错误 |
|------|---------|-----|------|------|---------|
| **e1 (critical)** | mcp | net-diag-1779385005 | node1 | busybox:1.36.1 | `dial tcp 31.13.67.33:443: i/o timeout` + `connection reset by peer` 到 docker.io |
| **e2 (critical)** | default | dig-tool | node1 | registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 | `dial tcp 142.250.157.82:443 i/o timeout` 到 asia-east1/us-west2 docker.pkg.dev |
| **e3 (critical)** | aiops-e2e | test-dns-1779360358 | node1 | busybox:1.36.1 | `connection reset by peer` + `i/o timeout` 到 docker.io (3.91.167.191:443, 199.59.148.229:443) |
| **e6 (important)** | default | dns-test-check | **node2** | busybox:1.36.1 | `dial tcp 202.160.128.40:443: i/o timeout` 到 docker.io |
| **e7 (important)** | mcp | node-debugger-node1-ckjnc | node1 | busybox (latest) | `i/o timeout` + `connection reset by peer` 到 docker.io |

**结论：** 跨 3 个命名空间（mcp、default、aiops-e2e）和 2 个节点（node1、node2）的所有 ImagePullBackOff/ErrImagePull Pod 拉取镜像失败的根本原因一致——**集群节点出口网络无法到达镜像仓库 docker.io（registry-1.docker.io:443）**。表现为 TCP i/o timeout 和 connection reset by peer，说明网络层面被阻断/过滤。

#### G1 组 — CrashLoopBackOff（非主异常组）— 最小验证

| 计划 | 命名空间 | Pod | 关键证据 |
|------|---------|-----|---------|
| **e4 (critical)** | aiops-e2e | rc-config-env-missing-5d9b8b766c-bq8pn | Exit Code=42, Last State=Error, 无 Environment 变量配置 |
| **e5 (critical)** | aiops-e2e | rc-config-env-missing-5d9b8b766c-bq8pn | 日志输出 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` |

**结论：** 该 Pod 的 CrashLoopBackOff 与镜像拉取无关（镜像 busybox:1.36 已成功拉取，Image ID 存在），根因是 **业务启动配置缺失——APP_BOOT_MODE 环境变量未设置**，退出码 42。属于 L4 ConfigError 类型，与 L3 网络问题是独立并发的两个故障。

### ⚠️ 未采集/冲突证据
- 无冲突证据。所有工具调用均成功返回，Pod 对象全部存在于预期命名空间。

### 最终诊断
1. **L3 主故障（影响范围 42 Pods）：** 集群节点（node1、node2）出口网络无法访问 docker.io 镜像仓库，TCP 连接被重置或超时。涉及镜像包括 `busybox:1.36.1`、`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` 等。建议：配置镜像代理/镜像仓库镜像（Mirror）或打通出口网络防火墙规则。
2. **L4 独立故障（影响范围 1 Pod）：** `rc-config-env-missing-5d9b8b766c-bq8pn` 需要 `APP_BOOT_MODE` 环境变量才能启动，当前 Environment 为空。建议：在 Deployment/Deployment spec 中添加 `env: [{name: APP_BOOT_MODE, value: "<mode>"}]`。
   ✅ [证据链采集] 完成 (43.3s)
   📤 → 下游数据: evidence_items=14/14
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证主异常组g2（ImagePullBackOff/ErrImagePull）代表Pod的Events，确认镜像拉取失败错误原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n mcp net-diag-1779385005","tool_args":{"kind":"pod","name":"net-diag-1779385005","namespace":"mcp"},"purpose":"获取ImagePullBackOff的Pod Events，确认错误类型（i/o timeout / connection reset / manifest unknown）","evidence_type":"Pod Events","target_scope":"g2代表Pod: mcp/net-diag-1779385005","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证主异常组g2中default命名空间代表Pod的镜像地址和Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dig-tool","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"交叉验证跨namespace的ImagePullBackOff是否一致为docker.io网络不可达","evidence_type":"Pod Events","target_scope":"g2代表Pod: default/dig-tool","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"验证主异常组g2中aiops-e2e命名空间代表Pod的镜像地址和Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e test-dns-1779360358","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"交叉验证aiops-e2e命名空间的ImagePullBackOff是否同为docker.io网络不可达","evidence_type":"Pod Events","target_scope":"g2代表Pod: aiops-e2e/test-dns-1779360358","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"验证g1异常组（CrashLoopBackOff）Pod的当前状态和Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-config-env-missing-5d9b8b766c-bq8pn","tool_args":{"kind":"pod","name":"rc-config-env-missing-5d9b8b766c-bq8pn","namespace":"aiops-e2e"},"purpose":"获取CrashLoopBackOff Pod的Events和Last State，确认退出码42和配置缺失","evidence_type":"Pod Events","target_scope":"g1 Pod: aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"验证g1异常组Pod的previous logs确认APP_BOOT_MODE缺失","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs --previous -n aiops-e2e rc-config-env-missing-5d9b8b766c-bq8pn","tool_args":{"namespace":"aiops-e2e","name":"rc-config-env-missing-5d9b8b766c-bq8pn"},"purpose":"获取CrashLoopBackOff Pod的上次日志，确认L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","evidence_type":"Pod Logs","target_scope":"g1 Pod: aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6","description":"验证g2主异常组node2上的Pod是否也有相同的ImagePull失败模式","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n default dns-test-check","tool_args":{"kind":"pod","name":"dns-test-check","namespace":"default"},"purpose":"确认node2上的ImagePullBackOff是否也表现为docker.io连接超时","evidence_type":"Pod Events","target_scope":"g2跨节点: default/dns-test-check (node2)","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7","description":"验证g2主异常组中ErrImagePull Pod的事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp node-debugger-node1-ckjnc","tool_args":{"kind":"pod","name":"node-debugger-node1-ckjnc","namespace":"mcp"},"purpose":"确认ErrImagePull Pod的错误内容是否与ImagePullBackOff一致","evidence_type":"Pod Events","target_scope":"g2 ErrImagePull代表Pod: mcp/node-debugger-node1-ckjnc","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod dig-tool (namespace default, node node1/10.2.0.49) is Pending. Container dig-tool (image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0) is in Waiting state (Reason: ImagePullBackOff). Ready=False, Restart Count=0. Multiple Failed events over 3h12m: kubelet reports ErrImagePull and pull failures with DeadlineExceeded to asia-east1 and us-west2 docker.pkg.dev endpoints (dial tcp i/o timeout). BackOff event x253.\nkey_facts: [\"pod: dig-tool | namespace: default | node: node1/10.2.0.49\", \"Status: Pending | IP: 172.16.166.157\", \"container: dig-tool | image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"State: Waiting (Reason: ImagePullBackOff) | Ready: False | Restart Count: 0\", \"Events: Warning Failed (x27 over 3h12m) - Error: ErrImagePull\", \"Events: Warning Failed (x4 over 3h2m) - pull failed: asia-east1-docker.pkg.dev dial tcp 142.250.157.82:443 i/o timeout\", \"Events: Warning Failed (x6 over 3h12m) - pull failed: us-west2-docker.pkg.dev dial tcp 108.177.125.82:443 i/o timeout\", \"Events: Warning Failed (x5 over 164m) - pull failed: us-west2-docker.pkg.dev dial tcp 142.250.157.82:443 i/o timeout\", \"Events: Normal BackOff (x253 over 3h12m) - Back-off pulling image\"]\nconflicts: [\"current_summary says 'Warning Failed 34m (x4 over 3h2m)' - raw_preview shows '34m (x4 over 3h2m)' for asia-east1; consistent. No material conflict.\"]\nmissing: [\"Container ID and Image ID are empty (image never pulled)\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-bq8pn\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  118s (x321 over 71m)  kubelet  Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-bq8pn_aiops-e2e(e49e4e4b-9359-4371-9a5e-bf2b7b082950)\n                  cni.projectcalico.org/containerID: 163a263de27393e0bca456e7f67ca48c38c689aa78b6f47c0f8498e963219a8a\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-config-env-missing-5d9b8b766c\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://efb57160c9f3a520b1bd026e3bb52f4326344c7a8885576e3193fa1459905d1f\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n    Args:\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42\n      Started:      Thu, 21 May 2026 18:42:30 +0000\n      Finished:     Thu, 21 May 2026 18:42:30 +0000\n    Ready:          False\n    Restart Count:  18\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-rlsf9:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  BackOff  118s (x321 over 71m)  kubelet  Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-bq8pn_aiops-e2e(e49e4e4b-9359-4371-9a5e-bf2b7b082950)\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod test-dns-1779360358 (ns: aiops-e2e) on node node1/10.2.0.49 is Pending. Container image busybox:1.36.1 cannot be pulled: all attempts hit network errors (i/o timeout, connection reset by peer, DeadlineExceeded) when connecting to docker.io registry. Container state Waiting (ImagePullBackOff). Events show repeated pull failures (x59, x107, x956 BackOff) over ~8h.\nkey_facts: [\"Pod: test-dns-1779360358\", \"Namespace: aiops-e2e\", \"Node: node1/10.2.0.49\", \"Status: Pending\", \"Container: test-dns-1779360358, Image: busybox:1.36.1\", \"Container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False\", \"Restart Count: 0\", \"Events: Warning Failed (x59 over 7h59m) - Error: ErrImagePull\", \"Events: Warning Failed (x107 over 7h24m) - Failed to pull image: read connection reset by peer on 3.91.167.191:443\", \"Events: Warning Failed (55m) - dial tcp 199.59.148.229:443: i/o timeout\", \"Events: Warning Failed (39m) - dial tcp 162.125.17.131:443: i/o timeout (DeadlineExceeded)\", \"Events: Warning Failed (28m) - read connection reset by peer on 3.233.166.60:443\", \"Events: Normal BackOff (x956 over 7h59m) - Back-off pulling image busybox:1.36.1\", \"Events: Normal Pulling (x82 over 8h) - Pulling image busybox:1.36.1\", \"Pod IP: 172.16.166.148\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary mentions 'Failed 55m (x59 over 7h59m) Error: ErrImagePull' without the corresponding 'Pulling' event - raw_preview confirms both exist\"]\nmissing: [\"current_summary truncates before events are fully listed; raw_preview adds Normal Pulling event (x82 over 8h) and BackOff (x956 over 7h59m) not fully captured in summary\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/004-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/004-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/004-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe pod net-diag-1779385005 (ns=mcp) on node node1/10.2.0.49: Status=Pending, State=Waiting(Reason=ImagePullBackOff). Container net-diag-1779385005 uses image busybox:1.36.1. All pull attempts to registry-1.docker.io failed consistently over ~70min — errors: i/o timeout (to 31.13.67.33:443, 162.125.17.131:443) and connection reset by peer (to 3.208.234.98:443, 98.95.147.200:443, 3.90.170.8:443, 35.153.85.165:443). 72 back-off events. Pod has Calico network with IP 172.16.166.161/32. QoS=BestEffort. Ready=False, ContainersReady=False.\nkey_facts: [\"Pod net-diag-1779385005 in namespace mcp is Pending\", \"Node: node1/10.2.0.49\", \"Container net-diag-1779385005 image busybox:1.36.1\", \"State: Waiting, Reason: ImagePullBackOff\", \"All pull attempts to docker.io/library/busybox:1.36.1 failed\", \"Errors: i/o timeout (to 31.13.67.33:443, 162.125.17.131:443) and connection reset by peer (to 3.208.234.98:443, 98.95.147.200:443, 3.90.170.8:443, 35.153.85.165:443)\", \"72 back-off events over 58m\", \"Pod IP: 172.16.166.161/32 via Calico CNI\", \"QoS Class: BestEffort, Ready=False, ContainersReady=False\", \"Container ID and Image ID are empty (never pulled)\"]\nmissing: [\"Pod start time (present in raw_preview but not critical for diagnosis)\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod node-debugger-node1-ckjnc (namespace mcp, node node1/10.2.0.49) is in Pending status. Container \"debugger\" uses image \"busybox\", command: nslookup registry.k8s.io. Container state: Waiting (Reason: ImagePullBackOff), Ready: False, Restart Count: 0. All image pull attempts to docker.io/library/busybox:latest failed with i/o timeout or connection reset by peer to various docker.io IPs. Events show repeated Failed (ErrImagePull) and BackOff (x829 over 7h10m) for pulling busybox.\nkey_facts: [\"name: node-debugger-node1-ckjnc\", \"namespace: mcp\", \"node: node1/10.2.0.49\", \"Status: Pending\", \"Container: debugger, Image: busybox, Command: nslookup registry.k8s.io\", \"Container State: Waiting, Reason: ImagePullBackOff\", \"Container Ready: False, Restart Count: 0\", \"Warning Failed: ErrImagePull (x54 over 7h10m)\", \"Warning Failed: Failed to pull image busybox - i/o timeout & connection reset by peer to docker.io registry IPs\", \"Normal BackOff: Back-off pulling image busybox (x829 over 7h10m)\", \"QoS Class: BestEffort\", \"Volumes: host-root (HostPath /), kube-api-access-cgd95 (Projected)\"]\nconflicts: [\"current_summary says 'Warning Failed 18m (x72 over 6h43m)' but raw_preview shows same event as 'Warning Failed 18m (x72 over 6h43m)' — consistent; no conflict.\"]\nmissing: [\"No container ID or Image ID set\", \"No environment variables set\", \"No node selectors\", \"Tolerations: op=Exists\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-test-check\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   4m48s (x49 over 4h57m)   kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 202.160.128.40:443: i/o timeout\n  Normal   BackOff  2m3s (x1027 over 5h31m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   31m (x50 over 5h31m)     kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 9e22290236797aa5f25c53b51c38e8bf6856c341e86020f57967c39f91341d92\n                  cni.projectcalico.org/podIP: 172.16.104.53/32\n                  cni.projectcalico.org/podIPs: 172.16.104.53/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-test-check:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      nslookup\n      registry.invalid\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-9z4n9:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   31m (x50 over 5h31m)     kubelet  Error: ErrImagePull\n  Warning  Failed   4m48s (x49 over 4h57m)   kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 202.160.128.40:443: i/o timeout\n  Normal   BackOff  2m3s (x1027 over 5h31m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c68cdf2dcdcf4063/tools/007-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"所有证据已采集完毕，下面汇总结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（全部 7 项计划已完成）\n\n#### G2 组 — ImagePullBackOff/ErrImagePull（主异常组，39+ Pods）— 完整验证\n\n| 计划 | 命名空间 | Pod | 节点 | 镜像 | 关键错误 |\n|------|---------|-----|------|------|---------|\n| **e1 (critical)** | mcp | net-diag-1779385005 | node1 | busybox:1.36.1 | `dial tcp 31.13.67.33:443: i/o timeout` + `connection reset by peer` 到 docker.io |\n| **e2 (critical)** | default | dig-tool | node1 | registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 | `dial tcp 142.250.157.82:443 i/o timeout` 到 asia-east1/us-west2 docker.pkg.dev |\n| **e3 (critical)** | aiops-e2e | test-dns-1779360358 | node1 | busybox:1.36.1 | `connection reset by peer` + `i/o timeout` 到 docker.io (3.91.167.191:443, 199.59.148.229:443) |\n| **e6 (important)** | default | dns-test-check | **node2** | busybox:1.36.1 | `dial tcp 202.160.128.40:443: i/o timeout` 到 docker.io |\n| **e7 (important)** | mcp | node-debugger-node1-ckjnc | node1 | busybox (latest) | `i/o timeout` + `connection reset by peer` 到 docker.io |\n\n**结论：** 跨 3 个命名空间（mcp、default、aiops-e2e）和 2 个节点（node1、node2）的所有 ImagePullBackOff/ErrImagePull Pod 拉取镜像失败的根本原因一致——**集群节点出口网络无法到达镜像仓库 docker.io（registry-1.docker.io:443）**。表现为 TCP i/o timeout 和 connection reset by peer，说明网络层面被阻断/过滤。\n\n#### G1 组 — CrashLoopBackOff（非主异常组）— 最小验证\n\n| 计划 | 命名空间 | Pod | 关键证据 |\n|------|---------|-----|---------|\n| **e4 (critical)** | aiops-e2e | rc-config-env-missing-5d9b8b766c-bq8pn | Exit Code=42, Last State=Error, 无 Environment 变量配置 |\n| **e5 (critical)** | aiops-e2e | rc-config-env-missing-5d9b8b766c-bq8pn | 日志输出 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` |\n\n**结论：** 该 Pod 的 CrashLoopBackOff 与镜像拉取无关（镜像 busybox:1.36 已成功拉取，Image ID 存在），根因是 **业务启动配置缺失——APP_BOOT_MODE 环境变量未设置**，退出码 42。属于 L4 ConfigError 类型，与 L3 网络问题是独立并发的两个故障。\n\n### ⚠️ 未采集/冲突证据\n- 无冲突证据。所有工具调用均成功返回，Pod 对象全部存在于预期命名空间。\n\n### 最终诊断\n1. **L3 主故障（影响范围 42 Pods）：** 集群节点（node1、node2）出口网络无法访问 docker.io 镜像仓库，TCP 连接被重置或超时。涉及镜像包括 `busybox:1.36.1`、`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` 等。建议：配置镜像代理/镜像仓库镜像（Mirror）或打通出口网络防火墙规则。\n2. **L4 独立故障（影响范围 1 Pod）：** `rc-config-env-missing-5d9b8b766c-bq8pn` 需要 `APP_BOOT_MODE` 环境变量才能启动，当前 Environment 为空。建议：在 Deployment/Deployment spec 中添加 `env: [{name: APP_BOOT_MODE, value: \"<mode>\"}]`。","collection_summary":"计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%；其中真实环境证据 14/14 项，完整度 100%；实际执行工具 14 个，匹配计划 7 个，未规划证据 7 个","plan_total":7,"plan_collected":7,"plan_completeness":1.0,"environment_evidence_total":14,"environment_evidence_collected":14,"environment_evidence_completeness":1.0,"executed_tool_count":14,"matched_tool_count":7,"unplanned_tool_count":7,"evidence_inventory":[{"id":"e1","description":"验证主异常组g2（ImagePullBackOff/ErrImagePull）代表Pod的Events，确认镜像拉取失败错误原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n mcp net-diag-1779385005","purpose":"获取ImagePullBackOff的Pod Events，确认错误类型（i/o timeout / connection reset / manifest unknown）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证主异常组g2中default命名空间代表Pod的镜像地址和Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n default dig-tool","purpose":"交叉验证跨namespace的ImagePullBackOff是否一致为docker.io网络不可达","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证主异常组g2中aiops-e2e命名空间代表Pod的镜像地址和Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e test-dns-1779360358","purpose":"交叉验证aiops-e2e命名空间的ImagePullBackOff是否同为docker.io网络不可达","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证g1异常组（CrashLoopBackOff）Pod的当前状态和Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-config-env-missing-5d9b8b766c-bq8pn","purpose":"获取CrashLoopBackOff Pod的Events和Last State，确认退出码42和配置缺失","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"验证g1异常组Pod的previous logs确认APP_BOOT_MODE缺失","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs --previous -n aiops-e2e rc-config-env-missing-5d9b8b766c-bq8pn","purpose":"获取CrashLoopBackOff Pod的上次日志，确认L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"验证g2主异常组node2上的Pod是否也有相同的ImagePull失败模式","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n default dns-test-check","purpose":"确认node2上的ImagePullBackOff是否也表现为docker.io连接超时","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7","description":"验证g2主异常组中ErrImagePull Pod的事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod -n mcp node-debugger-node1-ckjnc","purpose":"确认ErrImagePull Pod的错误内容是否与ImagePullBackOff一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证主异常组g2（ImagePullBackOff/ErrImagePull）代表Pod的... | `kubectl describe pod -n mcp net-diag-1779385005` |
   | e2 | critical | ✅ | kubectl_describe | 验证主异常组g2中default命名空间代表Pod的镜像地址和Events | `kubectl describe pod -n default dig-tool` |
   | e3 | critical | ✅ | kubectl_describe | 验证主异常组g2中aiops-e2e命名空间代表Pod的镜像地址和Events | `kubectl describe pod -n aiops-e2e test-dns-1779360358` |
   | e4 | critical | ✅ | kubectl_describe | 验证g1异常组（CrashLoopBackOff）Pod的当前状态和Events | `kubectl describe pod -n aiops-e2e rc-config-env-missing-5d9b8b766c-bq8pn` |
   | e5 | critical | ✅ | kubectl_previous_logs | 验证g1异常组Pod的previous logs确认APP_BOOT_MODE缺失 | `kubectl logs --previous -n aiops-e2e rc-config-env-missing-5d9b8b766c-bq8pn` |
   | e6 | important | ✅ | kubectl_describe | 验证g2主异常组node2上的Pod是否也有相同的ImagePull失败模式 | `kubectl describe pod -n default dns-test-check` |
   | e7 | important | ✅ | kubectl_describe | 验证g2主异常组中ErrImagePull Pod的事件 | `kubectl describe pod -n mcp node-debugger-node1-ckjnc` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (32.1s)
   📤 → 下游数据: root_cause=集群存在两个独立异常：**L3 主异常**（影响 42 Pods，跨 3 命名空间 × 2 节点）——节点 node1（10.2.0.49）和 node2（10.2.0.50）出口网络无法到达 docker.io 镜像仓库，事件明确显示 `dial tcp XXX.XXX.XXX.XXX:443: i/o timeout` 和 `connection reset by peer` 到 registry-1.docker.io 多个 CDN IP（如 31.13.67.33, 162.125.17.131, 3.208.234.98 等），涉及镜像包括 busybox:1.36.1、alpine:3.18、curlimages/curl、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 等。**L4 独立异常**（1 Pod）——aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn 处于 CrashLoopBackOff（退出码42, 重启18次），日志明确输出 `L4_CONFIG_BOO
... 截断，原始 603 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1/10.2.0.49, node2/10.2.0.50）出口网络到外部镜像仓库 docker.io (registry-1.docker.io:443) 的 TCP 连接被阻断——表现为同时出现 i/o timeout 和 connection reset by peer，覆盖多个 docker.io CDN IP 地址（31.13.67.33, 162.125.17.131, 3.208.234.98, 98.95.147.200, 3.90.170.8, 35.153.85.165, 202.160.128.40, 199.59.148.229 等），同时 docker.pkg.dev 也超时", "propagation": "节点无法TCP连接到外部镜像仓库 → kubelet 无法从 registry-1.docker.io 拉取任何容器镜像（包括 busybox:1.36.1, alpine:3.18, curlimages/curl, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 等）→ 所有依赖这些外部镜像的 Pod 进入 ImagePullBackOff/ErrImagePull 状态 → kubelet 持续重试并产生大量 BackOff 事件", "direct_cause": "节点出口防火墙/网络策略阻止了到 docker.io 和 docker.pkg.dev 的 HTTPS (443) 出站连接", "manifestation": "42个Pod（41个ImagePullBackOff + 1个ErrImagePull）分布在 aiops-e2e/default/mcp 三个命名空间、node1/node2 两个节点，全部处于 Pending 状态，Pod 事件显示反复的 ErrImagePull 和 BackOff，错误原文包含 'dial tcp i/o timeout' 和 'connection reset by peer' 到 docker.io 注册表 IP；1个独立Pod（aiops-e2e/rc-config-env-missing）CrashLoopBackOff 退出码42，日志显示缺少 APP_BOOT_MODE 环境变量"}
   rca_analysis={"phenomenon": "集群共43个异常Pod：(1) 主异常组g2（42个Pod）分布在 aiops-e2e、default、mcp 三个命名空间，状态为 ImagePullBackOff（41个）/ ErrImagePull（1个），分布在 node1 和 node2 两个节点上，均无法拉取镜像；(2) 非主异常组g1（1个Pod）aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn 处于 CrashLoopBackOff，退出码42", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod dig-tool (default, node1): 镜像 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 拉取失败，错误 dial tcp i/o timeout 到 asia-east1/us-west2 docker.pkg.dev (142.250.157.82:443, 108.177.125.82:443)", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe", "content": "Pod test-dns-1779360358 (aiops-e2e, node1): 镜像 busybox:1.36.1 拉取失败，错误 connection reset by peer + i/o timeout 到 docker.io (3.91.167.191:443, 199.59.148.229:443, 162.125.17.131:443)", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe", "content": "Pod net-diag-1779385005 (mcp, node1): 镜像 busybox:1.36.1 拉取失败，错误 dial tcp i/o timeout (31.13.67.33:443, 162.125.17.131:443) + connection reset by peer (3.208.234.98:443, 98.95.147.200:443, 3.90.170.8:443, 35.153.85.165:443)", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe", "content": "Pod node-debugger-node1-ckjnc (mcp, node1): 镜像 busybox (latest) 拉取失败，错误 i/o timeout + connection reset by peer 到 docker.io, BackOff x829 over 7h10m", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe", "content": "Pod dns-test-check (default, node2): 镜像 busybox:1.36.1 拉取失败，错误 dial tcp 202.160.128.40:443: i/o timeout 到 docker.io registry-1", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe", "content": "Pod rc-config-env-missing-5d9b8b766c-bq8pn (aiops-e2e, node1): CrashLoopBackOff, 退出码42, 镜像 busybox:1.36 已成功拉取(Image ID存在), 无Environment变量配置, 重启18次", "reliability": "高"}, {"id": "e7", "source": "kubectl_previous_logs", "content": "Pod rc-config-env-missing 日志: L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "reliability": "高"}, {"id": "e8", "source": "kubernetes_jq_query", "content": "40个容器中39个处于ImagePullBackOff等待状态；主要失败镜像包括 busybox:1.36.1 (dominant), alpine:3.18, curlimages/curl, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, registry.k8s.io/pause:3.9, busybox(no tag)", "reliability": "高"}, {"id": "e9", "source": "layer_handoff.current_abnormal_summary", "content": "集群Pod状态: Running~59, ImagePullBackOff~41, Completed 3, CrashLoopBackOff 1, ErrImagePull 1, 总计异常43", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "ErrImagePull + dial tcp 142.250.157.82:443 i/o timeout 到 docker.pkg.dev (asia-east1, us-west2)", "interpretation": "节点node1到Google Container Registry (docker.pkg.dev)的TCP连接超时，镜像拉取被网络层阻断"}, {"evidence_id": "e2", "raw_data": "connection reset by peer (3.91.167.191:443, 199.59.148.229:443) + i/o timeout (162.125.17.131:443) 到 docker.io", "interpretation": "节点node1到docker.io的TCP连接同时出现超时和连接重置两种网络错误，表明出口网络被过滤或阻断"}, {"evidence_id": "e3", "raw_data": "i/o timeout (31.13.67.33:443, 162.125.17.131:443) + connection reset by peer (3.208.234.98:443, 98.95.147.200:443, 3.90.170.8:443) 到 registry-1.docker.io", "interpretation": "节点node1到docker.io多个IP均失败，错误类型混合，确认是网络层问题而非镜像不存在或认证问题"}, {"evidence_id": "e4", "raw_data": "i/o timeout + connection reset by peer 到 docker.io, BackOff x829 over 7h10m", "interpretation": "节点node1上另一种镜像busybox(latest)同样失败，排除镜像tag问题，确认网络不可达"}, {"evidence_id": "e5", "raw_data": "dial tcp 202.160.128.40:443: i/o timeout 到 registry-1.docker.io (node2)", "interpretation": "节点node2同样无法到达docker.io，确认问题在集群出口网络层面而非单节点问题"}, {"evidence_id": "e6", "raw_data": "CrashLoopBackOff, ExitCode=42, Image=busybox:1.36 (已拉取成功, Image ID存在), Environment=<none>, Restart=18", "interpretation": "Pod镜像已成功拉取，CrashLoopBackOff根因不是镜像拉取问题。无环境变量配置，退出码42表示业务配置错误"}, {"evidence_id": "e7", "raw_data": "L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE", "interpretation": "业务容器启动时检测到缺少必需的APP_BOOT_MODE环境变量，主动退出并报告配置缺失"}, {"evidence_id": "e8", "raw_data": "39/40 containers ImagePullBackOff; failing images: busybox:1.36.1, alpine:3.18, curlimages/curl:8.12.1, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, registry.k8s.io/pause:3.9, busybox", "interpretation": "多种不同来源的镜像全部拉取失败，排除镜像源特定问题，指向集群出口网络全局不可达"}, {"evidence_id": "e9", "raw_data": "Running~59, ImagePullBackOff~41, CrashLoopBackOff 1, ErrImagePull 1", "interpretation": "异常Pod占比约40%，影响范围集中在default和mcp命名空间"}], "causal_chain": {"root_cause": "集群节点（node1/10.2.0.49, node2/10.2.0.50）出口网络到外部镜像仓库 docker.io (registry-1.docker.io:443) 的 TCP 连接被阻断——表现为同时出现 i/o timeout 和 connection reset by peer，覆盖多个 docker.io CDN IP 地址（31.13.67.33, 162.125.17.131, 3.208.234.98, 98.95.147.200, 3.90.170.8, 35.153.85.165, 202.160.128.40, 199.59.148.229 等），同时 docker.pkg.dev 也超时", "propagation": "节点无法TCP连接到外部镜像仓库 → kubelet 无法从 registry-1.docker.io 拉取任何容器镜像（包括 busybox:1.36.1, alpine:3.18, curlimages/curl, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 等）→ 所有依赖这些外部镜像的 Pod 进入 ImagePullBackOff/ErrImagePull 状态 → kubelet 持续重试并产生大量 BackOff 事件", "direct_cause": "节点出口防火墙/网络策略阻止了到 docker.io 和 docker.pkg.dev 的 HTTPS (443) 出站连接", "manifestation": "42个Pod（41个ImagePullBackOff + 1个ErrImagePull）分布在 aiops-e2e/default/mcp 三个命名空间、node1/node2 两个节点，全部处于 Pending 状态，Pod 事件显示反复的 ErrImagePull 和 BackOff，错误原文包含 'dial tcp i/o timeout' 和 'connection reset by peer' 到 docker.io 注册表 IP；1个独立Pod（aiops-e2e/rc-config-env-missing）CrashLoopBackOff 退出码42，日志显示缺少 APP_BOOT_MODE 环境变量"}, "root_cause": "集群存在两个独立异常：**L3 主异常**（影响 42 Pods，跨 3 命名空间 × 2 节点）——节点 node1（10.2.0.49）和 node2（10.2.0.50）出口网络无法到达 docker.io 镜像仓库，事件明确显示 `dial tcp XXX.XXX.XXX.XXX:443: i/o timeout` 和 `connection reset by peer` 到 registry-1.docker.io 多个 CDN IP（如 31.13.67.33, 162.125.17.131, 3.208.234.98 等），涉及镜像包括 busybox:1.36.1、alpine:3.18、curlimages/curl、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 等。**L4 独立异常**（1 Pod）——aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn 处于 CrashLoopBackOff（退出码42, 重启18次），日志明确输出 `L4_CONFIG_BOO\n... 截断，原始 603 字符", "root_cause_summary": "集群存在两个独立异常：**L3 主异常**（影响 42 Pods，跨 3 命名空间 × 2 节点）——节点 node1（10.2.0.49）和 node2（10.2.0.50）出口网络无法到达 docker.io 镜像仓库，事件明确显示 `dial tcp XXX.XXX.XXX.XXX:443: i/o timeout` 和 `connection reset by peer` 到 registry-1.docker.io 多个 CDN IP（如 31.13.67.33, 162.125.17.131, 3.208.234.98 等），涉及镜像包括 busybox:1.36.1、alpine:3.18、curlimages/curl、registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 等。**L4 独立异常**（1 Pod）——aiops-e2e/rc-config-env-missing-5d9b8b766c-bq8pn 处于 CrashLoopBackOff（退出码42, 重启18次），日志明确输出 `L4_CONFIG_BOO\n... 截断，原始 603 字符", "confidence": 0.95, "confidence_reason": "直接证据完备：(1) 7个Pod的kubectl describe事件原文包含明确的网络错误（i/o timeout + connection reset by peer），覆盖两个节点和多个不同镜像/镜像仓库；(2) CrashLoopBackOff Pod 的日志直接输出了缺失环境变量的错误信息；(3) 所有工具调用均成功返回且无冲突证据；(4) 因果链清晰完整，无推测环节", "primary_runbooks": ["pod-imagepull-failed.md", "pod-config-error.md"], "alternative_causes": [{"cause": "镜像地址或 tag 不存在导致 ImagePullBackOff", "probability": "low", "reason": "排除：涉及多种不同镜像源（docker.io, registry.k8s.io, docker.pkg.dev），错误均为网络层错误而非 manifest unknown 或 not found；kubectl describe 无 'manifest unknown' 类事件"}, {"cause": "imagePullSecret 缺失或认证失败导致镜像拉取失败", "probability": "low", "reason": "排除：错误信息全部为网络层（timeout/reset），无认证失败（denied/unauthorized）相关错误；且所有镜像为公共镜像（busybox, alpine, curlimages/curl 等）无需认证"}, {"cause": "DNS 解析失败导致无法解析镜像仓库域名", "probability": "low", "reason": "排除：kubectl describe 事件显示已经解析到具体的 IP 地址（如 31.13.67.33:443, 3.208.234.98:443），但 TCP 连接阶段超时/重置"}, {"cause": "rc-config-env-missing Pod 的 CrashLoopBackOff 由镜像拉取失败引起", "probability": "low", "reason": "排除：该 Pod 的 kubectl describe 显示 Image ID 已设置（sha256:114f4abb6799...），Container ID 也存在（containerd://efb57160c9...），说明镜像已成功拉取；退出码42与镜像拉取无关"}], "limitations": "未直接采集集群防火墙/网络策略配置，无法确认出口阻断的具体原因（是企业防火墙规则、云厂商安全组还是网络设备ACL）；未采集 containerd/cri-o 配置确认是否有 mirror 或 proxy 配置；未确认集群内是否有可用的私有镜像仓库可作为替代方案；rc-config-env-missing Pod 的 Deploy/ReplicaSet 或 Helm chart 中为何缺少 APP_BOOT_MODE 环境变量未进一步追溯", "llm_raw_analysis": "## 证据清点\n已采集7项计划证据 + 9项上游已验证工具结果。覆盖了主异常组g2（ImagePullBackOff/ErrImagePull, 42 Pods）和非主异常组g1（CrashLoopBackOff, 1 Pod）的所有关键维度。\n\n## 逐条分析\n**e1-e5 (主异常组g2):** 5个代表Pod的kubectl describe结果一致指向网络层问题——所有错误均为 `dial tcp i/o timeout` 或 `connection reset by peer`，目标均为 docker.io (registry-1.docker.io:443) 及其 CDN IP。覆盖：\n- 3个命名空间：mcp（net-diag, node-debugger）、default（dig-tool, dns-test-check）、aiops-e2e（test-dns）\n- 2个节点：node1（10.2.0.49）和 node2（10.2.0.50）\n- 多种镜像：busybox:1.36.1, busybox(latest), registry.k8s.io/e2e-te\n... 截断，原始 1361 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群存在两个独立异常：**L3 主异常**（影响 42 Pods，跨 3 命名空间 × 2 节点）——节点 node1（10.2.0.49）和 node2（10.2.0.50）出口网络无法到达 docker.io 镜像仓库，事件明确显示 `dial tcp XXX.XXX.XXX.XXX:443: ...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1/10.2.0.49, node2/10.2.0.50）出口网络到外部镜像仓库 docker.io (registry-1.docker.io:443) 的 TCP 连接被阻断——表现为同时出现 i/o timeout 和 connection reset by peer，覆盖多个 docker.io CDN IP 地址（31.13.67.33, 162.125.17.131, 3.208.234.98, 98.95.147.200, 3.90.170.8, 35.153.85.165, 202.160.128.40, 199.59.148.229 等），同时 docker.pkg.dev 也超时
     传导机制: 节点无法TCP连接到外部镜像仓库 → kubelet 无法从 registry-1.docker.io 拉取任何容器镜像（包括 busybox:1.36.1, alpine:3.18, curlimages/curl, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 等）→ 所有依赖这些外部镜像的 Pod 进入 ImagePullBackOff/ErrImagePull 状态 → kubelet 持续重试并产生大量 BackOff 事件
     最终表现: 42个Pod（41个ImagePullBackOff + 1个ErrImagePull）分布在 aiops-e2e/default/mcp 三个命名空间、node1/node2 两个节点，全部处于 Pending 状态，Pod 事件显示反复的 ErrImagePull 和 BackOff，错误原文包含 'dial tcp i/o timeout' 和 'connection reset by peer' 到 docker.io 注册表 IP；1个独立Pod（aiops-e2e/rc-config-env-missing）CrashLoopBackOff 退出码42，日志显示缺少 APP_BOOT_MODE 环境变量


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (35.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 9900 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 44.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深K8s诊断报告专家，我将根据您提供的信息，为您生成一份详尽、完整的诊断报告。

---

## 📊 诊断概览
*   **您的集群存在两个独立且关键的问题：**
    1.  **主问题（影响范围大）：** 39个Pod处于 `ImagePullBackOff`/`ErrImagePull` 状态，分布在 `aiops-e2e`, `default`, `mcp` 三个命名空间。**根因是集群节点无法连通外部镜像仓库。**
    2.  **独立问题（影响1个Pod）：** `aiops-e2e` 命名空间下的 `rc-config-env-missing-5d9b8b766c-bq8pn` Pod处于 `CrashLoopBackOff` 状态。**根因是其缺失必要的环境变量。**

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff (41 Pods), CrashLoopBackOff (1 Pod), ErrImagePull (1 Pod) |
| **兼容归因层** | L3 (主), 衍生 L3/L4 |
| **问题分类** | `image_pull` (镜像拉取失败) 和 `config_bootstrap` (启动配置/环境变量缺失) |
| **置信度** | 高 (95%) |
| **证据完整度** | 7/7 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体（问题一：ImagePullBackOff/ErrImagePull）**：
| 类型 | 值 |
|------|-----|
| 受影响的Pod数 | 39+ 个（含 `ImagePullBackOff` 和 `ErrImagePull`） |
| 受影响节点 | `node1 (10.2.0.49)`, `node2 (10.2.0.50)` |
| 受影响命名空间 | `aiops-e2e`, `default`, `mcp` |
| 失败镜像 | `busybox:1.36.1`, `alpine:3.18`, `curlimages/curl:8.12.1`, `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` |
| 错误信息 | `Failed to pull image ... dial tcp [IP]:443: i/o timeout` 和 `connection reset by peer` |

**关键实体（问题二：CrashLoopBackOff）**：
| 类型 | 值 |
|------|-----|
| 受影响Pod | `rc-config-env-missing-5d9b8b766c-bq8pn` |
| 受影响命名空间 | `aiops-e2e` |
| 错误信息 | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| e1 | Pod 状态和事件 | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` | 镜像: `busybox:1.36.1`。`Events: Warning Failed (x59 over 7h59m) - Error: ErrImagePull`, `... read connection reset by peer on 3.91.167.191:443`, `... dial tcp 199.59.148.229:443: i/o timeout` | 节点 `node1` 无法从 `docker.io` 拉取 `busybox` 镜像，错误类型覆盖 `i/o timeout` 和 `connection reset by peer` |
| e2 | Pod 状态和事件 | `kubectl describe pod dig-tool -n default` | 镜像: `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`。`Events: Warning Failed (x27 over 3h12m) - Error: ErrImagePull`, `... pull failed: asia-east1-docker.pkg.dev dial tcp 142.250.157.82:443 i/o timeout` | 节点 `node1` 也无法从 `docker.pkg.dev`（另一个常用镜像仓库）拉取镜像，进一步证实了出口网络的普遍性问题 |
| e3 | Pod 状态和事件 | `kubectl describe pod net-diag-1779385005 -n mcp` | 镜像: `busybox:1.36.1`。`Errors: i/o timeout (to 31.13.67.33:443, 162.125.17.131:443) and connection reset by peer (to 3.208.234.98:443, ...)` | 节点 `node1` 拉取镜像时，连接多个 `docker.io` CDN IP 均发生 `i/o timeout` 或 `connection reset by peer`，排除了镜像仓库单一IP故障的可能 |
| e4 | Pod 当前状态和事件 | `kubectl describe pod node-debugger-node1-ckjnc -n mcp` | 镜像: `busybox`。`Events: Warning Failed: Failed to pull image busybox - i/o timeout & connection reset by peer to docker.io registry IPs` | 节点 `node1` 连拉取公共镜像 `busybox:latest` 也不成功 |
| e5 | Pod 状态和事件 | `kubectl describe pod dns-test-check -n default` | 节点: `node2/10.2.0.50`。`Events: Warning Failed to pull image ...` | 问题不仅发生在 `node1`，`node2` 也存在相同的镜像拉取失败模式，确认该问题是集群级别的网络问题 |
| e6 | Pod 状态和事件 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e` | `State: Waiting (Reason: CrashLoopBackOff)`。`Warning BackOff 118s (x321 over 71m) kubelet Back-off restarting failed container` | Pod 因启动失败持续重启，退出码未直接显示，但后续日志揭示了原因 |
| e7 | Pod 启动日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 容器在启动时检测到必须的环境变量 `APP_BOOT_MODE` 缺失，导致启动失败并退出 |

### 证据关联分析
- **证据 #1, #2, #3, #4, #5 印证**：这5个证据覆盖了3个命名空间、2个节点、多种公共镜像（`busybox`, `jessie-dnsutils`），错误信息均指向网络连接失败（`i/o timeout`, `connection reset by peer`）。这表明整个集群的出口网络存在严重问题。
- **证据 #6, #7 印证**：Pod 处于 `CrashLoopBackOff` + 日志明确提示 `missing required APP_BOOT_MODE`。可确认 Pod 代码逻辑正确识别了环境变量缺失并主动退出。
- **证据链结论**：集群存在两个独立性很强的问题：一是节点层网络不可连通外部镜像仓库，导致41个Pod无法创建；二是一个Pod因配置错误，导致启动后退出并持续重启。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 集群防火墙/网络策略配置 | critical | 无法确认出口阻断的具体原因（是企业防火墙、云商安全组还是网络设备ACL） |
| 容器运行时配置 (`/etc/containerd/config.toml` 等) | medium | 无法确认是否有镜像仓库代理(mirror)或HTTP代理(proxy)配置 |
| CrashLoopBackOff Pod 的 Deployment YAML | low | 无法确认 `APP_BOOT_MODE` 环境变量为何未定义或未通过 ConfigMap/Secret 注入 |

---

## 🎯 根因分析
### 因果链
**问题一：大规模镜像拉取失败 (ImagePullBackOff)**
```
┌───────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                              │
│ 集群节点（node1, node2）出口网络策略/防火墙阻断了对公共镜像仓库的HTTPS  │
│ 访问（docker.io的 registry-1.docker.io:443, docker.pkg.dev:443等）。    │
│ 具体表现为 TCP 连接 i/o timeout 与 connection reset by peer。          │
└───────────────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                              │
│ kubelet 无法从 registry-1.docker.io 建立TCP连接 →                               │
│ 无法下载任何指向该仓库的容器镜像（busybox, alpine, curl等）                      │
└───────────────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                              │
│ 所有访问 docker.io 的镜像拉取请求都因底层网络错误失败。                        │
└───────────────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                          │
│ 42个Pod（41个ImagePullBackOff + 1个ErrImagePull）分布在aiops-e2e,        │
│ default, mcp命名空间，全部阻塞在 Pending 状态。Pod事件中反复出现           │
│ ErrImagePull, BackOff, 以及网络错误详情。                                │
└───────────────────────────────────────────────────────────────────────┘
```

**问题二：Pod 配置启动失败 (CrashLoopBackOff)**
```
┌───────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                              │
│ Pod `rc-config-env-missing-5d9b8b766c-bq8pn` 的容器启动环境           │
│ 缺少必须的操作环境变量 `APP_BOOT_MODE`。                                 │
└───────────────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                              │
│ 应用启动代码检查到缺失 `APP_BOOT_MODE` 变量，触发初始化异常。             │
└───────────────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                              │
│ 应用进程主动退出（退出码42），因为无法满足启动前置条件。                      │
└───────────────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                          │
│ Pod 反复启动、失败、然后被 kubelet 重启，状态显示为 CrashLoopBackOff，      │
│ 日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`。    │
└───────────────────────────────────────────────────────────────────────┘
```
### 根因结论

**结论一（主问题）**：根据证据 #1, #2, #3, #4, #5，问题根源是**集群出口网络策略阻止了节点（node1, node2）到 `docker.io` 和 `docker.pkg.dev` 等外部镜像仓库的 HTTPS(443) 出站连接。** 这导致所有依赖这些外部仓库的镜像无法拉取，造成41个Pod进入 `ImagePullBackOff` 或 `ErrImagePull` 状态。

**结论二（独立问题）**：根据证据 #6, #7，问题根源是**Pod `rc-config-env-missing` 的部署配置缺少 `APP_BOOT_MODE` 环境变量**，导致应用启动失败并持续重启。

**置信度**：高 (95%)

- ✅ 真实 `kubectl describe` 和 `kubectl logs` 输出提供了确凿证据。
- ✅ 错误类型和分布（跨节点、跨镜像、跨命名空间）明确指向了网络层面的问题。
- ✅ 日志 `missing required APP_BOOT_MODE` 是导致 CrashLoopBackOff 的直接系统反馈。

---

## 🛠️ 修复建议
### 问题一：大规模镜像拉取失败（立即执行）

此问题的根本解决方案是允许节点访问外部镜像仓库。请选择一种最适合您的方案：

**1. [最优方案] 开放集群出口防火墙/网络策略**
请联系基础设施或网络管理员，确认并放行节点到 `registry-1.docker.io`, `registry.k8s.io`, `docker.pkg.dev` 等仓库的 443 端口出站流量。
*依据*：事件明确显示 `dial tcp ... i/o timeout` 和 `connection reset by peer`，表明流量被中间设备阻断。

**2. [备用方案] 配置集群内镜像仓库代理 (Mirror)**
在 `containerd` 或 `cri-o` 配置中添加镜像仓库的 mirror 配置，使 kubelet 从内部代理拉取镜像。
```toml
# /etc/containerd/config.toml 示例
[plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
  endpoint = ["https://your-internal-proxy"] 
```
*依据*：这是绕过公共网络问题、使用内部缓存的标准方案。

**3. [临时应急方案] 手动导入镜像并修改 Pod**
*此方案仅适用于少量、核心的容器，不推荐大规模使用。*
在节点上手动拉取（`docker pull`）或导入镜像，或者将 `imagePullPolicy` 设置为 `IfNotPresent`。
```bash
# 在 node1 和 node2 上执行
docker pull busybox:1.36.1
# 如果无法公网拉取，需先在有网络的机器上拉取，打包，再导入
# docker save busybox:1.36.1 -o busybox.tar
# 将 busybox.tar 复制到节点
# ctr -n k8s.io images import busybox.tar
```
*依据*：可以快速让已存在的Pod启动，但不解决根本问题。

### 问题二：Pod CrashLoopBackOff（可单独修复）
**1. [推荐] 使用 `kubectl set env` 命令注入环境变量**
```bash
kubectl set env deployment/rc-config-env-missing -n aiops-e2e APP_BOOT_MODE=<期望值>
```
*依据*：根据证据 #7，应用需要 `APP_BOOT_MODE` 变量。

**2. [排查] 检查部署 YAML 或 Helm Chart**
如果上述命令后 Pod 仍未恢复，请检查部署 `rc-config-env-missing` 的 YAML 文件或 Helm values，确认 `APP_BOOT_MODE` 是否被遗漏。
```bash
# 查看当前 deployment 的完整 YAML
kubectl get deployment rc-config-env-missing -n aiops-e2e -o yaml
```

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 检查网络修复效果 | `kubectl describe pod <any_pending_pod_name> -n <namespace>` | Pod Events 中不再出现 `Failed to pull image` 错误 |
| 2. 确认 Pod 启动 | `kubectl get pods -n <namespace> -o wide \| grep -E 'ImagePullBackOff\|Pending'` | `STATUS` 列从 `Pending` 或 `ImagePullBackOff` 变为 `Running` 或 `ContainerCreating` |
| 3. 验证Env修复 | `kubectl logs rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e --previous \| grep APP_BOOT_MODE` | 不再输出 `missing required APP_BOOT_MODE` 错误 |
| 4. 验证Pod稳定性 | `kubectl get pod rc-config-env-missing-5d9b8b766c-bq8pn -n aiops-e2e` | `STATUS: Running` 且 `RESTARTS` 不再增加 |

---

## ⚠️ 注意事项
- **问题优先级**：**问题一（网络/镜像拉取）** 影响范围达 42 个 Pod，是当前最紧急、影响最大的问题，应优先处理。问题二影响单个 Pod，可并行修复。
- **网络排查方向**：后续需重点排查节点出口的防火墙规则、企业网络代理、云厂商安全组、或 Kubernetes NetworkPolicy，以确定阻断的具体组件。
- **长期优化**：考虑在企业内部搭建私有镜像仓库（Harbor, Sonatype Nexus 等），并将所有公共镜像同步至内网仓库，可从根本上避免此类外部依赖问题。

---

## 📊 性能统计

├─ 总耗时: 2.7m
├─ 问题定位: 53.2s (32%) ✅
├─ 证据链采集: 43.3s (26%) ✅
├─ 根因分析: 32.1s (20%) ✅
├─ 汇总总结: 35.5s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 16 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-config-error
- **参考 Runbook**: pod-imagepull-failed, pod-config-error
- **工具调用**: 16 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
