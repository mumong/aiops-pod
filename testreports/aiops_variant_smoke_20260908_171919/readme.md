# c01 / c03 多实体、多根因小样本实测

日期：2026-09-08。只运行两次真实诊断，不是全量，也未修改 Agent、Runbook 或评分器。
两次输入完全相同：**我的集群有什么问题？**。服务：`http://10.2.0.48:30800`。
每次最多等待 1200 秒，不重试；开始前按用户授权清理原 c10 测试 namespace。

## 结论

Agent 能发现、分组并分别分析多个异常实体。两次均没有漏掉本轮目标，
第二次正确区分了 Secret 对象不存在和 ConfigMap 存在但卷 key 缺失。
但两次均误读 CPU Quantity，导致 CPU 根因判断错误。**多实体覆盖成功，不等于根因全部正确。**

| 试验 | 实际注入 | 发现目标 | 人工核对主根因 | 诊断耗时 | Run ID |
|---|---|---:|---:|---:|---|
| 同类不同根因 | CPU request 过大 + memory request 过大 | 2/2 | 1/2（50%） | 91.471s | `1ba49130f36f4a6d` |
| c01 + c03 混合 | 上述两个 + Secret 卷对象缺失 + ConfigMap 卷 key 缺失 | 4/4 | 3/4（75%） | 109.265s | `37b3c969e98b4109` |

这是按真实报告人工核对“该 Pod 的具体注入原因”，不是套用旧 c01/c03 单根因评分签名。
只识别 Insufficient cpu、Pending、FailedMount 等表象，不足以通过具体根因判断。
两轮共享同一批 CPU/内存 Pod，不是两次独立重新注入；小样本不能作为稳定准确率或全量验收指标。

## 逐根因复核

| Case / namespace | 真实原因 | 第一次 | 第二次 |
|---|---|---|---|
| c01-cpu / aiops-case-v01 | requests.cpu = 100000 核，API 规范化为 `100k`，远大于任一节点容量 | **失败**：将 `100k` 写成 0.1 CPU，误判为集群 CPU 耗尽 | **失败**：将 `100k` 写成 50m，声称请求极小，误判资源枯竭甚至泄漏 |
| c01-memory / aiops-case-v02 | requests.memory 和 limits.memory 均为 `1Pi`，请求量远超节点容量 | 主根因通过；概览错误声称没有显式 memory request，报告前后矛盾 | 主根因通过，识别为 1Pi 请求过大 |
| c03-secret / aiops-case-v04 | 卷引用的 Secret `unavailable-input` 不存在 | 未部署 | 通过，没有混为 ConfigMap/PVC 问题 |
| c03-key / aiops-case-v05 | ConfigMap `workload-input` 存在且只有 available-key，卷指定 unavailable-key | 未部署 | 通过，没有混为 ConfigMap 对象不存在 |

### CPU 错误不是评分器误判

部署清单写的是 `100000`，Kubernetes API 的 Quantity 规范表示为 `100k`：

- `k` 是十进制千，`100k` = **100,000 CPU 核**；`m` 才表示千分之一核。
- 现场节点 allocatable CPU 分别为 master 18、node1 18、node2 12 核。
- before/after 快照中的 requests.cpu 和 limits.cpu 均为 `100k`。
- 归档 canonical fact `container.resource_request.cpu` 也保留值 `100k`，单位为 `kubernetes_quantity`。
- 调度事件 Insufficient cpu 说明无法满足该请求，不足以证明集群 CPU 使用率已满或存在资源泄漏。

因此这里应判断为请求配置过大，而不是“只申请很少 CPU，却因集群资源枯竭无法调度”。
原文和结构化记录保存了正确数值，但最终报告对数值和因果关系的解释错误。

## 其他观察

- 请求均成功返回最终报告，无超时。第一轮 25 条工具结果中 0 条 error；第二轮 43 条中 8 条 error。
- 第二轮 Layer 调用了当前节点没有开放的工具：`kubectl_describe_pod` 4 次、`kubectl_get_events` 4 次。错误有真实归档，后续 Evidence 仍完成诊断，不能将请求成功率等同于工具调用成功率。
- 第二轮两个 Pending 组的参考清单同时带上 `pod-volume-mount-failed`，范围过宽。挂载组的 Runbook 引用正确，但“有匹配 Runbook”不能证明整个引用清单都合适。
- 第一轮内存组概览声称未显式设置 request，但证据表和最终根因又正确记录 request=1Pi。主根因计通过，不代表整份报告无错误。
- 报告还有“单点指标证明持续状态”“仅凭小 requests 排除资源不足”等过强解释，本次只对主要根因给出上述人工判定。
- Pod 均尚未启动，日志/Trace 为空符合故障机制，不据此判定 Logging/Tracing 平台失效。
- Evidence Plan 完成比例为第一轮 13/14、第二轮 20/25，只是归档审计，不代表证据含义或根因正确；本次未重算四项正式验收指标。
- 两次 before/after 中目标 Pod UID、资源配置一致，未发现目标被替换或由 Agent 修改故障配置。

## 原始材料

- [第一次报告](01-pending-two-causes/report.md)：同类两个根因。
- [第二次报告](02-pending-and-mount-four-causes/report.md)：四个混合根因。
- 每轮 `before.json` / `after.json`：真实 Pod spec/status、UID 和 Events。
- 每轮 `events.json` / `raw.sse` / `live.log`：真实调用过程。
- 每轮 `evidence.archive.json`：Evidence 输出和工具事实；`metrics.json`：服务原始统计。
- [runner.json](runner.json)：请求和清理最终状态；[runner.log](runner.log)：完整执行日志。
- [run_smoke.py](run_smoke.py)：本次复用现有部署管理、SSE 请求和归档读取函数的执行脚本。

## 清理说明

用户授权删除的 c10 及本轮四个 namespace 均属于可通过 Case 清单重新部署的测试资源。
挂载失败 Pod 在普通删除时有等待：v05 在立即删除检查时已自行消失；
v04 经确认 `started=false`、无容器 ID、无重启且只有缺失 Secret 卷后，执行了单 Pod 立即删除。
没有移除 namespace 系统 finalizer，没有清理业务 namespace、PVC 或节点。
最终 runner.json 为 `completed`、`cleanup_errors=[]`；集群只读复查确认上述五个 namespace 均已不存在，后台 worker 已结束。
