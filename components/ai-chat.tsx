"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Bot, User, Loader2, Sparkles } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"

interface AiChatProps {
  onCommand: (command: string, response: string) => void
}

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export function AiChat({ onCommand }: AiChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [cooldownSeconds, setCooldownSeconds] = useState(0)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const lastRequestTimeRef = useRef<number>(0)
  const rateLimitCooldownRef = useRef<number>(0)
  
  // Minimum time between requests (5 seconds = 12 requests per minute max, safer than 15)
  const MIN_REQUEST_INTERVAL = 5000 // 5 seconds for safety margin

  // Update cooldown countdown every second
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now()
      if (rateLimitCooldownRef.current > now) {
        const remaining = Math.ceil((rateLimitCooldownRef.current - now) / 1000)
        setCooldownSeconds(remaining)
      } else {
        setCooldownSeconds(0)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Initialize messages on client side only
    setMessages([
      {
        role: "assistant",
        content:
          "👋 Hello! I'm **Orion AI**, your intelligent assistant powered by Google Gemini. I can help you with:\n\n• **Coding & Development** - Write, debug, and explain code\n• **Writing & Analysis** - Documents, summaries, research\n• **Problem Solving** - Math, logic, planning\n• **Creative Tasks** - Brainstorming, storytelling, design ideas\n• **General Knowledge** - Questions on any topic\n\nWhat would you like to explore today?",
        timestamp: new Date(),
      },
    ])
  }, [])

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    // Check rate limiting - prevent requests too close together
    const now = Date.now()
    const timeSinceLastRequest = now - lastRequestTimeRef.current
    
    if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
      const waitTime = Math.ceil((MIN_REQUEST_INTERVAL - timeSinceLastRequest) / 1000)
      setMessages((prev) => [
        ...prev,
        { 
          role: "assistant", 
          content: `⏳ Please wait ${waitTime} second${waitTime > 1 ? 's' : ''} before sending another message to avoid rate limits.`, 
          timestamp: new Date() 
        }
      ])
      return
    }

    // Check if we're in a cooldown period after a rate limit error
    if (rateLimitCooldownRef.current > now) {
      const waitTime = Math.ceil((rateLimitCooldownRef.current - now) / 1000)
      setMessages((prev) => [
        ...prev,
        { 
          role: "assistant", 
          content: `⏳ Rate limit cooldown active. Please wait ${waitTime} more second${waitTime > 1 ? 's' : ''} before trying again.`, 
          timestamp: new Date() 
        }
      ])
      return
    }

    const userMessage = input.trim()
    setMessages((prev) => [...prev, { role: "user", content: userMessage, timestamp: new Date() }])
    setInput("")
    setIsLoading(true)
    lastRequestTimeRef.current = now

    try {
      // Build conversation history for context
      // Filter out the initial greeting and only include actual conversation
      const conversationHistory = messages
        .filter((msg) => {
          // Skip the initial greeting message
          if (msg.role === "assistant" && msg.content.includes("👋 Hello! I'm **Orion AI**")) {
            return false
          }
          return true
        })
        .map((msg) => ({
          role: msg.role,
          content: msg.content,
        }))

      conversationHistory.push({ role: "user", content: userMessage })

      const response = await fetch("/api/ai/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: conversationHistory,
          system: `You are Orion AI, an advanced AI assistant integrated into the ORION OS command center. You are helpful, friendly, and highly capable. You can:
- Write and explain code in any programming language
- Help with writing, editing, and analysis
- Answer questions on a wide range of topics
- Assist with problem-solving and brainstorming
- Provide clear, well-formatted responses using markdown

Keep responses concise but thorough. Use bullet points, code blocks, and formatting when helpful. Be conversational and engaging.`,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Unknown error" }))
        let errorMessage = "⚠️ **Error**\n\n"
        
        if (response.status === 500 && errorData.error) {
          if (errorData.error.includes("API key")) {
            errorMessage += "**API Key Error**\n\n"
            errorMessage += "Your Gemini API key is not configured. To use Orion AI:\n\n"
            errorMessage += "1. Get an API key from: https://makersuite.google.com/app/apikey\n"
            errorMessage += "2. Add it to your `.env.local` file as:\n"
            errorMessage += "   `GEMINI_API_KEY=your_key_here`\n"
            errorMessage += "3. Restart the development server"
          } else if (errorData.error.includes("Rate limit") || errorData.error.includes("429")) {
            const cooldownMs = 90000 // 90 seconds
            rateLimitCooldownRef.current = Date.now() + cooldownMs
            
            errorMessage += "**Rate Limit Exceeded (429)**\n\n"
            errorMessage += "You've exceeded the Gemini API rate limit (15 requests/minute on free tier).\n\n"
            errorMessage += "**Please wait 90 seconds before trying again.**\n\n"
            errorMessage += "💡 **Tips to avoid rate limits:**\n"
            errorMessage += "• Wait at least 5 seconds between messages\n"
            errorMessage += "• Don't send multiple messages quickly\n"
            errorMessage += "• Consider upgrading your API plan for higher limits\n"
            errorMessage += "• The cooldown timer will show when you can try again"
          } else if (errorData.error.includes("temporarily unavailable")) {
            errorMessage += "**Service Unavailable**\n\n"
            errorMessage += "The AI service is temporarily unavailable. Please try again in a few moments."
          } else {
            errorMessage += errorData.error
          }
        } else if (response.status === 400) {
          // Show the actual error message from the API
          errorMessage += "**Request Error (400)**\n\n"
          if (errorData.error) {
            errorMessage += errorData.error
          } else {
            errorMessage += `Invalid request format. Please check the console for details.`
          }
        } else if (response.status === 429) {
          // Handle 429 rate limit errors - set longer cooldown
          const cooldownMs = 90000 // 90 seconds
          rateLimitCooldownRef.current = Date.now() + cooldownMs
          
          errorMessage += "**Rate Limit Exceeded (429)**\n\n"
          errorMessage += "You've exceeded the Gemini API rate limit (15 requests/minute on free tier).\n\n"
          errorMessage += "**Please wait 90 seconds before trying again.**\n\n"
          errorMessage += "💡 **Tips to avoid rate limits:**\n"
          errorMessage += "• Wait at least 5 seconds between messages\n"
          errorMessage += "• Don't send multiple messages quickly\n"
          errorMessage += "• Consider upgrading your API plan for higher limits\n"
          errorMessage += "• The cooldown timer will show when you can try again"
        } else {
          errorMessage += `Failed to get response from AI (Error ${response.status})`
          if (errorData.error) {
            errorMessage += `\n\n${errorData.error}`
          }
        }
        
        setMessages((prev) => [...prev, { role: "assistant", content: errorMessage, timestamp: new Date() }])
        setIsLoading(false)
        return
      }

      const data = await response.json()

      if (data.success && data.content) {
        setMessages((prev) => [...prev, { role: "assistant", content: data.content, timestamp: new Date() }])
        onCommand(userMessage, data.content)
      } else {
        const errorMsg = data.error || "Failed to get response from AI"
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `⚠️ Error: ${errorMsg}`, timestamp: new Date() },
        ])
      }
    } catch (error) {
      console.error("AI Error:", error)
      let errorMessage = "⚠️ **Connection Error**\n\n"
      
      if (error instanceof TypeError && error.message.includes("fetch")) {
        errorMessage += "Unable to connect to the AI service. This could be due to:\n\n"
        errorMessage += "• **No internet connection** - Check your network\n"
        errorMessage += "• **API key not configured** - Add `GEMINI_API_KEY` to your `.env.local` file\n"
        errorMessage += "• **Server error** - Check the console for details\n\n"
        errorMessage += "**Note:** The AI chat feature requires a Gemini API key. Get one at: https://makersuite.google.com/app/apikey"
      } else {
        errorMessage += `An unexpected error occurred: ${error instanceof Error ? error.message : "Unknown error"}\n\n`
        errorMessage += "Please check your network connection and try again."
      }
      
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: errorMessage,
          timestamp: new Date(),
        },
      ])
    }

    setIsLoading(false)
  }

  useEffect(() => {
    // Smooth scroll to bottom when messages change
    if (scrollAreaRef.current) {
      // Find the viewport element inside ScrollArea
      const viewport = scrollAreaRef.current.querySelector('[data-slot="scroll-area-viewport"]') as HTMLElement
      if (viewport) {
        // Use requestAnimationFrame to ensure DOM is updated
        requestAnimationFrame(() => {
          viewport.scrollTo({
            top: viewport.scrollHeight,
            behavior: "smooth",
          })
        })
      }
    }
  }, [messages])

  // Format message content with markdown-like styling
  const formatMessage = (content: string) => {
    return content.split("\n").map((line, i) => {
      // Headers
      if (line.startsWith("### ")) {
        return (
          <h4 key={i} className="font-bold text-violet-400 mt-3 mb-1">
            {line.slice(4)}
          </h4>
        )
      }
      if (line.startsWith("## ")) {
        return (
          <h3 key={i} className="font-bold text-violet-300 mt-4 mb-2 text-lg">
            {line.slice(3)}
          </h3>
        )
      }
      if (line.startsWith("# ")) {
        return (
          <h2 key={i} className="font-bold text-violet-300 mt-4 mb-2 text-xl">
            {line.slice(2)}
          </h2>
        )
      }
      // Bullet points
      if (line.startsWith("• ") || line.startsWith("- ") || line.startsWith("* ")) {
        const text = line.slice(2)
        return (
          <div key={i} className="flex gap-2 ml-2 my-1">
            <span className="text-violet-400">•</span>
            <span>{formatInlineText(text)}</span>
          </div>
        )
      }
      // Code blocks (simple detection)
      if (line.startsWith("```")) {
        return null
      }
      // Regular text
      if (line.trim()) {
        return (
          <p key={i} className="my-1">
            {formatInlineText(line)}
          </p>
        )
      }
      return <br key={i} />
    })
  }

  const formatInlineText = (text: string) => {
    // Bold text
    const parts = text.split(/\*\*(.*?)\*\*/g)
    return parts.map((part, i) =>
      i % 2 === 1 ? (
        <strong key={i} className="text-violet-300">
          {part}
        </strong>
      ) : (
        part
      ),
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-violet-500/20 flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-gradient-to-r from-violet-500 to-fuchsia-500">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="font-semibold text-white">Orion AI Assistant</h2>
          <p className="text-xs text-slate-400">Powered by Gemini • Real-time AI</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-emerald-400">Connected</span>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollAreaRef} className="flex-1 overflow-hidden">
        <ScrollArea className="h-full p-6">
          <div className="space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-cyan-500 to-blue-500"
                    : "bg-gradient-to-r from-violet-500 to-fuchsia-500"
                }`}
              >
                {msg.role === "user" ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
              </div>
              <div className={`flex-1 max-w-[85%] ${msg.role === "user" ? "text-right" : ""}`}>
                <div
                  className={`inline-block p-4 rounded-2xl ${
                    msg.role === "user"
                      ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 text-white"
                      : "glass border border-violet-500/20"
                  }`}
                >
                  <div className="text-sm text-left">{formatMessage(msg.content)}</div>
                </div>
                <p className="text-xs text-slate-500 mt-1.5">{msg.timestamp.toLocaleTimeString()}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-r from-violet-500 to-fuchsia-500 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="glass p-4 rounded-2xl border border-violet-500/20">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-violet-400" />
                  <span className="text-sm text-slate-400">Orion is thinking...</span>
                </div>
              </div>
            </div>
          )}
          </div>
        </ScrollArea>
      </div>

      {/* Input */}
      <div className="p-4 border-t border-violet-500/20">
        {cooldownSeconds > 0 && (
          <div className="mb-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-sm text-amber-300">
              ⏳ Rate limit cooldown: <strong>{cooldownSeconds}s</strong> remaining
            </span>
          </div>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault()
            sendMessage()
          }}
          className="flex gap-3"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={cooldownSeconds > 0 ? `Please wait ${cooldownSeconds}s...` : "Ask Orion AI anything..."}
            className="flex-1 bg-slate-900/50 border-violet-500/30 focus:border-violet-500/60 text-white placeholder:text-slate-500"
            disabled={isLoading || cooldownSeconds > 0}
          />
          <Button
            type="submit"
            disabled={isLoading || !input.trim() || cooldownSeconds > 0}
            className="px-5 bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 text-white border-0 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </Button>
        </form>
      </div>
    </div>
  )
}
