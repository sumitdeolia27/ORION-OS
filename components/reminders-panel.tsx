"use client"

import { useState, useEffect, useRef } from "react"
import { Plus, Bell, BellRing, Trash2, Clock, Calendar, RefreshCw } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { toast } from "sonner"

interface Reminder {
  id: string
  title: string
  time: string
  date: string
  active: boolean
}

export function RemindersPanel() {
  const [reminders, setReminders] = useState<Reminder[]>([])
  const [newReminder, setNewReminder] = useState("")
  const [time, setTime] = useState("09:00")
  const [date, setDate] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Load notified reminders from localStorage to persist across navigations
  const loadNotifiedReminders = (): Set<string> => {
    if (typeof window === "undefined") return new Set()
    try {
      const stored = localStorage.getItem("orion_notified_reminders")
      if (stored) {
        const data = JSON.parse(stored)
        // Only keep reminders from today to prevent localStorage from growing too large
        const today = new Date().toISOString().split("T")[0]
        const filtered = data.filter((key: string) => key.includes(today))
        return new Set(filtered)
      }
    } catch (err) {
      // If parsing fails, return empty set
    }
    return new Set()
  }
  
  const saveNotifiedReminders = (notified: Set<string>) => {
    if (typeof window === "undefined") return
    try {
      const today = new Date().toISOString().split("T")[0]
      // Only save reminders from today
      const filtered = Array.from(notified).filter((key) => key.includes(today))
      localStorage.setItem("orion_notified_reminders", JSON.stringify(filtered))
    } catch (err) {
      // If saving fails, silently continue
    }
  }
  
  const notifiedReminders = useRef<Set<string>>(loadNotifiedReminders()) // Track which reminders have been notified

  const fetchReminders = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await fetch("/api/reminders")
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      console.log("Reminders API response:", data)
      
      // Handle response - check for reminders array regardless of success flag
      const remindersArray = data.reminders || data.reminder || []
      
      if (Array.isArray(remindersArray)) {
        if (remindersArray.length > 0) {
          // Normalize reminders to ensure they have all required fields and unique IDs
          const normalizedReminders = remindersArray.map((reminder: any, index: number) => {
            // Handle both old format (text, created) and new format (title, time, date)
            const title = reminder.title || reminder.text || `Reminder ${index + 1}`
            // Generate unique ID for reminders without one - use index and timestamp to ensure uniqueness
            const id = reminder.id || `reminder-${Date.now()}-${index}-${Math.random().toString(36).substr(2, 9)}`
            
            // Parse time - handle both HH:MM format and full timestamp
            let time = "09:00"
            if (reminder.time) {
              if (reminder.time.includes("T") || reminder.time.includes(" ")) {
                // Full timestamp - extract time portion
                try {
                  const dateObj = new Date(reminder.time)
                  const hours = dateObj.getHours().toString().padStart(2, "0")
                  const minutes = dateObj.getMinutes().toString().padStart(2, "0")
                  time = `${hours}:${minutes}`
                } catch {
                  time = "09:00"
                }
              } else if (reminder.time.match(/^\d{2}:\d{2}$/)) {
                // Already in HH:MM format
                time = reminder.time
              }
            }
            
            // Parse date - handle both date string and timestamp
            let date = new Date().toISOString().split("T")[0]
            if (reminder.date) {
              date = reminder.date
            } else if (reminder.created) {
              try {
                date = new Date(reminder.created).toISOString().split("T")[0]
              } catch {
                date = new Date().toISOString().split("T")[0]
              }
            } else if (reminder.time && reminder.time.includes("T")) {
              // Extract date from timestamp
              try {
                date = new Date(reminder.time).toISOString().split("T")[0]
              } catch {
                date = new Date().toISOString().split("T")[0]
              }
            }
            
            const active = reminder.active !== undefined ? reminder.active : true
            
            return {
              id,
              title,
              time,
              date,
              active
            }
          })
          console.log("Normalized reminders:", normalizedReminders)
          console.log("Setting reminders count:", normalizedReminders.length)
          setReminders(normalizedReminders)
        } else {
          // Empty array - show empty state
          console.log("No reminders found in response (empty array)")
          setReminders([])
        }
      } else {
        // Invalid response format - no reminders array
        console.error("Invalid response format - no reminders array:", data)
        if (!data.success && data.error) {
          setError(data.error || "Failed to load reminders")
        } else {
          setError("Invalid response format from server")
        }
        setReminders([])
      }
    } catch (err) {
      console.error("Failed to fetch reminders:", err)
      setError(`Failed to load reminders: ${err instanceof Error ? err.message : "Unknown error"}. Make sure the backend server is running.`)
      // Show empty array on error - user can add reminders
      setReminders([])
    } finally {
      setIsLoading(false)
    }
  }

  const addReminder = async () => {
    if (!newReminder.trim()) return
    
    const newReminderObj: Reminder = {
      id: Date.now().toString(),
      title: newReminder,
      time,
      date: date || new Date().toISOString().split("T")[0],
      active: true,
    }
    
    // Optimistically update UI
    setReminders([...reminders, newReminderObj])
    setNewReminder("")
    
    // Try to save to backend and refresh
    try {
      const response = await fetch("/api/reminders", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ reminder: newReminderObj }),
      })
      
      if (response.ok) {
        // Refresh reminders from backend to ensure sync
        await fetchReminders()
      } else {
        console.error("Failed to save reminder:", await response.text())
      }
    } catch (err) {
      console.error("Failed to save reminder:", err)
      // Reminder is already in UI, so we continue
    }
  }

  const toggleReminder = async (id: string) => {
    const updated = reminders.map((r) => (r.id === id ? { ...r, active: !r.active } : r))
    setReminders(updated)
    
    // Try to update backend (but don't block on error)
    try {
      const reminder = updated.find((r) => r.id === id)
      if (reminder) {
        await fetch("/api/reminders", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ reminder }),
        })
      }
    } catch (err) {
      console.error("Failed to update reminder:", err)
    }
  }

  const deleteReminder = async (id: string) => {
    setReminders(reminders.filter((r) => r.id !== id))
    
    // Try to delete from backend (but don't block on error)
    try {
      await fetch("/api/reminders", {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ id }),
      })
    } catch (err) {
      console.error("Failed to delete reminder:", err)
    }
  }

  // Check for reminders that need to be triggered
  useEffect(() => {
    // Load notified reminders from localStorage on mount to persist across navigations
    notifiedReminders.current = loadNotifiedReminders()
    
    // Don't check if there are no reminders
    if (reminders.length === 0) return
    
    const checkReminders = () => {
      // Reload from localStorage at the start of each check to ensure we have latest state
      // This prevents notifications from showing on every navigation
      notifiedReminders.current = loadNotifiedReminders()
      
      const now = new Date()
      const currentDate = now.toISOString().split("T")[0]
      const currentHour = now.getHours()
      const currentMinute = now.getMinutes()
      
      // Only check active reminders
      const activeReminders = reminders.filter((r) => r.active ?? true)
      if (activeReminders.length === 0) return
      
      activeReminders.forEach((reminder) => {
        try {
          // Check if reminder date matches today
          if (reminder.date !== currentDate) return
          
          // Parse reminder time - handle both HH:MM and invalid formats
          const timeParts = reminder.time.split(":")
          if (timeParts.length !== 2) return
          
          const reminderHour = parseInt(timeParts[0], 10)
          const reminderMinute = parseInt(timeParts[1], 10)
          
          // Validate parsed time
          if (isNaN(reminderHour) || isNaN(reminderMinute)) return
          if (reminderHour < 0 || reminderHour > 23 || reminderMinute < 0 || reminderMinute > 59) return
          
          // Check if reminder time matches current time (exact match)
          if (reminderHour === currentHour && reminderMinute === currentMinute) {
            // Create unique key for this reminder at this time
            const reminderKey = `${reminder.id}-${currentDate}-${currentHour}-${currentMinute}`
            
            // Reload from localStorage to ensure we have the latest state (in case of navigation)
            const latestNotified = loadNotifiedReminders()
            notifiedReminders.current = latestNotified
            
            // Skip if already notified (check both in-memory and localStorage)
            if (notifiedReminders.current.has(reminderKey)) {
              return
            }
            
            // Show browser notification if permission granted
            if ("Notification" in window && Notification.permission === "granted") {
              try {
                new Notification("🔔 Reminder", {
                  body: reminder.title,
                  icon: "/icon-dark-32x32.png",
                  tag: reminderKey, // Prevent duplicate notifications
                  requireInteraction: false,
                  silent: false,
                })
              } catch (err) {
                // Notification creation failed, continue with toast
              }
            }
            
            // Show toast notification
            toast.success("🔔 Reminder", {
              description: `${reminder.title}\n${reminder.date} at ${reminder.time}`,
              duration: 10000, // Show for 10 seconds
              action: {
                label: "Dismiss",
                onClick: () => {},
              },
            })
            
            // Mark as notified immediately to prevent duplicates
            notifiedReminders.current.add(reminderKey)
            
            // Save to localStorage to persist across navigations
            saveNotifiedReminders(notifiedReminders.current)
            
            // Clean up old notification keys (keep only today's reminders)
            const today = new Date().toISOString().split("T")[0]
            const filtered = Array.from(notifiedReminders.current).filter((key) => key.includes(today))
            notifiedReminders.current = new Set(filtered)
          }
        } catch (err) {
          // Silently skip reminders with invalid data
          console.error("Error checking reminder:", err)
        }
      })
    }
    
    // Request notification permission on mount (only once)
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission().catch(() => {
        // User denied permission, silently continue
      })
    }
    
    // Check reminders immediately (only if there are active reminders)
    if (reminders.some((r) => r.active ?? true)) {
      checkReminders()
    }
    
    // Check reminders every 5 seconds for more responsive triggering
    const interval = setInterval(() => {
      if (reminders.some((r) => r.active ?? true)) {
        checkReminders()
      }
    }, 5000) // Check every 5 seconds
    
    return () => clearInterval(interval)
  }, [reminders])
  
  useEffect(() => {
    // Initialize date on client side only
    setDate(new Date().toISOString().split("T")[0])
    // Fetch reminders from API
    fetchReminders()
  }, [])

  return (
    <div className="h-full flex flex-col p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Bell className="w-5 h-5 text-amber-400" />
            Reminders
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            {isLoading ? "Loading..." : `${reminders.filter((r) => r.active ?? true).length} active reminders`}
          </p>
          {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
        </div>
        <Button
          onClick={fetchReminders}
          disabled={isLoading}
          variant="ghost"
          size="sm"
          className="text-slate-400 hover:text-white"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      <div className="space-y-3 mb-6">
        <Input
          value={newReminder}
          onChange={(e) => setNewReminder(e.target.value)}
          placeholder="Add new reminder..."
          className="w-full bg-slate-900/50 border-violet-500/30 focus:border-violet-500/60 text-white placeholder:text-slate-500"
        />
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <Input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="pl-10 bg-slate-900/50 border-violet-500/30 focus:border-violet-500/60 text-white"
            />
          </div>
          <div className="flex-1 relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <Input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="pl-10 bg-slate-900/50 border-violet-500/30 focus:border-violet-500/60 text-white"
            />
          </div>
          <Button
            onClick={addReminder}
            className="px-5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white border-0"
          >
            <Plus className="w-5 h-5" />
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-2">
          {reminders.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <Bell className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">No reminders yet</p>
              <p className="text-xs text-slate-600 mt-1">Add a reminder above to get started</p>
            </div>
          ) : (
            reminders.map((reminder, index) => {
              // Ensure each reminder has a unique key
              const uniqueKey = reminder.id || `reminder-${index}-${reminder.title}-${reminder.time}`
              return (
                <div
                  key={uniqueKey}
                  className={`glass p-4 rounded-xl border border-violet-500/20 flex items-center gap-3 transition-all ${
                    !(reminder.active ?? true) ? "opacity-60" : ""
                  }`}
                >
                  <button
                    onClick={() => toggleReminder(reminder.id)}
                    className={(reminder.active ?? true) ? "text-amber-400" : "text-slate-500"}
                  >
                    {(reminder.active ?? true) ? <BellRing className="w-5 h-5" /> : <Bell className="w-5 h-5" />}
                  </button>
                  <div className="flex-1">
                    <p className={!(reminder.active ?? true) ? "text-slate-500" : "text-white"}>{reminder.title}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {reminder.date} at {reminder.time}
                    </p>
                  </div>
                  <button
                    onClick={() => deleteReminder(reminder.id)}
                    className="text-slate-500 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              )
            })
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
