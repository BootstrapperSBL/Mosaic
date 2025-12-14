'use client'

import { useState, useEffect } from 'react'
import { analysisAPI, type TaskStatus } from '@/lib/api'

interface TaskProgressProps {
  taskId: string
  onComplete: (analysisId: string, resultData?: any) => void
}

export default function TaskProgress({ taskId, onComplete }: TaskProgressProps) {
  const [task, setTask] = useState<TaskStatus | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let interval: NodeJS.Timeout

    const checkStatus = async () => {
      try {
        const response = await analysisAPI.getTaskStatus(taskId)
        const taskData = response.data

        setTask(taskData)

        if (taskData.status === 'completed') {
          clearInterval(interval)
          if (taskData.result?.final_result?.analysis_id) {
            // 传递完整的结果数据
            onComplete(taskData.result.final_result.analysis_id, taskData.result)
          }
        } else if (taskData.status === 'failed') {
          clearInterval(interval)
          setError(taskData.error || '分析失败')
        }
      } catch (error: any) {
        setError(error.response?.data?.detail || error.message || '获取任务状态失败')
        clearInterval(interval)
      }
    }

    // 立即检查一次
    checkStatus()

    // 每2秒轮询一次
    interval = setInterval(checkStatus, 2000)

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [taskId, onComplete])

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <div className="flex items-start space-x-3">
          <div className="text-2xl">❌</div>
          <div className="flex-1">
            <h3 className="font-semibold text-red-900 mb-1">分析失败</h3>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!task) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="text-blue-900">正在初始化...</span>
        </div>
      </div>
    )
  }

  const getStepInfo = (progress: number) => {
    if (progress < 20) return { step: 1, name: '准备数据', icon: '📥' }
    if (progress < 40) return { step: 2, name: '深度解析 (Deep Decode)', icon: '🔍' }
    if (progress < 60) return { step: 3, name: '关联扩展 (Contextual Expand)', icon: '🧠' }
    if (progress < 100) return { step: 4, name: '动态拼贴 (Dynamic Mosaic)', icon: '🎨' }
    return { step: 5, name: '完成', icon: '✅' }
  }

  const stepInfo = getStepInfo(task.progress)

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-6">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">{stepInfo.icon}</span>
            <h3 className="font-semibold text-gray-900">{task.result?.step_message || stepInfo.name}</h3>
          </div>
          <span className="text-sm font-medium text-gray-600">{task.progress}%</span>
        </div>

        {/* 进度条 */}
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-full rounded-full transition-all duration-500 ease-out"
            style={{ width: `${task.progress}%` }}
          >
            <div className="h-full w-full bg-white/20 animate-pulse"></div>
          </div>
        </div>
      </div>

      {/* 步骤指示器 */}
      <div className="flex justify-between items-center text-xs text-gray-600">
        <div className={stepInfo.step >= 1 ? 'text-blue-600 font-medium' : ''}>
          准备
        </div>
        <div className={stepInfo.step >= 2 ? 'text-blue-600 font-medium' : ''}>
          解析
        </div>
        <div className={stepInfo.step >= 3 ? 'text-blue-600 font-medium' : ''}>
          扩展
        </div>
        <div className={stepInfo.step >= 4 ? 'text-blue-600 font-medium' : ''}>
          拼贴
        </div>
        <div className={stepInfo.step >= 5 ? 'text-green-600 font-medium' : ''}>
          完成
        </div>
      </div>

      {/* 关键词预览（如果有） */}
      {(task.result?.contextual_expand?.keywords || task.result?.final_result?.keywords) && (
        <div className="mt-4 pt-4 border-t border-blue-200">
          <p className="text-sm text-gray-600 mb-2">识别的关键词：</p>
          <div className="flex flex-wrap gap-2">
            {(task.result?.contextual_expand?.keywords || task.result?.final_result?.keywords).slice(0, 5).map((keyword: string, index: number) => (
              <span
                key={index}
                className="px-3 py-1 bg-white rounded-full text-sm text-gray-700 shadow-sm"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 意图分析结果 */}
      {task.result?.contextual_expand && (
        <div className="mt-4 pt-4 border-t border-blue-200">
          <p className="text-sm text-gray-600 mb-2">意图分析：</p>
          <div className="text-sm text-gray-700 space-y-1">
            <p><strong>主要意图:</strong> {task.result.contextual_expand.primary_intent}</p>
            <p><strong>兴趣等级:</strong> {task.result.contextual_expand.interest_level} / 10</p>
            <p><strong>兴趣标签:</strong> {task.result.contextual_expand.interest_tags.join(', ')}</p>
          </div>
        </div>
      )}

      {/* DeepSeek 原始结果 */}
      {task.result?.contextual_expand && (
        <details className="mt-4 pt-4 border-t border-blue-200">
          <summary className="text-sm font-semibold text-gray-600 cursor-pointer">查看 DeepSeek 分析详情</summary>
          <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
            {JSON.stringify(task.result.contextual_expand, null, 2)}
          </pre>
        </details>
      )}

      {/* Tavily 搜索结果 */}
      {task.result?.search_results && (
        <details className="mt-4 pt-4 border-t border-blue-200">
          <summary className="text-sm font-semibold text-gray-600 cursor-pointer">查看搜索引擎返回结果</summary>
          <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
            {JSON.stringify(task.result.search_results, null, 2)}
          </pre>
        </details>
      )}
    </div>
  )
}
