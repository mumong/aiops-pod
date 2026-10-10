# 分组证据与共享 Runbook 传递（2026-10-10）

## 边界

仅改善上下文传递，不改变诊断路由、工具选择、权限、审批或根因判断。不强制读 Runbook、不强制补查，不增加诊断 LLM 调用。

- `context/handoff.py`：保留分组目标、执行状态、失败边界、原始证据引用及已有采集元数据。来源索引不是诊断事实核验。
- 节点间压缩和采集循环压缩均携带 `protected_handoff`，后续节点从压缩事件恢复；再次压缩不能仅靠模型重建这些关系。
- 并发分支继承的成功 Runbook 原文，在有真实归档引用时替换为引用和自主补读说明。无引用、失败返回、分支新读取结果不做这种替换。原文归档仍保留，模型可自主读取。
- 轻量结构仍计入总上下文预算，不绕过预算校验。长分析与工具正文仍可能被摘要；不承诺所有高价值内容零损失，也不保证模型遵守全部呈现建议。
- 不修改前端、Runbook 页尾格式或报告分组渲染；这些不是本轮批准的两个传递改动。

## 测试

- 隔离 HEAD 快照叠加本轮变更：`pytest tests/unit -q`，1740 passed。
- 新测试覆盖：摘要完全遗漏分组时连续两次压缩仍保留结构；跨消息/节点恢复；共享全文替换；失败、无归档、新读取保持原样；工具调用 ID 不变。
- 12 项提示词快照更新前，移除新增字段与新增说明后，旧哈希全部恢复。工具配置及调用参数未变。
- `3a1d8afa96144e83` 原始输入回放：三组身份与引用关系保留。各分支的三本共享 Runbook 改用引用后，工具观察 JSON 各减少约 40KB（序列化字节测量，不是 token 或延迟）。
- 在线 Pod 中用真实模型压缩同一归档：通过；g1/g2/g3 保留，摘要 3460 字符，保护结构 21298 字符，耗时 95.3 秒。此项验证完整性，不代表压缩延迟已经降低。
- 前端代理真实只读验证 run：`16d807c073d34fd3`。真实分支输入已确认只携带三本共享手册引用。运行中原测试资源消失：后续 namespace/Pod 查询返回 NotFound；不能将其作为原故障根因准确性的完整验收。
- 该真实运行 277.2 秒收到完整 `final` / `run_end`，最终为 `partial`，披露 `step_limit` 与资源 NotFound，未虚构完整取证。总结前真实触发压缩，`after_compaction.protected_handoff.groups` 保留 g1/g2/g3，每组 14 条来源记录；摘要 2971 字符。分支执行 completed 不等于整次取证充分。
- 因环境变化及步骤限制，不能宣称端到端诊断准确性全部通过；本轮没有调高步数或新增自动重试。最终报告仍使用全局证据表，未扩大到展示重构。

## 部署

- 后端：`11.0.207-handoff-20261010`
- 镜像摘要：`sha256:6c013bfcdab82fada40f61748bdd0e7d8cf0e87f98b2512569e0c9c60b4897ac`
- 基于线上 206 镜像，仅覆盖本轮六个代码文件，排除工作区 evidence-view 等未发布实验。
- Deployment 滚动更新完成，Pod `aiops-copilot-5dc7f845f-5vtv6`，2/2 Ready。
- 前端 `/api/health` healthy；模型仍为 `openai/gpt-6-luna`。前端、MCP、A2A 镜像与配置、Secret、PVC 未改。
- 后续按用户要求提交本轮已上线代码、测试、版本与部署清单；工作区未发布实验保留，不混入本次提交。构建、测试和回放材料：`/tmp/aiops-handoff-release.gFkMY8/`。

回滚只需恢复后端容器镜像：

```bash
kubectl set image deployment/aiops-copilot -n aiops aiops-copilot=xnet.registry.io:8443/xnet-cloud/aiops-copilot:11.0.206-metric-labels-20261010
kubectl rollout status deployment/aiops-copilot -n aiops --timeout=300s
```
