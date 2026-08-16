const NAV_ITEMS = [
    { label: "Overview", active: true },
    { label: "Sessions", active: false },
    { label: "Funnel", active: false },
  ]
  
  export default function Sidebar() {
    return (
      <aside className="w-56 shrink-0 border-r border-neutral-800 bg-neutral-950 p-4">
        <div className="mb-8 px-2">
          <h1 className="text-sm font-semibold tracking-tight text-neutral-100">
            Clickstream
          </h1>
          <p className="text-xs text-neutral-500">Live analytics</p>
        </div>
  
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => (
            <div
              key={item.label}
              className={`rounded-md px-3 py-2 text-sm ${
                item.active
                  ? "bg-neutral-800 text-neutral-100"
                  : "text-neutral-400 hover:bg-neutral-900 hover:text-neutral-200"
              }`}
            >
              {item.label}
            </div>
          ))}
        </nav>
      </aside>
    )
  }