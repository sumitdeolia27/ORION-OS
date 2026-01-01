"use client"

import { useEffect, useRef } from "react"

interface OrionOrbProps {
  size?: "sm" | "md" | "lg"
}

export function OrionOrb({ size = "md" }: OrionOrbProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const dimensions = {
    sm: 48,
    md: 80,
    lg: 120,
  }

  const dim = dimensions[size]

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    let animationId: number
    let time = 0

    const animate = () => {
      time += 0.02
      ctx.clearRect(0, 0, dim, dim)

      const centerX = dim / 2
      const centerY = dim / 2
      const maxRadius = dim / 2 - 4

      // Outer glow - violet/cyan gradient
      const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, maxRadius)
      gradient.addColorStop(0, "rgba(139, 92, 246, 0.9)")
      gradient.addColorStop(0.3, "rgba(217, 70, 239, 0.6)")
      gradient.addColorStop(0.6, "rgba(6, 182, 212, 0.4)")
      gradient.addColorStop(1, "rgba(139, 92, 246, 0)")

      ctx.beginPath()
      ctx.arc(centerX, centerY, maxRadius, 0, Math.PI * 2)
      ctx.fillStyle = gradient
      ctx.fill()

      // Rotating rings
      for (let i = 0; i < 3; i++) {
        ctx.save()
        ctx.translate(centerX, centerY)
        ctx.rotate(time * (0.5 + i * 0.3))

        ctx.beginPath()
        ctx.ellipse(0, 0, maxRadius * (0.6 - i * 0.1), maxRadius * (0.3 - i * 0.05), 0, 0, Math.PI * 2)
        
        const ringGradient = ctx.createLinearGradient(-maxRadius, 0, maxRadius, 0)
        ringGradient.addColorStop(0, `rgba(139, 92, 246, ${0.8 - i * 0.2})`)
        ringGradient.addColorStop(0.5, `rgba(6, 182, 212, ${0.6 - i * 0.15})`)
        ringGradient.addColorStop(1, `rgba(217, 70, 239, ${0.8 - i * 0.2})`)
        
        ctx.strokeStyle = ringGradient
        ctx.lineWidth = 1.5
        ctx.stroke()

        ctx.restore()
      }

      // Core glow
      const coreGradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, maxRadius * 0.3)
      coreGradient.addColorStop(0, "rgba(255, 255, 255, 1)")
      coreGradient.addColorStop(0.3, "rgba(217, 70, 239, 0.8)")
      coreGradient.addColorStop(0.6, "rgba(139, 92, 246, 0.6)")
      coreGradient.addColorStop(1, "rgba(6, 182, 212, 0.3)")

      ctx.beginPath()
      ctx.arc(centerX, centerY, maxRadius * 0.25, 0, Math.PI * 2)
      ctx.fillStyle = coreGradient
      ctx.fill()

      // Inner bright core
      const innerCore = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, maxRadius * 0.15)
      innerCore.addColorStop(0, "rgba(255, 255, 255, 1)")
      innerCore.addColorStop(1, "rgba(255, 255, 255, 0)")

      ctx.beginPath()
      ctx.arc(centerX, centerY, maxRadius * 0.1, 0, Math.PI * 2)
      ctx.fillStyle = innerCore
      ctx.fill()

      // Orbiting particles
      for (let i = 0; i < 8; i++) {
        const angle = (time + (i * Math.PI * 2) / 8) % (Math.PI * 2)
        const radius = maxRadius * (0.5 + Math.sin(time * 2 + i) * 0.15)
        const x = centerX + Math.cos(angle) * radius
        const y = centerY + Math.sin(angle) * radius

        const particleGradient = ctx.createRadialGradient(x, y, 0, x, y, 3)
        particleGradient.addColorStop(0, "rgba(6, 182, 212, 1)")
        particleGradient.addColorStop(1, "rgba(6, 182, 212, 0)")

        ctx.beginPath()
        ctx.arc(x, y, 2 + Math.sin(time * 3 + i) * 0.5, 0, Math.PI * 2)
        ctx.fillStyle = particleGradient
        ctx.fill()
      }

      // Secondary particles (smaller, faster)
      for (let i = 0; i < 6; i++) {
        const angle = (-time * 1.5 + (i * Math.PI * 2) / 6) % (Math.PI * 2)
        const radius = maxRadius * 0.7
        const x = centerX + Math.cos(angle) * radius
        const y = centerY + Math.sin(angle) * radius

        ctx.beginPath()
        ctx.arc(x, y, 1.5, 0, Math.PI * 2)
        ctx.fillStyle = "rgba(217, 70, 239, 0.8)"
        ctx.fill()
      }

      animationId = requestAnimationFrame(animate)
    }

    animate()

    return () => cancelAnimationFrame(animationId)
  }, [dim])

  return (
    <div className="relative animate-float">
      <canvas
        ref={canvasRef}
        width={dim}
        height={dim}
        className="drop-shadow-[0_0_30px_rgba(139,92,246,0.6)]"
      />
      {/* Extra glow layer */}
      <div
        className="absolute inset-0 rounded-full bg-gradient-to-br from-violet-500/20 via-fuchsia-500/10 to-cyan-500/20 blur-xl animate-pulse"
        style={{ animationDuration: "3s" }}
      />
    </div>
  )
}
