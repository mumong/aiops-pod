# 维护约定

本仓库是 K8s AIOps Copilot。项目介绍与入口见 [README](README.md)，模块职责和当前默认行为见[核心流程与模块架构](docs/ARCHITECTURE.md)。不要把历史实验结论作为当前架构约束。

## 修改入口

- HTTP/SSE：app/api/、app/core/service.py、app/core/workflow/executor.py。
- 诊断节点：app/core/workflow/nodes/；路由：app/core/workflow/graph.py。
- 观测解析与投影：app/core/context/；模型循环与压缩：app/core/aicall/。
- Runbook：deploy/configmap/runbooks.yaml；运行配置：deploy/configmap/config.yaml。
- 部署：Makefile、VERSION、deploy/k8s-simple.yaml。
- 测试：全部在 tests/（unit 单元、a2a、acceptance 验收脚本、cases 故障 Case、quality 质量评测）。
- MCP、可观测性组件、前端在独立仓库，链接以 README 为准。

## 维护边界

- 先查代码和配置，不按旧截图、旧行号或旧模型成绩推断当前行为。
- 工具事实、模型解释、评分器预期分开。采集完成不等于诊断正确。
- 修改观测字段、分组或压缩时，验证身份、数值、来源引用、遗漏计数与回读路径。
- 单 Pod 与多 Pod 默认复用独立 lane 的 Evidence 和正式 RCA；保留对应回归。
- 新工具必须同时核对注册 schema、节点暴露范围和权限；关闭修复不代表工具全部只读。
- 测试用标准答案不注入诊断提示词；评分变化与 Agent 改动分别记录。
- 不提交 Secret、API Key、测试 config.env；不覆盖用户未提交改动。
- 集群部署、故障注入、清理与诊断代码修改是不同动作，先核对授权和 kubectl context。
- 核心说明只保留一份来源文档，其余位置引用。过程记录不要当作当前使用指南。
- 更新文档时校验相对链接和示例命令；历史报告保留原分及批次，不随文档更新改写。

A2A 使用独立依赖环境，参见 [A2A 指南](docs/a2a.md)。测试和部署命令以相应 README 为准，不在本文件重复维护。
