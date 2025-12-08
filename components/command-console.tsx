"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { Send, Loader2, ChevronRight, Volume2, VolumeX, Mic } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"

interface CommandConsoleProps {
  onCommand: (command: string, response: string) => void
  isListening: boolean
  setIsListening: (listening: boolean) => void
  isMuted: boolean
  setIsMuted: (muted: boolean) => void
  voiceController: AbortController | null
  setVoiceController: (controller: AbortController | null) => void
}

interface ConsoleMessage {
  type: "input" | "output" | "system" | "error"
  content: string
  timestamp: Date
}

export function CommandConsole({ 
  onCommand,
  isListening,
  setIsListening,
  isMuted,
  setIsMuted,
  voiceController,
  setVoiceController
}: CommandConsoleProps) {
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<ConsoleMessage[]>(() => {
    // Load messages from localStorage on mount
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("orion-console-messages")
      if (saved) {
        try {
          const parsed = JSON.parse(saved)
          // Convert timestamp strings back to Date objects
          return parsed.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          }))
        } catch (e) {
          console.error("Failed to load console messages:", e)
        }
      }
    }
    return []
  })
  const [isProcessing, setIsProcessing] = useState(false)
  const [voiceEnabled, setVoiceEnabled] = useState(true) // Voice enabled by default
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const isInitializedRef = useRef(false)

  const processCommand = async (command: string) => {
    const lowerCmd = command.toLowerCase().trim()

    // Add user input to messages
    setMessages((prev) => [...prev, { type: "input", content: command, timestamp: new Date() }])

    setIsProcessing(true)

    // Handle clear command locally
    if (lowerCmd === "clear") {
      setMessages([])
      if (typeof window !== "undefined") {
        localStorage.removeItem("orion-console-messages")
      }
      setIsProcessing(false)
      return
    }

    try {
      // Call backend API with voice option
      const response = await fetch("/api/command", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ command, speak: voiceEnabled && !isMuted }),
      })

      const data = await response.json()

      if (data.success) {
        const responseText = data.response || "Command executed successfully."
        setMessages((prev) => [...prev, { type: "output", content: responseText, timestamp: new Date() }])
        onCommand(command, responseText)
      } else {
        const errorMsg = data.error || "Failed to process command"
        setMessages((prev) => [
          ...prev,
          { type: "error", content: `❌ Error: ${errorMsg}`, timestamp: new Date() },
        ])
        onCommand(command, `Error: ${errorMsg}`)
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Failed to connect to backend"
      setMessages((prev) => [
        ...prev,
        {
          type: "error",
          content: `❌ Connection Error: ${errorMsg}\n\nMake sure the Python backend server is running:\npython scripts/api_server.py`,
          timestamp: new Date(),
        },
      ])
      onCommand(command, `Error: ${errorMsg}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isProcessing) return
    processCommand(input)
    setInput("")
  }

  const stopListening = async () => {
    if (voiceController) {
      voiceController.abort()
      setVoiceController(null)
    }
    
    // Also call the backend stop endpoint
    try {
      await fetch("/api/voice/stop", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      })
    } catch (error) {
      console.error("Error stopping voice:", error)
    }
    
    setIsListening(false)
    setMessages((prev) => [
      ...prev,
      { type: "system", content: "🛑 Voice listening stopped.", timestamp: new Date() },
    ])
  }

  const handleVoiceCommand = async () => {
    // If already listening, stop it
    if (isListening) {
      stopListening()
      return
    }

    if (isProcessing) return

    setIsListening(true)
    setMessages((prev) => [
      ...prev,
      { type: "system", content: "🎤 Listening... Speak your command now. Click microphone again to stop.", timestamp: new Date() },
    ])

    let timeoutMessageShown = false
    try {
      // Create abort controller for timeout and manual stop
      const controller = new AbortController()
      setVoiceController(controller)
      
      // Set a timeout to abort the request if it takes too long (10 seconds total)
      const timeoutId = setTimeout(() => {
        timeoutMessageShown = true
        controller.abort()
        setMessages((prev) => [
          ...prev,
          { type: "system", content: "⏱️ Listening timeout. Please try again.", timestamp: new Date() },
        ])
      }, 10000) // 10 second timeout

      const response = await fetch("/api/voice/listen", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ timeout: 7 }),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)
      setVoiceController(null)

      // Handle response - check status first
      let data
      if (!response.ok) {
        // Try to get error data
        const errorData = await response.json().catch(() => ({ error: "Unknown error" }))
        
        // If it's a "no speech detected" error (400), handle it gracefully
        if (response.status === 400 && errorData.error && errorData.error.toLowerCase().includes("no speech")) {
          data = { success: false, error: errorData.error }
        } else {
          // For other errors, throw
          throw new Error(errorData.error || `HTTP ${response.status}`)
        }
      } else {
        data = await response.json()
      }

      if (data.success && data.text) {
        const recognizedCommand = data.text.trim()
        setMessages((prev) => [
          ...prev,
          { type: "system", content: `✓ Heard: "${recognizedCommand}"`, timestamp: new Date() },
        ])
        
        // Automatically execute the recognized command
        await processCommand(recognizedCommand)
      } else {
        const errorMsg = data.error || "No speech detected"
        const isNoSpeech = errorMsg.toLowerCase().includes("no speech")
        setMessages((prev) => [
          ...prev,
          { 
            type: isNoSpeech ? "system" : "error", 
            content: isNoSpeech 
              ? `🎤 ${errorMsg}. Please try again and speak clearly.` 
              : `❌ ${errorMsg}. Please try again.`, 
            timestamp: new Date() 
          },
        ])
      }
    } catch (error) {
      // Check if it was aborted (user stopped listening or timeout)
      if (error instanceof Error && error.name === 'AbortError') {
        console.log("Voice listening stopped (aborted)")
        // Only show message if timeout message wasn't already shown
        if (!timeoutMessageShown) {
          setMessages((prev) => [
            ...prev,
            { type: "system", content: "🛑 Voice listening stopped.", timestamp: new Date() },
          ])
        }
      } else {
        const errorMsg = error instanceof Error ? error.message : "Connection failed"
        setMessages((prev) => [
          ...prev,
          {
            type: "error",
            content: `❌ Voice recognition error: ${errorMsg}\n\nMake sure the Python backend server is running and microphone is available.`,
            timestamp: new Date(),
          },
        ])
      }
    } finally {
      // Always clear listening state and controller
      setIsListening(false)
      setVoiceController(null)
    }
  }

  useEffect(() => {
    // Initialize messages on client side only, but only if no messages exist in localStorage
    if (typeof window !== "undefined" && !isInitializedRef.current) {
      const saved = localStorage.getItem("orion-console-messages")
      if (!saved) {
        // Only initialize if there's nothing saved
        const initialMessages = [
          {
            type: "system" as const,
            content: "⚡ Orion OS Navigator initialized. System check complete.",
            timestamp: new Date(),
          },
          {
            type: "system" as const,
            content: "✓ All systems operational. Ready for commands.",
            timestamp: new Date(),
          },
        ]
        setMessages(initialMessages)
        localStorage.setItem("orion-console-messages", JSON.stringify(initialMessages))
      }
      isInitializedRef.current = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Save messages to localStorage whenever they change (but skip initial load)
  useEffect(() => {
    if (typeof window !== "undefined" && isInitializedRef.current && messages.length > 0) {
      localStorage.setItem("orion-console-messages", JSON.stringify(messages))
    }
  }, [messages])

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

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  return (
    <div className="flex flex-col h-full">
      {/* Console Header */}
      <div className="px-4 py-3 border-b border-violet-500/20 flex items-center gap-3">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <div className="w-3 h-3 rounded-full bg-amber-500" />
          <div className="w-3 h-3 rounded-full bg-emerald-500" />
        </div>
        <span className="text-sm text-slate-400 font-mono">orion@navigator:~$</span>
        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={async () => {
              const muteCommand = isMuted ? "unmute" : "mute"
              
              // Optimistically update UI immediately
              setIsMuted(!isMuted)
              
              try {
                // Add timeout to prevent hanging
                const controller = new AbortController()
                const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
                
                const response = await fetch("/api/command", {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({ command: muteCommand, speak: false }),
                  signal: controller.signal,
                })
                
                clearTimeout(timeoutId)
                
                const data = await response.json()
                if (data.success) {
                  setMessages((prev) => [
                    ...prev,
                    { type: "system", content: data.response || `${!isMuted ? "Muted" : "Unmuted"} system`, timestamp: new Date() },
                  ])
                } else {
                  // Revert on error
                  setIsMuted(isMuted)
                  setMessages((prev) => [
                    ...prev,
                    { type: "error", content: `❌ Failed to ${muteCommand}: ${data.error || "Unknown error"}`, timestamp: new Date() },
                  ])
                }
              } catch (error) {
                // Revert on error
                setIsMuted(isMuted)
                console.error("Mute error:", error)
                if (error instanceof Error && error.name === 'AbortError') {
                  setMessages((prev) => [
                    ...prev,
                    { type: "error", content: `❌ Mute command timed out. Please try again.`, timestamp: new Date() },
                  ])
                } else {
                  setMessages((prev) => [
                    ...prev,
                    { type: "error", content: `❌ Failed to ${muteCommand}. Check backend connection.`, timestamp: new Date() },
                  ])
                }
              }
            }}
            className={`p-1.5 rounded-lg transition-all ${
              isMuted
                ? "bg-amber-500/20 text-amber-400 hover:bg-amber-500/30"
                : "bg-slate-800/50 text-slate-500 hover:bg-slate-700/50"
            }`}
            title={isMuted ? "Muted - Click to unmute" : "Unmuted - Click to mute"}
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
          <button
            onClick={() => {
              setVoiceEnabled(!voiceEnabled)
            }}
            className={`p-1.5 rounded-lg transition-all ${
              voiceEnabled
                ? "bg-violet-500/20 text-violet-400 hover:bg-violet-500/30"
                : "bg-slate-800/50 text-slate-500 hover:bg-slate-700/50"
            }`}
            title={voiceEnabled ? "Voice enabled - Click to disable" : "Voice disabled - Click to enable"}
          >
            {voiceEnabled ? <Mic className="w-4 h-4" /> : <Mic className="w-4 h-4 opacity-50" />}
          </button>
          <div className="text-xs text-slate-500">v3.0.0</div>
        </div>
      </div>

      {/* Console Output */}
      <div ref={scrollAreaRef} className="flex-1 overflow-hidden">
        <ScrollArea className="h-full p-4">
          <div className="font-mono text-sm space-y-2">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex items-start gap-2 ${
                msg.type === "input"
                  ? "text-cyan-400"
                  : msg.type === "error"
                    ? "text-red-400"
                    : msg.type === "system"
                      ? "text-slate-500"
                      : "text-slate-300"
              }`}
            >
              {msg.type === "input" ? (
                <ChevronRight className="w-4 h-4 mt-0.5 text-cyan-400" />
              ) : (
                <span className="text-slate-600 text-xs">[{msg.timestamp.toLocaleTimeString()}]</span>
              )}
              <pre className="whitespace-pre-wrap flex-1">{msg.content}</pre>
            </div>
          ))}
          {isListening && (
            <div className="flex items-center gap-2 text-red-400 animate-pulse">
              <Mic className="w-4 h-4" />
              <span>🎤 Listening... Speak your command now.</span>
            </div>
          )}
          {isProcessing && !isListening && (
            <div className="flex items-center gap-2 text-violet-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing...</span>
            </div>
          )}
          </div>
        </ScrollArea>
      </div>

      {/* Command Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-violet-500/20 flex gap-3">
        <div className="flex-1 relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-cyan-400 font-mono">{">"}</span>
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter command for Orion..."
            className="pl-8 bg-slate-900/50 border-violet-500/30 focus:border-violet-500/60 font-mono text-white placeholder:text-slate-500"
            disabled={isProcessing || isListening}
          />
        </div>
        <Button
          type="button"
          onClick={handleVoiceCommand}
          disabled={isProcessing} // Don't disable when listening - need to be able to stop
          className={`px-4 border-0 transition-all ${
            isListening
              ? "bg-gradient-to-r from-red-500 to-rose-500 hover:from-red-600 hover:to-rose-600 animate-pulse"
              : "bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600"
          }`}
          title={isListening ? "Click to stop listening" : "Voice command (speak your command)"}
        >
          {isListening ? (
            <Loader2 className="w-4 h-4 animate-spin text-white" />
          ) : (
            <Mic className="w-4 h-4 text-white" />
          )}
        </Button>
        <Button
          type="submit"
          disabled={isProcessing || isListening || !input.trim()}
          className="px-5 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white border-0"
        >
          {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </Button>
      </form>
    </div>
  )
}
