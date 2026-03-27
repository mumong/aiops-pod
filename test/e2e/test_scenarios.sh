#!/usr/bin/env bash
# ==========================================================================
# E2E 自动化验收脚本
# 
# 功能：
# 1. 调用 AIOps API 发起诊断请求
# 2. 解析 SSE 响应，验证 deterministic_decision 事件
# 3. 输出验收结果报告
# ==========================================================================

set -euo pipefail

# 配置
AIOPS_ENDPOINT="${AIOPS_ENDPOINT:-http://localhost:30800}"
NS="aiops-e2e"
TIMEOUT=120
PASSED=0
FAILED=0

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }
log_pass()  { echo -e "${GREEN}[PASS]${NC} $1"; PASSED=$((PASSED+1)); }
log_fail()  { echo -e "${RED}[FAIL]${NC} $1"; FAILED=$((FAILED+1)); }

# ==========================================================================
# 辅助函数
# ==========================================================================

call_aiops() {
    local query="$1"
    local output_file=$(mktemp)
    
    log_info "发起诊断请求: ${query:0:60}..."
    
    # 调用 API，超时 120 秒
    curl -sS -N -G "${AIOPS_ENDPOINT}/ask" \
        --data-urlencode "q=${query}" \
        --data-urlencode "format=sse" \
        --max-time "${TIMEOUT}" \
        > "${output_file}" 2>&1 || true
    
    echo "${output_file}"
}

check_event() {
    local file="$1"
    local event_type="$2"
    
    grep -q "event: ${event_type}" "${file}" 2>/dev/null
}

extract_deterministic_decision() {
    local file="$1"
    
    # 提取 deterministic_decision 事件的 data
    grep -A1 "event: deterministic_decision" "${file}" 2>/dev/null | grep "data:" | sed 's/data: //'
}

extract_final_answer() {
    local file="$1"
    
    # 提取 final 事件的 answer 字段
    grep -A1 "event: final" "${file}" 2>/dev/null | grep "data:" | sed 's/data: //'
}

validate_scenario() {
    local scenario="$1"
    local query="$2"
    local expected_layer="$3"
    local expected_category="$4"
    
    echo ""
    echo "=========================================="
    echo "测试场景: ${scenario}"
    echo "=========================================="
    
    local result_file=$(call_aiops "${query}")
    
    # 检查 1: final 事件存在
    if check_event "${result_file}" "final"; then
        log_pass "[${scenario}] final 事件存在"
    else
        log_fail "[${scenario}] 未收到 final 事件"
        rm -f "${result_file}"
        return 1
    fi
    
    # 检查 2: deterministic_decision 事件
    if check_event "${result_file}" "deterministic_decision"; then
        log_pass "[${scenario}] deterministic_decision 事件存在"
        
        # 提取并验证内容
        local decision=$(extract_deterministic_decision "${result_file}")
        
        # 检查 layer
        if echo "${decision}" | grep -q "\"layer\":.*\"${expected_layer}\""; then
            log_pass "[${scenario}] 层级判定正确: ${expected_layer}"
        else
            log_fail "[${scenario}] 层级判定错误，期望: ${expected_layer}"
        fi
        
        # 检查 category
        if echo "${decision}" | grep -qi "${expected_category}"; then
            log_pass "[${scenario}] 分类判定正确: ${expected_category}"
        else
            log_warn "[${scenario}] 分类判定可能不匹配，期望: ${expected_category}"
        fi
        
        # 检查 confidence
        if echo "${decision}" | grep -q "\"confidence\":"; then
            log_pass "[${scenario}] 置信度字段存在"
        else
            log_warn "[${scenario}] 置信度字段缺失"
        fi
    else
        log_warn "[${scenario}] 未收到 deterministic_decision 事件（可能规则未匹配）"
    fi
    
    # 检查 3: 证据链表格
    local final_answer=$(extract_final_answer "${result_file}")
    if echo "${final_answer}" | grep -qi "证据"; then
        log_pass "[${scenario}] 最终答案包含证据相关内容"
    else
        log_warn "[${scenario}] 最终答案可能缺少证据链"
    fi
    
    # 清理
    rm -f "${result_file}"
    
    echo ""
}

# ==========================================================================
# 测试用例
# ==========================================================================

run_all_tests() {
    echo ""
    echo "============================================================"
    echo "  K8s-SRE Agent E2E 验收测试"
    echo "  Endpoint: ${AIOPS_ENDPOINT}"
    echo "  Namespace: ${NS}"
    echo "============================================================"
    echo ""
    
    # 检查 API 可用性
    log_info "检查 AIOps API 可用性..."
    if curl -s "${AIOPS_ENDPOINT}/health" | grep -q "healthy"; then
        log_pass "AIOps API 健康检查通过"
    else
        log_error "AIOps API 不可用，请检查服务是否启动"
        exit 1
    fi
    
    # --------------------------------
    # L2: OOMKilled
    # --------------------------------
    POD_OOM="$(kubectl -n "${NS}" get pod -l app=memhog -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo '')"
    if [[ -n "${POD_OOM}" ]]; then
        validate_scenario \
            "L2-OOMKilled" \
            "namespace=${NS} pod=${POD_OOM} 一直重启 OOMKilled 排查" \
            "L2" \
            "OOMKilled"
    else
        log_warn "跳过 L2 测试：memhog Pod 不存在"
    fi
    
    # --------------------------------
    # L4: App Health Fail
    # --------------------------------
    if kubectl -n "${NS}" get deploy apphealth &>/dev/null; then
        validate_scenario \
            "L4-AppHealthFail" \
            "namespace=${NS} 应用 apphealth 健康检查失败 日志有 L4_APP_HEALTH_FAIL" \
            "L4" \
            "AppHealthFail"
    else
        log_warn "跳过 L4 测试：apphealth Deployment 不存在"
    fi

    # --------------------------------
    # L1: Node Taint
    # --------------------------------
    echo "准备 L1 场景：应用 Node Taint..."
    kubectl apply -f manifests/l1-taint-node.yaml 2>/dev/null || log_warn "L1 Taint 注入失败"

    # --------------------------------
    # L0: DiskFull (ENOSPC simulation)
    # --------------------------------
    if kubectl -n "${NS}" get deploy logfill &>/dev/null; then
        validate_scenario \
            "L0-DiskFull" \
            "namespace=${NS} Pod logfill 日志写入失败 no space left on device ENOSPC" \
            "L0" \
            "DiskFull"
    else
        log_warn "跳过 L0 测试：logfill Deployment 不存在"
    fi
    
    # --------------------------------
    # L3: ImagePullBackOff
    # --------------------------------
    if kubectl -n "${NS}" get pod imagepull-fail-victim &>/dev/null; then
        validate_scenario \
            "L3-ImagePullFailed" \
            "namespace=${NS} Pod imagepull-fail-victim 镜像拉取失败 ImagePullBackOff" \
            "L3" \
            "ImagePull"
    else
        log_warn "跳过 L3 测试：imagepull-fail-victim Pod 不存在"
    fi

    # --------------------------------
    # L1: Node Taint (NotReady simulation)
    # --------------------------------
    if kubectl -n "${NS}" get nodes &>/dev/null; then
        validate_scenario \
            "L1-TaintNode" \
            "namespace=${NS} 节点 NotReady (Taint 导致) 调度器不向此节点调度 Pod，kubectl get nodes 直接可见" \
            "L1" \
            "TaintNode"
    else
        log_warn "跳过 L1 测试：没有可用节点"
    fi

    # --------------------------------
    # 输出总结
    # --------------------------------
    echo ""
    echo "============================================================"
    echo "  验收结果汇总"
    echo "============================================================"
    echo -e "  ${GREEN}通过${NC}: ${PASSED}"
    echo -e "  ${RED}失败${NC}: ${FAILED}"
    echo ""
    
    if [[ ${FAILED} -gt 0 ]]; then
        log_error "存在失败的测试用例"
        exit 1
    else
        log_pass "所有测试用例通过"
        exit 0
    fi
}

# ==========================================================================
# 主入口
# ==========================================================================

case "${1:-all}" in
    all)
        run_all_tests
        ;;
    l0)
        validate_scenario "L0-DiskFull" "Pod logfill 日志写入失败 ENOSPC" "L0" "DiskFull"
        ;;
    l1)
        validate_scenario "L1-TaintNode" "节点有 taint 不可调度" "L1" "TaintNode"
        ;;
    l2)
        validate_scenario "L2-OOMKilled" "Pod OOMKilled 排查" "L2" "OOMKilled"
        ;;
    l3)
        validate_scenario "L3-ImagePullFailed" "镜像拉取失败 ImagePullBackOff" "L3" "ImagePull"
        ;;
    l4)
        validate_scenario "L4-AppHealthFail" "应用健康检查失败 L4_APP_HEALTH_FAIL" "L4" "AppHealthFail"
        ;;
    *)
        echo "Usage: $0 [all|l0|l1|l2|l3|l4]"
        exit 1
        ;;
esac
