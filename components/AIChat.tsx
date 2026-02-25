"use client"

import React, { useEffect, useRef, useState } from 'react'
import { sendMessage, getSessionId } from '../lib/api'
import TypingIndicator from './TypingIndicator'

type Message = {
  role: 'user' | 'assistant'
  content: string
}

export default function AIChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const inputRef = useRef<HTMLTextAreaElement | null>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // ensure session id exists in localStorage for contextual requests
  useEffect(() => {
    try {
      getSessionId()
    } catch (e) {
      // ignore
    }
  }, [])

  async function handleSend(text?: string) {
    const content = (text ?? input).trim()
    if (!content) return
    // append user message immediately
    const userMsg: Message = { role: 'user', content }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await sendMessage(content)
      const assistantMsg: Message = { role: 'assistant', content: res.reply || 'No reply' }
      setMessages((m) => [...m, assistantMsg])
    } catch (err) {
      const msg = (err as Error)?.message || 'AI service temporarily unavailable'
      const assistantMsg: Message = { role: 'assistant', content: '⚠️ AI service temporarily unavailable' }
      setMessages((m) => [...m, assistantMsg])
      console.error('AI request failed:', msg)
    } finally {
      setLoading(false)
      inputRef.current?.focus()
      // reset textarea height after sending
      if (inputRef.current) {
        inputRef.current.style.height = 'auto'
      }
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSend()
    }
  }

  function onInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value)
    // auto-resize up to ~6 lines
    const ta = e.target
    ta.style.height = 'auto'
    const maxHeight = 6 * 24 // approximate line-height 24px
    const newHeight = Math.min(ta.scrollHeight, maxHeight)
    ta.style.height = `${newHeight}px`
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
      <div className="w-full max-w-2xl bg-white shadow-md rounded-lg overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">AI Food Assistant</h2>
          <p className="text-sm text-gray-500">Ask the assistant about menus, orders, or recipes.</p>
        </div>

        <div className="flex-1 p-4 overflow-auto space-y-4" style={{ maxHeight: '60vh' }}>
          {messages.length === 0 && (
            <div className="text-center text-sm text-gray-400">Start the conversation by asking a question.</div>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] px-4 py-2 rounded-lg shadow-sm break-words whitespace-pre-wrap ${
                  m.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-100 text-gray-900 rounded-bl-none'
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <TypingIndicator />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            void handleSend()
          }}
          className="px-4 py-3 border-t bg-white"
        >
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={onInputChange}
              onKeyDown={onKeyDown}
              disabled={loading}
              placeholder={loading ? 'Please wait...' : 'Type your message and press Enter'}
              className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-60 resize-none max-h-36"
              aria-label="Message input"
              rows={1}
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
