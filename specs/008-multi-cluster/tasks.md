# Tasks: 多集群与新旧可观测后端适配

**Input**: [spec.md](spec.md)、[plan.md](plan.md)、[contracts/](contracts/)
**规则**：每个实现任务之前都有一个先失败的测试或验收脚本任务（宪章 III）。`[P]` 表示可以并行。仓库前缀：`R:` robusta，`M:` mcpstander，`F:` frountind。

## Phase 0: 准备（mc-p0 之前）

- [x] T001 三个仓库创建分支 `008-multi-cluster`；版本号设为 R 13.0.0、M 8.0.0、runner 1.0.0、F 0.2.0
- [x] T002 [P] R: `scripts/acceptance/multicluster/env_check.py`：三个集群在线、隧道可用、VM/VLogs 有数据、噪声清单、`xnet`/`monitor` 对象快照
- [x] T003 [P] R: `snapshot_diff.py`（SC-007）
- [x] T004 [P] R: `runtime_dependency_check.py`（SC-006）：检查中心 AIOps/MCP 的镜像、ConfigMap、Secret、环境变量中没有边缘 kubeconfig 和边缘 API Server 地址
- [x] T005 R: `contract_xnet.py`（A15）：`/proxy` 可用、无证书被拒、Node 名与 UUID 互转、`cluster` 标签与 Node 名一致
- [x] T006 执行 T002–T005，记录基线

## Phase 1: 链路打通（US4 的基础，mc-p0）

测试先行：

- [x] T010 [P] M: 单元测试——签名生成与校验（过期、重放、篡改）
- [x] T011 [P] M: 单元测试——垫片参数检查（拒绝 -f/-w/-it/port-forward/proxy/attach；本地集群直通）
- [x] T012 [P] R: 单元测试——runner `mode=read` 拒绝写子命令；输出截断与压缩（`tests/unit/multicluster/`）
- [x] T013 M: `tests/multicluster/test_tunnel_client.py`：错误分类（握手失败、离线、超时、401、403），用本地假隧道
- [x] T014 R: `tools_direct.py` 的 P0 部分（P0-3 至 P0-8）

实现：

- [x] T015 M: `servers/cluster/signing.py`
- [x] T016 M: `servers/cluster/xnet_tunnel.py`（证书从挂载的 Secret 读取，失效时 `tunnel_auth_failed`）
- [x] T017 R: `aiops_edge/runner/`、`Dockerfile.edge-runner`、`deploy-edge/runner.yaml`：`/healthz`、`/v1/kubectl`（read）、reader/writer SA、部署清单、镜像
- [x] T018 M: `bin/kubectl` 垫片；`_command_runner` 传递 `AIOPS_CLUSTER`
- [x] T019 R/M: Makefile 目标 `sync-xnet-cert`、`edge-deploy`、`runner-build`、`runner-push`（R）；`deploy-mc`、`sync-aiops-edge`（M）
- [x] T020 部署到中心和 edge-88，执行 T014、T005、T004；通过后打 `mc-p0`

## Phase 2: 可观测适配（US1 工具层、US3，mc-p1）

测试先行：

- [x] T030 [P] M: 单元测试——注册表（静态配置 + Node 发现合并、别名解析、未知集群）
- [x] T031 [P] M: 单元测试——后端档案选择；未配置档案时回退环境变量（FR-003）
- [x] T032 [P] M: 单元测试——VictoriaMetrics 请求带 `extra_label`；模型写错集群时仍被限定（FR-010）
- [x] T033 [P] M: 单元测试——事件文本解析（含 `reasoni`、`type: Warning`、`count`），用实测样本
- [x] T034 [P] M: 单元测试——victoria 后端的 tracing 返回 `capability_missing`
- [x] T035 M: 结果契约测试：现有字段不变，只新增 `cluster`、`backend`（FR-012）
- [x] T036 R: `contract_backends.py`：`extra_label` 生效、VLogs 能按集群取事件、常用指标在两套后端都存在
- [x] T037 R: `tools_direct.py` 的 P1 部分（A1–A4b、A8、P1-1、P1-2）

实现：

- [x] T038 M: `servers/cluster/registry.py` + `list_clusters` 工具
- [x] T039 M: `aiops_observability/config.py` 后端档案
- [x] T040 [P] M: `collectors/victoriametrics.py`
- [x] T041 [P] M: `collectors/victorialogs_events.py`
- [x] T042 M: `query/{metrics,logs,tracing,topology}.py` 按集群选择后端，结果新增字段
- [x] T043 M: `holmes_tools/prometheus.py` 按集群选择地址
- [x] T044 M: 各工具 schema 增加可选的 `cluster`
- [x] T045 部署到三集群环境，执行 T036、T037
- [x] T046 A5（与 Phase 3 合并执行，10.2.0.48 只部署一次）：在 10.2.0.48 部署 MCP 8.0.x（不配置多集群），执行现有全部验收；结果与 7.0.52 一致
- [x] T047 诊断质量对比（验收文档 §5）：新旧环境 c06、c09 均 6/6，正确率无差距，编造 0 次

## Phase 3: AIOps 集群范围（US1 端到端、US2，mc-p2）

测试先行：

- [x] T050 [P] R: 路由测试——三种范围的识别；范围不明确时强制 `clarify`；追问沿用集群；未知集群（A7、A8a–c）
- [x] T051 [P] R: 工具包装测试——单集群范围强制注入并覆盖模型的值；多集群范围校验；单集群部署不处理（P2-3）
- [x] T052 [P] R: 身份测试——不同集群的同名 Pod 不合并（FR-008）
- [x] T053 R: `e2e_ask.py`：从运行报告中断言范围和每次工具调用的集群

实现：

- [x] T054 R: `request_router.py` + 路由提示词：`clusters`、`cluster_mode`，代码按注册表解析
- [x] T055 R: `aicall/tools.py`：注入与校验
- [x] T056 R: `pod_identity.py`、分组和事实身份带集群
- [x] T057 F: 路由卡片显示集群范围
- [x] T058 部署，执行 T053 覆盖 A6、A7、A8a–c、P2-1、P2-2；A5 回归；通过后打 `mc-p2`

## Phase 4: 远端执行与修复（US4、US5，mc-p3）

测试先行：

- [x] T060 [P] M: runner 测试——`mode=exec` 按规则检查；需审批命令必须带 `approval_id`（FR-015）
- [x] T061 [P] M: runner 测试——任务幂等；重启后从 emptyDir 恢复任务记录
- [x] T062 [P] R: 执行器测试——远端目标走 `/v1/jobs`；结果无法确认时标记"结果未知"且不重新提交（FR-017）
- [x] T063 R: `tools_direct.py` 的 P3 部分（A10b、A10c、A11c）

实现：

- [x] T064 M: runner `/v1/kubectl` exec 模式、`/v1/jobs`
- [x] T065 R: `remediation/plans.py` 目标带集群；`pod_executor.py`、`recovery.py` 的远端路径；`audit.py` 带集群
- [x] T066 F: 审批卡片和修复结果显示集群（FR-018）
- [x] T067 部署，执行 A9、A10、A10b、A10c、A11、A11b、A11c、A12（runner 重启）、P3-1；A5 回归；通过后打 `mc-p3`

## Phase 5: 一次诊断涉及多个集群（US6，mc-p4）

- [x] T070 R: 测试——layer 按集群并行、异常组 key 带集群、单个集群失败不阻塞（FR-019）
- [x] T071 R: 实现 layer 按集群并行与合并、结论按集群分段
- [x] T072 R: 已知采集噪声的识别说明——P4-2 中噪声没有被报告为故障，无需额外处理（不修改采集）
- [x] T073 F: 异常组标题显示集群
- [x] T074 部署，执行 A13、P4-1、P4-2；通过后打 `mc-p4`

## Phase 6: 收尾

- [x] T080 更新 `docs/ARCHITECTURE.md`、README（中英文）中的多集群说明
- [x] T081 验收结果写入 `docs/multi-cluster-acceptance.md` §7
- [ ] T082 由 Boss 决定是否合并回主线

## 依赖

Phase 0 → 1 → 2 → 3 → 4 → 5。Phase 2 的 MCP 工作与 Phase 1 的 runner 镜像构建可以部分并行；US3 回归（T046）在每个阶段之后都重复执行。
