"""
分析相关 API
处理上传内容的 AI 分析和推荐生成（异步处理）
"""
from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import json
import asyncio
from datetime import datetime
from app.database import supabase
from app.services.deepseek import deepseek_service
from app.services.jina import jina_service
from app.services.recommender import recommender_service
from app.api.upload import get_user_from_token

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalyzeRequest(BaseModel):
    upload_id: str


class AnalyzeResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


async def process_analysis_task(task_id: str, upload_id: str, user_id: str):
    """
    后台处理分析任务
    完整流程: Deep Decode -> Contextual Expand -> Dynamic Mosaic
    """
    try:
        logger.info(f"开始处理分析任务 {task_id} for upload {upload_id}")
        intermediate_results = {}

        # 更新任务状态为处理中
        supabase.table("async_tasks").update({
            "status": "processing",
            "progress": 10,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()

        # 1. 获取上传内容
        upload_result = supabase.table("uploads").select("*").eq("id", upload_id).execute()
        if not upload_result.data:
            raise Exception("上传记录不存在")

        upload_data = upload_result.data[0]
        upload_type = upload_data["type"]

        # 更新进度: 20%
        intermediate_results["step_message"] = "正在准备内容..."
        supabase.table("async_tasks").update({
            "progress": 20,
            "result_data": intermediate_results,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()

        # 2. Step 1: Deep Decode (深度解析)
        logger.info(f"Step 1: Deep Decode - 解析内容类型: {upload_type}")

        visual_description = None
        extracted_text = None
        content_for_analysis = ""

        if upload_type == "image":
            # 图片分析
            image_url = upload_data["image_url"]
            vision_result = await deepseek_service.analyze_image(image_url, is_url=True)

            visual_description = vision_result.get("visual_description", "")
            extracted_text = vision_result.get("extracted_text", "")
            content_for_analysis = f"{visual_description}\n{extracted_text}"

        elif upload_type == "url":
            # URL 内容抓取
            url = upload_data["content_text"]
            url_content = await jina_service.fetch_url_content(url)
            # 保存完整内容到 extracted_text 用于前端展示
            extracted_text = url_content["content"]
            # 分析用的内容可以稍微长一些 (30k 字符)
            content_for_analysis = url_content["content"][:30000]
            
            # 使用 DeepSeek 分析文本内容
            visual_description = await deepseek_service.analyze_text_content(content_for_analysis)

        elif upload_type == "text":
            # 纯文本
            content_for_analysis = upload_data["content_text"]
            # 使用 DeepSeek 分析文本内容
            visual_description = await deepseek_service.analyze_text_content(content_for_analysis[:30000])

        intermediate_results["deep_decode"] = {
            "visual_description": visual_description,
            "extracted_text": extracted_text,
            "content_for_analysis": content_for_analysis
        }
        intermediate_results["step_message"] = "深度解析完成."

        # 更新进度: 40%
        supabase.table("async_tasks").update({
            "progress": 40,
            "result_data": intermediate_results,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()

        # 3. Step 2: Contextual Expand (意图分析和扩展)
        logger.info("Step 2: Contextual Expand - 进行意图分析")

        # 获取用户历史偏好
        user_pref_result = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
        user_history = []
        if user_pref_result.data:
            user_history = user_pref_result.data[0].get("liked_keywords", [])

        # AI 意图分析
        intent_result = await deepseek_service.analyze_intent(
            content=content_for_analysis,
            visual_context={"visual_description": visual_description} if visual_description else None,
            user_history=user_history
        )

        keywords = intent_result.get("keywords", [])
        interest_tags = intent_result.get("interest_tags", [])

        # 保存分析结果
        analysis_data = {
            "upload_id": upload_id,
            "user_id": user_id,
            "visual_description": visual_description,
            "extracted_text": extracted_text,
            "intent_analysis": intent_result,
            "keywords": keywords,
            "interest_tags": interest_tags,
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }

        analysis_result = supabase.table("analyses").insert(analysis_data).execute()
        intermediate_results["contextual_expand"] = intent_result
        intermediate_results["step_message"] = "关联扩展完成."
        analysis_id = analysis_result.data[0]["id"]

        # 更新进度: 60%
        supabase.table("async_tasks").update({
            "progress": 60,
            "result_data": intermediate_results,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()

        # 4. Step 3: Dynamic Mosaic (生成推荐磁贴)
        logger.info("Step 3: Dynamic Mosaic - 生成推荐内容")

        recommendations, search_results = await recommender_service.generate_recommendations(
            analysis_data=intent_result,
            user_id=user_id,
            count=10
        )
        intermediate_results["search_results"] = search_results
        intermediate_results["step_message"] = "搜索完成，正在生成推荐..."

        # 更新进度: 80%
        supabase.table("async_tasks").update({
            "progress": 80,
            "result_data": intermediate_results,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()

        # 保存推荐结果
        saved_recommendations = []
        for rec in recommendations:
            rec_data = {
                "analysis_id": analysis_id,
                "user_id": user_id,
                **rec
            }
            res = supabase.table("recommendations").insert(rec_data).execute()
            if res.data:
                saved_rec = res.data[0]
                saved_recommendations.append(saved_rec)

        # 触发后台文章生成任务 (不等待完成)
        asyncio.create_task(
            recommender_service.generate_articles_background(
                saved_recommendations,
                intermediate_results
            )
        )

        # 更新 analysis 记录，添加完整上下文
        supabase.table("analyses").update({
            "full_context": intermediate_results
        }).eq("id", analysis_id).execute()

        final_result_data = {
            "analysis_id": analysis_id,
            "upload_id": upload_id,
            "recommendations_count": len(recommendations),
            "keywords": keywords,
            "interest_tags": interest_tags
        }
        intermediate_results["final_result"] = final_result_data
        intermediate_results["step_message"] = "动态拼贴完成."

        supabase.table("async_tasks").update({
            "status": "completed",
            "progress": 100,
            "result_data": intermediate_results,
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()

        logger.info(f"分析任务 {task_id} 完成")

    except Exception as e:
        logger.error(f"分析任务 {task_id} 失败: {str(e)}", exc_info=True)

        # 更新任务为失败状态
        supabase.table("async_tasks").update({
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()

        # 同时更新 analysis 表状态
        try:
            supabase.table("analyses").update({
                "status": "failed",
                "error_message": str(e)
            }).eq("upload_id", upload_id).execute()
        except:
            pass


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_upload(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """
    开始分析上传的内容（异步处理）
    """
    try:
        user_id = get_user_from_token(authorization)
        logger.info(f"用户 {user_id} 请求分析 upload {request.upload_id}")

        # 验证上传记录是否存在且属于当前用户
        upload_result = supabase.table("uploads").select("*").eq("id", request.upload_id).eq("user_id", user_id).execute()
        if not upload_result.data:
            raise HTTPException(status_code=404, detail="上传记录不存在或无权访问")

        # 检查是否已经有进行中的分析任务
        existing_task = supabase.table("async_tasks").select("*").eq("input_data", json.dumps({"upload_id": request.upload_id})).eq("status", "processing").execute()
        if existing_task.data:
            return AnalyzeResponse(
                task_id=existing_task.data[0]["id"],
                status="processing",
                message="分析任务已在进行中"
            )

        # 创建异步任务
        task_data = {
            "user_id": user_id,
            "task_type": "analyze",
            "status": "pending",
            "progress": 0,
            "input_data": {"upload_id": request.upload_id}
        }

        task_result = supabase.table("async_tasks").insert(task_data).execute()
        task_id = task_result.data[0]["id"]

        # 添加后台任务
        background_tasks.add_task(process_analysis_task, task_id, request.upload_id, user_id)

        logger.info(f"分析任务 {task_id} 已创建并提交到后台处理")

        return AnalyzeResponse(
            task_id=task_id,
            status="pending",
            message="分析任务已创建，正在后台处理"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建分析任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建分析任务失败: {str(e)}")


class AnalysisDetailResponse(BaseModel):
    id: str
    upload_id: str
    visual_description: Optional[str] = None
    extracted_text: Optional[str] = None
    intent_analysis: Optional[Dict[str, Any]] = None
    full_context: Optional[Dict[str, Any]] = None
    status: str
    created_at: str


@router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
async def get_analysis_details(
    analysis_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    获取分析详情
    """
    try:
        user_id = get_user_from_token(authorization)
        
        result = supabase.table("analyses").select("*").eq("id", analysis_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="分析记录不存在或无权访问")
            
        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    查询任务状态
    """
    try:
        user_id = get_user_from_token(authorization)

        # 获取任务信息
        task_result = supabase.table("async_tasks").select("*").eq("id", task_id).eq("user_id", user_id).execute()

        if not task_result.data:
            raise HTTPException(status_code=404, detail="任务不存在或无权访问")

        task = task_result.data[0]

        return TaskStatusResponse(
            task_id=task["id"],
            status=task["status"],
            progress=task.get("progress", 0),
            result=task.get("result_data"),
            error=task.get("error_message")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}")
