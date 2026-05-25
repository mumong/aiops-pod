# 部署与运维指南

本文只保留当前正式部署方式，不再展开历史模式。

## 相关架构文档

- [架构说明](/root/huhu/agent/combine-aiops-mcp/robusta/docs/ARCHITECTURE.md)
- [工作流上下文流转说明](/root/huhu/agent/combine-aiops-mcp/robusta/docs/工作流上下文流转说明.md)
- [工作流结构化运行时演进说明（2026-05-09）](/root/huhu/agent/combine-aiops-mcp/robusta/docs/workflow-structured-runtime-evolution-2026-05-09.md)
- [修复执行与人工审批使用说明](/root/huhu/agent/combine-aiops-mcp/robusta/docs/remediation-usage.md)

## 1. 部署前准备

### 必要文件

- [deploy/secrets/core.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/secrets/core.yaml)
- [deploy/configmap/config.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/configmap/config.yaml)
- [deploy/configmap/runbooks.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/configmap/runbooks.yaml)
- [deploy/k8s-simple.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/k8s-simple.yaml)
- [deploy/rbac.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/rbac.yaml)

### 必改项

#### Secret

编辑 [deploy/secrets/core.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/secrets/core.yaml)：

- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_API_BASE`
- `AUTO_REMEDIATE`
- `LOG_LEVEL`

#### ConfigMap

编辑 [deploy/configmap/config.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/configmap/config.yaml)：

- `i18n`
- `mcp_servers`
- `workflow`
- `metrics`
- `federation`

## 2. 单集群部署

### 构建与推送

```bash
make build
make push
```

### 部署

```bash
make deploy
```

该命令会：

1. 同步镜像版本到 [deploy/k8s-simple.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/k8s-simple.yaml)
2. 创建 `aiops` namespace
3. 递归应用 `deploy/`
4. 等待 `aiops-copilot` rollout 完成

### 验证

```bash
kubectl get pods -n aiops
kubectl get svc -n aiops
curl http://<node-ip>:30800/health
```

## 3. 联邦部署

### 主集群

```bash
make deploy-master
```

该命令会自动把 `federation.enabled` 改为 `true`，然后执行 `make deploy`。

主集群配置重点：

```yaml
federation:
  enabled: true
  sub_agents:
    - name: "main"
      url: "http://localhost:8000"
      enabled: true
    - name: "cluster-24"
      url: "http://10.2.0.24:30800"
      enabled: true
```

说明：

- 主集群自身应使用 `http://localhost:8000`
- 其他子集群使用可被主集群访问的地址

### 子集群

```bash
make deploy-slave
```

该命令会自动把 `federation.enabled` 改为 `false`，然后执行 `make deploy`。

## 4. 升级

### 升级镜像

```bash
echo "8.0.0" > VERSION
make build
make push
make deploy
```

### 仅修改配置

```bash
kubectl apply -f deploy/configmap/ --recursive
kubectl apply -f deploy/secrets/ --recursive
make restart
```

### 仅修改 Runbook

```bash
kubectl apply -f deploy/configmap/runbooks.yaml
make restart
```

## 5. 卸载

### 保留 namespace 的卸载

```bash
make delete
```

该命令会删除：

- `deploy/k8s-simple.yaml`
- `deploy/rbac.yaml`
- `deploy/secrets/*`
- `deploy/configmap/*`

不会删除：

- `aiops` namespace

### 完全清理

```bash
make delete
kubectl delete namespace aiops --ignore-not-found
```

## 6. 日常运维

### 查看日志

```bash
make logs
```

### 重启

```bash
make restart
```

### 查看服务

```bash
kubectl get deployment,svc,cm,secret -n aiops
```

### 查看已保存报告

```bash
curl http://<node-ip>:30800/reports
```

## 7. 常见访问方式

### 诊断

```bash
curl --no-buffer -G "http://<node-ip>:30800/ask" \
  --data-urlencode "q=我的集群有什么问题？"
```

### 查询

```bash
curl --no-buffer -G "http://<node-ip>:30800/query" \
  --data-urlencode "q=集群 CPU 和内存使用率是多少"
```

### 联邦诊断

```bash
curl --no-buffer -G "http://<node-ip>:30800/federation/ask/v2" \
  --data-urlencode "q=main 和 cluster-24 现在分别有什么问题？"
```

### 联邦查询

```bash
curl --no-buffer -G "http://<node-ip>:30800/federation/query/v2" \
  --data-urlencode "q=对比 main 和 cluster-24 的 CPU 使用率"
```

## 8. 配置建议

### `workflow.rca_mode`

- `lite`
  推荐默认值，避免 RCA 节点重复采集
- `full`
  只有在你确实需要 RCA 再调工具时才打开

### `workflow.max_steps`

- `layer`
  控制定位阶段探索深度
- `evidence`
  对总耗时影响最大
- `rca`
  仅 `rca_mode=full` 时生效

### `metrics.enabled`

- `false`
  输出更干净
- `true`
  额外展示质量指标

### `AUTO_REMEDIATE`

- `false`
  仅诊断，不执行修复
- `true`
  允许模型执行修复动作，风险更高
