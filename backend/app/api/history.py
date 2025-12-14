"""
历史记录相关 API
按时间线展示所有上传内容和分析结果
"""
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from app.database import supabase
from app.api.upload import get_user_from_token

logger = logging.getLogger(__name__)

router = APIRouter()


class HistoryItem(BaseModel):
    id: str
    type: str
    content_preview: str
    analysis_id: Optional[str] = None
    analysis_summary: Optional[str] = None
    recommendation_count: int
    created_at: str
    full_context: Optional[Dict[str, Any]] = None



class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None)
):
    """
    获取用户的历史上传记录（按时间线展示）
    """
    try:
        user_id = get_user_from_token(authorization)
        logger.info(f"用户 {user_id} 请求历史记录，页码: {page}")

        # 计算偏移量
        offset = (page - 1) * page_size

        # 获取总数
        count_result = supabase.table("uploads").select("id", count="exact").eq("user_id", user_id).execute()
        total = count_result.count if hasattr(count_result, 'count') else 0

        # 获取上传记录（按时间倒序）
        uploads_result = supabase.table("uploads").select("*").eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + page_size - 1).execute()

        items = []
        for upload in uploads_result.data:
            upload_id = upload["id"]

            # 获取对应的分析结果
            analysis_result = supabase.table("analyses").select("id, intent_analysis, keywords, interest_tags, status, full_context").eq("upload_id", upload_id).execute()

            analysis_id = None
            analysis_summary = None
            recommendation_count = 0
            full_context = None

            if analysis_result.data:
                analysis = analysis_result.data[0]
                analysis_id = analysis["id"]
                full_context = analysis.get("full_context")

                # 生成更智能的标题 (基于关键词)
                keywords = analysis.get("keywords", [])
                if keywords and len(keywords) > 0:
                    # 使用前两个关键词作为标题
                    display_title = " · ".join(keywords[:2])
                    # 如果是 URL，尝试结合 URL 标题
                    if upload["type"] == "url" and upload.get("content_preview"):
                         # 如果 content_preview 是标题，可以保留，或者用关键词增强
                         # 这里我们优先展示 AI 提取的关键词，因为它们代表了"对内容的总结"
                         pass
                else:
                    display_title = upload.get("content_preview", "未命名内容")

                # 生成分析摘要
                if analysis["status"] == "completed":
                    interest_tags = analysis.get("interest_tags", [])
                    analysis_summary = f"兴趣: {', '.join(interest_tags[:3])}"

                    # 获取推荐数量
                    rec_count_result = supabase.table("recommendations").select("id", count="exact").eq("analysis_id", analysis_id).execute()
                    recommendation_count = rec_count_result.count if hasattr(rec_count_result, 'count') else 0
                elif analysis["status"] == "processing":
                    analysis_summary = "正在分析中..."
                    display_title = f"分析中: {upload.get('content_preview', '')[:10]}..."
                elif analysis["status"] == "failed":
                    analysis_summary = "分析失败"
                    display_title = f"失败: {upload.get('content_preview', '')[:10]}..."
            else:
                display_title = upload.get("content_preview", "未处理内容")

            items.append(HistoryItem(
                id=upload["id"],
                type=upload["type"],
                content_preview=display_title,
                analysis_id=analysis_id,
                analysis_summary=analysis_summary,
                recommendation_count=recommendation_count,
                created_at=upload["created_at"],
                full_context=full_context
            ))

        return HistoryResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.delete("/{upload_id}")
async def delete_history_item(
    upload_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    删除历史记录项
    """
    try:
        user_id = get_user_from_token(authorization)
        logger.info(f"用户 {user_id} 删除历史记录: {upload_id}")

        # 验证记录是否存在且属于当前用户
        upload_result = supabase.table("uploads").select("*").eq("id", upload_id).eq("user_id", user_id).execute()
        if not upload_result.data:
            raise HTTPException(status_code=404, detail="记录不存在或无权访问")

        upload = upload_result.data[0]

        # 如果是图片，删除 Storage 中的文件
        if upload["type"] == "image" and upload.get("image_url"):
            try:
                # 从 URL 提取文件路径
                image_url = upload["image_url"]
                # Supabase Storage URL 格式: https://{project}.supabase.co/storage/v1/object/public/uploads/{path}
                path = image_url.split("/uploads/")[-1]
                supabase.storage.from_("uploads").remove([path])
                logger.info(f"已删除 Storage 文件: {path}")
            except Exception as e:
                logger.warning(f"删除 Storage 文件失败: {str(e)}")

        # 删除上传记录（级联删除会自动删除关联的分析和推荐）
        supabase.table("uploads").delete().eq("id", upload_id).execute()

        logger.info(f"历史记录已删除: {upload_id}")

        return {"message": "删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除历史记录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
