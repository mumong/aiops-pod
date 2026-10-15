# 安全审查记录

2026-09-24 三项目规范化期间独立扫描的复核记录。扫描结果不是运行安全证明，
下列暂未修复项也不代表已获准接受风险。不得将原始扫描报告或真实凭据提交仓库。

## 已修复并验证

联邦 Agent 的工具参数兼容解析原先在 JSON 失败后执行 `eval`，参数来自模型输出，
不能视为可信代码。改为 `ast.literal_eval`，保留 JSON 和 Python 字面量兼容输入，
拒绝调用表达式。测试覆盖合法输入、嵌套字面量及表达式拒绝；完整回归未新增失败。

## 必须继续处理

| 项目 | 证据与影响 | 处理状态 |
|---|---|---|
| Git 跟踪的模型凭据 | `deploy/secrets/core.yaml` 含非占位配置；ignore 不会停止已跟踪文件 | 已从索引移除且验证本地字节未变；新增公共示例，未 commit；轮换与历史清理仍待协调 |
| MCP SDK 传输漏洞 | 后端声明 1.25.0，MCP 服务声明 1.12.2；扫描命中传输相关高危项 | 待验证实际传输及兼容升级，不能以“内网”认定安全 |
| Elasticsearch TLS | MCP 的日志查询/采集显式 `verify=False` | 有中间人风险，待核实现场 CA 与配置兼容方案 |
| Shell 工具 | MCP 含 `shell=True`，属于已有命令执行能力 | 保留功能，继续检查入口鉴权、权限和参数边界 |
| 基础镜像及依赖 | 后端/MCP 现有镜像有多项高危及严重漏洞 | 逐项评估升级和功能风险，不盲目跨版本升级 |
| 开发工具 | pytest 版本有扫描告警 | 与运行时分开处理，不把开发工具带入运行镜像 |

## LiteLLM 可达性初查

本仓库直接调用 LiteLLM 的位置为 `app/core/federation/agent.py` 和
`app/core/federation/aggregator.py`，使用 `litellm.completion` SDK。
镜像默认入口为 `python run.py`，部署未配置 LiteLLM proxy 启动命令。
源码搜索未发现 `proxy_server` 路由导入。因此扫描命中的代理 JWT/OIDC/管理接口漏洞
（CVE-2026-35030、CVE-2026-49468）尚无本应用直接暴露对应接口的证据。
这仅是可达性初查，不是批准例外，也不能推广为整个依赖无风险；仍需镜像/进程复核。

## 本轮发布镜像复扫

最终后端11.0.197精确digest
`sha256:6e51bce2b2dcb1f7f97a0432bd59ca9decec889683e5012f9e8199253bcf346c`
复扫退出0，仍为530条告警（16严重、160高危、204中危、117低危、33未知）。
最终后端源码复扫覆盖175文件，0命中、0解析/超时错误，覆盖最后import合并，
扫描前后该文件哈希一致。证据目录`/tmp/aiops-release197-security.vVGtqd`，
只保存脱敏统计用于交付；原始报告权限0600，不能提交仓库。

前端 0.1.28 的 Trivy 结果无漏洞记录。后端 11.0.195 为原运行时依赖与系统层缓存，
扫描仍有 530 条记录（16 CRITICAL、160 HIGH、204 MEDIUM、117 LOW、33 UNKNOWN），
与基线分类数量一致。源码安全修复不能消除基础镜像和依赖风险；不宣称扫描全绿。
MCP 7.0.31 发布镜像复扫为734条（18 CRITICAL、245 HIGH、301 MEDIUM、140 LOW、
30 UNKNOWN），与基线分类数量一致。镜像另有 pipenet 传递依赖声明 Node>=22，
当前Node20，SSE冒烟虽通过，仍保留兼容性警告，不将其解释为全部功能兼容的证明。
pytest 9.0.3 仅用于开发检查，运行镜像依赖未升级；A2A 专用开发依赖仍待独立兼容验证。

A2A 开发工具约束已核实：pytest-asyncio 1.2.0 要求 `pytest<9,>=8.2`，
不能只改 pytest 至9.0.3。A2A 原依赖测试 17过/1失败；同一失败在旧11.0.168镜像
及纯SDK队列复现中存在，属于订阅终态丢失的既有问题，不以升级测试工具掩盖。
该开发工具风险仍待协调升级插件及验证，不是已经接受的永久例外。

源码独立复扫（同规则、timeout 30，排除虚拟环境/生成目录）：后端 171 文件无命中，
MCP 97 文件 5 项命中，前端 136 文件无命中；三个项目均无解析或超时警告。
已确认联邦 eval 告警消失，前端清单 YAML 警告消失。
MCP 仍有两处 TLS 关闭、命令 runner shell、启动器 shell、calculate eval。
启动器告警减少来自去重，不是风险修复；通用 Bash 移入 helper 后不再被规则命中，
也不表示风险消失。kubectl_run_image 的 argv 修复由源码和安全回归单独证明。
脱敏复扫报告：`/tmp/aiops-security-rescan.MrKEpy/REPORT.md`，原始报告不得提交。

## MCP 运行边界复核

只读检查确认线上 test-tools、k8s-core、bash_command 已启用；对 test 8091 和 bash
8094 的 `/sse` 不带凭据连接得到 HTTP 200，未调用任何工具。连接可达不单独证明
所有工具执行无需鉴权，但结合服务端无鉴权实现需要按高风险入口处理。
服务为 ClusterIP，所在命名空间未列出 NetworkPolicy；不能因此推断公网可达，
也不能把内网连通视为授权。服务账号 ClusterRole 含 apiGroups/resources/verbs 全 `*`。

命令工具使用 shell 是业务能力；然而 `_command_runner` 会把字符串插入命令模板，
现有 sanitize 仅保留标量，不是 shell 转义。故“只读工具名”不构成命令级安全边界。
待选方案是 MCP 入口鉴权、网络访问控制、按服务拆分权限，以及逐个命令参数契约改造。
这些会改变既有调用/运维能力，本次不直接删除工具或收紧全部路由权限；需单独兼容验证。

test_server 的 calculate 有字符白名单，禁止标识符，不能等同任意 Python 代码执行；
但仍允许 `**` 且缺少输入规模限制，同步计算存在资源耗尽风险。
Elasticsearch 的 `verify=False` 所在 direct URL 分支在当前现场配置未启用，
属于条件可达；默认 exec 路径还使用 `curl -sk`，所以不能仅因 direct 分支未启用
就关闭 TLS 风险记录。正确处理需确认证书/CA及所有访问路径。

## 许可证及第三方归属

初次审计时三个仓库均无LICENSE/NOTICE，前端旧README仅声明MIT。维护者现已明确
选择Apache-2.0；三个仓库已新增标准LICENSE并更新README，限定项目自有代码，
第三方代码和依赖保留原授权。文本取自系统标准许可证，三份SHA256均为
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`。
未虚构版权主体名称，未将许可选择等同第三方归属核查完成。MCP的holmes gitlink指向
`bc3faa87ecb0ac653e4e1f373dea3c12652862b8`，当前无 .gitmodules 来源映射，
本地目录未见许可证；若干模块明确注明移植 Holmes。不能根据项目名称猜测授权。
仍需核实实际上游仓库/版本，再补相应第三方许可与归属材料。
Apache-2.0允许商业使用，并非“非商业许可证”。本次仅许可/文档变更，不改变运行服务。

## 扫描执行情况

基线使用指定 secagent v4.0 的 Semgrep、Trivy，源码只读挂载；规则下载不上传源码。
关闭遥测后 `--config auto` 不兼容，改用显式 `p/ci`、`p/security-audit`、`p/secrets`。
Trivy 使用指定内网服务。非标准名称的 requirements 文件在临时目录按标准名称扫描。
npm lockfile 已扫描。另以指定 secagent v4.1 / Retire 5.7.0 扫描前端源码及 dist，
只读挂载，排除 .git 和 node_modules；结果 data/messages/errors 均为空，退出码 0。
此结果不覆盖排除的依赖目录，依赖清单以 Trivy npm lockfile 扫描补充，
不能理解为所有打包后的依赖都已被 Retire 识别。已完成上一发布批次源码复扫；
最终提示词整理批次的复扫证据已补在本节开头。

A2A sidecar 11.0.168 已补做 Trivy 镜像扫描：OS 173 条（3 CRITICAL、51 HIGH、
56 MEDIUM、57 LOW、6 UNKNOWN），Python 11 条（2 HIGH、7 MEDIUM、2 LOW）。
这是扫描记录数量，不是去重后的可利用漏洞数；尚待逐项分析，并未因主镜像重构而消失。
没有 Go、Ansible、Yarn 项目配置，相应语言检查不适用；镜像内 Go 工具仍由镜像扫描覆盖。
扫描工具未报告秘密不意味着仓库没有秘密，人工检查已发现上述被跟踪的配置。
