"use client"

import { useState, useEffect } from "react"
import { Plus, Trash2, Circle, CheckCircle2, Flag, ListTodo } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"

interface Task {
  id: string
  title: string
  completed: boolean
  priority: "low" | "medium" | "high"
  createdAt: Date
}

export function TasksPanel() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [newTask, setNewTask] = useState("")
  const [priority, setPriority] = useState<"low" | "medium" | "high">("medium")

  const addTask = () => {
    if (!newTask.trim()) return
    setTasks([
      ...tasks,
      { id: Date.now().toString(), title: newTask, completed: false, priority, createdAt: new Date() },
    ])
    setNewTask("")
  }

  const toggleTask = (id: string) => {
    setTasks(tasks.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t)))
  }

  const deleteTask = (id: string) => {
    setTasks(tasks.filter((t) => t.id !== id))
  }

  useEffect(() => {
    // Initialize tasks on client side only
    setTasks([
      { id: "1", title: "Initialize Orion core systems", completed: true, priority: "high", createdAt: new Date() },
      {
        id: "2",
        title: "Configure neural network parameters",
        completed: false,
        priority: "high",
        createdAt: new Date(),
      },
      { id: "3", title: "Run diagnostic tests", completed: false, priority: "medium", createdAt: new Date() },
      { id: "4", title: "Update voice recognition models", completed: false, priority: "low", createdAt: new Date() },
    ])
  }, [])

  const priorityColors = {
    low: "text-slate-400",
    medium: "text-amber-400",
    high: "text-red-400",
  }

  const priorityBg = {
    low: "bg-slate-400/20",
    medium: "bg-amber-400/20",
    high: "bg-red-400/20",
  }

  const completedCount = tasks.filter((t) => t.completed).length

  return (
    <div className="h-full flex flex-col p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ListTodo className="w-5 h-5 text-emerald-400" />
            Task Manager
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            {completedCount}/{tasks.length} tasks completed
          </p>
        </div>
        <div className="flex items-center gap-2">
          {(["low", "medium", "high"] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPriority(p)}
              className={`p-2.5 rounded-xl transition-all ${
                priority === p
                  ? `${priorityBg[p]} border border-current ${priorityColors[p]}`
                  : "bg-slate-800/50 text-slate-500 hover:bg-slate-700/50 border border-transparent"
              }`}
            >
              <Flag className="w-4 h-4" />
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-3 mb-6">
        <Input
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)}
          placeholder="Add new task..."
          onKeyDown={(e) => e.key === "Enter" && addTask()}
          className="flex-1 bg-slate-900/50 border-violet-500/30 focus:border-violet-500/60 text-white placeholder:text-slate-500"
        />
        <Button
          onClick={addTask}
          className="px-5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white border-0"
        >
          <Plus className="w-5 h-5" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-2">
          {tasks.map((task) => (
            <div
              key={task.id}
              className={`glass p-4 rounded-xl border border-violet-500/20 flex items-center gap-3 transition-all ${
                task.completed ? "opacity-60" : ""
              }`}
            >
              <button
                onClick={() => toggleTask(task.id)}
                className="text-emerald-400 hover:text-emerald-300 transition-colors"
              >
                {task.completed ? <CheckCircle2 className="w-5 h-5" /> : <Circle className="w-5 h-5" />}
              </button>
              <div className={`p-1 rounded ${priorityBg[task.priority]}`}>
                <Flag className={`w-3.5 h-3.5 ${priorityColors[task.priority]}`} />
              </div>
              <span className={`flex-1 ${task.completed ? "line-through text-slate-500" : "text-white"}`}>
                {task.title}
              </span>
              <button
                onClick={() => deleteTask(task.id)}
                className="text-slate-500 hover:text-red-400 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
