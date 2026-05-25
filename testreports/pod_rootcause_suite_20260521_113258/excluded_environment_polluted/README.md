# Excluded Environment-Polluted Results

这些目录从最终 `suite_summary.md` / `suite_stats.json` 中排除，但原始 `stats.json`、`summary.md` 和 response 文件仍保留。

排除起点: `imagepull/10-imagepull-invalid-registry`。

原因: 从该阶段开始，集群中出现非当前 case 的调试/网络测试 Pod，例如 `mcp/node-debugger-*`、`default/dns-test*`、`registry-*`、`connectivity-*`。这些 Pod 被全局扫描识别为异常，导致后续 case 的根因判断和质量统计不再代表单一目标异常。

被排除的 case:
- `imagepull/10-imagepull-invalid-registry`: 环境污染后产生，移出最终统计
- `imagepull/11-imagepull-image-not-found`: 环境污染后产生，移出最终统计
- `imagepull/12-imagepull-missing-pull-secret`: 环境污染后产生，移出最终统计
- `crashloop/13-crashloop-exit-code-nonzero`: 环境污染后产生，移出最终统计
- `crashloop/14-crashloop-command-not-found`: 环境污染后产生，移出最终统计
- `crashloop/15-crashloop-config-file-missing`: 环境污染后产生，移出最终统计
- `configerror/16-configerror-env-missing`: 环境污染后产生，移出最终统计
- `configerror/17-configerror-configmap-key-missing-env`: 环境污染后产生，移出最终统计
- `configerror/18-configerror-secret-key-missing-env`: 环境污染后产生，移出最终统计
- `oomkilled/19-oomkilled-memory-limit-too-low`: 环境污染后产生，移出最终统计
- `notready/20-notready-readiness-probe-failed`: 环境污染后产生，移出最终统计
- `notready/21-notready-liveness-probe-failed`: 环境污染后产生，移出最终统计
- `terminating/22-terminating-finalizer-stuck`: 环境污染后产生且测试中途停止，无 stats.json；已发现 response 文件 18 个
