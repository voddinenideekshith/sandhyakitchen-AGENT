"use client"

import React from 'react'

export default function TypingIndicator({ className = '' }: { className?: string }) {
  return (
    <div className={`max-w-[80%] px-4 py-2 rounded-lg shadow-sm bg-gray-100 text-gray-500 ${className}`}>
      <div className="flex items-center space-x-2">
        <div className="flex items-end h-6">
          <span
            className="inline-block w-2.5 h-2.5 bg-gray-500 rounded-full mr-1 animate-bounce"
            style={{ animationDelay: '0s' }}
          />
          <span
            className="inline-block w-2.5 h-2.5 bg-gray-500 rounded-full mr-1 animate-bounce"
            style={{ animationDelay: '0.15s' }}
          />
          <span
            className="inline-block w-2.5 h-2.5 bg-gray-500 rounded-full animate-bounce"
            style={{ animationDelay: '0.3s' }}
          />
        </div>
        <div className="text-sm text-gray-500">Thinking</div>
      </div>
    </div>
  )
}
