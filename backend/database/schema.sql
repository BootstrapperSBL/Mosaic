-- Mosaic 数据库表结构设计
-- 请在 Supabase SQL Editor 中执行此脚本

-- 1. 用户扩展表 (扩展 Supabase Auth 的 users 表)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    username TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 上传记录表
CREATE TABLE IF NOT EXISTS public.uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('image', 'url', 'text')),

    -- 内容存储
    content_text TEXT,  -- 用于存储 URL 或纯文本
    image_url TEXT,     -- Supabase Storage 中的图片路径

    -- 元数据
    content_preview TEXT,  -- 内容预览（前200字符）
    file_size INTEGER,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 索引
    CONSTRAINT uploads_type_check CHECK (
        (type = 'image' AND image_url IS NOT NULL) OR
        (type IN ('url', 'text') AND content_text IS NOT NULL)
    )
);

CREATE INDEX idx_uploads_user_id ON public.uploads(user_id);
CREATE INDEX idx_uploads_created_at ON public.uploads(created_at DESC);


-- 3. 分析结果表
CREATE TABLE IF NOT EXISTS public.analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID REFERENCES public.uploads(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,

    -- AI 分析结果
    visual_description TEXT,      -- DeepSeek-OCR 的视觉描述
    extracted_text TEXT,           -- OCR 提取的文字
    intent_analysis JSONB,         -- DeepSeek-V3.2 的意图分析结果
    keywords TEXT[],               -- 提取的关键词数组
    interest_tags TEXT[],          -- 兴趣标签数组
    full_context JSONB,            -- 完整的分析过程上下文

    -- 处理状态
    status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    error_message TEXT,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_analyses_upload_id ON public.analyses(upload_id);
CREATE INDEX idx_analyses_user_id ON public.analyses(user_id);
CREATE INDEX idx_analyses_status ON public.analyses(status);


-- 4. 推荐内容表
CREATE TABLE IF NOT EXISTS public.recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES public.analyses(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,

    -- 推荐内容详情
    title TEXT NOT NULL,
    description TEXT,
    url TEXT,
    image_url TEXT,
    source TEXT,                   -- 内容来源（Tavily, Serper 等）
    relevance_score DECIMAL(3,2),  -- 0.00 - 1.00 的相关性评分
    tile_type TEXT,                -- knowledge, product, location, tutorial, etc.
    article_html TEXT,             -- 深度文章 HTML 内容

    -- 用户反馈
    user_action TEXT CHECK (user_action IN ('keep', 'discard', NULL)),
    user_action_at TIMESTAMP WITH TIME ZONE,

    -- 排序和展示
    display_order INTEGER,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_recommendations_analysis_id ON public.recommendations(analysis_id);
CREATE INDEX idx_recommendations_user_id ON public.recommendations(user_id);
CREATE INDEX idx_recommendations_user_action ON public.recommendations(user_action);


-- 5. 用户偏好表 (用于实时学习和调整推荐)
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,

    -- 偏好数据
    liked_keywords TEXT[],         -- 用户喜欢的关键词
    disliked_keywords TEXT[],      -- 用户不喜欢的关键词
    preferred_tile_types TEXT[],   -- 偏好的内容类型
    avoided_tile_types TEXT[],     -- 避免的内容类型

    -- 统计数据
    total_uploads INTEGER DEFAULT 0,
    total_keeps INTEGER DEFAULT 0,
    total_discards INTEGER DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id)
);


-- 6. 异步任务表 (用于跟踪后台处理任务)
CREATE TABLE IF NOT EXISTS public.async_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    task_type TEXT NOT NULL,  -- 'analyze', 'recommend', etc.

    -- 任务状态
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    progress INTEGER DEFAULT 0,  -- 0-100

    -- 任务数据
    input_data JSONB,
    result_data JSONB,
    error_message TEXT,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_async_tasks_user_id ON public.async_tasks(user_id);
CREATE INDEX idx_async_tasks_status ON public.async_tasks(status);


-- 启用 Row Level Security (RLS)
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.async_tasks ENABLE ROW LEVEL SECURITY;


-- RLS 策略: 用户只能访问自己的数据
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON public.user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);


CREATE POLICY "Users can view own uploads" ON public.uploads
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own uploads" ON public.uploads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own uploads" ON public.uploads
    FOR DELETE USING (auth.uid() = user_id);


CREATE POLICY "Users can view own analyses" ON public.analyses
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own analyses" ON public.analyses
    FOR INSERT WITH CHECK (auth.uid() = user_id);


CREATE POLICY "Users can view own recommendations" ON public.recommendations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own recommendations" ON public.recommendations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own recommendations" ON public.recommendations
    FOR UPDATE USING (auth.uid() = user_id);


CREATE POLICY "Users can view own preferences" ON public.user_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences" ON public.user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences" ON public.user_preferences
    FOR UPDATE USING (auth.uid() = user_id);


CREATE POLICY "Users can view own tasks" ON public.async_tasks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own tasks" ON public.async_tasks
    FOR INSERT WITH CHECK (auth.uid() = user_id);


-- 创建更新 updated_at 的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 应用触发器
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_async_tasks_updated_at BEFORE UPDATE ON public.async_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- Storage bucket 配置 (在 Supabase Dashboard 中手动创建，或使用 SQL)
-- 创建 'uploads' bucket 用于存储用户上传的图片
INSERT INTO storage.buckets (id, name, public)
VALUES ('uploads', 'uploads', true)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS 策略
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
