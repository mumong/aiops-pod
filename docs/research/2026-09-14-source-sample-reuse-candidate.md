# 候选：保留底层采样复用关系的运维观测投影

日期：2026-09-14。状态：新问题证据及完整扩展草案；尚未完成新颖性/创造性检索，不推荐立即定稿申请。

本轮未改业务代码、测试脚本或服务。运行的是独立 Prometheus 离线表达式测试与提取的纯函数，不是线上 Agent 诊断。

## 1. 切口与第一性原理

查询返回五个时间点，并不必然表示采集器采到了五条底层样本。查询引擎可能在多个求值时间重复采用同一条最近样本。

这与之前“极值时间丢失”不同：这里即使保留了每个返回点的时间戳与数值，仍可能不知道它们用了几条不同的源样本。需要区分查询求值时间与底层样本时间，而不是仅扩大摘要或改用更强的选择模型。

适用问题：有限运维上下文里的重复展示占据空间，同时“重复使用一次采样”与“多次采样得到相同读数”难以区分。不是解决全部智能诊断，也不预设采集持续失败或模型已经误诊。

## 2. 公开机制与现有代码

### 2.1 Prometheus 机制

本轮核读官方 [PromQL basics 的 Staleness 部分](https://prometheus.io/docs/prometheus/latest/querying/basics/)：查询求值时间独立于实际序列样本时间；在 lookback 内取最近样本。默认 lookback 为五分钟；显式 stale 标记可令序列提前不再返回，不能把 missing 与 stale 混为一谈。

同页明确范围查询相当于在多个时间运行瞬时查询。官方 [timestamp 函数说明](https://prometheus.io/docs/prometheus/latest/querying/functions/#timestamp) 提供样本时间读取能力。网页为滚动版本，下面另用固定的 v3.5.0 引擎验证具体表达式行为，不将网页最新特性全部视为 v3.5.0 已有能力。

### 2.2 当前 MCP 的可观察口径

`../mcpstander/servers/aiops_observability/query/metrics.py`：

- `compact_prometheus_result` 从范围查询 `values` 的长度取得 `sample_count`；时间戳是响应点的时间戳。
- `_annotate_series` 使用 `query_type == "range" and sample_count >= 2` 计算 `trend_evaluable`。
- Agent 的 `_normalize_metric` 复制这些字段，未从中反推出源样本身份。

这不说明 API 的点数算错，也不说明“查询输出曲线可比较”本身有错。问题是当前元数据**不足以区分输出点数与不同底层样本数**，不能直接据它认证已经多次采到了资源状态。

## 3. 实际执行：原版 Prometheus 引擎，而非模拟其查询逻辑

使用官方 v3.5.0 Linux amd64 release 中的 `promtool`，只提取该二进制到临时目录，没有启动 Prometheus、Docker 容器或集群资源。

- GitHub release API 标注发布日期：2025-07-14。
- `promtool --version`：3.5.0；revision `8be3a9560fbdd18a94dedec4b747c35178177202`。
- release 压缩包 SHA256 与 GitHub asset digest 一致：`e811827af26d822afb09a4f28314f61b618b12cff5369835a67f674d8b46f39a`。
- 临时可执行文件：`/tmp/aiops-promql-provenance-tGRN5S/prometheus-3.5.0.linux-amd64/promtool`。临时目录不保证长期存在。
- 可保留、重跑的输入：[promql_source_reuse.test.yml](promql_source_reuse.test.yml)。

```bash
promtool test rules docs/research/promql_source_reuse.test.yml
```

13 个表达式断言、3 组构造数据通过，输出 `SUCCESS`。没有 recording rules。测试通过子查询验证重复求值行为，没有启动 HTTP API 去执行 `/query_range`。

### 3.1 两种不同采集历史

测试时间为 0、10、20、30、40 秒，指标值为 7。

| 情况 | 底层存储样本 | 重复求值获得的值 |
|---|---|---|
| A | 仅 0 秒存在一条样本，其余为 missing | 五次均为 7 |
| B | 五个时间各存在一条值为 7 的样本 | 五次均为 7 |

40 秒时的引擎实测：

| 表达式 | A | B |
|---|---:|---:|
| `demo_gauge` | 7 | 7 |
| `count_over_time(demo_gauge[50s:10s])` | 5 | 5 |
| `count_over_time(demo_gauge[50s])` | 1 | 5 |
| `timestamp(demo_gauge)` | 0 | 40 |
| `changes(timestamp(demo_gauge)[50s:10s])` | 0 | 4 |

第三组在 10 秒加入显式 stale 标记，40 秒 `demo_gauge` 无样本，已单独断言。这防止把 lookback 误写成所有故障后都持续返回五分钟。

另通过 AST 提取当前 MCP 的 compaction/annotation 相关纯函数，输入五个值均为 7 的构造 API matrix，得到 `sample_count: 5`、`trend_evaluable: true`、first/min/max/last 均为 7。该步骤不是网络响应实录，只验证代码如何处理这种响应形态。

### 3.2 重要反例：不能在任意表达式外包 timestamp

A 在 40 秒时：

- `timestamp(demo_gauge)` 返回 0。
- `timestamp(demo_gauge + 0)` 返回 40。

二者数值计算等价，但时间来源不同。因此 `timestamp(复杂表达式)` 不能自动提供全部底层输入的时间或依赖集合。拟方案必须在受支持的原始选择器处取样本时间；复杂聚合、rate、join 和多叶表达式另需来源传播机制，不能冒称已解决。

## 4. 一个不靠模型凭空判断关系的完整扩展流程

初版只支持明确命名、范围受控的原始浮点序列选择器；指标可为底层存储中的 recording-rule 产物，此时这里的“源”仅到该存储样本，不追溯它的上游传感器或规则计算。

1. **检查表达式类别和对象范围。** AST 识别可支持的选择器，固定 namespace/Pod/时间窗/step。任意复杂表达式不直接套用这个方案，返回来源解析不支持，而非推断来源。
2. **同一查询返回数值通道与源时间通道。** 由程序生成两个带区分标签的分支，一个返回原始值，另一个在原始选择器处调用 `timestamp`。通过 `or` 联合返回，避免另发两次不同时间窗请求。区分标签若与原序列标签冲突则更换并验证或拒绝，不能静默覆盖。
3. **在任何独立截样前配对。** 按原序列标签、求值时间及通道标记配对，恢复 `(series, evaluation_time, source_sample_time, value)`。保留具体采集端身份，不使用当前删 scraper labels 后的结果作为唯一键。任一通道缺失、截断或出现重复冲突，相关部分为来源未知。
4. **按源样本复用关系压缩。** 同一源样本被多个求值点使用时，形成带源时间、值、求值区间/网格及次数的复用段；相同数值但不同源时间不得仅因数值相等合为“一次采样”。同时保留值/时间冲突和未配对范围。
5. **按这份关系构建有限输入。** 输出求值点数、已识别的不同源样本数、复用段和遗漏信息；容量不足时优先省去重复求值细节，不删除“这是复用而非新采样”的区别。新源样本太多仍可省略，但必须标记，不宣称完整时序。
6. **将采样状态交给分析/后续取证。** 只有一个已识别源样本时，不把多次求值当作多次实际采样来支持资源变化判断。Agent 或可选小模型可据此选择查看采集状态、读取原始样本或等待有界补采；不由程序直接断言采集器故障。
7. **有界终止和回退。** 不支持的运算、通道预算不足、源身份不确定等保留 unknown；最多执行约定次数的补采。不得以旧快照中的“无新增源样本”证明未来不会有更新，也不能自动阻止可能有价值的细粒度查询。

步骤 2 的表达式机制已由离线引擎测试验证；步骤 3–7 为设计，未实现服务接入、配对器、投影器或模型调度。不是现有 MCP 新功能说明。

### 已验证的双通道表达式机制

```promql
label_replace(demo_gauge, "obs_channel", "value", "__name__", ".*")
or
label_replace(timestamp(demo_gauge), "obs_channel", "source_timestamp", "__name__", ".*")
```

在 A 的 40 秒，前一通道为 7，后一通道为 0。实际业务生成时必须加入对象过滤；测试 fixture 本身已用单一固定标签序列，不等于上述裸表达式可绕过 MCP 的范围校验。

单查询减少两次独立请求的配对歧义，但本轮未核实所有远端代理、存储实现的事务快照保证，不泛称全链路强一致。

### 设计的紧凑输出示意

```json
{
  "evaluation_point_count": 5,
  "distinct_source_samples_used": 1,
  "source_scope": "stored_samples_of_this_selector",
  "reuse_segments": [
    {"source_time": 0, "value": 7, "evaluation_start": 0, "evaluation_end": 40, "step": 10, "count": 5}
  ],
  "sampling_statement": "one stored sample reused at five evaluation points"
}
```

这不是线上返回。`distinct_source_samples_used` 仅统计返回点所使用的源样本，**不等于窗口内存储的全部样本数**。粗网格可能错过短暂存在的其他样本；没有原始范围样本索引时，不能提前证明减小 step 没有信息增益。

## 5. 技术作用与边界

可解释的作用：让“多次展示一次采样”与“多次采样值相同”在压缩后仍不同；在同源复用较多时减少重复点占用。不能保证所有数据上更短，因为双通道与来源字段自身增加开销。

下列主张目前均不成立：

- 不同源时间表示统计独立观测或独立的因果证据；
- 一条源样本证明整个窗口内资源稳定或采集故障；
- 根据已用源样本数得出整个窗口没有漏采/漏看；
- 支持任意 PromQL 及全部嵌套算子的完整 lineage；
- 本例证明线上根因准确率得到改善。

合适的对照不是仅比较“长文本 vs 短文本”，还需比较：原始点列、仅按相同值合并、加 source timestamp、按源复用关系组织。在 A/B 两个输入上，值去重和现有点数不能区分；标准 timestamp/read-raw 已能提供区分信息，所以新增控制关系不能只说“加一个时间戳”。

## 6. 跨域与专利检索进展

跨域问题线索是信息融合中的重复利用同一数据（data incest），但不能直接把传感器置信度模型移到 LLM 上，也不能给源样本数量赋予未经验证的概率含义。

### 6.1 关键词命中必须核对

FPO `"data incest"` 返回 4 项，其中 US9411072B2 *Real-time adaptive weather surveillance system and method* 本轮读了 FPO 首页信息及权利要求 1–25。其主题是天气预测与选择摄像头的影像确认，抓取文本中的权项 1 出现 `data incest module`，而上下文反复使用 `data ingest module`；未找到支持重复信息纠偏的相关说明书段落。不能把这个疑似文本用词问题当作直接近邻。

### 6.2 US12313409B2 的核验范围

名称：*Method of estimating a metric of interest related to the motion of a body*；Focal Point Positioning Limited；申请日 2021-04-12，授权公告日 2025-05-27；首页记载 US20210254979A1 于 2021-08-19 公开，更早优先权未逐项核定。

[USPTO 官方原件](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12313409)，37 页。本轮目视读取首页、第 14–18 页（说明书栏 1–10）、第 34–37 页（含全部权利要求 1–41）。未完整读取其余说明书，尤其尚未定位搜索命中的 data-incest 段落，不假称已核实其对应解决手段。

权利要求 1 是用主定位单元与副传感器的第一时段数据训练，之后用副传感器数据估计运动指标；8、10、12 等涉及以估计运动指标约束进一步估计、纠正数据以及 Kalman filter。它不能仅因包含传感器和多个时间段，就被描述成“跟踪重复源采样身份”的同一个方法。

### 6.3 当前选择

保留本候选继续研究：问题由原版引擎和现有纯函数支持，来源关联有实际取数方法，不依赖虚构语义关系；比单纯扩大输入或增加模型角色更具体。

但 Prometheus 的 timestamp、原始 range vector、普通来源追踪和按重复数据压缩都已有基础。当前只形成可实施方案和若干区别要求，**尚无足够依据认定新颖性或创造性**。下一步需要对照“源样本关联怎样同时控制配对截样、摘要信息及后续取证反馈”，而不是把单个内建查询函数当作发明。

## 7. 续查：工业遥测与时序数据处理的更直接近邻

### 7.1 OPC UA：源时间、服务器时间与可用性已有明确分工

核读 [OPC UA Part 4，7.11 DataValue](https://reference.opcfoundation.org/Core/Part4/v105/docs/7.11) 的第 7.11.1–7.11.5 节。页面显示版本 v1.05.07。本轮另尝试 v104 地址，但实际仍显示 v1.05.07，**没有据此声称已读到历史 v1.04 原文或核定该文本最早公开日**。

- DataValue 同时携带 value、statusCode、sourceTimestamp、serverTimestamp。
- sourceTimestamp 与收到的 value instance 关联，不只取决于实际数值；源时间一旦赋予该实例就不改变。跨 OPC UA Server 传递时保留源时间，不重写成中转时间。
- ServerTimestamp 表示服务器收到值或知道值仍准确的时间，各服务器可分别赋予。
- 标准明确举例：源设备按变化上报，三分钟前发过一个值，但持续检查连接和状态时，服务器时间仍可每半秒更新。
- 客户端使用值前至少检查 StatusCode 的 Good/Uncertain/Bad 严重性；源时间不可得时可为 null。

因此，“旧源时间与新接收/检查时间共存”“不把重新处理时间替代源时间”“时间字段配合可用性判断”不是新的上位思想。

**不能照搬：** OPC UA 的 sourceTimestamp 可指向值或状态的最近变化，其 serverTimestamp 在具备异常上报契约时可表示值仍准确。PromQL 的求值时间并不自动具备这种持续有效性保证。旧 sourceTimestamp 也不能单独证明采集器故障。我们的候选只能先谈 Prometheus 底层存储样本，不应直接泛化为所有遥测协议的真实采样次数。

### 7.2 US10417251B2：传感器行折叠、区间查询及展开已连接

标题：*System and method for storage and analysis of time-based data*；The Boeing Company；申请日 2014-10-31，授权公告日 2019-09-17；官方首页记载早期公开 US20160125053A1，2016-05-05。

- [FPO 文本](https://www.freepatentsonline.com/10417251.html)
- [USPTO 官方原件](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10417251)
- 本轮先读 FPO 权利要求 1–20，再目视核对官方 PDF 第 1、15–17 页，覆盖全部权利要求。没有精读全部说明书；不复述其未复现的性能增益作为本项目效果。

权利要求 1、9、15 的实际链条包括：

1. 传感器记录包括飞行/车辆身份、传感器身份、时间偏移与值。
2. 每行与相同身份的后继行连接，转为起止时间区间。
3. 相同身份、相同值而时间不同的行被折叠为较少区间。
4. 通过时间区间重叠进行查询/连接，也可按指定时间粒度展开回非区间形式。
5. 对后续输入识别、排序并规范化净变化，生成查询语言代码更新折叠后的表。

权利要求 16–20 还涉及时间内序列、源时间、快照输入及避免导入除时间外重复的记录等。

**与本候选的差别：** 上述折叠条件显式允许相同值、不同时间的行合并；本候选需要额外保留“各求值点实际用了哪条存储样本”，不把一次样本的重复采用与不同样本同值混为一类。这是待讨论区别，不意味着该专利实现必然无法另保采样信息，也不意味着加入 source timestamp 作为归并字段就非显而易见。

### 7.3 US11275726B2：双时间、确定性处理与输入范围追踪已连接

标题：*Distributed data processing method with complete provenance and reproducibility*；Kamu Data Inc.；FPO 记载申请日 2020-12-06，授权公告日 2022-03-15。

核读 [FPO 文本](https://www.freepatentsonline.com/11275726.html) 的首页信息、全部权利要求 1–9，以及说明书的 bitemporal modelling/temporal metadata 段落。未核对官方扫描件或审查档案。

权利要求 1 包含：事件发生时间和接收时间的双时间事件账本；不可变数据块及元数据哈希关联；对源/派生数据应用流处理；限制为确定性、可重现且不能访问外部系统的运算；记录运算源码、处理器版本、每次处理的输入范围及输出哈希。权利要求 2 包含预聚合账本数据。

因此，“来源记录—确定性转换—派生数据—输入范围与版本追踪”已经不是未连接的零散操作。本候选不能通过再增加 source map、版本或归档来逃避这类近邻。

但该权利要求的输入批次/范围 provenance 并不自动等于 PromQL 输出点到源采样的逐点复用关系；本轮没有认定它逐项公开当前全部候选。

### 7.4 研究决定与更强的简单基线

| 候选组成 | 已有公开基础 | 本轮决定 |
|---|---|---|
| 源时间与求值/处理时间不同 | OPC UA；Prometheus timestamp/求值语义 | 不作为独有发现 |
| 同值点折叠为区间并可展开 | US10417251B2 | 不把区间压缩本身作为贡献 |
| 处理版本与输入来源跟踪 | US11275726B2 | 不靠附加 lineage/版本标签区分 |
| 源采样复用关系参与有限观测投影 | 本轮所读文献未直接给出完整相同链 | 仍需论证，不由“尚未看见完全相同”认定创造性 |

还必须比较一个更简单的 Prometheus 原生方案：用原始 range vector 或 `count_over_time(selector[W])` 取得原始窗口样本/数量，再由普通程序生成统计和有限摘要。上一轮引擎测试已显示原生 count_over_time 能区分 1 条与 5 条底层样本。若目标只是避免混淆两种样本数量，未必需要双通道和复用段结构。

本轮不将候选升级为推荐申请，也不因为组成步骤分别已知就宣判整个组合相同。剩余需要回答的是：**除了原始样本查询加常规摘要之外，复用关系参与处理到底带来了哪项具体、必要、且非显而易见的改变？** 对这一问题目前尚无充分答案，继续追加 Agent 或时间戳字段不是替代办法。
