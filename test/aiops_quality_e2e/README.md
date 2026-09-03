# AIOps 异常 Case E2E 质量测试

本目录用于盲测当前 AIOps 诊断服务的四项核心指标：

1. MTTR（一次诊断请求到最终报告的时间）
2. 根因准确率
3. Runbook 覆盖率
4. 证据完整度

Ground Truth 和固定证据合同位于 `demo_cases.yaml`，只由本地评分器使用，
不会注入 AIOps Prompt，也不会发送给 Agent。

## 1. 运行方式

### 单个 Case

```bash
.venv/bin/python test/aiops_quality_e2e/run_quality_demo.py --scenario c04 -n 1 -c 1 --timeout 1200 --url http://10.2.0.48:30800
```

### 多个 Case

```bash
.venv/bin/python test/aiops_quality_e2e/run_quality_demo.py --scenario c02,c08 -n 5 -c 2 --timeout 1200 --url http://10.2.0.48:30800
```

`-n 5` 表示每个 Case 运行 5 次，`-c 2` 表示同一 Case 内最多并发 2 个
诊断请求。不同 Case 依次部署，不会把 c02 和 c08 同时注入集群。

### 全量过夜测试

`--scenario all` 依次测试 c01～c11：

```bash
.venv/bin/python test/aiops_quality_e2e/run_quality_demo.py --scenario all -n 50 -c 5 --timeout 1200 --url http://10.2.0.48:30800 --output-dir testreports/aiops_quality_overnight
```

脚本只清理 `test/pod-anomaly-cases/catalog.yaml` 明确声明的 `aiops-case-XX`
namespace。c11 清理前会先释放指定 Pod 的 finalizer。

## 2. 断网保护和断点续跑

默认启用 detached worker 保护：

```text
启动命令
├─ 后台 worker 执行测试并写 runner.log
└─ 当前终端实时跟随 runner.log
```

SSH/网络断开或在当前窗口按 `Ctrl+C` 只会停止日志跟随，不会终止后台
worker。重新登录后可查看：

```bash
tail -f testreports/<report-dir>/runner.log
cat testreports/<report-dir>/runner.status.json
```

仅当需要让测试与当前终端绑定时使用 `--foreground`。

`stats.json` 在每次运行完成后更新。中断后使用同一输出目录续跑：

```bash
.venv/bin/python test/aiops_quality_e2e/run_quality_demo.py --scenario all -n 50 -c 5 --timeout 1200 --url http://10.2.0.48:30800 --output-dir testreports/aiops_quality_overnight --resume
```

已写入 `stats.json` 的运行不会重跑；没有完成评分的运行编号会重新执行。

每个逻辑运行默认最多发起 2 次请求，退避 30 秒。每次尝试都保留独立现场，
但请求重试不能替代 `--resume`：如果整个 worker 被主动终止，仍需要断点续跑。

## 3. 输出文件

```text
testreports/aiops_quality_<scenarios>_<timestamp>/
├── runner.log                         # 受保护 worker 的完整日志
├── runner.status.json                 # PID、运行状态、时间和退出码
├── summary.md                         # 每轮更新的 Markdown 汇总
├── overview.txt                       # 与终端一致的质量总览
├── stats.json                         # 断点和结构化总结果
└── cXX/run-<NN>-<run_id>/
    ├── report.md                      # AIOps 最终诊断报告
    ├── score.json                     # 本次评分和命中明细
    ├── evidence.archive.json           # Evidence lane 真实工具归档
    ├── events.json                    # 完整 SSE 事件
    ├── live.log                       # 本轮人工可读日志
    ├── raw.sse                        # 原始 SSE
    └── attempt-XX/                    # 每次请求尝试的原始现场
```

## 4. 指标统计口径

### 4.1 MTTR

单次 MTTR 是从发起 `/ask` 到接收 SSE `final` 事件的时间，包括：

```text
Layer → Evidence/RCA → Conclusion → final
```

汇总 MTTR 是所有成功返回运行的算术平均值。请求失败不进入 MTTR 分母，而是单独
进入请求成功率。当前验收阈值为 `< 15m`。

### 4.2 根因准确率

评分器只读取最终报告中每个 `根因结论`，不使用证据表、Runbook 或 Ground Truth
拼接答案。一次运行通过需要：

- 所有期望根因都被已确认的结论命中；
- 没有额外发布不属于该 Case 的确定性根因；
- `证据不足/根因无法确认` 不能通过根因验收。

当前 c01～c11 为单 Case、单主根因，因此明细只展示统一的 `根因准确率`：

```text
本次根因通过 = 100%
本次根因失败 = 0%
```

总体公式：

```text
根因准确率 = 根因验收通过的成功运行数 / 成功返回运行数
```

`demo_cases.yaml` 可以为真实报告中的等价表达声明 aliases，例如：

```text
OOMKilled ↔ OOM Killer
64Mi ↔ 64 MiB ↔ 67108864 bytes
```

aliases 只用于真实同义表达；模糊的“可能 OOM”或根因级“证据不足”仍判定失败。

### 4.3 Runbook 覆盖率

当前 Runbook 指标衡量期望 Runbook 是否实际被诊断 lane 参考：

```text
Runbook 覆盖率 = 已参考的期望 Runbook 数 / 期望 Runbook 总数
```

数据来自最终报告、`fetch_runbook` 真实调用和 workflow Runbook 元数据。
该指标本质上是 Runbook 召回/覆盖：额外获取无关 Runbook 不会降低当前覆盖率。

### 4.4 证据完整度

正式证据完整度使用 Evidence Plan 的实际执行完成率。评分器从每个 Evidence lane
归档读取：

```text
plan_total
plan_collected
```

其中 `plan_total` 是该 lane 计划采集的证据项数，`plan_collected` 是实际成功执行并
采集到结果的工具项数。仅调用工具但查询失败、返回空结果或未形成已采集项，不应计入
`plan_collected`。

单次运行公式：

```text
证据完整度 = Σ各 Evidence lane 的 plan_collected / Σ各 Evidence lane 的 plan_total
```

例如同一次诊断包含两个 lane：g1 完成 4/5，g2 完成 6/9，则：

```text
证据完整度 = (4 + 6) / (5 + 9) = 71.4%
```

多次成功运行对每次运行的完整度做算术平均，每次运行等权：

```text
总证据完整度 = Σ(每次成功运行的证据完整度) / 成功运行数
```

例如两次运行分别为 4/5=80% 和 6/9=66.7%，总证据完整度为
`(80% + 66.7%) / 2 = 73.35%`。请求失败不进入证据完整度分母，另行统计请求成功率。

该指标回答的是“Agent 对自己制定的调查计划完成了多少”，不等同于“Case 理想证据是否
全部覆盖”。`demo_cases.yaml` 中的固定语义证据合同仍会基于真实 `tool_data` 和 canonical
`fact_ledger.records` 计算，并保存在 `score.json.evidence_contract_audit`，作为独立审计
结果，不参与正式证据完整度与验收判定。正式值同时保存在 `score.json.evidence`；
`evidence_plan_audit` 保留为兼容审计副本。

## 5. 验收阈值

| 指标 | 通过阈值 |
|---|---:|
| MTTR | `< 15m` |
| 根因准确率 | `>= 70%` |
| Runbook 覆盖率 | `>= 70%` |
| 证据完整度 | `>= 70%` |

请求成功率单独展示，不混入上述四项指标的分母。

## 6. 指标边界

- 根因评分器是可审计的确定性语义合同，能识别已登记的真实同义表达，但不是
  通用语义裁判模型。例如报告同时包含 `/work`、Readiness 和 HTTP 503 时，
  纯词项合同无法完全判断报告是否把 `/work` 和真实探针路径 `/ready` 的
  因果关系写反。关键 Case 仍应抽样人工复核。
- Runbook 覆盖率只衡量期望 Runbook 是否被参考，不惩罚额外获取的无关
  Runbook。如需衡量工具选择收敛性，应另行统计 Runbook 选择精确率。
- 证据完整度衡量 Evidence lane 是否采集到了理想事实，不代表最终 RCA
  一定正确使用了这些事实。因此可能出现“证据 100%，根因错误”。
- MTTR 只对成功返回的运行求平均，必须与请求成功率一起解读，避免
  忽略超时长尾。
