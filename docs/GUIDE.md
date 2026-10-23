# 部署与运维

[返回 README](../README.md)。本文以仓库中的 Makefile 和部署清单为准，不假设某台机器已配置完成。

## 1. 配套服务

- [可观测性组件](http://10.2.0.86/platform/observability)：部署指标、日志和链路后端，确认目标集群数据已进入。
- [MCP](http://10.2.0.86/wanghuhu/mcpstander)：配置 Kubernetes 和可观测后端访问，再部署工具服务。
- [前端](http://10.2.0.86/wanghuhu/aiops-frount)：可选，指向本 Agent 的 HTTP/SSE 接口。

跨仓库的部署参数以各仓库 README 为准，不要求源码目录必须相邻。Agent 需要可达的 MCP 地址，而不是读取 MCP 源文件。

## 2. Agent 配置

| 文件 | 需要核对 |
|---|---|
| 本地 deploy/secrets/core.yaml | 模型地址、模型名、API Key、实际上下文容量 |
| [deploy/configmap/config.yaml](../deploy/configmap/config.yaml) | MCP SSE 地址、工作流、语言、修复策略 |
| [deploy/configmap/runbooks.yaml](../deploy/configmap/runbooks.yaml) | 排障知识及目录，挂载后由 fetch_runbook 读取 |
| [deploy/k8s-simple.yaml](../deploy/k8s-simple.yaml) | 主服务、A2A、initContainer 镜像；PVC、资源、端口 |
| [deploy/rbac.yaml](../deploy/rbac.yaml) | Agent ServiceAccount 权限 |
| [Makefile](../Makefile)、[VERSION](../VERSION) | 镜像仓库与发布版本 |

缺少 Secret 文件时，可复制 [Secret 示例](../deploy/secrets/core.yaml.example) 到
`deploy/secrets/core.yaml`，将占位内容换成真实配置，勿提交。模板以 `.example` 结尾，
`kubectl apply -R` 不会应用它，不会用占位值覆盖真实 Secret；已有本地配置无需覆盖。结构如下：

~~~yaml
apiVersion: v1
kind: Secret
metadata:
  name: aiops-secret
  namespace: aiops
type: Opaque
stringData:
  LLM_API_KEY: "<API key>"
  LLM_MODEL: "<provider/model>"
  LLM_API_BASE: "<OpenAI-compatible API base>"
  MODEL_CONTEXT_WINDOW: "<实际上下文 token 数>"
  LOG_LEVEL: "INFO"
~~~

A2A 可增加 A2A_API_TOKEN。模型需要支持工具调用；配置中的 llm.extra_body 是模型服务特定参数，不支持 Qwen chat_template_kwargs 的服务应移除或改成对应参数。

### 模型循环的配置旋钮（config.yaml `llm` / `workflow`）

这些参数决定小模型在工具循环里的稳定性，全部是配置而不是代码常量；换模型后按 `run_report.md` 的观测调整，不要为具体故障类型加规则。

| 键 | 当前值 | 作用 |
|---|---|---|
| `llm.output_tokens.agent / delivery / compaction / router` | 4000 / 10000 / 3000 / 1200 | 各类调用的 `max_tokens` 预留：工具循环单轮、无工具结构化交付、压缩摘要、意图路由。被截断（`finish_reason=length`）的轮次不进入收卷材料。环境变量 `AICALL_*_MAX_OUTPUT_TOKENS` 可覆盖单项 |
| `llm.agent_guards.max_tool_calls_per_turn` | 16 | 单条模型消息最多执行的工具调用数，超出部分不执行并提示 |
| `llm.agent_guards.max_identical_calls` | 3 | 同一工具+参数在一个阶段内最多重复次数：重复不执行、只回"结果未变化，数据已齐全请直接作答"；再多一次即停止本阶段并基于已有材料交付（报告 `repeat_limit_stop`） |
| `llm.agent_guards.repeat_page_chars` | 3000 | 首次结果被截断时，重复同一调用改为返回原始结果的下一段 |
| `llm.history_reasoning_field` | `reasoning` | 工具循环内把前几轮的模型 reasoning 以该请求字段回传。Qwen3 对话模板只渲染最后一条用户消息之后的 assistant reasoning，不回传时模型会复发上一轮的同一调用；vLLM 0.19 + Qwen3.6 读 `reasoning`，旧 Qwen3 模板读 `reasoning_content`，DeepSeek 拒收该字段时留空关闭 |
| `llm.structured_tool_choice` | `auto` | 结构化交付（RCA/结论/修复方案 JSON）的函数调用方式。`auto`：schema 作为唯一工具、`tool_choice=auto`，模型按原生格式写参数，服务端 Pydantic 校验，被拒的原始回复归档到 `structured/<node>-rejected-NNN.json`（含 `finish_reason`、usage、原始参数）；`named`：`with_structured_output` 指名 tool_choice，vLLM 走语法约束解码，实测 Qwen3.6 在约束下不转义字符串内双引号，首个内层引号即截断字段、后续字段丢失（run 6ec40015e1024f8a） |
| `llm.no_thinking_nodes` | `[]` | 以内部（不带 thinking）设置运行工具循环的节点；Qwen3.6 实测关 thinking 后工具规划退化，保持为空 |
| `llm.internal_extra_body` | 关 thinking + instruct 采样 | 只用于路由、压缩、结构化收卷等内部调用 |
| `workflow.max_steps.<node>` | 48 / 64 | LangGraph 递归上限，到顶进入结构化收卷而不是丢弃结果 |
| `workflow.context_compaction.recent_keep_interactions / recent_keep_ratio / summary_output_ratio` | 2 / 0.06 / 0.08 | 压缩"重前期"：近期原文最多保留 2 次完整交互（最新一次 ≤ 窗口 15%，其余 ≤ 窗口 6%），较早历史的工作记忆预算 = 窗口 × 8% |
| `workflow.evidence.parallel.max_workers` | 10 | 多 Pod 取证 lane 并发（上限 16） |

每个护栏触发都会在 `run_report.md` 的"发现"里出现，并在最终回答的 `missing` 中如实标注"执行未完成"的原因，不会伪装成完整结果。

### 修复安全控制（高危命令黑名单 / 审批与自动执行开关 / 恢复观察）

| 能力 | 怎么看、怎么试 |
|---|---|
| 高危命令规则 | `GET /repair/policy` 列出生效规则（禁止动词、强制/批量参数、禁止写入的资源、容器内禁止命令）；`POST /repair/policy/check {"commands":[...]}` 逐条返回 `allowed/rule/reason`，**不执行**。前端修复面板只展示执行方式与拦截规则，命令检查与模式切换通过接口进行。规划、执行预检、检查接口共用一套引擎，拒绝时带规则名并写审计 |
| 人工审批 | `mode: review`（配置默认）：每个动作先出现审批请求，批准后执行审批时的命令快照；拒绝、超时（`approval_timeout_seconds`）、取消都不执行 |
| 自动执行开关 | `PUT /repair/policy/mode {"mode":"auto","reason":"…","ttl_minutes":30}`，请求头 `X-AIOps-Admin-Token`（Secret `AIOPS_ADMIN_TOKEN`，未配置则开关不可用）。覆盖到期自动回到配置值；`DELETE` 立即恢复。只影响之后创建的任务；任务记录 `mode` 与 `mode_source`，命令事件带 `approval: "auto"` 或审批 ID |
| 审计 | `GET /repair/audit?kind=mode_changed|approval_decided|command_executed|command_denied`（管理员令牌或原会话 Cookie）；文件 `repair_records/audit.jsonl` |
| 恢复观察与超时 | 命令执行完后只读轮询目标 Pod（`workflow.remediation.recovery`），`recovered` / `not_recovered`（超时反馈，附最后一次观测）/ `needs_followup`；整体执行时限 `max_duration_seconds` 到时终态 `timeout` |

验收脚本（对运行中的服务执行，打印 PASS/FAIL 表，任一 FAIL 退出非零）：

```bash
tests/acceptance/sprint1_repair_plan.sh aiops-case-09          # 从诊断报告进入修复 → 对象/原因/命令 → 对话修改生成新版本
tests/acceptance/sprint2_policy_and_switch.sh                  # 黑名单 24 条高危命令全拦 + 12 条合规放行；开关需令牌、带 TTL、写审计
tests/acceptance/sprint2_policy_and_switch.sh aiops-case-09    # 追加真实链路：review 等待审批→拒绝不执行；auto 直接执行并标记
tests/acceptance/sprint3_scenarios.sh all                      # 重置 c06/c09/c11 → 诊断 → 修复 → 恢复观察 → kubectl 复核
```

当前 MCP 默认使用集群 DNS，例如 http://mcp-server-manager.mcp.svc.cluster.local:8100/sse。外部 MCP 要改为可达地址，并核实查询的是目标集群。

清单申请 aiops-reports-pvc，容量 20Gi、ReadWriteOnce；需要默认 StorageClass 或匹配 PV。修改仓库前缀时同步核对 Makefile 与清单：版本替换只匹配 Makefile 当前定义的镜像前缀，initContainer 镜像不会跟随主镜像版本更新。

## 3. 发布与验证

部署、升级、多集群和边缘 runner 的命令统一见 [README 部署](../README.md#部署复制即用)，这里只补充细节：

- `make build push` 包含主服务和 A2A 两个镜像，不包含前端和 MCP。
- `make deploy` 会更新清单里的镜像版本和 `A2A_PUBLIC_URL`，递归应用 `deploy/`，然后等待滚动更新完成；同一命名空间有前端时会顺带重启前端，刷新后端 DNS。所以不要把临时 YAML 或备份放进 `deploy/`。
- A2A 对外地址默认取第一个 Node 的 InternalIP。需要时显式指定：`make deploy A2A_PUBLIC_HOST=<节点IP>`，或 `A2A_PUBLIC_URL=https://<域名>`。
- 健康检查可达，不代表可观测后端都正常：

~~~bash
curl -fsS http://<节点IP>:30800/health              # version、mcp_failed_servers
curl -fsS http://<节点IP>:30800/api/v1/mcp/status   # 各 MCP 服务连接状态
curl -fsS http://<节点IP>:30801/.well-known/agent-card.json
~~~

### 日常变更、卸载与可选变量

| 场景 | 命令 |
|---|---|
| 改了 `config.yaml`、Runbook 或 `core.yaml` | 单集群 `make deploy`，多集群中心 `make deploy-mc`（Agent 仓库） |
| 新增一个边缘 | 中心：`make mc-discover` → 更新 `clusters.mc.yaml` → Agent 仓库和 MCP 仓库各执行 `make deploy-mc` → `make edge-deploy EDGE=<新边缘>` |
| 修改高危命令规则（`workflow.remediation`） | 中心 `make deploy-mc`，并对每个边缘重新执行 `make edge-deploy`（规则随 runner 下发） |
| xnet 证书轮换 | Agent 仓库和 MCP 仓库各执行 `make deploy-mc` |
| 使用运维提供的专用 xnet 证书 | `make mc-init XNET_CERT_DIR=<含 cert.pem、key.pem、ca.pem 的目录>` |
| 查看日志 | `kubectl -n aiops logs deploy/aiops-copilot -c aiops-copilot -f` |
| 卸载 | 各仓库执行 `make delete`（保留报告 PVC）；边缘执行 `make edge-delete EDGE=<别名>` |

可选变量（加在 make 命令后面，例如 `make deploy-mc MC_A2A_PUBLIC_URL=https://aiops.example.com`）：

| 变量 | 默认 | 说明 |
|---|---|---|
| `CENTER_KUBECONFIG` | `~/.kube/aiops-mc/center`，不存在时用当前上下文 | 中心集群 |
| `EDGE` | 无，必须指定 | `EDGE=edge-88` 使用 `~/.kube/aiops-mc/edge-88`；`EDGE=local` 使用当前上下文 |
| `RUNNER_LEVEL` | `2` | runner 权限等级 1 / 2 / 3 |
| `A2A_PUBLIC_HOST` / `MC_A2A_PUBLIC_URL` | 本集群第一个节点（多集群跳过 xnet 虚拟 Node） | Agent Card 里对外公布的 A2A 地址（单集群 / 多集群中心） |
| `MC_SECRET_FILE` | 有 `deploy-edge/center/secret.yaml` 就用它，否则用 `deploy/secrets/core.yaml` | 中心的模型配置；同一台机器同时部署单集群和中心、两边模型不同时使用（该文件不入库） |
| `MC_CLUSTERS_FILE` | `deploy-edge/clusters.mc.yaml` | 集群配置 |
| `MC_KEY_FILE` | `~/.kube/aiops-mc/runner.key` | runner 签名密钥；本机没有时从中心取回 |
| `MC_LOAD_HOSTS`、`MC_PULL_POLICY` | 无、`Always` | 仅用于测试环境：镜像仓库推不上去时，经 SSH 把镜像导入节点，例如 `SSHPASS=… make deploy-mc MC_LOAD_HOSTS=10.2.5.85` |

kubeconfig 只在部署时使用。运行时中心只用自己 Pod 的 ServiceAccount，边缘只用 runner 的 ServiceAccount。

## 4. 配置更新、日志与卸载

~~~bash
# 配置或 Runbook 修改后，重启使进程重新加载
kubectl apply -f deploy/configmap/ --recursive
kubectl apply -f deploy/secrets/ --recursive
make restart

# 查看主服务日志
kubectl logs -n aiops deployment/aiops-copilot -c aiops-copilot -f
~~~

RBAC 由 Kubernetes API 实时执行，权限变更通常不需要重启 Pod；进程加载的配置、Secret 环境变量和 Runbook 则应按上述步骤更新。

升级不需要先卸载。确需停用服务时，make delete 删除主 Deployment、Service、RBAC、Secret 和 ConfigMap，保留 namespace、PVC/PV；它不是清空报告的命令。删除 namespace 会连带删除其中资源及 PVC，必须另行确认数据备份，不作为常规升级步骤。

## 5. 权限边界

自动修复当前默认为关闭，但这不等于所有已接入工具只读。生产环境需同时约束 MCP 工具暴露、ServiceAccount、后端凭据和 API 入口。

若 MCP 配置通过 exec 进入已有后端 Pod 查询，需给该 MCP 身份对应 namespace 的 pods/exec create 权限；这不是 pods create，不会因此创建新 Pod，但 exec 本身允许执行命令，应限制目标范围。撤销 exec 可能使日志与链路查询失效。具体权限由 MCP 仓库管理，本仓库的 Agent RBAC 不能替代它。

测试 Case 由操作者的 kubectl 身份部署，与诊断 Agent 的权限分开。

## 6. 多集群与 A2A

- **多集群**：同一套镜像，挂载集群配置（`make mc-init` 生成的 ConfigMap `aiops-clusters`）就是多集群，不挂载就是单集群。单集群的工具定义、接口和行为不变。部署见 README，设计见[多集群设计](multi-cluster-design.md)。
- **A2A**：单集群和多集群使用同一个 Agent Card 和同一套调用方式。多集群下，问题没写明集群时，任务会进入 `input-required` 并附上反问，调用方在同一个任务里回复即可继续。详见 [A2A 指南](a2a.md)。

## 7. 排查入口

| 现象 | 优先检查 |
|---|---|
| Pod Pending | PVC/StorageClass、资源和调度事件 |
| 工具缺失或连接失败 | MCP enabled、地址、端口、网络及服务版本 |
| 指标 empty | exporter 抓取、指标名、标签、时间窗 |
| 日志/链路 error | 后端连接、凭据、exec 权限、索引与 selector |
| 日志/链路 empty | 容器是否启动、流量、采集延迟、查询条件及埋点 |
| 报告与现场冲突 | run_id、Pod UID、时间窗、原始归档；不能用旧报告替代当前观测 |

报告路径、组 ID 和 Langfuse 定位见[核心流程与模块架构](ARCHITECTURE.md#8-归档布局)。

- 验收：高危命令黑名单拦截的标准测试流程见 [acceptance-blacklist.md](acceptance-blacklist.md)。
