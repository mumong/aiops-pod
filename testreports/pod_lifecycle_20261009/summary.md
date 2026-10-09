# Pod 生命周期事实验证（2026-10-09）

## 后续调整：默认窗口 10m

按用户要求将工具描述、输入 schema 默认值及执行默认值统一改为 10 分钟；
累计重启次数、原始终止事实、显式指定窗口的能力不变。以下早先 30 分钟验收记录保留历史口径。

- MCP 全量单测 253 项通过，后端生命周期单测 2 项通过。
- 新增 600 秒计入、601 秒不计入、20 分钟终止不落入默认窗口，以及显式 30 分钟覆盖测试。
- 真实 MCP `tools/list` 默认值为 10；省略 window_minutes 返回 10，显式传 30 返回 30，均成功。
- 部署镜像 `7.0.33-pod-lifecycle-10m-20261009`，digest
  `sha256:517ea91148495987b328fae02f75971fce089940900aff040d8c1cb0dc9c3fc0`。
- 后端代码镜像仍为 `11.0.204-pod-lifecycle-20261009`，滚动重启刷新工具定义；未修改前端。

## 范围

新增可选只读 MCP 工具 `query_pod_lifecycle`，后端开放给快速查询和自主诊断，
分页事实原样传递。无强制诊断步骤、故障分类或修复脚本；未改前端、模型、RBAC 和旧工具接口。

## 自动测试

- 后端 `tests/unit` + `test/workflow/test_runbook_remediation_guidance.py`：1718 passed。
- MCP `scripts/test_unit.py`：252 passed。
- 既有 kubernetes_core 工具定义摘要保持不变（新工具除外）。
- 覆盖 Running/Ready + 27 秒前 OOM、20/30 分钟与超窗边界、缺失/未来时间、
  初始化/临时容器、Completed、分页、UID、空结果、API 错误及超时。
- 大页在后端原样保留，不受单工具摘要长度限制。
- 集群内 raw API 配置引用 ServiceAccount tokenFile；临时配置为 0600，使用后删除，
  不将 token 写入参数或日志，显式外部 kubeconfig 优先。

## 真实部署与 MCP

- 后端：`11.0.204-pod-lifecycle-20261009`
  - digest: `sha256:44e3d38a6870f6757a1ceb10479dba19b5faa92f933acef02fa2b655bc2525f4`
- MCP：`7.0.32-pod-lifecycle-20261009-r2`
  - digest: `sha256:b86ba21c58f540646a0f649c94911d680cd966f04619be41415ff890b762eb91`
- Deployment 滚动更新成功，前端代理 `/api/health` 返回 healthy，模型保持 `openai/gpt-6-luna`。
- 经真实 SSE MCP 验证：现有 OOM Pod、连续两页的不同 UID 和相同 resourceVersion、
  健康 Pod 的旧终止记录、无匹配项、不存在 Pod 的错误，全部通过。
- 验证过程未创建异常资源或执行修复写操作。

## 前端同路径对话验证

### 普通查询：6c6f04d8f407491e

问题：`xnet下有哪些pod？`
16.7 秒完成；自主使用原有列表工具一次，返回全部 4 个 Pod，原有查询行为保留。

### 已恢复但近期 OOM：b122d7b1acbc44fe

问题：`查询 aiops-case-08 下 Pod 当前状态和最近30分钟的终止、重启情况。`
27.5 秒完成，Agent 自主调用 `query_pod_lifecycle` 一次。
03:27:29 UTC 工具观测：workload 当前 Running、Ready=true，累计重启 11 次；
last_state=OOMKilled，exitCode=137，finishedAt=03:22:14，当前启动时间03:27:14。
最终答案明确报告最近 OOM 并已恢复，不将累计 11 次解释为窗口内 11 次。
正常 traffic-driver 的缺失终止历史没有被当成完整历史证明。

该运行工具 raw.txt 与 summary.txt SHA256 相同：
`bc1e54fb6ec9e5bfb0bd186491b1d380a89c63c03b7a11e286510756b7ddc857`。

## 验证发现与边界

### 全群诊断：77dcaab555d84e6c

问题：`我的集群有什么问题？`，未指定工具，也没有提示查 OOM。
Agent 首次取证即自主调用生命周期工具（page_size=100），覆盖 67 个 Pod；
此时目标 Pod 是 Running/Ready，仍通过 last_state 的 OOMKilled 识别出异常，
随后读取 OOM Runbook，再查询指标、日志、拓扑、链路及 describe。
整轮 282.5 秒，最终状态 **partial**：OOM 问题被识别，但不能算完整全群验收通过。

遗留问题：

- 第一次使用 `pod-oomkilled` 未找到，随后改成 `pod-oomkilled.md` 成功，额外一次调用。
- 工具首个结果实际为 `returned_count=67, coverage=present, next_continue_token=null`。
  后端记录 raw=88538、summary=88538，两者 SHA256 均为
  `a17f1791eb6fd9f7c81e697362605282095966d1556c79156c00c9b83a35c31c`，无单工具摘要截断。
  Agent 却在后续称结果中途截断，自行构造 offset/page 形式的 token。Kubernetes 正确拒绝该 token；
  最终报告沿用“分页失败导致覆盖不完整”的错误解释。这不能算修好所有覆盖判断问题。
- 最终确认 OOM 和资源限制，未将现有指标当作精确 OOM 峰值，未声称已查明完整故障机制。
- 本轮未出现上下文压缩或 execution_incomplete 事件。未执行修复命令。

本轮解决的是生命周期取证字段遗漏，不是模型任意工具参数和证据覆盖解释的全面正确性。
后续应单独评估分页契约理解、手册名称匹配及覆盖解释传播；不要以故障特判或强制流程补丁代替。

- 初版真实验证发现 kubectl get --raw 在容器内未自动装载 ServiceAccount，错误连接localhost:8080。
  已在 r2 修复并补单测，真实 MCP 重测通过。不能用初版运行 f21526c7584941af 作为成功验收：
  该运行两次生命周期读取失败，最终 partial，定位阶段还达到步骤限制。
- 发布后首次 MCP 连接遇到进程尚未监听端口，稍后真实握手和工具调用通过。
  当前 Deployment Ready 不完全等于每个 MCP 子服务已就绪，这是既有部署探针边界，本轮未扩展修改。
- 单测和当前真实对话不能保证模型未来永不漏诊；当前快照不提供完整窗口历史。
- 全局上下文压缩、Runbook 路由/名称解析、修复、前端展示和其他资源契约不在本轮修改范围。
