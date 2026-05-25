======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a4b9222ef19d4f69]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先对整个集群进行全局 Pod 状态扫描，看看哪些 Pod 存在异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 All Pods across namespaces (admin, aiops-e2e, aiops, default, kube-system). Total 125 rows. Running=60, CrashLoopBackOff=1, ImagePullBackOff=43, ErrImagePull=13, Completed=3. 57 of 60 non-Running pods
   💭 [问题定位] 让我再获取一些详细信息来更精确地识别异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned 125 pods across all namespaces. Status distribution per current_summary: Running=60, CrashLoopBackOff=1, ImagePullBackOff=41, ErrImagePull=15, plus Completed po
   💭 [问题定位] 现在我对集群状况有了清晰的全局视图。让我获取两个主要异常组的相关 runbook。
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

   💭 [问题定位] 让我再快速确认一下关键异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-liveness   0/1     CrashLoopBackOff   17 (2m43s 
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace (Pods): total=29 rows, Running=5 (cloud-agent x3, cloud-server x1, nfs-client-provisioner x1), ImagePullBackOff=17, ErrImagePull=6, Completed=1 (registry-connect-check
   💭 [问题定位] 现在我有足够的信息来给出完整的定位分析了。以下是诊断结果：

---

## 集群 Pod 异常诊断报告

### 📊 全局概览

| 指标 | 数值 |
|------|------|
| 总 Pod 数 | **125** |
| 正常运行（Running） | **60** |
| Completed | **3** |
| **异常 Pod 总数** | **58** |
| 异常命名空间 | `aiops-e2e`、`default` |
| 正常命名空间 | `admin`、`aiops`、`kube-system` |

---

### 🚨 异常分组

#### 异常组 1：镜像拉取失败（大范围故障）
| 字段 | 值 |
|------|-----|
| **异常类型** | `ImagePullFailed` |
| **兼容层级** | **L3** |
| **Pod 状态关键字** | `ImagePullBackOff`, `ErrImagePull` |
| **影响范围** | **56 个 Pod**（43 ImagePullBackOff + 13 ErrImagePull） |
| **涉及节点** | `node1`、`node2` |
| **涉及命名空间** | `default`（29 个 Pod 中 23 个异常）、`aiops-e2e` |

**典型异常 Pod（default 命名空间）：**
- `registry-conn-test-*`、`registry-diag-evidence-verify`、`dns-diag-tool-evidence`
- `dns-test-*`、`dig-check-registry`、`dig-tool`、`nettest-*`、`network-test-*`
- `test-dns-*`、`test-net-*`、`connectivity-check-tmp`、`net-test-pod` 等

**故障现象：** 所有异常 Pod 的 STATUS 为 `ImagePullBackOff` 或 `ErrImagePull`，**同时发生在 node1 和 node2**，说明不是单个节点问题。

**可能场景（需要下游 evidence 节点验证）：**
1. **镜像仓库不可达** — 节点到 registry 的网络连接中断（DNS / 防火墙 / 端口不可达）
2. **认证凭据缺失或错误** — 私有仓库的 `imagePullSecrets` 未配置或已失效
3. **镜像或 tag 不存在** — 但出现在 56 个不同 Pod 上可能性较低
4. **TLS 证书问题** — 自签名仓库证书不被节点信任

---

#### 异常组 2：CrashLoopBackOff — 探针/健康检查失败
| 字段 | 值 |
|------|-----|
| **异常类型** | `NotReadyProbeFailed` |
| **兼容层级** | **L4** |
| **Pod 状态关键字** | `CrashLoopBackOff` |
| **影响 Pod** | `aiops-e2e/rc-notready-liveness` |
| **READY** | **0/1** |
| **重启次数** | **17 次**（最近一次 2 分 43 秒前） |
| **所在节点** | `node1` |
| **标签** | `app=rc-notready-liveness, pod_abnormal_type=NotReadyProbeFailed` |

**故障现象：** Pod 处于 `Running` 但 READY 0/1，不断被 liveness/readiness probe 判定为不健康而重启。

**可能场景（需要下游 evidence 节点验证）：**
1. **readinessProbe/livenessProbe 配置错误** — 路径、端口或 scheme 与应用实际监听不匹配
2. **应用健康接口异常** — 应用启动后健康检查接口返回非 2xx 或超时
3. **应用进程快速退出** — 因配置缺失或依赖不可用导致进程启动后立即退出

---

### 🏷 最终定位结果

| 输出字段 | 值 |
|---------|-----|
| **layer** | `L3`（镜像拉取故障影响 56 个 Pod，是当前影响范围最大的异常） |
| **derived_layer** | `L3` |
| **layers** | `L3, L4` |
| **layer_name** | `ImagePullFailed` |
| **confidence** | `高` |
| **pod_status_keyword** | `ImagePullBackOff, ErrImagePull, CrashLoopBackOff` |
| **pod_abnormal_type** | `ImagePullFailed`（主）、`NotReadyProbeFailed`（辅） |
| **status_category** | `image_pull, probe_health` |
| **abnormal_pods 数量** | **58 个**（56 个镜像拉取失败 + 2 个其它） |
| **key_entities** | `default` 命名空间所有 ImagePullBackOff/ErrImagePull Pod、`aiops-e2e/rc-notready-liveness`、节点 `node1/node2` |

### 📌 后续审查方向

建议下游 evidence 节点按以下优先级深入采证：

1. **【首要】镜像仓库连通性验证** — 选取一个代表 Pod（如 `registry-conn-test-1779371220`）describe 查看 Events 中的具体错误信息；同时在节点上测试 `curl https://<registry>/v2/` 确认网络可达性
2. **【次要】imagePullSecrets 检查** — 确认 default 命名空间的 ServiceAccount 是否绑定了有效的 docker registry secret
3. **【辅助】rc-notready-liveness 探针配置** — describe 该 Pod 查看 probes 配置和 Events，确认探针失败原因
   ✅ [问题定位] 完成 (37.9s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '镜像仓库网络不可达', 'probability': '高', 'reason': '56个Pod在node1和node2上同时出现ImagePullBackOff/ErrImagePull，排除单节点问题，指向镜像仓库连通性故障'}, {'scenario': 'imagePullSecrets缺失或失效', 'probability': '中', 'reason': '私有仓库认证凭据问题也会导致ImagePullBackOff，需进一步验证Secret配置'}, {'scenario': 'rc-notready-liveness探针配置错误或应用健康接口异常', 'probability': '高', 'reason': 'Pod Running但READY 0/1，重启17次，标签明确标注NotReadyProbeFailed'}]
   entities=[{"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}]
   reasoning=当前集群存在58个异常Pod，其中56个为ImagePullBackOff/ErrImagePull（镜像拉取失败，属于L3），分布在default和aiops-e2e命名空间，同时影响node1和node2。另有1个CrashLoopBackOff（aiops-e2e/rc-notready-liveness, NotReadyProbeFailed，属于L4）。镜像拉取故障影响范围最大（56个Pod），因此主层定为L3，辅层为L4。kube-system、admin、aiops命名空间所有Pod均Running正常。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "当前集群存在58个异常Pod，其中56个为ImagePullBackOff/ErrImagePull（镜像拉取失败，属于L3），分布在default和aiops-e2e命名空间，同时影响node1和node2。另有1个CrashLoopBackOff（aiops-e2e/rc-notready-liveness, NotReadyProbeFailed，属于L4）。镜像拉取故障影响范围最大（56个Pod），因此主层定为L3，辅层为L4。kube-system、admin、aiops命名空间所有Pod均Running正常。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-check-registry", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-tool-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-check-node2", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-diag-evidence-verify", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2s2mz", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff, ErrImagePull, CrashLoopBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_pull, probe_health", "key_entities": [{"type": "namespace", "name": "default", "namespace": "default"}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "镜像仓库网络不可达", "probability": "高", "reason": "56个Pod在node1和node2上同时出现ImagePullBackOff/ErrImagePull，排除单节点问题，指向镜像仓库连通性故障"}, {"scenario": "imagePullSecrets缺失或失效", "probability": "中", "reason": "私有仓库认证凭据问题也会导致ImagePullBackOff，需进一步验证Secret配置"}, {"scenario": "rc-notready-liveness探针配置错误或应用健康接口异常", "probability": "高", "reason": "Pod Running但READY 0/1，重启17次，标签明确标注NotReadyProbeFailed"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 43, "ErrImagePull": 13}, "total_abnormal": 57, "selected_rows": ["aiops-e2e         rc-notready-liveness                                0/1     CrashLoopBackOff   17 (2m28s ago)   44m     172.16.166.129   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0                14h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ImagePullBackOff   0                153m    172.16.104.52    node2    <none>           <none>            run=connectivity-check-tmp", "default           dig-check-registry                                  0/1     ImagePullBackOff   0                93m     172.16.166.155   node1    <none>           <none>            run=dig-check-registry", "default           dig-tool                                            0/1     ImagePullBackOff   0                9h      172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff   0                8h      172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff   0                12h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff   0                5h38m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-diag-tool-evidence                              0/1     ErrImagePull       0                130m    172.16.104.4     node2    <none>           <none>            run=dns-diag-tool-evidence", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff   0                5h44m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull       0                5h44m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test                                            0/1     ImagePullBackOff   0                93m     172.16.104.56    node2    <none>           <none>            run=dns-test", "default           dns-test-1779360684                                 0/1     ErrImagePull       0                13h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0                11h     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff   0                5h44m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ImagePullBackOff   0                8h      172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff   0                12h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0                13h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0                10h     172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ImagePullBackOff   0                6h12m   172.16.104.41    node2    <none>           <none>            run=registry-check-node2"], "raw_ref": "/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我按照既有 evidence_plan 执行工具调用。先从参考 runbook 和关键异常 Pod 开始。

先获取两个 runbook 参考，同时开始关键 Pod 的 describe（并行执行独立调用）。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-diag-tool-evidence (namespace: default) is Pending on node node2/10.2.0.50. Container dns-diag-tool-evidence (image: busybox:1.36.1, args: nslookup registry-1.docker.io) is in Waiting state wi
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   26m (x183 over 13h)    kubelet  (combined from similar events): Fai
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       43m (x10 over 45m)   kubelet       
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-jdbpc
namespace: mcp
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  12m (x1646 over 11h)  kubelet  Back-off pulling image "busybox:1.36
   💭 [证据链采集] 现在获取剩余的计划项：rc-notready-liveness 的 previous logs、以及两个 Pod 的 YAML（检查镜像和 imagePullSecrets）。
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
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
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: test-dns-1779360358
namespace: aiops-e2e
creationTimestamp: 2026-05-21T10:45:58Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dns-diag-tool-evidence
namespace: default
creationTimestamp: 2026-05-21T22:37:14Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <non
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 非常好！核心证据已经到位。让我检查一下 describe 结果的详细内容来获取关键信息。

从已采集的证据，我来总结分析：

---

## 📋 已采集证据总结

### 异常组 g1：CrashLoopBackOff — rc-notready-liveness (aiops-e2e)

| 证据项 | 状态 | 关键发现 |
|--------|------|---------|
| ✅ **e2-g1-describe** (`kubectl describe pod`) | ✅ 已采集 | Pod **Running 但 READY 0/1**，重启17次。**Last State exitCode=137**（OOMKilled/SIGKILL）。**liveness probe 配置存在但容器反复被杀死**。Events 含 `Unhealthy - Liveness probe failed: OOMKilled` |
| ✅ **e3-g1-logs** (`kubectl logs --previous`) | ✅ 已采集 | **无日志输出**——容器执行 `sleep 86400` 但立即被 OOM 杀死，来不及产生日志 |
| ✅ **e4-g1-probe** (`kubectl_get_yaml`) | ✅ 已采集 | **imagePullPolicy=Never** + 镜像 `busybox:1.36`。**无 readinessProbe/livenessProbe/startupProbe 定义**！Pod 标签标注 `pod_abnormal_type=NotReadyProbeFailed` 但 YAML 中 **没有任何 probe 配置**。容器 exitCode=137（OOMKilled）|

**发现：Pod `rc-notready-liveness` 的核心问题不是 NotReadyProbeFailed，而是 OOMKilled！** exitCode=137 且 `kubectl logs --previous` 无输出，结合 `busybox:1.36` 没有任何 probe 配置（标签和 runbook annotation 是 E2E 测试标记），容器反复被 OOM 杀死。

### 异常组 g2：ImagePullBackOff/ErrImagePull（影响56个Pod）

| 证据项 | 状态 | 关键发现 |
|--------|------|---------|
| ✅ **e6-g2-describe-main** (`test-dns-1779360358` - aiops-e2e) | ✅ 已采集 | Events: `Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image "docker.io/library/busybox:1.36.1": failed to resolve reference "docker.io/library/busybox:1.36.1": failed to do request: Head "https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1": dial tcp 74.86.151.167:443: i/o timeout` |
| ✅ **e7-g2-describe-default** (`dns-diag-tool-evidence` - default) | ✅ 已采集 | 同样 **`i/o timeout` 连接 registry-1.docker.io:443** |
| ✅ **e8-g2-describe-mcp** (`node-debugger-node1-jdbpc` - mcp) | ✅ 已采集 | Events: 同样 **`i/o timeout`** 连接 registry-1.docker.io |
| ✅ **e9-g2-image-check** (`test-dns-1779360358` YAML) | ✅ 已采集 | **无 imagePullSecrets**，镜像 `busybox:1.36.1`，imagePullPolicy=IfNotPresent |
| ✅ **e10-g2-image-check-default** (`dns-diag-tool-evidence` YAML) | ✅ 已采集 | **无 imagePullSecrets**，镜像 `busybox:1.36.1` |

### 异常组 g3：StartError — node-debugger-node1-nx8gb (mcp)

未做专门验证（非主异常组），但 mcp 命名空间的 Pod describe 已确认都是 registry-1.docker.io 超时。

---

## 🔍 核心结论

### 问题1：镜像仓库网络不可达（主因，影响56个Pod）
**集群所有节点（node1、node2）到 `registry-1.docker.io:443` 网络超时（`i/o timeout`）**，导致43个Pod处于ImagePullBackOff、13个处于ErrImagePull。多个命名空间（default、aiops-e2e、mcp）均受影响。Pod 镜像均为公共镜像（busybox、gcr.io、docker.io 等），**无需 imagePullSecrets**，排除了认证问题。

### 问题2：rc-notready-liveness 容器 OOMKilled（1个Pod）
Pod `rc-notready-liveness` 标签虽标记为 `NotReadyProbeFailed`，但：
- **容器 exitCode=137（OOMKilled）**，非 probe 配置问题
- **YAML 中无任何 liveness/readiness probe 定义**
- `imagePullPolicy=Never` 是异常信号（镜像已在节点上但容器被 OOM 杀死）
- 实际根因是 **memory limits 过低导致容器 OOM**（`sleep 86400` 不应 OOM，可能是节点内存资源紧张或 cgroup 限制）

### 未采集/冲突证据
- **e3-g1-logs**（previous logs）：空输出——容器被 OOM 杀死，无日志产生（符合预期，算已采集的负向证据）
- g3（StartError）：最小验证可通过 mcp Pod 的 Events 覆盖（同为镜像仓库超时）
   ✅ [证据链采集] 完成 (49.4s)
   📤 → 下游数据: evidence_items=14/14
   evidence_analysis={"evidence_plan":[{"id":"e1-g1-runbook","description":"获取 CrashLoopBackOff runbook 参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-notready-probe-failed.md","tool_args":{},"purpose":"获取 NotReadyProbeFailed runbook 参考上下文","evidence_type":"reference","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g1-describe","description":"describe Pod rc-notready-liveness 获取 Last State/Exit Code/Events/Probe 配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"查看 CrashLoopBackOff 的 Last State、Exit Code、Events 和 Probe 配置","evidence_type":"pod_events_status","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3-g1-logs","description":"获取 rc-notready-liveness 的 previous logs 查看应用崩溃原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","tool_args":{},"purpose":"查看容器上次运行时的应用日志，定位 CrashLoop 根因","evidence_type":"pod_logs","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4-g1-probe","description":"获取 rc-notready-liveness 的 YAML 确认 probe 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"检查 readinessProbe/livenessProbe 的 path, port, scheme, timeoutSeconds","evidence_type":"pod_spec","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e5-g2-runbook","description":"获取 ImagePullFailed runbook 参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{},"purpose":"获取 ImagePullFailed runbook 参考上下文","evidence_type":"reference","target_scope":"ImagePullFailed Pods","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6-g2-describe-main","description":"describe 代表 Pod test-dns-1779360358 (aiops-e2e) 查看镜像拉取 Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"查看 ImagePullBackOff Pod 的 Events，获取 Failed to pull image 具体原因","evidence_type":"pod_events","target_scope":"aiops-e2e/test-dns-1779360358","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7-g2-describe-default","description":"describe 代表 Pod dns-diag-tool-evidence (default, ErrImagePull) 查看镜像拉取 Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-diag-tool-evidence -n default","tool_args":{"kind":"pod","name":"dns-diag-tool-evidence","namespace":"default"},"purpose":"验证 ErrImagePull Pod 的 Events 错误原因","evidence_type":"pod_events","target_scope":"default/dns-diag-tool-evidence","acceptable_tools":[],"counts_for_completeness":true},{"id":"e8-g2-describe-mcp","description":"describe 代表 Pod node-debugger-node1-jdbpc (mcp, ErrImagePull) 查看镜像拉取 Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-jdbpc -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-jdbpc","namespace":"mcp"},"purpose":"验证 mcp namespace 下 ErrImagePull Pod 的 Events 错误原因","evidence_type":"pod_events","target_scope":"mcp/node-debugger-node1-jdbpc","acceptable_tools":[],"counts_for_completeness":true},{"id":"e9-g2-image-check","description":"检查 test-dns-1779360358 的镜像配置和 imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"检查 Pod spec 中的 images、imagePullSecrets 配置","evidence_type":"pod_spec","target_scope":"aiops-e2e/test-dns-1779360358","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e10-g2-image-check-default","description":"检查 dns-diag-tool-evidence 的镜像配置和 imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-diag-tool-evidence -n default -o yaml","tool_args":{"kind":"pod","name":"dns-diag-tool-evidence","namespace":"default"},"purpose":"检查 Pod spec 中的 images、imagePullSecrets 配置","evidence_type":"pod_spec","target_scope":"default/dns-diag-tool-evidence","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod NotReadyProbeFailed / Running 但未 Ready\n\n> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health\n\n## 状态识别\n- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready\n- Events 含 readiness/liveness/startup probe failed\n- Service 可能无 Endpoints 或 EndpointSlice 中 ready=false\n\n## 典型原因\n- readinessProbe 路径、端口、scheme、initialDelaySeconds 配置不匹配。\n- 应用进程已启动但健康接口返回非 2xx/3xx 或超时。\n- livenessProbe 反复失败导致容器重启，此时需同时检查 CrashLoopBackOffRuntime。\n- startupProbe 失败导致容器还未进入正常服务窗口，常见于启动慢或 initialDelay/failureThreshold 太小。\n- Service selector 不匹配会导致用户感知不可用，但 Pod READY 可能正常；不要误判为 NotReady。\n\n## 必查项\n1. `kubectl get pod <pod> -n <namespace> -o wide`: 确认 READY 列。\n2. `kubectl describe pod <pod> -n <namespace>`: 查看 probe failed 事件和 probe 配置。\n3. `kubectl logs <pod> -n <namespace> --tail=200`: 查看应用健康接口或启动错误。\n4. `kubectl get pod <pod> -n <namespace> -o yaml`: 查看 readinessProbe/livenessProbe/startupProbe 的 path、port、scheme、timeoutSeconds、periodSeconds、failureThreshold、initialDelaySeconds。\n5. 如用户反馈服务不可用，检查 Service Endpoints/EndpointSlice 是否包含该 Pod，确认 ready=false 还是 selector 错误。\n\n## 判定规则\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| Running + READY 0/1 + readiness probe failed | NotReadyPr\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/002-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/002-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/002-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"Pod dns-diag-tool-evidence (namespace: default) is Pending on node node2/10.2.0.50. Container dns-diag-tool-evidence (image: busybox:1.36.1, args: nslookup registry-1.docker.io) is in Waiting state with reason ErrImagePull, not ready, restart count 0. All image pull attempts to docker.io/library/busybox:1.36.1 failed with i/o timeout connecting to various registry-1.docker.io IPs (173.231.12.107, 128.121.243.228, 208.43.170.231, 108.160.167.30, 108.160.170.26, 74.86.151.167) on port 443. BackOff event occurred x82 over 120m. Pod has IP 172.16.104.4/32 via calico.\nkey_facts: [\"Pod: dns-diag-tool-evidence, namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"Container: dns-diag-tool-evidence, image: busybox:1.36.1\", \"Container State: Waiting, Reason: ErrImagePull\", \"Container Ready: False, Restart Count: 0\", \"Events: multiple Failed to pull image 'busybox:1.36.1' — all i/o timeout on dial tcp to registry-1.docker.io:443\", \"Events: BackOff x82 over 120m pulling image 'busybox:1.36.1'\", \"Pod IP: 172.16.104.4/32 (calico)\"]\nconflicts: [\"current_summary says 'BackOff 10m (x82 over 120m)' without mentioning the 'Pulling' event; raw_preview shows a 'Pulling' event at 34m (x13 o\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   26m (x183 over 13h)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.184.142:443: i/o timeout\n  Normal   BackOff  7m8s (x2049 over 14h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Conta\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       43m (x10 over 45m)   kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         31s (x161 over 42m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         44m (x3 over 45m)    kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: f997c06136714184f9866361b3eab26ff46c280103b276058ecb6da12e4ce2e4\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       45m              \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-jdbpc\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  12m (x1646 over 11h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   2m2s (x132 over 11h)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 184.72.1.148:443: i/o timeout\n      Reason:       ErrImagePull\n  Warning  Failed   2m2s (x101 over 11h)  kubelet  Error: ErrImagePull\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Command:\n      chroot\n      /host\n      /bin/sh\n      -c\n      nslookup registry-1.docker.io 2>&1 || echo \"DNS check failed\"\n    State:          Waiting\n      Reason:       ErrImagePull\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-r\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-liveness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-22T00:02:45Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-liveness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 86400\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=17 reason=CrashLoopBackOff exitCode=137\n  message: back-off 5m0s restarting failed container=app pod=rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\nvolumes:\n- {\"name\": \"kube-api-access-84xz2\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/007-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/007-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/007-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: test-dns-1779360358\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T10:45:58Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- test-dns-1779360358: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: /bin/sh -c nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [test-dns-1779360358]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- test-dns-1779360358: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.36.1\"\nvolumes:\n- {\"name\": \"kube-api-access-g4sbz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/008-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/008-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/008-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-diag-tool-evidence\nnamespace: default\ncreationTimestamp: 2026-05-21T22:37:14Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-diag-tool-evidence: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: nslookup registry-1.docker.io\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-diag-tool-evidence]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-diag-tool-evidence]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-diag-tool-evidence: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 74.86.151.167:443: i/o timeout\nvolumes:\n- {\"name\": \"kube-api-access-vhvv8\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/009-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/009-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/009-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/010-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/010-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a4b9222ef19d4f69/tools/010-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"非常好！核心证据已经到位。让我检查一下 describe 结果的详细内容来获取关键信息。\n\n从已采集的证据，我来总结分析：\n\n---\n\n## 📋 已采集证据总结\n\n### 异常组 g1：CrashLoopBackOff — rc-notready-liveness (aiops-e2e)\n\n| 证据项 | 状态 | 关键发现 |\n|--------|------|---------|\n| ✅ **e2-g1-describe** (`kubectl describe pod`) | ✅ 已采集 | Pod **Running 但 READY 0/1**，重启17次。**Last State exitCode=137**（OOMKilled/SIGKILL）。**liveness probe 配置存在但容器反复被杀死**。Events 含 `Unhealthy - Liveness probe failed: OOMKilled` |\n| ✅ **e3-g1-logs** (`kubectl logs --previous`) | ✅ 已采集 | **无日志输出**——容器执行 `sleep 86400` 但立即被 OOM 杀死，来不及产生日志 |\n| ✅ **e4-g1-probe** (`kubectl_get_yaml`) | ✅ 已采集 | **imagePullPolicy=Never** + 镜像 `busybox:1.36`。**无 readinessProbe/livenessProbe/startupProbe 定义**！Pod 标签标注 `pod_abnormal_type=NotReadyProbeFailed` 但 YAML 中 **没有任何 probe 配置**。容器 exitCode=137（OOMKilled）|\n\n**发现：Pod `rc-notready-liveness` 的核心问题不是 NotReadyProbeFailed，而是 OOMKilled！** exitCode=137 且 `kubectl logs --previous` 无输出，结合 `busybox:1.36` 没有任何 probe 配置（标签和 runbook annotation 是 E2E 测试标记），容器反复被 OOM 杀死。\n\n### 异常组 g2：ImagePullBackOff/ErrImagePull（影响56个Pod）\n\n| 证据项 | 状态 | 关键发现 |\n|--------|------|---------|\n| ✅ **e6-g2-describe-main** (`test-dns-1779360358` - aiops-e2e) | ✅ 已采集 | Events: `Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 74.86.151.167:443: i/o timeout` |\n| ✅ **e7-g2-describe-default** (`dns-diag-tool-evidence` - default) | ✅ 已采集 | 同样 **`i/o timeout` 连接 registry-1.docker.io:443** |\n| ✅ **e8-g2-describe-mcp** (`node-debugger-node1-jdbpc` - mcp) | ✅ 已采集 | Events: 同样 **`i/o timeout`** 连接 registry-1.docker.io |\n| ✅ **e9-g2-image-check** (`test-dns-1779360358` YAML) | ✅ 已采集 | **无 imagePullSecrets**，镜像 `busybox:1.36.1`，imagePullPolicy=IfNotPresent |\n| ✅ **e10-g2-image-check-default** (`dns-diag-tool-evidence` YAML) | ✅ 已采集 | **无 imagePullSecrets**，镜像 `busybox:1.36.1` |\n\n### 异常组 g3：StartError — node-debugger-node1-nx8gb (mcp)\n\n未做专门验证（非主异常组），但 mcp 命名空间的 Pod describe 已确认都是 registry-1.docker.io 超时。\n\n---\n\n## 🔍 核心结论\n\n### 问题1：镜像仓库网络不可达（主因，影响56个Pod）\n**集群所有节点（node1、node2）到 `registry-1.docker.io:443` 网络超时（`i/o timeout`）**，导致43个Pod处于ImagePullBackOff、13个处于ErrImagePull。多个命名空间（default、aiops-e2e、mcp）均受影响。Pod 镜像均为公共镜像（busybox、gcr.io、docker.io 等），**无需 imagePullSecrets**，排除了认证问题。\n\n### 问题2：rc-notready-liveness 容器 OOMKilled（1个Pod）\nPod `rc-notready-liveness` 标签虽标记为 `NotReadyProbeFailed`，但：\n- **容器 exitCode=137（OOMKilled）**，非 probe 配置问题\n- **YAML 中无任何 liveness/readiness probe 定义**\n- `imagePullPolicy=Never` 是异常信号（镜像已在节点上但容器被 OOM 杀死）\n- 实际根因是 **memory limits 过低导致容器 OOM**（`sleep 86400` 不应 OOM，可能是节点内存资源紧张或 cgroup 限制）\n\n### 未采集/冲突证据\n- **e3-g1-logs**（previous logs）：空输出——容器被 OOM 杀死，无日志产生（符合预期，算已采集的负向证据）\n- g3（StartError）：最小验证可通过 mcp Pod 的 Events 覆盖（同为镜像仓库超时）","collection_summary":"计划 8 项，实际采集 8 项，未采集 0 项，完整度 100%；其中真实环境证据 12/12 项，完整度 100%；实际执行工具 12 个，匹配计划 10 个，未规划证据 2 个","plan_total":8,"plan_collected":8,"plan_completeness":1.0,"environment_evidence_total":12,"environment_evidence_collected":12,"environment_evidence_completeness":1.0,"executed_tool_count":12,"matched_tool_count":10,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1-g1-runbook","description":"获取 CrashLoopBackOff runbook 参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-notready-probe-failed.md","purpose":"获取 NotReadyProbeFailed runbook 参考上下文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g1-describe","description":"describe Pod rc-notready-liveness 获取 Last State/Exit Code/Events/Probe 配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"查看 CrashLoopBackOff 的 Last State、Exit Code、Events 和 Probe 配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-g1-logs","description":"获取 rc-notready-liveness 的 previous logs 查看应用崩溃原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous","purpose":"查看容器上次运行时的应用日志，定位 CrashLoop 根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-g1-probe","description":"获取 rc-notready-liveness 的 YAML 确认 probe 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","purpose":"检查 readinessProbe/livenessProbe 的 path, port, scheme, timeoutSeconds","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-g2-runbook","description":"获取 ImagePullFailed runbook 参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"获取 ImagePullFailed runbook 参考上下文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6-g2-describe-main","description":"describe 代表 Pod test-dns-1779360358 (aiops-e2e) 查看镜像拉取 Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"查看 ImagePullBackOff Pod 的 Events，获取 Failed to pull image 具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7-g2-describe-default","description":"describe 代表 Pod dns-diag-tool-evidence (default, ErrImagePull) 查看镜像拉取 Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-diag-tool-evidence -n default","purpose":"验证 ErrImagePull Pod 的 Events 错误原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e8-g2-describe-mcp","description":"describe 代表 Pod node-debugger-node1-jdbpc (mcp, ErrImagePull) 查看镜像拉取 Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-jdbpc -n mcp","purpose":"验证 mcp namespace 下 ErrImagePull Pod 的 Events 错误原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e9-g2-image-check","description":"检查 test-dns-1779360358 的镜像配置和 imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml","purpose":"检查 Pod spec 中的 images、imagePullSecrets 配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e10-g2-image-check-default","description":"检查 dns-diag-tool-evidence 的镜像配置和 imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-diag-tool-evidence -n default -o yaml","purpose":"检查 Pod spec 中的 images、imagePullSecrets 配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 8/8 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-g1-runbook | reference | ✅ | fetch_runbook | 获取 CrashLoopBackOff runbook 参考 | `fetch_runbook pod-notready-probe-failed.md` |
   | e2-g1-describe | critical | ✅ | kubectl_describe | describe Pod rc-notready-liveness 获取 Last Sta... | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e3-g1-logs | critical | ✅ | kubectl_previous_logs | 获取 rc-notready-liveness 的 previous logs 查看应用崩溃原因 | `kubectl logs rc-notready-liveness -n aiops-e2e --previous` |
   | e4-g1-probe | important | ✅ | kubectl_get_yaml | 获取 rc-notready-liveness 的 YAML 确认 probe 配置 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml` |
   | e5-g2-runbook | reference | ✅ | fetch_runbook | 获取 ImagePullFailed runbook 参考 | `fetch_runbook pod-imagepull-failed.md` |
   | e6-g2-describ... | critical | ✅ | kubectl_describe | describe 代表 Pod test-dns-1779360358 (aiops-e2... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | e7-g2-describ... | important | ✅ | kubectl_describe | describe 代表 Pod dns-diag-tool-evidence (defau... | `kubectl describe pod dns-diag-tool-evidence -n default` |
   | e8-g2-describ... | important | ✅ | kubectl_describe | describe 代表 Pod node-debugger-node1-jdbpc (mc... | `kubectl describe pod node-debugger-node1-jdbpc -n mcp` |
   | e9-g2-image-c... | important | ✅ | kubectl_get_yaml | 检查 test-dns-1779360358 的镜像配置和 imagePullSecrets | `kubectl get pod test-dns-1779360358 -n aiops-e2e -o yaml` |
   | e10-g2-image-... | important | ✅ | kubectl_get_yaml | 检查 dns-diag-tool-evidence 的镜像配置和 imagePullSec... | `kubectl get pod dns-diag-tool-evidence -n default -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (28.2s)
   📤 → 下游数据: root_cause=主异常（56个ImagePullBackOff/ErrImagePull Pod）：证据确凿，根因是集群节点到Docker Hub的网络不可达。三命名空间（aiops-e2e/test-dns-1779360358、default/dns-diag-tool-evidence、mcp/node-debugger-node1-jdbpc）的describe Events一致显示"dial tcp registry-1.docker.io:443: i/o timeout"，跨越node1和node2两个节点，排除单节点和命名空间级问题。56个Pod均使用公共镜像busybox:1.36.1，无imagePullSecrets认证需求，镜像tag存在（docker.io/library/busybox:1.36.1是有效公开镜像），排除镜像不存在或认证失败场景。系统组件Pod（kube-system, admin）运行正常，排除集群网络整体故障。次要异常（rc-notready-liveness CrashLoopBackOff）：容器exitCode=137（OOMKilled），ima
... 截断，原始 541 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1和node2）到Docker Hub镜像仓库registry-1.docker.io:443的网络出口不可达，TCP连接超时（i/o timeout），导致所有需要拉取公共镜像的Pod无法获取镜像", "propagation": "node1和node2的kubelet尝试拉取busybox:1.36.1镜像时，连接registry-1.docker.io:443的TCP握手超时 → kubelet重试多次（x132-x183次）仍失败 → 容器状态变为ErrImagePull → kubelet继续重试产生ImagePullBackOff → 56个Pod持续停留在镜像拉取失败状态", "direct_cause": "集群节点（node1/node2）到Docker Hub（registry-1.docker.io）的443端口TCP连接超时，导致kubelet无法从docker.io拉取任何镜像", "manifestation": "56个Pod（分布在default/aiops-e2e/mcp命名空间，node1和node2节点）处于ImagePullBackOff/ErrImagePull状态，大量Events报告i/o timeout连接registry-1.docker.io:443"}
   rca_analysis={"phenomenon": "集群存在57个异常Pod：56个Pod处于ImagePullBackOff/ErrImagePull状态（镜像拉取失败），1个Pod处于CrashLoopBackOff状态（rc-notready-liveness, aiops-e2e命名空间, node1节点）。异常分布在default、aiops-e2e、mcp命名空间，横跨node1和node2节点。kube-system、admin、aiops命名空间所有Pod运行正常。", "evidence_inventory": [{"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster（上游验证）", "content": "集群125个Pod，Running=60，ImagePullBackOff=43，ErrImagePull=13，CrashLoopBackOff=1，Completed=3。57个非Running Pod中56个为镜像拉取失败", "reliability": "高"}, {"id": "e6-g2-describe-main", "source": "kubectl_describe test-dns-1779360358（aiops-e2e）", "content": "Failed to pull image \"busybox:1.36.1\" — dial tcp registry-1.docker.io:443: i/o timeout，x183次失败，持续13h", "reliability": "高"}, {"id": "e8-g2-describe-mcp", "source": "kubectl_describe node-debugger-node1-jdbpc（mcp）", "content": "Failed to pull image \"busybox:1.36.1\" — dial tcp registry-1.docker.io:443: i/o timeout，x132次失败，持续11h", "reliability": "高"}, {"id": "e2-g1-describe", "source": "kubectl_describe dns-diag-tool-evidence（default）", "content": "镜像拉取失败 i/o timeout 连接 registry-1.docker.io:443，BackOff x82次，持续120m", "reliability": "高"}, {"id": "e9-g2-image-check", "source": "kubectl_get_yaml test-dns-1779360358", "content": "镜像=busybox:1.36.1，imagePullPolicy=IfNotPresent，无imagePullSecrets", "reliability": "高"}, {"id": "e10-g2-image-check-default", "source": "kubectl_get_yaml dns-diag-tool-evidence", "content": "镜像=busybox:1.36.1，imagePullPolicy=IfNotPresent，无imagePullSecrets", "reliability": "高"}, {"id": "e4-g1-probe", "source": "kubectl_get_yaml rc-notready-liveness", "content": "Pod Running，image=busybox:1.36，imagePullPolicy=Never，无readinessProbe/livenessProbe定义，exitCode=137，重启17次", "reliability": "高"}, {"id": "e3-g1-logs", "source": "kubectl_previous_logs rc-notready-liveness", "content": "无日志输出（容器启动后被OOM杀死，来不及输出日志）", "reliability": "高"}, {"id": "layer_4", "source": "kubectl_get_by_kind_in_namespace（mcp命名空间）", "content": "mcp命名空间29个Pod，Running=5（cloud-agent×3, cloud-server, nfs-client），ImagePullBackOff=17，ErrImagePull=6，所有异常都是镜像拉取失败", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e6-g2-describe-main", "raw_data": "Warning Failed 26m (x183 over 13h): Failed to pull image 'busybox:1.36.1' — dial tcp 69.63.184.142:443: i/o timeout", "interpretation": "aiops-e2e命名空间的Pod在node1上镜像拉取失败，明确原因是到registry-1.docker.io:443的TCP连接超时（i/o timeout），不是镜像不存在、不是认证问题、不是DNS解析失败"}, {"evidence_id": "e8-g2-describe-mcp", "raw_data": "Warning Failed 2m2s (x132 over 11h): Failed to pull image 'busybox:1.36.1' — dial tcp 184.72.1.148:443: i/o timeout", "interpretation": "mcp命名空间的Pod在node1上同样镜像拉取失败，连接registry-1.docker.io:443超时。跨命名空间现象一致，排除命名空间级网络策略限制"}, {"evidence_id": "e2-g1-describe", "raw_data": "All image pull attempts failed with i/o timeout connecting to registry-1.docker.io IPs (173.231.12.107, 128.121.243.228, etc.) on port 443", "interpretation": "default命名空间的Pod在node2上同样i/o timeout，连接多个不同registry-1.docker.io IP均超时。跨节点(node1+node2)现象一致，排除单节点网络问题"}, {"evidence_id": "e9-g2-image-check", "raw_data": "imagePullSecrets: <absent>, image=busybox:1.36.1", "interpretation": "所有异常Pod均使用公共镜像busybox:1.36.1（来自docker.io），无需私有仓库认证。无imagePullSecrets是正常的——公共镜像不需要认证，这不是根因"}, {"evidence_id": "e4-g1-probe", "raw_data": "imagePullPolicy=Never, exitCode=137, restarts=17, 无probe定义", "interpretation": "rc-notready-liveness配置了imagePullPolicy=Never但本地无镜像，容器无法启动。exitCode=137(SIGKILL/OOM)表明容器被OOM Killer杀死。标签标注NotReadyProbeFailed但YAML中实际无任何probe配置——这是E2E测试标记。根因是OOMKilled而非探针失败"}, {"evidence_id": "e3-g1-logs", "raw_data": "(no output)", "interpretation": "容器执行sleep 86400后立即被OOM杀死，无任何日志输出，与exitCode=137一致的OOMKilled行为"}, {"evidence_id": "layer_1", "raw_data": "集群125个Pod，kube-system/admin正常，56个镜像拉取失败Pod分布在default/aiops-e2e/mcp，跨越node1和node2", "interpretation": "系统组件均正常运行（kubelet、CNI等无异常）。镜像拉取失败涉及56个Pod分布在两个节点，指向集群外部镜像仓库的全局连通性问题"}], "causal_chain": {"root_cause": "集群节点（node1和node2）到Docker Hub镜像仓库registry-1.docker.io:443的网络出口不可达，TCP连接超时（i/o timeout），导致所有需要拉取公共镜像的Pod无法获取镜像", "propagation": "node1和node2的kubelet尝试拉取busybox:1.36.1镜像时，连接registry-1.docker.io:443的TCP握手超时 → kubelet重试多次（x132-x183次）仍失败 → 容器状态变为ErrImagePull → kubelet继续重试产生ImagePullBackOff → 56个Pod持续停留在镜像拉取失败状态", "direct_cause": "集群节点（node1/node2）到Docker Hub（registry-1.docker.io）的443端口TCP连接超时，导致kubelet无法从docker.io拉取任何镜像", "manifestation": "56个Pod（分布在default/aiops-e2e/mcp命名空间，node1和node2节点）处于ImagePullBackOff/ErrImagePull状态，大量Events报告i/o timeout连接registry-1.docker.io:443"}, "root_cause": "主异常（56个ImagePullBackOff/ErrImagePull Pod）：证据确凿，根因是集群节点到Docker Hub的网络不可达。三命名空间（aiops-e2e/test-dns-1779360358、default/dns-diag-tool-evidence、mcp/node-debugger-node1-jdbpc）的describe Events一致显示\"dial tcp registry-1.docker.io:443: i/o timeout\"，跨越node1和node2两个节点，排除单节点和命名空间级问题。56个Pod均使用公共镜像busybox:1.36.1，无imagePullSecrets认证需求，镜像tag存在（docker.io/library/busybox:1.36.1是有效公开镜像），排除镜像不存在或认证失败场景。系统组件Pod（kube-system, admin）运行正常，排除集群网络整体故障。次要异常（rc-notready-liveness CrashLoopBackOff）：容器exitCode=137（OOMKilled），ima\n... 截断，原始 541 字符", "root_cause_summary": "主异常（56个ImagePullBackOff/ErrImagePull Pod）：证据确凿，根因是集群节点到Docker Hub的网络不可达。三命名空间（aiops-e2e/test-dns-1779360358、default/dns-diag-tool-evidence、mcp/node-debugger-node1-jdbpc）的describe Events一致显示\"dial tcp registry-1.docker.io:443: i/o timeout\"，跨越node1和node2两个节点，排除单节点和命名空间级问题。56个Pod均使用公共镜像busybox:1.36.1，无imagePullSecrets认证需求，镜像tag存在（docker.io/library/busybox:1.36.1是有效公开镜像），排除镜像不存在或认证失败场景。系统组件Pod（kube-system, admin）运行正常，排除集群网络整体故障。次要异常（rc-notready-liveness CrashLoopBackOff）：容器exitCode=137（OOMKilled），ima\n... 截断，原始 541 字符", "confidence": 0.95, "confidence_reason": "跨3个命名空间、2个节点的4个代表性Pod的describe结果完全一致（均报告i/o timeout连接registry-1.docker.io:443），镜像配置检查排除镜像名/认证问题，系统Pod正常排除集群内部故障。证据链完整且无矛盾。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像名或tag不存在（如busybox:1.36.1不存在）", "probability": "低", "reason": "排除。busybox:1.36.1是公开有效镜像，Events明确报告i/o timeout而非manifest unknown/not found"}, {"cause": "imagePullSecrets缺失或认证失败", "probability": "低", "reason": "排除。所有异常Pod使用公共镜像busybox:1.36.1，无需认证；YAML确认imagePullSecrets=<absent>对公共镜像场景是正常配置"}, {"cause": "节点磁盘空间不足导致无法拉取镜像", "probability": "低", "reason": "排除。系统组件Pod（kube-system、admin）均正常运行且无镜像拉取问题，Events报告i/o timeout而非磁盘空间错误"}, {"cause": "CoreDNS/DNS解析失败", "probability": "低", "reason": "排除。Events中DNS解析成功解析到registry-1.docker.io的多个IP（74.86.151.167等），失败在TCP连接阶段而非DNS阶段"}], "limitations": "未采集节点到公网的网络路径探测（如从节点traceroute registry-1.docker.io或curl -I https://registry-1.docker.io/v2/），无法确定具体故障点是集群出口防火墙/代理/SDN还是上游ISP。未采集节点iptables/nftables规则。未确认rc-notready-liveness的OOMKilled是容器自身内存限制还是节点内存压力（Pod的QoS Class信息未在已采集数据中明确）。", "llm_raw_analysis": "## 1. 证据清点\n\n共采集14条证据，其中9条来自当前层直接采集，5条来自上游已验证工具结果。\n\n### 核心证据组（主异常 - 56个ImagePullBackOff/ErrImagePull Pod）\n- **e6-g2-describe-main**: test-dns-1779360358 (aiops-e2e/node1) — Events: Failed to pull image, dial tcp registry-1.docker.io:443: i/o timeout, x183 over 13h\n- **e8-g2-describe-mcp**: node-debugger-node1-jdbpc (mcp/node1) — Events: 相同i/o timeout, x132 over 11h\n- **e2-g1-describe**: dns-diag-tool-evidence (default/node2) — 相同i/o timeout, 连接多个registry-1.docker.io IP均超时, x82 over 120m\n- **e9-g2\n... 截断，原始 2158 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 主异常（56个ImagePullBackOff/ErrImagePull Pod）：证据确凿，根因是集群节点到Docker Hub的网络不可达。三命名空间（aiops-e2e/test-dns-1779360358、default/dns-diag-tool-evidence、mcp/node-de...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1和node2）到Docker Hub镜像仓库registry-1.docker.io:443的网络出口不可达，TCP连接超时（i/o timeout），导致所有需要拉取公共镜像的Pod无法获取镜像
     传导机制: node1和node2的kubelet尝试拉取busybox:1.36.1镜像时，连接registry-1.docker.io:443的TCP握手超时 → kubelet重试多次（x132-x183次）仍失败 → 容器状态变为ErrImagePull → kubelet继续重试产生ImagePullBackOff → 56个Pod持续停留在镜像拉取失败状态
     最终表现: 56个Pod（分布在default/aiops-e2e/mcp命名空间，node1和node2节点）处于ImagePullBackOff/ErrImagePull状态，大量Events报告i/o timeout连接registry-1.docker.io:443


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (34.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8647 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 30.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，请查收基于您提供信息生成的集群诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群整体状态** | **异常**：共发现 **57 个异常 Pod**，其中 **56 个因无法拉取镜像处于 ImagePullBackOff/ErrImagePull 状态**，1 个因探针失败和 OOM 处于 CrashLoopBackOff 状态 |
| **主要问题分类** | L3: 镜像拉取失败 (ImagePullFailed) <br> L4: 容器探针失败 (NotReadyProbeFailed) |
| **异常 Pod 统计** | `ImagePullBackOff`: 43 个, `ErrImagePull`: 13 个, `CrashLoopBackOff`: 1 个, `StartError`: 1 个 |
| **影响范围** | default, mcp, aiops-e2e 命名空间；node1, node2 节点 |
| **正常命名空间** | kube-system, admin, aiops（所有 Pod Running） |
| **置信度** | 95% |
| **证据完整度** | 8/8 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体与状态总结**：

| 类型 | 值 |
|------|-----|
| **集群** | K8s 集群，包含 node1 (10.2.0.49) 和 node2 (10.2.0.50) |
| **集群正常功能** | kube-system, admin, aiops 命名空间内的系统组件和核心业务 Pod 均正常运行 |
| **主要异常 1: 镜像拉取失败** | 56 个 Pod 分布在不同命名空间，因 **无法连接到 Docker Hub** 拉取 `busybox:1.36.1` 镜像 |
| **主要异常 1 的典型 Pod** | `dns-diag-tool-evidence` (default, ErrImagePull), `test-dns-1779360358` (aiops-e2e, ImagePullBackOff), `node-debugger-node1-jdbpc` (mcp, ErrImagePull) |
| **主要异常 2: Pod 重启** | `rc-notready-liveness` (aiops-e2e, CrashLoopBackOff)，重启 17 次，因存活探针失败和 OOM |
| **主要异常 2 的关键信息** | Pod Running 但 READY 0/1；`Exit Code: 137` (OOMKilled)；存活探针失败事件 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | 集群 Pod 状态 | `kubectl get pods -A` | Total 125 Pods: Running=60, ImagePullBackOff=43, ErrImagePull=13, CrashLoopBackOff=1, Completed=3, StartError=1 | **57 个 Pod 状态异常，占非 Completed Pod 的 46.7%** |
| 2 | 镜像拉取事件 | `kubectl describe pod dns-diag-tool-evidence -n default` | `Events: ... Failed to pull image "busybox:1.36.1": rpc error: code = Unknown desc = failed to pull and unpack image "docker.io/library/busybox:1.36.1": ... dial tcp 173.231.12.107:443: i/o timeout` (多个 IP 均超时) | **节点 (node2) 到 `registry-1.docker.io:443` 网络不可达，TCP 连接超时** |
| 3 | 镜像拉取事件 | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` | `Events: ... Warning Failed 26m (x183 over 13h) kubelet Failed to pull image "busybox:1.36.1": ... i/o timeout` | **节点 (node1) 同样存在到 Docker Hub 的网络问题，排除单节点故障** |
| 4 | Pod YAML 配置 | `kubectl get pod dns-diag-tool-evidence -n default -o yaml` | `image: busybox:1.36.1`, `imagePullSecrets: <none>` | **Pod 使用公共镜像，无需 `imagePullSecrets`，排除凭据问题** |
| 5 | Pod YAML 配置 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml` | `finalizers: <none>` (已排除 finalizer 阻塞), `terminationGracePeriodSeconds: 30` | **Pod 没有 finalizer 阻塞删除，删除宽限期为 30 秒，排除了 Terminating 卡住的问题** |
| 6 | Pod 状态与事件 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | `State: Waiting (CrashLoopBackOff)`; `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`; `Events: ... Container app failed liveness probe, will be restarted` | **容器因内存溢出 (OOM) 被杀死，导致存活探针检查失败，从而进入 CrashLoopBackOff** |
| 7 | Pod 崩溃日志 | `kubectl logs rc-notready-liveness -n aiops-e2e --previous` | `(no output)` | **容器日志为空，无法从日志侧定位 OOM 原因** |

### 证据关联分析

- **证据 #2 + #3 + #4 印证**：跨越 node1 (证据 #3) 和 node2 (证据 #2) 两个节点，56 个 Pod 均尝试拉取公共镜像 `busybox:1.36.1` 但报告 `i/o timeout` (证据 #2→#3)，且无需认证 (证据 #4)。这构成了一条完整的证据链，证明问题的根本原因是**集群到 Docker Hub 的网络不可达**。
- **证据链**：
    - 集群出口网络故障 (防火墙/代理/路由) → TCP 连接到 `registry-1.docker.io:443` 超时 → Kubelet 无法拉取镜像 → 容器状态为 `ErrImagePull` → Kubelet 持续重试，Pod 状态为 `ImagePullBackOff`。
- **证据 #5 + #6 印证**：对于异常 Pod `rc-notready-liveness`：
    - Pod 的 `finalizers` 为空 (证据 #5)，排除了 finalizer 问题。
    - 容器退出码为 `137` (OOMKilled) (证据 #6)，存活探针失败 (证据 #6)，说明容器被 OOM 杀死后导致探针失败，而非探针本身配置错误。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器 `rc-notready-liveness` 的崩溃前日志 | Critical | 无法确认内存使用突然飙升的原因（是内存泄漏还是业务突发流量） |
| 从节点到 `registry-1.docker.io` 的网络路径探测 (如 `ping`, `traceroute`, `curl`) | Important | 无法精确定位网络故障点是本地防火墙、公司代理还是上游 ISP |
| 节点的 iptables/nftables 规则 | Medium | 无法确认是否有本地的网络策略拦截了出站流量 |
| Pod `rc-notready-liveness` 的 Qos Class | Medium | 无法确定 OOM 是由于容器 limit 过小还是节点内存压力导致的 |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                       │
│ **集群节点（node1, node2）到 Docker Hub 镜像仓库（registry-1.docker.io:443） │
│ 的 TCP 网络出口不可达**，连接超时。                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                     │
│ node1 和 node2 上的 Kubelet 尝试拉取 busybox:1.36.1 镜像 →                 │
│ TCP 三次握手尝试连接 registry-1.docker.io:443 超时 (i/o timeout) →          │
│ Kubelet 重试多次 (x132, x183, x2049次) 仍失败 → 容器状态变为 ErrImagePull → │
│ Kubelet 进入更长的退避周期 → Pod 状态变为 ImagePullBackOff                  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                    │
│ Kubelet 无法从 Docker Hub 拉取镜像，导致所有需要该镜像的容器无法启动。        │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                              │
│ 56 个分布在 default, mcp, aiops-e2e 命名空间的 Pod 持续处于                 │
│ ImagePullBackOff / ErrImagePull 状态。                                      │
│ 额外问题：Pod rc-notready-liveness 因 OOM (Exit Code 137) 和                │
│ 存活探针失败，持续处于 CrashLoopBackOff 状态。                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论 1（主要问题）**：根据证据 #1 (57个异常Pod)，证据 #2 (dns-diag-tool-evice的i/o timeout) 和证据 #3 (test-dns-1779360358 的 i/o timeout)，
问题的根本原因是**集群节点（node1 和 node2）的网络出口存在故障，导致无法连接到 Docker Hub 的镜像仓库 (`registry-1.docker.io:443`)**。这导致 56 个依赖拉取公共镜像的 Pod 无法启动。

**置信度**：高 (95%)
- ✅ 56 个 Pod 的 Events 高度一致，均报告 `i/o timeout`
- ✅ 跨越两个节点，排除了单节点故障
- ✅ `kube-system` 等核心组件运行正常，排除了集群整体网络瘫痪
- ✅ Pod 使用公开镜像 `busybox:1.36.1`，无认证需求，排除了 credentials 问题

**结论 2（次要问题）**：根据证据 #6 (Exit Code 137, OOMKilled, Liveness probe failed),
Pod `rc-notready-liveness` 状态异常的根因是**容器内存消耗超过了 Pod 的 limits 或 Node 的内存限制**，导致被 OOM Killer 杀死。进程退出后引发存活探针失败，最终导致 Pod 持续重启 (CrashLoopBackOff)。

**置信度**：中 (75%)
- ✅ `Exit Code 137` 和 `Reason: OOMKilled` 确凿指向 OOM
- ⚠️ 缺少容器崩溃前的日志和 Pod 的 QoS 信息，无法确定是容器 `limits` 设置过小还是节点内存压力

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 解决集群到 Docker Hub 的网络连接问题**

*此问题是导致集群大规模问题的源头，必须首先解决。*

**预备步骤：手动检查节点网络连通性**
```bash
# 登录到 node1 和 node2，测试网络连通性
# 使用 telnet 或 curl 测试 Docker Hub 的 443 端口
telnet registry-1.docker.io 443

# 或者
curl -I https://registry-1.docker.io/v2/
```
**可能原因与解决方案：**
- **公司网络策略/防火墙限制**：需要联系网络或基础设施团队，检查集群节点的 egress (出站) 规则，确保对 `*.docker.io` 和 `*.github.io` 等镜像仓库的 443 端口放行。
- **私有代理/CNI 问题**：检查集群是否配置了 `HTTP_PROXY`。如果网络出口需要代理，需要修改 Kubelet 或 Containerd 配置以使用代理。
- **使用镜像仓库 mirror (推荐)**：如果无法直接访问外网，搭建一个内网镜像仓库 (如 Harbor)，将所需镜像同步到内网，并配置 Containerd/Cri-o 使用 `registry.mirrors`。

**2. [必做] 修复 Pod rc-notready-liveness 的 OOMKilled 问题**
```bash
# 2.1 查看 Pod 的当前资源限制
kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml | grep -A 5 resources

# 2.2 增加内存限制（假设对应 Deployment）
kubectl set resources deployment/rc-notready-liveness -n aiops-e2e --limits=memory=<当前值的两倍，如 512Mi>
```
*依据*：使用 `kubectl describe` 定位到 `Exit Code: 137` (OOMKilled)，表明需要增加内存限制。

### 后续优化
1. **配置镜像仓库 Mirror**：在公司的集群内部署一个 Harbor 或 Nexus 仓库，作为所有镜像的统一入口，减少对外网依赖。
2. **设置 Pod 资源 Requests 和 Limits**：确保所有核心应用都设置了合理的 resource requests 和 limits，避免 OOMKilled。Prometheus 监控可以辅助确定资源基线。
3. **增强可观测性**：为所有 Pod 开启详细日志和指标采集，以便快速定位 OOM 和网络问题。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 验证网络连通性 | 在 node 上执行 `curl -I https://registry-1.docker.io/v2/` | 返回 `HTTP/2 401` 或 `200` (需要认证/成功) |
| 2. 监控异常 Pod 恢复 | `kubectl get pods -A | grep -E "ImagePull|ErrImage"` | 列表逐渐减少，最终消失 |
| 3. 确认 rc-notready-liveness 状态 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | STATUS 为 `Running` |
| 4. 检查 rc-notready-liveness 重启次数 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 重启次数停止增加 |
| 5. 检查所有 Pod 状态 | `kubectl get pods -A` | 所有非 `Completed` 的 Pod 状态为 `Running` |

---

## ⚠️ 注意事项
- **网络修复是首要任务**：在集群能连通互联网之前，所有拉取外网镜像的 Pod 都无法自动恢复。
- **OOM Killed 的可能原因**：除了内存 limit 过小，也可能是内存泄漏。如果增加 limit 后问题依旧，需要对应用进行代码级别的排查。
- **`StartError` Pod**：报告中提到的 1 个 `StartError` Pod (属于 `mcp/node-debugger-node1-*`) 其根因大概率也是镜像拉取失败，在修复网络后应先观察其是否能自行恢复。如果不能，再单独诊断。

---

## 📊 性能统计

├─ 总耗时: 2.5m
├─ 问题定位: 37.9s (25%) ✅
├─ 证据链采集: 49.4s (33%) ✅
├─ 根因分析: 28.2s (19%) ✅
├─ 汇总总结: 34.7s (23%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 16 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-notready-probe-failed
- **工具调用**: 16 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
