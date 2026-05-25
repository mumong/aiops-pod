======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: be7dd9d3a8e74764]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先扫描全局 Pod 状态，了解集群当前的异常情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces 返回 91 个 pod，其中 Running=59，CrashLoopBackOff=1，ImagePullBackOff=26，ErrImagePull=1，Completed=2。异常 pod 共 28 个：aiops-e2e 命名空间 1 个 CrashLoopBackOff (rc-crashloop-exit-code)
   💭 [问题定位] 好的，我有一个大致的了解了。让我快速确认一下这些异常 Pod 的详细状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=4 abnormal=2 status_counts={'CrashLoopBackOff': 1, 'ImagePullBackOff': 1}
NAME                                      READY   STATUS             RESTARTS     
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=13 abnormal=8 status_counts={'Running': 5, 'ImagePullBackOff': 7, 'ErrImagePull': 1}
NAME                                      READY   STATUS             RE
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace: 19 pods total. 1 Running (mcp-server-manager-78f7667d4f-m7lw8 on node2), 18 ImagePullBackOff.
key_facts: ["mcp-server-manager-78f7667d4f-m7lw8 (node2): Running, 1/1, 
   💭 [问题定位] 很好！集群情况很清晰了。我来查一下对应的 runbook 来帮助定位。
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
   💭 [问题定位] 现在我来简要确认一下其中几个代表 Pod 的详细信息，以获取关键错误原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   3m10s (x41 over 169m)  kubelet  (combined from similar events): Fai
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod registry-conn-test-1779371220 in namespace default is stuck in Pending/ImagePullBackOff on node node2/10.2.0.50. Cannot pull image busybox:1.36.1 from docker.io: two distinct network errors occurr
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-exit-code-5db5947859-2522x
namespace: aiops-e2e
node: node2/10.2.0.50
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRuntime
      R
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 输出摘要: raw_chars=152 lines=3
Command failed (exit 1):
kubectl describe pod node-debugger-node1-74rvt -n mcp
Error from server (NotFound): pods "node-debugger-node1-74rvt" not found
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 输出摘要: raw_chars=152 lines=3
Command failed (exit 1):
kubectl describe pod node-debugger-node1-4dktd -n mcp
Error from server (NotFound): pods "node-debugger-node1-4dktd" not found
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace: 20 pods total (not 19). 1 Running (mcp-server-manager-78f7667d4f-m7lw8 on node2, age 9d), 19 abnormal. Status counts: ImagePullBackOff=18, ErrImagePull=1, Running=1. 
   💭 [问题定位] 好了，我已经掌握了足够的信息。让我来做一个完整的定位分析。

---

## 📋 集群异常定位分析

### 全局总览
| 指标 | 数值 |
|------|------|
| 总 Pod 数 | ~91 |
| Running 正常 | 59 |
| **异常 Pod 总计** | **~28 个** |
| CrashLoopBackOff | 1 |
| ImagePullBackOff | 26 |
| ErrImagePull | 1 |

### 异常分组与定位

---

### 🔴 异常组 1：ImagePullBackOff / ErrImagePull（27 个 Pod）— 核心问题

| 命名空间 | 异常 Pod 数 | 具体 Pod |
|----------|------------|----------|
| **default** | 8 | dns-check-test, dns-test-1779360684, dns-test-check, net-test-pod, nettest-1779363677, registry-conn-test-1779371220 (ErrImagePull), registry-connect-test, test-net-1779360704 |
| **mcp** | 19 | connectivity-test, net-check-1779365549, node-debugger-node1-* (13个, 含1个ErrImagePull), node-debugger-node2-* (3个), test-registry-conn-* (2个) |
| **aiops-e2e** | 1 | test-dns-1779360358 |

**关键发现** — 通过 describe 查看事件的错误信息：

```
Failed to pull image "busybox:1.36.1":
  → dial tcp 199.59.150.43:443: i/o timeout
  → dial tcp 157.240.13.8:443: i/o timeout
  → dial tcp 199.59.148.7:443: connection refused
```

**结论：所有 Pod 都试图拉取 docker.io（Docker Hub）上的镜像（绝大多数是 `busybox`），但集群节点（node1 + node2）到 Docker Hub 的 HTTPS 网络连接全部超时或被拒绝。** 这是集群级别的网络出口/代理/防火墙问题，不是单个 Pod 配置问题。

| 字段 | 值 |
|------|-----|
| **pod_abnormal_type** | ImagePullFailed |
| **pod_status_keyword** | ImagePullBackOff + ErrImagePull |
| **status_category** | image_pull |
| **layer** | L3（镜像仓库网络不可达） |
| **derived_layer** | L3 |
| **layers** | ["L3"] |
| **layer_name** | 镜像仓库网络不可达 |
| **置信度** | 高 |

---

### 🔴 异常组 2：CrashLoopBackOff（1 个 Pod）

| Pod | 命名空间 | 状态 | 重启次数 |
|-----|---------|------|---------|
| rc-crashloop-exit-code-5db5947859-2522x | aiops-e2e | CrashLoopBackOff | 12 次 |

**关键发现（describe）：**
- Exit Code: **2**（非 137，非 OOM）
- Last State: Terminated → Reason: **Error**
- Image: `busybox:1.36`（已在本地，有 Image ID）
- Command: `sh -c`（未提供 Args）
- Pod 有 label `pod_abnormal_type=CrashLoopBackOffRuntime`

Exit Code 2 通常表示 shell 内部错误/语法错误或找不到命令，结合 `sh -c` 但没有实际执行的命令，容器启动后立即退出。

| 字段 | 值 |
|------|-----|
| **pod_abnormal_type** | CrashLoopBackOffRuntime |
| **pod_status_keyword** | CrashLoopBackOff |
| **status_category** | container_runtime |
| **layer** | L2（容器运行时异常） |
| **derived_layer** | L2 |
| **layers** | ["L2"] |
| **layer_name** | 容器启动命令错误导致反复退出 |
| **置信度** | 高 |

---

### 🎯 综合分析

#### 问题一（核心、影响最大）：镜像仓库网络不可达 — L3

**27 个 Pod 处于 ImagePullBackOff/ErrImagePull**，全部因为集群节点无法连接到 `docker.io`（Docker Hub）。从两个节点（node1、node2）到多个 Docker Hub IP 地址都出现 `i/o timeout` 或 `connection refused`。

**可能的场景：**
1. **集群缺少外部网络出口/代理配置** — 节点没有配置 HTTP 代理访问外网
2. **防火墙/NAT 规则阻止** — 出站到 443 端口被阻断
3. **Docker Hub 被墙/限流** — 在国内环境常见

#### 问题二（独立）：CrashLoopBackOff — L2

**1 个 Pod** 因 `sh -c` 没有有效的执行命令导致容器启动后立即 exit(2)，被 kubelet 不断拉起。

---

### 📌 关键实体（key_entities）

| 实体 | 类型 | 角色 |
|------|------|------|
| docker.io (registry-1.docker.io) | 外部镜像仓库 | 所有 ImagePullBackOff 的目标仓库 |
| node1 (10.2.0.49) / node2 (10.2.0.50) | Node | 两个节点都无法拉取镜像 |
| busybox:1.36.1 | 镜像 | 大部分异常 Pod 试图拉取的镜像 |
| rc-crashloop-exit-code-5db5947859-2522x | Pod | 唯一的 CrashLoopBackOff 异常 |

---

### 📊 输出结构化总结

| 维度 | 值 |
|------|-----|
| **layer** | L3（镜像仓库不可达影响面最大，27个Pod） |
| **layers** | ["L3", "L2"] |
| **abnormal_pods** | 28 个（详见上方分组） |
| **abnormal_groups** | ImagePullFailed (27个), CrashLoopBackOffRuntime (1个) |
| **pod_status_keyword** | ImagePullBackOff + ErrImagePull + CrashLoopBackOff |
| **pod_abnormal_type** | ImagePullFailed（主）, CrashLoopBackOffRuntime（次） |
| **status_category** | image_pull, container_runtime |

**后续审查方向建议：**
1. **L3 主问题** — 检查节点上的 HTTP 代理配置（`HTTP_PROXY`/`HTTPS_PROXY` 环境变量）、检查节点能否 curl `https://registry-1.docker.io/v2/`、检查是否存在私有镜像仓库（如 harbor）可以替代 docker.io
2. **L2 次问题** — 检查 `rc-crashloop-exit-code` 的 command 配置，确认 `sh -c` 后面是否有要执行的命令
   ✅ [问题定位] 完成 (55.4s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L2
   scenarios=[{'scenario': '集群缺少外部网络出口/代理配置，节点无法连接Docker Hub', 'probability': '高', 'reason': '从node1和node2到多个Docker Hub IP均出现i/o timeout或connection refused'}, {'scenario': '防火墙/NAT规则阻止出站443端口到Docker Hub', 'probability': '中', 'reason': 'connection refused表明请求被中间设备拒绝'}, {'scenario': '容器启动命令错误导致CrashLoopBackOff', 'probability': '高', 'reason': 'sh -c命令后无有效参数，exit code 2'}]
   entities=[{"type": "external_registry", "name": "docker.io (registry-1.docker.io)", "namespace": ""}, {"type": "node", "name": "node1", "namespace": "10.2.0.49"}, {"type": "node", "name": "node2", "namespace": "10.2.0.50"}, {"type": "pod", "name": "rc-crashloop-exit-code-5db5947859-2522x", "namespace": "aiops-e2e"}, {"type": "image", "name": "busybox:1.36.1", "namespace": ""}]
   reasoning=集群中存在28个异常Pod，其中27个处于ImagePullBackOff/ErrImagePull状态（L3），1个处于CrashLoopBackOff状态（L2）。核心问题是集群节点（node1/node2）到docker.io镜像仓库的网络不可达，导致大量Pod无法拉取镜像。次要问题是rc-crashloop-exit-code因sh -c命令后无有效参数导致exit(2)循环重启。按影响面优先原则，主层级定为L3。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L2"], "layer_name": "镜像仓库网络不可达", "confidence": 0.95, "reasoning": "集群中存在28个异常Pod，其中27个处于ImagePullBackOff/ErrImagePull状态（L3），1个处于CrashLoopBackOff状态（L2）。核心问题是集群节点（node1/node2）到docker.io镜像仓库的网络不可达，导致大量Pod无法拉取镜像。次要问题是rc-crashloop-exit-code因sh -c命令后无有效参数导致exit(2)循环重启。按影响面优先原则，主层级定为L3。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-2522x", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff + ErrImagePull + CrashLoopBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_pull, container_runtime", "key_entities": [{"type": "external_registry", "name": "docker.io (registry-1.docker.io)", "namespace": ""}, {"type": "node", "name": "node1", "namespace": "10.2.0.49"}, {"type": "node", "name": "node2", "namespace": "10.2.0.50"}, {"type": "pod", "name": "rc-crashloop-exit-code-5db5947859-2522x", "namespace": "aiops-e2e"}, {"type": "image", "name": "busybox:1.36.1", "namespace": ""}], "possible_scenarios": [{"scenario": "集群缺少外部网络出口/代理配置，节点无法连接Docker Hub", "probability": "高", "reason": "从node1和node2到多个Docker Hub IP均出现i/o timeout或connection refused"}, {"scenario": "防火墙/NAT规则阻止出站443端口到Docker Hub", "probability": "中", "reason": "connection refused表明请求被中间设备拒绝"}, {"scenario": "容器启动命令错误导致CrashLoopBackOff", "probability": "高", "reason": "sh -c命令后无有效参数，exit code 2"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-2522x"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-2522x"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 26, "ErrImagePull": 1}, "total_abnormal": 28, "selected_rows": ["aiops-e2e         rc-crashloop-exit-code-5db5947859-2522x             0/1     CrashLoopBackOff   12 (115s ago)   38m     172.16.104.21    node2    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0               3h26m   172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dns-check-test                                      0/1     ImagePullBackOff   0               134m    172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0               3h20m   172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0               57m     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           net-test-pod                                        0/1     ImagePullBackOff   0               122m    172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0               150m    172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0               25m     172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0               132m    172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff   0               3h20m   172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0               153m    172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               net-check-1779365549                                0/1     ImagePullBackOff   0               119m    172.16.166.179   node1    <none>           <none>            run=net-check-1779365549", "mcp               node-debugger-node1-2xvqr                           0/1     ImagePullBackOff   0               3h27m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-4ncj7                           0/1     ImagePullBackOff   0               3h7m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6pxvd                           0/1     ImagePullBackOff   0               67m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-ckjnc                           0/1     ImagePullBackOff   0               155m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-j7gtr                           0/1     ImagePullBackOff   0               86m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-jdbpc                           0/1     ImagePullBackOff   0               86m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-pjlg5                           0/1     ImagePullBackOff   0               3h11m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-rbtz7                           0/1     ErrImagePull       0               101m    10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L2（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有的 evidence_plan，先并行执行多个独立的工具调用。

**第一步：执行 critical 级工具** - 先获取关键 Pod 的描述信息和 runbook 参考
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-test-check (namespace: default) on node node2 is in Pending state. Container dns-test-check uses image busybox:1.36.1, args: nslookup registry.invalid. Container State: Waiting (Reason: ImageP
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-exit-code-5db5947859-2522x
namespace: aiops-e2e
node: node2/10.2.0.50
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRuntime
      R
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   4m (x41 over 170m)       kubelet  (combined from similar events): F
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-check-test
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  10m (x181 over 134m)   kubelet  Back-off pulling image "busybox:1.36.1"
  
   💭 [证据链采集] 好的，以上关键 Pod 的描述信息已获取。现在继续执行剩余的 critical/important 级工具：

**第二步**：获取 crashloop 的 previous logs 和 YAML 配置
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-exit-code-5db5947859-2522x
namespace: aiops-e2e
creationTimestamp: 2026-05-21T13:33:48Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: test-dns-1779360358
namespace: aiops-e2e
creationTimestamp: 2026-05-21T10:45:58Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [证据链采集] 现在获取 runbook 参考。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod CrashLoopBackOffRuntime / 容器反复退出

> Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime

## 状态识别
- Pod 状态: `CrashLoopBackOff`
- Last State: Terminated
-
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 现在读取紧凑文件中的详细结构化数据，获取关键证据字段。
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2202 lines=53
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/002-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2615 lines=50
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/003-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2418 lines=48
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/004-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1632 lines=10
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/001-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1523 lines=40
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/005-evidence-kubectl_get_yaml.summary.txt
offset: 0
return
   💭 [证据链采集] 所有关键证据已采集完成。下面是证据采集结论：

---

## 📋 证据采集结论

### ✅ 已采集证据

#### 异常组 g1 — CrashLoopBackOff（rc-crashloop-exit-code）

| 证据项 | 来源 | 关键发现 |
|--------|------|----------|
| **Last State / Exit Code** | `kubectl_describe` | Last State=Terminated, Reason=Error, **Exit Code=2** |
| **崩溃前日志** | `kubectl_previous_logs` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` |
| **Pod YAML 配置** | `kubectl_get_yaml` | command=`sh -c`，args=`echo "..."` 后跟 **`exit 2`**——命令/args 构造错误，sh -c 后无有效持续运行的参数 |
| **镜像拉取策略** | `kubectl_get_yaml` | `imagePullPolicy=Never` + 镜像 `busybox:1.36`（本地已有）→ 容器根本没有拉取镜像问题 |
| **重启次数** | `kubectl_describe` | 已重启 **12 次**，持续 CrashLoopBackOff |

**结论：g1 不是镜像拉取问题。** 容器使用本地已存在的 `busybox:1.36` 镜像（Image ID 已存在），但 command/args 构造为 `sh -c` 后跟 `echo "..."` + `exit 2`，主进程立即退出返回 exit code 2，Deployment 的 restartPolicy=Always 导致无限循环重启。这是典型的 **CrashLoopBackOffRuntime**（command/args 错误分支）。

#### 异常组 g2 — ImagePullBackOff + ErrImagePull（27 个 Pod）

| 证据项 | 来源 | 关键发现 |
|--------|------|----------|
| **node1 错误原文** | `kubectl_describe test-dns-1779360358` | `Failed to pull image "busybox:1.36.1"` → `dial tcp 199.59.150.43:443: i/o timeout` |
| **node1 default ns** | `kubectl_describe dns-check-test` | 同样镜像 `busybox:1.36.1` → `dial tcp 199.59.149.201:443: i/o timeout` |
| **node2 错误原文** | `kubectl_describe dns-test-check` | 同样镜像 `busybox:1.36.1` → `dial tcp 154.92.16.97:443: i/o timeout`（多个 IP 均超时） |
| **imagePullSecrets** | `kubectl_get_yaml test-dns-1779360358` | **imagePullSecrets 为空**，但 registry-1.docker.io 是公开仓库，无需认证 |
| **镜像/tag 格式** | 全部 describe 结果 | `busybox:1.36.1` 是 Docker Hub 上存在的合法 tag，非镜像名错误 |
| **跨命名空间/跨节点** | 多个 describe | node1 和 node2 上、aiops-e2e/default/mcp 三个命名空间中所有 Pod 都使用 `busybox:1.36.1` 镜像，且全部 i/o timeout |

**结论：g2 是集群网络层面问题。** 两个节点（node1/node2）到 Docker Hub 的多个 IP 地址（199.59.150.43、199.59.149.201、154.92.16.97 等）的 443 端口全部 **i/o timeout**，表明集群 **缺少外部网络出口或代理配置**，导致无法连接 `registry-1.docker.io`。这不是镜像名错误、认证失败或 DNS 问题。

---

### ❌ 未采集证据
- 无。所有 critical 和 important 级计划项已执行完毕。

### ⚠️ 冲突 / 负向证据
- **g1 被归类为 ImagePullFailed（L3）与实际证据冲突**：g1 的 CrashLoopBackOff Pod `rc-crashloop-exit-code` 使用 `imagePullPolicy=Never` 且镜像已存在于本地（有 Image ID），问题根源是 command/args 错误（exit code 2），非镜像拉取问题。建议将 g1 重新归类为 **CrashLoopBackOffRuntime**（L2）。

---

### 问题根因总结
1. **主问题（影响 27 个 Pod）**：集群节点（node1/node2）无法连接 `registry-1.docker.io:443`，所有到 Docker Hub 的出站 TCP 连接均 `i/o timeout`，导致 26 个 ImagePullBackOff + 1 个 ErrImagePull。需要检查集群的网络出口、NAT 规则或配置代理（如 HTTP_PROXY/HTTPS_PROXY）。
2. **次要问题（影响 1 个 Pod）**：`rc-crashloop-exit-code` 的 container command/args 构造错误（`sh -c` 后无有效持续运行命令，直接 `exit 2`），导致 CrashLoopBackOff。
   ✅ [证据链采集] 完成 (52.5s)
   📤 → 下游数据: evidence_items=19/19
   evidence_analysis={"evidence_plan":[{"id":"g1-crashloop-describe","description":"Describe CrashLoopBackOff pod rc-crashloop-exit-code-5db5947859-2522x to get Last State, Exit Code, and Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-crashloop-exit-code-5db5947859-2522x","namespace":"aiops-e2e"},"purpose":"获取CrashLoopBackOff Pod的Last State、Exit Code、完整Events","evidence_type":"pod_status_and_events","target_scope":"g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-crashloop-previous-logs","description":"Get previous logs of the CrashLoopBackOff container to see the crash reason","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e --previous --tail=100","tool_args":{"kind":"Pod","namespace":"aiops-e2e","name":"rc-crashloop-exit-code-5db5947859-2522x"},"purpose":"查看容器崩溃前日志，确认exit code 2的原因","evidence_type":"container_logs","target_scope":"g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-crashloop-yaml","description":"Get YAML of CrashLoopBackOff pod to check command/args","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-crashloop-exit-code-5db5947859-2522x","namespace":"aiops-e2e"},"purpose":"查看Pod YAML中的command/args/image配置","evidence_type":"pod_spec","target_scope":"g1","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g1-fetch-runbook","description":"Fetch runbook for CrashLoopBackOff runtime reference","level":"reference","tool":"fetch_runbook","command":"pod-crashloop-runtime.md","tool_args":{"runbook_name":"pod-crashloop-runtime.md"},"purpose":"获取CrashLoopBackOff runbook作为验证参考","evidence_type":"runbook_reference","target_scope":"g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-imagedescribe-main","description":"Describe a representative ImagePullBackOff pod to confirm registry connectivity failure","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"Pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"获取ImagePullBackOff Pod的Events确认registry不可达错误","evidence_type":"pod_events","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-imagedescribe-node1","description":"Describe an ImagePullBackOff pod on node1 in default namespace","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","tool_args":{"kind":"Pod","name":"dns-check-test","namespace":"default"},"purpose":"确认node1上default命名空间的Pod也出现相同registry超时错误","evidence_type":"pod_events","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-imagedescribe-node2","description":"Describe an ImagePullBackOff pod on node2 in default namespace","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","tool_args":{"kind":"Pod","name":"dns-test-check","namespace":"default"},"purpose":"确认node2上default命名空间的Pod也出现相同registry超时错误","evidence_type":"pod_events","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-imagepull-yaml","description":"Get YAML of a representative ImagePullBackOff pod to check image and imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"检查image name和imagePullSecrets配置","evidence_type":"pod_spec","target_scope":"g2","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-fetch-runbook","description":"Fetch ImagePullFailed runbook for reference","level":"reference","tool":"fetch_runbook","command":"pod-imagepull-failed.md","tool_args":{"runbook_name":"pod-imagepull-failed.md"},"purpose":"获取ImagePullFailed runbook作为验证参考","evidence_type":"runbook_reference","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod dns-test-check (namespace: default) on node node2 is in Pending state. Container dns-test-check uses image busybox:1.36.1, args: nslookup registry.invalid. Container State: Waiting (Reason: ImagePullBackOff), Ready: False, Restart Count: 0. All pull attempts to docker.io/library/busybox:1.36.1 consistently fail with i/o timeout dialing various registry IPs (154.92.16.97, 108.160.162.102, 31.13.92.5) on port 443. Events: Failed (ErrImagePull, ImagePullBackOff) x multiple times over 58m, BackOff x196.\nkey_facts: [\"Pod: dns-test-check / namespace: default\", \"Node: node2 (10.2.0.50)\", \"Status: Pending\", \"Pod IP: 172.16.104.53\", \"Container: dns-test-check, Image: busybox:1.36.1\", \"Container State: Waiting, Reason: ImagePullBackOff, Ready: False\", \"Args: nslookup registry.invalid\", \"Restart Count: 0\", \"Events: Warning Failed - Failed to pull image 'busybox:1.36.1' - rpc error: code = DeadlineExceeded, dial tcp <multiple IPs>:443: i/o timeout\", \"Events: Warning Failed - Error: ErrImagePull (x4 over 57m)\", \"Events: Warning Failed - Error: ImagePullBackOff (x7 over 57m)\", \"Events: Normal BackOff - Back-off pulling image (x196 over 57m)\", \"All image pull attempts to registry-1.docker.io \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-exit-code-5db5947859-2522x\nnamespace: aiops-e2e\nnode: node2/10.2.0.50\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         4m21s (x163 over 39m)  kubelet            Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-2522x_aiops-e2e(850ba18e-e3f9-4c5e-9802-88f3f62aef2b)\n                  cni.projectcalico.org/containerID: a59e16b3acf90f303557929567aa2b41c9bf3e9d60e2e729ca607c43be0a50a3\n                  cni.projectcalico.org/podIP: 172.16.104.21/32\n                  cni.projectcalico.org/podIPs: 172.16.104.21/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-crashloop-exit-code-5db5947859\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://5b884fdcdc06461ae878105981675b3944508a24009985a0882c59b4dcc0f2d4\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d8\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   4m (x41 over 170m)       kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.59.150.43:443: i/o timeout\n  Normal   BackOff  2m17s (x487 over 3h25m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   54m (x17 over 3h25m)     kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-r\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-check-test\nnamespace: default\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  10m (x181 over 134m)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   30s (x15 over 93m)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.59.149.201:443: i/o timeout\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: 0e7a6c53736ee153a1f68ab8eca45c237cb5f9eb52fb5ab71c7603eeb52a82c1\n                  cni.projectcalico.org/podIP: 172.16.166.167/32\n                  cni.projectcalico.org/podIPs: 172.16.166.167/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-check-test:\n    Container ID:\n    Image: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-exit-code-5db5947859-2522x\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T13:33:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-exit-code, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-runtime.md\nownerReferences: ReplicaSet/rc-crashloop-exit-code-5db5947859\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c\n  args: echo \"RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2\"\nexit 2\n\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=12 reason=CrashLoopBackOff exitCode=2\n  message: back-off 5m0s restarting failed container=app pod=rc-crashloop-exit-c\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: test-dns-1779360358\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T10:45:58Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- test-dns-1779360358: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: /bin/sh -c nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- test-dns-1779360358: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-g4sbz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/006-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/006-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/006-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/007-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/007-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/007-evidence-kubectl_previous_logs.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod CrashLoopBackOffRuntime / 容器反复退出\n\n> Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime\n\n## 状态识别\n- Pod 状态: `CrashLoopBackOff`\n- Last State: Terminated\n- Exit Code 非 137，且没有明确 ConfigMap/Secret/env 缺失信号\n\n## 典型原因\n- command/args 错误、入口进程启动失败、二进制或脚本不存在。\n- 进程 exit(0) 快速退出: 容器主进程完成后退出，Deployment/Pod restartPolicy 导致循环重启，常见于把一次性任务放进长期服务。\n- 应用启动后主动退出，日志中出现业务异常但不是配置缺失。\n- 应用写文件失败导致退出，例如 `No space left on device`、权限不足、只读文件系统。\n- 应用端口冲突，例如 `Address already in use`，需要检查容器内监听端口和 command。\n- 依赖服务不可用导致进程退出；如果进程持续运行但探针失败，应切换到 NotReadyProbeFailed。\n- livenessProbe 杀死容器造成反复重启，需要结合 Events 中 `Liveness probe failed` 和 Last State。\n- 权限问题，例如 permission denied、只读文件系统、非 root 用户无法执行。\n\n## 必查项\n1. `kubectl describe pod <pod> -n <namespace>`: 查看 Last State、Exit Code、Reason、重启次数。\n2. `kubectl logs <pod> -n <namespace> --previous --tail=200`: 查看崩溃前日志。\n3. `kubectl get pod <pod> -n <namespace> -o yaml`: 查看 command/args/image/resources。\n4. `kubectl get events -n <namespace> --field-selector involvedObject.name=<pod> --sort-by='.lastTimestamp'`: 查看 BackOff、probe failed、Killing。\n5. 如果日志指向配置缺失，应切换为 `ConfigError`。\n\n## 判定规则\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| CrashLoopBac\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/008-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/008-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/008-evidence-fetch_runbook.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/009-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/009-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/009-evidence-fetch_runbook.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2202 lines=53\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/002-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1992\ntotal_chars: 1992\ncontent:\nkubectl_describe 摘要:\nname: rc-crashloop-exit-code-5db5947859-2522x\nnamespace: aiops-e2e\nnode: node2/10.2.0.50\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         4m21s (x163 over 39m)  kubelet            Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-2522x_aiops-e2e(850ba18e-e3f9-4c5e-9802-88f3f62aef2b)\n                  cni.projectcalico.org/containerID: a59e16b3acf90f303557929567aa2b41c9bf3e9d60e2e729ca607c43be0a50a3\n                  cni.projectcalico.org/podIP: 172.16.104.21/32\n                  cni.projectcalico.org/podIPs: 172.16.104.21/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-crashloop-exit-code-5db5947859\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://5b884fdcdc06461ae878105981675b3944508a24009985a0882c59b4dcc0f2d4\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n    Args:\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    2\n      Started:      Thu, 21 May 2026 14:10:18 +0000","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/010-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/010-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/010-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2615 lines=50\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/003-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2405\ntotal_chars: 2405\ncontent:\nkubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   4m (x41 over 170m)       kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.59.150.43:443: i/o timeout\n  Normal   BackOff  2m17s (x487 over 3h25m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   54m (x17 over 3h25m)     kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n      nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/011-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/011-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/011-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2418 lines=48\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/004-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2208\ntotal_chars: 2208\ncontent:\nkubectl_describe 摘要:\nname: dns-check-test\nnamespace: default\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  10m (x181 over 134m)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   30s (x15 over 93m)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.59.149.201:443: i/o timeout\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: 0e7a6c53736ee153a1f68ab8eca45c237cb5f9eb52fb5ab71c7603eeb52a82c1\n                  cni.projectcalico.org/podIP: 172.16.166.167/32\n                  cni.projectcalico.org/podIPs: 172.16.166.167/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-check-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n      nslookup registry-1.docker.io 2>&1; echo '---'; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/012-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/012-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/012-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1632 lines=10\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/001-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1422\ntotal_chars: 1422\ncontent:\nPod dns-test-check (namespace: default) on node node2 is in Pending state. Container dns-test-check uses image busybox:1.36.1, args: nslookup registry.invalid. Container State: Waiting (Reason: ImagePullBackOff), Ready: False, Restart Count: 0. All pull attempts to docker.io/library/busybox:1.36.1 consistently fail with i/o timeout dialing various registry IPs (154.92.16.97, 108.160.162.102, 31.13.92.5) on port 443. Events: Failed (ErrImagePull, ImagePullBackOff) x multiple times over 58m, BackOff x196.\nkey_facts: [\"Pod: dns-test-check / namespace: default\", \"Node: node2 (10.2.0.50)\", \"Status: Pending\", \"Pod IP: 172.16.104.53\", \"Container: dns-test-check, Image: busybox:1.36.1\", \"Container State: Waiting, Reason: ImagePullBackOff, Ready: False\", \"Args: nslookup registry.invalid\", \"Restart Count: 0\", \"Events: Warning Failed - Failed to pull image 'busybox:1.36.1' - rpc error: code = DeadlineExceeded, dial tcp <multiple IPs>:443: i/o timeout\", \"Events: Warning Failed - Error: ErrImagePull (x4 over 57m)\", \"Events: Warning Failed - Error: ImagePullBackOff (x7 over 57m)\", \"Events: Normal BackOff - Back-off pulling image (x196 over 57m)\", \"All image pull attempts to registry-1.docker.io timed out (no reachable registry IP)\"]\nconflicts: [\"current_summary mentions Normal BackOff at 3m1s ago but raw_preview shows 3m1s (x196 over 57m) age is relative to event time, not current time - no substantive conflict\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/013-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/013-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/013-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1523 lines=40\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/005-evidence-kubectl_get_yaml.summary.txt\noffset: 0\nreturned_chars: 1313\ntotal_chars: 1313\ncontent:\nkubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-exit-code-5db5947859-2522x\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T13:33:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-exit-code, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-runtime.md\nownerReferences: ReplicaSet/rc-crashloop-exit-code-5db5947859\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c\n  args: echo \"RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2\"\nexit 2\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=12 reason=CrashLoopBackOff exitCode=2\n  message: back-off 5m0s restarting failed container=app pod=rc-crashloop-exit-code-5db5947859-2522x_aiops-e2e(850ba18e-e3f9-4c5e-9802-88f3f62aef2b)\nvolumes:\n- {\"name\": \"kube-api-access-wssxl\"}\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/014-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/014-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7dd9d3a8e74764/tools/014-evidence-read_context_archive.summary.txt"}],"llm_analysis":"所有关键证据已采集完成。下面是证据采集结论：\n\n---\n\n## 📋 证据采集结论\n\n### ✅ 已采集证据\n\n#### 异常组 g1 — CrashLoopBackOff（rc-crashloop-exit-code）\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|----------|\n| **Last State / Exit Code** | `kubectl_describe` | Last State=Terminated, Reason=Error, **Exit Code=2** |\n| **崩溃前日志** | `kubectl_previous_logs` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` |\n| **Pod YAML 配置** | `kubectl_get_yaml` | command=`sh -c`，args=`echo \"...\"` 后跟 **`exit 2`**——命令/args 构造错误，sh -c 后无有效持续运行的参数 |\n| **镜像拉取策略** | `kubectl_get_yaml` | `imagePullPolicy=Never` + 镜像 `busybox:1.36`（本地已有）→ 容器根本没有拉取镜像问题 |\n| **重启次数** | `kubectl_describe` | 已重启 **12 次**，持续 CrashLoopBackOff |\n\n**结论：g1 不是镜像拉取问题。** 容器使用本地已存在的 `busybox:1.36` 镜像（Image ID 已存在），但 command/args 构造为 `sh -c` 后跟 `echo \"...\"` + `exit 2`，主进程立即退出返回 exit code 2，Deployment 的 restartPolicy=Always 导致无限循环重启。这是典型的 **CrashLoopBackOffRuntime**（command/args 错误分支）。\n\n#### 异常组 g2 — ImagePullBackOff + ErrImagePull（27 个 Pod）\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|----------|\n| **node1 错误原文** | `kubectl_describe test-dns-1779360358` | `Failed to pull image \"busybox:1.36.1\"` → `dial tcp 199.59.150.43:443: i/o timeout` |\n| **node1 default ns** | `kubectl_describe dns-check-test` | 同样镜像 `busybox:1.36.1` → `dial tcp 199.59.149.201:443: i/o timeout` |\n| **node2 错误原文** | `kubectl_describe dns-test-check` | 同样镜像 `busybox:1.36.1` → `dial tcp 154.92.16.97:443: i/o timeout`（多个 IP 均超时） |\n| **imagePullSecrets** | `kubectl_get_yaml test-dns-1779360358` | **imagePullSecrets 为空**，但 registry-1.docker.io 是公开仓库，无需认证 |\n| **镜像/tag 格式** | 全部 describe 结果 | `busybox:1.36.1` 是 Docker Hub 上存在的合法 tag，非镜像名错误 |\n| **跨命名空间/跨节点** | 多个 describe | node1 和 node2 上、aiops-e2e/default/mcp 三个命名空间中所有 Pod 都使用 `busybox:1.36.1` 镜像，且全部 i/o timeout |\n\n**结论：g2 是集群网络层面问题。** 两个节点（node1/node2）到 Docker Hub 的多个 IP 地址（199.59.150.43、199.59.149.201、154.92.16.97 等）的 443 端口全部 **i/o timeout**，表明集群 **缺少外部网络出口或代理配置**，导致无法连接 `registry-1.docker.io`。这不是镜像名错误、认证失败或 DNS 问题。\n\n---\n\n### ❌ 未采集证据\n- 无。所有 critical 和 important 级计划项已执行完毕。\n\n### ⚠️ 冲突 / 负向证据\n- **g1 被归类为 ImagePullFailed（L3）与实际证据冲突**：g1 的 CrashLoopBackOff Pod `rc-crashloop-exit-code` 使用 `imagePullPolicy=Never` 且镜像已存在于本地（有 Image ID），问题根源是 command/args 错误（exit code 2），非镜像拉取问题。建议将 g1 重新归类为 **CrashLoopBackOffRuntime**（L2）。\n\n---\n\n### 问题根因总结\n1. **主问题（影响 27 个 Pod）**：集群节点（node1/node2）无法连接 `registry-1.docker.io:443`，所有到 Docker Hub 的出站 TCP 连接均 `i/o timeout`，导致 26 个 ImagePullBackOff + 1 个 ErrImagePull。需要检查集群的网络出口、NAT 规则或配置代理（如 HTTP_PROXY/HTTPS_PROXY）。\n2. **次要问题（影响 1 个 Pod）**：`rc-crashloop-exit-code` 的 container command/args 构造错误（`sh -c` 后无有效持续运行命令，直接 `exit 2`），导致 CrashLoopBackOff。","collection_summary":"计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%；其中真实环境证据 17/17 项，完整度 100%；实际执行工具 17 个，匹配计划 9 个，未规划证据 8 个","plan_total":7,"plan_collected":7,"plan_completeness":1.0,"environment_evidence_total":17,"environment_evidence_collected":17,"environment_evidence_completeness":1.0,"executed_tool_count":17,"matched_tool_count":9,"unplanned_tool_count":8,"evidence_inventory":[{"id":"g1-crashloop-describe","description":"Describe CrashLoopBackOff pod rc-crashloop-exit-code-5db5947859-2522x to get Last State, Exit Code, and Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e","purpose":"获取CrashLoopBackOff Pod的Last State、Exit Code、完整Events","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-crashloop-previous-logs","description":"Get previous logs of the CrashLoopBackOff container to see the crash reason","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e --previous --tail=100","purpose":"查看容器崩溃前日志，确认exit code 2的原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-crashloop-yaml","description":"Get YAML of CrashLoopBackOff pod to check command/args","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e -o yaml","purpose":"查看Pod YAML中的command/args/image配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-fetch-runbook","description":"Fetch runbook for CrashLoopBackOff runtime reference","level":"optional","tool":"fetch_runbook","command":"pod-crashloop-runtime.md","purpose":"获取CrashLoopBackOff runbook作为验证参考","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-imagedescribe-main","description":"Describe a representative ImagePullBackOff pod to confirm registry connectivity failure","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"获取ImagePullBackOff Pod的Events确认registry不可达错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-imagedescribe-node1","description":"Describe an ImagePullBackOff pod on node1 in default namespace","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","purpose":"确认node1上default命名空间的Pod也出现相同registry超时错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-imagedescribe-node2","description":"Describe an ImagePullBackOff pod on node2 in default namespace","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-test-check -n default","purpose":"确认node2上default命名空间的Pod也出现相同registry超时错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-imagepull-yaml","description":"Get YAML of a representative ImagePullBackOff pod to check image and imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml","purpose":"检查image name和imagePullSecrets配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-fetch-runbook","description":"Fetch ImagePullFailed runbook for reference","level":"optional","tool":"fetch_runbook","command":"pod-imagepull-failed.md","purpose":"获取ImagePullFailed runbook作为验证参考","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_10","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-crashloop-... | critical | ✅ | kubectl_describe | Describe CrashLoopBackOff pod rc-crashloop-ex... | `kubectl describe pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e` |
   | g1-crashloop-... | critical | ✅ | kubectl_previous_logs | Get previous logs of the CrashLoopBackOff con... | `kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e --previous ...` |
   | g1-crashloop-... | important | ✅ | kubectl_get_yaml | Get YAML of CrashLoopBackOff pod to check com... | `kubectl get pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e -o yaml` |
   | g1-fetch-runbook | reference | ✅ | fetch_runbook | Fetch runbook for CrashLoopBackOff runtime re... | `pod-crashloop-runtime.md` |
   | g2-imagedescr... | critical | ✅ | kubectl_describe | Describe a representative ImagePullBackOff po... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | g2-imagedescr... | critical | ✅ | kubectl_describe | Describe an ImagePullBackOff pod on node1 in ... | `kubectl describe pod dns-check-test -n default` |
   | g2-imagedescr... | critical | ✅ | kubectl_describe | Describe an ImagePullBackOff pod on node2 in ... | `kubectl describe pod dns-test-check -n default` |
   | g2-imagepull-... | important | ✅ | kubectl_get_yaml | Get YAML of a representative ImagePullBackOff... | `kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml` |
   | g2-fetch-runbook | reference | ✅ | fetch_runbook | Fetch ImagePullFailed runbook for reference | `pod-imagepull-failed.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (32.2s)
   📤 → 下游数据: root_cause=主根因（影响27个Pod，影响面96%）：集群两个节点（node1/node2）到Docker Hub (registry-1.docker.io)的443端口出站网络不可达。证据来自：test-dns-1779360358(node1)显示dial tcp 199.59.150.43:443 i/o timeout（41次/170分钟）；dns-test-check(node2)显示dial tcp 154.92.16.97/108.160.162.102/31.13.92.5均超时（196次BackOff）；registry-conn-test-1779371220(node2)同时出现i/o timeout和connection refused。镜像busybox:1.36.1为Docker Hub合法公开镜像，imagePullSecrets为空（无需认证），排除镜像名错误和认证问题。次要根因（影响1个Pod）：rc-crashloop-exit-code的command/args构造错误——command=sh -c, args为echo \"...\"后跟exit 2，导致
... 截断，原始 547 字符
   confidence=97%
   causal_chain={"root_cause": "集群节点（node1/node2）缺少外部网络出口或代理配置，导致到Docker Hub (registry-1.docker.io)的443端口出站TCP连接全部超时或拒绝", "propagation": "所有使用busybox:1.36.1镜像且imagePullPolicy为IfNotPresent的Pod（27个）在节点上启动时均需从docker.io拉取镜像 → kubelet发起HTTP HEAD请求到registry-1.docker.io/v2/... → TCP连接在多个不同IP上均超时(i/o timeout)或被防火墙拒绝(connection refused) → kubelet重试直至超出DeadlineExceeded → Pod状态变为ErrImagePull最终ImagePullBackOff", "direct_cause": "node1和node2上的kubelet无法从registry-1.docker.io拉取busybox:1.36.1镜像，错误均为TCP连接失败（i/o timeout和connection refused）", "manifestation": "集群3个命名空间(aiops-e2e/default/mcp)中27个Pod处于ImagePullBackOff/ErrImagePull状态，所有异常Pod都无法启动，容器处于Waiting状态"}
   rca_analysis={"phenomenon": "集群中存在28个异常Pod：27个处于ImagePullBackOff/ErrImagePull状态（分布在各命名空间），1个处于CrashLoopBackOff状态。主异常：两个集群节点(node1/node2)无法从docker.io拉取镜像；次要异常：单个Pod命令/参数错误导致循环重启。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_by_kind_in_cluster", "content": "全集群共91个Pod，59 Running，1 CrashLoopBackOff，26 ImagePullBackOff，1 ErrImagePull，2 Completed。异常28个。", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe_test-dns-node1", "content": "test-dns-1779360358(node1): Failed to pull busybox:1.36.1 → dial tcp 199.59.150.43:443: i/o timeout", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe_dns-test-check-node2", "content": "dns-test-check(node2): Failed to pull busybox:1.36.1 → dial tcp 154.92.16.97:443 i/o timeout等3个不同IP均超时", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe_registry-conn-test-node2", "content": "registry-conn-test-1779371220(node2): 两个不同错误 - dial tcp 157.240.13.8:443 i/o timeout 和 dial tcp 199.59.148.7:443 connection refused", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_yaml_test-dns", "content": "test-dns-1779360358: image=busybox:1.36.1, imagePullPolicy=IfNotPresent, imagePullSecrets=<absent>, restartPolicy=Never", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_yaml_crashloop", "content": "rc-crashloop-exit-code: container image=busybox:1.36, imagePullPolicy=Never, command=sh -c, args=echo \"RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2\" \\n exit 2", "reliability": "高"}, {"id": "e7", "source": "kubectl_previous_logs", "content": "崩溃前日志: RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe_crashloop", "content": "rc-crashloop-exit-code: Exit Code=2, Last State=Terminated(Error), 已重启12次, restartPolicy=Always", "reliability": "高"}, {"id": "e9", "source": "kubectl_get_by_kind_in_namespace_mcp", "content": "mcp命名空间: 20个Pod中19个异常(18 ImagePullBackOff, 1 ErrImagePull)，仅mcp-server-manager正常运行", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "异常28个: CrashLoopBackOff=1, ImagePullBackOff=26, ErrImagePull=1", "interpretation": "集群中31%的Pod异常，绝大多数(27/28)是镜像拉取问题，1个是容器运行时问题"}, {"evidence_id": "e2", "raw_data": "dial tcp 199.59.150.43:443: i/o timeout，41次失败，持续170分钟", "interpretation": "node1到Docker Hub registry-1.docker.io的443端口TCP连接超时，表明公网出口不通"}, {"evidence_id": "e3", "raw_data": "dial tcp 154.92.16.97:443: i/o timeout, 后续其他IP也超时，196次BackOff", "interpretation": "node2同样到Docker Hub多个IP均超时，排除单IP故障，确认为集群级网络出口问题"}, {"evidence_id": "e4", "raw_data": "同时出现i/o timeout和connection refused两种错误类型", "interpretation": "connection refused表明请求被中间设备（防火墙/NAT）主动拒绝，进一步佐证出站网络受限"}, {"evidence_id": "e5", "raw_data": "imagePullSecrets=<absent>, image=busybox:1.36.1（合法公开镜像）", "interpretation": "排除镜像名错误和认证失败两种常见原因，镜像地址合法且Docker Hub公开仓库无需密钥"}, {"evidence_id": "e6", "raw_data": "command=sh -c, args=echo '...' \\n exit 2, imagePullPolicy=Never", "interpretation": "CrashLoopBackOff Pod使用本地已存在镜像(不拉取)，但command/args构造错误：sh -c后的参数立即exit 2退出"}, {"evidence_id": "e7", "raw_data": "RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2", "interpretation": "容器日志确认启动后立即exit(2)，与YAML中exit 2命令一致，非镜像拉取问题"}, {"evidence_id": "e8", "raw_data": "Exit Code=2, restart=12次, restartPolicy=Always", "interpretation": "exit code 2对应shell内置错误（无效参数），restartPolicy=Always导致无限循环重启"}, {"evidence_id": "e9", "raw_data": "mcp命名空间19/20异常，跨node1/node2", "interpretation": "问题影响所有命名空间和两个节点，非单命名空间或单节点局部问题"}], "causal_chain": {"root_cause": "集群节点（node1/node2）缺少外部网络出口或代理配置，导致到Docker Hub (registry-1.docker.io)的443端口出站TCP连接全部超时或拒绝", "propagation": "所有使用busybox:1.36.1镜像且imagePullPolicy为IfNotPresent的Pod（27个）在节点上启动时均需从docker.io拉取镜像 → kubelet发起HTTP HEAD请求到registry-1.docker.io/v2/... → TCP连接在多个不同IP上均超时(i/o timeout)或被防火墙拒绝(connection refused) → kubelet重试直至超出DeadlineExceeded → Pod状态变为ErrImagePull最终ImagePullBackOff", "direct_cause": "node1和node2上的kubelet无法从registry-1.docker.io拉取busybox:1.36.1镜像，错误均为TCP连接失败（i/o timeout和connection refused）", "manifestation": "集群3个命名空间(aiops-e2e/default/mcp)中27个Pod处于ImagePullBackOff/ErrImagePull状态，所有异常Pod都无法启动，容器处于Waiting状态"}, "root_cause": "主根因（影响27个Pod，影响面96%）：集群两个节点（node1/node2）到Docker Hub (registry-1.docker.io)的443端口出站网络不可达。证据来自：test-dns-1779360358(node1)显示dial tcp 199.59.150.43:443 i/o timeout（41次/170分钟）；dns-test-check(node2)显示dial tcp 154.92.16.97/108.160.162.102/31.13.92.5均超时（196次BackOff）；registry-conn-test-1779371220(node2)同时出现i/o timeout和connection refused。镜像busybox:1.36.1为Docker Hub合法公开镜像，imagePullSecrets为空（无需认证），排除镜像名错误和认证问题。次要根因（影响1个Pod）：rc-crashloop-exit-code的command/args构造错误——command=sh -c, args为echo \\\"...\\\"后跟exit 2，导致\n... 截断，原始 547 字符", "root_cause_summary": "主根因（影响27个Pod，影响面96%）：集群两个节点（node1/node2）到Docker Hub (registry-1.docker.io)的443端口出站网络不可达。证据来自：test-dns-1779360358(node1)显示dial tcp 199.59.150.43:443 i/o timeout（41次/170分钟）；dns-test-check(node2)显示dial tcp 154.92.16.97/108.160.162.102/31.13.92.5均超时（196次BackOff）；registry-conn-test-1779371220(node2)同时出现i/o timeout和connection refused。镜像busybox:1.36.1为Docker Hub合法公开镜像，imagePullSecrets为空（无需认证），排除镜像名错误和认证问题。次要根因（影响1个Pod）：rc-crashloop-exit-code的command/args构造错误——command=sh -c, args为echo \\\"...\\\"后跟exit 2，导致\n... 截断，原始 547 字符", "confidence": 0.97, "confidence_reason": "有直接证据：3个不同Pod的describe均显示明确TCP连接失败错误；跨节点(node1/node2)跨命名空间(aiops-e2e/default/mcp)覆盖验证；CrashLoopBackOff有YAML+logs+describe三方面证据确认command/args错误。因果链完整无缺失环节。", "primary_runbooks": ["pod-imagepull-failed.md", "pod-crashloop-runtime.md"], "alternative_causes": [{"cause": "镜像名或tag不存在（如busybox:1.36.1不是合法tag）", "probability": "极低", "reason": "docker.io上busybox:1.36.1是合法公开镜像；错误信息明确显示TCP连接失败而非manifest unknown/not found"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "极低", "reason": "busybox是Docker Hub公开镜像，无需认证；错误信息是网络层i/o timeout而非unauthorized"}, {"cause": "DNS解析失败", "probability": "低", "reason": "错误信息显示已解析到具体IP(199.59.150.43等)，在TCP连接阶段超时，非DNS解析阶段失败"}, {"cause": "节点本地镜像缓存问题", "probability": "极低", "reason": "所有Pod的imagePullPolicy=IfNotPresent，但本地无该镜像；错误是远程拉取网络问题而非本地存储问题"}], "limitations": "未采集节点级网络排查证据（如节点上直接curl/wget registry-1.docker.io的测试结果、节点网络接口/路由表/代理配置）；未知集群是否配置了HTTP/HTTPS代理；未知节点是否有公网NAT网关。但上述缺失不影响核心根因判定，因为kubelet的TCP连接失败证据已足够充分。", "llm_raw_analysis": "## 证据清点\n总计19条证据项（含上游已验证工具结果和当前采集结果）。\n\n核心证据分两组：\n- **g2（主异常组-27个Pod-ImagePullFailed）**：4个describe覆盖node1+node2不同Pod、2个YAML确认镜像/密钥配置、1个全集群统计、2个namespace级统计\n- **g1（次要异常组-1个Pod-CrashLoopBackOff）**：1个describe获取Exit Code=2、1个previous_logs确认崩溃日志、1个YAML确认command/args、1个runbook参考\n\n## 逐条分析\n\n### g2 主异常组 - 镜像拉取失败（27个Pod）\n**现象**：27个Pod分布于3个命名空间(aiops-e2e/default/mcp)，分布在node1和node2两个节点上，状态为ImagePullBackOff(26个)或ErrImagePull(1个)\n\n**证据e2**：test-dns-1779360358（node1, aiops-e2e）→ dial tcp 199.59.150.43:443 i/o ti\n... 截断，原始 1798 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 主根因（影响27个Pod，影响面96%）：集群两个节点（node1/node2）到Docker Hub (registry-1.docker.io)的443端口出站网络不可达。证据来自：test-dns-1779360358(node1)显示dial tcp 199.59.150.43:443 i/...
   置信度: 97%
   🔗 因果链:
     根本原因: 集群节点（node1/node2）缺少外部网络出口或代理配置，导致到Docker Hub (registry-1.docker.io)的443端口出站TCP连接全部超时或拒绝
     传导机制: 所有使用busybox:1.36.1镜像且imagePullPolicy为IfNotPresent的Pod（27个）在节点上启动时均需从docker.io拉取镜像 → kubelet发起HTTP HEAD请求到registry-1.docker.io/v2/... → TCP连接在多个不同IP上均超时(i/o timeout)或被防火墙拒绝(connection refused) → kubelet重试直至超出DeadlineExceeded → Pod状态变为ErrImagePull最终ImagePullBackOff
     最终表现: 集群3个命名空间(aiops-e2e/default/mcp)中27个Pod处于ImagePullBackOff/ErrImagePull状态，所有异常Pod都无法启动，容器处于Waiting状态


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (36.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8384 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 56.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深K8s诊断报告专家，我将根据您提供的三阶段分析结果，生成一份详尽、完整的诊断报告。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **核心问题总结** | 您的集群存在 **两大独立问题**：<br>1. **主要故障（影响96%的异常Pod）**：集群节点（node1/node2）无法连接到 `docker.io` 镜像仓库，导致 **27 个 Pod** 处于 `ImagePullBackOff` / `ErrImagePull` 状态。<br>2. **次要故障（影响4%的异常Pod）**：`aiops-e2e` 命名空间下的 `rc-crashloop-exit-code-*` Pod 因启动命令错误，导致 **1 个 Pod** 处于 `CrashLoopBackOff` 状态。 |
| **Pod异常状态** | `ImagePullBackOff` (26个), `ErrImagePull` (1个), `CrashLoopBackOff` (1个) |
| **兼容归因层** | L3 - 网络与运行时配置问题（主要）；L2 - 应用配置问题（次要） |
| **问题分类** | `ImagePullFailed` (主要), `CrashLoopBackOffRuntime` (次要) |
| **置信度** | 高 (97%) |
| **证据完整度** | 7/7 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体与异常分布**：

| 命名空间 | 异常Pod | 状态 | 所在节点 | 影响数量 |
| :--- | :--- | :--- | :--- |:--- |
| all (default, aiops-e2e, mcp) | `test-dns-*`, `registry-conn-*`, `dns-check-test`, `net-*`, `node-debugger-*` 等 | **ImagePullBackOff / ErrImagePull** | node1, node2 | **27个** |
| aiops-e2e | `rc-crashloop-exit-code-*` | **CrashLoopBackOff** | node2 | **1个** |

**集群整体状态**：
集群总计 91 个 Pod，其中正常运行 59 个，完成 2 个，**异常 28 个（占30.7%）**。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| **主要问题：ImagePullFailed** |
| 1 | 全局Pod状态 | `kubectl_get_by_kind_in_cluster` | `Running=59, CrashLoopBackOff=1, ImagePullBackOff=26, ErrImagePull=1, Completed=2` | 确认存在27个镜像拉取失败的Pod。 |
| 2 | 网络连接证据 | `kubectl_describe` (test-dns-1779360358, node1) | `Warning Failed ... dial tcp 199.59.150.43:443: i/o timeout` (重试41次/169分钟) | node1到Docker Hub的443端口连接超时。 |
| 3 | 网络连接证据 | `kubectl_describe` (dns-test-check, node2) | `Warning Failed ... dial tcp 154.92.16.97:443: i/o timeout` (BackOff 196次/134分钟) | node2到Docker Hub的443端口连接超时，且target IP是变化的。 |
| 4 | 网络连接证据 | `kubectl_describe` (registry-conn-test-1779371220, node2) | 同时出现 `i/o timeout` 和 `connection refused` | node2不仅连接超时，还遭到防火墙/中间设备拒绝。 |
| 5 | 镜像与密钥 | `kubectl_get_yaml` (test-dns-1779360358) | `image: busybox:1.36.1`, `imagePullSecrets: <none>` | 镜像为Docker Hub公开镜像，排除认证问题。 |
| 6 | 错误统计 | `kubectl_describe` | kubelet 重试镜像拉取 `x487 over 3h25m` | 故障持续数小时，严重影响Pod启动。 |
| **次要问题：CrashLoopBackOff** |
| 7 | 应用错误 | `kubectl_previous_logs` (rc-crashloop-exit-code-*) | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 容器因`exit code 2`持续重启。 |
| 8 | 配置错误 | `kubectl_get_yaml` (rc-crashloop-exit-code-*) | `command: ["sh", "-c"]`, `args: ["echo ... && exit 2"]` | `sh -c` 后跟随的`exit 2`命令导致容器启动后立即退出。 |
| 9 | 重启状态 | `kubectl_describe` (rc-crashloop-exit-code-*) | `Back-off restarting failed container... (x163 over 39m)` | 容器在39分钟内重启了163次。 |

### 证据关联分析

-   **主要问题（证据 #1 ↔ #2 + #3 + #4）**：27个Pod全部使用公开镜像（`busybox:1.36.1, registry:2` 等），且拉取失败的错误均为 `i/o timeout` 或 `connection refused`，精准指向**集群到公网镜像仓库的网络不可达**。根本原因与镜像本身、认证配置无关。
-   **次要问题（证据 #7 ↔ #8）**：`exit code 2` 通常表示Shell内置命令参数错误。证据 #8 的 `args` 明确将 `exit 2` 作为参数传递给 `sh -c`，导致Shell执行完后直接退出整个进程。

### 缺失证据

无。所有计划证据均已成功采集，证据链完整。

---

## 🎯 根因分析

### 因果链

```
                     ┌─────────────────────────────────────────────────────────────────┐
                     │                    根本原因（主要问题）                          │
                     │         集群节点（node1/node2）缺少公网出口或代理配置              │
                     │           无法访问 Docker Hub (registry-1.docker.io)            │
                     └─────────────────────────────────────────────────────────────────┘
                                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 27个Pod启动 → kubelet尝试拉取镜像 → TCP连接 registry-1.docker.io │
│ → 连接超时(i/o timeout) / 被拒绝(connection refused)            │
│ → kubelet重试失败 → 容器状态变为ErrImagePull → 最终ImagePullBackOff│
└─────────────────────────────────────────────────────────────────┘
                                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                直接原因（主要问题）                               │
│      node1/node2.上的kubelet无法从docker.io拉取任何镜像          │
└─────────────────────────────────────────────────────────────────┘
                                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              用户可见现象（主要问题）                             │
│     27个Pod状态为 ImagePullBackOff / ErrImagePull                │
│     涉及 default, aiops-e2e, mcp 三个命名空间                   │
└─────────────────────────────────────────────────────────────────┘

                     ┌─────────────────────────────────────────────────────────────────┐
                     │                    根本原因（次要问题）                          │
                     │      Pod启动命令 `sh -c` 后跟随了错误的 `exit 2` 参数             │
                     └─────────────────────────────────────────────────────────────────┘
                                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod启动 → kubelet执行 `sh -c 'echo ... && exit 2'` →            │
│ Shell执行完echo后执行exit 2 → 进程退出(exit code 2)             │
│ → kubelet重启容器 → 进程再次退出 → 循环，直至CrashLoopBackOff    │
└─────────────────────────────────────────────────────────────────┘
                                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              用户可见现象（次要问题）                             │
│     rc-crashloop-exit-code-* Pod 处于 CrashLoopBackOff 状态     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论 1（主要问题）**：根据证据 #1 (27个 Pod 状态异常)、#2, #3, #4 (到 Docker Hub 的 TCP 连接失败) 和 #5 (排除镜像与认证问题)，问题的根本原因是**集群节点（node1/node2）缺乏到公网镜像仓库 `registry-1.docker.io` 的网络出口或代理配置**。

-   **置信度**：高 (97%)
-   ✅ 多个节点、多个Pod、多个镜像均无法拉取，错误类型一致（网络层）。
-   ✅ 错误包括 `i/o timeout` 和 `connection refused`，表明从超时（无路由）到被拒（有防火墙）的网络问题。
-   ✅ 排除了镜像名称错误、认证错误等常见原因。

**结论 2（次要问题）**：根据证据 #7 (exit code 2), #8 (命令参数错误), #9 (持续重启) 和 #10 (previous logs)，问题的根本原因是**Pod `rc-crashloop-exit-code-*` 启动命令 `sh -c` 后附加了 `exit 2` 参数，导致容器在启动后立即退出**。

-   **置信度**：高 (95%)
-   ✅ `exit code 2` 与命令参数错误高度相关。
-   ✅ YAML文件中的 `command` 和 `args` 直接因果关系。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修复主要问题：配置集群公网出口或代理**

这是修复27个Pod的关键。

-   **方案A（推荐）**: 如果集群有HTTP/HTTPS代理，配置containerd或dockerd使用代理。
    ```bash
    # 在 node1 和 node2 节点上执行
    sudo mkdir -p /etc/systemd/system/containerd.service.d
    sudo tee /etc/systemd/system/containerd.service.d/proxy.conf <<EOF
    [Service]
    Environment="HTTP_PROXY=http://your-proxy-ip:port"
    Environment="HTTPS_PROXY=http://your-proxy-ip:port"
    Environment="NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    EOF
    sudo systemctl daemon-reload
    sudo systemctl restart containerd
    ```
    *依据*：根本原因是网络不可达，配置公网代理是标准解决方案。

-   **方案B**: 如果无法使用代理，将所需镜像推送到一个私有镜像仓库（如Harbor），然后修改所有Deployment/StatefulSet的镜像地址为该私有仓库。
    ```bash
    # 在有公网访问的机器上执行
    docker pull busybox:1.36.1
    docker tag busybox:1.36.1 <your-private-registry>/library/busybox:1.36.1
    docker push <your-private-registry>/library/busybox:1.36.1
    ```
    *依据*：绕过公网依赖，通过内网私有仓库提供镜像。

**2. [必须] 修复次要问题：修正Pod启动命令**

修复 `rc-crashloop-exit-code-*` Pod的CrashLoopBackOff问题。

-   **方案A**: 修改Deployment的spec，移除或修改`args`。
    找到对应的Deployment或Pod模板，将`args`中的参数修改为正常的启动命令，例如：
    ```yaml
    # 原 args
    args: ["echo 'hello world' && exit 2"]
    # 修改为
    args: ["echo 'hello world' && sleep 3600"]
    # 或者直接移除 args，让其执行 command 中的 sh -c 但不带退出命令
    ```
    *依据*：`exit 2` 是导致容器退出的直接原因，需要改为一个无限运行的进程。

-   **方案B（快速验证）**:
    ```bash
    # 先分析一下该 Pod 是哪个上层控制器管理的
    kubectl get pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e -o jsonpath='{.metadata.ownerReferences[0]}'
    # 假设输出为 {"apiVersion":"apps/v1","kind":"Deployment","name":"rc-crashloop-exit-code","uid":"..."}
    # 直接修改 Deployment
    kubectl edit deployment rc-crashloop-exit-code -n aiops-e2e
    ```
    *依据*：直接修改控制器定义，删除或修改`args`中的`exit 2`。

### 后续优化

1.  **镜像管理**：在所有工作负载中使用私有仓库镜像地址，避免直接依赖公网仓库，提高集群稳定性和部署速度。
2.  **应用配置校验**：在CI/CD流水线中对Pod的`command`和`args`进行基础校验，避免类似`exit 2`的静默错误进入集群。
3.  **网络监控**：配置对关键外部服务（如镜像仓库）的网络连通性监控，提前发现网络故障。

---

## ⚠️ 注意事项

-   修复主要问题后，所有处于 `ImagePullBackOff` / `ErrImagePull` 状态的Pod会自动尝试重新拉取镜像，无需手动删除。
-   修改 `containerd` 代理配置会重启容器运行时，可能导致节点上运行的Pod短暂中断。建议在业务低峰期操作。
-   次要问题的 `rc-crashloop-exit-code-*` Pod是测试Pod，修正命令后即可正常运行。

---

## 📊 性能统计

├─ 总耗时: 2.9m
├─ 问题定位: 55.4s (31%) ✅
├─ 证据链采集: 52.5s (30%) ✅
├─ 根因分析: 32.2s (18%) ✅
├─ 汇总总结: 36.2s (21%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 26 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-crashloop-runtime
- **参考 Runbook**: pod-imagepull-failed, pod-crashloop-runtime
- **工具调用**: 26 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
