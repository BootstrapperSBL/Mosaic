'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import useSWR, { mutate } from 'swr'
import api, { historyAPI, type HistoryItem } from '@/lib/api'

const fetcher = (url: string) => api.get(url).then(res => res.data)
const HISTORY_KEY = '/api/history/?page=1&page_size=50'

interface SidebarProps {
  onAddSource: () => void
  user: any
  onSignOut: () => void
}

export default function Sidebar({ onAddSource, user, onSignOut }: SidebarProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const currentAnalysisId = searchParams.get('analysis')
  
  const { data, error, isLoading } = useSWR(HISTORY_KEY, fetcher, {
    refreshInterval: 30000, // 每30秒自动刷新一次
    revalidateOnFocus: true
  })
  
  const historyItems: HistoryItem[] = data?.items || []

  const handleSelect = (item: HistoryItem) => {
    if (item.analysis_id) {
      router.push(`/dashboard?analysis=${item.analysis_id}`)
    } else {
      alert("该内容尚未分析完成或分析失败")
    }
  }

  const handleDelete = async (e: React.MouseEvent, itemId: string) => {
    e.stopPropagation() // Prevent triggering selection
    if (!confirm('确定要删除这条记录吗？相关的分析和推荐也将一并删除。')) return

    try {
      await historyAPI.delete(itemId)
      // 乐观更新：先过滤掉，然后重新验证
      mutate(HISTORY_KEY, { ...data, items: historyItems.filter(i => i.id !== itemId) }, false)
      // If deleted item was selected, clear selection
      if (currentAnalysisId && historyItems.find(i => i.id === itemId)?.analysis_id === currentAnalysisId) {
        router.push('/dashboard')
      }
    } catch (error) {
      console.error('Delete failed', error)
      alert('删除失败，请稍后重试')
      mutate(HISTORY_KEY) // 失败后恢复数据
    }
  }

  const getTypeEmoji = (type: string) => {
    const map: Record<string, string> = { image: '🖼️', url: '🔗', text: '📝' }
    return map[type] || '📄'
  }

  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <span className="mr-2">🧩</span> Mosaic
        </h1>
        <button
          onClick={onAddSource}
          className="w-full bg-white border-2 border-dashed border-gray-300 text-gray-600 hover:border-blue-500 hover:text-blue-600 font-medium py-2 px-4 rounded-xl transition flex items-center justify-center space-x-2"
        >
          <span>+</span>
          <span>添加内容源 (Source)</span>
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
        {isLoading ? (
          <div className="flex justify-center p-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div>
          </div>
        ) : historyItems.length === 0 ? (
          <div className="text-center text-gray-400 text-sm p-4">
            暂无历史记录
          </div>
        ) : (
          historyItems.map((item) => (
            <div
              key={item.id}
              onClick={() => handleSelect(item)}
              className={`group flex items-start p-3 rounded-lg cursor-pointer transition-all ${
                item.analysis_id === currentAnalysisId
                  ? 'bg-blue-100 border-blue-200 shadow-sm'
                  : 'hover:bg-gray-100'
              }`}
            >
              <span className="text-xl mr-3">{getTypeEmoji(item.type)}</span>
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-start">
                  <p className={`text-sm font-medium truncate pr-6 ${
                    item.analysis_id === currentAnalysisId ? 'text-blue-900' : 'text-gray-700'
                  }`}>
                    {item.content_preview}
                  </p>
                  
                  <button
                    onClick={(e) => handleDelete(e, item.id)}
                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 transition-opacity p-1 -mr-1"
                    title="删除"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-gray-400">
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                  {item.recommendation_count > 0 && (
                    <span className="text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded-full">
                      {item.recommendation_count}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
      
      {/* User Info / Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 min-w-0">
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-sm">
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-700 truncate" title={user?.email}>
                {user?.email}
              </p>
            </div>
          </div>
          <button
            onClick={onSignOut}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
            title="退出登录"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
