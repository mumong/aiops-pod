# 同状态、不同根因的异常 Case

在原有 c01～c11 上新增 17 个独立变体，复用公共 Pod 模板及现有 Python 镜像。
每个 Case 只注入一种原因，用来检查 Agent 能否区分同类异常，**不是同时注入多个根因**。
已经接入 [正式质量测试](../../aiops_quality_e2e/README.md)：`--scenario variants` 单独遍历变体，
`--scenario expanded` 遍历基础和变体；`--combine` 可以同时部署选中的多个 Case。

## 使用

在 robusta 根目录执行：

```bash
make case-list-variants                  # 列出新增 Case
make case-render CASE=c03-secret         # 仅本地渲染 YAML，不访问集群
kubectl config current-context          # 确认是专用测试集群
make case-deploy CASE=c03-secret         # 部署一个 Case
make case-validate CASE=c03-secret       # 确认状态及具体故障原因已经成立
```

验证通过后，在 AIOps 中提问：**我的集群有什么问题？**
诊断结束后先清理，再部署下一个变体：

```bash
make case-clean CASE=c03-secret          # 只删除该 Case 的测试 namespace
make case-deploy CASE=c03-key
make case-validate CASE=c03-key
```

`case-deploy` 不会自动清理其他 Case；为了单故障盲测，请先手动清理上一个。
新增命名空间为 `aiops-case-v01`～`aiops-case-v17`，名称和 Pod 标签不包含根因答案。
同一变体重复部署前必须先清理，避免旧 Pod、事件及不可变字段干扰。
部署失败也可能已经创建部分资源，可执行该 Case 的清理命令。

原有 `make case-deploy-all`、`make case-deploy-errors`、质量测试 `--scenario all`
仍仅包含 c01～c11，不会顺带部署这些变体。
不带 `CASE` 的 `make case-clean` 仍只清理原 c01～c11；
`make case-clean-variants` 明确清理全部新增变体。
上述清理都会删除对应测试 namespace 中的资源，不要在这些 namespace 存放业务数据。

## 场景对应

所有 11 个基础 Case 至少有 1 个新增变体。新增补齐项：

| Case | namespace | 新原因 / 验收依据 |
|---|---|---|
| `c05-plugin` | aiops-case-v14 | NAD 存在，但 CNI 插件不存在；须有包含插件名和找不到插件的 Sandbox 失败事件 |
| `c08-startup` | aiops-case-v15 | 启动时分配 256Mi 超过 64Mi limit；须有启动日志、OOMKilled、137 和重启 |
| `c09-port` | aiops-case-v16 | 应用监听 18080，readiness 错配 18081；须有连接拒绝事件、监听日志及 Ready=False |
| `c10-timeout` | aiops-case-v17 | /health 延迟 3 秒超过 liveness 的 1 秒超时；须有对应超时事件和重启 |

`c05-plugin` 依赖已有 Multus 和 NAD CRD，只在测试 namespace 创建 NAD，不修改节点 CNI。
这些变体不生成完整的业务 tracing spans；查询空结果不代表工具失效。

| 实际异常状态／事件 | 原有原因 | 新增 Case 与原因 |
|---|---|---|
| Pending / FailedScheduling | c01：nodeSelector 不匹配 | `c01-cpu`：CPU 请求过大；`c01-memory`：内存请求过大；`c01-pvc`：PVC 不存在 |
| ContainerCreating / FailedMount | c03：ConfigMap 不存在 | `c03-secret`：Secret 不存在；`c03-key`：ConfigMap 存在但卷 key 缺失；`c03-hostpath`：hostPath 目录不存在 |
| ImagePullBackOff | c02：无效仓库域名 | `c02-tag`：可访问的仓库中 tag 不存在 |
| CrashLoopBackOff | c06：应用退出 2；c07：应用报 CONFIG_MISSING 后退出 78 | `c06-command`：命令不存在，退出 127；`c06-file`：配置文件不存在，退出 1；`c07-env`：必需环境变量缺失，退出 78 |
| CreateContainerConfigError | c04：Secret 环境变量 key 缺失 | `c04-configmap-key`：ConfigMap 环境变量 key 缺失 |
| Terminating | c11：finalizer 阻塞 | `c11-prestop`：preStop 长时间执行；`c11-grace`：进程忽略 SIGTERM，等待长宽限期 |

**分类按 Kubernetes 实际机制处理**：不存在的 PVC 通常在调度阶段就被拦截，
所以只计为 `c01-pvc`，不伪装成一个 FailedMount Case 再重复计算。
应用自己检查环境变量后退出属于 CrashLoopBackOff，不是 kubelet 的 CreateContainerConfigError。

## 验证什么

新增变体的 `make case-validate` 复用原状态检查，并补充具体原因检查：

- Pending／挂载／拉取／配置错误：当前 Pod UID 的事件必须匹配具体原因；配置错误也允许当前容器 waiting.message 满足全部原因模式。仅看到异常状态不算通过。
- CrashLoop：重启状态、退出码、上一实例的真实错误日志必须同时成立。
- preStop：删除已触发、容器仍运行、无 finalizer，并通过 exec 确认 hook 已创建启动标记文件。
- 长宽限期：删除已触发、无 finalizer／preStop、容器仍运行，并有实际接收 SIGTERM 的日志。

验证失败表示**故障注入或前置环境未满足**，不是 Agent 根因判断失败。
这里不计算根因准确率，也不验收三维遥测；新增简单容器主要提供 Kubernetes 事件和 stdout，
没有复用旧 c06～c11 的业务流量／Trace 驱动，不应声称它们天然具有完整 Logging/Tracing 数据。
原 c01～c11 的 `case-validate` 仍调用原三维可观测性验收脚本。

## 环境与边界

- 仅用于专用测试集群。默认复用 `xnet.registry.io:8443/observability/python:3-alpine`；节点需能拉取该镜像。
- CPU／内存变体通过不可满足的 request 阻止调度，不启动压力程序、不耗尽节点资源。准入策略或 ResourceQuota 直接拒绝 Pod 时，不算目标故障成立。
- `c02-tag` 必须得到 manifest/tag 不存在的错误；DNS、TLS、鉴权或网络错误均不会通过验证。若该 tag 意外存在，需换一个确实不存在的 tag 并同步验证规则。
- `c02-tag` 使用 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908`。部署前可用同仓库正常 tag `3.9` 作对照，确认测试 tag 返回 404/MANIFEST_UNKNOWN；节点仍须能访问该仓库，不关闭 TLS 校验。镜像来源变更后的结果应保存到独立补测目录，不直接覆盖历史样本。
- `c03-hostpath` 仅使用只读挂载和 `type: Directory`，不会创建宿主机目录；要求测试集群允许 hostPath，且指定路径不存在。它不加入原 safe 批量清单。
- Terminating 变体在就绪后自动触发删除，不使用 finalizer。配置的故障等待约 60～65 分钟，实际删除仍取决于 kubelet；重新测试需先清理再部署。清理在评分结束后对自有测试 Pod 写入 `/state/teardown-requested`，让 preStop/进程主动结束等待，再缩短宽限期并确认资源删除。不再只依赖重复 `delete --grace-period=1`。
- preStop 验证需要测试执行者的 `pods/exec` 权限，仅检查已有 Pod，不创建额外探测 Pod。
- 清理先正常删除 namespace。只有删除超时、namespace 归属确认、Pod 已在删除且状态记录显示容器从未启动时，才允许对该 Pod 做带 UID/resourceVersion 前置条件的零宽限期删除；不清除未知 finalizer，不用于运行过或状态不明的容器。

以下历史变体**本次未宣称覆盖**：

| 待补充变体 | 必须先明确的条件 |
|---|---|
| ImagePull：缺少 pull Secret | 需要真实受保护仓库及已知存在的镜像；公开镜像即使 Secret 不存在也可能拉取成功 |
| Sandbox：RuntimeClass 无效 | 不存在的 RuntimeClass 可能直接被准入拒绝；要稳定复现 Sandbox 创建失败，需有效 RuntimeClass 对象配合节点不支持的 handler，涉及集群级资源 |
| Evicted：临时存储 | 需要受控存储配额及隔离环境，不能用填满共享节点磁盘的方式加入默认测试 |

离线渲染及模拟状态／事件回归检查不能替代真实集群验收；每次测试仍需执行上述部署、验证流程确认。
