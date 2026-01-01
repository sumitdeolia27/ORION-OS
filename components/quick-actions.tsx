"use client"

import { useState } from "react"
import {
  Terminal,
  ListTodo,
  Bell,
  FolderOpen,
  Bot,
  History,
  Activity,
  Mic,
  MicOff,
  Camera,
  MonitorDown,
  Volume2,
  VolumeX,
  Power,
  Sparkles,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

interface QuickActionsProps {
  activePanel: string
  setActivePanel: (panel: string) => void
  onCommand?: (command: string, response: string) => void
  isListening: boolean
  setIsListening: (listening: boolean) => void
  isMuted: boolean
  setIsMuted: (muted: boolean) => void
  voiceController: AbortController | null
  setVoiceController: (controller: AbortController | null) => void
}

export function QuickActions({ 
  activePanel, 
  setActivePanel, 
  onCommand,
  isListening,
  setIsListening,
  isMuted,
  setIsMuted,
  voiceController,
  setVoiceController
}: QuickActionsProps) {
  const [isProcessing, setIsProcessing] = useState<string | null>(null)
  const [showShutdownDialog, setShowShutdownDialog] = useState(false)

  const panels = [
    { id: "ai", icon: Bot, label: "AI Assistant", shortcut: "A", gradient: "from-violet-500 to-fuchsia-500" },
    { id: "console", icon: Terminal, label: "Command Console", shortcut: "K", gradient: "from-cyan-500 to-blue-500" },
    { id: "tasks", icon: ListTodo, label: "Tasks", shortcut: "T", gradient: "from-emerald-500 to-teal-500" },
    { id: "reminders", icon: Bell, label: "Reminders", shortcut: "R", gradient: "from-amber-500 to-orange-500" },
    { id: "files", icon: FolderOpen, label: "File Explorer", shortcut: "F", gradient: "from-fuchsia-500 to-pink-500" },
    { id: "history", icon: History, label: "Command History", shortcut: "H", gradient: "from-indigo-500 to-violet-500" },
    { id: "metrics", icon: Activity, label: "System Metrics", shortcut: "M", gradient: "from-rose-500 to-red-500" },
  ]

  const quickCommands = [
    { 
      icon: Mic, // Always show Mic icon, state is indicated by styling
      label: isListening ? "Stop Listening" : "Voice", 
      command: null, 
      gradient: "from-violet-500 to-fuchsia-500", 
      speak: false, 
      isVoice: true 
    },
    { icon: Camera, label: "Camera", command: "camera", gradient: "from-cyan-500 to-blue-500", speak: false },
    { icon: MonitorDown, label: "Screenshot", command: "take screenshot", gradient: "from-emerald-500 to-teal-500", speak: true },
    { 
      icon: isMuted ? VolumeX : Volume2, 
      label: isMuted ? "Unmute" : "Mute", 
      command: "mute", 
      gradient: "from-amber-500 to-orange-500", 
      speak: false,
      isMute: true 
    },
    { icon: Power, label: "Shutdown", command: null, gradient: "from-rose-500 to-red-500", speak: false, isShutdown: true },
  ]

  const handleShutdown = () => {
    setShowShutdownDialog(true)
  }

  const confirmShutdown = () => {
    setShowShutdownDialog(false)
    
    // Try to close the window
    window.close()
    
    // If window.close() doesn't work (some browsers block it), show instructions
    setTimeout(() => {
      alert("⚠️ ORION OS Shutdown\n\nPlease close this browser tab manually.\n\nTo stop the backend server:\nPress Ctrl+C in the terminal where you ran:\npython scripts/api_server.py")
    }, 100)
  }

  const handleStopListening = async () => {
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
    setIsProcessing(null)
    
    if (onCommand) {
      onCommand("voice", "Voice listening stopped")
    }
  }

  const handleQuickCommand = async (command: string | null, label: string, shouldSpeak: boolean = false, isVoice: boolean = false, isShutdown: boolean = false, isMute: boolean = false) => {
    if (isProcessing && !isVoice) return

    // Handle shutdown separately
    if (isShutdown) {
      handleShutdown()
      return
    }

    // Handle mute toggle
    if (isMute) {
      // Optimistically update UI immediately (no loading state)
      setIsMuted(!isMuted)
      
      try {
        const muteCommand = !isMuted ? "mute" : "unmute" // Use opposite since we already toggled
        
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
          if (onCommand) {
            onCommand(muteCommand, data.response || `${!isMuted ? "Muted" : "Unmuted"} system`)
          }
        } else {
          // Revert on error
          setIsMuted(isMuted)
          if (onCommand) {
            onCommand(muteCommand, `Error: ${data.error || "Failed to mute/unmute"}`)
          }
        }
      } catch (error) {
        // Revert on error
        setIsMuted(isMuted)
        console.error("Mute error:", error)
        if (onCommand) {
          const errorMsg = error instanceof Error && error.name === 'AbortError' 
            ? "Mute command timed out" 
            : error instanceof Error ? error.message : "Connection failed"
          onCommand("mute", `Error: ${errorMsg}`)
        }
      }
      return
    }

    // Handle voice listening/stopping
    if (isVoice) {
      if (isListening) {
        // Stop listening (works from either button)
        handleStopListening()
        return
      }
      
      // Start listening (works from either button)
      setIsListening(true)
      
        try {
          console.log("Starting voice recognition...")
          
        // Create abort controller for timeout and manual stop
          const controller = new AbortController()
        setVoiceController(controller)
          const timeoutId = setTimeout(() => {
            controller.abort()
            if (onCommand) {
              onCommand("voice", "⏱️ Listening timeout. Please try again.")
            }
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

          console.log("Voice recognition response:", data)

          if (data.success && data.text) {
            // Execute the recognized command
            const recognizedCommand = data.text.trim()
            console.log("Recognized command:", recognizedCommand)
            
            if (onCommand) {
              onCommand(recognizedCommand, `Heard: ${recognizedCommand}`)
            }
            
            // Execute the recognized command
            try {
              const cmdResponse = await fetch("/api/command", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
              body: JSON.stringify({ command: recognizedCommand, speak: !isMuted }),
              })

              const cmdData = await cmdResponse.json()
              console.log("Command execution response:", cmdData)
              
              if (cmdData.success && onCommand) {
                onCommand(recognizedCommand, cmdData.response || "Command executed")
              } else if (onCommand) {
                onCommand(recognizedCommand, `Error: ${cmdData.error || "Command failed"}`)
              }
            } catch (cmdError) {
              console.error("Command execution error:", cmdError)
              if (onCommand) {
                onCommand(recognizedCommand, `Error executing command: ${cmdError instanceof Error ? cmdError.message : "Unknown error"}`)
              }
            }
          } else {
          // Handle "no speech detected" as a normal case, not an error
            const errorMsg = data.error || "No speech detected"
          const isNoSpeech = errorMsg.toLowerCase().includes("no speech")
          
          console.warn("Voice recognition:", errorMsg)
            if (onCommand) {
            if (isNoSpeech) {
              onCommand("voice", `🎤 No speech detected. Please try again and speak clearly.`)
            } else {
              onCommand("voice", `⚠️ ${errorMsg}`)
            }
            }
          }
        } catch (fetchError) {
        // Check if it was aborted (user stopped listening)
        if (fetchError instanceof Error && fetchError.name === 'AbortError') {
          console.log("Voice listening stopped by user")
          setIsListening(false)
          setVoiceController(null)
          if (onCommand) {
            onCommand("voice", "Voice listening stopped")
          }
        } else {
          console.error("Voice listening error:", fetchError)
          const errorMsg = fetchError instanceof Error ? fetchError.message : "Connection failed"
          setIsListening(false)
          setVoiceController(null)
          if (onCommand) {
            onCommand("voice", `Error: ${errorMsg}. Make sure the backend is running and microphone is available.`)
          }
        }
      } finally {
        setIsProcessing(null)
        setIsListening(false)
        setVoiceController(null)
      }
      return
    }
    
        // Handle regular commands
    if (command) {
      setIsProcessing(label)
      try {
        const response = await fetch("/api/command", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ command, speak: shouldSpeak }),
        })

        const data = await response.json()

        if (data.success) {
          if (onCommand) {
            onCommand(command, data.response || "Command executed")
          }
        } else {
          console.error("Command failed:", data.error)
          if (onCommand) {
            onCommand(command, `Error: ${data.error || "Command failed"}`)
        }
      }
    } catch (error) {
      console.error("Failed to execute command:", error)
      if (onCommand) {
          onCommand(command, `Error: ${error instanceof Error ? error.message : "Connection failed"}`)
      }
    } finally {
      setIsProcessing(null)
      }
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Navigation Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-4 h-4 text-violet-400" />
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Navigation</h3>
        </div>
        <div className="flex flex-col gap-2">
          {panels.map((panel) => {
            const Icon = panel.icon
            const isActive = activePanel === panel.id
            return (
              <button
                key={panel.id}
                onClick={() => setActivePanel(panel.id)}
                className={`group relative flex items-center gap-3 px-4 py-3 rounded-xl text-sm transition-all duration-300 ${
                  isActive
                    ? "bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 text-white border border-violet-500/50 shadow-lg shadow-violet-500/20"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-white border border-transparent hover:border-slate-700/50"
                }`}
              >
                <div
                  className={`p-1.5 rounded-lg transition-all ${
                    isActive ? `bg-gradient-to-r ${panel.gradient}` : "bg-slate-700/50"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-400 group-hover:text-white"}`} />
                </div>
                <span className="flex-1 text-left font-medium">{panel.label}</span>
                <span
                  className={`px-1.5 py-0.5 text-[10px] font-mono rounded ${
                    isActive ? "bg-white/20 text-white" : "bg-slate-700/50 text-slate-500"
                  }`}
                >
                  {panel.shortcut}
                </span>
                {isActive && (
                  <div className={`absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b ${panel.gradient} rounded-r-full`} />
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Quick Commands Section */}
      <div className="border-t border-violet-500/20 pt-6">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Quick Commands</h3>
        </div>
        <div className="grid grid-cols-5 gap-2">
          {quickCommands.map((cmd, i) => {
            const Icon = cmd.icon
            const processing = isProcessing === cmd.label
            return (
              <Button
                key={i}
                variant="ghost"
                size="icon"
                onClick={() => handleQuickCommand(cmd.command || null, cmd.label, cmd.speak, cmd.isVoice || false, cmd.isShutdown || false, cmd.isMute || false)}
                disabled={processing && !cmd.isVoice} // Don't disable voice button when listening (need to be able to stop)
                className={`h-12 w-full rounded-xl border transition-all duration-300 hover:scale-105
                  ${processing 
                    ? "border-violet-500/50 bg-violet-500/20 opacity-50 cursor-not-allowed" 
                    : isListening && cmd.isVoice
                    ? "border-red-500/50 bg-red-500/20 hover:border-red-500/70"
                    : isMuted && cmd.isMute
                    ? "border-amber-500/50 bg-amber-500/20 hover:border-amber-500/70"
                    : "border-slate-700/50 hover:border-violet-500/50 bg-slate-800/30 hover:bg-slate-700/50"
                  }`}
                title={cmd.label}
              >
                <Icon className={`w-4 h-4 ${
                  processing 
                    ? "text-violet-400 animate-pulse" 
                    : isListening && cmd.isVoice
                    ? "text-red-400 animate-pulse"
                    : isMuted && cmd.isMute
                    ? "text-amber-400"
                    : "text-slate-400"
                }`} />
              </Button>
            )
          })}
        </div>
      </div>

      {/* Shutdown Confirmation Dialog */}
      <AlertDialog open={showShutdownDialog} onOpenChange={setShowShutdownDialog}>
        <AlertDialogContent className="bg-slate-900 border-violet-500/30 text-white">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-red-400">
              <Power className="w-5 h-5" />
              Shutdown ORION OS?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-slate-400 pt-2">
              This will close the ORION OS application in your browser.
              <br /><br />
              <span className="text-amber-400">⚠️ Note:</span> The backend server will continue running.
              <br />
              To stop the backend server, press <kbd className="px-2 py-1 bg-slate-800 rounded text-xs">Ctrl+C</kbd> in the terminal where you started it.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-slate-800 hover:bg-slate-700 text-white border-slate-700">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmShutdown}
              className="bg-gradient-to-r from-rose-500 to-red-500 hover:from-rose-600 hover:to-red-600 text-white border-0"
            >
              <Power className="w-4 h-4 mr-2" />
              Shutdown
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
