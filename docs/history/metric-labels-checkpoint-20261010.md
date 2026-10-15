# 修改分页/排序前的回滚检查点

本检查点保存当前已部署的指标解读与展示版本，尚未加入有界预读、快照分页、关注项排序或模型视图 UTC 转换。

| 项目 | 分支/提交 | 镜像版本 |
|---|---|---|
| 后端 | 本文所在提交；`qwen-before-architecture` | `11.0.206-metric-labels-20261010` |
| 前端 | `main` / `c4b6b90` | `0.1.41` |
| MCP | `81787ae810dd15e3d430405dcac37bb4d0f6940e`，无新改动 | `7.0.34-records-20261009` |
| A2A | 未改动 | `11.0.168-security-20260924` |

提交推送目标为三个仓库现有内网 `origin`，不是 GitHub 镜像仓库。实际推送完成情况以本次交付消息及远端分支核对结果为准。

## 回滚服务

以下仅记录命令，本轮没有执行回滚。镜像已导入当前三个节点的 containerd；需要保留这些镜像，使用现有 `IfNotPresent` 拉取策略。

```sh
kubectl set image -n aiops deployment/aiops-copilot aiops-copilot=xnet.registry.io:8443/xnet-cloud/aiops-copilot:11.0.206-metric-labels-20261010
kubectl set image -n aiops deployment/aiops-copilot-frontend frontend=xnet.registry.io:8443/xnet-cloud/aiops-copilot-frontend:0.1.41
kubectl rollout status -n aiops deployment/aiops-copilot --timeout=300s
kubectl rollout status -n aiops deployment/aiops-copilot-frontend --timeout=300s
```

不要为回滚运行 `make delete`，也不要使用后端通用 `make deploy` 覆盖 Secret、配置和 A2A 镜像。后续如修改 MCP 协议，必须同步评估 MCP/后端/前端兼容性，不能只回滚其中一个组件。

## 验证与已知边界

详见 [本轮验证记录](metric-labels-release-20261010.md)：后端 1738 passed / 2 skipped，前端 98 passed，浏览器回放和真实只读查询已验证。深度诊断已发现总结时间换算错误，检查点不表示所有诊断结论均准确。

工作区未发布的 evidence-view/computation 实验文件及其对 observation/aicall 的改动没有纳入本提交，也没有部署。它们仍原样保留在本地。后续构建应从该检查点的干净 worktree 开始，不要将整个当前脏工作区打包。临时分页/时间验证原型位于 `/tmp/aiops-pagination-time-probe-20261010.hMsUrP/`，不属于生产提交。
