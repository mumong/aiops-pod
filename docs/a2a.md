# A2A：服务与真实 Agent-to-Agent 测试

本项目通过独立 Adapter 将现有 Kubernetes AIOps 能力封装为标准
Agent2Agent Server。Adapter 使用官方 `a2a-sdk==0.3.25`，实现 A2A Protocol
`v0.3.0` 的 JSON-RPC 和 SSE 流式传输。

## 1. 架构与端点

```text
A2A Client
  -> A2A Adapter :8001
  -> AIOps Copilot :8000 (/ask 或 /query)
  -> LangGraph / MCP / Kubernetes / Observability
```

| 地址 | 用途 |
| --- | --- |
| `GET /.well-known/agent-card.json` | 标准 Agent Card |
| `GET /.well-known/agent.json` | SDK 提供的兼容 Agent Card 地址 |
| `POST /` | A2A JSON-RPC：message、task、cancel、resubscribe |
| `GET /health` | Adapter 存活状态 |
| `GET /ready` | Adapter 与主 Agent 的就绪状态 |

支持的主要 JSON-RPC 方法：

- `message/send`
- `message/stream`
- `tasks/get`
- `tasks/cancel`
- `tasks/resubscribe`

不支持 Push Notification。写操作只有修复技能一条路径，且每个动作都要人工审批（见 1.1）。

### 1.1 修复技能（kubernetes-repair）

调用方**直接用文字提出修复**即可（如"帮我修复 aiops-case-10 的异常 Pod"），不需要 metadata：适配器每次调用都带 `repair=on_request`，由后端按意图判断；是修复请求时，诊断（或复用同一 contextId 的诊断）并按异常组生成修复方案。`metadata.aiops_mode=repair` 仍可用，含义是"诊断完后总是生成修复方案"。有待审批动作时任务进入 `input-required`，调用方在同一任务回复 `{approval_id, approved, reviewer}`（DataPart）或文本"批准/拒绝 <approval_id>"（每个动作一行，同一决定两种形式都发时只提交一次），适配器调用后端审批接口后继续，结束时返回各组恢复结果。需要配置 `A2A_BACKEND_API_TOKEN`（后端 `AIOPS_API_TOKENS` 中的 `a2a` 身份）。完整 curl 示例见 [HTTP API 第 7 节](api.md#7-a2a-调用含修复与人工审批)。

### 1.2 单集群与多集群：调用方式相同

接给其他 Agent 时不需要区分部署形态：Agent Card、端点、三个技能都一样。区别只有一点：

- **单集群**：直接回答。
- **多集群**：问题里写明集群（如"edge-88 有哪些异常 Pod"、"所有边缘集群"）就直接回答；没写明时，任务进入 `input-required`，状态消息里是反问（例如"要查看哪个集群：edge-88、edge-89，还是所有边缘集群？"）。调用方在**同一个任务**里回复，适配器会把回复和原问题一起交给后端，接着执行：

```bash
# 回复反问：taskId、contextId 取自上一次返回的 result.id 和 result.contextId
curl -sS http://<节点IP>:30801/ -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": "2", "method": "message/send",
  "params": {"message": {"kind": "message", "role": "user", "messageId": "m-2",
    "taskId": "<上次的 result.id>", "contextId": "<上次的 result.contextId>",
    "parts": [{"kind": "text", "text": "edge-88"}]}, "configuration": {"blocking": true}}}'
```

调用方只需要正确处理 `input-required` 这个标准状态：把状态消息展示给用户或让自己的 LLM 作答，再在同一任务里回复。修复审批走同一种机制，多集群下每个待审批动作都会标明所在集群（文本里的"集群 edge-88"，DataPart 里的 `cluster` 字段）。

## 1.3 最快的测试方式：终端对话

```bash
python3 scripts/a2a_chat.py http://<节点IP>:30801     # 只依赖 python3
```

脚本用标准 `message/stream` 调用，和外部 Agent 走同一条路径：实时显示进度；`input-required` 时列出待审批动作（`y` 全部批准 / `n` 全部拒绝）或显示反问（直接回答）；同一窗口内的问题共用一个 contextId（`/new` 重新开始）。`-q "问题"` 只问一次。

## 2. 本地启动

A2A Adapter 必须使用独立虚拟环境。不要把它安装到 HolmesGPT 的 `.venv`：
HolmesGPT 0.21.0 要求 `httpx<0.28`，而 a2a-sdk 0.3.25 要求
`httpx>=0.28.1`。

先启动主 Agent：

```bash
.venv/bin/python -m app
```

再启动 Adapter：

```bash
python3 -m venv .venv-a2a
.venv-a2a/bin/pip install -r requirements/a2a.txt

export A2A_BACKEND_URL=http://127.0.0.1:8000
export A2A_PUBLIC_URL=http://127.0.0.1:8001
.venv-a2a/bin/python -m a2a_adapter
```

可选鉴权：

```bash
export A2A_API_TOKEN='replace-with-a-random-token'
```

启用后，所有 `POST /` 请求都需要：

```text
Authorization: Bearer replace-with-a-random-token
```

## 3. curl 调用

### 3.1 发现 Agent

```bash
curl http://127.0.0.1:8001/.well-known/agent-card.json | jq
```

### 3.2 阻塞式诊断

```bash
curl -sS http://127.0.0.1:8001/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer replace-with-a-random-token' \
  -d '{
    "jsonrpc": "2.0",
    "id": "request-1",
    "method": "message/send",
    "params": {
      "message": {
        "kind": "message",
        "role": "user",
        "messageId": "message-1",
        "parts": [
          {"kind": "text", "text": "请诊断 production 命名空间中的异常 Pod"}
        ]
      },
      "configuration": {"blocking": true}
    }
  }' | jq
```

未设置 `A2A_API_TOKEN` 时删除 Authorization Header。

### 3.3 SSE 流式诊断

```bash
curl -N http://127.0.0.1:8001/ \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": "request-stream-1",
    "method": "message/stream",
    "params": {
      "message": {
        "kind": "message",
        "role": "user",
        "messageId": "message-stream-1",
        "parts": [
          {"kind": "text", "text": "为什么 Pod api-0 一直 CrashLoopBackOff？"}
        ]
      }
    }
  }'
```

响应包含标准 `TaskStatusUpdateEvent` 和 `TaskArtifactUpdateEvent`。最终 Markdown
报告位于 Artifact 的 `parts[].text`。

### 3.4 快速查询模式

默认走 `/query` 两节点自主运维分析，支持查询和故障分析。需要旧的 `/ask` 完整分组诊断时，在请求 metadata 中指定 `aiops_mode=diagnosis`（或 `ask`）。显式 `aiops_mode=query` 仍受支持：

```json
{
  "jsonrpc": "2.0",
  "id": "query-1",
  "method": "message/send",
  "params": {
    "message": {
      "kind": "message",
      "role": "user",
      "messageId": "query-message-1",
      "parts": [{"kind": "text", "text": "查询各 Node CPU 使用率"}]
    },
    "metadata": {"aiops_mode": "query"},
    "configuration": {"blocking": true}
  }
}
```

### 3.5 查询和取消 Task

把 `message/send` 返回的 Task `id` 代入：

```bash
curl -sS http://127.0.0.1:8001/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":"get-1","method":"tasks/get","params":{"id":"TASK_ID"}}'

curl -sS http://127.0.0.1:8001/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":"cancel-1","method":"tasks/cancel","params":{"id":"TASK_ID"}}'
```

## 4. 使用官方 Python Client

调用方安装相同 SDK：

```bash
pip install 'a2a-sdk==0.3.25' httpx
```

```python
import asyncio

import httpx
from a2a.client import ClientConfig, ClientFactory, create_text_message_object


async def main():
    async with httpx.AsyncClient(
        headers={"Authorization": "Bearer replace-with-a-random-token"},
        timeout=None,
    ) as http_client:
        client = await ClientFactory.connect(
            "http://127.0.0.1:8001",
            client_config=ClientConfig(
                streaming=True,
                httpx_client=http_client,
                accepted_output_modes=["text/markdown"],
            ),
        )
        message = create_text_message_object(content="请检查当前集群异常 Pod")
        async for task, update in client.send_message(message):
            print(task.status.state, update)


asyncio.run(main())
```

如果服务未启用 Token，删除 `headers` 参数即可。

仓库也提供了同样基于官方 SDK 的命令行客户端：

```bash
.venv-a2a/bin/python scripts/a2a_client.py \
  --url http://127.0.0.1:8001 \
  --mode diagnosis \
  '请诊断当前异常 Pod'

.venv-a2a/bin/python scripts/a2a_client.py \
  --url http://127.0.0.1:8001 \
  --mode query \
  '查询各 Node CPU 使用率'
```

## 5. Docker 与 Kubernetes

按项目标准发布流程构建并推送主 Agent 和 A2A Adapter：

```bash
make build
make push
make deploy
```

只构建 Adapter：

```bash
make build-a2a
make push-a2a
```

Kubernetes Service 暴露：

- 原 API：`30800 -> 8000`
- A2A：`30801 -> 8001`

集群外调用前，通过 `make deploy A2A_PUBLIC_HOST=<节点IP> A2A_PUBLIC_URL=http://<节点IP>:30801`
传入调用方真正能访问的地址。Makefile 会写回清单中的 `A2A_PUBLIC_URL`，只手改清单可能被覆盖。
Agent Card 中的 URL 必须与实际可访问协议地址一致。

如需鉴权，通过部署环境的 `aiops-secret` 添加 `A2A_API_TOKEN`，不要将真实 Token
提交到仓库。

## 6. 测试

测试也使用独立环境：

```bash
python3 -m venv .venv-a2a
.venv-a2a/bin/pip install -r requirements/a2a-dev.txt
.venv-a2a/bin/python -m pytest -q tests/a2a
# 或完成上述环境安装后执行 make test-a2a
```

覆盖 Agent Card、阻塞调用、SSE 流式调用、快速查询路由、进程内 Task 存取、Task
取消、鉴权、后端 SSE 解析与错误处理。

当前 Kubernetes 清单固定 `replicas: 1`，因此首版使用 SDK 的
`InMemoryTaskStore`。Pod 重启后历史 Task 会丢失；如后续扩展多副本，需要先切换为
SDK 的数据库 TaskStore，不能仅靠增加 Deployment replicas。

