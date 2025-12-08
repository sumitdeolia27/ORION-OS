"use client"

import { Search, Clock, Terminal, ArrowRight, History } from "lucide-react"
import { useState, useRef, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"

interface CommandHistoryProps {
  history: { command: string; response: string; timestamp: Date }[]
}

export function CommandHistory({ history }: CommandHistoryProps) {
  const [search, setSearch] = useState("")
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  const filtered = history.filter(
    (item) =>
      item.command.toLowerCase().includes(search.toLowerCase()) ||
      item.response.toLowerCase().includes(search.toLowerCase()),
  )

  // Smooth scroll to top when search changes
  useEffect(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector('[data-slot="scroll-area-viewport"]') as HTMLElement
      if (viewport) {
        requestAnimationFrame(() => {
          viewport.scrollTo({
            top: 0,
            behavior: "smooth",
          })
        })
      }
    }
  }, [search])

  // Auto-scroll to bottom when new history items are added
  useEffect(() => {
    if (scrollAreaRef.current && history.length > 0) {
      const viewport = scrollAreaRef.current.querySelector('[data-slot="scroll-area-viewport"]') as HTMLElement
      if (viewport) {
        requestAnimationFrame(() => {
          viewport.scrollTo({
            top: viewport.scrollHeight,
            behavior: "smooth",
          })
        })
      }
    }
  }, [history.length])

  return (
    <div className="h-full flex flex-col p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            Command History
          </h2>
          <p className="text-sm text-slate-400 mt-1">{history.length} commands executed</p>
        </div>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search history..."
          className="pl-11 bg-slate-900/50 border-violet-500/30 focus:border-violet-500/60 text-white placeholder:text-slate-500"
        />
      </div>

      <div ref={scrollAreaRef} className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
        {filtered.length === 0 ? (
          <div className="text-center py-12">
            <Terminal className="w-12 h-12 mx-auto text-slate-600 mb-4" />
            <p className="text-slate-400">No commands in history</p>
            <p className="text-sm text-slate-500">Execute some commands to see them here</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((item, i) => (
              <div key={i} className="glass p-4 rounded-xl border border-violet-500/20">
                <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
                  <Clock className="w-3 h-3" />
                  {item.timestamp.toLocaleString()}
                </div>
                <div className="flex items-start gap-2 mb-2">
                  <ArrowRight className="w-4 h-4 text-cyan-400 mt-0.5" />
                  <p className="text-cyan-400 font-mono text-sm">{item.command}</p>
                </div>
                <p className="text-sm text-slate-400 pl-6">
                  {item.response.slice(0, 150)}
                  {item.response.length > 150 && "..."}
                </p>
              </div>
            ))}
          </div>
        )}
        </ScrollArea>
      </div>
    </div>
  )
}
