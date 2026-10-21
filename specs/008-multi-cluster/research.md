# Research: 多集群与新旧可观测后端适配

所有结论均于 2026-10-21 在三集群测试环境实测或读源码得出。详细数据见 [docs/multi-cluster-design.md §2](../../docs/multi-cluster-design.md#2-现状)。

## R1 中心如何访问边缘

- **Decision**: 经 xnet 隧道 `/proxy` 的 http 协议访问边缘内我们自己的 runner Service。
- **Rationale**: 实测带 xnet 客户端证书调用 `/proxy` 访问边缘任意 Service 返回 200，约 20ms；隧道完整转发请求头和请求体，可以携带我们的签名。
- **Alternatives considered**:
  - kubeconfig 直连边缘 API Server：违反"中心连不进边缘"的前提（FR-016）。
  - 隧道的 exec/logs 协议：只定义了名称，没有实现。
  - xnet 虚拟 Node 的 exec：打日志后返回成功，属于空实现。
  - 经隧道访问边缘 API Server：隧道使用 Go 默认客户端，不带集群 CA 和 token，不支持连接升级。

## R2 隧道证书

- **Decision**: 部署时把 `xnet/xnet-client-cert`、`xnet/xnet-ca-cert` 复制到我们的命名空间。
- **Rationale**: 隧道服务端要求 `RequireAndVerifyClientCert`；证书有效期 2026-10-21 至 2031-10-20；复制后运行时不需要访问 xnet 命名空间（FR-001）。
- **Alternatives considered**: 在 xnet 命名空间创建 Role 读取证书：需要在 xnet 命名空间创建对象，Boss 不接受。

## R3 集群标识

- **Decision**: 集群规范名称 = xnet 虚拟 Node 名 = 可观测数据的 `cluster` 标签值；隧道 `clientid` = 从 Node 名反解的 UUID。
- **Rationale**: 实测三者一致；Node 名为 `vc-` + UUID 的 base36 编码；边缘数据还带 `cluster_id` 标签（UUID）。
- **Alternatives considered**: 只用配置里的静态名称：需要手工维护，和 xnet 的集群生命周期脱节。

## R4 指标查询的集群隔离

- **Decision**: VictoriaMetrics 查询附加 `extra_label=cluster=<name>`。
- **Rationale**: VM 会把这个条件强制加到所有序列选择器上，不需要改写模型给出的 PromQL，模型也无法越界。
- **Alternatives considered**: 改写 PromQL 插入标签：解析复杂，容易漏掉子查询。

## R5 新后端的"日志"

- **Decision**: `query_pod_logs` 在 victoria 后端返回目标 Pod 的 K8s 事件：按 `cluster` 字段过滤，并在 `_msg` 中匹配 `involvedObject_name`，解析出 type、reason、message、count。
- **Rationale**: 新后端只采集了 event-exporter 的输出；`level` 恒为 INFO，真实类型在文本里；`kubernetes.pod_name` 是 event-exporter 自己的 Pod。
- **Alternatives considered**: 新增 `query_pod_events` 工具：MCP 的工具列表是静态的，新增工具需要修改 AIOps 各节点的工具清单和提示词。

## R6 隧道的限制

- 每个 http 请求固定 20 秒超时，响应整包缓冲 → 同步调用 ≤ 15 秒，修复用异步任务，runner 截断输出（≤ 256KB）。
- xnet-management 3 个副本中只有 1 个 Ready（选主），主副本切换时边缘约 10 秒后重连 → 快速失败，只读调用重试一次。

## R7 已知采集噪声

- 三个集群的 kube-controller-manager、kube-scheduler、etcd 为 `up==0`（kubeadm 绑定 127.0.0.1）；中心采集 3 个虚拟 Node 的 kubelet 失败。不修改采集，在 runbook 中说明识别方法（US6 场景 3）。

## R8 现有联邦查询

- **Decision**: 不复用、不修改 `app/core/federation/`，新环境中关闭。
- **Rationale**: 它要求每个集群部署整套 AIOps，并且中心能访问各集群的 `/ask`。
