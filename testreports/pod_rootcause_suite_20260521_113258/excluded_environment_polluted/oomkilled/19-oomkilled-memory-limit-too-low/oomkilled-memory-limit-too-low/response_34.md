======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ac0740bd047040e3]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先扫描整个集群的所有 Pod 状态，看看有什么异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned 119 pods across all namespaces. Running=60, abnormal=53. Key abnormal pattern: 27 ImagePullBackOff + 22 ErrImagePull (mostly in default namespace dns/registry t
   💭 [问题定位] 现在看到了全局情况，让我进一步确认关键异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                     READY   STATUS              RESTARTS   AGE     IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
connectivity-check-tmp   0/1     ContainerCreating   0          5m55s
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME           READY   STATUS        RESTARTS   AGE    IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
reg-diag-tmp   0/1     Terminating   0          2m8s   <none>   node2   <none>        
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                      READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-oomkilled-memory-limit-b6d999d-5f29d  
   💭 [问题定位] 现在让我获取对应的 runbook 来辅助分析。
   💭 [问题定位] 调用工具: fetch_runbook
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
# Pod OOMKilled (Exit Code 137)

> Pod异常类型: OOMKilled | 典型状态: CrashLoopBackOff / Error / Restarting | 兼容分类: container_memory

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | CrashLoopB
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod TerminatingStuck / 删除卡住

> runbook_id: pod-terminating-stuck.md
> Pod异常类型: TerminatingStuck | 典型状态: Terminating | 兼容分类: lifecycle

## 状态识别
- Pod 长时间处于 `Terminating`
- metadata.deletion
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod SandboxCreateFailed / Pod sandbox 创建失败

> Pod异常类型: SandboxCreateFailed | 典型状态: ContainerCreating / FailedCreatePodSandBox | 兼容分类: sandbox_runtime

## 状态识别
- Events 含 `FailedCreatePodSa
   💭 [问题定位] 让我快速查看几个代表 Pod 的详情，确认具体失败原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-oomkilled-memory-limit-b6d999d-5f29d
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
Name:             rc-oomkilled-memory-limit-b6d999d-5f29d
Labels:  
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-check-tmp
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
Annotations:      cni.projectcalico.org/containerID: 7b14601683632a8cc21a499a9ef0bb8d9
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: reg-diag-tmp
namespace: default
node: node2/10.2.0.50
status: Terminating (lasts 41s)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: cc091de6c0c8d3fcf6
   💭 [问题定位] 现在让我确认一下那些 ImagePullBackOff/ErrImagePull Pod 的具体事件信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod dns-test-check (namespace: default, node: node2/10.2.0.50) is Pending. Container dns-test-check with image busybox:1.36.1 (args: nslookup registry.invalid) is in Waiting state, Reason: ErrImagePul
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod registry-check-node2 in namespace default, on node node2 (10.2.0.50), status Pending. Container image busybox:1.36.1 cannot be pulled. State Waiting (Reason: ErrImagePull). All 5 pull attempts fai
   💭 [问题定位] 很好，信息已经非常清晰了。现在让我看看还有没有更多关于节点的信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node2   Ready    <none>   238d   v1.26.8   10.2.0.50     <
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   238d   v1.26.8   10.2.0.49     <
   💭 [问题定位] 现在信息齐全了。让我整理分析结果。

以下是完整的诊断分析：

---

## 📋 集群 Pod 异常诊断分析

### 全局概览
| 指标 | 值 |
|------|-----|
| 总 Pod 数 | **119** |
| Running 正常 | **60** |
| 异常 Pod 数 | **53** |
| 异常 Pod 占比 | **~45%** |

### 异常分组（abnormal_groups）

| 异常类型 | Pod 数量 | 状态关键字 |
|---------|---------|-----------|
| **ImagePullBackOff** | **27** | ImagePullBackOff |
| **ErrImagePull** | **22** | ErrImagePull |
| **CrashLoopBackOff (OOMKilled)** | **1** | CrashLoopBackOff |
| **Terminating** | **1** | Terminating |
| **ContainerCreating** | **1** | ContainerCreating |

---

### 📌 异常一：大规模镜像拉取失败 (ImagePullFailed) — 最严重问题

**影响 Pod 数：49 个**（27 ImagePullBackOff + 22 ErrImagePull）
**兼容层级：L3**

**分布特征：**
- **node2**（10.2.0.50）：以 `ErrImagePull` 为主（dns-resolve-test, dns-test-check, registry-check-node2, registry-conn-test-* 等）
- **node1**（10.2.0.49）：以 `ImagePullBackOff` 为主（dns-check-test, dns-test, dig-tool, net-test-pod 等）

**根因定位：**
通过 `describe registry-check-node2` 和 `dns-test-check` 可以发现，所有拉取失败事件的错误信息完全一致：
> **`dial tcp 159.138.20.20:443: i/o timeout`**
> **`dial tcp registry-1.docker.io:443: i/o timeout`**

多个不同 Docker Hub IP 均超时，说明：
- ✅ **这不是 DNS 解析问题**（IP 已正确解析到 registry-1.docker.io）
- ❌ **节点到 Docker Hub 的网络出口不通** — 两个节点都无法访问外网 Docker 镜像仓库
- ❌ **没有配置镜像代理/镜像仓库镜像（mirror）或私有仓库兜底**

这些 Pod 都是测试/诊断用途（dns-check、registry-check、network-test 等），镜像统一为 `busybox:1.36.1`，是集群对公网 Docker Hub 不可达导致的系统性故障。

---

### 📌 异常二：OOMKilled / CrashLoopBackOff

**Pod：** `aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d`
**节点：** node1
**兼容层级：L2**

关键证据：
- `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`
- `Restart Count: 12`，持续 CrashLoopBackOff
- 受 ReplicaSet 管理，带标签 `pod_abnormal_type=OOMKilled`
- 运行 `python:3.11-slim` 镜像，使用 Python 不断分配内存（`data = []`），是典型的 **内存 limit 过低/内存泄漏测试用例**

---

### 📌 异常三：ContainerCreating 卡住

**Pod：** `default/connectivity-check-tmp`
**节点：** node2
**状态：** 卡在 `ContainerCreating` 已有约 6 分钟

事件显示：
- CNI 已成功分配 IP（`AddedInterface eth0 [172.16.104.52/32] from k8s-pod-network`）
- 正在 `Pulling image "busybox:1.36.1"`

**根本原因：** 由于节点无法连接到 Docker Hub（与异常一同理），拉取 busybox 镜像超时卡住。

---

### 📌 异常四：Terminating 卡住

**Pod：** `default/reg-diag-tmp`
**节点：** node2
**状态：** 已删除 2 分钟但仍在 Terminating

事件显示：
- 同样卡在 `Pulling image "busybox:1.36.1"` 阶段（`ContainerCreating` 状态）
- `terminationGracePeriodSeconds: 30s` — 已超时
- **原因：** 容器从未成功启动（busybox 无法拉取），kubelet 无法正常停止容器进程，导致 Terminating 卡住

---

### 最终诊断输出

| 字段 | 值 |
|------|-----|
| **layer** | L3（镜像拉取失败影响范围最大 49 Pod） |
| **layer_name** | ImagePullFailed |
| **pod_status_keyword** | ImagePullBackOff, ErrImagePull |
| **pod_abnormal_type** | ImagePullFailed |
| **status_category** | image_pull |
| **layers** | L3（ImagePullFailed）、L2（OOMKilled）、L1（TerminatingStuck） |
| **confidence** | 高 |
| **key_entities** | node1, node2, registry-1.docker.io, busybox:1.36.1 |
| **possible_scenarios** | 集群节点公网出口不通/防火墙限制/无镜像代理配置导致 Docker Hub 不可达，所有依赖 busybox 镜像的测试 Pod 无法启动；同时存在 1 个 OOMKilled 测试 Pod 持续 CrashLoopBackOff |

### 审查方向建议

1. **首要（L3）：** 检查节点防火墙/网络策略是否阻止了出站 HTTPS 到 `registry-1.docker.io:443`；建议配置私有镜像仓库代理或 Harbor 缓存
2. **次要（L2）：** OOMKilled Pod 是预期测试用例，如需解决可增大 memory limit
3. **轻量（L1）：** Terminating/ContainerCreating Pod 在镜像拉取问题修复后会自然恢复
   ✅ [问题定位] 完成 (43.9s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L2+L1
   scenarios=[{'scenario': '集群节点到公网Docker Hub网络不可达', 'probability': '高', 'reason': '多个Pod describe均显示 dial tcp registry-1.docker.io:443 i/o timeout，多IP均超时，两个节点node1和node2均受影响'}, {'scenario': '防火墙/网络策略阻止了出站HTTPS到registry-1.docker.io:443', 'probability': '高', 'reason': 'DNS解析正常（IP正确解析），但TCP连接超时，典型防火墙/代理阻断特征'}, {'scenario': '缺少私有镜像仓库代理或Harbor缓存配置', 'probability': '中', 'reason': '集群未配置image mirror/proxy，直接依赖公网Docker Hub'}, {'scenario': 'OOMKilled为预期测试用例，非生产故障', 'probability': '高', 'reason': 'Pod标签为pod_abnormal_type=OOMKilled，且为e2e测试用例，Python代码持续分配内存'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "image", "name": "busybox:1.36.1", "namespace": ""}, {"type": "pod", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d", "namespace": "aiops-e2e"}, {"type": "pod", "name": "connectivity-check-tmp", "namespace": "default"}, {"type": "pod", "name": "reg-diag-tmp", "namespace": "default"}]
   reasoning=当前集群有49个Pod处于镜像拉取失败状态（27 ImagePullBackOff + 22 ErrImagePull），错误均为 i/o timeout 连接 registry-1.docker.io:443，节点无法访问公网Docker Hub。这是影响范围最大的异常（49/53异常Pod），归类L3 ImagePullFailed。同时存在1个OOMKilled的CrashLoopBackOff Pod（aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d，restart=12），归类L2。另有1个Terminating卡住（reg-diag-tmp）和1个ContainerCreating卡住（connectivity-check-tmp），其根因均系镜像拉取失败导致，归类L1。节点均为Ready状态，无节点级异常。综合根因为L3镜像仓库网络不可达。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L2", "L1"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "当前集群有49个Pod处于镜像拉取失败状态（27 ImagePullBackOff + 22 ErrImagePull），错误均为 i/o timeout 连接 registry-1.docker.io:443，节点无法访问公网Docker Hub。这是影响范围最大的异常（49/53异常Pod），归类L3 ImagePullFailed。同时存在1个OOMKilled的CrashLoopBackOff Pod（aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d，restart=12），归类L2。另有1个Terminating卡住（reg-diag-tmp）和1个ContainerCreating卡住（connectivity-check-tmp），其根因均系镜像拉取失败导致，归类L1。节点均为Ready状态，无节点级异常。综合根因为L3镜像仓库网络不可达。", "abnormal_pods": [{"name": "rc-oomkilled-memory-limit-b6d999d-5f29d", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ContainerCreating"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "reg-diag-tmp", "namespace": "default", "status": "Terminating"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff, ErrImagePull", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_pull", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "image", "name": "busybox:1.36.1", "namespace": ""}, {"type": "pod", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d", "namespace": "aiops-e2e"}, {"type": "pod", "name": "connectivity-check-tmp", "namespace": "default"}, {"type": "pod", "name": "reg-diag-tmp", "namespace": "default"}], "possible_scenarios": [{"scenario": "集群节点到公网Docker Hub网络不可达", "probability": "高", "reason": "多个Pod describe均显示 dial tcp registry-1.docker.io:443 i/o timeout，多IP均超时，两个节点node1和node2均受影响"}, {"scenario": "防火墙/网络策略阻止了出站HTTPS到registry-1.docker.io:443", "probability": "高", "reason": "DNS解析正常（IP正确解析），但TCP连接超时，典型防火墙/代理阻断特征"}, {"scenario": "缺少私有镜像仓库代理或Harbor缓存配置", "probability": "中", "reason": "集群未配置image mirror/proxy，直接依赖公网Docker Hub"}, {"scenario": "OOMKilled为预期测试用例，非生产故障", "probability": "高", "reason": "Pod标签为pod_abnormal_type=OOMKilled，且为e2e测试用例，Python代码持续分配内存"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g4", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "default", "name": "reg-diag-tmp"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g5", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-oomkilled-memory-limit-b6d999d-5f29d"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g4", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "default", "name": "reg-diag-tmp"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g5", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "OOMKilled": 1, "ImagePullBackOff": 27, "ErrImagePull": 22, "Terminating": 1}, "total_abnormal": 52, "selected_rows": ["aiops-e2e         rc-oomkilled-memory-limit-b6d999d-5f29d             0/1     CrashLoopBackOff    12 (3m6s ago)   39m     172.16.166.147   node1    <none>           <none>            app=rc-oomkilled-memory-limit,pod-template-hash=b6d999d,pod_abnormal_type=OOMKilled,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff    0               11h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ContainerCreating   0               5m48s   <none>           node2    <none>           <none>            run=connectivity-check-tmp", "default           dig-tool                                            0/1     ImagePullBackOff    0               6h51m   172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff    0               5h51m   172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff    0               10h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff    0               3h10m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff    0               3h16m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull        0               3h16m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff    0               11h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull        0               9h      172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff    0               3h16m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull        0               5h58m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff    0               10h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull        0               10h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull        0               7h34m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           reg-diag-tmp                                        0/1     Terminating         0               2m1s    <none>           node2    <none>           <none>            run=reg-diag-tmp", "default           registry-check-node2                                0/1     ErrImagePull        0               3h44m   172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull        0               8h      172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-conn-test-evidence                         0/1     ErrImagePull        0               129m    172.16.104.22    node2    <none>           <none>            run=registry-conn-test-evidence"], "raw_ref": "/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L2 + L1（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来按照既有 evidence_plan 执行工具调用。先并行执行所有独立工具调用。

## 首先执行 g2 主异常组（ImagePullFailed）+ 其他异常组的独立调用
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-test-check (namespace: default, node: node2/10.2.0.50) is Pending. Container dns-test-check (image: busybox:1.36.1, args: nslookup registry.invalid) is in Waiting/ErrImagePull state, Ready=Fal
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: registry-diag-timeout
namespace: mcp
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   45m (x39 over 4h)        kubelet  (combined from similar events): Faile
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod node-debugger-node2-2cg95 (namespace: mcp, node: node2/10.2.0.50) is Pending. Container "debugger" image busybox:1.36.1 cannot be pulled — all pull attempts fail with i/o timeout dialing registry-
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-oomkilled-memory-limit-b6d999d-5f29d
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
Name:             rc-oomkilled-memory-limit-b6d999d-5f29d
Labels:  
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-check-tmp
namespace: default
node: node2/10.2.0.50
status: Pending
关键诊断行:
Annotations:      cni.projectcalico.org/containerID: 7b14601683632a8cc21a499a9ef0bb8d9
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: reg-diag-tmp
namespace: default
creationTimestamp: 2026-05-21T22:17:36Z
deletionTimestamp: 2026-05-21T22:19:07Z
deletionGracePeriodSeconds: 30
finalizers: <non
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 现在执行证据计划中剩余的工具调用：g2-e4（全局Failed事件）、g1-e2（OOMKilled previous logs）。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_container_previous_logs
   ✅ [证据链采集] 完成 (31.6s)
   📤 → 下游数据: evidence_items=18/20
   evidence_analysis={"evidence_plan":[{"id":"g2-e1","description":"主异常组g2：describe代表Pod dns-test-check (default, ErrImagePull)确认镜像拉取错误原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","tool_args":{"kind":"pod","name":"dns-test-check","namespace":"default"},"purpose":"确认ImagePull失败的具体错误原因","evidence_type":"current_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e2","description":"主异常组g2：describe代表Pod registry-diag-timeout (mcp, ImagePullBackOff) 验证错误是否一致","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod registry-diag-timeout -n mcp","tool_args":{"kind":"pod","name":"registry-diag-timeout","namespace":"mcp"},"purpose":"跨namespace验证i/o timeout是否一致","evidence_type":"current_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e3","description":"主异常组g2：describe代表Pod node-debugger-node2-2cg95 (mcp, ErrImagePull)验证node2侧错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node2-2cg95 -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node2-2cg95","namespace":"mcp"},"purpose":"验证node2上的镜像拉取错误是否一致","evidence_type":"current_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-e4","description":"主异常组g2：通过事件确认全局镜像拉取失败模式","level":"important","tool":"kubectl_events","command":"kubectl get events -A --field-selector reason=Failed --sort-by=.lastTimestamp 2>/dev/null | tail -20","tool_args":{},"purpose":"确认全局Failed事件原文","evidence_type":"events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-e1","description":"异常组g1：验证CrashLoopBackOff/OOMKilled Pod的LastState和OOM确认","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-oomkilled-memory-limit-b6d999d-5f29d","namespace":"aiops-e2e"},"purpose":"确认OOMKilled的Last State、exitCode和restart计数","evidence_type":"current_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-e2","description":"异常组g1：获取前次容器日志以验证OOMKilled","level":"important","tool":"kubectl_container_previous_logs","command":"kubectl logs rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e --previous","tool_args":{"pod_name":"rc-oomkilled-memory-limit-b6d999d-5f29d","namespace":"aiops-e2e"},"purpose":"查看OOMKilled前次日志","evidence_type":"logs","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g4-e1","description":"异常组g4：验证Terminating Pod reg-diag-tmp的YAML确认deletionTimestamp和finalizers","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod reg-diag-tmp -n default -o yaml","tool_args":{"kind":"pod","name":"reg-diag-tmp","namespace":"default"},"purpose":"确认deletionTimestamp、finalizers","evidence_type":"current_status","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g3-e1","description":"异常组g3：验证ContainerCreating Pod connectivity-check-tmp当前状态和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","tool_args":{"kind":"pod","name":"connectivity-check-tmp","namespace":"default"},"purpose":"确认ContainerCreating卡住原因","evidence_type":"current_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g5-e1","description":"异常组g5：验证StartError Pod node-debugger-node1-nx8gb当前状态最小确认","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"确认StartError Pod当前状态","evidence_type":"current_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod dns-test-check (namespace: default, node: node2/10.2.0.50) is Pending. Container dns-test-check (image: busybox:1.36.1, args: nslookup registry.invalid) is in Waiting/ErrImagePull state, Ready=False, Restarts=0. All 6 recent image pull attempts to docker.io/library/busybox:1.36.1 failed with i/o timeout on Head requests to registry-1.docker.io (various IPs: 69.63.180.173, 159.138.20.20, 104.31.142.88, 31.13.95.169, 108.160.170.39, 31.13.95.34:443). Errors: Unknown desc / DeadlineExceeded. Last event: Failed 6m19s (x76 over 9h) Error: ErrImagePull. Pod IP: 172.16.104.53. Calico network configured.\nkey_facts: [\"Pod dns-test-check, namespace=default, node=node2/10.2.0.50, status=Pending\", \"Container dns-test-check, image=busybox:1.36.1, args=['nslookup', 'registry.invalid']\", \"Container State=Waiting, Reason=ErrImagePull, Ready=False, Restart Count=0\", \"All image pull attempts to docker.io/library/busybox:1.36.1 failed with i/o timeout connecting to registry-1.docker.io:443 (multiple IPs attempted)\", \"Failed event count: x76 over 9h with Error: ErrImagePull\", \"Pod IP: 172.16.104.53, Calico CNI network configured\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: registry-diag-timeout\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   45m (x39 over 4h)        kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:37214->23.20.95.219:443: read: connection reset by peer\n  Normal   BackOff  5m20s (x754 over 5h10m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: 4392dc9a6cae7947cfe958d1203b214896971fe84bf922c753319f860561d387\n                  cni.projectcalico.org/podIP: 172.16.166.162/32\n                  cni.projectcalico.org/podIPs: 172.16.166.162/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  regi\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod node-debugger-node2-2cg95 (namespace: mcp, node: node2/10.2.0.50) is Pending. Container \"debugger\" image busybox:1.36.1 cannot be pulled — all pull attempts fail with i/o timeout dialing registry-1.docker.io (multiple IPs tried: 104.244.46.85, 199.96.58.177, 199.59.149.206, 202.53.137.209, 168.143.162.58, 31.13.94.23). Container State: Waiting (Reason: ErrImagePull). 81 Pulling events over 9h, but all pull attempts failed over 9h (last at 2m49s). Pod command: nslookup registry-1.docker.io. QoS: BestEffort. No container ID assigned.\nkey_facts: [\"Pod node-debugger-node2-2cg95 in namespace mcp\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Container: debugger, Image: busybox:1.36.1\", \"Container State: Waiting, Reason: ErrImagePull\", \"Container Ready: False, Restart Count: 0\", \"No Container ID assigned\", \"Events: Warning Failed (x63 over 9h) — Error: ErrImagePull\", \"All pull attempts failed with i/o timeout dialing registry-1.docker.io:443 (multiple IPs)\", \"Events: Normal Pulling 34m (x81 over 9h) — pulling image, followed by failure\", \"Last pull failure at 2m49s\", \"Pod command: chroot /host /bin/sh -c 'nslookup registry-1.docker.io 2>&1 || echo DNS check failed'\", \"QoS Class: Best\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-oomkilled-memory-limit-b6d999d-5f29d\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\nName:             rc-oomkilled-memory-limit-b6d999d-5f29d\nLabels:           app=rc-oomkilled-memory-limit\n                  pod_abnormal_type=OOMKilled\nAnnotations:      aiops.e2e/runbook: pod-oomkilled.md\nControlled By:  ReplicaSet/rc-oomkilled-memory-limit-b6d999d\n      Reason:       OOMKilled\n      Exit Code:    137\n  Normal   Scheduled       40m                  default-scheduler  Successfully assigned aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d to node1\n  Warning  BackOff         38s (x183 over 40m)  kubelet            Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-5f29d_aiops-e2e(2a0a6edf-c1a7-4057-abfb-be8ea3edfa50)\n      Reason:       CrashLoopBackOff\n                  cni.projectcalico.org/containerID: a31bbc9e3699735c3f9d3873265a2428dcff2f435ffcefe4489801098b253eda\n                  cni.projectcalico.org/podIP: 172.16.166.147/32\n                  cni.projectcalico.org/podIPs: 172.16.166.147/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-oomkilled-memory-limit-b6d999d\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://7c6d76ec56a4a1922582db3ee8408ba6181e786b07ef7017137e17945dd34301\n    Image:         python:3.11-slim\n    Image ID:      sha256:fa659464a114c340e31c7b7954a1aa679de7e7f5346e4b5804e8422b2596aff9\n    Command:\n      python\n      -c\n    Args:\n      import time\n      data = []\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       OOMKilled\n      Exit Code:    137\n      Started:      Thu, 21 May 2026 22:16:30 +0000\n      Finished:     Thu, 21 May 2026 22:16:31 +0000\n    Ready:          False\n    Restart Count:  12\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-8tgtg:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Normal   Scheduled       40m                  default-scheduler  Successfully assigned aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d to node1\n  Warning  BackOff         38s (x183 over 40m)  kubelet            Back-off restarting failed container app in pod rc-oomkilled-memory-limit-b6d999d-5f29d_aiops-e2e(2a0a6edf-c1a7-4057-abfb-be8ea3edfa50)\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-check-tmp\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\nAnnotations:      cni.projectcalico.org/containerID: 7b14601683632a8cc21a499a9ef0bb8d9bfbd66021fcd24d205ecd346f2c2767\n                  cni.projectcalico.org/podIP: 172.16.104.52/32\n                  cni.projectcalico.org/podIPs: 172.16.104.52/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  connectivity-check-tmp:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-8qvlz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason          Age    From               Message\n  ----    ------          ----   ----               -------\n  Normal  Scheduled       6m41s  default-scheduler  Successfully assigned default/connectivity-check-tmp to node2\n  Normal  AddedInterface  6m41s  multus             Add eth0 [172.16.104.52/32] from k8s-pod-network\n  Normal  Pulling         6m41s  kubelet            Pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: reg-diag-tmp\nnamespace: default\ncreationTimestamp: 2026-05-21T22:17:36Z\ndeletionTimestamp: 2026-05-21T22:19:07Z\ndeletionGracePeriodSeconds: 30\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- reg-diag-tmp: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c timeout 5 wget -q -O- https://registry-1.docker.io/v2/\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [reg-diag-tmp]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [reg-diag-tmp]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- reg-diag-tmp: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"kube-api-access-295fg\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/006-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/006-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/006-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ac0740bd047040e3/tools/007-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"现在执行证据计划中剩余的工具调用：g2-e4（全局Failed事件）、g1-e2（OOMKilled previous logs）。","collection_summary":"计划 9 项，实际采集 7 项，未采集 2 项，完整度 78%；其中真实环境证据 18/20 项，完整度 90%；实际执行工具 18 个，匹配计划 7 个，未规划证据 11 个","plan_total":9,"plan_collected":7,"plan_completeness":0.7777777777777778,"environment_evidence_total":20,"environment_evidence_collected":18,"environment_evidence_completeness":0.9,"executed_tool_count":18,"matched_tool_count":7,"unplanned_tool_count":11,"evidence_inventory":[{"id":"g2-e1","description":"主异常组g2：describe代表Pod dns-test-check (default, ErrImagePull)确认镜像拉取错误原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","purpose":"确认ImagePull失败的具体错误原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e2","description":"主异常组g2：describe代表Pod registry-diag-timeout (mcp, ImagePullBackOff) 验证错误是否一致","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod registry-diag-timeout -n mcp","purpose":"跨namespace验证i/o timeout是否一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e3","description":"主异常组g2：describe代表Pod node-debugger-node2-2cg95 (mcp, ErrImagePull)验证node2侧错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node2-2cg95 -n mcp","purpose":"验证node2上的镜像拉取错误是否一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-e4","description":"主异常组g2：通过事件确认全局镜像拉取失败模式","level":"important","tool":"kubectl_events","command":"kubectl get events -A --field-selector reason=Failed --sort-by=.lastTimestamp 2>/dev/null | tail -20","purpose":"确认全局Failed事件原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-e1","description":"异常组g1：验证CrashLoopBackOff/OOMKilled Pod的LastState和OOM确认","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e","purpose":"确认OOMKilled的Last State、exitCode和restart计数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-e2","description":"异常组g1：获取前次容器日志以验证OOMKilled","level":"important","tool":"kubectl_container_previous_logs","command":"kubectl logs rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e --previous","purpose":"查看OOMKilled前次日志","collected":false,"source":"planned","outcome":"unknown"},{"id":"g4-e1","description":"异常组g4：验证Terminating Pod reg-diag-tmp的YAML确认deletionTimestamp和finalizers","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod reg-diag-tmp -n default -o yaml","purpose":"确认deletionTimestamp、finalizers","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-e1","description":"异常组g3：验证ContainerCreating Pod connectivity-check-tmp当前状态和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","purpose":"确认ContainerCreating卡住原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g5-e1","description":"异常组g5：验证StartError Pod node-debugger-node1-nx8gb当前状态最小确认","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"确认StartError Pod当前状态","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_10","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_11","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["g1-e2(异常组g1：获取前次容器日志以验证OOMKilled): 已规划但工具执行失败或无匹配结果","g5-e1(异常组g5：验证StartError Pod node-debugger-node1-nx8gb当前状态最小确认): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/9 项, 完整度: 90%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g2-e1 | critical | ✅ | kubectl_describe | 主异常组g2：describe代表Pod dns-test-check (default,... | `kubectl describe pod dns-test-check -n default` |
   | g2-e2 | critical | ✅ | kubectl_describe | 主异常组g2：describe代表Pod registry-diag-timeout (m... | `kubectl describe pod registry-diag-timeout -n mcp` |
   | g2-e3 | critical | ✅ | kubectl_describe | 主异常组g2：describe代表Pod node-debugger-node2-2cg9... | `kubectl describe pod node-debugger-node2-2cg95 -n mcp` |
   | g2-e4 | important | ✅ | kubectl_events | 主异常组g2：通过事件确认全局镜像拉取失败模式 | `kubectl get events -A --field-selector reason=Failed --sort-by=.lastTimestamp...` |
   | g1-e1 | critical | ✅ | kubectl_describe | 异常组g1：验证CrashLoopBackOff/OOMKilled Pod的LastSt... | `kubectl describe pod rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e` |
   | g1-e2 | important | ❌ | kubectl_container_previou... | 异常组g1：获取前次容器日志以验证OOMKilled | `kubectl logs rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e --previous` |
   | g4-e1 | important | ✅ | kubectl_get_yaml | 异常组g4：验证Terminating Pod reg-diag-tmp的YAML确认de... | `kubectl get pod reg-diag-tmp -n default -o yaml` |
   | g3-e1 | important | ✅ | kubectl_describe | 异常组g3：验证ContainerCreating Pod connectivity-ch... | `kubectl describe pod connectivity-check-tmp -n default` |
   | g5-e1 | important | ❌ | kubectl_describe | 异常组g5：验证StartError Pod node-debugger-node1-nx... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |

   ⚠️ 未采集原因:
   - g1-e2(异常组g1：获取前次容器日志以验证OOMKilled): 已规划但工具执行失败或无匹配结果
   - g5-e1(异常组g5：验证StartError Pod node-debugger-node1-nx8gb当前状态最小确认): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.3s)
   📤 → 下游数据: root_cause=根因为集群节点无法访问公网Docker Hub。关键证据：(1) 代表Pod dns-test-check (default, node2)的6次pull均i/o timeout到registry-1.docker.io:443的多IP（如69.63.180.173、159.138.20.20等），events x76 over 9h；(2) registry-diag-timeout (mcp, node1)也出现同样错误 + connection reset by peer；(3) node-debugger-node2-2cg95 (mcp, node2)同样i/o timeout，x63 events over 9h。三个代表Pod覆盖两个节点、两个namespace，错误完全一致，排除单点故障。同时两个节点均为Ready状态（containerd://1.6.32），排除节点异常。影响范围：49个Pod（27 ImagePullBackOff + 22 ErrImagePull），连带导致1个ContainerCreating卡住(connectivity-check-tmp
... 截断，原始 713 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点无法访问公网Docker Hub（registry-1.docker.io:443），因网络防火墙/出站策略阻止了HTTPS出站连接或缺少代理配置，导致49个Pod无法拉取镜像", "propagation": "节点→网络出口→Docker Hub: 两个节点(node1, node2)均无法建立到registry-1.docker.io:443的TCP连接。DNS解析正常（多种IP均被解析），但TCP握手均i/o timeout或connection reset，说明公网出口方向被网络策略阻断", "direct_cause": "kubelet无法拉取镜像busybox:1.36.1：每个异常Pod的容器运行时通过containerd尝试从docker.io拉取镜像时，TCP连接registry-1.docker.io:443均超时", "manifestation": "49个Pod处于ImagePullBackOff(27个)/ErrImagePull(22个)状态，分布在aiops-e2e、default、mcp三个namespace和node1/node2两个节点上；连带1个ContainerCreating卡住(connectivity-check-tmp也在等镜像)、1个Terminating卡住(reg-diag-tmp容器未启动无法完成终止)"}
   rca_analysis={"phenomenon": "集群共有53个异常Pod，其中49个Pod处于镜像拉取失败状态（27 ImagePullBackOff + 22 ErrImagePull），错误均为i/o timeout连接registry-1.docker.io:443，节点无法访问公网Docker Hub。另有1个OOMKilled导致CrashLoopBackOff (aiops-e2e/rc-oomkilled-memory-limit-b6d999d-5f29d, restart=12)，1个Terminating卡住 (default/reg-diag-tmp)，1个ContainerCreating卡住 (default/connectivity-check-tmp)，1个StartError (mcp/node-debugger-node1-nx8gb)。两个节点node1/node2均为Ready状态。", "evidence_inventory": [{"id": "g2-e1", "source": "kubectl_describe dns-test-check (default)", "content": "Pod dns-test-check, ns=default, node=node2, Pending, Container Waiting/ErrImagePull, 6次pull全部i/o timeout连接registry-1.docker.io:443（多IP），events x76 over 9h", "reliability": "高"}, {"id": "g2-e2", "source": "kubectl_describe registry-diag-timeout (mcp)", "content": "registry-diag-timeout, ns=mcp, node=node1, Pending, ImagePullBackOff, Failed事件x39 over 4h: i/o timeout + connection reset by peer to registry-1.docker.io:443", "reliability": "高"}, {"id": "g2-e3", "source": "kubectl_describe node-debugger-node2-2cg95 (mcp)", "content": "node-debugger-node2-2cg95, ns=mcp, node=node2, Pending, ErrImagePull, 所有pull均i/o timeout, events x63 over 9h", "reliability": "高"}, {"id": "g1-e1", "source": "kubectl_describe rc-oomkilled (aiops-e2e)", "content": "rc-oomkilled-memory-limit-b6d999d-5f29d, ns=aiops-e2e, node=node1, CrashLoopBackOff, LastState=OOMKilled exitCode=137, restart=12, 标签pod_abnormal_type=OOMKilled", "reliability": "高"}, {"id": "g4-e1", "source": "kubectl_get_yaml reg-diag-tmp (default)", "content": "reg-diag-tmp, ns=default, node=node2, Terminating, deletionTimestamp已设, finalizers=none, phase=Pending, 镜像busybox:1.36.1无法拉取", "reliability": "高"}, {"id": "g3-e1", "source": "kubectl_describe connectivity-check-tmp (default)", "content": "connectivity-check-tmp, ns=default, node=node2, ContainerCreating, 事件显示Pulling image busybox:1.36.1进行中，但registry不可达导致卡住", "reliability": "高"}, {"id": "g5-e1", "source": "kubectl_describe node-debugger-node1-nx8gb (mcp)", "content": "node-debugger-node1-nx8gb, ns=mcp, node=node1, Failed/StartError, exec: curl not found in busybox:1.36 image", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "119 pods total, 60 Running, 53 abnormal: 27 ImagePullBackOff + 22 ErrImagePull + 1 CrashLoopBackOff + 1 Terminating + 1 ContainerCreating + 1 StartError", "reliability": "高"}, {"id": "layer_10", "source": "kubectl_get_by_name node2", "content": "node2 Ready, 238d, containerd://1.6.32, 无节点级异常", "reliability": "高"}, {"id": "layer_11", "source": "kubectl_get_by_name node1", "content": "node1 Ready, 238d, containerd://1.6.32, 无节点级异常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "g2-e1", "raw_data": "All 6 recent image pull attempts to docker.io/library/busybox:1.36.1 failed with i/o timeout on Head requests to registry-1.docker.io (IPs: 69.63.180.173, 159.138.20.20, 104.31.142.88...)", "interpretation": "代表Pod dns-test-check在node2上无法从任何Docker Hub IP拉取镜像，DNS解析成功(IP多样化)但TCP连接全部超时，说明公网出口被阻断"}, {"evidence_id": "g2-e2", "raw_data": "Warning Failed 45m (x39 over 4h) kubelet: Failed to pull image 'busybox:1.36.1' ... read tcp 10.2.0.49:37214->23.20.95.219:443: read: connection reset by peer", "interpretation": "代表Pod registry-diag-timeout在node1上也出现同样的镜像拉取失败，且出现connection reset by peer，进一步确认是网络层面问题而非单节点故障"}, {"evidence_id": "g2-e3", "raw_data": "All pull attempts fail with i/o timeout dialing registry-1.docker.io (multiple IPs: 104.244.46.85, 199.96.58.177, 199.59.149.206, 202.53.137.209, 168.143.162.58, 31.13.94.23)", "interpretation": "node2上又一代表Pod验证了相同错误模式，证明两个节点(node1和node2)均无法访问Docker Hub，排除单节点故障可能"}, {"evidence_id": "g1-e1", "raw_data": "Last State: Terminated, Reason: OOMKilled, Exit Code: 137. Labels: pod_abnormal_type=OOMKilled, rootcause-e2e=true. Restart Count: 12", "interpretation": "CrashLoopBackOff Pod的根因是OOMKilled(exitCode=137)，且为e2e测试用例(pod_abnormal_type标签)，与镜像拉取问题无关"}, {"evidence_id": "g4-e1", "raw_data": "deletionTimestamp: 2026-05-21T22:19:07Z, finalizers: <none>, phase: Pending, container image=busybox:1.36.1", "interpretation": "Terminating Pod reg-diag-tmp无finalizer、无volume，卡住原因在于容器未成功启动(镜像拉取失败导致kubelet无法完成容器停止流程)"}, {"evidence_id": "g3-e1", "raw_data": "Events: Normal Pulling 6m41s kubelet Pulling image 'busybox:1.36.1'. State: Waiting, Reason: ContainerCreating", "interpretation": "ContainerCreating Pod connectivity-check-tmp正在拉取镜像busybox:1.36.1但registry不可达，导致长时间卡在ContainerCreating状态"}, {"evidence_id": "g5-e1", "raw_data": "failed to create containerd task: OCI runtime create failed: exec: 'curl': executable file not found in $PATH: unknown", "interpolation": "StartError Pod node-debugger-node1-nx8gb镜像为busybox:1.36（注意不是1.36.1），命令为curl，但busybox镜像中无curl可执行文件，导致StartError"}, {"evidence_id": "layer_10", "raw_data": "node2 Ready, containerd://1.6.32", "interpretation": "两个节点均为Ready状态，无节点级异常，镜像拉取失败不是节点不可用导致"}, {"evidence_id": "layer_11", "raw_data": "node1 Ready, containerd://1.6.32", "interpretation": "节点正常，进一步确认为出站网络策略问题"}], "causal_chain": {"root_cause": "集群节点无法访问公网Docker Hub（registry-1.docker.io:443），因网络防火墙/出站策略阻止了HTTPS出站连接或缺少代理配置，导致49个Pod无法拉取镜像", "propagation": "节点→网络出口→Docker Hub: 两个节点(node1, node2)均无法建立到registry-1.docker.io:443的TCP连接。DNS解析正常（多种IP均被解析），但TCP握手均i/o timeout或connection reset，说明公网出口方向被网络策略阻断", "direct_cause": "kubelet无法拉取镜像busybox:1.36.1：每个异常Pod的容器运行时通过containerd尝试从docker.io拉取镜像时，TCP连接registry-1.docker.io:443均超时", "manifestation": "49个Pod处于ImagePullBackOff(27个)/ErrImagePull(22个)状态，分布在aiops-e2e、default、mcp三个namespace和node1/node2两个节点上；连带1个ContainerCreating卡住(connectivity-check-tmp也在等镜像)、1个Terminating卡住(reg-diag-tmp容器未启动无法完成终止)"}, "root_cause": "根因为集群节点无法访问公网Docker Hub。关键证据：(1) 代表Pod dns-test-check (default, node2)的6次pull均i/o timeout到registry-1.docker.io:443的多IP（如69.63.180.173、159.138.20.20等），events x76 over 9h；(2) registry-diag-timeout (mcp, node1)也出现同样错误 + connection reset by peer；(3) node-debugger-node2-2cg95 (mcp, node2)同样i/o timeout，x63 events over 9h。三个代表Pod覆盖两个节点、两个namespace，错误完全一致，排除单点故障。同时两个节点均为Ready状态（containerd://1.6.32），排除节点异常。影响范围：49个Pod（27 ImagePullBackOff + 22 ErrImagePull），连带导致1个ContainerCreating卡住(connectivity-check-tmp\n... 截断，原始 713 字符", "root_cause_summary": "根因为集群节点无法访问公网Docker Hub。关键证据：(1) 代表Pod dns-test-check (default, node2)的6次pull均i/o timeout到registry-1.docker.io:443的多IP（如69.63.180.173、159.138.20.20等），events x76 over 9h；(2) registry-diag-timeout (mcp, node1)也出现同样错误 + connection reset by peer；(3) node-debugger-node2-2cg95 (mcp, node2)同样i/o timeout，x63 events over 9h。三个代表Pod覆盖两个节点、两个namespace，错误完全一致，排除单点故障。同时两个节点均为Ready状态（containerd://1.6.32），排除节点异常。影响范围：49个Pod（27 ImagePullBackOff + 22 ErrImagePull），连带导致1个ContainerCreating卡住(connectivity-check-tmp\n... 截断，原始 713 字符", "confidence": 0.95, "confidence_reason": "三个代表Pod跨两个节点、跨两个namespace均采集到完全一致的i/o timeout错误原文，DNS解析成功但TCP连接全部超时，证据充分且因果链清晰。OOMKilled、StartError等其他异常亦有明确的describe证据支撑。", "primary_runbooks": ["pod-imagepull-failed.md", "pod-oomkilled.md", "pod-terminating-stuck.md", "pod-sandbox-create-failed.md"], "alternative_causes": [{"cause": "镜像名或tag不存在", "probability": "low", "reason": "所有Pod尝试拉取的镜像均为busybox:1.36.1，这是一个合法且广泛使用的镜像tag。错误不是manifest unknown，而是i/o timeout，排除此因"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "错误信息为TCP连接超时，不是认证失败(401/denied)。Docker Hub公共镜像busybox不需要认证"}, {"cause": "DNS解析失败", "probability": "low", "reason": "events中显示连接到了多个不同IP(69.63.180.173、159.138.20.20等)，这些是registry-1.docker.io的有效CDN IP，说明DNS解析正常"}, {"cause": "节点级故障导致所有Pod异常", "probability": "low", "reason": "两个节点(node1/node2)均为Ready状态且运行正常，排除节点故障"}], "limitations": "缺失证据：(1) 未获取g1-e2(OOMKilled的前次容器日志验证) —— 但describe已明确显示Last State=OOMKilled, exitCode=137，证据已足够；(2) 未获取g5-e1(StartError的最小状态确认) —— 但describe已完整显示exec: curl not found错误。网络层面未进一步采集节点上直接curl/wget到registry-1.docker.io的结果或检查iptables/nftables规则，但Pod层证据已充分证明出站不可达。", "llm_raw_analysis": "## 证据清点\n共采集17项证据，覆盖5个异常组(g1~g5)，核心证据集中在g2(主异常组，49个镜像拉取失败Pod)。\n\n## 逐条分析\n- g2-e1/g2-e2/g2-e3：三个代表Pod跨node1/node2、跨default/mcp namespace，一致证实registry-1.docker.io:443 TCP超时\n- g1-e1：OOMKilled Pod为独立的e2e测试用例，exitCode=137，lastState=OOMKilled\n- g4-e1：Terminating Pod无finalizer/volume，卡住因容器未启动(kubelet无法完成Terminating流程)\n- g3-e1：ContainerCreating Pod正在Pulling镜像但registry不可达\n- g5-e1：StartError Pod因busybox:1.36镜像不含curl命令\n- layer_10/layer_11：两个节点均Ready，排除节点级故障\n\n## 关联分析\n主异常组g2(49个Pod)的根因是统一且明确的——registry-1.docke\n... 截断，原始 883 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因为集群节点无法访问公网Docker Hub。关键证据：(1) 代表Pod dns-test-check (default, node2)的6次pull均i/o timeout到registry-1.docker.io:443的多IP（如69.63.180.173、159.138.20.20等），...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点无法访问公网Docker Hub（registry-1.docker.io:443），因网络防火墙/出站策略阻止了HTTPS出站连接或缺少代理配置，导致49个Pod无法拉取镜像
     传导机制: 节点→网络出口→Docker Hub: 两个节点(node1, node2)均无法建立到registry-1.docker.io:443的TCP连接。DNS解析正常（多种IP均被解析），但TCP握手均i/o timeout或connection reset，说明公网出口方向被网络策略阻断
     最终表现: 49个Pod处于ImagePullBackOff(27个)/ErrImagePull(22个)状态，分布在aiops-e2e、default、mcp三个namespace和node1/node2两个节点上；连带1个ContainerCreating卡住(connectivity-check-tmp也在等镜像)、1个Terminating卡住(reg-diag-tmp容器未启动无法完成终止)


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (26.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8094 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 4.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为一名资深 K8s 诊断报告专家，我将基于您提供的所有阶段分析结果，生成一份详尽、完整的诊断报告。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | 49个Pod镜像拉取失败（ImagePullBackOff/ErrImagePull），1个OOMKilled，1个Terminating，1个ContainerCreating |
| **兼容归因层** | L3 - 集群级基础设施 |
| **问题分类** | 镜像仓库网络不可达 (ImagePullFailed) |
| **置信度** | 高 (95%) |
| **证据完整度** | 7/9 (78%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键事实总结**：
您的 Kubernetes 集群当前面临的主要问题是 **大规模镜像拉取失败**，导致集群中 49 个 Pod 处于异常状态，占全部异常 Pod 的 92.5%。根本原因是集群中的所有节点（node1， node2）**无法连接到公网 Docker Hub 镜像仓库** (`registry-1.docker.io:443`)。此外，还存在一个由 e2e 测试引起的 OOMKilled 问题，以及两个因镜像拉取失败而间接陷入 `ContainerCreating` 和 `Terminating` 状态的 Pod。

**关键实体**：
| 类型 | 值 |
|------|-----|
| **根因** | 集群节点出站网络无法连接公网 Docker Hub (`registry-1.docker.io:443`) |
| **核心异常组** | `ImagePullBackOff` (27个) + `ErrImagePull` (22个) |
| **影响命名空间** | `aiops-e2e`, `default`, `mcp` |
| **影响节点** | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| **节点状态** | 所有节点 `Ready` |

**次要问题**：
| 问题 | Pod | 状态 | 状态原因 |
|------|-----|------|----------|
| OOMKilled (E2E测试) | `aiops-e2e/rc-oomkilled-memory-limit-*` | `CrashLoopBackOff` | 容器因内存超限被 kill，为预期测试行为 |
| Terminating 卡住 | `default/reg-diag-tmp` | `Terminating` | 根因为镜像无法拉取导致容器未启动，无法完成优雅终止 |
| ContainerCreating 卡住 | `default/connectivity-check-tmp` | `ContainerCreating` | 根因为镜像无法拉取 |

---

## 🕵️ 证据链

### 已采集关键证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl_get_by_kind_in_cluster` | 运行 Pod 60个，异常 Pod 53个。其中：`ImagePullBackOff` x27， `ErrImagePull` x22 | 确认集群存在大规模镜像拉取失败问题，占异常 Pod 的 92.5%。 |
| 2 | Pod 事件（代表Pod） | `kubectl describe pod dns-test-check -n default` | `Warning Failed … failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image "docker.io/library/busybox:1.36.1": failed to resolve reference "docker.io/library/busybox:1.36.1": failed to do request: Head "https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1": dial tcp 69.63.180.173:443: i/o timeout` (共76次失败事件) | 镜像拉取失败的具体错误为 `i/o timeout`，目标地址为 `registry-1.docker.io:443`，明确指向网络不可达。 |
| 3 | Pod 事件（跨节点验证） | `kubectl describe pod node-debugger-node2-2cg95 -n mcp` | `Warning Failed … failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = … dial tcp 104.244.46.85:443: i/o timeout` (共63次失败事件) | 节点2(node2)上也出现完全相同的 `i/o timeout` 错误，排除了单节点故障，确认是集群层面的网络问题。 |
| 4 | Pod 事件（跨命名空间验证） | `kubectl describe pod registry-diag-timeout -n mcp` | 同样 `i/o timeout + connection reset` 错误 | 在 `mcp` 命名空间和 `node1` 节点上也复现相同错误，进一步确认问题影响范围覆盖整个集群。 |
| 5 | Terminating Pod YAML | `kubectl get pod reg-diag-tmp -n default -o yaml` | `deletionTimestamp: 2026-05-21T22:19:07Z`, `deletionGracePeriodSeconds: 30`, `finalizers: <none>` | 确认该Pod处于 `Terminating` 状态，但**没有 finalizers** 阻塞删除，其卡住的原因是容器因无法拉取镜像而从未启动，导致 `kubelet` 无法完成 `preStop` 钩子或向容器进程发送 SIGTERM 信号。 |
| 6 | OOMKilled Pod 状态 | `kubectl describe pod rc-oomkilled-memory-limit-b6d999d-5f29d -n aiops-e2e` | `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`，且重启次数为12次 | 确认该Pod因内存限制不足被OOM Kill，处于 `CrashLoopBackOff`。此Pod由AI OPS E2E测试创建，属于预期行为。 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 形成完整证据链**：`kubectl_get_by_kind_in_cluster` 发现大规模异常 → `kubectl describe` 对跨节点、跨命名空间的代表 Pod 进行诊断，发现**错误模式完全一致**（`i/o timeout` 到 `registry-1.docker.io:443`），有力地证实了**集群出站网络访问 Docker Hub 被阻断**是根本原因。
- **证据 #5 解释 Terminating 根因**：`reg-diag-tmp` 的 YAML 显示最终器为空，结合其镜像拉取失败的背景，可以判断其 `Terminating` 状态是由于容器从未成功运行，进程不存在，导致优雅终止（发送 SIGTERM）流程无法执行，只能等待 `terminationGracePeriodSeconds` 超时。
- **证据 #6 独立于网络问题**：OOMKilled 的 Pod 是由 E2E 测试触发的独立问题，与当前的网络故障无关。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 崩溃 Pod 的前次容器日志 (g1-e2) | important | 对于确认 OOMKilled 应用的内存增长模式有帮助，但当前证据已足够确定原因。 |
| StartError Pod 的状态最小确认 (g5-e1) | important | 描述已显示其主要错误为 `exec: "curl" not found`，此证据缺失不影响主要结论。 |

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                        │
│ 集群节点 (node1, node2) 出站网络策略/防火墙阻止了流向 registry-1.docker.io:443    │
│ 的 HTTPS (TCP 443) 连接，导致整个集群无法访问公网 Docker Hub。                    │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                        │
│ kubelet 通过 containerd 尝试拉取镜像 → DNS 解析成功(多IP) → TCP 连接 registry-...│
│ → 连接请求被网络出口策略阻断 → 内核返回 SYN 无应答/连接被重置 → 超时 (i/o timeout)│
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                        │
│ kubelet 无法拉取镜像 (e.g., `busybox:1.36.1`)，所有拉取尝试均因网络 i/o timeout   │
│ 而失败。Pod 状态变为 ErrImagePull 并最终退避至 ImagePullBackOff。                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                    │
│ 1. 49个Pod处于 ImagePullBackOff / ErrImagePull 状态                              │
│ 2. Pod 'connectivity-check-tmp' 因无法下载镜像而卡在 ContainerCreating           │
│ 3. Pod 'reg-diag-tmp' 因容器从未启动而无法完成优雅终止，卡在 Terminating          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1、#2、#3、#4，集群中49个Pod镜像拉取失败的根本原因是**集群节点 (node1， node2) 无法建立到公网 Docker Hub (`registry-1.docker.io:443`) 的出站 HTTPS 连接**。证据显示连接请求均因 `i/o timeout` 而被拒绝，这强烈指向了集群出口的网络防火墙或安全策略拦截。

- **置信度**：高 (95%)
    - ✅ 证据 #2、#3、#4 在多个节点和命名空间的代表 Pod 上复现了完全一致的错误 (`i/o timeout` 到 `registry-1.docker.io:443`)。
    - ✅ 证据 #1 确认了受影响 Pod 的巨大范围 (49个)，与网络中断的全局性影响相符。
    - ✅ 所有节点均处于 `Ready` 状态（工具事实），排除了节点故障的可能性。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [应急] 配置私有镜像仓库或代理**
这是最根本的解决方案，可以避免依赖不稳定或不安全的公网仓库。
- **方案A (推荐): 配置镜像仓库代理 (Mirror/Proxy Cache)**。在集群内或内网部署一个 Harbor 或类似工具，所有节点配置 Docker Daemon 或 containerd 使用该代理拉取镜像。Node 级别配置参考 `config.toml`。
- **方案B (临时): 调整集群网络策略**。通过 `iptables` 或云服务商防火墙，添加规则允许从 Node IP 到 `registry-1.docker.io:443` 的出站流量。
    ```bash
    # 在所有节点上执行以下命令可能会导致安全风险，请先评估环境
    # iptables -I OUTPUT -p tcp --dport 443 -d registry-1.docker.io -j ACCEPT
    ```
- **方案C (快速验证): 使用自有仓库**。如果集群能访问内网镜像仓库，修改 Pod 的 Deployment/DaemonSet YAML，将 `image` 指向内网已同步的镜像地址。例如：
    ```bash
    kubectl set image deployment/<deployment-name> <container-name>=<your-private-registry>/busybox:1.36.1 -n <namespace>
    ```

**2. [清理] 强制删除卡住的 Pod**
解除 `reg-diag-tmp` 和 `connectivity-check-tmp` 的卡死状态。
```bash
# 强制删除 Terminating Pod
kubectl delete pod reg-diag-tmp -n default --force --grace-period=0

# 强制删除 ContainerCreating Pod
kubectl delete pod connectivity-check-tmp -n default --force --grace-period=0
```

### 后续优化

1.  **镜像管理**：建立完善的镜像拉取策略。所有关键应用镜像必须从内网私有仓库拉取，避免对公网仓库的强依赖。使用 ImagePullPolicy: `IfNotPresent` 可以减少不必要的拉取。
2.  **监控告警**：配置对大规模 `ImagePullBackOff` / `ErrImagePull` 事件的告警，以便第一时间发现网络或仓库异常。
3.  **资源评估**：对于 `rc-oomkilled-memory-limit-*` 这类 E2E 测试 Pod，确认其资源限制是否合理，或将其标记为非关键，避免占用注意力。
4.  **网络诊断**：如果集群出于安全考虑必须封锁出站流量，请确保已正确配置镜像仓库代理，并验证其可达性。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认网络故障修复 | `kubectl describe pod <任意问题Pod> -n <namespace>` | Events 中不再出现 `Failed to pull image` 或 `ErrImagePull` 错误 |
| 2. 确认问题Pod重建 | `kubectl get pods -A \| grep -E 'ImagePullBackOff\|ErrImagePull\|Terminating\|ContainerCreating'` | 列表中不再有异常Pod |
| 3. 检查 Pod 状态 | `kubectl get pods -A` | 所有 Pod 状态恢复正常 (`Running`， `Completed`)，重启次数不再增加 |

---

## ⚠️ 注意事项
- **强制删除 Pod** (`--force --grace-period=0`) 可能会导致Pod内正在处理的数据丢失，请确保该Pod无状态或数据已持久化。此处诊断工具 `reg-diag-tmp` 和 `connectivity-check-tmp` 是临时诊断 Pod，强制删除风险极低。
- **修改 iptables 规则**前请务必备份当前规则 (`iptables-save > /tmp/iptables-backup.rules`)，以免造成网络中断。
- 当前集群中有一个 `CrashLoopBackOff` 的 Pod (`rc-oomkilled-memory-limit-*`)，它是由 E2E 测试程序创建的，属于预期内的故障模拟，不必对其处理。

---

## 📊 性能统计

├─ 总耗时: 2.1m
├─ 问题定位: 43.9s (35%) ✅
├─ 证据链采集: 31.6s (25%) ✅
├─ 根因分析: 22.3s (18%) ✅
├─ 汇总总结: 26.3s (21%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 24 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-oomkilled, pod-terminating-stuck, pod-sandbox-create-failed
- **参考 Runbook**: pod-imagepull-failed, pod-oomkilled, pod-terminating-stuck, pod-sandbox-create-failed
- **工具调用**: 24 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
