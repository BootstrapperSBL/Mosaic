"""
推荐和反馈相关 API
"""
from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime
from app.database import supabase
from app.api.upload import get_user_from_token
from app.services.recommender import recommender_service

logger = logging.getLogger(__name__)

router = APIRouter()


class RecommendationItem(BaseModel):
    id: str
    title: str
    description: str
    url: Optional[str]
    image_url: Optional[str]
    source: str
    relevance_score: float
    tile_type: str
    user_action: Optional[str] = None
    display_order: int
    article_html: Optional[str] = None


class ArticleResponse(BaseModel):
    id: str
    article_html: str


@router.get("/{recommendation_id}/article", response_model=ArticleResponse)
async def get_recommendation_article(
    recommendation_id: str,
    regenerate: bool = False,
    authorization: Optional[str] = Header(None)
):
    """
    获取或生成推荐内容的深度文章
    """
    try:
        user_id = get_user_from_token(authorization)

        # 1. 获取推荐详情
        rec_result = supabase.table("recommendations").select("*").eq("id", recommendation_id).eq("user_id", user_id).execute()
        if not rec_result.data:
            raise HTTPException(status_code=404, detail="推荐不存在")
        
        recommendation = rec_result.data[0]
        
        # 2. 如果已有文章且不强制重新生成，直接返回
        if recommendation.get("article_html") and not regenerate:
            return ArticleResponse(id=recommendation_id, article_html=recommendation["article_html"])
            
        # 3. 获取分析上下文 (Full Context)
        analysis_id = recommendation["analysis_id"]
        analysis_result = supabase.table("analyses").select("full_context").eq("id", analysis_id).execute()
        
        full_context = {}
        if analysis_result.data and analysis_result.data[0].get("full_context"):
            full_context = analysis_result.data[0]["full_context"]
            
        # 4. 生成文章
        article_html = await recommender_service.generate_article(recommendation, full_context)
        
        if article_html is None:
            # 如果返回 None，说明被锁住并等待结束，此时应该从数据库重新获取
            rec_result = supabase.table("recommendations").select("article_html").eq("id", recommendation_id).execute()
            if rec_result.data:
                article_html = rec_result.data[0].get("article_html")
        else:
            # 5. 保存文章
            try:
                supabase.table("recommendations").update({
                    "article_html": article_html
                }).eq("id", recommendation_id).execute()
            except Exception as e:
                logger.warning(f"保存文章到数据库失败 (可能是缺少 article_html 字段): {str(e)}")
                # 继续执行，返回生成的文章给前端
        
        return ArticleResponse(id=recommendation_id, article_html=article_html or "")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文章失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文章失败: {str(e)}")


class RecommendationsResponse(BaseModel):
    analysis_id: str
    recommendations: List[RecommendationItem]
    total: int


class FeedbackRequest(BaseModel):
    recommendation_id: str
    action: str  # "keep" or "discard"


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    updated_recommendations: Optional[List[RecommendationItem]] = None


async def update_user_preferences(user_id: str, recommendation_id: str, action: str):
    """
    根据用户反馈更新用户偏好（后台任务）
    """
    try:
        logger.info(f"更新用户 {user_id} 的偏好，基于反馈: {action}")

        # 获取推荐内容详情
        rec_result = supabase.table("recommendations").select("*").eq("id", recommendation_id).execute()
        if not rec_result.data:
            return

        recommendation = rec_result.data[0]
        analysis_id = recommendation["analysis_id"]

        # 获取分析结果中的关键词
        analysis_result = supabase.table("analyses").select("keywords, interest_tags").eq("id", analysis_id).execute()
        if not analysis_result.data:
            return

        keywords = analysis_result.data[0].get("keywords", [])
        interest_tags = analysis_result.data[0].get("interest_tags", [])
        tile_type = recommendation.get("tile_type", "")

        # 获取当前用户偏好
        pref_result = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()

        if not pref_result.data:
            # 创建新的偏好记录
            pref_data = {
                "user_id": user_id,
                "liked_keywords": keywords if action == "keep" else [],
                "disliked_keywords": keywords if action == "discard" else [],
                "preferred_tile_types": [tile_type] if action == "keep" and tile_type else [],
                "avoided_tile_types": [tile_type] if action == "discard" and tile_type else [],
                "total_keeps": 1 if action == "keep" else 0,
                "total_discards": 1 if action == "discard" else 0
            }
            supabase.table("user_preferences").insert(pref_data).execute()
        else:
            # 更新现有偏好
            current_pref = pref_result.data[0]

            liked_keywords = current_pref.get("liked_keywords", [])
            disliked_keywords = current_pref.get("disliked_keywords", [])
            preferred_types = current_pref.get("preferred_tile_types", [])
            avoided_types = current_pref.get("avoided_tile_types", [])

            if action == "keep":
                # 添加到喜欢列表
                for kw in keywords[:5]:  # 只取前5个关键词
                    if kw not in liked_keywords:
                        liked_keywords.append(kw)
                    if kw in disliked_keywords:
                        disliked_keywords.remove(kw)

                if tile_type and tile_type not in preferred_types:
                    preferred_types.append(tile_type)
                if tile_type in avoided_types:
                    avoided_types.remove(tile_type)

                total_keeps = current_pref.get("total_keeps", 0) + 1

            else:  # discard
                # 添加到不喜欢列表
                for kw in keywords[:5]:
                    if kw not in disliked_keywords:
                        disliked_keywords.append(kw)
                    if kw in liked_keywords:
                        liked_keywords.remove(kw)

                if tile_type and tile_type not in avoided_types:
                    avoided_types.append(tile_type)
                if tile_type in preferred_types:
                    preferred_types.remove(tile_type)

                total_keeps = current_pref.get("total_keeps", 0)

            total_discards = current_pref.get("total_discards", 0) + (1 if action == "discard" else 0)

            # 限制列表长度
            liked_keywords = liked_keywords[-50:]
            disliked_keywords = disliked_keywords[-50:]

            update_data = {
                "liked_keywords": liked_keywords,
                "disliked_keywords": disliked_keywords,
                "preferred_tile_types": preferred_types,
                "avoided_tile_types": avoided_types,
                "total_keeps": total_keeps,
                "total_discards": total_discards,
                "updated_at": datetime.utcnow().isoformat()
            }

            supabase.table("user_preferences").update(update_data).eq("user_id", user_id).execute()

        logger.info(f"用户偏好更新完成")

    except Exception as e:
        logger.error(f"更新用户偏好失败: {str(e)}", exc_info=True)


@router.get("/analysis/{analysis_id}", response_model=RecommendationsResponse)
async def get_recommendations(
    analysis_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    获取分析结果的推荐内容
    """
    try:
        user_id = get_user_from_token(authorization)

        # 验证分析结果是否存在且属于当前用户
        analysis_result = supabase.table("analyses").select("*").eq("id", analysis_id).eq("user_id", user_id).execute()
        if not analysis_result.data:
            raise HTTPException(status_code=404, detail="分析结果不存在或无权访问")

        # 获取推荐内容
        rec_result = supabase.table("recommendations").select("*").eq("analysis_id", analysis_id).order("display_order").execute()

        recommendations = [
            RecommendationItem(
                id=rec["id"],
                title=rec["title"],
                description=rec["description"],
                url=rec.get("url"),
                image_url=rec.get("image_url"),
                source=rec["source"],
                relevance_score=float(rec.get("relevance_score", 0.5)),
                tile_type=rec["tile_type"],
                user_action=rec.get("user_action"),
                display_order=rec.get("display_order", 0)
            )
            for rec in rec_result.data
        ]

        return RecommendationsResponse(
            analysis_id=analysis_id,
            recommendations=recommendations,
            total=len(recommendations)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取推荐失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {str(e)}")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """
    提交用户反馈（保留/丢弃）并实时调整推荐
    """
    try:
        user_id = get_user_from_token(authorization)
        logger.info(f"用户 {user_id} 提交反馈: {request.action} for {request.recommendation_id}")

        # 验证 action
        if request.action not in ["keep", "discard"]:
            raise HTTPException(status_code=400, detail="无效的操作类型")

        # 验证推荐是否存在且属于当前用户
        rec_result = supabase.table("recommendations").select("*").eq("id", request.recommendation_id).eq("user_id", user_id).execute()
        if not rec_result.data:
            raise HTTPException(status_code=404, detail="推荐不存在或无权访问")

        recommendation = rec_result.data[0]
        analysis_id = recommendation["analysis_id"]

        # 更新推荐的用户反馈
        supabase.table("recommendations").update({
            "user_action": request.action,
            "user_action_at": datetime.utcnow().isoformat()
        }).eq("id", request.recommendation_id).execute()

        # 后台更新用户偏好
        background_tasks.add_task(update_user_preferences, user_id, request.recommendation_id, request.action)

        # 实时调整：基于更新后的偏好重新生成推荐
        # 获取分析数据
        analysis_result = supabase.table("analyses").select("*").eq("id", analysis_id).execute()
        if not analysis_result.data:
            raise HTTPException(status_code=404, detail="分析结果不存在")

        analysis_data = analysis_result.data[0]
        intent_analysis = analysis_data.get("intent_analysis", {})

        # 重新生成推荐（异步）
        try:
            new_recommendations, search_results = await recommender_service.generate_recommendations(
                analysis_data=intent_analysis,
                user_id=user_id,
                count=10
            )

            # 删除旧的推荐（除了已有用户反馈的）
            supabase.table("recommendations").delete().eq("analysis_id", analysis_id).is_("user_action", "null").execute()

            # 保存新推荐
            saved_new_recs = []
            for rec in new_recommendations:
                rec_data = {
                    "analysis_id": analysis_id,
                    "user_id": user_id,
                    **rec
                }
                res = supabase.table("recommendations").insert(rec_data).execute()
                if res.data:
                    saved_new_recs.append(res.data[0])
            
            # 触发后台文章生成
            if saved_new_recs:
                context = {"search_results": search_results}
                asyncio.create_task(
                    recommender_service.generate_articles_background(saved_new_recs, context)
                )

            # 获取更新后的推荐列表
            updated_result = supabase.table("recommendations").select("*").eq("analysis_id", analysis_id).order("display_order").execute()

            updated_recs = [
                RecommendationItem(
                    id=rec["id"],
                    title=rec["title"],
                    description=rec["description"],
                    url=rec.get("url"),
                    image_url=rec.get("image_url"),
                    source=rec["source"],
                    relevance_score=float(rec.get("relevance_score", 0.5)),
                    tile_type=rec["tile_type"],
                    user_action=rec.get("user_action"),
                    display_order=rec.get("display_order", 0)
                )
                for rec in updated_result.data
            ]

            return FeedbackResponse(
                success=True,
                message="反馈已提交，推荐已实时更新",
                updated_recommendations=updated_recs
            )

        except Exception as e:
            logger.warning(f"实时更新推荐失败: {str(e)}")
            # 即使更新失败，也返回成功（因为反馈已保存）
            return FeedbackResponse(
                success=True,
                message="反馈已提交"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交反馈失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")
