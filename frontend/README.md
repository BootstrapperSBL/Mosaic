# Mosaic Frontend

Mosaic 前端应用 - 基于 Next.js 的 AI 兴趣图谱与推荐系统前端界面

## 技术栈

- **框架**: Next.js 15 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **认证**: Supabase Auth
- **HTTP客户端**: Axios
- **瀑布流布局**: react-masonry-css

## 安装和运行

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 环境配置

环境变量已在 `.env.local` 中预配置好，包含：
- Supabase URL 和 API Key
- 后端 API 地址

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 4. 构建生产版本

```bash
npm run build
npm start
```

## 项目结构

```
frontend/
├── app/                      # Next.js App Router 页面
│   ├── auth/                 # 认证页面
│   │   ├── signin/           # 登录页
│   │   └── signup/           # 注册页
│   ├── dashboard/            # 主控制台
│   ├── history/              # 历史记录
│   ├── layout.tsx            # 根布局
│   ├── page.tsx              # 首页（重定向）
│   └── globals.css           # 全局样式
├── components/               # React 组件
│   ├── UploadZone.tsx        # 上传区域组件
│   ├── TaskProgress.tsx      # 任务进度��件
│   ├── RecommendationGrid.tsx # 推荐网格（瀑布流）
│   └── RecommendationCard.tsx # 推荐卡片
├── lib/                      # 工具库
│   ├── supabase.ts           # Supabase 客户端
│   └── api.ts                # 后端 API 客户端
├── public/                   # 静态资源
├── .env.local                # 环境变量
├── next.config.js            # Next.js 配置
├── tailwind.config.ts        # Tailwind 配置
└── package.json              # 依赖配置
```

## 核心功能

### 1. 用户认证

- **注册**: `/auth/signup`
- **登录**: `/auth/signin`
- 使用 Supabase Auth 进行身份验证
- JWT Token 存储在 localStorage

### 2. 上传界面

支持三种上传方式：
- **图片上传**: 拖拽、点击选择、粘贴（Ctrl+V）
- **URL 上传**: 输入网页链接
- **文本上传**: 直接输入文本内容

### 3. 任务进度显示

实时显示 AI 分析进度：
- 准备数据 (0-20%)
- 深度解析 Deep Decode (20-40%)
- 关联扩展 Contextual Expand (40-60%)
- 动态拼贴 Dynamic Mosaic (60-100%)

使用轮询机制每 2 秒查询一次任务状态。

### 4. 推荐内容展示

- **瀑布流布局**: 使用 react-masonry-css
- **响应式**: 自动适配 1/2/3 列
- **卡片类型**: 知识、产品、位置、教程、新闻、社区等
- **相关性评分**: 显示推荐内容的相关度

### 5. 用户反馈

每个推荐卡片提供两个操作：
- **👍 保留**: 标记为喜欢，更新用户偏好
- **👎 丢弃**: 标记为不感兴趣
- 反馈后实时重新生成推荐

### 6. 历史记录

- **时间线展示**: 按时间倒序显示所有上传记录
- **内容预览**: 显示上传内容和分析摘要
- **快速访问**: 点击查看历史推荐
- **删除功能**: 删除不需要的记录

## API 集成

所有 API 调用都通过 `lib/api.ts` 中定义的方法：

```typescript
// 认证
authAPI.signup(email, password, username)
authAPI.signin(email, password)

// 上传
uploadAPI.image(file)
uploadAPI.url(url, userId)
uploadAPI.text(text, userId)

// 分析
analysisAPI.analyze(uploadId)
analysisAPI.getTaskStatus(taskId)

// 推荐
recommendationsAPI.get(analysisId)
recommendationsAPI.feedback(recommendationId, action)

// 历史
historyAPI.list(page, pageSize)
historyAPI.delete(uploadId)
```

## 样式设计

### 颜色方案

使用 Tailwind CSS 自定义主题：
- 主色调: 蓝色 (#2563EB)
- 背景: 灰白色 (#F9FAFB)
- 卡片: 白色带阴影
- 渐变: 蓝色到紫色

### 交互效果

- 悬停动画
- 平滑过渡
- 加载状态
- 错误提示

## 开发注意事项

### 状态管理

使用 React Hooks 进行状态管理：
- `useState`: 本地状态
- `useEffect`: 副作用和数据获取
- `useRouter`: 路由导航

### 错误处理

所有 API 错误都会：
1. 显示在界面上（红色提示框）
2. 包含详细错误信息
3. 方便调试

### 认证流程

1. 用户登录后，Token 存储在 localStorage
2. 所有 API 请求自动携带 Token（通过 axios 拦截器）
3. 未登录用户自动重定向到登录页

## 性能优化

- 图片懒加载
- 组件按需渲染
- API 请求去重
- 合理的轮询间隔

## 常见问题

### 上传失败

检查后端是否正常运行（http://localhost:8000）。

### 图片无法显示

确认 Supabase Storage 中的图片URL 域名已添加到 `next.config.js` 的 `images.domains`。

### Token 过期

Token 过期后会自动重定向到登录页，重新登录即可。

### 推荐内容为空

可能是搜索 API（Tavily/Serper）未配置，检查后端 `.env` 文件。

## 后续优化建议

1. 添加 WebSocket 支持实时推送（替代轮询）
2. 实现无限滚动加载历史记录
3. 添加图片预览和放大功能
4. 支持导出推荐内容为 PDF/Markdown
5. 添加用户偏好设置页面
6. 实现深色模式切换
