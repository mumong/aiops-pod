# c02-tag 独立补测（2026-09-15）

目的：补齐历史 `aiops_quality_expanded-c0e3e093e80c_20260910_181943` 中因仓库 TLS 错误没有获得样本的 tag 缺失根因。不是将 TLS 故障改判为 tag 缺失。

## 实际调整

- 故障类型、namespace `aiops-case-v07`、评分预期不变。
- 测试镜像改为 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908`，命令匹配镜像为 `/pause`。
- 环境门槛保留旧 python tag 的识别，并增加新 pause tag 精确 not-found 形式；未接受 DNS、TLS、403 或其他资源 not-found 作为目标故障。
- 不修改 Agent、Runbook、RBAC、节点证书，不关闭 TLS 校验。

## 补测前验证

- 同仓库正常 tag `3.9`：HTTP 200，digest `sha256:7031c1b283388d2c2e09b57badb803c05ebed362dc88d84b480cc47f72a21097`。
- 故意不存在 tag：HTTP 404，错误 `MANIFEST_UNKNOWN`。
- `make case-deploy CASE=c02-tag` 后实际部署至 node2；Pod UID `e8551fa2-3c5c-4324-b99e-eee766ac71d1`。
- `make case-validate CASE=c02-tag`：matched=true，status=true，cause_event=true，blocking_events=[]。该预检 Pod 会由正式测试脚本清理并重建，正式运行快照中的 UID 因此不同。
- 离线场景测试55项通过；评分及恢复测试36项独立运行通过。两套测试合跑有 tests.unit 导入冲突，独立运行通过；未修改无关测试基础设施。

## 运行与可比性

计划50次、并发1、每次超时1200秒，通过原 runner 的 protected worker 后台执行；实际进度见 runner.status.json、runner.log、stats.json。完成后自动清理测试 namespace。

2026-09-15 10:57 检查线上：health=healthy；模型 `openai/Qwen3.6-35B-A3B`；服务镜像 `aiops-copilot:11.0.157`，适配器 `aiops-a2a-adapter:11.0.157`。本轮未变更服务配置。历史运行的完整模型配置未独立证实一致，因此不得无说明地当成同一历史批次。

结果保存在本目录，不覆盖历史 stats.json、summary.md 或人工裁定。后续展示可以增加“独立补测”列，若合并指标必须标明不同执行时间、镜像来源及原始统计来源。c05-plugin 等历史未完成项不会因本次补测而自动变成完成。

## 首次有效样本检查（不是最终统计）

第1次 `9749ece7ccff48ab` 请求成功且 fixture_valid=true，耗时73.854秒。Runbook覆盖1，证据完整度6/7。原脚本根因分0，失败理由为 `missing_causal_mechanism`。

已人工读该报告全文：因果链明确“Pod Spec 配置了不存在的镜像 tag → 远程仓库返回 NotFound → 拉取失败”，根因结论亦定位具体镜像引用不存在，核心根因通过。原根因评分限制机制词间跨度且主要评结论段，长镜像地址／表达顺序造成漏判；本次运行期间不改评分规则、不重写原分。待50次完成后再单独汇总人工与原评分差异。
