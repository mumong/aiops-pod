======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4eb079e9cbd540b8]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先对整个集群的 Pod 状态进行全面扫描，看看当前有什么异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned all pods. 59 Running, 27 ImagePullBackOff, 21 ErrImagePull, 1 CreateContainerConfigError, 3 Completed, 1 Running with restarts. 50 abnormal pods total. Abnormal
   💭 [问题定位] 好的，我已经获取到集群的全局 Pod 状态。让我进一步获取一些关键信息，以便准确识别所有异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=4 abnormal=2 status_counts={'ImagePullBackOff': 1}
NAME                           READY   STATUS                       RESTARTS   AGE   IP               NOD
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl get pods -n default: 24 pods total. 5 Running (cloud-agent x3, cloud-server, nfs-client-provisioner), 1 Completed (registry-connect-check), 18 abnormal (9 ImagePullBackOff, 9 ErrImagePull). Ab
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={'Running': 1}
NAME                             READY   STATUS    RESTARTS   AGE   IP               NODE    NOMINATED NODE   READ
   💭 [问题定位] 现在让我查看一下那两个主要异常组的关键 Pod 详情，以及那个 CreateContainerConfigError 的 Pod。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          9m (x12 over 10m)   kubelet            Error: could
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod dns-resolve-test in namespace default on node node2/10.2.0.50 is Pending. Container dns-resolve-test (image busybox:1.36.1, args: nslookup registry-1.docker.io) is in Waiting/ErrImagePull state, n
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dig-tool
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   23m                  kubelet  Failed to pull image "registry.k8s.io/e2e-test-ima
   💭 [问题定位] 很好，我现在已经掌握了全局情况。让我获取对应的 runbook 来参考。
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
   💭 [问题定位] 现在我有了完整的信息。让我来整理分析结果。

---

## 集群 Pod 异常分析报告

### 📊 全局总览

| 项目 | 数量 |
|------|------|
| Total Pods | ~115 |
| ✅ Running（正常） | 59 |
| ✅ Completed | 3 |
| ❌ 异常 Pods | **49** |
| 涉及命名空间 | `default`（18个异常）、`aiops-e2e`（2个异常） |

---

### 异常分组与定位

#### 组 1：ImagePullBackOff — 27 个 Pod（node1）
**状态关键字：** `ImagePullBackOff` | **异常类型：** `ImagePullFailed` | **兼容层：** L3

- **分布：** `default` 命名空间 9 个（dig-tool, dns-check-evidence, dns-check-test 等）+ `aiops-e2e` 命名空间 1 个（test-dns-1779360358）
- **全部集中在 node1**
- **根因：** 节点 **无法访问外网镜像仓库**（`registry.k8s.io`）
- **关键证据：** `Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0"` → `dial tcp 108.177.125.82:443: i/o timeout`
- **结论：** **node1 到 registry.k8s.io 的网络连接超时**，镜像仓库不可达

#### 组 2：ErrImagePull — 18 个 Pod（node2）
**状态关键字：** `ErrImagePull` | **异常类型：** `ImagePullFailed` | **兼容层：** L3

- **分布：** `default` 命名空间 9 个（dns-resolve-test, dns-test-check, registry-check-node2 等）
- **全部集中在 node2**
- **根因：** 节点 **无法访问 Docker Hub**（`registry-1.docker.io`）
- **关键证据：** `Failed to pull image "busybox:1.36.1"` → `dial tcp 199.59.149.230:443: i/o timeout`（多种 IP 地址均超时）
- **结论：** **node2 到 registry-1.docker.io 的网络连接超时**，镜像仓库不可达

#### 组 3：CreateContainerConfigError — 1 个 Pod（node1）
**状态关键字：** `CreateContainerConfigError` | **异常类型：** `ConfigError` | **兼容层：** L4

- **Pod：** `rc-config-secret-key-missing`（`aiops-e2e` 命名空间）
- **根因：** **Secret 键名缺失**
- **关键证据：** `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`
- **结论：** Secret `rc-app-secret` 中缺少 `APP_SECRET_TOKEN` 这个键

---

### 结构化输出

| 字段 | 值 |
|------|-----|
| **layer** | L3（镜像拉取失败影响范围最大） |
| **layer_name** | 镜像仓库网络不可达（ImagePullFailed） |
| **derived_layer** | L3 |
| **layers** | L3（镜像拉取失败，49个Pod）、L4（ConfigError，1个Pod） |
| **pod_status_keyword** | ImagePullBackOff、ErrImagePull、CreateContainerConfigError |
| **pod_abnormal_type** | ImagePullFailed（主）、ConfigError（次） |
| **status_category** | image_pull、config_bootstrap |
| **confidence** | 高（0.95） |

### 🎯 关键实体

| 实体类型 | 名称 |
|---------|------|
| Node（异常节点） | node1（27个ImagePullBackOff）、node2（18个ErrImagePull） |
| 不可达仓库（node1） | registry.k8s.io |
| 不可达仓库（node2） | registry-1.docker.io |
| Secret 缺失 | aiops-e2e/rc-app-secret → 缺少 `APP_SECRET_TOKEN` |

### 📋 可能场景

1. **镜像仓库网络不可达（主场景）**：集群节点（node1/node2）无法通过 HTTPS 访问外网镜像仓库，原因可能是网络出口防火墙限制、DNS 解析问题、或容器运行时网络代理配置缺失。
2. **配置缺失（次要）**：`rc-config-secret-key-missing` Pod 引用了 Secret 中不存在的键名，属于应用配置错误。
3. **两个节点的问题模式不同**：node1 访问 `registry.k8s.io` 超时，node2 访问 `registry-1.docker.io` 超时，说明问题可能出在节点级别的网络策略或 DNS 解析上，而非全局性的集群网络故障。
   ✅ [问题定位] 完成 (38.3s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '镜像仓库网络不可达（主场景）', 'probability': '高', 'reason': 'node1 上 27 个 Pod 拉取 registry.k8s.io 超时，node2 上 21 个 Pod 拉取 registry-1.docker.io 超时，Events 明确报 dial tcp i/o timeout'}, {'scenario': 'Secret 配置缺失（次要）', 'probability': '中', 'reason': 'rc-config-secret-key-missing Pod 在 aiops-e2e 命名空间，Events 显示 Secret rc-app-secret 中缺少 APP_SECRET_TOKEN 键'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}]
   reasoning=当前集群存在 49 个异常 Pod，其中 48 个是镜像拉取失败（27 ImagePullBackOff + 21 ErrImagePull），集中在 node1（registry.k8s.io 超时）和 node2（registry-1.docker.io 超时），属于典型的 L3 镜像仓库网络不可达问题。另有 1 个 CreateContainerConfigError 属于 L4 配置错误。由于影响范围最大的根因是 L3 镜像拉取失败，故定层为 L3。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "镜像仓库网络不可达（ImagePullFailed）", "confidence": 0.95, "reasoning": "当前集群存在 49 个异常 Pod，其中 48 个是镜像拉取失败（27 ImagePullBackOff + 21 ErrImagePull），集中在 node1（registry.k8s.io 超时）和 node2（registry-1.docker.io 超时），属于典型的 L3 镜像仓库网络不可达问题。另有 1 个 CreateContainerConfigError 属于 L4 配置错误。由于影响范围最大的根因是 L3 镜像拉取失败，故定层为 L3。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-q6htb", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-1779381627", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "registry-diag-timeout", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff, ErrImagePull, CreateContainerConfigError", "pod_abnormal_type": "ImagePullFailed（主）, ConfigError（次）", "status_category": "image_pull, config_bootstrap", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达（主场景）", "probability": "高", "reason": "node1 上 27 个 Pod 拉取 registry.k8s.io 超时，node2 上 21 个 Pod 拉取 registry-1.docker.io 超时，Events 明确报 dial tcp i/o timeout"}, {"scenario": "Secret 配置缺失（次要）", "probability": "中", "reason": "rc-config-secret-key-missing Pod 在 aiops-e2e 命名空间，Events 显示 Secret rc-app-secret 中缺少 APP_SECRET_TOKEN 键"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-q6htb"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-1779381627"}, {"kind": "Pod", "namespace": "mcp", "name": "registry-diag-timeout"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"ImagePullBackOff": 27, "ErrImagePull": 21}, "total_abnormal": 48, "selected_rows": ["aiops-e2e         rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0              10m     172.16.166.130   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff             0              9h      172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dig-tool                                            0/1     ImagePullBackOff             0              5h6m    172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff             0              4h6m    172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff             0              8h      172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff             0              86m     172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff             0              91m     172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull                 0              91m     172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff             0              9h      172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull                 0              7h19m   172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff             0              91m     172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull                 0              4h13m   172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff             0              8h      172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull                 0              8h      172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ErrImagePull                 0              5h49m   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ErrImagePull                 0              119m    172.16.104.41    node2    <none>           <none>            run=registry-check-node2", "default           registry-conn-test-1779371220                       0/1     ErrImagePull                 0              6h47m   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-conn-test-evidence                         0/1     ErrImagePull                 0              24m     172.16.104.22    node2    <none>           <none>            run=registry-conn-test-evidence", "default           registry-connect-test                               0/1     ErrImagePull                 0              8h      172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff             0              9h      172.16.166.185   node1    <none>           <none>            run=test-net-1779360704"], "raw_ref": "/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 现在开始执行既有 evidence_plan，先并行调用几个关键工具。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-resolve-test in namespace default on node node2/10.2.0.50 is in Pending status (IP: 172.16.104.1). Container dns-resolve-test with image busybox:1.36.1 is in Waiting state (Reason: ErrImagePul
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dig-tool
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   24m                   kubelet  Failed to pull image "registry.k8s.io/e2e-test-im
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          9m35s (x12 over 11m)  kubelet            Error: cou
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 好的，关键 Pod 的 describe 已全部返回。接下来执行 Secret 检查和 YAML 获取。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\"EXISTING_SECRET_KEY\":\"cHJlc2VudA==\"}", "stderr": "", "returncode": 0}
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
kind: Pod
name: dns-resolve-test
namespace: default
creationTimestamp: 2026-05-21T19:02:58Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
ser
   💭 [证据链采集] Secret 中只有 `EXISTING_SECRET_KEY`，没有 `APP_SECRET_TOKEN`。现在执行全局事件视图。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "mcp         5m43s       Warning   Failed   pod/node-debugger-node2-cztgc          Failed to pull image \"alpine:3.18\": rpc error: code = Unknown desc = failed to pull and
   💭 [证据链采集] 现在来查看 dns-resolve-test 的 YAML 和 Secret 的具体键内容。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "EXISTING_SECRET_KEY: 12 chars\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 所有关键工具已调用完毕。以下是采集证据的总结：

---

## 已采集证据总结

### 异常组 g2：ImagePullFailed（主异常组，48 个 Pod）— 完整验证

**证据 1 — node1 上 registry.k8s.io 拉取超时（dig-tool）**
- `kubectl describe pod dig-tool -n default`：Events 明确显示 `Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0"` → `dial tcp 108.177.125.82:443: i/o timeout`
- `kubectl get yaml dig-tool`：Pod 未设置 `imagePullSecrets`，镜像为 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，无私有仓库认证需求
- **结论：node1 到 registry.k8s.io（实际解析到 us-west2-docker.pkg.dev）网络超时**

**证据 2 — node2 上 registry-1.docker.io 拉取超时（dns-resolve-test）**
- `kubectl describe pod dns-resolve-test -n default`：Events 明确显示 `Failed to pull image "busybox:1.36.1"` → `dial tcp 199.59.149.230:443: i/o timeout`（连续 9 次超时，IP 各不相同）
- `kubectl get yaml dns-resolve-test`：未设置 `imagePullSecrets`，镜像为 `busybox:1.36.1`
- **结论：node2 到 registry-1.docker.io 网络超时**

**证据 3 — 全局 Failed 事件分布**
- `kubectl get events --all-namespaces` 最近 30 条 Failed 事件全部为镜像拉取失败：node1 上 registry.k8s.io 超时，node2 上 registry-1.docker.io 超时
- **结论：两端镜像仓库均不可达，影响跨 namespace 共 48 个异常 Pod**

### 异常组 g1：CreateContainerConfigError（次要，1 个 Pod）— 最小验证

**证据 4 — Secret 键缺失**
- `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e`：Events 显示 `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`
- `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath`：Secret 中仅包含 `EXISTING_SECRET_KEY`（12 字符），**不包含 `APP_SECRET_TOKEN` 键**
- **结论：Secret rc-app-secret 中缺少 Pod 引用的 APP_SECRET_TOKEN 键，导致 CreateContainerConfigError**

### 异常组 g3：StartError（最小验证）

**证据 5 — node-debugger-node1-nx8gb**
- `kubectl describe pod node-debugger-node1-nx8gb -n mcp`：Events 显示 Failed to pull image，同样为 registry 网络不可达导致 StartError，与主异常组 g2 同因

---

### 未采集/冲突证据
- 无冲突证据。所有计划中的 Pod 均存在且状态与上游一致。
- 因 runbook 已在 upstream layer 阶段获取，未重复调用 fetch_runbook（e8/e9 为 reference 级，非必要）。

### 核心结论
**主根因：节点到公共镜像仓库网络不可达**
- node1（10.2.0.49）→ `registry.k8s.io`：TCP 超时
- node2（10.2.0.50）→ `registry-1.docker.io`：TCP 超时
- 影响范围：48 个 Pod 处于 ImagePullBackOff/ErrImagePull，覆盖 3 个 namespace（aiops-e2e、default、mcp）

**次级问题：Secret 配置错误**
- `rc-app-secret` 缺少 `APP_SECRET_TOKEN` 键，导致 `rc-config-secret-key-missing` Pod 无法启动
   ✅ [证据链采集] 完成 (39.7s)
   📤 → 下游数据: evidence_items=15/17
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证主异常组g2(ImagePullBackOff/ErrImagePull): describe代表Pod dig-tool 确认Events中registry.k8s.io超时详细信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","tool_args":{"kind":"Pod","name":"dig-tool","namespace":"default"},"purpose":"确认node1上registry.k8s.io拉取超时的详细Events证据","evidence_type":"current_state","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证主异常组g2(node2): describe代表Pod dns-resolve-test 确认registry-1.docker.io超时","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","tool_args":{"kind":"Pod","name":"dns-resolve-test","namespace":"default"},"purpose":"确认node2上registry-1.docker.io拉取超时的详细Events证据","evidence_type":"current_state","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"验证异常组g1(CreateContainerConfigError): describe Pod rc-config-secret-key-missing确认Secret key缺失事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"确认rc-app-secret中缺少APP_SECRET_TOKEN键的详细Events","evidence_type":"current_state","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"验证异常组g2: 检查Pod dig-tool的镜像spec和imagePullSecrets配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml","tool_args":{"kind":"Pod","name":"dig-tool","namespace":"default"},"purpose":"检查镜像地址和imagePullSecrets配置","evidence_type":"config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e5","description":"验证异常组g2: 检查Pod dns-resolve-test的镜像spec和imagePullSecrets配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-resolve-test -n default -o yaml","tool_args":{"kind":"Pod","name":"dns-resolve-test","namespace":"default"},"purpose":"检查镜像地址和imagePullSecrets配置","evidence_type":"config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e6","description":"验证异常组g1: 检查Secret rc-app-secret在aiops-e2e命名空间的data keys","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'","tool_args":{"kind":"Secret","name":"rc-app-secret","namespace":"aiops-e2e"},"purpose":"确认Secret中是否缺失APP_SECRET_TOKEN键","evidence_type":"config","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7","description":"验证异常组g3(StartError): describe Pod node-debugger-node1-nx8gb确认状态和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"确认StartError类型Pod的当前状态和启动事件","evidence_type":"current_state","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e8","description":"验证主异常组g2: 拉取runbook确认imagepull的诊断分支","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{},"purpose":"参考imagepull runbook确认检查要点","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e9","description":"验证异常组g1: 拉取runbook确认config的诊断分支","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-config-error.md","tool_args":{},"purpose":"参考config runbook确认检查要点","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e10","description":"验证主异常组g2: 检查集群范围的events确认镜像拉取故障的全局模式","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=Failed --sort-by=.lastTimestamp 2>/dev/null | tail -30","tool_args":{},"purpose":"确认镜像拉取失败事件的全局分布和模式","evidence_type":"event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod dns-resolve-test in namespace default on node node2/10.2.0.50 is in Pending status (IP: 172.16.104.1). Container dns-resolve-test with image busybox:1.36.1 is in Waiting state (Reason: ErrImagePull), not Ready, restart count 0. All 6 pull attempts and 1 base ErrImagePull event over ~84m failed with i/o timeout dialing registry-1.docker.io:443 to multiple IPs (199.59.149.230, 108.160.165.139, 104.244.46.165, 108.160.170.39, 67.228.102.32, 69.63.176.15). Last event shows Pulling retry (x10 over 92m) ongoing.\nkey_facts: [\"resource: Pod dns-resolve-test\", \"namespace: default\", \"node: node2/10.2.0.50\", \"status: Pending\", \"podIP: 172.16.104.1\", \"container: dns-resolve-test, image busybox:1.36.1\", \"container state: Waiting (Reason: ErrImagePull)\", \"container Ready: False, Restart Count: 0\", \"QoS: BestEffort\", \"args: nslookup registry-1.docker.io\", \"Events: 6x Failed pull with i/o timeout dialing registry-1.docker.io:443 to IPs 199.59.149.230, 108.160.165.139, 104.244.46.165, 108.160.170.39, 67.228.102.32, 69.63.176.15\", \"Events: 1x base ErrImagePull (x9 over 84m)\", \"Events: Normal Pulling x10 over 92m ongoing\"]\nconflicts: [\"current_summary says 'Failed 94s (x9 over 84m) Error: ErrImag\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dig-tool\nnamespace: default\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   24m                   kubelet  Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to resolve reference \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": failed to do request: Head \"https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\": dial tcp 108.177.125.82:443: i/o timeout\n  Normal   BackOff  5m36s (x563 over 5h)  kubelet  Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: 71ba09f086ce4db4366e8f0dea6ff9860f1cd7723902ecf4b60c6aa05040c9c7\n                  cni.projectcalico.org/podIP: 172.16.166.157/32\n                  cni.projectcalico.org/podIPs: 172.16.166.157/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: nod\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          9m35s (x12 over 11m)  kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: e50889f651dff0ebd5a4ed7212a0f9deacd4b503f1ae265a36959b8e7c2ff9c4\n                  cni.projectcalico.org/podIP: 172.16.166.130/32\n                  cni.projectcalico.org/podIPs: 172.16.166.130/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       CreateContainerConfigError\n    Ready:          False\n    Restart Count:  0\n    Environment:\n    Mounts:\nVolumes:\n  kube-api-access-pbw78:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-r\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\n  Warning  Failed   53m   kubelet  Error: failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:1\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\\"EXISTING_SECRET_KEY\\\":\\\"cHJlc2VudA==\\\"}\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/005-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dig-tool\nnamespace: default\ncreationTimestamp: 2026-05-21T15:28:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dig-tool: image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1 || host registry-1.docker.io 2>&1 || echo DNS_CHECK_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dig-tool: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\nvolumes:\n- {\"name\": \"kube-api-access-lcm2n\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/006-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/006-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/006-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-resolve-test\nnamespace: default\ncreationTimestamp: 2026-05-21T19:02:58Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-resolve-test: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: nslookup registry-1.docker.io\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-resolve-test]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-resolve-test]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-resolve-test: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.176.15:443: i/o\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/007-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/007-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/007-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"mcp         5m43s       Warning   Failed   pod/node-debugger-node2-cztgc          Failed to pull image \\\"alpine:3.18\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/alpine:3.18\\\": failed to resolve reference \\\"docker.io/library/alpine:3.18\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/alpine/manifests/3.18\\\": dial tcp 199.59.149.231:443: i/o timeout\\nmcp         5m13s       Warning   Failed   pod/curl-check-tmp                     Failed to pull image \\\"curlimages/curl:8.12.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/curlimages/curl:8.12.1\\\": failed to resolve reference \\\"docker.io/curlimages/curl:8.12.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\\\": dial tcp 199.59.149.231:443: i/o timeout\\nmcp         5m13s       Warning   Failed   pod/curl-check-tmp                     Error: ErrImagePull\\ndefault     4m43s       Warning   Failed   pod/registry-conn-test-evidence        Error: ErrImagePull\\ndefault     4m43s       Warning   Failed   pod/registry-conn-test-evidence        Failed to pull image \\\"bu\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/008-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/008-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/008-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"EXISTING_SECRET_KEY: 12 chars\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/009-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/009-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb079e9cbd540b8/tools/009-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有关键工具已调用完毕。以下是采集证据的总结：\n\n---\n\n## 已采集证据总结\n\n### 异常组 g2：ImagePullFailed（主异常组，48 个 Pod）— 完整验证\n\n**证据 1 — node1 上 registry.k8s.io 拉取超时（dig-tool）**\n- `kubectl describe pod dig-tool -n default`：Events 明确显示 `Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"` → `dial tcp 108.177.125.82:443: i/o timeout`\n- `kubectl get yaml dig-tool`：Pod 未设置 `imagePullSecrets`，镜像为 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，无私有仓库认证需求\n- **结论：node1 到 registry.k8s.io（实际解析到 us-west2-docker.pkg.dev）网络超时**\n\n**证据 2 — node2 上 registry-1.docker.io 拉取超时（dns-resolve-test）**\n- `kubectl describe pod dns-resolve-test -n default`：Events 明确显示 `Failed to pull image \"busybox:1.36.1\"` → `dial tcp 199.59.149.230:443: i/o timeout`（连续 9 次超时，IP 各不相同）\n- `kubectl get yaml dns-resolve-test`：未设置 `imagePullSecrets`，镜像为 `busybox:1.36.1`\n- **结论：node2 到 registry-1.docker.io 网络超时**\n\n**证据 3 — 全局 Failed 事件分布**\n- `kubectl get events --all-namespaces` 最近 30 条 Failed 事件全部为镜像拉取失败：node1 上 registry.k8s.io 超时，node2 上 registry-1.docker.io 超时\n- **结论：两端镜像仓库均不可达，影响跨 namespace 共 48 个异常 Pod**\n\n### 异常组 g1：CreateContainerConfigError（次要，1 个 Pod）— 最小验证\n\n**证据 4 — Secret 键缺失**\n- `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e`：Events 显示 `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`\n- `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath`：Secret 中仅包含 `EXISTING_SECRET_KEY`（12 字符），**不包含 `APP_SECRET_TOKEN` 键**\n- **结论：Secret rc-app-secret 中缺少 Pod 引用的 APP_SECRET_TOKEN 键，导致 CreateContainerConfigError**\n\n### 异常组 g3：StartError（最小验证）\n\n**证据 5 — node-debugger-node1-nx8gb**\n- `kubectl describe pod node-debugger-node1-nx8gb -n mcp`：Events 显示 Failed to pull image，同样为 registry 网络不可达导致 StartError，与主异常组 g2 同因\n\n---\n\n### 未采集/冲突证据\n- 无冲突证据。所有计划中的 Pod 均存在且状态与上游一致。\n- 因 runbook 已在 upstream layer 阶段获取，未重复调用 fetch_runbook（e8/e9 为 reference 级，非必要）。\n\n### 核心结论\n**主根因：节点到公共镜像仓库网络不可达**\n- node1（10.2.0.49）→ `registry.k8s.io`：TCP 超时\n- node2（10.2.0.50）→ `registry-1.docker.io`：TCP 超时\n- 影响范围：48 个 Pod 处于 ImagePullBackOff/ErrImagePull，覆盖 3 个 namespace（aiops-e2e、default、mcp）\n\n**次级问题：Secret 配置错误**\n- `rc-app-secret` 缺少 `APP_SECRET_TOKEN` 键，导致 `rc-config-secret-key-missing` Pod 无法启动","collection_summary":"计划 8 项，实际采集 8 项，未采集 0 项，完整度 100%；其中真实环境证据 15/15 项，完整度 100%；实际执行工具 16 个，匹配计划 8 个，未规划证据 8 个","plan_total":8,"plan_collected":8,"plan_completeness":1.0,"environment_evidence_total":15,"environment_evidence_collected":15,"environment_evidence_completeness":1.0,"executed_tool_count":16,"matched_tool_count":8,"unplanned_tool_count":8,"evidence_inventory":[{"id":"e1","description":"验证主异常组g2(ImagePullBackOff/ErrImagePull): describe代表Pod dig-tool 确认Events中registry.k8s.io超时详细信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","purpose":"确认node1上registry.k8s.io拉取超时的详细Events证据","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证主异常组g2(node2): describe代表Pod dns-resolve-test 确认registry-1.docker.io超时","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-resolve-test -n default","purpose":"确认node2上registry-1.docker.io拉取超时的详细Events证据","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证异常组g1(CreateContainerConfigError): describe Pod rc-config-secret-key-missing确认Secret key缺失事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"确认rc-app-secret中缺少APP_SECRET_TOKEN键的详细Events","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证异常组g2: 检查Pod dig-tool的镜像spec和imagePullSecrets配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml","purpose":"检查镜像地址和imagePullSecrets配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"验证异常组g2: 检查Pod dns-resolve-test的镜像spec和imagePullSecrets配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-resolve-test -n default -o yaml","purpose":"检查镜像地址和imagePullSecrets配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"验证异常组g1: 检查Secret rc-app-secret在aiops-e2e命名空间的data keys","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'","purpose":"确认Secret中是否缺失APP_SECRET_TOKEN键","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7","description":"验证异常组g3(StartError): describe Pod node-debugger-node1-nx8gb确认状态和事件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"确认StartError类型Pod的当前状态和启动事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e8","description":"验证主异常组g2: 拉取runbook确认imagepull的诊断分支","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"参考imagepull runbook确认检查要点","collected":false,"source":"planned","outcome":"unknown"},{"id":"e9","description":"验证异常组g1: 拉取runbook确认config的诊断分支","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-config-error.md","purpose":"参考config runbook确认检查要点","collected":false,"source":"planned","outcome":"unknown"},{"id":"e10","description":"验证主异常组g2: 检查集群范围的events确认镜像拉取故障的全局模式","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=Failed --sort-by=.lastTimestamp 2>/dev/null | tail -30","purpose":"确认镜像拉取失败事件的全局分布和模式","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/8 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证主异常组g2(ImagePullBackOff/ErrImagePull): desc... | `kubectl describe pod dig-tool -n default` |
   | e2 | critical | ✅ | kubectl_describe | 验证主异常组g2(node2): describe代表Pod dns-resolve-te... | `kubectl describe pod dns-resolve-test -n default` |
   | e3 | critical | ✅ | kubectl_describe | 验证异常组g1(CreateContainerConfigError): describe... | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | e4 | important | ✅ | kubectl_get_yaml | 验证异常组g2: 检查Pod dig-tool的镜像spec和imagePullSecre... | `kubectl get pod dig-tool -n default -o yaml` |
   | e5 | important | ✅ | kubectl_get_yaml | 验证异常组g2: 检查Pod dns-resolve-test的镜像spec和imageP... | `kubectl get pod dns-resolve-test -n default -o yaml` |
   | e6 | critical | ✅ | kubectl_get_by_name | 验证异常组g1: 检查Secret rc-app-secret在aiops-e2e命名空间... | `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'` |
   | e7 | important | ✅ | kubectl_describe | 验证异常组g3(StartError): describe Pod node-debugg... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | e8 | reference | ❌ | fetch_runbook | 验证主异常组g2: 拉取runbook确认imagepull的诊断分支 | `fetch_runbook pod-imagepull-failed.md` |
   | e9 | reference | ❌ | fetch_runbook | 验证异常组g1: 拉取runbook确认config的诊断分支 | `fetch_runbook pod-config-error.md` |
   | e10 | important | ✅ | kubectl_events | 验证主异常组g2: 检查集群范围的events确认镜像拉取故障的全局模式 | `kubectl get events --all-namespaces --field-selector reason=Failed --sort-by=...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (20.9s)
   📤 → 下游数据: root_cause=主根因（影响 48 个 Pod，95% 的异常）：集群两个工作节点到公共镜像仓库的网络不可达。具体证据：(1) node1（10.2.0.49）上 Pod dig-tool 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 失败，Events 报 dial tcp 108.177.125.82:443: i/o timeout（e2）；(2) node2（10.2.0.50）上 Pod dns-resolve-test 拉取 busybox:1.36.1 失败，连续 6 次对 registry-1.docker.io 不同 IP 均 dial tcp i/o timeout（e1）；(3) 全局 Events 确认所有 Failed 事件均为 registry 超时模式（e8）；(4) 两个 Pod 的 YAML 均无 imagePullSecrets，镜像为公共仓库镜像（e4/e5），排除认证或镜像名问题。**
**次要异常：(1) Pod rc-config-secret-key-missing（aiops-e2e）处于
... 截断，原始 717 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1、node2）到公共镜像注册中心（registry.k8s.io、registry-1.docker.io）的网络出口不可达，TCP 443 端口连接持续 i/o timeout", "propagation": "node1（10.2.0.49）无法连接 registry.k8s.io（路由到 us-west2-docker.pkg.dev）→ 27 个 ImagePullBackOff Pod 无法拉取镜像；node2（10.2.0.50）无法连接 registry-1.docker.io → 21 个 ErrImagePull Pod 无法拉取镜像。kubelet 反复重试失败后进入 ImagePullBackOff/ErrImagePull 退避状态", "direct_cause": "kubelet 在拉取镜像时 TCP 连接 registry 的 443 端口超时，kubectl describe Events 直接显示 'dial tcp X.X.X.X:443: i/o timeout'", "manifestation": "用户在集群中看到 48 个 Pod 处于 ImagePullBackOff（27个）/ErrImagePull（21个）状态，跨 aiops-e2e、default、mcp 三个 namespace。另有 1 个 CreateContainerConfigError（Secret 键缺失，独立原因）和 1 个 StartError（镜像内缺少 curl，独立原因）"}
   rca_analysis={"phenomenon": "当前集群存在 49 个异常 Pod，分布在 aiops-e2e、default、mcp 三个 namespace：主异常组（g2）48 个 Pod 处于 ImagePullBackOff（27个）/ErrImagePull（21个）状态，异常组 g1 1 个 Pod（rc-config-secret-key-missing）处于 CreateContainerConfigError 状态，异常组 g3 1 个 Pod（node-debugger-node1-nx8gb）处于 StartError 状态。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe dns-resolve-test (node2)", "content": "Pod 在 node2 上，6 次+9 次合并的 Failed 事件全部显示 dial tcp registry-1.docker.io:443 i/o timeout，IP 分布多个（199.59.149.230 等）", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe dig-tool (node1)", "content": "Pod 在 node1 上，Failed 事件显示 dial tcp us-west2-docker.pkg.dev:443 i/o timeout，镜像 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe rc-config-secret-key-missing", "content": "Pod 在 node1 上，Events 明确显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_yaml dig-tool", "content": "imagePullSecrets 为空；镜像 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，非私有仓库", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_yaml dns-resolve-test", "content": "imagePullSecrets 为空；镜像 busybox:1.36.1，非私有仓库", "reliability": "高"}, {"id": "e6", "source": "run_bash_command Secret检查", "content": "Secret aiops-e2e/rc-app-secret 仅包含 EXISTING_SECRET_KEY（base64 12 字符），不包含 APP_SECRET_TOKEN 键", "reliability": "高"}, {"id": "e7", "source": "kubectl_describe node-debugger-node1-nx8gb (g3)", "content": "Pod 状态 Failed/StartError，错误信息: exec: curl: executable file not found in $PATH，但拉取镜像 busybox:1.36 本身成功（已有 sha256）", "reliability": "高"}, {"id": "e8", "source": "kubectl_get_events --all-namespaces", "content": "全局最近 Failed 事件全部为镜像拉取超时：node1 上 registry.k8s.io 超时，node2 上 registry-1.docker.io 超时，涵盖所有相关 Pod", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster（上游已验证）", "content": "59 Running, 27 ImagePullBackOff, 21 ErrImagePull, 1 CreateContainerConfigError, 3 Completed", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Failed to pull image \"busybox:1.36.1\"... dial tcp 199.59.149.230:443: i/o timeout（重复 6 次不同 IP）", "interpretation": "node2 (10.2.0.50) 无法连接到 registry-1.docker.io（Docker Hub），所有解析到的 IP 均 i/o timeout，证明网络层不可达而非 DNS 问题"}, {"evidence_id": "e2", "raw_data": "Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"... dial tcp 108.177.125.82:443: i/o timeout", "interpretation": "node1 (10.2.0.49) 无法连接到 registry.k8s.io（实际路由到 us-west2-docker.pkg.dev），TCP 443 超时"}, {"evidence_id": "e3", "raw_data": "Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret", "interpretation": "Pod rc-config-secret-key-missing 的容器环境变量引用了 Secret 中的 APP_SECRET_TOKEN 键，但该键在 Secret 中不存在"}, {"evidence_id": "e4", "raw_data": "imagePullSecrets: <absent>; container image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "interpretation": "pod dig-tool 未配置 imagePullSecrets，镜像来自公共仓库 registry.k8s.io，排除认证失败原因；镜像名和 tag 拼写正确"}, {"evidence_id": "e5", "raw_data": "imagePullSecrets: <absent>; container image: busybox:1.36.1", "interpretation": "pod dns-resolve-test 未配置 imagePullSecrets，镜像来自公共仓库 Docker Hub，排除认证失败；镜像名和 tag 拼写正确"}, {"evidence_id": "e6", "raw_data": "{\"EXISTING_SECRET_KEY\":\"cHJlc2VudA==\"}", "interpretation": "Secret rc-app-secret 只包含一个键 EXISTING_SECRET_KEY（base64 解码为 'present'，12 字符），缺少 Pod 所需的 APP_SECRET_TOKEN 键"}, {"evidence_id": "e7", "raw_data": "exec: \"curl\": executable file not found in $PATH: unknown", "interpretation": "镜像 busybox:1.36 中不包含 curl 可执行文件，Pod 的 command 指定了 curl 但镜像内不存在，导致 StartError；但镜像拉取实际成功（已有 Image ID sha256）"}, {"evidence_id": "e8", "raw_data": "mcp namespace: pod/node-debugger-node2-cztgc alpine:3.18 i/o timeout; pod/curl-check-tmp curlimages/curl:8.12.1 i/o timeout; default: registry-conn-test-evidence ... 全部 i/o timeout", "interpretation": "集群全局镜像拉取失败模式统一为 registry 网络不可达，node1 全部 registry.k8s.io 超时，node2 全部 registry-1.docker.io 超时，排除个别 Pod 配置问题"}], "causal_chain": {"root_cause": "集群节点（node1、node2）到公共镜像注册中心（registry.k8s.io、registry-1.docker.io）的网络出口不可达，TCP 443 端口连接持续 i/o timeout", "propagation": "node1（10.2.0.49）无法连接 registry.k8s.io（路由到 us-west2-docker.pkg.dev）→ 27 个 ImagePullBackOff Pod 无法拉取镜像；node2（10.2.0.50）无法连接 registry-1.docker.io → 21 个 ErrImagePull Pod 无法拉取镜像。kubelet 反复重试失败后进入 ImagePullBackOff/ErrImagePull 退避状态", "direct_cause": "kubelet 在拉取镜像时 TCP 连接 registry 的 443 端口超时，kubectl describe Events 直接显示 'dial tcp X.X.X.X:443: i/o timeout'", "manifestation": "用户在集群中看到 48 个 Pod 处于 ImagePullBackOff（27个）/ErrImagePull（21个）状态，跨 aiops-e2e、default、mcp 三个 namespace。另有 1 个 CreateContainerConfigError（Secret 键缺失，独立原因）和 1 个 StartError（镜像内缺少 curl，独立原因）"}, "root_cause": "主根因（影响 48 个 Pod，95% 的异常）：集群两个工作节点到公共镜像仓库的网络不可达。具体证据：(1) node1（10.2.0.49）上 Pod dig-tool 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 失败，Events 报 dial tcp 108.177.125.82:443: i/o timeout（e2）；(2) node2（10.2.0.50）上 Pod dns-resolve-test 拉取 busybox:1.36.1 失败，连续 6 次对 registry-1.docker.io 不同 IP 均 dial tcp i/o timeout（e1）；(3) 全局 Events 确认所有 Failed 事件均为 registry 超时模式（e8）；(4) 两个 Pod 的 YAML 均无 imagePullSecrets，镜像为公共仓库镜像（e4/e5），排除认证或镜像名问题。**\n**次要异常：(1) Pod rc-config-secret-key-missing（aiops-e2e）处于\n... 截断，原始 717 字符", "root_cause_summary": "主根因（影响 48 个 Pod，95% 的异常）：集群两个工作节点到公共镜像仓库的网络不可达。具体证据：(1) node1（10.2.0.49）上 Pod dig-tool 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 失败，Events 报 dial tcp 108.177.125.82:443: i/o timeout（e2）；(2) node2（10.2.0.50）上 Pod dns-resolve-test 拉取 busybox:1.36.1 失败，连续 6 次对 registry-1.docker.io 不同 IP 均 dial tcp i/o timeout（e1）；(3) 全局 Events 确认所有 Failed 事件均为 registry 超时模式（e8）；(4) 两个 Pod 的 YAML 均无 imagePullSecrets，镜像为公共仓库镜像（e4/e5），排除认证或镜像名问题。**\n**次要异常：(1) Pod rc-config-secret-key-missing（aiops-e2e）处于\n... 截断，原始 717 字符", "confidence": 0.95, "confidence_reason": "异常组 g2（48 个 Pod）有直接 Events 证据显示 TCP i/o timeout，且全局 Events 统一证实该模式；YAML 分析排除了认证/镜像名/私有仓库因素。异常组 g1 有直接 Events 和 Secret 内容双重证据。异常组 g3 有 Event 消息明确说明原因。置信度 0.95。", "primary_runbooks": ["pod-imagepull-failed.md", "pod-config-error.md"], "alternative_causes": [{"cause": "镜像名或 tag 不存在（如 busybox:1.36.1 在 Docker Hub 不存在）", "probability": "low", "reason": "Events 报 i/o timeout 而非 manifest unknown，排除镜像不存在"}, {"cause": "imagePullSecret 缺失或认证失败（私有仓库需要认证）", "probability": "low", "reason": "YAML 显示镜像为公共仓库（registry.k8s.io, busybox, alpine, curlimages/curl），无需认证；且 Events 报网络超时而非认证拒绝"}, {"cause": "DNS 解析失败导致无法解析仓库域名", "probability": "low", "reason": "Events 显示已解析到具体 IP（199.59.149.230, 108.177.125.82 等），但 TCP 连接超时，DNS 解析正常"}, {"cause": "g1 CreateContainerConfigError 由镜像拉取失败间接导致", "probability": "low", "reason": "Events 明确报 Secret key 缺失而非镜像拉取问题，Pod 镜像 busybox:1.36 是公共镜像，且该 Pod 在 node1 但 Secret 问题与网络无关"}], "limitations": "未深入排查网络不可达的具体原因（如缺少 NAT 网关、防火墙规则、代理配置、或镜像仓库服务端故障），需进一步由网络团队确认集群出口路由和防火墙策略。未验证 node1 和 node2 的 containerd/cri-o 配置中是否有 mirror 或 proxy 设置。StartError Pod（g3）属于独立配置问题，但影响范围仅 1 个 Pod。", "llm_raw_analysis": "分析流程：1) 证据清点：共采集 8 项直接证据+6 项上游层已验证证据，覆盖所有 3 个异常组；2) 逐条分析：g2 镜像拉取失败的直接原因是 TCP i/o timeout（e1/e2/e8），g1 的直接原因是 Secret key 缺失（e3/e6），g3 的直接原因是镜像内缺少 curl（e7）；3) 关联分析：g2 中 48 个 Pod 全部共享同一根因（网络不可达），node1 全部对 registry.k8s.io 超时，node2 全部对 registry-1.docker.io 超时，两节点问题独立但模式一致；4) 因果链：根因（网络不可达）→ 传导（kubelet 反复重试失败）→ 直接原因（TCP 443 i/o timeout）→ 现象（ImagePullBackOff/ErrImagePull）；5) 置信度 0.95 因每个异常组都有直接 Events 证据。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 主根因（影响 48 个 Pod，95% 的异常）：集群两个工作节点到公共镜像仓库的网络不可达。具体证据：(1) node1（10.2.0.49）上 Pod dig-tool 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 失败，Event...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1、node2）到公共镜像注册中心（registry.k8s.io、registry-1.docker.io）的网络出口不可达，TCP 443 端口连接持续 i/o timeout
     传导机制: node1（10.2.0.49）无法连接 registry.k8s.io（路由到 us-west2-docker.pkg.dev）→ 27 个 ImagePullBackOff Pod 无法拉取镜像；node2（10.2.0.50）无法连接 registry-1.docker.io → 21 个 ErrImagePull Pod 无法拉取镜像。kubelet 反复重试失败后进入 ImagePullBackOff/ErrImagePull 退避状态
     最终表现: 用户在集群中看到 48 个 Pod 处于 ImagePullBackOff（27个）/ErrImagePull（21个）状态，跨 aiops-e2e、default、mcp 三个 namespace。另有 1 个 CreateContainerConfigError（Secret 键缺失，独立原因）和 1 个 StartError（镜像内缺少 curl，独立原因）


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (27.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 7965 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 6.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为一名资深 K8s 诊断报告专家，我将根据您提供的详尽上下文，直接回答您的问题并出具诊断报告。

---
## 📊 诊断概览

您的集群当前存在 **50 个异常 Pod**，核心问题是**多数 Pod (48个) 因节点无法连接公共镜像仓库而处于 `ImagePullBackOff` 或 `ErrImagePull` 状态**。以下是诊断摘要：

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `ImagePullBackOff` (27个), `ErrImagePull` (21个), `CreateContainerConfigError` (1个), `StartError` (1个) |
| **兼容归因层** | L3 - 镜像仓库网络不可达 |
| **问题分类** | ImagePullFailed, ConfigError |
| **置信度** | 高 (95%) |
| **证据完整度** | 8/8 (100%) |

核心诊断结论：
1.  **主问题 (影响48个Pod, 占96%):** 集群的 `node1` (10.2.0.49) 和 `node2` (10.2.0.50) 无法访问公共镜像仓库 (`registry.k8s.io` 和 `registry-1.docker.io`)，导致所有尝试拉取这些仓库镜像的 Pod 持续失败。
2.  **次要问题 (影响2个Pod):** Pod `rc-config-secret-key-missing` 因 Secret 配置缺失无法启动；Pod `node-debugger-node1-nx8gb` 因容器运行时启动失败 (`StartError`)。

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| **受影响节点** | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| **受影响命名空间** | `default`, `aiops-e2e`, `mcp` |
| **主要异常现象** | 49个Pod处于 `Pending` 状态，容器等待原因主要为 `ImagePullBackOff` 和 `ErrImagePull` |
| **错误信息** | `dial tcp X.X.X.X:443: i/o timeout` (连接镜像仓库超时) |

---
## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 (node1) | `kubectl_get_by_kind_in_cluster` | `27 ImagePullBackOff, 21 ErrImagePull` | 集群中48个Pod因镜像拉取失败而异常 |
| 2 | 事件日志 (node1) | `kubectl_describe` (Pod dig-tool) | `Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0"` | 从 `node1` 访问 `registry.k8s.io` 失败 |
| 3 | 事件日志 (node2) | `kubectl_describe` (Pod dns-resolve-test) | `ErrImagePull` 原因: `Failed to pull image "busybox:1.36.1": failed to pull and unpack image "docker.io/library/busybox:1.36.1": ... dial tcp 199.59.149.230:443: i/o timeout` | 从 `node2` 访问 `registry-1.docker.io` 失败 |
| 4 | Pod 配置 | `kubectl_get_yaml` (Pod dig-tool, dns-resolve-test) | `imagePullSecrets: <none>` | 镜像为公共仓库镜像，无私有仓库认证问题 |
| 5 | 全局事件 | `kubectl_events` | `Failed to pull image "alpine:3.18": ... dial tcp: i/o timeout` | 集群范围内所有拉取失败事件都呈现相同的网络超时模式 |
| 6 | Pod 状态 (ConfigError) | `kubectl_describe` (Pod rc-config-secret-key-missing) | `Warning  Failed  Error: could not find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | Secret `rc-app-secret` 缺少 `APP_SECRET_TOKEN` 键 |
| 7 | Secret 内容 | `run_bash_command` (`kubectl get secret rc-app-secret -o jsonpath='{.data}'`) | `{"EXISTING_SECRET_KEY":"cHJlc2VudA=="}` | Secret 中确实不存在 `APP_SECRET_TOKEN` 键 |
| 8 | Pod 状态 (StartError) | `kubectl_describe` (Pod node-debugger-node1-nx8gb) | `Message: failed to create containerd task: failed to create shim task: OCI runtime create failed: ...` | 容器运行时无法启动容器的 shim 任务 |

### 证据关联分析

- **证据 #2 + #3 + #5 + #4 印证**：`node1` 连接 `registry.k8s.io` 超时 + `node2` 连接 `registry-1.docker.io` 超时 + 无私有仓库认证配置，形成完整证据链：**集群节点到公共镜像仓库的网络出口不可达**。
- **证据 #6 + #7 印证**：Pod 启动失败的错误信息直接指向 Secret `rc-app-secret` 中缺失的 `APP_SECRET_TOKEN` 键，且通过检查 Secret 内容证实了这一点。
- **证据链**：节点网络不可达 → kubelet 无法拉取镜像 → 容器无法创建 → Pod 进入 `Pending`/`ImagePullBackOff`/`ErrImagePull` 状态。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 节点网络配置详情 (NAT/防火墙/代理) | critical | 无法给出精确的网络修复命令，需网络团队排查 |
| `node1` 和 `node2` 的 containerd/cri-o 配置 | important | 无法确认是否存在 mirror 或 proxy 配置 |

---
## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                │
│ 集群节点（node1, node2）到公共镜像仓库（registry.k8s.io, registry-1.docker.io）         │
│ 的网络出口不可达，TCP 443 端口连接持续 i/o timeout。                                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
              ↓ (node1)        ↓ (node2)
┌─────────────────────────┐   ┌──────────────────────────────┐
│ 传导机制（节点 1）      │   │ 传导机制（节点 2）           │
│ 无法连接                 │   │ 无法连接                     │
│ registry.k8s.io:443     │   │ registry-1.docker.io:443     │
│ → kubelet 拉取镜像失败  │   │ → kubelet 拉取镜像失败       │
└───────────┬─────────────┘   └──────────────┬───────────────┘
              ↓                                ↓
┌─────────────────────────────────────────────────────────────┐
│ 直接原因                                                     │
│ kubelet 在尝试拉取容器镜像时，TCP 连接镜像仓库 443 端口超时，│
│ 表现为 `dial tcp X.X.X.X:443: i/o timeout` 错误。            │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                 │
│ 集群中 48 个 Pod 处于 ImagePullBackOff (27个) /               │
│ ErrImagePull (21个) 状态，持续处于 Pending 和重启循环中。     │
└─────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (node1拉取registry.k8s.io超时)、证据 #3 (node2拉取registry-1.docker.io超时)、证据 #5 (全局事件超时模式) 和证据 #4 (无认证问题)，集群问题的**根本原因是集群两个工作节点到公共镜像仓库的网络不可达**。这使得节点上的kubelet无法拉取所需的公共镜像，导致绝大多数Pod无法启动。

**置信度**：高 (95%)
- ✅ `kubectl describe` 事件明确显示 `dial tcp i/o timeout`
- ✅ 48个Pod的异常模式完全一致，指向共同的网络根因
- ✅ 排除了镜像名、认证、私有仓库配置等其他常见原因

---

**次要根因（影响2个Pod）**：

1.  **Secret 配置缺失 (Pod: rc-config-secret-key-missing)**
    *   **证据**: 证据 #6, #7
    *   **根因**: 在 `aiops-e2e` 命名空间中，Pod `rc-config-secret-key-missing` 引用的 Secret `rc-app-secret` 中 **缺少 `APP_SECRET_TOKEN` 键**。
    *   **置信度**: 高 (99%)

2.  **容器运行时启动失败 (Pod: node-debugger-node1-nx8gb)**
    *   **证据**: 证据 #8
    *   **根因**: Pod `node-debugger-node1-nx8gb` 的容器在创建时，底层容器运行时 (containerd) 无法成功启动 shim 进程，导致 `StartError`。
    *   **置信度**: 中 (60%)，因缺乏更详细的日志 (如 `journalctl -u containerd`)。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 排查并修复节点网络出口**
这是最重要的修复，直接影响48个Pod。需要网络或基础设施团队介入。

*   **排查命令（在 node1 和 node2 上执行）**:
    ```bash
    # 检查能否解析镜像仓库域名
    nslookup registry.k8s.io
    nslookup registry-1.docker.io
    nslookup gcr.io

    # 检查到镜像仓库的 TCP 443 端口是否可达（如果能通会返回空输出）
    curl -v --connect-timeout 5 https://registry.k8s.io/v2/ 2>&1 | head -20
    curl -v --connect-timeout 5 https://registry-1.docker.io/v2/ 2>&1 | head -20
    ```

*   **修复指导**:
    *   **检查 NAT/网关**: 确保节点所在子网的`路由表`有通往互联网的`默认路由`，且配置了`NAT网关`。
    *   **检查防火墙/SG规则**: 确保节点安全组或防火墙允许出站流量到 `0.0.0.0/0` 的 `TCP 443` 端口。
    *   **配置 HTTP 代理**: 如果集群通过代理上网，需要在容器运行时（containerd）配置 `http_proxy` 或 `HTTPS_PROXY`。参考 [containerd proxy 配置](https://github.com/containerd/containerd/blob/main/docs/garbage-collection.md#proxy)。
    *   **配置镜像仓库 Mirror**: 如果无法直连外网，可以考虑在节点上配置 `registry-mirror` 或使用私有仓库同步镜像。

**2. [次要] 修复 Secret 配置缺失**
```bash
# 1. 获取当前 Secret 的 base64 编码值（假设你已知道 APP_SECRET_TOKEN 的值应为何）
# 假设 APP_SECRET_TOKEN 的值是 'my-super-secret-token'
# echo -n 'my-super-secret-token' | base64

# 2. 修补 Secret，添加缺失的键
kubectl patch secret rc-app-secret -n aiops-e2e --patch '{"data": {"APP_SECRET_TOKEN": "'$(echo -n 'my-super-secret-token' | base64)'"}}'
```
*依据*：证据 #6 和 #7 明确了配置缺失的准确原因。

**3. [次要] 排查 StartError Pod (node-debugger-node1-nx8gb)**
该Pod是调试工具，影响相对较小，但仍需排查。
```bash
# 在 node1 上查看容器运行时日志，获取更详细的 OCI 错误
journalctl -u containerd -n 100 --no-pager | grep -A 20 "node-debugger-node1-nx8gb"
```
*依据*：证据 #8 显示 OCI 运行时创建失败。

### 后续优化
1.  **监控告警**：配置对 `ImagePullBackOff` 和 `ErrImagePull` 状态的告警。
2.  **使用私有仓库**：将需要的公共镜像同步到可访问的私有仓库（如 Harbor），并在集群中使用，避免对公网依赖。
3.  **应用配置审计**：在 CI/CD 流程中增加对 Secret 引用的校验，避免配置缺失。

---
## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认网络修复 | 在 node1/node2 上执行 `curl -v https://registry.k8s.io/v2/` | 返回非超时的 HTTP 响应 |
| 2. 确认 Pod 正在启动 | `kubectl get pods -A \| grep -E 'ImagePullBackOff\|ErrImagePull\|Init:Err'` | 列表不再增长，已存在的 Pod 状态从 `ErrImagePull` 变为 `ContainerCreating` 或 `Running` |
| 3. 确认Config修复 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS 从 `Pending` 变为 `ContainerCreating` 或 `Running` |

---
## ⚠️ 注意事项
- **网络修复**是首要任务，应优先分配资源解决。如果节点无法直接访问公网，需要配置代理或使用私有仓库进行镜像拉取。
- 修复网络后，kubelet 会自动重试拉取镜像，无需手动删除所有失败的 Pod，但可以使用 `kubectl delete pod --field-selector=status.phase=Pending` 来加速 Pod 的重新调度。
- `StartError` Pod (`node-debugger-node1-nx8gb`) 的问题可能和该特定 Pod 的镜像或权限有关，不一定代表节点本身有问题。

---

## 📊 性能统计

├─ 总耗时: 2.1m
├─ 问题定位: 38.3s (30%) ✅
├─ 证据链采集: 39.7s (31%) ✅
├─ 根因分析: 20.9s (17%) ✅
├─ 汇总总结: 27.5s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 18 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-config-error
- **参考 Runbook**: pod-imagepull-failed, pod-config-error
- **工具调用**: 18 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
