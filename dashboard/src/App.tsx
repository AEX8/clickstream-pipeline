import Sidebar from "./components/Sidebar"
import StatStrip from "./components/StatStrip"

function App() {
  return (
    <div className="flex min-h-screen bg-neutral-950 text-neutral-100">
      <Sidebar />
      <div className="flex-1">
        <StatStrip />
        <main className="p-6">
          <p className="text-sm text-neutral-500">
            Funnel and session data will go here.
          </p>
        </main>
      </div>
    </div>
  )
}

export default App