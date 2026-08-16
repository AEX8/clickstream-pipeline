import { useEffect, useState } from "react"

interface SessionRow {
  session_id: string
  device: string
  entry_page: string
  exit_page: string
  event_count: number
  reached_checkout: boolean
  last_seen_at: string
}

export default function SessionsTable() {
  const [sessions, setSessions] = useState<SessionRow[]>([])

  useEffect(() => {
    const fetchSessions = () => {
      fetch("http://localhost:8000/sessions/recent")
        .then((res) => res.json())
        .then(setSessions)
        .catch(() => {
          // silently ignore — table just stays empty/stale if the api's briefly unreachable
        })
    }

    fetchSessions()
    const interval = setInterval(fetchSessions, 5000) // refresh every 5s
    return () => clearInterval(interval)
  }, [])

  return (
    <div>
      <h2 className="mb-3 text-sm font-medium text-neutral-300">Recent sessions</h2>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-neutral-800 text-xs uppercase tracking-wide text-neutral-500">
            <th className="py-2 font-medium">Session</th>
            <th className="py-2 font-medium">Device</th>
            <th className="py-2 font-medium">Entry</th>
            <th className="py-2 font-medium">Exit</th>
            <th className="py-2 font-medium">Events</th>
            <th className="py-2 font-medium">Converted</th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((s) => (
            <tr key={s.session_id} className="border-b border-neutral-900">
              <td className="py-2 text-neutral-400">{s.session_id}...</td>
              <td className="py-2 text-neutral-300">{s.device}</td>
              <td className="py-2 text-neutral-300">{s.entry_page}</td>
              <td className="py-2 text-neutral-300">{s.exit_page}</td>
              <td className="py-2 text-neutral-300">{s.event_count}</td>
              <td className="py-2">
                {s.reached_checkout ? (
                  <span className="text-emerald-400">yes</span>
                ) : (
                  <span className="text-neutral-600">no</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}