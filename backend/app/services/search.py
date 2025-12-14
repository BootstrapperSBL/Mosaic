"""
搜索服务
支持 Tavily AI 和 Serper.dev 双搜索引擎
"""
import httpx
import logging
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self):
        self.tavily_api_key = settings.TAVILY_API_KEY
        self.serper_api_key = settings.SERPER_API_KEY
        self.provider = settings.SEARCH_PROVIDER

    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        搜索内容

        Args:
            query: 搜索关键词
            max_results: 最大结果数量

        Returns:
            搜索结果列表
        """
        if self.provider == "tavily":
            return await self._search_tavily(query, max_results)
        elif self.provider == "serper":
            return await self._search_serper(query, max_results)
        else:
            raise ValueError(f"不支持的搜索引擎: {self.provider}")

    async def _search_tavily(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """使用 Tavily AI 搜索"""
        try:
            if not self.tavily_api_key:
                raise ValueError("Tavily API Key 未配置")

            logger.info(f"使用 Tavily 搜索: {query}")

            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "advanced",  # basic 或 advanced
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False
            }

            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

            # 转换为统一格式
            results = []
            for item in result.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.5),
                    "source": "tavily"
                })

            logger.info(f"Tavily 搜索完成，返回 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"Tavily 搜索失败: {str(e)}", exc_info=True)
            raise Exception(f"Tavily 搜索失败: {str(e)}")

    async def _search_serper(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """使用 Serper.dev 搜索"""
        try:
            if not self.serper_api_key:
                raise ValueError("Serper API Key 未配置")

            logger.info(f"使用 Serper 搜索: {query}")

            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "q": query,
                "num": max_results
            }

            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()

            # 转换为统一格式
            results = []
            for item in result.get("organic", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "content": item.get("snippet", ""),
                    "score": 0.7,  # Serper 不提供评分，给一个默认值
                    "source": "serper"
                })

            logger.info(f"Serper 搜索完成，返回 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"Serper 搜索失败: {str(e)}", exc_info=True)
            raise Exception(f"Serper 搜索失败: {str(e)}")


# 创建全局实例
search_service = SearchService()
