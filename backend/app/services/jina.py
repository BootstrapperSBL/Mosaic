"""
Jina Reader 服务
用于将 URL 网页转换为干净的 Markdown 格式
"""
import httpx
import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class JinaReaderService:
    def __init__(self):
        self.api_key = settings.JINA_API_KEY
        self.base_url = "https://r.jina.ai"

    async def fetch_url_content(self, url: str) -> Dict[str, Any]:
        """
        使用 Jina Reader 获取 URL 内容并转换为 Markdown

        Args:
            url: 要抓取的 URL

        Returns:
            包含标题、内容、摘要的字典
        """
        try:
            logger.info(f"开始使用 Jina Reader 抓取 URL: {url}")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "X-Return-Format": "markdown"
            }

            # 禁用 trust_env 以避免代理问题，并增加超时时间
            async with httpx.AsyncClient(timeout=60.0, trust_env=False, follow_redirects=True) as client:
                response = await client.get(
                    f"{self.base_url}/{url}",
                    headers=headers
                )
                response.raise_for_status()

                # Jina Reader 返回的是 Markdown 文本
                markdown_content = response.text

            logger.info(f"Jina Reader 抓取成功，内容长度: {len(markdown_content)}")

            # 提取标题（第一行通常是标题）
            lines = markdown_content.split('\n')
            title = lines[0].replace('#', '').strip() if lines else "无标题"

            # 生成摘要（前 500 字符）
            summary = markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content

            return {
                "title": title,
                "content": markdown_content,
                "summary": summary,
                "url": url,
                "content_length": len(markdown_content)
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Jina Reader HTTP 错误: {e.response.status_code} - {e.response.text}")
            raise Exception(f"URL 抓取失败 (HTTP {e.response.status_code}): {str(e)}")
        except Exception as e:
            logger.error(f"Jina Reader 抓取失败: {str(e)}", exc_info=True)
            raise Exception(f"URL 抓取失败: {str(e)}")


# 创建全局实例
jina_service = JinaReaderService()
