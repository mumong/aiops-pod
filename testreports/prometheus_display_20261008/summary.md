# 两类 Prometheus 工具结果解析与展示验收

## 范围

统一原生 Prometheus API 结果与 execute_pod_promql 的 facts 展示。未修改 MCP 返回协议、PromQL、提示词、路由、权限、去重策略或模型原始工具正文。保留前端既有 UI 改动，仅修改共用工具展示函数。

- 原生 vector/scalar/string：保留值、时间、标签；没有依据不猜单位。
- matrix：每条序列展示最新点、采样数与时间范围，明确不是区间平均值。完整数据仍在原文。
- 展示最多 20 条结构化记录，并披露未展开数量；不对指标业务含义作判断或自动聚合去重。
- 空结果、查询错误、部分解析与不支持格式分别披露。原生 histogram 暂不转换成数值，明确提示查看原文。
- 保留 Pod 工具的单位、标签、采样数及统计信息。错误文案不再将未解析等同于无数据。
- 不重写浏览器中已经保存的旧版展示文字；新查询使用新协议。

## 验证

- 后端定向测试：57 passed。
- 全量单元及 Runbook 测试：1701 passed，27 条既有弃用警告。
- 前端 make check：86 tests passed、ESLint 通过、TypeScript/Vite 构建通过。仍有大于 500 kB 的 bundle 警告。
- 浏览器：原有 direct-query 回归通过；两类指标、matrix、空/错误/不支持格式、采样时间及历史刷新回放通过；部署后重复验证通过。
- 真实只读请求通过前端代理到线上后端和 MCP：
  - `3cd0185f941a4ba0`：通用即时工具返回内存值 23.39513815657747；SSE 的 measurements 含值、时间和标签，不再为空。
  - `0e399c11d36a4567`：Pod 工具返回应用容器 28774400 bytes，以及 Pod 聚合、pause 容器两条独立序列；单位和标签保留。
- 前一个 run 模型请求相同工具两次，但实际执行一次、去重一次；不是两次访问 Prometheus。未为此新增特殊处理。
- 以上真实 SSE 另行回放到已部署前端，两个工具数值均显示，未出现“未返回可展示的数值事实”。这是录制回放验证，不冒充浏览器发起的新模型调用。

## 部署

- 后端：`11.0.201-metric-display-20261008`，Pod `aiops-copilot-698847b9f7-mxzs8` 2/2 Running。
- 前端：`0.1.31`，Pod `aiops-copilot-frontend-6bfbdcbfbb-zp4nz` 1/1 Running。
- 两个 rollout 成功，前端 `/api/health` healthy，核心模型仍为 CPA gpt-6-luna / low。未动 Secret、PVC、A2A 或 MCP。
- 镜像使用当前已部署依赖基底，后端更新应用代码，前端更新已通过构建的静态资源。前端首次构建因根目录 .dockerignore 排除 dist 而失败，改用 dist 作为独立构建上下文后成功；未改用户 .dockerignore。
- 未创建任何集群测试 Pod/命名空间，未执行资源写入测试，未 Git commit/push。

## 边界

修复的是数据格式适配，不保证 LLM 生成的统计公式正确。此前 CPU 重复采集造成的分母错误未在本轮用代码修正。线上端到端覆盖两类即时查询；区间、标量、空结果和异常格式使用单元/浏览器回放覆盖。
