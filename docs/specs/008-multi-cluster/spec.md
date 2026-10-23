# Feature Specification: 多集群与新旧可观测后端适配

**Feature Branch**: `008-multi-cluster`
**Created**: 2026-10-21
**Status**: Implemented（开发过程记录，2026-10-21 至 2026-10-22；当前行为以 [docs/multi-cluster-design.md](../../docs/multi-cluster-design.md) 为准）
**Input**: Boss："在多集群环境中可以使用新的可观测性数据方式；兼容旧的可观测组件；主要使用方式（快速查询、深度诊断）和现在差别不大，AIOps 逻辑改动不大，主要是 MCP 的适配。"

设计说明（对外）：[docs/multi-cluster-design.md](../../docs/multi-cluster-design.md)；验收说明：[docs/multi-cluster-acceptance.md](../../docs/multi-cluster-acceptance.md)。本 spec 只写"要什么"，实现见 [plan.md](plan.md)。

## Clarifications

### Session 2026-10-21

- Q: xnet-cloud 参与到什么程度？ → A: 所有新增内容都属于 AIOps 自己的服务；不修改 xnet 的代码、配置和数据，不要求它做任何适配，不在 xnet 命名空间创建对象，不使用 Vessel。只以调用方身份使用隧道 `/proxy`、客户端证书和虚拟 Node 列表（只读）。
- Q: 隧道客户端证书怎么获得？ → A: 部署时复制到我们的命名空间，不在 xnet 命名空间创建 Role。证书有效期到 2031-10-20。
- Q: 边缘组件怎么部署？ → A: 用我们自己的部署清单，在边缘本地执行。三套集群共用一个 harbor，边缘可以直接拉取镜像，不需要 chart 仓库。
- Q: 部署和测试怎么访问集群？ → A: 通过 SSH 在各主机上执行；为了方便操作和测试也可以在本机使用 kubeconfig。**运行时不得依赖任何边缘 kubeconfig 或对边缘 API Server 的直连。**
- Q: 多集群模式下用户没说集群怎么办？ → A: 必须让用户说明是操作一个集群、多个集群还是中心集群；理解上下文意图，追问时沿用。没有默认值。
- Q: 中心能否访问 LLM 网关？ → A: 可以。
- Q: 测试时是否用防火墙模拟中心连不进边缘？ → A: 不加防火墙。改为证明运行时没有任何访问边缘 API Server 的配置和路径（FR-016、SC-006）。
- Q: 现有的联邦查询（`/federation/*`）怎么办？ → A: 不复用、不修改；新环境中关闭。
- Q: spec 是否进 git？ → A: 进。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 在指定集群上快速查询（Priority: P1）

运维人员在网页上问"edge-88 上有哪些 Pod 不正常""edge-89 上 xx Pod 的内存使用"。系统只查询这个集群的数据，回答方式和现在的快速查询一样。

**Why this priority**: 这是多集群最基础的能力，也是验证"新可观测数据 + 集群范围"整条链路的最小闭环。

**Independent Test**: 只部署中心的 AIOps、MCP 和一个边缘的 runner，在网页上对边缘集群提问即可验证。

**Acceptance Scenarios**:

1. **Given** edge-88 和 edge-89 各有一个同名工作负载，**When** 问 edge-88 上该工作负载的状态，**Then** 回答和所有工具调用只涉及 edge-88。
2. **Given** 新后端只采集了 K8s 事件，**When** 查询某个 Pod 的日志，**Then** 返回该 Pod 的事件，并明确说明这个集群没有采集容器日志。
3. **Given** 新后端没有链路数据，**When** 查询链路，**Then** 明确返回"该集群未提供链路数据"，回答中不出现编造的链路结论。
4. **Given** 多集群部署，**When** 问"有哪些 Pod 异常"而没有说明集群，**Then** 系统反问要查看中心集群、某个边缘集群还是全部集群，并且不调用任何工具。
5. **Given** 上一轮已经说明是 edge-89，**When** 追问"那它的事件呢"，**Then** 沿用 edge-89，不再反问。
6. **Given** 用户提到一个不存在的集群，**When** 提问，**Then** 回复找不到，并列出可用集群。

---

### User Story 2 - 在指定集群上深度诊断（Priority: P1）

运维人员要求"深度诊断 edge-88 上 aiops-case-08 的 Pod"。诊断流程（问题定位、取证、根因、总结）和现在一样，数据来自该集群。

**Why this priority**: 深度诊断是核心价值。第一期每次诊断只针对一个集群，现有工作流不变。

**Independent Test**: 在 edge-88 部署故障 case，网页上发起深度诊断。

**Acceptance Scenarios**:

1. **Given** edge-88 有 OOMKilled 的 case，**When** 深度诊断该命名空间，**Then** 识别出 OOM，所有工具调用的集群都是 edge-88，指标来自中心的新后端。
2. **Given** 新后端没有容器日志，**When** 诊断需要日志，**Then** 结论如实说明缺失，并改用经 runner 实时获取的容器日志；不编造证据。

---

### User Story 3 - 兼容现有可观测组件（Priority: P1）

现有环境（10.2.0.48，Prometheus + Elasticsearch + DeepFlow + Tempo）升级到新版本后，行为、配置和验收结果都与现在一致；以后某个集群也可以改回旧后端。

**Why this priority**: Boss 明确以后可能用回现有组件，回归必须先守住。

**Independent Test**: 在 10.2.0.48 部署新版本 MCP（不配置多集群），执行现有全部验收。

**Acceptance Scenarios**:

1. **Given** 现有环境不做任何配置修改，**When** 部署新版本，**Then** 现有验收（含高危命令验收）结果与改动前一致。
2. **Given** 多集群配置中某个集群的后端档案设为 legacy，**When** 查询该集群，**Then** 使用旧后端。

---

### User Story 4 - 在边缘集群的 Pod 内执行命令（Priority: P2）

运维人员说"在 edge-88 的 xx Pod 里执行 ls /tmp"。行为和单集群一致：合规命令直接执行；黑名单命令被拒；需要人工审批的命令在对话中不执行。

**Why this priority**: 依赖 P1 的链路，但属于独立能力。

**Independent Test**: 在 edge-88 上执行合规命令和黑名单命令。

**Acceptance Scenarios**:

1. **Given** edge-88 上有一个运行中的 Pod，**When** 要求执行 `ls /tmp`，**Then** 返回目录列表。
2. **Given** 同一个 Pod，**When** 要求执行 `rm`、`reboot`，或者对节点执行 `drain`，**Then** 结果与单集群的高危命令验收一致。
3. **Given** 有人绕过中心直接调用边缘 runner，**When** 请求执行黑名单命令，或者执行需要审批但没有审批凭据的命令，**Then** 边缘拒绝。

---

### User Story 5 - 修复边缘集群上的故障（Priority: P2）

诊断 edge-88 的故障后生成修复方案。审批卡片显示目标集群；批准后在 edge-88 执行，并观察恢复情况。

**Why this priority**: 修复是闭环的最后一步，依赖 US2 和 US4。

**Independent Test**: edge-88 上的 readiness 失败 case，诊断 → 方案 → 批准 → 恢复。

**Acceptance Scenarios**:

1. **Given** 方案目标在 edge-88，**When** 等待审批，**Then** 卡片写明"将在 edge-88 执行"。
2. **Given** 已批准，**When** 执行，**Then** 在 edge-88 执行，恢复观察判定恢复，审计中有集群信息。
3. **Given** 自动执行模式下方案包含需要审批的命令，**When** 执行，**Then** 仍然等待人工审批。
4. **Given** 同一个动作被重复提交，**When** 边缘收到，**Then** 只执行一次。
5. **Given** 执行过程中边缘 runner 重启，**When** 恢复后，**Then** 中心取回结果，不重复执行；无法确认结果时标记为"结果未知，需人工确认"。

---

### User Story 6 - 一次诊断涉及多个集群（Priority: P3）

"检查 edge-88 和 edge-89 有什么问题"。两个集群分别定位问题，异常组并发取证，报告按集群分段。

**Why this priority**: 需要扩展问题定位节点，放到最后。

**Independent Test**: 两个边缘各部署故障 case，一次提问。

**Acceptance Scenarios**:

1. **Given** 两个边缘都有 case，**When** 提问，**Then** 两个集群的 case 都识别出来，报告按集群分段。
2. **Given** 其中一个集群的 runner 不可用，**When** 提问，**Then** 该集群标为不完整，另一个集群正常完成。
3. **Given** 中心集群有已知的采集噪声（控制面组件 up==0、虚拟 Node 采集失败），**When** 检查所有集群，**Then** 噪声不被报告为故障，或者被明确标为采集配置问题。

### Edge Cases

- 集群名过长：用户使用我们配置的别名（edge-88），系统解析为规范名称。
- 集群离线（xnet 虚拟 Node NotReady，或 runner 不可用）：K8s 类工具 15 秒内返回"不可达"；指标类工具仍然可用，并标明数据截止时间。
- 远端命令输出过大：runner 截断，并标明截断。
- 长连接类命令（`logs -f`、`--watch`、`exec -it`、`port-forward`）：直接拒绝并说明原因。
- 远端集群的 helm 操作：第一期不支持，明确告知。
- xnet 主副本切换：短时间不可达，只读调用重试一次。
- xnet 证书失效：明确报错，提示重新同步证书。

## Requirements *(mandatory)*

### Functional Requirements

**边界**

- **FR-001**: 系统 MUST NOT 修改 xnet-cloud 的代码、配置或数据，MUST NOT 在 xnet 命名空间创建任何对象，也不得要求 xnet 做任何适配。
- **FR-002**: 系统 MUST NOT 修改可观测组件的采集配置；集群没有的数据 MUST 如实标注为"未提供"，不得补造。
- **FR-003**: 未配置多集群时，系统行为、配置项和工具接口 MUST 与 12.0.69 / 7.0.52 保持一致。

**集群与范围**

- **FR-004**: 系统 MUST 维护集群注册表：来自配置和 xnet 虚拟 Node（只读），包含名称、别名、在线状态、可观测后端和能力。
- **FR-005**: 多集群部署下，系统 MUST 根据问题和会话上文识别范围：一个集群、多个集群或中心集群；范围不明确时 MUST 反问，并且不调用任何工具。
- **FR-006**: 集群名称 MUST 由代码按注册表解析；模型不能自造集群名。
- **FR-007**: 工具调用的集群 MUST 由工程代码按本次范围注入或校验，不依赖模型自觉遵守。
- **FR-008**: 工具结果和事实身份 MUST 带上集群；不同集群中同名的对象不得合并。

**可观测适配**

- **FR-009**: 系统 MUST 支持按集群选择可观测后端：legacy（Prometheus、Elasticsearch、DeepFlow、Tempo）和 victoria（VictoriaMetrics、VictoriaLogs）。
- **FR-010**: victoria 后端的指标查询 MUST 被强制限定在目标集群，即使模型的查询语句写错或指向别的集群。
- **FR-011**: victoria 后端的日志工具 MUST 返回目标 Pod 相关的 K8s 事件，正确识别事件类型，并标明没有容器日志。
- **FR-012**: 现有工具的名称和结果格式 MUST 保持兼容；只新增可选的 `cluster` 参数和结果中的 `cluster`、`backend` 字段。

**远端访问与执行**

- **FR-013**: 中心访问边缘集群 MUST 只经过 xnet 隧道和我们部署在边缘的 runner。
- **FR-014**: runner MUST 校验中心的签名，拒绝未签名、签名错误、过期或重放的请求。
- **FR-015**: runner MUST 在本地执行与中心相同的命令规则；需要审批的命令 MUST 携带有效的审批凭据。
- **FR-016**: 运行时 MUST NOT 依赖任何边缘集群的 kubeconfig 或对边缘 API Server 的直接连接。运维和测试时在本机使用的 kubeconfig 不得进入镜像、ConfigMap 或 Secret。
- **FR-017**: 远端修复动作 MUST 以带幂等键的异步任务执行；结果无法确认时 MUST 标记为"结果未知"，不得重新提交。
- **FR-018**: 审批卡片、修复结果和审计 MUST 显示目标集群。

**多集群诊断（P3）**

- **FR-019**: 一次诊断涉及多个集群时，系统 MUST 按集群分别定位问题，并发取证，报告按集群分段；单个集群不可用不得阻塞其他集群。

### Key Entities

- **集群（Cluster）**：名称（等于可观测数据的 `cluster` 标签和 xnet 虚拟 Node 名）、别名、访问方式（local / xnet）、可观测后端、在线状态、能力。
- **可观测后端档案（Observability Profile）**：一组数据源及其类型（指标、日志、链路），决定工具使用哪种实现。
- **运行范围（Run Scope）**：本次运行涉及的集群和范围类型（single / multiple / center），由路由确定。
- **远端任务（Edge Job）**：幂等键、命令、审批凭据、状态、输出。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 范围类断言（工具调用的集群是否正确、是否串集群、范围不明确时是否不调用工具）在所有端到端用例中 100% 通过。
- **SC-002**: 现有环境的全部验收结果与改动前一致。
- **SC-003**: 工具级用例（直接调用 MCP 工具和 runner）100% 通过。
- **SC-004**: 新环境的诊断中，编造证据的次数为 0；根因正确率与现有环境的差距在 Boss 于 P1 结束时确认的范围内。
- **SC-005**: 远端 K8s 类调用在集群不可达时 15 秒内返回明确错误；可达时单次调用的额外耗时不超过 1 秒。
- **SC-006**: 运行时依赖检查通过：中心的 AIOps 和 MCP 的镜像、ConfigMap、Secret 和环境变量中，没有任何边缘 kubeconfig 或边缘 API Server 地址。
- **SC-007**: 每个阶段前后，`xnet` 和 `monitor` 命名空间的对象快照没有变化。

## Assumptions

- 三集群测试环境：中心 10.2.5.85，边缘 10.2.5.88 / 10.2.5.89；三套集群共用一个 harbor。
- 边缘可以访问中心的隧道端口（xnet 现有前提）。
- xnet 的 `/proxy` 行为与 2026-10-21 实测一致（mTLS、20 秒超时、完整转发请求）。
- 中心可以访问 LLM 网关。
- 新后端的事件文本格式与实测一致；格式变化由契约测试发现。
