# c01 + c03 六对象混合分组实测

## 结论

**分组、单对象分支展开和汇总在两轮均正常；根因正确性并非全部通过。**

| 轮次 | Layer 实际分组 → 执行分支 | 对象覆盖 | 主根因通过 | 请求耗时 | 原始报告 |
|---|---|---|---|---:|---|
| 1 | 6 个单对象 group → 6 个 lane | 6/6，无重复 | 4/6 | 142.9s | [8be6496386db442d](01-mixed/run-01/report.md) |
| 2 | 2 个三对象 group → 6 个 lane | 6/6，无重复 | 5/6 | 627.6s | [87b95b89ca46403c](01-mixed/run-02/report.md) |

主根因按“是否识别具体注入原因”人工判断，不把仅识别 Pending/Insufficient cpu 当作识别了 CPU request 配置过大。第二轮 CPU 识别到调度资源不足，但没有定位请求异常，按该口径未通过。两轮比例算术平均为 **75.0%**；这是本次人工复核口径，不是重算历史正式评分。次要错误仍单列，不意味着通过的报告每句话都正确。

测试结束于 2026-09-08 18:46:11：`runner.status=completed`，`cleanup_errors=[]`，工作进程 4151238 已退出，六个测试 namespace 已清理。2026-09-09 继续审查时也确认不存在这些 namespace，非 Running/Succeeded Pod 查询为空。

## 测试条件

- 同时部署 c01-cpu/v01、c01-memory/v02、c01-pvc/v03、c03-secret/v04、c03-key/v05、c03-hostpath/v06。
- 每次提问均为 **“我的集群有什么问题？”**，不向 Agent 提供 namespace、Pod 或预期原因。
- 请求串行两次，共用同一批六个 Pod；每次请求前验证当前 UID 的故障事件，保存前后快照，两次内的 UID 均未变化。
- 超时 1200 秒，每次只尝试一次，无请求重跑。
- 线上版本均为 **11.0.157**。此前本地修复的 observation.py 没有部署，因此本次不是修复后的效果回归。
- 本轮仅增加测试执行记录、分组审计脚本和本说明，未修改 Agent、Runbook、评分规则或线上配置。

这验证的是多个独立 Pod 共享异常状态、分别具有不同原因，不是一个 Pod 同时承受全部六种故障。

## 分组为何判断正常

审查依据不是模型文字自述，而是 `layer/handoff.json`、`parallel_evidence.output.json` 和各分支 `evidence.input.json`。

第一轮实际为 g1～g6，每个 group 对应一个 Pod。模型前面的文字曾按 Pending/ContainerCreating 描述两类异常，但最终交接不是两个 group；应以结构化交接为准。

第二轮实际关系为：

```text
g1 Pending
  g1-p1 → aiops-case-v01/workload → CPU
  g1-p2 → aiops-case-v02/workload → memory
  g1-p3 → aiops-case-v03/workload → PVC
g2 ContainerCreating
  g2-p1 → aiops-case-v04/workload → Secret
  g2-p2 → aiops-case-v05/workload → ConfigMap key
  g2-p3 → aiops-case-v06/workload → hostPath
```

两轮均通过以下确定性检查：

- Layer 和 lane 的目标集合均与部署快照中的六个对象一致。
- 每个 lane 只有一个对象，没有重复分配或遗漏。
- 每个 Evidence 输入的 issue_groups 与其 lane 的目标一致。
- `expected_group_count=6`、`terminal_group_count=6`、`group_count=6`、`join_complete=true`、`error_count=0`。
- 最终报告中都有六个对象的独立章节，没有发现用另一个对象的根因替代当前对象。

`diagnosed_count=6` 仅代表系统将六个分支标记为已诊断，**不代表六个根因经过人工验证都正确**。可执行 [audit_groups.py](audit_groups.py) 复核上述结构检查；脚本不判断自然语言根因语义。

## 逐根因审查

| 具体场景 | 第一轮 | 第二轮 |
|---|---|---|
| CPU request=100000，API 显示 100k | 错误：把 100k 换算成 0.1 核，并推断集群 CPU 耗尽 | 不充分：仍归因集群资源枯竭，未指出 CPU request 超大 |
| memory request=1Pi | 主根因正确：请求超过节点容量 | 主根因正确 |
| PVC unavailable-claim 不存在 | 主根因正确 | 主根因正确 |
| Secret unavailable-input 不存在 | 主根因正确 | 主根因正确 |
| ConfigMap 缺 unavailable-key | **错误：编造 Pod spec.template 为空** | 主根因正确 |
| hostPath 不满足 Directory 检查 | 主根因正确，但“路径一定不存在”表述比事件更强 | 主根因正确，保留“不存在或非目录”边界 |

第一轮未调用 Runbook；第二轮各 lane 引用了 Runbook，但 Pending 父组的 pending + volume 手册会同时传给三个子分支，故 CPU/memory 也带有 volume 参考。这是父组知识继承，不等于跨对象证据串用；Runbook 是否相关应单独评估。

## 重点问题 1：ConfigMap 误诊不是 group 混淆

第一轮 `8be6496386db442d-g5` 的真实执行记录只有：

1. execute_pod_promql：ContainerCreating/Pending 等状态指标。
2. query_pod_logs：empty。
3. query_pod_tracing：无 pod_ip，未取得流量/span。

计划中列出了 Describe、Events、YAML，但实际没有执行。归档仅有三个工具调用；`evidence.full.json` 记录 `plan_total=7`、`plan_collected=3`，诊断充分度为 0.1333，标签为“不足”。

然而 Evidence 的 `llm_analysis` 声称：

```text
kubectl get yaml 真实返回 spec.template: {}
Warning FailedCreate: pod template is empty
缺口：无
```

这些不是工具返回。它还提到早于该 Pod 创建时间的 Pulling/Pulled 事件。真实快照有 `spec.containers`，真实故障事件为 `configmap references non-existent config key: unavailable-key`。普通 Pod 本来也不以 `spec.template` 作为容器定义入口，这是 Deployment 等控制器模板的层级。

RCA 输入同时包含了“缺少 Describe/Events/YAML”的信息、三条真实工具观察，以及这段错误的 LLM 分析；RCA 仍采纳错误草稿，最终报告把“诊断结论指出 spec.template 为空”写进“真实原始结果”。

归因需要分开：

- **模型问题**：没有执行工具却声称有真实返回，且混淆 Kubernetes 对象结构。
- **当前工程约束不足**：计划未执行、关键依据缺失没有阻止其发布“已确认根因”。该 lane 的 `claim_validation.output.json` 明确为 `enabled=false/skipped=true`，所以本轮没有事实绑定/发布验证兜底。
- **不是原始工具返回错误，也不是 group 把其他 Pod 的证据串进来。** 这次 YAML 根本没查，不能将此误诊归因于此前已修复的 YAML 投影丢字段。

因此，不能把这一问题完全归为“模型能力有限，工程无需处理”。可考虑在无真实支持、且关键计划项未执行又无等价证据时，补采或标为未确认，而不是信任自然语言自述。不要简单以一个完整度百分比作为所有诊断的正确性阈值。

## 重点问题 2：第二轮为何用了 10.5 分钟

慢点是 hostPath 的 `g2-p3`：Evidence 580.3 秒，RCA 8.2 秒，合计 588.6 秒。其他五个 lane 为 37.9～104.6 秒，说明不是六个分支顺序执行。

时间证据（UTC）：

- 10:35:23 左右开始各 lane 的 Evidence Plan 阶段。
- 10:44:44.785 服务日志：`native structured output returned unsupported type=NoneType schema=EvidencePlanOutput`。
- 随后使用后备计划并开始该 lane 的首轮工具查询。
- SSE 中 g2-p3 首个 tool_start 距整次请求开始 **581.38 秒**；Metrics/Logs/Tracing 查询各约 **2.1 秒**，Describe 和 Topology 也很快返回。

因此长等待在**模型计划生成/结构化响应路径**，不是 MCP 查询耗时，也不是 group join 丢失结果。所有 lane 最终完成，但总报告必须等待最慢的 lane，因而放大了这次长尾。

目前证据不能进一步区分模型服务排队、生成耗时、底层重试或客户端等待各占多少。可考虑独立的 plan 阶段超时和有界 fallback，配套保留请求耗时/失败原因；本轮仅定位，没有修改超时或并发策略。

## 后续建议与边界

1. **不需要因这两轮结果重写 group 分组逻辑。** 对象覆盖、展开和汇总均通过。
2. 优先处理“未取得核心证据仍发布确定性 RCA”的保护，再单独验证 plan 长尾的阶段超时策略。
3. CPU 仍有单位和调度机制理解问题。此前摘要字段修复尚未上线，本轮也不能证明它足以解决 CPU 误判。
4. 报告仍有把单点指标说成长期状态、用 restarts=0 单独证明从未运行、小请求值直接排除资源不足等过度推断。
5. 只有两轮，不能据此断言六路并发导致模型幻觉，也不能把 75% 当作稳定总体准确率。

## 证据位置

- [runner.json](runner.json)：运行状态、镜像版本、耗时、Run ID、清理结果。
- [run_mixed.py](run_mixed.py)：复用 c01 实测流程的启动脚本。
- 各 run 目录：report.md、events.json、raw.sse、evidence.archive.json、before.json、after.json。
- 完整归档根目录：`/data/redis/aiops-aiops-reports-pvc-pvc-52d8916d-bd02-4ad3-9c91-ea2e59356b51/context_archives/`。
- 分组：`<run_id>/layer/handoff.json`、`<run_id>/node_outputs/parallel_evidence.output.json`。
- 幻觉链路：`8be6496386db442d-g5/node_outputs/evidence.full.json` → `node_inputs/rca.input.json` → `node_outputs/rca.output.json`。
- 第二轮慢分支：`87b95b89ca46403c-g2-p3/`，结合 run-02/events.json 的 evidence_context.group_id 与 ts_ms。
