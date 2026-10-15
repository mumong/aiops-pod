# 分组修复最小框架

## 已实现边界

- 复用已持久化诊断 groups，不增加故障分类器或按故障名分支。无分组的旧报告按单组处理。
- 单组和多组使用相同修复节点；并发调度器与诊断共用。规划并发度沿用 `AIOPS_AUTONOMOUS_PARALLEL_WORKERS`。
- 每组独立工作流、模型客户端、会话和方案版本。仅投递本组诊断、证据摘录及共享证据/Runbook 引用；模型自主补读，不拼接全部方案再次压缩。
- 修复任务在后端运行，不依赖 SSE 或页面保持连接。前端刷新通过 batch ID 重新读取；未提交的反馈草稿只在当前组件内按 job ID 隔离。
- 人工反馈通过明确的 job ID/version 重新调用修复规划节点，不进入普通意图识别；旧版方案原子失效，其他组不受影响。
- 沿用既有安全校验与人工审批/自动执行配置，不新增故障特判。所有 Pod 修复执行器共享进程内命令锁，审批等待不持有命令锁。
- 命令返回与恢复验证分离：`needs_followup` 表示命令已完成，不能视为故障已恢复。持续观察器属于后续 Sprint。

## 接口（与前端无关）

所有接口使用原诊断的 `aiops_query_owner` cookie；CLI 须保存并回传 cookie，不得把 run ID 当鉴权凭证。

| 接口 | 用途 |
|---|---|
| POST `/repair/batches`，`{diagnosis_run_id, question?}` | 每份诊断一个修复工作区；重复请求返回同一工作区，避免重复启动 |
| GET `/repair/batches/{batch_id}` | 组状态列表，不合并所有方案正文 |
| GET `/repair/jobs/{job_id}` | 本组方案、版本、待审批动作与执行输出 |
| POST `/repair/jobs/{job_id}/feedback`，`{version, feedback}` | 定向修改，返回新 job ID/版本；冲突返回 409 |
| POST `/repair/jobs/{job_id}/cancel`，`{}` | 请求停止后续操作；不回滚已执行动作 |
| POST `/remediation/approve` | 既有表单接口，job ID 作为 run_id，逐动作批准/拒绝 |

前端卡片仅调用这些接口，未引入浏览器专用的后端权限路径。既有 A2A 适配器尚未接入新协议；后续需传递所属会话身份和目标 job/version，不能声称已有 A2A 修复能力。

## 部署约束和已知限制

- 当前按既有单实例、单进程部署。审批存储与后台线程不是分布式任务队列；多副本需要另行设计协调，不可直接扩容。
- 诊断、方案和任务元数据持久化于 reports PVC。进程重启时活动任务显示 interrupted，不自动重放命令；中断时的写操作可能已生效，需核实状态。
- 执行中的旧方案不允许修改。服务恰在执行时重启，记录仍为 executing 时也不会强制解除，需要人工核实后处理。
- Pod 作用域占用沿用既有实现。不同 Pod 归属同一 Deployment 的互斥/方案合并尚未实现；本轮命令串行不等于消除所有跨资源配置冲突。
- 原始工具证据仍遵循现有摘录预算，不承诺信息零损失；这里解决的是分组交接和方案隔离。
- 安全控制扩展、完整恢复观察器、任务保留/回收策略仍是后续工作。没有新增 Secret 值读取过滤，也没有因此宣称安全审查完成。

## 验证入口

- 后端：`tests/unit/remediation/test_jobs.py`、`test_group_context.py`、`tests/unit/workflow/test_group_runner.py`，以及原诊断/执行器回归。
- 前端：`tests/grouped-repair.browser.py`（桌面/移动端三卡片、草稿隔离、反馈、刷新）和旧方案兼容回放。
- 真实集群：`scripts/test_grouped_repair_live.py --api URL --namespace UNUSED_NAMESPACE --output DIRECTORY`。显式创建隔离测试资源，按审批模式验证，不修改全局自动开关；脚本不会自动删除现场，测试后需定点清理。

## 2026-10-10 验收记录

- 发布：后端 `11.0.214-group-repair-20261010`，前端 `0.1.46`。MCP、A2A 镜像及生产配置未改；当前 `review` 人工审批模式。
- 隔离发布目录后端单测 **1763 passed**；前端 **100 passed**，ESLint、TypeScript、Vite 构建通过。构建仍有既有大 bundle 提示；后端依赖有弃用警告。
- 浏览器：桌面/移动端三组卡片、草稿隔离、定向反馈、版本替换、刷新恢复、旧方案兼容、普通查询和会话切换回放通过。部署页面读取真实三个任务亦通过。
- 普通查询与上下文追问：`e60de31532f64813`、`d966cc89fc944ec4`，均正确绑定 aiops/aiops-copilot，分别查询配置副本及可用副本数。
- 真实诊断 `ebd090bf1585434e`，工作区 `batch-ebd090bf1585434e`：三组分别规划，定向修改第一组时其他组版本及审批不变；批准后实际执行命令。两个 Deployment 新 Pod `1/1 Running`、重启计数 0，独立 HTTP 检查均为 200，finalizer 测试 Pod 已删除。执行器仍诚实返回 `needs_followup`，恢复结果来自验收脚本独立检查，不是已实现通用持续观察器。
- 不能算首次全自动成功：第一组初稿提前停止调查控制器，通过本组反馈继续补证后生成动作；第三组初稿使用 `get Pod` 验证删除，NotFound 会导致非零退出，通过本组反馈改正了验证表达。没有为此增加故障特判或强制生成命令。
- 联调修正的工程缺口：后台入口遗漏 `query_mode=auto` 导致误走旧诊断链；正常工作流结束误设置取消信号；分组规划上下文未在提示中明确范围；前端工作区 ID 未即时保存。已补对应回归。
- 第一套测试夹具误用了 Python 默认 HTTP handler，返回 501，执行器正确报验证失败；修正夹具并创建新隔离场景重测后通过，不将失败试验计为恢复成功。
- 原诊断全量报告的压缩/总结仍有明显耗时，本轮未改其压缩架构。自动模式有执行器回归覆盖，真实集群本轮仅走人工审批；完整 A2A 修复、长时间恢复观察、多实例协调尚未验收。

运行日志与现场快照：`/tmp/aiops-grouped-verified-20261010/`；其中 `session.json` 为测试会话身份，权限 0600，不应提交或公开。发布回归日志：`/tmp/aiops-repair-release.lvLpSl/unit-grouped-final.log`。
