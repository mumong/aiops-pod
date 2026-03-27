# L4 依赖服务固定返回 503

> **层级**: L4 - 应用层 | **类型**: procedure | **场景ID**: L4-Dependency503

---

## 1. 场景识别特征

### 1.1 触发关键词
| 类别 | 关键词 |
|------|--------|
| 中文 | 依赖异常、上游 503、5xx 激增、Service Unavailable |
| 英文 | upstream 503, service unavailable, 5xx |
| 状态 | HTTP 503 (Service Unavailable) |
| 特定标记 | 日志中出现 `L4_DEPENDENCY_FAULT`, `L4_UPSTREAM_HTTP_CODE: 503`，或资源带有 `l4-scenario=dependency-503` Label |

### 1.2 快速判定
```
IF (curl 依赖返回 503) AND (应用日志有 upstream 503 或 L4_DEPENDENCY_FAULT/L4_UPSTREAM_HTTP_CODE:503 等标记):
    场景 = L4-Dependency503, 置信度 = 高
```

## 2. 证据清单

| # | 证据项 | 级别 | 采集命令 | 判定依据 |
|---|--------|------|----------|----------|
| E1 | 应用 5xx 统计 | Critical | `kubectl logs | grep -c 5xx` | 有 5xx |
| E2 | 应用日志上游错误 | Critical | `kubectl logs | grep -E "upstream 503|L4_DEPENDENCY_FAULT|L4_UPSTREAM_HTTP_CODE"` | upstream 503 或 L4 依赖故障标记 |
| E3 | 依赖服务返回码 | Critical | `curl -w "%{http_code}"` | 503 |
| E4 | 依赖 Endpoints | Important | `kubectl get endpoints` | 有后端 |

## 3. 固定取证流程

```bash
# Step 1: 量化应用 5xx
kubectl logs -n <ns> deploy/<app> --tail=500 | grep -c " 5[0-9][0-9]"

# Step 2: 从应用日志证明 upstream=503
kubectl logs -n <ns> deploy/<app> --tail=500 | grep -i "upstream\|503" | tail -30

# Step 3: 直接验证依赖返回码
kubectl run curl-test --rm -it --image=curlimages/curl -- \
  curl -s -o /dev/null -w "http_code=%{http_code}\n" http://<dep-svc>:<port>/

# Step 4: 检查依赖 Endpoints
kubectl get endpoints <dep-svc> -n <ns> -o wide
```

## 4. 判定规则

| 规则ID | 条件 | 结论 | 置信度 |
|--------|------|------|--------|
| R-L4-DEP-1 | 依赖 curl=503 + 应用日志有 upstream 503 | Dependency503 | 高 |
| R-L4-DEP-2 | 依赖 curl=200 但应用仍 5xx | 非依赖原因 | 中 |
| R-L4-DEP-3 | Endpoints 为空 | L3 问题 | 高 |

## 5. 修复方案

### 立即止血
```bash
kubectl rollout undo deploy/<dep> -n <ns>  # 回滚
kubectl rollout restart deploy/<dep> -n <ns>  # 或重启
curl http://<dep-svc>:<port>/health  # 确认恢复
```

### 根治
- 依赖侧：健康检查 + 灰度发布
- 应用侧：熔断 + 降级 + 重试策略
