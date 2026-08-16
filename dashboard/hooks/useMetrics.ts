import { useEffect, useRef, useState } from "react"

interface FunnelSteps {
  [eventType: string]: number
}

interface MetricsPayload {
  active_user_count: number
  event_count: number
  window_start: string
  window_end: string
  funnel: FunnelSteps
}

const WS_URL = "ws://localhost:8000/ws/metrics"

export function useMetrics() {
  const [metrics, setMetrics] = useState<MetricsPayload | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)

    ws.onmessage = (event) => {
      const data: MetricsPayload = JSON.parse(event.data)
      setMetrics(data)
    }

    return () => ws.close()
  }, [])

  return { metrics, connected }
}