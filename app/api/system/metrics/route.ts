import { NextRequest, NextResponse } from 'next/server'

const API_BASE_URL = process.env.BACKEND_API_URL || 'http://localhost:5000'

export async function GET(request: NextRequest) {
  try {
    // Add timeout to prevent hanging requests
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
    
    const response = await fetch(`${API_BASE_URL}/api/system/metrics`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    })
    
    clearTimeout(timeoutId)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }))
      return NextResponse.json(
        { success: false, error: error.error || 'Backend request failed' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    // Handle timeout and connection errors gracefully
    if (error instanceof Error && error.name === 'AbortError') {
      return NextResponse.json(
        { success: false, error: 'Request timeout - backend may be slow or unavailable' },
        { status: 504 }
      )
    }
    console.error('API route error:', error)
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Failed to connect to backend' },
      { status: 500 }
    )
  }
}

