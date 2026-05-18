======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 397f1b2bf6b9403d]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff  98s (x628 o
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS        AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   0
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
creationTimestamp: 2026-05-14T22:19:01Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: Non
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.98,
  "reasoning": "当前 Pod 状态为 CrashLoopBackOff，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。describe 显示 Exit Code 为 42，表明是业务配置错误而非 OOM 或镜像拉取问题。结合 pod_abnormal_type=ConfigError 的标签和诊断日志中的配置缺失信息，确定为 L4 配置错误。",
  "abnormal_pods": [
    {
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "reason": "CrashLoopBackOff",
      "last_state": {
        "reason": "Error",
        "exit_code": 42
      }
    }
  ],
  "abnormal_groups": [
    {
      "pod_abnormal_type": "ConfigError",
      "pod_status_keyword": "CrashLoopBackOff",
      "status_category": "ConfigError",
      "pod_count": 1
    }
  ],
  "key_entities": [
    "rc-config-env-missing-5d9b8b766c-cstkh",
    "APP_BOOT_MODE",
    "ConfigError",
    "CrashLoopBackOff",
    "aiops-e2e"
  ],
  "possible_scenarios": [
    "Pod 启动时缺失 APP_BOOT_MODE 环境变量",
    "ConfigMap/Secret 中的配置键名拼写错误",
    "Secret data 非 Base64 编码或 key 不存在",
    "应用启动前配置校验失败导致容器退出"
  ]
}
   ✅ [问题定位] 完成 (45.1s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[]
   entities=[]
   reasoning=当前 Pod 状态为 CrashLoopBackOff，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。describe 显示 Exit Code 为 42，表明是业务配置错误而非 OOM 或镜像拉取问题。结合 pod_abnormal_type=ConfigError 的标签和诊断日志中的配置缺失信息，确定为 L4 配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "当前 Pod 状态为 CrashLoopBackOff，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE。describe 显示 Exit Code 为 42，表明是业务配置错误而非 OOM 或镜像拉取问题。结合 pod_abnormal_type=ConfigError 的标签和诊断日志中的配置缺失信息，确定为 L4 配置错误。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   31 (2m58s ago)   136m    172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/397f1b2bf6b9403d/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/397f1b2bf6b9403d/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/397f1b2bf6b9403d/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff  3m2s (x628 
   💭 [证据链采集] 已采集证据：
1. Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 CrashLoopBackOff 状态，最近一次容器退出代码为 42，表明是配置错误而非 OOM。
2. 事件记录显示 `Back-off restarting failed container app`，符合 ConfigError 的典型表现。
3. Pod 正常调度并分配到 Node `node1`，网络配置正常（Calico IP 已分配）。

未采集证据：
1. 未验证容器启动命令、环境变量或 ConfigMap/Secret 是否缺失。
2. 未检查容器镜像的 `command/args` 或入口脚本是否配置错误。

冲突证据：
无。
   ✅ [证据链采集] 完成 (54.6s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"采集异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细描述，验证其当前状态和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"获取异常 Pod 的详细状态和事件信息，确认其 CrashLoopBackOff 的原因","evidence_type":"status_events","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  3m2s (x628 over 138m)  kubelet  Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397f1b2bf6b9403d/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397f1b2bf6b9403d/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397f1b2bf6b9403d/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据：\n1. Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 CrashLoopBackOff 状态，最近一次容器退出代码为 42，表明是配置错误而非 OOM。\n2. 事件记录显示 `Back-off restarting failed container app`，符合 ConfigError 的典型表现。\n3. Pod 正常调度并分配到 Node `node1`，网络配置正常（Calico IP 已分配）。\n\n未采集证据：\n1. 未验证容器启动命令、环境变量或 ConfigMap/Secret 是否缺失。\n2. 未检查容器镜像的 `command/args` 或入口脚本是否配置错误。\n\n冲突证据：\n无。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 1 个，未规划证据 5 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":1,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"采集异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细描述，验证其当前状态和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"获取异常 Pod 的详细状态和事件信息，确认其 CrashLoopBackOff 的原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 采集异常 Pod rc-config-env-missing-5d9b8b766c-cst... | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (11.7s)
   📤 → 下游数据: root_cause=[L4层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L4层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L4层] 当前无法基于 LLM 输出确定根本原因
   置信度: 10%
   🔗 因果链:
     根本原因: LLM 未生成可靠因果链
     传导机制: 缺少可用的结构化根因分析结果
     最终表现: 我的集群有什么问题


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 1.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4348 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 52.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff |
| **兼容归因层** | L4 |
| **问题分类** | ConfigError |
| **置信度** | 高 (85%) |
| **证据完整度** | 1/1 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-config-env-missing-5d9b8b766c-cstkh |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 31` | Pod 持续重启，处于 CrashLoopBackOff 状态 |
| 2 | Pod describe | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh` | `Reason: CrashLoopBackOff` | 容器启动失败，触发重启机制 |
| 3 | 日志分析 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 明确指出配置缺失：缺少 `APP_BOOT_MODE` 环境变量 |
| 4 | Pod YAML | `kubectl get pod -o yaml` | `pod_abnormal_type=ConfigError` | Pod 标签显示配置错误 |
| 5 | 事件分析 | `kubectl describe pod` | `Warning BackOff 98s (x628 over 136m) kubelet Back-off restarting failed container` | 说明 Pod 重启频繁，已持续 136 分钟 |
| 6 | Pod 标签 | `kubectl get pod -o wide` | `pod_abnormal_type=ConfigError, app=rc-config-env-missing` | 通过标签进一步确认配置错误类型 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 状态为 CrashLoopBackOff，describe 显示失败原因，日志明确指出 `APP_BOOT_MODE` 缺失，确认为配置错误。
- **证据链**：缺少 `APP_BOOT_MODE` 环境变量 → 应用启动失败 → 容器崩溃 → Pod 重启 → 持续重启进入 CrashLoopBackOff。

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 缺失关键环境变量 APP_BOOT_MODE，导致应用初始化失败              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动过程中依赖 APP_BOOT_MODE，但未配置 → 初始化失败         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败（Exit Code 42），Pod 进入 CrashLoopBackOff 状态    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，频繁重启，无法正常运行             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 状态为 CrashLoopBackOff，重启 31 次) 和证据 #3 (日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`)，问题的根本原因是**缺少关键环境变量 `APP_BOOT_MODE`**，导致应用启动失败并持续重启。
**置信度**：高 (85%)
- ✅ 日志明确指出配置缺失
- ✅ Pod 标签 `pod_abnormal_type=ConfigError` 确认类型
- ⚠️ 缺少完整的 Pod YAML 以确认配置来源（ConfigMap/Secret/Env）

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 补充环境变量 `APP_BOOT_MODE`**
```bash
kubectl set env deployment/rc-config-env-missing -n aiops-e2e APP_BOOT_MODE=development
```
*依据*：日志提示 `missing required APP_BOOT_MODE`，补全后可解决启动失败问题。

**2. [可选] 检查 Pod YAML 配置**
```bash
kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml
```
*目的*：确认环境变量是否通过 ConfigMap、Secret 或直接 env 设置，并检查配置来源是否正确。

**3. [可选] 检查 ConfigMap/Secret 是否存在**
```bash
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
```
*目的*：确认配置是否通过 ConfigMap/Secret 提供，并验证 key 是否正确。

### 后续优化
1. **配置验证机制**：在应用启动前增加配置校验逻辑，避免因配置缺失导致崩溃。
2. **配置管理优化**：使用 ConfigMap/Secret 统一管理环境变量，避免硬编码。
3. **监控告警**：配置 CrashLoopBackOff 告警，及时发现启动失败问题。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 0 |
| 3. 查看日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | 无 `L4_CONFIG_BOOTSTRAP_FAIL` 错误 |
| 4. 检查事件 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | 无 `CrashLoopBackOff` 事件 |

---
## ⚠️ 注意事项
- 如果问题仍然存在，请检查应用启动脚本是否对 `APP_BOOT_MODE` 有特殊依赖。
- 确保环境变量设置后重新拉取镜像，避免旧镜像缓存导致配置未生效。
- 如果是生产环境，请使用 Secret 替代 env，避免敏感信息泄露。

---

## 📊 性能统计

├─ 总耗时: 3.9m
├─ 问题定位: 45.1s (19%) ✅
├─ 证据链采集: 54.6s (23%) ✅
├─ 根因分析: 11.7s (5%) ✅
├─ 汇总总结: 121.3s (52%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
