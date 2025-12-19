'use client'

import { useEffect, useState } from 'react'
import useSWR from 'swr'
import api from '@/lib/api'
import AnalysisResult from './AnalysisResult'
import RecommendationGrid from './RecommendationGrid'
import TaskProgress from './TaskProgress'

interface MainContentProps {
  analysisId: string | null
  taskId: string | null
  onAnalysisComplete: (id: string, data?: any) => void
}

const analysisFetcher = (url: string) => api.get(url).then(response => {
  // Normalize data structure for AnalysisResult component
  let data = response.data.full_context || {
    deep_decode: {
      visual_description: response.data.visual_description,
      extracted_text: response.data.extracted_text
    },
    contextual_expand: response.data.intent_analysis
  }

  // Ensure original_content is present
  if (response.data.original_content) {
    data = { ...data, original_content: response.data.original_content }
  }
  return data
})

export default function MainContent({ analysisId, taskId, onAnalysisComplete }: MainContentProps) {
  const { data: analysisData, isLoading } = useSWR(
    analysisId ? `/api/analysis/${analysisId}` : null,
    analysisFetcher
  )

  if (taskId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-white">
        <div className="w-full max-w-2xl">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            正在分析您的内容... (AI Processing)
          </h2>
          <TaskProgress taskId={taskId} onComplete={onAnalysisComplete} />
        </div>
      </div>
    )
  }

  if (!analysisId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-gray-50 text-gray-500">
        <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center mb-6 text-4xl">
          👈
        </div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">选择一个内容源 (Source)</h2>
        <p>从左侧列表选择历史记录，或点击 "+" 添加新内容。</p>
      </div>
    )
  }

  return (
    <div className="flex-1 h-full overflow-y-auto bg-gray-50 p-6 sm:p-8 custom-scrollbar">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header Section */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">分析与洞察 (Insights)</h1>
          {/* Controls could go here */}
        </div>

        {/* 1. Context / Process (Analysis Result) */}
        {isLoading ? (
          <div className="h-64 bg-white rounded-xl animate-pulse"></div>
        ) : (
          <div className="space-y-4">
             {/* We can organize AnalysisResult to look more like 'Notes' */}
             <AnalysisResult data={analysisData} />
          </div>
        )}

        {/* Divider */}
        <div className="border-t border-gray-200"></div>

        {/* 2. Output (Recommendations) */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">为您推荐 (Recommendations)</h2>
          <RecommendationGrid analysisId={analysisId} />
        </div>
        
      </div>
    </div>
  )
}
