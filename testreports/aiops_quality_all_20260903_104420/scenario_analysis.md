# AIOps 全量质量测试：分场景分析

## 1. 测试信息

- 测试范围：c01～c11
- 每个场景运行：50 次
- 总运行数：550 次
- 请求成功：550/550
- 测试时间：2026-09-03 10:44 ～ 2026-09-04 08:05
- 总耗时：约 21.35 小时
- 验收阈值：根因准确率、Runbook 覆盖率、证据完整度均为 `>= 70%`，MTTR 为 `< 15m`
- 数据来源：同目录下的 `stats.json`、`summary.md`、`overview.txt` 和 `runner.log`

## 2. 总览

| Case | 异常类型 | 根因准确率 | Runbook 覆盖率 | 证据完整度 | 平均 MTTR | 初步判定 |
|---|---|---:|---:|---:|---:|---|
| c01 | PendingUnschedulable | 80.0% ✅ | 94.0% ✅ | 70.7% ⚠️ | 2.1m ✅ | 根因基本稳定；证据受旧 RBAC 影响 |
| c02 | ImagePullFailed | 100.0% ✅ | 98.0% ✅ | 49.5% ❌ | 2.0m ✅ | 根因稳定；证据分数不可作为干净基线 |
| c03 | VolumeMountFailed | 100.0% ✅ | 90.0% ✅ | 71.9% ⚠️ | 2.0m ✅ | 诊断稳定；证据受旧 RBAC 影响 |
| c04 | ConfigError | 96.0% ✅ | 98.0% ✅ | 46.8% ❌ | 1.9m ✅ | 根因稳定；证据分数不可作为干净基线 |
| c05 | SandboxCreateFailed | 98.0% ✅ | 48.0% ❌ | 80.4% ✅ | 2.8m ✅ | 根因稳定，Runbook 选择不稳定 |
| c06 | CrashLoopBackOffRuntime | 68.0% ❌ | 98.0% ✅ | 78.1% ✅ | 2.4m ✅ | 根因临界不达标，且有评分假阴性 |
| c07 | ConfigError + Exit 78 | 94.0% ✅ | 49.0% ❌ | 82.1% ✅ | 1.8m ✅ | 根因稳定，双 Runbook 覆盖不足 |
| c08 | OOMKilled | 80.0% ✅ | 46.0% ❌ | 77.4% ✅ | 2.8m ✅ | 根因通过但波动，OOM Runbook 经常缺失 |
| c09 | Readiness Probe 503 | 18.0% ❌ | 100.0% ✅ | 87.4% ✅ | 2.7m ✅ | 最优先排查：证据充分但 RCA 路径混淆 |
| c10 | Liveness Probe 500 | 8.0% ❌ | 49.0% ❌ | 75.4% ✅ | 2.8m ✅ | 最优先排查：评分假阴性与输出缺词并存 |
| c11 | TerminatingStuck | 76.0% ✅ | 96.0% ✅ | 87.4% ✅ | 1.9m ✅ | 通过但根因波动，部分缺少 finalizer 事实 |

## 3. 优先排查顺序

1. **c09**：41/50 次根因评分失败，但 Runbook 50/50、证据完整度 87.4%。采集链路不是主要瓶颈，RCA 多次把真实探针路径 `/ready` 写成 `/work`。
2. **c10**：46/50 次根因评分失败，双 Runbook 仅 49/100。部分输出实际已正确说明 Liveness Probe 500，但评分器把“排除 OOMKilled”中的 `OOMKilled` 当作冲突词，存在大量假阴性。
3. **c06**：根因准确率 68%，只差一个百分点等级即可通过。失败同时包含格式匹配问题、排除项误判以及 Agent 过度输出“证据不足”。
4. **c05、c07、c08**：根因整体可用，主要问题是 Runbook 选择或双 Runbook 覆盖不完整。
5. **c01～c04**：需要在 RBAC 修复后重跑，尤其是 c02、c04 的证据完整度不能代表当前系统能力。

## 4. 逐场景结果

### c01 — PendingUnschedulable

- 故障：`nodeSelector: aiops.lab/unavailable=true` 无匹配节点。
- 期望 Runbook：`pod-pending-unschedulable`。
- 根因准确率：40/50，80.0%；失败 10 次。
- Runbook：47/50，94.0%；完整通过 47 次。
- 证据完整度：70.7%；19/50 次低于 70%；最低为 40.0%。
- MTTR：平均 2.1m，P95 9.9m，最大 10.7m。
- 初步分析：多数输出正确识别节点选择器不匹配；部分评分失败是结论没有稳定包含具体值 `aiops.lab/unavailable`，即使语义上已经说明 nodeSelector 不匹配。
- 代表性根因失败 Run ID：`b8bc48031421481d`、`c04b806c8fb14ef2`、`25c8b846f5d24919`。
- 最低证据 Run ID：`9f7d39bd9bda4834`（40.0%）。
- 数据备注：运行于 Logging RBAC 修复前，证据完整度受污染。

### c02 — ImagePullFailed

- 故障：镜像仓库 `registry.invalid` 无法解析。
- 期望 Runbook：`pod-imagepull-failed`。
- 根因准确率：50/50，100.0%。
- Runbook：49/50，98.0%；完整通过 49 次。
- 证据完整度：49.5%；44/50 次低于 70%；最低为 20.0%。
- MTTR：平均 2.0m，P95 3.5m，最大 10.1m。
- 初步分析：根因和 Runbook 都稳定。证据低分与根因质量不一致，主要因为运行时 Logging 查询被 RBAC 拒绝，以及动态 Evidence Plan 中部分计划未完成。
- 最低证据 Run ID：`9fa5c23a6db24774`（20.0%）。
- 数据备注：当前 49.5% 不能作为修复后的证据能力基线，建议单独重跑。

### c03 — VolumeMountFailed

- 故障：Pod 引用不存在的 ConfigMap 卷。
- 期望 Runbook：`pod-volume-mount-failed`。
- 根因准确率：50/50，100.0%。
- Runbook：45/50，90.0%；完整通过 45 次。
- 证据完整度：71.9%；22/50 次低于 70%；最低为 40.0%。
- MTTR：平均 2.0m，P95 9.7m，最大 10.2m。
- 初步分析：Kubernetes Event/YAML 足以稳定锁定 ConfigMap 不存在。Logging 在本场景本来通常无业务日志，但 RBAC `Forbidden` 仍会使相应 Plan 项判定失败。
- 最低证据 Run ID：`2b7bcb8340de431e`（40.0%）。
- 数据备注：运行于 Logging RBAC 修复前，证据完整度受污染。

### c04 — ConfigError

- 故障：Secret 中缺少 `unavailable-key`。
- 期望 Runbook：`pod-config-error`。
- 根因准确率：48/50，96.0%；失败 2 次。
- Runbook：49/50，98.0%；完整通过 49 次。
- 证据完整度：46.8%；49/50 次低于 70%；最低为 20.0%。
- MTTR：平均 1.9m，P95 2.5m，最大 10.5m。
- 初步分析：根因识别稳定；证据完整度异常低与 Logging/Tracing 的 `pods/exec Forbidden` 明确相关，不能据此判断当前可观测性能力差。
- 根因失败 Run ID：`b074d9467e7b41dc`、`c39a57a1721a40fc`。
- 最低证据 Run ID：`eb366a9e0443442a`（20.0%）。
- 数据备注：建议修复后重跑 c04，再与 46.8% 对比。

### c05 — SandboxCreateFailed

- 故障：Multus 引用的 NetworkAttachmentDefinition `unavailable-network` 不存在。
- 期望 Runbook：`pod-sandbox-create-failed`。
- 根因准确率：49/50，98.0%；失败 1 次。
- Runbook：24/50，48.0%；完整通过 24 次。
- 证据完整度：80.4%；13/50 次低于 70%；最低为 50.0%。
- MTTR：平均 2.8m，P95 9.8m，最大 10.0m。
- 初步分析：Agent 基本都能根据 `NoNetworkFound` / `FailedCreatePodSandBox` 得出正确根因，但定位阶段经常只参考 ImagePull 或 VolumeMount Runbook，未稳定选中 Sandbox Runbook。
- 根因失败 Run ID：`c72356a22c3742a8`。
- 最低证据 Run ID：`73b35497f25a4104`（50.0%）。
- 主要改进点：Runbook 选举，而不是证据采集或 RCA。

### c06 — CrashLoopBackOffRuntime

- 故障：应用处理 `/work` 时主动以 Exit Code 2 非零退出。
- 期望 Runbook：`pod-crashloop-runtime`。
- 根因准确率：34/50，68.0%；失败 16 次。
- Runbook：49/50，98.0%；完整通过 49 次。
- 证据完整度：78.1%；13/50 次低于 70%；最低为 57.1%。
- MTTR：平均 2.4m，P95 9.2m，最大 10.3m。
- 初步分析：三类问题混合存在：
  1. 输出写成 `exit_code: 2` 等格式，未命中评分器的 `Exit Code 2` 词形；
  2. 输出正确排除 OOMKilled，但排除词仍可能被机械冲突规则命中；
  3. Agent 已确认运行时退出机制后，仍将结论写成“证据不足”，降低确定性。
- 代表性根因失败 Run ID：`d3b14d41e69045ca`、`104b5ebc0ef141f8`、`aae7b93a1f0941b4`。
- 最低证据 Run ID：`e5c79dcfe52a4986`（57.1%）。
- 主要改进点：先人工区分真实 RCA 失败与评分器假阴性，再决定改 Agent 还是评分规则。

### c07 — ConfigError + Exit 78

- 故障：应用因 `CONFIG_MISSING` 配置缺失，以 Exit Code 78 退出。
- 期望 Runbook：`pod-config-error`、`pod-crashloop-runtime`。
- 根因准确率：47/50，94.0%；失败 3 次。
- Runbook：49/100，49.0%；仅 2/50 次同时覆盖两个 Runbook。
- 证据完整度：82.1%；9/50 次低于 70%；最低为 42.9%。
- MTTR：平均 1.8m，P95 2.5m，最大 2.6m。
- 初步分析：根因输出稳定且耗时稳定；低 Runbook 分来自该场景要求同时参考“配置错误”和“运行时崩溃”两个 Runbook，但 Agent 通常只选其中一个。
- 根因失败 Run ID：`3f5ca161353a4086`、`3b9df4aa68754176`、`e0725374f44241f6`。
- 最低证据 Run ID：`0cc4f9b3c30c4cc0`（42.9%）。
- 主要改进点：明确双机制 Case 的 Runbook 选举策略。

### c08 — OOMKilled

- 故障：请求驱动内存增长超过 64Mi Limit，触发 OOMKilled。
- 期望 Runbook：`pod-oomkilled`。
- 根因准确率：40/50，80.0%；失败 10 次。
- Runbook：23/50，46.0%；完整通过 23 次。
- 证据完整度：77.4%；16/50 次低于 70%；最低为 50.0%。
- MTTR：平均 2.8m，P95 10.1m，最大 13.5m。
- 初步分析：大部分运行能识别 Exit 137/OOMKilled，但根因和 Runbook 都存在明显波动。由于证据完整度已通过，优先检查 RCA 是否被 HTTP 500、探针或业务请求等伴随现象带偏，以及 OOM Runbook 为什么未被稳定 fetch。
- 代表性根因失败 Run ID：`22fd3df3ade543d5`、`79f64c84667e4950`、`41dd3173a0944671`。
- 最低证据 Run ID：`224a29ee32104521`（50.0%）。
- 主要改进点：OOMKilled 决定性事实的优先级和 Runbook 稳定选举。

### c09 — Readiness Probe 503

- 故障：Readiness Probe 请求 `/ready` 返回 HTTP 503。
- 期望 Runbook：`pod-notready-probe-failed`。
- 根因准确率：9/50，18.0%；失败 41 次。
- Runbook：50/50，100.0%。
- 证据完整度：87.4%；仅 2/50 次低于 70%；最低为 60.0%。
- MTTR：平均 2.7m，P95 9.9m，最大 10.6m。
- 初步分析：这是最明确的 RCA 问题。证据和 Runbook 均稳定，但大量结论将健康检查路径写为 `/work`，缺少期望的 `/ready`；有些报告还把“内部依赖不可用”继续下钻成证据不足，未把 Readiness `/ready` 503 作为当前异常的直接根因。
- 代表性根因失败 Run ID：`397eabaa5db048ef`、`7b9028baee3648d5`、`4f6e25c6d7234a23`。
- 最低证据 Run ID：`c2782de0347942dc`（60.0%）。
- 主要改进点：防止业务路径 `/work` 覆盖探针路径 `/ready`，并统一“当前异常直接根因”的诊断层级。

### c10 — Liveness Probe 500

- 故障：Liveness Probe 请求 `/health` 返回 HTTP 500，Kubelet 随后终止并重启容器。
- 期望 Runbook：`pod-notready-probe-failed`、`pod-crashloop-runtime`。
- 根因准确率：4/50，8.0%；失败 46 次。
- Runbook：49/100，49.0%；仅 4/50 次同时覆盖两个 Runbook。
- 证据完整度：75.4%；17/50 次低于 70%；最低为 37.5%。
- MTTR：平均 2.8m，P95 7.5m，最大 13.4m。
- 初步分析：自动 8% 严重低估了部分真实输出质量。抽样中多次已经正确写出 `Liveness Probe`、`/health`、HTTP 500 和 Kubelet Kill，但评分器存在两类假阴性：
  1. 报告写“排除 OOMKilled”，机械评分仍把 `OOMKilled` 识别为冲突；
  2. 有些结论正文未同时保留 `/health` 或 `HTTP 500`，导致严格词组合同不通过。
- 代表性根因失败 Run ID：`deb83ec157f049d6`、`ef49c603a98d4664`、`937a9e846e6f4d72`。
- 最低证据 Run ID：`0818abc6afc5460e`（37.5%）。
- 主要改进点：首先修正否定语义评分，再复算真实准确率；随后处理 `/health`/500 关键事实在结论中丢失的问题。

### c11 — TerminatingStuck

- 故障：自定义 finalizer `aiops.lab/hold` 阻塞 Pod 删除。
- 期望 Runbook：`pod-terminating-stuck`。
- 根因准确率：38/50，76.0%；失败 12 次。
- Runbook：48/50，96.0%；完整通过 48 次。
- 证据完整度：87.4%；仅 2/50 次低于 70%；最低为 62.5%。
- MTTR：平均 1.9m，P95 3.3m，最大 11.3m。
- 初步分析：多数运行正确锁定 finalizer；失败样本分为两类：部分已正确写出 `aiops.lab/hold`，但因同时讨论或排除 OOMKilled 被冲突规则判失败；另一部分确实没有在证据中拿到 finalizer 字段，因此保守输出“证据不足”。
- 代表性根因失败 Run ID：`6c42aa2c20ac4d07`、`e3c77871d3c049c2`、`cbee577281154263`。
- 最低证据 Run ID：`c0cfb415f6724411`（62.5%）。
- 主要改进点：确保 Pod YAML 的 `metadata.finalizers` 成为稳定关键证据，并让评分器理解“排除 OOM”不是把 OOM 当根因。

## 5. 环境与评分口径注意事项

### 5.1 c01～c04 的 Logging 数据污染

c01～c04 运行期间，`mcp:mcp-server-manager` 尚无 `monitor` Namespace 的 `pods/exec` 权限。Runner 表面的：

```text
query_pod_logs status=success
```

仅代表 MCP 调用返回了结构化响应；归档内部实际为：

```text
status: query_rejected
coverage: error
Forbidden: cannot create resource pods/exec in namespace monitor
```

因此 c01～c04 的动态 Evidence Plan 完成度会被压低。RBAC 修复后的 c05 开始，Logging/Tracing 返回 `coverage=empty/present`，不再是权限错误。

### 5.2 根因准确率不是完整的人工正确率

当前根因准确率由严格语义合同自动评分。以下情况可能产生假阴性：

- 正确写出根因，但没有保留合同要求的具体路径或配置值；
- 使用 `exit_code: 2` 等未完全覆盖的词形；
- 在“排除 OOMKilled”中出现排除词，机械评分仍将其当成冲突；
- 已确认直接失败机制，但报告又使用“证据不足”降低结论确定性。

因此 c06、c10、c11 应先人工复核失败样本，再将自动分数解释为真实 Agent 准确率。

### 5.3 证据完整度口径

单次运行按以下公式计算：

```text
单次证据完整度 = Evidence Plan 实际成功采集项 / Evidence Plan 计划项
```

场景证据完整度是 50 次成功运行各自完整度的算术平均，不是先汇总全部计划项后按数量加权。

## 6. 建议的下一轮验证

1. RBAC 修复后单独重跑 c01～c04，更新证据完整度基线。
2. 对 c09 先人工查看 5～10 个失败 Run，确认 `/ready` 被 `/work` 替换发生在 Evidence、RCA 还是 Conclusion。
3. 对 c10 使用现有 50 次输出离线修正否定语义评分后重新计分，不必先重新调用 Agent。
4. c06、c11 同样先离线复算，避免把评分器问题误认为 Agent 能力问题。
5. c05、c07、c08 聚焦 Runbook fetch/选举链路，不需要优先调整证据采集。
