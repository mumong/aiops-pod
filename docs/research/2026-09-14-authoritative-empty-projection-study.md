# 过滤结果为空，不等于没有过滤结果

日期：2026-09-14。研究范围：现有代码只读核查、构造输入调用真实投影函数、公开技术对照。没有执行集群查询、线上模型、业务测试或部署；没有修改业务代码。

## 1. 为什么需要这次纠偏

此前候选把重点放在“字段仍在输入内，但共享字典导致消费模型误读”。当前核读的三维观测投影并不是原型的 `groups/rows` 字典：指标名、值、单位、统计字段主要逐条存在；部分身份字段由顶层对象信息代替。

因此，原型只能说明一种拟扩展表示可以执行，不能证明当前工程的问题就是共享字典误读，更不能因为构造的展开过程可逆，就证明值得增加模型回读调用。

这次实际发现的是另一种程序边界：**源端已经过滤过的空结果，在下游可能被当作“没有结果格式可用”，进而恢复未过滤的旧格式数据。** 这与模型能力无关，也不需要小模型判断旧 UID 是否等于当前 UID。

## 2. 已核对的代码链

### 2.1 MCP 可以合法发布“有旧格式事实，但当前对象 ledger 为空”的响应

`mcpstander/servers/aiops_observability/query/fact_ledger.py`：

- `_fact_record` 在事实携带 `pod_uid` 且不等于当前 scope UID 时返回 `None`，排除该 canonical record。
- ledger 构建仍可返回带 `contract_version`、`scope_entity_ids`、`records: []`、`record_count: 0` 的结果。
- `tests/test_aiops_observability_query_logs.py::test_old_uid_hit_is_not_published_in_current_pod_fact_ledger` 明确构造旧 UID 日志，并断言旧格式 `samples/facts` 保留旧 UID，而序列化后的 canonical ledger records 为空。

本轮读了这个测试，没有运行该测试或重现真实 Elasticsearch 请求。它支持这是代码考虑过的响应形态，而不是证明线上已出现此故障。

### 2.2 Agent 投影把空 ledger 与缺失 ledger 合并处理

`app/core/context/observability_projection.py::_canonical_records` 的相关逻辑：

```python
ledger = payload.get("fact_ledger") if isinstance(payload.get("fact_ledger"), dict) else {}
records = ledger.get("records") if isinstance(ledger.get("records"), list) else []
if not records:
    records = payload.get("facts") if isinstance(payload.get("facts"), list) else []
```

这里没有区分：

1. 未提供或未识别 canonical ledger；
2. 已提供有效 ledger，且范围过滤后的记录集合为空。

第二种情况下仍可能使用旧格式事实。`_canonical_records` 随后可从事实或样本恢复每条 `pod_uid`，所以 structured evidence 此时仍可看见差异。

### 2.3 多条事实的摘要又省略逐条 UID

`_summary_evidence(..., compact=True)` 会删除 `pod_uid` 和 `identity_basis`；`render_observability_summary` 在原始 evidence 数量大于 1 时使用这个模式，保留顶层 `entity`。

该函数没有就每条 UID 与顶层 UID 做相等核对。它也没有把 `related_context` 自动变为 `direct`：这一点必须保留，不能描述成程序已经把所有旧数据认证为当前对象直接事实。

## 3. 本轮实际执行的隔离观察

通过 `importlib` 从文件加载真实 `observability_projection.py`，直接调用 `project_observability_payload`。没有加载业务应用或连接数据源。

构造输入的关键部分：

```json
{
  "dimension": "logging",
  "status": "query_succeeded",
  "coverage": "present",
  "entity": {"namespace": "ns", "pod": "pod", "pod_uid": "uid-current"},
  "fact_ledger": {
    "scope_entity_ids": ["k8s.pod:ns/pod:uid-current"],
    "records": []
  },
  "facts": [
    {"ref": "old-a", "source_system": "elasticsearch", "pod_uid": "uid-old", "directness": "related_context", "value": "first old log"},
    {"ref": "old-b", "source_system": "elasticsearch", "pod_uid": "uid-old", "directness": "related_context", "value": "second old log"}
  ]
}
```

预算 12,000 字符，实得：

| 阶段 | 记录数及身份 |
|---|---|
| 输入 canonical ledger | 0 条 |
| structured 中保留的 canonical ledger | 0 条 |
| structured evidence | 2 条，均携带 `uid-old` |
| 模型摘要 evidence | 2 条，逐条 UID 被删除；顶层仍为 `uid-current` |
| 模型摘要直接性 | 两条仍为 `related_context` |

输入的简化 ledger 未填全真实合同字段；当前被测选择函数不校验这些字段。MCP 的有效空 ledger 响应形态另有上节源码和既有测试支撑。这里不冒称已运行完整 MCP→Agent 的端到端测试。

**可确认：** 当前投影函数对构造输入存在上述可重复行为；源端过滤与下游兼容选择之间存在值得复核的语义不一致。

**不能确认：** 历史报告曾由此误诊、当前线上加载同一代码、所有后续 RCA 输入都使用这个摘要、正常源查询必然返回旧 UID。后续 canonical ledger 路径仍可能再次排除；`related_context` 也仍提供弱化提示。

## 4. 第一性原理与跨领域对应

“数据集合为空”只描述数量，不能表达产生该集合的处理状态。把已完成过滤的空集合退回原集合，会撤销过滤决定。

跨领域近邻：[Apache Cassandra Tombstones 官方文档](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html)，本轮读取相关全文。

- 分布式副本中，如果删除只留下空白，仍保有旧值的副本可在修复时让数据重新出现，文档称为 zombies。
- 带时间戳的删除标记让其他副本识别删除操作，防止把“空”当作缺少待恢复的数据。
- 标记保留期与修复条件影响何时能够清除标记。

迁移启发：保存的不只是正向记录，还包括“某范围内哪些记录已被排除”的处理结果，使兼容回退或归档恢复不能撤销既有筛选。

重要区别：我们的记录并未物理删除；同一记录可在另一诊断对象范围内合法使用。不能直接永久 tombstone 整条源记录，也不能把 Cassandra 副本协议原样移植后宣称创新。引用的是数据恢复歧义的对应关系，不是其整个数据库一致性机制。

## 5. 可实施的最小处理方法，但目前不作为创新结论

1. **区分处理状态。** 把未提供/未识别结果、已处理为空、已处理非空分开；不单凭列表真值决定旧格式回退。
2. **关联源与范围。** 处理状态绑定源响应版本和诊断对象身份，而不是仅绑定文件名或 Pod 名。
3. **保留排除依据。** 对规则可判定的 UID 冲突等，记录被排除 ID 和原因；预算未展示应标为待展开，不混同为不合格。
4. **下游按状态取数。** 有有效处理结果时，以其范围与合格集合构建输入；旧格式或归档中的记录须重新通过相同资格规则，不能直接补回。
5. **显式处理变化。** 新源版本/新对象范围触发重新判断，而不是无期限继承旧排除；无法验证状态时披露未确认，不能默认为有效或源端无数据。
6. **分开事实资格与分析。** 模型可申请展开或改变合法分析范围，但不能仅凭“信息不足”覆盖源端身份核对。程序检查通过仅表示满足这一资格规则，不表示根因正确。

最简单的工程修正可能只需正确区分有效空结果与缺失结果，并在省略身份时比较源值。它们属于常规防御性处理；不能因为在 Agent 中出现，就视为有创造性。

本轮关于 `language model` 与 `tombstone` 的 FPO 查询连接失败，未取得结果，不能用来宣称此迁移未有公开。这里只形成新的真实问题证据和可执行边界，尚未形成经过近邻对照的创新性方案。

## 6. 对候选选择的影响

暂不优先扩写“模型回读＋局部字典展开”。当前工程已呈现更直接的输入构建问题，源事实根本没有按原有筛选结果进入模型，增加回读模型不是首要处理。

保留本节问题作为下一轮候选筛选依据，而不是宣称“空结果标记”就是专利。若要从中提出新方法，必须比常规状态标记、访问控制、删除标记及按范围重新过滤多出具体且有必要性的处理关系；否则应将它视为工程修正并继续寻找，而不是改个名称凑成申请。

## 7. 续查决定：单纯范围化负结果控制不再作为首选专利方向

### 7.1 RFC 2308 已将负结果、范围、有效期和再次返回连起来

[Negative Caching of DNS Queries，RFC 2308](https://www.rfc-editor.org/rfc/rfc2308.txt)，1998 年 3 月。本轮核读第 5、6、7 节及相邻第 8 节，不声称逐条核验整个 DNS 协议及其更新。

- 第 5 节：负结果需要 TTL；因答案区没有可附 TTL 的记录，用 authority 区的 SOA 承载。有效期归零后不得再次使用该负结果。
- NXDOMAIN 按 `<QNAME, QCLASS>` 缓存；NODATA 按 `<QNAME, QTYPE, QCLASS>` 缓存。即不同负结果绑定不同使用范围，不是无条件否定所有后续问题。
- 没有 SOA 的负结果不应缓存；协议明确讨论转发环路可能让负结果不断重置、永远流转的问题。
- 第 6 节：下游再次返回负缓存时需携带已扣减停留时间的 SOA TTL，不是每次交接都重新生成一个完整寿命。
- 第 7 节：服务器失败和不可达另行处理，不能与不存在结果混为一谈；服务器失败缓存有单独期限和包括服务器地址的键。

这已经提供了“负结果不是空白数据—按原因绑定范围—交接保留其有效性—失效后不得继续复用”的完整成熟机制。

### 7.2 RFC 8198 进一步把负结果用于范围内的新查询

[Aggressive Use of DNSSEC-Validated Cache，RFC 8198](https://www.rfc-editor.org/rfc/rfc8198.txt)，2017 年 7 月。本轮核读摘要、第 5–9 节和附录 A；未逐条精读其所有规范性引用和附录 B。

- 第 5 节：已有缓存信息足以验证查询时可合成回答；不足时必须回到权威 DNS 查询。
- 第 5.1/5.2 节：用匹配或覆盖查询名的 NSEC/NSEC3 记录判断不存在。NSEC3 Opt-Out 情况不能据覆盖就证明不存在。
- 第 5.3 节：通配符合成也有额外前提；对应记录缺失时须回源。
- 第 5.4/9 节：有效期影响新增名称何时可被看到，且过旧负结果可能压制新数据。
- 附录 A：在缓存查找阶段用已验证的否定记录检查覆盖范围，建议有序索引；算法出错时按通常方式解析查询。

所以，“不是只复用完全相同请求，而是根据已有否定依据判断新请求是否仍在排除范围内，必要时回源”也不是新出现的抽象链。

### 7.3 迁移边界与当前判断

DNS 的不存在证明不同于 AIOps 的证据资格：日志旧 UID 不等于日志不存在，预算省略更不等于记录不合格。模型提出的相关性意见也不是 DNSSEC 式可验证证明。不能借用“验证”一词就宣称模型判断获得认证。

不过，DNS 文献加上 Cassandra 的删除标记已经给出很强的跨域组合启发。如果候选只把 key 换成 Pod UID/源版本，把缓存读取换成归档回读，再加一个小模型选择请求，当前没有充分理由认为产生了非显而易见的处理方法。

**研究决定：第 5 节的方法保留为工程基线，不再作为首选专利核心。** 这是基于更接近的公开技术作出的候选降级，不是判定所有 AIOps 范围控制发明均不可授权。已复现的函数边界仍有效，业务代码未修改。

本轮两次 FPO 负缓存/LLM-tombstone 查询及一次简化查询均连接失败，没有新增可核读的专利结果。RFC 是公开非专利资料，本节没有冒称已完成该切口的全面专利查新。
