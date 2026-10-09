# 快速 Query 目标驱动提示词验收

日期：2026-10-09。结论：提示词精简及部署完成，核心读路径可用，但不是全部准确性通过；Pod 指标重复统计仍然存在。

## 修改范围

- 仅将 QUERY_COLLECT_PROMPT 改为 Role / Goal / Decision Policy / Boundaries / Completion / Output 六段。
- 主字符串 3,178 → 880 字符（减少 72.3%）；完整 system prompt 还包含目录、schema、语言片段，不能把 880 当作全部上下文。
- 不把移除规则迁移到其他公共提示词；工具参数仍靠 schema，领域查询依赖 Runbook。
- 不修改 DIAGNOSTIC_TOOL_GUIDANCE、深度提示词、路由、权限、安全模块、MCP、监控配置、工具结果处理和压缩。
- 本轮没有新增普通写操作或故障特判，没有创建测试资源。没有 commit/push Git。
- 备份：docs/prompt_backups/query_collect_20261009.txt；恢复：restore_query_collect_20261009.patch。
- 清单：docs/prompt-inventory.md，覆盖主文件全部 128 项公开常量、导入片段、别名/注册表及构造入口，区分默认路径与兼容路径。

## 自动检查

命令：`.venv/bin/python -m pytest tests/unit test/workflow/test_runbook_remediation_guidance.py -q`

结果：**1716 passed，27 个既有弃用警告**。

- 首轮 1715 passed / 1 failed：旧测试精确匹配“没有后续总结 Agent”，新文案为“没有后续总结节点”；仅更新这个提示词字面断言后全过。
- 新增测试验证六段结构、关键边界、结构化输出、备份完整性与长度；更新 4 个 Query 完整输入快照。
- 深度诊断、并发子任务和旧 Focused 输入快照未更新，测试仍通过。
- `git apply --check docs/prompt_backups/restore_query_collect_20261009.patch` 通过；没有实际恢复源码。
- `git diff --check` 通过。
- 全套单元测试包括路由与操作工具可见性，但本轮未对集群执行写操作，不声明真实创建/修复操作已验收。

## 真实测试（经前端同一个 /api 代理）

模型保持 **openai/gpt-6-luna / low**，没有改成 Qwen 或迁移模型。以下调用不是浏览器截图测试；验证了前端代理、SSE、工具详情数据与最终结构化回答。

| 问题 | run_id | 实际工具 | 耗时 | 评估 |
|---|---|---|---:|---|
| xnet 下有哪些 Pod | 98b478c7e9f84464 | 1 次 namespace Pod 列表 | 29.8s | 4 个 Pod、节点及重启数与 kubectl 复核一致 |
| 它们分别在哪些节点（同会话，不重查集群） | 549338399a52416f | 1 次 read_context_archive | 20.6s | 正确恢复四个 Pod 指代；只回读旧证据，未重查现场 |
| 集群 CPU/内存使用率 | b77322b6f7f24a8f | Runbook + 2 次 instant | 30.6s | CPU 5.64%、内存 22.54% 与同时间原始序列独立复算一致；时间对齐及来源核验见下 |
| 各节点 CPU/内存（/ask） | 0ddffcd600c849a4 | Runbook + CPU / 内存 / node_uname_info，3 次 instant 并行 | 24.8s | 3 个节点真实 instance/nodename 映射；每行数值与原始返回吻合 |
| 指定 Prometheus 空查询 | 99ad02bdde1b4576 | 1 次 instant | 19.4s | status=success、coverage=empty、parse_status=parsed，未当成零或调用失败 |
| requests / limits 知识解释，不访问集群 | dc37910c56294e45 | 0 | 16.4s | 回答 CPU 节流、内存 OOM 与调度区别；未伪称访问集群 |
| ham-nnvzq 当前实际内存 | 1f1785d7ca2e433a | 1 次 execute_pod_promql | 20.2s | **准确性失败**：将三份重复采集合计为 85.2 MiB，实际同一容器每份 28.41 MiB |
| 集群 CPU/内存，明确参考 Runbook（/ask） | 75dc744a10914c6c | Runbook + 2 次 instant | 68.3s | 正确节点整体加权口径，数值来自真实返回；两查询共用同一显式 time；未独立查询覆盖/来源 |
| 无历史“那个 Pod 的日志” | 588aa496e0874768 | 0 | 3.8s | router 请求必要的 Pod/namespace，不猜目标；此例未进入 Query 节点 |

共 9 个请求（其中 8 个进入 Query，一个直接澄清）。成功传输或合法 JSON 不等于准确性通过。

## 与前一版同模型样本比较

| 同一问题 | 旧版调用 / 耗时 | 新版调用 / 耗时 | 变化 |
|---|---|---|---|
| 集群 CPU/内存 | 8 / 57.8s | 3 / 30.6s | 少一次指标目录及额外核对查询；减少探索，也减少了来源/覆盖检查 |
| 各节点 CPU/内存 | 4 / 26.1s | 4 / 24.8s | 使用真实映射，旧版为节点列表、新版为 node_uname_info |
| 集群 CPU/内存，参考 Runbook | 6 / 39.4s | 3 / 68.3s | 工具更少但更慢；不能由短 prompt 推导整体延迟必然降低 |
| Pod 内存 | 重试曾出现三倍重复统计 | 仍出现三倍重复统计 | 不属于本次精简新增问题，但没有解决 |

旧版记录见 ../query_guidance_20261009/summary.md。不同时间、少量样本，部分新用例并发执行，不是严格性能基准，也不能统计为模型准确率提升。
第三条新请求 router 17.6s、Query 50.6s；该阶段延迟包含模型与工具等待，不能仅凭事件间隔把慢全部归因于某个模型调用。

## 重要发现与边界

### 1. 普通集群指标可复核，但模型核验仍不稳定

b77322b6f7f24a8f 的两项指标分别为 02:09:29.942 和 02:09:34.052 UTC，相差 4.11 秒；不是同一严格快照。
Agent 只做汇总查询，正文披露未提供节点覆盖数；没有核查源序列唯一性。

测试者随后按原查询时间直接读取 Prometheus 原序列：
- CPU idle rate 48 条、48 个唯一 instance/cpu，独立计算 5.638440470143291%，与报告数据一致。
- 内存 3 条、3 个唯一节点，独立容量加权 22.539430792435166%，与报告数据一致。
- 这属于验收补查，不应说成 Agent 本轮自己进行了核验。

75dc744a10914c6c 能显式对齐同一个时间，但仍仅查汇总，说明读取 Runbook 不保证执行全部适用核查。

### 2. Pod 内存重复计数：工具执行正确，查询语义有问题

真实执行：
`sum by (namespace,pod,container) (container_memory_working_set_bytes{namespace="xnet",pod="ham-nnvzq",container!="",image!=""})`

原时间 2026-10-09 02:10:49.355 UTC：
- 同一个 instance、Pod UID、容器 ID 被 3 个 service 采集；
- 每份 29,790,208 bytes = 28.41015625 MiB；
- 表达式先相加为 89,358,336 bytes，Agent 忠实展示成约 85.2 MiB，但不能叫正确的单容器实际用量。
- 本轮未读 Runbook；当前节点/集群手册的描述本身不覆盖这个 Pod 场景。

详细独立复核证据见 independent-metric-audit.json。没有按固定倍数替用户纠正；结论基于真实源身份和每份原值。
后续建议：经确认后处理重复采集归属；补足 Pod 指标查询参考知识与通用来源核验示例。不要重新往主提示词堆故障特判、强制工具链或代码除数。

### 3. 既有结构化结果被进度文本覆盖的问题仍未修改

上一轮已有隔离复现：AICall 先保存 structured_response，随后同一消息的普通文本覆盖 final_content，Query 读取 response.result 时可能丢失结构化答案。
本轮真实 Query 样本未触发；这不证明工程缺口消失。本次仅按授权调整提示词，没有偷偷修改输出链路。

### 4. 验收未覆盖

真实普通写操作、自动修复、深度诊断准确性、压力并发、长上下文压缩和浏览器完整视觉回归未在本轮重新执行。相关路径代码未修改，单元回归通过不代替其真实端到端验收。

## 部署证据

- 后端镜像：`xnet.registry.io:8443/xnet-cloud/aiops-copilot:11.0.203-query-goal-20261009`
- digest：`sha256:ec44560ac883391b58854154b854ed6bb6216d1bd6a19bbf1e696fee693e6d11`
- Pod：`aiops-copilot-5886bbfdc7-ddhd2`，2/2 Running；Deployment rollout 成功。
- 前端代理 `http://10.2.0.48:30081/api/health`：healthy，config_loaded=true，ai_initialized=true。
- 容器内实查：模型 openai/gpt-6-luna、effort=low、Query prompt 880 字符。
- 容器内 prompt SHA256：`806f11a72a0266c7d281dd2dca4511292303c2ecbe25dbbda7d7139d04e89019`。
- 前端本轮没有代码变动，沿用上一轮已部署版本；A2A sidecar、凭据、PVC、Runbook ConfigMap 均未修改。
- 临时原始 SSE/工具结果：`/tmp/aiops-query-goal-20261009.5AXXRU/`；含测试会话 Cookie，不要整目录发布。

## 恢复

源码只恢复 Query 常量：
```bash
git apply --check docs/prompt_backups/restore_query_collect_20261009.patch
git apply docs/prompt_backups/restore_query_collect_20261009.patch
```

然后重建、部署；不要回滚整个 prompts.py，以免覆盖其他修改。若需要立刻线上回到上一版本，上一镜像为 `11.0.202-query-guidance-20261009`；本轮未执行回退。
