## E2E 故障注入与验收

为 L0-L4 五个典型故障场景提供可复现的故障环境与验收脚本。

### 场景矩阵

| 层级 | 场景 | Manifest | Runbook | 注入方式 |
|------|------|----------|---------|----------|
| L0 | EmptyDir 超限驱逐 | `l0-logfill-enospc.yaml` | `l0-volume-limit.md` | emptyDir sizeLimit 30Mi 写满 |
| L1 | Node Taint 不可调度 | `l1-taint-node.yaml` | `l1-taint-node.md` | nodeSelector 指定节点 |
| L2 | OOMKilled | `l2-oomkilled.yaml` | `l2-oomkilled.md` | 小内存 limit + 内存分配 |
| L3 | ImagePullBackOff | `l3-imagepull-fail-victim.yaml` | `l3-imagepull-failed.md` | 拉取不可达镜像 |
| L4 | 应用健康检查失败 | `l4-app-health-fail.yaml` | `l4-app-health-fail.md` | 日志输出 L4 标记 |

### 使用方式

```bash
cd test/e2e

# 1. 部署所有场景
./run_all.sh

# 2. 手动取证（确认场景注入成功）
./validate.sh

# 3. 运行验收测试（需要 AIOps 服务已启动）
AIOPS_ENDPOINT=http://10.2.0.48:30800 ./test_scenarios.sh

# 4. 单独测试某个场景
./test_scenarios.sh l0   # L0
./test_scenarios.sh l2   # L2
```

### 前置依赖

- `kubectl`（已配置集群访问）
- `curl`
- AIOps 服务已启动（`/health` 返回 healthy）
