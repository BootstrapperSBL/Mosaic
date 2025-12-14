# ⚡ 快速修复：创建 Supabase Storage Bucket

## 问题原因

你遇到的错误 `Bucket not found` 是因为 Supabase Storage 中还没有创建 `uploads` bucket。

## 🎯 解决步骤（2分钟完成）

### 方式 1: 可视化界面创建（最简单）

1. **打开浏览器，访问**:
   ```
   https://app.supabase.com/project/yddhnfecjfumxqreiwze/storage/buckets
   ```

2. **点击绿色按钮** "New bucket"

3. **填写信息**:
   - Name: `uploads`
   - Public bucket: ✅ **必须勾选**
   - File size limit: 保持默认
   - Allowed MIME types: 保持默认

4. **点击** "Create bucket"

5. **完成！** 刷新前端页面，重新上传图片

### 方式 2: SQL 创建

1. **访问 SQL Editor**:
   ```
   https://app.supabase.com/project/yddhnfecjfumxqreiwze/sql/new
   ```

2. **复制以下 SQL** (已为你准备在 `backend/database/create-storage-bucket.sql`):

   ```sql
   -- 创建 uploads bucket
   INSERT INTO storage.buckets (id, name, public)
   VALUES ('uploads', 'uploads', true)
   ON CONFLICT (id) DO NOTHING;

   -- 配置权限策略
   CREATE POLICY "Users can upload own files" ON storage.objects
       FOR INSERT WITH CHECK (
           bucket_id = 'uploads' AND
           auth.uid()::text = (storage.foldername(name))[1]
       );

   CREATE POLICY "Users can view own files" ON storage.objects
       FOR SELECT USING (
           bucket_id = 'uploads' AND
           auth.uid()::text = (storage.foldername(name))[1]
       );

   CREATE POLICY "Users can delete own files" ON storage.objects
       FOR DELETE USING (
           bucket_id = 'uploads' AND
           auth.uid()::text = (storage.foldername(name))[1]
       );
   ```

3. **点击** "Run" 按钮

4. **验证**: 应该看到 "Success. No rows returned"

## ✅ 验证创建成功

执行以下 SQL 验证：

```sql
SELECT * FROM storage.buckets WHERE id = 'uploads';
```

应该返回一行数据，包含 bucket 信息。

## 🔄 完成后

1. **刷新前端页面** (http://localhost:3000)
2. **重新上传图片**
3. **应该成功了！**

## 💡 临时测试方案

如果你不想立即创建 bucket，可以先测试其他功能：

### 测试 URL 上传
1. 点击 "URL" 标签
2. 输入任意网址，如：`https://www.wikipedia.org/`
3. 点击提交

### 测试文本上传
1. 点击 "文本" 标签
2. 输入任意文本内容
3. 点击提交

这两个功能不依赖 Storage，可以立即测试 AI 分析流程。

---

**推荐**: 使用方式 1 创建，最快最简单！
