"""
推荐内容生成服务
整合搜索结果和 AI 分析，生成个性化推荐磁贴
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from app.services.search import search_service
from app.services.deepseek import deepseek_service
from app.database import supabase

logger = logging.getLogger(__name__)


class RecommenderService:
    def __init__(self):
        self._generation_locks = set()

    async def generate_recommendations(
        self,
        analysis_data: Dict[str, Any],
        user_id: str,
        count: int = 10
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        基于分析结果生成推荐内容

        Args:
            analysis_data: AI 分析结果
            user_id: 用户 ID
            count: 推荐数量

        Returns:
            (推荐磁贴列表, 原始搜索结果列表)
        """
        try:
            logger.info(f"开始为用户 {user_id} 生成 {count} 个推荐")

            # 1. 提取搜索关键词
            search_queries = analysis_data.get("search_queries", [])
            keywords = analysis_data.get("keywords", [])

            if not search_queries and keywords:
                search_queries = keywords[:3]

            if not search_queries:
                raise ValueError("无法提取搜索关键词")

            # 2. 获取用户偏好
            user_preferences = await self._get_user_preferences(user_id)

            # 3. 执行多个搜索查询
            all_results = []
            for query in search_queries[:5]:  # 增加搜索次数限制，覆盖更多联想词
                try:
                    results = await search_service.search(query, max_results=5)
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"搜索查询 '{query}' 失败: {str(e)}")
                    continue

            if not all_results:
                logger.warning("搜索未返回结果，使用默认推荐")
                return self._generate_fallback_recommendations(analysis_data), []

            # 4. 使用 AI 对搜索结果进行评分和分类
            recommendations = await self._rank_and_classify(
                all_results,
                analysis_data,
                user_preferences,
                count
            )

            logger.info(f"成功生成 {len(recommendations)} 个推荐")
            return recommendations, all_results

        except Exception as e:
            logger.error(f"生成推荐失败: {str(e)}", exc_info=True)
            raise Exception(f"生成推荐失败: {str(e)}")

    async def generate_article(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        基于推荐内容和上下文生成深度文章 (HTML)
        返回生成的 HTML，如果因锁等待而未生成（由其他任务处理），返回 None
        """
        rec_id = recommendation.get("id")
        
        # 检查锁
        if rec_id in self._generation_locks:
            logger.info(f"推荐 {rec_id} 正在生成中，等待...")
            while rec_id in self._generation_locks:
                await asyncio.sleep(1)
            logger.info(f"推荐 {rec_id} 等待结束，返回 None")
            return None

        self._generation_locks.add(rec_id)
        
        try:
            logger.info(f"开始为推荐 {rec_id} 生成文章")
            
            # 准备上下文
            search_results = context.get("search_results", [])
            relevant_info = "\n".join([
                f"- {r['title']}: {r['content'][:300]}"
                for r in search_results
            ])
            
            title = recommendation.get("title", "相关内容")
            description = recommendation.get("description", "")
            
            prompt = f"""请基于以下信息，写一篇关于 "{title}" 的深度文章。

文章主题: {title}
简介: {description}

参考资料:
{relevant_info}

要求:
1. **使用中文撰写**，内容深度、专业且引人入胜，篇幅要求 **1500字以上**。
2. 使用 HTML 格式输出（只输出 body 内容，不需要 html/head 标签）。
3. 使用 Tailwind CSS 类名来美化排版 (例如: class="text-2xl font-bold mb-4", class="text-gray-700 mb-4 leading-relaxed", class="bg-gray-50 p-4 rounded-lg border-l-4 border-blue-500 italic")。
4. 包含适当的标题 (h2, h3)、段落 (p)、列表 (ul/li) 和引用 (blockquote)。
5. 如果有相关图片概念，使用 <div class="bg-gray-200 h-64 w-full rounded-lg flex items-center justify-center text-gray-500 mb-6">[图片占位符: 描述]</div> 表示。

请直接返回 HTML 代码。"""

            # 调用 AI 生成
            payload = {
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": [
                    {"role": "system", "content": "你是一位专业的专栏作家和编辑，擅长撰写图文并茂的深度好文。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 5000
            }

            import httpx
            async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                response = await client.post(
                    f"{deepseek_service.base_url}/chat/completions",
                    json=payload,
                    headers=deepseek_service.headers
                )
                response.raise_for_status()
                result = response.json()

            content = result["choices"][0]["message"]["content"]
            
            # 清理可能包含的 markdown 代码块标记
            content = content.replace("```html", "").replace("```", "").strip()
            
            return content

        except Exception as e:
            logger.error(f"生成文章失败: {str(e)}", exc_info=True)
            return f"<div class='p-4 text-red-600'>生成文章失败: {str(e)}</div>"
        finally:
            if rec_id in self._generation_locks:
                self._generation_locks.remove(rec_id)

    async def generate_articles_background(
        self,
        recommendations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ):
        """
        后台批量生成推荐文章
        """
        logger.info(f"开始后台生成 {len(recommendations)} 篇文章")
        
        for rec in recommendations:
            try:
                # 生成文章
                article_html = await self.generate_article(rec, context)
                
                if article_html:
                    # 更新数据库
                    supabase.table("recommendations").update({
                        "article_html": article_html
                    }).eq("id", rec["id"]).execute()
                    
                    logger.info(f"推荐 {rec['id']} 文章生成完成")
                
            except Exception as e:
                logger.error(f"后台生成文章失败 (ID: {rec.get('id')}): {str(e)}")

    async def _get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好"""
        try:
            result = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.warning(f"获取用户偏好失败: {str(e)}")
            return None

    async def _rank_and_classify(
        self,
        search_results: List[Dict[str, Any]],
        analysis_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]],
        count: int
    ) -> List[Dict[str, Any]]:
        """对搜索结果进行排序和分类"""
        try:
            # 构建提示词
            results_text = "\n".join([
                f"{i+1}. {r['title']}: {r['content'][:200]}"
                for i, r in enumerate(search_results[:15])
            ])

            user_pref_text = ""
            if user_preferences:
                liked = user_preferences.get("liked_keywords", [])
                disliked = user_preferences.get("disliked_keywords", [])
                if liked:
                    user_pref_text += f"\n用户喜欢: {', '.join(liked[:10])}"
                if disliked:
                    user_pref_text += f"\n用户不喜欢: {', '.join(disliked[:10])}"

            prompt = f"""用户分析结果:
意图: {analysis_data.get('primary_intent', 'unknown')}
兴趣标签: {', '.join(analysis_data.get('interest_tags', []))}
{user_pref_text}

搜索结果:
{results_text}

请从以上搜索结果中选择最相关的 {count} 个，并为每个结果分配类型和评分。
返回 JSON 格式的列表，每项包含:
- index: 原始结果的序号 (1-based)
- tile_type: 类型 (knowledge/product/location/tutorial/news/community)
- relevance_score: 相关性评分 (0.0-1.0)
- why: 推荐理由（一句话）

请直接返回 JSON 数组，不要包含额外文字。"""

            # 调用 AI 进行评分
            payload = {
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": [
                    {"role": "system", "content": "你是推荐系统专家，擅长根据用户兴趣筛选内容。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }

            import httpx
            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                response = await client.post(
                    f"{deepseek_service.base_url}/chat/completions",
                    json=payload,
                    headers=deepseek_service.headers
                )
                response.raise_for_status()
                result = response.json()

            content = result["choices"][0]["message"]["content"]

            # 解析 AI 返回的排序结果
            import json
            try:
                # Find the start and end of the JSON object
                start_index = content.find('[')
                if start_index == -1:
                    start_index = content.find('{')
                end_index = content.rfind(']')
                if end_index == -1:
                    end_index = content.rfind('}')
                
                if start_index != -1 and end_index != -1:
                    json_str = content[start_index:end_index+1]
                    rankings = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON object found", content, 0)
            except json.JSONDecodeError:
                # 如果解析失败，使用默认排序
                logger.warning(f"AI 返回结果解析失败，使用默认排序. Content: {content}")
                rankings = [
                    {"index": i+1, "tile_type": "knowledge", "relevance_score": 0.7, "why": "相关内容"}
                    for i in range(min(count, len(search_results)))
                ]

            # 构建最终推荐列表
            recommendations = []
            for rank in rankings[:count]:
                idx = rank.get("index", 1) - 1
                if 0 <= idx < len(search_results):
                    original = search_results[idx]
                    recommendations.append({
                        "title": original["title"],
                        "description": original["content"][:300],
                        "url": original["url"],
                        "image_url": None,  # 可以后续增加图片抓取
                        "source": original["source"],
                        "relevance_score": rank.get("relevance_score", 0.5),
                        "tile_type": rank.get("tile_type", "knowledge"),
                        "display_order": len(recommendations)
                    })

            return recommendations

        except Exception as e:
            logger.error(f"排序和分类失败: {str(e)}", exc_info=True)
            # 返回简化版推荐
            return [
                {
                    "title": r["title"],
                    "description": r["content"][:300],
                    "url": r["url"],
                    "image_url": None,
                    "source": r["source"],
                    "relevance_score": r.get("score", 0.5),
                    "tile_type": "knowledge",
                    "display_order": i
                }
                for i, r in enumerate(search_results[:count])
            ]

    def _generate_fallback_recommendations(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成备用推荐（当搜索失败时）"""
        keywords = analysis_data.get("keywords", [])
        return [
            {
                "title": f"探索更多关于 {keyword} 的内容",
                "description": "由于搜索服务暂时不可用，请稍后重试或手动搜索相关内容。",
                "url": f"https://www.google.com/search?q={keyword}",
                "image_url": None,
                "source": "fallback",
                "relevance_score": 0.5,
                "tile_type": "knowledge",
                "display_order": i
            }
            for i, keyword in enumerate(keywords[:5])
        ]


# 创建全局实例
recommender_service = RecommenderService()
