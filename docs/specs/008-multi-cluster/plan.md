# Implementation Plan: 多集群与新旧可观测后端适配

**Branch**: `008-multi-cluster` | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

## Summary

在中心的 MCP 中增加集群注册表、按集群选择的可观测后端档案和集群访问层；在边缘部署一个我们自己的轻量 runner，中心经 xnet 隧道 `/proxy` 调用它。AIOps 只增加集群范围的识别、注入和显示。架构细节见 [docs/multi-cluster-design.md](../../docs/multi-cluster-design.md)（单一来源，本文件不重复）。

## Technical Context

| 项 | 内容 |
|---|---|
| 语言 | Python 3.12（robusta）、Python 3.10（mcpstander、runner）、TypeScript（frontend） |
| 主要依赖 | 现有：FastAPI、LangGraph/LangChain、MCP SDK、kubectl；新增：无第三方库（HTTP 用已有的 requests/httpx，签名用标准库 hmac） |
| 存储 | runner 任务记录：内存 + emptyDir；其余沿用现有 |
| 测试 | pytest（robusta、mcpstander）、node test（frontend）、`tests/acceptance/multicluster/` |
| 目标环境 | 三集群测试环境（中心 10.2.5.85，边缘 .88/.89，K8s 1.33）；回归环境 10.2.0.48 |
| 性能目标 | 远端调用额外耗时 ≤ 1 秒；不可达时 15 秒内失败（SC-005） |
| 约束 | 不修改 xnet、不修改采集；运行时不依赖边缘 kubeconfig；单集群行为不变 |
| 规模 | 3 个集群，每个边缘 1 个 runner 副本 |

## Constitution Check

| 原则 | 检查 | 结论 |
|---|---|---|
| I. 高内聚低耦合 | 集群与后端的差异都收在 MCP 的适配层；AIOps 只在路由、工具包装和修复目标三处感知集群；runner 是独立组件 | 通过 |
| II. 证据优先与可验证 | 结果标注 `cluster`、`backend`、`coverage`；没有的数据返回 `capability_missing`；每个阶段都有真实环境验收 | 通过 |
| III. 测试先行 | tasks 中每个实现任务前都有失败的测试或验收脚本 | 通过 |
| IV. 安全修复优先 | 规则在中心和 runner 各执行一遍；需要审批的命令必须带审批凭据；修复异步执行且幂等，结果不明时不重发 | 通过 |
| V. 最小可用变更 | 不新增工具（只新增 `list_clusters`）；用 kubectl 垫片避免改动 20 多个工具模板；多集群诊断放到最后一期 | 通过 |
| 交付工作流 | spec → plan → tasks → 实现 → 验证；每次 VERSION+1，构建推送部署，并真实 `/ask` 验证 | 通过 |

需要说明的复杂度见 Complexity Tracking。

## Project Structure

### Documentation

```
specs/008-multi-cluster/
├── spec.md
├── plan.md          # 本文件
├── research.md      # xnet 与新后端的实测结论
├── contracts/
│   ├── runner-api.md
│   └── tool-result.md
├── quickstart.md    # 部署与验收入口
└── tasks.md
```

### Source Code

```
mcpstander/
├── servers/cluster/                  # 新增：registry.py、xnet_tunnel.py、signing.py
├── servers/aiops_observability/
│   ├── config.py                     # 后端档案；未配置时回退环境变量
│   ├── collectors/victoriametrics.py # 新增
│   ├── collectors/victorialogs_events.py  # 新增
│   └── query/{metrics,logs,tracing,topology}.py  # 按集群选择后端
├── servers/holmes_tools/
│   ├── prometheus.py                 # 按集群选择地址 + extra_label
│   └── _command_runner.py            # 子进程带 AIOPS_CLUSTER
├── servers/aiops_edge/               # 同步自 robusta/aiops_edge（不含 runner）
├── bin/kubectl                       # 新增：垫片入口（真正的 kubectl 改名为 kubectl.real）
├── deploy/envs/mc/                   # 新增：测试环境 kustomize overlay（make deploy-mc）
└── tests/multicluster/               # 新增

robusta/
├── aiops_edge/                                 # 新增：共享多集群访问库 + runner
├── Dockerfile.edge-runner、deploy-edge/          # 新增：runner 镜像与边缘部署清单、测试环境集群配置
├── app/core/workflow/nodes/request_router.py   # clusters / cluster_mode / 强制澄清
├── app/core/aicall/tools.py                    # 注入与校验 cluster
├── app/core/workflow/pod_identity.py 等        # 身份带集群
├── app/core/remediation/{plans,pod_executor,recovery,audit}.py  # 目标带集群、远端异步任务
├── tests/acceptance/multicluster/            # 验收脚本
└── tests/unit/multicluster/

frountind/src/components/aiops-chat/            # 路由卡、异常组、审批卡显示集群
```

**Structure Decision**（实现时修订，2026-10-21）：共享的多集群访问代码放在 **robusta 的 `aiops_edge/`**（只依赖标准库）：`signing`、`kubectl_args`、`clusters`、`tunnel`、`streams`、`shim`，以及 `runner/`。原因是 runner 必须复用 robusta 的命令规则（`app/core/remediation/policy.py`、`execution_guard.py`，同样只依赖标准库）。mcpstander 通过 `scripts/sync_aiops_edge.sh` 同步除 `runner/` 外的文件到 `servers/aiops_edge/`，`tests/test_aiops_edge_sync.py` 校验两份一致。runner 镜像由 robusta 的 `Dockerfile.edge-runner` 构建，部署清单在 `deploy-edge/`（不在 `deploy/` 下，避免被 `make deploy` 应用到中心）。

## 部署与测试方式

- 本地修改，构建镜像并推送到共用的 harbor（`10.2.0.86:8443`）。
- **实测更正**：三集群测试环境的 `xnet.registry.io` 解析到它自己的 Harbor（10.2.5.85），我们没有推送权限，按 IP 拉取 10.2.0.86 又因证书不含 IP SAN 失败。测试环境因此用 `deploy-edge/load_image.sh` 经 SSH 把镜像导入节点的 containerd 缓存，清单使用 `IfNotPresent`（每次发版版本号都会加一）。不修改节点的 hosts 或 containerd 配置。
- 部署和测试通过 SSH 在各主机上执行；为方便操作，本机也可以使用三个集群的 kubeconfig（`~/.kube/aiops-mc/`，不提交）。**这些 kubeconfig 只用于运维和测试，不进入镜像、ConfigMap 或 Secret**，SC-006 的检查脚本负责证明这一点。
- 不使用防火墙模拟网络隔离；"运行时不依赖中心直连边缘"由 SC-006 的依赖检查和代码路径检查证明。
- 新版本线：robusta 13.0.x、MCP 8.0.x、runner 1.0.x、frontend 0.2.x，只部署到三集群环境；10.2.0.48 保持现有版本，只用于 A5 回归。

## Complexity Tracking

| 新增的复杂度 | 为什么需要 | 被放弃的更简单方案 |
|---|---|---|
| 边缘 runner（新组件） | 隧道只能转发普通 HTTP，无法让中心的 kubectl 访问边缘 API Server，也不支持 exec 升级 | 中心用 kubeconfig 直连边缘：违反"中心连不进边缘"的前提和 FR-016；用 xnet 虚拟 Node 的 exec：它是空实现 |
| kubectl 垫片 | 让 20 多个现有工具模板不用修改就能访问远端集群 | 逐个修改工具：改动面大，与"最小变更"冲突 |
| HMAC 签名 | 持有 xnet 客户端证书的任何人都能经隧道访问 runner | 只靠 xnet 的 mTLS：无法区分我们和其他持证方 |
| 远端异步任务 | 隧道单次请求最长 20 秒，修复动作可能更长；断线时需要避免重复执行 | 同步调用：超时后结果未知，重试有重复执行的风险 |
