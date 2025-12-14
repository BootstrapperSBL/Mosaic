'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { supabase } from '@/lib/supabase'
import Sidebar from '@/components/Sidebar'
import MainContent from '@/components/MainContent'
import UploadModal from '@/components/UploadModal'
import { analysisAPI } from '@/lib/api'

function DashboardLayout() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // State
  const [user, setUser] = useState<any>(null)
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null)
  
  // Derived state from URL
  const currentAnalysisId = searchParams.get('analysis')

  useEffect(() => {
    checkUser()
  }, [])

  async function checkUser() {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) {
      router.push('/auth/signin')
    } else {
      setUser(session.user)
    }
  }

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    localStorage.removeItem('access_token')
    router.push('/auth/signin')
  }

  // Handlers
  const handleUploadComplete = async (uploadId: string) => {
    // Start analysis immediately
    try {
      const response = await analysisAPI.analyze(uploadId)
      setCurrentTaskId(response.data.task_id)
      // Clear current selection while analyzing
      router.push('/dashboard') 
    } catch (error: any) {
      alert(`启动分析失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleAnalysisComplete = (analysisId: string) => {
    setCurrentTaskId(null)
    // Select the new analysis
    router.push(`/dashboard?analysis=${analysisId}`)
  }

  if (!user) return null // Or loading spinner

  return (
    <div className="flex h-screen w-full overflow-hidden bg-gray-50">
      {/* Left Sidebar */}
      <Sidebar 
        onAddSource={() => setIsUploadModalOpen(true)} 
        user={user}
        onSignOut={handleSignOut}
      />

      {/* Main Content Area */}
      <MainContent 
        analysisId={currentAnalysisId}
        taskId={currentTaskId}
        onAnalysisComplete={handleAnalysisComplete}
      />

      {/* Modals */}
      <UploadModal 
        isOpen={isUploadModalOpen} 
        onClose={() => setIsUploadModalOpen(false)}
        onUploadComplete={handleUploadComplete}
      />
    </div>
  )
}

export default function Dashboard() {
  return (
    <Suspense fallback={<div className="flex h-screen w-full items-center justify-center">Loading...</div>}>
      <DashboardLayout />
    </Suspense>
  )
}
