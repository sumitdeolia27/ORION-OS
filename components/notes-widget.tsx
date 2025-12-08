"use client"

import { useState } from "react"
import type React from "react"
import { StickyNote, Plus, X } from "lucide-react"
import { Button } from "@/components/ui/button"

export function NotesWidget() {
  const [notes, setNotes] = useState(["Check system logs", "Update voice models"])
  const [newNote, setNewNote] = useState("")
  const [isAdding, setIsAdding] = useState(false)

  const addNote = () => {
    if (newNote.trim()) {
      setNotes([...notes, newNote])
      setNewNote("")
      setIsAdding(false)
    }
  }

  const removeNote = (index: number) => setNotes(notes.filter((_: string, i: number) => i !== index))

  return (
    <div className="glass p-4 rounded-xl border border-violet-500/20">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
          <StickyNote className="w-3.5 h-3.5 text-fuchsia-400" />
          Quick Notes
        </h4>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 text-slate-400 hover:text-white"
          onClick={() => setIsAdding(!isAdding)}
        >
          <Plus className="w-3.5 h-3.5" />
        </Button>
      </div>

      {isAdding && (
        <div className="mb-3">
          <input
            type="text"
            value={newNote}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewNote(e.target.value)}
            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === "Enter" && addNote()}
            placeholder="Add note..."
            className="w-full bg-slate-900/50 border border-violet-500/30 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:border-violet-500/60 focus:outline-none"
            autoFocus
          />
        </div>
      )}

      <div className="space-y-2">
        {notes.map((note: string, i: number) => (
          <div key={i} className="flex items-start gap-2 text-xs text-slate-400 group">
            <StickyNote className="w-3 h-3 mt-0.5 text-fuchsia-400" />
            <span className="flex-1">{note}</span>
            <button
              onClick={() => removeNote(i)}
              className="opacity-0 group-hover:opacity-100 text-red-400 transition-opacity"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
