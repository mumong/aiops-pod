# L0 Pod 存储卷超限被驱逐 (Volume Limit Exceeded)

> **层级**: L0 - 基础设施层 | **类型**: procedure | **场景ID**: L0-VolumeLimit

---

## 1. 场景识别特征

### 1.1 触发关键词
| 类别 | 关键词 |
|------|--------|
| 中文 | 磁盘满、磁盘空间不足、写入失败、空间耗尽、存储卷超限、被驱逐 |
| 英文 | disk full, no space left, ENOSPC, disk pressure, Evicted, volume limit, emptyDir, sizeLimit, ephemeral-storage |
| 指标 | node_disk_utilization > 95%, Use% >= 95 |

### 1.2 快速判定
```
IF (Pod Status = Evicted) AND (Message 包含 "exceeds the limit" 或 "emptyDir"):
    场景 = L0-VolumeLimit, 置信度 = 高
IF (df -h 显示 Use% >= 95%) OR (日志包含 ENOSPC):
    场景 = L0-DiskFull, 置信度 = 高
```

## 2. 证据清单

| # | 证据项 | 级别 | 采集命令 | 判定依据 |
|---|--------|------|----------|----------|
| E1 | 磁盘使用率 | Critical | `df -h` | Use% >= 95% |
| E2 | Inode 使用率 | Critical | `df -i` | IUse% >= 95% |
| E3 | Top 占用目录 | Important | `du -sh /var/log/* | sort -hr | head` | 定位写满点 |
| E4 | Top 大文件 | Important | `find /var/log -size +100M` | 定位具体文件 |
| E5 | 删未释放 | Optional | `lsof +L1 | grep deleted` | 句柄泄漏 |

## 3. 固定取证流程

```bash
# Step 1: 确认磁盘状态
df -h && df -i

# Step 2: 定位 Top 占用目录
du -sh /var/log/* 2>/dev/null | sort -hr | head -20

# Step 3: 定位大文件
find /var/log -type f -size +100M -exec ls -lh {} \; 2>/dev/null | head -20

# Step 4: 检查删未释放
lsof +L1 2>/dev/null | grep deleted | head -30
```

## 4. 判定规则

| 规则ID | 条件 | 结论 | 置信度 |
|--------|------|------|--------|
| R-L0-DISK-1 | Use% >= 95% 或 ENOSPC | DiskFull(Block) | 高 |
| R-L0-DISK-2 | IUse% >= 95% 且 Use% 正常 | DiskFull(Inode) | 高 |
| R-L0-DISK-3 | lsof 显示大 deleted 文件 | 句柄泄漏 | 中 |

## 5. 修复方案

### 立即止血
```bash
truncate -s 0 /var/log/xxx.log  # 优先 truncate，保留句柄
df -h  # 确认释放
```

### 根治（需审批）
- 配置 logrotate 日志轮转
- 重启占用 deleted 文件的进程

### 禁止操作
- ❌ `rm -rf /var/log/*`
- ❌ `rm -rf /var/lib/docker/*`
