<div align="center">

# K8s AIOps Copilot

**用自然语言诊断 Kubernetes 故障，跨集群查询数据，自动生成根因报告**

HolmesGPT · FastAPI · LangGraph · MCP · 多集群联邦

[![Version](https://img.shields.io/badge/version-4.0.3-blue)]()
[![Python](https://img.shields.io/badge/python-3.12-green)]()
[![License](https://img.shields.io/badge/license-Private-lightgrey)]()

[快速开始](#快速开始) · [架构](#架构概览) · [API 文档](#api-端点) · [配置](#配置体系) · [部署](#部署)

</div>

---

## 它能做什么

**自然语言驱动** — 用中文或英文提问，AI 自动选择工具、采集证据、输出结构化报告

**五层故障诊断** — 自动将问题分类到 L0 基础设施 / L1 集群节点 / L2 工作负载 / L3 服务网络 / L4 应用层，走针对性诊断流程

**四阶段工作流** — 问题定层 → 证据采集 → 根因分析 → 报告生成，每阶段独立 LLM 调用，实时流式输出推理过程

**多集群联邦查询** — Agent-to-Agent 智能路由，按需选择集群、并发查询、实时转发每个子集群的诊断过程，最终合成跨集群报告

**质量可量化** — 每次诊断自动输出 MTTR、根因置信度（5 维加权评分）、证据完整率、Runbook 覆盖率，所有阈值可配置

**MCP 工具生态** — 通过 Model Context Protocol 接入 kubectl、Helm、Prometheus、Elasticsearch、Bash 等任意外部工具

**Runbook 知识库** — 内置 11+ 故障手册（OOMKilled、CrashLoop、磁盘满、镜像拉取失败等），AI 自动匹配并引用

**多 LLM 支持** — 通过 LiteLLM 统一接口，支持 DeepSeek / Claude / GLM / OpenAI 等任意提供商

---

## 架构概览

```
                        用户（自然语言提问）
                              │
                              ▼
                    ┌─── FastAPI Server ───┐
                    │                      │
                    │  /ask     单集群诊断  │
                    │  /federation/ask/v2   │──── 多集群联邦
                    │  /health  /tools     │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                  ▼
    ┌── HolmesGPT 模式 ──┐          ┌── LangGraph 工作流 ──┐
    │  LLM 自主规划       │          │  定层 → 采证 → 根因   │
    │  + Tool Calling     │          │  → 报告（四阶段）     │
    └─────────┬───────────┘          └─────────┬───────────┘
              │                                │
              └────────────┬───────────────────┘
                           │
              ┌────────────┼────────────────┐
              ▼            ▼                ▼
         MCP 工具集    Runbook 知识库   质量评分引擎
       (K8s/Prom/ES)   (11+ 故障手册)  (5 维置信度)
```

### 联邦查询架构

```
  主集群 (Master Agent)
    │
    ├── LLM 分析意图 → 决定查哪些集群、问什么问题
    │
    ├── 并发查询 ──┬── 子集群 A (/ask) ── 独立诊断工作流
    │              ├── 子集群 B (/ask) ── 独立诊断工作流
    │              └── 子集群 C (/ask) ── 独立诊断工作流
    │
    └── LLM 合成 → 跨集群统一报告
```

---

## 快速开始

### 本地运行

1. 安装依赖：`pip install -r requirements.txt`
2. 设置 LLM Key：`export LLM_API_KEY=sk-xxx`
3. 启动服务：`python run.py`
4. 访问 `http://localhost:8000/docs` 查看 Swagger 文档

### K8s 部署

1. 配置 Secret：编辑 `deploy/secrets/core.yaml` 填入 LLM 凭证
2. 主集群部署：`make build push deploy-master`
3. 子集群部署：`make build push deploy-slave`

> 详细部署步骤见 [部署与使用指南](docs/GUIDE.md)

---

## API 端点

| 端点 | 说明 | 适用场景 |
|------|------|----------|
| `GET/POST /ask` | 单集群查询与诊断 | 日常使用，速度最快 |
| `GET /q/{问题}` | 路径参数快捷查询 | 浏览器直接访问 |
| `GET/POST /federation/ask` | 多集群并发查询 (v1) | 对比所有集群同一指标 |
| `GET/POST /federation/ask/v2` | Agent 智能路由 (v2) | 按需选集群，推荐多集群首选 |
| `GET /health` | 健康检查 | 监控探针 |
| `GET /tools` | 可用工具列表 | 调试 |
| `GET /runbooks` | Runbook 知识库列表 | 查看已加载的故障手册 |
| `GET /reports` | 诊断报告列表 | 历史报告查询（支持集群过滤） |

### 请求参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `q` | string | 必填 | 问题内容（中文需 URL 编码，推荐 `--data-urlencode`） |
| `stream` | bool | `true` | 流式输出（实时推送）或同步返回（等全部完成） |
| `format` | string | `text` | 流式格式：`text`（纯文本）或 `sse`（结构化事件，适合前端） |
| `max_steps` | int | `20` | LLM 最大工具调用轮数（1-100），简单查询设小、深度诊断设大 |

### 使用示例

**数据查询**
```bash
# 查询集群 CPU 使用率
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=集群 CPU 使用率是多少"

# 查看某个 namespace 下的 Pod 状态
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=查看 namespace kube-system 下所有 Pod 状态"
```

**故障诊断**
```bash
# 诊断集群问题（走完整四阶段工作流）
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=我的集群有什么问题？"

# 深度诊断，增加工具调用轮数
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=分析 production 下所有异常 Pod 的根因" \
  --data-urlencode "max_steps=50"
```

**多集群联邦查询**
```bash
# Agent 智能路由：对不同集群问不同问题
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=我想要知道 main 的内存使用率和 cluster-24 的 CPU 使用率"

# 对比两个集群
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=对比 main 和 cluster-24 的 CPU 使用率"

# v1：查询所有集群同一指标
curl -G "http://10.2.0.48:30800/federation/ask" \
  --data-urlencode "q=哪个集群 CPU 利用率最高"
```

**输出控制**
```bash
# 非流式（脚本集成，等全部完成后返回）
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=列出所有 CrashLoopBackOff 的 Pod" \
  --data-urlencode "stream=false"

# SSE 格式（前端 EventSource 解析）
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=磁盘使用率" \
  --data-urlencode "format=sse"
```

### 选择哪个端点？

| 场景 | 推荐 |
|------|------|
| 查询/诊断当前集群 | `/ask` |
| 对比所有集群某个指标 | `/federation/ask` |
| 只查指定集群或对不同集群问不同问题 | `/federation/ask/v2` |

### max_steps 调优建议

| 场景 | 建议值 |
|------|--------|
| 简单状态查询（Pod 列表、节点数量） | 5-10 |
| 常规指标查询（CPU、内存使用率） | 10-20（默认） |
| 深度故障诊断（根因分析、多维采证） | 30-50 |
| 复杂多集群分析 | 50+ |

---

## 配置体系

所有配置遵循统一优先级：**环境变量 > config.yaml > 默认值**

本地开发编辑 `config/config.yaml`，K8s 部署编辑 `deploy/configmap/config.yaml`（两份需同步）。

### 核心配置块

| 配置块 | 作用 | 关键项 |
|--------|------|--------|
| `llm` | LLM 提供商 | model、api_key、api_base（litellm 格式） |
| `toolsets` | 内置工具开关 | core_investigation、runbook 默认开启，其余由 MCP 替代 |
| `mcp_servers` | MCP 远程工具 | url、mode(sse)、description、enabled |
| `workflow` | 工作流参数 | 节点开关、rca_mode、各节点 max_steps |
| `metrics` | 质量指标 | 输出开关、达标阈值、置信度评分权重、惩罚项 |
| `federation` | 多集群联邦 | enabled、sub_agents 列表、synthesis_timeout |

### 工作流配置（workflow）

```yaml
workflow:
  rca_mode: lite          # RCA 节点调用模式
  nodes:                  # 节点启用/禁用
    layer: true
    evidence: true
    rca: true
    conclusion: true      # 不可禁用
  max_steps:              # 各节点 LLM 最大工具调用轮数
    layer: 14
    evidence: 18
    rca: 0                # lite 模式下无效（不调工具）
    conclusion: 0         # 始终无效（不调工具）
```

| 参数 | 说明 |
|------|------|
| `rca_mode` | `lite`：RCA 节点用 litellm 直接调用，基于已有证据分析，不调工具（避免重复采集）。`full`：走 HolmesGPT agentic loop，可调工具补充数据 |
| `nodes.*` | 节点开关。设为 `false` 跳过该节点，工作流自动连接相邻的启用节点。`conclusion` 强制启用 |
| `max_steps.layer` | 问题定位节点的工具调用轮数。控制 LLM 在定位阶段最多执行多少轮 kubectl/prometheus 等工具调用 |
| `max_steps.evidence` | 证据采集节点的工具调用轮数。这是最关键的参数，决定了采集证据的深度 |
| `max_steps.rca` | 仅 `rca_mode: full` 时有效。`lite` 模式下 RCA 不调工具，此值无效 |
| `max_steps.conclusion` | 始终无效。conclusion 节点用 litellm 直接生成报告，不调工具 |

### 质量指标配置（metrics）

```yaml
metrics:
  enabled: true           # 输出开关
  thresholds:             # 达标阈值
    mttr_seconds: 600
    rca_confidence: 0.8
    evidence_completeness: 0.9
  confidence_dimensions:  # 置信度 5 维评分权重
    evidence_strength:    { weight: 0.35 }
    causal_chain:         { weight: 0.20 }
    tool_coverage:        { weight: 0.10 }
    runbook_match:        { weight: 0.15 }
    llm_self_score:       { weight: 0.20 }
  penalties:              # 惩罚项
    critical_missing: 0.15
    critical_missing_cap: 0.45
    fallback_applied: 0.05
  evidence_level_weights: # 证据级别权重
    CRITICAL: 1.0
    IMPORTANT: 0.6
    SUPPLEMENTARY: 0.3
  baseline:               # 保底分
    with_evidence: 0.80
    with_root_cause: 0.75
```

| 参数 | 说明 |
|------|------|
| `enabled` | `false` 时输出只显示性能统计和诊断追踪，隐藏质量指标表和评分明细。环境变量 `METRICS_ENABLED` 可覆盖 |
| `thresholds.mttr_seconds` | MTTR 达标阈值（秒）。默认 600s = 10 分钟 |
| `thresholds.rca_confidence` | 根因置信度达标阈值。默认 0.8 = 80% |
| `thresholds.evidence_completeness` | 证据完整率达标阈值。默认 0.9 = 90% |
| `confidence_dimensions` | 置信度 5 个评分维度的权重（总和应为 1.0）。`evidence_strength`：加权证据完整率。`causal_chain`：因果链是否完整。`tool_coverage`：工具调用成功率。`runbook_match`：是否匹配到 Runbook。`llm_self_score`：LLM 自评分数 |
| `penalties.critical_missing` | 每缺失一项关键证据（CRITICAL 级别）扣多少分 |
| `penalties.critical_missing_cap` | 关键证据缺失扣分的上限 |
| `penalties.fallback_applied` | 使用回退路径（如规则引擎替代 LLM）时的扣分 |
| `evidence_level_weights` | 证据完整率计算时各级别的权重。CRITICAL 级证据权重最高（1.0），SUPPLEMENTARY 最低（0.3） |
| `baseline.with_evidence` | 有结论 + 有证据/工具调用时的最低置信度保底分 |
| `baseline.with_root_cause` | 有结论 + 有根因但无工具证据时的最低置信度保底分 |

### MCP 工具配置

MCP 是本项目的主力工具接入方式。每个 MCP Server 通过 SSE 端点提供工具，AI 根据 `description` 自动判断何时调用。

在 `config.yaml` 的 `mcp_servers` 块中添加：

```yaml
mcp_servers:
  # 工具名（自定义，唯一即可）
  my-tool:
    description: "工具描述（AI 用此判断何时调用，写清楚能力范围）"
    config:
      url: "http://mcp-server-address:8099/sse"   # MCP Server 的 SSE 端点
      mode: "sse"                                   # 固定 sse
    llm_instructions: "可选：给 AI 的额外使用提示"    # 如 "只在用户要求测试时调用"
    enabled: true                                    # false 可临时禁用
```

项目默认接入的 MCP 工具：

| 工具 | 能力 |
|------|------|
| k8s-mcp-service | kubectl get/describe/logs/events 等 K8s 操作 |
| helmcharts | helm list/status/values 等 Helm 操作 |
| bash_tool | 执行 bash 命令（需开启 BASH_TOOL_UNSAFE_ALLOW_ALL） |
| prometheus_tool | PromQL 即时查询和范围查询 |
| elasticsearch | 查询索引、搜索日志 |
| connectivity_check_tool | TCP 端口连通性检查 |

### 联邦查询配置

```yaml
federation:
  enabled: true                     # 主集群 true，子集群 false
  max_tokens_per_agent: 0           # 子集群报告压缩阈值（0=不压缩）
  synthesis_timeout: 300             # 等待子集群响应超时（秒）
  sub_agents:
    - name: "main"
      url: "http://localhost:8000"   # 主集群用容器内端口
      description: "主集群"
      enabled: true
    - name: "cluster-24"
      url: "http://10.2.0.24:30800" # 子集群用 NodePort
      description: "子集群 24"
      enabled: true
```

> 主集群 URL 必须用 `http://localhost:8000`（容器内端口），不能用 NodePort。

### 关键环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_API_KEY` | — | LLM API Key（必填） |
| `LLM_MODEL` | `deepseek/deepseek-chat` | litellm 模型 ID，格式 `提供商/模型名` |
| `LLM_API_BASE` | — | API 端点覆盖（代理或兼容端点，留空用默认） |
| `USE_WORKFLOW` | `false` | 启用四阶段工作流模式 |
| `WORKFLOW_MAX_STEPS_{LAYER,EVIDENCE,RCA,CONCLUSION}` | 3/10/8/3 | 各节点 LLM 最大迭代次数 |
| `METRICS_MTTR_THRESHOLD` | `600` | MTTR 达标阈值（秒） |
| `METRICS_RCA_CONFIDENCE_THRESHOLD` | `0.8` | 根因置信度达标阈值 |
| `BASH_TOOL_UNSAFE_ALLOW_ALL` | `false` | 允许执行所有 bash 命令 |

> 完整配置说明见 [架构与开发参考](docs/ARCHITECTURE.md)

---

## 质量指标体系

每次工作流诊断自动输出可量化的质量评估：

| 指标 | 评估方式 | 默认阈值 |
|------|----------|----------|
| **MTTR** | 从请求到报告的端到端耗时 | < 10 分钟 |
| **根因置信度** | 5 维加权评分（证据强度 35% + 因果链 25% + 工具覆盖 15% + Runbook 匹配 15% + LLM 自评 10%） | >= 80% |
| **证据完整率** | 按级别加权（CRITICAL 1.0 / IMPORTANT 0.6 / SUPPLEMENTARY 0.3） | > 90% |
| **Runbook 覆盖** | 多维评分（引用 50% + 主 Runbook 识别 30% + 结论相关性 20%） | — |

所有权重、阈值、惩罚项均可通过 `config.yaml` 的 `metrics` 块调整。

---

## 五层诊断模型

```
QUERY   数据查询    状态查看、使用率统计（非故障，走快速路径）
  L4    应用层      业务逻辑错误、配置错误、依赖服务不可用
  L3    服务网络层  Service/Ingress、DNS、NetworkPolicy
  L2    工作负载层  Pod 生命周期、镜像拉取、资源限制、探针
  L1    集群节点层  Node 状态、kubelet、容器运行时、调度
  L0    基础设施层  磁盘、内存、CPU、内核、文件系统
```

---

## 扩展

**添加工具** — 实现 MCP Server（HTTP/SSE），在 `mcp_servers` 配置块注册即可，无需改代码

**添加 Runbook** — 在 `knowledge_base/runbooks/` 创建 Markdown 文件，在 `catalog.json` 注册标题和描述

**切换 LLM** — 修改环境变量 `LLM_MODEL` 为任意 litellm 支持的模型 ID（如 `anthropic/claude-sonnet-4-6`）

**添加子集群** — 在 `federation.sub_agents` 中添加集群 name/url/description，主集群设 `federation.enabled: true`

---

## 技术栈

| 组件 | 技术 |
|------|------|
| API 框架 | [FastAPI](https://fastapi.tiangolo.com/) |
| AI 引擎 | [HolmesGPT](https://github.com/robusta-dev/holmesgpt)（Tool Calling） |
| 工作流编排 | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM 路由 | [LiteLLM](https://github.com/BerriAI/litellm) |
| 工具协议 | [MCP](https://modelcontextprotocol.io/)（Model Context Protocol） |

---

## 文档

| 文档 | 说明 |
|------|------|
| [架构与开发参考](docs/ARCHITECTURE.md) | 请求链路、目录结构、Prompt 架构、配置详解 |
| [部署与使用指南](docs/GUIDE.md) | 部署步骤、API 使用示例、常见问题 |

---

完整 Prompt 架构图
      663 -
      664 -  LLM 收到的 messages 只有两条：system + user。你的 prompts.py 里的内容和框架注入的内容，分别被塞进这两个 role 里。
      665 -
      666 -  一、messages 结构
      667 -
      668 -  messages = [
      669 -      {"role": "system", "content": <system_prompt>},   ← 第1条
      670 -      {"role": "user",   "content": <user_prompt>},      ← 第2条
      671 -  ]
      672 -
      673 -  二、System Prompt 的组装（role: system）
      674 -
      675 -  由 generic_ask.jinja2 模板渲染，按顺序拼接：
      676 -
      677 -  ┌─────────────────────────────────────────────────────────────┐
      678 -  │  role: system                                               │
      679 -  ├─────────────────────────────────────────────────────────────┤
      680 -  │                                                             │
      681 -  │  ① HolmesGPT 框架 intro（固定文本）                          │
      682 -  │     "You are a tool-calling AI assist..."                   │
      683 -  │     "Ask for multiple tool calls at the same time..."       │
      684 -  │     来源: generic_ask.jinja2 intro_enabled 块               │
      685 -  │                                                             │
      686 -  │  ② investigation_procedure（TodoWrite 调查流程指令）          │
      687 -  │     "You MUST use the TodoWrite tool..."                    │
      688 -  │     "Your FIRST tool call MUST be TodoWrite..."             │
      689 -  │     来源: _general_instructions.jinja2 → todowrite_enabled  │
      690 -  │                                                             │
      691 -  │  ③ AI Safety 指令                                           │
      692 -  │     来源: _ai_safety.jinja2                                 │
      693 -  │                                                             │
      694 -  │  ④ General Instructions（K8s 调查通用指令）                   │
      695 -  │     "use the five whys methodology..."                      │
      696 -  │     "if a runbook url is present you MUST fetch..."         │
      697 -  │     来源: _general_instructions.jinja2                      │
      698 -  │                                                             │
      699 -  │  ⑤ Toolset Instructions（各工具集的使用说明）                 │
      700 -  │     每个启用的 toolset 的 llm_instructions                   │
      701 -  │     来源: _toolsets_instructions.jinja2                     │
      702 -  │                                                             │
      703 -  │  ⑥ MANDATORY Task Management（TodoWrite 强制指令）           │
      704 -  │     "Your FIRST tool call MUST be TodoWrite..."             │
      705 -  │     "FAILURE TO UPDATE TodoList = INCOMPLETE..."            │
      706 -  │     来源: _general_instructions.jinja2 todowrite_enabled    │
      707 -  │                                                             │
      708 -  │  ⑦ ★ 你的 prompts.py ★（system_prompt_additions）           │
      709 -  │     通过 {{ system_prompt_additions }} 插入到最末尾           │
      710 -  │     来源: generic_ask.jinja2 最后一个块                      │
      711 -  │                                                             │
      712 -  └─────────────────────────────────────────────────────────────┘
      713 -
      714 -  三、User Prompt 的组装（role: user）
      715 -
      716 -  由 build_user_prompt() 函数拼接：
      717 -
      718 -  ┌─────────────────────────────────────────────────────────────┐
      719 -  │  role: user                                                 │
      720 -  ├─────────────────────────────────────────────────────────────┤
      721 -  │                                                             │
      722 -  │  ① 用户的原始问题                                            │
      723 -  │     就是 initial_user_prompt（如"集群有什么问题"）            │
      724 -  │     来源: 前端/API 传入的 question                           │
      725 -  │                                                             │
      726 -  │  ② TodoWrite Reminder（追加在问题后面）                      │
      727 -  │     "<system-reminder>IMPORTANT: You have access to         │
      728 -  │      the TodoWrite tool... FAILURE TO UPDATE TodoList       │
      729 -  │      = INCOMPLETE INVESTIGATION</system-reminder>"          │
      730 -  │     来源: get_tasks_management_system_reminder()            │
      731 -  │     ⚠️   虽然叫 system-reminder，但实际在 user message 里！    │
      732 -  │                                                             │
      733 -  │  ③ Runbook Catalog（runbook 目录索引）                       │
      734 -  │     "# Runbook Selection"                                   │
      735 -  │     "If one of the following runbooks relates to..."        │
      736 -  │     + catalog.json 的全部 runbook 描述列表                   │
      737 -  │     来源: _runbook_instructions.jinja2                      │
      738 -  │                                                             │
      739 -  │  ④ 当前日期时间                                              │
      740 -  │     来源: _current_date_time.jinja2                         │
      741 -  │                                                             │
      742 -  └─────────────────────────────────────────────────────────────┘

---

