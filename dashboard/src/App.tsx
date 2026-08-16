import Sidebar from "./components/Sidebar"
import StatStrip from "./components/StatStrip"
import { useMetrics } from "../hooks/useMetrics"

function App() {
  const { metrics, connected } = useMetrics()

  const pageViews = metrics?.funnel["page_view"] ?? 0
  const completions = metrics?.funnel["checkout_complete"] ?? 0
  const conversionRate =
    pageViews > 0 ? `${((completions / pageViews) * 100).toFixed(1)}%` : null

  return (
    <div className="flex min-h-screen bg-neutral-950 text-neutral-100">
      <Sidebar />
      <div className="flex-1">
        <div className="flex items-center justify-between border-b border-neutral-800 px-6 py-3">
          <span className="text-xs text-neutral-500">
            Window: {metrics ? new Date(metrics.window_start).toLocaleTimeString() : "—"}
          </span>
          <span className={`text-xs ${connected ? "text-emerald-400" : "text-red-400"}`}>
            {connected ? "● live" : "● disconnected"}
          </span>
        </div>

        <StatStrip
          activeUsers={metrics?.active_user_count ?? null}
          eventsPerWindow={metrics?.event_count ?? null}
          conversionRate={conversionRate}
        />

        <main className="p-6">
          <p className="text-sm text-neutral-500">
            Funnel visualization will go here.
          </p>
        </main>
      </div>
    </div>
  )
}

export default App