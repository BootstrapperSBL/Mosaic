# Supabase 数据库设置指南

## 步骤 1: 在 Supabase 中执行 SQL 脚本

1. 登录 Supabase Dashboard: https://app.supabase.com/
2. 选择你的项目 (yddhnfecjfumxqreiwze)
3. 点击左侧菜单的 "SQL Editor"
4. 点击 "New Query"
5. 复制 `schema.sql` 的全部内容
6. 粘贴到 SQL 编辑器中
7. 点击 "Run" 执行脚本

## 步骤 2: 创建 Storage Bucket

如果 SQL 脚本中的 Storage 创建失败，请手动创建：

1. 在 Supabase Dashboard 中点击 "Storage"
2. 点击 "Create a new bucket"
3. Bucket 名称: `uploads`
4. 设置为 Public bucket
5. 点击 "Create bucket"

## 数据库表结构说明

### 1. user_profiles (用户资料)
- 扩展 Supabase Auth 的用户信息
- 存储用户名、头像等额外信息

### 2. uploads (上传记录)
- 存储用户上传的所有内容
- 支持三种类型: image, url, text
- 图片存储在 Supabase Storage，路径记录在 image_url

### 3. analyses (分析结果)
- 存储 AI 对上传内容的分析结果
- 包含视觉描述、文本提取、意图分析、关键词等
- 支持异步处理状态

### 4. recommendations (推荐内容)
- 存储根据分析生成的推荐磁贴
- 包含标题、描述、URL、图片、相关性评分等
- 记录用户的反馈(保留/丢弃)

### 5. user_preferences (用户偏好)
- 存储用户的长期偏好数据
- 基于用户反馈动态更新
- 用于实时调整推荐算法

### 6. async_tasks (异步任务)
- 跟踪后台处理任务的状态
- 支持进度显示和错误追踪

## Row Level Security (RLS)

所有表都启用了 RLS，确保:
- 用户只能访问自己的数据
- 数据隔离和安全性

## 验证安装

执行以下 SQL 验证表是否创建成功:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'user_profiles',
    'uploads',
    'analyses',
    'recommendations',
    'user_preferences',
    'async_tasks'
);
```

应该返回 6 行结果。
