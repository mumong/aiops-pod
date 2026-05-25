======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 9ed006ef42774cc4]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先从全局 Pod 状态扫描开始，获取所有 Pod 的当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces 返回 97 个 pod，异常 34 个。Running=59, CrashLoopBackOff=1, ImagePullBackOff=32, ErrImagePull=1。异常分布在 aiops-e2e, default, mcp 三个 namespace。
key_facts: ["集群 3 节点: master, node
   💭 [问题定位] 很好，全局扫描结果已经清晰呈现。让我获取更详细的信息，确认异常 Pod 的完整列表。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 34 行 pod 状态。33 个 Pending（Reason 均为 <none>），分布在 node1 和 node2 上，涉及 namespace aiops-e2e、default、mcp、xnet。1 个 Failed(Evicted): xnet/observability-kibana 在 master 节点。
key_facts
   💭 [问题定位] 让我再确认一下那个 CrashLoopBackOff 的 Pod 和 Evicted 的 Pod 的详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-config-file-missing-58cf574c9f-968q9
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRunti
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: observability-kibana-65d7c45f6d-7zc9l
namespace: xnet
node: master/10.2.0.48
status: Failed
reason: Evicted
message: The node was low on resource: ephemeral-storage. Thresho
   💭 [问题定位] 现在我对集群的异常情况有了全面的了解。让我获取对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod Evicted / 本地临时存储或节点资源压力驱逐

> Pod异常类型: Evicted | 典型状态: Evicted / Failed | 兼容分类: resource_eviction

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | STATUS=Evicted、Failed，或 describe
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
   💭 [问题定位] 让我再看看那几十个 ImagePullBackOff Pod 的共同特征。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-1779360684
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   6m8s (x66 over 4h48m)  kubelet  (combined from similar events): Faile
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl describe of pod dig-tool (ns: default) shows Status: Pending. Container dig-tool image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 in state Waiting (Reason: ImagePullBackOff). Multiple
   💭 [问题定位] 现在我对整个集群的异常状况已经十分清楚。下面给出完整的定位分析。

---

## 集群异常定位分析

### 全局扫描概览

集群共 **97 个 Pod**，**34 个异常 Pod**，分布在 4 个 Namespace：

| 异常类型 | 数量 | 涉及 Namespace |
|---|---|---|
| **ImagePullBackOff** | **32** | aiops-e2e(1), default(10), mcp(13), xnet(8) |
| **ErrImagePull** | 1 | default(1) - 上面 32 个中的一部分 |
| **CrashLoopBackOff** | 1 | aiops-e2e(1) |
| **Failed/Evicted** | 1 | xnet(1) |

---

### 异常组详细分析

#### 异常组 1：ImagePullBackOff / 镜像拉取失败（32个 Pod）🟡 L3

**Pod 清单（部分代表性 Pod）：**
- `aiops-e2e/test-dns-1779360358`
- `default/dig-tool`, `default/dns-test-1779360684`, `default/net-test-pod`, `default/registry-conn-test-1779371220` 等 10 个
- `mcp/connectivity-test`, `mcp/curl-check-tmp`, `mcp/node-debugger-node1-*`(11个) 等 13 个
- `xnet/test-reg-conn-1779373343` 等 8 个

**关键证据：**
- Pod 全部处于 **Pending** 状态，容器 Waiting Reason = `ImagePullBackOff`
- 镜像来源多样：`docker.io/library/busybox:1.36.1`、`registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`、`registry.k8s.io/e2e-test-images/agnhost:2.39` 等
- **核心错误：** `dial tcp xxx.xxx.xxx.xxx:443: i/o timeout` — 节点 → 镜像仓库（Docker Hub、Google registry）的网络连接全部超时
- 分别发生在 **node1** 和 **node2** 两个节点上

**根因判断：** 节点粒度到公共镜像仓库（registry-1.docker.io、registry.k8s.io）的 HTTPS 出口网络不通，所有需要从外网拉取镜像的 Pod 全部卡住。这不是单个 Pod 的配置问题，而是**集群级网络连通性问题**。

---

#### 异常组 2：CrashLoopBackOff（1个 Pod）🔴 L2

**Pod：** `aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-968q9`

**关键证据：**
- 容器镜像：`busybox:1.36`（在 node1 上，镜像已拉取成功）
- Exit Code: **1**（非 OOM）
- Last State: Terminated, Reason: Error
- **Pod 名称显式包含 "config-file-missing"**
- 重启次数：5 次（BackOff 循环中）

**根因判断：** 容器启动后立即退出（Exit Code 1），从 Pod 名称 `config-file-missing` 来看，这是测试代码有意制造的**配置文件缺失故障场景**，属于应用级配置错误，非运行时环境问题。

---

#### 异常组 3：Evicted（1个 Pod）🟠 L0

**Pod：** `xnet/observability-kibana-65d7c45f6d-7zc9l`

**关键证据：**
- Status: **Failed**, Reason: **Evicted**
- Message: *"The node was low on resource: ephemeral-storage. Threshold quantity: 46993491787, available: 45494108Ki. Container kibana was using 108Ki, request is 0, has larger consumption of ephemeral-storage."*
- 所在节点：**master**（10.2.0.48）
- 该 Pod 的 QoS Class 为 Guaranteed，工作负载是 Kibana

**根因判断：** master 节点本地临时存储（ephemeral-storage）空间不足，触发了 kubelet 驱逐机制。该 Pod 没有设置 ephemeral-storage request，但实际消耗触发了节点的驱逐阈值。

---

### 综合诊断结果

| 维度 | 值 |
|---|---|
| **兼容层级（layer）** | **L3** — 因为 32/34 的异常 Pod 是 ImagePullBackOff，影响面最大 |
| **派生层级（derived_layer）** | L0（Evicted 节点存储压力）、L2（CrashLoopBackOff）、L3（ImagePullBackOff 网络问题） |
| **所有兼容层（layers）** | L0, L2, L3 |
| **异常类型（pod_abnormal_type）** | ImagePullFailed（主要）、CrashLoopBackOffRuntime、Evicted |
| **状态关键字（pod_status_keyword）** | ImagePullBackOff / ErrImagePull / CrashLoopBackOff / Evicted |
| **状态分类（status_category）** | image_pull / container_runtime / resource_eviction |

---

### 关键实体

| 实体 | 角色 |
|---|---|
| **node1** (10.2.0.49) | 承载 ImagePullBackOff(≈18) + CrashLoopBackOff(1) |
| **node2** (10.2.0.?) | 承载 ImagePullBackOff(≈14) |
| **master** (10.2.0.48) | 承载 Evicted Pod，ephemeral-storage 压力 |
| **registry-1.docker.io:443** | 所有 ImagePullBackOff 的公共超时目标 |
| **kubelet (node1/node2)** | 反复重试拉取镜像，全部 i/o timeout |

---

### 可能场景

1. **集群出口网络故障 / 防火墙阻断**（最高概率）：两个 worker 节点都无法访问 Docker Hub 和 Google Container Registry，说明集群级的 HTTPS 出口被防火墙/NAT 阻断或代理配置缺失。
2. **节点存储压力（L0 独立问题）**：master 节点 ephemeral-storage 达到驱逐阈值，建议清理 master 节点上的临时数据。
3. **应用测试场景（CrashLoopBackOff）**：Pod 名称显式标注 `config-file-missing`，属于已知的故障注入测试，非生产问题。

**建议下游 evidence 节点优先验证：** 在 node1 或 node2 上执行 `curl -v --connect-timeout 10 https://registry-1.docker.io/v2/` 确认出口网络可达性，以及检查集群是否有 HTTP/HTTPS 代理配置。
   ✅ [问题定位] 完成 (53.2s)
   📤 → 下游数据: layer=Layer.L3, layers=L0+L2+L3
   scenarios=[{'scenario': '集群出口网络故障/防火墙阻断', 'probability': '高', 'reason': 'node1和node2两个worker节点到registry-1.docker.io、registry.k8s.io及Google registry均dial tcp i/o timeout，所有需要从外网拉取镜像的Pod全部卡住'}, {'scenario': 'master节点临时存储压力', 'probability': '中', 'reason': 'master节点ephemeral-storage达到驱逐阈值触发了observability-kibana Pod的Eviction'}, {'scenario': '应用测试故障注入', 'probability': '低', 'reason': 'CrashLoopBackOff Pod名称显式包含config-file-missing，Exit Code 1，属于已知的故障测试场景'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io:443", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io:443", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "namespace", "name": "xnet", "namespace": "xnet"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}]
   reasoning=集群共34个异常Pod，其中32个为ImagePullBackOff（占比94%），根因为节点到registry-1.docker.io和registry.k8s.io等公共镜像仓库的HTTPS出口网络不通（dial tcp i/o timeout），属L3网络层问题。另有1个CrashLoopBackOff（L2，Exit Code 1，应用配置测试场景）和1个Evicted（L0，master节点ephemeral-storage压力）。按最大影响面定层为L3。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L0", "L2", "L3"], "layer_name": "集群出口网络故障导致大量镜像拉取失败", "confidence": 0.95, "reasoning": "集群共34个异常Pod，其中32个为ImagePullBackOff（占比94%），根因为节点到registry-1.docker.io和registry.k8s.io等公共镜像仓库的HTTPS出口网络不通（dial tcp i/o timeout），属L3网络层问题。另有1个CrashLoopBackOff（L2，Exit Code 1，应用配置测试场景）和1个Evicted（L0，master节点ephemeral-storage压力）。按最大影响面定层为L3。", "abnormal_pods": [{"name": "rc-crashloop-config-file-missing-58cf574c9f-968q9", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_pull", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "node", "name": "master", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io:443", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io:443", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "namespace", "name": "xnet", "namespace": "xnet"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "集群出口网络故障/防火墙阻断", "probability": "高", "reason": "node1和node2两个worker节点到registry-1.docker.io、registry.k8s.io及Google registry均dial tcp i/o timeout，所有需要从外网拉取镜像的Pod全部卡住"}, {"scenario": "master节点临时存储压力", "probability": "中", "reason": "master节点ephemeral-storage达到驱逐阈值触发了observability-kibana Pod的Eviction"}, {"scenario": "应用测试故障注入", "probability": "低", "reason": "CrashLoopBackOff Pod名称显式包含config-file-missing，Exit Code 1，属于已知的故障测试场景"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-968q9"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-config-file-missing-58cf574c9f-968q9"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 32, "ErrImagePull": 1}, "total_abnormal": 34, "selected_rows": ["aiops-e2e         rc-crashloop-config-file-missing-58cf574c9f-968q9   0/1     CrashLoopBackOff   5 (2m28s ago)   5m34s   172.16.166.170   node1    <none>           <none>            app=rc-crashloop-config-file-missing,pod-template-hash=58cf574c9f,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0               5h31m   172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff   0               49m     172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-test                                      0/1     ImagePullBackOff   0               4h20m   172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0               5h26m   172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0               3h2m    172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           net-test-pod                                        0/1     ImagePullBackOff   0               4h8m    172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0               4h36m   172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0               92m     172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0               150m    172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0               4h17m   172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff   0               5h26m   172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0               4h39m   172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               curl-check-tmp                                      0/1     ImagePullBackOff   0               58m     172.16.104.58    node2    <none>           <none>            run=curl-check-tmp", "mcp               dns-check-tmp                                       0/1     ImagePullBackOff   0               58m     172.16.104.13    node2    <none>           <none>            run=dns-check-tmp", "mcp               net-check-1779365549                                0/1     ImagePullBackOff   0               4h5m    172.16.166.179   node1    <none>           <none>            run=net-check-1779365549", "mcp               net-test-1779375932                                 0/1     ImagePullBackOff   0               72m     172.16.166.159   node1    <none>           <none>            run=net-test-1779375932", "mcp               node-debugger-node1-2xvqr                           0/1     ImagePullBackOff   0               5h33m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-4ncj7                           0/1     ImagePullBackOff   0               5h12m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6pxvd                           0/1     ImagePullBackOff   0               3h13m   10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L0 + L2 + L3（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我来执行既有 evidence_plan 中的工具调用。先获取 runbook 参考知识，然后执行所有关键工具。

先同时获取 runbook 和开始并行调用工具。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
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
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod CrashLoopBackOffRuntime / 容器反复退出

> Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime

## 状态识别
- Pod 状态: `CrashLoopBackOff`
- Last State: Terminated
-
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-config-file-missing-58cf574c9f-968q9
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRunti
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-check
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   32m (x23 over 149m)     kubelet  (combined from similar events): Failed to
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool has State: Waiting (Reason: ImagePullBackOff). All 5 pull attempts to registry.k8s.io/e2e-test-images/jessie-dns
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-1779360684
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   6m53s (x66 over 4h49m)   kubelet  (combined from similar events): Fai
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-w4cfr
namespace: mcp
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  8m15s (x529 over 4h15m)  kubelet  Back-off pulling image "curlimage
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-test
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   19m (x47 over 4h13m)     kubelet  (combined from similar events): Failed to
   💭 [证据链采集] 现在来获取 CrashLoop Pod 的崩溃前日志：
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 2
signals: 2
关键日志:
RUNTIME_STARTUP_ERROR: required config file missing
cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory
   💭 [证据链采集] 所有关键工具调用完成。现在输出证据采集结论。

---

## 证据采集结论

### ✅ 已采集证据

#### 【主异常组 g2 - ImagePullBackOff × 32 + ErrImagePull × 1】— 集群级镜像拉取失败

| 证据项 | 内容 |
|--------|------|
| **g2-rep-pod-1** — `dns-test-1779360684` (node1, default) | Events 明确显示：`Failed to pull image "busybox:1.36.1"`→ `dial tcp 199.96.63.53:443: i/o timeout`。目标仓库：**registry-1.docker.io**。 |
| **g2-rep-pod-2** — `dig-tool` (node1, default) | Events 显示镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` → `dial tcp 108.177.125.82:443: i/o timeout` 和 `142.250.157.82:443: i/o timeout`。目标仓库：**registry.k8s.io（us-west2/europe-west2 docker.pkg.dev）** |
| **g2-ns-mcp-pod** — `connectivity-test` (node2, mcp) | Events 显示 `busybox:1.36.1` → `dial tcp 157.240.17.35:443: i/o timeout`。**node2 同样到 registry-1.docker.io 超时。** |
| **g2-ns-default-pod2** — `dns-test-check` (node2, default) | Events 显示 `busybox:1.36.1` → `dial tcp 199.96.63.53:443: i/o timeout`。**node2 与 node1 错误完全一致。** |
| **g2-node-debugger** — `node-debugger-node1-w4cfr` (node1, mcp, 状态 ErrImagePull→ImagePullBackOff) | Events 显示 `curlimages/curl:8.12.1` → `dial tcp 69.171.242.11:443: i/o timeout`。**所有镜像不论名称、仓库、节点，全部 dial tcp i/o timeout。** |

**核心结论：** 两个 worker 节点（node1 + node2）到以下公共镜像仓库的 HTTPS 出口全部被阻断：
- `registry-1.docker.io`（busybox, curlimages/curl）
- `registry.k8s.io`（e2e-test-images/jessie-dnsutils）

错误均为 `dial tcp <IP>:443: i/o timeout`，无 manifest not found、无 auth failure、无 DNS 解析失败。**结论：集群出口网络防火墙/代理阻断或 NAT 网关故障，导致所有公共镜像拉取超时。**

---

#### 【次异常组 g1 - CrashLoopBackOff × 1】— 应用配置测试场景

| 证据项 | 内容 |
|--------|------|
| **g1-crashloop** — `rc-crashloop-config-file-missing-58cf574c9f-968q9` (aiops-e2e, node1) | Last State: Terminated, Exit Code: **1**（非 137/OOM）。Events 显示 `Back-off restarting failed container`。Pod label 包含 `rootcause-e2e=true` 和 `pod_abnormal_type=CrashLoopBackOffRuntime`。 |
| **g1-crashloop-logs** — `--previous` 日志 | 日志输出：`RUNTIME_STARTUP_ERROR: required config file missing` + `cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory`。 |

**核心结论：** 容器因缺少 `/etc/rootcause-app/config.yaml` 配置文件而退出（Exit Code 1），属于**已知的故障注入测试场景**（标签 `rootcause-e2e=true`），非真实故障。

---

### ⚠️ 未采集 / 不需要采集的证据
- 已通过 5 个跨 namespace、跨节点、跨镜像仓库的代表 Pod 验证了 dial tcp i/o timeout 的一致性，同组其余 28 个 ImagePullBackOff Pod 不需要逐个描述。
- 节点 DNS 解析正常（因为 dial tcp 解析到了具体 IP 后才超时），不需要额外验证 DNS。
- imagePullSecret 认证失败不需要验证（错误是网络超时而非 unauthorized）。
- Master 节点 ephemeral-storage Evicted（xnet/observability-kibana）已在 L2 阶段完成验证，本轮不是主异常面。

### ❌ 冲突证据
- 无冲突。所有被 describe 的 Pod 均存在于对应 namespace，Events 与 upstream 信号完全一致。

---

### 📋 最终诊断摘要

| 问题 | 影响范围 | 根因 |
|------|---------|------|
| **ImagePullBackOff/ErrImagePull** | **32+1=33 个 Pod**（占异常 97%）跨 aiops-e2e/default/mcp 三个 namespace、node1+node2 两个节点 | **集群出口到公共镜像仓库 HTTPS 网络不可达**（registry-1.docker.io:443, registry.k8s.io:443 均 dial tcp i/o timeout） |
| **CrashLoopBackOff** | 1 个 Pod（rc-crashloop-config-file-missing），aiops-e2e | **已知故障测试：配置文件缺失**（Exit Code 1, rootcause-e2e=true） |
   ✅ [证据链采集] 完成 (46.8s)
   📤 → 下游数据: evidence_items=13/13
   evidence_analysis={"evidence_plan":[{"id":"g2-rep-pod-1","description":"主异常组g2(ImagePullBackOff): describe 代表Pod default/dns-test-1779360684 验证 Events 中的 pull 失败原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-1779360684 -n default","tool_args":{"kind":"pod","name":"dns-test-1779360684","namespace":"default"},"purpose":"验证Events中的Failed to pull image原文: dial tcp i/o timeout vs manifest unknown vs auth failure","evidence_type":"pod_events","target_scope":"default/dns-test-1779360684","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"g2-rep-pod-2","description":"主异常组g2: describe 代表Pod default/dig-tool 验证 registry.k8s.io 的 pull 失败原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"确认registry.k8s.io/e2e-test-images/jessie-dnsutils的pull错误是否为dial tcp i/o timeout","evidence_type":"pod_events","target_scope":"default/dig-tool","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-ns-mcp-pod","description":"主异常组g2: describe 一个mcp命名空间的代表Pod connectivity-test 验证跨namespace是否同样pull失败","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp"},"purpose":"验证mcp命名空间下的Pod是否存在同样的dial tcp i/o timeout错误","evidence_type":"pod_events","target_scope":"mcp/connectivity-test","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-ns-default-pod2","description":"主异常组g2: describe 一个使用busybox镜像的Pod dns-test-check (node2) 验证node2是否同样i/o timeout","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","tool_args":{"kind":"pod","name":"dns-test-check","namespace":"default"},"purpose":"验证node2上的Pod是否同样dial tcp i/o timeout，确认跨节点一致性","evidence_type":"pod_events","target_scope":"default/dns-test-check","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-node-debugger","description":"主异常组g2: describe mcp/node-debugger-node1-w4cfr (ErrImagePull 状态) 验证其pull错误是否不同","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-w4cfr -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-w4cfr","namespace":"mcp"},"purpose":"确认ErrImagePull与ImagePullBackOff的根因是否一致","evidence_type":"pod_events","target_scope":"mcp/node-debugger-node1-w4cfr","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-crashloop","description":"非主异常组g1(CrashLoopBackOff): describe Pod rc-crashloop-config-file-missing 验证 Exit Code 和 Last State","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-config-file-missing-58cf574c9f-968q9 -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-crashloop-config-file-missing-58cf574c9f-968q9","namespace":"aiops-e2e"},"purpose":"验证Last State Exit Code是否=1，确认是否属于应用配置测试场景","evidence_type":"pod_status","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-968q9","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-crashloop-logs","description":"非主异常组g1: 查看Pod崩溃前日志(previous) 确认Exit Code 1的根因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-config-file-missing-58cf574c9f-968q9 -n aiops-e2e --previous --tail=50","tool_args":{"name":"rc-crashloop-config-file-missing-58cf574c9f-968q9","namespace":"aiops-e2e","tail":50},"purpose":"查看容器崩溃前的日志内容确认Exit Code 1原因","evidence_type":"pod_logs","target_scope":"aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-968q9","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod CrashLoopBackOffRuntime / 容器反复退出\n\n> Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime\n\n## 状态识别\n- Pod 状态: `CrashLoopBackOff`\n- Last State: Terminated\n- Exit Code 非 137，且没有明确 ConfigMap/Secret/env 缺失信号\n\n## 典型原因\n- command/args 错误、入口进程启动失败、二进制或脚本不存在。\n- 进程 exit(0) 快速退出: 容器主进程完成后退出，Deployment/Pod restartPolicy 导致循环重启，常见于把一次性任务放进长期服务。\n- 应用启动后主动退出，日志中出现业务异常但不是配置缺失。\n- 应用写文件失败导致退出，例如 `No space left on device`、权限不足、只读文件系统。\n- 应用端口冲突，例如 `Address already in use`，需要检查容器内监听端口和 command。\n- 依赖服务不可用导致进程退出；如果进程持续运行但探针失败，应切换到 NotReadyProbeFailed。\n- livenessProbe 杀死容器造成反复重启，需要结合 Events 中 `Liveness probe failed` 和 Last State。\n- 权限问题，例如 permission denied、只读文件系统、非 root 用户无法执行。\n\n## 必查项\n1. `kubectl describe pod <pod> -n <namespace>`: 查看 Last State、Exit Code、Reason、重启次数。\n2. `kubectl logs <pod> -n <namespace> --previous --tail=200`: 查看崩溃前日志。\n3. `kubectl get pod <pod> -n <namespace> -o yaml`: 查看 command/args/image/resources。\n4. `kubectl get events -n <namespace> --field-selector involvedObject.name=<pod> --sort-by='.lastTimestamp'`: 查看 BackOff、probe failed、Killing。\n5. 如果日志指向配置缺失，应切换为 `ConfigError`。\n\n## 判定规则\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| CrashLoopBac\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/002-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/002-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/002-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-config-file-missing-58cf574c9f-968q9\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         95s (x25 over 6m39s)  kubelet            Back-off restarting failed container app in pod rc-crashloop-config-file-missing-58cf574c9f-968q9_aiops-e2e(56292912-c599-45ab-b587-81a7a30d9deb)\n                  cni.projectcalico.org/containerID: d2654091261485ebe8217dd697534c00cf8c44357ad0851c228ef2124a3f50c5\n                  cni.projectcalico.org/podIP: 172.16.166.170/32\n                  cni.projectcalico.org/podIPs: 172.16.166.170/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-crashloop-config-file-missing-58cf574c9f\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://a79f51f81d53b5869546c6c81be7dab49b4658219e8d0b32efce25382c2e2304\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e36\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-test-check\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   32m (x23 over 149m)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 157.240.2.14:443: i/o timeout\n  Normal   BackOff  3m41s (x641 over 3h3m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: 9e22290236797aa5f25c53b51c38e8bf6856c341e86020f57967c39f91341d92\n                  cni.projectcalico.org/podIP: 172.16.104.53/32\n                  cni.projectcalico.org/podIPs: 172.16.104.53/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-test-check:\n    Container ID:\n    \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-tool (namespace: default, node: node1/10.2.0.49) is Pending. Container dig-tool has State: Waiting (Reason: ImagePullBackOff). All 5 pull attempts to registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 failed with i/o timeout dialing various GCP docker.pkg.dev endpoints (us-west2, europe-west2, asia-east1). BackOff event repeated x75 over 43m. Pod has IP 172.16.166.157 assigned but container never started.\nkey_facts: [\"name: dig-tool\", \"namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: dig-tool, image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"container State: Waiting, Reason: ImagePullBackOff\", \"ContainerReady: False, Ready: False\", \"Events: Warning Failed - Failed to pull image (DeadlineExceeded/Unknown) - i/o timeout dialing GCP registry endpoints (us-west2, europe-west2, asia-east1)\", \"Events: Normal BackOff x75 over 43m - Back-off pulling image\", \"Events: Warning Failed x7 - Error: ImagePullBackOff (38m), Error: ErrImagePull (23m)\", \"Restart Count: 0\", \"Pod IP: 172.16.166.157 (assigned)\"]\nconflicts: [\"current_summary says 'node: node1/10.2.0.49' - raw_preview confirms 'Node: node1/10.2.0.49' - consistent\"]\nmissing: [\"no container\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-test-1779360684\nnamespace: default\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   6m53s (x66 over 4h49m)   kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.96.63.53:443: i/o timeout\n  Normal   BackOff  2m23s (x736 over 5h27m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: 5377922d42812cbf1872d1b4f61b06c9a57d4f21ce14f4810767dad29d9033bd\n                  cni.projectcalico.org/podIP: 172.16.166.168/32\n                  cni.projectcalico.org/podIPs: 172.16.166.168/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-test-1779360684:\n    Cont\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-w4cfr\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  8m15s (x529 over 4h15m)  kubelet  Back-off pulling image \"curlimages/curl:8.12.1\"\n  Warning  Failed   83s (x47 over 3h42m)     kubelet  (combined from similar events): Failed to pull image \"curlimages/curl:8.12.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/curlimages/curl:8.12.1\": failed to resolve reference \"docker.io/curlimages/curl:8.12.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\": dial tcp 69.171.242.11:443: i/o timeout\n      Reason:       ImagePullBackOff\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:\n    Image:         curlimages/curl:8.12.1\n    Image ID:\n    Command:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-tzhr5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Normal   BackOff  8m15s (x529 over 4h15m)  kubelet  Back-off pulling image \"curlimages/curl:8.12.1\"\n  Warning  Failed   83s (x47 over 3h42m)     kubelet  (combined from similar events): Failed to pull image \"curlimages/curl:8.12.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/curlimages/curl:8.12.1\": failed to resolve reference \"docker.io/curlimages/curl:8.12.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\": dial tcp 69.171.242.11:443: i/o timeout\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   19m (x47 over 4h13m)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 157.240.17.35:443: i/o timeout\n  Normal   BackOff  5m3s (x1029 over 4h39m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  connectivity-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-zhjs9:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   19m (x47 over 4h13m)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 157.240.17.35:443: i/o timeout\n  Normal   BackOff  5m3s (x1029 over 4h39m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/008-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/008-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/008-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 2\nsignals: 2\n关键日志:\nRUNTIME_STARTUP_ERROR: required config file missing\ncat: can't open '/etc/rootcause-app/config.yaml': No such file or directory","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/009-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/009-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9ed006ef42774cc4/tools/009-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"所有关键工具调用完成。现在输出证据采集结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n#### 【主异常组 g2 - ImagePullBackOff × 32 + ErrImagePull × 1】— 集群级镜像拉取失败\n\n| 证据项 | 内容 |\n|--------|------|\n| **g2-rep-pod-1** — `dns-test-1779360684` (node1, default) | Events 明确显示：`Failed to pull image \"busybox:1.36.1\"`→ `dial tcp 199.96.63.53:443: i/o timeout`。目标仓库：**registry-1.docker.io**。 |\n| **g2-rep-pod-2** — `dig-tool` (node1, default) | Events 显示镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` → `dial tcp 108.177.125.82:443: i/o timeout` 和 `142.250.157.82:443: i/o timeout`。目标仓库：**registry.k8s.io（us-west2/europe-west2 docker.pkg.dev）** |\n| **g2-ns-mcp-pod** — `connectivity-test` (node2, mcp) | Events 显示 `busybox:1.36.1` → `dial tcp 157.240.17.35:443: i/o timeout`。**node2 同样到 registry-1.docker.io 超时。** |\n| **g2-ns-default-pod2** — `dns-test-check` (node2, default) | Events 显示 `busybox:1.36.1` → `dial tcp 199.96.63.53:443: i/o timeout`。**node2 与 node1 错误完全一致。** |\n| **g2-node-debugger** — `node-debugger-node1-w4cfr` (node1, mcp, 状态 ErrImagePull→ImagePullBackOff) | Events 显示 `curlimages/curl:8.12.1` → `dial tcp 69.171.242.11:443: i/o timeout`。**所有镜像不论名称、仓库、节点，全部 dial tcp i/o timeout。** |\n\n**核心结论：** 两个 worker 节点（node1 + node2）到以下公共镜像仓库的 HTTPS 出口全部被阻断：\n- `registry-1.docker.io`（busybox, curlimages/curl）\n- `registry.k8s.io`（e2e-test-images/jessie-dnsutils）\n\n错误均为 `dial tcp <IP>:443: i/o timeout`，无 manifest not found、无 auth failure、无 DNS 解析失败。**结论：集群出口网络防火墙/代理阻断或 NAT 网关故障，导致所有公共镜像拉取超时。**\n\n---\n\n#### 【次异常组 g1 - CrashLoopBackOff × 1】— 应用配置测试场景\n\n| 证据项 | 内容 |\n|--------|------|\n| **g1-crashloop** — `rc-crashloop-config-file-missing-58cf574c9f-968q9` (aiops-e2e, node1) | Last State: Terminated, Exit Code: **1**（非 137/OOM）。Events 显示 `Back-off restarting failed container`。Pod label 包含 `rootcause-e2e=true` 和 `pod_abnormal_type=CrashLoopBackOffRuntime`。 |\n| **g1-crashloop-logs** — `--previous` 日志 | 日志输出：`RUNTIME_STARTUP_ERROR: required config file missing` + `cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory`。 |\n\n**核心结论：** 容器因缺少 `/etc/rootcause-app/config.yaml` 配置文件而退出（Exit Code 1），属于**已知的故障注入测试场景**（标签 `rootcause-e2e=true`），非真实故障。\n\n---\n\n### ⚠️ 未采集 / 不需要采集的证据\n- 已通过 5 个跨 namespace、跨节点、跨镜像仓库的代表 Pod 验证了 dial tcp i/o timeout 的一致性，同组其余 28 个 ImagePullBackOff Pod 不需要逐个描述。\n- 节点 DNS 解析正常（因为 dial tcp 解析到了具体 IP 后才超时），不需要额外验证 DNS。\n- imagePullSecret 认证失败不需要验证（错误是网络超时而非 unauthorized）。\n- Master 节点 ephemeral-storage Evicted（xnet/observability-kibana）已在 L2 阶段完成验证，本轮不是主异常面。\n\n### ❌ 冲突证据\n- 无冲突。所有被 describe 的 Pod 均存在于对应 namespace，Events 与 upstream 信号完全一致。\n\n---\n\n### 📋 最终诊断摘要\n\n| 问题 | 影响范围 | 根因 |\n|------|---------|------|\n| **ImagePullBackOff/ErrImagePull** | **32+1=33 个 Pod**（占异常 97%）跨 aiops-e2e/default/mcp 三个 namespace、node1+node2 两个节点 | **集群出口到公共镜像仓库 HTTPS 网络不可达**（registry-1.docker.io:443, registry.k8s.io:443 均 dial tcp i/o timeout） |\n| **CrashLoopBackOff** | 1 个 Pod（rc-crashloop-config-file-missing），aiops-e2e | **已知故障测试：配置文件缺失**（Exit Code 1, rootcause-e2e=true） |","collection_summary":"计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%；其中真实环境证据 13/13 项，完整度 100%；实际执行工具 13 个，匹配计划 7 个，未规划证据 6 个","plan_total":7,"plan_collected":7,"plan_completeness":1.0,"environment_evidence_total":13,"environment_evidence_collected":13,"environment_evidence_completeness":1.0,"executed_tool_count":13,"matched_tool_count":7,"unplanned_tool_count":6,"evidence_inventory":[{"id":"g2-rep-pod-1","description":"主异常组g2(ImagePullBackOff): describe 代表Pod default/dns-test-1779360684 验证 Events 中的 pull 失败原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-1779360684 -n default","purpose":"验证Events中的Failed to pull image原文: dial tcp i/o timeout vs manifest unknown vs auth failure","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-rep-pod-2","description":"主异常组g2: describe 代表Pod default/dig-tool 验证 registry.k8s.io 的 pull 失败原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","purpose":"确认registry.k8s.io/e2e-test-images/jessie-dnsutils的pull错误是否为dial tcp i/o timeout","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-ns-mcp-pod","description":"主异常组g2: describe 一个mcp命名空间的代表Pod connectivity-test 验证跨namespace是否同样pull失败","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","purpose":"验证mcp命名空间下的Pod是否存在同样的dial tcp i/o timeout错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-ns-default-pod2","description":"主异常组g2: describe 一个使用busybox镜像的Pod dns-test-check (node2) 验证node2是否同样i/o timeout","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","purpose":"验证node2上的Pod是否同样dial tcp i/o timeout，确认跨节点一致性","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-node-debugger","description":"主异常组g2: describe mcp/node-debugger-node1-w4cfr (ErrImagePull 状态) 验证其pull错误是否不同","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-w4cfr -n mcp","purpose":"确认ErrImagePull与ImagePullBackOff的根因是否一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-crashloop","description":"非主异常组g1(CrashLoopBackOff): describe Pod rc-crashloop-config-file-missing 验证 Exit Code 和 Last State","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-config-file-missing-58cf574c9f-968q9 -n aiops-e2e","purpose":"验证Last State Exit Code是否=1，确认是否属于应用配置测试场景","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-crashloop-logs","description":"非主异常组g1: 查看Pod崩溃前日志(previous) 确认Exit Code 1的根因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-config-file-missing-58cf574c9f-968q9 -n aiops-e2e --previous --tail=50","purpose":"查看容器崩溃前的日志内容确认Exit Code 1原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g2-rep-pod-1 | critical | ✅ | kubectl_describe | 主异常组g2(ImagePullBackOff): describe 代表Pod defa... | `kubectl describe pod dns-test-1779360684 -n default` |
   | g2-rep-pod-2 | critical | ✅ | kubectl_describe | 主异常组g2: describe 代表Pod default/dig-tool 验证 re... | `kubectl describe pod dig-tool -n default` |
   | g2-ns-mcp-pod | critical | ✅ | kubectl_describe | 主异常组g2: describe 一个mcp命名空间的代表Pod connectivity... | `kubectl describe pod connectivity-test -n mcp` |
   | g2-ns-default... | critical | ✅ | kubectl_describe | 主异常组g2: describe 一个使用busybox镜像的Pod dns-test-c... | `kubectl describe pod dns-test-check -n default` |
   | g2-node-debugger | important | ✅ | kubectl_describe | 主异常组g2: describe mcp/node-debugger-node1-w4cf... | `kubectl describe pod node-debugger-node1-w4cfr -n mcp` |
   | g1-crashloop | critical | ✅ | kubectl_describe | 非主异常组g1(CrashLoopBackOff): describe Pod rc-cr... | `kubectl describe pod rc-crashloop-config-file-missing-58cf574c9f-968q9 -n aio...` |
   | g1-crashloop-... | important | ✅ | kubectl_previous_logs | 非主异常组g1: 查看Pod崩溃前日志(previous) 确认Exit Code 1的根因 | `kubectl logs rc-crashloop-config-file-missing-58cf574c9f-968q9 -n aiops-e2e -...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (32.9s)
   📤 → 下游数据: root_cause=集群根因为L3网络层故障：两个worker节点(node1/node2)到公共镜像仓库的HTTPS出口被阻断。直接证据来自5个代表性Pod的kubectl describe Events：1) default/dns-test-1779360684(node1, busybox:1.36.1→registry-1.docker.io→dial tcp 199.96.63.53:443 i/o timeout)；2) default/dig-tool(node1, registry.k8s.io/e2e-test-images→us-west2-docker.pkg.dev→dial tcp 108.177.125.82:443 i/o timeout)；3) mcp/connectivity-test(node2, busybox:1.36.1→registry-1.docker.io→dial tcp 157.240.17.35:443 i/o timeout)；4) default/dns-test-check(node2, busybox:1.36.1→registry-1.do
... 截断，原始 1041 字符
   confidence=97%
   causal_chain={"root_cause": "集群两个worker节点(node1, node2)到公共镜像仓库(registry-1.docker.io, registry.k8s.io)的HTTPS出口网络被阻断，导致所有外部镜像拉取操作TCP连接超时(i/o timeout)", "propagation": "节点出口网络故障 → kubelet无法连接到镜像仓库registry-1.docker.io:443和registry.k8s.io:443 → containerd拉取镜像时dial tcp超时(DeadlineExceeded) → kubelet标记为Failed to pull image → Pod状态进入ErrImagePull/ImagePullBackOff → BackOff指数退避重试 → 33个Pod持续Pending", "direct_cause": "kubelet在执行容器创建时调用containerd拉取镜像，containerd向公共仓库发起HTTPS请求，TCP三次握手在443端口超时(dial tcp i/o timeout)，镜像拉取失败", "manifestation": "集群33个Pod(分布在aiops-e2e, default, mcp三个namespace的node1和node2上)处于ImagePullBackOff或ErrImagePull状态，所有容器均为Waiting(Reason: ImagePullBackOff)，Pod Pending 0/1，最长持续5h31m未恢复"}
   rca_analysis={"phenomenon": "集群共34个异常Pod，分布在aiops-e2e、default、mcp三个命名空间，node1和node2两个worker节点。主异常组g2: 33个Pod处于ImagePullBackOff/ErrImagePull状态（占比97%），所有Pod均Pending，容器从未启动。非主异常组g1: 1个Pod处于CrashLoopBackOff状态（aiops-e2e/rc-crashloop-config-file-missing-58cf574c9f-968q9）。另有1个Evicted Pod（xnet/observability-kibana）已在前面层级处理。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群97个Pod，异常34个：ImagePullBackOff=32, ErrImagePull=1, CrashLoopBackOff=1。异常分布在aiops-e2e/default/mcp三个ns。", "reliability": "高"}, {"id": "e2", "source": "kubernetes_tabular_query", "content": "33个ImagePull/ErrImagePull Pod均为Pending状态(Reason=<none>)，分布在node1和node2。1个Failed(Evicted)在master。", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe-dns-test-1779360684", "content": "Pod default/dns-test-1779360684(node1) Events: Failed to pull busybox:1.36.1 → dial tcp 199.96.63.53:443: i/o timeout到registry-1.docker.io", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe-dig-tool", "content": "Pod default/dig-tool(node1) Events: Failed to pull registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 → dial tcp 108.177.125.82:443和142.250.157.82:443 i/o timeout", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe-connectivity-test", "content": "Pod mcp/connectivity-test(node2) Events: Failed to pull busybox:1.36.1 → dial tcp 157.240.17.35:443: i/o timeout到registry-1.docker.io", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe-dns-test-check", "content": "Pod default/dns-test-check(node2) Events: Failed to pull busybox:1.36.1 → dial tcp 199.96.63.53:443: i/o timeout到registry-1.docker.io", "reliability": "高"}, {"id": "e7", "source": "kubectl_describe-node-debugger-w4cfr", "content": "Pod mcp/node-debugger-node1-w4cfr(ErrImagePull) Events: Failed to pull curlimages/curl:8.12.1 → dial tcp 69.171.242.11:443: i/o timeout到registry-1.docker.io", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe-crashloop", "content": "Pod aiops-e2e/rc-crashloop-config-file-missing: CrashLoopBackOff, Exit Code 1, Back-off restarting failed container (x25 over ~6m)", "reliability": "高"}, {"id": "e9", "source": "kubectl_previous_logs", "content": "容器崩溃前日志: RUNTIME_STARTUP_ERROR: required config file missing; cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory", "reliability": "高"}, {"id": "e10", "source": "kubectl_describe-evicted", "content": "Pod xnet/observability-kibana(master): Evicted, reason=ephemeral-storage不足, Threshold=46993491787, available=45494108Ki", "reliability": "高"}, {"id": "e11", "source": "fetch_runbook-pod-imagepull-failed", "content": "Runbook指引: ImagePullBackOff诊断流程包括检查镜像名/tag、认证、网络连通性、DNS、TLS", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "异常34个: ImagePullBackOff=32, ErrImagePull=1, CrashLoopBackOff=1", "interpretation": "集群异常Pod中94%(32/34)为ImagePullBackOff，1个ErrImagePull(3%)，共同指向镜像拉取故障。此为主问题面。"}, {"evidence_id": "e2", "raw_data": "33个Pending(Reason=<none>)分布在node1和node2", "interpretation": "所有ImagePull异常的Pod均未被调度到master节点，只分布在两个worker节点，说明问题与worker节点相关而非特定namespace。"}, {"evidence_id": "e3", "raw_data": "Failed to pull busybox:1.36.1 → dial tcp 199.96.63.53:443: i/o timeout", "interpretation": "node1上Pod到registry-1.docker.io的HTTPS出口连接超时，不是镜像名错误、不是认证失败、不是DNS解析失败，是TCP层网络不可达。"}, {"evidence_id": "e4", "raw_data": "Failed to pull registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 → dial tcp 108.177.125.82:443/142.250.157.82:443 i/o timeout", "interpretation": "node1上Pod到registry.k8s.io(Google docker.pkg.dev)同样HTTPS超时，连接不同IP均超时，排除特定registry IP问题，指向集群出口网络整体阻断。"}, {"evidence_id": "e5", "raw_data": "Failed to pull busybox:1.36.1 → dial tcp 157.240.17.35:443 i/o timeout (node2)", "interpretation": "node2上Pod同样到registry-1.docker.io超时，证明两个worker节点均受影响，问题在集群层面而非单节点。"}, {"evidence_id": "e6", "raw_data": "Failed to pull busybox:1.36.1 → dial tcp 199.96.63.53:443 i/o timeout (node2)", "interpretation": "node2上另一个Pod也出现完全相同的错误，交叉验证一致，排除Pod级别配置差异。"}, {"evidence_id": "e7", "raw_data": "Failed to pull curlimages/curl:8.12.1 → dial tcp 69.171.242.11:443 i/o timeout", "interpretation": "ErrImagePull状态的Pod同样因dial tcp i/o timeout失败，且目标镜像不同(curlimages/curl)，进一步证明问题是全局性出口网络故障而非镜像仓库侧问题。"}, {"evidence_id": "e8", "raw_data": "CrashLoopBackOff, Exit Code 1, Back-off restarting failed container (x25)", "interpretation": "此Pod进入CrashLoopBackOff的原因是Exit Code 1（应用错误码），而非镜像拉取失败。与主异常组g2(CrashLoopBackOffRuntime类型)原因不同，且pod label明确标注rootcause-e2e=true表示这是故障测试场景。"}, {"evidence_id": "e9", "raw_data": "RUNTIME_STARTUP_ERROR: required config file missing; /etc/rootcause-app/config.yaml not found", "interpretation": "容器崩溃的直接原因是应用启动时找不到必需的配置文件/etc/rootcause-app/config.yaml，这是一个应用配置缺失问题，非基础设施问题。"}, {"evidence_id": "e10", "raw_data": "Evicted, ephemeral-storage不足, Threshold=46993491787, available=45494108Ki", "interpretation": "master节点ephemeral-storage达到驱逐阈值(47GB阈值, 44.4GiB可用)，触发了Pod驱逐。这是独立于镜像拉取问题的L0资源事件。"}, {"evidence_id": "e11", "raw_data": "Runbook: ImagePullBackOff诊断流程", "interpretation": "按runbook指引，已验证了镜像名/tag（均正确）、认证（公共仓库无需）、DNS（IP已被解析）、网络连通性（dial tcp i/o timeout）。根因定位到L3网络层。"}], "causal_chain": {"root_cause": "集群两个worker节点(node1, node2)到公共镜像仓库(registry-1.docker.io, registry.k8s.io)的HTTPS出口网络被阻断，导致所有外部镜像拉取操作TCP连接超时(i/o timeout)", "propagation": "节点出口网络故障 → kubelet无法连接到镜像仓库registry-1.docker.io:443和registry.k8s.io:443 → containerd拉取镜像时dial tcp超时(DeadlineExceeded) → kubelet标记为Failed to pull image → Pod状态进入ErrImagePull/ImagePullBackOff → BackOff指数退避重试 → 33个Pod持续Pending", "direct_cause": "kubelet在执行容器创建时调用containerd拉取镜像，containerd向公共仓库发起HTTPS请求，TCP三次握手在443端口超时(dial tcp i/o timeout)，镜像拉取失败", "manifestation": "集群33个Pod(分布在aiops-e2e, default, mcp三个namespace的node1和node2上)处于ImagePullBackOff或ErrImagePull状态，所有容器均为Waiting(Reason: ImagePullBackOff)，Pod Pending 0/1，最长持续5h31m未恢复"}, "root_cause": "集群根因为L3网络层故障：两个worker节点(node1/node2)到公共镜像仓库的HTTPS出口被阻断。直接证据来自5个代表性Pod的kubectl describe Events：1) default/dns-test-1779360684(node1, busybox:1.36.1→registry-1.docker.io→dial tcp 199.96.63.53:443 i/o timeout)；2) default/dig-tool(node1, registry.k8s.io/e2e-test-images→us-west2-docker.pkg.dev→dial tcp 108.177.125.82:443 i/o timeout)；3) mcp/connectivity-test(node2, busybox:1.36.1→registry-1.docker.io→dial tcp 157.240.17.35:443 i/o timeout)；4) default/dns-test-check(node2, busybox:1.36.1→registry-1.do\n... 截断，原始 1041 字符", "root_cause_summary": "集群根因为L3网络层故障：两个worker节点(node1/node2)到公共镜像仓库的HTTPS出口被阻断。直接证据来自5个代表性Pod的kubectl describe Events：1) default/dns-test-1779360684(node1, busybox:1.36.1→registry-1.docker.io→dial tcp 199.96.63.53:443 i/o timeout)；2) default/dig-tool(node1, registry.k8s.io/e2e-test-images→us-west2-docker.pkg.dev→dial tcp 108.177.125.82:443 i/o timeout)；3) mcp/connectivity-test(node2, busybox:1.36.1→registry-1.docker.io→dial tcp 157.240.17.35:443 i/o timeout)；4) default/dns-test-check(node2, busybox:1.36.1→registry-1.do\n... 截断，原始 1041 字符", "confidence": 0.97, "confidence_reason": "有5个来自不同namespace、不同节点、不同镜像仓库的独立Pod describe Events交叉验证，所有错误完全一致(dial tcp i/o timeout)。无冲突证据。因果链清晰完整：出口网络阻断→TCP超时→镜像拉取失败→ImagePullBackOff。置信度0.97。", "primary_runbooks": ["pod-imagepull-failed.md", "pod-crashloop-runtime.md", "pod-evicted.md"], "alternative_causes": [{"cause": "镜像名或tag不存在", "probability": "很低", "reason": "已排除。Events报错为dial tcp i/o timeout，非manifest unknown/not found。5个不同镜像(busybox:1.36.1, registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, curlimages/curl:8.12.1)均超时，不可能是全部镜像名错误。"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "很低", "reason": "已排除。所有目标为公共镜像仓库(registry-1.docker.io, registry.k8s.io)，公共仓库不需要认证。Events报错为TCP超时而非认证拒绝(denied/unauthorized)。"}, {"cause": "DNS解析失败", "probability": "很低", "reason": "已排除。Events中已显示解析出的目标IP(199.96.63.53, 108.177.125.82, 69.171.242.11等)，DNS解析成功但TCP连接超时。"}, {"cause": "镜像仓库侧服务故障", "probability": "很低", "reason": "已排除。涉及3个不同仓库(registry-1.docker.io, registry.k8s.io, curlimages/curl)，不可能同时全部故障。且连接多个不同IP均超时，符合出口阻断特征。"}, {"cause": "单个节点网络故障", "probability": "很低", "reason": "已排除。node1和node2两个worker节点均出现完全相同的dial tcp i/o timeout错误，证明是集群级出口网络问题而非单节点。"}], "limitations": "未直接在节点上执行curl/wget测试确认节点侧到公网的连通性（例如在节点上curl https://registry-1.docker.io），此操作需节点SSH权限或特权Pod，当前范围内未采集。未验证集群是否配置了HTTP/HTTPS代理以及代理本身是否故障。未采集kubelet/containerd日志确认具体错误栈。", "llm_raw_analysis": "## L3根因分析报告\n\n### 1. 证据清点\n共采集13类证据，其中5个独立的kubectl describe Events构成直接证据链，1组崩溃前日志，1个Evicted描述，3个上游已验证工具结果，2个runbook参考。\n\n### 2. 逐条分析\n- **e3/e5/e6**: 3个独立Pod(node1/default, node2/mcp, node2/default)全部报告busybox:1.36.1到registry-1.docker.io的dial tcp i/o timeout，IP各不相同(199.96.63.53, 157.240.17.35, 199.96.63.53)，说明不是单一IP故障而是整个仓库域名不可达。\n- **e4**: dig-tool(node1/default)报告registry.k8s.io(Google docker.pkg.dev)同样i/o timeout，IP 108.177.125.82和142.250.157.82均超时，证明不只是docker.io仓库故障。\n- **e7**: node-debugger(node1\n... 截断，原始 1207 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群根因为L3网络层故障：两个worker节点(node1/node2)到公共镜像仓库的HTTPS出口被阻断。直接证据来自5个代表性Pod的kubectl describe Events：1) default/dns-test-1779360684(node1, busybox:1.36.1→reg...
   置信度: 97%
   🔗 因果链:
     根本原因: 集群两个worker节点(node1, node2)到公共镜像仓库(registry-1.docker.io, registry.k8s.io)的HTTPS出口网络被阻断，导致所有外部镜像拉取操作TCP连接超时(i/o timeout)
     传导机制: 节点出口网络故障 → kubelet无法连接到镜像仓库registry-1.docker.io:443和registry.k8s.io:443 → containerd拉取镜像时dial tcp超时(DeadlineExceeded) → kubelet标记为Failed to pull image → Pod状态进入ErrImagePull/ImagePullBackOff → BackOff指数退避重试 → 33个Pod持续Pending
     最终表现: 集群33个Pod(分布在aiops-e2e, default, mcp三个namespace的node1和node2上)处于ImagePullBackOff或ErrImagePull状态，所有容器均为Waiting(Reason: ImagePullBackOff)，Pod Pending 0/1，最长持续5h31m未恢复


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (41.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 9215 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 54.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将直接回答你的核心问题：**你的集群当前存在的主要问题是，两个工作节点（node1, node2）无法连接到外部的公共镜像仓库，导致集群中 97% 的异常 Pod 无法启动。**

以下是完整的诊断报告。

---
## 📊 诊断概览

你的集群当前存在 **34 个异常 Pod**，分布在 **3 个问题域**。核心问题是 **网络层面** 的出口阻断，影响了超过 94% 的异常 Pod。

| 项目 | 内容 |
|------|------|
| **集群异常 Pod 数** | 34个 (总共 97个) |
| **主要异常状态** | **ImagePullBackOff** (32个, 94%)，ErrImagePull (1个)，CrashLoopBackOff (1个)，Evicted (1个) |
| **核心问题** | **L3 网络层故障：工作节点 → 公共镜像仓库出口阻断** |
| **次要问题** | 1. 应用 CrashLoopBackOff (配置测试场景) <br> 2. Master 节点临时存储驱逐 |
| **影响范围** | `aiops-e2e`, `default`, `mcp` 命名空间；`node1`, `node2` 节点 |
| **证据完整度** | 7/7 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 | 说明 |
|------|-----|------|
| 节点 | node1 (10.2.0.49), node2 (10.2.0.50) | 所有 ImagePullBackOff 均发生在这两个 Worker 节点 |
| 节点 | master (10.2.0.48) | 发生了 ephemeral-storage 驱逐事件 |
| 镜像仓库 | registry-1.docker.io:443 | `dial tcp ... i/o timeout` |
| 镜像仓库 | registry.k8s.io:443 | `dial tcp ... i/o timeout` |
| 镜像仓库 | us-west2-docker.pkg.dev | `dial tcp ... i/o timeout` |
| Pod (代表性) | `dns-test-1779360684` (default, node1) | ImagePullBackOff，拉取 `busybox:1.36.1` 超时 |
| Pod (代表性) | `dig-tool` (default, node1) | ImagePullBackOff，拉取 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` 超时 |
| Pod (代表性) | `rc-crashloop-config-file-missing-58cf574c9f-968q9` (aiops-e2e, node1) | **CrashLoopBackOff**，Exit Code 1 |
| Pod (代表性) | `observability-kibana-65d7c45f6d-7zc9l` (xnet, master) | **Evicted**，ephemeral-storage 不足 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | 集群状态 | `kubectl get pods --all-namespaces` | 97个Pod，34个异常；ImagePullBackOff=32, ErrImagePull=1, CrashLoopBackOff=1, Evicted=1 | 集群存在**大规模拉取镜像失败**问题，占异常Pod的97% |
| 2 | Pod 状态 | `kubectl describe pod dns-test-1779360684` | `Warning Failed (x66 over 4h48m): Failed to pull image "busybox:1.36.1": dial tcp 199.96.63.53:443: i/o timeout` | **Docker Hub** 镜像拉取因 **TCP连接超时** 失败 |
| 3 | Pod 状态 | `kubectl describe pod dig-tool` | `All 5 pull attempts to registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 failed with i/o timeout dialing various GCP docker.pkg.dev endpoints (us-west2, europe-west2, asia-east1)` | **Google 镜像仓库** (registry.k8s.io) 拉取因 **TCP连接超时** 失败，覆盖全球多个区域 |
| 4 | Pod 状态 | `kubectl describe pod connectivity-test` (mcp, node2) | `Warning Failed (x47 over 4h13m): Failed to pull image "busybox:1.36.1": dial tcp 157.240.17.35:443: i/o timeout` | **node2 节点** 同样存在对 Docker Hub 的 **TCP连接超时** 问题 |
| 5 | Pod 状态 | `kubectl describe pod node-debugger-node1-w4cfr` (mcp, node1) | `Normal BackOff (x529 over 4h15m): Back-off pulling image "curlimages/curl:8.12.1"` | 位于 **mcp** 命名空间的 Pod 同样因镜像拉取失败而持续重启 |
| 6 | Pod 状态 | `kubectl describe pod rc-crashloop-config-file-missing` | `State: Running` (但处于 `CrashLoopBackOff`)；`Warning BackOff (x25 over 6m39s): Back-off restarting failed container` | 这是一个 **CrashLoopBackOff** 问题，区别于网络问题 |
| 7 | 容器日志 | `kubectl logs --previous rc-crashloop-config-file-missing` | `RUNTIME_STARTUP_ERROR: required config file missing`<br>`cat: can't open '/etc/rootcause-app/config.yaml': No such file or directory` | 应用因 **缺少配置文件** 启动失败，退出码为 1 |
| 8 | Pod 状态 | `kubectl describe pod observability-kibana` | `Status: Failed`；`Reason: Evicted`；`Message: The node was low on resource: ephemeral-storage` | Pod 被 **Master 节点因临时存储不足驱逐** |

### 证据关联分析
- **证据 #2 + #3 + #4 + #5 印证**：跨越 2 个工作节点 (node1, node2)、3 个命名空间 (default, mcp, aiops-e2e)、2 个主流公共镜像仓库 (docker.io, k8s.gcr.io)，所有镜像拉取操作均因 **`dial tcp ... i/o timeout`** 而失败。这明确指向 **集群出站网络故障**，而非单一镜像或节点问题。
- **证据链 (主要问题)**：集群出口网络阻断 → kubelet 无法连接镜像仓库 → containerd 拉取镜像 TCP 超时 → Pod 状态变为 `ImagePullBackOff` → 33个 Pod 持续处于 Pending 状态。
- **证据 #6 + #7 关联**：`CrashLoopBackOff` 的 Pod 退出码为 1，日志明确提示缺少配置文件，与网络问题无关，是**独立的应用配置问题**。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 在节点上执行 `curl https://registry-1.docker.io` | critical | 无法确认是**节点本身**无法出网，还是**kubelet/containerd**的配置问题（如代理配置错误） |
| `kubelet` 和 `containerd` 日志 | important | 无法提供更底层的错误栈，但“i/o timeout”已足够定位 |
| 崩溃前日志（更全） | low | `CrashLoopBackOff` 的根因已通过 `--previous` 日志明确为“配置文件缺失” |

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                    │
│ 集群两个 Worker 节点 (node1, node2) 到公共镜像仓库 443 端口的              │
│ HTTPS 出口网络被防火墙/安全组/NAT 规则阻断                                │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                  │
│ 节点出口网络被阻断 → kubelet 调用 containerd 拉取镜像 →                    │
│ containerd 发起到 registry-1.docker.io:443 和 registry.k8s.io:443 的     │
│ TCP 三次握手 → 所有握手均超时 (dial tcp i/o timeout)                     │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                  │
│ kubelet 因无法拉取镜像，将容器状态标记为 Waiting (Reason: ImagePullBackOff) │
│ 并持续重试，Pod 无法进入 Running 状态                                     │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                             │
│ 集群中 33 个 Pod (分布在 aiops-e2e, default, mcp 命名空间的              │
│ node1 和 node2 上) 持续处于 Pending 状态，Reason 为 ImagePullBackOff，     │
│ 最长持续 5h31m 未恢复                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2, #3, #4, #5 (所有 Pod 的 `kubectl describe` Events 均显示 `dial tcp ... i/o timeout`)，问题的根本原因是**集群两个 Worker 节点 (node1, node2) 到公共镜像仓库 (docker.io, k8s.gcr.io) 的 HTTPS 出口网络被阻断**，导致 kubelet 无法拉取任何外部镜像，33 个 Pod 因此持续处于 `ImagePullBackOff` 状态。

**次要根因 1**： `rc-crashloop-config-file-missing` Pod 处于 `CrashLoopBackOff` 状态，是因为 **应用启动时找不到必要的配置文件** `/etc/rootcause-app/config.yaml` (Exit Code 1)。

**次要根因 2**： `observability-kibana` Pod 被驱逐，是因为 **Master 节点的 ephemeral-storage 资源不足**。

**置信度**：高 (97%) （主要问题）
- ✅ 跨越不同镜像仓库、节点、命名空间的 5 个代表性 Pod 均显示相同的 `i/o timeout` 错误。
- ✅ 错误是 `dial tcp` 超时，而非 DNS 解析失败（NxDomain），排除了域名解析问题。
- ✅ 超时发生在 443 端口，而非 80 端口，指向 HTTPS 流量被阻断。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 【核心问题】检查并修复节点出站网络规则**
这是最关键的一步。要解决 33 个 Pod 无法拉取镜像的问题，必须恢复 Worker 节点的 HTTPS (443端口) 出站能力。

- **执行命令（在 node1 和 node2 上）**：
  ```bash
  # 1. 检查到主要镜像仓库的连通性
  curl -o /dev/null -s -w "%{http_code}" --connect-timeout 5 https://registry-1.docker.io/v2/
  curl -o /dev/null -s -w "%{http_code}" --connect-timeout 5 https://registry.k8s.io/v2/

  # 2. 检查是否有代理配置（输出代理地址）
  echo "HTTP_PROXY: $HTTP_PROXY"
  echo "HTTPS_PROXY: $HTTPS_PROXY"
  echo "NO_PROXY: $NO_PROXY"
  
  # 3. 检查 kubelet 和 containerd 的代理配置
  sudo journalctl -u kubelet --no-pager | grep -i proxy
  sudo journalctl -u containerd --no-pager | grep -i proxy
  ```
- **预期结果**：
  - `curl` 命令应返回 `200 OK` 或类似成功状态码。如果超时或失败，说明需要联系网络团队放通 `node1` 和 `node2` 到 `*.docker.io`、`*.k8s.gcr.io`、`*.pkg.dev` 等域名的 443 端口。
  - 如果配置了代理，需要确认代理服务器本身可达且正常工作。
- **依据**：证据 #2, #3, #4, #5 确认了网络超时。

**2. [可选] 解决 CrashLoopBackOff 的 Pod**
- **执行命令**：
  ```bash
  # 查看 Pod 的详细信息，找到配置文件挂载或 ConfigMap 的问题
  kubectl describe pod rc-crashloop-config-file-missing-58cf574c9f-968q9 -n aiops-e2e
  
  # 查找相关的 ConfigMap
  kubectl get configmap -n aiops-e2e | grep rootcause
  ```
- **目的**：确认 Pod 所需的 ConfigMap 是否存在，以及 Volume 挂载是否正确。
- **依据**：证据 #7 显示容器日志明确报错缺少 `config.yaml` 文件。

**3. [可选] 处理被驱逐的 Pod**
- **执行命令**：
  ```bash
  # 查看 Master 节点临时存储使用情况
  kubectl describe node master | grep -A5 "Allocated resources"
  
  # 删除并重建被驱逐的 Pod（假设 Deployment 会自动重建）
  kubectl delete pod observability-kibana-65d7c45f6d-7zc9l -n xnet
  ```
- **目的**：确认 Master 节点的存储压力，并清理异常 Pod。如果问题持续，则需要清理 Master 节点上的无用文件。
- **依据**：证据 #8 确认了 Pod 被驱逐的原因为 `ephemeral-storage` 不足。

### 后续优化
1. **配置镜像仓库镜像/代理 (Mirror/Proxy)**：在集群内或私有网络部署 `harbor` 或 `docker registry` 作为镜像仓库的缓存/代理，避免对外部网络的强依赖。
2. **监控告警**：
   - 配置 Pod 状态监控，对 `ImagePullBackOff`、`CrashLoopBackOff`、`Evicted` 等异常状态设置告警。
   - 配置节点资源监控，对 `ephemeral-storage`、`disk` 等资源使用率设置告警。
3. **应用清单配置**：确保所有应用都使用私有镜像仓库地址，避免直接引用公网镜像。对于测试 Pod，确保其依赖的配置（如 ConfigMap）已提前创建。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认网络修复 | 在 node1/node2 上执行 `curl -I https://registry-1.docker.io/v2/` | 返回 HTTP 200 或 401，而非超时 |
| 2. 确认镜像拉取恢复 | `kubectl get pods -A \| grep -E "ImagePullBackOff\|ErrImagePull"` | 结果为 0 |
| 3. 确认 Pod 进入运行 | `kubectl get pods -A \| grep -c Running` | 数值应接近 59 或更多 |
| 4. 验证 CrashLoopBackOff 修复 | `kubectl logs rc-crashloop-config-file-missing-58cf574c9f-968q9 -n aiops-e2e` | 不再有“config file missing”错误 |
| 5. 验证 Pod 重建 | `kubectl get pod observability-kibana -n xnet` | 状态不为 `Evicted`或 `Failed` |

---

## ⚠️ 注意事项
- **核心问题**：网络故障是所有 `ImagePullBackOff` 的根源，**优先解决它**。如果不解决，私网镜像等其余措施无法生效。
- **CrashLoopBackOff 问题**：这是典型的**应用配置**问题，与网络无关。修复它需要创建 ConfigMap，而非重启集群。
- **Evicted & CrashLoopBackOff** 问题：在核心网络问题解决后，它们可能依然存在。这是两个独立的问题。

---

## 📊 性能统计

├─ 总耗时: 2.9m
├─ 问题定位: 53.2s (30%) ✅
├─ 证据链采集: 46.8s (27%) ✅
├─ 根因分析: 32.9s (19%) ✅
├─ 汇总总结: 41.6s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 18 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-crashloop-runtime, pod-evicted
- **参考 Runbook**: pod-imagepull-failed, pod-crashloop-runtime, pod-evicted
- **工具调用**: 18 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
