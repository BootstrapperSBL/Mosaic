#!/bin/bash

# Mosaic 开发环境启动脚本

echo "🚀 启动 Mosaic 开发环境..."
echo ""

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 错误: 请在项目根目录下运行此脚本"
    exit 1
fi

# 启动后端
echo "📦 启动后端服务..."
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

sleep 3

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务启动成功: http://localhost:8000"
    echo "   API 文档: http://localhost:8000/docs"
else
    echo "❌ 后端服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""

# 启动前端
echo "🎨 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

sleep 10

# 检查前端是否启动成功
if curl -s -I http://localhost:3000 > /dev/null; then
    echo "✅ 前端服务启动成功: http://localhost:3000"
else
    echo "⚠️  前端服务可能需要更多时间启动"
fi

echo ""
echo "✨ Mosaic 开发环境已就绪！"
echo ""
echo "📊 访问地址："
echo "   - 前端: http://localhost:3000"
echo "   - 后端: http://localhost:8000"
echo "   - API 文档: http://localhost:8000/docs"
echo ""
echo "⏹️  停止服务："
echo "   按 Ctrl+C 或运行: kill $BACKEND_PID $FRONTEND_PID"
echo ""

# 保存 PID 到文件
echo "$BACKEND_PID $FRONTEND_PID" > .dev-pids

# 等待用户中断
wait
