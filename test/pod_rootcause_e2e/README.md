# 历史 Pod 精确根因测试

本目录保留早期“同症状、不同根因”测试，供历史回放和专项调试。**历史成绩不代表当前服务表现**，本页不再重复展示旧批次成绩。当前正式入口见 [AIOps 质量测试](../aiops_quality_e2e/README.md)，使用 `--scenario expanded` 遍历当前基础及变体 Case。

## 场景与运行

`cases.yaml` 和 `manifests/` 定义具体原因；`test.txt` 选择 case 或 `group:<name>`，例如 `group:pending`、`group:volumemount`。从仓库根目录执行：

```bash
kubectl config current-context
.venv/bin/python test/pod_rootcause_e2e/run_rootcause_suite.py --scenarios-file test/pod_rootcause_e2e/test.txt -n 1 -c 1 --question "我的集群有什么问题" --url http://10.2.0.48:30800
```

suite 按 case 串行清理、部署、触发、等待、诊断和保存结果。旧入口不等同于当前质量脚本的后台保护与指纹续跑；长任务建议使用当前入口。

输出在 `testreports/pod_rootcause_suite_*/`：`summary.md`、`stats.json` 及单次 `response_N.md`。旧分数来自该版本规则，不能直接合并到当前基线。

## 操作边界

- 仅在专用测试集群运行；部署和清理会改变真实 Kubernetes 资源。
- preStop/长宽限期历史清单的故障窗口可达 6 小时，旧 suite 会强制删除实验 Pod；不用于承载业务或持久数据的环境。
- RuntimeClass 场景涉及集群级对象；节点失联、压力驱逐、CNI/runtime 修改不应加入默认测试。
- 缺失 PVC 常在调度阶段被拦截；缺少 pull Secret 不保证公开镜像拉取失败。应核对真实事件，不能依据场景名认定注入成立。
- 精确根因仍是规则匹配，低分和高分均可能需要人工复核；需要新版具体原因门槛与前后快照时使用当前质量测试。
