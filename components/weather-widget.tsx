"use client"

import { useState, useEffect } from "react"
import { Cloud, Sun, CloudRain, Thermometer, CloudSnow, CloudDrizzle, Wind } from "lucide-react"

interface WeatherData {
  temp: number
  condition: string
  humidity: number
  loading: boolean
  error: string | null
}

export function WeatherWidget() {
  const [weather, setWeather] = useState<WeatherData>({
    temp: 22,
    condition: "Sunny",
    humidity: 45,
    loading: true,
    error: null,
  })

  useEffect(() => {
    const fetchWeather = async () => {
      try {
        setWeather((prev) => ({ ...prev, loading: true, error: null }))
        
        // Try to get user's location first (optional)
        let location = "London" // Default location
        
        try {
          // Try to get location from browser (requires user permission)
          const position = await new Promise<GeolocationPosition>((resolve, reject) => {
            if (!navigator.geolocation) {
              reject(new Error("Geolocation not supported"))
              return
            }
            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 })
          })
          
          // Use coordinates for weather API
          const lat = position.coords.latitude
          const lon = position.coords.longitude
          location = `${lat},${lon}`
        } catch (geoError) {
          // Use default location if geolocation fails
          console.log("Using default location:", location)
        }

        // Fetch weather from wttr.in API with timeout
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout

        try {
        const response = await fetch(`https://wttr.in/${location}?format=j1`, {
          method: "GET",
          headers: {
            "Accept": "application/json",
          },
            signal: controller.signal,
        })

          clearTimeout(timeoutId)

        if (!response.ok) {
            throw new Error(`Weather API returned ${response.status}`)
        }

        const data = await response.json()
          
          if (!data || !data.current_condition || !data.current_condition[0]) {
            throw new Error("Invalid weather data received")
          }

        const current = data.current_condition[0]
        
        const temp = parseInt(current.temp_C) || 22
          const condition = current.weatherDesc?.[0]?.value || "Clear"
        const humidity = parseInt(current.humidity) || 45

        setWeather({
          temp,
          condition,
          humidity,
          loading: false,
          error: null,
        })
        } catch (fetchError) {
          clearTimeout(timeoutId)
          
          // If aborted due to timeout
          if (fetchError instanceof Error && fetchError.name === 'AbortError') {
            throw new Error("Weather request timed out")
          }
          
          // Re-throw other errors
          throw fetchError
        }
      } catch (error) {
        console.error("Failed to fetch weather:", error)
        
        // Keep default values and just show error message
        setWeather((prev) => ({
          ...prev,
          loading: false,
          error: error instanceof Error ? error.message : "Failed to load weather",
        }))
      }
    }

    fetchWeather()
    
    // Refresh every 30 minutes
    const interval = setInterval(fetchWeather, 30 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  // Map weather conditions to icons
  const getWeatherIcon = (condition: string): typeof Sun => {
    const lower = condition.toLowerCase()
    if (lower.includes("rain") || lower.includes("drizzle")) return CloudRain
    if (lower.includes("snow")) return CloudSnow
    if (lower.includes("cloud") || lower.includes("overcast")) return Cloud
    if (lower.includes("wind") || lower.includes("breeze")) return Wind
    return Sun // Default to sun for clear/sunny
  }

  const Icon = getWeatherIcon(weather.condition)

  return (
    <div className="glass p-4 rounded-xl border border-violet-500/20">
      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <Cloud className="w-3.5 h-3.5 text-cyan-400" />
        Weather
        {weather.loading && (
          <span className="text-[10px] text-slate-500 ml-auto">Loading...</span>
        )}
      </h4>
      {weather.error ? (
        <div className="text-xs text-amber-400 py-2">
          <p className="text-slate-400">Weather unavailable</p>
          <p className="text-slate-500 mt-1 text-[10px]">Showing default data</p>
        </div>
      ) : (
        <>
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
        </>
      )}
    </div>
  )
}
