'use client'

import { useState } from 'react'

interface AnalysisResultProps {
  data: any
}

function ExpandableText({ text, label }: { text: string; label: string }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const limit = 300

  if (!text) return null
  
  if (text.length <= limit) {
    return <p><strong>{label}:</strong> {text}</p>
  }

  return (
    <div>
      <p>
        <strong>{label}:</strong> {isExpanded ? text : `${text.substring(0, limit)}...`}
      </p>
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-xs text-blue-600 hover:text-blue-800 mt-1 font-medium"
      >
        {isExpanded ? '收起' : '展开全部'}
      </button>
    </div>
  )
}

export default function AnalysisResult({ data }: AnalysisResultProps) {
  if (!data) return null

  // 提取数据
  const originalContent = data.original_content
  const contextualExpand = data.contextual_expand
  const searchResults = data.search_results
  const deepDecode = data.deep_decode

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8 space-y-6">
      <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">AI 分析详情</h2>

      {/* 0. 原始内容 (Original Content) */}
      {originalContent && (
        <div>
          <h3 className="text-sm font-medium text-gray-800 mb-2">📄 原始内容 (Original)</h3>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
            {originalContent.type === 'image' && (
              <div className="flex justify-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img 
                  src={originalContent.content} 
                  alt="Uploaded Content" 
                  className="max-h-96 rounded-lg shadow-sm object-contain" 
                />
              </div>
            )}
            {originalContent.type === 'url' && (
              <div className="flex items-center space-x-2">
                <span className="text-xl">🔗</span>
                <a 
                  href={originalContent.content} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-blue-600 hover:underline break-all"
                >
                  {originalContent.content}
                </a>
              </div>
            )}
            {originalContent.type === 'text' && (
              <ExpandableText label="文本内容" text={originalContent.content} />
            )}
          </div>
        </div>
      )}

      {/* 1. 深度解析结果 (如果有) */}
      {deepDecode && (
        <div>
          <h3 className="text-sm font-medium text-blue-800 mb-2">📸 深度解析 (Deep Decode)</h3>
          <div className="bg-blue-50 rounded-lg p-4 text-sm text-gray-700 space-y-2">
            {deepDecode.visual_description && (
              <p><strong>内容分析:</strong> <span className="whitespace-pre-wrap">{deepDecode.visual_description}</span></p>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
               {deepDecode.scene_type && (
                 <p><strong>场景类型:</strong> {deepDecode.scene_type}</p>
               )}
               {deepDecode.main_subjects && deepDecode.main_subjects.length > 0 && (
                 <p><strong>主要对象:</strong> {Array.isArray(deepDecode.main_subjects) ? deepDecode.main_subjects.join(', ') : deepDecode.main_subjects}</p>
               )}
               {deepDecode.possible_intent && deepDecode.possible_intent.length > 0 && (
                 <div className="col-span-1 md:col-span-2">
                   <p><strong>潜在意图:</strong> {Array.isArray(deepDecode.possible_intent) ? deepDecode.possible_intent.join(', ') : deepDecode.possible_intent}</p>
                 </div>
               )}
            </div>

            {deepDecode.extracted_text && (
              <ExpandableText label="提取内容" text={deepDecode.extracted_text} />
            )}

            <details className="mt-2">
              <summary className="text-xs font-medium text-blue-600 cursor-pointer hover:text-blue-800">
                查看原始 JSON
              </summary>
              <pre className="mt-2 p-3 bg-white rounded border border-blue-100 text-xs overflow-auto max-h-60">
                {JSON.stringify(deepDecode, null, 2)}
              </pre>
            </details>
          </div>
        </div>
      )}

      {/* 2. 意图分析结果 */}
      {contextualExpand && (
        <div>
          <h3 className="text-sm font-medium text-purple-800 mb-2">🧠 意图分析 (Contextual Expand)</h3>
          <div className="bg-purple-50 rounded-lg p-4 text-sm text-gray-700 space-y-2">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p><strong>主要意图:</strong> {contextualExpand.primary_intent}</p>
                <p><strong>兴趣等级:</strong> {contextualExpand.interest_level} / 10</p>
              </div>
              <div>
                <p><strong>兴趣标签:</strong> {contextualExpand.interest_tags?.join(', ')}</p>
                <p><strong>关键词:</strong> {contextualExpand.keywords?.join(', ')}</p>
              </div>
            </div>
            
            <details className="mt-2">
              <summary className="text-xs font-medium text-purple-600 cursor-pointer hover:text-purple-800">
                查看原始 JSON
              </summary>
              <pre className="mt-2 p-3 bg-white rounded border border-purple-100 text-xs overflow-auto max-h-60">
                {JSON.stringify(contextualExpand, null, 2)}
              </pre>
            </details>
          </div>
        </div>
      )}

      {/* 3. 搜索结果 */}
      {searchResults && searchResults.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-green-800 mb-2">🔍 搜索扩展 (Search Results)</h3>
          <div className="bg-green-50 rounded-lg p-4 text-sm text-gray-700">
             <p className="mb-2">基于关键词搜索到的相关信息：</p>
             <ul className="list-disc list-inside space-y-1 pl-2 mb-3">
               {searchResults.slice(0, 5).map((result: any, idx: number) => (
                 <li key={idx} className="truncate">
                   <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                     {result.title}
                   </a>
                   <span className="text-gray-500 ml-2 text-xs">({result.source})</span>
                 </li>
               ))}
             </ul>

            <details>
              <summary className="text-xs font-medium text-green-600 cursor-pointer hover:text-green-800">
                查看完整搜索结果 JSON
              </summary>
              <pre className="mt-2 p-3 bg-white rounded border border-green-100 text-xs overflow-auto max-h-60">
                {JSON.stringify(searchResults, null, 2)}
              </pre>
            </details>
          </div>
        </div>
      )}
    </div>
  )
}
