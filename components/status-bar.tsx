"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Wifi, WifiOff, Mic, MicOff, Activity, Cpu, HardDrive, Volume2, Battery, BatteryCharging } from "lucide-react"
import { Progress } from "@/components/ui/progress"

export function StatusBar() {
  const [time, setTime] = useState<Date | null>(null)
  const [isOnline, setIsOnline] = useState(true)
  const [isMicActive, setIsMicActive] = useState(false)
  const [volume, setVolume] = useState(65)
  const [isChangingVolume, setIsChangingVolume] = useState(false)
  const volumeTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const isChangingVolumeRef = useRef(false)
  const [battery, setBattery] = useState(87)
  const [isCharging, setIsCharging] = useState(false)
  const [systemStats, setSystemStats] = useState({
    cpu: 0,
    memory: 0,
    storage: 0,
  })

  useEffect(() => {
    // Initialize time on client side only
    setTime(new Date())
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    window.addEventListener("online", handleOnline)
    window.addEventListener("offline", handleOffline)
    setIsOnline(navigator.onLine)
    return () => {
      window.removeEventListener("online", handleOnline)
      window.removeEventListener("offline", handleOffline)
    }
  }, [])

  const handleVolumeChange = (newVolume: number) => {
    // Update UI immediately for better UX
    setVolume(newVolume)
    
    // Clear existing timeout
    if (volumeTimeoutRef.current) {
      clearTimeout(volumeTimeoutRef.current)
    }
    
    // Debounce the API call - only send after user stops dragging
    volumeTimeoutRef.current = setTimeout(async () => {
      setIsChangingVolume(true)
      isChangingVolumeRef.current = true
      try {
        // Send volume change to backend API
        const response = await fetch("/api/volume", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ volume: newVolume }),
        })

        const data = await response.json()
        if (data.success) {
          // Update with actual volume from backend
          if (data.volume !== undefined) {
            setVolume(data.volume)
          }
        } else {
          console.error("Failed to set volume:", data.error)
          // Revert on error
          await fetchCurrentVolume()
        }
      } catch (err) {
        console.error("Failed to change volume:", err)
        // Revert on error
        await fetchCurrentVolume()
      } finally {
        setIsChangingVolume(false)
        isChangingVolumeRef.current = false
      }
    }, 300) // Wait 300ms after user stops dragging
  }

  const fetchCurrentVolume = useCallback(async () => {
    // Don't update volume if user is currently changing it
    if (isChangingVolumeRef.current) {
      return
    }
    try {
      // Add timeout to prevent hanging requests
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 3000) // 3 second timeout
      
      const response = await fetch("/api/volume", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        signal: controller.signal,
      }).catch((fetchErr) => {
        // Catch fetch errors (network, CORS, etc.) and convert to a handled error
        clearTimeout(timeoutId)
        throw new Error("Network error")
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        return // Silently return on non-OK responses
      }

      const data = await response.json().catch(() => null)
      if (data?.success && data.volume !== undefined) {
        setVolume(data.volume)
      }
    } catch (err) {
      // Completely suppress all errors - don't log anything
      // This prevents console spam from network issues
    }
  }, [])

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        // Add timeout to prevent hanging requests
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
        
        const response = await fetch("/api/system/metrics", {
          signal: controller.signal,
        }).catch((fetchErr) => {
          // Catch fetch errors (network, CORS, etc.) and convert to a handled error
          clearTimeout(timeoutId)
          throw new Error("Network error")
        })
        
        clearTimeout(timeoutId)
        
        if (!response.ok) {
          return // Silently return on non-OK responses
        }
        
        const data = await response.json().catch(() => null)

        if (data?.success && data.metrics) {
          setSystemStats({
            cpu: data.metrics.cpu || 0,
            memory: data.metrics.memory || 0,
            storage: data.metrics.storage || 0,
          })

          // Update battery if available
          if (data.metrics.battery !== null && data.metrics.battery !== undefined) {
            setBattery(data.metrics.battery)
            setIsCharging(data.metrics.battery_plugged || false)
          }
        }
      } catch (err) {
        // Completely suppress all errors - don't log anything
        // This prevents console spam from network issues, timeouts, etc.
        // The UI will continue to show the last known values
      }
    }

    // Fetch immediately
    fetchMetrics()
    fetchCurrentVolume()
    
    // Then fetch every 3 seconds (reduced frequency to avoid overwhelming)
    const interval = setInterval(() => {
      fetchMetrics()
      // Periodically fetch volume to sync with external changes (keyboard, system controls)
      fetchCurrentVolume()
    }, 3000)
    return () => {
      clearInterval(interval)
      if (volumeTimeoutRef.current) {
        clearTimeout(volumeTimeoutRef.current)
      }
    }
  }, [fetchCurrentVolume])

  return (
    <div className="glass-strong border-b border-violet-500/20 px-6 py-2.5 flex items-center justify-between text-sm">
      <div className="flex items-center gap-4">
        {/* Connection Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
          {isOnline ? (
            <Wifi className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          ) : (
            <WifiOff className="w-3.5 h-3.5 text-red-400" />
          )}
          <span className={`font-medium text-xs ${isOnline ? "text-emerald-400" : "text-red-400"}`}>
            {isOnline ? "Online" : "Offline"}
          </span>
        </div>

        {/* System Metrics */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <Cpu className="w-3.5 h-3.5 text-violet-400" />
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">CPU</span>
              <div className="w-12 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                <div
                  className="h-full bg-violet-500 rounded-full transition-all duration-500"
                  style={{ width: `${systemStats.cpu}%` }}
                />
              </div>
              <span className="text-xs font-medium text-violet-400 w-7">{Math.round(systemStats.cpu)}%</span>
            </div>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">RAM</span>
              <div className="w-12 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                <div
                  className="h-full bg-cyan-500 rounded-full transition-all duration-500"
                  style={{ width: `${systemStats.memory}%` }}
                />
              </div>
              <span className="text-xs font-medium text-cyan-400 w-7">{Math.round(systemStats.memory)}%</span>
            </div>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <HardDrive className="w-3.5 h-3.5 text-fuchsia-400" />
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">SSD</span>
              <div className="w-12 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                <div
                  className="h-full bg-fuchsia-500 rounded-full transition-all duration-500"
                  style={{ width: `${systemStats.storage}%` }}
                />
              </div>
              <span className="text-xs font-medium text-fuchsia-400 w-7">{Math.round(systemStats.storage)}%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Volume Control */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
          <Volume2 className="w-3.5 h-3.5 text-violet-400" />
          <div className="flex items-center gap-2">
            <input
              type="range"
              min="0"
              max="100"
              value={volume}
              onChange={(e) => handleVolumeChange(Number(e.target.value))}
              onMouseUp={(e) => {
                // Immediately send on mouse up
                if (volumeTimeoutRef.current) {
                  clearTimeout(volumeTimeoutRef.current)
                }
                handleVolumeChange(Number((e.target as HTMLInputElement).value))
              }}
              className="w-16 h-1 rounded-full appearance-none cursor-pointer transition-opacity"
              style={{
                background: `linear-gradient(to right, #8b5cf6 ${volume}%, #1e293b ${volume}%)`,
                opacity: isChangingVolume ? 0.7 : 1,
              }}
            />
            <span className="text-xs font-medium text-violet-400 w-7">{volume}%</span>
          </div>
        </div>

        {/* Battery Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
          {isCharging ? (
            <BatteryCharging className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          ) : (
            <Battery className="w-3.5 h-3.5 text-emerald-400" />
          )}
          <div className="flex items-center gap-2">
            <div className="w-12 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                style={{ width: `${battery}%` }}
              />
            </div>
            <span className="text-xs font-medium text-emerald-400 w-7">{Math.round(battery)}%</span>
          </div>
        </div>

        {/* Mic Status */}
        <button
          onClick={() => setIsMicActive(!isMicActive)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all border ${
            isMicActive
              ? "bg-violet-500/20 text-violet-400 border-violet-500/50 shadow-lg shadow-violet-500/20"
              : "bg-slate-800/50 text-slate-400 border-slate-700/50 hover:bg-slate-700/50"
          }`}
        >
          {isMicActive ? <Mic className="w-3.5 h-3.5 animate-pulse" /> : <MicOff className="w-3.5 h-3.5" />}
          <span className="text-xs font-medium">{isMicActive ? "Listening" : "Mic Off"}</span>
        </button>

        {/* Time Display */}
        <div className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-violet-500/20 via-fuchsia-500/20 to-cyan-500/20 border border-violet-500/30">
          <div className="font-mono text-violet-400 font-semibold text-sm glow-text">
            {time ? time.toLocaleTimeString("en-US", { hour12: false }) : "--:--:--"}
          </div>
          <div className="text-[10px] text-slate-500 text-center">
            {time ? time.toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "--"}
          </div>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-violet-500/10 border border-violet-500/30">
          <div className="relative">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-400 animate-ping opacity-75" />
          </div>
          <span className="text-xs font-semibold text-violet-400">Orion Online</span>
        </div>
      </div>
    </div>
  )
}
