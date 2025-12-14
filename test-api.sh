#!/bin/bash

# Mosaic API 测试脚本

echo "🧪 测试 Mosaic API..."
echo ""

BASE_URL="http://localhost:8000"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 测试函数
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local expected_code=$4

    echo -n "测试 $name ... "

    if [ "$method" = "GET" ]; then
        status_code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    else
        status_code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BASE_URL$endpoint")
    fi

    if [ "$status_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ 通过${NC} (HTTP $status_code)"
    else
        echo -e "${RED}✗ 失败${NC} (预期 $expected_code, 实际 $status_code)"
    fi
}

# 基础端点测试
echo "📍 基础端点"
test_endpoint "根路径" "GET" "/" "200"
test_endpoint "健康检查" "GET" "/health" "200"
test_endpoint "API 文档" "GET" "/docs" "200"

echo ""
echo "🔐 认证端点（需要请求体，预期返回 422）"
test_endpoint "注册" "POST" "/api/auth/signup" "422"
test_endpoint "登录" "POST" "/api/auth/signin" "422"

echo ""
echo "📤 上传端点（需要认证，预期返回 401）"
test_endpoint "上传图片" "POST" "/api/upload/image" "401"
test_endpoint "上传URL" "POST" "/api/upload/url" "401"
test_endpoint "上传文本" "POST" "/api/upload/text" "401"

echo ""
echo "🔍 分析端点（需要认证，预期返回 401）"
test_endpoint "开始分析" "POST" "/api/analysis/analyze" "401"

echo ""
echo "📊 推荐端点（需要认证和参数）"
test_endpoint "获取推荐" "GET" "/api/recommendations/analysis/test-id" "401"

echo ""
echo "📜 历史端点（需要认证）"
test_endpoint "历史记录" "GET" "/api/history/" "401"

echo ""
echo "✅ API 基础测试完成！"
echo ""
echo "💡 提示："
echo "   - 所有需要认证的端点返回 401 是正常的"
echo "   - 需要请求体的端点返回 422 是正常的"
echo "   - 完整功能测试请访问前端页面进行操作"
echo ""
echo "🌐 访问地址："
echo "   - API 文档: http://localhost:8000/docs"
echo "   - 前端页面: http://localhost:3000"
