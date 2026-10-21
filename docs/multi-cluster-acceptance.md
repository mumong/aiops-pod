# 多集群验收方案

状态：开发前制定（2026-10-21）。配套设计见 [多集群设计](multi-cluster-design.md)，SDD 产物（spec、plan、tasks）见 [specs/008-multi-cluster](../specs/008-multi-cluster/spec.md)，用例编号与设计 §12 一致，并在此基础上补全。

每个阶段**先写验收脚本、再开发功能**；脚本跑通、用例全部通过，才进入下一阶段。

## 1. 代码、版本与环境

### 1.1 代码在哪里改

| 内容 | 位置 | 说明 |
|---|---|---|
| AIOps、MCP、前端、边缘 runner 的全部代码 | **本机仓库**：`robusta/`、`mcpstander/`、`frountind/` | 提交后推送到 GitHub 和 GitLab 的特性分支 |
| 镜像 | 本机构建，推送到 `10.2.0.86:8443` | —— |
| 测试集群上的变化 | 只有部署动作：中心的 `aiops`、`mcp` 命名空间，边缘的 `aiops` 命名空间，以及测试用的故障 case | 都可以撤销，见 §6；**不加防火墙** |
| 测试机上的 `~/huhu/scp` 副本 | **不修改** | 只是代码副本；需要同步时，在那里 `git pull` 对应的特性分支 |
| xnet-cloud、可观测组件（`xnet`、`monitor` 命名空间） | **不修改** | 用例 X1 每个阶段都检查 |

现有的"联邦查询"（`/federation/ask`，`app/core/federation/`）是另一种模式：每个集群部署一整套 AIOps，中心通过 HTTP 把问题广播给各集群的 `/ask`。它要求中心能访问边缘，而且每个边缘都要部署完整服务，与"中心连不进边缘、边缘尽量轻"的目标冲突。**新设计不复用它，也不修改它**。新环境中关闭联邦（`federation.enabled: false`）；多集群功能稳定后，再评估是否下线。

### 1.2 分支与版本

这是一个大功能，单独开分支、单独编版本号，**不影响现有环境 10.2.0.48**。

| 仓库 | 特性分支（基于） | 新版本线 | 现有环境保持 |
|---|---|---|---|
| robusta | `008-multi-cluster`（`qwen-before-architecture`） | 13.0.x | 12.0.69 |
| mcpstander（含边缘 runner） | `008-multi-cluster`（`feature/aiops-observability-mcp-migration`） | MCP 8.0.x；runner 1.0.x（新镜像 `aiops-edge-runner`） | 7.0.52 |
| frountind | `008-multi-cluster`（`main`） | 0.2.x | 0.1.71 |

- 新版本线只部署到三集群环境。每次改动仍然是版本号加一再部署。
- 每个阶段验收通过后打标签：`mc-p0`、`mc-p1` …… 三个仓库使用同名标签。
- 现有环境的问题修复继续在原分支上做，版本仍为 12.0.x、7.0.x、0.1.x。
- 合并回主线的条件：P2 通过，并且 A5（现有环境回归）通过，再由 Boss 决定。

### 1.3 测试环境

| 主机 | 角色 | 集群名（`cluster` 标签） | 别名 |
|---|---|---|---|
| 10.2.5.85 | 中心：可观测全套、xnet-management，以及我们部署的 AIOps、MCP、前端 | `vc-xnet-management` | `center` |
| 10.2.5.88 | 边缘 | `vc-942nkkozc8o5fyb9q3bznb1ws` | `edge-88` |
| 10.2.5.89 | 边缘 | `vc-dluw0jousipr6h5co2bwpyqk2` | `edge-89` |

- **部署和测试**：通过 SSH 在各主机上执行；为了方便操作，本机也可以使用三个集群的 kubeconfig（`~/.kube/aiops-mc/`，不提交到仓库）。各 Make 目标都支持 `KUBECONFIG=...`。
- **运行时**：只经过 xnet 隧道和边缘 runner。上面的 SSH 和 kubeconfig **只用于运维和测试**，不得进入镜像、ConfigMap 或 Secret；用例 X3（`runtime_dependency_check.py`）每个阶段都检查。
- 登录凭据由 Boss 提供，**不写进任何文件或文档**。
- 端口：中心已占用的 NodePort 为 30081（xnet 的 `cloud-mgmt-frontend`）、30808、30909、31400、31500、31600、31700。我们的 AIOps 沿用 30800（A2A 为 30801），**前端改用 30082**（现有环境仍为 30081），通过部署变量设置，不修改现有环境。

### 1.4 故障 case 的放置

复用 `make case-deploy`，部署在边缘（中心资源较紧）：

| 集群 | case |
|---|---|
| edge-88 | c06 CrashLoop、c08 OOMKilled、c09 readiness 失败、c11 Terminating 卡住 |
| edge-89 | c02 镜像拉取失败、c10 liveness 失败；另部署一个与 c06 **同命名空间、同名**的健康工作负载（用于 A6 隔离测试） |
| center | 不部署 case |

## 2. 测试分层

| 层 | 内容 | 是否依赖 LLM | 通过标准 |
|---|---|---|---|
| L0 单元测试 | 注册表、别名解析、后端档案选择、`extra_label` 拼装、事件文本解析、垫片参数检查、签名校验、注入规则 | 否 | 全部通过；现有测试全部通过 |
| L1 契约测试 | xnet 隧道、VictoriaMetrics/VictoriaLogs 接口、新旧后端常用指标是否都存在 | 否 | 全部通过 |
| L2 工具级测试 | 脚本直接调用 MCP 工具和 runner，不经过模型 | 否 | **100% 通过**（行为确定） |
| L3 端到端测试 | 网页或 `/ask` 接口提问，完整走工作流 | 是 | 范围类断言 100%；诊断质量见 §5 |
| L4 故障测试 | 边缘 runner 停止或重启、隧道断线（用测试用的假隧道模拟） | 部分 | 全部通过 |
| L5 回归测试 | 现有环境 10.2.0.48 的全部验收 | 是 | 结果与改动前一致 |

范围类断言（集群是否正确、有没有串集群、有没有调用不该调用的工具）由工程代码保证，所以要求 100%。诊断结论的正确率受模型影响，按 §5 单独评估。

## 3. 验收脚本（随各阶段开发，先于功能代码）

放在 `robusta/scripts/acceptance/multicluster/`：

| 脚本 | 作用 | 首次需要的阶段 |
|---|---|---|
| `env_check.py` | 环境基线：三个集群在线、xnet 隧道可用、VM/VLogs 有数据、已知噪声清单；输出 `xnet`、`monitor` 命名空间的对象快照（X1 用） | P0 |
| `contract_xnet.py` | A15：`/proxy` 可用、不带证书被拒、Node 名与 UUID 可以互相转换、`cluster` 标签与 Node 名一致 | P0 |
| `contract_backends.py` | VM 的 `extra_label` 生效；VLogs 能按集群查询事件；常用指标在新旧两套后端上都存在 | P1 |
| `tools_direct.py` | L2：逐个调用 MCP 工具和 runner 接口并断言结果 | P0 起逐步扩充 |
| `e2e_ask.py` | L3：用 `/ask` 提问，从运行报告中取出路由范围、工具调用的集群参数和结论，并做断言 | P2 |
| `fault_inject.py` | L4：把指定边缘的 runner 副本数设为 0 或删除 runner Pod，到时自动恢复。只操作我们自己的组件，不加防火墙 | P3 |
| `runtime_dependency_check.py` | X3：检查中心 AIOps 和 MCP 的镜像、ConfigMap、Secret、环境变量中没有边缘 kubeconfig 和边缘 API Server 地址 | P0 |
| `snapshot_diff.py` | X1：比较前后两次快照 | P0 |

每个脚本输出 `PASS` 或 `FAIL`、用例编号，以及证据（运行 ID、任务 ID、请求耗时）。

## 4. 用例

格式：编号 | 阶段 | 操作 | 预期。"网页"表示在前端对话框输入。

### 4.1 每个阶段都执行

| # | 操作 | 预期 |
|---|---|---|
| X1 | 阶段开始前和结束后各执行一次 `env_check.py`，再执行 `snapshot_diff.py` | `xnet`、`monitor` 命名空间的 Deployment、Service、ConfigMap、Secret、CRD 和 Helm release 没有变化（Pod 重启和事件除外） |
| X2 | 现有单元测试 | 全部通过 |
| X3 | `runtime_dependency_check.py` | 中心的运行时配置中没有任何边缘 kubeconfig 或边缘 API Server（`<边缘IP>:6443`）地址；访问边缘的唯一配置是 xnet 隧道地址和 runner 地址 |

### 4.2 P0 打通链路

| # | 操作 | 预期 |
|---|---|---|
| P0-1 | `make sync-xnet-cert KUBECONFIG=<center>` | 中心的 `mcp` 和 `aiops` 命名空间出现复制的证书；xnet 命名空间没有变化 |
| P0-2 | `make edge-deploy KUBECONFIG=<edge-88>` | runner 运行正常；只有 ClusterIP，没有 NodePort |
| P0-3 | 中心执行 `AIOPS_CLUSTER=<edge-88> kubectl get pods -A` | 返回 edge-88 的 Pod 列表，退出码 0 |
| P0-4 | `AIOPS_CLUSTER=<edge-88> kubectl get pods -A \| jq ...` | 管道在本地正常处理 |
| P0-5 | `AIOPS_CLUSTER=<edge-88> kubectl logs -f ...`、`get -w`、`exec -it` | 垫片直接拒绝，并给出原因 |
| P0-6 | 不带签名、签名错误、时间戳过期、重放同一个签名，直接调用 runner | 全部 401，runner 审计中有记录 |
| P0-7 | 只读接口执行 `kubectl delete pod ...` | 403，`mode=read` 不允许写操作 |
| P0-8 | 不设置 `AIOPS_CLUSTER` 执行 `kubectl get ns` | 返回中心结果（行为不变） |
| A15 | `contract_xnet.py` | 全部通过 |

### 4.3 P1 可观测适配（MCP）

工具级（L2）：

| # | 操作 | 预期 |
|---|---|---|
| A1 | `execute_pod_promql`：edge-88 上 c08 Pod 的内存使用 | 只有 edge-88 的序列；结果带 `cluster` 和 `backend=victoria` |
| A2 | 同上，但模型给的 PromQL 不带集群条件；或者故意写成 `cluster="<edge-89>"` | 仍然只返回 edge-88 的数据 |
| A3 | `query_pod_logs`：edge-88 的 c06 Pod | 返回该 Pod 的 K8s 事件（BackOff 等），`log_source=k8s_events`，`coverage=partial`，并说明没有容器日志；Warning 识别正确 |
| A3b | `query_pod_logs`：edge-89 上不存在的 Pod | 返回空，不报错，不编造 |
| A4 | `query_pod_tracing`：victoria 集群 | `capability_missing` |
| A4b | `query_pod_topology`：edge-88 的 c06 Pod | 经 runner 返回所属工作负载和 Service 关系 |
| A8 | `list_clusters` | 三个集群、别名、在线状态、能力 |
| P1-1 | `prometheus_tool` 的标签和序列查询（edge-89） | 只返回 edge-89 的标签值和序列 |
| P1-2 | 在中心停掉 runner 对应的路由（把 edge-88 的 runner 副本数设为 0） | k8s 类工具返回 `cluster_unreachable`，耗时不超过 15 秒；指标类工具仍然正常 |

回归：

| # | 操作 | 预期 |
|---|---|---|
| A5 | 在 10.2.0.48 部署 MCP 8.0.x（不配置多集群），执行现有全部验收（含 [高危命令验收](acceptance-blacklist.md)） | 结果与 7.0.52 一致；工具结果中新增的 `cluster`、`backend` 字段不影响 AIOps 解析 |

### 4.4 P2 AIOps 的集群范围

端到端（L3，网页或 `e2e_ask.py`）：

| # | 网页输入 | 预期 |
|---|---|---|
| A8a | `有哪些 Pod 异常` | 反问要查看中心集群、某个边缘集群还是全部集群；**不调用任何工具** |
| A8b | 接着回答 `edge-89`，再追问 `那它的事件呢` | 第一轮只查 edge-89；追问沿用 edge-89，不再反问 |
| A8c | 分别输入 `中心集群的 vmagent 正常吗`、`edge-88 和 edge-89 各有几个 Pod`、`所有集群的节点状态` | 范围分别为 `center`、`multiple`（两个）、`multiple`（全部在线集群）；路由卡片显示一致 |
| A6 | `edge-88 上 aiops-case-06 命名空间的 Pod 为什么异常`（edge-89 有同名的健康工作负载） | 运行报告中所有工具调用的集群都是 edge-88；结论里没有 edge-89 的对象 |
| A7 | `edge-99 上有什么问题` | 回复找不到 edge-99，并列出可用集群；不调用任何工具 |
| P2-1 | `深度诊断 edge-88 上 aiops-case-08 的 Pod` | 完整走 layer → evidence → rca → conclusion；所有工具调用的集群都是 edge-88；指标来自 VictoriaMetrics |
| P2-2 | 单集群部署（10.2.0.48）问 `有哪些 Pod 异常` | 不反问，行为与现在相同 |
| P2-3 | 模型在单集群范围内把 `cluster` 填成别的集群（用测试桩模拟） | 被注入的值覆盖，运行报告中可以看到 |

### 4.5 P3 远端执行与修复

| # | 操作 | 预期 |
|---|---|---|
| A9 | 网页：`在 edge-88 的 aiops-case-09 命名空间 <Pod> 里执行 ls /tmp` | 正常返回目录列表 |
| A10 | 网页：同一个 Pod 里执行 `rm -f /tmp/a.txt`、`reboot`；以及 `kubectl drain master1` | 与单集群黑名单验收的结果一致（`approval_required` / `denied_executables` / 需审批） |
| A10b | 绕过中心，直接带有效签名调用 runner，执行 `reboot` | runner 拒绝（本地规则生效） |
| A10c | 直接调用 runner，执行需人工审批的 `rm`，不带 `approval_id` 或带伪造的 ID | 拒绝 |
| A11 | 诊断 edge-88 的 c09，生成修复方案并批准 | 审批卡片显示"将在 edge-88 执行"；runner 执行；恢复观察判定恢复；审计中有集群和 `job_id` |
| A11b | 自动执行模式下，方案中包含 `rm` | 仍然停在等待审批（与单集群一致） |
| A11c | 同一个修复动作被重复提交（模拟中心重试） | runner 返回同一个 `job_id`，只执行一次 |

### 4.6 P3 故障（L4，不加防火墙）

只操作我们自己的组件（runner），由 `fault_inject.py` 自动恢复。隧道断线类场景在集成测试中用假隧道模拟。

| # | 操作 | 预期 |
|---|---|---|
| A12 | 集成测试：修复任务执行中，假隧道断开 30 秒后恢复 | 中心恢复后继续按 `job_id` 查询，取回结果；没有重复提交 |
| A12b | 集成测试：断开时间超过任务查询时限 | 修复结果标记为"结果未知，需人工确认"，不重新提交 |
| A12c | 真实环境：审批等待期间把 edge-88 的 runner 副本数设为 0 | 审批卡片显示"集群当前不可达"；批准后不执行；runner 恢复后才执行 |
| A12d | 真实环境：修复任务执行中删除 edge-88 的 runner Pod | 中心查不到任务结果，标记为"结果未知，需人工确认"，不重新提交 |
| P3-1 | 真实环境：删除 edge-88 的 runner Pod，让它重建 | 期间 k8s 类工具返回 `cluster_unreachable`（15 秒内）；重建后自动恢复 |
| P3-2 | 重启 xnet-management 的主副本 | 边缘重连期间快速失败；约 10 秒后恢复，只读调用重试成功（**这是对 xnet 的运维操作，执行前要经过 Boss 确认**） |

"运行时不依赖中心直连边缘"不用防火墙验证，而是由 X3（运行时配置中没有任何访问边缘 API Server 的地址和凭据）和代码路径检查（远端集群的所有访问都经过隧道客户端）共同证明。

### 4.7 P4 一次诊断涉及多个集群

| # | 网页输入 | 预期 |
|---|---|---|
| A13 | `检查 edge-88 和 edge-89 有什么问题` | 两个集群各自做 layer；异常组的 key 带集群；取证并发进行；报告按集群分段；case 全部识别出来 |
| P4-1 | 执行 A13 期间把 edge-89 的 runner 副本数设为 0 | edge-89 段标为"不可达，结果不完整"；edge-88 段正常完成 |
| P4-2 | `所有集群有什么问题` | 中心集群没有 case，结论为"正常"；已知噪声（控制面组件 down、虚拟 Node 采集失败）没有被报告为故障，或者被明确标为采集配置问题 |

## 5. 诊断质量的评估方式

范围类断言之外，诊断结论的正确率受模型影响，不作为硬性门槛，而是与现有环境对比：

- 同一个 case，在现有环境（旧后端，有容器日志和链路）和新环境（新后端，只有事件）各诊断 3 次。
- 记录：根因是否正确、是否承认数据缺失、是否有编造的证据、耗时、工具调用次数。
- 判定：新环境的根因正确率**不低于现有环境减去一个合理的差值**。差值来自容器日志和链路的缺失，P1 结束时由 Boss 确认。**编造证据的次数必须为 0**。
- 结果记录在本文档 §7。

## 6. 测试环境操作规范

- 只在 `aiops`、`mcp` 命名空间和 case 命名空间里部署和删除资源；不碰 `xnet`、`monitor`、`kube-system`。
- 每个阶段结束后清理 case（`make case-clean`）和临时 Pod，确认 runner 副本数已恢复。
- 不在测试主机上添加防火墙规则。
- 正在执行修复、审批或验收时不发版（与现有约定一致）。
- 对 xnet 或可观测组件的任何运维操作（如 P3-2 的重启），都要先经过 Boss 确认。

## 7. 结果记录

每个阶段一张表：用例编号、结果、证据（运行 ID、任务 ID、脚本输出）、版本号、日期。

### Phase 0 基线（2026-10-21，开发前）

| 用例 | 结果 | 证据 |
|---|---|---|
| 环境基线 `env_check.py` | 8/8 通过 | 三个集群节点 Ready；两个边缘在 xnet 上 Ready；隧道到两个边缘 200；VM 与 VLogs 都有三个集群的数据；已知噪声 18 条（9 条虚拟 Node kubelet、9 条控制面组件） |
| A15 `contract_xnet.py` | 11/11 通过 | Node 名与 UUID 互转一致；`/proxy` 到两个边缘 200；未知集群返回 400 "The side client is not online!"；不带证书被拒；`cluster`、`cluster_id` 标签与 Node 名、UUID 一致 |
| X3 `runtime_dependency_check.py` | 2/2 通过 | 中心尚未部署 aiops、mcp 命名空间，作为基线 |
| X1 快照 | 已生成 | 119 个对象 |

### P0 链路打通（2026-10-21，runner 1.0.1、MCP 8.0.2）

| 用例 | 结果 | 证据 |
|---|---|---|
| P0-1 `make sync-xnet-cert` | 通过 | 证书复制到 `mcp`、`aiops` 命名空间；有效期至 2031-10-20；xnet 命名空间无变化（X1） |
| P0-2 `make edge-deploy`（edge-88） | 通过 | runner 只有 ClusterIP；镜像经 SSH 导入节点缓存（测试环境 Harbor 无推送权限） |
| P0-3 远端 `get pods -A` | 通过 | 经隧道约 130ms |
| P0-4 别名 + 本地 jq 管道 | 通过 | `items=20`。首次因 256KB 截断失败，上限改为 4MB 并启用压缩传输 |
| P0-5 `-f`、`-w`、`-it` | 通过 | 垫片直接拒绝并说明原因 |
| P0-6 不带签名、错误密钥、过期、重放 | 通过 | 均为 401 |
| P0-7 只读接口执行 `delete` | 通过 | 403 `mode_denied` |
| P0-8 不设集群执行 `kubectl get ns` | 通过 | 返回中心命名空间 |
| P0-9 未部署 runner 的 edge-89 | 通过 | `cluster_unreachable` |
| P0-10 未知集群 | 通过 | `cluster_unknown`，并列出可用集群 |
| X1 快照 / X3 运行时依赖 / A15 契约 | 通过 | 119 个对象无变化；aiops、mcp 中无边缘 kubeconfig 或 API Server 地址；契约 11/11 |
| 单元测试 | 通过 | robusta `tests/unit/multicluster` 100 个；mcpstander 316 个 |

开发中发现并修复：垫片收到的 `argv[0]` 是绝对路径（单元测试补充了该场景）。

### P1 可观测适配（2026-10-21，MCP 8.0.3、runner 1.0.1）

故障 case：edge-88 部署 c06、c08、c09；edge-89 部署 c02、c10，以及与 c06 同命名空间、同名的健康工作负载 `aiops-case-06/workload`。

| 用例 | 结果 | 证据 |
|---|---|---|
| A1 edge-88 上 c08 的内存（30 分钟峰值） | 通过 | `backend=victoriametrics`，`cluster` 为 edge-88，有数据。OOM 容器不断重启，此刻没有当前序列，所以用 `max_over_time` |
| A2 PromQL 显式写 edge-89 的 cluster | 通过 | 结果为空：`extra_label` 优先于查询里的匹配条件 |
| A2b 在 edge-88 范围内查询 edge-89 的同名 Pod | 通过 | `pod_not_found` |
| A3 c06 的"日志" | 通过 | 返回 K8s 事件（BackOff、Unhealthy、Started……），`log_source=k8s_events`、`coverage=partial`，正确识别 Warning |
| A4 链路 | 通过 | `capability_missing` |
| A4b 拓扑 | 通过 | 经 runner 获取所属工作负载与 Service |
| A8 `list_clusters` | 通过 | 三个集群，均在线，能力标注正确 |
| P1-1 edge-89 的 namespace 标签值 | 通过 | 包含 aiops-case-10，不含只在 edge-88 的 aiops-case-08 |
| P1-required 多集群下不传集群 | 通过 | `cluster_required` |
| P1-2 edge-88 runner 副本数设为 0 | 通过 | k8s 工具 1.5 秒返回 `cluster_unreachable`；指标工具仍然可用；随后恢复 runner |
| 后端契约 `contract_backends.py` | 7/7 通过 | `extra_label` 生效；常用指标在三个集群（等待和终止原因指标只在有对应状态的集群上出现）和旧 Prometheus 中都存在；VLogs 事件可以按集群查询和解析 |
| A5 现有环境回归 | 待执行 | 与 Phase 3 合并执行 |
| mcpstander 单元测试 | 344 个通过 | 新增 cluster_scope、接线、远端 shell 规则、list_clusters 测试 |
