# Mosaic 快速启动指南

## 📋 部署检查清单

在开始之前，请确认：

- [ ] Python 3.12+ 已安装
- [ ] Node.js 18+ 已安装
- [ ] 已有 Supabase 账号
- [ ] 已在 Supabase 执行了数据库脚本

## 🚀 启动步骤

### 步骤 1: 设置 Supabase 数据库（首次使用必须）

1. 登录 Supabase Dashboard: https://app.supabase.com/
2. 选择项目 ID: `yddhnfecjfumxqreiwze`
3. 点击左侧 "SQL Editor"
4. 点击 "New Query"
5. 复制 `backend/database/schema.sql` 的**全部内容**
6. 粘贴到编辑器并点击 "Run"
7. 确认所有表创建成功

**验证**: 执行以下 SQL 应该返回 6 个表

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('user_profiles', 'uploads', 'analyses', 'recommendations', 'user_preferences', 'async_tasks');
```

### 步骤 2: 启动后端

打开**第一个终端**：

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（首次）
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖（首次或更新后）
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**验证**: 访问 http://localhost:8000/docs 应该看到 API 文档

### 步骤 3: 启动前端

打开**第二个终端**：

```bash
# 进入前端目录
cd frontend

# 安装依赖（首次或更新后）
npm install

# 启动开发服务器
npm run dev
```

**验证**: 访问 http://localhost:3000 应该看到登录页面

## ✅ 验证部署

### 后端检查

```bash
# 健康检查
curl http://localhost:8000/health

# 应返回: {"status":"healthy"}
```

### 前端检查

1. 访问 http://localhost:3000
2. 应自动跳转到登录页面
3. 界面显示正常，无报错

## 🧪 功能测试

### 1. 用户注册

1. 访问 http://localhost:3000/auth/signup
2. 填写邮箱和密码（至少6位）
3. 点击注册

**注意**: Supabase 默认需要邮箱验证，测试时可在 Supabase Dashboard -> Authentication -> Settings 中禁用邮箱验证。

### 2. 用户登录

1. 使用注册的邮箱和密码登录
2. 成功后跳转到 `/dashboard`

### 3. 上传测试

#### 测试文本上传：

1. 选择"文本"标签
2. 输入测试文本：
   ```
   我最近对手冲咖啡很感兴趣，想了解不同产区的咖啡豆风味特点，
   以及如何选择合适的研磨度和水温。
   ```
3. 点击提交
4. 等待分析进度条（约30-60秒）
5. 查看生成的推荐内容

#### 测试 URL 上传：

1. 选择"URL"标签
2. 输入测试 URL：`https://www.example.com`
3. 点击提交并等待分析

#### 测试图片上传：

1. 选择"图片"标签
2. 拖拽一张图片或点击选择文件
3. 等待分析完成

### 4. 反馈测试

1. 在推荐卡片上点击"👍 保留"或"👎 丢弃"
2. 观察推荐列表是否实时更新
3. 刷新页面，反馈状态应该保持

### 5. 历史记录测试

1. 点击顶部导航的"历史记录"
2. 应该看到时间线展示的所有上传记录
3. 点击"查看推荐"可以返回查看历史推荐
4. 测试删除功能

## ⚠️ 常见问题排查

### 问题 1: 后端启动失败

**错误**: `ModuleNotFoundError`

**解决**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 问题 2: 前端启动失败

**错误**: `Module not found`

**解决**:
```bash
rm -rf node_modules package-lock.json
npm install
```

### 问题 3: Supabase 连接失败

**错误**: `Unable to connect to Supabase`

**检查**:
1. `.env` 文件中的 `SUPABASE_URL` 和 `SUPABASE_KEY` 是否正确
2. 网络连接是否正常
3. Supabase 项目是否暂停

### 问题 4: AI 分析失败

**错误**: 任务状态显示 `failed`

**检查**:
1. 后端日志中的详细错误信息
2. DeepSeek API Key 是否有效
3. API 配额是否充足

**查看后端日志**: 在后端终端查看详细错误信息

### 问题 5: 搜索功能不可用

**错误**: 推荐内容为默认 Google 搜索链接

**原因**: 未配置 Tavily 或 Serper API Key

**解决**:
1. 获取 Tavily API Key: https://tavily.com/
2. 或获取 Serper API Key: https://serper.dev/
3. 在 `backend/.env` 中配置：
   ```
   TAVILY_API_KEY=your_key_here
   # 或
   SERPER_API_KEY=your_key_here
   SEARCH_PROVIDER=tavily  # 或 serper
   ```
4. 重启后端服务

### 问题 6: 图片上传失败

**错误**: Storage upload failed

**检查**:
1. Supabase Storage 中是否已创建 `uploads` bucket
2. Bucket 是否设置为 Public
3. RLS 策略是否正确配置

**手动创建 Bucket**:
1. Supabase Dashboard -> Storage
2. Create bucket: `uploads`
3. Make it public

### 问题 7: 认证失败

**错误**: `401 Unauthorized`

**检查**:
1. 是否已注册用户
2. Token 是否过期（重新登录）
3. Supabase Auth 是否启用

## 🔧 开发调试

### 查看后端日志

后端终端会实时显示所有日志，包括：
- API 请求
- AI 调用状态
- 错误堆栈

### 查看前端日志

- 浏览器控制台（F12）查看前端日志
- Network 标签查看 API 请求

### 查看 Supabase 数据

1. Supabase Dashboard -> Table Editor
2. 查看各个表的数据
3. 检查 RLS 策略是否生效

## 📊 监控运行状态

### 后端健康检查

```bash
curl http://localhost:8000/health
# 应返回: {"status":"healthy"}
```

### 查看 API 文档

访问 http://localhost:8000/docs 查看完整的 API 文档和测试接口。

### 数据库状态

在 Supabase Dashboard -> Database -> Roles 查看连接数和活跃查询。

## 🎯 下一步

项目已成功启动！现在你可以：

1. **测试完整流程**: 上传 -> 分析 -> 推荐 -> 反馈
2. **配置搜索 API**: 获取更好的推荐质量
3. **自定义样式**: 修改 Tailwind 配置
4. **扩展功能**: 添加新特性

## 📞 需要帮助？

- 查看详细文档: `README.md`
- 后端文档: `backend/README.md`
- 前端文档: `frontend/README.md`
- 数据库文档: `backend/database/README.md`

---

**开始体验 Mosaic 吧！** 🚀
