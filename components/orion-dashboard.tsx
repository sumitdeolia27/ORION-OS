"use client"

import { useState, useEffect } from "react"
import { StatusBar } from "./status-bar"
import { CommandConsole } from "./command-console"
import { QuickActions } from "./quick-actions"
import { SystemMetrics } from "./system-metrics"
import { TasksPanel } from "./tasks-panel"
import { RemindersPanel } from "./reminders-panel"
import { AiChat } from "./ai-chat"
import { FileExplorer } from "./file-explorer"
import { CommandHistory } from "./command-history"
import { WeatherWidget } from "./weather-widget"
import { NotesWidget } from "./notes-widget"
import { OrionOrb } from "./orion-orb"
import { Sparkles, Zap, Command } from "lucide-react"

export function OrionDashboard() {
  const [activePanel, setActivePanel] = useState<string>("ai")
  const [commandHistory, setCommandHistory] = useState<{ command: string; response: string; timestamp: Date }[]>([])
  
  // Shared voice state for Quick Commands and Command Console
  const [isListening, setIsListening] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [voiceController, setVoiceController] = useState<AbortController | null>(null)

  const addToHistory = (command: string, response: string) => {
    setCommandHistory((prev: { command: string; response: string; timestamp: Date }[]) => [
      { command, response, timestamp: new Date() },
      ...prev.slice(0, 99),
    ])
  }

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case "k":
            e.preventDefault()
            setActivePanel("console")
            break
          case "a":
            e.preventDefault()
            setActivePanel("ai")
            break
          case "t":
            e.preventDefault()
            setActivePanel("tasks")
            break
          case "r":
            e.preventDefault()
            setActivePanel("reminders")
            break
          case "f":
            e.preventDefault()
            setActivePanel("files")
            break
        }
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white relative overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-violet-950/30 via-transparent to-cyan-950/30" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-600/10 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-fuchsia-600/5 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: "2s" }} />
        
        {/* Grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: "linear-gradient(rgba(139, 92, 246, 0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(139, 92, 246, 0.5) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />
        
        {/* Scan line */}
        <div className="scan-line" />
      </div>

      <div className="relative z-10 flex flex-col h-screen">
        <StatusBar />

        {/* Modern Header */}
        <header className="glass-strong border-b border-violet-500/20 px-8 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="relative">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-600 via-fuchsia-500 to-cyan-500 flex items-center justify-center animate-glow">
                  <Sparkles className="w-7 h-7 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-400 rounded-full animate-pulse border-2 border-[#0a0a0f]" />
              </div>
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 via-fuchsia-400 to-cyan-400 bg-clip-text text-transparent glow-text">
                    ORION OS
                  </h1>
                  <Sparkles className="w-5 h-5 text-violet-400 animate-pulse" />
                </div>
                <p className="text-sm text-slate-400 flex items-center gap-2">
                  <Zap className="w-3.5 h-3.5 text-cyan-400" />
                  Advanced AI Command Center v3.0
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="glass px-4 py-2.5 rounded-xl border border-violet-500/30 flex items-center gap-3">
                <Command className="w-4 h-4 text-violet-400" />
                <kbd className="px-2 py-1 text-xs bg-violet-500/20 text-violet-400 rounded font-mono border border-violet-500/30">
                  Ctrl+A
                </kbd>
                <span className="text-xs text-slate-400">AI Chat</span>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden gap-4 p-4">
          {/* Left Sidebar - Navigation & Quick Actions */}
          <aside className="w-72 glass-strong rounded-2xl p-5 flex flex-col gap-5 overflow-y-auto">
            <QuickActions 
              activePanel={activePanel} 
              setActivePanel={setActivePanel} 
              onCommand={addToHistory}
              isListening={isListening}
              setIsListening={setIsListening}
              isMuted={isMuted}
              setIsMuted={setIsMuted}
              voiceController={voiceController}
              setVoiceController={setVoiceController}
            />
            <div className="border-t border-violet-500/20 pt-5">
              <WeatherWidget />
            </div>
            <div className="border-t border-violet-500/20 pt-5">
              <NotesWidget />
            </div>
          </aside>

          {/* Main Panel - Dynamic Content */}
          <main className="flex-1 glass-strong rounded-2xl overflow-hidden flex flex-col">
            <div className="flex-1 overflow-hidden">
              {activePanel === "console" && (
                <CommandConsole 
                  onCommand={addToHistory}
                  isListening={isListening}
                  setIsListening={setIsListening}
                  isMuted={isMuted}
                  setIsMuted={setIsMuted}
                  voiceController={voiceController}
                  setVoiceController={setVoiceController}
                />
              )}
              {activePanel === "tasks" && <TasksPanel />}
              {activePanel === "reminders" && <RemindersPanel />}
              {activePanel === "files" && <FileExplorer />}
              {activePanel === "ai" && <AiChat onCommand={addToHistory} />}
              {activePanel === "history" && <CommandHistory history={commandHistory} />}
              {activePanel === "metrics" && <SystemMetrics />}
            </div>
          </main>

          {/* Right Sidebar - System Info */}
          <aside className="w-80 glass-strong rounded-2xl p-6 overflow-y-auto">
            <div className="flex flex-col gap-6">
              <div className="flex items-center justify-center py-6">
                <OrionOrb size="lg" />
              </div>
              <div className="border-t border-violet-500/20 pt-6">
                <SystemMetrics compact />
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
