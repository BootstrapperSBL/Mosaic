# Mosaic Backend

Mosaic 后端服务 - 基于 FastAPI 的 AI 驱动的兴趣图谱和推荐系统

## 技术栈

- **框架**: FastAPI
- **数据库**: Supabase (PostgreSQL)
- **AI 服务**:
  - DeepSeek-OCR (视觉理解)
  - DeepSeek-V3.2 (文本推理)
  - Jina Reader (网页转 Markdown)
  - Tavily / Serper (搜索引擎)

## 安装步骤

### 1. 创建虚拟环境

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，已经预填了所有密钥：

```bash
cp .env.example .env
```

如果需要使用搜索功能，请配置 TAVILY_API_KEY 或 SERPER_API_KEY。

### 4. 设置 Supabase 数据库

1. 登录 [Supabase Dashboard](https://app.supabase.com/)
2. 选择项目
3. 进入 SQL Editor
4. 执行 `database/schema.sql` 中的所有 SQL 语句
5. 确认所有表和 RLS 策略已创建

详细说明请查看 `database/README.md`。

### 5. 启动服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或者直接运行
python -m app.main
```

服务将在 http://localhost:8000 启动。

### 6. 查看 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 认证 (Auth)

- `POST /api/auth/signup` - 用户注册
- `POST /api/auth/signin` - 用户登录
- `POST /api/auth/signout` - 用户登出
- `GET /api/auth/me` - 获取当前用户信息

### 上传 (Upload)

- `POST /api/upload/image` - 上传图片
- `POST /api/upload/url` - 上传 URL
- `POST /api/upload/text` - 上传文本

### 分析 (Analysis)

- `POST /api/analysis/analyze` - 开始分析（异步）
- `GET /api/analysis/task/{task_id}` - 查询任务状态

### 推荐 (Recommendations)

- `GET /api/recommendations/analysis/{analysis_id}` - 获取推荐内容
- `POST /api/recommendations/feedback` - 提交反馈（保留/丢弃）

### 历史 (History)

- `GET /api/history/` - 获取历史记录（分页）
- `DELETE /api/history/{upload_id}` - 删除历史记录

## 核心流程

### 1. 用户上传内容

用户可以上传三种类型的内容：
- 图片（存储在 Supabase Storage）
- URL（使用 Jina Reader 抓取）
- 纯文本

### 2. AI 分析（异步处理）

分为三个步骤：

#### Step 1: Deep Decode (深度解析)
- 图片：使用 DeepSeek-OCR 进行视觉理解和 OCR
- URL：使用 Jina Reader 转换为 Markdown
- 文本：直接使用

#### Step 2: Contextual Expand (关联扩展)
- 使用 DeepSeek-V3.2 进行意图分析
- 提取关键词和兴趣标签
- 结合用户历史偏好
- 生成搜索查询

#### Step 3: Dynamic Mosaic (动态拼贴)
- 执行多个搜索查询
- 使用 AI 对结果进行评分和分类
- 生成 10 个推荐磁贴
- 保存到数据库

### 3. 用户反馈和实时调整

用户可以对推荐内容进行"保留"或"丢弃"操作：
- 后台更新用户偏好
- 实时重新生成推荐
- 返回更新后的推荐列表

## 错误处理

所有错误都会：
1. 记录到日志（带完整堆栈）
2. 返回原始错误信息给前端
3. 更新任务状态为 failed（异步任务）

这样方便开发阶段的调试。

## 开发注意事项

### 异步处理

分析任务使用 FastAPI 的 BackgroundTasks 进行异步处理：
- 用户提交后立即返回 task_id
- 前端可以轮询 `/api/analysis/task/{task_id}` 查询状态
- 任务完成后可以获取 analysis_id

### 用户认证

使用 Supabase Auth：
- JWT token 验证
- Row Level Security (RLS) 数据隔离
- 所有 API 都需要 Authorization header

### 数据库操作

使用 Supabase Python Client：
- 自动处理 RLS
- 支持实时订阅（未使用）
- Storage 集成

## 生产部署建议

1. 使用 gunicorn + uvicorn workers
2. 配置 HTTPS
3. 设置合适的超时时间
4. 使用 Redis 缓存（可选）
5. 配置日志系统（如 Sentry）
6. 限流和速率限制

## 故障排查

### 数据库连接失败

检查 `.env` 中的 Supabase 配置是否正确。

### AI API 调用失败

检查 API 密钥是否有效，配额是否充足。

### 搜索功能不可用

确保配置了 TAVILY_API_KEY 或 SERPER_API_KEY。

### 图片上传失败

确认 Supabase Storage bucket `uploads` 已创建且配置了正确的 RLS 策略。
