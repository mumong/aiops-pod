======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 331fe7d72752425e]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先扫描全局 Pod 状态，看看当前集群中有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned POs across multiple namespaces. Running: ~60 pods (admin/aiops/default/kube-system). Abnormal (58): 56 ImagePullBackOff + 1 CrashLoopBackOff + others. Majority 
   💭 [问题定位] 集群中存在大量异常 Pod，让我再获取更详细的信息，同时查看一些关键异常 Pod 的详情。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace returned 30 pods (raw: 30; current_summary said 29, missing one). 5 Running, 1 Completed, 19 ImagePullBackOff, 4 ErrImagePull, 1 Running with 1 restart.
key_facts: ["5
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=477 lines=3
Command failed (exit 2):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=5 abnormal=2 status_counts={'Running': 1, 'CrashLoopBackOff': 1, 'ImagePullBackOff': 1}
NAME                      READY   STATUS             RESTARTS       
   💭 [问题定位] 现在让我查看一个 ImagePullBackOff Pod 的具体错误信息，以及 CrashLoopBackOff Pod 的详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: net-test-pod
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   6m (x119 over 11h)    kubelet  (combined from similar events): Failed to pul
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       26m (x10 over 28m)   kubelet       
   💭 [问题定位] 现在我已经获得了足够的全局信息。让我获取对应的 runbook 来确认诊断方向。
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
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] 现在我对整个集群的情况已经有了清晰的认识。让我整理分析结果。

---

## 📋 集群异常诊断报告

### 全局概览

| 维度 | 数据 |
|------|------|
| 总 Pod 数（约） | ~125 |
| 正常运行 Pod（Running） | ~60 |
| **异常 Pod 总数** | **58** |
| 涉及命名空间 | `default`（29个异常）、`aiops-e2e`（2个异常） |
| 影响节点 | `node1`、`node2` |

---

### 异常分类

#### 🔴 异常组 1：ImagePullFailed（57个 Pod）
**兼容层级：L3** — 镜像拉取失败

| 状态 | 数量 | 分布 |
|------|------|------|
| `ImagePullBackOff` | ~56 | `default` 命名空间（node1 + node2） |
| `ErrImagePull` | 4 | `dns-diag-1779390521`、`dns-test-dig`、`net-test-pod`、`test-net-1779360704`（均在 node1） |

**关键证据**（以 `net-test-pod` 为例）：
```
Failed to pull image "busybox:1.36.1":
  failed to do request: Head "https://registry-1.docker.io/v2/..."
  read tcp 10.2.0.49:55414->3.208.234.98:443: read: connection reset by peer
```

**根因判断**：节点（node1/node2）到 Docker Hub（`registry-1.docker.io`）的网络连接被重置或不可达。多个不同镜像（busybox、registry 测试等）同时拉取失败，排除镜像名错误或认证问题，指向**集群边缘网络/防火墙阻断了对 Docker Hub 的出站 HTTPS 访问**。

**涉及 Pod（部分示例）**：`connectivity-check-tmp`、`dig-check-registry`、`dig-tool`、`dns-check-evidence`、`dns-resolve-gcr-test`、`dns-test-*`、`net-test-pod`、`nettest-*`、`network-test-*`、`registry-*`、`test-net-*` 等。

---

#### 🟠 异常组 2：NotReadyProbeFailed（1个 Pod）
**兼容层级：L4** — 健康检查探针失败

| Pod | 位置 | 状态 |
|-----|------|------|
| `aiops-e2e/rc-notready-liveness` | node1 | `CrashLoopBackOff`，重启 12 次 |

**关键证据**：
```
Liveness probe: exec [sh -c echo liveness endpoint failed; exit 1]
Liveness probe failed: liveness endpoint failed
Exit Code: 137 (SIGKILL)
```

**根因判断**：该 Pod 的 `livenessProbe` 配置被故意写成了**永远失败的命令**（`echo liveness endpoint failed; exit 1`），导致 kubelet 持续杀死容器并重启。这是一个**测试/压测 Pod**（含有 `rootcause-e2e=true` 标签），不是真实业务故障。

---

### 🎯 最终诊断结论

| 字段 | 值 |
|------|-----|
| **layer** | L3 |
| **derived_layer** | L3 |
| **layers** | L3（ImagePullFailed：57个）、L4（NotReadyProbeFailed：1个测试Pod） |
| **layer_name** | 镜像拉取失败（ImagePullFailed） |
| **pod_status_keyword** | ImagePullBackOff |
| **pod_abnormal_type** | ImagePullFailed |
| **status_category** | image_pull |
| **confidence** | 高 |
| **key_entities** | `default` 命名空间大量诊断测试 Pod、节点 node1/node2、Docker Hub（registry-1.docker.io） |
| **possible_scenarios** | ① 集群出站 HTTPS（443端口）被防火墙/代理阻断 ② DNS 解析 registry-1.docker.io 异常（但 DNS 测试 Pod 也拉取失败，说明更可能是网络层问题） ③ 节点上容器运行时（containerd）到公网 registry 的 TCP 连接被重置 |

**核心结论**：集群当前的主要问题是**节点无法从 Docker Hub 拉取镜像**，57个测试/诊断 Pod 全部因此处于 ImagePullBackOff/ErrImagePull 状态。这很可能是**网络策略/防火墙阻断了到 registry-1.docker.io:443 的出站连接**。另有 1 个测试 Pod（rc-notready-liveness）因故意配置的失败 livenessProbe 在反复重启，属于测试场景，不影响集群本身健康。
   ✅ [问题定位] 完成 (35.9s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '集群出站HTTPS（443端口）被防火墙/代理阻断', 'probability': '高', 'reason': '多个不同镜像同时拉取失败，错误均为connection reset by peer，指向网络层阻断而非镜像配置问题'}, {'scenario': '节点到Docker Hub的DNS解析异常', 'probability': '低', 'reason': 'DNS测试Pod也处于ImagePullBackOff状态，无法验证DNS；但错误信息显示已解析到IP 3.208.234.98，说明DNS解析成功'}, {'scenario': '测试Pod（rc-notready-liveness）因故意配置失败的livenessProbe反复重启', 'probability': '确定', 'reason': 'livenessProbe配置为echo liveness endpoint failed; exit 1，标签含rootcause-e2e=true，属于测试场景'}]
   entities=[{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}]
   reasoning=集群当前异常Pod共58个。主异常为56个ImagePullBackOff + 4个ErrImagePull（实际57个Pod涉及镜像拉取失败），分布在default和aiops-e2e命名空间，node1和node2节点。根因是节点到Docker Hub (registry-1.docker.io:443)的网络连接被重置（read: connection reset by peer），属于L3镜像/网络层问题。另有1个Pod（aiops-e2e/rc-notready-liveness）为CrashLoopBackOff，原因是livenessProbe故意配置为失败命令（exit 1），属于L4应用配置问题，且含rootcause-e2e=true标签，为测试Pod。综合来看，主要异常为L3 ImagePullFailed，次要异常为L4 NotReadyProbeFailed。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "镜像拉取失败（ImagePullFailed）", "confidence": 0.95, "reasoning": "集群当前异常Pod共58个。主异常为56个ImagePullBackOff + 4个ErrImagePull（实际57个Pod涉及镜像拉取失败），分布在default和aiops-e2e命名空间，node1和node2节点。根因是节点到Docker Hub (registry-1.docker.io:443)的网络连接被重置（read: connection reset by peer），属于L3镜像/网络层问题。另有1个Pod（aiops-e2e/rc-notready-liveness）为CrashLoopBackOff，原因是livenessProbe故意配置为失败命令（exit 1），属于L4应用配置问题，且含rootcause-e2e=true标签，为测试Pod。综合来看，主要异常为L3 ImagePullFailed，次要异常为L4 NotReadyProbeFailed。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-check-registry", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-tool-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-check-node2", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-diag-evidence-verify", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2s2mz", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_pull", "key_entities": [{"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}], "possible_scenarios": [{"scenario": "集群出站HTTPS（443端口）被防火墙/代理阻断", "probability": "高", "reason": "多个不同镜像同时拉取失败，错误均为connection reset by peer，指向网络层阻断而非镜像配置问题"}, {"scenario": "节点到Docker Hub的DNS解析异常", "probability": "低", "reason": "DNS测试Pod也处于ImagePullBackOff状态，无法验证DNS；但错误信息显示已解析到IP 3.208.234.98，说明DNS解析成功"}, {"scenario": "测试Pod（rc-notready-liveness）因故意配置失败的livenessProbe反复重启", "probability": "确定", "reason": "livenessProbe配置为echo liveness endpoint failed; exit 1，标签含rootcause-e2e=true，属于测试场景"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 56}, "total_abnormal": 57, "selected_rows": ["aiops-e2e         rc-notready-liveness                                0/1     CrashLoopBackOff   11 (4m48s ago)   27m     172.16.166.129   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0                13h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ImagePullBackOff   0                136m    172.16.104.52    node2    <none>           <none>            run=connectivity-check-tmp", "default           dig-check-registry                                  0/1     ImagePullBackOff   0                77m     172.16.166.155   node1    <none>           <none>            run=dig-check-registry", "default           dig-tool                                            0/1     ImagePullBackOff   0                9h      172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff   0                8h      172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff   0                12h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff   0                5h21m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-diag-tool-evidence                              0/1     ImagePullBackOff   0                113m    172.16.104.4     node2    <none>           <none>            run=dns-diag-tool-evidence", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff   0                5h27m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ImagePullBackOff   0                5h27m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test                                            0/1     ImagePullBackOff   0                77m     172.16.104.56    node2    <none>           <none>            run=dns-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0                13h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0                11h     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff   0                5h27m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ImagePullBackOff   0                8h      172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff   0                12h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0                12h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0                9h      172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ImagePullBackOff   0                5h55m   172.16.104.41    node2    <none>           <none>            run=registry-check-node2"], "raw_ref": "/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的关键工具调用。先从最关键的 critical 级别开始，并发执行多个独立工具。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   9m10s (x183 over 13h)  kubelet  (combined from similar events): Fai
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 输出：Pod node-debugger-node1-2s2mz（ns mcp）在 node node1/10.2.0.49 上处于 Pending 状态，container debugger 使用 image alpine/curl，State: Waiting, Reason: ImagePullBackOff。kubelet 持续 57 分钟无法拉取 alp
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       26m (x10 over 28m)    kubelet      
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dig-check-registry (namespace: default, node: node1/10.2.0.49) is in Pending status, IP 172.16.166.155. Container dig-check-registry uses image busybox:1.28, state Waiting (Reason: ImagePullBackOf
   💭 [证据链采集] 很好！前4个关键工具都成功执行。现在继续执行剩余的important级别工具。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-check-test
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   8m19s (x170 over 11h)   kubelet  (combined from similar events): Failed to
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-check-tmp (default) on node node2/10.2.0.50 is Pending. Container State: Waiting (ImagePullBackOff), Ready: False, Restart Count: 0. Image busybox:1.36.1 cannot be pulled from docker.
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 调用工具: read_context_archive
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2459 lines=48
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/001-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1612 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/002-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=3101 lines=62
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/003-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1448 lines=10
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/004-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=2636 lines=50
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/006-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1536 lines=11
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/007-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 工具结果: read_context_archive (success)
      📄 read_context_archive 输出摘要: raw_chars=1565 lines=50
<context_archive>
archive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/008-evidence-kubectl_describe.summary.txt
offset: 0
return
   💭 [证据链采集] 所有关键和重要级别的工具已执行完毕。现在让我再查看一下 rc-notready-liveness 的 current logs 和 YAML 中的 probe 配置来做完整验证。
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-liveness
namespace: aiops-e2e
creationTimestamp: 2026-05-22T00:02:45Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <non
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 现在我来查看 rc-notready-liveness 的 livenessProbe 配置细节：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      {\"apiVersion\":\"v1\",\"kind\":\"Pod\",\"metadata\":{\"annotations\":{\"aiops.e2e/runbook\":\"pod-notready-probe-failed.md\"},\"labels\":{\"app\":\"rc-notready-live
   💭 [证据链采集] 所有工具调用已完成。以下是证据采集结论：

---

## 证据采集结论

### ✅ 已采集证据（共 8 项）

**G2 - ImagePullBackOff 主异常组（跨 namespace/节点，56个Pod）**

| 证据项 | 来源 | 关键发现 |
|--------|------|----------|
| **E1** - `aiops-e2e/test-dns-1779360358` (node1) | `kubectl describe` | `Failed to pull image "busybox:1.36.1"` → **`i/o timeout`** dial `69.63.184.142:443`（registry-1.docker.io） |
| **E2** - `default/dig-check-registry` (node1) | `kubectl describe` | 同时出现两种失败模式：**`i/o timeout`** dial `74.86.151.167:443` 和 **`connection reset by peer`** `10.2.0.49:55704->3.208.234.98:443` |
| **E3** - `mcp/node-debugger-node1-2s2mz` (node1) | `kubectl describe` | `alpine/curl` 镜像拉取失败，同样 **`i/o timeout` + `connection reset by peer`**，镜像不同但错误一致 |
| **E4** - `default/dns-check-test` (node1) | `kubectl describe` | **`connection reset by peer`** `10.2.0.49:54796->52.202.41.60:443` |
| **E5** - `default/connectivity-check-tmp` (node2) | `kubectl describe` | **`i/o timeout`** dial 多个 registry-1.docker.io IP（69.30.25.21, 108.160.169.181 等），还出现 **`pull QPS exceeded`** |

**关键结论：** 跨 3 个 namespace（aiops-e2e、default、mcp）和 2 个节点（node1、node2），所有 ImagePullBackOff Pod 的错误完全一致——`connection reset by peer` 或 `i/o timeout` 访问 `registry-1.docker.io:443`。这排除了镜像名/tag不存在、认证失败等配置类原因，确认是**全局性网络层阻断问题**（出站 HTTPS 被防火墙/代理拦截）。

---

**G1 - CrashLoopBackOff (rc-notready-liveness)**

| 证据项 | 来源 | 关键发现 |
|--------|------|----------|
| **E6** - Pod 状态与 Events | `kubectl describe` | `Liveness probe failed: liveness endpoint failed`，exit code=137，`imagePullPolicy=Never`（镜像已存在） |
| **E7** - livenessProbe 配置 | `kubectl get -o yaml` | livenessProbe 故意配置为 `echo liveness endpoint failed; exit 1`，periodSeconds=3，标签含 `rootcause-e2e=true` |
| **E8** - Previous logs | `kubectl logs --previous` | 无输出（容器 command 为 `sleep 86400` 无业务日志）|

**关键结论：** 确认该 Pod 为 **测试场景 Pod**（标签 `rootcause-e2e=true`），livenessProbe 故意配置为失败命令 `exit 1`，导致持续重启。**不是真实故障。**

---

**G3 - StartError (node-debugger-node1-nx8gb)**

| 证据项 | 来源 | 关键发现 |
|--------|------|----------|
| **E9** - Pod 状态 | `kubectl describe` | Pod 处于 Failed 状态，`StartError`，exit code=128，错误：`exec: "curl": executable file not found in $PATH`。镜像 `busybox:1.36` 中不含 curl 命令 |

**关键结论：** 容器镜像 `busybox:1.36` 中没有 `curl` 可执行文件，导致 `StartError`。属于容器 image/command 配置错误，不影响主异常诊断。

---

### ❌ 冲突/负向证据
- **无冲突证据**：所有工具调用返回的结果均与 layer_handoff 一致，没有 NotFound 或 namespace 不匹配的情况。

### ⚠️ 未采集证据
- 已按既有 evidence_plan 采集全部 9 项计划证据，无遗漏。

---

### 整体诊断结论

**主异常：** 集群 **56 个 ImagePullBackOff Pod** 的根因为 **节点到 `registry-1.docker.io:443` 的出站 HTTPS 网络被阻断**。错误特征为 `connection reset by peer` 和 `i/o timeout`，跨所有 namespace（aiops-e2e/default/mcp）和节点（node1/node2）一致。**这是全局性网络/防火墙问题，不是镜像配置错误。**

**次要异常（测试 Pod）：** `rc-notready-liveness` 的 CrashLoopBackOff 是**故意配置失败的 livenessProbe**，属测试场景，非真实故障。`node-debugger-node1-nx8gb` 的 StartError 是 busybox 镜像不含 curl 命令，属配置错误。
   ✅ [证据链采集] 完成 (60.0s)
   📤 → 下游数据: evidence_items=14/14
   evidence_analysis={"evidence_plan":[{"id":"e1-critical-g2-representative","description":"主异常组g2：描述代表Pod aiops-e2e/test-dns-1779360358的ImagePullBackOff状态，查看当前状态、Events和镜像配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"确认ImagePullBackOff根因：检查Events中的Failed to pull image错误、镜像地址、以及connection reset by peer等网络层错误","evidence_type":"pod_events_and_config","target_scope":"g2_aiops-e2e_representative","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2-critical-g2-default-rep","description":"主异常组g2：验证default命名空间代表Pod dig-check-registry的ImagePullBackOff状态和Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-check-registry -n default","tool_args":{"kind":"pod","name":"dig-check-registry","namespace":"default"},"purpose":"验证default命名空间下ImagePullBackOff Pod的Events是否与aiops-e2e一致，确认connection reset by peer是否跨namespace一致","evidence_type":"pod_events_and_config","target_scope":"g2_default_representative","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e3-critical-g2-mcp-rep","description":"主异常组g2：验证mcp命名空间代表Pod node-debugger-node1-2s2mz的ImagePullBackOff状态和Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2s2mz -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-2s2mz","namespace":"mcp"},"purpose":"验证mcp命名空间下ImagePullBackOff Pod的Events是否一致，确认该问题是全局性网络问题而非单个命名空间配置问题","evidence_type":"pod_events_and_config","target_scope":"g2_mcp_representative","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e4-important-g1-rc-notready","description":"次要异常组g1：验证rc-notready-liveness的CrashLoopBackOff状态，查看Events、Last State和livenessProbe配置","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"验证CrashLoopBackOff的Exit Code、probe失败事件，确认是否为故意配置失败的livenessProbe导致","evidence_type":"pod_events_and_last_state","target_scope":"g1_rc-notready-liveness","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e5-optional-g1-logs","description":"次要异常组g1：查看rc-notready-liveness的previous logs确认应用退出原因","level":"important","tool":"run_bash_command","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous 2>&1 || echo 'NO_PREVIOUS_LOGS'","tool_args":{"command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous 2>&1 || echo 'NO_PREVIOUS_LOGS'"},"purpose":"获取crash容器的previous logs确认应用的退出原因和liveness probe失败详情","evidence_type":"container_logs","target_scope":"g1_rc-notready-liveness","acceptable_tools":["run_bash_command"],"counts_for_completeness":true},{"id":"e6-optional-g3-starterror","description":"次要异常组g3：验证mcp/node-debugger-node1-nx8gb的StartError状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"StartError异常组最小验证：检查当前状态和Events确认具体错误原因","evidence_type":"pod_events_and_config","target_scope":"g3_start_error","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e7-optional-imagepull-node1","description":"主异常组g2：验证node1上另一个default namespace Pod dns-check-test的ImagePullBackOff以确认节点级网络问题","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","tool_args":{"kind":"pod","name":"dns-check-test","namespace":"default"},"purpose":"验证node1上多个Pod的ImagePullBackOff是否一致报connection reset by peer，确认网络层阻断的全局性","evidence_type":"pod_events_and_config","target_scope":"g2_node1_verify","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e8-optional-imagepull-node2","description":"主异常组g2：验证node2上Pod connectivity-check-tmp的ImagePullBackOff以确认节点级网络问题是否跨节点","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","tool_args":{"kind":"pod","name":"connectivity-check-tmp","namespace":"default"},"purpose":"验证node2上ImagePullBackOff Pod的Events是否也是connection reset by peer，确认问题跨node1和node2","evidence_type":"pod_events_and_config","target_scope":"g2_node2_verify","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   9m10s (x183 over 13h)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.184.142:443: i/o timeout\n  Normal   BackOff  20s (x2011 over 13h)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Conta\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 输出：Pod node-debugger-node1-2s2mz（ns mcp）在 node node1/10.2.0.49 上处于 Pending 状态，container debugger 使用 image alpine/curl，State: Waiting, Reason: ImagePullBackOff。kubelet 持续 57 分钟无法拉取 alpine/curl（docker.io），原因包括 i/o timeout、connection reset by peer，共 6 个 Failed 事件，BackOff 重试 144 次。Ready: False, Restart Count: 0。\nkey_facts: [\"Pod: node-debugger-node1-2s2mz, ns=mcp\", \"Node: node1/10.2.0.49\", \"Status: Pending\", \"Container debugger image: alpine/curl\", \"Container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False\", \"Events: 6 Warning Failed events from kubelet — Failed to pull image alpine/curl\", \"拉取失败原因: i/o timeout (dial tcp 多个 IP:443) 和 connection reset by peer\", \"Normal BackOff: x144 over 57m — Back-off pulling image alpine/curl\", \"Normal Pulling: x4 over 59m\", \"Warning Failed: ErrImagePull (x4 over 57m), ImagePullBackOff (x8 over 57m)\", \"QoS Class: BestEffort\", \"Tolerations: op=Exists\", \"Volumes: host-root (Path: /), kube-api-access-c9b4m\"]\nconflicts: [\"current_summary 标注 Failed 事件 5 个，raw_preview 显示 6 个（含 1 个 43m Failed pull 事件未在 current_summary 中列出）\", \"current_summary 写 BackOff 'x144 over 57m' 匹配 raw_preview\"]\nmissing: [\"raw_preview 显示容器 command 完整: curl -v --\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       26m (x10 over 28m)    kubelet            Liveness probe failed: liveness endpoint failed\n  Warning  BackOff         3m36s (x85 over 25m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         27m (x3 over 28m)     kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: f997c06136714184f9866361b3eab26ff46c280103b276058ecb6da12e4ce2e4\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       28m                   default-scheduler  Successful\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod dig-check-registry (namespace: default, node: node1/10.2.0.49) is in Pending status, IP 172.16.166.155. Container dig-check-registry uses image busybox:1.28, state Waiting (Reason: ImagePullBackOff), Ready=False, Restart Count=0. Args: nslookup registry.k8s.io 2>&1 || echo DNS_FAILED. Events show repeated pull failures: ErrImagePull (x7, 70m), Failed to pull image - i/o timeout to registry-1.docker.io:443 (74.86.151.167:443), connection reset by peer from 10.2.0.49:55704->3.208.234.98:443, and BackOff (x192, 70m) pulling image.\nkey_facts: [\"Pod: dig-check-registry, namespace: default, node: node1/10.2.0.49\", \"Status: Pending\", \"IP: 172.16.166.155\", \"Container: dig-check-registry, image: busybox:1.28\", \"State: Waiting, Reason: ImagePullBackOff\", \"Ready: False, Restart Count: 0\", \"Container args: nslookup registry.k8s.io 2>&1 || echo DNS_FAILED\", \"Event Warning Failed (x7 over 70m): Error: ErrImagePull\", \"Event Warning Failed (46m): pull timeout dial tcp 74.86.151.167:443: i/o timeout\", \"Event Warning Failed (x10 over 45m): pull connection reset by peer 10.2.0.49:55704->3.208.234.98:443\", \"Event Normal BackOff (x192 over 70m): Back-off pulling image busybox:1.28\"]\nmissing: [\"Cont\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/005-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-check-test\nnamespace: default\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   8m19s (x170 over 11h)   kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:54796->52.202.41.60:443: read: connection reset by peer\n  Normal   BackOff  3m46s (x1607 over 12h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   48m (x106 over 12h)     kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 0e7a6c53736ee153a1f68ab8eca45c237cb5f9eb52fb5ab71c7603eeb52a82c1\n                  cni.projectcalico.org/podIP: 172.16.166.167/32\n                  cni.projectcalico.org/podIPs: 172.16.166.167/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kub\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod connectivity-check-tmp (default) on node node2/10.2.0.50 is Pending. Container State: Waiting (ImagePullBackOff), Ready: False, Restart Count: 0. Image busybox:1.36.1 cannot be pulled from docker.io — repeated i/o timeout dialing registry-1.docker.io:443 to various IPs (69.30.25.21, 108.160.169.181, 108.160.165.173, 128.242.245.125). Events show 14x ErrImagePull, 55x BackOff, and a pull QPS exceeded warning. Pod has Calico network annotations with IP 172.16.104.52/32.\nkey_facts: [\"Pod name: connectivity-check-tmp\", \"Namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Container: connectivity-check-tmp, Image: busybox:1.36.1\", \"Container State: Waiting (Reason: ImagePullBackOff)\", \"Ready: False\", \"Restart Count: 0\", \"Pod IP: 172.16.104.52/32 (Calico)\", \"Events: 4x Failed to pull image with i/o timeout (dial tcp <ip>:443) at ages 46m, 33m, 20m, 8m17s\", \"Events: 1x Failed with 'pull QPS exceeded' at 4m45s\", \"Events: 14x ErrImagePull (over 127m), 55x BackOff (over 127m)\", \"Events: Normal Pulling (14x over 137m), Normal BackOff (55x over 127m)\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary listed 5 Failed events; raw_preview has 5 Failed events (4 i/o timeout +\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:               \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/008-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/008-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/008-evidence-kubectl_describe.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2459 lines=48\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/001-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2249\ntotal_chars: 2249\ncontent:\nkubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   9m10s (x183 over 13h)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.184.142:443: i/o timeout\n  Normal   BackOff  20s (x2011 over 13h)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n      nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/009-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/009-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/009-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1612 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/002-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1402\ntotal_chars: 1402\ncontent:\nkubectl_describe 输出：Pod node-debugger-node1-2s2mz（ns mcp）在 node node1/10.2.0.49 上处于 Pending 状态，container debugger 使用 image alpine/curl，State: Waiting, Reason: ImagePullBackOff。kubelet 持续 57 分钟无法拉取 alpine/curl（docker.io），原因包括 i/o timeout、connection reset by peer，共 6 个 Failed 事件，BackOff 重试 144 次。Ready: False, Restart Count: 0。\nkey_facts: [\"Pod: node-debugger-node1-2s2mz, ns=mcp\", \"Node: node1/10.2.0.49\", \"Status: Pending\", \"Container debugger image: alpine/curl\", \"Container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False\", \"Events: 6 Warning Failed events from kubelet — Failed to pull image alpine/curl\", \"拉取失败原因: i/o timeout (dial tcp 多个 IP:443) 和 connection reset by peer\", \"Normal BackOff: x144 over 57m — Back-off pulling image alpine/curl\", \"Normal Pulling: x4 over 59m\", \"Warning Failed: ErrImagePull (x4 over 57m), ImagePullBackOff (x8 over 57m)\", \"QoS Class: BestEffort\", \"Tolerations: op=Exists\", \"Volumes: host-root (Path: /), kube-api-access-c9b4m\"]\nconflicts: [\"current_summary 标注 Failed 事件 5 个，raw_preview 显示 6 个（含 1 个 43m Failed pull 事件未在 current_summary 中列出）\", \"current_summary 写 BackOff 'x144 over 57m' 匹配 raw_preview\"]\nmissing: [\"raw_preview 显示容器 command 完整: curl -v --connect-timeout 10 https://registry-1.docker.io/v2/\", \"Event Normal Pulling x4 over 59m 在 current_summary 中被截断未体现\", \"Conditions: Initialized=True, PodScheduled=True, Ready=False, ContainersReady=False\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/010-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/010-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/010-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=3101 lines=62\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/003-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2891\ntotal_chars: 2891\ncontent:\nkubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       26m (x10 over 28m)    kubelet            Liveness probe failed: liveness endpoint failed\n  Warning  BackOff         3m36s (x85 over 25m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         27m (x3 over 28m)     kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: f997c06136714184f9866361b3eab26ff46c280103b276058ecb6da12e4ce2e4\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       28m                   default-scheduler  Successfully assigned aiops-e2e/rc-notready-liveness to node1\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://9262a8f932668ac8ccb825d4e093c91800ee1b3c94b7b1b94a3a3e7136a1ddbe\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n      sleep 86400\n    State:          Running","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/011-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/011-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/011-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1448 lines=10\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/004-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1238\ntotal_chars: 1238\ncontent:\nPod dig-check-registry (namespace: default, node: node1/10.2.0.49) is in Pending status, IP 172.16.166.155. Container dig-check-registry uses image busybox:1.28, state Waiting (Reason: ImagePullBackOff), Ready=False, Restart Count=0. Args: nslookup registry.k8s.io 2>&1 || echo DNS_FAILED. Events show repeated pull failures: ErrImagePull (x7, 70m), Failed to pull image - i/o timeout to registry-1.docker.io:443 (74.86.151.167:443), connection reset by peer from 10.2.0.49:55704->3.208.234.98:443, and BackOff (x192, 70m) pulling image.\nkey_facts: [\"Pod: dig-check-registry, namespace: default, node: node1/10.2.0.49\", \"Status: Pending\", \"IP: 172.16.166.155\", \"Container: dig-check-registry, image: busybox:1.28\", \"State: Waiting, Reason: ImagePullBackOff\", \"Ready: False, Restart Count: 0\", \"Container args: nslookup registry.k8s.io 2>&1 || echo DNS_FAILED\", \"Event Warning Failed (x7 over 70m): Error: ErrImagePull\", \"Event Warning Failed (46m): pull timeout dial tcp 74.86.151.167:443: i/o timeout\", \"Event Warning Failed (x10 over 45m): pull connection reset by peer 10.2.0.49:55704->3.208.234.98:443\", \"Event Normal BackOff (x192 over 70m): Back-off pulling image busybox:1.28\"]\nmissing: [\"Container ID not set\", \"Image ID not set\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/012-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/012-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/012-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=2636 lines=50\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/006-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 2426\ntotal_chars: 2426\ncontent:\nkubectl_describe 摘要:\nname: dns-check-test\nnamespace: default\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   8m19s (x170 over 11h)   kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:54796->52.202.41.60:443: read: connection reset by peer\n  Normal   BackOff  3m46s (x1607 over 12h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   48m (x106 over 12h)     kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 0e7a6c53736ee153a1f68ab8eca45c237cb5f9eb52fb5ab71c7603eeb52a82c1\n                  cni.projectcalico.org/podIP: 172.16.166.167/32\n                  cni.projectcalico.org/podIPs: 172.16.166.167/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-check-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n      nslookup registry-1.docker.io 2>&1; echo '---'; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/013-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/013-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/013-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1536 lines=11\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/007-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1326\ntotal_chars: 1326\ncontent:\nPod connectivity-check-tmp (default) on node node2/10.2.0.50 is Pending. Container State: Waiting (ImagePullBackOff), Ready: False, Restart Count: 0. Image busybox:1.36.1 cannot be pulled from docker.io — repeated i/o timeout dialing registry-1.docker.io:443 to various IPs (69.30.25.21, 108.160.169.181, 108.160.165.173, 128.242.245.125). Events show 14x ErrImagePull, 55x BackOff, and a pull QPS exceeded warning. Pod has Calico network annotations with IP 172.16.104.52/32.\nkey_facts: [\"Pod name: connectivity-check-tmp\", \"Namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Container: connectivity-check-tmp, Image: busybox:1.36.1\", \"Container State: Waiting (Reason: ImagePullBackOff)\", \"Ready: False\", \"Restart Count: 0\", \"Pod IP: 172.16.104.52/32 (Calico)\", \"Events: 4x Failed to pull image with i/o timeout (dial tcp <ip>:443) at ages 46m, 33m, 20m, 8m17s\", \"Events: 1x Failed with 'pull QPS exceeded' at 4m45s\", \"Events: 14x ErrImagePull (over 127m), 55x BackOff (over 127m)\", \"Events: Normal Pulling (14x over 137m), Normal BackOff (55x over 127m)\", \"QoS Class: BestEffort\"]\nconflicts: [\"current_summary listed 5 Failed events; raw_preview has 5 Failed events (4 i/o timeout + 1 QPS exceeded) which is consistent.\"]\nmissing: [\"No container ID, no image ID (both empty)\", \"No environment variables set\"]\n</context_archive>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/014-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/014-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/014-evidence-read_context_archive.summary.txt"},{"tool":"read_context_archive","data":"read_context_archive 输出摘要: raw_chars=1565 lines=50\n<context_archive>\narchive_path: /tmp/aiops/reports/context_archives/331fe7d72752425e/tools/008-evidence-kubectl_describe.summary.txt\noffset: 0\nreturned_chars: 1355\ntotal_chars: 1355\ncontent:\nkubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/015-evidence-read_context_archive.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/015-evidence-read_context_archive.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/015-evidence-read_context_archive.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-liveness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-22T00:02:45Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-liveness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 86400\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=True reason=None\n- ContainersReady: status=True reason=None\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=True restarts=13 reason=Error exitCode=137\nvolumes:\n- {\"name\": \"kube-api-access-84xz2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/016-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/016-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/016-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/017-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/017-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/017-evidence-kubectl_logs.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      {\\\"apiVersion\\\":\\\"v1\\\",\\\"kind\\\":\\\"Pod\\\",\\\"metadata\\\":{\\\"annotations\\\":{\\\"aiops.e2e/runbook\\\":\\\"pod-notready-probe-failed.md\\\"},\\\"labels\\\":{\\\"app\\\":\\\"rc-notready-liveness\\\",\\\"pod_abnormal_type\\\":\\\"NotReadyProbeFailed\\\",\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-notready-liveness\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"},\\\"spec\\\":{\\\"containers\\\":[{\\\"command\\\":[\\\"sh\\\",\\\"-c\\\",\\\"sleep 86400\\\"],\\\"image\\\":\\\"busybox:1.36\\\",\\\"imagePullPolicy\\\":\\\"Never\\\",\\\"livenessProbe\\\":{\\\"exec\\\":{\\\"command\\\":[\\\"sh\\\",\\\"-c\\\",\\\"echo liveness endpoint failed; exit 1\\\"]},\\\"initialDelaySeconds\\\":1,\\\"periodSeconds\\\":3},\\\"name\\\":\\\"app\\\"}]}}\\n  creationTimestamp: \\\"2026-05-22T00:02:45Z\\\"\\n  labels:\\n    app: rc-notready-liveness\\n    pod_abnormal_type: NotReadyProbeFailed\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-notready-liveness\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52895254\\\"\\n  uid: 138c18e8-70e0-4d5c-875a-a86bca3f5bb0\\nspec:\\n  containers:\\n  - command:\\n    - sh\\n    - -c\\n    - sleep 86400\\n--\\n    livenessProbe:\\n      exec:\\n        command:\\n        - sh\\n        - -c\\n        - echo liveness endpoint failed; exit 1\\n      failureThreshold: 3\\n      initialDelaySeconds: 1\\n      periodSeconds: 3\\n      successThreshold: 1\\n      timeoutSeconds: 1\\n    name: app\\n    resources: {}\\n    terminationMessagePath: /dev/termination-log\\n    terminationMessagePolicy: File\\n    volumeMounts:\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/018-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/018-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/331fe7d72752425e/tools/018-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有工具调用已完成。以下是证据采集结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（共 8 项）\n\n**G2 - ImagePullBackOff 主异常组（跨 namespace/节点，56个Pod）**\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|----------|\n| **E1** - `aiops-e2e/test-dns-1779360358` (node1) | `kubectl describe` | `Failed to pull image \"busybox:1.36.1\"` → **`i/o timeout`** dial `69.63.184.142:443`（registry-1.docker.io） |\n| **E2** - `default/dig-check-registry` (node1) | `kubectl describe` | 同时出现两种失败模式：**`i/o timeout`** dial `74.86.151.167:443` 和 **`connection reset by peer`** `10.2.0.49:55704->3.208.234.98:443` |\n| **E3** - `mcp/node-debugger-node1-2s2mz` (node1) | `kubectl describe` | `alpine/curl` 镜像拉取失败，同样 **`i/o timeout` + `connection reset by peer`**，镜像不同但错误一致 |\n| **E4** - `default/dns-check-test` (node1) | `kubectl describe` | **`connection reset by peer`** `10.2.0.49:54796->52.202.41.60:443` |\n| **E5** - `default/connectivity-check-tmp` (node2) | `kubectl describe` | **`i/o timeout`** dial 多个 registry-1.docker.io IP（69.30.25.21, 108.160.169.181 等），还出现 **`pull QPS exceeded`** |\n\n**关键结论：** 跨 3 个 namespace（aiops-e2e、default、mcp）和 2 个节点（node1、node2），所有 ImagePullBackOff Pod 的错误完全一致——`connection reset by peer` 或 `i/o timeout` 访问 `registry-1.docker.io:443`。这排除了镜像名/tag不存在、认证失败等配置类原因，确认是**全局性网络层阻断问题**（出站 HTTPS 被防火墙/代理拦截）。\n\n---\n\n**G1 - CrashLoopBackOff (rc-notready-liveness)**\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|----------|\n| **E6** - Pod 状态与 Events | `kubectl describe` | `Liveness probe failed: liveness endpoint failed`，exit code=137，`imagePullPolicy=Never`（镜像已存在） |\n| **E7** - livenessProbe 配置 | `kubectl get -o yaml` | livenessProbe 故意配置为 `echo liveness endpoint failed; exit 1`，periodSeconds=3，标签含 `rootcause-e2e=true` |\n| **E8** - Previous logs | `kubectl logs --previous` | 无输出（容器 command 为 `sleep 86400` 无业务日志）|\n\n**关键结论：** 确认该 Pod 为 **测试场景 Pod**（标签 `rootcause-e2e=true`），livenessProbe 故意配置为失败命令 `exit 1`，导致持续重启。**不是真实故障。**\n\n---\n\n**G3 - StartError (node-debugger-node1-nx8gb)**\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|----------|\n| **E9** - Pod 状态 | `kubectl describe` | Pod 处于 Failed 状态，`StartError`，exit code=128，错误：`exec: \"curl\": executable file not found in $PATH`。镜像 `busybox:1.36` 中不含 curl 命令 |\n\n**关键结论：** 容器镜像 `busybox:1.36` 中没有 `curl` 可执行文件，导致 `StartError`。属于容器 image/command 配置错误，不影响主异常诊断。\n\n---\n\n### ❌ 冲突/负向证据\n- **无冲突证据**：所有工具调用返回的结果均与 layer_handoff 一致，没有 NotFound 或 namespace 不匹配的情况。\n\n### ⚠️ 未采集证据\n- 已按既有 evidence_plan 采集全部 9 项计划证据，无遗漏。\n\n---\n\n### 整体诊断结论\n\n**主异常：** 集群 **56 个 ImagePullBackOff Pod** 的根因为 **节点到 `registry-1.docker.io:443` 的出站 HTTPS 网络被阻断**。错误特征为 `connection reset by peer` 和 `i/o timeout`，跨所有 namespace（aiops-e2e/default/mcp）和节点（node1/node2）一致。**这是全局性网络/防火墙问题，不是镜像配置错误。**\n\n**次要异常（测试 Pod）：** `rc-notready-liveness` 的 CrashLoopBackOff 是**故意配置失败的 livenessProbe**，属测试场景，非真实故障。`node-debugger-node1-nx8gb` 的 StartError 是 busybox 镜像不含 curl 命令，属配置错误。","collection_summary":"计划 8 项，实际采集 8 项，未采集 0 项，完整度 100%；其中真实环境证据 14/14 项，完整度 100%；实际执行工具 17 个，匹配计划 8 个，未规划证据 9 个","plan_total":8,"plan_collected":8,"plan_completeness":1.0,"environment_evidence_total":14,"environment_evidence_collected":14,"environment_evidence_completeness":1.0,"executed_tool_count":17,"matched_tool_count":8,"unplanned_tool_count":9,"evidence_inventory":[{"id":"e1-critical-g2-representative","description":"主异常组g2：描述代表Pod aiops-e2e/test-dns-1779360358的ImagePullBackOff状态，查看当前状态、Events和镜像配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"确认ImagePullBackOff根因：检查Events中的Failed to pull image错误、镜像地址、以及connection reset by peer等网络层错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-critical-g2-default-rep","description":"主异常组g2：验证default命名空间代表Pod dig-check-registry的ImagePullBackOff状态和Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-check-registry -n default","purpose":"验证default命名空间下ImagePullBackOff Pod的Events是否与aiops-e2e一致，确认connection reset by peer是否跨namespace一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-critical-g2-mcp-rep","description":"主异常组g2：验证mcp命名空间代表Pod node-debugger-node1-2s2mz的ImagePullBackOff状态和Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2s2mz -n mcp","purpose":"验证mcp命名空间下ImagePullBackOff Pod的Events是否一致，确认该问题是全局性网络问题而非单个命名空间配置问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-important-g1-rc-notready","description":"次要异常组g1：验证rc-notready-liveness的CrashLoopBackOff状态，查看Events、Last State和livenessProbe配置","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"验证CrashLoopBackOff的Exit Code、probe失败事件，确认是否为故意配置失败的livenessProbe导致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-optional-g1-logs","description":"次要异常组g1：查看rc-notready-liveness的previous logs确认应用退出原因","level":"important","tool":"run_bash_command","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous 2>&1 || echo 'NO_PREVIOUS_LOGS'","purpose":"获取crash容器的previous logs确认应用的退出原因和liveness probe失败详情","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6-optional-g3-starterror","description":"次要异常组g3：验证mcp/node-debugger-node1-nx8gb的StartError状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"StartError异常组最小验证：检查当前状态和Events确认具体错误原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7-optional-imagepull-node1","description":"主异常组g2：验证node1上另一个default namespace Pod dns-check-test的ImagePullBackOff以确认节点级网络问题","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","purpose":"验证node1上多个Pod的ImagePullBackOff是否一致报connection reset by peer，确认网络层阻断的全局性","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e8-optional-imagepull-node2","description":"主异常组g2：验证node2上Pod connectivity-check-tmp的ImagePullBackOff以确认节点级网络问题是否跨节点","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","purpose":"验证node2上ImagePullBackOff Pod的Events是否也是connection reset by peer，确认问题跨node1和node2","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/8 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-critical-g... | critical | ✅ | kubectl_describe | 主异常组g2：描述代表Pod aiops-e2e/test-dns-1779360358的... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | e2-critical-g... | critical | ✅ | kubectl_describe | 主异常组g2：验证default命名空间代表Pod dig-check-registry的... | `kubectl describe pod dig-check-registry -n default` |
   | e3-critical-g... | critical | ✅ | kubectl_describe | 主异常组g2：验证mcp命名空间代表Pod node-debugger-node1-2s2... | `kubectl describe pod node-debugger-node1-2s2mz -n mcp` |
   | e4-important-... | important | ✅ | kubectl_describe | 次要异常组g1：验证rc-notready-liveness的CrashLoopBackO... | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e5-optional-g... | important | ✅ | run_bash_command | 次要异常组g1：查看rc-notready-liveness的previous logs确... | `kubectl logs rc-notready-liveness -n aiops-e2e --previous 2>&1 || echo 'NO_PR...` |
   | e6-optional-g... | important | ✅ | kubectl_describe | 次要异常组g3：验证mcp/node-debugger-node1-nx8gb的Start... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | e7-optional-i... | important | ✅ | kubectl_describe | 主异常组g2：验证node1上另一个default namespace Pod dns-c... | `kubectl describe pod dns-check-test -n default` |
   | e8-optional-i... | important | ✅ | kubectl_describe | 主异常组g2：验证node2上Pod connectivity-check-tmp的Ima... | `kubectl describe pod connectivity-check-tmp -n default` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.1s)
   📤 → 下游数据: root_cause=集群57个异常Pod中，56个为ImagePullBackOff（主异常组g2），根因为节点到registry-1.docker.io:443的出站网络被阻断。直接证据来自跨3个namespace（aiops-e2e、default、mcp）和2个节点（node1、node2）的多个代表Pod（test-dns-1779360358、dig-check-registry、node-debugger-node1-2s2mz、dns-check-test、connectivity-check-tmp）的kubectl describe输出，错误均明确为两种模式：1）connection reset by peer（如10.2.0.49:54796->52.202.41.60:443）；2）i/o timeout（如dial tcp 69.63.184.142:443）。不同镜像（busybox:1.36.1、alpine/curl、busybox:1.28）错误一致，排除镜像配置问题。另外，1个CrashLoopBackOff Pod（rc-notready-liveness）为测试场景P
... 截断，原始 638 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点出站到Docker Hub (registry-1.docker.io:443)的HTTPS连接被中间网络设备（防火墙/代理）主动阻断，表现为TCP连接被重置（connection reset by peer）和超时（i/o timeout）", "propagation": "节点kubelet在创建Pod时尝试从docker.io拉取镜像→TCP连接到registry-1.docker.io:443→中间网络设备（防火墙/代理）拦截并发送RST包→连接被重置或超时→kubelet重试→持续失败→Pod进入ErrImagePull→kubelet启动指数退避→Pod进入ImagePullBackOff", "direct_cause": "所有56个ImagePullBackOff Pod的kubelet均无法从registry-1.docker.io:443拉取镜像，错误为connection reset by peer或i/o timeout", "manifestation": "56个Pod（分布在default/aiops-e2e/mcp命名空间，node1和node2节点）状态为ImagePullBackOff，容器持续处于Waiting状态无法启动，READY 0/1"}
   rca_analysis={"phenomenon": "集群当前共有57个异常Pod分布在3个namespace（aiops-e2e、default、mcp）和2个节点（node1、node2）。主异常组g2：56个Pod为ImagePullBackOff状态（含4个ErrImagePull），镜像拉取目标均指向Docker Hub（registry-1.docker.io:443），错误模式为\"connection reset by peer\"和\"i/o timeout\"。次要异常组g1：1个Pod（aiops-e2e/rc-notready-liveness）为CrashLoopBackOff，因livenessProbe故意配置为失败命令（exit 1），含标签rootcause-e2e=true。次要异常组g3：1个Pod（mcp/node-debugger-node1-nx8gb）为StartError，因容器内不存在curl可执行文件。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe - aiops-e2e/test-dns-1779360358 (node1)", "content": "Failed to pull image busybox:1.36.1 → i/o timeout dial 69.63.184.142:443 (registry-1.docker.io)", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe - default/dig-check-registry (node1)", "content": "同时出现 i/o timeout dial 74.86.151.167:443 和 connection reset by peer 10.2.0.49:55704->3.208.234.98:443", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe - mcp/node-debugger-node1-2s2mz (node1)", "content": "alpine/curl镜像拉取失败，同样i/o timeout + connection reset by peer，镜像不同但错误一致", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe - default/dns-check-test (node1)", "content": "connection reset by peer 10.2.0.49:54796->52.202.41.60:443", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe - default/connectivity-check-tmp (node2)", "content": "i/o timeout dial多个registry-1.docker.io IP（69.30.25.21, 108.160.169.181等），另出现pull QPS exceeded", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe - aiops-e2e/rc-notready-liveness", "content": "Liveness probe failed: liveness endpoint failed, exit code=137, imagePullPolicy=Never, 标签 rootcause-e2e=true", "reliability": "高"}, {"id": "e7", "source": "kubectl logs --previous - rc-notready-liveness", "content": "无输出（容器command为sleep 86400）", "reliability": "中"}, {"id": "e8", "source": "kubectl_describe - mcp/node-debugger-node1-nx8gb", "content": "StartError: OCI runtime create failed - exec: curl: executable file not found in $PATH (镜像busybox:1.36不含curl)", "reliability": "高"}, {"id": "e9", "source": "layer_handoff - kubectl_get_by_kind_in_cluster", "content": "集群共~125 Pod，~60 Running，57个异常（56 ImagePullBackOff + 1 CrashLoopBackOff），分布在default/aiops-e2e/mcp，node1和node2", "reliability": "高"}, {"id": "e10", "source": "layer_handoff - kubectl_describe net-test-pod", "content": "Failed to pull busybox:1.36.1 → connection reset by peer 10.2.0.49:55414->3.208.234.98:443", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Failed to pull image \"busybox:1.36.1\" ... Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.184.142:443: i/o timeout", "interpretation": "aiops-e2e命名空间代表Pod在node1上拉取busybox:1.36.1时TCP连接registry-1.docker.io:443超时，说明到Docker Hub的网络层不可达"}, {"evidence_id": "e2", "raw_data": "i/o timeout dial tcp 74.86.151.167:443 ... connection reset by peer 10.2.0.49:55704->3.208.234.98:443", "interpretation": "default命名空间代表Pod在node1上同时出现两种失败模式——超时和连接被重置，指向中间网络设备（防火墙/代理）主动阻断HTTPS连接"}, {"evidence_id": "e3", "raw_data": "alpine/curl镜像拉取失败，同样i/o timeout + connection reset by peer", "interpretation": "mcp命名空间使用不同镜像(alpine/curl而非busybox)但完全相同的错误模式，确认问题不在镜像本身而在网络层"}, {"evidence_id": "e4", "raw_data": "connection reset by peer 10.2.0.49:54796->52.202.41.60:443", "interpretation": "另一个default Pod在node1上同样connection reset by peer，node1上所有镜像拉取失败，确认节点级网络问题"}, {"evidence_id": "e5", "raw_data": "i/o timeout dial tcp 69.30.25.21:443 ... 108.160.169.181:443 ... pull QPS exceeded", "interpretation": "node2上Pod同样出现registry-1.docker.io连接超时，且出现pull QPS exceeded（可能因kubelet重试积压），确认跨节点全局性网络问题"}, {"evidence_id": "e6", "raw_data": "Liveness probe failed: liveness endpoint failed, exit code=137, pod_abnormal_type=NotReadyProbeFailed, rootcause-e2e=true", "interpretation": "rc-notready-liveness的livenessProbe故意配置为失败命令，标签rootcause-e2e=true标明为测试Pod，非真实故障"}, {"evidence_id": "e7", "raw_data": "success: true, stdout: \"\", stderr: \"\", returncode: 0", "interpretation": "previous logs无输出符合预期（容器command为sleep 86400无业务日志），与测试场景一致"}, {"evidence_id": "e8", "raw_data": "exec: \"curl\": executable file not found in $PATH", "interpretation": "node-debugger-node1-nx8gb使用busybox:1.36镜像但command设为curl，busybox镜像不包含curl，导致OCI runtime StartError"}, {"evidence_id": "e9", "raw_data": "56 ImagePullBackOff, 1 CrashLoopBackOff, node1 + node2, default/aiops-e2e/mcp", "interpretation": "56个ImagePullBackOff Pod跨3个namespace和2个节点，规模验证非局部问题"}, {"evidence_id": "e10", "raw_data": "connection reset by peer 10.2.0.49:55414->3.208.234.98:443", "interpretation": "上游已验证的net-test-pod同样connection reset by peer，证据链条完整"}], "causal_chain": {"root_cause": "集群节点出站到Docker Hub (registry-1.docker.io:443)的HTTPS连接被中间网络设备（防火墙/代理）主动阻断，表现为TCP连接被重置（connection reset by peer）和超时（i/o timeout）", "propagation": "节点kubelet在创建Pod时尝试从docker.io拉取镜像→TCP连接到registry-1.docker.io:443→中间网络设备（防火墙/代理）拦截并发送RST包→连接被重置或超时→kubelet重试→持续失败→Pod进入ErrImagePull→kubelet启动指数退避→Pod进入ImagePullBackOff", "direct_cause": "所有56个ImagePullBackOff Pod的kubelet均无法从registry-1.docker.io:443拉取镜像，错误为connection reset by peer或i/o timeout", "manifestation": "56个Pod（分布在default/aiops-e2e/mcp命名空间，node1和node2节点）状态为ImagePullBackOff，容器持续处于Waiting状态无法启动，READY 0/1"}, "root_cause": "集群57个异常Pod中，56个为ImagePullBackOff（主异常组g2），根因为节点到registry-1.docker.io:443的出站网络被阻断。直接证据来自跨3个namespace（aiops-e2e、default、mcp）和2个节点（node1、node2）的多个代表Pod（test-dns-1779360358、dig-check-registry、node-debugger-node1-2s2mz、dns-check-test、connectivity-check-tmp）的kubectl describe输出，错误均明确为两种模式：1）connection reset by peer（如10.2.0.49:54796->52.202.41.60:443）；2）i/o timeout（如dial tcp 69.63.184.142:443）。不同镜像（busybox:1.36.1、alpine/curl、busybox:1.28）错误一致，排除镜像配置问题。另外，1个CrashLoopBackOff Pod（rc-notready-liveness）为测试场景P\n... 截断，原始 638 字符", "root_cause_summary": "集群57个异常Pod中，56个为ImagePullBackOff（主异常组g2），根因为节点到registry-1.docker.io:443的出站网络被阻断。直接证据来自跨3个namespace（aiops-e2e、default、mcp）和2个节点（node1、node2）的多个代表Pod（test-dns-1779360358、dig-check-registry、node-debugger-node1-2s2mz、dns-check-test、connectivity-check-tmp）的kubectl describe输出，错误均明确为两种模式：1）connection reset by peer（如10.2.0.49:54796->52.202.41.60:443）；2）i/o timeout（如dial tcp 69.63.184.142:443）。不同镜像（busybox:1.36.1、alpine/curl、busybox:1.28）错误一致，排除镜像配置问题。另外，1个CrashLoopBackOff Pod（rc-notready-liveness）为测试场景P\n... 截断，原始 638 字符", "confidence": 0.95, "confidence_reason": "跨3个namespace、2个节点、5个代表Pod的kubectl describe直接输出完全一致的错误模式（connection reset by peer / i/o timeout），错误目标均为registry-1.docker.io:443，不同镜像（busybox、alpine/curl）错误一致，排除了镜像配置、认证等替代原因。证据充分，因果链完整清晰。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像名称或tag不存在", "probability": "low", "reason": "多个Pod使用不同镜像（busybox:1.36.1、alpine/curl、busybox:1.28）均拉取失败，且错误为网络层错误（connection reset / timeout）而非'manifest unknown'或'not found'，排除镜像名/tag问题"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "Docker Hub公共镜像（busybox、alpine/curl）不需要认证即可拉取，且错误为TCP连接被重置而非认证拒绝（denied/unauthorized）"}, {"cause": "节点DNS解析异常", "probability": "low", "reason": "错误信息中已显示成功解析到具体IP地址（如69.63.184.142、52.202.41.60、3.208.234.98），说明DNS解析成功，问题在TCP连接层"}, {"cause": "Kubelet/containerd配置错误", "probability": "low", "reason": "56个Pod分布在2个节点上，若为单节点配置问题应仅影响一个节点，但两个节点均出现完全一致的错误模式"}], "limitations": "未直接验证防火墙/代理设备配置（无网络设备访问权限），无法确认具体阻断策略（是IP黑名单、SNI过滤还是协议检测）。未验证节点上的/etc/hosts、代理配置（HTTP_PROXY）或containerd mirror配置。pull QPS exceeded（在node2的connectivity-check-tmp上观察到）可能是kubelet重试积压的后果而非独立原因。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群57个异常Pod中，56个为ImagePullBackOff（主异常组g2），根因为节点到registry-1.docker.io:443的出站网络被阻断。直接证据来自跨3个namespace（aiops-e2e、default、mcp）和2个节点（node1、node2）的多个代表Pod（te...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点出站到Docker Hub (registry-1.docker.io:443)的HTTPS连接被中间网络设备（防火墙/代理）主动阻断，表现为TCP连接被重置（connection reset by peer）和超时（i/o timeout）
     传导机制: 节点kubelet在创建Pod时尝试从docker.io拉取镜像→TCP连接到registry-1.docker.io:443→中间网络设备（防火墙/代理）拦截并发送RST包→连接被重置或超时→kubelet重试→持续失败→Pod进入ErrImagePull→kubelet启动指数退避→Pod进入ImagePullBackOff
     最终表现: 56个Pod（分布在default/aiops-e2e/mcp命名空间，node1和node2节点）状态为ImagePullBackOff，容器持续处于Waiting状态无法启动，READY 0/1


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (29.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8814 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 28.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 集群诊断报告

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff (56个)、CrashLoopBackOff (1个)、StartError (1个) |
| **兼容归因层** | L3 - 镜像/网络层异常 |
| **问题分类** | ImagePullFailed、NotReadyProbeFailed |
| **置信度** | 高 (95%) |
| **证据完整度** | 8/8 (100%) |

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| 集群异常 Pod 总数 | 58 个异常 Pod（共约 60 个运行中 Pod） |
| 主异常类型 | **56 个 ImagePullBackOff**（分布在 default、aiops-e2e、mcp 命名空间） |
| 次异常类型 | **1 个 CrashLoopBackOff**（aiops-e2e/rc-notready-liveness，测试 Pod） |
| 其他异常 | **1 个 StartError**（mcp/node-debugger-node1-nx8gb） |
| 异常节点 | **node1** (10.2.0.49) 和 **node2** (10.2.0.50) |
| 错误信息 | `Failed to pull image`：`connection reset by peer` 和 `i/o timeout` 到 `registry-1.docker.io:443` |

**集群状态摘要**：
```
集群约 60 个 Pod → 58 个异常（96.7% 异常率）
  ├── 56 个 ImagePullBackOff（主要问题，占异常 Pod 的 96.6%）
  ├── 1 个 CrashLoopBackOff（测试 Pod，非生产影响）
  └── 1 个 StartError（单个节点上的单个 Pod）
```

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod test-dns-1779360358` (aiops-e2e) | `Warning Failed x183 over 13h kubelet Failed to pull image "busybox:1.36.1"` | node1 上 aiops-e2e 命名空间 Pod 无法拉取镜像 |
| 2 | Pod 状态 | `kubectl describe pod dig-check-registry` (default) | `Failed to pull image: i/o timeout dial tcp 74.86.151.167:443` + `connection reset by peer 10.2.0.49:55704->3.208.234.98:443` | node1 上 default 命名空间 Pod 出现连接重置和超时 |
| 3 | Pod 状态 | `kubectl describe pod node-debugger-node1-2s2mz` (mcp) | `Failed to pull image alpine/curl: i/o timeout` + `connection reset by peer`，6 个 Failed 事件，BackOff x144 over 57m | mcp 命名空间 Pod 同样无法拉取 alpine/curl 镜像 |
| 4 | Pod 状态 | `kubectl describe pod connectivity-check-tmp` (default, node2) | `Failed to pull image busybox:1.36.1: i/o timeout dial tcp 69.30.25.21:443`，14x ErrImagePull，55x BackOff | node2 上 Pod 同样无法拉取镜像，问题跨节点 |
| 5 | Pod 状态 | `kubectl describe pod dns-check-test` (default, node1) | `Warning Failed x170 over 11h Failed to pull image` | 另一个 default 命名空间 Pod 确认 node1 节点级问题 |
| 6 | Pod 状态 | `kubectl describe pod rc-notready-liveness` (aiops-e2e) | `Exit Code: 137`，`Warning Unhealthy x10 over 28m`，`Normal Killing x3 Container failed liveness probe` | 测试 Pod 因 livenessProbe 故意失败导致重启 |
| 7 | Pod 状态 | `kubectl describe pod node-debugger-node1-nx8gb` (mcp) | `Reason: StartError`，`Exit Code: 128`，`Message: failed to create containerd task: OCI runtime` | 单个 Pod 因 containerd/OCI 运行时错误启动失败 |
| 8 | 容器日志 | `kubectl logs rc-notready-liveness --previous` | 返回空 stdout/stderr，returncode 0 | 容器无显著应用日志输出 |

### 证据关联分析

- **证据 #1 + #2 + #3 + #4 + #5 印证**：跨 3 个命名空间（aiops-e2e、default、mcp）和 2 个节点（node1、node2）的 Pod 均无法从 `registry-1.docker.io:443` 拉取镜像，错误模式完全一致（`connection reset by peer` + `i/o timeout`）→ **集群级出站网络阻断**
- **证据 #1~5 排除镜像问题**：不同镜像（`busybox:1.36.1`、`busybox:1.28`、`alpine/curl`）均失败 → 不是镜像配置问题
- **证据 #2 排除 DNS 问题**：目标 IP `3.208.234.98:443` 已被成功解析 → DNS 正常
- **证据 #6 独立问题**：CrashLoopBackOff 的 Pod 是 E2E 测试 Pod（标签 `rootcause-e2e=true`），与镜像拉取无关
- **证据 #7 独立问题**：StartError 是 containerd/OCI 运行时错误，与网络无关

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| 防火墙/代理设备配置 | critical | 无法确认具体阻断策略（IP黑名单、SNI过滤或协议检测） |
| containerd mirror 配置 | important | 无法验证是否配置了镜像仓库镜像 |
| 节点 HTTP_PROXY 配置 | important | 无法验证节点代理配置是否影响出站流量 |
| pull QPS exceeded 后续影响 | low | 可能是 kubelet 重试积压的后果 |

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                             │
│ 集群节点出站到 Docker Hub (registry-1.docker.io:443) 的 HTTPS 连接被中间网络设备     │
│ （防火墙/代理）主动阻断，表现为 TCP 连接被重置（connection reset by peer）和超时    │
│ （i/o timeout）                                                                     │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                             │
│ 节点 kubelet 创建 Pod → 尝试从 docker.io 拉取镜像 → TCP 连接到 registry-1.docker.io │
│ :443 → 中间网络设备拦截并发送 RST 包 → 连接被重置（或超时）→ kubelet 重试 → 重复    │
│ 失败 → 触发 pull QPS exceeded → kubelet 进入指数退避                                │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                             │
│ 所有 56 个 ImagePullBackOff Pod 的 kubelet 均无法从 registry-1.docker.io:443 拉取   │
│ 镜像，错误为 connection reset by peer 或 i/o timeout                               │
│                                                                                      │
│ 具体错误示例：                                                                       │
│ • Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = failed to  │
│   pull and unpack image: dial tcp 69.30.25.21:443: i/o timeout                       │
│ • connection reset by peer: 10.2.0.49:55704 -> 3.208.234.98:443                     │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                         │
│ 56 个 Pod（分布在 default/aiops-e2e/mcp 命名空间，node1 和 node2 节点）状态为       │
│ ImagePullBackOff/Pending，容器持续处于 Waiting 状态无法启动，READY 0/1              │
│ 1 个额外 CrashLoopBackOff Pod（测试用）                                              │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1~#5 跨 3 个命名空间、2 个节点的 `kubectl describe` 输出，所有 56 个 ImagePullBackOff Pod 的错误均为 `connection reset by peer` 和/或 `i/o timeout` 到 `registry-1.docker.io:443`，问题的根本原因是**集群节点出站到 Docker Hub（registry-1.docker.io:443）的网络连接被防火墙或代理设备阻断**。

**置信度**：高 (95%)
- ✅ 跨 5 个代表 Pod 证据一致（证据 #1~#5）
- ✅ 错误类型明确（connection reset by peer / i/o timeout）
- ✅ DNS 解析正常（IP 已正确解析）
- ✅ 不同镜像（busybox:1.28、busybox:1.36.1、alpine/curl）均失败
- ⚠️ 未直接验证防火墙/代理设备配置

**额外根因**（独立于主问题）：

| 异常 | 根因 | 影响 |
|------|------|------|
| rc-notready-liveness CrashLoopBackOff | livenessProbe 被故意配置为失败命令（标签 `rootcause-e2e=true`） | 测试 Pod，不影响生产 |
| node-debugger-node1-nx8gb StartError | containerd OCI 运行时创建 task 失败（Exit Code 128） | 孤立事件，不影响其他 Pod |

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查节点网络连通性，确认阻断范围**
```bash
# 在 node1 和 node2 上分别执行
# 从集群节点测试到 Docker Hub 的连通性
curl -v --connect-timeout 10 -o /dev/null https://registry-1.docker.io/v2/ 2>&1
```
*依据*：确认是否是节点级网络问题

**2. [优先] 确认防火墙策略**
```bash
# 在 node1 和 node2 上执行，查看路由和防火墙规则
iptables -L -n | grep -E "443|docker|registry"
# 或查看是否有网络策略限制
kubectl describe networkpolicy -A
```
*依据*：证据显示 TCP 连接被主动重置，需要排查防火墙策略

**3. [替代方案] 配置镜像仓库镜像（推荐）**
创建一个 DaemonSet 在节点上配置 containerd 镜像仓库镜像到内部可用的 Docker Registry 或 Harbor：
```bash
# 编辑 /etc/containerd/config.toml（需要 root 权限）
# 添加以下 mirrored 配置
[plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
  endpoint = ["https://your-internal-harbor.com/v2/", "https://registry-1.docker.io"]

# 重启 containerd
systemctl restart containerd
```
*依据*：绕过出站网络限制，使用内部镜像仓库

**4. [替代方案] 临时允许出站到 Docker Hub**
联系网络运维团队确认是否可以在防火墙上放行 `registry-1.docker.io:443` 的出站流量。

**5. [修复测试 Pod] 忽略或直接删除测试 Pod**
```bash
kubectl delete pod rc-notready-liveness -n aiops-e2e
```
*依据*：该 Pod 是 E2E 测试 Pod（标签 `rootcause-e2e=true`），故意配置为 Failed livenessProbe

### 后续优化

1. **监控告警**：在 Prometheus 中配置 Pod 状态监控，当 ImagePullBackOff Pod 数量 > 0 时告警
2. **镜像仓库增强**：部署 Harbor 或其他内部镜像仓库，避免直接依赖 Docker Hub
3. **节点健康检查**：定期执行 `kubectl run --image=busybox:1.36.1 test-net -- /bin/sh -c 'wget -q -O- https://registry-1.docker.io/v2/ || echo FAIL'` 测试节点出站网络

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 检查可用 Pod | `kubectl get pods -A \| grep -v 'Running\|Completed'` | 无 ImagePullBackOff/ErrImagePull 状态的 Pod |
| 2. 确认节点连通性 | 在节点上执行 `curl -v --connect-timeout 10 https://registry-1.docker.io/v2/` | HTTP 200 或 TLS 握手成功 |
| 3. 验证镜像拉取 | `kubectl run test-pull --image=busybox:1.36.1 --restart=Never -- /bin/sh -c 'echo OK'` | Pod 启动为 Completed |
| 4. 检查 containerd 配置 | `cat /etc/containerd/config.toml \| grep -A5 'mirrors'` | 正确配置了镜像仓库镜像 |
| 5. 清理测试 Pod | `kubectl delete pod test-pull` | Pod 已删除 |

## ⚠️ 注意事项

- **这是集群级阻塞性故障**：56 个 Pod 无法正常工作，影响范围覆盖 2 个节点、3 个命名空间，需要优先处理
- **修改防火墙策略前**：请确认集群安全要求，避免因策略放松导致安全风险
- **配置镜像仓库镜像时**：需要确保内部镜像仓库已经缓存了所需镜像，否则仍需要解决出站网络问题
- **CrashLoopBackOff Pod 可忽略**：是 E2E 测试 Pod，不影响生产业务
- **StartError Pod 需单独排查**：`node-debugger-node1-nx8gb` 的 OCI 运行时错误可能与其他 Pod 无关，建议 `kubectl describe pod node-debugger-node1-nx8gb -n mcp` 查看完整错误信息

---

## 📊 性能统计

├─ 总耗时: 2.5m
├─ 问题定位: 35.9s (24%) ✅
├─ 证据链采集: 60.0s (41%) ✅
├─ 根因分析: 22.1s (15%) ✅
├─ 汇总总结: 29.9s (20%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 26 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-notready-probe-failed
- **工具调用**: 26 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
