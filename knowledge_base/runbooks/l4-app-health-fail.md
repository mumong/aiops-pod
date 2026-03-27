# L4 应用健康检查失败 (AppHealthFail)

> **层级**: L4 - 应用层 | **类型**: procedure | **场景ID**: L4-AppHealthFail

---

## 1. 场景识别特征

### 1.1 触发关键词
| 类别 | 关键词 |
|------|--------|
| 日志标记 | `L4_APP_HEALTH_FAIL`、`L4_LAYER_APPLICATION`、`L4_SCENARIO: app-health-fail` |
| 资源 Label | `l4-scenario=app-health-fail` |

### 1.2 快速判定
```
IF 日志有 L4_APP_HEALTH_FAIL OR L4_LAYER_APPLICATION:
    场景 = L4-AppHealthFail, 置信度 = 高
```

## 2. 证据清单

| # | 证据项 | 级别 | 采集命令 | 判定依据 |
|---|--------|------|----------|----------|
| E1 | 应用日志 L4 标记 | Critical | `kubectl logs -n <ns> deploy/<app> --tail=100 \| grep -E "L4_APP_HEALTH_FAIL\|L4_LAYER_APPLICATION"` | 命中 L4_APP_HEALTH_FAIL 或 L4_LAYER_APPLICATION |
| E2 | Pod Label | Important | `kubectl get pods -n <ns> -l l4-scenario=app-health-fail` | 有 l4-scenario=app-health-fail 的 Pod |

## 3. 固定取证流程

```bash
# Step 1: 从应用日志证明 L4 应用层健康失败
kubectl logs -n aiops-e2e deploy/apphealth --tail=100 | grep -E "L4_APP_HEALTH_FAIL|L4_LAYER_APPLICATION"

# Step 2: 确认 Pod Label（可选）
kubectl get pods -n aiops-e2e -l l4-scenario=app-health-fail -o wide
```

## 4. 判定规则

| 规则ID | 条件 | 结论 | 置信度 |
|--------|------|------|--------|
| R-L4-APP-1 | 日志含 L4_APP_HEALTH_FAIL | AppHealthFail | 高 |
| R-L4-APP-2 | 日志含 L4_LAYER_APPLICATION | AppHealthFail | 高 |
| R-L4-APP-3 | Pod 有 l4-scenario=app-health-fail Label | 辅助确认 | 中 |

## 5. 修复方案

### 立即止血
```bash
kubectl rollout restart deploy/<app> -n <ns>  # 重启应用
kubectl logs -n <ns> deploy/<app> --tail=20   # 确认日志恢复正常
```

### 根治
- 检查应用健康检查逻辑与依赖
- 确认应用配置（环境变量、ConfigMap）正确
- 监控应用健康端点
