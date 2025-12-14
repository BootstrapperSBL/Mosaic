-- 创建 Supabase Storage Bucket 和 RLS 策略
-- 请在 Supabase Dashboard -> SQL Editor 中执行此脚本

-- 1. 创建 uploads bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('uploads', 'uploads', true)
ON CONFLICT (id) DO NOTHING;

-- 2. 配置 Storage RLS 策略

-- 允许用户上传自己的文件
CREATE POLICY "Users can upload own files" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'uploads' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- 允许用户查看自己的文件
CREATE POLICY "Users can view own files" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'uploads' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- 允许用户删除自己的文件
CREATE POLICY "Users can delete own files" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'uploads' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- 验证创建成功
SELECT * FROM storage.buckets WHERE id = 'uploads';
