## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，容器 app 无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-b7e3d5bca11b) | `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 直接证明镜像域名无效导致 DNS 解析失败，为根因提供核心事实支撑 |
| 2 | K8s State | kubernetes (fact-25dbb755157f) | `container.waiting_reason`: `ImagePullBackOff` | 确证当前 Pod 处于镜像拉取失败并退避的状态 |
| 3 | K8s State | kubernetes (fact-5745c3c3b232) | `pod.status`: `Pending` | 表明 Pod 尚未成功调度至容器运行阶段，符合启动受阻表现 |
| 4 | Metric | prometheus (fact-b9a4306cded8) | `kube_pod_container_status_waiting_reason` 在 `ImagePullBackOff` 维度下值为 `1` | 独立于 K8s 事件，通过遥测数据再次确证容器等待原因为拉取失败 |
| 5 | K8s Config | kubernetes (fact-51daa7e67d73) | `container.waiting_message`: `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 揭示配置的具体镜像地址包含无效域名，指明配置错误源 |

K8s 事件与遥测 Metric 在 `ImagePullBackOff` 状态上保持一致，证实状态未处于瞬时波动；K8s 状态与配置事实结合，明确指向 `registry.invalid` 这一具体镜像地址为引发拉取失败的配置缺陷，事件中的 `no such host` 彻底排除了镜像不存在等其他网络/认证错误。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了无效的镜像域名 (registry.invalid) → DNS 解析失败 (no such host) → 镜像拉取失败并进入退避 (ImagePullBackOff) → Pod 处于 Pending 状态且容器未启动
```

### 根因结论

已确认的根因是 Pod `workload-65b7f54794-rnlv4` 的容器 `app` 配置了无效的镜像仓库域名 `registry.invalid`。这导致 Kubelet 在执行拉取操作时发生 DNS 解析失败（证据 #1, #5），进而触发镜像拉取失败并持续尝试（退避），使 Pod 维持在 `Pending` 状态（证据 #2, #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.2m
├─ 问题定位: 19.9s
├─ 并发证据采集: 522.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 522.2s (Evidence 54.8s, RCA 467.3s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
