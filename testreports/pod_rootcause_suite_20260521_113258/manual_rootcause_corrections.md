# Pod RootCause 人工校正记录

- 校正时间: 2026-05-26
- 校正范围: `INCLUDED_CLEAN` 范围内的 pending 组低分 case
- 校正原则: 以最终诊断报告的根因结论为准；如果最终报告明确定位到目标异常的真实根因，则判为正确。自动评分中的否定上下文冲突词和语义等价表达漏判不作为失败依据。

## 汇总

| Case | 自动根因率 | 人工校正后 | 修正说明 |
|------|------------|------------|----------|
| `06-pending-nodeselector-mismatch` | 78.0% | 100.0% | `pvc`/`Insufficient cpu` 多为“已排除”上下文，被自动评分误判为冲突。 |
| `07-pending-insufficient-cpu` | 34.0% | 78.0% | `nodeSelector`/`PVC` 排除项误伤；`100k`、`100 核`、`100,000m` 等语义等价表达被漏判。 |
| `08-pending-insufficient-memory` | 68.0% | 80.0% | `nodeSelector`/`PVC` 排除项误伤；`100TB`、`100,000Gi`、`requests.memory` 等表达被漏判；同时扣除 2 个自动 false positive。 |
| `09-pending-missing-pvc` | 84.0% | 100.0% | `nodeSelector`、`configmap`、`secret` 多为“已排除/无此依赖”上下文，被自动评分误判为冲突。 |

## 总体影响

| 范围 | 校正前 | 校正后 |
|------|--------|--------|
| pending group 根因准确率 | 77.0% | 89.5% |
| INCLUDED_CLEAN 总根因准确率 | 89.1% | 94.7% |

## 保留失败

### `07-pending-insufficient-cpu`

保留失败: `#3 #8 #15 #22 #34 #35 #36 #37 #40 #43 #45`

主要原因: 误判为镜像问题、模拟场景、真实集群资源耗尽、Webhook/调度器注入，或 LLM 连接失败。

### `08-pending-insufficient-memory`

保留失败: `#5 #13 #16 #19 #36 #41 #43 #45 #46 #47`

主要原因: 未识别 `resources.requests.memory=100000Gi`，误判为集群内存耗尽、MemoryPressure、ResourceQuota/LimitRange、隐式默认 request 或存量 Pod requests 饱和。

## 后续评分规则建议

- 对 `已排除`、`无`、`没有`、`not`、`without` 附近出现的冲突关键词做更大窗口的否定上下文识别。
- 将 `100k`、`100 核`、`100 vCPU`、`100,000m`、`100000m` 视为 CPU request 异常的等价表达。
- 将 `100TB`、`100,000Gi`、`100000Gi`、`requests.memory` 视为 memory request 异常的等价表达。
- 对 `Node-Selectors`、`node selector`、`spec.nodeSelector` 做归一化，避免大小写和连接符导致漏判。
- 对 `PersistentVolumeClaim`、`PVC`、`claimName`、具体 PVC 名称做归一化，同时避免 `configmap/secret/nodeSelector` 排除项误伤。
