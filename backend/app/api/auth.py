"""
认证相关 API
使用 Supabase Auth
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from app.database import supabase

logger = logging.getLogger(__name__)

router = APIRouter()


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user_id: str
    email: str
    access_token: str
    refresh_token: str


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignUpRequest):
    """用户注册"""
    try:
        logger.info(f"用户注册请求: {request.email}")

        # 使用 Supabase Auth 注册
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password
        })

        if not response.user:
            raise HTTPException(status_code=400, detail="注册失败")

        user = response.user
        session = response.session

        # 创建用户 profile
        if request.username:
            try:
                supabase.table("user_profiles").insert({
                    "id": user.id,
                    "username": request.username
                }).execute()
            except Exception as e:
                logger.warning(f"创建用户 profile 失败: {str(e)}")

        # 初始化用户偏好
        try:
            supabase.table("user_preferences").insert({
                "user_id": user.id,
                "liked_keywords": [],
                "disliked_keywords": [],
                "preferred_tile_types": [],
                "avoided_tile_types": []
            }).execute()
        except Exception as e:
            logger.warning(f"初始化用户偏好失败: {str(e)}")

        logger.info(f"用户注册成功: {user.id}")

        return AuthResponse(
            user_id=user.id,
            email=user.email,
            access_token=session.access_token,
            refresh_token=session.refresh_token
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.post("/signin", response_model=AuthResponse)
async def signin(request: SignInRequest):
    """用户登录"""
    try:
        logger.info(f"用户登录请求: {request.email}")

        # 使用 Supabase Auth 登录
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if not response.user or not response.session:
            raise HTTPException(status_code=401, detail="邮箱或密码错误")

        user = response.user
        session = response.session

        logger.info(f"用户登录成功: {user.id}")

        return AuthResponse(
            user_id=user.id,
            email=user.email,
            access_token=session.access_token,
            refresh_token=session.refresh_token
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


@router.post("/signout")
async def signout(authorization: Optional[str] = Header(None)):
    """用户登出"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="未提供认证信息")

        # Supabase 会自动处理 token
        supabase.auth.sign_out()

        logger.info("用户登出成功")
        return {"message": "登出成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登出失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"登出失败: {str(e)}")


@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """获取当前用户信息"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="未提供认证信息")

        token = authorization.replace("Bearer ", "")

        # 验证 token 并获取用户信息
        user = supabase.auth.get_user(token)

        if not user:
            raise HTTPException(status_code=401, detail="无效的认证信息")

        return {
            "user_id": user.user.id,
            "email": user.user.email
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")
