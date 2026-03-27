# L2 OOMKilled（Exit Code 137）

> **层级**: L2 - 工作负载层 | **类型**: procedure | **场景ID**: L2-OOMKilled

---

## 1. 场景识别特征

### 1.1 触发关键词
| 类别 | 关键词 |
|------|--------|
| 中文 | 内存超限、OOM、被杀、重启、ExitCode=137 |
| 英文 | OOMKilled, out of memory, exit code 137 |

### 1.2 快速判定
```
IF (terminated.reason == OOMKilled) OR (exitCode == 137):
    场景 = L2-OOMKilled, 置信度 = 高
```

## 2. 证据清单

| # | 证据项 | 级别 | 采集命令 | 判定依据 |
|---|--------|------|----------|----------|
| E1 | Pod 状态 | Critical | `kubectl get pod -o json` | terminated.reason |
| E2 | Exit Code | Critical | `kubectl describe pod` | exitCode=137 |
| E3 | 崩溃前日志 | Important | `kubectl logs --previous` | 内存错误 |
| E4 | 资源限制 | Important | `kubectl get pod -o yaml` | limits.memory |

## 3. 固定取证流程

```bash
# Step 1: 确认 Pod 状态
kubectl get pod <pod> -n <ns> -o json | jq '.status.containerStatuses'

# Step 2: 获取事件和描述
kubectl describe pod <pod> -n <ns>

# Step 3: 获取崩溃前日志
kubectl logs <pod> -n <ns> --previous --tail=200

# Step 4: 检查资源配置
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[*].resources}'
```

## 4. 判定规则

| 规则ID | 条件 | 结论 | 置信度 |
|--------|------|------|--------|
| R-L2-OOM-1 | terminated.reason=OOMKilled 或 exitCode=137 | OOMKilled | 高 |
| R-L2-OOM-2 | 日志包含 "Cannot allocate memory" | OOMKilled | 高 |
| R-L2-OOM-3 | exitCode=1/127 且无 OOM 标记 | 非 OOM | 中 |

## 5. 修复方案

### 立即止血（需审批）
```bash
kubectl patch deploy <name> -n <ns> -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"<c>","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
```

### 根治
- 分析日志确定内存消耗来源
- 若为泄漏：修复代码
- 建立 memory 使用率告警
