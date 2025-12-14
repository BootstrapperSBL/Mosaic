'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabase'
import { historyAPI, type HistoryItem } from '@/lib/api'

export default function History() {
  const router = useRouter()
  const [items, setItems] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  useEffect(() => {
    checkUser()
    loadHistory()
  }, [page])

  async function checkUser() {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) {
      router.push('/auth/signin')
    }
  }

  const loadHistory = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await historyAPI.list(page, pageSize)
      setItems(response.data.items)
      setTotal(response.data.total)
    } catch (error: any) {
      setError(error.response?.data?.detail || error.message || '加载历史记录失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (uploadId: string) => {
    if (!confirm('确定要删除这条记录吗？')) return

    try {
      await historyAPI.delete(uploadId)
      // 重新加载当前页
      loadHistory()
    } catch (error: any) {
      alert(`删除失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleViewRecommendations = (analysisId: string) => {
    router.push(`/dashboard?analysis=${analysisId}`)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getTypeEmoji = (type: string) => {
    const emojiMap: Record<string, string> = {
      image: '🖼️',
      url: '🔗',
      text: '📝',
    }
    return emojiMap[type] || '📄'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-gray-600 hover:text-gray-900"
              >
                ← 返回
              </button>
              <h1 className="text-2xl font-bold text-gray-900">历史记录</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容区 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && page === 1 ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">加载中...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg">
            {error}
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">暂无历史记录</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              开始使用
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* 时间线 */}
            <div className="relative">
              {items.map((item, index) => (
                <div key={item.id} className="relative pb-8">
                  {/* 时间线竖线 */}
                  {index !== items.length - 1 && (
                    <div className="absolute left-5 top-8 bottom-0 w-0.5 bg-gray-200"></div>
                  )}

                  <div className="relative flex items-start space-x-4">
                    {/* 时间线圆点 */}
                    <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-xl">
                      {getTypeEmoji(item.type)}
                    </div>

                    {/* 内容卡片 */}
                    <div className="flex-1 bg-white rounded-xl shadow-sm border p-6">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-xs font-medium text-gray-500 uppercase">
                              {item.type}
                            </span>
                            <span className="text-xs text-gray-400">•</span>
                            <span className="text-xs text-gray-500">
                              {formatDate(item.created_at)}
                            </span>
                          </div>
                          <p className="text-gray-700 mb-2">{item.content_preview}</p>
                          {item.analysis_summary && (
                            <p className="text-sm text-gray-500 italic">
                              {item.analysis_summary}
                            </p>
                          )}
                        </div>

                        <button
                          onClick={() => handleDelete(item.id)}
                          className="ml-4 text-gray-400 hover:text-red-600 transition"
                          title="删除"
                        >
                          🗑️
                        </button>
                      </div>

                      {item.full_context && (
                        <details className="mt-4">
                          <summary className="text-sm font-semibold text-gray-600 cursor-pointer">查看分析详情</summary>
                          <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
                            {JSON.stringify(item.full_context, null, 2)}
                          </pre>
                        </details>
                      )}

                      {item.analysis_id && item.recommendation_count > 0 && (
                        <div className="mt-4 pt-4 border-t flex items-center justify-between">
                          <span className="text-sm text-gray-600">
                            {item.recommendation_count} 个推荐
                          </span>
                          <button
                            onClick={() => handleViewRecommendations(item.analysis_id!)}
                            className="text-blue-600 hover:text-blue-700 font-medium text-sm"
                          >
                            查看推荐 →
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* 分页 */}
            {total > pageSize && (
              <div className="flex justify-center items-center space-x-4 pt-8">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1 || loading}
                  className="px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  上一页
                </button>
                <span className="text-gray-600">
                  第 {page} 页 / 共 {Math.ceil(total / pageSize)} 页
                </span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= Math.ceil(total / pageSize) || loading}
                  className="px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  下一页
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
