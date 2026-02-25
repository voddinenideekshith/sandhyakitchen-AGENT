export type AIResponse = {
  reply: string
  tokens_used?: number
}

function getLocalStorage(): Storage | null {
  try {
    return typeof window !== 'undefined' ? window.localStorage : null
  } catch (e) {
    return null
  }
}

export function getSessionId(): string {
  const ls = getLocalStorage()
  if (!ls) {
    // fallback to ephemeral id
    return typeof crypto !== 'undefined' && typeof (crypto as any).randomUUID === 'function'
      ? (crypto as any).randomUUID()
      : `sid-${Date.now()}-${Math.floor(Math.random() * 100000)}`
  }
  let sid = ls.getItem('sandhya_session_id')
  if (!sid) {
    sid = typeof crypto !== 'undefined' && typeof (crypto as any).randomUUID === 'function'
      ? (crypto as any).randomUUID()
      : `sid-${Date.now()}-${Math.floor(Math.random() * 100000)}`
    try {
      ls.setItem('sandhya_session_id', sid)
    } catch (e) {
      // ignore storage write errors
    }
  }
  return sid
}

export async function sendMessage(message: string): Promise<AIResponse> {
  const base = process.env.NEXT_PUBLIC_API_URL
  if (!base) throw new Error('NEXT_PUBLIC_API_URL is not configured')

  const url = `${base.replace(/\/$/, '')}/ai/test`

  const context = {
    session_id: getSessionId(),
    timestamp: new Date().toISOString(),
    platform: 'web' as const,
  }

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, context }),
  })

  if (!res.ok) {
    let text = res.statusText || 'Network error'
    try {
      const json = await res.json()
      text = json?.detail || json || text
    } catch (e) {
      /* ignore JSON parse errors */
    }
    throw new Error(String(text))
  }

  const data = (await res.json()) as AIResponse
  return data
}
