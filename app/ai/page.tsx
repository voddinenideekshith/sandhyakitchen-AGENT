import React from 'react'
import AIChat from '../../components/AIChat'

export const metadata = {
  title: 'AI Food Assistant',
}

export default function Page() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">AI Food Assistant</h1>
        <AIChat />
      </div>
    </main>
  )
}
