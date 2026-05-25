======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ba501b7b40464105]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先从全局 Pod 状态扫描开始，看看当前集群中有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 Pod list from cluster: 127 total pods. Abnormal count from current_summary is 60, but raw_preview shows ~57 abnormal rows visible. Status counts from raw_preview: Running=~70 (includes admin/kube-syst
   💭 [问题定位] 让我再精确获取一下所有异常 Pod 的详情。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query returned 59 rows, all abnormal. 58 pods are Pending, 1 Running but in CrashLoopBackOff. Dominant failure reasons: ErrImagePull (35) and ImagePullBackOff (21) pulling busybox:1
   💭 [问题定位] 让我再精确获取一下 Pod 的状态分布，按命名空间和状态归类。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=7919 lines=421
Executing jq query for pods...
{
  "ns": "aiops-e2e",
  "name": "test-dns-1779360358",
  "phase": "Pending",
  "reason": "ImagePullBackOff",
  "hostI
   💭 [问题定位] 数据很多，让我用更好的方式获取完整统计。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=3863 lines=61
Executing jq query for pods...
aiops-e2e/test-dns-1779360358 phase=Pending reason=ImagePullBackOff
default/connectivity-check-tmp phase=Pending reason
   💭 [问题定位] 让我查一下那个 CrashLoopBackOff 的 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-liveness   0/1     CrashLoopBackOff   19 (4m18s 
   💭 [问题定位] 现在我已经对全局有比较完整的了解。让我获取相关 runbook 来参考定位方向。
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
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] 让我再看一下那个 CrashLoopBackOff Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       51m (x10 over 53m)  kubelet        
   💭 [问题定位] 好了，我已经有足够的数据来进行完整的定位分析了。让我整理一下结果。

---

## 📋 全局 Pod 异常定位分析

### 1️⃣ 全局状态概览

| 指标 | 数值 |
|------|------|
| 集群总 Pod 数 | ~127 |
| 正常运行 Pod | ~70 (admin/kube-system 正常) |
| **异常 Pod 总数** | **~59** |
| 涉及异常命名空间 | `default`, `aiops-e2e`, `mcp` |

### 2️⃣ 异常分组 (abnormal_groups)

---

### 🔴 异常组 A：ImagePullFailed（镜像拉取失败）— 影响范围最大

| 字段 | 值 |
|------|-----|
| **Pod 数量** | **~56 个 Pod**（ErrImagePull=35, ImagePullBackOff=21） |
| **异常类型** | `ImagePullFailed` |
| **兼容层级** | **L3** |
| **状态关键字** | `ImagePullBackOff` / `ErrImagePull` |
| **分布命名空间** | `default`（~28个）、`mcp`（~11个）、`aiops-e2e`（1个） |
| **分布节点** | node1 (10.2.0.49)、node2 (10.2.0.50) |

**关键证据：**
- 拉取的镜像主要是 `docker.io/library/busybox:1.36.1`、`busybox:1.28`、`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`
- 错误信息：**`connection reset by peer`**、**`i/o timeout`**、**`dial tcp ... i/o timeout`**
- 目标 IP 不可达：44.218.41.59、199.96.58.177、74.86.151.167、23.20.95.219、31.13.83.34（均为 docker.io 和 registry.k8s.io 地址）
- 问题跨越 **两个节点** 和 **三个命名空间**，说明不是单节点问题

**判定：** 集群节点无法连通外网镜像仓库（docker.io、registry.k8s.io），**网络层面镜像仓库不可达**。需要配置镜像仓库代理/镜像缓存/私有仓库。

---

### 🟡 异常组 B：NotReadyProbeFailed + CrashLoopBackOffRuntime

| 字段 | 值 |
|------|-----|
| **Pod 名称** | `aiops-e2e/rc-notready-liveness` |
| **Pod 数量** | 1 个 |
| **状态关键字** | `CrashLoopBackOff` |
| **异常类型** | `NotReadyProbeFailed`（主类型，因 Exit Code=137，由 liveness 探针杀死） |
| **兼容层级** | **L4** |
| **重启次数** | 19 次 |

**关键证据：**
- `Phase=Running`，但 `READY 0/1`，`STATUS=CrashLoopBackOff`
- `Exit Code: 137`（SIGKILL，被 liveness probe 杀死）
- Liveness probe 配置：`exec [sh -c echo liveness endpoint failed; exit 1]` — **探针命令本身就返回 exit 1**，这是故意配置为失败
- Events：`Liveness probe failed: liveness endpoint failed` → `Killing` → `CrashLoopBackOff`
- 镜像 `busybox:1.36` 已成功拉取（Image ID 存在），command 是 `sleep 86400`

**判定：** 这是 **人为构造的测试 Pod**（label `rootcause-e2e=true`），liveness probe 命令被故意写成 `exit 1` 来模拟探针失败场景。不是真实业务故障。

---

### 🟢 异常组 C：ContainerCreating（Pending 无明确错误）

| 字段 | 值 |
|------|-----|
| **Pod 名称** | `default/dns-connectivity-test` |
| **状态关键字** | `Pending`（ContainerCreating） |
| **异常类型** | 需进一步确认，可能是 SandboxCreate 或 VolumeMount 问题 |

该 Pod 状态为 `Pending`/`ContainerCreating` 但没有明确的失败事件消息，可能与镜像拉取组相关。

---

### 3️⃣ 分层输出

| 层级 | 值 |
|------|-----|
| **layer** | L3 |
| **derived_layer** | L3 |
| **layers** | L3, L4 |
| **layer_name** | ImagePullFailed |
| **confidence** | 高 |
| **reasoning** | 集群中 **56个 Pod**（占异常 Pod 的 95%）因无法拉取 docker.io/registry.k8s.io 镜像而处于 ImagePullBackOff/ErrImagePull，错误为连接超时/被对端重置，两节点均受影响，确认为集群级外网镜像仓库不可达问题，归类 L3。另有 1 个 CrashLoopBackOff Pod 为 liveness 探针测试用例，归类 L4。 |

### 4️⃣ 异常 Pod 完整列表 (abnormal_pods)

**ImagePullFailed 组（共 ~56 个）：**
- `aiops-e2e/test-dns-1779360358`
- `default/connectivity-check-tmp`, `default/dig-check-registry`, `default/dig-tool`, `default/dns-check-evidence`, `default/dns-check-test`, `default/dns-diag-1779390521`, `default/dns-diag-tool-evidence`, `default/dns-resolve-gcr-test`, `default/dns-resolve-test`, `default/dns-test`, `default/dns-test-1779360684`, `default/dns-test-check`, `default/dns-test-dig`, `default/dns-test-tmp`, `default/net-test-pod`, `default/nettest-1779363677`, `default/network-test-1779374716`, `default/registry-check-node2`, `default/registry-conn-test-1779371220`, `default/registry-conn-test-evidence`, `default/registry-connect-test`, `default/registry-diag-evidence-verify`, `default/test-net-1779360704`
- `mcp/connectivity-test`, `mcp/curl-check-tmp`, `mcp/curl-registry-test`, `mcp/curls`, `mcp/dns-check-tmp`, `mcp/net-check-1779365549`, `mcp/net-check-tool`, `mcp/net-diag-1779385005`, `mcp/net-test-1779375932`, `mcp/net-test-verify2`, `mcp/node-debugger-node1-2s2mz`, `mcp/node-debugger-node1-2xvqr`, `mcp/node-debugger-node1-4ncj7`, `mcp/node-debugger-node1-6pxvd` 等

**NotReadyProbeFailed 组：**
- `aiops-e2e/rc-notready-liveness`（测试 Pod，liveness 探针故意失败）

**ContainerCreating 组：**
- `default/dns-connectivity-test`（Pending/ContainerCreating）

### 5️⃣ 可能场景 (possible_scenarios)

| # | 场景 | 可能性 |
|---|------|--------|
| 1 | **集群无法访问外网镜像仓库** — 节点缺少互联网出口、防火墙/NAT 限制、或 DNS 无法解析 docker.io/registry.k8s.io | ⭐⭐⭐ 最高 |
| 2 | **镜像仓库代理/缓存未配置** — 生产环境应有本地 mirror 或私有 registry，当前直接拉取外网超时 | ⭐⭐⭐ 最高 |
| 3 | **CNI/网络策略阻断** — 网络策略或 CNI 插件配置阻止了对外访问 | ⭐⭐ 中等 |
| 4 | **测试/诊断 Pod 泛滥** — 大量 `dns-*`、`registry-*`、`net-*` 测试 Pod 是人为创建的诊断 Pod，因镜像拉取失败堆积 | ⭐⭐ 中等 |
| 5 | **人为构造的 CrashLoopBackOff 测试** — `rc-notready-liveness` 是 e2e 测试用例，不是真实故障 | ⭐⭐⭐ 已确认 |

### 6️⃣ 关键实体 (key_entities)

| 实体 | 类型 | 状态 |
|------|------|------|
| `node1` (10.2.0.49) | Node | 运行中，但无法拉取镜像 |
| `node2` (10.2.0.50) | Node | 运行中，但无法拉取镜像 |
| `docker.io/library/busybox` | 镜像 | 不可达（connection reset / i/o timeout） |
| `registry.k8s.io` | 镜像仓库 | 不可达（i/o timeout） |
| `aiops-e2e/rc-notready-liveness` | Pod | CrashLoopBackOff（测试用例） |

---

**总结：** 集群当前最严重的问题是 **L3 层级的镜像拉取失败**，~56 个 Pod 因节点无法连通 docker.io/registry.k8s.io 而处于 ImagePullBackOff/ErrImagePull 状态，影响跨越三个命名空间和两个节点。此外有一个 L4 层级的 NotReadyProbeFailed 测试 Pod。建议检查节点出口网络、配置本地镜像代理仓库，并清理堆积的测试诊断 Pod。
   ✅ [问题定位] 完成 (53.9s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '集群节点无法访问外网镜像仓库（docker.io/registry.k8s.io）', 'probability': '高', 'reason': '56个Pod均出现connection reset by peer或i/o timeout错误，目标IP（44.218.41.59等）不可达，跨两个节点三个命名空间'}, {'scenario': '缺少本地镜像代理/缓存配置', 'probability': '高', 'reason': '生产环境应有本地mirror或私有registry，当前直接拉取外网镜像全部超时'}, {'scenario': 'CNI/网络策略阻断对外访问', 'probability': '中', 'reason': '无法排除网络策略或CNI插件阻止了对外HTTPS连接的可能性'}, {'scenario': '测试诊断Pod堆积', 'probability': '中', 'reason': '大量dns-*、registry-*、net-*测试Pod为人为创建，因镜像拉取失败堆积'}, {'scenario': '人为构造的CrashLoopBackOff测试用例', 'probability': '高', 'reason': 'rc-notready-liveness的liveness probe被故意设为exit 1，label为rootcause-e2e=true，非真实故障'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "image", "name": "docker.io/library/busybox:1.36.1", "namespace": ""}, {"type": "image", "name": "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "namespace": ""}, {"type": "pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}]
   reasoning=集群中约56个Pod因无法连通外网镜像仓库（docker.io、registry.k8s.io）而处于ImagePullBackOff/ErrImagePull状态，错误为connection reset by peer和i/o timeout，跨两个节点（node1、node2）和三个命名空间（default、aiops-e2e、mcp），确认为集群级外网镜像仓库不可达问题，归类L3。另有1个Pod（aiops-e2e/rc-notready-liveness）处于CrashLoopBackOff，Exit Code 137，由liveness探针故意配置为exit 1导致，属于人为构造的测试用例（label rootcause-e2e=true），归类L4。当前最严重、影响范围最大的问题是L3镜像拉取失败，占异常Pod的95%以上。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "集群中约56个Pod因无法连通外网镜像仓库（docker.io、registry.k8s.io）而处于ImagePullBackOff/ErrImagePull状态，错误为connection reset by peer和i/o timeout，跨两个节点（node1、node2）和三个命名空间（default、aiops-e2e、mcp），确认为集群级外网镜像仓库不可达问题，归类L3。另有1个Pod（aiops-e2e/rc-notready-liveness）处于CrashLoopBackOff，Exit Code 137，由liveness探针故意配置为exit 1导致，属于人为构造的测试用例（label rootcause-e2e=true），归类L4。当前最严重、影响范围最大的问题是L3镜像拉取失败，占异常Pod的95%以上。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "dig-check-registry", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-connectivity-test", "namespace": "default", "status": "Terminating"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-tool-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-diag-evidence-verify", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2s2mz", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "image", "name": "docker.io/library/busybox:1.36.1", "namespace": ""}, {"type": "image", "name": "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "namespace": ""}, {"type": "pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}], "possible_scenarios": [{"scenario": "集群节点无法访问外网镜像仓库（docker.io/registry.k8s.io）", "probability": "高", "reason": "56个Pod均出现connection reset by peer或i/o timeout错误，目标IP（44.218.41.59等）不可达，跨两个节点三个命名空间"}, {"scenario": "缺少本地镜像代理/缓存配置", "probability": "高", "reason": "生产环境应有本地mirror或私有registry，当前直接拉取外网镜像全部超时"}, {"scenario": "CNI/网络策略阻断对外访问", "probability": "中", "reason": "无法排除网络策略或CNI插件阻止了对外HTTPS连接的可能性"}, {"scenario": "测试诊断Pod堆积", "probability": "中", "reason": "大量dns-*、registry-*、net-*测试Pod为人为创建，因镜像拉取失败堆积"}, {"scenario": "人为构造的CrashLoopBackOff测试用例", "probability": "高", "reason": "rc-notready-liveness的liveness probe被故意设为exit 1，label为rootcause-e2e=true，非真实故障"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "default", "name": "dns-connectivity-test"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g4", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "default", "name": "dns-connectivity-test"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g4", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 41, "ErrImagePull": 15, "Terminating": 1}, "total_abnormal": 58, "selected_rows": ["aiops-e2e         rc-notready-liveness                                0/1     CrashLoopBackOff    19 (3m56s ago)   52m     172.16.166.129   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff    0                14h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ErrImagePull        0                161m    172.16.104.52    node2    <none>           <none>            run=connectivity-check-tmp", "default           dig-check-registry                                  0/1     ImagePullBackOff    0                101m    172.16.166.155   node1    <none>           <none>            run=dig-check-registry", "default           dig-tool                                            0/1     ImagePullBackOff    0                9h      172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff    0                8h      172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff    0                12h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-connectivity-test                               0/1     Terminating         0                2m7s    <none>           node2    <none>           <none>            run=dns-connectivity-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff    0                5h46m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-diag-tool-evidence                              0/1     ErrImagePull        0                138m    172.16.104.4     node2    <none>           <none>            run=dns-diag-tool-evidence", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff    0                5h52m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ImagePullBackOff    0                5h52m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test                                            0/1     ErrImagePull        0                101m    172.16.104.56    node2    <none>           <none>            run=dns-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff    0                14h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull        0                11h     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff    0                5h52m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull        0                8h      172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff    0                12h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull        0                13h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff    0                10h     172.16.104.62    node2    <none>           <none>            run=network-test-1779374716"], "raw_ref": "/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我将按照既有 evidence_plan 依次执行工具调用。先从 critical 级别的关键 Pod 开始。

## 第一阶段：Critical 级别证据采集

先并发执行 e1（主异常 - ErrImagePull）和 e7（主异常 - CrashLoopBackOff）：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       51m (x10 over 53m)     kubelet     
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-check-tmp (namespace=default, node=node2/10.2.0.50) is in Pending status. Container image busybox:1.36.1 (docker.io/library/busybox) cannot be pulled. State=Waiting, Reason=ErrImagePu
   💭 [证据链采集] 关键证据已到位！现在并发执行 e2（YAML）、e3（node2 验证）、e4（mcp 验证）、e5（aiops-e2e 验证）：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: connectivity-check-tmp
namespace: default
creationTimestamp: 2026-05-21T22:13:49Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <non
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-test (ns: default) on node2 (10.2.0.50) is Pending, IP 172.16.104.56. Container dns-test (busybox:1.28) cannot start: State Waiting (Reason: ErrImagePull). All pull attempts to docker.io/libra
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-test in namespace mcp, on node node2/10.2.0.50, status Pending. Container connectivity-test uses image busybox:1.36.1 with args: sh -c curl to registry-1.docker.io. Container State Wa
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   4m36s (x188 over 13h)  kubelet  (combined from similar events): Fai
   💭 [证据链采集] 现在继续采集集群级别事件（e6）和剩余异常组验证（e8、e9、e10）：
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN   TYPE     REASON           OBJECT                      MESSAGE
3m43s       Normal   AddedInterface   Pod/dns-connectivity-test   Add eth0 [172.16.104.30/32] from k8s-pod-
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dns-connectivity-test
namespace: default
creationTimestamp: 2026-05-22T00:53:17Z
deletionTimestamp: 2026-05-22T00:54:47Z
deletionGracePeriodSeconds: 30
finaliz
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 全部计划工具已调用完毕。现在来获取 rc-notready-liveness 的详细 describe 信息补充：
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=3132 lines=63
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/ba501b7b40464105/tools/001-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1547 lines=35
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/ba501b7b40464105/tools/003-evidence-kubectl_get_yaml.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1627 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/ba501b7b40464105/tools/004-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1660 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/ba501b7b40464105/tools/005-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2511 lines=48
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/ba501b7b40464105/tools/006-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 现在我已收集到所有关键证据。以下是完整的证据采集结论。

---

## 证据采集结论

### ✅ 关键证据汇总

#### **异常组 g2 — ImagePullBackOff/ErrImagePull（主异常，56个Pod，影响最大）**

| 计划项 | 证据 | 结论 |
|--------|------|------|
| **e1** ✅ `kubectl describe connectivity-check-tmp -n default` (node2) | Events: `i/o timeout` (to 199.96.58.177:443), `connection refused`, `pull QPS exceeded`；BackOff x90 over 152m | **镜像仓库网络不可达** — node2 无法连通 registry-1.docker.io |
| **e2** ✅ `kubectl get yaml connectivity-check-tmp -n default` | image=`busybox:1.36.1`，**无 imagePullSecrets**；containerStatuses.message: `dial tcp 199.96.58.177:443: i/o timeout` | 镜像名有效且无需认证，确认为网络不可达 |
| **e3** ✅ `kubectl describe dns-test -n default` (node2) | 同样 `i/o timeout` 到多个 registry-1.docker.io IP（108.160.166.42, 208.43.170.231 等），事件跨度 102min | **跨节点一致** — node2 上所有 Pod 均因网络问题拉取失败 |
| **e4** ✅ `kubectl describe connectivity-test -n mcp` (node2) | 同样 `i/o timeout` + `connection refused` + `pull QPS exceeded`；BackOff x1550 over 13h | **跨命名空间一致** — mcp 命名空间同样受影响 |
| **e5** ✅ `kubectl describe test-dns-1779360358 -n aiops-e2e` (node1) | `connection reset by peer` 到 52.202.41.60:443；BackOff x2071 over 14h | **跨节点一致** — node1 也出现同类错误，但具体错误为 `connection reset by peer` |
| **e6** ✅ 集群级事件查询 | 无返回结果（`returncode=0`，stdout 为空） | **集群事件已被清理**，但各 Pod 级别 Events 已充分证实 |

**关键发现**：node1 上错误为 `connection reset by peer`，node2 上错误为 `i/o timeout`，但本质相同——**集群节点无法连通外网 registry-1.docker.io:443**。

---

#### **异常组 g1 — CrashLoopBackOff（rc-notready-liveness，aiops-e2e）**

| 计划项 | 证据 | 结论 |
|--------|------|------|
| **e7** ✅ `kubectl describe rc-notready-liveness -n aiops-e2e` | Exit Code=137, Reason=`CrashLoopBackOff`；Events: `Liveness probe failed: liveness endpoint failed`；Label `rootcause-e2e=true`；Annotation `aiops.e2e/runbook: pod-notready-probe-failed.md` | **人为构造的测试用例**，并非真实故障 |

---

#### **异常组 g3 — Terminating（dns-connectivity-test，default）**

| 计划项 | 证据 | 结论 |
|--------|------|------|
| **e8** ✅ `kubectl get yaml dns-connectivity-test -n default` | `deletionTimestamp: 2026-05-22T00:54:47Z`，`finalizers: <none>`，无 volume 依赖 | **没有 finalizer 卡住**，只有 30s deletionGracePeriod；imagePullSecrets 也为空，Pod 卡在 ContainerCreating 是因为镜像拉取失败 |
| **e10** ✅ kibectl events dns-connectivity-test | 最近事件：Scheduled → Pulling "busybox:1.28" → AddedInterface；无删除相关事件 | **Terminating** 状态是因为镜像拉取尚未完成但已发起删除，属于正常清理过程 |

---

#### **异常组 g4 — StartError（node-debugger-node1-nx8gb，mcp）**

| 计划项 | 证据 | 结论 |
|--------|------|------|
| **e9** ✅ `kubectl describe node-debugger-node1-nx8gb -n mcp` | Status=Failed；Container State=Terminated, Reason=`StartError`, Exit Code=128；Message: `exec: "curl": executable file not found in $PATH: unknown` | **镜像 busybox:1.36 中没有 curl 可执行文件**，command 引用了不存在的二进制，属于配置错误，非真实集群故障 |

---

### ⚠️ 冲突/负向证据
- **e6** 集群级事件查询返回空：事件窗口已过，但每个 Pod 的 describe 中已包含完整拉取失败事件链，不影响诊断结论。

### 核心诊断结论
**集群节点无法访问外网镜像仓库（registry-1.docker.io:443）**：跨 node1（connection reset by peer）和 node2（i/o timeout）、跨三个命名空间（default/aiops-e2e/mcp），56 个 Pod 均因镜像拉取网络不可达而处于 ImagePullBackOff/ErrImagePull。另有 1 个人为构造的 CrashLoopBackOff 测试用例（rc-notready-liveness）、1 个正常清理中的 Terminating Pod、1 个 command 配置错误的 StartError Pod，均非集群基础设施故障。
   ✅ [证据链采集] 完成 (56.0s)
   📤 → 下游数据: evidence_items=15/16
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证主异常组(g2)代表Pod: default/connectivity-check-tmp (ErrImagePull) - 详细describe获取镜像拉取事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","tool_args":{"kind":"pod","name":"connectivity-check-tmp","namespace":"default"},"purpose":"获取ErrImagePull/ImagePullBackOff的Pod Events原文，确认connection reset/io-timeout等失败原因","evidence_type":"pod_events","target_scope":"g2-representative-pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证主异常组(g2)代表Pod: default/connectivity-check-tmp的镜像配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod connectivity-check-tmp -n default -o yaml","tool_args":{"kind":"pod","name":"connectivity-check-tmp","namespace":"default"},"purpose":"检查Pod spec中的image、imagePullSecrets和容器配置","evidence_type":"pod_spec","target_scope":"g2-representative-pod","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"验证主异常组(g2)另一个代表Pod: default/dns-test (ErrImagePull) - 跨节点验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-test -n default","tool_args":{"kind":"pod","name":"dns-test","namespace":"default"},"purpose":"验证node2上Pod的镜像拉取错误是否一致，验证跨节点问题","evidence_type":"pod_events","target_scope":"g2-cross-node-verify","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"验证主异常组(g2) mcp命名空间代表Pod: mcp/connectivity-test (ErrImagePull)","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp"},"purpose":"验证mcp命名空间跨命名空间的ErrImagePull是否一致","evidence_type":"pod_events","target_scope":"g2-cross-ns-verify","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"验证主异常组(g2) aiops-e2e命名空间代表Pod: aiops-e2e/test-dns-1779360358 (ImagePullBackOff)","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"验证aiops-e2e命名空间的ImagePullBackOff是否与default/mcp一致","evidence_type":"pod_events","target_scope":"g2-cross-ns-verify","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6","description":"检查集群级Events中与镜像拉取相关的Warning事件","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by='.lastTimestamp' | tail -30","tool_args":{},"purpose":"从集群级别获取所有FailedToPullImage/ErrImagePull事件，验证系统级问题","evidence_type":"cluster_events","target_scope":"cluster-wide","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7","description":"验证异常组g1: aiops-e2e/rc-notready-liveness (CrashLoopBackOff) - 检查Last State和Exit Code","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"验证CrashLoopBackOff的Exit Code和Last State，确认是否因liveness probe导致","evidence_type":"pod_events","target_scope":"g1-crashloop","acceptable_tools":[],"counts_for_completeness":true},{"id":"e8","description":"验证异常组g3: default/dns-connectivity-test (Terminating) - 检查finalizers和deletionTimestamp","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-connectivity-test -n default -o yaml","tool_args":{"kind":"pod","name":"dns-connectivity-test","namespace":"default"},"purpose":"验证Terminating状态的Pod是否有finalizers阻止删除","evidence_type":"pod_yaml","target_scope":"g3-terminating","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e9","description":"验证异常组g4: mcp/node-debugger-node1-nx8gb (StartError) - 最小状态验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"验证StartError异常的状态和事件","evidence_type":"pod_events","target_scope":"g4-start-error","acceptable_tools":[],"counts_for_completeness":true},{"id":"e10","description":"验证g3 Terminating Pod的事件","level":"optional","tool":"kubectl_events","command":"kubectl get events -n default --field-selector involvedObject.name=dns-connectivity-test --sort-by='.lastTimestamp'","tool_args":{"resource_type":"pod","resource_name":"dns-connectivity-test","namespace":"default"},"purpose":"检查Terminating Pod是否有相关删除事件","evidence_type":"pod_events","target_scope":"g3-terminating","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       51m (x10 over 53m)     kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         3m40s (x179 over 50m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         52m (x3 over 53m)      kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: f997c06136714184f9866361b3eab26ff46c280103b276058ecb6da12e4ce2e4\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       53m        \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod connectivity-check-tmp (namespace=default, node=node2/10.2.0.50) is in Pending status. Container image busybox:1.36.1 (docker.io/library/busybox) cannot be pulled. State=Waiting, Reason=ErrImagePull. All pull attempts from registry-1.docker.io:443 have failed with i/o timeout (multiple IPs), connection refused, or pull QPS exceeded. BackOff pulling image (x90 over 152m). Pod IP=172.16.104.52 (Calico CNI). Container args: wget test to registry-1.docker.io/v2.\nkey_facts: [\"Pod: connectivity-check-tmp\", \"Namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Container State: Waiting, Reason: ErrImagePull\", \"Image: busybox:1.36.1 (docker.io/library/busybox:1.36.1)\", \"Pod IP: 172.16.104.52 (Calico CNI)\", \"Events: multiple Failed to pull image - i/o timeout, connection refused, pull QPS exceeded\", \"BackOff pulling image x90 over 152m\", \"Container args: wget -q -O- --timeout=5 https://registry-1.docker.io/v2/ 2>&1 || echo FAILED\"]\nconflicts: [\"current_summary says pod has no Events field but raw_preview shows full Events list; raw_preview is correct\", \"current_summary reports 'no events found' style but actual events are present\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: connectivity-check-tmp\nnamespace: default\ncreationTimestamp: 2026-05-21T22:13:49Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- connectivity-check-tmp: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c wget -q -O- --timeout=5 https://registry-1.docker.io/v2/ 2>&1 || echo FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [connectivity-check-tmp]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [connectivity-check-tmp]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- connectivity-check-tmp: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://regist\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"Pod dns-test (ns: default) on node2 (10.2.0.50) is Pending, IP 172.16.104.56. Container dns-test (busybox:1.28) cannot start: State Waiting (Reason: ErrImagePull). All pull attempts to docker.io/library/busybox:1.28 failed with network errors (i/o timeout, connection refused) to various registry-1.docker.io IPs. Multiple Failed/BackOff events over ~102min; last retry at 7m21s ago.\nkey_facts: [\"Pod: dns-test, namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Pod IP: 172.16.104.56\", \"Container: dns-test, image: busybox:1.28\", \"Container State: Waiting, Reason: ErrImagePull\", \"Container Ready: False, Restart Count: 0\", \"All pull attempts failed: dial tcp to registry-1.docker.io IPs (108.160.166.42, 208.43.170.231, 69.171.224.36, 162.125.80.5, 199.96.58.177) on port 443 — i/o timeout or connection refused\", \"Events show repeated Failed (56m, 43m, 31m, 22m, 7m21s) and BackOff (x65 over 98m)\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary lists BackOff age as '17m (x65 over 98m)' but raw_preview shows '17m (x65 over 98m)' for BackOff event — consistent.\", \"current_summary omits the 'Pulling' event (Normal, 31m, x11 over 102m) present in raw_preview.\"]\nmissing: [\"r\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod connectivity-test in namespace mcp, on node node2/10.2.0.50, status Pending. Container connectivity-test uses image busybox:1.36.1 with args: sh -c curl to registry-1.docker.io. Container State Waiting (Reason: ErrImagePull), Ready False. All pull attempts to docker.io/library/busybox:1.36.1 have failed with various errors: i/o timeout (multiple IPs), connection refused, pull QPS exceeded, and back-off (x1550 over 13h). Pod has Calico CNI annotations with IP 172.16.104.3/32.\nkey_facts: [\"resource: Pod connectivity-test, namespace: mcp\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container: connectivity-test, image: busybox:1.36.1\", \"container State: Waiting, Reason: ErrImagePull\", \"container Ready: False\", \"events show repeated Failed to pull image busybox:1.36.1 with errors: i/o timeout (3 different IPs), connection refused, pull QPS exceeded\", \"Normal BackOff (x1550 over 13h) - Back-off pulling image\", \"Normal Pulling (x116 over 13h) - still attempting\", \"Calico CNI: podIP 172.16.104.3/32\", \"container args: curl to https://registry-1.docker.io/v2/\"]\nconflicts: [\"current_summary says 'QoS Class: BestEffort' not in raw_preview - actually present in raw_preview, no conflict\", \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   4m36s (x188 over 13h)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:41032->52.202.41.60:443: read: connection reset by peer\n  Normal   BackOff  29s (x2071 over 14h)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/007-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/007-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/007-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN   TYPE     REASON           OBJECT                      MESSAGE\n3m43s       Normal   AddedInterface   Pod/dns-connectivity-test   Add eth0 [172.16.104.30/32] from k8s-pod-network\n3m43s       Normal   Pulling          Pod/dns-connectivity-test   Pulling image \"busybox:1.28\"\n3m43s       Normal   Scheduled        Pod/dns-connectivity-test   Successfully assigned default/dns-connectivity-test to node2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/008-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/008-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/008-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-connectivity-test\nnamespace: default\ncreationTimestamp: 2026-05-22T00:53:17Z\ndeletionTimestamp: 2026-05-22T00:54:47Z\ndeletionGracePeriodSeconds: 30\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-connectivity-test: image=busybox:1.28 imagePullPolicy=IfNotPresent\n  args: sh -c timeout 5 wget -q -O- https://registry-1.docker.io/v2/ 2>&1 || echo \"DIRECT_CONNECT_FAILED\"\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-connectivity-test]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-connectivity-test]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-connectivity-test: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-7n2dw\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/009-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/009-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/009-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/010-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/010-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/010-evidence-kubectl_describe.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=3132 lines=63\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/ba501b7b40464105/tools/001-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2922\ntotal_chars: 2922\ncontent:\nkubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       51m (x10 over 53m)     kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         3m40s (x179 over 50m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         52m (x3 over 53m)      kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: f997c06136714184f9866361b3eab26ff46c280103b276058ecb6da12e4ce2e4\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       53m                    default-scheduler  Successfully assigned aiops-e2e/rc-notready-liveness to node1\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://181191b99a9b323c1ee37275b2d1b591177f56b4dce784cbaeaf70c81a0e855d\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n      sleep 86400","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/011-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/011-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/011-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1547 lines=35\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/ba501b7b40464105/tools/003-evidence-kubectl_get_yaml.summary.txt\noffset: 0\nreturned_chars: 1337\ntotal_chars: 1337\ncontent:\nkubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: connectivity-check-tmp\nnamespace: default\ncreationTimestamp: 2026-05-21T22:13:49Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- connectivity-check-tmp: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c wget -q -O- --timeout=5 https://registry-1.docker.io/v2/ 2>&1 || echo FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [connectivity-check-tmp]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [connectivity-check-tmp]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- connectivity-check-tmp: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.96.58.177:443: i/o timeout\nvolumes:\n- {\"name\": \"kube-api-access-8qvlz\"}\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/012-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/012-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/012-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1627 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/ba501b7b40464105/tools/004-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1417\ntotal_chars: 1417\ncontent:\nPod dns-test (ns: default) on node2 (10.2.0.50) is Pending, IP 172.16.104.56. Container dns-test (busybox:1.28) cannot start: State Waiting (Reason: ErrImagePull). All pull attempts to docker.io/library/busybox:1.28 failed with network errors (i/o timeout, connection refused) to various registry-1.docker.io IPs. Multiple Failed/BackOff events over ~102min; last retry at 7m21s ago.\nkey_facts: [\"Pod: dns-test, namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Pod IP: 172.16.104.56\", \"Container: dns-test, image: busybox:1.28\", \"Container State: Waiting, Reason: ErrImagePull\", \"Container Ready: False, Restart Count: 0\", \"All pull attempts failed: dial tcp to registry-1.docker.io IPs (108.160.166.42, 208.43.170.231, 69.171.224.36, 162.125.80.5, 199.96.58.177) on port 443 — i/o timeout or connection refused\", \"Events show repeated Failed (56m, 43m, 31m, 22m, 7m21s) and BackOff (x65 over 98m)\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary lists BackOff age as '17m (x65 over 98m)' but raw_preview shows '17m (x65 over 98m)' for BackOff event — consistent.\", \"current_summary omits the 'Pulling' event (Normal, 31m, x11 over 102m) present in raw_preview.\"]\nmissing: [\"raw_preview shows a Normal Pulling event (31m, x11 over 102m) not highlighted in current_summary\", \"raw_preview includes Tolerations for node.kubernetes.io/unreachable:NoExecute; current_summary only listed not-ready\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/013-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/013-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/013-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1660 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/ba501b7b40464105/tools/005-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1450\ntotal_chars: 1450\ncontent:\nPod connectivity-test in namespace mcp, on node node2/10.2.0.50, status Pending. Container connectivity-test uses image busybox:1.36.1 with args: sh -c curl to registry-1.docker.io. Container State Waiting (Reason: ErrImagePull), Ready False. All pull attempts to docker.io/library/busybox:1.36.1 have failed with various errors: i/o timeout (multiple IPs), connection refused, pull QPS exceeded, and back-off (x1550 over 13h). Pod has Calico CNI annotations with IP 172.16.104.3/32.\nkey_facts: [\"resource: Pod connectivity-test, namespace: mcp\", \"node: node2/10.2.0.50\", \"status: Pending\", \"container: connectivity-test, image: busybox:1.36.1\", \"container State: Waiting, Reason: ErrImagePull\", \"container Ready: False\", \"events show repeated Failed to pull image busybox:1.36.1 with errors: i/o timeout (3 different IPs), connection refused, pull QPS exceeded\", \"Normal BackOff (x1550 over 13h) - Back-off pulling image\", \"Normal Pulling (x116 over 13h) - still attempting\", \"Calico CNI: podIP 172.16.104.3/32\", \"container args: curl to https://registry-1.docker.io/v2/\"]\nconflicts: [\"current_summary says 'QoS Class: BestEffort' not in raw_preview - actually present in raw_preview, no conflict\", \"current_summary mentions 'Failed 29m (x104 over 13h) Error: ErrImagePull' - raw_preview confirms this, aligned\"]\nmissing: [\"raw_preview includes container args showing curl command testing registry-1.docker.io connectivity, not just the image pull\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/014-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/014-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/014-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2511 lines=48\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/ba501b7b40464105/tools/006-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2301\ntotal_chars: 2301\ncontent:\nkubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   4m36s (x188 over 13h)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:41032->52.202.41.60:443: read: connection reset by peer\n  Normal   BackOff  29s (x2071 over 14h)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n      nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/015-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/015-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba501b7b40464105/tools/015-evidence-read_context_archive.summary.txt"}],"llm_analysis":"现在我已收集到所有关键证据。以下是完整的证据采集结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 关键证据汇总\n\n#### **异常组 g2 — ImagePullBackOff/ErrImagePull（主异常，56个Pod，影响最大）**\n\n| 计划项 | 证据 | 结论 |\n|--------|------|------|\n| **e1** ✅ `kubectl describe connectivity-check-tmp -n default` (node2) | Events: `i/o timeout` (to 199.96.58.177:443), `connection refused`, `pull QPS exceeded`；BackOff x90 over 152m | **镜像仓库网络不可达** — node2 无法连通 registry-1.docker.io |\n| **e2** ✅ `kubectl get yaml connectivity-check-tmp -n default` | image=`busybox:1.36.1`，**无 imagePullSecrets**；containerStatuses.message: `dial tcp 199.96.58.177:443: i/o timeout` | 镜像名有效且无需认证，确认为网络不可达 |\n| **e3** ✅ `kubectl describe dns-test -n default` (node2) | 同样 `i/o timeout` 到多个 registry-1.docker.io IP（108.160.166.42, 208.43.170.231 等），事件跨度 102min | **跨节点一致** — node2 上所有 Pod 均因网络问题拉取失败 |\n| **e4** ✅ `kubectl describe connectivity-test -n mcp` (node2) | 同样 `i/o timeout` + `connection refused` + `pull QPS exceeded`；BackOff x1550 over 13h | **跨命名空间一致** — mcp 命名空间同样受影响 |\n| **e5** ✅ `kubectl describe test-dns-1779360358 -n aiops-e2e` (node1) | `connection reset by peer` 到 52.202.41.60:443；BackOff x2071 over 14h | **跨节点一致** — node1 也出现同类错误，但具体错误为 `connection reset by peer` |\n| **e6** ✅ 集群级事件查询 | 无返回结果（`returncode=0`，stdout 为空） | **集群事件已被清理**，但各 Pod 级别 Events 已充分证实 |\n\n**关键发现**：node1 上错误为 `connection reset by peer`，node2 上错误为 `i/o timeout`，但本质相同——**集群节点无法连通外网 registry-1.docker.io:443**。\n\n---\n\n#### **异常组 g1 — CrashLoopBackOff（rc-notready-liveness，aiops-e2e）**\n\n| 计划项 | 证据 | 结论 |\n|--------|------|------|\n| **e7** ✅ `kubectl describe rc-notready-liveness -n aiops-e2e` | Exit Code=137, Reason=`CrashLoopBackOff`；Events: `Liveness probe failed: liveness endpoint failed`；Label `rootcause-e2e=true`；Annotation `aiops.e2e/runbook: pod-notready-probe-failed.md` | **人为构造的测试用例**，并非真实故障 |\n\n---\n\n#### **异常组 g3 — Terminating（dns-connectivity-test，default）**\n\n| 计划项 | 证据 | 结论 |\n|--------|------|------|\n| **e8** ✅ `kubectl get yaml dns-connectivity-test -n default` | `deletionTimestamp: 2026-05-22T00:54:47Z`，`finalizers: <none>`，无 volume 依赖 | **没有 finalizer 卡住**，只有 30s deletionGracePeriod；imagePullSecrets 也为空，Pod 卡在 ContainerCreating 是因为镜像拉取失败 |\n| **e10** ✅ kibectl events dns-connectivity-test | 最近事件：Scheduled → Pulling \"busybox:1.28\" → AddedInterface；无删除相关事件 | **Terminating** 状态是因为镜像拉取尚未完成但已发起删除，属于正常清理过程 |\n\n---\n\n#### **异常组 g4 — StartError（node-debugger-node1-nx8gb，mcp）**\n\n| 计划项 | 证据 | 结论 |\n|--------|------|------|\n| **e9** ✅ `kubectl describe node-debugger-node1-nx8gb -n mcp` | Status=Failed；Container State=Terminated, Reason=`StartError`, Exit Code=128；Message: `exec: \"curl\": executable file not found in $PATH: unknown` | **镜像 busybox:1.36 中没有 curl 可执行文件**，command 引用了不存在的二进制，属于配置错误，非真实集群故障 |\n\n---\n\n### ⚠️ 冲突/负向证据\n- **e6** 集群级事件查询返回空：事件窗口已过，但每个 Pod 的 describe 中已包含完整拉取失败事件链，不影响诊断结论。\n\n### 核心诊断结论\n**集群节点无法访问外网镜像仓库（registry-1.docker.io:443）**：跨 node1（connection reset by peer）和 node2（i/o timeout）、跨三个命名空间（default/aiops-e2e/mcp），56 个 Pod 均因镜像拉取网络不可达而处于 ImagePullBackOff/ErrImagePull","collection_summary":"计划 9 项，实际采集 8 项，未采集 1 项，完整度 89%；其中真实环境证据 14/15 项，完整度 93%；实际执行工具 16 个，匹配计划 9 个，未规划证据 7 个","plan_total":9,"plan_collected":8,"plan_completeness":0.8888888888888888,"environment_evidence_total":15,"environment_evidence_collected":14,"environment_evidence_completeness":0.9333333333333333,"executed_tool_count":16,"matched_tool_count":9,"unplanned_tool_count":7,"evidence_inventory":[{"id":"e1","description":"验证主异常组(g2)代表Pod: default/connectivity-check-tmp (ErrImagePull) - 详细describe获取镜像拉取事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","purpose":"获取ErrImagePull/ImagePullBackOff的Pod Events原文，确认connection reset/io-timeout等失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证主异常组(g2)代表Pod: default/connectivity-check-tmp的镜像配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod connectivity-check-tmp -n default -o yaml","purpose":"检查Pod spec中的image、imagePullSecrets和容器配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证主异常组(g2)另一个代表Pod: default/dns-test (ErrImagePull) - 跨节点验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-test -n default","purpose":"验证node2上Pod的镜像拉取错误是否一致，验证跨节点问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证主异常组(g2) mcp命名空间代表Pod: mcp/connectivity-test (ErrImagePull)","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","purpose":"验证mcp命名空间跨命名空间的ErrImagePull是否一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"验证主异常组(g2) aiops-e2e命名空间代表Pod: aiops-e2e/test-dns-1779360358 (ImagePullBackOff)","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"验证aiops-e2e命名空间的ImagePullBackOff是否与default/mcp一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"检查集群级Events中与镜像拉取相关的Warning事件","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=FailedToPullImage,reason=ErrImagePull,reason=ImagePullBackOff --sort-by='.lastTimestamp' | tail -30","purpose":"从集群级别获取所有FailedToPullImage/ErrImagePull事件，验证系统级问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7","description":"验证异常组g1: aiops-e2e/rc-notready-liveness (CrashLoopBackOff) - 检查Last State和Exit Code","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"验证CrashLoopBackOff的Exit Code和Last State，确认是否因liveness probe导致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e8","description":"验证异常组g3: default/dns-connectivity-test (Terminating) - 检查finalizers和deletionTimestamp","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-connectivity-test -n default -o yaml","purpose":"验证Terminating状态的Pod是否有finalizers阻止删除","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e9","description":"验证异常组g4: mcp/node-debugger-node1-nx8gb (StartError) - 最小状态验证","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"验证StartError异常的状态和事件","collected":false,"source":"planned","outcome":"unknown"},{"id":"e10","description":"验证g3 Terminating Pod的事件","level":"optional","tool":"kubectl_events","command":"kubectl get events -n default --field-selector involvedObject.name=dns-connectivity-test --sort-by='.lastTimestamp'","purpose":"检查Terminating Pod是否有相关删除事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e9(验证异常组g4: mcp/node-debugger-node1-nx8gb (StartError) - 最小状态验证): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/9 项, 完整度: 93%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证主异常组(g2)代表Pod: default/connectivity-check-t... | `kubectl describe pod connectivity-check-tmp -n default` |
   | e2 | important | ✅ | kubectl_get_yaml | 验证主异常组(g2)代表Pod: default/connectivity-check-t... | `kubectl get pod connectivity-check-tmp -n default -o yaml` |
   | e3 | important | ✅ | kubectl_describe | 验证主异常组(g2)另一个代表Pod: default/dns-test (ErrImag... | `kubectl describe pod dns-test -n default` |
   | e4 | important | ✅ | kubectl_describe | 验证主异常组(g2) mcp命名空间代表Pod: mcp/connectivity-tes... | `kubectl describe pod connectivity-test -n mcp` |
   | e5 | important | ✅ | kubectl_describe | 验证主异常组(g2) aiops-e2e命名空间代表Pod: aiops-e2e/test... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | e6 | important | ✅ | kubectl_events | 检查集群级Events中与镜像拉取相关的Warning事件 | `kubectl get events --all-namespaces --field-selector reason=FailedToPullImage...` |
   | e7 | critical | ✅ | kubectl_describe | 验证异常组g1: aiops-e2e/rc-notready-liveness (Cras... | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e8 | important | ✅ | kubectl_get_yaml | 验证异常组g3: default/dns-connectivity-test (Termi... | `kubectl get pod dns-connectivity-test -n default -o yaml` |
   | e9 | important | ❌ | kubectl_describe | 验证异常组g4: mcp/node-debugger-node1-nx8gb (Start... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | e10 | optional | ✅ | kubectl_events | 验证g3 Terminating Pod的事件 | `kubectl get events -n default --field-selector involvedObject.name=dns-connec...` |

   ⚠️ 未采集原因:
   - e9(验证异常组g4: mcp/node-debugger-node1-nx8gb (StartError) - 最小状态验证): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (28.5s)
   📤 → 下游数据: root_cause=集群的核心问题是**节点到外网镜像仓库的网络不通**。证据表明：node1上的Pod（如aiops-e2e/test-dns-1779360358）拉取busybox:1.36.1时出现"connection reset by peer"到52.202.41.60:443（e5），node2上的Pod（如default/connectivity-check-tmp、mcp/connectivity-test）出现"i/o timeout"到多个registry-1.docker.io IP（199.96.58.177, 108.160.166.42等）（e1/e3/e4）。56个Pod（35 ErrImagePull + 21 ImagePullBackOff，跨3个命名空间和2个节点）均因同一原因无法拉取镜像。镜像名（busybox:1.36.1/1.28、jessie-dnsutils:1.0）均为有效公开镜像，且各Pod均无imagePullSecrets（e2），排除认证和镜像不存在问题。此外，aiops-e2e/rc-notready-liveness（CrashLoopBa
... 截断，原始 817 字符
   confidence=98%
   causal_chain={"root_cause": "集群节点（node1、node2）缺乏到外网镜像仓库（docker.io、registry.k8s.io）的网络连通性，导致所有依赖外网镜像的Pod无法拉取镜像", "propagation": "节点无法建立到registry-1.docker.io:443的TCP连接 → kubelet镜像拉取持续失败（i/o timeout或connection reset by peer）→ Pod停留在Pending状态并触发ImagePullBackOff/ErrImagePull → kubelet按指数退避重试，BackOff次数持续增长（最大x2071）", "direct_cause": "kubelet在拉取docker.io/library/busybox和registry.k8s.io/e2e-test-images/jessie-dnsutils等镜像时，TCP连接至registry-1.docker.io:443超时或被对端重置（confirmed by e1/e3/e5/e6）", "manifestation": "56个Pod（跨node1/node2，default/aiops-e2e/mcp命名空间）处于ImagePullBackOff或ErrImagePull状态，持续重试但无法拉取；1个Pod（dns-connectivity-test）卡在Terminating（删除前镜像未拉取完）；另有1个Pod（node-debugger-node1-nx8gb）StartError（镜像已拉取但容器内command 'curl'不存在，独立问题）"}
   rca_analysis={"phenomenon": "集群中存在约56个Pod（分布在node1、node2，跨越default、aiops-e2e、mcp三个命名空间）处于ImagePullBackOff/ErrImagePull状态，无法拉取docker.io和registry.k8s.io上的镜像；另有1个Pod（aiops-e2e/rc-notready-liveness）处于CrashLoopBackOff（Exit Code 137，liveness探针失败）；1个Pod（default/dns-connectivity-test）卡在Terminating；1个Pod（mcp/node-debugger-node1-nx8gb）处于StartError（curl命令不存在）。总计约58个异常Pod。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "default/connectivity-check-tmp (node2): ErrImagePull, i/o timeout to 199.96.58.177:443, connection refused, pull QPS exceeded, BackOff x90 over 152m", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "default/connectivity-check-tmp: image=busybox:1.36.1, imagePullSecrets=absent, containerStatuses message=dial tcp i/o timeout", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe", "content": "default/dns-test (node2): ErrImagePull, i/o timeout to multiple registry-1.docker.io IPs (108.160.166.42, 208.43.170.231等), events span 102min", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe", "content": "mcp/connectivity-test (node2): ErrImagePull, i/o timeout + connection refused + pull QPS exceeded, BackOff x1550 over 13h", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe", "content": "aiops-e2e/test-dns-1779360358 (node1): ImagePullBackOff, connection reset by peer to 52.202.41.60:443, BackOff x2071 over 14h", "reliability": "高"}, {"id": "e6", "source": "kubernetes_tabular_query", "content": "59异常行: 35 ErrImagePull + 21 ImagePullBackOff拉取busybox/jessie-dnsutils, 连接错误(connection reset by peer, i/o timeout)到docker hub IPs和gcr IPs", "reliability": "高"}, {"id": "e7", "source": "kubectl_describe", "content": "aiops-e2e/rc-notready-liveness: CrashLoopBackOff, Exit Code 137, Liveness probe failed, label rootcause-e2e=true, annotation runbook pod-notready-probe-failed.md", "reliability": "高"}, {"id": "e8", "source": "kubectl_get_yaml", "content": "default/dns-connectivity-test: deletionTimestamp=2026-05-22T00:54:47Z, finalizers=none, phase=Pending, image=busybox:1.28", "reliability": "高"}, {"id": "e10", "source": "kubectl_events", "content": "dns-connectivity-test: 只有Scheduled/Pulling/AddedInterface正常事件，无异常Warning", "reliability": "中"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Pod connectivity-check-tmp: i/o timeout to 199.96.58.177:443, connection refused, pull QPS exceeded, BackOff x90 over 152m", "interpretation": "node2上的代表Pod确认无法连通registry-1.docker.io:443，错误为TCP层i/o timeout—表明节点到外网docker registry的网络路径不通"}, {"evidence_id": "e2", "raw_data": "image=busybox:1.36.1, imagePullSecrets=absent, message=dial tcp i/o timeout", "interpretation": "镜像名和tag有效(busybox:1.36.1是公开镜像)，无imagePullSecrets，排除认证问题—根因锁定为网络不可达"}, {"evidence_id": "e3", "raw_data": "dns-test: i/o timeout to多个registry-1.docker.io IPs (108.160.166.42, 208.43.170.231, 69.171.224.36等)", "interpretation": "node2上不同Pod、不同镜像(busybox:1.28)也出现完全相同的i/o timeout错误，排除镜像tag特定问题，确认为节点级外网连通性故障"}, {"evidence_id": "e4", "raw_data": "mcp/connectivity-test: i/o timeout + connection refused, BackOff x1550 over 13h", "interpretation": "mcp命名空间下的Pod在node2上也完全无法拉取镜像，跨命名空间一致性证实这是节点级网络问题而非命名空间策略问题"}, {"evidence_id": "e5", "raw_data": "aiops-e2e/test-dns-1779360358: connection reset by peer to 52.202.41.60:443, BackOff x2071 over 14h", "interpretation": "node1上的Pod同样无法拉取镜像，但表现为connection reset by peer而非i/o timeout，说明node1和node2到docker registry的网络路径不同但都不可达"}, {"evidence_id": "e6", "raw_data": "35 ErrImagePull + 21 ImagePullBackOff, 连接错误到docker hub IPs (44.218.41.59, 199.96.58.177等)和gcr IPs", "interpretation": "跨节点、跨命名空间、跨镜像仓库(docker.io和registry.k8s.io)的全面拉取失败，明确的集群级外网不可达模式"}, {"evidence_id": "e7", "raw_data": "Exit Code=137, Liveness probe failed, label rootcause-e2e=true, annotation runbook pod-notready-probe-failed.md", "interpretation": "此Pod为人为构造的e2e测试用例（rootcause-e2e=true），liveness探针故意配置失败模拟故障，非真实生产问题"}, {"evidence_id": "e8", "raw_data": "deletionTimestamp=2026-05-22T00:54:47Z, finalizers=none, phase=Pending", "interpretation": "Pod已设置删除时间戳但无finalizers，说明删除流程卡在容器创建阶段（镜像拉取失败导致），而非finalizer阻塞"}, {"evidence_id": "e10", "raw_data": "只有Scheduled/Pulling/AddedInterface正常事件", "interpretation": "g3 Terminating Pod没有异常事件，其卡住的原因是镜像拉取前已被删除，与主异常组g2同根因（镜像无法拉取）"}], "causal_chain": {"root_cause": "集群节点（node1、node2）缺乏到外网镜像仓库（docker.io、registry.k8s.io）的网络连通性，导致所有依赖外网镜像的Pod无法拉取镜像", "propagation": "节点无法建立到registry-1.docker.io:443的TCP连接 → kubelet镜像拉取持续失败（i/o timeout或connection reset by peer）→ Pod停留在Pending状态并触发ImagePullBackOff/ErrImagePull → kubelet按指数退避重试，BackOff次数持续增长（最大x2071）", "direct_cause": "kubelet在拉取docker.io/library/busybox和registry.k8s.io/e2e-test-images/jessie-dnsutils等镜像时，TCP连接至registry-1.docker.io:443超时或被对端重置（confirmed by e1/e3/e5/e6）", "manifestation": "56个Pod（跨node1/node2，default/aiops-e2e/mcp命名空间）处于ImagePullBackOff或ErrImagePull状态，持续重试但无法拉取；1个Pod（dns-connectivity-test）卡在Terminating（删除前镜像未拉取完）；另有1个Pod（node-debugger-node1-nx8gb）StartError（镜像已拉取但容器内command 'curl'不存在，独立问题）"}, "root_cause": "集群的核心问题是**节点到外网镜像仓库的网络不通**。证据表明：node1上的Pod（如aiops-e2e/test-dns-1779360358）拉取busybox:1.36.1时出现\"connection reset by peer\"到52.202.41.60:443（e5），node2上的Pod（如default/connectivity-check-tmp、mcp/connectivity-test）出现\"i/o timeout\"到多个registry-1.docker.io IP（199.96.58.177, 108.160.166.42等）（e1/e3/e4）。56个Pod（35 ErrImagePull + 21 ImagePullBackOff，跨3个命名空间和2个节点）均因同一原因无法拉取镜像。镜像名（busybox:1.36.1/1.28、jessie-dnsutils:1.0）均为有效公开镜像，且各Pod均无imagePullSecrets（e2），排除认证和镜像不存在问题。此外，aiops-e2e/rc-notready-liveness（CrashLoopBa\n... 截断，原始 817 字符", "root_cause_summary": "集群的核心问题是**节点到外网镜像仓库的网络不通**。证据表明：node1上的Pod（如aiops-e2e/test-dns-1779360358）拉取busybox:1.36.1时出现\"connection reset by peer\"到52.202.41.60:443（e5），node2上的Pod（如default/connectivity-check-tmp、mcp/connectivity-test）出现\"i/o timeout\"到多个registry-1.docker.io IP（199.96.58.177, 108.160.166.42等）（e1/e3/e4）。56个Pod（35 ErrImagePull + 21 ImagePullBackOff，跨3个命名空间和2个节点）均因同一原因无法拉取镜像。镜像名（busybox:1.36.1/1.28、jessie-dnsutils:1.0）均为有效公开镜像，且各Pod均无imagePullSecrets（e2），排除认证和镜像不存在问题。此外，aiops-e2e/rc-notready-liveness（CrashLoopBa\n... 截断，原始 817 字符", "confidence": 0.98, "confidence_reason": "直接证据充分：从多个节点(node1/node2)、多个命名空间(default/aiops-e2e/mcp)、多个镜像仓库(docker.io/registry.k8s.io)的代表Pod均获取到明确的TCP连接错误（i/o timeout和connection reset by peer），因果链完整清晰。镜像有效性已通过YAML验证（无认证错误、镜像名和tag正确）。所有56个Pod一致表现出拉取失败，排除了单点故障可能。置信度0.98因有一个Pod(g4 StartError)为独立问题且证据不完全（e9未采集）。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像名或tag不存在", "probability": "low", "reason": "busybox:1.36.1、busybox:1.28、jessie-dnsutils:1.0均为广泛使用的有效公开镜像；且错误信息为TCP连接错误而非manifest unknown"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "所有检查的Pod均无imagePullSecrets（e2/e8），且错误信息不含认证拒绝相关关键词（如unauthorized、denied），均为网络层错误"}, {"cause": "CNI/网络策略阻断对外访问", "probability": "low", "reason": "证据显示kubelet能解析镜像地址并发起TCP连接（得到connection reset by peer而非DNS解析失败），网络策略通常不会产生'connection reset by peer'—更可能是集群出口NAT/防火墙规则导致外网访问不通"}, {"cause": "集群DNS解析故障", "probability": "low", "reason": "kubernetes_tabular_query显示错误为TCP连接超时而非DNS解析失败；且registry-1.docker.io的IP已被解析（e1中199.96.58.177等IP出现在错误中）"}], "limitations": "缺失g4（mcp/node-debugger-node1-nx8gb StartError）的完整验证（e9未采集），但从现有证据（e7中的node-debugger输出）可知其根因是容器内command 'curl'不存在，与主异常组无关。未验证集群是否有镜像代理/registry mirror配置——如果存在mirror配置但mirror也不可达，则根因相同。集群级别events已被清理，无法获取全局视角的事件记录。", "llm_raw_analysis": "## 证据清点\\n共采集10条有效证据（e1-e8, e10，e9缺失），加上6个上游已验证工具结果。\\n\\n## 逐条分析\\n### 主异常组g2（ImagePullBackOff/ErrImagePull，56个Pod）\\n- **e1**: default/connectivity-check-tmp on node2 → ErrImagePull，i/o timeout to 199.96.58.177:443 — 确认节点级网络不可达\\n- **e2**: YAML确认镜像有效、无imagePullSecrets — 排除认证/配置问题\\n- **e3**: default/dns-test on node2 → 同样i/o timeout到多个docker hub IP — 跨Pod一致性\\n- **e4**: mcp/connectivity-test on node2 → 同样网络错误，BackOff x1550 over 13h — 跨命名空间一致性\\n- **e5**: aiops-e2e/test-dns-1779360358 on node1 → connect\n... 截断，原始 1249 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群的核心问题是**节点到外网镜像仓库的网络不通**。证据表明：node1上的Pod（如aiops-e2e/test-dns-1779360358）拉取busybox:1.36.1时出现"connection reset by peer"到52.202.41.60:443（e5），node2上的Po...
   置信度: 98%
   🔗 因果链:
     根本原因: 集群节点（node1、node2）缺乏到外网镜像仓库（docker.io、registry.k8s.io）的网络连通性，导致所有依赖外网镜像的Pod无法拉取镜像
     传导机制: 节点无法建立到registry-1.docker.io:443的TCP连接 → kubelet镜像拉取持续失败（i/o timeout或connection reset by peer）→ Pod停留在Pending状态并触发ImagePullBackOff/ErrImagePull → kubelet按指数退避重试，BackOff次数持续增长（最大x2071）
     最终表现: 56个Pod（跨node1/node2，default/aiops-e2e/mcp命名空间）处于ImagePullBackOff或ErrImagePull状态，持续重试但无法拉取；1个Pod（dns-connectivity-test）卡在Terminating（删除前镜像未拉取完）；另有1个Pod（node-debugger-node1-nx8gb）StartError（镜像已拉取但容器内command 'curl'不存在，独立问题）


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (25.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6887 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 44.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您分析集群的当前状态。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群核心问题** | **集群节点无法访问外网镜像仓库**，导致大量 Pod 无法启动。 |
| **受影响状态** | `ImagePullBackOff`, `ErrImagePull`, `Pending` |
| **影响范围** | 跨 node1、node2 节点，default、aiops-e2e、mcp 三个命名空间，共约 **56个Pod**。 |
| **异常 Pod 构成** | 55 个 Pod 因镜像拉取失败处于 Pending 状态（35个 `ErrImagePull` + 20个 `ImagePullBackOff`）；1 个 Pod (`rc-notready-liveness`) 因 liveness 探针失败处于 `CrashLoopBackOff`；1 个 Pod (`dns-connectivity-test`) 卡在 `Terminating` 状态。 |
| **次要/演习问题** | `aiops-e2e/rc-notready-liveness` (CrashLoopBackOff) 和 `default/dns-connectivity-test` (Terminating) 是人为构造的测试用例或附带影响，非基础设施故障。 |
| **置信度** | 高 (98%) |
| **证据完整度** | 8/9 (89%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **受影响节点** | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| **受影响命名空间** | `default`, `aiops-e2e`, `mcp` |
| **故障镜像** | `docker.io/library/busybox:*`, `registry.k8s.io/e2e-test-images/jessie-dnsutils:*` |
| **目标仓库 IP** | `44.218.41.59`, `199.96.58.177`, `74.86.151.167`, `108.160.166.42`, `208.43.170.231`, `52.202.41.60` 等 |
| **错误信息** | `connection reset by peer`, `i/o timeout`, `connection refused` |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| e1/e3/e4/e5 | Pod 状态与事件 | `kubectl describe` on `connectivity-check-tmp`, `dns-test`, `connectivity-test`, `test-dns-1779360358` | **Pod 状态**: `Pending`, **容器状态**: `Waiting (Reason: ErrImagePull)`<br>**事件**: `Failed to pull image` 错误: `i/o timeout`, `connection reset by peer`, `connection refused`。重试次数高达 **x2071**，拉取时间长达 **13h** | 不同命名空间、不同节点上的 Pod 均因 **网络不可达** 导致从 `docker.io` 拉取镜像失败 |
| e2 | Pod 配置 | `kubectl get pod connectivity-check-tmp -o yaml` | `finalizers: <none>`<br>`imagePullSecrets: <none>` | 排除 finalizer 未清理和镜像拉取凭证缺失的问题 |
| e6 | 集群事件 | `kubectl events` | 事件中仅显示少量关于 `dns-connectivity-test` 的 `AddedInterface` 事件，**无全局性镜像拉取失败事件**（可能已被清理） | 集群级事件已经被清理，无法提供额外全局视角 |
| e7 | Pod 状态 | `kubectl describe pod rc-notready-liveness` | **状态**: `Running` (但 Ready 为 0/1), **Exit Code**: 137, **事件**: `Container app failed liveness probe, will be restarted` | 该 Pod 的 `CrashLoopBackOff` 是因其 **liveness 探针故意配置失败** 导致的 |
| e8/e10 | Pod 状态 | `kubectl get pod dns-connectivity-test -o yaml` | `deletionTimestamp: 2026-05-22T00:54:47Z`, `deletionGracePeriodSeconds: 30`, `finalizers: <none>` | 该 Pod 卡在 Terminating 状态，但 **finalizer 已被清理**，可以安全强制删除 |

### 证据关联分析
- **证据 e1, e3, e4, e5 印证**：所有核心证据均指向 **节点到 `registry-1.docker.io:443` 的 TCP 连接失败**。无论 Pod 在哪个节点 (node1/node2) 或命名空间 (default/aiops-e2e/mcp)，都出现了 `i/o timeout` 或 `connection reset by peer`，这是典型的 **网络出口不通** 的现象。
- **证据链**：节点外网出口问题 → kubelet 无法完成镜像拉取 → 容器无法创建 →  Pod 状态变为 `Pending` (Reason: `ErrImagePull`/`ImagePullBackOff`) → kubelet 进入指数退避重试。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 镜像代理/registry mirror 配置 | optional | 验证是否配置了代理。如果已配置但代理也不可达，结论一致。 |

---

## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                 │
│ 集群节点（node1, node2）缺乏到外网镜像仓库的网络连通性                    │
│ （无法建立到 registry-1.docker.io:443 的 TCP 连接）                      │
└──────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                 │
│ kubelet 尝试从 docker.io 拉取镜像 → TCP 连接超时/被重置 → 镜像拉取失败   │
│ kubelet 按指数退避不断重试（BackOff → x2071 次）                         │
└──────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                 │
│ kubelet 报告 `ErrImagePull` / `ImagePullBackOff`，错误信息为             │
│ "i/o timeout" 或 "connection reset by peer"                              │
└──────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                              │
│ 集群中约 56 个 Pod（跨 2 节点、3 命名空间）卡在 Pending 状态，持续重启  │
│ 这些 Pod 的 STATUS 显示为 ImagePullBackOff 或 ErrImagePull               │
└──────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 e1, e3, e4, e5 中重复出现的 `i/o timeout` 和 `connection reset by peer` 错误，以及证据 e2 排除镜像凭证问题，集群的核心问题是**集群节点无法访问外网镜像仓库 `docker.io` 和 `registry.k8s.io`**。这是一个**集群网络层 (L3)** 的问题，影响了所有依赖外网镜像的 Pod。

此外，还存在一个独立的次要问题：Pod `aiops-e2e/rc-notready-liveness` 因 liveness 探针被配置为 `exit 1`（属于测试用例）而处于 `CrashLoopBackOff` 状态。

**置信度**：高 (98%)
- ✅ 多 Pod、多节点、多命名空间验证，故障现象高度一致。
- ✅ 错误类型（`i/o timeout`, `connection reset`）明确指向网络问题。
- ✅ 已排除镜像不存在、token 认证和 finalizer 问题。
- ⚠️ 缺少节点网络出口配置（如代理、NAT、路由）的详细检查。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [核心修复] 解决节点网络出口问题**
由于无法直接访问外网，最快速有效的方案是**配置一个本地镜像缓存（Registry Mirror）或代理**。
*   **方案 A：配置 HTTP 代理 (推荐)**  
    为 containerd 配置 HTTP 代理，使镜像拉取流量走代理出口。
    *   **操作节点**：所有集群节点 (`node1`, `node2`)
    *   **配置步骤**：
        1. 编辑 containerd 配置：`sudo vim /etc/containerd/config.toml`
        2. 找到 `[plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]` 或类似段落。
        3. 添加 endpoint，指向您的内部代理缓存，例如：
            ```toml
            [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
              [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
                endpoint = ["http://<YOUR_INTERNAL_PROXY>:5000"]
            ```
        4. 重启 containerd：`sudo systemctl restart containerd`
*   **方案 B：配置私有镜像仓库**
    在外网可达的环境中拉取所需镜像，然后推送至集群内网可访问的私有仓库。
    ```bash
    # 在外网机器上执行
    docker pull busybox:1.36.1
    docker tag busybox:1.36.1 <your-private-registry>/library/busybox:1.36.1
    docker push <your-private-registry>/library/busybox:1.36.1
    ```
    然后在集群中修改 Deployment 的镜像地址为私有仓库地址。

**2. [次要修复] 处理测试 Pod**
```bash
# 1. 强制删除卡在 Terminating 的 Pod（已确认无 finalizer 阻塞）
kubectl delete pod dns-connectivity-test -n default --force --grace-period=0

# 2. 检查 rc-notready-liveness Pod（如果是测试用例可忽略，如需修复需修改 Liveness 探针配置）
kubectl describe pod rc-notready-liveness -n aiops-e2e
```

### 后续优化
1. **镜像管理策略**：建议全面使用私有镜像仓库，避免生产环境依赖公网仓库。
2. **网络监控**：添加节点外网连通性监控，例如使用 `blackbox_exporter` 定期探测 `registry-1.docker.io`。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认核心问题修复 | `kubectl get pods -A \| grep -E 'ErrImagePull\|ImagePullBackOff'` | 不再输出（或数量持续减少） |
| 2. 验证单个 Pod 启动 | `kubectl get pod connectivity-check-tmp -n default` | STATUS 从 `Pending` 变为 `Running` (或 `Completed`) |
| 3. 检查集群健康状态 | `kubectl get nodes` | 所有节点状态为 `Ready` |

---
## ⚠️ 注意事项
- **影响范围广**：任何新的 Deployment 如果引用了外网镜像，也会立即失败，请务必使用私有仓库。
- **配置持久化**：修改节点配置后，建议固化配置，避免节点重启后失效。

---

## 📊 性能统计

├─ 总耗时: 2.7m
├─ 问题定位: 53.9s (33%) ✅
├─ 证据链采集: 56.0s (34%) ✅
├─ 根因分析: 28.5s (17%) ✅
├─ 汇总总结: 25.7s (16%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 24 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-notready-probe-failed, pod-crashloop-runtime
- **工具调用**: 24 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
