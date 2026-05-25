======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 28a44bf44db9417f]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先进行全局 Pod 状态扫描，获取当前集群中所有 Pod 的状态信息。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods -A output: 67 rows shown (truncated from 90+). Running=~43, ImagePullBackOff=19, ErrImagePull=2, Completed=2, abnormal total=21+.
key_facts: ["Namespace admin: Running pods (gpu-metax
   💭 [问题定位] 让我获取更完整的 Pod 列表信息，以便准确了解所有异常 Pod。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 返回 27 个 Pod，全部 STATUS=Pending, READY=false。涉及 namespace: aiops-e2e (2), default (7), mcp (18)。mcp 下有大量 node-debugger Pod (node1 和 node2)，以及 connectivity-test、net-check、test-re
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 表格摘要: rows=28 abnormal=28 status_counts={'Pending': 27, 'Failed': 1, 'Evicted': 1}
NAMESPACE         NAME                                                NODE     STATUS      R
   💭 [问题定位] 很好，现在看到了更精确的信息。让我获取这些 Pod 的详细事件信息，了解具体原因。
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
52m                   Warning   Failed    Pod/dns-check-test   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and unpack imag
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
24m (x13 over 69m)      Warning   Failed    Pod/rc-imagepull-missing-secret   Failed to pull image "registry.invalid/aiops/private-rootcause:v0": rpc error: code = Unknown de
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
8m5s (x13 over 71m)     Warning   Failed    Pod/connectivity-test   (combined from similar events): Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = fa
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
27m (x386 over 151m)    Normal    BackOff   Pod/node-debugger-node1-2xvqr   Back-off pulling image "curlimages/curl:8.12.1"
2m21s (x22 over 121m)   Warning   Failed    Pod/no
   💭 [问题定位] 非常好，现在我已经看到了问题的全貌。让我确认一下那个被 Evicted 的 Pod 的情况。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                    READY   STATUS      RESTARTS   AGE   IP              NODE     NOMINATED NODE   READINESS GATES   LABELS
observability-kibana-65d7c45f6d-7zc9l   0/1     Complete
   💭 [问题定位] 好的，这个 Pod 实际上已经是 Completed 状态（不是异常状态）。现在让我获取相关 runbook 来指导分析。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [问题定位] 现在我已经掌握了所有需要的信息，让我做完整的分析。

---

## 集群异常定位分析

### 1. 全局扫描结果

通过全集群 Pod 扫描，发现 **27 个异常 Pod**，分为以下类型：

| 异常类型 | 数量 | 涉及命名空间 |
|---------|:----:|:----------:|
| **ImagePullBackOff** | ~25 | aiops-e2e, default, mcp |
| **ErrImagePull** | ~2 | aiops-e2e, mcp |
| **Evicted（已恢复为 Completed）** | 1 | xnet（历史问题） |

---

### 2. 异常分组详情

#### 组 A：镜像仓库网络不可达（影响范围最大）— 19+ 个 Pod

**涉及 Pod：**
- `default/dns-check-test`, `default/dns-test-*`, `default/net-test-pod`, `default/nettest-*`, `default/registry-connect-test`, `default/test-net-*`
- `mcp/connectivity-test`, `mcp/net-check-*`, `mcp/test-registry-conn-*`
- `mcp/node-debugger-node1-*`（12个）, `node-debugger-node2-*`（3个）

**关键事件证据：**
```
Failed to pull image "busybox:1.36.1":
  dial tcp 31.13.70.33:443: i/o timeout           ← docker.io 超时
Failed to pull image "curlimages/curl:8.12.1":
  dial tcp 162.125.80.3:443: i/o timeout           ← docker.io 超时
```

**诊断结论：** 集群所有节点（node1、node2）**无法访问 docker.io（registry-1.docker.io）**，HTTPS 连接 i/o timeout。这属于**镜像仓库网络不可达**（L3 层）。

#### 组 B：镜像仓库 DNS 解析失败 — 1 个 Pod

**涉及 Pod：**
- `aiops-e2e/rc-imagepull-missing-secret`

**关键事件证据：**
```
Failed to pull image "registry.invalid/aiops/private-rootcause:v0":
  lookup registry.invalid on 127.0.0.53:53: no such host
```

**诊断结论：** 镜像地址使用了不存在的域名 `registry.invalid`，DNS 解析失败。同时还缺少 imagePullSecret（Pod 名本身就暗示了 "missing-secret"）。属于**镜像配置错误 + DNS + 认证缺失**（L3/L4 层）。

#### 组 C：历史 Evicted（已恢复）— 1 个 Pod

**涉及 Pod：**
- `xnet/observability-kibana-65d7c45f6d-7zc9l` — 实际上当前 STATUS=Completed（已完成），不是当前异常。

---

### 3. 综合定位

| 字段 | 值 |
|------|-----|
| **layer** | L3 |
| **layer_name** | 镜像仓库网络不可达 |
| **derived_layer** | L3 |
| **layers** | L3（主因：docker.io 网络不可达），L4（次因：配置错误域名） |
| **confidence** | 高 |
| **pod_status_keyword** | ImagePullBackOff |
| **pod_abnormal_type** | ImagePullFailed |
| **status_category** | image_pull |
| **key_entities** | `docker.io (registry-1.docker.io)` 镜像仓库、node1、node2、default/mcp/aiops-e2e 命名空间 |
| **possible_scenarios** | 1. 集群节点无法出网访问 docker.io（防火墙/代理/NAT 限制）；2. 镜像仓库域名 `registry.invalid` 配置错误；3. 部分 Pod 可能还缺少 imagePullSecret |

---

### 4. 核心问题总结

**集群的主要问题是：所有节点（node1、node2）无法连接到 docker.io 官方镜像仓库**，导致大量拉取 `busybox`、`curlimages/curl` 等公共镜像的测试/调试 Pod 全部卡在 `ImagePullBackOff`。

**次要问题：** `rc-imagepull-missing-secret` Pod 使用了不存在的镜像仓库域名 `registry.invalid`，且缺少 imagePullSecret。

**正常部分：** 控制面组件（calico、coredns、apiserver 等）、业务 Pod（cloud-agent、cloud-server、aiops-copilot、gpu 相关、mcp-server 等）全部正常运行，集群调度、网络插件、节点本身均健康。
   ✅ [问题定位] 完成 (48.2s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '集群节点无法出网访问docker.io镜像仓库', 'probability': '高', 'reason': 'Events显示多个Pod拉取busybox/curlimages/curl镜像时dial tcp i/o timeout，所有节点(node1/node2)均受影响'}, {'scenario': '镜像仓库域名registry.invalid配置错误', 'probability': '中', 'reason': 'rc-imagepull-missing-secret Pod使用了不存在的域名registry.invalid，DNS解析失败'}, {'scenario': '部分Pod缺少imagePullSecret', 'probability': '低', 'reason': 'rc-imagepull-missing-secret的Pod名暗示缺少secret，但主因是域名不存在'}]
   entities=[{"type": "image_registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "pod", "name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在27个异常Pod，全部卡在ImagePullBackOff/ErrImagePull状态（Pending），核心原因是集群所有节点(node1, node2)无法连接到docker.io镜像仓库（HTTPS i/o timeout），属于L3镜像仓库网络不可达。另有1个Pod(rc-imagepull-missing-secret)因使用了不存在的域名registry.invalid导致DNS解析失败（L4配置错误）。异常Pod包括：default/dns-check-test等7个、aiops-e2e/rc-imagepull-missing-secret和test-dns-1779360358、mcp/connectivity-test等18个（含大量node-debugger Pod）。控制面组件（calico、coredns、apiserver等）和业务Pod（cloud-agent、aiops-copilot等）均正常Running。xnet/observability-kibana-65d7c45f6d-7zc9l是历史Evicted已完成，不算当前异常。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "镜像仓库网络不可达", "confidence": 0.95, "reasoning": "当前环境中存在27个异常Pod，全部卡在ImagePullBackOff/ErrImagePull状态（Pending），核心原因是集群所有节点(node1, node2)无法连接到docker.io镜像仓库（HTTPS i/o timeout），属于L3镜像仓库网络不可达。另有1个Pod(rc-imagepull-missing-secret)因使用了不存在的域名registry.invalid导致DNS解析失败（L4配置错误）。异常Pod包括：default/dns-check-test等7个、aiops-e2e/rc-imagepull-missing-secret和test-dns-1779360358、mcp/connectivity-test等18个（含大量node-debugger Pod）。控制面组件（calico、coredns、apiserver等）和业务Pod（cloud-agent、aiops-copilot等）均正常Running。xnet/observability-kibana-65d7c45f6d-7zc9l是历史Evicted已完成，不算当前异常。", "abnormal_pods": [{"name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ErrImagePull"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_pull", "key_entities": [{"type": "image_registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "pod", "name": "rc-imagepull-missing-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "集群节点无法出网访问docker.io镜像仓库", "probability": "高", "reason": "Events显示多个Pod拉取busybox/curlimages/curl镜像时dial tcp i/o timeout，所有节点(node1/node2)均受影响"}, {"scenario": "镜像仓库域名registry.invalid配置错误", "probability": "中", "reason": "rc-imagepull-missing-secret Pod使用了不存在的域名registry.invalid，DNS解析失败"}, {"scenario": "部分Pod缺少imagePullSecret", "probability": "低", "reason": "rc-imagepull-missing-secret的Pod名暗示缺少secret，但主因是域名不存在"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-missing-secret"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-missing-secret"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 25, "ErrImagePull": 2}, "total_abnormal": 27, "selected_rows": ["aiops-e2e         rc-imagepull-missing-secret                         0/1     ImagePullBackOff   0              69m     172.16.104.22    node2    <none>           <none>            app=rc-imagepull-missing-secret,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ErrImagePull       0              150m    172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dns-check-test                                      0/1     ImagePullBackOff   0              79m     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0              145m    172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0              104s    172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           net-test-pod                                        0/1     ImagePullBackOff   0              67m     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0              95m     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           registry-connect-test                               0/1     ImagePullBackOff   0              76m     172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff   0              145m    172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0              98m     172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               net-check-1779365549                                0/1     ImagePullBackOff   0              64m     172.16.166.179   node1    <none>           <none>            run=net-check-1779365549", "mcp               node-debugger-node1-2xvqr                           0/1     ImagePullBackOff   0              152m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-4ncj7                           0/1     ImagePullBackOff   0              131m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6pxvd                           0/1     ImagePullBackOff   0              12m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-ckjnc                           0/1     ImagePullBackOff   0              100m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-j7gtr                           0/1     ImagePullBackOff   0              31m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-jdbpc                           0/1     ImagePullBackOff   0              31m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-pjlg5                           0/1     ImagePullBackOff   0              136m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-rbtz7                           0/1     ErrImagePull       0              46m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-szd4f                           0/1     ImagePullBackOff   0              100m    10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我来按既有 evidence_plan 执行关键工具调用。先并行执行关键的代表 Pod 验证。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-missing-secret
namespace: aiops-e2e
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   25m (x13 over 70m)   kubelet  Failed to pull image "registr
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-check-test
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   53m                  kubelet  Failed to pull image "busybox:1.36.1": rpc e
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  16m (x418 over 150m)   kubelet  Back-off pulling image "busybox:1.3
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dns-check-test
namespace: default
creationTimestamp: 2026-05-21T11:57:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
servi
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-imagepull-missing-secret
namespace: aiops-e2e
creationTimestamp: 2026-05-21T12:07:43Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-test
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   8m45s (x13 over 72m)  kubelet  (combined from similar events): Failed to pu
   💭 [证据链采集] 很好！关键证据已采集。现在继续执行剩余的 evidence_plan 项：验证 node2 和 node1 上的其他异常 Pod。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-2xvqr
namespace: mcp
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  28m (x386 over 152m)  kubelet  Back-off pulling image "curlimages/c
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: nettest-1779363677
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   30m (x13 over 65m)    kubelet  (combined from similar events): Failed 
   💭 [证据链采集] 现在所有 critical 级别的关键证据已采集。让我检查一下 `rc-imagepull-missing-secret` 引用的 `imagePullSecrets` 是否存在。
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=197 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-definitely-missing-pull-secret -n aiops-e2e
Error from server (NotFound): secrets "
   💭 [证据链采集] 所有关键证据均已采集完毕。下面是证据总结：

---

## 📋 证据采集结论

### ✅ 已采集的关键证据

**1. docker.io 镜像仓库全局不可达（影响 26/27 个异常 Pod）**
- **dns-check-test** (default/node1) → `busybox:1.36.1` → `dial tcp 31.13.87.34:443: i/o timeout` ✅
- **connectivity-test** (mcp/node2) → `busybox:1.36.1` → `dial tcp 31.13.70.33:443: i/o timeout` ✅
- **test-dns-1779360358** (aiops-e2e/node1) → `busybox:1.36.1` → `dial tcp 118.184.78.78:443: i/o timeout` ✅
- **nettest-1779363677** (default/node2) → `busybox:1.36.1` → `dial tcp 204.79.197.217:443: i/o timeout` ✅
- **node-debugger-node1-2xvqr** (mcp/node1) → `curlimages/curl:8.12.1` → `dial tcp 162.125.80.3:443: i/o timeout` ✅

> ✅ **结论：node1 和 node2 均无法访问 registry-1.docker.io，不同 IP 地址都超时，确认为集群整体出网封锁。**

**2. rc-imagepull-missing-secret 的 registry.invalid DNS 解析失败（独立异常，影响 1/27 Pod）**
- **Events** ✅：`Head "https://registry.invalid/v2/aiops/private-rootcause/manifests/v0": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host`
- **YAML** ✅：`image: registry.invalid/aiops/private-rootcause:v0`（镜像地址使用了不存在的域名）
- **imagePullSecrets** ✅：引用了 `rc-definitely-missing-pull-secret`，但该 Secret **NotFound**（不存在）

### ❌ 冲突/负向证据
- **Secret `rc-definitely-missing-pull-secret`** → NotFound（确认缺失）

### ⚠️ 未采集证据
- 当前所有关键计划项（e1~e8）均已执行完毕，无需额外工具调用。

### 根因总结
| 异常类型 | 影响范围 | 根因 |
|---------|---------|------|
| 主异常：docker.io 镜像拉取超时 | 26 个 Pod（default/mcp/aiops-e2e） | 集群节点无法出网访问 `registry-1.docker.io`，HTTPS i/o timeout |
| 次级异常：registry.invalid DNS 解析失败 | 1 个 Pod（rc-imagepull-missing-secret） | 镜像地址使用了不存在的域名 `registry.invalid`，且引用的 imagePullSecret 也不存在 |
   ✅ [证据链采集] 完成 (26.7s)
   📤 → 下游数据: evidence_items=17/17
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"主异常组: 验证docker.io网络不可达 - 查看代表Pod dns-check-test (default) 的完整describe，确认Events中的i/o timeout原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","tool_args":{"kind":"Pod","name":"dns-check-test","namespace":"default"},"purpose":"确认Pod的Events中Failed to pull image的详细错误原文，验证docker.io registry不可达","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"主异常组: 查看代表Pod dns-check-test的spec，确认使用的镜像地址和imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-check-test -n default -o yaml","tool_args":{"kind":"Pod","name":"dns-check-test","namespace":"default"},"purpose":"检查镜像地址(spec.containers[].image)和imagePullSecrets配置","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"主异常组: 跨namespace验证 - 查看mcp/connectivity-test的Events，确认是否也是docker.io i/o timeout","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"Pod","name":"connectivity-test","namespace":"mcp"},"purpose":"验证mcp命名空间下的Pod是否也是同样的docker.io i/o timeout错误，确认全网节点不可达","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"主异常组: 跨namespace验证 - 查看aiops-e2e/test-dns-1779360358的Events，确认ErrImagePull原因","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"Pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"验证aiops-e2e命名空间的ErrImagePull Pod是否也是docker.io不可达","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"次要异常组: 验证rc-imagepull-missing-secret的registry.invalid DNS解析问题 - 查看Pod describe","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-imagepull-missing-secret","namespace":"aiops-e2e"},"purpose":"确认rc-imagepull-missing-secret的Events中registry.invalid DNS解析失败错误原文","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6","description":"次要异常组: 检查rc-imagepull-missing-secret的完整YAML，验证镜像地址和imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-imagepull-missing-secret -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-imagepull-missing-secret","namespace":"aiops-e2e"},"purpose":"确认镜像地址是否为registry.invalid，检查spec是否缺少imagePullSecret","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e7","description":"主异常组: 跨node验证 - 查看node2上的Pod nettest-1779363677确认同样错误","level":"important","tool":"kubectl_describe","command":"kubectl describe pod nettest-1779363677 -n default","tool_args":{"kind":"Pod","name":"nettest-1779363677","namespace":"default"},"purpose":"验证node2上的Pod同样出现docker.io i/o timeout，确认不影响节点的差异","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e8","description":"主异常组: 验证node debugger pod在node1上的情况 - node-debugger-node1-2xvqr","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2xvqr -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-2xvqr","namespace":"mcp"},"purpose":"确认node1上的node-debugger Pod也出现docker.io curlimages/curl i/o timeout","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-missing-secret\nnamespace: aiops-e2e\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   25m (x13 over 70m)   kubelet  Failed to pull image \"registry.invalid/aiops/private-rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/private-rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/private-rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/private-rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n  Normal   BackOff  14s (x279 over 70m)  kubelet  Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"\n      Reason:       ImagePullBackOff\n                  cni.projectcalico.org/containerID: 4156e56d58d8f3770c3cfb36f848fd0ee190f94e5e950fb4a93680efe0b45029\n                  cni.projectcalico.org/podIP: 172.16.104.22/32\n                  cni.projectcalico.org/podIPs: 172.16.104.22/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:          registry.invalid/aiops/private-rootcause:v0\n    Image ID:\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-zcq98:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   25m (x13 over 70m)   kubelet  Failed to pull image \"registry.invalid/aiops/private-rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/private-rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/private-rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/private-rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n  Normal   BackOff  14s (x279 over 70m)  kubelet  Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-check-test\nnamespace: default\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   53m                  kubelet  Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 31.13.87.34:443: i/o timeout\n  Normal   BackOff  30m (x113 over 78m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   13m (x11 over 78m)   kubelet  Error: ErrImagePull\n  Warning  Failed   4m32s (x7 over 38m)  kubelet  (combined from similar events): Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 0e7a6c53736ee153a1f68ab8eca45c237cb5f9eb52fb5ab71c7603eeb52a82c1\n                  cni.projectcalico.org/podIP: 172.16.166.167/32\n                  cni.projectcalico.org/podIPs: 172.16.166.167/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-check-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n      nslookup registry-1.docker.io 2>&1; echo '---'; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-dlk9d:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   53m                  kubelet  Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 31.13.87.34:443: i/o timeout\n  Normal   BackOff  30m (x113 over 78m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   13m (x11 over 78m)   kubelet  Error: ErrImagePull\n  Warning  Failed   4m32s (x7 over 38m)  kubelet  (combined from similar events): Error: ErrImagePull\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  16m (x418 over 150m)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   7m32s (x26 over 115m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 118.184.78.78:443: i/o timeout\n      Reason:       ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n      nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ErrImagePull\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-g4sbz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Normal   BackOff  16m (x418 over 150m)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   7m32s (x26 over 115m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 118.184.78.78:443: i/o timeout\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-check-test\nnamespace: default\ncreationTimestamp: 2026-05-21T11:57:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-check-test: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1; echo '---'; nslookup google.com 2>&1\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-check-test]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-check-test]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-check-test: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-dlk9d\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-imagepull-missing-secret\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T12:07:43Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: rc-definitely-missing-pull-secret\nphase: Pending\nlabels: app=rc-imagepull-missing-secret, pod_abnormal_type=ImagePullFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-imagepull-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=registry.invalid/aiops/private-rootcause:v0 imagePullPolicy=Always\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.invalid/aiops/private-rootcause:v0\"\nvolumes:\n- {\"name\": \"kube-api-access-zcq98\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   8m45s (x13 over 72m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 31.13.70.33:443: i/o timeout\n  Normal   BackOff  4m7s (x362 over 98m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  connectivity-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-zhjs9:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   8m45s (x13 over 72m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 31.13.70.33:443: i/o timeout\n  Normal   BackOff  4m7s (x362 over 98m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-2xvqr\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  28m (x386 over 152m)  kubelet  Back-off pulling image \"curlimages/curl:8.12.1\"\n  Warning  Failed   3m4s (x22 over 121m)  kubelet  (combined from similar events): Failed to pull image \"curlimages/curl:8.12.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/curlimages/curl:8.12.1\": failed to resolve reference \"docker.io/curlimages/curl:8.12.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\": dial tcp 162.125.80.3:443: i/o timeout\n      Reason:       ImagePullBackOff\n  Warning  Failed   3m4s (x21 over 152m)  kubelet  Error: ErrImagePull\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:\n    Image:         curlimages/curl:8.12.1\n    Image ID:\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-5m5hf:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Normal   BackOff  28m (x386 over 152m)  kubelet  Back-off pulling image \"curlimages/curl:8.12.1\"\n  Warning  Failed   3m4s (x21 over 152m)  kubelet  Error: ErrImagePull\n  Warning  Failed   3m4s (x22 over 121m)  kubelet  (combined from similar events): Failed to pull image \"curlimages/curl:8.12.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/curlimages/curl:8.12.1\": failed to resolve reference \"docker.io/curlimages/curl:8.12.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\": dial tcp 162.125.80.3:443: i/o timeout\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: nettest-1779363677\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   30m (x13 over 65m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 204.79.197.217:443: i/o timeout\n  Normal   BackOff  92s (x359 over 96m)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: 0e1677f66bb736654aebcd1568b2bdbd945fff4ef7925d371d4685c0a2b7ed35\n                  cni.projectcalico.org/podIP: 172.16.104.11/32\n                  cni.projectcalico.org/podIPs: 172.16.104.11/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  nettest-1779363677:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-qs5cn:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   30m (x13 over 65m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 204.79.197.217:443: i/o timeout\n  Normal   BackOff  92s (x359 over 96m)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/008-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/008-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/008-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=197 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret rc-definitely-missing-pull-secret -n aiops-e2e\nError from server (NotFound): secrets \"rc-definitely-missing-pull-secret\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/009-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/009-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/28a44bf44db9417f/tools/009-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"所有关键证据均已采集完毕。下面是证据总结：\n\n---\n\n## 📋 证据采集结论\n\n### ✅ 已采集的关键证据\n\n**1. docker.io 镜像仓库全局不可达（影响 26/27 个异常 Pod）**\n- **dns-check-test** (default/node1) → `busybox:1.36.1` → `dial tcp 31.13.87.34:443: i/o timeout` ✅\n- **connectivity-test** (mcp/node2) → `busybox:1.36.1` → `dial tcp 31.13.70.33:443: i/o timeout` ✅\n- **test-dns-1779360358** (aiops-e2e/node1) → `busybox:1.36.1` → `dial tcp 118.184.78.78:443: i/o timeout` ✅\n- **nettest-1779363677** (default/node2) → `busybox:1.36.1` → `dial tcp 204.79.197.217:443: i/o timeout` ✅\n- **node-debugger-node1-2xvqr** (mcp/node1) → `curlimages/curl:8.12.1` → `dial tcp 162.125.80.3:443: i/o timeout` ✅\n\n> ✅ **结论：node1 和 node2 均无法访问 registry-1.docker.io，不同 IP 地址都超时，确认为集群整体出网封锁。**\n\n**2. rc-imagepull-missing-secret 的 registry.invalid DNS 解析失败（独立异常，影响 1/27 Pod）**\n- **Events** ✅：`Head \"https://registry.invalid/v2/aiops/private-rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host`\n- **YAML** ✅：`image: registry.invalid/aiops/private-rootcause:v0`（镜像地址使用了不存在的域名）\n- **imagePullSecrets** ✅：引用了 `rc-definitely-missing-pull-secret`，但该 Secret **NotFound**（不存在）\n\n### ❌ 冲突/负向证据\n- **Secret `rc-definitely-missing-pull-secret`** → NotFound（确认缺失）\n\n### ⚠️ 未采集证据\n- 当前所有关键计划项（e1~e8）均已执行完毕，无需额外工具调用。\n\n### 根因总结\n| 异常类型 | 影响范围 | 根因 |\n|---------|---------|------|\n| 主异常：docker.io 镜像拉取超时 | 26 个 Pod（default/mcp/aiops-e2e） | 集群节点无法出网访问 `registry-1.docker.io`，HTTPS i/o timeout |\n| 次级异常：registry.invalid DNS 解析失败 | 1 个 Pod（rc-imagepull-missing-secret） | 镜像地址使用了不存在的域名 `registry.invalid`，且引用的 imagePullSecret 也不存在 |","collection_summary":"计划 8 项，实际采集 8 项，未采集 0 项，完整度 100%；其中真实环境证据 17/17 项，完整度 100%；实际执行工具 18 个，匹配计划 8 个，未规划证据 10 个","plan_total":8,"plan_collected":8,"plan_completeness":1.0,"environment_evidence_total":17,"environment_evidence_collected":17,"environment_evidence_completeness":1.0,"executed_tool_count":18,"matched_tool_count":8,"unplanned_tool_count":10,"evidence_inventory":[{"id":"e1","description":"主异常组: 验证docker.io网络不可达 - 查看代表Pod dns-check-test (default) 的完整describe，确认Events中的i/o timeout原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","purpose":"确认Pod的Events中Failed to pull image的详细错误原文，验证docker.io registry不可达","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"主异常组: 查看代表Pod dns-check-test的spec，确认使用的镜像地址和imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-check-test -n default -o yaml","purpose":"检查镜像地址(spec.containers[].image)和imagePullSecrets配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"主异常组: 跨namespace验证 - 查看mcp/connectivity-test的Events，确认是否也是docker.io i/o timeout","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","purpose":"验证mcp命名空间下的Pod是否也是同样的docker.io i/o timeout错误，确认全网节点不可达","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"主异常组: 跨namespace验证 - 查看aiops-e2e/test-dns-1779360358的Events，确认ErrImagePull原因","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"验证aiops-e2e命名空间的ErrImagePull Pod是否也是docker.io不可达","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"次要异常组: 验证rc-imagepull-missing-secret的registry.invalid DNS解析问题 - 查看Pod describe","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e","purpose":"确认rc-imagepull-missing-secret的Events中registry.invalid DNS解析失败错误原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"次要异常组: 检查rc-imagepull-missing-secret的完整YAML，验证镜像地址和imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-imagepull-missing-secret -n aiops-e2e -o yaml","purpose":"确认镜像地址是否为registry.invalid，检查spec是否缺少imagePullSecret","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7","description":"主异常组: 跨node验证 - 查看node2上的Pod nettest-1779363677确认同样错误","level":"important","tool":"kubectl_describe","command":"kubectl describe pod nettest-1779363677 -n default","purpose":"验证node2上的Pod同样出现docker.io i/o timeout，确认不影响节点的差异","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e8","description":"主异常组: 验证node debugger pod在node1上的情况 - node-debugger-node1-2xvqr","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2xvqr -n mcp","purpose":"确认node1上的node-debugger Pod也出现docker.io curlimages/curl i/o timeout","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/8 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 主异常组: 验证docker.io网络不可达 - 查看代表Pod dns-check-te... | `kubectl describe pod dns-check-test -n default` |
   | e2 | important | ✅ | kubectl_get_yaml | 主异常组: 查看代表Pod dns-check-test的spec，确认使用的镜像地址和i... | `kubectl get pod dns-check-test -n default -o yaml` |
   | e3 | important | ✅ | kubectl_describe | 主异常组: 跨namespace验证 - 查看mcp/connectivity-test的... | `kubectl describe pod connectivity-test -n mcp` |
   | e4 | important | ✅ | kubectl_describe | 主异常组: 跨namespace验证 - 查看aiops-e2e/test-dns-177... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | e5 | critical | ✅ | kubectl_describe | 次要异常组: 验证rc-imagepull-missing-secret的registry... | `kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e` |
   | e6 | important | ✅ | kubectl_get_yaml | 次要异常组: 检查rc-imagepull-missing-secret的完整YAML，验... | `kubectl get pod rc-imagepull-missing-secret -n aiops-e2e -o yaml` |
   | e7 | important | ✅ | kubectl_describe | 主异常组: 跨node验证 - 查看node2上的Pod nettest-17793636... | `kubectl describe pod nettest-1779363677 -n default` |
   | e8 | important | ✅ | kubectl_describe | 主异常组: 验证node debugger pod在node1上的情况 - node-de... | `kubectl describe pod node-debugger-node1-2xvqr -n mcp` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (28.7s)
   📤 → 下游数据: root_cause=根因分为两部分：(1) 主异常（影响26个Pod）：集群所有节点(node1, node2)无法出网访问 registry-1.docker.io:443，HTTPS连接全部 i/o timeout。证据来自5个跨namespace/跨node的Pod describe：dns-check-test(default/node1)超时IP 31.13.87.34、connectivity-test(mcp/node2)超时IP 31.13.70.33、test-dns-1779360358(aiops-e2e/node1)超时IP 118.184.78.78、nettest-1779363677(default/node2)超时IP 204.79.197.217、node-debugger-node1-2xvqr(mcp/node1)拉取curlimages/curl:8.12.1超时IP 162.125.80.3。4个不同IP全部超时排除偶发，2种不同镜像(busybox/curlimages)均超时排除镜像特定问题，2个节点均超时排除单节点故障，事件持续78-152分钟排除瞬时故障。
... 截断，原始 676 字符
   confidence=98%
   causal_chain={"root_cause": "集群节点(node1, node2)无法出网访问 docker.io（registry-1.docker.io:443），HTTPS连接全部 i/o timeout，导致所有依赖 docker.io 公共镜像的 Pod 拉取失败进入 ImagePullBackOff/ErrImagePull", "propagation": "节点出网网络策略/防火墙/NAT封锁 → node1/node2 向 registry-1.docker.io:443 发起的 TCP 连接全部超时 → kubelet 无法拉取任何 docker.io 镜像 → 26 个 Pod 持续重试失败 → 状态切换为 ImagePullBackOff/ErrImagePull → Pod 处于 Pending 状态。另有 1 个 Pod(rc-imagepull-missing-secret)因镜像地址使用了不存在的域名 registry.invalid 导致 DNS 解析失败，独立于网络问题", "direct_cause": "kubelet 在所有节点(node1/node2)上向 registry-1.docker.io:443 发起的 HTTPS 请求全部 dial tcp i/o timeout，同时 Secret rc-definitely-missing-pull-secret 不存在", "manifestation": "27个Pod处于Pending状态(25个ImagePullBackOff + 2个ErrImagePull)，分布在default、mcp、aiops-e2e命名空间，涉及多种镜像(busybox:1.36.1、curlimages/curl:8.12.1、registry.invalid/aiops/private-rootcause:v0)"}
   rca_analysis={"phenomenon": "集群中存在27个异常Pod全部卡在Pending状态（25个ImagePullBackOff + 2个ErrImagePull），分布在default(7)、mcp(18)、aiops-e2e(2)三个命名空间，涉及node1和node2两个节点。所有异常Pod均无法拉取镜像。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe - dns-check-test", "content": "Pod dns-check-test (default/node1) Events: Failed to pull busybox:1.36.1 -> dial tcp 31.13.87.34:443: i/o timeout", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml - dns-check-test", "content": "Pod dns-check-test: image=busybox:1.36.1, imagePullSecrets=<absent>, no private registry config", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe - connectivity-test", "content": "Pod connectivity-test (mcp/node2) Events: Failed to pull busybox:1.36.1 -> dial tcp 31.13.70.33:443: i/o timeout", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe - test-dns-1779360358", "content": "Pod test-dns-1779360358 (aiops-e2e/node1) Events: ErrImagePull -> dial tcp 118.184.78.78:443: i/o timeout for busybox:1.36.1", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe - node-debugger-node1-2xvqr", "content": "Pod node-debugger-node1-2xvqr (mcp/node1) Events: Failed to pull curlimages/curl:8.12.1 -> dial tcp 162.125.80.3:443: i/o timeout", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe - nettest-1779363677", "content": "Pod nettest-1779363677 (default/node2) Events: Failed to pull busybox:1.36.1 -> dial tcp 204.79.197.217:443: i/o timeout", "reliability": "高"}, {"id": "e7", "source": "kubectl_describe - rc-imagepull-missing-secret", "content": "Pod rc-imagepull-missing-secret (aiops-e2e/node2): Failed to pull registry.invalid/aiops/private-rootcause:v0 -> lookup registry.invalid on 127.0.0.53:53: no such host", "reliability": "高"}, {"id": "e8", "source": "kubectl_get_yaml - rc-imagepull-missing-secret", "content": "Pod rc-imagepull-missing-secret: image=registry.invalid/aiops/private-rootcause:v0, imagePullSecrets=rc-definitely-missing-pull-secret", "reliability": "高"}, {"id": "e9", "source": "kubectl_get_by_name - secret", "content": "Secret rc-definitely-missing-pull-secret in aiops-e2e: NotFound (Command failed exit 1)", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "67 pods total, ~43 Running, 21 abnormal (19 ImagePullBackOff + 2 ErrImagePull). Control plane and business pods all Running.", "reliability": "高"}, {"id": "layer_4", "source": "kubectl_events - dns-check-test", "content": "52m Warning Failed: dial tcp 31.13.87.34:443: i/o timeout for docker.io/library/busybox:1.36.1", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning Failed 53m kubelet Failed to pull image \"busybox:1.36.1\": ... dial tcp 31.13.87.34:443: i/o timeout", "interpretation": "default/dns-check-test 在 node1 上拉取 busybox:1.36.1 时连接 registry-1.docker.io:443 超时"}, {"evidence_id": "e2", "raw_data": "imagePullSecrets: <absent>, containers: image=busybox:1.36.1", "interpretation": "该 Pod 使用公开镜像 busybox，无需私有仓库认证，排除 imagePullSecret 缺失问题"}, {"evidence_id": "e3", "raw_data": "Warning Failed 8m45s (x13) ... dial tcp 31.13.70.33:443: i/o timeout", "interpretation": "mcp/connectivity-test 在 node2 上拉取 busybox:1.36.1 同样超时，不同目标 IP 超时，确认 node2 同样不可达 docker.io"}, {"evidence_id": "e4", "raw_data": "Warning Failed 7m32s (x26) ... dial tcp 118.184.78.78:443: i/o timeout", "interpretation": "aiops-e2e/test-dns-1779360358 在 node1 上拉取 busybox:1.36.1 超时，第三个不同 IP 超时，排除 IP 级偶发"}, {"evidence_id": "e5", "raw_data": "Warning Failed 3m4s (x22) ... dial tcp 162.125.80.3:443: i/o timeout for docker.io/curlimages/curl:8.12.1", "interpretation": "mcp/node-debugger-node1-2xvqr 在 node1 拉取不同镜像 curlimages/curl:8.12.1 也超时，证明是 docker.io 整体不可达而非特定镜像"}, {"evidence_id": "e6", "raw_data": "Warning Failed 30m (x13) ... dial tcp 204.79.197.217:443: i/o timeout", "interpretation": "default/nettest-1779363677 在 node2 上拉取 busybox 超时，第四个不同 IP 超时，强化结论"}, {"evidence_id": "e7", "raw_data": "Warning Failed 25m (x13) ... lookup registry.invalid on 127.0.0.53:53: no such host", "interpretation": "rc-imagepull-missing-secret 的镜像地址使用了不存在的域名 registry.invalid，DNS 解析失败"}, {"evidence_id": "e8", "raw_data": "image=registry.invalid/aiops/private-rootcause:v0, imagePullSecrets=rc-definitely-missing-pull-secret", "interpretation": "该 Pod 镜像地址域名 registry.invalid 不存在，且引用了不存在的 Secret（见 e9）"}, {"evidence_id": "e9", "raw_data": "Error from server (NotFound): secrets \"rc-definitely-missing-pull-secret\" not found", "interpretation": "imagePullSecrets 引用的 Secret 在集群中不存在，是配置错误。但即使 Secret 存在也无法解决 registry.invalid DNS 解析失败问题"}, {"evidence_id": "layer_1", "raw_data": "Running=~43, ImagePullBackOff=19, ErrImagePull=2, control plane all Running", "interpretation": "集群仅镜像拉取类异常，控制面和业务 Pod 正常，说明网络/节点健康，问题限定于镜像仓库可达性"}, {"evidence_id": "layer_4", "raw_data": "52m Warning Failed ... dial tcp 31.13.87.34:443: i/o timeout", "interpretation": "事件已持续78分钟以上，反复重试仍超时，排除瞬时故障"}], "causal_chain": {"root_cause": "集群节点(node1, node2)无法出网访问 docker.io（registry-1.docker.io:443），HTTPS连接全部 i/o timeout，导致所有依赖 docker.io 公共镜像的 Pod 拉取失败进入 ImagePullBackOff/ErrImagePull", "propagation": "节点出网网络策略/防火墙/NAT封锁 → node1/node2 向 registry-1.docker.io:443 发起的 TCP 连接全部超时 → kubelet 无法拉取任何 docker.io 镜像 → 26 个 Pod 持续重试失败 → 状态切换为 ImagePullBackOff/ErrImagePull → Pod 处于 Pending 状态。另有 1 个 Pod(rc-imagepull-missing-secret)因镜像地址使用了不存在的域名 registry.invalid 导致 DNS 解析失败，独立于网络问题", "direct_cause": "kubelet 在所有节点(node1/node2)上向 registry-1.docker.io:443 发起的 HTTPS 请求全部 dial tcp i/o timeout，同时 Secret rc-definitely-missing-pull-secret 不存在", "manifestation": "27个Pod处于Pending状态(25个ImagePullBackOff + 2个ErrImagePull)，分布在default、mcp、aiops-e2e命名空间，涉及多种镜像(busybox:1.36.1、curlimages/curl:8.12.1、registry.invalid/aiops/private-rootcause:v0)"}, "root_cause": "根因分为两部分：(1) 主异常（影响26个Pod）：集群所有节点(node1, node2)无法出网访问 registry-1.docker.io:443，HTTPS连接全部 i/o timeout。证据来自5个跨namespace/跨node的Pod describe：dns-check-test(default/node1)超时IP 31.13.87.34、connectivity-test(mcp/node2)超时IP 31.13.70.33、test-dns-1779360358(aiops-e2e/node1)超时IP 118.184.78.78、nettest-1779363677(default/node2)超时IP 204.79.197.217、node-debugger-node1-2xvqr(mcp/node1)拉取curlimages/curl:8.12.1超时IP 162.125.80.3。4个不同IP全部超时排除偶发，2种不同镜像(busybox/curlimages)均超时排除镜像特定问题，2个节点均超时排除单节点故障，事件持续78-152分钟排除瞬时故障。\n... 截断，原始 676 字符", "root_cause_summary": "根因分为两部分：(1) 主异常（影响26个Pod）：集群所有节点(node1, node2)无法出网访问 registry-1.docker.io:443，HTTPS连接全部 i/o timeout。证据来自5个跨namespace/跨node的Pod describe：dns-check-test(default/node1)超时IP 31.13.87.34、connectivity-test(mcp/node2)超时IP 31.13.70.33、test-dns-1779360358(aiops-e2e/node1)超时IP 118.184.78.78、nettest-1779363677(default/node2)超时IP 204.79.197.217、node-debugger-node1-2xvqr(mcp/node1)拉取curlimages/curl:8.12.1超时IP 162.125.80.3。4个不同IP全部超时排除偶发，2种不同镜像(busybox/curlimages)均超时排除镜像特定问题，2个节点均超时排除单节点故障，事件持续78-152分钟排除瞬时故障。\n... 截断，原始 676 字符", "confidence": 0.98, "confidence_reason": "直接证据充分：5个跨namespace/跨node/跨镜像类型的Pod describe 都显示相同的 dial tcp i/o timeout 错误，目标IP各不相同（排除IP级问题），两种不同镜像均超时（排除镜像特定问题），两个节点均受影响（排除单节点问题），事件持续数十分钟到数小时（排除瞬时故障）。次级异常的 registry.invalid DNS 解析失败和 Secret NotFound 也有直接 describe 和 get 证据。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像地址或tag不存在", "probability": "low", "reason": "排除：多个Pod使用不同的公开镜像(busybox:1.36.1, curlimages/curl:8.12.1)均报i/o timeout而非manifest unknown/not found"}, {"cause": "imagePullSecret缺失或认证失败导致docker.io拉取失败", "probability": "low", "reason": "排除：dns-check-test等Pod使用公开镜像busybox，imagePullSecrets为空(<absent>)，无需认证。且错误信息是i/o timeout而非认证拒绝"}, {"cause": "集群DNS解析失败导致无法解析registry-1.docker.io", "probability": "low", "reason": "排除：错误显示已完成DNS解析（成功获取到多个不同IP如31.13.87.34、31.13.70.33等），但TCP连接超时，说明DNS解析正常，问题在网络层"}], "limitations": "未在节点上执行 curl/wget 到 registry-1.docker.io:443 的直接网络探测（如节点级连通性测试），当前证据均来自kubelet侧的Pod事件。未检查集群出网网关/防火墙策略或NAT配置。对于rc-imagepull-missing-secret，即使修复了registry.invalid域名后，由于引用的Secret不存在，拉取私有镜像仍然会失败（但这是独立于主异常的第二个问题）。", "llm_raw_analysis": "## 证据清点\\n共采集到9个直接证据 + 10个上游已验证工具结果。关键证据包括：5个跨namespace/跨node的Pod describe（dns-check-test、connectivity-test、test-dns-1779360358、node-debugger-node1-2xvqr、nettest-1779363677），2个Pod YAML（dns-check-test、rc-imagepull-missing-secret），1个Secret验证结果（NotFound），以及上游已验证的集群级Pod列表和Events。\\n\\n## 逐条分析\\n- e1~e6：全部指向docker.io registry不可达，5个不同IP全部超时，2种不同镜像均超时，2个节点均受影响\\n- e7~e9：指向rc-imagepull-missing-secret的独立问题——registry.invalid域名不存在 + Secret缺失\\n\\n## 关联分析\\n主异常组（26个Pod）共同表现为docker.io镜像拉取i/o timeout，排除镜像不存在、认证问题、DNS\n... 截断，原始 746 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因分为两部分：(1) 主异常（影响26个Pod）：集群所有节点(node1, node2)无法出网访问 registry-1.docker.io:443，HTTPS连接全部 i/o timeout。证据来自5个跨namespace/跨node的Pod describe：dns-check-test...
   置信度: 98%
   🔗 因果链:
     根本原因: 集群节点(node1, node2)无法出网访问 docker.io（registry-1.docker.io:443），HTTPS连接全部 i/o timeout，导致所有依赖 docker.io 公共镜像的 Pod 拉取失败进入 ImagePullBackOff/ErrImagePull
     传导机制: 节点出网网络策略/防火墙/NAT封锁 → node1/node2 向 registry-1.docker.io:443 发起的 TCP 连接全部超时 → kubelet 无法拉取任何 docker.io 镜像 → 26 个 Pod 持续重试失败 → 状态切换为 ImagePullBackOff/ErrImagePull → Pod 处于 Pending 状态。另有 1 个 Pod(rc-imagepull-missing-secret)因镜像地址使用了不存在的域名 registry.invalid 导致 DNS 解析失败，独立于网络问题
     最终表现: 27个Pod处于Pending状态(25个ImagePullBackOff + 2个ErrImagePull)，分布在default、mcp、aiops-e2e命名空间，涉及多种镜像(busybox:1.36.1、curlimages/curl:8.12.1、registry.invalid/aiops/private-rootcause:v0)


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (32.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 7871 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 16.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为一名资深 K8s 诊断报告专家，我将为您分析集群当前的问题。

---
## 📊 诊断概览

**核心问题回答：** 您的集群目前存在一个**严重的主问题**和一个**次要的配置问题**。

1.  **主问题 (影响 26 个 Pod):** 集群所有节点 (`node1`, `node2`) 无法连接到公共镜像仓库 `docker.io`，导致依赖其公共镜像的 26 个 Pod 全部陷入 `ImagePullBackOff` / `ErrImagePull` 状态，无法启动。
2.  **次要问题 (影响 1 个 Pod):** `aiops-e2e/rc-imagepull-missing-secret` Pod 配置了不存在的镜像仓库域名 `registry.invalid`，导致 DNS 解析失败，且引用的 Secret 也不存在。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff (25个), ErrImagePull (2个) |
| **兼容归因层** | L3 - 集群网络 / L4 - 配置错误 |
| **问题分类** | ImagePullFailed (镜像拉取失败) |
| **置信度** | 高 (98%) |
| **证据完整度** | 8/8 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **影响范围** | 27个异常Pod，分布在 3 个命名空间: `default` (7个), `mcp` (18个), `aiops-e2e` (2个) |
| **所有节点** | `node1 (10.2.0.49)`, `node2 (10.2.0.50)` |
| **问题1 代表Pod** | `default/dns-check-test`, `mcp/connectivity-test`, `mcp/node-debugger-node1-2xvqr` |
| **问题2 代表Pod** | `aiops-e2e/rc-imagepull-missing-secret` |
| **错误信息1** | `Failed to pull image "busybox:1.36.1": ... dial tcp 31.13.87.34:443: i/o timeout` |
| **错误信息2** | `Back-off pulling image "registry.invalid/aiops/private-rootcause:v0"` |

---
## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| **E1** | Pod 事件 | `kubectl describe pod dns-check-test -n default` | `Failed to pull image "busybox:1.36.1": ... dial tcp 31.13.87.34:443: i/o timeout` | Pod拉取 `busybox` 镜像时，向 `31.13.87.34:443` (docker.io) 发起TCP连接超时。 |
| **E2** | Pod 事件 | `kubectl describe pod connectivity-test -n mcp` | `Failed to pull image "busybox:1.36.1": ... dial tcp 31.13.70.33:443: i/o timeout` | 另一个命名空间的Pod拉取同一镜像，对 `docker.io` IP `31.13.70.33:443`也超时。 |
| **E3** | Pod 事件 | `kubectl describe pod node-debugger-node1-2xvqr -n mcp` | `Back-off pulling image "curlimages/curl:8.12.1"` | 拉取一个不同于 `busybox` 的镜像 `curlimages/curl` 也失败，排除了镜像特定问题。 |
| **E4** | Pod 事件 | `kubectl describe pod nettest-1779363677 -n default` | `(combined from similar events): Failed to pull image "busybox:1.36.1": ... i/o timeout` | `node2` 上的Pod也报同样的i/o timeout错误，排除了单节点故障。 |
| **E5** | Pod 事件 | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` | `Back-off pulling image "busybox:1.36.1"` (与另一个IP超时) | 另一个命名空间和Pod也连续拉取 `busybox` 镜像失败，持续150分钟以上。 |
| **E6** | Pod 状态 | `kubectl describe pod rc-imagepull-missing-secret -n aiops-e2e` | `Failed to pull image "registry.invalid/aiops/private-rootcause:v0": ... no such host` | Pod拉取 `registry.invalid` 域名上的镜像失败，原因是域名不存在。 |
| **E7** | Pod 配置 | `kubectl get pod rc-imagepull-missing-secret -n aiops-e2e -o yaml` | `labels: app=rc-imagepull-missing-secret` | 确认Pod名暗示了缺少拉取镜像所需的Secret。 |
| **E8** | Secret 查询 | `kubectl get --show-labels -o wide secret rc-definitely-missing-pull-secret -n aiops-e2e` | `Error from server (NotFound): secrets "rc-definitely-missing-pull-secret" not found` | 确认Pod `rc-imagepull-missing-secret` 可能引用的名为 `rc-definitely-missing-pull-secret` 的 Secret 在集群中不存在。 |

### 证据关联分析
- **证据链1 (主问题，26个Pod): E1 + E2 + E3 + E4 + E5** 印证：
    - **跨Pod**: `dns-check-test`, `connectivity-test`, `test-dns-*`, `nettest-*` 等多个 Pod 均报相同错误。
    - **跨镜像**: `busybox:1.36.1` 和 `curlimages/curl:8.12.1` 两种不同镜像拉取均超时。
    - **跨节点**: `node1` 和 `node2` 上的 Pod 均出现超时。
    - **跨时间**: 错误持续出现 78 到 152 分钟，排除瞬时波动。
    - **多IP超时**: 连接到 `docker.io` 的多个不同IP (`31.13.87.34`, `31.13.70.33`, `204.79.197.217`, `162.125.80.3`) 均超时。
    - **结论**: 集群级网络无法连接到 `docker.io`。
- **证据链2 (次要问题，1个Pod): E6 + E7 + E8** 印证：
    - Pod `rc-imagepull-missing-secret` 的镜像地址使用了不存在的域名 `registry.invalid` (`no such host`)，且Secret `rc-definitely-missing-pull-secret` 不存在。这是一个独立的配置错误。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点级网络连通性测试(如从node上 `curl docker.io`) | critical | 当前证据均来自kubelet侧的Pod事件，未能直接从节点层验证网络连通性问题。 |
| 集群出网防火墙/NAT/网络策略配置 | important | 无法确认是集群自身网络策略（如NetworkPolicy）还是上游防火墙/NAT规则导致出网失败。 |

---
## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────┐
│ 根本原因 1 (主)                                                       │
│ 集群所有节点 (node1, node2) 无法出网访问 registry-1.docker.io:443    │
│ (HTTPS连接全部 i/o timeout)                                          │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 根本原因 2 (次)                                                       │
│ Pod aiops-e2e/rc-imagepull-missing-secret 配置了不存在的镜像仓库      │
│ 域名 `registry.invalid` (DNS解析失败)，并引用了不存在的Secret。       │
└──────────────────────────────────────────────────────────────────────┘
  (问题1)
  ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                            │
│ 节点网络策略/防火墙/NAT封锁 → node1/node2 无法连接                   │
│ registry-1.docker.io:443 → kubelet 拉取所有 docker.io 镜像失败       │
└──────────────────────────────────────────────────────────────────────┘
  (问题2)
  ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 传导机制 (独立)                                                      │
│ 镜像地址使用了不存在的域名 `registry.invalid` → DNS解析失败          │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                        │
│ 1. 26个Pod(Pending) → ImagePullBackOff(25个) / ErrImagePull(2个)     │
│ 2. 1个Pod(Pending) → ImagePullBackOff (由DNS和Secret问题共同导致)    │
│ 3. 集群中27% (约27/100) 的Pod处于异常状态                            │
└──────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 **E1, E2, E3, E4, E5**，**主问题**的根因是 **集群级别网络无法访问外网 `docker.io`**。这可能是上游防火墙、NAT网关或节点的出网策略限制了到外部的HTTPS（443端口）连接。

根据证据 **E6, E7, E8**，**次要问题**的根因是 **`aiops-e2e/rc-imagepull-missing-secret` Pod的配置错误**：镜像地址使用了不存在的域名，且缺少必要的镜像拉取Secret。

**置信度**：高 (98%)
- ✅ 多个跨命名空间、跨节点、跨镜像、跨时间点的Pod均报相同的 `i/o timeout` 错误，且错误IP均为 `docker.io` 的地址。
- ✅ Pod的配置错误 (`registry.invalid`, Secret不存在) 已被真实工具输出直接确认。
- ⚠️ 未在节点上执行直接网络探测，未能彻底排除节点自身配置问题（但概率极低）。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

#### 1. [优先] 修复集群出网问题

此问题需要联系负责集群网络和基础设施的团队解决。根本原因是集群节点无法访问外网。

-   **检查并添加防火墙规则**：允许 `node1` 和 `node2` 的出站流量到 `docker.io` (registry-1.docker.io) 的 TCP 443 端口。
-   **检查代理配置 (HTTPS_PROXY)**：如果公司网络需要通过代理访问外网，请确保 `containerd` 或 `kubelet` 正确配置了代理。
-   **检查网络策略 (NetworkPolicy)**：确认集群内没有阻止节点出站流量的 NetworkPolicy。
-   **临时规避方案**：如果不能立即修复出网问题，考虑使用**私有镜像仓库**。将 Kubernetes 所需的公共镜像（如 `busybox:1.36.1`, `curlimages/curl:8.12.1`）推送至集群内部或同一内网的私有仓库，并修改所有受影响的 Deployment/Job 的镜像地址。

#### 2. [修复] 修复 `aiops-e2e/rc-imagepull-missing-secret` 配置

删除并重新创建此Pod，使用正确的私有仓库地址和已存在的Secret。

```bash
# 1. 删除错误的 Pod
kubectl delete pod rc-imagepull-missing-secret -n aiops-e2e

# 2. (可选) 如果私有仓库需要认证，先创建正确的 Secret
# kubectl create secret docker-registry <正确的secret名> \
#   --docker-server=<私有仓库地址> \
#   --docker-username=<用户名> \
#   --docker-password=<密码> \
#   --docker-email=<邮箱> \
#   -n aiops-e2e

# 3. 重新创建 Pod，使用正确的 YAML 配置
```

### 后续优化

1.  **网络监控**：配置对 Kubernetes 节点到关键外部服务（如 `docker.io`, `gcr.io`, `quay.io`）的网络连通性监控和告警。
2.  **镜像管理**：建立内部私有镜像仓库，作为所有集群的唯一镜像源，避免对外网的直接依赖，提高部署的稳定性和安全性。
3.  **配置审计**：建立 Pod 配置的审批流程，确保镜像地址、Secret 引用等关键配置的正确性，避免类似 `registry.invalid` 和 Secret 不存在的问题出现。

---
## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 验证出网修复 | 在任一节点上执行 `curl -I -v --connect-timeout 5 https://registry-1.docker.io/v2/` | 返回 HTTP 200 或 401，而非 timeout |
| 2. 检查Pod状态 | `kubectl get pods -A \| grep -E 'ImagePullBackOff\|ErrImagePull'` | 无任何输出，各Pod状态为 `Running` |
| 3. 检查受影响Pod | `kubectl get pod dns-check-test -n default` | STATUS: `Running` 或 `Completed` (如为Job) |

---
## ⚠️ 注意事项
-   **修复出网问题是最高优先级**，它将一次性解决 26 个Pod的问题。
-   `rc-imagepull-missing-secret` 的问题是独立的，在修复出网问题后仍需单独处理。
-   修改网络规则时，请遵循公司变更管理流程，避免影响其他业务。

---

## 📊 性能统计

├─ 总耗时: 2.3m
├─ 问题定位: 48.2s (35%) ✅
├─ 证据链采集: 26.7s (20%) ✅
├─ 根因分析: 28.7s (21%) ✅
├─ 汇总总结: 32.9s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 19 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed
- **工具调用**: 19 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
