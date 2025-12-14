"""
上传相关 API
支持图片、URL、文本三种类型的上传
"""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import logging
import base64
import uuid
from datetime import datetime
from app.database import supabase
from app.services.jina import jina_service

logger = logging.getLogger(__name__)

router = APIRouter()


class UploadTextRequest(BaseModel):
    type: str  # "url" or "text"
    content: str
    user_id: str


class UploadResponse(BaseModel):
    upload_id: str
    type: str
    status: str
    message: str


def get_user_from_token(authorization: Optional[str]) -> str:
    """从 token 获取用户 ID"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证信息")

    token = authorization.replace("Bearer ", "")
    try:
        user = supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="无效的认证信息")
        return user.user.id
    except Exception as e:
        logger.error(f"验证用户失败: {str(e)}")
        raise HTTPException(status_code=401, detail="认证失败")


@router.post("/image", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """上传图片"""
    try:
        user_id = get_user_from_token(authorization)
        logger.info(f"用户 {user_id} 上传图片: {file.filename}")

        # 验证文件类型
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="只支持图片文件")

        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)

        # 生成唯一文件名
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{user_id}/{uuid.uuid4()}.{file_ext}"

        # 上传到 Supabase Storage
        try:
            storage_response = supabase.storage.from_("uploads").upload(
                unique_filename,
                file_content,
                {"content-type": file.content_type}
            )
            logger.info(f"图片上传到 Storage: {unique_filename}")
        except Exception as e:
            logger.error(f"上传到 Storage 失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

        # 获取公开 URL
        image_url = supabase.storage.from_("uploads").get_public_url(unique_filename)

        # 保存上传记录到数据库
        upload_data = {
            "user_id": user_id,
            "type": "image",
            "image_url": image_url,
            "content_preview": f"图片: {file.filename}",
            "file_size": file_size
        }

        result = supabase.table("uploads").insert(upload_data).execute()
        upload_id = result.data[0]["id"]

        logger.info(f"上传记录已保存: {upload_id}")

        return UploadResponse(
            upload_id=upload_id,
            type="image",
            status="success",
            message="图片上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传图片失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/url", response_model=UploadResponse)
async def upload_url(
    request: UploadTextRequest,
    authorization: Optional[str] = Header(None)
):
    """上传 URL"""
    try:
        user_id = get_user_from_token(authorization)
        logger.info(f"用户 {user_id} 上传 URL: {request.content}")

        # 验证 URL 格式
        if not request.content.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="无效的 URL 格式")

        # 使用 Jina Reader 预抓取内容（可选，用于生成预览）
        try:
            url_content = await jina_service.fetch_url_content(request.content)
            content_preview = url_content.get("title", request.content)[:200]
        except Exception as e:
            logger.warning(f"预抓取 URL 失败: {str(e)}")
            content_preview = request.content[:200]

        # 保存上传记录
        upload_data = {
            "user_id": user_id,
            "type": "url",
            "content_text": request.content,
            "content_preview": content_preview
        }

        result = supabase.table("uploads").insert(upload_data).execute()
        upload_id = result.data[0]["id"]

        logger.info(f"URL 上传记录已保存: {upload_id}")

        return UploadResponse(
            upload_id=upload_id,
            type="url",
            status="success",
            message="URL 上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传 URL 失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/text", response_model=UploadResponse)
async def upload_text(
    request: UploadTextRequest,
    authorization: Optional[str] = Header(None)
):
    """上传文本"""
    try:
        user_id = get_user_from_token(authorization)
        logger.info(f"用户 {user_id} 上传文本，长度: {len(request.content)}")

        # 验证文本长度
        if len(request.content) < 10:
            raise HTTPException(status_code=400, detail="文本内容过短（至少10个字符）")

        if len(request.content) > 10000:
            raise HTTPException(status_code=400, detail="文本内容过长（最多10000个字符）")

        # 生成预览
        content_preview = request.content[:200]

        # 保存上传记录
        upload_data = {
            "user_id": user_id,
            "type": "text",
            "content_text": request.content,
            "content_preview": content_preview
        }

        result = supabase.table("uploads").insert(upload_data).execute()
        upload_id = result.data[0]["id"]

        logger.info(f"文本上传记录已保存: {upload_id}")

        return UploadResponse(
            upload_id=upload_id,
            type="text",
            status="success",
            message="文本上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文本失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
