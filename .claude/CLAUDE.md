这是我的一个核心项目，里面你可以参考readme.md和docs快速了解项目。
你需要按照我的指令和需求进行开发，你的核心原则是解决我的问题，写出高内聚低耦合可扩展的代码。

我在项目目录下维护了一个新的CLAUDE.md文档，那里面有我们讨论的技术细节，我希望你可以理解避免多轮对话后你忘记要去做什么，以及修改了我原有正常的代码。

## 部署与验证流程（铁律）

1. 修改 `VERSION` 文件（中间版本递增，如 4.4.5 → 4.5.5 → 4.6.5）
2. `make delete build push deploy-master` 完整重建部署
3. 等待 Pod Ready：`kubectl get pods -n aiops -l app=aiops-copilot`
4. 验证代码已更新：`kubectl exec deployment/aiops-copilot -n aiops -- grep "关键代码" /app/path/to/file.py`
5. 功能测试：`curl -G "http://10.2.0.48:30800/ask" --data-urlencode "q=测试问题"`
6. 查看日志：`kubectl logs deployment/aiops-copilot -n aiops --tail=100`
7. 查看 MCP 日志：`kubectl logs deployment/mcp-server-manager -n mcp --tail=100`

## 铁律

- **不要任何回退规则**——错了就继续优化，不用不准确的结果凑数
- **每次改动必须自测**——部署后发请求验证，看日志确认工具调用正常
- **版本号必须变**——否则 Docker 缓存导致旧代码