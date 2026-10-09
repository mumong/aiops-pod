# Query 提示词备份

`query_collect_20261009.txt` 保留精简前的完整常量定义，仅用于参考，不在运行时加载。

在仓库根目录恢复（只修改 Query 常量，不回滚其他提示词和代码）：

```bash
git apply --check docs/prompt_backups/restore_query_collect_20261009.patch
git apply docs/prompt_backups/restore_query_collect_20261009.patch
```

若之后修改了这个常量，检查可能失败；请人工对照备份，不使用强制覆盖。恢复源码后还需重新构建、部署才能影响线上。
