# Prompt 管理与精简规则

项目运行时 Prompt 统一由 `app/core/prompts.py` 管理。`WORKFLOW_PROMPTS_I18N` 和 `get_workflow_prompt()` 是节点取值入口；不要在 workflow node 中散落新的 system prompt。

Codex 的个人全局行为位于 `/root/.codex/AGENTS.md`。它不属于本仓库，用于跨项目的意图提纯；项目 `AGENTS.md` 只保存仓库约定，两者不要复制整段相同规则。

## 五段任务合同

新增或修改运行时 Prompt 时，按以下语义组织，短 Prompt 不必机械保留五个标题：

1. 目标：该节点只负责哪个决策或产物。
2. 权威输入：哪些 schema、事实或工具结果可以支撑决策。
3. 动作与停止：需要执行什么，何时停止继续探索。
4. 输出：下游消费的 schema 或人类产物。
5. 高代价边界：只保留高概率且后果大的偏移，并同时给出正确替代行为。

Prompt 不解释“第一性原理、隐性提纯、负向配平”等写作方法。它们是维护 Prompt 的方式，不是 K8s Agent 的运行任务。

## 隐性语义载体

优先使用已有结构表达语境：

- `LayerOutput`、`EvidencePlanOutput`、`RCAOutput` 等 schema 表达字段和类型。
- `kubectl_get_by_kind_in_cluster(kind="Pod")`、`execute_pod_promql` 等真实工具名表达能力边界。
- `kubectl get pods -A` 一类最小命令表达 Kubernetes/Linux 生态。
- `present/empty/absent/weak/error` 表达 coverage 语义。
- acceptance test 表达不能回退的行为。

一个载体已经表达清楚时，不再追加同义解释或完整手写 JSON 示例。

## 负向规则

负向规则只用于容易发生且代价高的偏移，例如编造事实、跨实体拼接、把历史 Event 当当前状态、生成未授权写操作。规则必须说明替代动作：

- 不写“不要猜测”后就结束；同时规定空结果或证据不足时的输出。
- 不只禁止重复工具；同时规定信息增益和停止条件。
- 不只禁止按故障类型写死；同时规定按 dimension、purpose、coverage 和上一轮真实结果选择查询。

同一规则只出现一次，并靠近它控制的决策。

## 当前字符预算

| Prompt | 变更前 | 当前上限 |
|---|---:|---:|
| Layer classifier | 3240 | 2600 |
| Layer extract | 1959 | 1400 |
| Query direct | 2301 | 1900 |
| Evidence collector | 5519 | 4000 |
| RCA analyzer | 6047 | 4300 |
| Conclusion formatter | 785 | 1200 |

预算是注意力门禁，不是鼓励写到上限。安全或事实合同确需增加时，先删除重复语义；仍需放宽上限时，在同一提交中说明原因并增加行为回归。

## 修改流程

1. 先在 `tests/unit/workflow/test_fast_paths.py` 写行为或预算失败测试。
2. 只修改对应节点 Prompt，运行该节点的 focused tests。
3. 检查 Prompt 中是否出现 fixture、workload、namespace 或某个故障答案。
4. 运行 Fact、evidence、report 和 remediation 回归。
5. 用字符表和 `git diff --check` 验证后提交。

常用命令：

```bash
pytest -q tests/unit/workflow/test_fast_paths.py -k prompt
pytest -q tests/unit/workflow/test_fact_contract.py
pytest -q tests/unit/workflow/test_evidence_dynamic_stop.py
```

生产代码和运行时 Prompt 都不能增加只服务某个 OOM、镜像、配置或调度样例的确定性分支。场景差异由标准事实、工具结果、runbook 和 schema 承载。
