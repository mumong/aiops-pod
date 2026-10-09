# Query 指引、Runbook 与工具状态优化验收

日期：2026-10-09。限定范围内改动已部署；补充测试发现未解决问题，不宣称全功能通过。

## 修改范围

- `app/core/prompts.py:QUERY_COLLECT_PROMPT`：优先参考匹配手册，明确统计口径、序列身份、真实映射、时间对齐及必答缺口。没有新增节点、强制工具链、自动 PromQL 改写或数值兜底。
- `app/core/runbook/catalog.py`、`nodes/query_answer.py`：无显式 catalog 描述的手册读取头部 `> 适用说明：`；已有 catalog 描述仍优先，没有硬编码文件名命中规则。
- `deploy/configmap/runbooks.yaml`：仅修改指标参考手册。覆盖节点/集群口径、容量加权、重复来源核查、节点身份映射、时间和空结果；移除混杂排障章节，诊断主目录保持原有内容。
- `ObservationProcessor`：通用 Prometheus 成功空向量/矩阵保持成功，coverage=empty；原文不变，不补零。
- 前端工具详情分别展示执行状态、数据覆盖、解析状态；真实错误仍是错误。
- 未修改 MCP 实现、监控采集配置、模型、凭据、PVC、A2A、诊断路由或修复流程。

## 已完成的自动检查

- 后端：`.venv/bin/python -m pytest tests/unit test/workflow/test_runbook_remediation_guidance.py -q`：1714 passed，27 个已有弃用警告。
- 前端：`make check`：88 tests passed，ESLint、TypeScript、Vite 构建成功；仍有 bundle >500kB 提示。
- 浏览器：本地 direct-query 与 metric-tools 回放通过，线上 metric-tools 回放通过。
- 真实 SSE 回放到线上 UI：空结果和 Pod 指标均正确显示；解析/展示通过不等于指标聚合口径正确。
- 基线测试中的旧提示词快照、旧空结果判失败期望已更新；新增边界测试覆盖空、零、源端错误、不支持格式与手册描述。
- `git diff --check`：前后端通过。未 commit/push Git。

## 真实查询（经前端 /api 代理）

| 用例 | run_id | 结果 | 耗时 |
|---|---|---|---:|
| 查询集群 CPU、内存 | 83ae5bbf6712465f | 主动读手册；节点整体口径；CPU 6.63%、内存 24.09%；核对 18/18/12 核、78.29 GiB；相关查询同 time | 57.8s |
| 查询各节点 CPU、内存（/ask） | 8a6d1cb3ff8f4b14 | 主动读手册；查询 NAME+InternalIP+Ready；正确映射三个节点；数值吻合原始返回 | 26.1s |
| 集群查询并明确参考 Runbook（/ask） | 7a5e8ceb675d4941 | 读取手册；集群加权 CPU 6.29%、内存 23.74%；同 time 并检查来源身份 | 39.4s |
| 指定不存在的监控标签 | c0b08219ddc94889 | status=success、transport_status=success、semantic_success=true、coverage=empty、parse_status=parsed；没有把空当成零 | 19.8s |

第一轮多做了一次 get_metric_names，仍有减少无效探索的空间；没有因此添加自动调用拦截。第二轮两项指标并行、评估时间相差约 8ms，但没有显式传同一个 time，正文也未写绝对评估时间，提示词仍不是完全可保证的约束。

## 补充回归发现的未解决问题

### 1. 结构化结果被进度文字覆盖（确定性工程问题）

Pod 用例 `917b974660bb4733` 实际调用 execute_pod_promql，工具成功返回数据，但 final 只有“已按 Pod 的实际内存工作集指标查询；下面给出当前采样值及时间。”，最终被标 partial。

代码路径：AICall 更新先保存 `structured_response` 到 final_content，随后处理同一更新中的 AIMessage.content，又用可见进度文字覆盖 final_content。外层 Query 读取 response.result，因此丢失结构化结果。

已用隔离 mock 复现：同一更新同时含合法 Pydantic structured_response 和非空进度文本；result.structured_response 正确，但 result.result 被覆盖。这个新增复现测试失败，**不计入上述基线 1714 通过**。

建议下一步保持已有结构化响应权威性，不让进度文字覆盖；不需要加总结 LLM、不生成兜底答案。本轮未扩大到该输出接收链路修复。

### 2. Pod 聚合仍可能重复计数（既有采集问题与模型查询问题）

相同 Pod 问题重试 `ddb747482b894cfa` 成功生成结构化答案，但模型使用未按采集来源筛选的 sum by(namespace,pod)，将 90980352 bytes 报为 Pod 实际用量。

通过 MCP 按原时刻按 service 分组复核：三套来源各 30326784 bytes，合计正好三倍。工具原文和前端数值展示没有改错；查询口径仍错误。说明节点 Runbook 改善并不保证其他指标查询自动避免重复，不能将此次重复 Pod 查询评为准确性通过。

三套 kubelet 采集配置按用户确认的本轮范围保留，没有修改；未偷偷除三，也没有让 Agent 自动调整监控资源。

## 部署

- 后端：`xnet.registry.io:8443/xnet-cloud/aiops-copilot:11.0.202-query-guidance-20261009`
  - digest：`sha256:999f456076bdde402e5f4b1092885f348e0d40cd171ef08f1c606acddb52a64c`
  - Pod：`aiops-copilot-5c7ccb869-mhdfw`，2/2 Running。
- 前端：`xnet.registry.io:8443/xnet-cloud/aiops-copilot-frontend:0.1.34`
  - digest：`sha256:7ebfd5e128d4cffb38361fbe64d5e493b233005e299e6965b555eddb5e8a6a55`
  - Pod：`aiops-copilot-frontend-6f47d5d687-lkkbs`，1/1 Running。
- 两个 rollout 成功，前端代理 `/api/health` healthy，模型仍为 `openai/gpt-6-luna`。
- 镜像复用此前线上已验证的不可变依赖基础镜像，只更新 app/VERSION 和前端 dist。ConfigMap 只 merge 更新一个指标手册键；旧 ConfigMap 数据已本地留档。
- 没有创建异常 case、测试 Pod 或 namespace，没有清理业务资源。

原始测试资料：`/tmp/aiops-query-guidance-20261009.YZGq5j/`。其中 owner.cookies 仅用于测试会话，不应发布整个目录。
