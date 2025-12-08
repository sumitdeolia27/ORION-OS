"use client"

import { useState, useEffect } from "react"
import { Cpu, MemoryStick, HardDrive, Thermometer, Zap, Clock, Activity } from "lucide-react"
import { Progress } from "@/components/ui/progress"

interface SystemMetricsProps {
  compact?: boolean
}

interface MetricsData {
  cpu: number
  memory: number
  storage: number
  temperature: number
  power: number | null
  uptime: string
}

export function SystemMetrics({ compact = false }: SystemMetricsProps) {
  const [metrics, setMetrics] = useState<MetricsData>({
    cpu: 0,
    memory: 0,
    storage: 0,
    temperature: 0,
    power: null,
    uptime: "Loading...",
  })
  const [error, setError] = useState<string | null>(null)

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
        // Use fallback values on error
        setMetrics((prev) => ({
          ...prev,
          cpu: prev.cpu || 0,
          memory: prev.memory || 0,
          storage: prev.storage || 0,
        }))
        return
      }
      
      const data = await response.json().catch(() => null)

      if (data?.success && data.metrics) {
        setMetrics({
          cpu: data.metrics.cpu || 0,
          memory: data.metrics.memory || 0,
          storage: data.metrics.storage || 0,
          temperature: data.metrics.temperature || 0,
          power: data.metrics.battery ?? null,
          uptime: data.metrics.uptime || "Unknown",
        })
        setError(null)
      } else {
        setError(data?.error || "Failed to fetch metrics")
        // Use fallback values on error
        setMetrics((prev) => ({
          ...prev,
          cpu: prev.cpu || 0,
          memory: prev.memory || 0,
          storage: prev.storage || 0,
        }))
      }
    } catch (err) {
      // Completely suppress console errors - just update UI state
      setError("Connection unavailable")
      // Use fallback values on error
      setMetrics((prev) => ({
        ...prev,
        cpu: prev.cpu || 0,
        memory: prev.memory || 0,
        storage: prev.storage || 0,
      }))
    }
  }

  useEffect(() => {
    // Fetch immediately
    fetchMetrics()
    
    // Then fetch every 2 seconds
    const interval = setInterval(fetchMetrics, 2000)
    return () => clearInterval(interval)
  }, [])

  const items = [
    {
      icon: Cpu,
      label: "CPU Usage",
      value: metrics.cpu,
      unit: "%",
      color: metrics.cpu > 80 ? "rose" : "violet",
    },
    {
      icon: MemoryStick,
      label: "Memory",
      value: metrics.memory,
      unit: "%",
      color: metrics.memory > 85 ? "rose" : "cyan",
    },
    {
      icon: HardDrive,
      label: "Storage",
      value: metrics.storage,
      unit: "%",
      color: "fuchsia",
    },
    {
      icon: Thermometer,
      label: "Temperature",
      value: metrics.temperature,
      unit: "°C",
      color: metrics.temperature > 70 ? "rose" : "amber",
    },
    {
      icon: Zap,
      label: "Power",
      value: metrics.power ?? 0,
      unit: metrics.power !== null ? "%" : "N/A",
      color: metrics.power !== null && metrics.power < 20 ? "rose" : "emerald",
    },
    {
      icon: Clock,
      label: "Uptime",
      value: metrics.uptime,
      unit: "",
      color: "slate",
      isText: true,
    },
  ]

  const colorClasses: Record<string, { text: string; bg: string }> = {
    violet: { text: "text-violet-400", bg: "bg-violet-500" },
    cyan: { text: "text-cyan-400", bg: "bg-cyan-500" },
    fuchsia: { text: "text-fuchsia-400", bg: "bg-fuchsia-500" },
    amber: { text: "text-amber-400", bg: "bg-amber-500" },
    emerald: { text: "text-emerald-400", bg: "bg-emerald-500" },
    rose: { text: "text-rose-400", bg: "bg-rose-500" },
    slate: { text: "text-slate-400", bg: "bg-slate-500" },
  }

  if (compact) {
    return (
      <div className="space-y-4">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-violet-400" />
          System Metrics
        </h3>
        {items.map((item, i) => {
          const colors = colorClasses[item.color]
          return (
            <div key={i} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <item.icon className={`w-4 h-4 ${colors.text}`} />
                  <span className="text-slate-400">{item.label}</span>
                </div>
                <span className={colors.text}>
                  {typeof item.value === "number" ? Math.round(item.value) : item.value}
                  {item.unit}
                </span>
              </div>
              {!item.isText && item.value > 0 && (
                <div className="h-1.5 bg-slate-800/50 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${colors.bg} rounded-full transition-all duration-500`}
                    style={{ width: `${Math.min(100, Math.max(0, item.value))}%` }}
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="h-full p-6">
      <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-6">
        <Activity className="w-5 h-5 text-rose-400" />
        System Metrics
        {error && (
          <span className="text-xs text-red-400 font-normal ml-2">
            (Backend offline - showing cached data)
          </span>
        )}
      </h2>
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item, i) => {
          const colors = colorClasses[item.color]
          return (
            <div key={i} className="glass p-5 rounded-xl border border-violet-500/20">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-slate-800/50">
                  <item.icon className={`w-5 h-5 ${colors.text}`} />
                </div>
                <span className="text-sm text-slate-400">{item.label}</span>
              </div>
              <div className={`text-2xl font-bold ${colors.text}`}>
                {typeof item.value === "number" ? Math.round(item.value) : item.value}
                {item.unit}
              </div>
              {!item.isText && item.value > 0 && (
                <div className="mt-3 h-2 bg-slate-800/50 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${colors.bg} rounded-full transition-all duration-500`}
                    style={{ width: `${Math.min(100, Math.max(0, item.value))}%` }}
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
