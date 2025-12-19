'use client'

import { useState, useEffect } from 'react'
import Masonry from 'react-masonry-css'
import { recommendationsAPI, type RecommendationTile } from '@/lib/api'
import RecommendationCard from './RecommendationCard'
import ArticleModal from './ArticleModal'

interface RecommendationGridProps {
  analysisId: string
}

export default function RecommendationGrid({ analysisId }: RecommendationGridProps) {
  const [recommendations, setRecommendations] = useState<RecommendationTile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Modal State
  const [modalOpen, setModalOpen] = useState(false)
  const [modalTitle, setModalTitle] = useState('')
  const [articleHtml, setArticleHtml] = useState('')
  const [articleLoading, setArticleLoading] = useState(false)
  const [currentRecId, setCurrentRecId] = useState<string | null>(null)

  useEffect(() => {
    loadRecommendations()
  }, [analysisId])
  
  const handleRegenerate = async () => {
    if (!currentRecId) return
    setArticleLoading(true)
    try {
        const response = await recommendationsAPI.getArticle(currentRecId, true)
        setArticleHtml(response.data.article_html)
        
        // 更新本地状态缓存
        setRecommendations(prev => 
          prev.map(r => r.id === currentRecId ? { ...r, article_html: response.data.article_html } : r)
        )
    } catch (error: any) {
        alert(`重新生成失败: ${error.response?.data?.detail || error.message}`)
    } finally {
        setArticleLoading(false)
    }
  }

  const loadRecommendations = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await recommendationsAPI.get(analysisId)
      setRecommendations(response.data.recommendations)
    } catch (error: any) {
      setError(error.response?.data?.detail || error.message || '加载推荐失败')
    } finally {
      setLoading(false)
    }
  }
  
  const handleFeedback = async (recommendationId: string, action: 'keep' | 'discard') => {
    try {
      const response = await recommendationsAPI.feedback(recommendationId, action)

      // 如果返回了更新后的推荐，使用新的推荐列表
      if (response.data.updated_recommendations) {
        setRecommendations(response.data.updated_recommendations)
      } else {
        // 否则只更新当前卡片的状态
        setRecommendations(prev =>
          prev.map(rec =>
            rec.id === recommendationId
              ? { ...rec, user_action: action }
              : rec
          )
        )
      }
    } catch (error: any) {
      alert(`反馈失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleReadArticle = async (recommendationId: string) => {
    const rec = recommendations.find(r => r.id === recommendationId)
    if (!rec) return
    
    setCurrentRecId(recommendationId)
    setModalTitle(rec.title)
    setArticleHtml('') // 清空之前的
    setModalOpen(true)
    setArticleLoading(true)
    
    try {
      // 检查本地是否已有 (虽然 API 也会检查，但前端缓存更好)
      if (rec.article_html) {
        setArticleHtml(rec.article_html)
      } else {
        const response = await recommendationsAPI.getArticle(recommendationId)
        setArticleHtml(response.data.article_html)
        
        // 更新本地状态缓存，避免下次点击再次请求
        setRecommendations(prev => 
          prev.map(r => r.id === recommendationId ? { ...r, article_html: response.data.article_html } : r)
        )
      }
    } catch (error: any) {
      alert(`无法加载文章: ${error.response?.data?.detail || error.message}`)
      setModalOpen(false)
    } finally {
      setArticleLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <p className="text-gray-600">正在加载推荐内容...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg">
        {error}
      </div>
    )
  }

  if (recommendations.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">暂无推荐内容</p>
      </div>
    )
  }

  // 瀑布流断点配置
  const breakpointColumns = {
    default: 3,
    1100: 2,
    700: 1
  }

  return (
    <div>
      <Masonry
        breakpointCols={breakpointColumns}
        className="flex -ml-4 w-auto"
        columnClassName="pl-4 bg-clip-padding"
      >
        {recommendations.map((rec) => (
          <div key={rec.id} className="mb-4">
            <RecommendationCard
              recommendation={rec}
              onFeedback={handleFeedback}
              onReadArticle={handleReadArticle}
            />
          </div>
        ))}
      </Masonry>
      
      <ArticleModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={modalTitle}
        contentHtml={articleHtml}
        isLoading={articleLoading}
        onRegenerate={handleRegenerate}
      />
    </div>
  )
}
