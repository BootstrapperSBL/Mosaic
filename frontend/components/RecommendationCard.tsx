'use client'

import { useState } from 'react'
import { type RecommendationTile } from '@/lib/api'

interface RecommendationCardProps {
  recommendation: RecommendationTile
  onFeedback: (id: string, action: 'keep' | 'discard') => void
  onReadArticle?: (id: string) => void
}

export default function RecommendationCard({ recommendation, onFeedback, onReadArticle }: RecommendationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [feedbackLoading, setFeedbackLoading] = useState(false)

  const handleFeedback = async (action: 'keep' | 'discard') => {
    setFeedbackLoading(true)
    try {
      await onFeedback(recommendation.id, action)
    } finally {
      setFeedbackLoading(false)
    }
  }
  
  const handleReadClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onReadArticle) {
      onReadArticle(recommendation.id)
    }
  }

  const getTileTypeEmoji = (type: string) => {
    const emojiMap: Record<string, string> = {
      knowledge: '📚',
      product: '🛍️',
      location: '📍',
      tutorial: '🎓',
      news: '📰',
      community: '💬',
    }
    return emojiMap[type] || '🔖'
  }

  const getTileTypeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      knowledge: 'bg-blue-100 text-blue-700',
      product: 'bg-green-100 text-green-700',
      location: 'bg-purple-100 text-purple-700',
      tutorial: 'bg-orange-100 text-orange-700',
      news: 'bg-red-100 text-red-700',
      community: 'bg-pink-100 text-pink-700',
    }
    return colorMap[type] || 'bg-gray-100 text-gray-700'
  }

  const userAction = recommendation.user_action

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border overflow-hidden transition-all hover:shadow-md ${
        userAction === 'discard' ? 'opacity-50' : ''
      } ${userAction === 'keep' ? 'ring-2 ring-green-400' : ''}`}
    >
      {/* 图片（如果有） */}
      {recommendation.image_url && (
        <img
          src={recommendation.image_url}
          alt={recommendation.title}
          className="w-full h-48 object-cover"
        />
      )}

      {/* 内容 */}
      <div className="p-4">
        {/* 类型标签 */}
        <div className="flex items-center justify-between mb-3">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTileTypeColor(
              recommendation.tile_type
            )}`}
          >
            <span className="mr-1">{getTileTypeEmoji(recommendation.tile_type)}</span>
            {recommendation.tile_type}
          </span>
          <span className="text-xs text-gray-500">
            {Math.round(recommendation.relevance_score * 100)}% 相关
          </span>
        </div>

        {/* 标题 */}
        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
          {recommendation.title}
        </h3>

        {/* 描述 */}
        <p
          className={`text-sm text-gray-600 ${
            isExpanded ? '' : 'line-clamp-3'
          } mb-3`}
        >
          {recommendation.description}
        </p>

        {recommendation.description.length > 150 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-blue-600 hover:text-blue-700 mb-3"
          >
            {isExpanded ? '收起' : '展开'}
          </button>
        )}
        
        {/* 阅读文章按钮 */}
        {onReadArticle && (
          <button
            onClick={handleReadClick}
            className="w-full mb-3 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition flex items-center justify-center space-x-2"
          >
            <span>📖</span>
            <span>阅读深度文章</span>
          </button>
        )}

        {/* 来源 */}
        {recommendation.url && (
          <a
            href={recommendation.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-gray-500 hover:text-blue-600 block mb-3 truncate"
          >
            🔗 {recommendation.url}
          </a>
        )}

        {/* 操作按钮 */}
        {!userAction && (
          <div className="flex space-x-2 pt-3 border-t">
            <button
              onClick={() => handleFeedback('keep')}
              disabled={feedbackLoading}
              className="flex-1 bg-green-50 text-green-700 hover:bg-green-100 px-4 py-2 rounded-lg font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              👍 保留
            </button>
            <button
              onClick={() => handleFeedback('discard')}
              disabled={feedbackLoading}
              className="flex-1 bg-red-50 text-red-700 hover:bg-red-100 px-4 py-2 rounded-lg font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              👎 丢弃
            </button>
          </div>
        )}

        {/* 已反馈状态 */}
        {userAction && (
          <div className="pt-3 border-t">
            <div
              className={`text-center py-2 rounded-lg font-medium ${
                userAction === 'keep'
                  ? 'bg-green-50 text-green-700'
                  : 'bg-gray-50 text-gray-500'
              }`}
            >
              {userAction === 'keep' ? '✅ 已保留' : '🗑️ 已丢弃'}
            </div>
          </div>
        )}
      </div>

      {/* 来源标记 */}
      <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
        来源: {recommendation.source}
      </div>
    </div>
  )
}
