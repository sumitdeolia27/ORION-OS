"use client"

import { useState } from "react"
import { Cloud, Sun, CloudRain, Thermometer } from "lucide-react"

export function WeatherWidget() {
  const [weather] = useState({ temp: 22, condition: "Sunny", humidity: 45 })
  const icons: Record<string, typeof Sun> = { Sunny: Sun, Cloudy: Cloud, Rainy: CloudRain }
  const Icon = icons[weather.condition] || Sun

  return (
    <div className="glass p-4 rounded-xl border border-violet-500/20">
      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <Cloud className="w-3.5 h-3.5 text-cyan-400" />
        Weather
      </h4>
      <div className="flex items-center gap-4">
        <div className="p-2.5 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20">
          <Icon className="w-10 h-10 text-amber-400" />
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{weather.temp}°C</p>
          <p className="text-xs text-slate-400">{weather.condition}</p>
        </div>
      </div>
      <div className="flex items-center gap-2 mt-3 text-xs text-slate-500">
        <Thermometer className="w-3 h-3" />
        <span>Humidity: {weather.humidity}%</span>
      </div>
    </div>
  )
}
