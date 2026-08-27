# 真实 Agent-to-Agent 测试服务

`a2a_test_agent` 是一个独立 Agent 服务，不是简单的 HTTP 转发脚本。它同时扮演：

- A2A Server：在 `:8002` 暴露 Agent Card、JSON-RPC、流式 Task 和 Artifact。
- A2A Client：使用官方 `a2a-sdk==0.3.25` 发现并调用运维 Agent `:8001`。

完整链路：

```text
官方 SDK 测试客户端
  -> A2A Test Delegator :8002
  -> Kubernetes AIOps A2A Agent :8001
  -> AIOps API :8000
  -> LangGraph / MCP / Kubernetes / Observability
```

两段 Agent 调用都使用 Agent2Agent Protocol v0.3.0 JSON-RPC/SSE。

## 1. 本机启动

先确保运维 A2A Agent 已经运行在 `http://127.0.0.1:8001`，然后使用独立 A2A
虚拟环境启动测试 Agent：

```bash
python3 -m venv .venv-a2a
.venv-a2a/bin/pip install -r requirements.a2a.txt

export TEST_AGENT_TARGET_URL=http://127.0.0.1:8001
export TEST_AGENT_PUBLIC_URL=http://127.0.0.1:8002
.venv-a2a/bin/python -m a2a_test_agent
```

如果运维 Agent 启用了 Bearer Token：

```bash
export TEST_AGENT_TARGET_TOKEN='operations-agent-token'
```

`TEST_AGENT_API_TOKEN` 是保护测试 Agent 自己的入站 Token，与下游 Token 独立：

```bash
export TEST_AGENT_API_TOKEN='test-agent-token'
```

## 2. Docker 启动

```bash
make build-a2a-test-agent

docker run --rm --name aiops-a2a-test-agent \
  -p 8002:8002 \
  -e TEST_AGENT_TARGET_URL=http://HOST_IP:30801 \
  -e TEST_AGENT_PUBLIC_URL=http://127.0.0.1:8002 \
  xnet.registry.io:8443/xnet-cloud/aiops-a2a-test-agent:$(cat VERSION)
```

容器中的 `127.0.0.1` 指向容器自身，因此下游地址不要填写宿主机的
`http://127.0.0.1:8001`。Linux 可使用可路由的宿主机 IP，或者将两个容器放入同一
Docker network 并使用运维 Adapter 的容器名。

## 2.1 按项目标准方式部署到 Kubernetes

测试 Agent 已纳入本仓库统一 `VERSION` 发布闭环。修改一次 `VERSION` 后执行：

```bash
make delete
make build
make push
make deploy
```

上述命令会使用同一个版本构建、推送并部署：

- `aiops-copilot`：主 Agent，Pod 端口 8000，NodePort 30800。
- `aiops-a2a-adapter`：主 Agent 同 Pod sidecar，端口 8001，NodePort 30801。
- `aiops-a2a-test-agent`：独立 Deployment，端口 8002，NodePort 30802。

`make deploy` 默认读取 Kubernetes 第一个 Node 的 InternalIP，写入两个 Agent Card 的
外部 URL。使用 Ingress、VIP 或其他 Node 时可以覆盖：

```bash
make deploy \
  A2A_PUBLIC_HOST=10.2.0.48 \
  A2A_PUBLIC_URL=https://aiops-a2a.example.com \
  A2A_TEST_AGENT_PUBLIC_URL=https://aiops-a2a-test.example.com
```

MCP Stander 和 Frontend 仍由各自仓库独立发布。测试 Agent 委派给运维 Agent 后，运维
Agent 仍按现有配置调用 `mcp-server-manager.mcp.svc.cluster.local`，Frontend 仍通过
`/api -> aiops-copilot:8000` 工作，A2A 接入不会替换这两条链路。

## 3. 检查双 Agent

发现测试 Agent：

```bash
curl -fsS http://127.0.0.1:8002/.well-known/agent-card.json | jq
curl -fsS http://127.0.0.1:8002/ready | jq
```

Kubernetes 部署后从集群外验证：

```bash
curl -fsS http://NODE_IP:30801/.well-known/agent-card.json | jq
curl -fsS http://NODE_IP:30802/.well-known/agent-card.json | jq
curl -fsS http://NODE_IP:30802/ready | jq
```

`/ready` 会通过官方 SDK 发现下游 Agent。正常结果中同时包含：

```json
{
  "status": "ready",
  "role": "a2a-delegating-agent",
  "target": {
    "status": "healthy",
    "agent_name": "Kubernetes AIOps Copilot",
    "protocol_version": "0.3.0"
  }
}
```

## 4. 进行真实 Agent-to-Agent 调用

调用地址必须是测试 Agent 的 `:8002`，不是运维 Agent 的 `:8001`：

```bash
.venv-a2a/bin/python tools/a2a_client.py \
  --url http://127.0.0.1:8002 \
  --mode diagnosis \
  '请诊断 production 命名空间中的异常 Pod，并给出证据'
```

快速查询模式的 metadata 会跨两段 A2A 调用透传：

```bash
.venv-a2a/bin/python tools/a2a_client.py \
  --url http://127.0.0.1:8002 \
  --mode query \
  '查询各 Node CPU 使用率'
```

最终 Artifact 包含下游运维 Agent 的 Markdown 报告，以及用于核验调用链的元数据：

```json
{
  "target_agent": "Kubernetes AIOps Copilot",
  "target_task_id": "下游任务 ID",
  "target_context_id": "下游上下文 ID"
}
```

日志和返回结果应证明：上游 Task 与下游 Task ID 不同，最终报告来自下游运维 Agent。

## 5. 自动化真实网络测试

```bash
.venv-a2a/bin/pip install -r requirements.a2a-dev.txt
.venv-a2a/bin/python -m pytest -q tests/a2a/test_agent_to_agent.py
```

其中 `test_real_http_two_hop_agent_to_agent_chain_with_official_sdk` 会启动两个真实
Uvicorn TCP 服务，并使用第三个官方 SDK Client 执行：

```text
Client --HTTP/SSE--> Test Agent --HTTP/SSE--> Operations Agent
```

这个测试不使用 `httpx.ASGITransport` 替代网络；运维 Agent 后面的业务输出使用可控
Backend，以便自动断言问题和 `aiops_mode` 确实到达第二个 Agent。
