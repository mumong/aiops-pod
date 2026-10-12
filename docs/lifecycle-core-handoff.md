# 诊断核心事实交接

## 边界

`protected_handoff.lifecycle_core` 是工具事实投影，不是诊断结论或待办清单。
所有已返回的 Pod 都保留，不按故障类型筛选，不规定诊断组数，不增加强制工具调用。
模型仍自行选择调查对象、Runbook、补证和结论。

## 保留与精简

- 保留 namespace、name、UID、node、phase、reason、deletion_timestamp。
- 保留 Ready、ContainersReady、Initialized、PodScheduled 条件的状态和原因。
- 保留所有容器的身份、角色、状态是否已观测、Ready、累计重启及窗口标记。
- 保留当前/上次容器状态种类、reason、exitCode、signal。
- 采集时间、查询范围、窗口、覆盖情况、分页信息和原文引用按来源保存一次。
- 不重复传递条件消息、资源详情及逐容器时间字段；完整原文和结构化归档不变。
- 缺失/null 不转换为健康值；false 和 0 必须保留。

`evidence-records.v1` 的筛选/统计结果独立保留原始查询、列、记录及覆盖信息，
不能用只有部分字段的记录替换完整 Pod 状态。

## 流程

1. 定位/取证工具输出紧凑事实，前端结构化数据和原文归档保持原契约。
2. 代码在压缩前提取核心 JSON；模型只整理其余内容。
3. 摘要输入提供“核心事实另行传递”的提示，避免误写成未采集。
4. 压缩完成后代码附加原核心 JSON，重复工具正文改为引用；保留工具调用配对。
5. 跨节点和并发汇总合并核心：同 namespace/name 采用较新采集，不混合不同 UID；
   同批来源不重复投递。原分支状态不被修改。
6. 如果附加核心后仍超过上下文预算，保留旧工作状态并明确报错，不能裁剪核心。

窗口标记只描述近期事件，不能把仍未就绪/删除中的对象当作已恢复。
同样，已就绪对象的历史重启/last_state 本身不能证明当前故障。

## 验证

单元/回归入口：`tests/unit/aicall/test_lifecycle_core.py`，以及原有
protected_handoff、working_context、context_handoff、observation、record_result、
repair_record_handoff 和 handoff_prompt_templates 测试。2026-10-12 共 275 项通过。

真实快照：`e7a403c767e24c6b` 的 `002-layer-query_pod_lifecycle.raw.txt`。
原始 72 个 Pod、93,749 字符；紧凑 JSON 约 46,981 字符，仍保留 72 个对象。
按 UTF-8 bytes/3 估算，约从 31,250 降至 15,661 token（不是模型精确计数）。

线上模型 `openai/gpt-6-luna` / `low` 的两轮直接回放都识别出四个候选异常。
进一步验证真实压缩链路时发现摘要可能误报“未采集”，或把已恢复历史重启列入候选；
已增加事实可用性提示及当前/历史状态区分原则，未增加故障特判或固定目标列表。
修正后候选代码的真实压缩→事实等值核验→分组回放通过：72 个对象、4 个目标，
下一轮不再次触发压缩。归档目录：`validation-lifecycle-core-219`。
最终部署 `11.0.219-lifecycle-core-20261012` 后，在真实服务 Pod 内重复上述链路通过，
后端和前端代理 `/health` 正常，Deployment 滚动更新完成。镜像 digest：
`sha256:05d54e988ab7ed7dc56e7da7714fd9ecd6cd126e1e3ab1af9b9a3085c24bd0bc`。
发布基于原线上 `.217` 镜像，仅覆盖本次相关文件，没有混入本地证据视图实验；
前端、A2A sidecar、凭证、PVC 和异常测试资源均未修改。没有执行 Git commit/push。

## 已知限制

保证的是已定义核心字段不被 LLM 摘要覆盖，并非模型必然作出正确诊断。
未采集的对象、被源查询过滤掉的字段不能恢复；详情需要按原文引用自主补读。
部分页未出现某对象不等于对象被删除，旧观测仍按原采集时间保留。
极大集群仍可能超过预算，此时明确失败；本次没有新增自动分区/分页调度。
当前集群已有场景被修复，因此四对象验证使用历史快照，不伪装成当前集群状态。
