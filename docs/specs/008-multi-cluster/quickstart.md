# Quickstart: 部署与验收

完整用例和操作规范见 [docs/multi-cluster-acceptance.md](../../docs/multi-cluster-acceptance.md)（单一来源）。

## 访问方式

- 部署与测试：SSH 到各主机执行（凭据由 Boss 提供，不写入任何文件），或使用本机 `~/.kube/aiops-mc/{center,edge-88,edge-89}` kubeconfig（不提交）。
- 这些访问方式只用于运维和测试，运行时只经过 xnet 隧道（spec FR-016）。

## 部署顺序

1. 本机构建并推送镜像到 harbor；测试环境的 Harbor 推不了镜像，部署时加 `MC_LOAD_HOSTS=<节点>` 经 SSH 导入（见设计 §3.2）。
2. 中心：Agent 仓库 `make mc-discover` 更新集群配置、`make mc-init`，然后在 mcpstander、robusta、frountind 依次执行 `make deploy-mc`（前端 NodePort 30082）。完整步骤见 README「多集群部署」。
3. 每个边缘：`make edge-deploy`，在边缘本地执行（SSH 管道或边缘 kubeconfig）。
4. `tests/acceptance/multicluster/env_check.py` → 当前阶段的验收脚本。

## 每个阶段的出口

- 当前阶段的用例全部通过，结果记录到验收文档 §7。
- SC-006 运行时依赖检查、SC-007 快照对比通过。
- 三个仓库打 `mc-pN` 标签。
