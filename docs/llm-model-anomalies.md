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
