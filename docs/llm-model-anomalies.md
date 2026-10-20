# LLM 自身异常记录（Qwen3.6-35B-A3B）

> 2026-10-19 整理。环境：Qwen3.6-35B-A3B（MoE，每 token 激活约 3B）→ LiteLLM 网关 → vLLM 0.19.0。
> 只记录有外部公开记录可佐证、不是由我们的工程造成的问题。

## 1. 工具调用陷入重复循环

**现象**：同一工具、同一参数被反复调用，甚至把上一批调用原样再发一遍；模型的思考里已经写着"数据已齐，现在提交最终结果"，实际发出的却仍是旧的工具调用，直到撞上步数上限。
**我们的运行**：`7f975a3dda15410d`（16 轮、31 次调用，其中 14 次重复）、`b9df540f00214480`。

**外部记录**：
- Qwen3.6-35B-A3B / 27B 无限循环，换到 LM Studio 才正常：[oMLX #934](https://github.com/jundot/omlx/issues/934)
- Qwen3.6-35B-A3B 即使 BF16 精度也会间歇性工具调用失败、出现循环：[unsloth GGUF 讨论 #5](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/discussions/5)
- Qwen3.6 全系列工具调用问题汇总：[Qwen3.6-27B 讨论 #13](https://huggingface.co/Qwen/Qwen3.6-27B/discussions/13)、[Qwen3.6-35B-A3B 讨论 #51](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/discussions/51)
- 官方模型卡也承认存在"无休止的重复"，并建议用 `presence_penalty`（0–2）来缓解：[Qwen3.6-35B-A3B 模型卡](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)
- 机制层面的研究：上下文里重复越多，模型越倾向继续重复（自我强化效应）：[Xu et al., NeurIPS 2022](https://arxiv.org/pdf/2206.02369)

### 1.1 机制分析（2026-10-20，基于 211 次线上运行轨迹 + Langfuse 原始返回）

**问题**：重复的是"同一工具 + 完全相同的参数"。它是在要新结果吗？为什么参数不变？

**数据**（含请求轨迹的 211 次运行，145 次出现重复，共 597 次跨轮重复 + 77 次同轮重复）：

| 重复前模型的思考内容 | 次数 | 说明 |
|---|---|---|
| 明确写着"信息已充分 / 提交最终方案 / 直接回答 / 准备输出 XxxOutput" | 153 | 不想要数据，想交卷；发出的却是旧调用 |
| 计划换参数（continue_token、where 过滤、另一个命名空间） | 46 | 想法是新查询，输出却抄了旧参数（layer 节点为主） |
| 想刷新状态（"再次确认是否恢复"） | 27 | 真的想重新观测（remediation 为主） |
| 其它 / 思考尾部未记录 | 371 | 大多没有提到要查新东西 |

重复调用等于**上一轮**调用的占 61%（327/533），落在最近两轮内的占 80%。

**Langfuse 原始返回佐证**（run `29e760da`、`54429f28`）：`reasoning_content` 为"信息已充分。提交最终方案。"，
同一条返回的 `tool_calls` 却是前几轮用过的 `kubectl_get_yaml`/`kubernetes_tabular_query`（参数逐字相同）；
`54429f28` 第 5 轮的思考里已经把 Helm Release 表格整段写完，动作仍是 `helm_list({})` 第三次。

**结论**：绝大多数重复不是"需要新结果"，而是**模型决定收尾时，输出端复制了上下文里最近的工具调用**。参数一样正是因为它是复制而不是重新组参：
现成的 token 序列在上下文里出现过多次，续写它的损失最低；Xu et al. 2022 描述的自我强化效应会让每次重复进一步提高下一次重复的概率。

**我们这边的工程因素**（不是纯模型问题）：

1. 整个工具循环运行在 `tool_choice=required` 下。LangChain `create_agent` 只要带 `response_format=ToolStrategy`，
   就把 `tool_choice` 固定为 `any`（OpenAI 兼容层即 `required`），Langfuse 的 modelParameters 可见。
   因此模型没有"不调工具、直接结束"的出口：收尾必须以调用 schema 工具（QueryAnswer / RepairDraft / EvidenceStageOutput）的形式完成，
   该工具是工具列表里最后、最长的一个；而"抄上一条调用"是更短、更熟悉的合法输出。
   `llm.structured_tool_choice=auto`（12.0.41）只改了循环结束后的补交付调用，没有改循环本身。
2. vLLM 对 `required` 的实现是语法约束解码（见下方来源），与第 3 节"指名函数时字段截断"是同一条解码路径。
3. 重复通知文本写着"请直接给出最终回答"，而在 `required` 下"直接回答"仍然必须是一次工具调用；104 次重复紧跟在通知之后。

**工程改法（已上线 12.0.63）**：`llm.loop_tool_choice`（字符串全局，或按节点映射）。`auto` 时工具循环用 `AutoToolChoiceChatOpenAI`，
把 create_agent 下发的 `any/required` 改为 `auto`；模型以文本收尾后由现有收卷路径交付结构化结果。本地 A/B（同集群、同网关、同 MCP，注入 case-04/06/09/11）：

| 场景 | required | auto |
|---|---|---|
| 轻量查询 4 题 | 3/4 partial，19 次重复 | 4/4 answered，0 重复 |
| 全集群深度诊断 | 707 s，92 次调用 / 44 次重复，1 条 lane 空转收卷 | 437 s，57 次调用 / 1 次重复，4 条 lane 正常交付 |
| 四组结论 | 4/4 正确 | 4/4 正确 |
| 修复规划 4 组 | 3/4 出方案，1 组撞重复上限失败 | 4/4 出方案，0 重复（case-04 有一次空转重试 + 校验拒收，382 s） |
| 定向诊断 case-06 | 280 s，7 次重复 | 177 s，0 重复 |

代价：正常以文本结束的阶段多一次收卷交付（约 12–30 s），`incomplete_reason=no_structured_output` 会出现在这类正常结束的报告里。

来源：[vLLM 文档 Tool Calling（required 走 guided decoding）](https://docs.vllm.ai/en/v0.10.2/features/tool_calling.html)、
[LangChain create_agent 结构化输出](https://docs.langchain.com/oss/python/langchain/structured-output)、
[LangChain 论坛：ToolStrategy + 工具时循环到递归上限](https://forum.langchain.com/t/create-agent-toolstrategy-tools-structured-output-not-working-across-models-langchain-1-0-2/2293)、
`langchain/agents/factory.py`（`tool_choice = "any" if structured_output_tools else request.tool_choice`）。

## 2. 一轮思考把输出额度用光，却没有发出任何工具调用

**现象**：某一轮把 4000 个输出 token 全部花在思考上，耗时 70–100 秒，`tool_calls=0`，这一阶段因此拿不到结果。
**我们的运行**：`1bbfc5ea441345ba`、`411cbba3bf2e4b74`（g4 lane）、`918cf2c77cc5498c`（g1 lane）；2026-10-16 的统计中约 3/5 次运行出现。

**外部记录**：
- **vLLM 0.19** 配合 Qwen3.5/3.6：模型把工具调用写在 `<think>` 里时，整段会被当作思考内容，返回的 `tool_calls` 为空，agent 循环提前结束。有报告称 0.18 起出现、0.17 正常。版本与我们一致：[vLLM #39056](https://github.com/vllm-project/vllm/issues/39056)
- Qwen3.6 生成内容过量、输出 token 被耗尽：[vLLM agentic-api #443](https://github.com/vllm-project/agentic-api/issues/443)
- Qwen3.6-35B-A3B 试图在思考块里调用工具：[LM Studio #2045](https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/2045)

> 注：vLLM #39056 属于推理服务（vLLM 解析器）的问题，不是我们的代码问题；但我们出现的现象是否就是它引起的，尚未确认。

## 3. 指定函数时结构化输出被截断

**现象**：在指定 `tool_choice` 调用某个函数时，命令中的 `-p='[{"` 在第一个内层双引号处就断掉，后面的字段（例如 `actions`）整体丢失。
**我们的运行**：`6ec40015e1024f8a`（连续 3 次都断在同一处）。改用 `tool_choice=auto` 后不再出现，网关探测可以复现。

**外部记录**：
- vLLM 上 Qwen3 系列工具解析器的问题汇总，包括参数内容丢失或被改写：[vLLM #61206](https://github.com/vllm-project/vllm/issues/61206)
- vLLM 上 Qwen3.6 工具调用出错，社区整理的修复方法：[Qwen3.6-35B-A3B on vLLM](https://allanchan339.github.io/bug-fixes/2026/04/20/Qwen36-35B-A3B-tool-calling.html)

> 注：这一条属于"vLLM 语法约束解码 + Qwen3.6"的组合问题；外部没有找到与我们现象完全相同的记录，佐证力度弱于第 1、2 条。
