# AIOps Copilot 项目交接说明（意图 + 技术路线 + 现状）

本文用于把当前项目背景、你的真实诉求、已落地方案、遗留问题，完整交给下一位 AI 或工程师继续执行。

## 1. 文档目标

- 说明“你到底想做什么”，避免下一位 AI 误解方向。
- 说明“项目在改造前是什么样子”（基于 `git` 基线）。
- 说明“为什么采用当前技术路线，而不是其他方案”。
- 给出“下一步应该继续做什么”，保证可持续推进。

## 2. Git 基线（变更前状态）

基线分支/提交：

- 分支：`stable-temp`
- 当前 HEAD：`eab93b4`（`03 final push`）

基线核心特征（通过 `git show HEAD:<file>` 回溯）：

1. 架构层面
- 只有单集群诊断主链路（HolmesGPT + MCP），没有 A2A 主从多集群编排模块。
- `app/core/` 下不存在已跟踪的 `a2a` 目录（当前 A2A 目录为新增未跟踪内容）。

2. 部署层面
- `Makefile` 只有传统目标：`build/push/deploy/delete/restart/logs/sync-version`。
- `make deploy` 为递归 apply 整个 `deploy/`，没有“主/从角色化部署”能力，没有 `KUBE_CONTEXT` 分集群发布能力。

3. API 层面
- `/ask` 仅支持基础参数（`q/stream/format/max_steps`），缺少 A2A 控制参数（`target_scope/a2a_strict/conclusion_max_tokens`）。
- 历史 POST 表单兼容较弱（参数容错与 JSON 兜底不足）。

4. 配置层面
- 配置文件中没有稳定处理 `sub_agents` 的机制。
- Holmes `Config` 严格校验时，可能因额外字段报错退出。

5. 文档层面
- 没有“真实双集群主从部署验收”独立手册（之前只有通用说明）。

## 3. 你的真实意图（必须保持不变）

这是项目的“产品目标”，下一位 AI 不应偏离：

1. 保持单集群能力原样可用
- 你强调单集群原本“很完美”，不能被多集群改造破坏。
- 旧调用方式必须继续可用（尤其 POST 表单）。

2. 在单集群之上叠加 A2A 能力，而不是重写业务逻辑
- 主 Agent 只负责编排：把同一个问题分发给多个子 Agent。
- 每个子 Agent 继续走“原有单集群诊断逻辑”（Agent + MCP）。
- 主 Agent 只做汇总、对比、归纳。

3. 不要本地模拟，必须支持真实集群落地
- 目标是“真实 2 集群（主/从）可部署、可验收、可复现”。
- 你希望继续沿用 `make deploy` 风格，降低操作心智负担。

4. 工程质量要求
- 要有 pytest 校验，避免低级错误回归。
- 要有可观察性（日志、run_id/report_id 可追踪）。
- 要有可交付文档，可直接给他人接手。

## 4. 当前技术路线（为什么这么设计）

### 4.1 架构路线

- 采用“可选 A2A 编排层”：
  - 子 Agent：`sub_agents.enabled=false`，仅单集群执行。
  - 主 Agent：`sub_agents.enabled=true`，加载 A2A 编排器。
- 路由策略：
  - `target_scope=single`：强制单集群（兼容旧行为）。
  - `target_scope=multi`：走 A2A 扇出。
  - `target_scope=auto`：由策略判断。
- 主调子时强制附带 `target_scope=single`，防止子 Agent 再次扇出形成递归。

### 4.2 部署路线

- 引入角色化 profile：
  - `deploy/profiles/sub/*`
  - `deploy/profiles/master/*`
- 引入 role-aware Make targets：
  - `deploy-sub`
  - `deploy-master`
  - `deploy-two-clusters`
- 按角色生成 `aiops-config` ConfigMap，避免手工改 YAML 出错。

### 4.3 兼容性路线

- 保持历史 `POST /ask -d q=...` 能跑。
- 新增参数安全解析，不合法参数返回 `422`（而非进程异常）。
- 对 Holmes 严格配置校验做“非 Holmes 字段清洗”，避免 `sub_agents` 导致启动失败。

### 4.4 可观测性路线

- 打通 A2A 全链路日志：
  - orchestrator start/done
  - fanout start/done
  - per-agent query start/retry/fail/success
  - run/report 存取日志
- 增加 `/a2a/runs/{run_id}` 与 `/a2a/reports/{report_id}` 追溯能力。

### 4.5 稳定性与性能路线

- A2A fanout 共享 `httpx.AsyncClient`，避免每个子调用重复建连。
- 引入分层超时和连接池参数（`A2A_TIMEOUT/A2A_CONNECT_TIMEOUT/...`）。
- 避免“仅 max_steps 改变就触发整套重初始化”的性能回归。

## 5. 已完成改造（工作树层面）

已落地的关键点：

1. A2A 模块（新增）
- `app/core/a2a/*`：registry/client/orchestrator/toolset/report_store/models/formatter。

2. 服务接入
- `app/core/service.py`：按配置启用 A2A，注入 patch，初始化 orchestrator。

3. API 增强
- `app/api/routes.py`：兼容旧 POST + 新参数解析 + A2A 回溯接口。

4. 配置安全
- `app/core/holmes/config_loader.py`：清理非 Holmes 字段（如 `sub_agents`）。
- `app/core/config_helpers.py`：增加 `resolve_registry_path` 路径解析。

5. 部署与文档
- `Makefile`：角色化部署目标 + test 目标。
- `docs/DEPLOYMENT.md`：部署与验收手册。
- `docs/REAL_CLUSTER_DEPLOYMENT.md`：真实双集群主从部署与验证（可复制命令）。
- 本文档：`docs/AI_HANDOFF_INTENT_TECH_ROUTE.md`。

6. 测试
- 新增/更新 unit tests（兼容性、配置清洗、A2A patch 兼容等）。
- 当前快速测试可通过：`make test`。

## 6. 关键问题与修复记录（按故障类型）

1. 启动崩溃：`sub_agents` 字段导致 Holmes 配置校验失败
- 表现：`Extra inputs are not permitted: sub_agents`
- 原因：Holmes 配置模型不认识扩展字段。
- 修复：加载前清洗非 Holmes 字段。

2. 启动崩溃：A2A patch 签名不兼容
- 表现：`_patched_load() got an unexpected keyword argument 'additional_search_paths'`
- 原因：holmes 新版本 loader 增加参数，patch 仍是旧签名。
- 修复：patch 改为 `*args, **kwargs` 透传，并防重复注入。

3. 主 Agent A2A 显示 0 个子 Agent
- 表现：`注册表文件不存在: /app/agents_registry.yaml`
- 原因：`registry_path` 被错误按项目根目录解析，而不是 `config.yaml` 所在目录。
- 修复：
  - 代码：`resolve_registry_path()` 优先相对 `config_file.parent`。
  - 配置：master profile 默认绝对路径 `/app/config-override/agents_registry.yaml`。

4. 当前仍在处理：主到子 health/query 超时
- 现象：`health_fail ... timeout`，A2A 报告子 Agent 不可达。
- 已验证：TCP 端口可能可达，但 HTTP `/health` 读取超时（应用层未响应或路径异常）。
- 结论：A2A 逻辑已通，当前主要是“跨集群网络/子端服务响应”问题，不是编排框架逻辑错误。

## 7. 当前真实部署状态（你最近一轮）

根据实际日志和命令反馈：

- 主 Agent 已启动，A2A 工具集已加载。
- 主 Agent 配置中子 endpoint 为 `http://10.2.0.24:30800`。
- A2A 健康检查可执行，但结果是 `reachable=0/unreachable=1`（timeout）。
- 子 Agent 直接访问时可返回单集群诊断结果（说明子端本身具备工作能力）。

这说明：

- “主从架构改造本身”基本成立；
- “主到子链路稳定性”仍是验收阻塞项（主要在网络与运行时层）。

## 8. 技术路线结论（给下一位 AI 的边界）

下一位 AI 必须遵守：

1. 不要推翻主从方案
- 保持“主编排 + 子单集群执行 + 主汇总”的设计。

2. 不要破坏旧接口
- `POST /ask` 表单兼容必须保留。

3. 继续围绕真实集群
- 禁止把问题引回本地 mock 作为最终方案。

4. 优先解决稳定性而非新功能
- 先把主到子的 timeout 问题打通，再谈功能扩展。

## 9. 给下一位 AI 的可直接输入 Prompt

可将以下内容直接复制给下一位 AI：

```text
你接手的是 K8s AIOps Copilot 项目，分支 stable-temp，当前工作树含未提交改造。

请先阅读：
1) docs/AI_HANDOFF_INTENT_TECH_ROUTE.md
2) docs/REAL_CLUSTER_DEPLOYMENT.md
3) docs/DEPLOYMENT.md

项目核心目标：
- 保持单集群旧逻辑与旧 API 兼容；
- 在此基础上增加 A2A 主从多集群能力；
- 主 Agent 编排，子 Agent 仍执行单集群逻辑；
- 必须支持真实双集群 make 部署与验收。

已知关键修复已做：
- 配置清洗避免 sub_agents 校验崩溃；
- A2A patch 兼容 additional_search_paths；
- registry_path 解析修复（相对 config 文件目录）；
- 主 profile 默认 registry_path 为 /app/config-override/agents_registry.yaml。

当前阻塞问题：
- 主 Agent 对子 Agent endpoint 发生 read timeout，A2A health 显示 unreachable；
- 需要优先排查并修复跨集群 HTTP 响应链路（网络/服务/运行时），并给出可复现验收命令。

执行要求：
- 先给出最短排障路径（5-10条命令）；
- 修复后必须通过 make test；
- 更新 docs/REAL_CLUSTER_DEPLOYMENT.md 的“故障排查”章节；
- 保持旧 API 兼容，不引入破坏性改动。
```

## 10. 推荐下一步（执行优先级）

1. 固化主/子两个 context，并分别执行连通性探针（Pod 内与节点侧同时验证）。
2. 对子 Agent `/health` 超时做二分：网络层 vs 应用层（是否被长任务阻塞）。
3. 视结果决定：
- 网络层：改 endpoint 为 Ingress/LB 或补路由策略。
- 应用层：增加并发 worker 或将阻塞执行移出事件循环。
4. 通过 `make test` 与真实双集群验收命令完成回归。

