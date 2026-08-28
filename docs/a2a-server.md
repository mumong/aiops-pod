# Agent2Agent（A2A）Server 使用指南

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

首版不支持 Push Notification，也不通过 A2A 开放自动修复写操作。

## 2. 本地启动

A2A Adapter 必须使用独立虚拟环境。不要把它安装到 HolmesGPT 的 `.venv`：
HolmesGPT 0.21.0 要求 `httpx<0.28`，而 a2a-sdk 0.3.25 要求
`httpx>=0.28.1`。

先启动主 Agent：

```bash
.venv/bin/python run.py
```

再启动 Adapter：

```bash
python3 -m venv .venv-a2a
.venv-a2a/bin/pip install -r requirements.a2a.txt

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

默认走完整 `/ask` 诊断。只查询指标或资源状态时，在请求 metadata 中指定
`aiops_mode=query`，Adapter 会调用现有 `/query` 快路径：

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
.venv-a2a/bin/python tools/a2a_client.py \
  --url http://127.0.0.1:8001 \
  --mode diagnosis \
  '请诊断当前异常 Pod'

.venv-a2a/bin/python tools/a2a_client.py \
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

集群外调用前，将 `deploy/k8s-simple.yaml` 中的 `A2A_PUBLIC_URL` 改为调用方
真正能够访问的 URL，例如 `http://NODE_IP:30801`。Agent Card 中的 URL 必须与
实际可访问协议地址一致。

如需鉴权，通过部署环境的 `aiops-secret` 添加 `A2A_API_TOKEN`，不要将真实 Token
提交到仓库。

## 6. 测试

测试也使用独立环境：

```bash
python3 -m venv .venv-a2a
.venv-a2a/bin/pip install -r requirements.a2a-dev.txt
.venv-a2a/bin/python -m pytest -q tests/a2a
# 或完成上述环境安装后执行 make test-a2a
```

覆盖 Agent Card、阻塞调用、SSE 流式调用、快速查询路由、Task 持久化、Task
取消、鉴权、后端 SSE 解析与错误处理。

当前 Kubernetes 清单固定 `replicas: 1`，因此首版使用 SDK 的
`InMemoryTaskStore`。Pod 重启后历史 Task 会丢失；如后续扩展多副本，需要先切换为
SDK 的数据库 TaskStore，不能仅靠增加 Deployment replicas。
