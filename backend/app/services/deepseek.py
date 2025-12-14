"""
DeepSeek AI 服务
集成 DeepSeek-OCR (视觉理解) 和 DeepSeek-V3.2 (文本推理)
"""
import httpx
import logging
import base64
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class DeepSeekService:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def analyze_image(self, image_data: str, is_url: bool = False) -> Dict[str, Any]:
        """
        使用 DeepSeek-OCR 分析图片

        Args:
            image_data: Base64 编码的图片数据或图片 URL
            is_url: 是否为 URL

        Returns:
            包含视觉描述和提取文本的字典
        """
        try:
            logger.info("开始使用 DeepSeek-OCR 分析图片")

            # 构建图片内容
            if is_url:
                image_content = {"type": "image_url", "image_url": {"url": image_data}}
            else:
                # 确保 base64 字符串格式正确
                if not image_data.startswith("data:image"):
                    image_data = f"data:image/jpeg;base64,{image_data}"
                image_content = {"type": "image_url", "image_url": {"url": image_data}}

            # 构建请求体
            payload = {
                "model": "deepseek-ai/DeepSeek-OCR",  # DeepSeek-OCR 模型
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            image_content,
                            {
                                "type": "text",
                                "text": """请详细分析这张图片，并以 JSON 格式返回以下信息：
1. visual_description: 图片的整体视觉描述（场景、物体、颜色、构图等）
2. extracted_text: 图片中的所有文字内容（如果有）
3. scene_type: 场景类型（如：游戏、购物、文章、社交媒体、设计作品等）
4. main_subjects: 主要对象列表
5. possible_intent: 用户可能感兴趣的方向（攻略、购买、学习、欣赏等）

请直接返回 JSON，不要包含额外的解释文字。"""
                            }
                        ]
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }

            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()

            # 解析结果
            content = result["choices"][0]["message"]["content"]
            logger.info(f"DeepSeek-OCR 分析完成: {content[:200]}...")

            # 尝试解析 JSON
            import json
            try:
                # Find the start and end of the JSON object
                start_index = content.find('{')
                end_index = content.rfind('}')
                if start_index != -1 and end_index != -1:
                    json_str = content[start_index:end_index+1]
                    parsed_result = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON object found", content, 0)
            except json.JSONDecodeError:
                # 如果不是标准 JSON，返回原始内容
                logger.warning(f"Failed to parse JSON from DeepSeek OCR response: {content}")
                parsed_result = {
                    "visual_description": content,
                    "extracted_text": "",
                    "scene_type": "unknown",
                    "main_subjects": [],
                    "possible_intent": []
                }

            return parsed_result

        except Exception as e:
            logger.error(f"DeepSeek-OCR 分析失败: {str(e)}", exc_info=True)
            raise Exception(f"图片分析失败: {str(e)}")

    async def analyze_text_content(self, content: str) -> str:
        """
        深度分析文本内容，提取关键信息（摘要、事件、人物、技术等）
        返回纯文本分析结果
        """
        try:
            logger.info("开始使用 DeepSeek-V3 分析文本内容")

            payload = {
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的内容分析师，擅长从长文中提取核心价值和关键信息。"
                    },
                    {
                        "role": "user",
                        "content": f"""请深度阅读并分析以下内容：

{content[:30000]}  # 限制长度以避免超长

请提供一份结构化的分析报告，包含以下部分（如果没有相关信息则跳过）：
1. **内容摘要**：一句话概括核心内容。
2. **关键信息**：列出3-5个最重要的观点或事实。
3. **关键事件/时间线**：如果有时间线或特定事件，请列出。
4. **涉及人物/地点**：提到的重要人物或地点。
5. **专业术语/技术/方法**：提到的专业概念、技术栈或方法论。

请直接输出分析结果，格式清晰易读（可以使用 Markdown 列表）。"""
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }

            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()

            analysis = result["choices"][0]["message"]["content"]
            return analysis

        except Exception as e:
            logger.error(f"文本内容分析失败: {str(e)}", exc_info=True)
            return "无法生成内容分析"

    async def analyze_intent(
        self,
        content: str,
        visual_context: Optional[Dict[str, Any]] = None,
        user_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        使用 DeepSeek-V3.2 进行意图分析和关键词提取

        Args:
            content: 要分析的文本内容
            visual_context: 可选的视觉上下文（来自图片分析）
            user_history: 可选的用户历史偏好

        Returns:
            包含意图分析、关键词、兴趣标签的字典
        """
        try:
            logger.info("开始使用 DeepSeek-V3.2 进行意图分析")

            # 构建上下文信息
            context_parts = [f"内容: {content}"]

            if visual_context:
                context_parts.append(f"视觉信息: {visual_context}")

            if user_history:
                context_parts.append(f"用户历史偏好: {', '.join(user_history[:10])}")

            context = "\n".join(context_parts)

            # 构建请求体
            payload = {
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个具有发散性思维的用户意图分析专家。请站在用户的视角，深度挖掘内容背后的潜在需求、兴趣点和关联话题。"
                    },
                    {
                        "role": "user",
                        "content": f"""{context}

请深度分析以上内容，进行联想扩展，以 JSON 格式返回：
1. primary_intent: 主要意图（学习知识、购买产品、寻找攻略、娱乐欣赏、社交分享等）
2. interest_level: 兴趣强度 (1-10)
3. keywords: 核心关键词列表（8-12个），包含具体名词和抽象概念。
4. interest_tags: 兴趣标签列表（如：游戏、咖啡、设计、旅行等）。
5. search_queries: 建议的搜索关键词列表（6-8个）。请务必包含：
   - 核心直接搜索词
   - 用户可能关心的具体问题（如“怎么做”、“哪里买”、“好用吗”）
   - 联想扩展词（如相关竞品、上下游知识、行业趋势）
6. content_preferences: 推荐的内容类型（知识图谱、产品链接、线下地点、教程视频等）
7. reasoning: 简短的分析理由

请直接返回 JSON，不要包含额外的解释文字。"""
                    }
                ],
                "temperature": 0.7,  # 稍微提高温度以增加发散性
                "max_tokens": 1500
            }

            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()

            # 解析结果
            content = result["choices"][0]["message"]["content"]
            logger.info(f"DeepSeek-V3.2 意图分析完成: {content[:200]}...")

            # 尝试解析 JSON
            import json
            try:
                # Find the start and end of the JSON object
                start_index = content.find('{')
                end_index = content.rfind('}')
                if start_index != -1 and end_index != -1:
                    json_str = content[start_index:end_index+1]
                    parsed_result = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON object found", content, 0)
            except json.JSONDecodeError:
                # 如果不是标准 JSON，提取关键信息
                logger.warning(f"Failed to parse JSON from DeepSeek response: {content}")
                parsed_result = {
                    "primary_intent": "explore",
                    "interest_level": 5,
                    "keywords": [],
                    "interest_tags": [],
                    "search_queries": [],
                    "content_preferences": [],
                    "reasoning": content[:500]
                }

            return parsed_result

        except Exception as e:
            logger.error(f"DeepSeek-V3.2 意图分析失败: {str(e)}", exc_info=True)
            raise Exception(f"意图分析失败: {str(e)}")


# 创建全局实例
deepseek_service = DeepSeekService()
