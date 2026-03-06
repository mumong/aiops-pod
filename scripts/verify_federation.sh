#!/bin/bash
# 联邦查询功能完整验证脚本
# 用途：验证所有代码、配置、部署文件的完整性

set -e

echo "=========================================="
echo "联邦查询功能完整性验证"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((pass_count++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((fail_count++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "1. 验证核心模块文件..."
echo "-----------------------------------"

files=(
    "app/core/federation/__init__.py"
    "app/core/federation/registry.py"
    "app/core/federation/client.py"
    "app/core/federation/aggregator.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "文件存在: $file"
    else
        check_fail "文件缺失: $file"
    fi
done

echo ""
echo "2. 验证集成改动..."
echo "-----------------------------------"

# 检查 config_loader.py 是否排除 federation
if grep -q '"federation"' app/core/holmes/config_loader.py; then
    check_pass "config_loader.py 已排除 federation 字段"
else
    check_fail "config_loader.py 未排除 federation 字段"
fi

# 检查 service.py 是否导入 federation
if grep -q "from app.core.federation import" app/core/service.py; then
    check_pass "service.py 已导入 federation 模块"
else
    check_fail "service.py 未导入 federation 模块"
fi

# 检查 routes.py 是否有 federation 路由
if grep -q "/federation/ask" app/api/routes.py; then
    check_pass "routes.py 已添加 /federation/ask 路由"
else
    check_fail "routes.py 未添加 /federation/ask 路由"
fi

echo ""
echo "3. 验证配置文件..."
echo "-----------------------------------"

# 检查本地配置
if grep -q "federation:" config/config.yaml; then
    check_pass "config/config.yaml 包含 federation 配置"
else
    check_fail "config/config.yaml 缺少 federation 配置"
fi

# 检查 K8s ConfigMap
if grep -q "federation:" deploy/configmap/config.yaml; then
    check_pass "deploy/configmap/config.yaml 包含 federation 配置"
else
    check_fail "deploy/configmap/config.yaml 缺少 federation 配置"
fi

echo ""
echo "4. 验证部署文件..."
echo "-----------------------------------"

deploy_files=(
    "deploy/k8s-simple.yaml"
    "deploy/rbac.yaml"
    "deploy/configmap/config.yaml"
    "deploy/configmap/runbooks.yaml"
)

for file in "${deploy_files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "部署文件存在: $file"
    else
        check_fail "部署文件缺失: $file"
    fi
done

echo ""
echo "5. 验证文档..."
echo "-----------------------------------"

docs=(
    "docs/FEDERATION.md"
    "docs/FEDERATION_SUMMARY.md"
    "test/test_federation_real.py"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "文档存在: $doc"
    else
        check_fail "文档缺失: $doc"
    fi
done

echo ""
echo "6. Python 模块导入测试..."
echo "-----------------------------------"

if .venv/bin/python -c "from app.core.federation import FederationCoordinator; print('OK')" 2>/dev/null | grep -q "OK"; then
    check_pass "federation 模块可正常导入"
else
    check_fail "federation 模块导入失败"
fi

echo ""
echo "=========================================="
echo "验证结果汇总"
echo "=========================================="
echo -e "通过: ${GREEN}${pass_count}${NC}"
echo -e "失败: ${RED}${fail_count}${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 发现 $fail_count 个问题，请修复后重试${NC}"
    exit 1
fi
