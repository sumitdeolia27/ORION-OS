import { NextRequest, NextResponse } from 'next/server'

const GEMINI_API_KEY = process.env.GEMINI_API_KEY || process.env.NEXT_PUBLIC_GEMINI_API_KEY
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta'

export async function POST(request: NextRequest) {
  try {
    // Debug: Log environment variable status (without exposing the key)
    const hasKey = !!GEMINI_API_KEY
    const keyLength = GEMINI_API_KEY?.length || 0
    console.log(`[AI Chat] API Key check: ${hasKey ? 'Found' : 'Missing'} (length: ${keyLength})`)
    
    if (!GEMINI_API_KEY) {
      return NextResponse.json(
        {
          success: false,
          error: 'Gemini API key is not configured. Please add GEMINI_API_KEY to your .env.local file and restart the development server.',
        },
        { status: 500 }
      )
    }

    const body = await request.json()
    const { messages, system } = body

    // Format messages correctly for Gemini API
    // Gemini uses contents array with parts containing text
    // Filter out empty messages and ensure proper format
    let formattedContents = (messages || [])
      .filter((msg: any) => msg && msg.content && msg.content.trim())
      .map((msg: any) => {
        const role = msg.role === 'assistant' ? 'model' : 'user'
        const content = typeof msg.content === 'string' ? msg.content.trim() : String(msg.content).trim()
        return {
          role,
          parts: [{ text: content }]
        }
      })
    
    // Ensure we have at least one user message
    if (formattedContents.length === 0 || !formattedContents.some((m: any) => m.role === 'user')) {
      return NextResponse.json(
        { success: false, error: 'At least one user message is required.' },
        { status: 400 }
      )
    }
    
    console.log('[AI Chat] Formatted contents:', formattedContents.map((m: any) => ({ role: m.role, contentLength: m.parts[0].text.length })))

    // Build request body for Gemini API
    const requestBody: any = {
      contents: formattedContents,
      generationConfig: {
        temperature: 0.9,
        topK: 64,
        topP: 0.95,
        maxOutputTokens: 32768, // Using half of the 65K limit for safety and cost efficiency
      }
    }

    // Add system instruction if provided (Gemini uses systemInstruction)
    if (system && system.trim()) {
      requestBody.systemInstruction = {
        parts: [{ text: system.trim() }]
      }
    }

    // Use gemini-2.5-flash (latest stable model with excellent free tier support and 1M token context)
    const model = 'gemini-2.5-flash'
    const url = `${GEMINI_API_URL}/models/${model}:generateContent?key=${GEMINI_API_KEY}`

    console.log('[AI Chat] Sending request with', formattedContents.length, 'messages')
    console.log('[AI Chat] Request body:', JSON.stringify(requestBody, null, 2).substring(0, 500))

    // Don't retry on rate limits - just fail immediately to avoid making it worse
    // Rate limits need to be handled by the client with proper cooldowns
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    })

    if (!response || !response.ok) {
      if (!response) {
        return NextResponse.json(
          { success: false, error: 'Failed to get response from API' },
          { status: 500 }
        )
      }

      let errorData: any = { error: { message: 'Unknown error' } }
      try {
        const errorText = await response.text()
        console.error('[AI Chat] API Error Response:', response.status, errorText)
        if (errorText) {
          errorData = JSON.parse(errorText)
        }
      } catch (e) {
        console.error('[AI Chat] Failed to parse error response:', e)
      }
      
      let errorMessage = 'Failed to get response from AI'
      if (response.status === 401 || response.status === 403) {
        errorMessage = 'API key is invalid or expired. Please check your GEMINI_API_KEY. Get a new key from: https://makersuite.google.com/app/apikey'
      } else if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After')
        if (retryAfter) {
          errorMessage = `Rate limit exceeded. Please wait ${retryAfter} seconds before trying again. Free tier has limits: ~15 requests per minute.`
        } else {
          errorMessage = 'Rate limit exceeded. Please wait a moment and try again. Free tier has limits: ~15 requests per minute. The request was automatically retried but still hit the limit.'
        }
      } else if (response.status >= 500) {
        errorMessage = 'AI service is temporarily unavailable. Please try again later.'
      } else if (response.status === 400) {
        // 400 errors usually mean bad request format
        if (errorData.error) {
          if (typeof errorData.error === 'string') {
            errorMessage = `Request error: ${errorData.error}`
          } else if (errorData.error.message) {
            errorMessage = `Request error: ${errorData.error.message}`
          } else {
            errorMessage = `Request error: ${JSON.stringify(errorData.error)}`
          }
        } else if (errorData.message) {
          errorMessage = `Request error: ${errorData.message}`
        } else {
          errorMessage = `Invalid request format (400). Details: ${JSON.stringify(errorData)}`
        }
      } else {
        errorMessage = errorData.error?.message || `Error ${response.status}: Failed to get response`
      }

      return NextResponse.json(
        { success: false, error: errorMessage },
        { status: response.status }
      )
    }

    const data = await response.json()

    let assistantResponse = ''
    try {
      // Gemini API response format: data.candidates[0].content.parts[0].text
      if (data.candidates && data.candidates.length > 0) {
        const candidate = data.candidates[0]
        if (candidate.content && candidate.content.parts && candidate.content.parts.length > 0) {
          assistantResponse = candidate.content.parts
            .filter((part: any) => part.text)
            .map((part: any) => part.text)
            .join('\n')
        }
      }
      
      if (!assistantResponse) {
        return NextResponse.json(
          { success: false, error: 'No response content received from Gemini API' },
          { status: 500 }
        )
      }
    } catch (e) {
      console.error('[AI Chat] Failed to parse Gemini response:', e, data)
      return NextResponse.json(
        { success: false, error: 'Failed to parse response from Gemini API' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      content: assistantResponse,
    })
  } catch (error) {
    console.error('AI Chat API error:', error)
    
    let errorMessage = 'Failed to connect to AI service'
    if (error instanceof TypeError && error.message.includes('fetch')) {
      errorMessage = 'Network error. Please check your internet connection.'
    } else if (error instanceof Error) {
      errorMessage = error.message
    }

    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    )
  }
}
