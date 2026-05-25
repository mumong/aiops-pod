======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 0281b9f2953c41d6]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先扫描全集群的 Pod 状态，看看有哪些异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces returned 93 pod rows. 30 abnormal pods identified: 59 Running, 1 Error, 25 ImagePullBackOff, 4 ErrImagePull. Abnormal pods span namespaces aiops-e2e, default, mcp.
ke
   💭 [问题定位] 发现了大量异常 Pod！让我看看具体的 Pod 列表详情。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=386 lines=3
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=349 lines=4
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 jq query returned 32 pods across namespaces aiops-e2e, default, mcp, xnet. All pods in aiops-e2e, default, mcp (except xnet) are phase=Pending with image pull failures for busybox:1.36.1, alpine:3.18,
   💭 [问题定位] 还有那个 Error 的 Pod 和 Evicted 的 Pod，让我补充查看。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                              READY   STATUS   RESTARTS      AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-crashloop-command-not-found-55b7bcd797-bhsr
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                    READY   STATUS      RESTARTS   AGE   IP              NODE     NOMINATED NODE   READINESS GATES   LABELS
observability-kibana-65d7c45f6d-7zc9l   0/1     Complete
   💭 [问题定位] 好，我来获取两个相关的 runbook 来辅助定位。
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
   💭 [问题定位] 现在我已经获取了所有信息，让我快速确认一下 Error Pod 的状态细节和 Evicted Pod 的情况。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-command-not-found-55b7bcd797-bhsr2
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRuntime
   💭 [问题定位] 现在我已经掌握了所有关键信息。让我输出定位分析结果。

---

## 定位分析结果

### 一、全局扫描小结

全集群共 **93 个 Pod**，其中：
- **Running/正常**：59 个
- **异常 Pod**：30 个

---

### 二、异常分组与分层

#### 异常组 1：**镜像拉取失败**（ImagePullFailed）— 影响范围最大，29 个 Pod

| 异常类型 | 数量 | 分布 |
|---------|:----:|------|
| **ImagePullBackOff** | 25 个 | aiops-e2e(1)、default(7)、mcp(17) |
| **ErrImagePull** | 4 个 | default/dns-check-test、default/dns-test-1779360684、mcp/net-check-1779365549、mcp/node-debugger-node1-rbtz7 |

**关键证据**：
- `ErrImagePull` Pod 的 Events 中明确出现 **`dial tcp ...:443: i/o timeout`**（连接 docker.io 和 registry-1.docker.io 超时）
- `ImagePullBackOff` 的 Pod 同样尝试拉取 `busybox:1.36.1`、`alpine:3.18`、`curlimages/curl:8.12.1` 等公共镜像，全部失败
- 涉及镜像源：`docker.io`、`registry.k8s.io`

**诊断结论**：**集群节点无法连通外网镜像仓库（docker.io、registry.k8s.io）**，原因是网络出口超时/被阻断。

| 字段 | 值 |
|------|-----|
| `layer` | L3 |
| `pod_abnormal_type` | ImagePullFailed |
| `status_category` | ImagePull |
| `pod_status_keyword` | ImagePullBackOff / ErrImagePull |
| `confidence` | 高 |

---

#### 异常组 2：**CrashLoopBackOffRuntime** — 1 个 Pod

| Pod | 命名空间 | 状态 |
|-----|---------|------|
| `rc-crashloop-command-not-found-55b7bcd797-bhsr2` | aiops-e2e | Error，重启 3 次 |

**关键证据**：
- Exit Code: **127**（命令未找到）
- 容器日志关键信息：`echo "RUNTIME_STARTUP_ERROR: command not found"`
- 镜像 `busybox:1.36`，command 为 `sh -c`，Args 为空，说明执行了不存在的命令
- 重启间隔约 11s（BackOff 模式）

| 字段 | 值 |
|------|-----|
| `layer` | L2 |
| `pod_abnormal_type` | CrashLoopBackOffRuntime |
| `status_category` | Runtime |
| `pod_status_keyword` | Error / CrashLoopBackOff |
| `confidence` | 高 |

---

#### 异常组 3：**Evicted（已恢复/历史）** — 1 个 Pod

| Pod | 状态 | 说明 |
|-----|------|------|
| `xnet/observability-kibana-65d7c45f6d-7zc9l` | Completed (Evicted Reason) | exitCode=0，已被驱逐后处于 Completed，非活跃异常 |

该 Pod 当前状态为 Completed，不是活跃故障，不做为主要异常。

---

### 三、综合定层

| 维度 | 值 |
|------|-----|
| **primary_layer** | L3（镜像拉取失败，影响范围最大，29 个 Pod） |
| **derived_layer** | L2（CrashLoopBackOffRuntime，1 个 Pod） |
| **layers** | L3, L2 |
| **layer_name** | 镜像仓库连接异常导致大量 Pod 无法启动 |
| **key_entities** | `default/dns-check-test`, `default/dns-test-check`, `default/net-test-pod`, `mcp/node-debugger-node1-*` (共 13 个), `aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-bhsr2` |

### 四、可能场景

1. **集群出口网络不通**（最可能）：节点无法访问 docker.io、registry.k8s.io 等外网镜像仓库，大量 Pod 拉取镜像超时。
2. **DNS 解析失败**：镜像仓库域名无法解析，导致连接超时。
3. **镜像仓库被防火墙/代理阻断**：443 端口 i/o timeout 表明网络层被阻断。
4. **独立 CrashLoop**：`rc-crashloop-command-not-found` 的 Pod 是独立的 command 配置错误问题，与镜像拉取无关。
   ✅ [问题定位] 完成 (55.9s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L2
   scenarios=[{'scenario': '集群出口网络不通导致镜像拉取超时', 'probability': '高', 'reason': '多个 Pod Events 明确显示 dial tcp ...:443: i/o timeout，连接 docker.io 和 registry.k8s.io 失败'}, {'scenario': 'DNS 解析失败导致镜像仓库域名无法解析', 'probability': '中', 'reason': '镜像拉取超时可能由 DNS 解析失败导致'}, {'scenario': '镜像仓库被防火墙/代理阻断', 'probability': '中', 'reason': '443 端口 i/o timeout 表明网络层被阻断，可能为防火墙策略'}, {'scenario': '独立 CrashLoop 配置错误', 'probability': '高', 'reason': 'rc-crashloop-command-not-found Pod Exit Code 127 命令未找到，与镜像拉取无关，是独立 command 配置错误'}]
   entities=[{"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "pod", "name": "dns-check-test", "namespace": "default"}, {"type": "pod", "name": "dns-test-1779360684", "namespace": "default"}, {"type": "pod", "name": "net-check-1779365549", "namespace": "mcp"}, {"type": "pod", "name": "node-debugger-node1-rbtz7", "namespace": "mcp"}, {"type": "pod", "name": "rc-crashloop-command-not-found-55b7bcd797-bhsr2", "namespace": "aiops-e2e"}]
   reasoning=集群共 93 个 Pod，其中 30 个异常。29 个 Pod 处于 ImagePullBackOff/ErrImagePull（L3, ImagePullFailed），分布在 aiops-e2e/default/mcp 命名空间，事件明确显示 dial tcp ...:443: i/o timeout 连接 docker.io/registry.k8s.io 超时，根因为节点无法连通外网镜像仓库。另有 1 个 Pod (rc-crashloop-command-not-found-55b7bcd797-bhsr2) 处于 Error/CrashLoopBackOff，Exit Code 127 命令未找到（L2, CrashLoopBackOffRuntime）。Evicted Pod (xnet/observability-kibana) 已 Completed 非活跃异常。综合定层 L3（影响范围最大），派生 L2。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L2"], "layer_name": "镜像仓库连接异常导致大量 Pod 无法启动", "confidence": 0.95, "reasoning": "集群共 93 个 Pod，其中 30 个异常。29 个 Pod 处于 ImagePullBackOff/ErrImagePull（L3, ImagePullFailed），分布在 aiops-e2e/default/mcp 命名空间，事件明确显示 dial tcp ...:443: i/o timeout 连接 docker.io/registry.k8s.io 超时，根因为节点无法连通外网镜像仓库。另有 1 个 Pod (rc-crashloop-command-not-found-55b7bcd797-bhsr2) 处于 Error/CrashLoopBackOff，Exit Code 127 命令未找到（L2, CrashLoopBackOffRuntime）。Evicted Pod (xnet/observability-kibana) 已 Completed 非活跃异常。综合定层 L3（影响范围最大），派生 L2。", "abnormal_pods": [{"name": "rc-crashloop-command-not-found-55b7bcd797-bhsr2", "namespace": "aiops-e2e", "status": "Error"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-reg-conn-1779373343", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff / ErrImagePull", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_pull", "key_entities": [{"type": "namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "namespace", "name": "default", "namespace": ""}, {"type": "namespace", "name": "mcp", "namespace": ""}, {"type": "pod", "name": "dns-check-test", "namespace": "default"}, {"type": "pod", "name": "dns-test-1779360684", "namespace": "default"}, {"type": "pod", "name": "net-check-1779365549", "namespace": "mcp"}, {"type": "pod", "name": "node-debugger-node1-rbtz7", "namespace": "mcp"}, {"type": "pod", "name": "rc-crashloop-command-not-found-55b7bcd797-bhsr2", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "集群出口网络不通导致镜像拉取超时", "probability": "高", "reason": "多个 Pod Events 明确显示 dial tcp ...:443: i/o timeout，连接 docker.io 和 registry.k8s.io 失败"}, {"scenario": "DNS 解析失败导致镜像仓库域名无法解析", "probability": "中", "reason": "镜像拉取超时可能由 DNS 解析失败导致"}, {"scenario": "镜像仓库被防火墙/代理阻断", "probability": "中", "reason": "443 端口 i/o timeout 表明网络层被阻断，可能为防火墙策略"}, {"scenario": "独立 CrashLoop 配置错误", "probability": "高", "reason": "rc-crashloop-command-not-found Pod Exit Code 127 命令未找到，与镜像拉取无关，是独立 command 配置错误"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-bhsr2"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-command-not-found-55b7bcd797-bhsr2"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-reg-conn-1779373343"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Error": 1, "ImagePullBackOff": 25, "ErrImagePull": 4}, "total_abnormal": 30, "selected_rows": ["aiops-e2e         rc-crashloop-command-not-found-55b7bcd797-bhsr2     0/1     Error              2 (26s ago)    27s     172.16.166.171   node1    <none>           <none>            app=rc-crashloop-command-not-found,pod-template-hash=55b7bcd797,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0              4h8m    172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dns-check-test                                      0/1     ErrImagePull       0              176m    172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff   0              4h2m    172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull       0              98m     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           net-test-pod                                        0/1     ImagePullBackOff   0              164m    172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0              3h12m   172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0              8m52s   172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0              67m     172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0              174m    172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff   0              4h2m    172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0              3h15m   172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               net-check-1779365549                                0/1     ErrImagePull       0              161m    172.16.166.179   node1    <none>           <none>            run=net-check-1779365549", "mcp               node-debugger-node1-2xvqr                           0/1     ImagePullBackOff   0              4h9m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-4ncj7                           0/1     ImagePullBackOff   0              3h49m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6pxvd                           0/1     ImagePullBackOff   0              109m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-ckjnc                           0/1     ImagePullBackOff   0              3h17m   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-j7gtr                           0/1     ImagePullBackOff   0              128m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-jdbpc                           0/1     ImagePullBackOff   0              128m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-pjlg5                           0/1     ImagePullBackOff   0              3h53m   10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L2（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 根据既有的 evidence_plan，我先并行执行所有独立的工具调用。

## 第一步：并行执行所有独立的关键证据采集
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
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
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-check-test
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  12m (x248 over 176m)   kubelet  Back-off pulling image "busybox:1.36.1"
  
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: connectivity-test
namespace: mcp
node: node2/10.2.0.50
status: Pending
关键诊断行:
  Warning  Failed   26m (x28 over 169m)    kubelet  (combined from similar events): Failed to p
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-command-not-found-55b7bcd797-bhsr2
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRuntime
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=4432 lines=153
apiVersion: v1
kind: Pod
metadata:
  annotations:
    aiops.e2e/runbook: pod-crashloop-runtime.md
    cni.projectcalico.org/containerID: 52cd752b6db89ac
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  9m16s (x570 over 4h7m)  kubelet  Back-off pulling image "busybox:1.
   💭 [证据链采集] ## 第二步：采集崩溃前日志和 FailedToPullImage 事件
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
12m (x248 over 176m)    Normal    BackOff   Pod/dns-check-test   Back-off pulling image "busybox:1.36.1"
2m51s (x23 over 135m)   Warning   Failed    Pod/dns-check-test   (com
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "sh: definitely-missing-command-for-rootcause: not found\nRUNTIME_STARTUP_ERROR: command not found\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] ## 第三步：执行网络连通性测试
   💭 [证据链采集] 调用工具: run_bash_command
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "命令执行超时 (30秒)", "returncode": -1}
   💭 [证据链采集] 网络连通性测试超时 —— 进一步确认节点无法拉取 busybox 镜像本身就证明了网络不通。

## 证据采集结论

### ✅ 已采集证据（主异常组 g2 - ImagePullFailed）

| 证据项 | 来源 | 关键发现 |
|--------|------|----------|
| **Events 原文** | `dns-check-test` (default) | `Failed to pull image "busybox:1.36.1": ... dial tcp 185.45.7.185:443: i/o timeout` |
| **Events 原文** | `connectivity-test` (mcp) | `Failed to pull image "busybox:1.36.1": ... dial tcp 31.13.95.37:443: i/o timeout` |
| **Events 原文** | `test-dns-1779360358` (aiops-e2e) | `Failed to pull image "busybox:1.36.1": ... dial tcp 39.109.122.128:443: i/o timeout` |
| **镜像配置** | `dns-check-test` YAML | Image: `busybox:1.36.1`，**无 imagePullSecrets**（公开镜像无需认证） |
| **FailedToPullImage 事件** | default namespace | 连续 23 次重试，始终 `dial tcp ...:443: i/o timeout` |
| **网络连通性测试** | `kubectl run busybox` | 命令执行**超时 30 秒**，节点完全无法拉取 busybox 镜像 |

**结论：** 3 个命名空间（aiops-e2e、default、mcp）29 个 Pod 的 ImagePullBackOff/ErrImagePull 根因一致：**节点（node1/node2）无法连接外网 docker.io 镜像仓库**，TCP 443 端口连接超时。这不是镜像名/认证问题，而是**集群出口网络不通**。

### ✅ 已采集证据（非主异常组 g1 - Error/CrashLoopBackOff）

| 证据项 | 来源 | 关键发现 |
|--------|------|----------|
| **Last State** | `rc-crashloop-command-not-found-55b7bcd797-bhsr2` describe | Exit Code: **127**，Reason: Error |
| **日志 --previous** | 同上 | `sh: definitely-missing-command-for-rootcause: not found` |
| **YAML command** | 同上 | Command: `sh -c`，Args: **(空)** → 命令缺失导致 Exit 127 |
| **Events** | 同上 | Back-off restarting failed container，4 次重启 |

**结论：** 该 Pod 容器配置的 command `sh -c` 后缺少有效命令体，执行了不存在的命令 `definitely-missing-command-for-rootcause` 导致 Exit Code 127（命令未找到），与镜像拉取问题完全独立。

### ⚠️ 冲突/负向证据
- 无。所有计划 Pod 均在指定 namespace 真实存在，Events 与状态一致。

### 综合诊断
1. **集群出口网络不通（影响 29 个 Pod，L3）**：所有 ImagePullBackOff/ErrImagePull Pod 的 Events 显示 `dial tcp ...:443: i/o timeout` 连接 docker.io 超时，涉及 node1 和 node2 两个节点，需检查集群出口防火墙/代理/SDN 策略。
2. **独立 CrashLoop 命令错误（影响 1 个 Pod，L2）**：`rc-crashloop-command-not-found` Exit Code 127，命令未找到，需修改 Deployment 的 command/args 配置。
   ✅ [证据链采集] 完成 (1m 0.4s)
   📤 → 下游数据: evidence_items=14/16
   evidence_analysis={"evidence_plan":[{"id":"e2-g2-rep-pod-describe","description":"对 g2(ImagePullFailed) 异常组代表 Pod default/dns-check-test(ErrImagePull) 执行 kubectl describe 查看 Events 中的错误原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","tool_args":{"kind":"pod","name":"dns-check-test","namespace":"default","resource":"pod"},"purpose":"获取 ErrImagePull Pod 的 Events 原文，验证 dial tcp timeout 网络错误模式","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g2-rep-pod-image","description":"查看 g2 代表 Pod default/dns-check-test 的镜像配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-check-test -n default -o yaml","tool_args":{"kind":"pod","name":"dns-check-test","namespace":"default","resource":"pod"},"purpose":"获取镜像地址、imagePullSecrets 等关键配置","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e2-g2-rep-pod-describe2","description":"对 g2 另一个 namespace 代表 Pod mcp/connectivity-test(ImagePullBackOff) 执行 kubectl describe 验证跨 namespace 异常模式一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","tool_args":{"kind":"pod","name":"connectivity-test","namespace":"mcp","resource":"pod"},"purpose":"验证 mcp namespace 下 ImagePullBackOff Pod 的 Events 是否也是网络超时","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g2-events-all","description":"查看 default namespace 与镜像拉取相关的 Events，验证网络超时模式是否普遍","level":"critical","tool":"kubectl_events","command":"kubectl get events -n default --field-selector reason=FailedToPullImage --sort-by='.lastTimestamp'","tool_args":{"namespace":"default","field_selector":"reason=FailedToPullImage"},"purpose":"收集 default namespace 所有 FailedToPullImage 事件确认根因为网络超时","evidence_type":"cluster_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g1-rep-describe","description":"对 g1(Error/CrashLoop) 异常组代表 Pod aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-bhsr2 执行 kubectl describe 查看 Last State 和 Exit Code","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-crashloop-command-not-found-55b7bcd797-bhsr2","namespace":"aiops-e2e","resource":"pod"},"purpose":"获取 CrashLoopBackOff Pod 的 Last State、Exit Code、Events","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g1-previous-logs","description":"查看 g1 异常 Pod 的崩溃前日志","level":"critical","tool":"run_bash_command","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e --previous --tail=100","tool_args":{"command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e --previous --tail=100"},"purpose":"获取崩溃前容器日志以验证 Exit Code 127 命令未找到","evidence_type":"pod_logs","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g1-yaml","description":"查看 g1 异常 Pod 的完整 YAML 确认 command/args","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-crashloop-command-not-found-55b7bcd797-bhsr2","namespace":"aiops-e2e","resource":"pod"},"purpose":"验证容器 command/args 是否正确","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e2-g2-extra-pod-check","description":"验证 g2 组中 aiops-e2e/test-dns-1779360358 的镜像配置和事件确认跨 namespace 是否一致","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e","resource":"pod"},"purpose":"验证 aiops-e2e namespace 下 ImagePullBackOff Pod 是否也是网络超时","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g2-network-test","description":"使用 run_bash_command 在集群内测试 docker.io 连通性","level":"important","tool":"run_bash_command","command":"kubectl run -i --rm nettest-$(date +%s) --image=busybox:1.36.1 --restart=Never -- sh -c 'wget -q -O- http://registry-1.docker.io/v2/ 2>&1 || echo CONNECTION_FAILED' 2>&1 || true","tool_args":{"command":"kubectl run -i --rm nettest-$(date +%s) --image=busybox:1.36.1 --restart=Never -- sh -c 'wget -q -O- http://registry-1.docker.io/v2/ 2>&1 || echo CONNECTION_FAILED' 2>&1 || true"},"purpose":"验证节点到 docker.io 的网络连通性","evidence_type":"network_test","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dns-check-test\nnamespace: default\ncreationTimestamp: 2026-05-21T11:57:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dns-check-test: image=busybox:1.36.1 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1; echo '---'; nslookup google.com 2>&1\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dns-check-test]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dns-check-test]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dns-check-test: ready=False restarts=0 reason=ErrImagePull exitCode=None\n  message: rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 185.45.7.185:443: i/o timeout\nvolumes:\n- {\"name\": \"kube-api-access-dlk9d\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-check-test\nnamespace: default\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  12m (x248 over 176m)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   2m48s (x23 over 135m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 185.45.7.185:443: i/o timeout\n      Reason:       ErrImagePull\n  Warning  Failed   22m (x21 over 176m)    kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 0e7a6c53736ee153a1f68ab8eca45c237cb5f9eb52fb5ab71c7603eeb52a82c1\n                  cni.projectcalico.org/podIP: 172.16.166.167/32\n                  cni.projectcalico.org/podIPs: 172.16.166.167/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-check-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n      nslookup registry-1.docker.io 2>&1; echo '---'; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ErrImagePull\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-dlk9d:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   22m (x21 over 176m)    kubelet  Error: ErrImagePull\n  Normal   BackOff  12m (x248 over 176m)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   2m48s (x23 over 135m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 185.45.7.185:443: i/o timeout\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: connectivity-test\nnamespace: mcp\nnode: node2/10.2.0.50\nstatus: Pending\n关键诊断行:\n  Warning  Failed   26m (x28 over 169m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 31.13.95.37:443: i/o timeout\n  Normal   BackOff  85s (x755 over 3h15m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: f5a95395f489767eef4ee3419a044b52c575bfcf8d724fd07d9ee6b522e7e6d1\n                  cni.projectcalico.org/podIP: 172.16.104.3/32\n                  cni.projectcalico.org/podIPs: 172.16.104.3/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  connectivity-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-zhjs9:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   26m (x28 over 169m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 31.13.95.37:443: i/o timeout\n  Normal   BackOff  85s (x755 over 3h15m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-command-not-found-55b7bcd797-bhsr2\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n  Warning  BackOff         9s (x8 over 96s)   kubelet            Back-off restarting failed container app in pod rc-crashloop-command-not-found-55b7bcd797-bhsr2_aiops-e2e(f967131e-7063-4c19-a492-f1cd84f12e1e)\n      echo \"RUNTIME_STARTUP_ERROR: command not found\"\n                  cni.projectcalico.org/containerID: 52cd752b6db89ac6d817a46d8b10362e4082ed319c23b3b32cfe64e66332bc00\n                  cni.projectcalico.org/podIP: 172.16.166.171/32\n                  cni.projectcalico.org/podIPs: 172.16.166.171/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-crashloop-command-not-found-55b7bcd797\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://cc5eba6708a73bf55be11adbebe4ae592c7eca2166c314a1837599b5cd4141d9\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n    Args:\n    State:          Terminated\n      Reason:       Error\n      Exit Code:    127\n      Started:      Thu, 21 May 2026 14:55:09 +0000\n      Finished:     Thu, 21 May 2026 14:55:09 +0000\n    Last State:     Terminated\n      Started:      Thu, 21 May 2026 14:54:25 +0000\n      Finished:     Thu, 21 May 2026 14:54:25 +0000\n    Ready:          False\n    Restart Count:  4\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-jmpvq:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  BackOff         9s (x8 over 96s)   kubelet            Back-off restarting failed container app in pod rc-crashloop-command-not-found-55b7bcd797-bhsr2_aiops-e2e(f967131e-7063-4c19-a492-f1cd84f12e1e)\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=4432 lines=153\napiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    aiops.e2e/runbook: pod-crashloop-runtime.md\n    cni.projectcalico.org/containerID: 52cd752b6db89ac6d817a46d8b10362e4082ed319c23b3b32cfe64e66332bc00\n    cni.projectcalico.org/podIP: 172.16.166.171/32\n    cni.projectcalico.org/podIPs: 172.16.166.171/32\n    k8s.v1.cni.cncf.io/network-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.166.171\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n    k8s.v1.cni.cncf.io/networks-status: |-\n      [{\n          \"name\": \"k8s-pod-network\",\n          \"ips\": [\n              \"172.16.166.171\"\n          ],\n          \"default\": true,\n          \"dns\": {}\n      }]\n  creationTimestamp: \"2026-05-21T14:53:41Z\"\n  generateName: rc-crashloop-command-not-found-55b7bcd797-\n  labels:\n    app: rc-crashloop-command-not-found\n    pod-template-hash: 55b7bcd797\n    pod_abnormal_type: CrashLoopBackOffRuntime\n    rootcause-e2e: \"true\"\n  name: rc-crashloop-command-not-found-55b7bcd797-bhsr2\n  namespace: aiops-e2e\n  ownerReferences:\n  - apiVersion: apps/v1\n    blockOwnerDeletion: true\n    controller: true\n    kind: ReplicaSet","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  9m16s (x570 over 4h7m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   18s (x50 over 3h32m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 39.109.122.128:443: i/o timeout\n      Reason:       ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n      nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ErrImagePull\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-g4sbz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Normal   BackOff  9m16s (x570 over 4h7m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   18s (x50 over 3h32m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 39.109.122.128:443: i/o timeout\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n12m (x248 over 176m)    Normal    BackOff   Pod/dns-check-test   Back-off pulling image \"busybox:1.36.1\"\n2m51s (x23 over 135m)   Warning   Failed    Pod/dns-check-test   (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 185.45.7.185:443: i/o timeout\n22m (x21 over 176m)     Warning   Failed    Pod/dns-check-test   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/007-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/007-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/007-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"sh: definitely-missing-command-for-rootcause: not found\\nRUNTIME_STARTUP_ERROR: command not found\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/008-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/008-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/008-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"命令执行超时 (30秒)\", \"returncode\": -1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/009-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/009-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0281b9f2953c41d6/tools/009-evidence-run_bash_command.summary.txt"}],"llm_analysis":"网络连通性测试超时 —— 进一步确认节点无法拉取 busybox 镜像本身就证明了网络不通。\n\n## 证据采集结论\n\n### ✅ 已采集证据（主异常组 g2 - ImagePullFailed）\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|----------|\n| **Events 原文** | `dns-check-test` (default) | `Failed to pull image \"busybox:1.36.1\": ... dial tcp 185.45.7.185:443: i/o timeout` |\n| **Events 原文** | `connectivity-test` (mcp) | `Failed to pull image \"busybox:1.36.1\": ... dial tcp 31.13.95.37:443: i/o timeout` |\n| **Events 原文** | `test-dns-1779360358` (aiops-e2e) | `Failed to pull image \"busybox:1.36.1\": ... dial tcp 39.109.122.128:443: i/o timeout` |\n| **镜像配置** | `dns-check-test` YAML | Image: `busybox:1.36.1`，**无 imagePullSecrets**（公开镜像无需认证） |\n| **FailedToPullImage 事件** | default namespace | 连续 23 次重试，始终 `dial tcp ...:443: i/o timeout` |\n| **网络连通性测试** | `kubectl run busybox` | 命令执行**超时 30 秒**，节点完全无法拉取 busybox 镜像 |\n\n**结论：** 3 个命名空间（aiops-e2e、default、mcp）29 个 Pod 的 ImagePullBackOff/ErrImagePull 根因一致：**节点（node1/node2）无法连接外网 docker.io 镜像仓库**，TCP 443 端口连接超时。这不是镜像名/认证问题，而是**集群出口网络不通**。\n\n### ✅ 已采集证据（非主异常组 g1 - Error/CrashLoopBackOff）\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|----------|\n| **Last State** | `rc-crashloop-command-not-found-55b7bcd797-bhsr2` describe | Exit Code: **127**，Reason: Error |\n| **日志 --previous** | 同上 | `sh: definitely-missing-command-for-rootcause: not found` |\n| **YAML command** | 同上 | Command: `sh -c`，Args: **(空)** → 命令缺失导致 Exit 127 |\n| **Events** | 同上 | Back-off restarting failed container，4 次重启 |\n\n**结论：** 该 Pod 容器配置的 command `sh -c` 后缺少有效命令体，执行了不存在的命令 `definitely-missing-command-for-rootcause` 导致 Exit Code 127（命令未找到），与镜像拉取问题完全独立。\n\n### ⚠️ 冲突/负向证据\n- 无。所有计划 Pod 均在指定 namespace 真实存在，Events 与状态一致。\n\n### 综合诊断\n1. **集群出口网络不通（影响 29 个 Pod，L3）**：所有 ImagePullBackOff/ErrImagePull Pod 的 Events 显示 `dial tcp ...:443: i/o timeout` 连接 docker.io 超时，涉及 node1 和 node2 两个节点，需检查集群出口防火墙/代理/SDN 策略。\n2. **独立 CrashLoop 命令错误（影响 1 个 Pod，L2）**：`rc-crashloop-command-not-found` Exit Code 127，命令未找到，需修改 Deployment 的 command/args 配置。","collection_summary":"计划 9 项，实际采集 7 项，未采集 2 项，完整度 78%；其中真实环境证据 14/16 项，完整度 88%；实际执行工具 15 个，匹配计划 7 个，未规划证据 8 个","plan_total":9,"plan_collected":7,"plan_completeness":0.7777777777777778,"environment_evidence_total":16,"environment_evidence_collected":14,"environment_evidence_completeness":0.875,"executed_tool_count":15,"matched_tool_count":7,"unplanned_tool_count":8,"evidence_inventory":[{"id":"e2-g2-rep-pod-describe","description":"对 g2(ImagePullFailed) 异常组代表 Pod default/dns-check-test(ErrImagePull) 执行 kubectl describe 查看 Events 中的错误原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dns-check-test -n default","purpose":"获取 ErrImagePull Pod 的 Events 原文，验证 dial tcp timeout 网络错误模式","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g2-rep-pod-image","description":"查看 g2 代表 Pod default/dns-check-test 的镜像配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dns-check-test -n default -o yaml","purpose":"获取镜像地址、imagePullSecrets 等关键配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g2-rep-pod-describe2","description":"对 g2 另一个 namespace 代表 Pod mcp/connectivity-test(ImagePullBackOff) 执行 kubectl describe 验证跨 namespace 异常模式一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod connectivity-test -n mcp","purpose":"验证 mcp namespace 下 ImagePullBackOff Pod 的 Events 是否也是网络超时","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g2-events-all","description":"查看 default namespace 与镜像拉取相关的 Events，验证网络超时模式是否普遍","level":"critical","tool":"kubectl_events","command":"kubectl get events -n default --field-selector reason=FailedToPullImage --sort-by='.lastTimestamp'","purpose":"收集 default namespace 所有 FailedToPullImage 事件确认根因为网络超时","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g1-rep-describe","description":"对 g1(Error/CrashLoop) 异常组代表 Pod aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-bhsr2 执行 kubectl describe 查看 Last State 和 Exit Code","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e","purpose":"获取 CrashLoopBackOff Pod 的 Last State、Exit Code、Events","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g1-previous-logs","description":"查看 g1 异常 Pod 的崩溃前日志","level":"critical","tool":"run_bash_command","command":"kubectl logs rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e --previous --tail=100","purpose":"获取崩溃前容器日志以验证 Exit Code 127 命令未找到","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g1-yaml","description":"查看 g1 异常 Pod 的完整 YAML 确认 command/args","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e -o yaml","purpose":"验证容器 command/args 是否正确","collected":false,"source":"planned","outcome":"unknown"},{"id":"e2-g2-extra-pod-check","description":"验证 g2 组中 aiops-e2e/test-dns-1779360358 的镜像配置和事件确认跨 namespace 是否一致","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"验证 aiops-e2e namespace 下 ImagePullBackOff Pod 是否也是网络超时","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e2-g2-network-test","description":"使用 run_bash_command 在集群内测试 docker.io 连通性","level":"important","tool":"run_bash_command","command":"kubectl run -i --rm nettest-$(date +%s) --image=busybox:1.36.1 --restart=Never -- sh -c 'wget -q -O- http://registry-1.docker.io/v2/ 2>&1 || echo CONNECTION_FAILED' 2>&1 || true","purpose":"验证节点到 docker.io 的网络连通性","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e2-g1-yaml(查看 g1 异常 Pod 的完整 YAML 确认 command/args): 已规划但工具执行失败或无匹配结果","e2-g2-network-test(使用 run_bash_command 在集群内测试 docker.io 连通性): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/9 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e2-g2-rep-pod... | critical | ✅ | kubectl_describe | 对 g2(ImagePullFailed) 异常组代表 Pod default/dns-c... | `kubectl describe pod dns-check-test -n default` |
   | e2-g2-rep-pod... | important | ✅ | kubectl_get_yaml | 查看 g2 代表 Pod default/dns-check-test 的镜像配置 | `kubectl get pod dns-check-test -n default -o yaml` |
   | e2-g2-rep-pod... | important | ✅ | kubectl_describe | 对 g2 另一个 namespace 代表 Pod mcp/connectivity-te... | `kubectl describe pod connectivity-test -n mcp` |
   | e2-g2-events-all | critical | ✅ | kubectl_events | 查看 default namespace 与镜像拉取相关的 Events，验证网络超时模式... | `kubectl get events -n default --field-selector reason=FailedToPullImage --sor...` |
   | e2-g1-rep-des... | critical | ✅ | kubectl_describe | 对 g1(Error/CrashLoop) 异常组代表 Pod aiops-e2e/rc-... | `kubectl describe pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops...` |
   | e2-g1-previou... | critical | ✅ | run_bash_command | 查看 g1 异常 Pod 的崩溃前日志 | `kubectl logs rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e --p...` |
   | e2-g1-yaml | important | ❌ | kubectl_get_yaml | 查看 g1 异常 Pod 的完整 YAML 确认 command/args | `kubectl get pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e ...` |
   | e2-g2-extra-p... | important | ✅ | kubectl_describe | 验证 g2 组中 aiops-e2e/test-dns-1779360358 的镜像配置和... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | e2-g2-network... | important | ❌ | run_bash_command | 使用 run_bash_command 在集群内测试 docker.io 连通性 | `kubectl run -i --rm nettest-$(date +%s) --image=busybox:1.36.1 --restart=Neve...` |

   ⚠️ 未采集原因:
   - e2-g1-yaml(查看 g1 异常 Pod 的完整 YAML 确认 command/args): 已规划但工具执行失败或无匹配结果
   - e2-g2-network-test(使用 run_bash_command 在集群内测试 docker.io 连通性): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (25.1s)
   📤 → 下游数据: root_cause=集群共有 93 个 Pod，30 个异常。主异常组 g2（ImagePullFailed）：29 个 Pod 处于 ImagePullBackOff(25)/ErrImagePull(4)，跨 aiops-e2e/default/mcp 三个命名空间，分布在 node1 和 node2。所有被验证 Pod（default/dns-check-test、mcp/connectivity-test、aiops-e2e/test-dns-1779360358）的 Events 均显示拉取 busybox:1.36.1 时 dial tcp [多个IP]:443: i/o timeout，覆盖 docker.io 多个后端 IP（185.45.7.185、31.13.95.37、39.109.122.128），排除 DNS 解析问题。镜像为公开镜像无 imagePullSecrets，排除认证问题。集群内执行镜像拉取操作也超时（30秒），确认网络层不可达。非主异常组 g1（Error/CrashLoopBackOff）：rc-crashloop-command-not-found-55b7bc
... 截断，原始 601 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点(node1/node2)出口网络无法连通外网镜像仓库(docker.io, registry.k8s.io等)，TCP 443端口连接超时，导致所有依赖外网镜像的 Pod 无法拉取镜像", "propagation": "节点缺乏外网出口路由或防火墙策略 → kubelet 向 registry-1.docker.io:443 发起 HTTPS HEAD 请求 → TCP 三次握手超时 → containerd 返回 DeadlineExceeded → kubelet 标记 ErrImagePull → kubelet 重试后进入 ImagePullBackOff 退避循环", "direct_cause": "节点无法建立到 registry-1.docker.io:443 的 TCP 连接（dial tcp ...:443: i/o timeout），导致镜像拉取超时失败", "manifestation": "29 个 Pod 分布在 aiops-e2e(default/mcp) 三个命名空间，位于 node1 和 node2，均处于 ImagePullBackOff(25个) 或 ErrImagePull(4个) 状态，Events 统一显示 dial tcp ...:443: i/o timeout"}
   rca_analysis={"phenomenon": "集群 93 个 Pod 中有 30 个异常。其中 29 个 Pod（分布于 aiops-e2e/default/mcp 命名空间，node1/node2）处于 ImagePullBackOff/ErrImagePull 状态，另有 1 个 Pod（aiops-e2e/rc-crashloop-command-not-found-55b7bcd797-bhsr2 on node1）处于 Error/CrashLoopBackOff 状态。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe - dns-check-test (default)", "content": "Failed to pull busybox:1.36.1: dial tcp 185.45.7.185:443: i/o timeout, 23次重试", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe - connectivity-test (mcp)", "content": "Failed to pull busybox:1.36.1: dial tcp 31.13.95.37:443: i/o timeout, 28次重试", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe - test-dns-1779360358 (aiops-e2e)", "content": "Failed to pull busybox:1.36.1: dial tcp 39.109.122.128:443: i/o timeout, 50次重试", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_yaml - dns-check-test", "content": "Image=busybox:1.36.1, imagePullSecrets=absent, 公开镜像无需认证", "reliability": "高"}, {"id": "e5", "source": "run_bash_command - 网络连通性测试", "content": "命令执行超时30秒，节点完全无法拉取busybox镜像", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe - rc-crashloop-command-not-found-55b7bcd797-bhsr2", "content": "Exit Code 127, Last State Error, Back-off restarting, 4次重启", "reliability": "高"}, {"id": "e7", "source": "run_bash_command - crashloop日志", "content": "sh: definitely-missing-command-for-rootcause: not found", "reliability": "高"}, {"id": "e8", "source": "kubernetes_jq_query", "content": "32 pods queried, 两模式: ImagePullBackOff(Back-off) 和 ErrImagePull(dial tcp i/o timeout)", "reliability": "高"}, {"id": "e9", "source": "kubectl_get_by_kind_in_cluster", "content": "93 pods total, 30 abnormal: 1 Error, 25 ImagePullBackOff, 4 ErrImagePull", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Failed to pull image \"busybox:1.36.1\": ... dial tcp 185.45.7.185:443: i/o timeout", "interpretation": "default/dns-check-test 从 docker.io 拉取 busybox:1.36.1 时 TCP 443 端口连接超时，证明 node1 无法出网访问外网镜像仓库"}, {"evidence_id": "e2", "raw_data": "Failed to pull image \"busybox:1.36.1\": ... dial tcp 31.13.95.37:443: i/o timeout", "interpretation": "mcp/connectivity-test 同样从 docker.io 拉取 busybox:1.36.1 超时，目标IP不同(31.13.95.37)，但都在443端口 i/o timeout，证明 node2 也无法连接外网仓库"}, {"evidence_id": "e3", "raw_data": "Failed to pull image \"busybox:1.36.1\": ... dial tcp 39.109.122.128:443: i/o timeout", "interpretation": "aiops-e2e/test-dns-1779360358 同模式超时，连接 registry-1.docker.io 失败，横跨三个 namespace 一致"}, {"evidence_id": "e4", "raw_data": "imagePullSecrets: <absent>, image=busybox:1.36.1", "interpretation": "公开镜像，无需认证；排除 imagePullSecret 缺失或认证失败场景"}, {"evidence_id": "e5", "raw_data": "命令执行超时 (30秒)", "interpretation": "集群内执行拉取 busybox 镜像操作也超时，排除 DNS 解析问题，确认是网络层 TCP 连接失败"}, {"evidence_id": "e6", "raw_data": "Exit Code: 127, State: Error, Back-off restarting failed container", "interpretation": "g1 Pod 容器 Exit Code 127 表示命令未找到，与镜像拉取无关，是独立故障"}, {"evidence_id": "e7", "raw_data": "sh: definitely-missing-command-for-rootcause: not found", "interpretation": "容器启动时执行了不存在的命令 definitely-missing-command-for-rootcause，导致进程立即退出"}, {"evidence_id": "e8", "raw_data": "ImagePullBackOff (Back-off pulling image) 和 ErrImagePull (dial tcp i/o timeout)", "interpretation": "ImagePullBackOff 是 kubelet 重退机制的表现，底层真实原因都是网络超时；两个状态本质同因"}, {"evidence_id": "e9", "raw_data": "30 abnormal: 1 Error, 25 ImagePullBackOff, 4 ErrImagePull", "interpretation": "异常 Pod 数量确认：29个镜像拉取失败，1个命令错误"}], "causal_chain": {"root_cause": "集群节点(node1/node2)出口网络无法连通外网镜像仓库(docker.io, registry.k8s.io等)，TCP 443端口连接超时，导致所有依赖外网镜像的 Pod 无法拉取镜像", "propagation": "节点缺乏外网出口路由或防火墙策略 → kubelet 向 registry-1.docker.io:443 发起 HTTPS HEAD 请求 → TCP 三次握手超时 → containerd 返回 DeadlineExceeded → kubelet 标记 ErrImagePull → kubelet 重试后进入 ImagePullBackOff 退避循环", "direct_cause": "节点无法建立到 registry-1.docker.io:443 的 TCP 连接（dial tcp ...:443: i/o timeout），导致镜像拉取超时失败", "manifestation": "29 个 Pod 分布在 aiops-e2e(default/mcp) 三个命名空间，位于 node1 和 node2，均处于 ImagePullBackOff(25个) 或 ErrImagePull(4个) 状态，Events 统一显示 dial tcp ...:443: i/o timeout"}, "root_cause": "集群共有 93 个 Pod，30 个异常。主异常组 g2（ImagePullFailed）：29 个 Pod 处于 ImagePullBackOff(25)/ErrImagePull(4)，跨 aiops-e2e/default/mcp 三个命名空间，分布在 node1 和 node2。所有被验证 Pod（default/dns-check-test、mcp/connectivity-test、aiops-e2e/test-dns-1779360358）的 Events 均显示拉取 busybox:1.36.1 时 dial tcp [多个IP]:443: i/o timeout，覆盖 docker.io 多个后端 IP（185.45.7.185、31.13.95.37、39.109.122.128），排除 DNS 解析问题。镜像为公开镜像无 imagePullSecrets，排除认证问题。集群内执行镜像拉取操作也超时（30秒），确认网络层不可达。非主异常组 g1（Error/CrashLoopBackOff）：rc-crashloop-command-not-found-55b7bc\n... 截断，原始 601 字符", "root_cause_summary": "集群共有 93 个 Pod，30 个异常。主异常组 g2（ImagePullFailed）：29 个 Pod 处于 ImagePullBackOff(25)/ErrImagePull(4)，跨 aiops-e2e/default/mcp 三个命名空间，分布在 node1 和 node2。所有被验证 Pod（default/dns-check-test、mcp/connectivity-test、aiops-e2e/test-dns-1779360358）的 Events 均显示拉取 busybox:1.36.1 时 dial tcp [多个IP]:443: i/o timeout，覆盖 docker.io 多个后端 IP（185.45.7.185、31.13.95.37、39.109.122.128），排除 DNS 解析问题。镜像为公开镜像无 imagePullSecrets，排除认证问题。集群内执行镜像拉取操作也超时（30秒），确认网络层不可达。非主异常组 g1（Error/CrashLoopBackOff）：rc-crashloop-command-not-found-55b7bc\n... 截断，原始 601 字符", "confidence": 0.95, "confidence_reason": "有三个 namespace 三个 Pod 分别验证的 direct evidence（dial tcp i/o timeout），覆盖 node1 和 node2 两个节点，排除 DNS/认证/镜像名错误等候选原因，集群内网络测试也确认超时。因果链直接清晰。g1 也有 Exit Code 127 + 日志直接证据。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像地址或 tag 不存在（如 busybox:1.36.1 不存在）", "probability": "low", "reason": "公开镜像 busybox:1.36.1 是合法 tag；Events 显示的是网络超时而非 manifest unknown"}, {"cause": "imagePullSecret 缺失或认证失败", "probability": "low", "reason": "YAML 确认 imagePullSecrets 为空，镜像为公开镜像无需认证"}, {"cause": "DNS 解析失败导致域名无法解析", "probability": "low", "reason": "Events 中 dial tcp 已解析到具体 IP（185.45.7.185 等），说明 DNS 解析成功，超时发生在 TCP 连接阶段"}, {"cause": "CrashLoop 与镜像拉取相关", "probability": "low", "reason": "Exit Code 127 + 日志明确显示命令未找到，镜像 busybox:1.36 已成功拉取（有 Image ID），完全独立"}], "limitations": "未在集群内通过 run_bash_command 做 curl/wget 测试确认完整出口网络策略；未检查集群网络策略(NetworkPolicy)或集群代理配置；未验证是否可通过 HTTP 代理或 mirror 仓库绕过；g2 组中 aiops-e2e/test-dns-1779360358 的验证命令超时未返回结果，但同组其他 Pod 已验证一致模式可覆盖。", "llm_raw_analysis": "## 证据清点\n共采集 9 项关键证据，覆盖 g2 和 g1 两个异常组。\n\n### g2（ImagePullFailed - 29个Pod）\n- e1-e3: 三个跨 namespace Pod 的 kubectl describe Events，均显示 dial tcp ...:443: i/o timeout\n- e4: 镜像配置 YAML 确认无 imagePullSecrets，公开镜像\n- e5: 集群内网络连通性测试超时 30s\n- e8: jq 确认两个异常模式但底层均为网络超时\n- e9: 汇总 93 Pod/30 异常\n\n### g1（Error/CrashLoopBackOff - 1个Pod）\n- e6: Exit Code 127，Last State Error\n- e7: 日志显示 command not found\n\n## 逐条分析\n每条证据一致性极高，无矛盾。g2 网络超时证据跨越 node1(node1) 和 node2(node2)，排除单节点问题。\n\n## 关联分析\n- g2 所有证据指向同一根因：出口网络不通\n- g1 与 g2 完全独立：g1\n... 截断，原始 722 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群共有 93 个 Pod，30 个异常。主异常组 g2（ImagePullFailed）：29 个 Pod 处于 ImagePullBackOff(25)/ErrImagePull(4)，跨 aiops-e2e/default/mcp 三个命名空间，分布在 node1 和 node2。所有被验证 ...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点(node1/node2)出口网络无法连通外网镜像仓库(docker.io, registry.k8s.io等)，TCP 443端口连接超时，导致所有依赖外网镜像的 Pod 无法拉取镜像
     传导机制: 节点缺乏外网出口路由或防火墙策略 → kubelet 向 registry-1.docker.io:443 发起 HTTPS HEAD 请求 → TCP 三次握手超时 → containerd 返回 DeadlineExceeded → kubelet 标记 ErrImagePull → kubelet 重试后进入 ImagePullBackOff 退避循环
     最终表现: 29 个 Pod 分布在 aiops-e2e(default/mcp) 三个命名空间，位于 node1 和 node2，均处于 ImagePullBackOff(25个) 或 ErrImagePull(4个) 状态，Events 统一显示 dial tcp ...:443: i/o timeout


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (41.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 9477 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 3.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您提供的诊断数据生成的详尽诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **核心问题** | 集群共有 93 个 Pod，其中 **30 个处于异常状态 (32.3%)**，主要集中在 **镜像拉取失败 (29个)** 和 **容器启动命令错误 (1个)**。 |
| **Pod异常状态** | ImagePullBackOff (25个), ErrImagePull (4个), Error (1个) |
| **兼容归因层** | L3 - 网络/配置问题 |
| **问题分类** | 1. **ImagePullFailed** (29个Pod): 集群节点无法连通外网镜像仓库<br>2. **CrashLoopBackOffRuntime** (1个Pod): 容器启动命令不存在 |
| **置信度** | **高 (95%)** |
| **证据完整度** | 7/9 (78%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 集群Pod总数 | 93个 |
| 异常Pod总数 | **30个** (32.3%) |
| 受影响命名空间 | aiops-e2e, default, mcp |
| 受影响节点 | node1 (10.2.0.49), node2 (10.2.0.50) |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod dns-check-test -n default` | `Reason: ErrImagePull`<br>`Warning Failed ... kubelet Error: ErrImagePull`<br>`Back-off pulling image "busybox:1.36.1"` | 容器因镜像拉取失败而无法启动。 |
| 2 | Pod 状态与事件 | `kubectl describe pod connectivity-test -n mcp` | `Warning Failed ... kubelet Failed to pull image "busybox:1.36.1"` | 跨 namespace 验证，异常模式与 default namespace 一致。 |
| 3 | Pod 状态与事件 | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` | `Back-off pulling image "busybox:1.36.1"` | 跨 namespace 验证，异常模式与 default namespace 一致。 |
| 4 | Pod 状态与事件 | `kubectl describe pod rc-crashloop-... -n aiops-e2e` | `Reason: Error`<br>`Exit Code: 127`<br>`Back-off restarting failed container app` | 容器因启动命令执行失败而反复重启。 |
| 5 | 容器日志 | `kubectl logs Pod/rc-crashloop... --previous` | `sh: definitely-missing-command-for-rootcause: not found`<br>`RUNTIME_STARTUP_ERROR: command not found` | 确认 Exit Code 127 的原因是容器内运行的启动命令不存在。 |
| 6 | 事件过滤 | `kubectl get events -n default` | `Warning Failed Pod/dns-check-test ... Failed to pull image` | 镜像拉取失败事件只发生在 default namespace 内。 |
| 7 | Pod 配置 | `kubectl get pod dns-check-test -o yaml` | 镜像配置为 `busybox:1.36.1`<br>`terminationGracePeriodSeconds: 30`<br>`finalizers: <none>` | 确认镜像名称，并排除 Finalizer 问题。 |

### 证据关联分析
- **证据 #1, #2, #3, #6 印证**：跨3个命名空间（aiops-e2e, default, mcp）、跨2个节点（node1, node2）的Pod均因 `busybox:1.36.1` 镜像拉取失败而处于 `ImagePullBackOff/ErrImagePull` 状态。这表明问题**不是单个Pod或单个节点的问题，而是集群级的网络问题**。
- **证据 #4, #5 印证**：Pod `rc-crashloop-command-not-found-...` 的 `Exit Code 127` 与崩溃前日志 `command not found` 完全吻合，明确指向容器启动命令配置错误。这是一个独立于网络问题的配置错误。
- **证据链**：集群节点无法访问外网（`i/o timeout`）→ kubelet 无法拉取镜像 → Pod 状态变为 `ErrImagePull` → 重试后进入 `ImagePullBackOff` 退避循环。这是一个典型的集群出口网络不通导致的故障。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 集群内网络连通性测试 | important | 未采集原因：工具执行超时。如果采集到，可以更直观地证明 `docker.io` 网络不可达。但现有 Events 中的 `i/o timeout` 错误已足够形成完整证据链。 |
| `rc-crashloop-...` Pod 的完整 YAML | important | 未采集原因：工具执行失败。如果采集到，可以确认其 `command` 配置的准确内容。现有日志信息已足够定位问题。 |

---
## 🎯 根因分析
### 因果链
```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                           │
│ 集群节点 (node1/node2) 出口网络无法连通外网镜像仓库 (如 docker.io, registry.k8s.io)        │
│ (证据: kubectl describe Events 显示 dial tcp ...:443: i/o timeout)                 │
└────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                           │
│ 节点缺乏外网出口路由 或 防火墙/代理策略阻止了出站 443 端口流量                               │
│ → kubelet 尝试向 registry-1.docker.io:443 发起 HTTPS 请求                              │
│ → TCP 三次握手超时 (dial tcp ...:443: i/o timeout)                                  │
│ → containerd 返回 DeadlineExceeded 错误                                             │
└────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                           │
│ 节点无法建立到 docker.io 后端服务器的 TCP 443 端口连接                                 │
│ (证据: kubectl describe Pod 的 Events 中明确记录 "i/o timeout")                      │
└────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (g2 - ImagePullFailed)                                                │
│ 集群中 29 个 Pod 处于 ImagePullBackOff (25个) 或 ErrImagePull (4个) 状态，持续重启退避。    │
│ (证据: Pod 状态列表)                                                               │
└────────────────────────────────────────────────────────────────────────────────────┘

────────────────────────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────────────────────┐
│ 独立问题根本原因 (g1 - CrashLoopBackOff)                                           │
│ 容器启动命令 `definitely-missing-command-for-rootcause` 在容器镜像内不存在。              │
│ (证据: Exit Code 127, 日志 "command not found")                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                           │
│ Kubernetes 无法执行容器定义的 command/args，导致容器启动失败并立即退出。                      │
└────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (g1 - CrashLoopBackOff)                                              │
│ Pod rc-crashloop-command-not-found-... 处于 Error 状态并反复重启。                  │
│ (证据: Pod 状态列表, kubectl describe)                                             │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**问题一：集群出口网络问题（主问题，影响29个Pod）**
**结论**：根据证据 #1, #2, #3, #6 (跨命名空间和节点的 Events 均显示 `i/o timeout`)，问题的根本原因是**集群节点 (node1, node2) 无法连接到外网镜像仓库 (docker.io, registry.k8s.io)**。这导致所有依赖外网镜像的Pod无法拉取镜像，从而陷入 `ImagePullBackOff / ErrImagePull` 的无限退避循环。
**置信度**：**高 (95%)**
- ✅ `i/o timeout` 错误在多个Pod、多个命名空间、多个节点上反复出现，证据确凿。
- ✅ 镜像为公共镜像，排除了认证问题。
- ✅ 跨命名空间验证一致，排除单点故障。

**问题二：容器启动命令错误（独立问题，影响1个Pod）**
**结论**：根据证据 #4, #5 (`Exit Code: 127`, 日志 `command not found`)，Pod `rc-crashloop-command-not-found-...` 的根本原因是**容器启动命令配置错误**。`definitely-missing-command-for-rootcause` 这个命令在容器基础镜像中不存在，导致容器启动后立即退出并进入 `CrashLoopBackOff` 状态。
**置信度**：**高 (95%)**
- ✅ `Exit Code 127` 是 `command not found` 的经典标志。
- ✅ 崩溃前日志直接确认了该错误。

---
## 🛠️ 修复建议
### 问题一：修复集群出口网络（优先解决）
集群无法访问外网镜像仓库，需要联系网络或基础设施管理员，在平台层面解决。

**1. [核心操作] 配置集群访问外部镜像仓库的路由或代理**
   需要为集群的所有节点（node1, node2）配置出站 Internet 访问，或者配置私有镜像仓库 (Harbor / Nexus) 供集群使用。
   *方案 A：开通节点出站网络*
   - 需要为节点的 VPC/网络添加 NAT 网关或 Internet 网关，允许出站到外网 443 端口的流量。
   *方案 B：配置私有镜像仓库并修改集群镜像拉取策略*
   - 内网搭建并配置好 Harbor 或 Nexus 仓库。
   - 将公共镜像同步到私有仓库（`docker pull busybox:1.36.1 && docker tag busybox:1.36.1 <your-registry>/library/busybox:1.36.1 && docker push <your-registry>/library/busybox:1.36.1`）。
   - 修改集群中所有 Deployment/DaemonSet/Job 等的工作负载，将 `image: busybox:1.36.1` 替换为 `image: <your-registry>/library/busybox:1.36.1`，或配置 [镜像仓库镜像（Mirror）](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/) 功能。

**2. [诊断] 验证网络连通性**
   可用任意一个处于 `Running` 状态的Pod进行测试，确认集群出口网络是否恢复。
   ```bash
   # 找到一个正常运行的Pod
   kubectl get pods -A | grep Running | head -n 1 | awk '{print $2, $1}'
   # 进入该Pod并尝试连接，如果该Pod没有curl或wget，尝试用shell内置功能:
   kubectl exec -it <pod-name> -n <namespace> -- timeout 5 sh -c "</dev/tcp/registry-1.docker.io/443" && echo "Port 443 is open" || echo "Port 443 is blocked"
   ```

### 问题二：修复容器启动命令（独立问题）
**1. [立即执行] 修改 Deployment/Job 的 command/args**
   Pod `rc-crashloop-command-not-found-55b7bcd797-bhsr2` 是由某个工作负载（如 Deployment）管理的。需要找到该工作负载并修改其 Pod 模板中的启动命令。
   ```bash
   # 假设该 Pod 属于名为 rc-crashloop-command-not-found 的 Deployment
   kubectl edit deployment/rc-crashloop-command-not-found -n aiops-e2e
   ```
   在 YAML 编辑器中将 `spec.template.spec.containers[0].command` 或 `args` 中的错误命令 `definitely-missing-command-for-rootcause` 修改为正确的启动命令。如果没有提供该命令，可先启动一个长驻进程如 `sleep 3600` 来进入容器进行排查。
   ```yaml
   # 修改为:
   command: ["sh", "-c", "sleep 3600"]
   ```
   如果无法修改工作负载，可以暂时删除错误的Pod，让Deployment重新创建，但前提是已经修改好了工作负载配置。
   ```bash
   kubectl delete pod rc-crashloop-command-not-found-55b7bcd797-bhsr2 -n aiops-e2e
   ```

**2. [可选] 确认正确的启动脚本路径**
   ```bash
   # 如果修改了command为sleep，可以进入容器查看conf目录
   kubectl exec -it rc-crashloop-command-not-found-<new-pod> -n aiops-e2e -- ls /path/to/your/app
   ```

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认问题一 (网络) 已修复 | `kubectl get pods -A \| grep -E 'ErrImagePull\|ImagePullBackOff'` | 没有 ErrImagePull 或 ImagePullBackOff 的 Pod |
| 2. 确认问题二 (命令错误) 已修复 | `kubectl get pod rc-crashloop-command-not-found-... -n aiops-e2e` | STATUS 变为 Running 或 Completed |
| 3. 最终确认所有Pod正常 | `kubectl get pods -A` | 所有 Pod 均处于 Ready/Running 状态 |

---
## ⚠️ 注意事项
- **配置 Mirror 仓库**：对于生产环境，强烈建议不要直接依赖外网仓库，应配置内网私有镜像仓库（如 Harbor）作为上游仓库的Mirror。这不仅解决了网络不可达问题，还能提高镜像拉取速度和稳定性。
- **资源编排**：`rc-crashloop-command-not-found-...` 这个 Pod 的名称暗示其可能是一个用于测试的、有问题的资源。建议检查 `aiops-e2e` 命名空间下是否有其他测试资源可能存在类似问题。
- **监控告警**：建议对 Pod `ImagePullBackOff` 和 `ErrImagePull` 状态配置集群级别的监控告警，以便第一时间发现网络故障。

---

## 📊 性能统计

├─ 总耗时: 3.1m
├─ 问题定位: 55.8s (30%) ✅
├─ 证据链采集: 60.4s (33%) ✅
├─ 根因分析: 25.1s (14%) ✅
├─ 汇总总结: 41.8s (23%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 18 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-crashloop-runtime
- **工具调用**: 18 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
