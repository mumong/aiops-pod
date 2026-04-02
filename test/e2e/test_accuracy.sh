#!/usr/bin/env bash
# ============================================================================
# AIOps Copilot 准确率测试工具
#
# 用法:
#   ./test_accuracy.sh [并发数] [服务地址] [问题]
#
# 示例:
#   ./test_accuracy.sh 3                                    # 3 次并发测试
#   ./test_accuracy.sh 100                                  # 100 次并发测试
#   ./test_accuracy.sh 100 http://10.2.0.48:30800           # 指定地址
#   ./test_accuracy.sh 100 http://10.2.0.48:30800 "集群有什么问题"  # 指定问题
# ============================================================================

set -euo pipefail

CONCURRENCY=${1:-100}
BASE_URL=${2:-"http://10.2.0.48:30800"}
QUESTION=${3:-"我的集群有什么问题？"}
RESULT_DIR="testreports/$(date +%Y%m%d_%H%M%S)"

mkdir -p "$RESULT_DIR"

echo "============================================"
echo "  AIOps Copilot 准确率测试"
echo "============================================"
echo "并发数:   $CONCURRENCY"
echo "服务地址: $BASE_URL"
echo "问题:     $QUESTION"
echo "结果目录: $RESULT_DIR"
echo "============================================"
echo ""

# 先检查服务是否可用
if ! curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
    echo "❌ 服务不可用: ${BASE_URL}/health"
    exit 1
fi
echo "✅ 服务健康检查通过"
echo ""

# 记录测试开始前的 reports 文件列表（用于后续过滤）
BEFORE_FILE="$RESULT_DIR/_before_reports.txt"
curl -sf "${BASE_URL}/reports?limit=9999" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('reports', []):
    print(r['filename'])
" > "$BEFORE_FILE" 2>/dev/null || touch "$BEFORE_FILE"

echo "📡 开始并发 $CONCURRENCY 次请求..."
START_TIME=$(date +%s)

# 并发执行请求，每个请求保存到独立文件
for i in $(seq 1 "$CONCURRENCY"); do
    (
        # stream=false 避免流式输出，直接拿最终结果
        HTTP_CODE=$(curl -s -o "$RESULT_DIR/response_${i}.txt" -w "%{http_code}" \
            -G "${BASE_URL}/ask" \
            --data-urlencode "q=${QUESTION}" \
            --data-urlencode "stream=false" \
            --data-urlencode "max_steps=20" \
            --max-time 600 2>/dev/null || echo "000")

        if [ "$HTTP_CODE" = "200" ]; then
            echo "  ✅ #${i} 完成 (HTTP ${HTTP_CODE})"
        else
            echo "  ❌ #${i} 失败 (HTTP ${HTTP_CODE})"
        fi
    ) &
done

# 等待所有后台任务完成
wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "⏱️  全部完成，耗时 ${ELAPSED}s"
echo ""

# 等待 2s 让服务端写完报告文件
sleep 2

# ============================================================================
# 统计方式一：从 /reports API 获取新增报告（需要部署新版本）
# ============================================================================
AFTER_FILE="$RESULT_DIR/_after_reports.txt"
curl -sf "${BASE_URL}/reports?limit=9999" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('reports', []):
    print(r['filename'])
" > "$AFTER_FILE" 2>/dev/null || touch "$AFTER_FILE"

NEW_REPORTS="$RESULT_DIR/_new_reports.txt"
comm -13 <(sort "$BEFORE_FILE") <(sort "$AFTER_FILE") > "$NEW_REPORTS"
NEW_COUNT=$(wc -l < "$NEW_REPORTS")

# ============================================================================
# 统计方式二：从响应内容中提取层级（兼容旧版本）
# 匹配 "## 📊 性能统计" 前面的节点输出中的层级，或从内容关键词推断
# ============================================================================
RESPONSE_LAYERS="$RESULT_DIR/_response_layers.txt"
> "$RESPONSE_LAYERS"

SUCCESS_COUNT=0
FAIL_COUNT=0
for f in "$RESULT_DIR"/response_*.txt; do
    [ -f "$f" ] || continue
    # 检查是否有实际内容（非空且非错误）
    if [ ! -s "$f" ] || grep -q '"detail"' "$f" 2>/dev/null; then
        FAIL_COUNT=$((FAIL_COUNT + 1))
        echo "FAILED" >> "$RESPONSE_LAYERS"
        continue
    fi
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))

    # 尝试从性能统计块前的节点输出提取层级
    # 工作流模式会输出 "[问题定位] 结果" 包含层级信息
    LAYER=$(python3 -c "
import sys, re
text = open('$f', encoding='utf-8').read()

# 方法1: 从报告文件名提取（新版本）
m = re.search(r'报告已保存.*?/(L[0-4]|QUERY)-', text)
if m:
    print(m.group(1)); sys.exit()

# 方法2: 从工作流节点输出提取层级判定
m = re.search(r'定位.*?层[级]?.*?(L[0-4]|QUERY)', text, re.IGNORECASE)
if m:
    print(m.group(1)); sys.exit()

# 方法3: 从内容关键词推断
keywords = {
    'L0': ['磁盘', '内存不足', 'CPU 过高', '文件系统', '内核', 'OOM', 'disk'],
    'L1': ['节点', 'NotReady', 'kubelet', '调度', 'node', 'taint'],
    'L2': ['Pod', 'CrashLoop', '重启', '镜像', 'OOMKilled', '驱逐', 'Evicted', 'pending', 'backoff'],
    'L3': ['Service', 'Ingress', 'DNS', 'NetworkPolicy', '网络', '连接'],
    'L4': ['应用', '业务', '配置错误', '依赖', '503', '500'],
}
scores = {}
lower = text.lower()
for layer, kws in keywords.items():
    scores[layer] = sum(1 for kw in kws if kw.lower() in lower)
if any(scores.values()):
    best = max(scores, key=scores.get)
    print(best)
else:
    print('UNKNOWN')
" 2>/dev/null || echo "UNKNOWN")
    echo "$LAYER" >> "$RESPONSE_LAYERS"
done
echo "============================================"
echo "  测试结果统计"
echo "============================================"
echo "总请求数:     $CONCURRENCY"
echo "成功:         $SUCCESS_COUNT"
echo "失败:         $FAIL_COUNT"
echo "耗时:         ${ELAPSED}s"
echo ""

# 优先用 /reports API 统计（新版本），否则用响应内容推断
if [ "$NEW_COUNT" -gt 0 ]; then
    echo "📊 层级分布（来源: /reports API 报告文件名）:"
    STAT_SOURCE="$NEW_REPORTS"
    STAT_TOTAL="$NEW_COUNT"
    EXTRACT_CMD="awk -F'-' '{print \$1}'"
else
    echo "📊 层级分布（来源: 响应内容关键词推断）:"
    STAT_SOURCE="$RESPONSE_LAYERS"
    STAT_TOTAL="$SUCCESS_COUNT"
    EXTRACT_CMD="cat"
fi

echo "--------------------------------------------"
printf "| %-7s | %-5s | %-6s |\n" "层级" "次数" "占比"
echo "|---------|-------|--------|"

eval "$EXTRACT_CMD" "$STAT_SOURCE" | sort | uniq -c | sort -rn | while read count layer; do
    if [ "$STAT_TOTAL" -gt 0 ]; then
        pct=$(echo "scale=1; $count * 100 / $STAT_TOTAL" | bc)
    else
        pct="0.0"
    fi
    printf "| %-7s | %-5s | %-6s |\n" "$layer" "$count" "${pct}%"
done

echo "--------------------------------------------"
echo ""

# 保存统计结果
STATS_FILE="$RESULT_DIR/stats.txt"
{
    echo "测试时间: $(date)"
    echo "并发数: $CONCURRENCY"
    echo "问题: $QUESTION"
    echo "服务: $BASE_URL"
    echo "耗时: ${ELAPSED}s"
    echo "成功: $SUCCESS_COUNT / $CONCURRENCY"
    echo ""
    echo "层级分布（响应内容推断）:"
    sort "$RESPONSE_LAYERS" | uniq -c | sort -rn
    if [ "$NEW_COUNT" -gt 0 ]; then
        echo ""
        echo "层级分布（报告文件名）:"
        awk -F'-' '{print $1}' "$NEW_REPORTS" | sort | uniq -c | sort -rn
    fi
} > "$STATS_FILE"

echo "📁 详细结果保存在: $RESULT_DIR/"
echo "   - stats.txt              统计摘要"
echo "   - _response_layers.txt   每次请求推断的层级"
echo "   - _new_reports.txt       新增的报告文件名（需新版本）"
echo "   - response_N.txt         每次请求的原始响应"
