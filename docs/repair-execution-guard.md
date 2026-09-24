# 修复执行命令检查（11.0.199）

仅作用于当前 `executor: pod` 修复路径，不改变 Query/MCP 全局权限、RBAC、提示词或修复方法。
不是全局安全沙箱，也不是对所有删除行为的保证。

## 流程

Agent 生成方案 → 对全部动作的非空 dry_run/execute/verify 命令预检查 → 原有审批 → 每条执行前再次检查 → 返回实际结果。
禁用项不能通过人工审批或 auto 模式绕过；管理员可通过配置调整。
检查失败返回 remediation_tool_result（failed、execution_skipped=true、error_code=repair_command_denied），然后 remediation_finished（blocked）。
预检查不通过时整个计划均未执行，不自动改写、重试或运行替代命令。

## 配置

位置：`deploy/configmap/config.yaml` 的 `workflow.remediation`。
线上：`aiops` 命名空间 `aiops-config` 中 `config.yaml` 的同一路径。修改后滚动重启后端加载，不能由工具参数覆盖。
省略这两个字段时使用下列默认值，因此升级镜像即可启用，不必覆盖现有 ConfigMap 的其他配置。

```yaml
denied_executables: [rm, unlink, shred, dd, "mkfs*", wipefs, fdisk, sfdisk, parted, reboot, shutdown, halt, poweroff]
allowed_exec_commands: [echo, printf, cat, ls, pwd, stat, head, tail, grep, wc, id, whoami, hostname, uname, date, ps, df, du, "true", "false", test, "["]
```

- 顶层入口仍只允许 kubectl；原有 allowed_operations/denied_operations 配置继续有效。
- denied_executables 按实际可执行文件名匹配，支持通配符，优先于 allowed_exec_commands。
- allowed_exec_commands 只限制 kubectl exec/run/debug 的明确内层命令，不限制普通 Kubernetes apply/patch 等操作。
- 明确的 sh/bash/dash/ash -c 字面量及简单 env/command/busybox 包装会继续检查内层命令。变量替换、脚本文件、重定向、后台执行、复杂语法和未知解释器默认拒绝。
- 不误将 --rm 参数、echo rm 或 /tmp/rm.txt 视为 rm 执行。
- 想开放额外容器内命令，加入 allowed_exec_commands；想解除默认禁令，需同时移出 denied_executables。配置为完整替换，不是追加。空 deny 列表意味着关闭默认命令名禁令，请谨慎使用。

## 明确不覆盖

Query 的 Bash 工具、MCP 直接调用、历史兼容执行器、manifest/patch 内的程序、容器镜像默认入口、已允许程序本身的副作用。不扫描清单、不增加故障专用脚本。允许 rm 之外的程序或 Kubernetes 删除资源，也可能删除数据。
命令名检查只针对误操作；即便允许的可执行文件被替换成其他内容也无法由本检查识别。
