# Pod RootCause E2E

这个目录用于“精确根因”测试，和 `test/pod_abnormal_e2e` 分开维护。

`pod_abnormal_e2e` 验证系统是否识别异常类型，例如 `VolumeMountFailed / L0`。
`pod_rootcause_e2e` 验证同一异常类型下是否识别具体根因，例如 ConfigMap 不存在、Secret 不存在、PVC 不存在、hostPath 错误。

## 根因准确率口径

根因准确率只匹配最终报告中的根因部分：

- 优先提取 `## 🎯 根因分析`
- 其次提取 `### 根因结论`
- 兜底使用整份报告，但会在结果中标记 `root_section_source=full_report_fallback`

每个 case 使用 `root_cause_signature` 判断：

- `include_all`: 必须全部命中
- `include_any`: 至少命中一个
- `exclude_any`: 如果命中任意冲突关键词，则判根因错误

报告中会展示：

- `命中关键词`
- `缺失关键词`
- `冲突关键词`

## 单个 case 测试

```bash
kubectl apply -f test/pod_rootcause_e2e/manifests/00-namespace.yaml
kubectl apply -f test/pod_rootcause_e2e/manifests/volumemount/missing-configmap.yaml

.venv/bin/python test/pod_rootcause_e2e/run_rootcause_cases.py \
  --case volume-mount-missing-configmap \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800
```

## 按 group 测试

```bash
.venv/bin/python test/pod_rootcause_e2e/run_rootcause_cases.py \
  --group volumemount \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800
```

注意：`run_rootcause_cases.py` 只发请求和统计结果，不自动 apply/cleanup 资源。

## 串行自动 apply + 测试

编辑 `test/pod_rootcause_e2e/test.txt`：

```text
group:volumemount
volume-mount-missing-pvc
group:imagepull
```

执行：

```bash
.venv/bin/python test/pod_rootcause_e2e/run_rootcause_suite.py \
  --scenarios-file test/pod_rootcause_e2e/test.txt \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800
```

suite 会串行执行 case：清理已知资源、apply 对应 manifest、等待异常稳定、调用 `run_rootcause_cases.py`、保存 summary。

如果 `test.txt` 同时写了具体 case 和包含它的 group，脚本会自动去重；执行顺序以首次选中的位置为准。

## v1-core 范围

- `volumemount`: ConfigMap 不存在、Secret 不存在、ConfigMap key 不存在、PVC 不存在、hostPath 路径不存在
- `pending`: nodeSelector 不匹配、CPU 不足、Memory 不足、PVC 不存在
- `imagepull`: registry 无效、镜像 tag 不存在、imagePullSecret 不存在
- `crashloop`: 非零退出码、命令不存在、配置文件缺失
- `configerror`: 必需 env 缺失、ConfigMap key 缺失、Secret key 缺失
- `oomkilled`: memory limit 过低
- `notready`: readinessProbe 失败、livenessProbe 失败

## v2-backlog

见 `backlog.yaml`。这些 case 更全面，但需要破坏节点、依赖私有 registry/CNI/storageclass，暂不进入 v1 夜间自动测试。
