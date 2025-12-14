'use client'

import { useState, useCallback } from 'react'
import { uploadAPI } from '@/lib/api'
import { supabase } from '@/lib/supabase'

interface UploadZoneProps {
  onUploadComplete: (uploadId: string) => void
}

export default function UploadZone({ onUploadComplete }: UploadZoneProps) {
  const [uploadType, setUploadType] = useState<'image' | 'url' | 'text'>('image')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dragActive, setDragActive] = useState(false)

  // URL 或文本输入
  const [inputValue, setInputValue] = useState('')

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = e.dataTransfer.files
    if (files && files[0]) {
      await handleFileUpload(files[0])
    }
  }

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files[0]) {
      await handleFileUpload(files[0])
    }
  }

  const handleFileUpload = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('只支持图片文件')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await uploadAPI.image(file)
      onUploadComplete(response.data.upload_id)
    } catch (error: any) {
      setError(error.response?.data?.detail || error.message || '上传失败')
    } finally {
      setLoading(false)
    }
  }

  const handleTextSubmit = async () => {
    if (!inputValue.trim()) {
      setError('请输入内容')
      return
    }

    setLoading(true)
    setError('')

    try {
      const { data: { session } } = await supabase.auth.getSession()
      const userId = session?.user?.id

      if (!userId) {
        throw new Error('用户未登录')
      }

      let response
      if (uploadType === 'url') {
        response = await uploadAPI.url(inputValue, userId)
      } else {
        response = await uploadAPI.text(inputValue, userId)
      }

      onUploadComplete(response.data.upload_id)
      setInputValue('')
    } catch (error: any) {
      setError(error.response?.data?.detail || error.message || '上传失败')
    } finally {
      setLoading(false)
    }
  }

  // 处理粘贴
  const handlePaste = async (e: React.ClipboardEvent) => {
    const items = e.clipboardData.items

    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const file = items[i].getAsFile()
        if (file) {
          e.preventDefault()
          await handleFileUpload(file)
          return
        }
      }
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      {/* 类型选择 */}
      <div className="flex space-x-2 mb-6">
        <button
          onClick={() => setUploadType('image')}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            uploadType === 'image'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          图片
        </button>
        <button
          onClick={() => setUploadType('url')}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            uploadType === 'url'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          URL
        </button>
        <button
          onClick={() => setUploadType('text')}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            uploadType === 'text'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          文本
        </button>
      </div>

      {/* 上传区域 */}
      {uploadType === 'image' ? (
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onPaste={handlePaste}
          className={`border-2 border-dashed rounded-xl p-12 text-center transition ${
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <div className="space-y-4">
            <div className="text-4xl">📸</div>
            <div>
              <p className="text-lg font-medium text-gray-700 mb-2">
                拖拽图片到这里，或者
              </p>
              <label className="cursor-pointer">
                <span className="text-blue-600 hover:text-blue-700 font-medium">
                  点击选择文件
                </span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileInput}
                  className="hidden"
                  disabled={loading}
                />
              </label>
            </div>
            <p className="text-sm text-gray-500">
              支持 JPG、PNG、GIF 等格式，也可以直接粘贴图片（Ctrl+V）
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {uploadType === 'url' ? (
            <input
              type="url"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="输入网页 URL，例如：https://example.com"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              disabled={loading}
            />
          ) : (
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="输入你感兴趣的文本内容..."
              rows={6}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
              disabled={loading}
            />
          )}
          <button
            onClick={handleTextSubmit}
            disabled={loading || !inputValue.trim()}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '上传中...' : '提交'}
          </button>
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="mt-4 text-center text-gray-600">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2">上传中...</p>
        </div>
      )}
    </div>
  )
}
