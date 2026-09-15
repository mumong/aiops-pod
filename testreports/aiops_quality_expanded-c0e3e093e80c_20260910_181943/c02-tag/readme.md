# c02-tag · 镜像 tag 不存在

[返回完整汇总](../summary.md)

## 最新结果：2026-09-15 独立补测

补测于 11:59:11 正常完成，退出码 0；50/50 请求成功且异常注入有效，没有排除样本。

| 根因准确率 | Runbook 覆盖率 | 证据完整度 | 平均诊断耗时 |
|---:|---:|---:|---:|
| 60.0%（30/50） | 100.0% | 85.1% | 70.9 秒 |

以上为脚本原始评分，不是人工裁定；执行完成不代表根因指标达标。

- [50 次运行明细及逐份报告](supplement-20260915/readme.md)
- [原始评分 stats.json](supplement-20260915/stats.json)
- [执行日志](supplement-20260915/runner.log)／[完成状态](supplement-20260915/runner.status.json)
- [补测准备与配置说明](supplement-20260915/SUPPLEMENT_NOTES.md)

报告、SSE、事件、证据归档、评分及注入快照一并保存在本目录的 `supplement-20260915/run-*/` 下。[补测源目录](../../aiops_quality_c02-tag_supplement_20260915_105800/readme.md)仍保留，复制文件内的原始来源路径未改写。

## 为什么原来没有样本

历史仓库返回 TLS 证书不受信任错误，尚未验证到 tag 是否存在，故脚本阻止了该场景进入评分。原阻塞记录仍在本目录，见[历史 README](readme-original.md)。

本次未改变“tag 不存在”的目标根因，只把镜像换成：
`registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908`。

补测前验证同仓库正常 tag `3.9` 返回 200，不存在 tag 返回 404 / MANIFEST_UNKNOWN，且实际 Pod 故障检查通过。未修改 Agent、Runbook、RBAC 或节点证书。

本次是独立补测，不能当作原历史运行产生的样本。全局汇总明确标记跨批次，并保留历史与补测两份 stats.json。
