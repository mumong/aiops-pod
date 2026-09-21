# c03 挂载失败多根因实测与工程审查

## 结论

**8 次诊断全部完成。** 6 次单独测试的主根因全部正确；两次组合均发现 3/3 个目标、分别判断出 3/3 个主根因，没有把三个同状态对象串因。平均请求耗时 **77.47 秒**，不含部署、归档与清理，也不是自动修复时间。

本轮未表现为模型无法理解三种挂载根因；但确实发现并修复了程序投影丢字段。旧模型靠 Events/Describe 中的冗余信息补救，不能因此忽略代码缺陷。Runbook 选择、少量证据解释仍有问题，不等于所有输出完全正确。

## 测试口径

分别部署 Secret 不存在、ConfigMap 存在但指定 key 不存在、hostPath 目录类型检查失败，各独立请求两次；随后三个场景同时部署，再请求两次。问题始终为 **“我的集群有什么问题？”**，不提供 Pod/namespace 或预期根因。

每次请求前验证当前 Pod UID 对应的 FailedMount 事件，保存请求前后 Pod/Events；组间清理，组内两次复用同一批 Pod。请求串行、超时 1200 秒、不重试。复用 c01 的请求、归档、部署与验收函数，见 [run_c03.py](run_c03.py)。

所有在线诊断均使用原线上 **11.0.157**，没有在测试中途部署本地修复，Runbook 快照哈希未变化。这里测试的是三个独立 Pod 的同症状不同根因，不是同一个 Pod 同时有三个故障。

## 逐次人工审查

“主根因正确”不代表报告的全部语句、证据编号、时间推断和 Runbook 选择都正确。hostPath 事件只证明路径不满足 Directory 检查，报告写“不存在或不是目录”属于合理保留，不判错。

| 部署方式 | 次数 | 耗时 | 主根因结论 | Run ID / 原文 |
|---|---:|---:|---|---|
| Secret 缺失 | 1 | 59.0s | 正确：volume 引用的 unavailable-input Secret 不存在 | [41ca129d629043a7](01-secret/run-01/report.md) |
| Secret 缺失 | 2 | 54.1s | 正确，且没有臆测 Secret 为什么缺失 | [218d4b11924f424e](01-secret/run-02/report.md) |
| ConfigMap 缺 key | 1 | 71.7s | 正确：不存在的是 unavailable-key；但 Runbook 选错 | [02ea1ba3a0e547d6](02-key/run-01/report.md) |
| ConfigMap 缺 key | 2 | 78.0s | 正确：workload-input 中缺少引用的 key | [8689935bab05479a](02-key/run-02/report.md) |
| hostPath | 1 | 78.5s | 正确：node2 上目标路径不满足目录类型检查 | [9d870197180d4b5a](03-hostpath/run-01/report.md) |
| hostPath | 2 | 72.2s | 正确：保留“不存在或不是目录”的合理边界 | [0fb87c6daa4d4599](03-hostpath/run-02/report.md) |
| 三场景同时 | 1 | 92.8s | 找全 3/3，三个主根因均正确，没有互相串因 | [bac1cc9ee03d482b](04-combined/run-01/report.md) |
| 三场景同时 | 2 | 113.4s | 找全 3/3，三个主根因均正确；Runbook 未正确覆盖且没有 lane 归属 | [81371eedec7a4693](04-combined/run-02/report.md) |

本组仅作小样本人工验证，不改动正式质量评分，也不将这些结果外推为所有挂载故障的准确率。

## 模型问题还是工程问题？

### 已确定、已本地修复：原文正确，程序投影漏掉关键配置

在真实归档中逐一对照同一次调用的 raw / structured / summary：

| 证据 | 原始返回 | 原结构化结果 | 修复 |
|---|---|---|---|
| Secret Pod YAML，41ca... / 005 | `secret.secretName: unavailable-input` | `{"name":"input","secret":null}` | 正确读取 secretName，并保留源配置 |
| ConfigMap Pod YAML，02ea... / 004 | `items[].key=unavailable-key, path=app.conf` | 只剩 ConfigMap 名称 | 保留 items、optional、defaultMode 等实际源字段 |
| hostPath Pod YAML，9d87... / 006 | `path=/var/lib/aiops-fixture-unavailable-7f394bef/input, type=Directory` | 只剩卷名 input | 保留 hostPath 的 path/type |

这些不是 LLM 改写错误，也不是 MCP 原文返回错误。用同一归档在本地重新执行提取即可验证；修复后三种真实 YAML 摘要约 1292～1347 字符，关键字段可以正常保留，不需要增加模型上下文。

**为什么旧代码有缺陷，Agent 仍诊断正确？** Describe 和 FailedMount Event 提供了重复的根因证据，模型从这些来源补全了 YAML 投影丢失的信息。本次成功不意味着这个缺陷可以忽略；缺少冗余证据时风险更大。

### 其他确定性缺陷：一并加回归保护

- ConfigMap YAML 原先只提取名称/命名空间，不保留 `data`/`binaryData` 的 key 清单。现在保留 key 清单及 UID/resourceVersion，**不把配置值加入摘要或结构化投影**。本次组合第一轮没有实际查询 ConfigMap 对象 YAML，因此报告不知道完整 keys，不能全部归因于这个潜在缺陷；此项由固定输入复现。
- YAML 中只要出现 `not found` 就被旧代码标记为命令失败，即使它是对象状态中的诊断消息。现在复用调用失败检测，仅识别命令本身失败；真实 NotFound 命令仍标记失败。
- c01 已证实的 Describe 跨作用域文本去重也会影响同类型的多个卷。现在保留容器、Limits/Requests、卷各自的行结构，不因为值相同而删掉字段。
- Pod YAML 摘要补充 resources、volumeMounts，保留配置关联，不做模型式推测或单位换算。

为兼容既有消费者，原有 `volumes[].configMap/secret/persistentVolumeClaim` 简写引用仍保留，增加 `source_details` 保存对应 Kubernetes 原始源字段。本次补全的源类型是 ConfigMap、Secret、PVC、hostPath，不声称覆盖所有 CSI/Projected 等卷类型。

### 未针对性修改：模型选择、推断和工作流取舍

1. **Runbook 选择仍不稳定。** ConfigMap 第一次最终只列出 `pod-imagepull-failed` 和 `pod-sandbox-create-failed`，实际挂载 key 缺失的根因却正确。组合第二次也只列出未归属 lane 的 `pod-config-error`、`pod-imagepull-failed`。已核查这两次 fetch_runbook 的真实归档，确实没有调用挂载 Runbook，不是正确 Runbook 被前端漏显示。因此如果脚本把它们判为未覆盖，是真实未覆盖，不是脚本误判。其他轮次也有正确 Runbook 与不相关 Runbook 同时列出的情况。
2. **Layer 的信息获取设计有取舍。** `FULL_DIAGNOSIS_ALLOWED_TOOLS` 只允许集群列表、单对象简表和 fetch_runbook；简表不包含 Events。模型反复用 get_by_name 索取 Events 无效，或在只知道 ContainerCreating 时猜 Runbook。它并非绝对无法取得 Events：集群列表工具允许 kind=events，但本次部分路径没有正确使用。既有阶段能力限制，也有模型工具选择问题，不能只归为“模型没领域知识”。本次未扩展 Layer 权限或修改路由/提示词。
3. **领域知识并非完全缺失。** 完整 VolumeMount Runbook 已描述 Secret/ConfigMap 对象或 key 缺失、hostPath 路径/类型检查，并要求按 Events 选择分支。Evidence 获得的是筛选章节，不等同于完整原文；`证据优先级/分支诊断流程` 不在该筛选白名单内。这里记录设计边界，不把所有错误归为硬截断。
4. **次要推断不严谨。** 例如把 restarts=0 当作从未启动的独立证明，把单点指标说成长期持续，把较小资源请求当作排除资源不足的充分条件；个别证据表出现“源自 diagnosis 描述”，不能视为直接工具观测。这些没有推翻本轮主根因，但不属于已修复范围。
5. **个别调用参数错误。** hostPath 第一轮 Layer 查询了不存在的资源种类 `imagepullsecret`；组合第二轮的 custom-columns 查询语法错误。正文命令失败但外层 status 为 success。后续获取了正确的 Describe/Event，因此未导致根因错误。不能用外层 success 代替有效采集判断。

### 对 c01 的结论没有改变

本次一并修复了 c01 的摘要去重问题，但没有修改 Kubernetes quantity 解释或模型。c01 曾在 Prometheus 明确返回 request=100000 core、节点容量 18/18/12 core 后仍推理错误，这部分仍有模型理解因素。不能因为修复了投影就宣称 CPU 误诊已经解决。

## 修复与验证范围

本次业务代码只修改 `app/core/context/observation.py`；新增 `tests/unit/context/test_observation_volume_projection.py`。没有修改 MCP 服务、Agent 提示词、Runbook、正式评分脚本或在线部署，也没有提交/push。

验证：

```bash
.venv/bin/python -m pytest tests/unit/context \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_fact_contract.py -q --tb=short
```

**282 passed**，其中新增 11 项回归。另对本次 Secret、ConfigMap-key、hostPath 真实 YAML 归档以及前次 CPU Describe 做了本地回放；`git diff --check` 通过。

边界：结构化源字段保留不等于最终自由文本受确定性语义约束；现有摘要预算、行数限制和 LLM 压缩路径仍存在。未在本轮中宣称全部事实始终无损、引用必然支持根因，或修复已提高线上准确率。

## 归档与清理

2026-09-08 18:24:10 完成：`runner.json.status=completed`、`cleanup_errors=[]`，工作进程 4075162 已退出；三个测试 namespace 均不存在，集群非 Running/Succeeded Pod 查询为空。8 次请求前后目标 UID 均一致。

- [runner.json](runner.json)：8 次运行的状态、耗时、Run ID；[runner.log](runner.log)：部署、校验、调用和清理过程。
- 各次目录保存 `report.md`、`events.json`、`raw.sse`、`evidence.archive.json`、`before.json`、`after.json`。
- [runbook-snapshot.json](runbook-snapshot.json)：测试期间的真实 Runbook。
- 完整节点/工具归档在 `/data/redis/aiops-aiops-reports-pvc-pvc-52d8916d-bd02-4ad3-9c91-ea2e59356b51/context_archives/<run_id>-<lane>/`。
- 三个单独场景清理时，未启动的测试 Pod 在删除阶段滞留；组合结束后 Secret/ConfigMap 两个 Pod 也出现同样情况。核对当前 UID、无 containerID、started=false 后，只强制移除了对应的本次 workload 对象，没有清空 namespace finalizer，也没有创建缺失的 Secret/key/宿主机目录去恢复它们。删除的是可重建的测试资源，诊断归档保留。
- 首次启动器错误地解析了虚拟环境 Python 的符号链接，导入 requests 失败，尚未部署或发出诊断；改用虚拟环境原路径启动后完成测试，未计作 Agent 失败。
