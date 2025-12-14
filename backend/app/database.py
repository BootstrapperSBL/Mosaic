from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# 初始化 Supabase 客户端
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

logger.info("Supabase client initialized successfully")
