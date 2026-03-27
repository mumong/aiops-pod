# 镜像拉取失败 (ImagePullBackOff) 诊断手册

> **层级**: L3 - 网络层 | **类型**: procedure | **场景ID**: L3-ImagePullBackOff

## 故障特征

**状态关键词**: `ImagePullBackOff`、`ErrImagePull`、`ImageInspectError`

**典型事件**:
- `Failed to pull image`
- `connection refused` / `timeout`
- `manifest unknown`

## 诊断命令

```bash
# 查看 Pod 事件（获取具体错误信息）
kubectl describe pod <pod-name> -n <namespace> | grep -A 10 Events

# 查看 Pod 使用的镜像
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'

# 查看 imagePullSecrets 配置
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'
```

## 常见场景与解决方案

### 场景 1: 镜像仓库网络不可达

**事件**: `connection canceled`、`timeout`

**根因**: 节点无法访问镜像仓库（可能被 iptables 阻断）

**诊断**:
```bash
# 检查 iptables 规则
iptables -L -n | grep -i reject

# 在节点上测试网络连通性
curl -v https://registry-1.docker.io/v2/

# 检查 DNS 解析
nslookup registry-1.docker.io
```

**修复**:
```bash
# 移除 iptables REJECT 规则（如被阻断）
iptables -D OUTPUT -d registry-1.docker.io -j REJECT
iptables -D INPUT -s registry-1.docker.io -j REJECT

# 删除 Pod 触发重试
kubectl delete pod <pod-name> -n <namespace>
```

### 场景 2: 镜像地址错误

**事件**: `manifest unknown`、`not found`

**根因**: 镜像名称或标签（tag）不存在

**修复**:
- 确认镜像名称和标签拼写正确
- 确认镜像已推送到仓库

### 场景 3: 认证失败（私有仓库）

**事件**: `unauthorized: authentication required`、`no basic auth credentials`

**修复**:
```bash
kubectl create secret docker-registry <secret-name> \
  --docker-server=<registry-url> \
  --docker-username=<username> \
  --docker-password=<password> \
  -n <namespace>
```

## 证据链

| 步骤 | 命令/工具 | 原始数据 | 分析结论 |
|-------|------------|----------|-----------|
| 1 | kubectl get pod | STATUS=ImagePullBackOff | Pod 异常状态 |
| 2 | kubectl describe pod | Events: Failed to pull image, connection canceled | 镜像拉取失败 |
| 3 | iptables -L | registry-1.docker.io REJECT 规则存在 | 网络层被阻断 |
| 4 | curl -v registry | timeout/connection refused | 镜像仓库不可达 |
