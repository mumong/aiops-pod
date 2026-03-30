# QUERY 模式快速查询参考手册

> **类型**: reference | **适用**: 数据查询、指标获取、状态检查

---

## 1. 基础：节点与 IP 映射

查询任何指标前，**必须先建立节点名称与 IP 的映射关系**：

```bash
kubectl get nodes -o wide
```

典型输出：
```
NAME     STATUS   ROLES           INTERNAL-IP
master   Ready    control-plane   10.2.0.48
node1    Ready    <none>          10.2.0.49
node2    Ready    <none>          10.2.0.50
```

Prometheus 的 `instance` label 格式为 `IP:9100`（如 `10.2.0.48:9100`），**不是节点名称**。
映射关系：`master = 10.2.0.48:9100`，`node1 = 10.2.0.49:9100`，`node2 = 10.2.0.50:9100`。

---

## 2. PromQL Label 使用规则

**核心原则：不要假设 label 存在，先查确认。**

```promql
# 先查原始指标，看返回了哪些 label
node_memory_MemTotal_bytes
```

从返回结果的 `metric` 字段中确认实际存在的 label key，再构造精确查询。

常见错误：
- ❌ `{node="master"}` — node-exporter 通常没有 `node` label
- ❌ `{kubernetes_io_hostname="master"}` — 通常不存在
- ✅ `{instance="10.2.0.48:9100"}` — 用 instance label
- ✅ `by (instance)` — 按 instance 分组

---

## 3. 常见指标查询

### CPU 使用率
```promql
# 集群总体
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 按节点
(1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)) * 100
```

### 内存使用率
```promql
# 集群总体
(1 - sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes)) * 100

# 按节点
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# 各节点总内存
node_memory_MemTotal_bytes

# 各节点可用内存
node_memory_MemAvailable_bytes
```

### 磁盘使用率
```promql
# 根分区
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100

# 所有挂载点
(1 - node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes) * 100
```

### 网络
```promql
# 网络接收速率（bytes/s）
rate(node_network_receive_bytes_total{device!~"lo|veth.*|cali.*|flannel.*"}[5m])

# 网络发送速率
rate(node_network_transmit_bytes_total{device!~"lo|veth.*|cali.*|flannel.*"}[5m])
```

### Pod 资源
```promql
# Pod CPU
sum(rate(container_cpu_usage_seconds_total{container!="", container!="POD"}[5m])) by (pod, namespace)

# Pod 内存
sum(container_memory_working_set_bytes{container!="", container!="POD"}) by (pod, namespace)
```

---

## 4. 数据验证规则

查询到数据后，**必须进行以下验证**：

### 4.1 节点数量验证
- `kubectl get nodes` 返回 N 个节点
- Prometheus 按节点查询应返回 <= N 条结果
- 如果返回数量 < N，说明部分节点缺少监控，需标注

### 4.2 数值合理性验证
- 内存总量：服务器通常 8GB/16GB/32GB/64GB/128GB，不会是奇怪的数字
- CPU 使用率：0-100% 范围，超过 100% 说明查询有误
- 磁盘使用率：0-100% 范围

### 4.3 交叉验证
当 Prometheus 数据存疑时，用系统命令验证：
```bash
# 内存验证
free -h

# CPU 核心数验证
nproc

# 磁盘验证
df -h
```

### 4.4 单位转换参考
- 1 GB = 1,073,741,824 bytes（GiB）或 1,000,000,000 bytes（GB）
- Prometheus 返回的 bytes 值除以 1024^3 得到 GiB
- `free -h` 显示的是 GiB

---

## 5. 输出格式

查询结果必须以表格形式展示，包含：
- 节点名称（不是 IP）
- 具体数值（带单位）
- 数据来源

示例：
```
| 节点 | 总内存 | 可用内存 | 使用率 | 数据来源 |
|------|--------|----------|--------|----------|
| master (10.2.0.48) | 31.34 GB | 21.63 GB | 31.0% | Prometheus |
| node1 (10.2.0.49) | 31.34 GB | 24.58 GB | 26.9% | Prometheus |
| node2 (10.2.0.50) | 无数据 | 无数据 | - | node-exporter 未部署 |
```
