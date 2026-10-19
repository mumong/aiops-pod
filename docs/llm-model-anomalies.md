# LLM 自身异常排查手册（Qwen3.6-35B-A3B / vLLM 0.19）

> 整理日期：2026-10-19。目的：遇到"模型行为不对"时，先按本文区分是**模型本身**、**推理服务（vLLM/网关）**、**采样配置**还是**我们的工程**造成的，再决定改哪里。
> 配套文档：`docs/run-diagnostics.md`（运行报告怎么读）。

## 1. 当前环境

| 项 | 值 | 怎么核对 |
|---|---|---|
| 模型 | `Qwen3.6-35B-A3B`（MoE，总 35B，每 token 激活约 3B） | `GET /health` 的 `model` 字段 |
| 链路 | robusta → LiteLLM 网关 `http://10.2.0.54:4000/v1` → vLLM | Secret `aiops-secret` 的 `LLM_API_BASE` / `LLM_MODEL`（不要打印 key） |
| vLLM | `0.19.0`（直连 `http://10.2.0.98:8005/version`） | `curl --noproxy '*' http://10.2.0.98:8005/version` |
| 上下文 | 网关 54000；直连 vLLM `max_model_len=62000` | `MODEL_CONTEXT_WINDOW` |
| 网关上的其他模型 | Qwen3.8-27B、Qwen3.6-27B-AWQ、Qwen3-Next-80B-A3B-Instruct、Qwen3-32B-AWQ | `GET $LLM_API_BASE/models` |
| 未知（需运维确认） | vLLM 的 `--tool-call-parser`、`--reasoning-parser`、是否开 MTP/推测解码；LiteLLM 是否注入默认采样参数 | 服务端启动参数 / 网关配置 |

**当前采样相关配置**（`deploy/configmap/config.yaml` → `llm`）：

| 调用类型 | thinking | 发送的采样参数 | 实际生效（推断） |
|---|---|---|---|
| 工具循环（layer / evidence / query_collect / remediation） | 开 | 无（`extra_body: {}`） | vLLM 默认读模型 `generation_config.json`：temperature 1.0、top_p 0.95、top_k 20，**presence_penalty 0** |
| 内部调用（路由、结构化交付、压缩） | 关 | `internal_extra_body`：temperature 0.7、top_p 0.8、top_k 20 | 同左，presence_penalty 0（有意未设，担心扭曲 JSON） |

> "vLLM 默认读 generation_config"是按 vLLM 默认行为推断，未看到服务端参数，可信度中。

## 2. 官方推荐（Qwen3.6-35B-A3B 模型卡）

来源：<https://huggingface.co/Qwen/Qwen3.6-35B-A3B>

| 模式 | 推荐采样 |
|---|---|
| Thinking，一般任务 | temperature=1.0, top_p=0.95, top_k=20, min_p=0.0, **presence_penalty=1.5**, repetition_penalty=1.0 |
| Thinking，精确编码 | temperature=0.6, top_p=0.95, top_k=20, min_p=0.0, presence_penalty=0.0 |
| Non-thinking（Instruct） | temperature=0.7, top_p=0.80, top_k=20, min_p=0.0, **presence_penalty=1.5** |

- 原文："you can adjust the `presence_penalty` parameter between 0 and 2 to reduce endless repetitions"；过高可能导致语言混杂、性能略降。
- `generation_config.json` 只有 temperature 1.0 / top_k 20 / top_p 0.95，**不含 presence_penalty**（<https://huggingface.co/Qwen/Qwen3.6-35B-A3B/raw/main/generation_config.json>）。不显式发送就等于 0。
- `preserve_thinking`（`chat_template_kwargs`）：Qwen3.6 训练时保留历史思考，默认只保留"最后一条用户消息之后"的思考（interleaved thinking）；模型卡称对 agent 场景尤其有益。我们目前没用它，而是自己通过 `llm.history_reasoning_field: reasoning` 回传当前工具循环内的思考。
- 推荐 vLLM 启动参数：`--reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder`。

## 3. 异常类型速查

每种异常给出：现象 → 在归档里怎么认 → 已观测的运行 → 可能原因（按层） → 外部出处。

归档位置：Pod 内 `/tmp/aiops/reports/context_archives/<run_id>[-gN]/`；报告：`GET http://10.2.0.48:30800/runs/<run_id>/report.md`。

### A. 重复调用同一工具 / 照抄上一批调用

- **现象**：同一工具同一参数被反复调用；整批（如 6 个）调用原样再发一遍；最终 `step_limit` 或 `idle_round_stop`。
- **怎么认**：报告"发现"里有 `identical_call_repeats`、`idle_round_stop`、`step_limit`；`ledger/<node>.json` 的 `tools[].guard` 为 `repeat_notice` / `repeat_page`；`requests/<node>-NNN.json` 中 ai 消息的 `reasoning_tail` 写"现在提交最终结果"，但 `tool_calls` 是旧工具。
- **已观测**：
  - `7f975a3dda15410d`（节点 CPU/内存查询）：16 轮、31 次调用、14 次重复；第 10 轮起数据已齐，思考写"提交最终结果"，实际发出 `query_pod_lifecycle`/`kubectl_describe`/`TodoWrite`；第 15、16 轮照抄第 10 轮的 6 个调用；撞 `step_limit`。
  - `b9df540f00214480`：最后一轮 5 个调用全部重复，`idle_round_stop`。
- **原因分层**：
  - 模型：意图与动作不一致（想提交、却调别的工具）；自我强化的重复（上下文里重复越多越容易继续重复）；3B 激活参数在 17+ 个工具里选对"提交"工具能力弱。
  - 推理服务：vLLM Qwen3 解析器可能把思考里"引用的"工具调用格式当成真实调用，凭空多出重复调用（vLLM #58147，报告于 0.28，0.19 是否同样受影响未核实）。
  - 采样配置：工具循环未设 presence_penalty（官方用它抑制重复）。
  - 我们的工程：
    1. 大输出压缩（如 `kubectl_describe` 7841 → 348 字符），重复调用会返回原文下一段（`agent_guards.repeat_page_chars: 3000`），**等于奖励重复**；
    2. 止损只认"整轮全部是已答调用"（`finalize_on_idle_round`），混入分页结果的轮次不算，一直跑到步数上限；
    3. 结构化提交（`QueryAnswer` 等）通过 LangChain ToolStrategy 作为工具之一挂在工具列表里，与业务工具并列；
    4. 简单查询也挂了 `TodoWrite` 等无关工具；
    5. 回传思考（`history_reasoning_field`）让"提交最终结果 → 调错工具"的模式出现在上下文里，可能加重照抄（**未验证**）。
- **出处**：
  - Xu et al., NeurIPS 2022, *Learning to Break the Loop*：句级重复具有自我强化效应，模型偏好重复上一句。<https://arxiv.org/pdf/2206.02369>（可信度高）
  - *Mitigating the Learning Bias towards Repetition by Self-Contrastive Training*，复现上述效应。<https://arxiv.org/pdf/2307.01542>
  - *Focused ReAct*：ReAct 的主要问题之一是重复循环，提出检测到重复动作即提前停止。<https://arxiv.org/html/2410.10779v1>
  - Cemri et al., *Why Do Multi-Agent LLM Systems Fail?*（1642 条轨迹）：失败主要源于系统设计和协作，而非仅模型能力。<https://arxiv.org/html/2503.13657v3>
  - vLLM #58147（解析器把引用的工具格式变成真实/重复调用，未修复）。<https://github.com/vllm-project/vllm/issues/58147>
  - Qwen3.6 社区无限循环/工具调用失败报告：<https://github.com/jundot/omlx/issues/934>、<https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/discussions/5>、<https://huggingface.co/Qwen/Qwen3.6-27B/discussions/13>

### B. 一轮思考耗尽输出额度、0 个工具调用

- **现象**：某轮 `output_tokens` 等于上限（`llm.output_tokens.agent: 4000`），耗时 70–100 秒，`tool_calls=0`；阶段以 `no_structured_output` 结束，或直接返回"本次结果整理未返回内容，请重试"。
- **怎么认**：报告"发现"里有 `long_model_round`（output_tokens=4000）、`empty_structured_delivery`；`ledger/<node>.json` 的 `rounds[]` 某轮 `output_tokens=4000, tool_calls=0`。
- **已观测**：`1bbfc5ea441345ba`（第 1 轮 70 秒、4000 token、0 调用，直接失败）；`411cbba3bf2e4b74-g4`（第 2 轮 70 秒）；`918cf2c77cc5498c-g1`（第 1 轮 98 秒）。2026-10-16 统计约 3/5 次运行出现。
- **原因分层**：
  - 模型：思考过长、绕圈（社区报告 Qwen3.6 反复回到同一分析步骤）。
  - 推理服务：**vLLM 0.19** + `qwen3` 推理解析器 + `qwen3_coder` 工具解析器，模型把工具调用写在 `<think>` 里时会被整体当作思考，`tool_calls` 为空（vLLM #39056，有人称 0.18 起出现、0.17 正常、0.24 才基本修复，单一来源）。**版本与我们一致，症状吻合，尚未确认是本因。**
  - 采样配置：同 A。
  - 我们的工程：这种轮次目前不会自动重试（候选修复"A：截断且 0 调用时重试一轮"，待定）。
- **出处**：vLLM #39056 <https://github.com/vllm-project/vllm/issues/39056>；LM Studio #2045（模型在思考里调用工具）<https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/2045>；vLLM agentic-api #443（Qwen3.6 生成过量、输出 token 耗尽）<https://github.com/vllm-project/agentic-api/issues/443>

### C. 结构化交付字段被截断（命令内引号处断开）

- **现象**：修复方案的 `execute_command` 在 `-p='[{"` 处断掉，`actions` 整体丢失。
- **怎么认**：`structured/<node>-rejected-NNN.json` 的 `arguments` 在内层引号处结束。
- **原因**：指名 `tool_choice`（或 `required` / `json_schema`）→ vLLM 语法约束解码 → Qwen3.6 不转义字符串内双引号。属于**推理服务 + 模型**的组合问题。
- **现状**：已规避，`llm.structured_tool_choice: auto`（robusta 12.0.41）。换模型或网关时需对照 `auto` / `named` 复测。
- **已观测**：`6ec40015e1024f8a`。

### D. 答案写成正文、没有调用提交函数

- **现象**：内容正确的 Markdown 直接写在正文，没有调用 `QueryAnswer` 等函数，被判"没有调用函数"后重试，多花一轮。
- **怎么认**：`structured/<node>-rejected-NNN.json` 的 `error` 为"没有调用函数 …"，`content_head` 是完整答案。
- **已观测**：`b9df540f00214480`。
- **原因**：模型（auto 模式下可以选择不调用工具）；属于可接受的偶发失败，已有带反馈的重试。

### E. 工具参数结构写错（字段与记录类型不匹配）

- **现象**：`query_pod_lifecycle` 报 "Unknown fields for this record_type" 或 "group_by must name an available scalar field"，有时原样重发。
- **已观测**：`b9df540f00214480`、`411cbba3bf2e4b74`、`5854968ca9d04685`（导致只发现 1 个异常 Pod）。
- **原因**：模型（小模型写多层查询参数易错）+ 工程（Pod 级关键字段如 `deletion_timestamp`、`finalizers` 需模型主动点名才返回）。

### F. 依据不足的推断（例：Terminating 判成 OOM）

- **现象**：`aiops-case-11` 实为 finalizer 阻塞删除，被判为"内存不足 OOMKilled"或"Readiness 失败触发 137"。
- **已观测**：`411cbba3bf2e4b74-g4`、`918cf2c77cc5498c-g4`。
- **原因**：模型（终止原因写的是 `Error` 而不是 `OOMKilled` 的反证被忽略）+ 工程（layer 交接问题已带入"137 + 96Mi"的方向；从未取到 finalizers）。

## 4. 排查流程

1. **看报告**：`curl --noproxy '*' http://10.2.0.48:30800/runs/<run_id>/report.md`，按"发现"里的代码对照第 3 节归类。
2. **拷归档**：
   ```bash
   P=$(kubectl -n aiops get pods -o name | grep aiops-copilot- | grep -v frontend | head -1); P=${P#pod/}
   mkdir -p /tmp/run && kubectl -n aiops exec $P -c aiops-copilot -- \
     tar cf - -C /tmp/aiops/reports/context_archives/<run_id> . | tar xf - -C /tmp/run
   ```
   并发 lane 的归档在 `<run_id>-g1` … `-gN`。
3. **看每轮**：`ledger/<node>.json` → `rounds[]`（耗时、output_tokens、tool_calls）和 `tools[]`（guard、raw_chars vs summary_chars）。
4. **看意图与动作**：`requests/<node>-NNN.json` 中 ai 消息的 `reasoning_tail` 与 `tool_calls` 是否一致。
5. **看被拒交付**：`structured/*-rejected-*.json`（`finish_reason`、`arguments`、`error`、`content_head`）。
6. **判层**：
   - 换参数（presence_penalty）明显改善 → 采样配置；
   - 换 vLLM 版本 / 解析器明显改善 → 推理服务；
   - 同一请求在其他模型（如 Qwen3.8-27B）上不出现 → 模型；
   - 与压缩、分页、止损、工具清单相关 → 我们的工程。

## 5. 待做的对照实验（只读，不改线上配置）

| # | 实验 | 方法 | 判据 |
|---|---|---|---|
| 1 | 核对服务端 | 运维提供 vLLM 启动参数（tool/reasoning parser、MTP）和 LiteLLM 默认参数 | 是否命中 vLLM #39056 / #58147 的条件 |
| 2 | presence_penalty | 同一问题（如"查询我各个节点的cpu和内存使用率"）在 0 与 1.5 下各跑 10 次 | 重复调用次数、"想提交却调别的工具"比例、4000-token 空轮比例 |
| 3 | preserve_thinking | 关闭 `history_reasoning_field`，改用 `chat_template_kwargs.preserve_thinking: true` | 同上 |
| 4 | 换模型 | 同一请求改用 Qwen3.8-27B | 区分模型与服务端问题 |
| 5 | 关闭重复分页 | `agent_guards.repeat_page_chars: 0` | 重复调用是否减少 |

## 6. 与同事环境对比时要问的问题

- 模型名和量化方式；vLLM 版本；`--tool-call-parser` / `--reasoning-parser`；是否开 MTP。
- 是否开 thinking；是否按模型卡设置 presence_penalty。
- 一次挂多少工具、单次任务多少轮工具循环。
- 工具输出是否被截断或压缩，是否有重复调用分页之类的机制。
- 是否使用 `preserve_thinking`，或自行回传历史思考。

## 7. 相关配置项

| 配置 | 位置 | 作用 |
|---|---|---|
| `llm.extra_body` | config.yaml | 工具循环请求附加字段（当前为空，未发送采样参数） |
| `llm.internal_extra_body` | config.yaml | 内部调用：关 thinking + 采样参数 |
| `llm.history_reasoning_field` | config.yaml | 工具循环内回传思考的字段名（`reasoning`） |
| `llm.structured_tool_choice` | config.yaml | 结构化交付方式（`auto` 规避 C 类问题） |
| `llm.output_tokens.agent` | config.yaml | 单轮输出上限（4000，限制 B 类问题的耗时） |
| `llm.agent_guards.*` | config.yaml | 重复上限、重复分页、空转收尾等护栏 |
| `workflow.max_steps.*` | config.yaml | 各节点步数上限 |
